// Built-in `drawdown_shift` chart type (roadmap item 17). A bar chart of how
// each Treasury yield changed between an S&P 500 peak and its trough, in basis
// points, for a drawdown window picked from a row of buttons in
// ctx.slots.controls (newest first). A bar above zero is a yield that rose
// while stocks fell — a bond that lost money. The selection lives in
// render()'s closure; redraws use Plotly.react.
//
// Payload: { tenors, min_drawdown_pct, windows: [{peak_date, trough_date,
// sp_change_pct, ongoing, changes_bp: {tenor: bp}}] }.
import { formatDateLong } from '../lib/dates.js';
import { baseLayout, PLOT_CONFIG } from '../lib/plotly-layout.js';

// "Jan 2026 (−9.1%)": the peak's month and the S&P's fall.
function windowLabel(w) {
    return `${formatDateLong(w.peak_date).slice(3)} (${w.sp_change_pct.toFixed(1)}%)`;
}

export function render(el, ctx) {
    const { data, theme, today } = ctx;
    let active = 0;

    function buildTrace() {
        const w = data.windows[active];
        const tenors = data.tenors.filter(t => w.changes_bp[t] !== undefined);
        const y = tenors.map(t => w.changes_bp[t]);
        return {
            type: 'bar',
            x: tenors,
            y,
            // A yield that rose lost bond holders money: the "down" colour.
            marker: { color: y.map(v => (v > 0 ? theme.down : theme.up)) },
            text: y.map(v => `${v > 0 ? '+' : ''}${v}`),
            textposition: 'outside',
            cliponaxis: false,
            hovertemplate: `%{x}: %{text} bp<extra></extra>`,
        };
    }

    function buildLayout() {
        const w = data.windows[active];
        const layout = baseLayout(ctx, { startISO: today });
        layout.xaxis = {
            type: 'category',
            categoryorder: 'array',
            categoryarray: data.tenors,
            gridcolor: theme.gridline,
            linecolor: theme.axisLine,
        };
        layout.yaxis = {
            gridcolor: theme.gridline, linecolor: theme.axisLine, ticksuffix: ' bp',
            zeroline: true, zerolinecolor: theme.zeroLine,
        };
        layout.title = {
            text: `S&P 500 ${w.sp_change_pct.toFixed(1)}%, ${formatDateLong(w.peak_date)} to ${formatDateLong(w.trough_date)}`
                + `${w.ongoing ? ' (ongoing)' : ''}`,
            font: { size: 13, color: theme.textMuted },
        };
        return layout;
    }

    const wrap = document.createElement('div');
    wrap.className = 'yc-controls';
    const label = document.createElement('label');
    label.textContent = 'Drawdown:';
    wrap.appendChild(label);
    const buttons = data.windows.map((w, i) => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'yc-toggle';
        btn.textContent = windowLabel(w);
        btn.addEventListener('click', () => { active = i; draw(); });
        wrap.appendChild(btn);
        return btn;
    });
    ctx.slots.controls.appendChild(wrap);

    function draw() {
        buttons.forEach((b, i) => b.classList.toggle('active', i === active));
        Plotly.react(el, [buildTrace()], buildLayout(), PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));
    }

    buttons[0].classList.add('active');
    Plotly.newPlot(el, [buildTrace()], buildLayout(), PLOT_CONFIG(`${ctx.id}_${ctx.as_of.last_observation}`));
    return { destroy() { wrap.remove(); Plotly.purge(el); } };
}

export function csv(ctx) {
    const { data } = ctx;
    const header = ['peak_date', 'trough_date', 'sp_change_pct', ...data.tenors.map(t => `${t}_bp`)].join(',');
    const lines = data.windows.map(w => [w.peak_date, w.trough_date, w.sp_change_pct,
        ...data.tenors.map(t => (w.changes_bp[t] === undefined ? '' : w.changes_bp[t]))].join(','));
    return [header, ...lines].join('\n');
}
