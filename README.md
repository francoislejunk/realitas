# Realitas Neo

Imported source baseline for Realitas, the vessel-based AI reality simulator.

## Current baseline status

This branch is a preservation/import baseline, not a production-ready deployment cut.

- Runtime: Python
- Dependencies: `requirements.txt`
- First CI gate: import/syntax smoke via `test_imports_quick.py`
- Local secrets must live in `.env` and are intentionally ignored by git.

## Local smoke test

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pytest
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python -m pytest test_imports_quick.py
```

## Engineering direction

Before treating this as deployable, the next slices should reduce the giant imported baseline into explicit contracts:

1. Stable local smoke/CI gate.
2. Entry-point map and runtime dependency audit.
3. Environment variable contract with `.env.example`.
4. VPS deployment path only after the runtime path is proven locally.
