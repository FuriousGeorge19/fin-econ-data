// Placeholder — the real timeseries chart type is S6b (openspec task 4.4),
// not this session (S6a, tasks.md groups 1-3). This file exists only so
// scripts/build_site.py's chart-type existence check passes now that
// series/dgs10.json carries a "timeseries" presentation block; without it
// the generator (and the gating pytest run) would refuse to build. S6b
// replaces this file's contents entirely.
export function render(el, ctx) {
  throw new Error("site/js/charts/timeseries.js: not yet implemented (S6b)");
}
