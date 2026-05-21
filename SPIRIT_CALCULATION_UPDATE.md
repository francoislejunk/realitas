# Spirit Calculation System Update

## Summary
Changed Spirit max capacity calculation from **sum** to **maximum** of Sociability and Smarts, removing the previous constraint.

## Changes Made

### 1. Core Calculation (actor_sheet.py)

**Before:**
```python
spirit_max = s_factors.get_factor(SFactorType.SOCIABILITY) + s_factors.get_factor(SFactorType.SMARTS)
```

**After:**
```python
spirit_max = max(s_factors.get_factor(SFactorType.SOCIABILITY), s_factors.get_factor(SFactorType.SMARTS))
```

**Rationale:** Spirit now follows the same pattern as Stamina:
- **Stamina** = max(Swiftness, Sturdiness)
- **Spirit** = max(Sociability, Smarts)

### 2. Removed Constraint (actor_sheet.py)

**Removed validation:**
```python
if sociability + smarts > 5:
    raise ValueError(f"Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts} exceeds maximum of 5. Spirit max capacity would be too high.")
```

**Impact:** Sociability and Smarts are now fully independent S-Factors with no mutual constraint.

### 3. Updated LLM Prompts (creator_agent.py)

**User Actor Generation:**
- Removed: "SPIRIT CONSTRAINT: Sociability + Smarts must be ≤ 5"
- Removed: "✓ Sociability + Smarts ≤ 5" from validation checklist
- Updated examples to show valid combinations without constraint

**NUA Generation:**
- Removed: "CRITICAL CONSTRAINT: Sociability + Smarts must NOT exceed 5"
- Removed validation logic checking `sociability_smarts_sum <= 5`
- Simplified error messages

### 4. Updated Test Files

Updated comments in:
- `quick_currency_test.py`
- `test_fallible_data_extraction.py`
- `test_proactor_rotation.py`
- `test_turn_queue_system.py`

## New System Behavior

### S-Factor Distribution Rules
1. **Total Points:** 15 for User Actors, 12 for NUAs
2. **Range:** Each S-Factor must be 1-5 (no zeros)
3. **No constraints between factors** (previously Sociability + Smarts ≤ 5)

### Status Max Capacity Formulas
- **Stamina:** max(Swiftness, Sturdiness)
- **Spirit:** max(Sociability, Smarts)
- **Supply:** Fixed at 5

### Example Character Builds

**Before (Constrained):**
- Sociability: 2, Smarts: 3 → Spirit max = 5 ✓
- Sociability: 4, Smarts: 4 → Spirit max = 8 ✗ (Invalid!)

**After (Unconstrained):**
- Sociability: 2, Smarts: 3 → Spirit max = 3 ✓
- Sociability: 4, Smarts: 4 → Spirit max = 4 ✓
- Sociability: 5, Smarts: 2 → Spirit max = 5 ✓
- Sociability: 2, Smarts: 5 → Spirit max = 5 ✓

## Benefits

1. **Consistency:** Spirit now follows the same pattern as Stamina
2. **Flexibility:** No artificial constraint on character builds
3. **Simplicity:** One less rule to validate and explain
4. **Balance:** Spirit max is naturally capped at 5 (since individual S-Factors are 1-5)

## Migration Notes

- Existing characters with valid S-Factors will continue to work
- Spirit max will be recalculated using the new formula
- Characters that were previously invalid due to the constraint are now valid
- No data migration needed - changes are purely computational
