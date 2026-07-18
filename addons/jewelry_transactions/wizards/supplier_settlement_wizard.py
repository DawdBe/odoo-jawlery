from odoo import models, fields, api, _
from odoo.exceptions import UserError


class SupplierSettlementWizard(models.TransientModel):
    _name = 'supplier.settlement.wizard'
    _description = 'Supplier Settlement Wizard'

    supplier_account_id = fields.Many2one(
        'supplier.account', string='Supplier Account', required=True)
    partner_id = fields.Many2one(
        'res.partner', string='Partner',
        related='supplier_account_id.partner_id', readonly=True)

    cash_amount = fields.Monetary(string='Cash Amount', default=0.0)
    gold_weight = fields.Float(string='Gold Weight (g)', default=0.0)
    gold_purity = fields.Float(
        string='Pureté (‰)', default=750.0,
        help='Titre de l\'or au moment du règlement.')
    gold_metal_type_id = fields.Many2one('metal.type', string='Metal Type')
    description = fields.Char(string='Description')
    payment_method = fields.Selection([
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('transfer', 'Bank Transfer'),
        ('check', 'Check'),
        ('other', 'Other'),
    ], string='Payment Method', default='cash')

    currency_id = fields.Many2one(
        'res.currency', related='supplier_account_id.currency_id', readonly=True)

    current_cash_creance = fields.Monetary(
        string='Créance', compute='_compute_current', readonly=True)
    current_cash_dette = fields.Monetary(
        string='Dette', compute='_compute_current', readonly=True)
    current_cash_solde = fields.Monetary(
        string='Solde Espèces', compute='_compute_current', readonly=True)
    current_gold_creance = fields.Float(
        string='Or Créance (g)', compute='_compute_current', readonly=True)
    current_gold_dette = fields.Float(
        string='Or Dette (g)', compute='_compute_current', readonly=True)
    current_gold_solde = fields.Float(
        string='Solde Or (g)', compute='_compute_current', readonly=True)

    cash_direction = fields.Selection([
        ('entree', 'Reçu — on reçoit'),
        ('sortie', 'Rendu — on donne'),
    ], string='Sens espèces')

    gold_direction = fields.Selection([
        ('entree', 'Reçu — on reçoit'),
        ('sortie', 'Rendu — on donne'),
    ], string='Sens or')

    projected_cash_solde = fields.Monetary(
        string='Solde Espèces Après',
        compute='_compute_projected', readonly=True)
    projected_gold_solde = fields.Float(
        string='Solde Or Après (g)',
        compute='_compute_projected', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('done', 'Done'),
    ], default='draft', readonly=True)

    @api.depends('supplier_account_id')
    def _compute_current(self):
        for wiz in self:
            if wiz.supplier_account_id:
                a = wiz.supplier_account_id
                wiz.current_cash_creance = a.cash_creance or 0.0
                wiz.current_cash_dette = a.cash_dette or 0.0
                wiz.current_cash_solde = a.cash_solde or 0.0
                wiz.current_gold_creance = a.gold_creance or 0.0
                wiz.current_gold_dette = a.gold_dette or 0.0
                wiz.current_gold_solde = a.gold_solde or 0.0
            else:
                wiz.current_cash_creance = 0.0
                wiz.current_cash_dette = 0.0
                wiz.current_cash_solde = 0.0
                wiz.current_gold_creance = 0.0
                wiz.current_gold_dette = 0.0
                wiz.current_gold_solde = 0.0

    @api.onchange('supplier_account_id', 'current_cash_solde')
    def _onchange_set_cash_direction(self):
        if self.supplier_account_id and not self.cash_direction:
            self.cash_direction = 'entree' if self.current_cash_solde > 0 else 'sortie'

    @api.onchange('supplier_account_id', 'current_gold_solde')
    def _onchange_set_gold_direction(self):
        if self.supplier_account_id and not self.gold_direction:
            self.gold_direction = 'entree' if self.current_gold_solde > 0 else 'sortie'

    @api.depends('cash_amount', 'gold_weight', 'cash_direction', 'gold_direction',
                 'current_cash_solde', 'current_gold_solde')
    def _compute_projected(self):
        for wiz in self:
            wiz.projected_cash_solde = wiz.current_cash_solde
            wiz.projected_gold_solde = wiz.current_gold_solde
            if wiz.cash_amount and wiz.cash_direction:
                if wiz.cash_direction == 'entree':
                    wiz.projected_cash_solde -= wiz.cash_amount
                else:
                    wiz.projected_cash_solde += wiz.cash_amount
            if wiz.gold_weight and wiz.gold_direction:
                if wiz.gold_direction == 'entree':
                    wiz.projected_gold_solde -= wiz.gold_weight
                else:
                    wiz.projected_gold_solde += wiz.gold_weight

    def action_confirm(self):
        self.ensure_one()
        if self.state == 'done':
            return True
        account = self.supplier_account_id
        cash_creance = account.cash_creance or 0.0
        cash_dette = account.cash_dette or 0.0
        gold_creance = account.gold_creance or 0.0
        gold_dette = account.gold_dette or 0.0

        if not self.cash_amount and not self.gold_weight:
            raise UserError(_(
                "Veuillez saisir un montant à régler (espèces et/ou or)."))

        if self.cash_amount:
            if not self.cash_direction:
                raise UserError(_("Veuillez sélectionner le sens du règlement espèces."))
            if self.cash_direction == 'entree':
                if self.cash_amount > cash_creance:
                    raise UserError(_(
                        "Le règlement espèces reçu (%.2f) dépasse la créance (%.2f). "
                        "Le fournisseur ne doit que %.2f.")
                        % (self.cash_amount, cash_creance, cash_creance))
                if cash_creance == 0:
                    raise UserError(_(
                        "La créance est nulle. Vous ne pouvez pas recevoir de règlement espèces."))
            else:
                if self.cash_amount > cash_dette:
                    raise UserError(_(
                        "Le règlement espèces donné (%.2f) dépasse la dette (%.2f). "
                        "Vous ne devez que %.2f.")
                        % (self.cash_amount, cash_dette, cash_dette))
                if cash_dette == 0:
                    raise UserError(_(
                        "La dette est nulle. Vous ne pouvez pas donner de règlement espèces."))
            self.env['cash.register.line'].create({
                'supplier_account_id': account.id,
                'partner_id': account.partner_id.id,
                'amount': self.cash_amount,
                'type': self.cash_direction,
                'payment_method': self.payment_method,
                'origin': 'settlement',
                'date': fields.Datetime.now(),
                'user_id': self.env.user.id,
                'description': self.description or _(
                    'Règlement fournisseur %s') % account.partner_id.name,
            })

        if self.gold_weight:
            if not self.gold_direction:
                raise UserError(_("Veuillez sélectionner le sens du règlement or."))
            if self.gold_direction == 'entree':
                if self.gold_weight > gold_creance:
                    raise UserError(_(
                        "Le règlement or reçu (%.2fg) dépasse la créance or (%.2fg).")
                        % (self.gold_weight, gold_creance))
                if gold_creance == 0:
                    raise UserError(_(
                        "La créance or est nulle. Vous ne pouvez pas recevoir d'or."))
            else:
                if self.gold_weight > gold_dette:
                    raise UserError(_(
                        "Le règlement or donné (%.2fg) dépasse la dette or (%.2fg).")
                        % (self.gold_weight, gold_dette))
                if gold_dette == 0:
                    raise UserError(_(
                        "La dette or est nulle. Vous ne pouvez pas donner d'or."))
            self.env['gold.movement'].create({
                'supplier_account_id': account.id,
                'purpose': 'settlement',
                'type': self.gold_direction,
                'weight': self.gold_weight,
                'purity': self.gold_purity,
                'metal_type_id': self.gold_metal_type_id.id,
                'date': fields.Datetime.now(),
                'description': self.description or _(
                    'Règlement fournisseur %s') % account.partner_id.name,
            })

        self.state = 'done'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Règlement effectué'),
                'message': _('Le règlement a été enregistré avec succès.'),
                'sticky': False,
                'type': 'success',
                'next': {'type': 'ir.actions.client', 'tag': 'reload'},
            },
        }
