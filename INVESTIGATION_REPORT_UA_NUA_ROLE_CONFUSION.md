# Investigation Report: Interpreter UA/NUA Role Confusion

## Issue Summary
Edge cases in role assignment during contested exchanges where the UA reacts to an NUA's action.

## Root Cause
At **MAIN/redesigned_main.py:17618**, when the UA is reacting to an NUA's proaction, the function call has incorrect role assignment:

```python
det = _strict_detect_inquiry_or_action(ua_react_input, reactor, proactor, _retries=3)
```

### Context at This Point:
- **`proactor`** = the NUA who just acted (the original proactor in this turn)
- **`reactor`** = variable name confusingly refers to the UA
- **`actor`** = the correct UA reference

The function signature is:
```python
def detect_inquiry_or_action(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]
```

Where:
- **`proactor`** = the actor currently taking action
- **`reactor`** = the target of that action

### The Problem:
When the UA is reacting, **the UA is now the proactor** (the one acting), and the NUA becomes the reactor (the target). But the code passes them in reverse order.

This causes the LLM analyzing the action to have confused role context, leading to:
1. Incorrect addressing detection
2. Wrong contested action classification
3. Misidentified movement targets
4. Improper addressed_type assignment

## Fix Required

**Location:** MAIN/redesigned_main.py:17618

**Current Code:**
```python
det = _strict_detect_inquiry_or_action(ua_react_input, reactor, proactor, _retries=3)
```

**Fixed Code (Option 1 - Use `actor` variable):**
```python
det = _strict_detect_inquiry_or_action(ua_react_input, actor, proactor, _retries=3)
```

**Fixed Code (Option 2 - Swap parameters with better naming):**
```python
# When UA reacts, UA is the new proactor (acting), NUA becomes reactor (target)
det = _strict_detect_inquiry_or_action(ua_react_input, actor, proactor, _retries=3)
```

## Consistency Check

Line **17766** uses **correct** keyword argument order:
```python
resp = conductor.handle_inquiry(ua_react_input, proactor=reactor, reactor=proactor)
```

However, this uses confusing variable names. The variable `reactor` at this point is actually the UA (who IS the proactor when reacting).

### Recommendation:
Rename the `reactor` variable in this section to `ua` or `acting_ua` for clarity, since it represents the User Actor who is reacting (and thus acting as proactor).

## Adjacent Code Section

**Lines 17113-17121** show reactor determination:
```python
# Determine reactor dynamically based on proactor's target or use fallback
reactor = None
if proactor.is_user_actor:
    reactor = None  # Will be determined by target detection
else:
    # For NPC proactors, use next actor in queue as fallback
    reactor_position = (encounter_checker.current_context.round_manager.turn_queue_position + 1) % len(turn_queue)
    reactor = turn_queue[reactor_position]['actor']
```

When an NPC is the proactor, `reactor` gets assigned correctly. But when the UA reacts later in the code (around line 17590+), the variable naming becomes confusing because `reactor` is used to refer to the UA who is now acting.

## Testing Recommendations

After fixing, test these scenarios:
1. **NPC attacks UA** → UA reacts with "dodge" or "counterattack"
   - Verify action is correctly classified as contested_action
   - Verify addressed_to is set to NPC name
   - Verify addressed_type is "nua"

2. **NPC asks UA a question** → UA responds with inquiry
   - Verify input_type is "inquiry"
   - Verify it doesn't incorrectly classify as contested_action

3. **NPC moves toward UA** → UA reacts with movement
   - Verify explicit_movement flag is set correctly
   - Verify movement_target matches intended destination

## Files Affected
- **MAIN/redesigned_main.py** (line 17618)

## Status
**INVESTIGATION COMPLETE** - Ready for implementation
