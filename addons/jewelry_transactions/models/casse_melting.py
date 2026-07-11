from odoo import models, fields, api


class CasseMelting(models.Model):
    _name = 'casse.melting'
    _description = 'Casse Melting'
    _order = 'date desc'
    # Records the melting (smelting) process where scrap gold is melted down
    # into refined gold. Tracks weight before/after, wastage, cost, and the
    # refined value based on current market rates. Profit = refined value - cost.

    name = fields.Char(required=True, default='New')
    date = fields.Date(default=fields.Date.today, required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('casse.melting') or 'New'
        return super().create(vals)
    metal_type_result = fields.Many2one('metal.type', string='Result Metal Type', required=True)
    karat_result = fields.Float(string='Result Karat')
    weight_before = fields.Float(string='Weight Before (g)')
    weight_after = fields.Float(string='Weight After (g)')
    wastage_weight = fields.Float(string='Wastage (g)', compute='_compute_values', store=True)
    total_cost = fields.Monetary(string='Total Cost')
    refined_value = fields.Monetary(string='Refined Value', compute='_compute_values', store=True)
    profit = fields.Monetary(string='Profit', compute='_compute_values', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

    line_ids = fields.One2many('casse.melting.line', 'melting_id', string='Lines')

    @api.depends('weight_before', 'weight_after', 'total_cost', 'metal_type_result')
    def _compute_values(self):
        for record in self:
            record.wastage_weight = (record.weight_before or 0.0) - (record.weight_after or 0.0)
            if record.metal_type_result and record.weight_after:
                rate = record.metal_type_result.get_current_rate('market')
                record.refined_value = record.weight_after * rate
            else:
                record.refined_value = 0.0
            record.profit = record.refined_value - (record.total_cost or 0.0)


