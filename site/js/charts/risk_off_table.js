// Built-in `risk_off_table` chart type (roadmap item 15). Draws no Plotly chart:
// an HTML table with one row per year (plus the last 120 sessions) of how the
// bond market behaved on days the S&P 500 fell at least 1%. A row of tenor
// buttons in ctx.slots.controls picks which Treasury yield the "yield change"
// and "yield fell" columns describe; the selection lives in render()'s closure.
// The fund and correlation columns do not depend on it.
//
// Payload: { tenors, threshold_pct, fund: {duration_years, tenor},
// rows: [{id, label, sessions, days, avg_sp_fall_pct, fund_move_pct,
// correlation_10yr, by_tenor: {tenor: {avg_change_bp, share_fell_pct}}}] }.
import { fmtChange } from '../lib/theme.js';

const DEFAULT_TENOR = '10yr';

function num(text, color) {
    return `<td class="num"${color ? ` style="color: ${color}"` : ''}>${text}</td>`;
}

export function render(el, ctx) {
    const { data, theme } = ctx;
    el.classList.add('chart--html');
    let active = data.tenors.includes(DEFAULT_TENOR) ? DEFAULT_TENOR : data.tenors[0];

    const wrap = document.createElement('div');
    wrap.className = 'yc-controls';
    const label = document.createElement('label');
    label.textContent = 'Yield:';
    wrap.appendChild(label);
    const buttons = data.tenors.map(t => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'yc-toggle';
        btn.textContent = t;
        btn.addEventListener('click', () => { active = t; draw(); });
        wrap.appendChild(btn);
        return { t, btn };
    });
    ctx.slots.controls.appendChild(wrap);

    function draw() {
        buttons.forEach(b => b.btn.classList.toggle('active', b.t === active));
        const head = `<tr><th>Period</th><th class="num">Bad days</th><th class="num">Avg S&amp;P fall</th>`
            + `<th class="num">Avg ${active} yield change</th><th class="num">${active} yield fell on</th>`
            + `<th class="num">Est. fund price move</th><th class="num">Stock–bond correlation</th></tr>`;
        const body = data.rows.map(r => {
            const t = r.by_tenor[active];
            if (!t) {
                return `<tr><th scope="row">${r.label}</th>${num(r.days)}${num('—')}${num('—')}${num('—')}${num('—')}`
                    + `${num(r.correlation_10yr === null ? '—' : r.correlation_10yr.toFixed(2))}</tr>`;
            }
            const ch = fmtChange(t.avg_change_bp, theme, { decimals: 1, suffix: ' bp' });
            // A fund price rise is good for its holder, the opposite colouring to a yield rise.
            const fundColor = r.fund_move_pct >= 0 ? theme.up : theme.down;
            const fund = `${r.fund_move_pct >= 0 ? '+' : ''}${r.fund_move_pct.toFixed(2)}%`;
            const corrColor = r.correlation_10yr >= 0 ? theme.up : theme.down;
            return `<tr><th scope="row">${r.label}</th>${num(r.days)}`
                + `${num(`${r.avg_sp_fall_pct.toFixed(2)}%`)}${num(ch.text, ch.color)}`
                + `${num(`${t.share_fell_pct}% of days`)}${num(fund, fundColor)}`
                + `${num(r.correlation_10yr.toFixed(2), corrColor)}</tr>`;
        }).join('');
        const foot = [
            `A bad day is one on which the S&P 500 fell at least ${Math.abs(data.threshold_pct)}%. A yield that falls is a bond price that rises: "yield fell on" is the hedge working.`,
            `Est. fund price move = −${data.fund.duration_years} × the average change in the ${data.fund.tenor} yield (an intermediate Treasury fund's duration), independent of the yield picked above.`,
            'Correlation: S&P daily return against the daily change in the 10yr yield, all sessions in the period. Positive = bond prices rise on bad stock days (hedge working); negative = they fall.',
        ].map(t => `<p class="subtitle">${t}</p>`).join('');
        el.innerHTML = `<table class="yields-grid"><thead>${head}</thead><tbody>${body}</tbody></table>${foot}`;
    }

    draw();
    return { destroy() { wrap.remove(); el.innerHTML = ''; el.classList.remove('chart--html'); } };
}

// Every period and tenor, independent of the selected button.
export function csv(ctx) {
    const { data } = ctx;
    const header = ['period', 'sessions', 'bad_days', 'avg_sp_fall_pct', 'tenor', 'avg_yield_change_bp',
        'share_yield_fell_pct', 'fund_move_pct', 'correlation_10yr'].join(',');
    const lines = data.rows.flatMap(r => Object.keys(r.by_tenor).map(t => [
        `"${r.label}"`, r.sessions, r.days, r.avg_sp_fall_pct, t, r.by_tenor[t].avg_change_bp,
        r.by_tenor[t].share_fell_pct, r.fund_move_pct, r.correlation_10yr === null ? '' : r.correlation_10yr,
    ].join(',')));
    return [header, ...lines].join('\n');
}
