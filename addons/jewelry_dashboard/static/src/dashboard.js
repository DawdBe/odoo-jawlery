odoo.define('jewelry_dashboard.dashboard', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t;

    var DashboardWidget = Widget.extend({
        template: 'jewelry_dashboard.Dashboard',
        events: {},

        start: function () {
            this._super.apply(this, arguments);
            return this;
        },
    });

    core.action_registry.add('jewelry_dashboard.dashboard', DashboardWidget);
    return DashboardWidget;
});
