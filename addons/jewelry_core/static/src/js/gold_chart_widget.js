/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class GoldChartWidget extends Component {
    static template = "jewelry_core.GoldChartWidget";
    static props = { ...standardFieldProps };

    setup() {
        this.canvasBourseRef = useRef("canvasBourse");
        this.canvasMarketRef = useRef("canvasMarket");
        this.orm = useService("orm");
        this.notification = useService("notification");
        this.state = useState({ range: "all", loading: false });

        onWillStart(async () => {
            await loadBundle("web.chartjs_lib");
        });

        useEffect(
            () => {
                this.renderCharts();
                this._checkAutoRefresh();
                return () => this._destroyCharts();
            },
            () => []
        );
    }

    async _checkAutoRefresh() {
        try {
            const error = await this.orm.call(
                "gold.price.overview",
                "get_auto_refresh_msg",
                [this.props.record.resId]
            );
            if (error) {
                this.notification.add(error, { type: "warning" });
            }
        } catch (_) {
            // silent – don't crash the widget on a notification check
        }
    }

    _destroyCharts() {
        [this.canvasBourseRef.el, this.canvasMarketRef.el].forEach((canvas) => {
            if (canvas) {
                const existing = Chart.getChart(canvas);
                if (existing) existing.destroy();
            }
        });
    }

    async onFilter(range) {
        this.state.range = range;
        this.state.loading = true;
        await this.renderCharts();
        this.state.loading = false;
    }

    _chartOptions(title, unit) {
        return {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { intersect: false, mode: "index" },
            plugins: {
                legend: { display: false },
                tooltip: {
                    intersect: false,
                    mode: "index",
                    backgroundColor: "#1a1a2e",
                    titleFont: { size: 13 },
                    bodyFont: { size: 12 },
                    padding: 12,
                    callbacks: {
                        label: function (ctx) {
                            return title + ": " + Number(ctx.parsed.y).toLocaleString(undefined, {
                                minimumFractionDigits: 2,
                                maximumFractionDigits: 2,
                            }) + " " + unit;
                        },
                    },
                },
            },
            scales: {
                x: {
                    type: "time",
                    time: {
                        unit: "day",
                        displayFormats: { day: "MMM d, yyyy" },
                        tooltipFormat: "MMM d, yyyy",
                    },
                    ticks: { maxTicksLimit: 10, font: { size: 11 } },
                    grid: { display: false },
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    title: {
                        display: true,
                        text: unit,
                        font: { size: 12, weight: "bold" },
                    },
                    beginAtZero: false,
                    ticks: { font: { size: 11 } },
                },
            },
        };
    }

    async renderCharts() {
        this._destroyCharts();

        const result = await this.orm.call(
            "gold.price.overview",
            "get_chart_data",
            [this.state.range]
        );

        const data = result.data;
        if (!data || !data.length) return;

        const labels = data.map((pt) => pt.x);

        new Chart(this.canvasBourseRef.el, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Bourse 24K (DZD/g)",
                    data: data.map((pt) => pt.bourse_dzd),
                    borderColor: "#1a1a2e",
                    backgroundColor: "rgba(26, 26, 46, 0.06)",
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: "#1a1a2e",
                    fill: false,
                    tension: 0.15,
                }],
            },
            options: this._chartOptions("Bourse 24K", "DZD/g"),
        });

        new Chart(this.canvasMarketRef.el, {
            type: "line",
            data: {
                labels,
                datasets: [{
                    label: "Market Price (USD/g)",
                    data: data.map((pt) => pt.market_usd),
                    borderColor: "#c9a84c",
                    backgroundColor: "rgba(201, 168, 76, 0.06)",
                    borderWidth: 2,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: "#c9a84c",
                    fill: false,
                    tension: 0.15,
                }],
            },
            options: this._chartOptions("Market Price", "USD/g"),
        });
    }
}

export const goldChartWidget = {
    component: GoldChartWidget,
    supportedTypes: ["text"],
};

registry.category("fields").add("gold_chart", goldChartWidget);
