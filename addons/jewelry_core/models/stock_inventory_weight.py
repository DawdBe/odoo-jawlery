from odoo import models, fields, api


class StockInventoryWeight(models.Model):
    _name = 'stock.inventory.weight'
    _description = 'Physical Weight Inventory'
    _order = 'date desc'

    name = fields.Char(required=True, default='New')
    date = fields.Date(default=fields.Date.today, required=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('stock.inventory.weight') or 'New'
        return super().create(vals)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
    ], default='draft', required=True)
    metal_type_id = fields.Many2one('metal.type', string='Metal Type', required=True)
    expected_weight = fields.Float(string='Expected Weight (g)')
    actual_weight = fields.Float(string='Actual Weight (g)')
    difference_weight = fields.Float(string='Difference (g)', compute='_compute_difference')
    line_ids = fields.One2many('stock.inventory.weight.line', 'inventory_id', string='Lines')

    @api.depends('expected_weight', 'actual_weight')
    def _compute_difference(self):
        for record in self:
            record.difference_weight = (record.actual_weight or 0.0) - (record.expected_weight or 0.0)

    def reconcile_weights(self):
        self.state = 'done'


class StockInventoryWeightLine(models.Model):
    _name = 'stock.inventory.weight.line'
    _description = 'Weight Inventory Line'

    inventory_id = fields.Many2one('stock.inventory.weight', string='Inventory', required=True, ondelete='cascade')
    product_id = fields.Many2one('product.product', string='Product', required=True)
    weight_before = fields.Float(string='Weight Before (g)')
    weight_after = fields.Float(string='Weight After (g)')
    weight_difference = fields.Float(string='Difference (g)', compute='_compute_difference')
    notes = fields.Text()

    @api.depends('weight_before', 'weight_after')
    def _compute_difference(self):
        for record in self:
            record.weight_difference = (record.weight_after or 0.0) - (record.weight_before or 0.0)
