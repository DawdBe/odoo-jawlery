from odoo import models, fields, api


class Dashboard360(models.TransientModel):
    _name = 'dashboard.360'
    _description = 'Dashboard 360°'

    total_cash = fields.Monetary(string='Total Cash', compute='_compute_values')
    safe_balance = fields.Monetary(string='Solde du Coffre', compute='_compute_values')
    register_balance = fields.Monetary(string='Solde des Caisses', compute='_compute_values')
    total_physical_cash = fields.Monetary(string='Total Physique', compute='_compute_values')
    today_sales = fields.Monetary(string="Today's Sales", compute='_compute_values')
    today_profit = fields.Monetary(string="Today's Profit", compute='_compute_values')
    today_remise = fields.Monetary(string="Today's Remise", compute='_compute_values')
    pending_payments = fields.Monetary(string='Pending Payments', compute='_compute_values')
    pending_fasonages = fields.Integer(string='Pending Fasonages', compute='_compute_values')
    total_suppliers_credit = fields.Monetary(string='Total Suppliers Credit', compute='_compute_values')
    total_suppliers_gold_weight = fields.Float(string='Créance Or Fournisseurs (g)', compute='_compute_values')
    total_gold_weight = fields.Float(string='Total Gold Stock Weight (g)', compute='_compute_values')
    poids_or_en_fonte_total = fields.Char(string='Poids Or en Fonte (total)', compute='_compute_values')
    poids_or_fabrique_by_metal_type = fields.Text(string='Poids Or Fabriqué', compute='_compute_values')
    total_shop_gold_weight = fields.Float(string='Total Or en Boutique (g)', compute='_compute_values')

    total_associate_capital = fields.Monetary(
        string='Capital Associés', compute='_compute_values',
        help="Total des comptes de capital des associés.")
    total_associate_advances = fields.Monetary(
        string='Avances Associés', compute='_compute_values',
        help="Total des avances aux associés.")
    associate_count = fields.Integer(
        string="Nombre d'Associés", compute='_compute_values',
        help="Nombre d'associés actifs.")

    last_update = fields.Datetime(string='Dashboard Last Update', compute='_compute_values')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    @api.depends('currency_id')
    def _compute_values(self):
        for record in self:
            today_dt = fields.Datetime.now().replace(hour=0, minute=0, second=0)

            today_data = self.env['jewelry.ticket'].read_group(
                [('date', '>=', today_dt)],
                ['total_cash_in:sum', 'balance:sum', 'total_remise:sum'],
                []
            )
            if today_data:
                record.today_sales = today_data[0]['total_cash_in'] or 0.0
                record.today_profit = today_data[0]['balance'] or 0.0
                record.today_remise = today_data[0]['total_remise'] or 0.0
            else:
                record.today_sales = 0.0
                record.today_profit = 0.0
                record.today_remise = 0.0

            pending_data = self.env['jewelry.ticket'].read_group(
                [('payment_status', 'in', ('impaye', 'partiel')), ('balance', '>', 0)],
                ['balance:sum'],
                []
            )
            record.pending_payments = pending_data[0]['balance'] or 0.0 if pending_data else 0.0

            fasonage_tickets = self.env['jewelry.ticket'].search([
                ('ticket_line_ids.line_type', '=', 'fasonage'),
            ])
            record.pending_fasonages = len(fasonage_tickets)

            safe = self.env['cash.safe']._get_main_safe()
            record.safe_balance = safe.current_balance or 0.0

            open_regs = self.env['daily.cash.register'].search([
                ('state', '=', 'open'),
            ])
            record.register_balance = sum(open_regs.mapped('expected_balance')) or 0.0

            record.total_physical_cash = record.safe_balance + record.register_balance

            record.total_cash = record.safe_balance

            accounts = self.env['supplier.account'].search([])
            record.total_suppliers_credit = sum(accounts.mapped('balance')) or 0.0

            record.total_suppliers_gold_weight = sum(accounts.mapped('weight_balance')) or 0.0

            quants = self.env['stock.quant'].search([('weight_total', '>', 0)])
            record.total_gold_weight = sum(quants.mapped('weight_total')) or 0.0

            metal_names = {m.id: m.name for m in self.env['metal.type'].search([])}

            draft = self.env['casse.melting']._get_current_draft()
            if draft:
                record.poids_or_en_fonte_total = f"{draft.weight_before:.2f}g"
            else:
                record.poids_or_en_fonte_total = 'No open casse/fonte'

            fabrique_data = self.env['stock.quant'].read_group(
                [('metal_type_id', '!=', False),
                 ('product_id.product_tmpl_id.jewelry_category', '=', 'fini'),
                 ('weight_total', '>', 0)],
                ['weight_total:sum', 'metal_type_id'],
                ['metal_type_id']
            )
            fabrique_lines = []
            for g in fabrique_data:
                mt_id = g['metal_type_id']
                if mt_id and g.get('weight_total'):
                    name = metal_names.get(mt_id[0], 'Unknown')
                    fabrique_lines.append(f"{name}: {g['weight_total']:.2f}g")
            record.poids_or_fabrique_by_metal_type = '\n'.join(fabrique_lines) if fabrique_lines else 'No finished gold in stock'

            fonte_weight = draft.weight_before if draft else 0.0
            record.total_shop_gold_weight = (record.total_gold_weight + fonte_weight) or 0.0

            assoc_data = self.env['associate.account'].read_group(
                [],
                ['capital_balance:sum', 'advance_balance:sum'],
                []
            )
            if assoc_data:
                record.total_associate_capital = assoc_data[0]['capital_balance'] or 0.0
                record.total_associate_advances = assoc_data[0]['advance_balance'] or 0.0
            else:
                record.total_associate_capital = 0.0
                record.total_associate_advances = 0.0
            record.associate_count = self.env['associate.account'].search_count([])

            record.last_update = fields.Datetime.now()
