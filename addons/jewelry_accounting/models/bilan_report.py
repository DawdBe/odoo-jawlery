from odoo import models, fields, api
from datetime import date, datetime


class BilanGlobalReport(models.TransientModel):
    _name = 'bilan.global.report'
    _description = 'Bilan Patrimonial Global (calculé en direct depuis les modèles métier)'

    year = fields.Integer(
        string='Année',
        default=lambda self: date.today().year,
        help="Année du bilan. Pour le mode courant, doit être l'année en cours.")
    date_cloture = fields.Date(
        string='Date de clôture',
        compute='_compute_date_cloture',
        help="Date d'arrêté du bilan. En mode courant = aujourd'hui ; en mode clôture = 31 décembre de l'année.")
    mode = fields.Selection([
        ('courant', 'Bilan courant'),
        ('cloture', 'Bilan de clôture'),
    ], string='Mode', default='courant',
        help="Courant : situation du jour. Clôture : arrêté au 31 décembre de l'année.")
    is_historical = fields.Boolean(
        string='Année historique',
        compute='_compute_date_cloture',
        help="True si l'année sélectionnée n'est pas l'année en cours.")
    year_bounds = fields.Char(
        string='Années disponibles',
        compute='_compute_year_meta',
        help="Bornes min/max calculées depuis les données en base.")

    # ── Actif ──────────────────────────────────────────────────────────────────
    stock_or_valorise = fields.Monetary(
        string='Stock Or valorisé',
        compute='_compute_actif',
        help="Valeur du stock d'or (tous les métaux de catégorie or) valorisé au cours du jour, via stock.quant.estimated_value.")
    stock_argent_valorise = fields.Monetary(
        string='Stock Argent valorisé',
        compute='_compute_actif',
        help="Valeur du stock d'argent (métaux de catégorie argent) valorisé au cours du jour, via stock.quant.estimated_value.")
    stock_autres_valorise = fields.Monetary(
        string='Autres stocks valorisés',
        compute='_compute_actif',
        help="Valeur des stocks des autres métaux (casse, plaqué, etc.) valorisés au cours du jour, via stock.quant.estimated_value.")
    tresorerie = fields.Monetary(
        string='Trésorerie',
        compute='_compute_actif',
        help="Solde attendu des caisses ouvertes (daily.cash.register.expected_balance).")
    creances_clients = fields.Monetary(
        string='Créances clients',
        compute='_compute_actif',
        help="Total des montants restants dus par les clients (tickets avec remaining_amount > 0, date ≤ date_cloture).")
    total_actif = fields.Monetary(
        string='Total Actif',
        compute='_compute_actif',
        help="Somme de tous les actifs : stock or + argent + autres + trésorerie + créances clients.")

    # ── Passif ─────────────────────────────────────────────────────────────────
    capital_associes = fields.Monetary(
        string='Capital associés',
        compute='_compute_passif',
        help="Total des comptes de capital des associés (associate.account.capital_balance).")
    avances_associes = fields.Monetary(
        string='Avances associés',
        compute='_compute_passif',
        help="Total des avances aux associés (associate.account.advance_balance).")
    repartition_globale = fields.Text(
        string='Répartition globale',
        compute='_compute_passif',
        help="Résumé du nombre d'associés et totaux — ouvrir le détail pour la ventilation complète.")
    dettes_fournisseurs = fields.Monetary(
        string='Dettes fournisseurs',
        compute='_compute_passif',
        help="Total des soldes négatifs fournisseurs : montant que le magasin doit aux fournisseurs.")
    dettes_clients = fields.Monetary(
        string='Dettes clients (créditeurs)',
        compute='_compute_passif',
        help="Total des soldes négatifs des tickets : montant que le magasin doit aux clients.")
    personnel = fields.Monetary(
        string='Personnel',
        compute='_compute_passif',
        help="Total des écritures comptables de type 'personnel' (account.move avec jewelry_operation_type = 'personnel'), agrégé via account.move.line.")
    investissements = fields.Monetary(
        string='Investissements',
        compute='_compute_passif',
        help="Total des écritures comptables de type 'invest' (account.move avec jewelry_operation_type = 'invest'), agrégé via account.move.line.")
    total_passif = fields.Monetary(
        string='Total Passif',
        compute='_compute_passif',
        help="Somme de tous les passifs : capital + avances + dettes fournisseurs + dettes clients + personnel + investissements.")

    # ── Contrôle ───────────────────────────────────────────────────────────────
    ecart_actif_passif = fields.Monetary(
        string='Écart Actif - Passif',
        compute='_compute_controle',
        help="Différence entre total actif et total passif.")
    last_update = fields.Datetime(
        string='Dernier calcul',
        compute='_compute_controle',
        help="Horodatage du dernier calcul du bilan.")
    currency_id = fields.Many2one(
        'res.currency',
        string='Devise',
        default=lambda self: self.env.company.currency_id)

    # ───────────────────────────────────────────────────────────────────────────

    def _get_metal_type_ids_by_category(self):
        """Retourne { 'or': [ids], 'argent': [ids], 'autres': [ids] }
        Logique unique de catégorisation des métaux, utilisée par _compute_actif
        et par les actions de détail (action_view_stock_*)."""
        all_metals = self.env['metal.type'].search([])
        or_ids = [m.id for m in all_metals if 'or' in (m.name or '').lower()]
        argent_ids = [m.id for m in all_metals if 'argent' in (m.name or '').lower()]
        autres_ids = [m.id for m in all_metals if m.id not in or_ids + argent_ids]
        return {'or': or_ids, 'argent': argent_ids, 'autres': autres_ids}

    def _get_year_bounds(self):
        AccountMove = self.env['account.move']
        Ticket = self.env['jewelry.ticket']
        Rate = self.env['gold.rate.history']
        min_year = date.today().year
        max_year = min_year
        for model, date_field in [
            (AccountMove, 'date'),
            (Ticket, 'date'),
            (Rate, 'effective_date'),
        ]:
            min_rec = model.search([], order=f'{date_field} asc', limit=1)
            if min_rec:
                val = getattr(min_rec, date_field)
                if val:
                    min_year = min(min_year, val.year)
            max_rec = model.search([], order=f'{date_field} desc', limit=1)
            if max_rec:
                val = getattr(max_rec, date_field)
                if val:
                    max_year = max(max_year, val.year)
        return min_year, max_year

    @api.depends('year', 'mode')
    def _compute_date_cloture(self):
        for rec in self:
            today = date.today()
            rec.is_historical = rec.year != today.year
            if rec.mode == 'courant' and not rec.is_historical:
                rec.date_cloture = today
            else:
                rec.date_cloture = date(rec.year or today.year, 12, 31)

    @api.depends()
    def _compute_year_meta(self):
        for rec in self:
            min_y, max_y = rec._get_year_bounds()
            rec.year_bounds = f"{min_y}-{max_y}"

    def action_recalculate(self):
        self.ensure_one()
        today = date.today()
        if self.mode == 'courant' and self.year != today.year:
            self.mode = 'cloture'
        self._compute_date_cloture()
        self._compute_actif()
        self._compute_passif()
        self._compute_controle()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bilan.global.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'inline',
        }

    # ── Actif ──────────────────────────────────────────────────────────────────

    @api.depends('year', 'date_cloture', 'mode')
    def _compute_actif(self):
        for rec in self:
            cat = rec._get_metal_type_ids_by_category()

            def sum_stock(metal_ids):
                if not metal_ids:
                    return 0.0
                quants = self.env['stock.quant'].search([('metal_type_id', 'in', metal_ids)])
                return sum(q.estimated_value for q in quants) if quants else 0.0

            rec.stock_or_valorise = sum_stock(cat['or'])
            rec.stock_argent_valorise = sum_stock(cat['argent'])
            rec.stock_autres_valorise = sum_stock(cat['autres'])

            open_regs = self.env['daily.cash.register'].search([('state', '=', 'open')])
            rec.tresorerie = sum(open_regs.mapped('expected_balance')) or 0.0

            dt = rec.date_cloture
            tickets = self.env['jewelry.ticket'].search([
                ('payment_status', 'in', ('impaye', 'partiel')),
                ('date', '<=', dt.isoformat()),
            ])
            total_creances = 0.0
            for t in tickets:
                remaining = t.balance - (
                    sum(l.amount for l in t.cash_line_ids if l.type == 'entree')
                    - sum(l.amount for l in t.cash_line_ids if l.type == 'sortie')
                )
                if remaining > 0:
                    total_creances += remaining
            rec.creances_clients = total_creances

            rec.total_actif = (
                rec.stock_or_valorise
                + rec.stock_argent_valorise
                + rec.stock_autres_valorise
                + rec.tresorerie
                + rec.creances_clients
            )

    # ── Passif ─────────────────────────────────────────────────────────────────

    @api.depends('year', 'date_cloture', 'mode')
    def _compute_passif(self):
        for rec in self:
            cap_data = self.env['associate.account'].read_group(
                [],
                ['capital_balance:sum', 'advance_balance:sum'],
                []
            )
            if cap_data:
                rec.capital_associes = cap_data[0]['capital_balance'] or 0.0
                rec.avances_associes = cap_data[0]['advance_balance'] or 0.0
            else:
                rec.capital_associes = 0.0
                rec.avances_associes = 0.0

            count = self.env['associate.account'].search_count([])
            if count:
                rec.repartition_globale = (
                    f"{count} associé(s) · Capital total : {rec.capital_associes:,.0f} DA · "
                    f"Avances totales : {rec.avances_associes:,.0f} DA — voir détail ci-dessous"
                )
            else:
                rec.repartition_globale = "Aucun associé"

            fourn_accounts = self.env['supplier.account'].search([])
            total_dettes_fourn = 0.0
            for a in fourn_accounts:
                if a.balance < 0:
                    total_dettes_fourn += abs(a.balance)
            rec.dettes_fournisseurs = total_dettes_fourn

            dt = rec.date_cloture
            tickets = self.env['jewelry.ticket'].search([
                ('payment_status', 'in', ('impaye', 'partiel')),
                ('date', '<=', dt.isoformat()),
            ])
            total_dettes_clients = 0.0
            for t in tickets:
                remaining = t.balance - (
                    sum(l.amount for l in t.cash_line_ids if l.type == 'entree')
                    - sum(l.amount for l in t.cash_line_ids if l.type == 'sortie')
                )
                if remaining < 0:
                    total_dettes_clients += abs(remaining)
            rec.dettes_clients = total_dettes_clients

            for fname, optype in [('personnel', 'personnel'), ('investissements', 'invest')]:
                lines_data = self.env['account.move.line'].read_group(
                    [
                        ('move_id.jewelry_operation_type', '=', optype),
                        ('move_id.date', '<=', dt.isoformat()),
                    ],
                    ['balance:sum'],
                    []
                )
                setattr(rec, fname, lines_data[0]['balance'] or 0.0 if lines_data else 0.0)

            rec.total_passif = (
                rec.capital_associes
                + rec.avances_associes
                + rec.dettes_fournisseurs
                + rec.dettes_clients
                + rec.personnel
                + rec.investissements
            )

    # ── Contrôle ────────────────────────────────────────────────────────────────

    @api.depends('total_actif', 'total_passif')
    def _compute_controle(self):
        for rec in self:
            rec.ecart_actif_passif = rec.total_actif - rec.total_passif
            rec.last_update = datetime.now()

    # ── Sauvegarde dans l'historique ────────────────────────────────────────────

    def action_save_bilan(self):
        self.ensure_one()
        history = self.env['bilan.global.history'].create({
            'year': self.year,
            'date_cloture': self.date_cloture,
            'mode': self.mode,
            'generated_on': datetime.now(),
            'generated_by': self.env.user.id,
            'currency_id': (self.currency_id.id or self.env.company.currency_id.id),
            'stock_or_valorise': self.stock_or_valorise,
            'stock_argent_valorise': self.stock_argent_valorise,
            'stock_autres_valorise': self.stock_autres_valorise,
            'tresorerie': self.tresorerie,
            'creances_clients': self.creances_clients,
            'total_actif': self.total_actif,
            'capital_associes': self.capital_associes,
            'avances_associes': self.avances_associes,
            'dettes_fournisseurs': self.dettes_fournisseurs,
            'dettes_clients': self.dettes_clients,
            'personnel': self.personnel,
            'investissements': self.investissements,
            'total_passif': self.total_passif,
            'repartition_globale': self.repartition_globale,
            'ecart_actif_passif': self.ecart_actif_passif,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bilan.global.report',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'inline',
        }

    # ── Impression ──────────────────────────────────────────────────────────────

    def action_print_bilan(self):
        self.ensure_one()
        return self.env.ref('jewelry_accounting.action_report_bilan_global').report_action(self)

    # ── Boutons de détail (drill-down) ──────────────────────────────────────────

    def _action_view_stock(self, metal_ids, name):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('metal_type_id', 'in', metal_ids)],
            'context': {'group_by': 'metal_type_id'},
        }

    def action_view_stock_or(self):
        cat = self._get_metal_type_ids_by_category()
        return self._action_view_stock(cat['or'], 'Stock Or')

    def action_view_stock_argent(self):
        cat = self._get_metal_type_ids_by_category()
        return self._action_view_stock(cat['argent'], 'Stock Argent')

    def action_view_stock_autres(self):
        cat = self._get_metal_type_ids_by_category()
        return self._action_view_stock(cat['autres'], 'Autres stocks')

    def action_view_tresorerie(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'jewelry_transactions.action_daily_cash_register')
        action['domain'] = [('state', '=', 'open')]
        action['context'] = {'search_default_group_by': 'state'}
        return action

    def action_view_creances(self):
        self.ensure_one()
        dt = self.date_cloture
        return {
            'type': 'ir.actions.act_window',
            'name': 'Créances clients',
            'res_model': 'jewelry.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('payment_status', 'in', ('impaye', 'partiel')),
                ('date', '<=', dt.isoformat()),
            ],
            'context': {'search_default_group_by': 'payment_status'},
        }

    def action_view_dettes_clients(self):
        self.ensure_one()
        dt = self.date_cloture
        return {
            'type': 'ir.actions.act_window',
            'name': 'Dettes clients (créditeurs)',
            'res_model': 'jewelry.ticket',
            'view_mode': 'tree,form',
            'domain': [
                ('payment_status', 'in', ('impaye', 'partiel')),
                ('balance', '<', 0),
                ('date', '<=', dt.isoformat()),
            ],
        }

    def action_view_associes(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'jewelry_transactions.action_associate_account')
        action['domain'] = []
        return action

    def action_view_fournisseurs(self):
        self.ensure_one()
        action = self.env['ir.actions.act_window']._for_xml_id(
            'jewelry_transactions.action_supplier_account')
        action['domain'] = []
        return action

    def _action_view_aml(self, optype, name):
        self.ensure_one()
        dt = self.date_cloture
        return {
            'type': 'ir.actions.act_window',
            'name': name,
            'res_model': 'account.move.line',
            'view_mode': 'tree,form',
            'domain': [
                ('move_id.jewelry_operation_type', '=', optype),
                ('move_id.date', '<=', dt.isoformat()),
            ],
        }

    def action_view_personnel(self):
        return self._action_view_aml('personnel', 'Écritures Personnel')

    def action_view_investissements(self):
        return self._action_view_aml('invest', 'Écritures Investissements')
