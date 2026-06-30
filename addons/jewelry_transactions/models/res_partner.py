from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ticket_ids = fields.One2many('jewelry.ticket', 'partner_id', string='Tickets')
