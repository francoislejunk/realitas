#!/usr/bin/env bash
set -euo pipefail

export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

python -m pytest test_imports_quick.py
