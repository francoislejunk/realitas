# Validation Bug Fix - Duplicate Field Checking

## Problem Identified

NUA proaction was failing with validation error claiming all UTAS fields were missing, even though the LLM generated them correctly:

```
UTAS Factors Keys: ['exchange_type', 's_trait_to_use', 's_trait_value', 'skill', 'endowment', 'supplement', 'stress_level', 'status_to_shift', 'shift_type', 'shift_polarity', 'self_effects']

CRITICAL ERROR: Missing/invalid required PROACTOR UTAS fields: ['exchange_type', 'status_to_shift', 's_trait_to_use', 's_trait_value', 'skill', 'endowment', 'supplement', 'stress_level', 'shift_type', 'shift_polarity', 'self_effects', 'status_to_shift', 'shift_polarity', 's_trait_to_use', 's_trait_value', 'stress_level', 'shift_type', 'skill', 'endowment', 'supplement']
```

**Notice:** Fields are listed **twice** in the error message!

## Root Cause

**File:** `response_normalizer.py` lines 346-354

The validation logic was checking fields **twice**:

1. **First Check** (lines 346-354): Checked if field exists BEFORE normalization
   - Added fields to `missing_fields` if not present or None
   
2. **Normalization** (lines 356-444): Normalized and validated fields
   - If validation failed, added field to `missing_fields` AGAIN
   
3. **Result:** Fields appeared twice in `missing_fields` list

### The Bug:

```python
# OLD CODE (BUGGY):
for field in required_fields:
    field_value = normalized["utas_factors"].get(field)
    
    if field == "self_effects":
        if field_value is None or (isinstance(field_value, list) and len(field_value) == 0):
            missing_fields.append(field)  # ← Added here
    else:
        if field not in normalized["utas_factors"] or field_value is None:
            missing_fields.append(field)  # ← Added here

# Then later...
try:
    sts = uf.get("status_to_shift")
    if isinstance(sts, str):
        # ... normalization ...
    else:
        missing_fields.append("status_to_shift")  # ← Added AGAIN here!
```

This caused:
- Fields to be added to `missing_fields` even if they existed but weren't normalized yet
- Duplicate entries when normalization also failed
- False positives claiming fields were missing when they were actually present

## Fix Applied

**Removed the premature validation check** and only validate AFTER normalization is complete:

```python
# NEW CODE (FIXED):
missing_fields = []
missing_justifications = []

# Don't check for missing fields yet - normalize first, then validate
# This prevents duplicate entries in missing_fields

for field in justification_fields:
    if field not in normalized["utas_factors"] or not normalized["utas_factors"][field]:
        missing_justifications.append(field)

# Normalize and validate key intent fields (no defaults injected)
# ... all normalization happens here ...

# Final validation: Check if required fields are still missing after normalization
for field in required_fields:
    if field == "self_effects":
        field_value = normalized["utas_factors"].get(field)
        if field_value is None or (isinstance(field_value, list) and len(field_value) == 0):
            if field not in missing_fields:  # Avoid duplicates
                missing_fields.append(field)
    else:
        if field not in normalized["utas_factors"] or normalized["utas_factors"].get(field) is None:
            if field not in missing_fields:  # Avoid duplicates
                missing_fields.append(field)
```

## Additional Fix: Removed Duplicate Dialogue Metadata Extraction

**Lines 283-297:** Had 4 identical blocks extracting dialogue_metadata

```python
# OLD CODE (BUGGY):
if "dialogue_metadata" in source_data:
    normalized["dialogue_metadata"] = source_data.get("dialogue_metadata", {})

# Extract optional dialogue metadata (non-blocking)
if "dialogue_metadata" in source_data:
    normalized["dialogue_metadata"] = source_data.get("dialogue_metadata", {})

# Extract optional dialogue metadata (non-blocking)
if "dialogue_metadata" in source_data:
    normalized["dialogue_metadata"] = source_data.get("dialogue_metadata", {})

# Extract optional dialogue metadata (non-blocking)
if "dialogue_metadata" in source_data:
    normalized["dialogue_metadata"] = source_data.get("dialogue_metadata", {})
```

**Fixed:** Removed all duplicates, keeping only the final extraction at line 314

## Expected Behavior Now

**Before Fix:**
```
LLM generates all fields correctly ✓
Validator checks fields before normalization → adds to missing_fields
Normalization happens
Validator checks again → adds to missing_fields AGAIN
Error: "Missing fields: [field1, field2, ..., field1, field2, ...]" ❌
```

**After Fix:**
```
LLM generates all fields correctly ✓
Normalization happens
Validator checks AFTER normalization → only adds truly missing fields
Success or accurate error message ✓
```

## Test Case

**LLM Response:**
```json
{
  "action_noun": "greet",
  "narrative_description": "approaches Dylan Cole with a warm smile",
  "utas_factors": {
    "exchange_type": "Sympathy",
    "s_trait_to_use": "SOCIABILITY",
    "s_trait_value": 3,
    "skill": {"name": "Customer Service", "value": 2},
    "endowment": {"name": "None", "value": 0},
    "supplement": {"name": "None", "value": 0},
    "stress_level": 1,
    "status_to_shift": "SYMPATHY",
    "shift_type": "Temporary",
    "shift_polarity": "Additive",
    "self_effects": [...]
  }
}
```

**Before Fix:**
```
CRITICAL ERROR: Missing/invalid required PROACTOR UTAS fields: ['exchange_type', 'status_to_shift', ..., 'exchange_type', 'status_to_shift', ...] ❌
```

**After Fix:**
```
✓ Validation passes
✓ NUA action proceeds normally
```

## Files Modified

1. **`response_normalizer.py`** (lines 343-499)
   - Removed premature field validation
   - Added final validation AFTER normalization
   - Added duplicate prevention (`if field not in missing_fields`)
   - Removed duplicate dialogue_metadata extraction blocks

## Summary

✅ **Validation order fixed** - Normalize first, then validate
✅ **Duplicate prevention** - Check if field already in missing_fields before adding
✅ **Accurate error messages** - No more duplicate field names
✅ **Code cleanup** - Removed 3 duplicate dialogue_metadata blocks

The validator now correctly identifies truly missing fields without false positives!
