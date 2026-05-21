# Scene Population System Integration Guide

## Philosophy

**CRITICAL PRINCIPLE:** All NUAs that could exist in a scene must be generated **BEFORE** the scene is narrated to the player.

### Why Pre-Generate?

❌ **OLD WAY (Broken):**
```
1. Scene: "You enter a diner"
2. Player: "I look around"
3. Narrator: "You see a grizzled trucker"
4. Player: "I approach the trucker"
5. System: *creates random NUA on-the-fly*
6. NUA: "Hey, I'm on main street!" ← WRONG CONTEXT
```

✅ **NEW WAY (Correct):**
```
1. Scene generation: "diner" detected
2. System pre-generates:
   - Sally (waitress) - full sheet
   - Frank (cook) - full sheet  
   - Old Timer (patron) - full sheet
   - Grizzled Trucker (patron) - full sheet
3. All NUAs stored in available_npcs
4. Sympathy initialized between UA and all NUAs
5. Scene narrated: "You enter a diner..."
6. Player: "I approach the trucker"
7. System: *uses pre-generated trucker* ← CORRECT CONTEXT
```

## Benefits

1. **Narrative Consistency** - NUAs know where they are
2. **No Creation Delays** - Instant interaction
3. **Proper Relationships** - Sympathy initialized upfront
4. **Discovery Mechanics** - `/people` shows who's around
5. **Progressive Revelation** - Skills hidden but exist in backend

## Integration Points

### 1. Scene Creation (Initial Scene)

**Location:** `redesigned_main.py` around line 2100-2130

```python
# BEFORE scene narration
from scene_population_system import populate_scene_with_nuas

# Generate scene elements
scene_elements = creator.generate_initial_scene(actor)

# PRE-POPULATE with NUAs
available_npcs = populate_scene_with_nuas(
    creator_agent=creator,
    scene_description=scene_elements['scene_elements']['setting'],
    time_context=master_time.get_current_time_context(),
    full_population=True  # Generate all potential NUAs
)

# Initialize sympathy between UA and all NUAs
for npc in available_npcs:
    # Sympathy initialization happens in actor registry
    pass

# NOW narrate the scene
scene_description = narrator.generate_scene_with_narrative_loop(...)
```

### 2. Location Changes (Travel/Movement)

**Location:** `redesigned_main.py` in `_apply_location_move()` function

```python
def _apply_location_move(conductor, move_label, time_context, actor, 
                        prev_desc, narrative_context_manager, tracker, available_npcs):
    # ... existing code ...
    
    # Generate new scene description
    new_scene_desc = narrator.generate_location_transition(...)
    
    # PRE-POPULATE new location with NUAs
    from scene_population_system import populate_scene_with_nuas, replace_scene_npcs
    new_npcs = populate_scene_with_nuas(
        creator_agent=creator,  # Need to pass creator
        scene_description=new_scene_desc,
        time_context=time_context,
        full_population=True
    )
    
    # SAFELY REPLACE NPCs (prevents overlap bug)
    replace_scene_npcs(
        available_npcs=available_npcs,
        new_npcs=new_npcs,
        tracker=tracker,
        location_name=move_label
    )
    
    return new_scene_desc
```

**Alternative (Manual):**
```python
# Clear old NPCs
available_npcs.clear()

# Add new NPCs
available_npcs.extend(new_npcs)

# Save to disk
tracker.save_available_npcs(available_npcs)
```

### 3. Scene Transitions (ROAM → ENCOUNTER → ROAM)

**Location:** `redesigned_main.py` around line 3089

```python
# When returning to ROAM after encounter
scene_description = _generate_connected_roam_scene(...)

# RE-POPULATE scene (some NPCs may have left)
from scene_population_system import populate_scene_with_nuas
available_npcs = populate_scene_with_nuas(
    creator_agent=creator,
    scene_description=scene_description,
    time_context=master_time.get_current_time_context(),
    full_population=False  # Minimal population for quick transitions
)
```

## Population Templates

The system automatically detects scene types and populates appropriately:

### Diner
- **Guaranteed:** Waitress (1-2), Cook (1)
- **Possible:** Patrons (2-5), Manager (0-1)

### Bar
- **Guaranteed:** Bartender (1)
- **Possible:** Bouncer (0-1), Patrons (3-8), Musicians (0-3)

### Office
- **Guaranteed:** Receptionist (1)
- **Possible:** Security (1-2), Employees (2-6), Janitor (0-1)

### Street
- **Possible:** Vendors (0-2), Pedestrians (3-8), Homeless (0-2), Cops (0-2)

### Store
- **Guaranteed:** Clerk (1-2)
- **Possible:** Manager (0-1), Customers (1-4), Security (0-1)

### Club
- **Guaranteed:** Bouncer (1-2), Bartender (1-2)
- **Possible:** DJ (0-1), Patrons (5-15), Dealers (0-2)

## Configuration Options

### Full Population (Recommended for Main Scenes)
```python
available_npcs = populate_scene_with_nuas(
    creator_agent=creator,
    scene_description=scene_desc,
    time_context=time_context,
    full_population=True  # 2-8 NUAs depending on scene type
)
```

### Minimal Population (Quick Transitions)
```python
available_npcs = populate_scene_with_nuas(
    creator_agent=creator,
    scene_description=scene_desc,
    time_context=time_context,
    full_population=False  # 1-3 key NUAs only
)
```

## Implementation Checklist

- [ ] Import `populate_scene_with_nuas` in `redesigned_main.py`
- [ ] Add population call BEFORE initial scene narration
- [ ] Add population call in `_apply_location_move()`
- [ ] Add population call in ROAM scene generation
- [ ] Pass `creator` agent to location move function
- [ ] Test diner scene (should have waitress + cook + patrons)
- [ ] Test bar scene (should have bartender + patrons)
- [ ] Test street scene (should have pedestrians)
- [ ] Verify `/people` command shows pre-generated NUAs
- [ ] Verify interaction with NUA uses pre-generated sheet
- [ ] Verify sympathy initialized for all NUAs

## Testing

### Test 1: Diner Population
```
1. Start new session
2. Scene should be populated with 3-7 NUAs
3. Use `/people` - should list all NUAs
4. Approach any NUA - should use pre-generated sheet
5. Check NUA knows they're in a diner (not main street)
```

### Test 2: Location Change
```
1. Start in diner (3-7 NUAs)
2. Move to street
3. New population should generate (3-10 NUAs)
4. Use `/people` - should show new NUAs
5. Old diner NPCs should be gone
```

### Test 3: Progressive Revelation
```
1. Check NUA sheet - skills should show ???
2. Engage in exchange
3. Used skill should be revealed
4. Backend should have had real skill values all along
```

## Performance Considerations

**Generation Time:**
- Each NUA takes ~2-3 seconds to generate
- Full population (5 NUAs) = ~10-15 seconds
- Minimal population (2 NUAs) = ~4-6 seconds

**Optimization:**
- Use `full_population=False` for quick transitions
- Use `full_population=True` for major scenes
- Consider caching NUAs for frequently visited locations

## Future Enhancements

1. **Persistent NPCs** - Save NUAs per location across sessions
2. **Dynamic Population** - NPCs arrive/leave based on time
3. **Relationship Networks** - NPCs know each other
4. **Schedule System** - NPCs appear at certain times
5. **Memory Integration** - NPCs remember previous encounters

## Critical Notes

⚠️ **NEVER create NUAs on-demand during encounters**
⚠️ **ALWAYS pre-generate before scene narration**
⚠️ **ALWAYS clear actor registry at session start**
⚠️ **ALWAYS initialize sympathy for all pre-generated NUAs**

This system ensures narrative consistency and prevents the "wrong context" bug where NUAs don't know where they are.
