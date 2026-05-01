odoo.define('hkd_dashboard.chart', function () {
    "use strict";

    function getJsonField(name) {
        const field = document.querySelector(`[name="${name}"]`);
        if (!field) {
            return null;
        }

        const candidate = field.querySelector('input, textarea, span, .o_field_char, .o_field_widget');
        const raw = candidate
            ? (candidate.value || candidate.textContent || '').trim()
            : (field.textContent || '').trim();

        if (!raw) {
            return null;
        }

        try {
            return JSON.parse(raw);
        } catch (e) {
            return null;
        }
    }

    function createChartHolder(targetId) {
        const holder = document.getElementById(targetId);
        if (!holder) {
            return null;
        }

        const canvas = holder.tagName && holder.tagName.toLowerCase() === 'canvas'
            ? holder
            : holder.querySelector('canvas');

        if (!canvas) {
            return null;
        }

        const wrap = canvas.closest('.hkd-canvas-wrap') || holder;
        wrap.style.minHeight = '320px';
        canvas.width = 800;
        canvas.height = 320;
        canvas.style.width = '100%';
        canvas.style.height = '320px';
        return canvas.getContext('2d');
    }

    function drawBarChart(ctx, labels, values, label, colors) {
        return new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
                    backgroundColor: colors,
                    borderRadius: 8,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { display: false } },
                scales: {
                    x: { grid: { display: false } },
                    y: { beginAtZero: true, grid: { color: '#eef2f7' } },
                },
            },
        });
    }

    function tryDrawChart() {
        if (typeof Chart === 'undefined') {
            return false;
        }

        const barCtxSupplier = createChartHolder('hkd_vendor_bar_supplier');
        const barCtxTrader = createChartHolder('hkd_vendor_bar_trader');
        const pieCtx = createChartHolder('hkd_overdue_doughnut');
        if (!barCtxSupplier || !barCtxTrader || !pieCtx) {
            return false;
        }

        const d1 = getJsonField('chart_debt_by_vendor');
        const d2 = getJsonField('chart_overdue_vs_notdue');
        if (!d1 || !d1.supplier || !d1.trader || !d2) {
            return false;
        }

        const supplierCanvas = barCtxSupplier.canvas;
        const traderCanvas = barCtxTrader.canvas;
        const pieCanvas = pieCtx.canvas;

        if (supplierCanvas._chart) supplierCanvas._chart.destroy();
        if (traderCanvas._chart) traderCanvas._chart.destroy();
        if (pieCanvas._chart) pieCanvas._chart.destroy();

        supplierCanvas._chart = drawBarChart(
            barCtxSupplier,
            d1.supplier.labels || [],
            d1.supplier.values || [],
            'Nhà cung cấp',
            ['#2563eb', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe']
        );

        traderCanvas._chart = drawBarChart(
            barCtxTrader,
            d1.trader.labels || [],
            d1.trader.values || [],
            'Tiểu thương',
            ['#059669', '#10b981', '#34d399', '#6ee7b7', '#a7f3d0', '#d1fae5']
        );

        pieCanvas._chart = new Chart(pieCtx, {
            type: 'doughnut',
            data: {
                labels: ['Quá hạn', 'Chưa đến hạn'],
                datasets: [{
                    data: [d2.overdue || 0, d2.not_due || 0],
                    backgroundColor: ['#ef4444', '#10b981'],
                    borderWidth: 0,
                }],
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: { legend: { position: 'bottom' } },
                cutout: '68%',
            },
        });

        return true;
    }

    function boot() {
        let attempts = 0;
        const interval = setInterval(function () {
            attempts += 1;
            if (tryDrawChart() || attempts > 20) {
                clearInterval(interval);
            }
        }, 500);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', boot);
    } else {
        boot();
    }
});