"""Minimal import/syntax smoke test for the Realitas baseline."""

import os
import sys
from pathlib import Path

if sys.platform == "win32":
    import codecs

    sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))


def test_realitas_import_smoke():
    """Verify the known baseline entry dependencies import/compile."""
    os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
    os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

    import pygame_spatial_map  # noqa: F401
    from agents import background_simulation_system  # noqa: F401

    redesigned_main = PROJECT_ROOT / "MAIN" / "redesigned_main.py"
    compile(redesigned_main.read_text(encoding="utf-8"), str(redesigned_main), "exec")


if __name__ == "__main__":
    print("Testing imports...")
    test_realitas_import_smoke()
    print("OK: pygame_spatial_map")
    print("OK: background_simulation_system")
    print("OK: redesigned_main.py syntax valid")
    print("\nAll imports successful!")
