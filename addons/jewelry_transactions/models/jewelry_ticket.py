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
    ], string='Product Status', default='donne_au_client', tracking=True)
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

    @api.depends('ticket_line_ids.price_subtotal', 'ticket_line_ids.line_type', 'ticket_line_ids.remise_amount')
    def _compute_totals(self):
        for ticket in self:
            cash_in = 0.0
            cash_out = 0.0
            remise = 0.0
            for line in ticket.ticket_line_ids:
                if line.line_type in ('vente', 'solde', 'service', 'fasonage'):
                    cash_in += line.price_subtotal or 0.0
                elif line.line_type in ('achat_casse', 'achat', 'verse'):
                    cash_out += line.price_subtotal or 0.0
                if line.remise_type != 'none':
                    remise += line.remise_amount or 0.0
            ticket.total_cash_in = cash_in
            ticket.total_cash_out = cash_out
            ticket.balance = cash_in - cash_out
            ticket.total_remise = remise

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
        date_map = {}
        for ticket in self:
            if not ticket.date:
                ticket.related_register_id = False
                continue
            ticket_date = ticket.date
            if isinstance(ticket_date, datetime):
                ticket_date = ticket_date.date()
            if ticket_date not in date_map:
                register = self.env['daily.cash.register']._get_or_create_for_date(ticket_date)
                date_map[ticket_date] = register.id if register else False
            ticket.related_register_id = date_map[ticket_date]

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('jewelry.ticket') or 'New'
        if not vals.get('barcode'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code('jewelry.ticket.barcode') or vals['name']
        return super().create(vals)

    def write(self, vals):
        return super().write(vals)

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


