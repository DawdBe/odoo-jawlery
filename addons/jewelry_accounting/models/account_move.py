from odoo import models, fields


class AccountMove(models.Model):
    _inherit = 'account.move'
    # Extends Odoo accounting entries with jewelry-specific operation types
    # and weight tracking. This allows the system to tag journal entries
    # by business operation (sale, purchase, fasonage, etc.) and track
    # gold weight movements through the accounting system.

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
    # Each journal entry line can track weight and metal type,
    # enabling reports that show gold quantity alongside monetary values.

    weight = fields.Float(string='Weight (g)')
    metal_type_id = fields.Many2one('metal.type', string='Metal Type')
