#!/usr/bin/env bash
set -euo pipefail

export SDL_VIDEODRIVER="${SDL_VIDEODRIVER:-dummy}"
export SDL_AUDIODRIVER="${SDL_AUDIODRIVER:-dummy}"

python -m pytest test_imports_quick.py test_world_exporter.py test_seed_dev_context.py
node tests/server-contract.test.js
