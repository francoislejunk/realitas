"""
Realitas Neo - Modular Main Entry Point

This orchestrator imports and wires together all modular components
extracted from the original redesigned_main.py.
"""

import sys
import os

# Ensure the project root is in the path (parent of main_modules)
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import all main modules to ensure they're loaded
# The actual functionality is delegated to main_loop.py's main() function
try:
    from main_modules import (
        mention_system,
        visualizer,
        internal_voice,
        ui_display,
        spark_generation,
        reputation_social,
        dialogue,
        location_travel,
        misc,
        main_loop
    )
    print("✓ All main modules imported successfully")
except ImportError as e:
    print(f"✗ Failed to import modules: {e}")
    sys.exit(1)


def main():
    """
    Main entry point - delegates to main_loop.main()
    
    This function serves as the orchestrator that:
    1. Verifies all modules are importable
    2. Delegates execution to the main_loop module
    3. Handles any top-level errors
    """
    try:
        # Run the main simulation loop
        return main_loop.main()
    except KeyboardInterrupt:
        print("\n\n[Simulation interrupted by user]")
        return 0
    except Exception as e:
        print(f"\n\n[Critical Error in main simulation: {e}]")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
