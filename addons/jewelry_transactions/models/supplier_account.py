from odoo import models, fields, api


class SupplierAccount(models.Model):
    _name = 'supplier.account'
    _description = 'Supplier / Atelier Account'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    partner_type = fields.Selection([
        ('fournisseur', 'Fournisseur'),
        ('atelier', 'Atelier'),
    ], string='Partner Type')
    weight_balance = fields.Float(
        string='Weight Balance (g)',
        compute='_compute_total_weight_balance',
        help='Total gold weight across all purities')
    balance = fields.Monetary(string='Solde', compute='_compute_balance')
    last_transaction_date = fields.Datetime(string='Last Transaction')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    purchase_order_ids = fields.One2many('purchase.order', 'supplier_account_id', string='Purchase Orders')
    gold_movement_ids = fields.One2many('gold.movement', 'supplier_account_id', string='Gold Movements')
    ticket_ids = fields.One2many('jewelry.ticket', compute='_compute_ticket_ids', string='Tickets')
    ticket_count = fields.Integer(string='Ticket Count', compute='_compute_ticket_ids')
    gold_balance_ids = fields.One2many(
        'supplier.gold.balance',
        compute='_compute_gold_balances',
        string='Gold Balances per Purity')

    @api.depends('partner_id', 'partner_id.ticket_ids')
    def _compute_ticket_ids(self):
        for account in self:
            tickets = account.partner_id.ticket_ids if account.partner_id else self.env['jewelry.ticket']
            account.ticket_ids = tickets
            account.ticket_count = len(tickets)

    @api.depends('gold_movement_ids.active', 'gold_movement_ids.type', 'gold_movement_ids.weight', 'gold_movement_ids.working_purity')
    def _compute_gold_balances(self):
        GoldMovement = self.env['gold.movement']
        for account in self:
            movements = GoldMovement.search([
                ('supplier_account_id', '=', account.id),
                ('active', '=', True),
            ])
            by_purity = {}
            for gm in movements:
                key = gm.working_purity or 0.0
                sign = 1 if gm.type == 'entree' else -1
                by_purity[key] = by_purity.get(key, 0.0) + sign * gm.weight
            balances = self.env['supplier.gold.balance']
            for purity, balance in by_purity.items():
                if balance:
                    balances |= self.env['supplier.gold.balance'].new({
                        'supplier_account_id': account.id,
                        'metal_type_id': False,
                        'working_purity': purity,
                        'balance_weight': balance,
                    })
            account.gold_balance_ids = balances

    @api.depends('gold_movement_ids.active', 'gold_movement_ids.type', 'gold_movement_ids.weight')
    def _compute_total_weight_balance(self):
        for account in self:
            total = 0.0
            for gm in account.gold_movement_ids:
                if gm.active:
                    total += gm.weight if gm.type == 'entree' else -gm.weight
            account.weight_balance = total

    @api.depends('partner_id', 'partner_id.ticket_ids.cash_line_ids.amount',
                 'partner_id.ticket_ids.cash_line_ids.type',
                 'partner_id.ticket_ids.ticket_line_ids.price_subtotal',
                 'partner_id.ticket_ids.ticket_line_ids.line_type',
                 'partner_id.ticket_ids.ticket_line_ids.settlement_type')
    def _compute_balance(self):
        for account in self:
            total = 0.0
            for ticket in account.ticket_ids:
                if not ticket.is_supplier_ticket:
                    entree = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'entree').mapped('amount'))
                    sortie = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'sortie').mapped('amount'))
                    total += ticket.balance - (entree - sortie)
                else:
                    cash_balance = 0.0
                    for line in ticket.ticket_line_ids:
                        if line.settlement_type != 'gold_credit' and line.line_type not in ('remise',):
                            if line.line_type in ('vente', 'solde', 'service', 'fasonage'):
                                cash_balance += line.price_subtotal or 0.0
                            elif line.line_type in ('achat_casse', 'achat', 'verse', 'personnel', 'fixe'):
                                cash_balance -= line.price_subtotal or 0.0
                        elif line.line_type == 'remise':
                            cash_balance += line.price_subtotal or 0.0
                    entree = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'entree').mapped('amount'))
                    sortie = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'sortie').mapped('amount'))
                    total += cash_balance - (entree - sortie)
            account.balance = total

    def compute_weight_value(self, current_rate):
        self.ensure_one()
        return self.weight_balance * current_rate

    def action_open_gold_movements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gold Movements',
            'res_model': 'gold.movement',
            'view_mode': 'tree,form',
            'domain': [('supplier_account_id', '=', self.id)],
            'context': {'default_supplier_account_id': self.id},
            'target': 'current',
        }
