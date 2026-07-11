from odoo import models, fields, api


class Dashboard360(models.TransientModel):
    _name = 'dashboard.360'
    _description = 'Dashboard 360°'
    # Transient (non-persisted) model that aggregates KPIs from all modules
    # in real-time. All fields are computed, none are stored.
    # Provides a single-page overview: cash positions, today's sales/profit,
    # pending payments, pending fasonages, and weight breakdown by metal type.

    total_cash = fields.Monetary(string='Total Cash', compute='_compute_values')
    weight_by_metal_type = fields.Text(string='Weight by Metal Type', compute='_compute_values')
    today_sales = fields.Monetary(string="Today's Sales", compute='_compute_values')
    today_profit = fields.Monetary(string="Today's Profit", compute='_compute_values')
    today_remise = fields.Monetary(string="Today's Remise", compute='_compute_values')
    pending_payments = fields.Monetary(string='Pending Payments', compute='_compute_values')
    pending_fasonages = fields.Integer(string='Pending Fasonages', compute='_compute_values')
    last_update = fields.Datetime(string='Dashboard Last Update', compute='_compute_values')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def _compute_values(self):
        for record in self:
            today_dt = fields.Datetime.now().replace(hour=0, minute=0, second=0)

            # -----------------------------------------------------------
            # 2. Today's KPIs — read_group aggregation, no Python loops
            # Junior Developer Note: read_group() performs SQL-level GROUP BY
            # aggregation directly in PostgreSQL. This is MUCH faster than
            # fetching every ticket and summing in Python, especially with
            # thousands of records.
            # -----------------------------------------------------------
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

            # -----------------------------------------------------------
            # 3. Pending payments
            # -----------------------------------------------------------
            pending_data = self.env['jewelry.ticket'].read_group(
                [('payment_status', 'in', ('impaye', 'partiel')), ('balance', '>', 0)],
                ['balance:sum'],
                []
            )
            record.pending_payments = pending_data[0]['balance'] or 0.0 if pending_data else 0.0

            # -----------------------------------------------------------
            # 4. Pending fasonages
            # -----------------------------------------------------------
            record.pending_fasonages = self.env['service.order'].search_count([
                ('status', 'not in', ('delivered',)),
            ])

            # -----------------------------------------------------------
            # 5. Total Caisse — single source of truth: open registers
            #    Orphan cash lines cannot exist: every cash.register.line
            #    auto-assigns to its date's register on creation.
            # -----------------------------------------------------------
            open_regs = self.env['daily.cash.register'].search([('state', '=', 'open')])
            record.total_cash = sum(open_regs.mapped('expected_balance')) or 0.0

            # -----------------------------------------------------------
            # 6. Weight by Metal Type — single read_group, no N+1
            # Junior Developer Note: read_group groups all ticket lines by
            # metal_type_id and sums their weights in ONE SQL query.
            # Without it, we'd need N queries for N metal types (N+1 problem).
            # -----------------------------------------------------------
            weight_data = self.env['jewelry.ticket.line'].read_group(
                [],
                ['weight:sum', 'metal_type_id'],
                ['metal_type_id']
            )
            metal_names = {m.id: m.name for m in self.env['metal.type'].search([])}
            lines = []
            for g in weight_data:
                mt_id = g['metal_type_id']
                if mt_id and g.get('weight'):
                    name = metal_names.get(mt_id[0], 'Unknown')
                    lines.append(f"{name}: {g['weight']:.2f}g")
            record.weight_by_metal_type = '\n'.join(lines) if lines else 'No weight data'

            record.last_update = fields.Datetime.now()
