from odoo import models, fields, api


class SupplierGoldBalance(models.Model):
    _name = 'supplier.gold.balance'
    _description = 'Supplier Gold Balance per Working Purity'
    _auto = False
    _rec_name = 'supplier_account_id'

    supplier_account_id = fields.Many2one('supplier.account', readonly=True)
    metal_type_id = fields.Many2one('metal.type', readonly=True)
    working_purity = fields.Float(string='Working Purity (‰)', readonly=True)
    balance_weight = fields.Float(string='Balance (g)', readonly=True)

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS supplier_gold_balance CASCADE")
        self.env.cr.execute("""
            CREATE VIEW supplier_gold_balance AS (
                SELECT
                    row_number() OVER () AS id,
                    gm.supplier_account_id AS supplier_account_id,
                    gm.metal_type_id AS metal_type_id,
                    COALESCE(gm.working_purity, 0) AS working_purity,
                    SUM(CASE WHEN gm.type = 'entree' THEN gm.weight ELSE -gm.weight END) AS balance_weight
                FROM gold_movement gm
                WHERE gm.active = True
                AND gm.weight > 0
                GROUP BY gm.supplier_account_id, gm.metal_type_id, gm.working_purity
                HAVING SUM(CASE WHEN gm.type = 'entree' THEN gm.weight ELSE -gm.weight END) != 0
            )
        """)
