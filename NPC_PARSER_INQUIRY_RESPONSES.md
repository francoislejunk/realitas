# NPC Parser Now Runs on Inquiry Responses

## The Problem

When the narrator generated an inquiry response mentioning NPCs:
```
"You lock eyes with a man in a worn leather jacket standing 
a few paces away..."
```

The NPC parser **did not detect** this new NPC because it only ran:
1. At initial scene setup
2. After scene transitions

It did **not** run on dynamically generated narrative from inquiry responses.

## The Solution

Added NPC parser calls after **both** successful and failed inquiry responses.

## Where NPC Parser Now Runs

### 1. Initial Scene Setup ✅
```python
# When scene first loads
auto_spawn_npcs_from_scene(scene_description=initial_scene, ...)
```

### 2. Scene Transitions ✅
```python
# When moving to new location
auto_spawn_npcs_from_scene(scene_description=new_scene, ...)
```

### 3. **NEW:** Successful Inquiry Responses ✅
```python
# After narrator generates inquiry answer
answer = narrator.generate_inquiry_response(...)
print(answer)

# NOW: Parse the answer for NPCs
auto_spawn_npcs_from_scene(scene_description=answer, ...)
```

### 4. **NEW:** Failed Inquiry Responses ✅
```python
# After narrator generates uncertainty response
uncertainty = process_failed_inquiry(...)
print(uncertainty)

# NOW: Parse the uncertainty for NPCs
auto_spawn_npcs_from_scene(scene_description=uncertainty, ...)
```

## Example Flow

### Before (Broken):
```
User: "Where am I?"

Narrator: "You lock eyes with a man in a worn leather jacket..."
[NPC Parser: NOT TRIGGERED]

User: "I approach him"
System: ⚠️ There is no 'him' in the scene description.
```

### After (Fixed):
```
User: "Where am I?"

Narrator: "You lock eyes with a man in a worn leather jacket..."
[NPC PARSER] Starting auto-spawn analysis...
[NPC PARSER] Detected 1 NPC(s) in scene
[NPC PARSER] Auto-spawned 1 NPC(s) from inquiry response
✓ Created NUA: Man in Leather Jacket

User: "I approach him"
System: ✓ Processes encounter with the man
```

## Files Modified

**`MAIN/redesigned_main.py`:**

1. **Lines 4706-4719:** Added NPC parser after successful inquiry response
   ```python
   # Display narrative answer
   print(f"{Color.NARRATIVE}{answer}{Color.RESET}\n")
   
   # Check for NPCs mentioned in the inquiry response
   spawned_count = auto_spawn_npcs_from_scene(
       scene_description=answer,  # Parse the inquiry response
       available_npcs=available_npcs,
       actor_generator=actor_generator,
       scene_id=scene_id
   )
   ```

2. **Lines 4788-4801:** Added NPC parser after failed inquiry response
   ```python
   # Display uncertainty
   print(f"{Color.NARRATIVE}{uncertainty}{Color.RESET}\n")
   
   # Check for NPCs mentioned in the failed inquiry response
   spawned_count = auto_spawn_npcs_from_scene(
       scene_description=uncertainty,  # Parse the uncertainty response
       available_npcs=available_npcs,
       actor_generator=actor_generator,
       scene_id=scene_id
   )
   ```

## Result

✅ NPCs mentioned in inquiry responses are now automatically detected and spawned  
✅ Players can interact with NPCs that appear in dynamically generated narrative  
✅ No more "There is no 'him' in the scene description" errors  
✅ Consistent NPC detection across all narrative sources

The NPC parser now runs on **all narrative output**, not just initial scenes and transitions.
