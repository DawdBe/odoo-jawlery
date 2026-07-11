from odoo import models, fields, api


class ServiceOrder(models.Model):
    _name = 'service.order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Service Order (Fasonage / Repair)'
    _order = 'received_date desc'
    # Manages workshop orders: fasonage (gold transformation), repairs,
    # gold plating (dorure/argenture), engraving (gravure), and assembly (goupelle).
    # Tracks raw gold input, finished weight, wastage, and pricing via atelier price tables.

    name = fields.Char(required=True, default='New')
    partner_id = fields.Many2one('res.partner', string='Client', required=True, tracking=True)

    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('service.order') or 'New'
        return super().create(vals)
    atelier_id = fields.Many2one('res.partner', string='Atelier', domain="[('partner_type','=','atelier')]")
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket')
    service_type = fields.Selection([
        ('fasonage', 'Fasonage'),
        ('reparation', 'Réparation'),
        ('dorure', 'Dorure'),
        ('argenture', 'Argenture'),
        ('gravure', 'Gravure'),
        ('goupelle', 'Goupelle'),
    ], string='Service Type', required=True)
    style = fields.Selection([
        ('massif', 'Massif'),
        ('massif_lux', 'Massif Lux'),
        ('bataille', 'Bataille'),
        ('massif_controle', 'Massif Controlé'),
        ('mesaise', 'Mesaise'),
        ('or_750', 'Or 750'),
    ], string='Style')
    raw_gold_weight = fields.Float(string='Raw Gold Weight (g)')
    raw_gold_metal = fields.Many2one('metal.type', string='Raw Gold Metal')
    finished_weight = fields.Float(string='Finished Weight (g)')
    wastage_weight = fields.Float(string='Wastage (g)', compute='_compute_wastage', store=True)
    wastage_percentage = fields.Float(string='Wastage %', compute='_compute_wastage', store=True)
    status = fields.Selection([
        ('received', 'Received'),
        ('in_progress', 'In Progress'),
        ('ready', 'Ready'),
        ('delivered', 'Delivered'),
    ], string='Status', default='received', tracking=True)
    payment_status = fields.Selection([
        ('impaye', 'Impayé'),
        ('partiel', 'Partiel'),
        ('paye', 'Payé'),
    ], string='Payment Status', default='impaye', tracking=True)
    price_from_table = fields.Monetary(string='Price from Atelier Table', compute='_compute_price_from_table')
    min_profit_percentage = fields.Float(string='Min Profit %', default=20.0)
    received_date = fields.Datetime(default=fields.Datetime.now)
    estimated_ready_date = fields.Date(string='Estimated Ready Date')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

    @api.depends('raw_gold_weight', 'finished_weight')
    def _compute_wastage(self):
        # Wastage = gold lost during the fasonage process (e.g., filings, dust).
        # This is normal in jewelry manufacturing and represents a profit center
        # for the store (wastage remains store property after fasonage).
        for order in self:
            raw = order.raw_gold_weight or 0.0
            fin = order.finished_weight or 0.0
            order.wastage_weight = raw - fin
            order.wastage_percentage = ((raw - fin) / raw * 100.0) if raw else 0.0

    @api.depends('atelier_id', 'style', 'raw_gold_metal')
    def _compute_price_from_table(self):
        for order in self:
            if order.atelier_id and order.style and order.raw_gold_metal:
                table = self.env['atelier.price.table'].search([
                    ('atelier_id', '=', order.atelier_id.id),
                    ('style', '=', order.style),
                    ('metal_type_id', '=', order.raw_gold_metal.id),
                ], limit=1)
                if table and order.finished_weight:
                    order.price_from_table = table.cost_per_gram * order.finished_weight
                else:
                    order.price_from_table = 0.0
            else:
                order.price_from_table = 0.0

    def validate_selling_price(self, proposed_price):
        # Ensures the selling price covers at least the atelier cost + min profit margin.
        # Returns (is_valid, minimum_price) tuple.
        self.ensure_one()
        if self.price_from_table and self.min_profit_percentage:
            min_price = self.price_from_table * (1 + self.min_profit_percentage / 100)
            return proposed_price >= min_price, min_price
        return True, 0.0
