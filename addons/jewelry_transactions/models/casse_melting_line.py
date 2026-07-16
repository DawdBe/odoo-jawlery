from odoo import models, fields, api
from odoo.exceptions import UserError


class CasseMeltingLine(models.Model):
    _name = 'casse.melting.line'
    _description = 'Casse Melting Line'

    melting_id = fields.Many2one('casse.melting', string='Melting', required=True, ondelete='cascade')
    ticket_id = fields.Many2one('jewelry.ticket', string='Ticket', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        related='ticket_id.partner_id', store=True, readonly=True)
    weight = fields.Float(string='Poids mesuré (g)', help='Poids physique mesuré de la ligne de ticket.')
    measured_purity = fields.Float(
        string='Pureté mesurée (‰)',
        help='Titre réel mesuré provenant de la ligne de ticket.')
    working_purity = fields.Float(
        string='Pureté de travail (‰)',
        help='Titre de travail choisi sur la ligne de ticket d\'origine.')
    working_weight = fields.Float(
        string='Poids de travail (g)', compute='_compute_working_weight', store=True,
        help='Poids normalisé = poids mesuré × pureté mesurée / pureté de travail.')
    cost = fields.Monetary(string='Cost')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('weight', 'measured_purity', 'working_purity')
    def _compute_working_weight(self):
        for line in self:
            if line.weight and line.measured_purity and line.working_purity and line.measured_purity != line.working_purity:
                line.working_weight = (line.weight or 0.0) * (line.measured_purity or 0.0) / (line.working_purity or 1.0)
            else:
                line.working_weight = line.weight or 0.0

    def unlink(self):
        for line in self:
            if line.melting_id.state == 'done':
                raise UserError(
                    'Cannot remove a line from a confirmed melting batch.')
        return super().unlink()

    def write(self, vals):
        for line in self:
            if line.melting_id.state == 'done':
                raise UserError(
                    'Cannot modify a line in a confirmed melting batch.')
        return super().write(vals)

    def action_open_ticket(self):
        self.ensure_one()
        if not self.ticket_id:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'jewelry.ticket',
            'res_id': self.ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
