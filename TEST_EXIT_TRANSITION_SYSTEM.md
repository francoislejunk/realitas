# Exit Transition System - Test Plan

## New Feature: Automatic Door Transitions

### Implementation Summary
When user says "I leave" or approaches an exit/door, the system now:
1. ✅ Detects nearby exits using `_check_exit_proximity_and_destination()`
2. ✅ Checks if UA is within interaction range (~25 units or explicit leave intent)
3. ✅ Pre-creates destination location BEFORE perceptual description
4. ✅ Automatically transitions without requiring "open door" action
5. ✅ Displays new location scene immediately

### Code Changes

#### 1. New Helper Function (Line ~5750)
**Function:** `_check_exit_proximity_and_destination()`

**Purpose:** Detect if UA should automatically transition through exit

**Logic:**
- Finds all exits/doors in current location (obstacle_type or portal_kind = 'exit'/'door')
- Calculates distance from UA to nearest exit
- Checks user intent for leave keywords ('leave', 'exit', 'go outside', etc.)
- Returns transition data if:
  - User explicitly says "I leave" AND within 50 units of exit, OR
  - User is within 25 units of exit (any movement)

**Returns:**
```python
{
    'should_transition': True,
    'destination': "Hallway",  # From connects_to or inferred
    'exit_name': "main_door",
    'distance': 15.2,
    'is_external': True,
    'narrative_hook': "through the main_door"
}
```

#### 2. Exit Check Integration (Line ~14286)
**Location:** Right before perceptual description generation in given_action block

**Process:**
1. Call `_check_exit_proximity_and_destination(user_input, spatial)`
2. If transition detected:
   - Calculate travel time
   - Clear previous location NPCs
   - Call `_apply_location_move()` to create destination
   - Update scene_description
   - Display new location
   - **SKIP** perceptual description generation (continue to next turn)
3. If no transition:
   - Proceed with normal perceptual description

### Test Scenarios

#### Test 1: Explicit Leave Intent
```
Session: Elias Thorne - EmpCog service van
Input: "I leave"
Expected:
  [EXIT SYSTEM] Automatic transition to 'Street' detected
  [EXIT SYSTEM] Distance to exit: 18.5 units
  [EXIT] Transitioned to 'Street'

  🎬 SCENE DESCRIPTION:
  You step out through the van's rear doors into the street. [New location description...]
```

#### Test 2: Approach Exit
```
Session: Any interior location with door
Input: "I walk to the door"
Expected:
  🏛️ ARCHITECT Walk to 'door': (100.0, 50.0) → (125.0, 10.0)
  [EXIT SYSTEM] Automatic transition to 'Hallway' detected
  [EXIT] Transitioned to 'Hallway'
```

#### Test 3: Far From Exit
```
Session: Large room, UA far from exit
Input: "I leave"
Expected:
  [EXIT SYSTEM] Automatic transition to 'Hallway' detected
  [MOVEMENT] First moves UA closer to exit
  [EXIT] Transitioned to 'Hallway'
```

#### Test 4: In-Room Object (No Transition)
```
Session: Any location
Input: "I approach the workbench"
Expected:
  🏛️ ARCHITECT Walk to 'workbench': (10.0, 20.0) → (15.0, 25.0)
  [No exit transition - workbench is in-room obstacle]

  Perceptual Description:
  You walk to the technician workbench. [Normal description...]
```

#### Test 5: Long Journey (Chunking)
```
Session: Current location has exit to distant place
Input: "I leave and go downtown"
Expected:
  [EXIT SYSTEM] Journey to Downtown requires 15 minutes - starting chunking
  [TRAVEL] Journey to Downtown will take 15 minutes (5 segments)
```

### Key Behaviors

**Destination Inference Logic:**
| Current Location Type | User Says "I leave" | Inferred Destination |
|---|---|---|
| Apartment/Room | "I leave" | "Hallway" |
| Building/Shop | "I leave" | "Street" |
| Hallway | "I leave" | "Building Entrance" or "Street" |
| Street | "I leave" | "Nearby Area" |

**Distance Thresholds:**
- **Explicit Intent** ("I leave"): Up to 50 units (lenient)
- **Implicit Movement**: Up to 25 units (must be right at exit)

**Exit Detection Keywords:**
- 'leave', 'exit', 'go outside', 'step out', 'walk out'
- 'head out', 'depart', 'go through door', 'open door'

### Integration Points

1. **Line 5750**: `_check_exit_proximity_and_destination()` function definition
2. **Line 14286**: Exit transition check in given_action block
3. **Line 5750-5920**: `_apply_location_move()` - destination creation
4. **Line 5605-5748**: `_detect_location_move()` - destination inference fallback

### Files Modified
- `MAIN/redesigned_main.py`: Added exit detection and automatic transition logic

### Dependencies
- `spatial_context_system.py`: Obstacle detection (exits/doors)
- `agents/architect_agent.py`: Movement resolution
- `agents/conductor_agent.py`: Scene generation for new location
- `journey_chunking_system.py`: Long-distance travel (if >3 minutes)

### Testing Checklist

- [ ] User says "I leave" from apartment → Transitions to hallway
- [ ] User says "I leave" from shop → Transitions to street
- [ ] User approaches door (within 25 units) → Auto-transition
- [ ] User approaches in-room object → No transition, normal movement
- [ ] User far from exit says "I leave" → Moves toward exit, then transitions
- [ ] Long journey triggers chunking system (not instant transition)
- [ ] Destination location is described immediately after transition
- [ ] Previous location NPCs are cleared
- [ ] New location NPCs are spawned
- [ ] Spatial map updates correctly

### Expected Output Example

```
(What do you want to do?): I leave

[EXIT SYSTEM] Automatic transition to 'Hallway' detected
[EXIT SYSTEM] Distance to exit: 22.3 units
[SYSTEM] Cleared NPCs from previous location
[EXIT] Transitioned to 'Hallway'

🎬 SCENE DESCRIPTION:
You push through the doorway into a narrow hallway. Fluorescent lights flicker overhead,
casting harsh shadows on the scuffed linoleum floor. A faint smell of mildew and stale air
hangs in the space. You see a bulletin board covered in faded notices and a fire extinguisher
mounted on the wall. At the far end, an elevator door stands closed, its call button glowing
a dim amber.

🌤️ The interior lighting is artificial and dim.

📊 Status: ROAM mode | Time: Day 1, 9:05 AM

(What do you want to do?):
```

### Success Criteria

✅ User can say "I leave" without needing separate "open door" action
✅ Destination is pre-created BEFORE perceptual description
✅ Transition is automatic when close to exit
✅ Door opening is implicit in the transition (not stealing agency)
✅ New location is immediately accessible and described
✅ System infers logical destination if not explicitly stated
✅ In-room movement still works normally (no false positives)
✅ Long journeys still trigger chunking system appropriately

## Notes

- The system respects the principle of "not stealing agency" - when user says "I leave", opening the door is part of that action, not a separate action to steal
- The destination is pre-created so it can be mentioned in the transition narrative
- Distance threshold ensures user is actually AT the exit before transitioning
- Inference system provides intelligent defaults when user doesn't specify destination
- Existing journey/chunking system handles long-distance travel (>3 minutes)
