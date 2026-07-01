from odoo import models


class IrActionsActions(models.Model):
    _inherit = 'ir.actions.actions'

    def _get_bindings(self, model_name):
        result = dict(super()._get_bindings(model_name))
        if model_name in ('product.template', 'product.product'):
            result['report'] = []
        return result


class IrActionsReport(models.Model):
    _inherit = 'ir.actions.report'

    def _restore_binding_type(self):
        self.env.cr.execute(
            "UPDATE ir_act_report_xml SET binding_type = 'report' "
            "WHERE binding_type = '_'"
        )
