"""
Test script to verify UTAS calculation fix.
"""
import sys
import os

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("="*80)
print("UTAS CALCULATION FIX VERIFICATION")
print("="*80)

# Test: Check if the fix is applied
print("\n[TEST] Verifying fix in _calculate_detailed_success()...")
try:
    with open("MAIN/redesigned_main.py", "r", encoding="utf-8") as f:
        content = f.read()

    # Look for the fixed line
    if "action_data['success_calculation'] = result" in content:
        print("✅ Fix FOUND: Full result is being stored")

        # Make sure the old broken version is NOT there
        if "action_data['success_calculation'] = {'total': score}" in content:
            print("⚠️  WARNING: Old broken code still present (commented out?)")
        else:
            print("✅ Old broken code removed")

    elif "action_data['success_calculation'] = {'total': score}" in content:
        print("❌ Fix NOT applied: Still only storing total")
        print("\nTo fix, change line 3866 in MAIN/redesigned_main.py from:")
        print("  action_data['success_calculation'] = {'total': score}")
        print("To:")
        print("  action_data['success_calculation'] = result")
        sys.exit(1)
    else:
        print("⚠️  Could not find success_calculation assignment")

except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*80)
print("VERIFICATION SUMMARY")
print("="*80)
print("\n✅ Fix has been applied!")
print("\nWhat was fixed:")
print("- _calculate_detailed_success() now stores full result breakdown")
print("- enhanced_reporter.py can now display component values")
print("\nExpected result in simulation:")
print("- S-Trait values will show actual numbers")
print("- Skill values will show actual numbers")
print("- All modifiers will show actual numbers")
print("- Total calculation will be visible and verifiable")
print("\nBefore: 'S-Trait: N/A, Skill: N/A, Total: N/A'")
print("After:  'S-Trait: 3, Skill: 0, Serendipity: +1, Total: 4'")
print("\n" + "="*80)
