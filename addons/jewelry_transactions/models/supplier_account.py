from odoo import models, fields, api


class SupplierAccount(models.Model):
    _name = 'supplier.account'
    _description = 'Supplier / Atelier Account'

    partner_id = fields.Many2one('res.partner', string='Partner', required=True)
    partner_type = fields.Selection([
        ('fournisseur', 'Fournisseur'),
        ('atelier', 'Atelier'),
    ], string='Partner Type')
    working_purity = fields.Float(
        string='Pureté de travail (‰)', default=750.0,
        help='Pureté utilisée pour normaliser tous les soldes or de ce fournisseur. '
             'Les poids des mouvements sont convertis dynamiquement vers cette pureté.')

    cash_creance = fields.Monetary(string='Créance', compute='_compute_cash_ledger')
    cash_dette = fields.Monetary(string='Dette', compute='_compute_cash_ledger')
    cash_solde = fields.Monetary(string='Solde Espèces', compute='_compute_cash_ledger')

    gold_creance = fields.Float(string='Or Créance (g)', compute='_compute_gold_ledger')
    gold_dette = fields.Float(string='Or Dette (g)', compute='_compute_gold_ledger')
    gold_solde = fields.Float(string='Or Solde (g)', compute='_compute_gold_ledger')

    last_transaction_date = fields.Datetime(string='Last Transaction')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    purchase_order_ids = fields.One2many('purchase.order', 'supplier_account_id', string='Purchase Orders')
    gold_movement_ids = fields.One2many('gold.movement', 'supplier_account_id', string='Gold Movements')
    ticket_ids = fields.One2many('jewelry.ticket', compute='_compute_ticket_ids', string='Tickets')
    ticket_count = fields.Integer(string='Ticket Count', compute='_compute_ticket_ids')
    gold_balance_ids = fields.One2many(
        'supplier.gold.balance',
        compute='_compute_gold_balances',
        string='Gold Balance')

    @api.depends('partner_id', 'partner_id.ticket_ids')
    def _compute_ticket_ids(self):
        for account in self:
            tickets = account.partner_id.ticket_ids if account.partner_id else self.env['jewelry.ticket']
            account.ticket_ids = tickets
            account.ticket_count = len(tickets)

    @api.depends('gold_movement_ids.active', 'gold_movement_ids.type', 'gold_movement_ids.weight',
                 'gold_movement_ids.purity', 'working_purity')
    def _compute_gold_ledger(self):
        for account in self:
            wp = account.working_purity or 1.0
            creance = 0.0
            dette = 0.0
            for gm in account.gold_movement_ids:
                if gm.active and gm.weight and gm.purity:
                    converted = gm.weight * gm.purity / wp
                    if gm.type == 'entree':
                        creance += converted
                    else:
                        dette += converted
                elif gm.active and gm.weight:
                    if gm.type == 'entree':
                        creance += gm.weight
                    else:
                        dette += gm.weight
            account.gold_creance = creance
            account.gold_dette = dette
            account.gold_solde = creance - dette

    @api.depends('gold_movement_ids.active', 'gold_movement_ids.type', 'gold_movement_ids.weight',
                 'gold_movement_ids.purity', 'working_purity')
    def _compute_gold_balances(self):
        for account in self:
            wp = account.working_purity or 1.0
            creance = 0.0
            dette = 0.0
            for gm in account.gold_movement_ids:
                if gm.active and gm.weight and gm.purity:
                    converted = gm.weight * gm.purity / wp
                    if gm.type == 'entree':
                        creance += converted
                    else:
                        dette += converted
                elif gm.active and gm.weight:
                    if gm.type == 'entree':
                        creance += gm.weight
                    else:
                        dette += gm.weight
            if creance or dette:
                account.gold_balance_ids = self.env['supplier.gold.balance'].new({
                    'supplier_account_id': account.id,
                    'working_purity': wp,
                    'gold_creance': creance,
                    'gold_dette': dette,
                    'gold_solde': creance - dette,
                })
            else:
                account.gold_balance_ids = self.env['supplier.gold.balance']

    @api.depends('partner_id', 'partner_id.ticket_ids.cash_line_ids.amount',
                 'partner_id.ticket_ids.cash_line_ids.type',
                 'partner_id.ticket_ids.ticket_line_ids.price_subtotal',
                 'partner_id.ticket_ids.ticket_line_ids.line_type',
                 'partner_id.ticket_ids.ticket_line_ids.settlement_type',
                 'partner_id.ticket_ids.ticket_line_ids.remise_amount')
    def _compute_cash_ledger(self):
        for account in self:
            creance_total = 0.0
            dette_total = 0.0
            for ticket in account.ticket_ids:
                if not ticket.is_supplier_ticket:
                    entree = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'entree').mapped('amount'))
                    sortie = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'sortie').mapped('amount'))
                    contribution = (ticket.balance or 0.0) - (entree - sortie)
                else:
                    cash_balance = sum(
                        line._get_account_effects()['cash_delta']
                        for line in ticket.ticket_line_ids)
                    entree = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'entree').mapped('amount'))
                    sortie = sum(ticket.cash_line_ids.filtered(lambda l: l.type == 'sortie').mapped('amount'))
                    contribution = cash_balance - (entree - sortie)
                if contribution > 0:
                    dette_total += contribution
                else:
                    creance_total += abs(contribution)
            account.cash_creance = creance_total
            account.cash_dette = dette_total
            account.cash_solde = creance_total - dette_total

    def compute_weight_value(self, current_rate):
        self.ensure_one()
        return self.gold_creance * current_rate

    def action_open_gold_movements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Gold Movements',
            'res_model': 'gold.movement',
            'view_mode': 'tree,form',
            'domain': [('supplier_account_id', '=', self.id)],
            'context': {'default_supplier_account_id': self.id, 'create': False},
            'target': 'current',
        }
