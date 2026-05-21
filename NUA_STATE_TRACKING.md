# NUA State Tracking & Memory Consistency Guide

## Philosophy

**Every NUA has a persistent state that must be tracked and matched with their memories to ensure consistent behavior across encounters.**

## Core Principles

1. **State Persistence** - NUA states are saved continuously
2. **Death Tracking** - Deceased NUAs are permanently recorded
3. **Memory Consistency** - NUA memories must match their tracked state
4. **No Resurrection** - Dead NUAs cannot reappear
5. **State History** - Full state snapshots at key moments

## New TrackerAgent Methods

### 1. Record NUA Death

```python
tracker.record_nua_death(
    nua_actor=guard,
    cause_of_death="Shot during robbery",
    killer_name="Jesse Monroe"  # Optional
)
```

**What It Does:**
- Records full state snapshot at time of death
- Removes NUA from available_npcs
- Adds to deceased_nuas list
- Saves timestamp, location, cause
- Prevents resurrection

**Death Record Structure:**
```json
{
  "name": "Security Guard Mike",
  "occupation": "Security Guard",
  "cause_of_death": "Shot during robbery",
  "killer": "Jesse Monroe",
  "timestamp": "2025-10-24T10:30:00Z",
  "final_state": {
    "stamina": 0,
    "spirit": 2,
    "skills": {...},
    "sympathy": {...},
    "inventory": [...]
  },
  "location": "Downtown Bank",
  "scene_description": "The bank lobby..."
}
```

### 2. Check If NUA Is Alive

```python
if tracker.is_nua_alive("Security Guard Mike"):
    # NUA can appear in scene
    pass
else:
    # NUA is dead, cannot appear
    print("Mike is deceased - cannot encounter")
```

### 3. Get NUA State History

```python
state = tracker.get_nua_state_history("Security Guard Mike")

if state is None:
    # Never encountered this NUA
    print("First time meeting Mike")
    
elif state['status'] == 'deceased':
    # NUA is dead
    print(f"Mike died: {state['death_info']['cause']}")
    print(f"Killed by: {state['death_info']['killer']}")
    print(f"Location: {state['death_info']['location']}")
    
elif state['status'] == 'alive':
    # NUA is alive, get their current state
    current_stamina = state['state']['statuses']['STAMINA']['value']
    current_location = state['location']
    print(f"Mike is alive at {current_location}")
```

### 4. Get All Deceased NUAs

```python
deceased = tracker.get_deceased_nuas()

for death_record in deceased:
    print(f"{death_record['name']} - {death_record['cause_of_death']}")
```

## Integration Points

### 1. After Combat Death

**Location:** `redesigned_main.py` or `exchange_system.py` when NUA dies

```python
# Check if NUA died in combat
if nua_actor.sheet.is_dead():
    # Record the death
    tracker.record_nua_death(
        nua_actor=nua_actor,
        cause_of_death="Killed in combat",
        killer_name=ua_actor.sheet.name if ua_killed_them else None
    )
    
    # Create death memory for UA
    auto_memory_creator.on_nua_death(
        nua_name=nua_actor.sheet.name,
        cause_of_death="Killed in combat",
        location=current_location,
        turn_number=turn_counter
    )
    
    # Remove from available_npcs (already done by record_nua_death)
    print(f"{Color.WARNING}💀 {nua_actor.sheet.name} has died{Color.RESET}")
```

### 2. Before Scene Population

**Location:** `scene_population_system.py` in `populate_scene()`

```python
def populate_scene(self, scene_description: str, time_of_day: str = "day") -> List[NonUserActor]:
    """Generate NUAs, but exclude deceased ones"""
    
    # ... existing population code ...
    
    # Filter out deceased NUAs
    if hasattr(self, 'tracker') and self.tracker:
        generated_nuas = [
            nua for nua in generated_nuas 
            if self.tracker.is_nua_alive(nua.sheet.name)
        ]
    
    return generated_nuas
```

### 3. Before NUA Creation

**Location:** `redesigned_main.py` before creating NUA from scene

```python
# Check if this NUA name is deceased
if tracker.is_nua_alive(npc_name):
    # Safe to create
    new_npc = creator.generate_nua(npc_prompt, scene_description)
else:
    # This NUA is dead, don't create them
    print(f"{Color.WARNING}Cannot create {npc_name} - they are deceased{Color.RESET}")
    
    # Optionally, inform player if they try to interact
    print(f"{Color.NARRATIVE}You remember that {npc_name} is no longer alive...{Color.RESET}")
```

### 4. Memory System Integration

**Location:** When loading NUA memories from `npc_memory_system.py`

```python
def load_nua_with_memories(nua_name: str, tracker, nua_memory_system):
    """Load NUA and verify consistency with tracked state"""
    
    # Get tracked state
    state = tracker.get_nua_state_history(nua_name)
    
    if state is None:
        # First encounter - no state yet
        return None
    
    if state['status'] == 'deceased':
        # NUA is dead - cannot load
        print(f"[MEMORY] {nua_name} is deceased - cannot load")
        return None
    
    # Load NUA memories
    memories = nua_memory_system.get_memories_for_nua(nua_name)
    
    # Verify memory consistency with tracked state
    # Example: Check if memories reference events after death
    # Example: Check if sympathy values match
    
    return {
        'state': state['state'],
        'memories': memories,
        'location': state['location']
    }
```

## Data Structure

### Runtime State Structure

```json
{
  "runtime_state": {
    "scene_description": "...",
    "current_location": "Downtown Bank",
    "available_npcs": [
      {
        "actor_type": "NonUserActor",
        "sheet_data": {
          "name": "Waitress Sally",
          "occupation": "Diner Waitress",
          ...
        }
      }
    ],
    "deceased_nuas": [
      {
        "name": "Security Guard Mike",
        "occupation": "Security Guard",
        "cause_of_death": "Shot during robbery",
        "killer": "Jesse Monroe",
        "timestamp": "2025-10-24T10:30:00Z",
        "final_state": {...},
        "location": "Downtown Bank",
        "scene_description": "The bank lobby..."
      }
    ]
  }
}
```

## Use Cases

### Use Case 1: Combat Death

```python
# During combat
if guard.sheet.is_dead():
    tracker.record_nua_death(
        nua_actor=guard,
        cause_of_death="Gunshot wounds",
        killer_name=player.sheet.name
    )
```

### Use Case 2: Prevent Resurrection

```python
# Player returns to bank
if not tracker.is_nua_alive("Security Guard Mike"):
    print("The bank is quiet. Mike's body has been removed.")
    # Don't add Mike to available_npcs
```

### Use Case 3: Memory Consistency

```python
# NUA remembers past encounter
state = tracker.get_nua_state_history("Bartender Joe")

if state and state['status'] == 'alive':
    # Load Joe's memories
    memories = nua_memory_system.get_memories_for_nua("Bartender Joe")
    
    # Verify Joe's current state matches his memories
    last_sympathy = state['state']['sympathy'].get(player_name, {}).get('value', 0)
    
    # Joe's behavior should match his sympathy level
    if last_sympathy < 0:
        joe_greeting = "Joe glares at you coldly."
    else:
        joe_greeting = "Joe nods in recognition."
```

### Use Case 4: Investigation

```python
# Player asks about deceased NUA
deceased = tracker.get_deceased_nuas()

for record in deceased:
    if "Mike" in record['name']:
        print(f"Mike died on {record['timestamp']}")
        print(f"Cause: {record['cause_of_death']}")
        print(f"Location: {record['location']}")
```

## Benefits

1. **Narrative Consistency** - Dead NUAs stay dead
2. **Memory Accuracy** - NUA memories match their tracked state
3. **Consequence Tracking** - Deaths are permanent and recorded
4. **Investigation Support** - Full death records for detective work
5. **State Verification** - Can check NUA state before interactions
6. **Session Persistence** - Death records survive session restarts

## Testing Checklist

- [ ] Kill NUA in combat
- [ ] Verify NUA recorded in deceased_nuas
- [ ] Verify NUA removed from available_npcs
- [ ] Return to same location
- [ ] Verify dead NUA doesn't reappear
- [ ] Check is_nua_alive() returns False
- [ ] Load NUA state history shows deceased
- [ ] Death record has correct cause/killer
- [ ] Session save/load preserves death records
- [ ] Memory system respects deceased status

## Error Prevention

### ❌ Don't Do This:
```python
# Creating NUA without checking if alive
new_npc = creator.generate_nua(prompt, scene)
available_npcs.append(new_npc)  # Might resurrect dead NUA!
```

### ✅ Do This:
```python
# Always check if NUA is alive first
if tracker.is_nua_alive(npc_name):
    new_npc = creator.generate_nua(prompt, scene)
    available_npcs.append(new_npc)
else:
    print(f"{npc_name} is deceased - cannot create")
```

## Future Enhancements

1. **Injury Tracking** - Track non-fatal injuries and recovery
2. **Relationship Changes** - Track sympathy changes over time
3. **Location History** - Track where NUA has been seen
4. **Interaction Log** - Full history of UA-NUA interactions
5. **State Snapshots** - Periodic state saves for time-travel debugging
6. **Memory Validation** - Automatic consistency checking

## Critical Notes

⚠️ **ALWAYS check is_nua_alive() before creating/loading NUA**
⚠️ **ALWAYS call record_nua_death() when NUA dies**
⚠️ **NEVER manually remove from deceased_nuas (permanent record)**
⚠️ **ALWAYS match NUA state with their memories**

This system ensures NUAs behave consistently and deaths have permanent consequences.
