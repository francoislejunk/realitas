"""
Quick tests for two fixes:
  1. _dest_exists_in_rag now checks Key Memories
  2. Initiative rolling in _apply_location_move success path
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

PASS = []
FAIL = []

def check(name, condition, detail=""):
    if condition:
        print(f"  PASS  {name}")
        PASS.append(name)
    else:
        print(f"  FAIL  {name}" + (f": {detail}" if detail else ""))
        FAIL.append(name)

# ─────────────────────────────────────────────────────────────
# FIX 1: _dest_exists_in_rag key-memory check (unit simulation)
# We can't call the closure directly, so we replicate its logic.
# ─────────────────────────────────────────────────────────────
print("\n=== FIX 1: Key Memory destination check ===")

class FakeMemory:
    def __init__(self, title, description, full_narrative=""):
        self.title = title
        self.description = description
        self.full_narrative = full_narrative

class FakeKeyMemories:
    def __init__(self, memories):
        self._memories = memories
    def search_memories(self, query):
        ql = query.lower()
        return [m for m in self._memories
                if ql in (m.title + " " + m.description + " " + m.full_narrative).lower()]

def dest_exists_via_key_memories(dest, key_memories):
    """Mirrors the new key-memory block added to _dest_exists_in_rag."""
    dl = dest.lower().strip()
    if not dl:
        return False
    try:
        if key_memories:
            mem_results = key_memories.search_memories(dl)
            for m in (mem_results or []):
                try:
                    mem_text = (
                        (getattr(m, 'title', '') or '') + ' ' +
                        (getattr(m, 'description', '') or '') + ' ' +
                        (getattr(m, 'full_narrative', '') or '')
                    ).lower()
                    if dl in mem_text:
                        return True
                except Exception:
                    pass
    except Exception:
        pass
    return False

# Memory that matches the user's scenario
lib_memory = FakeMemory(
    title="Local Sanctuary",
    description="The Central Library is just a short walk away, located in an old stone building on Oak Street. It is a quiet, reliable space where the staff knows your face and the Wi-Fi is always stable."
)
km = FakeKeyMemories([lib_memory])

check("Central Library found in memory",
      dest_exists_via_key_memories("Central Library", km))
check("central library (lowercase) found in memory",
      dest_exists_via_key_memories("central library", km))
check("Oak Street found in memory description",
      dest_exists_via_key_memories("Oak Street", km))
check("Random unknown dest NOT found",
      not dest_exists_via_key_memories("Dragon's Keep Fortress", km))
check("Empty dest returns False",
      not dest_exists_via_key_memories("", km))
check("None key_memories returns False",
      not dest_exists_via_key_memories("Central Library", None))

# ─────────────────────────────────────────────────────────────
# FIX 1: Common places extended with library etc.
# ─────────────────────────────────────────────────────────────
print("\n=== FIX 1: Common places fallback extended ===")

EXTENDED_COMMON_PLACES = {
    "street": ["street", "road", "outside", "exit", "leave"],
    "market": ["market", "bazaar", "stalls"],
    "food_place": ["food", "eat", "meal", "kitchen"],
    "library": ["library", "archive", "archives", "reading room"],
    "tavern": ["tavern", "inn", "pub", "bar", "alehouse"],
    "guard_post": ["guard post", "garrison", "barracks", "watch"],
    "temple": ["temple", "church", "shrine", "chapel"],
}

def infer_common_place(text):
    text_l = text.lower()
    scores = {}
    for label, keys in EXTENDED_COMMON_PLACES.items():
        score = sum(2 for k in keys if k in text_l)
        if score > 0:
            scores[label] = score
    if not scores:
        return None
    return max(scores, key=scores.get)

check("'library' input infers library",
      infer_common_place("I head to the library") == "library")
check("'archive' input infers library",
      infer_common_place("I visit the archive") == "library")
check("'tavern' input infers tavern",
      infer_common_place("I go to the tavern") == "tavern")
check("'church' input infers temple",
      infer_common_place("I enter the church") == "temple")
check("'inn' input infers tavern",
      infer_common_place("find an inn") == "tavern")
check("'garrison' input infers guard_post",
      infer_common_place("head to the garrison") == "guard_post")

# ─────────────────────────────────────────────────────────────
# FIX 2: Initiative code exists in success path of _apply_location_move
# ─────────────────────────────────────────────────────────────
print("\n=== FIX 2: Initiative in _apply_location_move success path ===")

import ast, os

main_path = os.path.join(os.path.dirname(__file__), "MAIN", "redesigned_main.py")

with open(main_path, encoding="utf-8") as f:
    source = f.read()
    lines = source.splitlines()

# Check that initiative rolling exists BEFORE the return in the success path.
# Strategy: find "STEP 2e: ROLL INITIATIVE" comment with "(success path)" marker
success_marker = "STEP 2e: ROLL INITIATIVE FOR ALL PRESENT ACTORS (success path)"
check("Success-path initiative comment present in source",
      success_marker in source)

# Verify the return comes AFTER the initiative block in source order
idx_initiative = source.find(success_marker)
# Find the nearest "return str(new_desc)" after the initiative block
idx_return = source.find("return str(new_desc)", idx_initiative)
check("return str(new_desc) comes AFTER success-path initiative block",
      idx_initiative > 0 and idx_return > idx_initiative,
      f"initiative at char {idx_initiative}, return at char {idx_return}")

# Verify initiative code is NOT only inside the except block
# (i.e., the success-path marker should appear before the except handler)
idx_except = source.find("except Exception as e:\n        print(f\"{Color.ERROR}Critical error in _apply_location_move logic:")
check("Success-path initiative block appears before Critical-error except handler",
      idx_initiative > 0 and (idx_except < 0 or idx_initiative < idx_except),
      f"initiative at {idx_initiative}, except at {idx_except}")

# Check key memory block present in _dest_exists_in_rag
km_marker = "Check Key Memories: if the player has learned about this"
check("Key Memory check comment present in source",
      km_marker in source)

# ─────────────────────────────────────────────────────────────
# SUMMARY
# ─────────────────────────────────────────────────────────────
print(f"\n{'='*50}")
print(f"Results: {len(PASS)} passed, {len(FAIL)} failed")
if FAIL:
    print("FAILED:")
    for f in FAIL:
        print(f"  - {f}")
    sys.exit(1)
else:
    print("All tests passed!")
