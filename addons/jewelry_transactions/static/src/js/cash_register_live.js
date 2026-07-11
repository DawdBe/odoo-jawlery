/** @odoo-module **/
import { FormController } from "@web/views/form/form_controller";
import { formView } from "@web/views/form/form_view";
import { registry } from "@web/core/registry";
import { onMounted, onWillDestroy } from "@odoo/owl";

class CashRegisterFormController extends FormController {
    setup() {
        super.setup();
        if (this.props.resModel !== "daily.cash.register") {
            return;
        }
        const busService = this.env.services.bus_service;
        if (!busService) return;

        onMounted(() => {
            busService.addChannel("daily.cash.register.balance").catch((e) => {
                console.error("Failed to subscribe to daily.cash.register.balance:", e);
            });
        });

        this._onNotification = (ev) => {
            const notifications = ev && ev.detail;
            if (!this.model.root || !notifications) {
                return;
            }
            const list = Array.isArray(notifications) ? notifications : [notifications];
            for (const { type, payload } of list) {
                if (!payload || payload.register_id !== this.model.root.resId) {
                    continue;
                }
                if (type === "register_balance_updated") {
                    this.model.root.update({
                        expected_balance: payload.expected_balance,
                        difference: payload.difference,
                    });
                } else if (type === "register_data_changed") {
                    this.model.root.load();
                }
            }
        };
        busService.addEventListener("notification", this._onNotification);
        onWillDestroy(() => {
            busService.removeEventListener("notification", this._onNotification);
        });
    }
}

registry.category("views").add("daily_cash_register_form", {
    ...formView,
    Controller: CashRegisterFormController,
});
