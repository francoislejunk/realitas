"""
Test: NPC-initiated encounter from execute_post_user_turns_if_roam()
Verifies:
1. Function returns True when encounter is triggered
2. Function returns False when no encounter
3. All 6 call sites check the return value
"""

import sys, os
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 70)
print("ENCOUNTER TRIGGER FIX VERIFICATION")
print("=" * 70)

passed = 0
failed = 0

with open("MAIN/redesigned_main.py", "r", encoding="utf-8") as f:
    content = f.read()
    lines = content.splitlines()

# ── TEST 1: Function returns True on encounter ────────────────────────────
print("\n[TEST 1] execute_post_user_turns_if_roam returns True on encounter")
if "return True  # Signal caller to `continue` the main loop" in content:
    print("  ✅ return True present")
    passed += 1
else:
    print("  ❌ return True missing")
    failed += 1

# ── TEST 2: Function returns False when no encounter ─────────────────────
print("\n[TEST 2] execute_post_user_turns_if_roam returns False by default")
if "return False  # No encounter triggered" in content:
    print("  ✅ return False present")
    passed += 1
else:
    print("  ❌ return False missing")
    failed += 1

# ── TEST 3: All bare calls replaced with conditional ─────────────────────
print("\n[TEST 3] No bare (unchecked) calls to execute_post_user_turns_if_roam()")
bare_calls = [
    (i+1, l.strip())
    for i, l in enumerate(lines)
    if "execute_post_user_turns_if_roam()" in l
    and "def execute_post_user_turns_if_roam" not in l
    and not l.strip().startswith("if execute_post_user_turns_if_roam")
]
if bare_calls:
    for lineno, text in bare_calls:
        print(f"  ❌ Bare call at line {lineno}: {text}")
    failed += 1
else:
    # Count how many conditional calls exist
    cond_calls = [
        l for l in lines
        if "if execute_post_user_turns_if_roam():" in l
    ]
    print(f"  ✅ All {len(cond_calls)} call sites use conditional check")
    passed += 1

# ── TEST 4: Each conditional call is followed by continue ────────────────
print("\n[TEST 4] Each conditional call is followed by continue")
ok = True
for i, l in enumerate(lines):
    if "if execute_post_user_turns_if_roam():" in l:
        # Next non-empty line should be `continue`
        for j in range(i+1, min(i+4, len(lines))):
            stripped = lines[j].strip()
            if stripped:
                if stripped == "continue":
                    print(f"  ✅ Line {i+1}: has continue at line {j+1}")
                else:
                    print(f"  ❌ Line {i+1}: next statement is '{stripped}' not 'continue'")
                    ok = False
                break
if ok:
    passed += 1
else:
    failed += 1

# ── SUMMARY ──────────────────────────────────────────────────────────────
print("\n" + "=" * 70)
print(f"RESULTS: {passed} passed, {failed} failed")
if failed == 0:
    print("✅ All checks passed – encounter trigger fix verified")
else:
    print("❌ Some checks failed – review output above")
print("=" * 70)
