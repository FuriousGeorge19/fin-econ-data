// Built-in `decomposition` chart type (roadmap item 14). Draws no Plotly chart:
// an HTML table splitting each tenor's nominal yield change into a real-yield
// change and a breakeven-inflation change (nominal = real + breakeven, all in
// whole basis points, computed by the fetcher — never here). A row of period
// buttons in ctx.slots.controls picks which period the table shows; the
// selection lives in render()'s closure.
//
// Payload: { tenors, latest: {date, levels: {tenor: {nominal, real, breakeven}}},
// periods: [{id, label, ref_date, changes: {tenor: {nominal_bp, real_bp, breakeven_bp}}}] }.
import { formatDateLong } from '../lib/dates.js';
import { fmtChange } from '../lib/theme.js';

const DEFAULT_PERIOD = '1y';

function bpCell(bp, theme) {
    const c = fmtChange(bp, theme, { decimals: 0, suffix: ' bp' });
    return `<td class="num" style="color: ${c.color}">${c.text}</td>`;
}

export function render(el, ctx) {
    const { data, theme } = ctx;
    el.classList.add('chart--html');
    let active = data.periods.some(p => p.id === DEFAULT_PERIOD) ? DEFAULT_PERIOD : data.periods[0].id;

    const wrap = document.createElement('div');
    wrap.className = 'yc-controls';
    const label = document.createElement('label');
    label.textContent = 'Period:';
    wrap.appendChild(label);
    const buttons = data.periods.map(p => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'yc-toggle';
        btn.textContent = p.label;
        btn.addEventListener('click', () => { active = p.id; draw(); });
        wrap.appendChild(btn);
        return { id: p.id, btn };
    });
    ctx.slots.controls.appendChild(wrap);

    function draw() {
        buttons.forEach(b => b.btn.classList.toggle('active', b.id === active));
        const period = data.periods.find(p => p.id === active);
        const head = '<tr><th>Tenor</th><th class="num">Nominal</th><th class="num">Real</th>'
            + '<th class="num">Breakeven</th><th class="num">Nominal change</th>'
            + '<th class="num">= Real change</th><th class="num">+ Breakeven change</th></tr>';
        const body = data.tenors.map(t => {
            const lv = data.latest.levels[t];
            const ch = period.changes[t];
            return `<tr><th scope="row">${t}</th>`
                + `<td class="num">${lv.nominal.toFixed(2)}%</td><td class="num">${lv.real.toFixed(2)}%</td>`
                + `<td class="num">${lv.breakeven.toFixed(2)}%</td>`
                + `${bpCell(ch.nominal_bp, theme)}${bpCell(ch.real_bp, theme)}${bpCell(ch.breakeven_bp, theme)}</tr>`;
        }).join('');
        el.innerHTML = `<p class="subtitle">Change from ${formatDateLong(period.ref_date)} to `
            + `${formatDateLong(data.latest.date)}, in basis points. Breakeven = nominal − real.</p>`
            + `<table class="yields-grid"><thead>${head}</thead><tbody>${body}</tbody></table>`;
    }

    draw();
    return { destroy() { wrap.remove(); el.innerHTML = ''; el.classList.remove('chart--html'); } };
}

// One row per period and tenor, all periods — independent of the selected button.
export function csv(ctx) {
    const { data } = ctx;
    const header = ['period', 'ref_date', 'latest_date', 'tenor', 'nominal_bp', 'real_bp', 'breakeven_bp'].join(',');
    const lines = data.periods.flatMap(p => data.tenors.map(t => {
        const c = p.changes[t];
        return [p.id, p.ref_date, data.latest.date, t, c.nominal_bp, c.real_bp, c.breakeven_bp].join(',');
    }));
    return [header, ...lines].join('\n');
}
