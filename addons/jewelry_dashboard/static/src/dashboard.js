// DashboardWidget — placeholder widget for the jewelry dashboard.
// Currently a shell; the actual dashboard KPIs are rendered server-side
// via the dashboard.360 TransientModel fields in the XML form view.
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
