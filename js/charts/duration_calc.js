// Built-in `duration_calc` chart type (roadmap item 19). Draws no Plotly chart:
// the chart slot holds a small form and a fixed grid. Price change ≈
// −duration × yield change (linear; convexity ignored, and the About tab says
// so). Runs over a view of `yields_table`, whose latest 5-year Treasury cell
// pre-fills the yield field.
//
// All form state lives in the DOM elements this render() creates, never at
// module scope, so two mounts on one page stay independent.
import { fmtChange } from '../lib/theme.js';

const GRID_DURATIONS = [1.9, 4.9, 7, 10, 17];
const GRID_SHIFTS_BP = [-100, -50, 50, 100, 200];

function pct(x, theme, digits = 2) {
    return fmtChange(x, theme, { decimals: digits, suffix: '%' });
}

// A price *rise* is good for a holder, but fmtChange colours a yield-style
// "up" as bad. Price effects invert the sign so the colour still reads as
// good/bad for the holder.
function priceEffect(durationYears, shiftBp, theme) {
    const price = -durationYears * (shiftBp / 100);
    const c = pct(price, theme);
    return { text: c.text, color: price >= 0 ? theme.up : theme.down };
}

function defaultYield(data) {
    const row = (data.rows || []).find(r => r.id === 'treasury');
    const cell = row && row.cells && row.cells['5Y'];
    return cell ? cell.value : 4;
}

export function render(el, ctx) {
    const { theme, data } = ctx;
    el.classList.add('chart--html');

    const y0 = defaultYield(data);
    el.innerHTML = `
        <form class="dur-form" onsubmit="return false">
            <label>Duration (years) <input type="number" class="dur-in" data-k="dur" value="4.9" min="0" max="50" step="0.1"></label>
            <label>Yield (%) <input type="number" class="dur-in" data-k="yld" value="${y0.toFixed(2)}" min="0" max="30" step="0.01"></label>
            <label>Yield change (bp) <input type="number" class="dur-in" data-k="shift" value="100" min="-1000" max="1000" step="10"></label>
        </form>
        <table class="dur-out"><tbody>
            <tr><th scope="row">Approximate price change</th><td class="num" data-o="price"></td></tr>
            <tr><th scope="row">One year of income at this yield</th><td class="num" data-o="income"></td></tr>
            <tr><th scope="row">Price change plus one year of income</th><td class="num" data-o="total"></td></tr>
            <tr><th scope="row">Yield rise that wipes out one year of income</th><td class="num" data-o="breakeven"></td></tr>
        </tbody></table>
        <p class="subtitle">Price change by duration and yield move (linear approximation, convexity ignored). A price fall is shown in the down colour.</p>
        <table class="dur-grid"><thead><tr><th>Duration</th>${
            GRID_SHIFTS_BP.map(s => `<th class="num">${s > 0 ? '+' : ''}${s} bp</th>`).join('')
        }</tr></thead><tbody>${
            GRID_DURATIONS.map(d => `<tr><th scope="row">${d} yr</th>${
                GRID_SHIFTS_BP.map(s => {
                    const c = priceEffect(d, s, theme);
                    return `<td class="num" style="color: ${c.color}">${c.text}</td>`;
                }).join('')
            }</tr>`).join('')
        }</tbody></table>`;

    const input = k => el.querySelector(`[data-k="${k}"]`);
    const out = k => el.querySelector(`[data-o="${k}"]`);

    function update() {
        const dur = parseFloat(input('dur').value);
        const yld = parseFloat(input('yld').value);
        const shift = parseFloat(input('shift').value);
        if (![dur, yld, shift].every(Number.isFinite) || dur < 0) {
            ['price', 'income', 'total', 'breakeven'].forEach(k => { out(k).textContent = '—'; out(k).style.color = ''; });
            return;
        }
        const price = priceEffect(dur, shift, theme);
        out('price').textContent = price.text;
        out('price').style.color = price.color;
        out('income').textContent = `${yld.toFixed(2)}%`;
        const total = -dur * (shift / 100) + yld;
        out('total').textContent = pct(total, theme).text;
        out('total').style.color = total >= 0 ? theme.up : theme.down;
        out('breakeven').textContent = dur > 0 ? `${Math.round((yld / dur) * 100)} bp` : '—';
    }

    el.querySelector('.dur-form').addEventListener('input', update);
    update();

    return { destroy() { el.innerHTML = ''; el.classList.remove('chart--html'); } };
}
