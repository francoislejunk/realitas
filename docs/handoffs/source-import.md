# Realitas Neo Source Import

Source archive: Google Drive file ID `1RkKBbCmZfyvxG39bANkxxtGKoOktAauT` (`Realitas.zip`).

Local staging archive:
`/Users/frankmcalvarez/clawd/realitas-source-import/Realitas.zip`

Archive SHA256:
`8737cdae7c0acc575efc43b1e189a95c49bc2b1b25b45a7882df8ec3a6bfba56`

Extracted project root:
`/Users/frankmcalvarez/clawd/realitas-source-import/extracted/Realitas/Realitas Neo`

## Original internal source git history

The zip contained a nested `.git` repo with no remote. Original commits observed:

```txt
f3969af Fix simulation startup hang caused by mention system LLM calls
e4497cd Add dynamic wake-up narration with personality integration
bfcc522 Add comprehensive Mention System with full agent integration
638675d Add comprehensive Fact System with full Phase 2 integrations
778d3f8 Snapshot: working baseline
```

Branches observed:
- `main`
- `restore-point-snapshot-2026-02-01`

Tag observed:
- `snapshot-working-2026-02-01`

## Import policy

The public GitHub scaffold stays as origin/history. The Drive source is imported as a cleaned baseline on branch `import/realitas-neo-baseline`.

Excluded from import:
- nested `.git`
- `.venv` / local environments
- `.env` and secret-bearing local config
- `__pycache__`, `.pytest_cache`
- logs, sessions, runtime UUID artifact directories
- `simulation_data`, `test_data`
- `TRASH BIN`
- local IDE/workflow files such as `.windsurf`
- source-local `.claude` files, preserving the GitHub scaffold `.claude` rules instead

Preserved from scaffold:
- `.claude/CLAUDE.md`
- `.claude/rules/*`
- `.claude/settings.json`
- `docs/specs`
- `docs/handoffs`
