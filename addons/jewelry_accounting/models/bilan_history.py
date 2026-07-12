from odoo import models, fields, api
from datetime import datetime


class BilanGlobalHistory(models.Model):
    _name = 'bilan.global.history'
    _description = 'Bilan Patrimonial Global — Historique'
    _order = 'year desc, generated_on desc'

    year = fields.Integer(string='Année', required=True)
    date_cloture = fields.Date(string='Date de clôture', required=True)
    mode = fields.Selection([
        ('courant', 'Bilan courant'),
        ('cloture', 'Bilan de clôture'),
    ], string='Mode', required=True)
    generated_on = fields.Datetime(string='Généré le', default=fields.Datetime.now, required=True)
    generated_by = fields.Many2one('res.users', string='Généré par', default=lambda self: self.env.user, required=True)

    currency_id = fields.Many2one(
        'res.currency', string='Devise',
        default=lambda self: self.env.company.currency_id,
        required=True)

    # ── Actif ──
    stock_or_valorise = fields.Monetary(string='Stock Or valorisé', currency_field='currency_id')
    stock_argent_valorise = fields.Monetary(string='Stock Argent valorisé', currency_field='currency_id')
    stock_autres_valorise = fields.Monetary(string='Autres stocks valorisés', currency_field='currency_id')
    tresorerie = fields.Monetary(string='Trésorerie', currency_field='currency_id')
    creances_clients = fields.Monetary(string='Créances clients', currency_field='currency_id')
    total_actif = fields.Monetary(string='Total Actif', currency_field='currency_id')

    # ── Passif ──
    capital_associes = fields.Monetary(string='Capital associés', currency_field='currency_id')
    avances_associes = fields.Monetary(string='Avances associés', currency_field='currency_id')
    dettes_fournisseurs = fields.Monetary(string='Dettes fournisseurs', currency_field='currency_id')
    dettes_clients = fields.Monetary(string='Dettes clients (créditeurs)', currency_field='currency_id',
        help="Total des soldes négatifs des tickets : montant que le magasin doit aux clients (balance < 0).")
    personnel = fields.Monetary(string='Personnel', currency_field='currency_id')
    investissements = fields.Monetary(string='Investissements', currency_field='currency_id')
    total_passif = fields.Monetary(string='Total Passif', currency_field='currency_id')

    # ── Autres ──
    repartition_globale = fields.Text(string='Répartition globale')

    # ── Contrôle ──
    ecart_actif_passif = fields.Monetary(string='Écart Actif - Passif', currency_field='currency_id')
    status = fields.Selection([
        ('balanced', 'Équilibré'),
        ('not_balanced', 'Non équilibré'),
    ], string='Statut', compute='_compute_status', store=True)

    @api.depends('ecart_actif_passif')
    def _compute_status(self):
        for rec in self:
            rec.status = 'balanced' if abs(rec.ecart_actif_passif or 0.0) < 0.01 else 'not_balanced'

    # ── Drill-down actions (same logic as transient but reading own stored values) ──

    def _get_metal_type_ids_by_category(self):
        all_metals = self.env['metal.type'].search([])
        or_ids = [m.id for m in all_metals if 'or' in (m.name or '').lower()]
        argent_ids = [m.id for m in all_metals if 'argent' in (m.name or '').lower()]
        autres_ids = [m.id for m in all_metals if m.id not in or_ids + argent_ids]
        return {'or': or_ids, 'argent': argent_ids, 'autres': autres_ids}

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

    def action_print_bilan(self):
        self.ensure_one()
        return self.env.ref('jewelry_accounting.action_report_bilan_global_history').report_action(self)

    def action_open_in_bilan(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'bilan.global.report',
            'view_mode': 'form',
            'target': 'inline',
            'context': {
                'default_year': self.year,
                'default_mode': self.mode,
            },
        }
