# Knockout State Tracking - Implementation Complete

## ✅ **Knockout State Now Stored in Tracker**

### What Was Added

**File:** `agents/tracker_agent.py` (lines 141-146)

Added a new `knockout_state` section to the actor sheet serialization that captures:

```python
"knockout_state": {
    "is_knocked_out": sheet.is_knocked_out(),
    "knockout_turns_remaining": sheet.get_knockout_turns_remaining(),
    "is_dead": sheet.is_dead(),
    "is_defeated": sheet.is_defeated()
}
```

### What This Tracks

**1. `is_knocked_out`** - Boolean indicating if the NUA is currently knocked out
- Returns `True` if defeated but not dead
- Calculated from: `is_defeated() and not is_dead()`

**2. `knockout_turns_remaining`** - Integer count of turns until recovery
- Tracks how many turns the NUA will remain unconscious
- Set to 1 when first knocked out (can be extended)
- Decrements each turn until 0

**3. `is_dead`** - Boolean indicating if the NUA is permanently dead
- Returns `True` if any status max capacity reached 0
- Dead actors cannot recover

**4. `is_defeated`** - Boolean indicating if the NUA is incapacitated
- Returns `True` if Stamina ≤ 0 OR Spirit ≤ 0
- Defeated actors skip their turns

### When Knockout State is Captured

**1. Session Start** (line 173)
- Initial actor state snapshot includes knockout state

**2. Turn Start** (line 326-327)
- Pre-turn snapshot captures state before action
- Includes both proactor and reactor knockout states

**3. Turn End** (line 357-358)
- Post-turn snapshot captures state after action
- Shows if knockout occurred during the turn

### How Knockout Works

**Automatic Knockout on Status Drop:**
- **File:** `actor_sheet.py` (lines 286-291)
- When Stamina or Spirit drops to 0:
  ```python
  if status_type in (StatusType.STAMINA, StatusType.SPIRIT) and original_value > 0 and new_value == 0:
      self.set_knockout_duration(1)
      print(f"{actor.name} is knocked out and will miss at least 1 turn")
  ```

**Turn Skipping:**
- **File:** `enhanced_round_manager.py` (lines 707-711)
- Knocked out actors automatically skip their turns
- System recursively advances to next actor

**Recovery:**
- Knockout turns decrement each round
- When `knockout_turns_remaining` reaches 0, actor can act again
- Temporary recovery system helps restore status values

### Storage Format Example

```json
{
  "actor_id": "actor_guard",
  "name": "Guard",
  "pre_turn_snapshots": {
    "proactor_sheet": {
      "name": "Guard",
      "statuses": {
        "STAMINA": {"value": 0, "max_value": 5},
        "SPIRIT": {"value": 3, "max_value": 5}
      },
      "knockout_state": {
        "is_knocked_out": true,
        "knockout_turns_remaining": 1,
        "is_dead": false,
        "is_defeated": true
      }
    }
  },
  "post_turn_snapshots": {
    "proactor_sheet": {
      "knockout_state": {
        "is_knocked_out": false,
        "knockout_turns_remaining": 0,
        "is_dead": false,
        "is_defeated": false
      }
    }
  }
}
```

### Benefits

**1. Complete State Tracking** ✓
- Every turn captures exact knockout status
- Can reconstruct when/how NUA was knocked out
- Historical record of unconscious periods

**2. Recovery Analysis** ✓
- Track how long NUA was unconscious
- See when they recovered
- Analyze knockout patterns

**3. Narrative Continuity** ✓
- Know if NUA should be unconscious when scene loads
- Maintain consistency across sessions
- Support for "you find them unconscious" scenarios

**4. Debugging Support** ✓
- Clear visibility into knockout mechanics
- Can verify turn-skipping is working
- Track recovery system effectiveness

**5. Future Features** ✓
- Foundation for "tend to unconscious NUA" actions
- Support for medical/healing mechanics
- Wake-up narrative triggers

### Integration Points

**Already Working:**
- ✅ Knockout detection (actor_sheet.py)
- ✅ Turn skipping (enhanced_round_manager.py)
- ✅ Recovery system (enhanced_temporary_recovery_system.py)
- ✅ State tracking (tracker_agent.py) ← **NEW**

**Storage Location:**
- `./simulation_data/sessions/{session_id}/session_data.json`
- Captured in pre/post turn snapshots
- Persists across session saves

### Example Scenario

```
TURN 1:
Player attacks Guard
→ Guard's Stamina: 3 → 0
→ System: "Guard is knocked out and will miss at least 1 turn"
→ Tracker stores: knockout_turns_remaining = 1

TURN 2:
Guard's turn comes up
→ System: "⏭️ Skipping Guard's turn (unconscious)"
→ Turn advances to next actor
→ Tracker stores: knockout_turns_remaining = 1 (still)

ROUND 2 START:
Initiative roll → Recovery triggered
→ Guard's Stamina recovers +1 (0 → 1)
→ Knockout turns decrement: 1 → 0
→ Guard can act again
→ Tracker stores: knockout_turns_remaining = 0, is_knocked_out = false
```

## Summary

**Knockout state is now fully tracked and stored** for all NUAs throughout the simulation. Every turn captures:
- Whether the NUA is knocked out
- How many turns until recovery
- Death/defeat status

This provides complete historical records and enables future features like tending to unconscious NPCs, wake-up narratives, and medical mechanics.

**Status: COMPLETE** ✅
