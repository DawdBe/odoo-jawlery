from odoo import api, models, fields


class CashMovementCategory(models.Model):
    _name = 'cash.movement.category'
    _description = 'Cash Movement Category'
    _order = 'sequence, name'
    _parent_store = True
    _rec_name = 'display_name'

    name = fields.Char(required=True, translate=True)
    display_name = fields.Char(compute='_compute_display_name', store=True)
    code = fields.Char(required=True)
    direction = fields.Selection([
        ('entree', 'Entrée — money comes in'),
        ('sortie', 'Sortie — money goes out'),
    ], string='Default Direction', required=True)
    parent_id = fields.Many2one(
        'cash.movement.category', string='Parent Category',
        ondelete='restrict', index=True)
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'cash.movement.category', 'parent_id', string='Subcategories')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Category code must be unique.'),
    ]

    @api.depends('name', 'parent_id')
    def _compute_display_name(self):
        for cat in self:
            if cat.parent_id:
                cat.display_name = f"{cat.parent_id.name} / {cat.name}"
            else:
                cat.display_name = cat.name
