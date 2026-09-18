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
        observations: data.observations.map(o => ({
            date: o.date, value: o[yField], source: o.source, frequency: o.frequency,
        })),
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

// A full date for daily cadence, month-and-year for monthly -- computed once
// per point here rather than left to Plotly's own hover formatting, which is
// zoom-adaptive (abbreviates at wide zoom) and so cannot satisfy the
// chart-chrome spec's "hover x-format derives from meta.cadence" rule on its
// own.
function hoverDateLabel(iso, cadence) {
    const full = formatDateLong(iso);
    return cadence === 'monthly' ? full.replace(/^\d+\s+/, '') : full;
}

// A point's `source` (the catalog slug that produced it, e.g. a stitched
// series' pre/post-cutover legs — see series/gs10_long.json) resolved to that
// source's short_name for the hover line. Absent on every chart that isn't
// stitched from more than one source, so this returns '' there.
function sourceHoverLine(observation, sources) {
    if (!observation.source || !sources) return '';
    const match = sources.find(s => s.slug === observation.source);
    if (!match) return '';
    return `<br>Source: ${match.short_name || match.name}`;
}

function plotlyTrace(trace, ctx, multi) {
    const { theme, meta, presentation } = ctx;
    const y = presentation.chart.y || {};
    const format = y.format || '.2f';
    const suffix = y.suffix || '';
    const prefix = multi ? `${trace.label}: ` : '';
    // Hover text is built here, point by point, rather than via Plotly's own
    // "%{y:<format>}" templating: that path is plain d3-format and does not
    // accept our "+.2f" (forced-sign) convention the way formatValue() does,
    // which silently drops the sign and logs a console warning on every
    // hover for any trace using it (e.g. the spreads chart).
    const text = trace.observations.map(o =>
        `${hoverDateLabel(o.date, meta.cadence)}<br>${prefix}${formatValue(o.value, format)}${suffix}` +
        sourceHoverLine(o, meta.sources)
    );
    return {
        x: trace.observations.map(o => o.date),
        y: trace.observations.map(o => o.value),
        type: 'scatter',
        mode: 'lines',
        name: trace.label,
        line: { color: tokenColor(theme, trace.colorToken), width: 1.5 },
        text,
        hovertemplate: '%{text}<extra></extra>',
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

function ordinal(n) {
    const tens = n % 100;
    const suffix = (tens >= 11 && tens <= 13) ? 'th' : ({ 1: 'st', 2: 'nd', 3: 'rd' }[n % 10] || 'th');
    return `${n}${suffix}`;
}

// "Where today sits in history" (roadmap item 18): the latest value's
// percentile over the whole file (ties count half), and how long ago the
// series last matched or beat it — "Highest since" when it sits in the upper
// half of its history, "Lowest since" otherwise.
function historyTiles(obs, format, suffix) {
    const vals = obs.filter(o => Number.isFinite(o.value));
    if (vals.length < 2) return [];
    const latest = vals[vals.length - 1];
    let below = 0, equal = 0;
    for (const o of vals) {
        if (o.value < latest.value) below++;
        else if (o.value === latest.value) equal++;
    }
    const pct = Math.round(100 * (below + equal / 2) / vals.length);
    const upper = pct >= 50;
    let since = null;
    for (let i = vals.length - 2; i >= 0; i--) {
        if (upper ? vals[i].value >= latest.value : vals[i].value <= latest.value) { since = vals[i]; break; }
    }
    const word = upper ? 'Highest' : 'Lowest';
    const first = formatDateLong(vals[0].date);
    return [
        { label: 'Percentile of History', value: ordinal(pct), date: `of ${vals.length.toLocaleString('en-US')} obs since ${first}` },
        since
            ? { label: `${word} Since`, value: formatDateLong(since.date), date: `then ${formatValue(since.value, format)}${suffix}` }
            : { label: `${word} Since`, value: 'Record', date: `${word.toLowerCase()} of all obs since ${first}` },
    ];
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

    return result.concat(historyTiles(obs, format, suffix));
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
