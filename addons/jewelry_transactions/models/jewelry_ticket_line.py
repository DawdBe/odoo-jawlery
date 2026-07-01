from odoo import models, fields, api


class JewelryTicketLine(models.Model):
    _name = 'jewelry.ticket.line'
    _description = 'Ticket Line'
    _order = 'id'

    ticket_id = fields.Many2one('jewelry.ticket', string='Ticket', required=True, ondelete='cascade')
    line_type = fields.Selection([
        ('vente', 'Vente'),
        ('achat_casse', 'Achat Casse'),
        ('achat', 'Achat'),
        ('service', 'Service'),
        ('fasonage', 'Fasonage'),
        ('verse', 'Versé'),
        ('solde', 'Solde'),
        ('remise', 'Remise'),
    ], string='Line Type', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    weight = fields.Float(string='Weight (g)')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    description = fields.Char(string='Description')
    price_unit = fields.Monetary(string='Unit Price')
    price_subtotal = fields.Monetary(string='Subtotal')
    remise_type = fields.Selection([
        ('none', 'None'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ], string='Remise Type', default='none')
    remise_value = fields.Float(string='Remise Value')
    remise_amount = fields.Monetary(string='Remise Amount', compute='_compute_remise_amount')
    currency_id = fields.Many2one('res.currency', related='ticket_id.currency_id', store=True)
    notes = fields.Text()

    casse_melting_line_ids = fields.One2many('casse.melting.line', 'ticket_line_id', string='Melting Lines')

    @api.depends('price_subtotal', 'remise_type', 'remise_value')
    def _compute_remise_amount(self):
        for line in self:
            if line.remise_type == 'percentage':
                line.remise_amount = (line.price_subtotal or 0.0) * (line.remise_value or 0.0) / 100.0
            elif line.remise_type == 'fixed':
                line.remise_amount = line.remise_value or 0.0
            else:
                line.remise_amount = 0.0

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            product = self.product_id
            self.description = product.display_name
            if product.weight:
                self.weight = product.weight
            else:
                tmpl = product.product_tmpl_id
                self.weight = tmpl.net_weight or tmpl.gross_weight or 0.0
            self.metal_type_id = product.product_tmpl_id.metal_type_id
            self.price_unit = product.lst_price

    @api.onchange('metal_type_id', 'line_type')
    def _onchange_metal_type(self):
        if self.metal_type_id and self.line_type in ('achat_casse', 'achat'):
            rate = self.metal_type_id.get_current_rate('market')
            if rate:
                self.price_unit = rate
            elif self.metal_type_id:
                live = self.env['gold.rate.history'].search([
                    ('metal_type_id', '=', self.metal_type_id.id),
                    ('is_active', '=', True),
                ], order='effective_date desc', limit=1)
                if live and live.base_24k_usd and live.dzd_parallel_rate:
                    self.price_unit = live.base_24k_usd * live.dzd_parallel_rate

    @api.onchange('weight', 'price_unit')
    def _onchange_price_subtotal(self):
        if self.weight and self.price_unit:
            self.price_subtotal = self.weight * self.price_unit
