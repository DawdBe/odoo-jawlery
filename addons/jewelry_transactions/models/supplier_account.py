from odoo import models, fields, api


class SupplierAccount(models.Model):
    _name = 'supplier.account'
    _description = 'Supplier / Atelier Account'
    # Tracks weight balance (gold) and cash balance (money) for suppliers and ateliers.
    # weight_balance is computed from gold movements and purchase orders.
    # balance is computed from tickets: negative = shop owes supplier, positive = supplier owes shop.

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    partner_type = fields.Selection([
        ('fournisseur', 'Fournisseur'),
        ('atelier', 'Atelier'),
    ], string='Partner Type')
    weight_balance = fields.Float(string='Weight Balance (g)', compute='_compute_balances', store=True)
    balance = fields.Monetary(string='Solde', compute='_compute_balance')
    last_transaction_date = fields.Datetime(string='Last Transaction')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    purchase_order_ids = fields.One2many('purchase.order', 'supplier_account_id', string='Purchase Orders')
    gold_movement_ids = fields.One2many('gold.movement', 'supplier_account_id', string='Gold Movements')
    ticket_ids = fields.One2many('jewelry.ticket', compute='_compute_ticket_ids', string='Tickets')
    ticket_count = fields.Integer(string='Ticket Count', compute='_compute_ticket_ids')

    @api.depends('partner_id', 'partner_id.ticket_ids')
    def _compute_ticket_ids(self):
        for account in self:
            tickets = account.partner_id.ticket_ids if account.partner_id else self.env['jewelry.ticket']
            account.ticket_ids = tickets
            account.ticket_count = len(tickets)

    @api.depends('purchase_order_ids.gold_weight_in', 'purchase_order_ids.gold_weight_out',
                 'gold_movement_ids.type', 'gold_movement_ids.weight')
    def _compute_balances(self):
        for account in self:
            weight = 0.0
            for po in account.purchase_order_ids:
                weight += (po.gold_weight_in or 0.0) - (po.gold_weight_out or 0.0)
            for gm in account.gold_movement_ids:
                if gm.type == 'entree':
                    weight += gm.weight or 0.0
                else:
                    weight -= gm.weight or 0.0
            account.weight_balance = weight

    @api.depends('ticket_ids.balance', 'ticket_ids.cash_line_ids.amount', 'ticket_ids.cash_line_ids.type')
    def _compute_balance(self):
        for account in self:
            total = 0.0
            for ticket in account.ticket_ids:
                entree = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'entree').mapped('amount'))
                sortie = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'sortie').mapped('amount'))
                total += ticket.balance - (entree - sortie)
            account.balance = total

    def compute_weight_value(self, current_rate):
        self.ensure_one()
        return self.weight_balance * current_rate
