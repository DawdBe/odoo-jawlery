# Odoo ORM Database Patterns

## Common Field Types
```python
from odoo import models, fields, api

class CustomModel(models.Model):
    _name = 'custom.model'
    _description = 'Custom Model'
    _rec_name = 'name'
    _order = 'sequence, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # For chatter

    name = fields.Char(string='Name', required=True, index=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    sequence = fields.Integer(string='Sequence', default=10)
    company_id = fields.Many2one('res.company', string='Company', 
        default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible',
        default=lambda self: self.env.user)
    partner_id = fields.Many2one('res.partner', string='Partner')
    category_id = fields.Many2one('custom.category', string='Category')
    tag_ids = fields.Many2many('custom.tag', string='Tags')
    line_ids = fields.One2many('custom.line', 'parent_id', string='Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='State', default='draft', tracking=True)
    date = fields.Date(string='Date', default=fields.Date.today)
    datetime = fields.Datetime(string='Date Time')
    monetary = fields.Monetary(string='Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency')
    float_value = fields.Float(string='Value', digits=(10, 2))
    integer_value = fields.Integer(string='Count')
    boolean_field = fields.Boolean(string='Is Active')
    binary_field = fields.Binary(string='Attachment')
    html_field = fields.Html(string='Rich Text')
```

## Constraints
```python
# Python constraints
@api.constrains('field_a', 'field_b')
def _check_consistency(self):
    for record in self:
        if record.field_a > record.field_b:
            raise ValidationError("field_a must be <= field_b")

# SQL constraints (in __manifest__.py or model)
_sql_constraints = [
    ('name_company_uniq', 'unique(name, company_id)',
     'Name must be unique per company!'),
]
```

## Computed Fields
```python
total_amount = fields.Monetary(
    string='Total', compute='_compute_total', store=True)

@api.depends('line_ids', 'line_ids.subtotal')
def _compute_total(self):
    for record in self:
        record.total_amount = sum(line.subtotal for line in record.line_ids)
```

## Related Fields (no compute needed)
```python
partner_email = fields.Char(related='partner_id.email', string='Email', store=False)
```
