## 1. Tokens file and cascade

- [x] 1.1 Create `site/css/tokens.css` with the light-default `:root`, the
      `@media (prefers-color-scheme: dark)` block guarded by
      `:not([data-theme="light"])`, and the explicit `:root[data-theme="dark"]` block;
      values per design.md's table. Comment explaining why no explicit
      `[data-theme="light"]` block exists.
- [x] 1.2 Remove the `:root {...}` block from `site/index.html`'s inline `<style>`; add
      `<link rel="stylesheet" href="css/tokens.css">`.
- [x] 1.3 Gate `.yc-date-input::-webkit-calendar-picker-indicator`'s
      `filter: invert(0.7)` to dark only; add a light counterpart. (manual browser check)

## 2. Toggle mechanism

- [x] 2.1 Add the anti-FOUC inline script as the first element in `<head>`.
- [x] 2.2 Add `#theme-toggle` button inside `<nav>` (no `data-tab`); CSS
      `margin-left: auto`, styled like `.export-btn`.
- [x] 2.3 Narrow the tab-click selector from `nav button` to `nav button[data-tab]` so
      the toggle isn't treated as a tab. (manual browser check)
- [x] 2.4 Add `currentTheme()`, `updateToggleLabel()`, `toggleTheme()`; wire the click
      handler; dispatch `themechange` on `document`.

## 3. getTheme() and chart/table wiring

- [x] 3.1 Add `getTheme()`; comment noting it is provisional scaffolding for S6b's
      `site/js/lib/theme.js`.
- [x] 3.2 `asOfAnnotation`/`addRecessionBands` take a `theme` parameter; update all call
      sites.
- [x] 3.3 `renderChart`: retone trace/line/font/grid/axis/rangeselector literals per
      design.md's mapping.
- [x] 3.4 `renderPEChart`: same, both traces; leave `legend.bgcolor: 'transparent'`
      untouched.
- [x] 3.5 `renderYieldCurve`: retone the current-curve colour; rebuild
      `OVERLAY_COLORS` from `theme` at call time (`1w`→`textMuted`,
      `1m`→`seriesColors[1]`, `1y`→`seriesColors[2]`, `5y`→`up`,
      `custom`→`seriesColors[3]`); retone legend bgcolor/bordercolor.
- [x] 3.6 `renderSpreadsChart`: retone both trace colours and `zerolinecolor`; pass
      `theme` to `addRecessionBands`; leave `legend.bgcolor: 'transparent'` untouched.
- [x] 3.7 `renderStats`, `renderTable`, `renderYCTable`'s `fmtChange`,
      `renderSpreadsTable`'s `fmtChange`: retone the up/down inline-style ternaries.
      (manual browser check)

## 4. Live redraw on themechange

- [x] 4.1 Add `dgs10Data`/`peData`/`spreadsData`/`spreadsUsrec` module-level caches, set
      on each successful load.
- [x] 4.2 Add the `themechange` listener; redraw each chart through `renderWhenVisible`;
      unconditionally re-run the four stat/table functions. (manual browser check)

## 5. Verify

- [x] 5.1 Claude in Chrome: fresh load at the OS/browser default — screenshot each of
      the 4 tabs and diff against the pre-S5b live site; zero unintended pixel/colour
      change. (manual browser check)
- [x] 5.2 Toggle Light→Dark→Light: all 4 charts' lines/gridlines/legend/source-line/
      recession band and the stat/table up-down colours change together; switch to a
      tab that was hidden during the toggle and confirm it draws correctly sized (not
      at Plotly's 700px fallback). (manual browser check)
- [x] 5.3 Reload after toggling to Light — Light persists (`localStorage`); a
      fresh/incognito context with no stored preference follows `prefers-color-scheme`;
      zero console errors either way. (manual browser check)
- [x] 5.4 Yield-curve date-picker icon legible in both themes. (manual browser check)
- [x] 5.5 `pytest -m "not staleness"` green (no Python changed; confirms no test
      references `site/index.html`).
- [x] 5.6 Run the dataviz skill's `scripts/validate_palette.js` against the assembled
      light and dark 6-series sets (with `--surface` set to this site's own light/dark
      surface hex); if `--series-5`/`--series-6` FAIL, pick another slot pair from the
      skill's categorical table — `--series-1..4` are frozen and must not move.
- [x] 5.7 `openspec validate s5b-theme-tokens` clean.
- [x] 5.8 Commit, push, `gh workflow run update-data.yml`, wait for green, re-verify
      5.1's screenshot and 5.2's toggle on http://joemirza.com. (manual browser check)

## 6. Docs

- [x] 6.1 CLAUDE.md: S5b changelog entry; Key Files table gains `site/css/tokens.css`;
      Chart Conventions gains an "Adopted 2026-09-13 (S5b)" bullet.
- [x] 6.2 ARCHITECTURE.md Decision Log entry (S4b/S4c format): token set frozen at
      `s5-chart-components`'s names; dark = extraction; light and
      `--series-5`/`--series-6` sourced from the dataviz skill; provisional
      `getTheme()` to be absorbed by S6b's `theme.js`.

## 7. Validate

- [x] 7.1 `openspec archive s5b-theme-tokens` after 5.8 and 6.1–6.2.
