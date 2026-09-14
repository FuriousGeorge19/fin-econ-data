// Built-in `timeseries` chart type. Draws one or more traces from a data
// file's payload, per the payload convention in
// openspec/changes/s5-chart-components/design.md decision 4. No module-level
// state: render/stats/table/csv all re-derive their traces from ctx alone,
// so the same module can be mounted more than once on one page.
import { addMonthsUTC, addYearsUTC, valueOnOrBefore, formatDateLong } from '../lib/dates.js';
import { fmtChange } from '../lib/theme.js';
import { baseLayout, PLOT_CONFIG } from '../lib/plotly-layout.js';

function tokenColor(theme, token) {
    const m = /^series-(\d+)$/.exec(token || '');
    return m ? theme.seriesColors[(Number(m[1]) - 1) % 6] : theme.textMuted;
}

function deriveTraces(ctx) {
    const { data, presentation } = ctx;
    const chart = presentation.chart || {};

    if (chart.traces) {
        return chart.traces.map((t, i) => ({
            key: t.key,
            label: t.label,
            colorToken: t.color || `series-${(i % 6) + 1}`,
            observations: (data.observations || []).map(o => ({ date: o.date, value: o[t.y || t.key] })),
        }));
    }

    if (data.series) {
        return Object.keys(data.series).map((key, i) => ({
            key,
            label: data.series[key].label,
            colorToken: `series-${(i % 6) + 1}`,
            observations: data.series[key].observations,
        }));
    }

    const yField = (chart.y && chart.y.field) || 'value';
    return [{
        key: yField,
        label: data.meta.short_title,
        colorToken: 'series-1',
        observations: data.observations.map(o => ({ date: o.date, value: o[yField] })),
    }];
}

function formatValue(value, format) {
    const forceSign = format.startsWith('+');
    const spec = forceSign ? format.slice(1) : format;
    const m = /\.(\d+)f/.exec(spec);
    const digits = m ? Number(m[1]) : 2;
    const fixed = value.toFixed(digits);
    return forceSign && value >= 0 ? `+${fixed}` : fixed;
}

function decimalsFromFormat(format) {
    const m = /\.(\d+)f/.exec(format);
    return m ? Number(m[1]) : 2;
}

function hoverXFormat(cadence) {
    return cadence === 'monthly' ? '|%b %Y' : '';
}

function plotlyTrace(trace, ctx, multi) {
    const { theme, meta, presentation } = ctx;
    const y = presentation.chart.y || {};
    const format = y.format || '.2f';
    const suffix = y.suffix || '';
    const xfmt = hoverXFormat(meta.cadence);
    const prefix = multi ? `${trace.label}: ` : '';
    return {
        x: trace.observations.map(o => o.date),
        y: trace.observations.map(o => o.value),
        type: 'scatter',
        mode: 'lines',
        name: trace.label,
        line: { color: tokenColor(theme, trace.colorToken), width: 1.5 },
        hovertemplate: `%{x${xfmt}}<br>${prefix}%{y:${format}}${suffix}<extra></extra>`,
    };
}

function recessionShapes(recessions, theme, today) {
    return recessions.map(r => ({
        type: 'rect',
        xref: 'x', yref: 'paper',
        x0: r.start, x1: r.end || today,
        y0: 0, y1: 1,
        fillcolor: theme.recessionFill,
        line: { width: 0 },
        layer: 'below',
    }));
}

export function render(el, ctx) {
    const traces = deriveTraces(ctx);
    const multi = traces.length > 1;
    const startISO = traces
        .map(t => t.observations[0] && t.observations[0].date)
        .filter(Boolean)
        .sort()[0] || ctx.today;

    const chart = ctx.presentation.chart || {};
    const layout = baseLayout(ctx, { startISO });
    layout.yaxis.ticksuffix = (chart.y && chart.y.suffix) || '';
    if (chart.zeroline) {
        layout.yaxis.zeroline = true;
        layout.yaxis.zerolinecolor = ctx.theme.zeroLine;
        layout.yaxis.zerolinewidth = 1.5;
    }
    layout.shapes = ctx.recessions ? recessionShapes(ctx.recessions, ctx.theme, ctx.today) : [];

    Plotly.newPlot(
        el,
        traces.map(t => plotlyTrace(t, ctx, multi)),
        layout,
        PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`),
    );

    return { destroy() { Plotly.purge(el); } };
}

export function stats(ctx) {
    const traces = deriveTraces(ctx);
    const obs = traces[0].observations;
    if (!obs.length) return [];

    const y = ctx.presentation.chart.y || {};
    const format = y.format || '.2f';
    const suffix = y.suffix || '';
    const decimals = decimalsFromFormat(format);

    const latest = obs[obs.length - 1];
    const yearAgoTarget = addYearsUTC(latest.date, -1);
    const yearAgoObs = valueOnOrBefore(obs, yearAgoTarget);
    const windowObs = obs.filter(o => o.date >= yearAgoTarget);
    const highObs = windowObs.reduce((a, b) => (b.value > a.value ? b : a));
    const lowObs = windowObs.reduce((a, b) => (b.value < a.value ? b : a));

    const result = [
        { label: 'Latest', value: `${formatValue(latest.value, format)}${suffix}`, date: formatDateLong(latest.date) },
        { label: '1-Year High', value: `${formatValue(highObs.value, format)}${suffix}`, date: formatDateLong(highObs.date) },
        { label: '1-Year Low', value: `${formatValue(lowObs.value, format)}${suffix}`, date: formatDateLong(lowObs.date) },
    ];

    if (yearAgoObs) {
        const diff = latest.value - yearAgoObs.value;
        const { text, color } = fmtChange(diff, ctx.theme, { decimals, suffix });
        result.push({ label: '1-Year Change', value: text, date: `vs ${formatDateLong(yearAgoObs.date)}`, color });
    } else {
        result.push({ label: '1-Year Change', value: '—' });
    }

    return result;
}

function tableRecent(ctx, traces, opts) {
    const rowCount = opts.rows || 10;
    const format = (ctx.presentation.chart.y && ctx.presentation.chart.y.format) || '.2f';
    const suffix = (ctx.presentation.chart.y && ctx.presentation.chart.y.suffix) || '';
    const decimals = decimalsFromFormat(format);

    const columns = ['Date', ...traces.flatMap(t => [t.label, 'Change'])];
    const dates = traces[0].observations.slice(-rowCount).map(o => o.date).reverse();
    const byDate = traces.map(t => new Map(t.observations.map(o => [o.date, o.value])));

    const rows = dates.map(date => {
        const cells = [{ text: date }];
        traces.forEach((t, i) => {
            const val = byDate[i].get(date);
            cells.push({ text: val === undefined ? '—' : `${formatValue(val, format)}${suffix}` });

            const idx = t.observations.findIndex(o => o.date === date);
            const prev = idx > 0 ? t.observations[idx - 1] : null;
            if (prev && val !== undefined) {
                const diff = val - prev.value;
                cells.push(fmtChange(diff, ctx.theme, { decimals, suffix }));
            } else {
                cells.push({ text: '—' });
            }
        });
        return cells;
    });

    return { columns, rows };
}

function windowTarget(dateISO, windowLabel) {
    const m = /^(\d+)([MY])$/.exec(windowLabel);
    if (!m) throw new Error(`unknown window: ${windowLabel}`);
    const n = Number(m[1]);
    return m[2] === 'M' ? addMonthsUTC(dateISO, -n) : addYearsUTC(dateISO, -n);
}

function tableChanges(ctx, traces, opts) {
    const windows = opts.windows || ['1M', '1Y'];
    const format = (ctx.presentation.chart.y && ctx.presentation.chart.y.format) || '.2f';
    const suffix = (ctx.presentation.chart.y && ctx.presentation.chart.y.suffix) || '';
    const decimals = decimalsFromFormat(format);

    const columns = ['Series', 'Latest', ...windows.map(w => `${w} Change`)];
    const rows = traces.map(t => {
        const obs = t.observations;
        const latest = obs[obs.length - 1];
        const cells = [{ text: t.label }, { text: `${formatValue(latest.value, format)}${suffix}` }];
        windows.forEach(w => {
            const target = windowTarget(latest.date, w);
            const prevObs = valueOnOrBefore(obs, target);
            if (prevObs) {
                const diff = latest.value - prevObs.value;
                const { text, color } = fmtChange(diff, ctx.theme, { decimals, suffix });
                cells.push({ text: `${text} (vs ${formatDateLong(prevObs.date)})`, color });
            } else {
                cells.push({ text: '—' });
            }
        });
        return cells;
    });

    return { columns, rows };
}

export function table(ctx) {
    const cfg = ctx.presentation.table;
    if (!cfg) return null;
    const traces = deriveTraces(ctx);
    return cfg.kind === 'changes' ? tableChanges(ctx, traces, cfg) : tableRecent(ctx, traces, cfg);
}

export function csv(ctx) {
    const traces = deriveTraces(ctx);
    const dateSet = new Set();
    traces.forEach(t => t.observations.forEach(o => dateSet.add(o.date)));
    const dates = Array.from(dateSet).sort();
    const maps = traces.map(t => new Map(t.observations.map(o => [o.date, o.value])));

    const header = ['date', ...traces.map(t => t.key)].join(',');
    const rows = dates.map(d => [d, ...maps.map(m => (m.has(d) ? m.get(d) : ''))].join(','));
    return [header, ...rows].join('\n');
}
