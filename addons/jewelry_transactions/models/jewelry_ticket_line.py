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
        ('personnel', 'Personnel'),
        ('fixe', 'Fixe'),
    ], string='Line Type', required=True)
    product_id = fields.Many2one('product.product', string='Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    weight = fields.Float(string='Poids mesuré (g)')
    measured_purity = fields.Float(
        string='Pureté mesurée (‰)', default=750.0,
        help='Titre réel mesuré de l\'or (ex: 875 pour 21K, 750 pour 18K). '
             'Ces données physiques ne sont jamais modifiées automatiquement.')
    working_purity = fields.Float(
        string='Pureté de travail (‰)', default=750.0,
        help='Titre choisi pour les calculs ERP (ex: 750, 585, 800). '
             'Le poids de travail est recalculé automatiquement lorsque vous modifiez cette valeur.')
    working_weight = fields.Float(
        string='Poids de travail (g)', compute='_compute_working_weight', store=True,
        help='Poids normalisé utilisé pour les calculs ERP (valorisation, soldes fournisseur, '
             'mouvements d\'or). Calculé automatiquement : poids mesuré × pureté mesurée / pureté de travail.')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    description = fields.Char(string='Description')
    price_unit = fields.Monetary(string='Unit Price')
    price_subtotal = fields.Monetary(string='Subtotal', compute='_compute_price_subtotal', store=True, inverse='_inverse_price_subtotal')
    remise_type = fields.Selection([
        ('none', 'None'),
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed'),
    ], string='Remise Type', default='none')
    remise_value = fields.Float(string='Remise Value')
    remise_amount = fields.Monetary(string='Remise Amount', compute='_compute_remise_amount', store=True)
    currency_id = fields.Many2one('res.currency', related='ticket_id.currency_id', store=True)
    settlement_type = fields.Selection([
        ('immediate_cash', 'Immediate Cash'),
        ('cash_credit', 'Cash Credit'),
        ('gold_credit', 'Gold Credit'),
    ], string='Settlement', default='immediate_cash')
    is_supplier_line = fields.Boolean(related='ticket_id.is_supplier_ticket', string='Is Supplier Line')
    notes = fields.Text()

    melting_id = fields.Many2one(
        'casse.melting', string='Melting Batch',
        readonly=True, copy=False, index=True,
        help='The melting batch that consumed this ticket line')

    @api.depends('weight', 'measured_purity', 'working_purity')
    def _compute_working_weight(self):
        for line in self:
            if line.weight and line.measured_purity and line.working_purity and line.measured_purity != line.working_purity:
                line.working_weight = (line.weight or 0.0) * (line.measured_purity or 0.0) / (line.working_purity or 1.0)
            else:
                line.working_weight = line.weight or 0.0

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
                self.weight = tmpl.net_weight or 0.0
            self.metal_type_id = product.product_tmpl_id.metal_type_id
            if self.metal_type_id:
                default_purity = self.metal_type_id.purity_percentage * 10.0
                self.measured_purity = default_purity
                self.working_purity = default_purity
            if self.metal_type_id and self.line_type != 'service':
                rate = self.metal_type_id.get_current_rate('market')
                if rate:
                    self.price_unit = rate
                    return
            self.price_unit = product.lst_price

    @api.onchange('weight', 'measured_purity', 'working_purity')
    def _onchange_purity_values(self):
        if self.weight and self.measured_purity and self.working_purity and self.measured_purity != self.working_purity:
            self.working_weight = (self.weight or 0.0) * (self.measured_purity or 0.0) / (self.working_purity or 1.0)
        else:
            self.working_weight = self.weight or 0.0

    @api.onchange('metal_type_id', 'line_type')
    def _onchange_metal_type(self):
        if self.line_type == 'solde':
            self.price_subtotal = self.ticket_id.balance
            return
        if self.metal_type_id:
            default_purity = self.metal_type_id.purity_percentage * 10.0
            self.measured_purity = default_purity
            self.working_purity = default_purity
        if self.metal_type_id and self.line_type != 'service':
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

    @api.depends('line_type', 'metal_type_id', 'working_weight', 'quantity', 'price_unit', 'settlement_type')
    def _compute_price_subtotal(self):
        for line in self:
            if line.settlement_type == 'gold_credit':
                line.price_subtotal = 0.0
            elif line.line_type == 'service':
                line.price_subtotal = (line.quantity or 0.0) * (line.price_unit or 0.0)
            elif line.metal_type_id:
                line.price_subtotal = (line.quantity or 0.0) * (line.working_weight or 0.0) * (line.price_unit or 0.0)
            else:
                line.price_subtotal = (line.quantity or 0.0) * (line.price_unit or 0.0)

    def _inverse_price_subtotal(self):
        for line in self:
            pass

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('metal_type_id') and not vals.get('measured_purity') and not vals.get('working_purity'):
                metal = self.env['metal.type'].browse(vals['metal_type_id'])
                default_purity = metal.purity_percentage * 10.0
                vals['measured_purity'] = default_purity
                vals['working_purity'] = default_purity
        lines = super().create(vals_list)
        for ticket in lines.ticket_id:
            ticket._sync_to_melting()
            ticket._sync_supplier_gold()
        return lines

    def write(self, vals):
        prev_tickets = {line.id: line.ticket_id for line in self}
        prev_types = {line.id: line.line_type for line in self}
        if vals.get('metal_type_id') and 'measured_purity' not in vals and 'working_purity' not in vals:
            metal = self.env['metal.type'].browse(vals['metal_type_id'])
            default_purity = metal.purity_percentage * 10.0
            vals['measured_purity'] = default_purity
            vals['working_purity'] = default_purity
        res = super().write(vals)
        sync_fields = {'weight', 'measured_purity', 'working_purity', 'price_unit', 'quantity', 'line_type', 'settlement_type'}
        if not any(f in vals for f in sync_fields):
            return res
        tickets = set()
        gold_tickets = set()
        for line in self:
            was_achat = prev_types[line.id] == 'achat_casse'
            now_achat = line.line_type == 'achat_casse'
            was_gold = prev_types[line.id] in ('achat_casse', 'achat', 'vente')
            now_gold = line.line_type in ('achat_casse', 'achat', 'vente')
            if was_achat or now_achat:
                tickets.add(line.ticket_id.id)
            if was_gold or now_gold:
                gold_tickets.add(line.ticket_id.id)
            tickets.add(prev_tickets[line.id].id)
        for tid in tickets:
            self.env['jewelry.ticket'].browse(tid)._sync_to_melting()
        for tid in gold_tickets:
            self.env['jewelry.ticket'].browse(tid)._sync_supplier_gold()
        return res

    def unlink(self):
        tickets = set()
        gold_tickets = set()
        for line in self:
            if line.line_type == 'achat_casse' and not line.melting_id:
                tickets.add(line.ticket_id.id)
            if line.line_type in ('achat_casse', 'achat', 'vente') and line.metal_type_id:
                gold_tickets.add(line.ticket_id.id)
            tickets.add(line.ticket_id.id)
        res = super().unlink()
        for tid in tickets:
            self.env['jewelry.ticket'].browse(tid)._sync_to_melting()
        for tid in gold_tickets:
            self.env['jewelry.ticket'].browse(tid)._sync_supplier_gold()
        return res
