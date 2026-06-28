from odoo import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    client_code = fields.Char(string='Client Code')
    partner_type = fields.Selection([
        ('client', 'Client'),
        ('frs', 'Fournisseur (FRS)'),
        ('atelier', 'Atelier (AT)'),
        ('associe', 'Associé'),
    ], string='Partner Type')
    is_supplier = fields.Boolean(string='Is Supplier')
    is_atelier = fields.Boolean(string='Is Atelier')
    is_associated = fields.Boolean(string='Is Associated')
