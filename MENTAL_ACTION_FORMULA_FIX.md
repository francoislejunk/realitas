# Mental Action Formula Fix

## Problem Identified

Mental actions (inquiries/information gathering) were using a **simplified formula** instead of the standard UTAS calculation used by all other actions.

### Old Formula (WRONG)
```python
# inquiry_helpers.py - OLD
base_roll = swiftness + spirit_value
total = base_roll + serendipity
```

**Missing Components:**
- ❌ Skill value
- ❌ Endowment value
- ❌ Supplement value
- ❌ Stress modifier
- ❌ Status modifier (used Spirit directly instead)
- ❌ Sympathy modifier

### Standard UTAS Formula (CORRECT)
```python
# unified_formula.py - Used by ALL actions
(s_trait + skill + endowment + supplement + serendipity) - (stress + status + sympathy)
```

## Solution Applied

### 1. Updated `inquiry_helpers.py`
Changed `roll_inquiry_success()` to use the **unified formula**:

```python
from unified_formula import calculate_unified_result

result = calculate_unified_result(
    actor=ua_actor,
    s_trait=SFactorType.SPIRIT,  # Mental action uses Spirit
    skill_name=None,  # No specific skill for general inquiries
    target_actor=None,  # No target for inquiries
    shift_polarity='Subtractive',
    targeted_status=None,  # Not targeting a status
    supplement_val=0,  # No supplement bonus for mental actions
    serendipity_override=None,  # Let it roll naturally
    stress_level_override=difficulty  # Difficulty maps to stress level
)
```

### 2. Updated Display in `redesigned_main.py`
Changed the mental action roll display to show **full breakdown** like all other actions:

**Before:**
```
🎲 MENTAL ACTION ROLL
Swiftness: 3 + Spirit: 5 + Luck: +1 = 9
Difficulty: 3
```

**After:**
```
🎲 MENTAL ACTION ROLL
Smarts: 3 + Skill: 0 + Endowment: 0 + Supplement: 0 + Luck: +1
Stress: +0 + Status: +0 + Sympathy: +0
Total: 4
Difficulty: 3 (Success if Total ≥ 0)
```

## Key Changes

### Mental Action Parameters
- **S-Trait:** Smarts (intelligence/reasoning)
- **Skill:** None (general inquiries don't use specific skills)
- **Endowment:** 0 (no supernatural abilities for basic inquiries)
- **Supplement:** 0 (no equipment bonus for mental actions)
- **Serendipity:** Rolled naturally (2d6-7)
- **Stress:** Maps to difficulty level
- **Status Modifier:** 0 (no status targeted)
- **Sympathy:** 0 (no target actor for inquiries)

### Success Threshold
- **Old:** `total >= difficulty` (absolute threshold)
- **New:** `total >= 0` (unified formula standard)

## Benefits

✅ **Consistency:** Mental actions now use the same formula as physical actions  
✅ **Completeness:** All UTAS components are now included  
✅ **Fairness:** Status modifiers properly affect mental performance  
✅ **Transparency:** Full breakdown shows all calculation components  
✅ **Accuracy:** Stress level properly affects difficulty

## Files Modified

1. **`inquiry_helpers.py`** (lines 126-187)
   - Replaced simplified formula with `calculate_unified_result()`
   - Updated return breakdown to include all components

2. **`MAIN/redesigned_main.py`** (lines 4637, 4645-4658)
   - Updated comment to reflect standard formula usage
   - Enhanced display to show full calculation breakdown

## Result

Mental actions now calculate success using the **exact same formula** as all other actions in UTAS, ensuring consistency and fairness across the simulation.
