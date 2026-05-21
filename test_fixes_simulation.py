"""
Test script to verify all 8 bug fixes in the simulation.
This script loads session 1 (Elias Thorne) and runs test actions.
"""

import sys
import os

# Set working directory
os.chdir(r"C:\Users\darre\OneDrive\Desktop\Realitas Neo")

# Add project to path
sys.path.insert(0, os.getcwd())

# Import necessary modules
from MAIN.redesigned_main import main
from io import StringIO

# Create a mock input stream to automate session selection
class AutoInput:
    def __init__(self, inputs):
        self.inputs = iter(inputs)

    def __call__(self, prompt=''):
        print(prompt, end='')
        try:
            value = next(self.inputs)
            print(value)  # Echo the input
            return value
        except StopIteration:
            print("quit")  # Exit gracefully when inputs exhausted
            return "quit"

if __name__ == "__main__":
    print("="*80)
    print("BUG FIX VERIFICATION TEST")
    print("="*80)
    print()
    print("Testing 8 fixes:")
    print("  1. Obstacle stability (no movement)")
    print("  2. NPC name persistence")
    print("  3. Background actions working")
    print("  4. Map/terminal display sync")
    print("  5. UTAS calculations visible")
    print("  6. Single movement call")
    print("  7. Movement narration present")
    print("  8. Clear trail display")
    print()
    print("Loading session 1: Elias Thorne - Technician EmpCog")
    print("="*80)
    print()

    # Automated inputs for testing
    test_inputs = [
        "1",  # Select session 1 (Elias Thorne)
        "look",  # Look at the scene
        "I head to the technician workbench",  # Test movement
        "examine the workbench",  # Test interaction after movement
        "quit"  # Exit simulation
    ]

    # Replace built-in input with our automated version
    original_input = __builtins__.input
    __builtins__.input = AutoInput(test_inputs)

    try:
        main()
    except (EOFError, KeyboardInterrupt):
        print("\n\nTest completed or interrupted.")
    except Exception as e:
        print(f"\n\nError during test: {e}")
        import traceback
        traceback.print_exc()
    finally:
        # Restore original input
        __builtins__.input = original_input

    print("\n" + "="*80)
    print("TEST COMPLETE")
    print("="*80)
    print()
    print("Review the output above for:")
    print("  ✓ Obstacles staying in place")
    print("  ✓ Consistent NPC names")
    print("  ✓ Background action logs")
    print("  ✓ NPC names (not occupations) in display")
    print("  ✓ UTAS calculation breakdowns (not N/A)")
    print("  ✓ Single movement log (no duplicate 0m moves)")
    print("  ✓ Movement mentioned in narration")
    print("  ✓ Clear trail progression logs")
