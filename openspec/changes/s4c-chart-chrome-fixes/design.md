## Context

`site/index.html` renders four Plotly charts, one per top-level tab. Only the first tab
is visible at load; the other three tabs are `display:none`. All four charts were drawn
as soon as their fetch resolved. Verified live on 2026-09-13 with Claude in Chrome and
against Plotly 2.35.0's source:

| Symptom | Root cause | Evidence |
|---|---|---|
| "Loading chart…" never goes away | `Plotly.newPlot` inserts `.plot-container` as the *first child* and leaves siblings alone | `.loading` still present in all four chart divs after render |
| P/E, yield curve, spreads render ~700px wide | Drawn while hidden; Plotly sets `_context._hasZeroWidth/_hasZeroHeight` (OR'd, sticky) and uses the 700px fallback | `pe-chart` `_fullLayout.width = 700`, container `clientWidth = 1086`; `Plotly.Plots.resize` while visible corrects it |
| Range slider hides the source line | Annotation at paper y=0, `yshift -30` (325–340px) is exactly where the slider draws (327–355px) | Geometry dump on the 10Y chart |
| "All" shows one month; P/E once ended in 2031 | `allButton()` passed `method`/`args`, which rangeselector buttons ignore → default `step: month, count: 1, backward` from the current axis end. The P/E slider's own extent ran to 2035-10-22 because the estimated trace has markers and Plotly pads marker traces by 5% | `rangeselector.buttons[4] = ['All','month',1,'backward']`; `rangeslider.range[1] = '2035-10-22'` |
| Card reopens on its last sub-tab | Nav switch only toggles `.tab-content` visibility | Nav handler |

Constraints: no build step, vanilla JS, single file (until S5 changes that), Plotly
from the CDN at 2.35.0. S5b will own theming, so no colour or typography changes here.

## Goals / Non-Goals

**Goals:**
- Every chart fills its card on first show, with no leftover placeholder.
- The source line is fully visible on every chart at both chart heights.
- "All", reset and double-click mean the same thing: full history to today.
- A card always opens on its Chart sub-tab.
- Leave S5 with explicit inputs rather than inherited accidents.

**Non-Goals:**
- Theming, preset-row restyling, or moving chart code out of `index.html` (S5/S5b/S6).
- Mobile layout beyond confirming the source line fits at 300px.
- Any Python, data or workflow change.

## Decisions

**D1. Draw a chart the first time its tab is visible; refit on later shows.**
Alternatives: (a) keep drawing eagerly and call `Plotly.Plots.resize` when the tab is
shown — works (verified), but shows the 700px chart for Plotly's 100ms resize debounce
and relies on the sticky hidden-flag being papered over; (b) draw eagerly with an
explicit `layout.width` — breaks `responsive: true`. Chosen: a small page-level
registry (`pendingRender` keyed by tab) that runs the stored render on first activation,
and `Plotly.Plots.resize` on subsequent activations so a resize while hidden is picked
up. Data fetch, stats, tables, badge, About and export wiring stay eager, so the
`dashboard-site` "fetched at load" requirement holds; only the Plotly draw is deferred.

**D2. Loading placeholder via `:empty::before`, not script.**
Alternatives: clear the container before `newPlot`; hide the placeholder in each render.
Chosen: CSS on the empty container. Zero bookkeeping, and it cannot regress when a new
chart is added. The error path still writes into the container, replacing the pseudo
element.

**D3. Pin autorange with `xaxis.autorangeoptions` and use `step: 'all'`.**
Alternatives: (a) a `plotly_relayout` listener that rewrites `autorange: true` into the
explicit range — works but flickers one frame and adds custom code; (b) HTML preset
buttons calling `Plotly.relayout` — full control and themeable, but that is the S5
component question, not a bug fix. Chosen: `{ clipmin: start, clipmax: today, include:
[start, today] }` on the axis, verified in 2.35.0 to make autorange return exactly
`[first_observation, today]`; then `{ step: 'all' }` (which sets `autorange: true`), the
mode bar reset and double-click all land there with no listener.

**D4. Remove the range slider (user decision, 2026-09-13).**
Alternative: keep it and push the source line below it (`yshift -73`, verified to clear
the slider) and raise the chart height ~20px so the plot area does not shrink. Chosen:
remove. The source line is already placed correctly without the slider, the plot area
grows from ~260px to ~320px of a 400px figure, FRED and Bloomberg charts have no slider,
and the slider was also the path by which the P/E axis wandered past today. Cost: no
drag-a-window history overview under the chart; presets, drag-zoom, pan and reset remain.

**D5. Sub-tab reset on activation, not on leaving.**
Selecting `chart` when a tab is shown covers both the returning-user case and the first
show, and is the same helper the sub-tab click handler already uses.

## Risks / Trade-offs

- [Tab activated before its fetch resolves] → `renderWhenVisible` draws immediately when
  the fetch resolves if the tab is visible by then; otherwise it stores the render.
- [Window resized while a tab is hidden] → `onTabShown` calls `Plotly.Plots.resize` on
  an already-drawn chart; Plotly's own resize listener skips hidden charts.
- [Source line touches the figure edge without the slider] → verify by screenshot at
  400px and 300px; raise `margin.b` from 46 if needed. Plotly auto-expands the bottom
  margin for a paper-referenced annotation, so clipping is unlikely.
- [Yield-curve toggles re-run `newPlot`] → unchanged; they can only be clicked while the
  tab is visible.
- [`autorangeoptions` needs Plotly ≥ 2.26] → pinned at 2.35.0 in the `<script>` tag.

## Migration Plan

One commit to `main`, then `gh workflow run update-data.yml` (the cron is weekday-only).
Rollback: revert the commit and re-run the workflow. No data or schema migration.

## Open Questions (handed to S5, not blocking)

1. **When may `render(el, options)` run?** Either the page calls render on first show
   (this change) or the component observes its own container
   (`IntersectionObserver`/`ResizeObserver`). S5 decides; do not inherit by accident.
2. **Is the preset row a component?** Plotly's rangeselector cannot express a custom
   range and its colours are layout literals (collides with S5b tokens). HTML buttons
   calling `Plotly.relayout` are the alternative.
3. **Source-line band rule** for the layout builder: nothing the chart draws may occupy
   the bottom-margin band the source line uses.
4. The `dashboard-site` rule "drawn the first time its tab is visible" is page-level;
   S5's multi-page design keeps it or consciously replaces it.
