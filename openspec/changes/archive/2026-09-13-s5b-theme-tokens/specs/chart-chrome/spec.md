## ADDED Requirements

### Requirement: Chart and table colors follow the active theme

Every chart-drawing function and every up/down-colored stat or table cell SHALL read
its colors from the active theme's CSS custom properties (via `getTheme()`), never
from a hard-coded literal. On a `themechange` event, a chart whose tab is visible
SHALL redraw immediately; a chart whose tab is hidden SHALL defer its redraw until the
tab is first shown, so the existing draw-when-visible rule (`dashboard-site`, "Data
fetched on page load, not lazily") is never bypassed. Dark-mode token values SHALL be
unchanged from the values in use before this requirement existed.

#### Scenario: Toggling recolors every chart together

- **WHEN** the user switches the theme
- **THEN** all currently visible charts' lines, gridlines, legend, source line, and
  recession bands, and every stat/table up-down color, update to the new theme's values

#### Scenario: A chart hidden during a toggle draws correctly on next show

- **WHEN** the theme is switched while a tab is hidden and the user then activates that
  tab
- **THEN** its chart draws once, sized to the visible container, never at Plotly's
  700px fallback

#### Scenario: Dark mode is unchanged

- **WHEN** the dashboard loads in dark mode (system preference or explicit choice)
- **THEN** every chart and table renders with the same colors as before this
  requirement existed
