// Reads the CSS custom properties tokens.css defines into a plain object
// (design.md decision 5's ctx.theme); token names are frozen and re-valued
// per mode by S5b, never read here as literals.
export function getTheme() {
    const cs = getComputedStyle(document.documentElement);
    const v = (name) => cs.getPropertyValue(name).trim();
    return {
        seriesColors: [1, 2, 3, 4, 5, 6].map(n => v(`--series-${n}`)),
        gridline: v('--gridline'),
        axisLine: v('--axis-line'),
        zeroLine: v('--zero-line'),
        annotation: v('--annotation'),
        up: v('--up'),
        down: v('--down'),
        recessionFill: v('--recession-fill'),
        legendBg: v('--legend-bg'),
        bg: v('--bg'),
        surface: v('--surface'),
        border: v('--border'),
        text: v('--text'),
        textMuted: v('--text-muted'),
        accent: v('--accent'),
    };
}

// The one shared "signed, coloured change" formatter (replaces four
// near-identical copies in the pre-S6 single-file dashboard). The colour
// convention is deliberate, not a bug: for a yield/spread series, a value
// going up is coloured theme.down (bad for a bond holder) and a value going
// down is coloured theme.up — established behaviour, preserved as-is.
export function fmtChange(diff, theme, { decimals = 2, suffix = '' } = {}) {
    const sign = diff >= 0 ? '+' : '';
    const color = diff >= 0 ? theme.down : theme.up;
    return { text: `${sign}${diff.toFixed(decimals)}${suffix}`, color };
}
