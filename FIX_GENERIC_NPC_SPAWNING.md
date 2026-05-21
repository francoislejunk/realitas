# Fix: Generic NPC Auto-Spawning

## Problem Identified

When the scene description mentioned environmental elements like "a yellow cab", the cab driver was not being created as an interactable NPC. This caused validation errors when the user tried to interact with them:

```
⚠️ There is no cab or cab driver present in the scene.
```

## Root Cause

The `scene_npc_parser.py` was configured to **only spawn named NPCs** (like "Linda the waitress" or "Marcus the bartender"), explicitly excluding generic role-based NPCs:

```python
# OLD BEHAVIOR:
DO NOT extract:
- Generic descriptions without names ("a waitress", "the bartender")
```

This meant that when a scene mentioned "a yellow cab", the system:
1. ✅ Included the cab in the scene description
2. ❌ Did NOT create a "Cab Driver" NPC
3. ❌ Blocked user attempts to interact with the non-existent driver

## Solution Implemented

Modified `scene_npc_parser.py` to detect and spawn **both named AND generic role-based NPCs**:

### Changes Made

**File:** `scene_npc_parser.py` (lines 33-83)

**New Behavior:**
```python
Look for:
1. **Named characters** who are physically present ("Linda the waitress approaches")
2. **Generic role-based characters** who are clearly present and interactable ("a cab driver", "the bartender")
3. Characters the protagonist can see/interact with directly
4. People operating vehicles mentioned in the scene ("a yellow cab" → extract "cab driver")
```

**Examples of what NOW gets extracted:**
- ✅ "A yellow cab idles at the curb" → Extract as "Cab Driver" (generic, role: cab driver)
- ✅ "The bartender wipes down the counter" → Extract as "Bartender" (generic, role: bartender)
- ✅ "A security guard stands by the door" → Extract as "Security Guard" (generic, role: security guard)

**Generic NPC Naming Convention:**
- Use their role as the name (e.g., "Cab Driver", "Bartender", "Security Guard")
- Capitalize the role to make it a proper name
- Include enough detail to make them interactable

## Result

Now when a scene mentions:
- "A yellow cab" → System auto-spawns "Cab Driver" NPC
- "The bartender" → System auto-spawns "Bartender" NPC
- "A security guard" → System auto-spawns "Security Guard" NPC

Users can immediately interact with these NPCs without validation errors.

## Testing

To test this fix:
1. Start a new simulation
2. Wait for a scene that mentions a vehicle or service person
3. Try to interact with them (e.g., "I talk to the cab driver")
4. The NPC should now exist and be interactable

## Technical Details

**Auto-Spawn Flow:**
1. Scene description is generated
2. `auto_spawn_scene_npcs()` is called (lines 2686 and 4047 in `redesigned_main.py`)
3. `SceneNPCParser.extract_npcs_from_scene()` analyzes the scene
4. LLM extracts both named and generic NPCs
5. Each detected NPC is spawned via `creator_agent.generate_nua()`
6. NPCs are added to `available_npcs` list
7. User can now interact with them

**Integration Points:**
- Initial scene spawn: `redesigned_main.py` line 2686
- Post-action spawn: `redesigned_main.py` line 4047
- Parser logic: `scene_npc_parser.py` lines 33-102

## Benefits

1. **More Immersive** - NPCs mentioned in narration are immediately interactable
2. **Fewer Errors** - No more "NPC doesn't exist" validation errors
3. **Better Continuity** - Scene descriptions and available NPCs stay in sync
4. **Natural Interaction** - Users can interact with anyone mentioned in the scene

## Notes

- Generic NPCs still get full character generation (stats, personality, goals)
- They're treated identically to named NPCs once spawned
- The system still avoids spawning vague background crowds
- Only clearly interactable characters are spawned
