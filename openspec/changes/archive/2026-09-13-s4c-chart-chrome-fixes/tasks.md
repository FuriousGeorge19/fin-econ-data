## 1. Placeholder and sizing (site/index.html)

- [x] 1.1 Remove the four `<div class="loading">Loading chart...</div>` placeholders; add `class="chart"` to `#chart`, `#pe-chart`, `#yc-chart`, `#spreads-chart`; move the width/height rules (desktop and the 640px breakpoint) onto `.chart`; add the `.chart:empty::before` rule. (manual browser check)
- [x] 1.2 Add `TAB_CHART`, `pendingRender`, `isTabVisible`, `renderWhenVisible`, `onTabShown`; route the four chart draws through `renderWhenVisible`; the nav handler calls `onTabShown` after showing the tab. (manual browser check)

## 2. Sub-tabs

- [x] 2.1 Extract `selectSubtab(strip, panel)` from `wireSubtabs`; the nav handler selects `chart` on the shown card before `onTabShown`. (manual browser check)

## 3. Axis range semantics

- [x] 3.1 `xaxisToToday` also sets `autorangeoptions { clipmin, clipmax, include }`; `allButton()` returns `{ step: 'all', label: 'All' }`; update its three call sites. (manual browser check)
- [x] 3.2 Remove `rangeslider` from the 10Y, P/E and spreads layouts; confirm the source line clears the x-axis labels at 400px and 300px heights, raising `margin.b` if it clips. (manual browser check)

## 4. Verify

- [x] 4.1 Local via `scripts/dev.sh` + Claude in Chrome: fresh load; each other tab fills the card on first show; no placeholder text after render; All / reset / double-click ranges on all three time-series charts; resize-while-hidden refit; sub-tab reset; PNG export keeps the source line; mobile width; zero console errors. (manual browser check)
- [x] 4.2 `pytest -m "not staleness"` green (no Python changed; sanity).
- [x] 4.3 Commit, push, `gh workflow run update-data.yml`, wait for green, re-verify 4.1's first three checks on http://joemirza.com. (manual browser check)

## 5. Docs and plan

- [x] 5.1 `CLAUDE.md`: S4c changelog entry; Chart Conventions gains "charts are drawn only when their container is visible", "All / reset = first observation → today", "no range slider on time-series charts".
- [x] 5.2 `ARCHITECTURE.md` Decision Log entry in the S4b entries' format.
- [x] 5.3 Obsidian: `Session Plan.md` (decision row, "Where things stand" S4c bullet, S4c session row between S4 and S5) and a new `HANDOFF — 13 Sep 2026 (S4c).md`; update the memory pointer to the new handoff.
