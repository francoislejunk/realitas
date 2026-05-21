import sys
import os
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
print("Testing imports...")
try:
    import pygame_spatial_map
    print("OK: pygame_spatial_map")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
try:
    from agents import background_simulation_system
    print("OK: background_simulation_system")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
try:
    with open("MAIN/redesigned_main.py", "r", encoding="utf-8") as f:
        compile(f.read(), "MAIN/redesigned_main.py", "exec")
    print("OK: redesigned_main.py syntax valid")
except Exception as e:
    print(f"ERROR: {e}")
    sys.exit(1)
print("\nAll imports successful!")
