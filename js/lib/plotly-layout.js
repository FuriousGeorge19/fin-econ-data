// The only file under site/js that sets Plotly margin, legend position,
// rangeslider or a chart height (chart-components spec, "One layout builder
// owns margins, legends and the band"). A chart's actual CSS height is set
// per size variant in site/css/site.css, never here or in a type module.
import { asOfAnnotation } from './asof.js';

export const PLOT_CONFIG_BASE = {
    responsive: true,
    displayModeBar: true,
    displaylogo: false,
    modeBarButtonsToRemove: ['lasso2d', 'select2d'],
};

export function PLOT_CONFIG(filenameBase) {
    return {
        ...PLOT_CONFIG_BASE,
        toImageButtonOptions: { format: 'png', filename: filenameBase },
    };
}

// The range is explicit, and autorange is clipped to the same window so that
// the "All" preset, the mode bar's reset-axes button and a double-click all
// land on [first observation, today] rather than Plotly's padded data extent
// (chart-chrome spec, "Time-series x-axis ends at today").
export function xaxisToToday(xaxis, startISO, todayISO) {
    xaxis.range = [startISO, todayISO];
    xaxis.autorange = false;
    xaxis.autorangeoptions = { clipmin: startISO, clipmax: todayISO, include: [startISO, todayISO] };
    return xaxis;
}

// Base chrome shared by every time-series-shaped chart: transparent paper,
// axis/grid/font colours from ctx.theme, the source-line annotation with its
// reserved bottom margin, and a legend Plotly only shows once there is more
// than one trace. Types layer their own yaxis suffix/zeroline/shapes on top
// of the returned object.
export function baseLayout(ctx, { startISO }) {
    const { theme, meta, as_of, today } = ctx;
    return {
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        font: { color: theme.textMuted, size: 12 },
        margin: { t: 10, r: 20, b: 56, l: 50 },
        legend: { font: { color: theme.textMuted }, bgcolor: 'transparent' },
        annotations: [asOfAnnotation(meta, as_of, theme)],
        xaxis: xaxisToToday(
            { gridcolor: theme.gridline, linecolor: theme.axisLine },
            startISO,
            today,
        ),
        yaxis: { gridcolor: theme.gridline, linecolor: theme.axisLine },
    };
}
