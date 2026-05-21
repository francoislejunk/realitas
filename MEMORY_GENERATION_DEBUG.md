# Memory Generation Debugging Guide

## Problem
Actor sheet shows "No key memories yet" even though `generate_initial_memories` should create 3 memories during character creation.

## Root Causes

### Possible Issues:
1. **LLM call failed** - API error, timeout, or invalid response
2. **JSON parsing failed** - LLM returned malformed JSON
3. **KeyMemoriesSystem not initialized** - System wasn't available during creation
4. **Silent failure** - Error was caught but not logged clearly

## Fixes Applied

### 1. Enhanced Error Reporting in `creator_agent.py`

**Added logging for:**
- Raw LLM response length
- JSON parsing errors with content preview
- KeyMemoriesSystem availability check
- Individual memory creation success/failure
- Final summary of created memories
- Full traceback on exceptions

**New log messages:**
```
DEBUG: Raw memory generation response length: X chars
WARNING: Expected 3 memories, got X
ERROR: KeyMemoriesSystem not available - memories cannot be saved!
✓ Created initial memory: [title] (ID: [id])
ERROR: Failed to create memory - create_memory returned None
✓ Successfully created X/3 initial memories for [name]
ERROR: Failed to parse memory JSON: [error]
```

### 2. Created Regeneration Utility

**File:** `regenerate_memories.py`

**Usage:**
```python
# In your simulation, after loading a character:
from regenerate_memories import regenerate_memories_for_actor
regenerate_memories_for_actor(actor)
```

**Features:**
- Checks for existing memories
- Prompts before deleting old memories
- Generates 3 new memories
- Shows success/failure with details

## How to Debug Your Current Character

### Step 1: Check Logs
Look for these messages in your simulation logs:
```
🧠 Generating foundational memories for Rowan Ives...
Generating 3 key memories for Rowan Ives...
✓ Created initial memory: [title] (ID: [id])
✓ Successfully created 3/3 initial memories for Rowan Ives
```

**If you see errors:**
- `ERROR: KeyMemoriesSystem not available` → System wasn't initialized
- `ERROR: Failed to parse memory JSON` → LLM returned bad JSON
- `ERROR: No response from LLM` → API call failed

### Step 2: Check KeyMemoriesSystem
```python
from key_memories_system import get_key_memories
kms = get_key_memories()

# Check total memories
print(f"Total memories: {len(kms.memories)}")

# Check for your character's memories
actor_tag = "rowan_ives"  # Your character name in snake_case
background_memories = [
    m for m in kms.memories.values()
    if "character_background" in m.tags and actor_tag in m.tags
]
print(f"Background memories for Rowan Ives: {len(background_memories)}")

# Show all memories
for mem in background_memories:
    print(f"  - {mem.title}: {mem.description}")
```

### Step 3: Regenerate Memories
```python
# In your simulation:
from regenerate_memories import regenerate_memories_for_actor
memories = regenerate_memories_for_actor(actor)

# Then display actor sheet again
actor.sheet.display_detailed()
```

## Memory Storage Details

### Tags Required:
Memories must have these tags to appear on actor sheet:
1. `"character_background"` - Identifies as background memory
2. `"defining_memory"` - Marks as character-defining
3. `"rowan_ives"` - Actor name in snake_case

### Storage Location:
- **In-memory:** `KeyMemoriesSystem.memories` dictionary
- **On-disk:** `simulation_data/key_memories.json`

### Retrieval Logic:
```python
# From actor_sheet.py line 764-767
actor_tag = self.name.lower().replace(" ", "_")
background_memories = [
    m for m in key_memories_system.memories.values()
    if "character_background" in m.tags and actor_tag in m.tags
]
```

## Expected Behavior

### During Character Creation:
1. `CreatorAgent` generates actor profile
2. `main()` calls `creator_agent.generate_initial_memories(actor)`
3. LLM generates 3 memories as JSON
4. Each memory is saved to `KeyMemoriesSystem` with proper tags
5. Logs show: "✓ Successfully created 3/3 initial memories"

### When Displaying Actor Sheet:
1. Actor sheet queries `KeyMemoriesSystem`
2. Filters by `character_background` + actor name tag
3. Displays up to 3 memories
4. Shows "No key memories yet" if none found

## Testing Checklist

After regenerating memories:
- [ ] Logs show "✓ Successfully created 3/3 initial memories"
- [ ] `len(kms.memories)` increased by 3
- [ ] Memories have correct tags: `character_background`, `defining_memory`, `rowan_ives`
- [ ] Actor sheet displays 3 memories in "KEY MEMORIES" section
- [ ] `memories` command shows the memories
- [ ] Memories persist after saving/loading session

## Common Issues

### Issue: "No response from LLM"
**Cause:** API timeout or connection error
**Fix:** Check internet connection, API key, OpenRouter status

### Issue: "Failed to parse memory JSON"
**Cause:** LLM returned text instead of JSON
**Fix:** Check prompt, try regenerating, verify model supports JSON

### Issue: "KeyMemoriesSystem not available"
**Cause:** System not initialized before character creation
**Fix:** Ensure `get_key_memories()` is called in `main()` before creating actors

### Issue: Memories created but not showing
**Cause:** Wrong tags or actor name mismatch
**Fix:** Check tags match exactly: `"character_background"` and `"rowan_ives"`

## Files Modified

1. **`agents/creator_agent.py`** (lines 2136-2230)
   - Added comprehensive error logging
   - Added success confirmations
   - Added traceback on failures

2. **`regenerate_memories.py`** (new file)
   - Utility to regenerate memories for existing characters
   - Interactive prompts for safety
   - Detailed status reporting

## Next Steps

1. **Start a new character** and watch logs for memory generation
2. **For existing character (Rowan Ives):**
   ```python
   from regenerate_memories import regenerate_memories_for_actor
   regenerate_memories_for_actor(actor)
   ```
3. **Check logs** for any errors during generation
4. **Verify memories appear** on actor sheet
