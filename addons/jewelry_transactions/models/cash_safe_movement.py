from odoo import models, fields, api, _


class CashSafeMovement(models.Model):
    _name = 'cash.safe.movement'
    _description = 'Safe Movement'
    _order = 'date desc, id desc'

    safe_id = fields.Many2one(
        'cash.safe', string='Safe', required=True, ondelete='cascade')
    type = fields.Selection([
        ('in', 'IN — Cash enters the safe'),
        ('out', 'OUT — Cash leaves the safe'),
    ], string='Direction', required=True)
    amount = fields.Monetary(string='Amount', required=True)
    reason = fields.Selection([
        ('opening_balance', "Solde d'ouverture"),
        ('register_float', 'Float vers Caisse'),
        ('register_return', 'Retour de Caisse'),
        ('owner_deposit', 'Dépôt Propriétaire'),
        ('owner_withdrawal', 'Retrait Propriétaire'),
        ('bank_deposit', 'Dépôt Banque'),
        ('bank_withdrawal', 'Retrait Banque'),
        ('direct_income', 'Revenu Direct'),
        ('direct_expense', 'Dépense Directe'),
        ('manual_adjustment', 'Ajustement Manuel'),
        ('transfer', 'Transfert'),
    ], string='Reason', required=True,
       help='Why this movement occurred. Used for audit trail.')
    register_id = fields.Many2one(
        'daily.cash.register', string='Cash Register',
        ondelete='set null',
        help='Linked daily register if this is a float or return movement.')
    date = fields.Datetime(
        string='Date', default=fields.Datetime.now, required=True)
    notes = fields.Char(string='Notes')
    company_id = fields.Many2one(
        'res.company', string='Company',
        related='safe_id.company_id', store=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        related='safe_id.currency_id', store=True)

    @api.constrains('amount')
    def _check_positive_amount(self):
        for line in self:
            if line.amount < 0:
                raise models.ValidationError(
                    _("Amount must be positive. Use 'type' to indicate direction."))
