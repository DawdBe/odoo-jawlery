from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    weight = fields.Float(
        string='Poids de travail (g)', required=True,
        help='Poids utilisé pour les calculs ERP (soldes fournisseur, reports).')
    measured_weight = fields.Float(
        string='Poids mesuré (g)',
        help='Poids physique réel mesuré. Donnée historique conservée à titre d\'audit.')
    measured_purity = fields.Float(
        string='Pureté mesurée (‰)',
        help='Titre réel mesuré (ex: 875, 750). Donnée physique conservée pour l\'audit.')
    working_purity = fields.Float(
        string='Pureté de travail (‰)',
        help='Titre utilisé par l\'ERP pour les calculs de solde et de valorisation.')
    metal_type_id = fields.Many2one('metal.type', string='Type de Métal')
    date = fields.Datetime(default=fields.Datetime.now, required=True)
    description = fields.Char(string='Description')

    active = fields.Boolean(default=True)
    inactive_reason = fields.Selection([
        ('ticket_update', 'Mise à jour du ticket'),
        ('ticket_deleted', 'Suppression du ticket'),
        ('conversion', 'Conversion Or → Espèces'),
        ('manual', 'Ajustement manuel'),
    ], string='Motif d\'archivage', readonly=True)
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    origin_model = fields.Char(string='Document d\'origine')
    origin_id = fields.Integer(string='ID du document d\'origine')
    ticket_id = fields.Many2one('jewelry.ticket', string='Ticket lié', ondelete='set null', index=True)

    def write(self, vals):
        protected = {'purpose', 'type', 'weight', 'measured_weight', 'measured_purity', 'working_purity',
                     'metal_type_id', 'date', 'description', 'supplier_account_id', 'partner_id', 'ticket_id'}
        changes = protected & set(vals)
        if changes:
            raise UserError(_(
                'Les champs suivants ne peuvent pas être modifiés après création : %s\n'
                'Cette écriture fait partie d\'un grand livre immutable. '
                'Archivez-la (active=False) si elle est erronée.'
            ) % ', '.join(changes))
        return super().write(vals)
