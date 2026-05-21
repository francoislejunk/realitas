# Exit System Bug Fix - February 18, 2026

## Bug Report

**Issue:** Exit system triggers false positives when user moves to in-room objects near exits

**Reported By:** User (2026-02-18)

**Scenario:**
```
User Input: "I head to the cracked mirror to examine it"
Expected: Move to mirror, examine it (stay in room)
Actual: Moved to mirror, then INCORRECTLY triggered exit transition to "outside"
```

### Root Cause

The `_check_exit_proximity_and_destination()` function was checking:
1. ✅ User has movement in input
2. ✅ There's an exit in location
3. ✅ UA is within range of exit (19.3 units)
4. ❌ **MISSING**: Is the user's TARGET actually an exit?

The function would trigger transition for ANY movement near an exit, even when the target was an in-room object like "cracked mirror", "workbench", "terminal", etc.

### The Fix

**Files Modified:** `MAIN/redesigned_main.py`

#### 1. Updated Function Signature (Line ~5751)

**Before:**
```python
def _check_exit_proximity_and_destination(user_input: str, spatial_manager, threshold_distance: float = 25.0):
```

**After:**
```python
def _check_exit_proximity_and_destination(user_input: str, spatial_manager, movement_target: Optional[str] = None, threshold_distance: float = 25.0):
```

Added `movement_target` parameter to check if user is explicitly targeting an exit.

#### 2. Added Target Validation Logic (Line ~5825)

**New Code:**
```python
# CRITICAL CHECK: Is the user's movement target actually an exit/door?
# Only transition if they're explicitly targeting an exit, not just moving near one
target_is_exit = False
if movement_target:
    target_lower = movement_target.lower()
    exit_keywords = ['exit', 'door', 'doorway', 'entrance', 'gate', 'hatch', 'portal', 'archway']
    target_is_exit = any(keyword in target_lower for keyword in exit_keywords)

    # Also check if target matches an exit obstacle name
    for exit_info in exits:
        if exit_info['obstacle_name'].lower() in target_lower or target_lower in exit_info['obstacle_name'].lower():
            target_is_exit = True
            break
```

#### 3. Updated Transition Logic (Line ~5845)

**Before:**
```python
if has_leave_intent:
    if nearest_exit['distance'] <= threshold_distance * 2:
        should_transition = True
elif nearest_exit['distance'] <= threshold_distance:
    # UA is right at the exit, any movement triggers transition
    should_transition = True
```

**After:**
```python
if has_leave_intent:
    # User wants to leave - check if reasonably close to exit
    if nearest_exit['distance'] <= threshold_distance * 2:
        should_transition = True
elif target_is_exit and nearest_exit['distance'] <= threshold_distance:
    # User is targeting an exit AND close enough - transition
    should_transition = True
```

**Key Change:** Second condition now requires BOTH:
- `target_is_exit == True` (user is targeting an exit)
- `nearest_exit['distance'] <= threshold_distance` (within range)

#### 4. Updated Function Call (Line ~14310)

**Before:**
```python
exit_transition = _check_exit_proximity_and_destination(user_input, spatial)
```

**After:**
```python
movement_target_for_exit_check = input_analysis.get('movement_target') if input_analysis else None
exit_transition = _check_exit_proximity_and_destination(user_input, spatial, movement_target=movement_target_for_exit_check)
```

Now passes the movement target from input analysis.

### New Behavior

#### Should Trigger Exit (✅):
```python
"I leave"                    # has_leave_intent = True
"I exit"                     # has_leave_intent = True
"I go outside"               # has_leave_intent = True
"I head to the door"         # target_is_exit = True (target = "door")
"I approach the exit"        # target_is_exit = True (target = "exit")
"I walk to the archway"      # target_is_exit = True (target = "archway")
```

#### Should NOT Trigger Exit (❌):
```python
"I head to the cracked mirror"    # target = "Cracked Mirror" (not an exit)
"I approach the workbench"         # target = "workbench" (not an exit)
"I examine the terminal"           # target = "terminal" (not an exit)
"I walk to the pillar"             # target = "pillar" (not an exit)
```

Even if these objects are near an exit, they won't trigger transition because the target is not an exit.

### Test Results

#### Before Fix:
```
Input: "I head to the cracked mirror to examine it"
[ARCHITECT] Kaelen Voss moved to 'Cracked Mirror'  ✅ Correct
[EXIT SYSTEM] Automatic transition to 'outside' detected  ❌ BUG!
[EXIT] Transitioned to 'outside'  ❌ Wrong!
```

#### After Fix (Expected):
```
Input: "I head to the cracked mirror to examine it"
[ARCHITECT] Kaelen Voss moved to 'Cracked Mirror'  ✅ Correct
[No exit transition - target is not an exit]  ✅ Correct
📦 PERCEPTUAL: You walk to the cracked mirror...  ✅ Correct
```

### Validation Rules

The exit system now only triggers when **ONE** of these conditions is true:

1. **Explicit Leave Intent**
   - User input contains: "leave", "exit", "go outside", etc.
   - AND UA is within 50 units of an exit
   - Example: "I leave" → Triggers exit

2. **Explicit Exit Target**
   - Movement target IS an exit/door
   - AND UA is within 25 units of that exit
   - Example: "I approach the door" → Triggers exit (if close)

If neither condition is met, NO transition occurs.

### Edge Cases Handled

| Scenario | Target | Leave Intent | Distance | Result |
|---|---|---|---|---|
| "I leave" | None | Yes | 20 units | ✅ Exit (leave intent) |
| "I head to door" | "door" | No | 10 units | ✅ Exit (target is exit) |
| "I head to mirror" | "mirror" | No | 10 units | ❌ No exit (target not exit) |
| "I approach workbench" | "workbench" | No | 15 units | ❌ No exit (target not exit) |
| "I leave" | None | Yes | 60 units | ❌ No exit (too far) |
| "I head to door" | "door" | No | 40 units | ❌ No exit (too far) |

### Summary

**Bug:** Exit system triggering for in-room movement near exits
**Fix:** Added target validation - only transition if target IS an exit
**Impact:** Prevents false positives, preserves intended in-room interactions
**Status:** ✅ FIXED (2026-02-18)

### Files Changed

1. `MAIN/redesigned_main.py`
   - Line ~5751: Updated function signature
   - Line ~5825: Added target validation logic
   - Line ~5845: Updated transition conditions
   - Line ~14310: Updated function call with movement_target

### Testing Recommendations

After fix:
1. ✅ "I head to the cracked mirror" - Should NOT exit
2. ✅ "I approach the workbench" - Should NOT exit
3. ✅ "I leave" - Should exit (if near exit)
4. ✅ "I head to the door" - Should exit (if close)
5. ✅ "I go outside" - Should exit (if near exit)

All in-room movements to non-exit objects should now work correctly without triggering unwanted location transitions.
