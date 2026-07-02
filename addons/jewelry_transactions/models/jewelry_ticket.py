from odoo import models, fields, api, _


class JewelryTicket(models.Model):
    _name = 'jewelry.ticket'
    _description = 'Unified Jewelry Ticket'
    _order = 'date desc, id desc'

    name = fields.Char(string='Ticket #', required=True, default='New')
    barcode = fields.Char(string='Barcode', copy=False)
    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    cashier_id = fields.Many2one('res.users', string='Cashier', default=lambda self: self.env.user)
    seller_id = fields.Many2one('res.users', string='Seller')
    payment_status = fields.Selection([
        ('impaye', 'Impayé'),
        ('partiel', 'Partiel'),
        ('paye', 'Payé'),
    ], string='Payment Status', default='impaye')
    product_status = fields.Selection([
        ('en_stock', 'En Stock'),
        ('en_fasonage', 'En Fasonage'),
        ('termine', 'Terminé'),
        ('donne_au_client', 'Donné au Client'),
    ], string='Product Status', default='en_stock')
    total_cash_in = fields.Monetary(string='Total Cash In', compute='_compute_totals', store=True)
    total_cash_out = fields.Monetary(string='Total Cash Out', compute='_compute_totals', store=True)
    balance = fields.Monetary(string='Balance', compute='_compute_totals', store=True)
    total_remise = fields.Monetary(string='Total Remise', compute='_compute_totals', store=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    active = fields.Boolean(default=True)
    notes = fields.Text()

    ticket_line_ids = fields.One2many('jewelry.ticket.line', 'ticket_id', string='Ticket Lines')
    associate_transaction_ids = fields.One2many('associate.transaction', 'ticket_id', string='Associate Transactions')
    service_order_ids = fields.One2many('service.order', 'ticket_id', string='Service Orders')
    cash_line_ids = fields.One2many('cash.register.line', 'ticket_id', string='Cash Lines')

    @api.depends('ticket_line_ids.price_subtotal', 'ticket_line_ids.line_type')
    def _compute_totals(self):
        for ticket in self:
            cash_in = 0.0
            cash_out = 0.0
            remise = 0.0
            for line in ticket.ticket_line_ids:
                if line.line_type in ('vente', 'solde'):
                    cash_in += line.price_subtotal or 0.0
                elif line.line_type in ('achat_casse', 'achat', 'verse'):
                    cash_out += line.price_subtotal or 0.0
                if line.remise_type != 'none':
                    remise += line.remise_amount or 0.0
            ticket.total_cash_in = cash_in
            ticket.total_cash_out = cash_out
            ticket.balance = cash_in - cash_out
            ticket.total_remise = remise

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('jewelry.ticket') or 'New'
        if not vals.get('barcode'):
            vals['barcode'] = self.env['ir.sequence'].next_by_code('jewelry.ticket.barcode') or vals['name']
        return super().create(vals)

    def action_update_prices_from_gold_rate(self):
        for ticket in self:
            for line in ticket.ticket_line_ids:
                if line.line_type in ('achat_casse', 'achat') and line.metal_type_id:
                    rate = line.metal_type_id.get_current_rate('market')
                    if rate:
                        line.price_unit = rate
                        line._onchange_price_subtotal()
        return True

    def register_payment(self, amount):
        self.ensure_one()
        if amount > 0:
            self.payment_status = 'paye' if amount >= abs(self.balance) else 'partiel'
            register = self.env['daily.cash.register'].search([('state', '=', 'open')], limit=1)
            self.env['cash.register.line'].create({
                'register_id': register.id if register else False,
                'ticket_id': self.id,
                'partner_id': self.partner_id.id,
                'amount': amount,
                'type': 'entree' if self.balance >= 0 else 'sortie',
                'description': _('Paiement ticket %s') % self.name,
            })
