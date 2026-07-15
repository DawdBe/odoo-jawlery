from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    weight_total = fields.Float(string='Total Weight (g)')
    metal_type_id = fields.Many2one('metal.type', related='product_id.product_tmpl_id.metal_type_id', store=True)
    move_type = fields.Selection([
        ('achat', 'Achat'),
        ('vente', 'Vente'),
        ('transfert', 'Transfert'),
        ('fasonage', 'Fasonage'),
        ('fonte', 'Fonte'),
    ], string='Move Type')

    def _action_done(self):
        res = super()._action_done()
        for move in self:
            if not move.weight_total:
                continue
            for ml in move.move_line_ids:
                if ml.product_id.type != 'product':
                    continue
                domain = [
                    ('product_id', '=', ml.product_id.id),
                    ('location_id', '=', ml.location_dest_id.id),
                    ('lot_id', '=', ml.lot_id.id or False),
                    ('package_id', '=', ml.result_package_id.id or False),
                    ('owner_id', '=', ml.owner_id.id or False),
                ]
                quant = self.env['stock.quant'].search(domain, limit=1, order='id DESC')
                if quant and not quant.weight_total:
                    quant.weight_total = move.weight_total
        return res
