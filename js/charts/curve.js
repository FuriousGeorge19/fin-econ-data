// Built-in `curve` chart type. Draws a tenor-vs-yield snapshot (today: the
// Treasury yield curve) on a categorical, evenly spaced tenor axis (Bloomberg
// convention), with overlay toggle buttons and an optional custom-date
// picker as DOM controls in ctx.slots.controls. All interactive state (which
// overlays are active, the custom date value) lives inside render()'s own
// closure — never at module scope — so a second mount of this type on one
// page (e.g. a future nominal + TIPS curve) keeps independent state.
import { addDaysUTC, addMonthsUTC, addYearsUTC, nearestOnOrBefore, formatDateLong } from '../lib/dates.js';
import { fmtChange } from '../lib/theme.js';
import { baseLayout, PLOT_CONFIG } from '../lib/plotly-layout.js';

// Grammar: <n><w|m|y> counting back from the latest date, e.g. "1w", "5y";
// or "ytd", the last observation on or before 31 Dec of the prior year.
function periodParts(period) {
    if (period === 'ytd') return { n: 0, unit: 'ytd' };
    const m = /^(\d+)([wmy])$/.exec(period);
    if (!m) throw new Error(`unknown overlay period: ${period}`);
    return { n: Number(m[1]), unit: m[2] };
}

function targetDateFor(period, latestDate) {
    const { n, unit } = periodParts(period);
    if (unit === 'ytd') return `${Number(latestDate.slice(0, 4)) - 1}-12-31`;
    if (unit === 'w') return addDaysUTC(latestDate, -n * 7);
    if (unit === 'm') return addMonthsUTC(latestDate, -n);
    return addYearsUTC(latestDate, -n);
}

function overlayLabel(period) {
    const { n, unit } = periodParts(period);
    if (unit === 'ytd') return 'Year to Date';
    const noun = { w: 'Week', m: 'Month', y: 'Year' }[unit];
    return `${n} ${noun}${n === 1 ? '' : 's'} Ago`;
}

// 1w/1m/1y/5y's colours follow the pre-rebuild dashboard exactly (1w ->
// muted text, not a genuine series colour, kept for visual continuity); a
// period outside that set continues the same series-colour cycle rather
// than repeating one of the four above.
function overlayColor(theme, period) {
    switch (period) {
        case '1w': return theme.textMuted;
        case '1m': return theme.seriesColors[1];
        case '1y': return theme.seriesColors[2];
        case '5y': return theme.up;
        default: return theme.seriesColors[4];
    }
}

function changeColumnLabel(period, compDateISO) {
    const { n, unit } = periodParts(period);
    const what = unit === 'ytd' ? 'YTD' : `${n}-${{ w: 'Week', m: 'Month', y: 'Year' }[unit]}`;
    return `${what} Change, bp (vs ${formatDateLong(compDateISO)})`;
}

// Whole basis points: the yields are published to two decimals, so a
// difference is always a whole number of bp (rounding only removes float noise).
function bpChange(diffPct, theme) {
    return fmtChange(Math.round(diffPct * 100), theme, { decimals: 0, suffix: ' bp' });
}

function formatDateLabel(dateISO) {
    const [y, m, d] = dateISO.split('-').map(Number);
    return new Date(Date.UTC(y, m - 1, d)).toLocaleDateString('en-US', {
        year: 'numeric', month: 'short', day: 'numeric', timeZone: 'UTC',
    });
}

function sortedDates(data) {
    return Object.keys(data.observations).sort();
}

function buildCurveTrace(data, date, name, color, opts) {
    const obs = data.observations[date];
    if (!obs) return null;
    const x = [], y = [];
    for (const t of data.tenors) {
        if (obs[t] !== undefined) {
            x.push(t);
            y.push(obs[t]);
        }
    }
    return {
        x, y,
        type: 'scatter',
        mode: 'lines+markers',
        name,
        line: { color, width: opts.width, dash: opts.dash },
        marker: { color, size: opts.markerSize },
        hovertemplate: `%{x}<br>%{y:.2f}${opts.suffix}<extra>${name}</extra>`,
    };
}

export function render(el, ctx) {
    const { data, theme, presentation, today } = ctx;
    const chart = presentation.chart || {};
    const suffix = (chart.y && chart.y.suffix) || '%';
    const overlays = chart.overlays || [];
    const dates = sortedDates(data);
    const latestDate = dates[dates.length - 1];

    // Per-mount state: which overlay periods are toggled on, and the custom
    // date input's current value. Declared here, inside render()'s closure.
    const active = new Set(overlays.length ? [overlays[0]] : []);
    let dateInput = null;

    // The custom date's change table (roadmap item 13) sits under the chart.
    // table() cannot see the picked date, so render() owns this one; it is a
    // sibling of `el`, which Plotly.react never touches.
    const customTable = document.createElement('div');
    customTable.className = 'yc-custom-table';
    customTable.hidden = true;
    el.after(customTable);

    function drawCustomTable() {
        if (!dateInput || !dateInput.value) {
            customTable.hidden = true;
            customTable.innerHTML = '';
            return;
        }
        const compDate = nearestOnOrBefore(dates, dateInput.value) || dates[0];
        const comp = data.observations[compDate] || {};
        const latest = data.observations[latestDate];
        const head = `<tr><th>Tenor</th><th>${formatDateLong(latestDate)}</th>`
            + `<th>${formatDateLong(compDate)}</th><th>Change, bp</th></tr>`;
        const body = data.tenors
            .filter(t => latest[t] !== undefined)
            .map(t => {
                if (comp[t] === undefined) {
                    return `<tr><td>${t}</td><td>${latest[t].toFixed(2)}${suffix}</td><td>—</td><td>—</td></tr>`;
                }
                const ch = bpChange(latest[t] - comp[t], theme);
                return `<tr><td>${t}</td><td>${latest[t].toFixed(2)}${suffix}</td>`
                    + `<td>${comp[t].toFixed(2)}${suffix}</td><td style="color: ${ch.color}">${ch.text}</td></tr>`;
            }).join('');
        customTable.innerHTML = `<table><thead>${head}</thead><tbody>${body}</tbody></table>`;
        customTable.hidden = false;
    }

    function buildTraces() {
        const traces = [];
        const current = buildCurveTrace(
            data, latestDate, formatDateLabel(latestDate), theme.seriesColors[0],
            { width: 3, markerSize: 8, dash: 'solid', suffix },
        );
        if (current) traces.push(current);

        overlays.forEach(period => {
            if (!active.has(period)) return;
            const compDate = nearestOnOrBefore(dates, targetDateFor(period, latestDate)) || dates[0];
            const trace = buildCurveTrace(
                data, compDate, formatDateLabel(compDate), overlayColor(theme, period),
                { width: 1.5, dash: 'dash', markerSize: 4, suffix },
            );
            if (trace) traces.push(trace);
        });

        if (dateInput && dateInput.value) {
            const nearestCustom = nearestOnOrBefore(dates, dateInput.value) || dates[0];
            const trace = buildCurveTrace(
                data, nearestCustom, formatDateLabel(nearestCustom), theme.seriesColors[3],
                { width: 1.5, dash: 'dot', markerSize: 4, suffix },
            );
            if (trace) traces.push(trace);
        }

        return traces;
    }

    function buildLayout() {
        const layout = baseLayout(ctx, { startISO: today });
        layout.xaxis = {
            type: 'category',
            categoryorder: 'array',
            categoryarray: data.tenors,
            gridcolor: theme.gridline,
            linecolor: theme.axisLine,
        };
        layout.yaxis.ticksuffix = suffix;
        return layout;
    }

    function draw() {
        Plotly.react(el, buildTraces(), buildLayout(), PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));
        drawCustomTable();
    }

    // A "yc-controls" wrapper (existing class, carried over specifically for
    // this port) groups the overlay toggles and date picker inside the
    // card's shared control row, alongside the preset row this chart type
    // doesn't use.
    const wrap = document.createElement('div');
    wrap.className = 'yc-controls';
    ctx.slots.controls.appendChild(wrap);

    if (overlays.length) {
        const compareLabel = document.createElement('label');
        compareLabel.textContent = 'Compare:';
        wrap.appendChild(compareLabel);

        overlays.forEach(period => {
            const btn = document.createElement('button');
            btn.type = 'button';
            btn.className = `yc-toggle${active.has(period) ? ' active' : ''}`;
            btn.textContent = overlayLabel(period);
            btn.addEventListener('click', () => {
                if (active.has(period)) {
                    active.delete(period);
                } else {
                    active.add(period);
                }
                btn.classList.toggle('active');
                draw();
            });
            wrap.appendChild(btn);
        });
    }

    if (chart.custom_date) {
        const customLabel = document.createElement('label');
        customLabel.textContent = 'Custom:';
        wrap.appendChild(customLabel);

        dateInput = document.createElement('input');
        dateInput.type = 'date';
        dateInput.className = 'yc-date-input';
        dateInput.min = dates[0];
        dateInput.max = dates[dates.length - 1];
        dateInput.addEventListener('change', draw);
        wrap.appendChild(dateInput);
    }

    Plotly.newPlot(el, buildTraces(), buildLayout(), PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));

    return { destroy() { customTable.remove(); Plotly.purge(el); } };
}

// Pure: uses the CONFIGURED overlays (ctx.presentation.chart.overlays), not
// whichever toggles happen to be active on screen, since this has no access
// to live DOM state.
export function table(ctx) {
    const { data, theme, presentation } = ctx;
    const chart = presentation.chart || {};
    const suffix = (chart.y && chart.y.suffix) || '%';
    const overlays = chart.overlays || [];
    const dates = sortedDates(data);
    const latestDate = dates[dates.length - 1];
    const latestObs = data.observations[latestDate];

    const comparisons = overlays.map(period => {
        const compDate = nearestOnOrBefore(dates, targetDateFor(period, latestDate)) || dates[0];
        return { period, obs: data.observations[compDate] || {}, compDate };
    });

    const columns = ['Tenor', 'Yield', ...comparisons.map(c => changeColumnLabel(c.period, c.compDate))];

    const rows = data.tenors
        .filter(t => latestObs[t] !== undefined)
        .map(t => {
            const val = latestObs[t];
            const cells = [{ text: t }, { text: `${val.toFixed(2)}${suffix}` }];
            comparisons.forEach(c => {
                const prev = c.obs[t];
                cells.push(prev === undefined ? { text: '—' } : bpChange(val - prev, theme));
            });
            return cells;
        });

    return { columns, rows };
}

// Pure: the full historical wide dump, independent of anything toggled on
// screen — one row per date present anywhere in the data, oldest first.
export function csv(ctx) {
    const { data } = ctx;
    const tenors = data.tenors;
    const dates = sortedDates(data);
    const header = ['date', ...tenors].join(',');
    const rows = dates.map(d => {
        const obs = data.observations[d];
        return [d, ...tenors.map(t => (obs[t] !== undefined ? obs[t] : ''))].join(',');
    });
    return [header, ...rows].join('\n');
}
