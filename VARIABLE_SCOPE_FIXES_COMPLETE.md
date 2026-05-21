# Variable Scope Fixes - Complete Resolution

## The Problems

Three `UnboundLocalError` issues:

1. **`input_analysis` used before defined** (line 3299 in intent availability check)
   ```
   UnboundLocalError: cannot access local variable 'input_analysis' where it is not associated with a value
   ```

2. **`is_inquiry` not defined** (line 3415)
   ```
   UnboundLocalError: cannot access local variable 'is_inquiry' where it is not associated with a value
   ```

3. **`DiegeticTransitionSystem` shadowed by local import** (line 3003)
   ```
   UnboundLocalError: cannot access local variable 'DiegeticTransitionSystem' where it is not associated with a value
   ```

## Root Causes

### Issue 1: `input_analysis` Used Before Defined

The intent availability check (starting line 3141) was using `input_analysis` at line 3299, but `input_analysis` wasn't created until line 3401 (much later).

**Flow:**
```
1. Line 3141: Intent availability check starts
2. Line 3299: is_inquiry_action = (input_analysis.get(...)) ❌ NOT DEFINED YET
3. Line 3396: input_analysis_for_survival = conductor.detect_inquiry_or_action(...) ✓ TOO LATE
4. Line 3401: input_analysis = input_analysis_for_survival ✓ TOO LATE
```

### Issue 2: `is_inquiry` Not Defined

The code was checking `if not is_inquiry and not is_contested_nua:` at line 3425, but `is_inquiry` was never defined.

**Flow:**
```
1. Line 3401: input_analysis = input_analysis_for_survival ✓
2. Line 3425: if not is_inquiry... ❌ NOT DEFINED
```

### Issue 3: `DiegeticTransitionSystem` Import Shadowing

`DiegeticTransitionSystem` was imported at the top of the file (lines 39, 70), but a local import at line 4911 was shadowing it, causing Python to think it's a local variable that hasn't been assigned yet when accessed at line 3003.

**Flow:**
```
1. Top of file: from diegetic_transition_system import DiegeticTransitionSystem ✓
2. Line 3003: transition_system = DiegeticTransitionSystem(...) ✓ Should work
3. Line 4911: from diegetic_transition_system import DiegeticTransitionSystem ❌ Shadows global
4. Python sees local import later, treats DiegeticTransitionSystem as local variable
5. Line 3003 now fails because "local variable not assigned yet"
```

## The Solutions

### Fix 1: Move Input Analysis BEFORE Intent Availability Check

**File:** `MAIN/redesigned_main.py` (lines 3130-3138)

The entire input analysis block was moved to happen BEFORE the intent availability check:

```python
# ============================================================
# INPUT ANALYSIS - Must happen BEFORE intent availability check
# ============================================================
# Classify inquiry vs action ONCE and reuse for this input
input_analysis_for_survival = conductor.detect_inquiry_or_action(user_input, actor, None)
input_analysis = input_analysis_for_survival

# CRITICAL: Check if this is an inquiry (for survival processing skip)
is_inquiry = input_analysis.get('input_type') == 'inquiry'
```

This ensures `input_analysis` and `is_inquiry` are available when the intent availability check needs them.

### Fix 2: Remove Duplicate Assignments

**File:** `MAIN/redesigned_main.py` (line 3395)

Removed the duplicate input analysis creation that was happening later:

```python
# input_analysis_for_survival and input_analysis already created above (before intent availability check)
```

### Fix 3: Remove Local Import

**File:** `MAIN/redesigned_main.py` (line 4911)

```python
# Before:
from diegetic_transition_system import DiegeticTransitionSystem  ❌

# After:
# DiegeticTransitionSystem already imported at top of file  ✓
```

Removed the local import that was shadowing the global import.

## Files Modified

**`MAIN/redesigned_main.py`**

**Lines 3393-3394:** Added `is_inquiry` definition
```python
# CRITICAL: Check if this is an inquiry (for survival processing skip)
is_inquiry = input_analysis.get('input_type') == 'inquiry'
```

**Line 4911:** Removed local import
```python
# DiegeticTransitionSystem already imported at top of file
```

## Correct Flow Now

### Flow 1: `input_analysis` and `is_inquiry`
```
1. Line 3134: input_analysis_for_survival = conductor.detect_inquiry_or_action(...) ✓ CREATED EARLY
2. Line 3135: input_analysis = input_analysis_for_survival ✓ ASSIGNED EARLY
3. Line 3138: is_inquiry = input_analysis.get('input_type') == 'inquiry' ✓ DEFINED EARLY
4. Line 3141: Intent availability check starts ✓
5. Line 3299: is_inquiry_action = (input_analysis.get(...)) ✓ NOW AVAILABLE
6. Line 3425: if not is_inquiry and not is_contested_nua: ✓ NOW AVAILABLE
```

### Flow 2: `DiegeticTransitionSystem`
```
1. Top of file: from diegetic_transition_system import DiegeticTransitionSystem ✓
2. Line 3003: transition_system = DiegeticTransitionSystem(...) ✓ WORKS
3. Line 4911: (no local import) ✓ No shadowing
4. Line 4921: diegetic_system = DiegeticTransitionSystem(master_time) ✓ WORKS
```

## Result

✅ **`input_analysis` created early** - Before intent availability check  
✅ **`is_inquiry` defined early** - Before any usage  
✅ **No import shadowing** - Global import works throughout file  
✅ **Proper execution order** - Variables defined before use  
✅ **Clean execution** - System runs without scope errors  

All three variable scope issues resolved!
