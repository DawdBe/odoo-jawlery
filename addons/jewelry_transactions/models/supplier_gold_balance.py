from odoo import models, fields


class SupplierGoldBalance(models.Model):
    _name = 'supplier.gold.balance'
    _description = 'Supplier Gold Balance (presentation view)'
    _auto = False
    _rec_name = 'supplier_account_id'

    supplier_account_id = fields.Many2one('supplier.account', readonly=True)
    working_purity = fields.Float(string='Working Purity (‰)', readonly=True)
    gold_creance = fields.Float(string='Créance Or (g)', readonly=True)
    gold_dette = fields.Float(string='Dette Or (g)', readonly=True)
    gold_solde = fields.Float(string='Solde Or (g)', readonly=True)

    def init(self):
        self.env.cr.execute("DROP VIEW IF EXISTS supplier_gold_balance CASCADE")
        self.env.cr.execute("""
            CREATE VIEW supplier_gold_balance AS (
                SELECT
                    row_number() OVER () AS id,
                    gm.supplier_account_id AS supplier_account_id,
                    sa.working_purity AS working_purity,
                    COALESCE(SUM(
                        CASE WHEN gm.type = 'entree'
                        THEN gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                        ELSE 0 END
                    ), 0) AS gold_creance,
                    COALESCE(SUM(
                        CASE WHEN gm.type = 'sortie'
                        THEN gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                        ELSE 0 END
                    ), 0) AS gold_dette,
                    COALESCE(SUM(
                        CASE WHEN gm.type = 'entree'
                        THEN gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                        ELSE -gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                        END
                    ), 0) AS gold_solde
                FROM gold_movement gm
                JOIN supplier_account sa ON sa.id = gm.supplier_account_id
                WHERE gm.active = True
                AND gm.weight > 0
                GROUP BY gm.supplier_account_id, sa.working_purity
                HAVING COALESCE(SUM(
                    CASE WHEN gm.type = 'entree'
                    THEN gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                    ELSE -gm.weight * COALESCE(gm.purity, 0) / NULLIF(sa.working_purity, 1)
                    END
                ), 0) != 0
            )
        """)
