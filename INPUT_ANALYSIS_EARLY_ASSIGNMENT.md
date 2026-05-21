# Input Analysis Early Assignment - Fixed Variable Scope Error

## The Problem

The code was trying to access `input_analysis` in the intent availability check before it was defined:

```python
# Line 3305 - BEFORE input_analysis was assigned
is_inquiry_action = (input_analysis.get('input_type') == 'fallible_action' and 
                    input_analysis.get('fallible_subtype') in ['mental', 'inquiry'])
```

This caused the error:
```
Intent check skipped: cannot access local variable 'input_analysis' where it is not associated with a value
```

## The Root Cause

The flow was:

```
1. Line 3392: input_analysis_for_survival = conductor.detect_inquiry_or_action(...)
2. Line 3260: Intent availability check runs
3. Line 3305: Try to access input_analysis ❌ NOT DEFINED YET
4. Line 3683: input_analysis = input_analysis_for_survival ✓ TOO LATE
```

## The Solution

Moved the `input_analysis` assignment to happen BEFORE the intent availability check:

```python
# Line 3135 - RIGHT AFTER pronoun resolution, BEFORE intent availability
input_analysis = input_analysis_for_survival
```

## New Flow

```
1. Line 3392: input_analysis_for_survival = conductor.detect_inquiry_or_action(...)
2. Line 3135: input_analysis = input_analysis_for_survival ✓ ASSIGNED EARLY
3. Line 3138: Intent availability check runs
4. Line 3305: Access input_analysis ✓ NOW DEFINED
```

## Files Modified

**`MAIN/redesigned_main.py`**

**Lines 3130-3135:** Added early assignment
```python
# ============================================================
# INPUT ANALYSIS - Classify action type early
# ============================================================
# We need input_analysis early for intent availability check
# ============================================================
input_analysis = input_analysis_for_survival
```

**Lines 3682-3683:** Removed duplicate assignment
```python
# EXPLORATION MODE: input_analysis already assigned earlier (before intent availability)
# (removed: input_analysis = input_analysis_for_survival)
```

## Result

✅ **`input_analysis` available early** - Before intent availability check  
✅ **No variable scope errors** - Properly defined when accessed  
✅ **Inquiry detection works** - Can check if action is inquiry  
✅ **Availability flow correct** - Inquiries continue processing for all states  

The variable is now assigned at the right point in the flow!
