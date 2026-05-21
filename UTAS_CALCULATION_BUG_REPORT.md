# UTAS Calculation Display Bug Report

## Issue

UTAS success calculations are showing "N/A" for all values instead of displaying actual computed numbers.

**Example Output:**
```
Success Calculation:
Calculation incomplete due to missing factors.
  • S-Trait: N/A
  • Skill: N/A
  • Endowment: N/A
  • Supplement: N/A
  • Serendipity: N/A
  • Stress Modifier: N/A
  • Status Modifier: N/A
  • Sympathy Modifier: N/A
  • Total: N/A
Success Threshold: N/A
Result: N/A (incomplete calculation)
```

---

## Root Cause

There's a **data structure mismatch** between:
1. What `_calculate_detailed_success()` returns (a single integer)
2. What `enhanced_reporter.py` expects (a dictionary with component breakdowns)

### The Flow:

**Step 1:** `_calculate_detailed_success()` is called
- **File:** `MAIN/redesigned_main.py:3755-3871`
- **Returns:** Single integer (total success value)
- **Side effect:** Stores `{'total': score}` in `action_data['success_calculation']`

**Step 2:** Enhanced reporter tries to display breakdown
- **File:** `enhanced_reporter.py:880-933`
- **Expects:** Dictionary with keys:
  - `positive_factors` → `{s_trait,skill,endowment,supplement,serendipity}`
  - `negative_factors` → `{stress_modifier, status_modifier, sympathy_modifier}`
  - `final_result` or `total`

**Problem:** The reporter expects a full breakdown dictionary, but only gets `{'total': score}`

---

## Why This Happens

### In `_calculate_detailed_success()` (redesigned_main.py:3848-3869):

```python
result = calculate_unified_result(
    actor=actor,
    s_trait=s_trait_enum,
    # ... parameters ...
)
try:
    score = int(result.get('final_result', 0) or 0)
except Exception:
    score = 0
try:
    if isinstance(action_data, dict):
        action_data['success_calculation'] = {'total': score}  # ← ONLY STORES TOTAL!
except Exception:
    pass
return score
```

The function calls `calculate_unified_result()` which presumably returns a full breakdown, but then **only extracts and stores the total**.

### In `enhanced_reporter.py` (880-933):

```python
success_data = success_calculation or {}
pos = success_data.get('positive_factors', {})  # ← EXPECTS THIS
neg = success_data.get('negative_factors', {})  # ← AND THIS
# ... tries to extract s_trait, skill, etc from pos/neg ...
```

The reporter expects the full `positive_factors` and `negative_factors` structure, which was never stored.

---

## The Fix

### Option 1: Store Full Breakdown (RECOMMENDED)

Modify `_calculate_detailed_success()` to store the complete result:

**File:** `MAIN/redesigned_main.py:3865-3868`

```python
# BEFORE:
try:
    if isinstance(action_data, dict):
        action_data['success_calculation'] = {'total': score}
except Exception:
    pass

# AFTER:
try:
    if isinstance(action_data, dict):
        action_data['success_calculation'] = result  # Store full breakdown, not just total!
except Exception:
    pass
```

###Option 2: Fix Reporter to Handle Simple Total (PARTIAL)

Modify `enhanced_reporter.py` to gracefully handle minimal data:

**File:** `enhanced_reporter.py:904-933`

```python
# Add fallback when only total is available
if 'positive_factors' not in success_data and 'total' in success_data:
    # Fallback: show simplified output when only total available
    total = success_data.get('total', 'N/A')
    print(f"Total Success: {total}")
    print("(Detailed breakdown not available)")
    # Continue with threshold check...
else:
    # Existing code...
```

**Problem with Option 2:** This doesn't fix the root issue - you still don't see the math breakdown.

---

## Recommended Solution

**Implement Option 1** - Store the full result from `calculate_unified_result()` instead of just extracting the total.

### Implementation:

**File:** `MAIN/redesigned_main.py:3865-3869`

Change:
```python
try:
    if isinstance(action_data, dict):
        action_data['success_calculation'] = {'total': score}  # OLD - loses breakdown
except Exception:
    pass
return score
```

To:
```python
try:
    if isinstance(action_data, dict):
        # Store full breakdown for reporter display
        action_data['success_calculation'] = result  # NEW - preserves all components
except Exception:
    pass
return score
```

---

## Expected Result After Fix

```
Success Calculation:
(S-Trait: 3 + Skill: 0 + Endowment: 0 + Supplement: 0 + Serendipity: +1) - (Stress Modifier: +0 + Status Modifier: -2 + Sympathy Modifier: +1) = 3
Success Threshold: 0
Result: SUCCESS (3 ≥ 0)
Factors Used:
  • S-Trait: Shadow (3, Default)
  • Skill: None (0, N/A)
  • Super: None (0)
  • Supplement: None (0)
  • Serendipity: +1 (2D6=7)
Modifiers:
  • Stress: +0
  • Status: -2
  • Sympathy: +1
```

---

## Impact

### Current State (Broken):
- ❌ No visibility into calculation
- ❌ Impossible to debug UTAS issues
- ❌ Players can't understand outcomes
- ❌ Appears as if math isn't running at all

### After Fix:
- ✅ Full calculation breakdown visible
- ✅ Easy to spot calculation bugs
- ✅ Players understand why actions succeed/fail
- ✅ Math transparency restored

---

## Files Involved

1. **MAIN/redesigned_main.py:3865-3869** - Where breakdown is lost
2. **enhanced_reporter.py:880-933** - Where breakdown is displayed
3. **unified_formula.py** - Where `calculate_unified_result()` generates the breakdown

---

## Testing Steps After Fix

1. Start simulation
2. Attempt any contested action
3. Check console output for "Success Calculation:"
4. Verify all components show numbers (not N/A)
5. Verify math adds up correctly

---

## Priority

**CRITICAL** - This breaks combat/exchange transparency completely. Players can't understand why actions succeed or fail, and developers can't debug UTAS issues.

**Estimated Fix Time:** 5 minutes (1-line change)
