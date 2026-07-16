from odoo import api, fields, models, _
from odoo.exceptions import UserError


class CasseMelting(models.Model):
    _name = 'casse.melting'
    _description = 'Casse Melting'
    _order = 'date desc'

    name = fields.Char(required=True, default='New')
    date = fields.Date(default=fields.Date.today, required=True)

    @api.model
    def create(self, vals):
        if self.search_count([('state', '=', 'draft')]):
            raise UserError(_(
                'Cannot create a new melting batch while another is still open. '
                'Confirm or cancel the current draft first.'))
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('casse.melting') or 'New'
        return super().create(vals)

    metal_type_result = fields.Many2one('metal.type', string='Result Metal Type')
    working_purity = fields.Float(string='Pureté de travail (‰)', default=750.0)
    weight_before = fields.Float(
        string='Weight Before (g)',
        compute='_compute_lines_totals', store=True)
    weight_before_working = fields.Float(
        string='Working Weight Before (g)',
        compute='_compute_lines_totals', store=True)
    weight_after = fields.Float(string='Weight After (g)')
    wastage_weight = fields.Float(string='Wastage (g)', compute='_compute_values', store=True)
    total_cost = fields.Monetary(
        string='Total Cost',
        compute='_compute_lines_totals', store=True)
    refined_value = fields.Monetary(string='Refined Value', compute='_compute_values', store=True)
    profit = fields.Monetary(string='Profit', compute='_compute_values', store=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', required=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    notes = fields.Text()

    line_ids = fields.One2many('casse.melting.line', 'melting_id', string='Lines')

    @api.depends('line_ids.weight', 'line_ids.working_weight', 'line_ids.cost')
    def _compute_lines_totals(self):
        for record in self:
            record.weight_before = sum(record.line_ids.mapped('weight') or [0.0])
            record.weight_before_working = sum(record.line_ids.mapped('working_weight') or [0.0])
            record.total_cost = sum(record.line_ids.mapped('cost') or [0.0])

    @api.depends('weight_before', 'weight_after', 'total_cost', 'metal_type_result',
                 'line_ids.weight', 'line_ids.cost')
    def _compute_values(self):
        for record in self:
            record.wastage_weight = (record.weight_before or 0.0) - (record.weight_after or 0.0)
            if record.metal_type_result and record.weight_after:
                rate = record.metal_type_result.get_current_rate('market')
                record.refined_value = record.weight_after * rate
            else:
                record.refined_value = 0.0
            record.profit = record.refined_value - (record.total_cost or 0.0)

    @api.model
    def _get_current_draft(self):
        return self.search([('state', '=', 'draft')], order='id desc', limit=1)

    def _add_ticket(self, ticket):
        self.ensure_one()
        if self.state != 'draft':
            return
        achat_lines = ticket.ticket_line_ids.filtered(
            lambda l: l.line_type == 'achat_casse')
        weight = sum(achat_lines.mapped('weight') or [0.0])
        cost = sum(achat_lines.mapped('price_subtotal') or [0.0])
        # Average measured purity weighted by weight from ticket lines
        total_weight = sum(l.weight or 0.0 for l in achat_lines)
        if total_weight:
            avg_measured_purity = sum((l.weight or 0.0) * (l.measured_purity or 0.0) for l in achat_lines) / total_weight
            avg_working_purity = sum((l.weight or 0.0) * (l.working_purity or 0.0) for l in achat_lines) / total_weight
        else:
            avg_measured_purity = 750.0
            avg_working_purity = 750.0
        existing = self.line_ids.filtered(lambda l: l.ticket_id == ticket)
        if weight:
            vals = {
                'weight': weight,
                'measured_purity': avg_measured_purity,
                'working_purity': avg_working_purity,
                'cost': cost,
            }
            if existing:
                existing.write(vals)
            else:
                vals['ticket_id'] = ticket.id
                self.write({'line_ids': [(0, 0, vals)]})
        elif existing:
            existing.unlink()

    def _remove_ticket(self, ticket):
        self.ensure_one()
        if self.state != 'draft':
            return
        existing = self.line_ids.filtered(lambda l: l.ticket_id == ticket)
        if existing:
            existing.unlink()

    def action_confirm(self):
        for record in self:
            if record.state != 'draft':
                raise UserError(_('This melting is already confirmed.'))
            if not record.line_ids:
                raise UserError(_(
                    'No Achat Casse ticket lines are available for melting. '
                    'Create some Achat Casse purchases first.'))
            if not record.weight_after:
                raise UserError(_('Please enter the weight after melting.'))
            record.state = 'done'
            for m_line in record.line_ids:
                if m_line.ticket_id:
                    achat_lines = m_line.ticket_id.ticket_line_ids.filtered(
                        lambda l: l.line_type == 'achat_casse')
                    achat_lines.write({'melting_id': record.id})
                    m_line.ticket_id.write({'melting_id': record.id})
        return True

    def write(self, vals):
        for record in self:
            if record.state == 'done':
                protected = {'line_ids', 'weight_before', 'total_cost',
                             'weight_after', 'metal_type_result'}
                if any(f in vals for f in protected):
                    raise UserError(_(
                        'Cannot modify a confirmed melting batch. '
                        'The batch is immutable after confirmation.'))
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state == 'done':
                raise UserError(_(
                    'Cannot delete a confirmed melting batch. '
                    'This batch is part of the permanent audit trail.'))
        return super().unlink()
