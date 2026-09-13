## Tasks

- [x] Create `scripts/build_earnings_overrides.py` from the CLAUDE.md heredoc; verify
      it runs against the current `reference_resources/sp-500-eps-est.xlsx` and
      produces the same entries as the committed `data/earnings_overrides.json`
      (only `last_updated`/description text may differ). Verified: 148 entries,
      same latest quarter (2025-09-30, TTM 234.06) as before.
- [x] Update `CLAUDE.md`: series count and tab list match `ls data/`.
- [x] Update `CLAUDE.md`: data-flow description no longer claims the workflow commits
      data back to `main`.
- [x] Add `fetch_spreads.py` / `fetch_usrec.py` rows to the Key Files table and their
      output files.
- [x] Add spreads and USREC changelog entries.
- [x] Replace the inline EPS-regeneration heredoc with a pointer to the new script.
- [x] Add the Chart Conventions section (established + 2026-09-12 additions).
- [x] Add the Licence Notes section.
- [x] Add the Obsidian planning-folder pointer.
- [x] Manual check: read through the edited `CLAUDE.md` once more for internal
      consistency (a human/reviewer pass, not scriptable).
