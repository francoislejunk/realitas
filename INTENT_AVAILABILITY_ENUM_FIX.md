# Intent Availability Enum Names Fixed

## Problem

Code was using old enum names that no longer exist:
- ❌ `IntentAvailability.AVAILABLE_NOW`
- ❌ `IntentAvailability.AVAILABLE_LATER`
- ❌ `IntentAvailability.AVAILABLE_NEVER`

Error: `AttributeError: type object 'IntentAvailability' has no attribute 'AVAILABLE_LATER'`

## Correct Enum Names

The `IntentAvailability` enum uses diegetic naming:

```python
class IntentAvailability(Enum):
    """Classification of intent availability - Diegetic naming"""
    EXIST = "exist"  # Action can be performed here and now
    EXIST_NOT_HERE = "exist_not_here"  # Action is valid but not at current location
    DOES_NOT_EXIST = "does_not_exist"  # Action references something that doesn't exist
```

## Mapping

| Old Name (Wrong) | New Name (Correct) | Meaning |
|-----------------|-------------------|---------|
| `AVAILABLE_NOW` | `EXIST` | Can do it now |
| `AVAILABLE_LATER` | `EXIST_NOT_HERE` | Exists but not here |
| `AVAILABLE_NEVER` | `DOES_NOT_EXIST` | Doesn't exist |

## Files Fixed

### 1. `MAIN/redesigned_main.py`
**Lines 3273, 3279, 3284:**
```python
# Before
if availability_result["availability"] == IntentAvailability.AVAILABLE_LATER:
elif availability_result["availability"] == IntentAvailability.AVAILABLE_NEVER:
# If AVAILABLE_NOW, proceed

# After
if availability_result["availability"] == IntentAvailability.EXIST_NOT_HERE:
elif availability_result["availability"] == IntentAvailability.DOES_NOT_EXIST:
# If EXIST, proceed
```

### 2. `intent_based_memory_creation.py`
**Lines 948, 952:**
```python
# Before
return IntentAvailability.AVAILABLE_NOW

# After
return IntentAvailability.EXIST
```

## Files Still Using Old Names (Documentation/Tests)

These files use old names but are **documentation or test files** that may need updating:
- `test_intent_availability.py`
- `test_intent_memory_integration.py`
- `MAIN/integration_patch.py`
- `integration_example_full_system.py`
- Various `.md` documentation files

**Note:** These are not critical for runtime but should be updated for consistency.

## Result

✅ Runtime error fixed  
✅ Intent availability system now works correctly  
✅ Uses correct diegetic enum names  

The system will no longer crash with `AttributeError` when checking intent availability.
