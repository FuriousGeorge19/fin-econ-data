## REMOVED Requirements

### Requirement: Dark theme and per-tab data loading

**Reason**: The per-tab-fetch content is already covered by the "Data fetched on page
load, not lazily" requirement below (added since this requirement was written). The
dark-theme-only content is no longer true: the dashboard now supports both a light and
a dark theme.

**Migration**: None — nothing depends on this requirement in isolation. See the ADDED
"Light and dark theme, toggle defaults to system preference" requirement below for
current behavior.

## ADDED Requirements

### Requirement: Light and dark theme, toggle defaults to system preference

The dashboard SHALL support a light and a dark theme via CSS custom properties defined
in `site/css/tokens.css`. The active theme SHALL follow the browser's
`prefers-color-scheme` when no explicit choice has been made. A toggle control SHALL
let the user pick Light or Dark explicitly; that choice SHALL be stamped as
`data-theme` on the document root, SHALL override `prefers-color-scheme`, and SHALL
persist across reloads via `localStorage`. Changing the theme SHALL dispatch a
`themechange` event that every themed chart and table listens for.

#### Scenario: System preference on first visit

- **WHEN** the page loads with no stored theme preference
- **THEN** the active theme matches the browser's `prefers-color-scheme`

#### Scenario: Explicit choice persists

- **WHEN** the user selects a theme via the toggle and reloads the page
- **THEN** the same theme is active, regardless of `prefers-color-scheme`

#### Scenario: Explicit choice overrides system preference

- **WHEN** the user's OS is set to dark but they have explicitly selected Light
- **THEN** the page renders in Light
