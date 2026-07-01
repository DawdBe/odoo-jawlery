from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_print_barcode(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/print/barcode/%s' % self.id,
            'target': 'new',
        }

    barcode = fields.Char(readonly=True)
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    jewelry_category = fields.Selection([
        ('fini', 'Fini (Finished)'),
        ('brut', 'Brut (Raw)'),
        ('pierre', 'Pierre (Stone)'),
        ('fourniture', 'Fourniture (Supply)'),
    ], string='Jewelry Category')
    net_weight = fields.Float(string='Weight (g)')
    style = fields.Selection([
        ('massif', 'Massif'),
        ('massif_lux', 'Massif Lux'),
        ('bataille', 'Bataille'),
        ('massif_controle', 'Massif Controlé'),
        ('mesaise', 'Mesaise'),
        ('or_750', 'Or 750'),
    ], string='Style')

    @api.model
    def create(self, vals):
        if not vals.get('list_price') and vals.get('metal_type_id') and vals.get('net_weight'):
            metal_type = self.env['metal.type'].browse(vals['metal_type_id'])
            rate = metal_type.get_current_rate('market')
            vals['list_price'] = (vals['net_weight'] or 0.0) * rate
        return super().create(vals)

    def write(self, vals):
        if 'list_price' not in vals and (vals.get('metal_type_id') or vals.get('net_weight')):
            for record in self:
                m_id = vals.get('metal_type_id', record.metal_type_id.id)
                w = vals.get('net_weight', record.net_weight)
                if m_id and w:
                    metal_type = self.env['metal.type'].browse(m_id)
                    rate = metal_type.get_current_rate('market')
                    vals['list_price'] = (w or 0.0) * rate
                break
        return super().write(vals)

    @api.onchange('metal_type_id', 'net_weight')
    def _onchange_metal_pricing(self):
        if self.metal_type_id and self.net_weight:
            rate = self.metal_type_id.get_current_rate('market')
            self.list_price = (self.net_weight or 0.0) * rate


class ProductProduct(models.Model):
    _inherit = 'product.product'

    serial_number = fields.Char(string='Serial Number')
    certificate_number = fields.Char(string='Certificate Number')
    weight = fields.Float(string='Weight (g)')
    location_id = fields.Many2one('stock.location', string='Location')

    @api.model
    def create(self, vals):
        if not vals.get('barcode'):
            tmpl_id = vals.get('product_tmpl_id')
            if tmpl_id:
                template = self.env['product.template'].browse(tmpl_id)
                if template.barcode:
                    barcode_taken = self.search_count([
                        ('barcode', '=', template.barcode),
                    ]) > 0
                    if not barcode_taken:
                        vals['barcode'] = template.barcode
            if not vals.get('barcode'):
                seq = self.env['ir.sequence'].next_by_code('product.barcode') or ''
                if seq:
                    vals['barcode'] = seq
        return super().create(vals)
