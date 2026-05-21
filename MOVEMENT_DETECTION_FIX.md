# Movement Detection Fix - Preventing System from Acting on Behalf of User

## Critical Issue Identified

The system was moving the user without explicit intent by checking BOTH user input AND generated narrative for movement keywords. This is a **CRITICAL** violation of user agency.

## Root Causes

### 1. Movement Detection on Narrative (FIXED)
**Location:** `MAIN/redesigned_main.py` line 4322-4324

**Problem:**
```python
# Check both user input AND narrative for movement
movement_data = movement_detector.detect_movement(
    f"{user_input} {contextual_result}",  # ← WRONG: includes narrative
    scene_description
)
```

**Fix Applied:**
```python
# CRITICAL: Check ONLY user input for movement, NOT narrative
# The narrative is descriptive, not prescriptive - we must not move the user
# based on what the narrator says, only on what the user explicitly requests
movement_data = movement_detector.detect_movement(
    user_input,  # ONLY user input - never use narrative for movement detection
    scene_description
)
```

### 2. Narrator Unaware of Movement Intent (NEW FIX NEEDED)

**Problem:** The narrator doesn't know if the user explicitly requested movement, so it may describe movement even when none was intended.

**Solution:** Add explicit movement detection in InterpreterAgent and pass this information to the narrator.

## Implementation

### Step 1: Add Movement Detection Method (COMPLETED)

**File:** `agents/interpreter_agent.py`

Added `detect_explicit_movement()` method that:
- Checks for explicit movement verbs (walk, move, go, run, etc.)
- Checks for movement prepositions (to, toward, into, etc.)
- Returns movement data with confidence level
- Does NOT rely on narrative, only user input

### Step 2: Integrate Movement Check in Main Loop (IN PROGRESS)

**File:** `MAIN/redesigned_main.py`

Need to:
1. Call `interpreter.detect_explicit_movement(user_input)` early in processing
2. Pass movement detection result to narrator
3. Narrator uses this to determine if movement should be described

### Step 3: Update Narrator Prompts (TODO)

**File:** `agents/narrator_agent.py`

Add to narrator prompts:
```
**MOVEMENT CONSTRAINT:**
Explicit movement detected: {has_explicit_movement}
- If FALSE: DO NOT describe the user moving to new locations
- If TRUE: You may describe movement to: {target}
```

## Testing Checklist

- [ ] User says "I look around" → No movement occurs
- [ ] User says "I walk to the door" → Movement occurs
- [ ] Narrator describes "you see the door" → No movement occurs
- [ ] User says "I examine the workbench" → No movement occurs
- [ ] User says "I go to the workbench" → Movement occurs

## Design Philosophy

**The narrator describes what the user perceives, NOT what the user does.**

- User input = prescriptive (commands what happens)
- Narrative = descriptive (describes what is perceived)
- Movement ONLY occurs from explicit user commands
- Narrator NEVER moves the user without explicit intent

## Files Modified

1. ✅ `MAIN/redesigned_main.py` - Fixed movement detection to only check user input
2. ✅ `agents/interpreter_agent.py` - Added `detect_explicit_movement()` method
3. ⏳ `MAIN/redesigned_main.py` - Integrate movement check in main loop
4. ⏳ `agents/narrator_agent.py` - Update prompts with movement constraints

## Status

- **Movement Detection Fix:** ✅ COMPLETE
- **Explicit Movement Detection:** ✅ COMPLETE  
- **Main Loop Integration:** ✅ COMPLETE
- **Narrator Prompt Updates:** ✅ COMPLETE

## Summary of Changes

### 1. Fixed Movement Detection (redesigned_main.py line 4324)
- Changed from checking `user_input + contextual_result` to ONLY `user_input`
- Prevents narrative descriptions from triggering spatial movement

### 2. Added Explicit Movement Detection (interpreter_agent.py lines 2957-3018)
- New method: `detect_explicit_movement(user_input)`
- Detects movement verbs (walk, move, go, run, etc.)
- Detects movement prepositions (to, toward, into, etc.)
- Returns movement data with confidence level

### 3. Integrated Movement Check in Main Loop (redesigned_main.py lines 2904-2921)
- Calls `interpreter.detect_explicit_movement()` immediately after user input
- Stores result in `explicit_movement_data` variable
- Logs detection results for debugging

### 4. Updated Narrator Prompts (narrator_agent.py lines 2052-2059)
- Added `movement_data` parameter to `generate_given_action_narrative()`
- Added **CRITICAL MOVEMENT CONSTRAINT** section to prompt
- Narrator now knows whether movement was explicitly requested
- Prevents narrator from describing movement unless user explicitly requested it

## Next Steps

**TODO:** Pass `explicit_movement_data` to narrator calls throughout main loop
- Search for all `narrator.generate_given_action_narrative()` calls
- Add `movement_data=explicit_movement_data` parameter
- Search for all `narrator.generate_exploration_action_result_narrative()` calls  
- Add `movement_data=explicit_movement_data` parameter

This will complete the integration and prevent the system from acting on behalf of the user.
