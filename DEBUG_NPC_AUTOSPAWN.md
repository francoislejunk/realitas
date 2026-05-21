# Debug: NPC Auto-Spawn System

## Issue Reported

NPCs/INUAs are not being added to the available actor list when entering new scenes, even though the auto-spawn system is implemented.

## Debug Output Added

Added comprehensive debug logging to `scene_npc_parser.py` to diagnose the issue:

### 1. Auto-Spawn Entry Point (line 322-332)
```python
print(f"[NPC PARSER] Starting auto-spawn analysis...")
print(f"[NPC PARSER] Scene length: {len(scene_description)} characters")
print(f"[NPC PARSER] Detected {len(detected_npcs)} NPC(s) in scene")
```

**What this shows:**
- When auto-spawn is triggered
- How long the scene description is
- How many NPCs were detected

### 2. LLM Extraction Process (line 86-120)
```python
print(f"[NPC PARSER] Calling LLM to extract NPCs from scene...")
print(f"[NPC PARSER] LLM response received: {len(response_content)} characters")
print(f"[NPC PARSER] Raw NPC count from LLM: {len(npcs)}")
print(f"[NPC PARSER] Valid NPC count after filtering: {len(valid_npcs)}")
for npc in valid_npcs:
    print(f"[NPC PARSER]   - {npc.get('name')} ({npc.get('role')})")
```

**What this shows:**
- When LLM is called
- LLM response size
- How many NPCs the LLM found
- How many passed validation
- List of each detected NPC with name and role

### 3. Spawn Success/Failure (line 338-378)
```python
print(f"[NPC PARSER] Detected mentioned NPC: {npc_name} ({npc_data.get('role')})")
print(f"✓ Auto-spawned NPC: {new_nua.sheet.name} (Role: {npc_data.get('role')})")
print(f"[NPC PARSER] Failed to spawn {npc_name}: {e}")
```

**What this shows:**
- Which NPCs are being processed
- Which NPCs successfully spawn
- Error messages if spawning fails

## Integration Points

Auto-spawn is called in two places:

### 1. Initial Scene (line 2686 in redesigned_main.py)
```python
spawned_count = auto_spawn_scene_npcs(
    scene_description=scene_description,
    creator_agent=scene_creator,
    available_npcs=available_npcs,
    continuity_validator=continuity_validator,
    auto_memory_creator=auto_memory_creator,
    actor_name=actor.sheet.name,
    scene_id=scene_id
)
```

### 2. After Actions (line 4047 in redesigned_main.py)
```python
spawned_count = auto_spawn_scene_npcs(
    scene_description=contextual_result,
    creator_agent=scene_creator,
    available_npcs=available_npcs,
    continuity_validator=continuity_validator,
    auto_memory_creator=auto_memory_creator,
    actor_name=actor.sheet.name,
    scene_id=scene_id
)
```

## How to Diagnose

When you run the simulation, you should now see output like:

### Scenario 1: NPCs Detected and Spawned
```
[NPC PARSER] Starting auto-spawn analysis...
[NPC PARSER] Scene length: 543 characters
[NPC PARSER] Calling LLM to extract NPCs from scene...
[NPC PARSER] LLM response received: 234 characters
[NPC PARSER] Raw NPC count from LLM: 1
[NPC PARSER] Valid NPC count after filtering: 1
[NPC PARSER]   - Cab Driver (cab driver)
[NPC PARSER] Detected 1 NPC(s) in scene
[NPC PARSER] Detected mentioned NPC: Cab Driver (cab driver)
✓ Auto-spawned NPC: Cab Driver (Role: cab driver)
[NPC PARSER] Auto-spawned 1 NPC(s) from scene
```

### Scenario 2: No NPCs Detected
```
[NPC PARSER] Starting auto-spawn analysis...
[NPC PARSER] Scene length: 543 characters
[NPC PARSER] Calling LLM to extract NPCs from scene...
[NPC PARSER] LLM response received: 45 characters
[NPC PARSER] Raw NPC count from LLM: 0
[NPC PARSER] Valid NPC count after filtering: 0
[NPC PARSER] Detected 0 NPC(s) in scene
[NPC PARSER] No NPCs detected in scene description
```

### Scenario 3: Detection Works but Spawning Fails
```
[NPC PARSER] Starting auto-spawn analysis...
[NPC PARSER] Scene length: 543 characters
[NPC PARSER] Calling LLM to extract NPCs from scene...
[NPC PARSER] LLM response received: 234 characters
[NPC PARSER] Raw NPC count from LLM: 1
[NPC PARSER] Valid NPC count after filtering: 1
[NPC PARSER]   - Cab Driver (cab driver)
[NPC PARSER] Detected 1 NPC(s) in scene
[NPC PARSER] Detected mentioned NPC: Cab Driver (cab driver)
[NPC PARSER] Failed to spawn Cab Driver: [error message]
```

## Possible Issues

Based on the debug output, we can identify:

1. **LLM Not Detecting NPCs**
   - Output shows "Raw NPC count from LLM: 0"
   - Issue: LLM prompt may need adjustment or scene descriptions don't mention NPCs clearly

2. **NPCs Filtered Out**
   - Output shows raw count > 0 but valid count = 0
   - Issue: NPCs missing required fields (name, role)

3. **Spawning Fails**
   - Output shows detection but "Failed to spawn" message
   - Issue: CreatorAgent.generate_nua() is failing

4. **Auto-Spawn Not Called**
   - No "[NPC PARSER] Starting auto-spawn analysis..." message
   - Issue: Integration point not being reached or exception thrown before call

## Next Steps

1. **Run the simulation** and watch for the debug output
2. **Copy the output** and share it to identify which scenario is happening
3. **Based on the output**, we can pinpoint exactly where the issue is:
   - Detection problem → Adjust LLM prompt
   - Spawning problem → Fix CreatorAgent integration
   - Integration problem → Check main loop flow

## Testing

To test if auto-spawn is working:

1. Start a new simulation
2. Look for the debug messages in the terminal
3. Check if NPCs are being detected
4. Check if they're being spawned successfully
5. Try interacting with a detected NPC (e.g., "I talk to the cab driver")

The debug output will tell us exactly what's happening at each step.
