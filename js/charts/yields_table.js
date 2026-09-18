// Built-in `yields_table` chart type (roadmap item 11). Draws no Plotly chart:
// the "chart" panel holds an HTML grid — instrument type down, maturity
// across, one number per cell — with each row's own as-of date in the last
// column, because the rows update on different schedules (daily Treasury and
// TIPS, monthly corporate).
//
// Payload: { columns: [{id, label, months}], rows: [{id, label, as_of,
// cells: {columnId: {value, date, series_id}}}] }. A cell absent from a row
// is a blank, never an interpolated number. A cell whose own date is older
// than its row's as-of date (one series reporting late) is marked with a dagger.
import { formatDateLong } from '../lib/dates.js';

function escapeHtml(str) {
    return String(str).replace(/[&<>"']/g, ch => ({
        '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;',
    }[ch]));
}

function decimals(ctx) {
    const m = /\.(\d+)f/.exec(((ctx.presentation.chart || {}).y || {}).format || '.2f');
    return m ? Number(m[1]) : 2;
}

function suffix(ctx) {
    return ((ctx.presentation.chart || {}).y || {}).suffix || '';
}

function formatCell(cell, ctx) {
    return `${cell.value.toFixed(decimals(ctx))}${suffix(ctx)}`;
}

// A row's freshness stamp. Monthly rows are stamped with the month they
// describe, not the first-of-month date FRED stores it under.
function rowStamp(row, ctx) {
    const input = ctx.as_of.inputs && ctx.as_of.inputs[row.input];
    if (input && input.period_label) return input.period_label;
    return formatDateLong(row.as_of);
}

function isLate(row, ctx) {
    const input = ctx.as_of.inputs && ctx.as_of.inputs[row.input];
    return !!(input && ctx.today > input.due_by);
}

export function render(el, ctx) {
    const { columns, rows } = ctx.data;
    el.classList.add('chart--html');

    const head = `<tr><th>Instrument</th>${columns.map(c => `<th class="num">${escapeHtml(c.label)}</th>`).join('')}<th>As of</th></tr>`;
    let dagger = false;
    const body = rows.map(row => {
        const cells = columns.map(c => {
            const cell = row.cells[c.id];
            if (!cell) return '<td class="num yields-blank">—</td>';
            const off = cell.date !== row.as_of;
            if (off) dagger = true;
            const title = `${cell.series_id}, ${formatDateLong(cell.date)}`;
            return `<td class="num" title="${escapeHtml(title)}">${escapeHtml(formatCell(cell, ctx))}${off ? '†' : ''}</td>`;
        }).join('');
        const late = isLate(row, ctx);
        return `<tr><th scope="row">${escapeHtml(row.label)}</th>${cells}`
            + `<td class="yields-asof${late ? ' yields-late' : ''}">${escapeHtml(rowStamp(row, ctx))}${late ? ' · overdue' : ''}</td></tr>`;
    }).join('');

    const foot = [
        'Index and constant-maturity averages, not offers: a brokerage’s grid shows its best inventory price, so expect its numbers to differ.',
        dagger ? '† This cell’s series last reported before the rest of its row.' : null,
    ].filter(Boolean).map(t => `<p class="subtitle">${escapeHtml(t)}</p>`).join('');

    el.innerHTML = `<table class="yields-grid"><thead>${head}</thead><tbody>${body}</tbody></table>${foot}`;
    return { destroy() { el.innerHTML = ''; el.classList.remove('chart--html'); } };
}

export function csv(ctx) {
    const { columns, rows } = ctx.data;
    const header = ['instrument', 'as_of', ...columns.map(c => c.id)].join(',');
    const lines = rows.map(row => [
        `"${row.label.replace(/"/g, '""')}"`,
        row.as_of,
        ...columns.map(c => (row.cells[c.id] ? row.cells[c.id].value : '')),
    ].join(','));
    return [header, ...lines].join('\n');
}
