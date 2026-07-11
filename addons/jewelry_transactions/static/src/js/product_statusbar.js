/** @odoo-module **/
import { registry } from "@web/core/registry";
import { statusBarField } from "@web/views/fields/statusbar/statusbar_field";

const clickableStatusBarField = {
    ...statusBarField,
    extractProps: ({ attrs, options, viewType }, dynamicInfo) => ({
        isDisabled: !options.clickable || dynamicInfo.readonly,
        visibleSelection: attrs.statusbar_visible?.trim().split(/\s*,\s*/g),
        withCommand: viewType === "form",
        foldField: options.fold_field,
        domain: dynamicInfo.domain(),
    }),
};

registry.category("fields").add("clickable_statusbar", clickableStatusBarField);
