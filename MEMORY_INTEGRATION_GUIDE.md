# Memory Systems Integration Guide

## Overview

Two memory systems work together to create persistent, meaningful memories:

1. **NUA Memory System** - Tracks what NUAs remember about events and actors
2. **Key Memories System** - Highlights important moments for the player
3. **Automatic Memory Creator** - Automatically creates key memories for important events

## NUA Memory System (Persistent)

### Storage Location
`./simulation_data/nua_memories/nua_memories.json`

### What It Tracks
- All interactions with actors
- Threats received
- Help received
- Witnessed violence
- Conversations
- Important events

### When Memories Are Saved
**Automatically after every event recording:**
- `record_threat()` - Saves immediately
- `record_help()` - Saves immediately
- `record_witnessed_violence()` - Saves immediately
- `record_conversation()` - Saves immediately
- `record_event()` - Saves immediately (if `auto_save=True`)

### Integration Points in Main Loop

```python
from npc_memory_system import get_nua_memory_system

nua_memory = get_nua_memory_system()

# When NUA is threatened
nua_memory.record_threat(
    nua_name="Guard",
    threatener_name=actor.sheet.name,
    threat_description="Threatened with weapon"
)

# When NUA is helped
nua_memory.record_help(
    nua_name="Merchant",
    helper_name=actor.sheet.name,
    help_description="Gave food"
)

# When NUA witnesses violence
nua_memory.record_witnessed_violence(
    nua_name="Bystander",
    perpetrator_name=actor.sheet.name,
    victim_name="Guard",
    violence_description="Stabbed the guard"
)

# When having conversation
nua_memory.record_conversation(
    nua_name="Bartender",
    other_actor=actor.sheet.name,
    topic="local rumors",
    key_points="Discussed missing persons"
)
```

## Key Memories System (Player Highlights)

### Storage Location
`./simulation_data/memories/{session_id}_memories.json`

### What It Tracks
- Task completions
- First meetings with NUAs
- Combat victories/defeats
- Major discoveries
- Relationship milestones
- Critical moments
- Deaths

### When Memories Are Saved
**Automatically after creation:**
- Every `create_memory()` call saves to disk immediately
- Pin/unpin operations save immediately
- Adding notes saves immediately

## Automatic Memory Creator

### Triggers Automatic Key Memory Creation

#### 1. Task Completion
```python
from automatic_memory_creation import get_automatic_memory_creator

auto_memory = get_automatic_memory_creator()

# When task is completed
auto_memory.on_task_completed(
    task_description="Find food",
    location=current_location,
    actors_involved=[actor.sheet.name],
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id
)
```

#### 2. First Meeting with NUA
```python
# When new NUA is created/met
auto_memory.on_nua_first_met(
    nua_name=new_nua.sheet.name,
    nua_occupation=new_nua.sheet.occupation,
    location=current_location,
    first_impression="Seems friendly and helpful",
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id
)
```

#### 3. Combat Ended
```python
# When combat ends
auto_memory.on_combat_ended(
    victory=True,  # or False
    opponent_name="Bandit",
    location=current_location,
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id,
    casualties=["Bandit Leader"]  # optional
)
```

#### 4. Major Discovery
```python
# When discovering something important
auto_memory.on_major_discovery(
    discovery_type="location",  # or "item", "secret", etc.
    discovery_description="Found hidden underground bunker",
    location=current_location,
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id,
    actors_involved=[actor.sheet.name]
)
```

#### 5. Relationship Milestone
```python
# When relationship changes significantly
auto_memory.on_relationship_milestone(
    nua_name="Guard",
    milestone_type="became_friends",  # or "became_enemies", "betrayal", "reconciliation"
    description="Guard now trusts you after you saved their life",
    location=current_location,
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id
)
```

#### 6. Death
```python
# When someone dies
auto_memory.on_death(
    deceased_name="Merchant",
    cause="Stabbed by bandits",
    location=current_location,
    narrative=last_narrative,
    turn_number=turn_counter,
    scene_id=current_scene_id,
    witnesses=[actor.sheet.name, "Guard"]
)
```

## Integration Checklist

### Main Loop Initialization
- [x] Initialize NUA memory system with storage path
- [x] Initialize automatic memory creator
- [x] Both systems ready before simulation starts

### During Simulation

#### When NUA is Created/Met
```python
# After creating new NUA
if new_nua and new_nua.sheet.name not in auto_memory.met_nuas:
    auto_memory.on_nua_first_met(
        nua_name=new_nua.sheet.name,
        nua_occupation=new_nua.sheet.occupation,
        location=scene_description[:100],
        first_impression="Initial impression from scene",
        narrative=last_action_narrative,
        turn_number=turn_counter,
        scene_id=current_scene_id
    )
```

#### When Task is Completed
```python
# Check if task was completed
if goal_task_manager.current_task and task_just_completed:
    auto_memory.on_task_completed(
        task_description=goal_task_manager.current_task.description,
        location=scene_description[:100],
        actors_involved=[actor.sheet.name],
        narrative=last_action_narrative,
        turn_number=turn_counter,
        scene_id=current_scene_id
    )
```

#### When Combat Ends
```python
# After combat resolution
if combat_ended:
    auto_memory.on_combat_ended(
        victory=actor_won,
        opponent_name=opponent.sheet.name,
        location=scene_description[:100],
        narrative=combat_narrative,
        turn_number=turn_counter,
        scene_id=current_scene_id
    )
```

#### When Sympathy Changes Significantly
```python
# After sympathy shift
if abs(sympathy_change) >= 2:  # Significant change
    milestone_type = "became_friends" if sympathy_change > 0 else "became_enemies"
    auto_memory.on_relationship_milestone(
        nua_name=target_actor.sheet.name,
        milestone_type=milestone_type,
        description=f"Relationship changed by {sympathy_change}",
        location=scene_description[:100],
        narrative=last_action_narrative,
        turn_number=turn_counter,
        scene_id=current_scene_id
    )
```

#### When Actor Dies
```python
# After death check
if actor_died:
    auto_memory.on_death(
        deceased_name=dead_actor.sheet.name,
        cause=death_cause,
        location=scene_description[:100],
        narrative=death_narrative,
        turn_number=turn_counter,
        scene_id=current_scene_id,
        witnesses=[w.sheet.name for w in witnesses]
    )
```

## Benefits

### For NUAs
- ✅ Remember past interactions across sessions
- ✅ React appropriately to history (threats, help, violence)
- ✅ Build realistic relationships over time
- ✅ No more "fake signals" where NUAs forget important events

### For Players
- ✅ Automatic highlights of important moments
- ✅ Can review key memories anytime with `/mem`
- ✅ Memories persist across sessions
- ✅ No manual memory creation needed
- ✅ Natural story progression tracking

## Commands

### View Memories
- `/mem` - List all key memories
- `/mem 3` - View memory #3 in detail
- `/mem pinned` - Show only pinned memories
- `/mem search combat` - Search for combat memories

### Natural Language
- `memories` - List all memories
- `recall 5` - View memory #5
- `pinned` - Show pinned memories
- `search memories food` - Search for food-related memories
