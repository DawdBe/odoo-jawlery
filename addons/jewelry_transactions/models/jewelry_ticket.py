from datetime import datetime

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class JewelryTicket(models.Model):
    _name = 'jewelry.ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Unified Jewelry Ticket'
    _order = 'date desc, id desc'
    # Core business document: a single ticket handles ALL operations types
    # (sales, purchases, services, deposits, etc.) in one unified document.
    # This implements the "bon multi-opérations" requirement where a customer
    # can sell old gold AND buy new jewelry on the same ticket.
    # Lines define the operation type via the line_type field.

    name = fields.Char(string='Ticket #', required=True, default='New')
    barcode = fields.Char(string='Barcode', copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True, tracking=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    cashier_id = fields.Many2one('res.users', string='Cashier', default=lambda self: self.env.user, tracking=True)
    payment_status = fields.Selection([
        ('impaye', 'Impayé'),
        ('partiel', 'Partiel'),
        ('paye', 'Payé'),
    ], string='Payment Status', compute='_compute_payment_status', store=True, tracking=True)
    product_status = fields.Selection([
        ('donne_au_client', 'Donné au Client'),
        ('termine', 'Terminé'),
        ('en_fasonage', 'En Fasonage'),
        ('en_stock', 'En Stock'),
    ], string='Product Status', default='en_stock', tracking=True)
    # Product status tracks the physical goods:
    # Items can be in stock, sent for fasonage (workshop), finished, or given to customer.
    total_cash_in = fields.Monetary(string='Total Cash In', compute='_compute_totals', store=True)
    total_cash_out = fields.Monetary(string='Total Cash Out', compute='_compute_totals', store=True)
    balance = fields.Monetary(string='Balance', compute='_compute_totals', store=True)
    total_remise = fields.Monetary(string='Total Remise', compute='_compute_totals', store=True)
    paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_payment_info')
    remaining_amount = fields.Monetary(string='Remaining', compute='_compute_payment_info')
    payment_amount = fields.Monetary(string='Payment Amount')
    payment_type = fields.Selection([
        ('entree', 'Entrée — on reçoit'),
        ('sortie', 'Sortie — on donne'),
    ], string='Type', default='entree')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True, tracking=True)
    notes = fields.Text()

    ticket_line_ids = fields.One2many('jewelry.ticket.line', 'ticket_id', string='Ticket Lines')

    # Supplier running account fields (visible only when partner has a supplier.account)
    has_supplier_account = fields.Boolean(
        compute='_compute_supplier_balances',
        help='Whether the partner has an associated supplier account')

    partner_cash_creance_before = fields.Monetary(
        string='Créance Avant', compute='_compute_supplier_balances', currency_field='currency_id')
    partner_cash_dette_before = fields.Monetary(
        string='Dette Avant', compute='_compute_supplier_balances', currency_field='currency_id')
    partner_cash_solde_before = fields.Monetary(
        string='Solde Espèces Avant', compute='_compute_supplier_soldes', currency_field='currency_id')
    partner_cash_creance_after = fields.Monetary(
        string='Créance Après', compute='_compute_supplier_balances', currency_field='currency_id')
    partner_cash_dette_after = fields.Monetary(
        string='Dette Après', compute='_compute_supplier_balances', currency_field='currency_id')
    partner_cash_solde_after = fields.Monetary(
        string='Solde Espèces Après', compute='_compute_supplier_soldes', currency_field='currency_id')
    ticket_cash_creance_delta = fields.Monetary(
        string='Variation Créance', compute='_compute_supplier_balances', currency_field='currency_id')
    ticket_cash_dette_delta = fields.Monetary(
        string='Variation Dette', compute='_compute_supplier_balances', currency_field='currency_id')

    partner_gold_creance_before = fields.Float(
        string='Or Créance Avant (g)', compute='_compute_supplier_balances')
    partner_gold_dette_before = fields.Float(
        string='Or Dette Avant (g)', compute='_compute_supplier_balances')
    partner_gold_solde_before = fields.Float(
        string='Or Solde Avant (g)', compute='_compute_supplier_soldes')
    partner_gold_creance_after = fields.Float(
        string='Or Créance Après (g)', compute='_compute_supplier_balances')
    partner_gold_dette_after = fields.Float(
        string='Or Dette Après (g)', compute='_compute_supplier_balances')
    partner_gold_solde_after = fields.Float(
        string='Or Solde Après (g)', compute='_compute_supplier_soldes')
    ticket_gold_creance_delta = fields.Float(
        string='Variation Or Créance (g)', compute='_compute_supplier_balances')
    ticket_gold_dette_delta = fields.Float(
        string='Variation Or Dette (g)', compute='_compute_supplier_balances')
    is_supplier_ticket = fields.Boolean(
        compute='_compute_is_supplier_ticket',
        help='Whether the partner is a supplier/atelier')
    supplier_gold_balance_ids = fields.One2many(
        'supplier.gold.balance',
        compute='_compute_supplier_gold_balances',
        string='Gold Balances per Purity')
    gold_credit_line_ids = fields.One2many(
        'jewelry.ticket.line',
        compute='_compute_gold_credit_lines',
        string='Gold Credit Lines')

    melting_id = fields.Many2one(
        'casse.melting', string='Melting Batch',
        readonly=True, copy=False, index=True,
        help='Melting batch that consumed all Achat Casse lines from this ticket')
    melting_ids = fields.Many2many(
        'casse.melting', string='Melting Batches',
        compute='_compute_melting_ids',
        help='Melting batches that consumed Achat Casse lines from this ticket')
    associate_transaction_ids = fields.One2many('associate.transaction', 'ticket_id', string='Associate Transactions')
    service_order_ids = fields.One2many('service.order', 'ticket_id', string='Service Orders')
    cash_line_ids = fields.One2many('cash.register.line', 'ticket_id', string='Cash Lines')
    related_register_id = fields.Many2one(
        'daily.cash.register',
        string='Related Register',
        compute='_compute_related_register',
        store=True,
        help="Registre de caisse dont la date correspond à celle du ticket. "
             "Permet le recalcule automatique du solde attendu du registre.",
    )

    client_cash_balance = fields.Monetary(
        string='Solde dû',
        compute='_compute_client_cash_balance',
        currency_field='currency_id',
        help="Solde dû par le client : somme des soldes de tous ses tickets "
             "− somme des encaissements + somme des décaissements. "
             "Positif = le client doit de l'argent à la boutique. "
             "Négatif = la boutique doit de l'argent au client.",
    )
    contrib_to_cash_balance = fields.Monetary(
        string='Contribution Cash',
        compute='_compute_contrib_to_cash_balance',
        currency_field='currency_id',
    )

    @api.depends('partner_id', 'partner_id.partner_type')
    def _compute_is_supplier_ticket(self):
        for ticket in self:
            ticket.is_supplier_ticket = ticket.partner_id and ticket.partner_id.partner_type in ('frs', 'atelier')

    @api.depends('partner_id')
    def _compute_supplier_gold_balances(self):
        for ticket in self:
            if ticket.is_supplier_ticket:
                account = self.env['supplier.account'].search(
                    [('partner_id', '=', ticket.partner_id.id)], limit=1)
                ticket.supplier_gold_balance_ids = account and self.env['supplier.gold.balance'].search(
                    [('supplier_account_id', '=', account.id)]) or self.env['supplier.gold.balance']
            else:
                ticket.supplier_gold_balance_ids = self.env['supplier.gold.balance']

    @api.depends('ticket_line_ids.settlement_type', 'ticket_line_ids.line_type')
    def _compute_gold_credit_lines(self):
        for ticket in self:
            ticket.gold_credit_line_ids = ticket.ticket_line_ids.filtered(
                lambda l: l.settlement_type == 'gold_credit'
                and l.metal_type_id)

    @api.depends('melting_id', 'ticket_line_ids.melting_id')
    def _compute_melting_ids(self):
        for ticket in self:
            ids = set()
            if ticket.melting_id:
                ids.add(ticket.melting_id.id)
            ids.update(ticket.ticket_line_ids.mapped('melting_id').ids)
            ticket.melting_ids = [(6, 0, list(ids))]

    @api.depends('ticket_line_ids.price_subtotal', 'ticket_line_ids.line_type', 'ticket_line_ids.settlement_type', 'ticket_line_ids.remise_amount')
    def _compute_totals(self):
        for ticket in self:
            cash_in = 0.0
            cash_out = 0.0
            for line in ticket.ticket_line_ids:
                if line.settlement_type == 'gold_credit':
                    continue
                if line.line_type in ('vente', 'solde', 'service', 'fasonage'):
                    cash_in += line.price_subtotal or 0.0
                elif line.line_type in ('achat_casse', 'achat', 'verse'):
                    cash_out += line.price_subtotal or 0.0
            ticket.total_cash_in = cash_in
            ticket.total_cash_out = cash_out
            ticket.balance = cash_in - cash_out
            ticket.total_remise = sum(
                line.remise_amount or 0.0
                for line in ticket.ticket_line_ids)

    @api.depends('cash_line_ids.amount', 'cash_line_ids.type', 'balance')
    def _compute_payment_info(self):
        for ticket in self:
            entree = sum(l.amount for l in ticket.cash_line_ids if l.type == 'entree')
            sortie = sum(l.amount for l in ticket.cash_line_ids if l.type == 'sortie')
            ticket.paid_amount = entree - sortie
            ticket.remaining_amount = ticket.balance - (entree - sortie)

    @api.depends('cash_line_ids.amount', 'cash_line_ids.type', 'balance')
    def _compute_payment_status(self):
        for ticket in self:
            entree = sum(l.amount for l in ticket.cash_line_ids if l.type == 'entree')
            sortie = sum(l.amount for l in ticket.cash_line_ids if l.type == 'sortie')
            net_paid = entree - sortie
            remaining = ticket.balance - net_paid
            if net_paid == 0:
                ticket.payment_status = 'impaye'
            elif abs(remaining) < 0.01:
                ticket.payment_status = 'paye'
            else:
                ticket.payment_status = 'partiel'

    def action_update_prices_from_gold_rate(self):
        # Recalculates purchase line prices using the latest gold market rate.
        # Useful when rates change between ticket creation and finalization.
        for ticket in self:
            for line in ticket.ticket_line_ids:
                if line.line_type in ('achat_casse', 'achat') and line.metal_type_id:
                    rate = line.metal_type_id.get_current_rate('market')
                    if rate:
                        line.price_unit = rate
        return True

    def _get_cash_contribution(self):
        self.ensure_one()
        entree = sum(l.amount for l in self.cash_line_ids if l.type == 'entree')
        sortie = sum(l.amount for l in self.cash_line_ids if l.type == 'sortie')
        return (self.balance or 0.0) - entree + sortie

    @api.depends('partner_id')
    def _compute_client_cash_balance(self):
        grouped = {}
        for ticket in self:
            if not ticket.partner_id:
                ticket.client_cash_balance = 0.0
                continue
            grouped.setdefault(ticket.partner_id.id, []).append(ticket)
        for partner_id, tickets in grouped.items():
            all_tickets = self.search([('partner_id', '=', partner_id)])
            total = sum(t._get_cash_contribution() for t in all_tickets)
            for ticket in tickets:
                ticket.client_cash_balance = total

    @api.depends('balance', 'cash_line_ids.amount')
    def _compute_contrib_to_cash_balance(self):
        for ticket in self:
            ticket.contrib_to_cash_balance = ticket._get_cash_contribution()

    @api.depends('date')
    def _compute_related_register(self):
        for ticket in self:
            if not ticket.date:
                ticket.related_register_id = False
                continue
            ticket_date = ticket.date
            if isinstance(ticket_date, datetime):
                ticket_date = ticket_date.date()
            register = self.env['daily.cash.register'].search(
                [('date', '=', ticket_date)], limit=1)
            ticket.related_register_id = register.id if register else False

    @api.depends(
        'partner_id',
        'ticket_line_ids.line_type',
        'ticket_line_ids.weight',
        'ticket_line_ids.metal_type_id',
        'ticket_line_ids.settlement_type',
        'ticket_line_ids.price_subtotal',
        'ticket_line_ids.remise_amount',
    )
    def _compute_supplier_balances(self):
        for ticket in self:
            account = self.env['supplier.account'].search(
                [('partner_id', '=', ticket.partner_id.id)], limit=1)
            if account:
                ticket.has_supplier_account = True

                # ── Read old line effects from DB (for saved tickets) ──
                old_creance = 0.0
                old_dette = 0.0
                old_gold_creance = 0.0
                old_gold_dette = 0.0
                if isinstance(ticket.id, int):
                    self.env.cr.execute("""
                        SELECT price_subtotal, remise_amount, line_type,
                               settlement_type, metal_type_id, weight, purity
                        FROM jewelry_ticket_line
                        WHERE ticket_id = %s
                    """, [ticket.id])
                    for row in self.env.cr.dictfetchall():
                        temp = self.env['jewelry.ticket.line'].new(row)
                        effects = temp._get_account_effects()
                        cash = effects['cash_delta']
                        if cash > 0:
                            old_dette += cash
                        elif cash < 0:
                            old_creance += abs(cash)
                        raw_gc = effects['gold_creance']
                        raw_gd = effects['gold_dette']
                        old_gold_creance += raw_gc
                        old_gold_dette += raw_gd

                # ── Cash: new line effects from current form ──
                new_creance = 0.0
                new_dette = 0.0
                for line in ticket.ticket_line_ids:
                    effects = line._get_account_effects()
                    if effects['cash_delta'] > 0:
                        new_dette += effects['cash_delta']
                    elif effects['cash_delta'] < 0:
                        new_creance += abs(effects['cash_delta'])

                # ── Cash: Before / After (line effects only; payments excluded) ──
                ticket.partner_cash_creance_before = max(
                    0.0, (account.cash_creance or 0.0) - old_creance)
                ticket.partner_cash_dette_before = max(
                    0.0, (account.cash_dette or 0.0) - old_dette)
                ticket.partner_cash_creance_after = max(
                    0.0,
                    ticket.partner_cash_creance_before + new_creance)
                ticket.partner_cash_dette_after = max(
                    0.0,
                    ticket.partner_cash_dette_before + new_dette)

                ticket.ticket_cash_creance_delta = new_creance
                ticket.ticket_cash_dette_delta = new_dette

                # ── Gold: new effects ──
                new_gold_creance = 0.0
                new_gold_dette = 0.0
                for line in ticket.ticket_line_ids:
                    effects = line._get_account_effects()
                    new_gold_creance += effects['gold_creance']
                    new_gold_dette += effects['gold_dette']

                # ── Gold: Before / After ──
                ticket.partner_gold_creance_before = max(
                    0.0, (account.gold_creance or 0.0) - old_gold_creance)
                ticket.partner_gold_dette_before = max(
                    0.0, (account.gold_dette or 0.0) - old_gold_dette)
                ticket.partner_gold_creance_after = max(
                    0.0,
                    ticket.partner_gold_creance_before + new_gold_creance)
                ticket.partner_gold_dette_after = max(
                    0.0,
                    ticket.partner_gold_dette_before + new_gold_dette)

                ticket.ticket_gold_creance_delta = new_gold_creance
                ticket.ticket_gold_dette_delta = new_gold_dette
            else:
                ticket.has_supplier_account = False
                ticket.partner_cash_creance_before = 0.0
                ticket.partner_cash_dette_before = 0.0
                ticket.partner_cash_creance_after = 0.0
                ticket.partner_cash_dette_after = 0.0
                ticket.ticket_cash_creance_delta = 0.0
                ticket.ticket_cash_dette_delta = 0.0
                ticket.partner_gold_creance_before = 0.0
                ticket.partner_gold_dette_before = 0.0
                ticket.partner_gold_creance_after = 0.0
                ticket.partner_gold_dette_after = 0.0
                ticket.ticket_gold_creance_delta = 0.0
                ticket.ticket_gold_dette_delta = 0.0

    @api.depends(
        'partner_cash_creance_before', 'partner_cash_dette_before',
        'partner_cash_creance_after', 'partner_cash_dette_after',
        'partner_gold_creance_before', 'partner_gold_dette_before',
        'partner_gold_creance_after', 'partner_gold_dette_after')
    def _compute_supplier_soldes(self):
        for ticket in self:
            ticket.partner_cash_solde_before = \
                (ticket.partner_cash_creance_before or 0.0) \
                - (ticket.partner_cash_dette_before or 0.0)
            ticket.partner_cash_solde_after = \
                (ticket.partner_cash_creance_after or 0.0) \
                - (ticket.partner_cash_dette_after or 0.0)
            ticket.partner_gold_solde_before = \
                (ticket.partner_gold_creance_before or 0.0) \
                - (ticket.partner_gold_dette_before or 0.0)
            ticket.partner_gold_solde_after = \
                (ticket.partner_gold_creance_after or 0.0) \
                - (ticket.partner_gold_dette_after or 0.0)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('jewelry.ticket') or 'New'
        if not vals.get('barcode'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code('jewelry.ticket.barcode') or vals['name']
        ticket = super().create(vals)
        ticket._sync_to_melting()
        return ticket

    def write(self, vals):
        res = super().write(vals)
        for ticket in self:
            ticket._sync_to_melting()
            ticket._sync_supplier_gold()
        return res

    def unlink(self):
        GoldMovement = self.env['gold.movement']
        MeltingLine = self.env['casse.melting.line']
        for ticket in self:
            GoldMovement.search([('ticket_id', '=', ticket.id), ('active', '=', True)]).write(
                {'active': False, 'inactive_reason': 'ticket_deleted'})
            MeltingLine.search([('ticket_id', '=', ticket.id)]).unlink()
        return super().unlink()

    def _sync_to_melting(self):
        self.ensure_one()
        if self.melting_id:
            return
        draft = self.env['casse.melting']._get_current_draft()
        if not draft:
            return
        draft._add_ticket(self)

    def _sync_supplier_gold(self):
        self.ensure_one()
        account = self.env['supplier.account'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not account:
            return
        GoldMovement = self.env['gold.movement']
        existing = GoldMovement.search([('ticket_id', '=', self.id), ('active', '=', True)])
        gold_lines = self.ticket_line_ids.filtered(
            lambda l: l.settlement_type == 'gold_credit' and l.metal_type_id)
        expected_descs = []
        for line in gold_lines:
            if line.line_type in ('achat_casse', 'achat'):
                direction = 'entree'
            elif line.line_type == 'vente':
                direction = 'sortie'
            else:
                continue
            expected_descs.append({
                'direction': direction,
                'line': line,
            })
        used_move_ids = set()
        for desc in expected_descs:
            line = desc['line']
            move = existing.filtered(
                lambda m, d=desc: m.type == d['direction']
                and m.metal_type_id.id == line.metal_type_id.id
                and m.id not in used_move_ids)
            if move:
                move = move[0]
                used_move_ids.add(move.id)
                changed = (
                    abs(move.weight - (line.weight or 0.0)) > 0.001
                    or abs(move.purity - (line.purity or 0.0)) > 0.001
                )
                if changed:
                    move.write({'active': False, 'inactive_reason': 'ticket_update'})
                    GoldMovement.create({
                        'supplier_account_id': account.id,
                        'purpose': 'deposit' if desc['direction'] == 'entree' else 'payment',
                        'type': desc['direction'],
                        'weight': line.weight,
                        'purity': line.purity,
                        'metal_type_id': line.metal_type_id.id,
                        'date': fields.Datetime.now(),
                        'description': _('Ticket %s') % self.name,
                        'ticket_id': self.id,
                        'origin_model': 'jewelry.ticket',
                        'origin_id': self.id,
                    })
            else:
                GoldMovement.create({
                    'supplier_account_id': account.id,
                    'purpose': 'deposit' if desc['direction'] == 'entree' else 'payment',
                    'type': desc['direction'],
                    'weight': line.weight,
                    'purity': line.purity,
                    'metal_type_id': line.metal_type_id.id,
                    'date': fields.Datetime.now(),
                    'description': _('Ticket %s') % self.name,
                    'ticket_id': self.id,
                    'origin_model': 'jewelry.ticket',
                    'origin_id': self.id,
                })
        for move in existing:
            if move.id not in used_move_ids:
                move.write({'active': False, 'inactive_reason': 'ticket_update'})

    def action_register_payment(self):
        self.ensure_one()
        if self.payment_amount <= 0:
            return True
        if abs(self.remaining_amount) < 0.01:
            return True
        if self.payment_amount > abs(self.remaining_amount):
            raise UserError(
                _('Payment amount (%.2f) exceeds remaining balance (%.2f).')
                % (self.payment_amount, abs(self.remaining_amount))
            )
        self.register_payment(self.payment_amount, self.payment_method)
        self.payment_amount = 0.0
        return True

    def register_payment(self, amount, payment_method='cash'):
        self.ensure_one()
        if amount <= 0:
            return
        today_date = fields.Date.today()
        register = self.env['daily.cash.register'].search([('date', '=', today_date)], limit=1)
        if register and register.state == 'closed':
            raise UserError(_(
                "Le registre du %s est déjà clôturé. "
                "Rouvrez-le avant d'enregistrer ce paiement."
            ) % today_date)
        self.write({
            'cash_line_ids': [(0, 0, {
                'partner_id': self.partner_id.id,
                'amount': amount,
                'type': 'entree' if self.remaining_amount >= 0 else 'sortie',
                'payment_method': payment_method,
                'date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'description': _('Paiement ticket %s') % self.name,
                'origin': 'ticket',
            })]
        })

    def action_open_ticket_form(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jewelry.ticket',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_cash_balance_lines(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Détail Solde Espèces'),
            'res_model': 'jewelry.ticket',
            'view_mode': 'tree',
            'views': [(self.env.ref('jewelry_transactions.view_jewelry_ticket_cash_balance_tree').id, 'tree')],
            'domain': [('partner_id', '=', self.partner_id.id), ('payment_status', '!=', 'paye')],
            'target': 'new',
        }

    def action_open_associate_account(self):
        self.ensure_one()
        if not self.partner_id:
            return
        account = self.env['associate.account'].search(
            [('partner_id', '=', self.partner_id.id)], limit=1)
        if not account:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'associate.account',
            'view_mode': 'form',
            'res_id': account.id,
            'target': 'current',
            'name': _('Associate Account'),
        }

    def action_open_melting(self):
        self.ensure_one()
        if not self.melting_ids:
            return
        if len(self.melting_ids) == 1:
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'casse.melting',
                'res_id': self.melting_ids.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'casse.melting',
            'domain': [('id', 'in', self.melting_ids.ids)],
            'view_mode': 'tree,form',
            'target': 'current',
        }


