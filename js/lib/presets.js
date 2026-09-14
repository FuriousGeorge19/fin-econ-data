import { addMonthsUTC, addYearsUTC } from './dates.js';

function presetRange(preset, today) {
    if (preset === 'All') return null; // signal: xaxis.autorange
    if (preset === 'YTD') return [`${today.slice(0, 4)}-01-01`, today];
    const m = /^(\d+)([MY])$/.exec(preset);
    if (!m) throw new Error(`unknown preset: ${preset}`);
    const n = Number(m[1]);
    const start = m[2] === 'M' ? addMonthsUTC(today, -n) : addYearsUTC(today, -n);
    return [start, today];
}

// Renders presentation.chart.presets as buttons into `container` (the
// card's control row) and wires them to Plotly.relayout on `gd`. Active
// state follows plotly_relayout; a drag-zoom (which this module did not
// itself trigger) clears every button, per the "Preset row as HTML
// buttons" requirement.
export function mountPresets(container, { presets, gd, today, initialPreset }) {
    if (!presets || !presets.length) return null;

    const buttons = [];
    let ownRelayout = false;

    function setActive(preset) {
        buttons.forEach(b => b.classList.toggle('active', b.dataset.preset === preset));
    }

    function applyInitial(preset) {
        const range = presetRange(preset, today);
        ownRelayout = true;
        Plotly.relayout(gd, range
            ? { 'xaxis.range': range, 'xaxis.autorange': false }
            : { 'xaxis.autorange': true });
        setActive(preset);
    }

    presets.forEach(preset => {
        const btn = document.createElement('button');
        btn.type = 'button';
        btn.className = 'preset-btn';
        btn.textContent = preset;
        btn.dataset.preset = preset;
        btn.addEventListener('click', () => applyInitial(preset));
        container.appendChild(btn);
        buttons.push(btn);
    });

    gd.on('plotly_relayout', () => {
        if (ownRelayout) {
            ownRelayout = false;
            return;
        }
        setActive(null);
    });

    if (initialPreset) applyInitial(initialPreset);

    return { applyInitial };
}
