from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssociateTransaction(models.Model):
    _name = 'associate.transaction'
    _description = 'Associate Transaction'
    _order = 'date desc, id desc'

    account_id = fields.Many2one(
        'associate.account', string='Account',
        required=True, ondelete='restrict', index=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner', required=True,
        help="Historical partner reference. Synced from account on creation.")
    transaction_type = fields.Selection([
        ('capital_deposit', 'Capital Deposit'),
        ('capital_withdrawal', 'Capital Withdrawal'),
        ('advance_profit', 'Advance on Profit'),
        ('profit_distribution', 'Profit Distribution'),
        ('profit_effort', 'Profit Effort'),
        ('zakat', 'Zakat'),
    ], string='Type', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('posted', 'Posted'),
        ('cancelled', 'Cancelled'),
    ], string='State', required=True, default='draft',
        help="Draft: editable. Posted: immutable, affects balances. "
             "Cancelled: no effect on balances.")
    origin = fields.Selection([
        ('manual', 'Manual Entry'),
        ('ticket', 'From Ticket'),
        ('accounting', 'From Accounting'),
        ('profit_close', 'Profit Closing'),
        ('zakat', 'Zakat Calculation'),
    ], string='Origin', required=True, default='manual',
        help='How this transaction was created.')
    source_model = fields.Char(
        string='Source Document',
        help='Model name of the originating business document '
             '(e.g. jewelry.ticket, account.move).')
    source_id = fields.Integer(
        string='Source Document ID',
        help='ID of the originating business document.')
    user_id = fields.Many2one(
        'res.users', string='Originator',
        default=lambda self: self.env.user, readonly=True)
    date = fields.Datetime(default=fields.Datetime.now)
    fiscal_year = fields.Char(string='Fiscal Year')
    ticket_id = fields.Many2one(
        'jewelry.ticket', string='Linked Ticket',
        index=True, ondelete='set null')
    account_move_id = fields.Many2one(
        'account.move', string='Journal Entry',
        index=True, ondelete='set null')
    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

    @api.onchange('account_id')
    def _onchange_account_id(self):
        if self.account_id:
            self.partner_id = self.account_id.partner_id

    @api.constrains('amount')
    def _check_positive_amount(self):
        for rec in self:
            if rec.amount < 0:
                raise ValidationError(
                    _("Amount must be positive. Use transaction_type "
                      "to indicate direction."))

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('account_id') and not vals.get('partner_id'):
                account = self.env['associate.account'].browse(vals['account_id'])
                vals['partner_id'] = account.partner_id.id
            if not vals.get('state'):
                vals['state'] = 'draft'
        return super().create(vals_list)

    def write(self, vals):
        posted = self.filtered(lambda r: r.state == 'posted')
        if posted:
            allowed = {'state'}
            if not set(vals.keys()) <= allowed:
                raise ValidationError(
                    _("Cannot modify a posted transaction. Cancel it first."))
        return super().write(vals)

    def unlink(self):
        if self.filtered(lambda r: r.state != 'draft'):
            raise ValidationError(
                _("Only draft transactions can be deleted."))
        return super().unlink()

    def action_post(self):
        for rec in self:
            if rec.state != 'draft':
                raise ValidationError(
                    _("Only draft transactions can be posted."))
            rec.state = 'posted'

    def action_cancel(self):
        for rec in self:
            if rec.state != 'posted':
                raise ValidationError(
                    _("Only posted transactions can be cancelled."))
            rec.state = 'cancelled'

    def action_draft(self):
        for rec in self:
            if rec.state != 'cancelled':
                raise ValidationError(
                    _("Only cancelled transactions can be reset to draft."))
            rec.state = 'draft'
