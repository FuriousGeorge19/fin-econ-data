// Custom chart type for the S&P 500 trailing P/E ratio. Not expressible as
// `timeseries` config: the confirmed/estimated dashed-line split (with the
// last confirmed point prepended so the dash visually connects), the
// long-term-average stat, and the dagger-marked table rows. Ported from the
// pre-rebuild site/index.html's renderPEChart/renderPEStats/renderPETable/
// csvFromObservations (search that file for "S&P 500 P/E").
//
// No module-level state: every export re-derives everything from ctx alone.
import { addYearsUTC } from '../lib/dates.js';
import { baseLayout, PLOT_CONFIG } from '../lib/plotly-layout.js';

function fmtPE(value) {
    return `${value.toFixed(1)}x`;
}

function monthYear(iso) {
    return new Date(iso).toLocaleDateString('en-US', { year: 'numeric', month: 'short', timeZone: 'UTC' });
}

function formatPrice(value) {
    return value.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

export function render(el, ctx) {
    const { theme, data } = ctx;
    const obs = data.observations;
    const confirmed = obs.filter(o => !o.estimated);
    const estimated = obs.filter(o => o.estimated);
    const lastConfirmed = confirmed[confirmed.length - 1];

    const traces = [{
        x: confirmed.map(o => o.date),
        y: confirmed.map(o => o.pe),
        type: 'scatter',
        mode: 'lines',
        name: 'Trailing P/E',
        line: { color: theme.seriesColors[1], width: 1.5 },
        hovertemplate: '%{x|%b %Y}<br>P/E: %{y:.1f}x<extra></extra>',
    }];

    if (estimated.length > 0) {
        traces.push({
            x: [lastConfirmed.date, ...estimated.map(o => o.date)],
            y: [lastConfirmed.pe, ...estimated.map(o => o.pe)],
            type: 'scatter',
            mode: 'lines+markers',
            name: 'Estimated (†)',
            line: { color: theme.seriesColors[2], width: 1.5, dash: 'dash' },
            marker: { color: theme.seriesColors[2], size: 4 },
            hovertemplate: '%{x|%b %Y}<br>P/E: %{y:.1f}x (est.)<extra></extra>',
        });
    }

    const startISO = obs[0].date;
    const layout = baseLayout(ctx, { startISO });
    layout.yaxis.ticksuffix = 'x';

    Plotly.newPlot(el, traces, layout, PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));

    return { destroy() { Plotly.purge(el); } };
}

export function stats(ctx) {
    const obs = ctx.data.observations;
    if (!obs.length) return [];

    const confirmed = obs.filter(o => !o.estimated);
    const latest = obs[obs.length - 1];
    const avgPE = confirmed.reduce((sum, o) => sum + o.pe, 0) / confirmed.length;

    const windowStart = addYearsUTC(latest.date, -10);
    const windowObs = obs.filter(o => o.date >= windowStart);
    const highObs = windowObs.reduce((a, b) => (b.pe > a.pe ? b : a));
    const lowObs = windowObs.reduce((a, b) => (b.pe < a.pe ? b : a));

    return [
        { label: 'Latest P/E', value: fmtPE(latest.pe), date: ctx.as_of.period_label },
        { label: 'Long-term Avg', value: fmtPE(avgPE) },
        { label: '10Y High', value: fmtPE(highObs.pe) },
        { label: '10Y Low', value: fmtPE(lowObs.pe) },
    ];
}

export function table(ctx) {
    const obs = ctx.data.observations;
    const recent = obs.slice(-24).reverse();

    const rows = recent.map(o => [
        { text: `${o.estimated ? '† ' : ''}${monthYear(o.date)}` },
        { text: fmtPE(o.pe) },
        { text: formatPrice(o.price) },
        { text: o.earnings.toFixed(2) },
    ]);

    return {
        columns: ['Date', 'P/E Ratio', 'S&P 500 Price', 'TTM Earnings'],
        rows,
        note: '† Estimated — earnings forward-filled from the last confirmed quarter',
    };
}

export function csv(ctx) {
    const obs = ctx.data.observations;
    const header = 'date,pe,price,earnings,estimated';
    const rows = obs.map(o => `${o.date},${o.pe},${o.price},${o.earnings},${o.estimated ? 'true' : 'false'}`);
    return [header, ...rows].join('\n');
}
