---
name: wrap-up
description: End-of-session docs pass for fin-econ-data — route what the session learned to the right file (CHANGELOG, nested CLAUDE.md, ARCHITECTURE, HOW-IT-WORKS, catalog), write the Obsidian handoff and Session Plan row, run the doc guards, commit. Use when the user says a session is done, asks to wrap up, hand off, or record the session, or before declaring work on this repo finished.
---

Close out the session so the next one can start from the docs alone. Work the checklist in
order; skip a step that has nothing to write and say so. Never append to the root `CLAUDE.md`
by default — the routing table below is the rule.

## 0. Establish what happened

From the conversation and `git log --oneline main@{upstream}..HEAD` plus `git status`: what
shipped, which commits, which decisions the user made, which rules or gotchas were learned,
what was found stale or wrong, what is still open. If the work is not yet committed, commit
it first (no `Co-Authored-By` trailers) so the entry can cite a hash.

## 1. Route each fact (the table from the root `CLAUDE.md`)

| Kind of fact | Destination |
|---|---|
| A rule an agent could break in one edit | the `CLAUDE.md` nearest the files it protects (`series/`, `scripts/`, `site/js/`, `catalog/`, `tests/`); the root only if it spans directories; cite the enforcing test if one exists |
| A decision with rationale | `ARCHITECTURE.md` → Decision Log (or the OpenSpec change's `design.md`); plus a one-line rule in the relevant `CLAUDE.md` if it constrains future edits |
| A licence or terms fact | `catalog/sources/<slug>.json` (`terms`, `notes`, `verified`) + `catalog/research-log.md` entry + `catalog/CLAUDE.md`'s status table if a row changes; `LICENCE_RESTRICTED` in `tests/test_build_site.py` if publishability changes |
| A gotcha (port, CDN lag, a flaky test, a browser trick) | `HOW-IT-WORKS.md` → Troubleshooting; a one-line imperative in the root only if every session needs it |
| A correction to a stale claim | fix it where it lives; do not add a note saying it was wrong (that is history — step 2) |
| A new series, source or chart type | nothing in docs; `ls` and `python3 scripts/catalog.py report` are the inventory |
| A directory that has acquired three or more rules of its own | a new `<dir>/CLAUDE.md`, added to the root's Map and to `NESTED` in `tests/test_docs.py` |

## 2. CHANGELOG.md — one entry at the top of "Sessions"

`- **YYYY-MM-DD**: <session id>: <what shipped>` — at most ~15 lines: what was built or changed,
the commit hash(es), decisions taken (who decided), anything verified live, what was found and
fixed in passing, and "Details: the <session> handoff." No counts that will drift, no
narrative; the handoff carries that.

## 3. Obsidian (`~/Obsidian/Investing/Finance and Economic Data Website/`)

- `HANDOFF — <D Mon YYYY> (<session>).md`: "Supersedes …", `main` at `<hash>`, pushed/deployed
  or not; What <session> built; Decisions; Found in review; Still open; Next: <session> with
  what to decide at its start. Two screens at most.
- `Session Plan.md`: strike through the session's row and append **Done <date>** with the
  outcome; add any user decision to the "Decisions so far" table; add a bullet under
  "Where things stand" naming the next session.
- Memory (`~/.claude/projects/-Users-joemirza-projects-fin-econ-data/memory/`):
  `obsidian-project-notes.md` gets the new handoff as the read-first entry and the previous
  one demoted to "superseded"; `MEMORY.md`'s index line follows. A new durable fact about the
  user or the project gets its own memory file, not a line in a handoff.

## 4. Guards, then commit and push

```bash
python3 -m pytest tests/test_docs.py -q      # root ≤ 200 lines, no dated bullets, nested files exist
python3 scripts/catalog.py check             # if any catalogue or descriptor file changed
python3 -m pytest -m "not staleness" -q      # if any test, script or descriptor changed
grep -rn "CLAUDE.md's" tests scripts series catalog --include='*.py' --include='*.json' --include='*.sh'   # no pointer to a section that no longer exists
```

Commit the docs pass separately from the session's code (`<session>: record …`), push, and
close with a recap that names the handoff file and the next session.

## What this skill does not do

It does not deploy (`gh workflow run "Update Data"` is a separate, deliberate step), does not
archive an OpenSpec change (`/opsx:archive`), and does not decide anything — a decision the
user has not made goes under "Still open", not into a doc as if settled.
