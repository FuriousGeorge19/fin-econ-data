## Context

joemirza.com is a live, working static dashboard with three data series, a daily
GitHub Actions refresh, and a custom domain — but no specs. This change is the first
OpenSpec artifact set for the repo. Its job is purely to write down how the system
behaves today so future changes have a baseline to diff against. There is real risk in
a "document the baseline" change: it can drift into describing how we *wish* the system
worked, or into re-deriving behavior from memory instead of from code. The design below
exists to keep the capture honest and consistently scoped.

## Goals / Non-Goals

**Goals:**
- Capture the running system as a small set of capability specs that match the code,
  scripts, `site/index.html`, and workflow exactly as they exist now.
- Choose a capability granularity that future changes can extend without reshuffling.
- Record known behavioral gaps as explicit requirements/notes rather than silently
  "correcting" them in the spec.

**Non-Goals:**
- No changes to any production code, data, scripts, `site/index.html`, or the workflow.
- No new features, refactors, or bug fixes (the FRED key gap is documented, not fixed).
- Not attempting to spec the *planned* roadmap in `ARCHITECTURE.md` — only what ships today.

## Decisions

- **Six capabilities, split by data-flow role.** One cross-cutting `data-pipeline`
  spec for the shared fetch→JSON→site contract; one spec per data series
  (`treasury-10y-series`, `sp500-pe-series`, `yield-curve-series`); one `dashboard-site`
  for the frontend shell; one `daily-automation` for CI/deploy.
  - *Alternative considered:* a single monolithic "site" spec. Rejected — it would force
    every future series change to touch one giant spec and lose the clean
    one-series-per-spec extension path the architecture was built for.
  - *Alternative considered:* a spec per fetch script *and* a separate spec per chart.
    Rejected as too granular — fetcher and its chart share a contract (the JSON file) and
    read most naturally as one capability.

- **Describe-as-built, sourced from code.** Every requirement is written from the actual
  scripts / HTML / workflow read during this change, not from CLAUDE.md prose. Where
  CLAUDE.md and code disagree, code wins and the discrepancy is noted.

- **Known gaps are first-class.** The missing `FRED_API_KEY` on the P/E workflow step is
  captured as a scenario describing the actual degraded behavior, so a later change can
  reference and close it.

## Risks / Trade-offs

- **Spec drifts from code over time** → Baseline is only useful if kept honest; future
  changes MUST update the relevant spec as part of their delta, which OpenSpec's
  archive flow enforces.
- **Granularity guess is wrong for future series** → If a fourth series needs a shape
  the per-series template doesn't fit, `data-pipeline` is the shared spec to evolve;
  the per-series specs stay independent so the cost of being wrong is localized.
- **Documenting a known bug as "behavior"** → Mitigated by labeling it explicitly as a
  gap/degradation in its scenario, not as desired behavior, so it reads as a TODO not a contract.
