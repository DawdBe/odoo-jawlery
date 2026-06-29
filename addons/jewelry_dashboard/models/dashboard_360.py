from odoo import models, fields, api


class Dashboard360(models.TransientModel):
    _name = 'dashboard.360'
    _description = 'Dashboard 360°'

    total_cash = fields.Monetary(string='Total Cash', compute='_compute_values')
    weight_by_metal_type = fields.Text(string='Weight by Metal Type', compute='_compute_values')
    today_sales = fields.Monetary(string="Today's Sales", compute='_compute_values')
    today_profit = fields.Monetary(string="Today's Profit", compute='_compute_values')
    today_remise = fields.Monetary(string="Today's Remise", compute='_compute_values')
    pending_payments = fields.Monetary(string='Pending Payments', compute='_compute_values')
    pending_fasonages = fields.Integer(string='Pending Fasonages', compute='_compute_values')
    base_24k_dzd = fields.Monetary(string='24k Base (DZD/g)', compute='_compute_values')
    gold_rate_market = fields.Monetary(string='Gold Rate (Market)', compute='_compute_values')
    silver_rate = fields.Monetary(string='Silver Rate', compute='_compute_values')
    dzd_parallel_rate = fields.Float(string='DZD Parallel Rate', compute='_compute_values')
    last_update = fields.Datetime(string='Last Update', compute='_compute_values')
    currency_id = fields.Many2one('res.currency', default=lambda self: self.env.company.currency_id)

    def _compute_values(self):
        for record in self:
            today = fields.Date.today()

            gold_rate_rec = self.env['gold.rate.history'].search([
                ('metal_type_id.category', 'in', ('or', 'casse')),
                ('is_active', '=', True),
            ], order='effective_date desc, id desc', limit=1)
            record.base_24k_dzd = gold_rate_rec.base_24k_dzd if gold_rate_rec else 0.0
            record.gold_rate_market = gold_rate_rec.market_rate if gold_rate_rec else 0.0

            silver_metal = self.env['metal.type'].search([('category', '=', 'argent')], limit=1)
            if silver_metal:
                silver_rate_rec = self.env['gold.rate.history'].search([
                    ('metal_type_id', '=', silver_metal.id),
                    ('is_active', '=', True),
                ], order='effective_date desc, id desc', limit=1)
                record.silver_rate = silver_rate_rec.market_rate if silver_rate_rec else 0.0

            today_start = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            today_tickets = self.env['jewelry.ticket'].search([
                ('date', '>=', today_start),
            ])
            record.today_sales = sum(t.total_cash_in for t in today_tickets)
            record.today_remise = sum(t.total_remise for t in today_tickets)
            record.today_profit = sum(t.balance for t in today_tickets)

            latest_gold = self.env['gold.rate.history'].search([
                ('metal_type_id.category', 'in', ('or', 'casse')),
                ('is_active', '=', True),
            ], order='effective_date desc, id desc', limit=1)
            record.dzd_parallel_rate = latest_gold.dzd_parallel_rate if latest_gold else 0.0

            pending = self.env['jewelry.ticket'].search([('payment_status', 'in', ('impaye', 'partiel'))])
            record.pending_payments = sum(max(t.balance, 0) for t in pending)

            record.pending_fasonages = self.env['service.order'].search_count([
                ('status', 'not in', ('delivered',)),
            ])

            record.total_cash = sum(
                r.expected_balance for r in self.env['daily.cash.register'].search([
                    ('state', '=', 'open'),
                ])
            )

            metal_types = self.env['metal.type'].search([])
            lines = []
            for mt in metal_types:
                total_weight = sum(
                    l.weight or 0.0
                    for l in self.env['jewelry.ticket.line'].search([
                        ('metal_type_id', '=', mt.id),
                    ])
                )
                if total_weight:
                    lines.append(f"{mt.name}: {total_weight:.2f}g")
            record.weight_by_metal_type = '\n'.join(lines) if lines else 'No weight data'

            record.last_update = fields.Datetime.now()
