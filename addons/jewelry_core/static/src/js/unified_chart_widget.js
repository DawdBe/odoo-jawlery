/** @odoo-module **/

import { loadBundle } from "@web/core/assets";
import { registry } from "@web/core/registry";
import { standardFieldProps } from "@web/views/fields/standard_field_props";

import { Component, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

class UnifiedChartWidget extends Component {
    static template = "jewelry_core.UnifiedChartWidget";
    static props = { ...standardFieldProps };

    COLORS = {
        gold: { bourse: "#1a1a2e", market: "#c9a84c" },
        silver: { bourse: "#4a4a6e", market: "#8a8a9e" },
    };

    setup() {
        this.canvasGoldBourse = useRef("canvasGoldBourse");
        this.canvasGoldMarket = useRef("canvasGoldMarket");
        this.canvasSilverBourse = useRef("canvasSilverBourse");
        this.canvasSilverMarket = useRef("canvasSilverMarket");
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
        }
    }

    _destroyCharts() {
        const canvases = [
            this.canvasGoldBourse.el, this.canvasGoldMarket.el,
            this.canvasSilverBourse.el, this.canvasSilverMarket.el,
        ];
        canvases.forEach((canvas) => {
            if (canvas && typeof Chart !== "undefined") {
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
                    ticks: { maxTicksLimit: 8, font: { size: 10 } },
                    grid: { display: false },
                },
                y: {
                    type: "linear",
                    display: true,
                    position: "left",
                    title: {
                        display: true,
                        text: unit,
                        font: { size: 11, weight: "bold" },
                    },
                    beginAtZero: false,
                    ticks: { font: { size: 10 } },
                },
            },
        };
    }

    async renderCharts() {
        this._destroyCharts();
        if (typeof Chart === "undefined") return;

        this.state.loading = true;

        const [goldResult, silverResult] = await Promise.all([
            this.orm.call("gold.price.overview", "get_chart_data", [this.state.range]),
            this.orm.call("gold.price.overview", "get_silver_chart_data", [this.state.range]),
        ]);

        const goldData = goldResult.data;
        const silverData = silverResult.data;

        if (goldData && goldData.length) {
            const labels = goldData.map((pt) => pt.x);
            new Chart(this.canvasGoldBourse.el, {
                type: "line",
                data: {
                    labels,
                    datasets: [{
                        label: "Bourse Gold (DZD/g)",
                        data: goldData.map((pt) => pt.bourse_dzd),
                        borderColor: this.COLORS.gold.bourse,
                        backgroundColor: "rgba(26, 26, 46, 0.06)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.COLORS.gold.bourse,
                        fill: false,
                        tension: 0.15,
                    }],
                },
                options: this._chartOptions("Bourse Gold", "DZD/g"),
            });
            new Chart(this.canvasGoldMarket.el, {
                type: "line",
                data: {
                    labels,
                    datasets: [{
                        label: "Market Gold (DZD/g)",
                        data: goldData.map((pt) => pt.market_dzd),
                        borderColor: this.COLORS.gold.market,
                        backgroundColor: "rgba(201, 168, 76, 0.06)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.COLORS.gold.market,
                        fill: false,
                        tension: 0.15,
                    }],
                },
                options: this._chartOptions("Market Gold", "DZD/g"),
            });
        }

        if (silverData && silverData.length) {
            const labels = silverData.map((pt) => pt.x);
            new Chart(this.canvasSilverBourse.el, {
                type: "line",
                data: {
                    labels,
                    datasets: [{
                        label: "Bourse Silver (DZD/g)",
                        data: silverData.map((pt) => pt.bourse_dzd),
                        borderColor: this.COLORS.silver.bourse,
                        backgroundColor: "rgba(74, 74, 110, 0.06)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.COLORS.silver.bourse,
                        fill: false,
                        tension: 0.15,
                    }],
                },
                options: this._chartOptions("Bourse Silver", "DZD/g"),
            });
            new Chart(this.canvasSilverMarket.el, {
                type: "line",
                data: {
                    labels,
                    datasets: [{
                        label: "Market Silver (DZD/g)",
                        data: silverData.map((pt) => pt.market_dzd),
                        borderColor: this.COLORS.silver.market,
                        backgroundColor: "rgba(138, 138, 158, 0.06)",
                        borderWidth: 2,
                        pointRadius: 3,
                        pointHoverRadius: 6,
                        pointBackgroundColor: this.COLORS.silver.market,
                        fill: false,
                        tension: 0.15,
                    }],
                },
                options: this._chartOptions("Market Silver", "DZD/g"),
            });
        }

        this.state.loading = false;
    }
}

export const unifiedChartWidget = {
    component: UnifiedChartWidget,
    supportedTypes: ["text"],
};

registry.category("fields").add("unified_chart", unifiedChartWidget);
