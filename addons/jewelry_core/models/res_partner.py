from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('client', 'Client'),
        ('frs', 'Fournisseur (FRS)'),
        ('atelier', 'Atelier (AT)'),
        ('associe', 'Associé'),
    ], string='Partner Type')
