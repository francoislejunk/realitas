# Mission Tracking System - Structured Narrative Progression

## Overview

Implemented a **structured narrative progression system** that transforms the 4-mode loop from "soft guidance" to a "narrative engine" that actively shapes story arcs.

## What Was Added

### 1. Mission Tracking in NarrativeState (narrative_loop_system.py)

**New Fields:**
```python
active_mission: Optional[str] = None  # Current mission being pursued
mission_description: Optional[str] = None  # Detailed description
available_sparks: List[str] = []  # Potential missions in SPARK mode
mission_progress: float = 0.0  # 0.0 to 1.0 progress
obstacles_overcome: List[str] = []  # Progress milestones
mission_rewards: List[str] = []  # Potential rewards
mission_started_at: Optional[datetime] = None  # Timestamp
```

**Helper Methods:**
- `start_mission(name, description)` - Begin tracking a mission
- `add_obstacle_overcome(obstacle)` - Record progress (auto-increments progress by 25%)
- `complete_mission()` - Mark as complete (progress = 1.0)
- `clear_mission()` - Reset after resolution
- `has_active_mission()` - Check if mission is active

### 2. Mode-Specific Narrative Guidance (Enhanced)

#### ROAM Mode - Open World Freedom
```
- Emphasize the world is open and accessible
- Describe 2-3 visible locations, NUAs, or opportunities casually
- Make the player feel they can go anywhere based on their intent
- Frame at point of uncertainty with diegetic elements
- Allow organic exploration and socializing without pressure
```

#### SPARK Mode - Introduce Potential Missions
```
- Casually introduce 2-3 potential missions/goals through:
  * NUA dialogue ('I heard the warehouse is hiring')
  * Environmental cues (wanted poster, broken fence, overheard conversation)
  * Opportunities that align with character interests
- Frame as interesting possibilities, not obligations
- Let the player choose which spark to pursue
- Available sparks: [list of detected sparks]
```

#### PRESSURE Mode - Advance Mission (Mission-Aware)
```
**When mission is active:**
- Mission: [mission_description]
- Progress: [X%]
- Obstacles overcome: [count]
- Present challenges that directly advance this mission:
  * 1 hard challenge (requires planning/resources/skill)
  * 2 easy wins (build momentum, show progress)
- Each obstacle should feel like progress toward the goal
- Use Kishōtenketsu Ten-style twists to heighten stakes

**When no mission:**
- Introduce obstacles or complications
- Use perspective shifts, revelations, or schedule changes
- Heighten stakes without forcing conflict
```

#### OUTCOME Mode - Resolve Mission (Mission-Aware)
```
**When mission is active:**
- Mission completed: [mission_description]
- Obstacles overcome: [list]
- Tie up loose ends (what happened to involved NUAs?)
- Deliver clear rewards (items, relationships, information) OR consequences (setbacks, complications)
- Show how the world changed from this mission
- Provide closure and hint at new possibilities
- Follow with reflective sequel beat for processing

**When no mission:**
- Deliver natural consequences or rewards in-fiction
- Follow with reflective sequel beat for processing and new direction
```

### 3. Automatic Mission Detection

**Spark Selection (lines 502-509):**
```python
# If in SPARK mode and player shows clear intent, start mission
if (self.current_state.mode == NarrativeMode.SPARK and 
    not self.current_state.has_active_mission() and
    strongest.strength >= 0.7):
    self.current_state.start_mission(
        mission_name=strongest.description,
        description=strongest.source_data.get('context', strongest.description)
    )
```

**Progress Tracking (lines 534-547):**
```python
def _track_mission_progress(self, signals: List[SoftSignal]):
    # Check for successful actions that advance the mission
    for signal in signals:
        if signal.signal_type == SoftSignalType.WANT:
            if signal.strength >= 0.6:
                obstacle_desc = signal.source_data.get('action_description', 'obstacle')
                self.current_state.add_obstacle_overcome(obstacle_desc)
        
        # Check for mission completion
        if signal.signal_type == SoftSignalType.CLOSURE:
            if self.current_state.mission_progress >= 0.75:
                self.current_state.complete_mission()
```

### 4. Mission Context in Guidance

**Framing guidance now includes (lines 528-529):**
```python
'active_mission': self.current_state.active_mission,
'mission_progress': self.current_state.mission_progress
```

This gets passed to all agents so they can reference the active mission.

## How It Works

### The Full Narrative Arc

**1. ROAM → Player explores freely**
- Agents emphasize open world
- Describe multiple locations/NUAs/opportunities
- Player feels they can go anywhere

**2. SPARK → System introduces potential missions**
- 2-3 missions casually introduced through NUA dialogue, environmental cues
- Framed as possibilities, not obligations
- Player chooses which spark to pursue

**3. Mission Auto-Starts**
- When player shows clear intent (WANT signal strength ≥ 0.7)
- System starts tracking the mission
- Mode transitions to PRESSURE

**4. PRESSURE → Challenges advance the mission**
- Agents present obstacles directly related to the mission
- Mix of hard challenges and easy wins
- Each obstacle = 25% progress
- Progress tracked automatically

**5. Mission Completes**
- When progress ≥ 75% and CLOSURE signal detected
- Mode transitions to OUTCOME

**6. OUTCOME → Resolution and rewards**
- Tie up loose ends
- Deliver rewards or consequences
- Show how world changed
- Clear mission data
- Return to ROAM for new cycle

## Integration Points

### Agents Need to Use Mission Context

**DeciderAgent, CreatorAgent, NarratorAgent** will receive:
```python
narrative_guidance = loop_state.get('narrative_guidance')
active_mission = loop_state.get('active_mission')
mission_progress = loop_state.get('mission_progress')
```

They should reference the active mission in their prompts when in PRESSURE/OUTCOME modes.

### Main Loop Integration

The main loop already passes `loop_state` to agents. The mission context is now included automatically in the guidance dict.

## Implementation Status

1. ✅ **Mission tracking system** - COMPLETE
2. ✅ **Mode-specific guidance** - COMPLETE
3. ✅ **Auto-detection logic** - COMPLETE
4. ✅ **Agent prompt enhancement** - COMPLETE
   - ✅ DeciderAgent references active mission in PRESSURE/OUTCOME
   - ✅ CreatorAgent references active mission in PRESSURE/OUTCOME
   - ✅ NarratorAgent uses framing_guidance (includes mission context)
5. ✅ **Reward/consequence system** - COMPLETE
   - ✅ Reward tracking in NarrativeState
   - ✅ Reward display in OUTCOME mode guidance
   - ✅ Mission summary method for status checks
6. ⏳ **Testing** - PENDING
   - Test full ROAM → SPARK → PRESSURE → OUTCOME cycle
   - Verify mission tracking works correctly
   - Confirm agents use mission context appropriately

## Benefits

**Before (Soft Guidance):**
- ❌ Modes just changed agent attitude
- ❌ No story continuity
- ❌ No mission tracking
- ❌ Vague "present prompts" instructions

**After (Structured Progression):**
- ✅ Modes drive story structure
- ✅ Missions tracked from spark to resolution
- ✅ Progress monitored automatically
- ✅ Specific mission-aware instructions
- ✅ Clear narrative arc: freedom → goal → challenge → resolution

The system now provides **structured narrative progression** while maintaining the invisible, diegetic feel! 🎭
