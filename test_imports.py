"""Test script to verify imports from all extracted modules."""

import sys
import os

# Add the project root to path
sys.path.insert(0, r'c:\Users\darre\OneDrive\Desktop\Realitas Neo')

print("=" * 60)
print("TESTING IMPORTS FROM EXTRACTED MODULES")
print("=" * 60)

test_results = {}

# Test main_modules
modules_to_test = [
    'main_modules.mention_system',
    'main_modules.visualizer',
    'main_modules.internal_voice',
    'main_modules.ui_display',
    'main_modules.spark_generation',
    'main_modules.reputation_social',
    'main_modules.dialogue',
    'main_modules.location_travel',
    'main_modules.misc',
]

print("\n--- Testing main_modules ---")
for module in modules_to_test:
    try:
        __import__(module)
        test_results[module] = "✓ PASS"
        print(f"  ✓ {module}")
    except Exception as e:
        test_results[module] = f"✗ FAIL: {str(e)[:50]}"
        print(f"  ✗ {module}: {str(e)[:60]}")

# Test main_loop_chunks
print("\n--- Testing main_loop_chunks ---")
loop_chunks = [
    'main_modules.main_loop_chunks.main_init_start',
    'main_modules.main_loop_chunks.main_init_systems',
    'main_modules.main_loop_chunks.main_scene_setup',
    'main_modules.main_loop_chunks.main_game_loop',
    'main_modules.main_loop_chunks.main_input_handling',
    'main_modules.main_loop_chunks.main_rendering',
]

for module in loop_chunks:
    try:
        __import__(module)
        test_results[module] = "✓ PASS"
        print(f"  ✓ {module}")
    except Exception as e:
        test_results[module] = f"✗ FAIL: {str(e)[:50]}"
        print(f"  ✗ {module}: {str(e)[:60]}")

# Test main_loop (original, may fail due to size/imports)
print("\n--- Testing main_loop.py (original) ---")
try:
    __import__('main_modules.main_loop')
    test_results['main_modules.main_loop'] = "✓ PASS"
    print(f"  ✓ main_modules.main_loop")
except Exception as e:
    test_results['main_modules.main_loop'] = f"✗ FAIL: {str(e)[:50]}"
    print(f"  ✗ main_modules.main_loop: {str(e)[:60]}")

# Summary
print("\n" + "=" * 60)
print("SUMMARY")
print("=" * 60)

passed = sum(1 for v in test_results.values() if v.startswith("✓"))
failed = sum(1 for v in test_results.values() if v.startswith("✗"))

print(f"\nPassed: {passed}/{len(test_results)}")
print(f"Failed: {failed}/{len(test_results)}")

if failed > 0:
    print("\nFailed modules:")
    for module, result in test_results.items():
        if result.startswith("✗"):
            print(f"  - {module}: {result}")

print("\n" + "=" * 60)
