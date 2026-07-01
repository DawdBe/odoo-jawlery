/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { getColor, hexToRGBA } from "@web/core/colors/colors";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, onWillStart, useEffect, useRef } from "@odoo/owl";
import { cookie } from "@web/core/browser/cookie";

class GoldChartWidget extends Component {
    static template = "jewelry_core.GoldChartWidget";
    static props = {
        ...standardFieldProps,
    };

    setup() {
        this.chart = null;
        this.canvasRef = useRef("canvas");

        onWillStart(async () => await loadBundle("web.chartjs_lib"));

        useEffect(() => {
            this.renderChart();
            return () => {
                if (this.chart) {
                    this.chart.destroy();
                }
            };
        });
    }

    renderChart() {
        if (this.chart) {
            this.chart.destroy();
        }
        const raw = this.props.record.data[this.props.name];
        if (!raw) return;
        const data = JSON.parse(raw);
        if (!data || !data.length) return;

        const palette = [10, 13, 19, 7, 3];
        const datasets = data.map((series, i) => {
            const c = getColor(palette[i % palette.length], cookie.get("color_scheme"));
            return {
                label: series.key,
                data: series.values,
                borderColor: c,
                backgroundColor: hexToRGBA(c, 0.1),
                borderWidth: 2,
                pointRadius: 0,
                fill: false,
                tension: 0.1,
            };
        });

        const labels = data[0].values.map((pt) => pt.x);

        this.chart = new Chart(this.canvasRef.el, {
            type: "line",
            data: { labels, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { intersect: false, mode: "index" },
                plugins: {
                    legend: { position: "top" },
                    tooltip: { intersect: false, position: "nearest", caretSize: 0 },
                },
                scales: {
                    x: {
                        type: "time",
                        time: { unit: "day", displayFormats: { day: "MMM d" } },
                        ticks: { maxTicksLimit: 10 },
                    },
                    y: { beginAtZero: false },
                },
            },
        });
    }
}

export const goldChartWidget = {
    component: GoldChartWidget,
    supportedTypes: ["text"],
};

registry.category("fields").add("gold_chart", goldChartWidget);
