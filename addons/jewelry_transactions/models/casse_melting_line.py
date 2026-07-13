from odoo import models, fields
from odoo.exceptions import UserError


class CasseMeltingLine(models.Model):
    _name = 'casse.melting.line'
    _description = 'Casse Melting Line'

    melting_id = fields.Many2one('casse.melting', string='Melting', required=True, ondelete='cascade')
    ticket_id = fields.Many2one('jewelry.ticket', string='Ticket', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Customer',
        related='ticket_id.partner_id', store=True, readonly=True)
    weight = fields.Float(string='Weight (g)')
    cost = fields.Monetary(string='Cost')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

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
