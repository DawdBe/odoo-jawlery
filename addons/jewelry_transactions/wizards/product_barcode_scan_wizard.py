from odoo import models, fields, api


class ProductBarcodeScanWizard(models.TransientModel):
    _name = 'product.barcode.scan.wizard'
    _description = 'Scan Product Barcode Wizard'

    barcode = fields.Char(string='Barcode', required=True, help='Scan or type the product barcode')
    product_id = fields.Many2one('product.product', string='Product', readonly=True)
    product_name = fields.Char(string='Product Name', readonly=True)
    product_barcode = fields.Char(string='Barcode', readonly=True)
    product_weight = fields.Float(string='Weight (g)', readonly=True)
    product_price = fields.Monetary(string='Price', readonly=True)
    metal_type_id = fields.Many2one('metal.type', string='Metal Type', readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    partner_id = fields.Many2one('res.partner', string='Partner')
    open_ticket_id = fields.Many2one('jewelry.ticket', string='Open Ticket', readonly=True)
    has_open_ticket = fields.Boolean(compute='_compute_has_open_ticket')

    @api.depends('open_ticket_id')
    def _compute_has_open_ticket(self):
        for wiz in self:
            wiz.has_open_ticket = bool(wiz.open_ticket_id)

    @api.model
    def create(self, vals):
        rec = super().create(vals)
        if vals.get('barcode'):
            rec._lookup_barcode()
        return rec

    def _lookup_barcode(self):
        self.ensure_one()
        if not self.barcode:
            return
        product = self.env['product.product'].search([('barcode', '=', self.barcode)], limit=1)
        if not product and self.barcode.isdigit():
            product = self.env['product.product'].browse(int(self.barcode)).exists()
        if not product and self.barcode.isdigit():
            tmpl = self.env['product.template'].browse(int(self.barcode)).exists()
            if tmpl:
                product = tmpl.product_variant_id
        if not product:
            product = self.env['product.product'].search([('default_code', '=', self.barcode)], limit=1)
        if not product:
            tmpl = self.env['product.template'].search([('barcode', '=', self.barcode)], limit=1)
            if tmpl:
                product = tmpl.product_variant_id
        self.product_id = product
        if product:
            self.product_name = product.display_name
            self.product_barcode = product.barcode
            self.product_weight = product.weight or product.product_tmpl_id.net_weight or 0.0
            self.product_price = product.lst_price
            self.metal_type_id = product.product_tmpl_id.metal_type_id
        self._find_open_ticket()

    @api.onchange('barcode')
    def _onchange_barcode(self):
        self._lookup_barcode()

    def _find_open_ticket(self):
        open_ticket = self.env['jewelry.ticket'].search([
            ('payment_status', '=', 'impaye'),
        ], order='date desc, id desc', limit=1)
        self.open_ticket_id = open_ticket
        if open_ticket:
            self.partner_id = open_ticket.partner_id

    def action_add_to_ticket(self):
        self.ensure_one()
        if not self.product_id or not self.open_ticket_id:
            return
        self.env['jewelry.ticket.line'].create({
            'ticket_id': self.open_ticket_id.id,
            'line_type': 'vente',
            'product_id': self.product_id.id,
            'quantity': 1.0,
            'weight': self.product_weight,
            'metal_type_id': self.metal_type_id.id if self.metal_type_id else False,
            'price_unit': self.product_price,
            'price_subtotal': self.product_price,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jewelry.ticket',
            'res_id': self.open_ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_ticket_and_add(self):
        self.ensure_one()
        if not self.product_id:
            return
        if not self.partner_id:
            return {
                'type': 'ir.actions.show_warning',
                'message': 'Please select a partner before creating a new ticket.',
            }
        ticket = self.env['jewelry.ticket'].create({
            'partner_id': self.partner_id.id,
            'cashier_id': self.env.user.id,
        })
        self.env['jewelry.ticket.line'].create({
            'ticket_id': ticket.id,
            'line_type': 'vente',
            'product_id': self.product_id.id,
            'quantity': 1.0,
            'weight': self.product_weight,
            'metal_type_id': self.metal_type_id.id if self.metal_type_id else False,
            'price_unit': self.product_price,
            'price_subtotal': self.product_price,
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jewelry.ticket',
            'res_id': ticket.id,
            'view_mode': 'form',
            'target': 'current',
        }
