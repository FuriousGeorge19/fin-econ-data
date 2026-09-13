## Context

`site/index.html` (1562 lines) renders four Plotly charts, one per top-level tab. Six
colour tokens exist in `:root`, all dark-mode values; roughly 60 additional colour
literals are hard-coded inside the inline `<script>`'s Plotly `layout` objects, plus a
handful in CSS rules. No `prefers-color-scheme` query, `data-theme` attribute, or
toggle exists anywhere in the file (confirmed by grep). `site/css/` and `site/js/` do
not exist yet — S6a/S6b will create them; until then all code stays inline in
`site/index.html`.

Full literal inventory, verified against the file:

| Role | Dark value | Where |
|---|---|---|
| `--bg`/`--surface`/`--border`/`--text`/`--text-muted`/`--accent` | `#0f172a`/`#1e293b`/`#334155`/`#e2e8f0`/`#94a3b8`/`#38bdf8` | `:root`, CSS only |
| Chart trace 1 | `#38bdf8` | DGS10 line; yield-curve current curve; spreads 10y2y line |
| Chart trace 2 | `#a78bfa` | P/E confirmed line; spreads 10y3m line; yield-curve `1m` overlay |
| Chart trace 3 | `#fb923c` | P/E estimated segment; yield-curve `1y` overlay (also, separately, `.badge`/`.est-badge`/`.about-note` CSS text) |
| Chart trace 4 | `#f472b6` | yield-curve `custom` overlay |
| Axis/grid font | `#94a3b8` | every chart's `font.color`, rangeselector font |
| Gridline | `#1e293b` | every chart's `gridcolor`, rangeselector `bgcolor` |
| Axis line | `#334155` | every chart's `linecolor`, rangeselector `activecolor`, yield-curve legend `bordercolor` |
| Annotation / zero-line | `#64748b` | `asOfAnnotation`'s font color; spreads `zerolinecolor` |
| Up / down | `#4ade80` / `#f87171` | `renderStats`, `renderTable`, `renderYCTable`'s and `renderSpreadsTable`'s `fmtChange` |
| Recession fill | `rgba(148,163,184,0.18)` | `addRecessionBands` shape `fillcolor` |
| Legend background | `rgba(30,41,59,0.8)` | yield-curve legend only; the other three charts use `transparent` |

The `s5-chart-components` design doc fixes the token *names* (decision 5, "Theme
tokens") and says dark mode should not be redesigned: "Should S6b ever run first, it
creates the names with today's hex values and S5b re-values them; names never change."
It also names `site/js/lib/theme.js` — which "reads them into `ctx.theme`" — as an S6b
deliverable, so this session does not create that file; it adds the equivalent inline
`getTheme()` to today's script block, explicitly as scaffolding for S6b to absorb.

## Goals / Non-Goals

**Goals:**
- Every one of the 20 required tokens (6 existing + 14 new) gets a value in both a
  light and a dark palette.
- Dark mode is pixel-identical before and after this change.
- A working toggle, defaulting to system preference, persisting an explicit choice.
- Leave `site/css/tokens.css` in the shape `s5-chart-components` task 4.1 expects to
  find it ("values from `site/css/tokens.css` if S5b has landed").

**Non-Goals:**
- Building `site/js/lib/theme.js` itself, the generator, or any chart-type module
  (S6a/S6b).
- A `--warning` token, or tokenizing the `.badge`/`.est-badge`/`.about-note` literal —
  out of scope; avoid scope creep past the required token list.
- Any Python, data or workflow change.
- Redesigning dark mode's actual colours.

## Decisions

**D1. Dark-mode values are an extraction, not a redesign.**

| Token | Dark value | Source |
|---|---|---|
| `--series-1` | `#38bdf8` | today's DGS10/yield-curve-current/spreads-10y2y colour |
| `--series-2` | `#a78bfa` | today's P/E/spreads-10y3m/`1m`-overlay colour |
| `--series-3` | `#fb923c` | today's P/E-estimated/`1y`-overlay colour |
| `--series-4` | `#f472b6` | today's `custom`-overlay colour |
| `--gridline` | `#1e293b` | == today's `--surface`, reused as `gridcolor` |
| `--axis-line` | `#334155` | == today's `--border`, reused as `linecolor` |
| `--zero-line` / `--annotation` | `#64748b` | today's one shared gray, two role names |
| `--up` / `--down` | `#4ade80` / `#f87171` | today's shared green/red pair |
| `--recession-fill` | `rgba(148,163,184,0.18)` | == `--text-muted` @ 18% |
| `--legend-bg` | `rgba(30,41,59,0.8)` | == `--surface` @ 80% |
| existing six | unchanged | |

The yield curve's `OVERLAY_COLORS` has six slots, not four: `1w` uses `#94a3b8`
(coincides with `--text-muted`) and `5y` uses `#4ade80` (coincides with `--up`), by
accident of shared hex, not because they are genuine series colours. To keep dark mode
byte-identical they map to `theme.textMuted`/`theme.up` at redraw time, **not** to the
new `--series-5`/`--series-6` (different hex, which would change dark mode's
appearance).

**D2. Light-mode values and two new series slots sourced from the dataviz skill's
validated palette, not picked by eye.**

The skill's `references/palette.md` publishes a dual-mode default palette already
checked for CVD separation and WCAG contrast per mode, with a runnable validator
(`scripts/validate_palette.js`/`.py`). Reusing it is cheaper and more defensible than
inventing new values with no check. `--series-1..4` stay pinned to today's dark hex
family (D1); `--series-5`/`--series-6` (new, nothing today uses a 5th/6th trace colour)
and the light-mode counterpart of every token take the skill's values or its
OKLCH-lightness-rebanding method (independent per-mode placement, not a mirror).

Final value table (all 20 tokens):

| Token | Dark (unchanged) | Light (new) | Note |
|---|---|---|---|
| `--bg` | `#0f172a` | `#f1f5f9` | slate-100 |
| `--surface` | `#1e293b` | `#ffffff` | |
| `--border` | `#334155` | `#cbd5e1` | slate-300 |
| `--text` | `#e2e8f0` | `#0f172a` | |
| `--text-muted` | `#94a3b8` | `#64748b` | ≈4.76:1 on white |
| `--accent` | `#38bdf8` | `#0369a1` | dark's sky-400 is ~1.8:1 on white — unusable; sky-700 clears AA (~6.3:1) |
| `--series-1` | `#38bdf8` | `#0284c7` | same hue family, darkened for contrast |
| `--series-2` | `#a78bfa` | `#7c3aed` | |
| `--series-3` | `#fb923c` | `#ea580c` | |
| `--series-4` | `#f472b6` | `#db2777` | |
| `--series-5` (new) | `#199e70` | `#1baf7a` | dataviz skill categorical "aqua" |
| `--series-6` (new) | `#dc2626` | `#991b1b` | not the skill's stock "yellow" slot — see D2's validator note |
| `--gridline` | `#1e293b` (== `--surface`) | `#ffffff` (== `--surface`) | gridlines invisible by design, carried forward |
| `--axis-line` | `#334155` (== `--border`) | `#cbd5e1` (== `--border`) | |
| `--zero-line` / `--annotation` | `#64748b` | `#94a3b8` | one step quieter than `--text-muted`, each mode's own direction |
| `--up` | `#4ade80` | `#15803d` | dark's green-400 is ~1.8:1 on white — unusable; green-700 clears AA |
| `--down` | `#f87171` | `#dc2626` | ≈4.8:1 on white |
| `--recession-fill` | `rgba(148,163,184,0.18)` | `rgba(100,116,139,0.10)` | skill's wash convention is an 8–12% alpha band; 18% on white reads too heavy |
| `--legend-bg` | `rgba(30,41,59,0.8)` | `rgba(255,255,255,0.8)` | same derivation as dark (`--surface` @ 80%) |

*Alternative considered — derive light mode by mechanically inverting dark's hex
values:* rejected. The skill's own method note is that each mode needs independent
OKLCH-lightness-band placement; a straight invert of a mid-lightness dark hue routinely
misses the light band's contrast floor on a near-white surface (verified against dark's
own `--accent`/`--up`, both under 2:1 on white unmodified).

**Validator run** (`node scripts/validate_palette.js "<6 hex>" --mode <light|dark>
--surface <hex> --pairs all`, run against this site's own surfaces, `#ffffff`/`#1e293b`,
not the skill's reference surfaces):
- Light 6-set (`#0284c7,#7c3aed,#ea580c,#db2777,#1baf7a,#991b1b`): **ALL CHECKS PASS**
  (two non-blocking WARNs — CVD 6.6 on the aqua/pink pair, and aqua's own 2.82:1
  contrast — both satisfied by relief already present: every chart has hover labels and
  a Table sub-tab).
- Dark 6-set (`#38bdf8,#a78bfa,#fb923c,#f472b6,#199e70,#dc2626`): **FAILS** lightness
  band and CVD separation, both on the frozen `#a78bfa`↔`#38bdf8` pair — pre-existing in
  today's site (confirmed by running the frozen four alone, same two failures, same
  values) and out of scope to fix under D1. The normal-vision floor **PASSES** at 15.8,
  identical to the frozen-four-alone baseline, confirming `--series-5`/`--series-6`
  introduce no *new* failure.
- The skill's own stock "yellow" slot (`#c98500`/`#eda100`) was tried first for
  `--series-6` and **failed** the normal-vision floor against the frozen `#fb923c`
  orange (ΔE 10.0, dark; a genuinely new problem, unlike the pre-existing ones above) —
  discarded per D2, replaced with a red (`#dc2626`/`#991b1b`) after testing several
  candidates.

**D3. Toggle: two explicit states, system-default on first visit, `data-theme` +
`localStorage`.**

Pattern deliberately borrowed from this environment's own Artifact theming convention
(explicit `data-theme="light"`/`"dark"` stamps override; unset means follow
`prefers-color-scheme`), for consistency with a pattern already familiar. A synchronous
anti-FOUC script in `<head>`, before the Plotly CDN tag, stamps `data-theme` from
`localStorage` before first paint so a returning visitor's choice never flashes wrong.

*Alternative considered — three-state Light/Dark/System cycle:* more complete in the
abstract, but adds a third UI state and an explicit "System" label for what is, in
practice, one user's own site. Two states already cover "system" implicitly (the media
query governs until the button is first clicked). Rejected as unneeded complexity for
the audience.

**D4. `getTheme()` inline, not a new `theme.js` — explicitly provisional.**

`site/js/lib/theme.js` is named as an S6b deliverable in `s5-chart-components`
tasks.md (4.2, "reads the tokens into `ctx.theme`"); creating it now would build on a
module structure (`site/js/lib/`) that doesn't exist and would need rework at S6b
regardless. Instead `getTheme()` lives in today's script block, reading all 20 custom
properties via `getComputedStyle(document.documentElement)`. A code comment marks it
for S6b to lift near-verbatim. This satisfies `s5-chart-components` design.md's own
framing: "on a `themechange` event, `destroy()` then `render()` (S5b's hook — no
contract change needed)."

**D5. `themechange` redraw goes through `renderWhenVisible`, not a direct
`Plotly.newPlot`.**

Calling `Plotly.newPlot` directly into a hidden tab on toggle would reproduce the S4c
700px-fallback bug (Plotly sizes a hidden container to a fallback width and remembers
it). The existing `renderWhenVisible`/`pendingRender`/`onTabShown` machinery (added in
S4c) already encodes the right rule — redraw now if visible, otherwise queue for next
show — so the redraw handler reuses it rather than adding a second, competing
visibility rule.

*Accepted cost:* a redraw drops the user's current zoom/pan/preset selection.
`s5-chart-components` design.md already accepts this same tradeoff for the future
`card.js` ("themechange re-render drops the user's zoom… accepted; the toggle is rare
and the alternative couples `card.js` to every type's internals") — same reasoning
applies here.

**D6. `--legend-bg` applies only where a legend background is already drawn today (the
yield curve); the other three charts' `transparent` legend backgrounds are untouched.**

Per this repo's "don't add it unasked" convention (CLAUDE.md Chart Conventions) —
adding legend chrome to three charts that don't have it today would be a separate,
unasked design change.

**D7. `--up`/`--down` also retone `renderStats`/`renderTable`/`renderYCTable`/
`renderSpreadsTable`, not just the chart-drawing functions.**

These four helpers hardcode the same red/green literals as inline styles, independent
of the Plotly layouts. Dark's `#4ade80`/`#f87171` pair is ~1.8:1 contrast on white —
leaving them frozen at whichever theme was active on page load would make light mode's
up/down text nearly invisible after a toggle. Included in scope for that reason, even
though `s5-chart-components`'s token list frames this as a chart-chrome concern.

## Risks / Trade-offs

- **`Plotly.newPlot` into a hidden tab on `themechange` reproduces the S4c
  700px-fallback bug** if the redraw path doesn't route through `renderWhenVisible`. →
  Mitigated by D5.
- **`nav button` selector regression**: today's tab-click handler
  (`document.querySelectorAll('nav button')`, no filter) would treat a naively-added
  toggle button as a tab. → Narrowed to `nav button[data-tab]`.
- **Partial theming**: `--up`/`--down` are pointless if the four stat/table helpers
  aren't also retoned and rerun on `themechange`. → D7.
- **FOUC** (flash of the wrong theme for a returning visitor) if the `localStorage`
  read happens in the bottom script instead of a synchronous head script run before
  first paint. → Anti-FOUC script, D3.
- **Transparent Plotly `paper_bgcolor`/`plot_bgcolor`** rely on the page/card
  background showing through; since that's pure CSS cascade with no JS involvement and
  `--surface` retones automatically via `tokens.css`, this should continue to work
  unmodified in light mode — verified visually, not assumed.
- **`--series-1..4` (frozen, today's literals) fail the validator's lightness-band and
  CVD-separation checks in dark mode**, confirmed pre-existing (same failures with only
  those four hexes present) and out of scope to fix without redesigning dark mode. →
  Accepted; not a regression, and normal-vision separation still passes.
- **`--series-5`/`--series-6` tested as a combined set** with the four frozen dark
  values, not chosen by eye. → Validator run recorded in D2; the skill's stock "yellow"
  slot introduced a genuine new normal-vision-floor failure against frozen orange and
  was discarded for a red that doesn't.
- **Cosmetic, deliberately accepted**: `tr:hover { background: rgba(56,189,248,0.05) }`
  is a literal derived from dark's `--accent` RGB and is not retoned for light (out of
  scope, avoids scope creep past the required token list); it still reads as a
  plausible subtle hover tint in light mode, just not an exact hue match.
- No workflow change — ships through the normal deploy; rollback is a revert of the one
  commit, same as S4c.

## Migration Plan

One commit to `main` (OpenSpec scaffold + `tokens.css` + `index.html` retoning +
docs), then `gh workflow run update-data.yml` (the cron is weekday-only). Rollback:
revert the commit. No data or schema migration.

## Open Questions (handed to S6b, not blocking)

1. Whether `getTheme()`'s inline form is lifted verbatim into `site/js/lib/theme.js`
   or rewritten against the eventual `ctx` object shape — S6b decides.
2. Whether `--series-5`/`--series-6`'s chosen slots still hold once `s5-chart-components`
   ships enough concurrent-series charts (Fed Funds, real rate, credit spreads, ERP) to
   actually exercise a 5th/6th simultaneous trace and the validator's `--pairs all`
   check.
