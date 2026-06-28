from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'

    jewelry_operation_type = fields.Selection([
        ('vente', 'Vente'),
        ('achat', 'Achat'),
        ('fasonage', 'Fasonage'),
        ('service', 'Service'),
        ('frais', 'Frais'),
        ('associe', 'Associé'),
        ('personnel', 'Personnel'),
        ('invest', 'Investissement'),
        ('transfert', 'Transfert'),
        ('verse', 'Versé'),
        ('solde', 'Solde'),
        ('remise', 'Remise'),
    ], string='Operation Type')
    weight_total = fields.Float(string='Total Weight (g)')


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    weight = fields.Float(string='Weight (g)')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
