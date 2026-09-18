// Built-in `tenors` chart type (roadmap chart 9). Draws selected Treasury
// tenors as time series from a CURVE-shaped payload — the date-keyed
// {tenor: value} object that fetch_yield_curve.py writes — transposing it
// into one trace per tenor.
//
// It reads yield_curve.json rather than a file of its own, via the descriptor's
// `presentation.data`. That matters: the payload is ~16,000 dates × 11 tenors,
// and giving this chart its own fetcher would ship a second multi-megabyte copy
// of identical numbers.
//
// Like curve.js, all interactive state (which tenors are selected) lives inside
// render()'s own closure, never at module scope, so two mounts on one page keep
// independent selections.
import { formatDateLong } from '../lib/dates.js';
import { baseLayout, PLOT_CONFIG } from '../lib/plotly-layout.js';

function tokenColor(theme, index) {
    return theme.seriesColors[index % theme.seriesColors.length];
}

// Transpose {date: {tenor: value}} into per-tenor observation lists. A tenor
// is absent from a date it did not report — the tenors phase in across the
// 1960s-2001 as Treasury began issuing them — and the gap stays a gap rather
// than being carried forward, per the site's own convention.
function tracesForTenors(data, tenors) {
    const dates = Object.keys(data.observations).sort();
    return tenors.map(tenor => {
        const observations = [];
        for (const date of dates) {
            const value = data.observations[date][tenor];
            if (value !== undefined && value !== null) observations.push({ date, value });
        }
        return { tenor, observations };
    });
}

function formatValue(value, decimals) {
    return value.toFixed(decimals);
}

function plotlyTrace(trace, colorIndex, ctx, decimals, suffix) {
    // Hover text is precomputed rather than left to Plotly's %{y:...}
    // templating, for the reason timeseries.js documents: that path is plain
    // d3-format and silently mishandles this repo's formats.
    const text = trace.observations.map(o =>
        `${formatDateLong(o.date)}<br>${trace.tenor}: ${formatValue(o.value, decimals)}${suffix}`
    );
    return {
        x: trace.observations.map(o => o.date),
        y: trace.observations.map(o => o.value),
        type: 'scatter',
        mode: 'lines',
        name: trace.tenor,
        line: { color: tokenColor(ctx.theme, colorIndex), width: 1.5 },
        text,
        hovertemplate: '%{text}<extra></extra>',
    };
}

function recessionShapes(recessions, theme, today) {
    return recessions.map(r => ({
        type: 'rect',
        xref: 'x',
        yref: 'paper',
        x0: r.start,
        x1: r.end || today,
        y0: 0,
        y1: 1,
        fillcolor: theme.recessionFill,
        line: { width: 0 },
        layer: 'below',
    }));
}

// The tenors a chart offers, and which start selected. Defaults to every tenor
// the payload carries, with `default_tenors` selected — a sensible spread
// rather than all eleven lines at once, which is unreadable.
function tenorConfig(ctx) {
    const chart = ctx.presentation.chart || {};
    const available = chart.tenors || ctx.data.tenors || [];
    const initial = chart.default_tenors || available;
    return { available, initial: available.filter(t => initial.includes(t)) };
}

export function render(el, ctx) {
    const chart = ctx.presentation.chart || {};
    const y = chart.y || {};
    const suffix = y.suffix || '';
    const decimals = (() => {
        const m = /\.(\d+)f/.exec(y.format || '.2f');
        return m ? Number(m[1]) : 2;
    })();

    const { available, initial } = tenorConfig(ctx);
    const selected = new Set(initial);          // closure state, never module state

    const allDates = Object.keys(ctx.data.observations).sort();
    const startISO = allDates[0] || ctx.today;

    function draw() {
        const chosen = available.filter(t => selected.has(t));
        const traces = tracesForTenors(ctx.data, chosen);

        const layout = baseLayout(ctx, { startISO });
        layout.yaxis.ticksuffix = suffix;
        layout.shapes = ctx.recessions
            ? recessionShapes(ctx.recessions, ctx.theme, ctx.today)
            : [];

        // Colour by position in the FULL tenor list, not in the selection, so a
        // tenor keeps its colour as others are toggled on and off.
        const plotted = traces.map(t =>
            plotlyTrace(t, available.indexOf(t.tenor), ctx, decimals, suffix)
        );
        Plotly.react(el, plotted, layout, PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));
    }

    if (ctx.slots.controls && available.length) {
        const wrap = document.createElement('div');
        wrap.className = 'yc-controls';
        ctx.slots.controls.appendChild(wrap);

        const label = document.createElement('label');
        label.textContent = 'Tenors:';
        wrap.appendChild(label);

        available.forEach(tenor => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `yc-toggle${selected.has(tenor) ? ' active' : ''}`;
            btn.textContent = tenor;
            btn.addEventListener('click', () => {
                // Never let the last line be switched off: an empty chart reads
                // as broken, and there is no other affordance saying why.
                if (selected.has(tenor) && selected.size === 1) return;
                if (selected.has(tenor)) selected.delete(tenor);
                else selected.add(tenor);
                btn.classList.toggle('active', selected.has(tenor));
                draw();
            });
            wrap.appendChild(btn);
        });
    }

    draw();
    return { destroy() { Plotly.purge(el); } };
}

export function stats(ctx) {
    const { available } = tenorConfig(ctx);
    const dates = Object.keys(ctx.data.observations).sort();
    if (!dates.length) return [];

    const latestDate = dates[dates.length - 1];
    const latest = ctx.data.observations[latestDate];
    const y = ctx.presentation.chart.y || {};
    const suffix = y.suffix || '';
    const m = /\.(\d+)f/.exec(y.format || '.2f');
    const decimals = m ? Number(m[1]) : 2;

    // The stat row reports the configured highlight tenors on the latest date,
    // not whatever is toggled on — stats() is pure and has no access to the
    // live selection, the same rule curve.js's table() follows.
    const highlight = (ctx.presentation.chart.stat_tenors || available).filter(
        t => latest[t] !== undefined
    );
    return highlight.map(tenor => ({
        label: tenor,
        value: `${formatValue(latest[tenor], decimals)}${suffix}`,
        date: formatDateLong(latestDate),
    }));
}

export function table(ctx) {
    const { available } = tenorConfig(ctx);
    const dates = Object.keys(ctx.data.observations).sort();
    const rows = ctx.presentation.table && ctx.presentation.table.rows
        ? ctx.presentation.table.rows
        : 30;
    const y = ctx.presentation.chart.y || {};
    const suffix = y.suffix || '';
    const m = /\.(\d+)f/.exec(y.format || '.2f');
    const decimals = m ? Number(m[1]) : 2;

    const recent = dates.slice(-rows).reverse();
    return {
        columns: ['Date', ...available],
        rows: recent.map(date => {
            const row = ctx.data.observations[date];
            return [
                { text: formatDateLong(date) },
                ...available.map(tenor => ({
                    text: row[tenor] === undefined
                        ? '—'
                        : `${formatValue(row[tenor], decimals)}${suffix}`,
                })),
            ];
        }),
        note: 'A dash marks a tenor Treasury was not issuing on that date; '
            + 'the chart leaves the same gaps visible rather than interpolating across them.',
    };
}

export function csv(ctx) {
    const { available } = tenorConfig(ctx);
    const dates = Object.keys(ctx.data.observations).sort();
    const header = ['date', ...available].join(',');
    const rows = dates.map(date => {
        const row = ctx.data.observations[date];
        return [date, ...available.map(t => (row[t] === undefined ? '' : row[t]))].join(',');
    });
    return [header, ...rows].join('\n');
}
