from odoo import api, models, fields, _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ticket_ids = fields.One2many('jewelry.ticket', 'partner_id', string='Tickets')

    @api.model
    def create(self, vals):
        partner = super().create(vals)
        if vals.get('partner_type') in ('frs', 'atelier'):
            partner._ensure_supplier_account()
        if vals.get('partner_type') == 'associe':
            partner._ensure_associate_account()
        return partner

    def write(self, vals):
        result = super().write(vals)
        if vals.get('partner_type') in ('frs', 'atelier'):
            for partner in self:
                partner._ensure_supplier_account()
        if vals.get('partner_type') == 'associe':
            for partner in self:
                partner._ensure_associate_account()
        return result

    def _ensure_supplier_account(self):
        self.ensure_one()
        existing = self.env['supplier.account'].search(
            [('partner_id', '=', self.id)], limit=1)
        if not existing:
            partner_type_map = {'frs': 'fournisseur', 'atelier': 'atelier'}
            self.env['supplier.account'].create({
                'partner_id': self.id,
                'partner_type': partner_type_map.get(self.partner_type),
            })

    def _ensure_associate_account(self):
        self.ensure_one()
        existing = self.env['associate.account'].search(
            [('partner_id', '=', self.id)], limit=1)
        if not existing:
            self.env['associate.account'].create({
                'partner_id': self.id,
            })

    def action_open_supplier_account(self):
        self.ensure_one()
        account = self.env['supplier.account'].search(
            [('partner_id', '=', self.id)], limit=1)
        if not account:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'supplier.account',
            'view_mode': 'form',
            'res_id': account.id,
            'target': 'current',
            'name': _('Supplier Account'),
        }

    def action_open_associate_account(self):
        self.ensure_one()
        account = self.env['associate.account'].search(
            [('partner_id', '=', self.id)], limit=1)
        if not account:
            return
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'associate.account',
            'view_mode': 'form',
            'res_id': account.id,
            'target': 'current',
            'name': _('Associate Account'),
        }
