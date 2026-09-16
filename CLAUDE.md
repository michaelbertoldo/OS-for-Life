# LifeOS (repo)

Full spec: `docs/SPEC.md`. Current status and task ledger: `PROGRESS.md` — read it first, every session.

This is the sync-engine repo, not the vault. The vault lives separately (default `~/LifeOS`).

## Lessons

- 2026-09-16 | Obsidian's Bases YAML doesn't document a `sort` key in the official schema (only `groupBy` and column `order` are shown) | followed the `groupBy` {property, direction} shape as the closest documented pattern for `sort`, flagged it in PROGRESS.md -> Decisions to verify against the Sort menu once real data loads.
- 2026-09-16 | `uv run pytest` / `uv run lifeos ...` intermittently fails with `ModuleNotFoundError: No module named 'lifeos'` even though the editable install is present | root cause not fully isolated (the `.venv` python is a symlink into a conda install, which is unusual); `uv sync --reinstall-package lifeos` fixes it every time. If imports break for no code reason, run that before debugging further.
