from odoo import models, fields


class CasseMeltingLine(models.Model):
    _name = 'casse.melting.line'
    _description = 'Casse Melting Line'

    melting_id = fields.Many2one('casse.melting', string='Melting', required=True, ondelete='cascade')
    ticket_line_id = fields.Many2one('jewelry.ticket.line', string='Source Ticket Line')
    weight = fields.Float(string='Weight (g)')
    cost = fields.Monetary(string='Cost')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
