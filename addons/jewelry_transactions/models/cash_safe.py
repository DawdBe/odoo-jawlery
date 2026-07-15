from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CashSafe(models.Model):
    _name = 'cash.safe'
    _description = 'Cash Safe / Coffre'
    _rec_name = 'name'

    name = fields.Char(string='Safe Name', default='Coffre Principal', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company, required=True)
    currency_id = fields.Many2one(
        'res.currency', string='Currency',
        default=lambda self: self.env.company.currency_id, required=True)
    current_balance = fields.Monetary(
        string='Current Balance',
        compute='_compute_current_balance',
        currency_field='currency_id',
        help="Solde actuel du coffre : total des entrées moins total des sorties.")
    movement_ids = fields.One2many(
        'cash.safe.movement', 'safe_id', string='Movements')
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('single_safe_per_company',
         'UNIQUE(company_id)',
         _("Un seul coffre peut exister par société. Utilisez le coffre existant.")),
    ]

    @api.depends('movement_ids.type', 'movement_ids.amount')
    def _compute_current_balance(self):
        for safe in self:
            total_in = sum(
                m.amount for m in safe.movement_ids if m.type == 'in')
            total_out = sum(
                m.amount for m in safe.movement_ids if m.type == 'out')
            safe.current_balance = total_in - total_out

    @api.model
    def _get_main_safe(self):
        safe = self.search([('company_id', '=', self.env.company.id)], limit=1)
        if not safe:
            safe = self.create({'name': 'Coffre Principal'})
        return safe

    def action_open_movements(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Safe Movements'),
            'res_model': 'cash.safe.movement',
            'view_mode': 'tree,form',
            'domain': [('safe_id', '=', self.id)],
            'context': {
                'default_safe_id': self.id,
                'search_default_group_by_reason': True,
            },
        }
