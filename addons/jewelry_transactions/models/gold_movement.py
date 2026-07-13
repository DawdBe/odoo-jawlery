from odoo import models, fields, _


class GoldMovement(models.Model):
    _name = 'gold.movement'
    _description = 'Gold Movement'
    _order = 'date desc, id desc'

    supplier_account_id = fields.Many2one(
        'supplier.account', string='Supplier Account',
        required=True, ondelete='cascade')
    partner_id = fields.Many2one(
        'res.partner', string='Partner',
        related='supplier_account_id.partner_id', store=True)

    purpose = fields.Selection([
        ('payment', 'Paiement'),
        ('deposit', 'Dépôt'),
        ('return', 'Rendu'),
        ('adjustment', 'Ajustement'),
    ], string='Motif', required=True)

    type = fields.Selection([
        ('entree', 'Reçu'),
        ('sortie', 'Rendu'),
    ], string='Sens', required=True)

    weight = fields.Float(string='Poids (g)', required=True)
    metal_type_id = fields.Many2one('metal.type', string='Type de Métal')
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    description = fields.Char(string='Description')

    reversed = fields.Boolean(default=False)
    reversal_id = fields.Many2one('gold.movement', string='Contre-passation', ondelete='set null')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)
    ticket_id = fields.Many2one('jewelry.ticket', string='Linked Ticket', ondelete='set null', index=True)

    def action_reverse(self):
        self.ensure_one()
        if self.reversed:
            return
        reversal = self.create({
            'supplier_account_id': self.supplier_account_id.id,
            'partner_id': self.partner_id.id,
            'purpose': self.purpose,
            'type': 'sortie' if self.type == 'entree' else 'entree',
            'weight': self.weight,
            'metal_type_id': self.metal_type_id.id if self.metal_type_id else False,
            'date': fields.Datetime.now(),
            'description': _('Contre-passation: %s') % (self.description or ''),
        })
        self.reversed = True
        self.reversal_id = reversal.id
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Gold Movement Reversed'),
                'message': _('The gold movement has been reversed.'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }
