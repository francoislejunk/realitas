# Built-In Memories Now Persist to Disk

## The Problem

Built-in memories were only stored in `ActorSheet.memories` (in-memory list), not in the **Key Memories System** (persistent disk storage):

```
User: "memories"
Result: ❌ "No memories found matching criteria."

Reason: Built-in memories weren't in the Key Memories System
```

This meant:
- **Not searchable** via `memories` command
- **Not persistent** across sessions
- **Not accessible** to LLM context
- **Separate from other memories** (inconsistent)

## The Solution

Added automatic registration of built-in memories to the Key Memories System when an actor is created:

```python
def _register_builtin_memories(self):
    """Register built-in memories to the Key Memories System for persistence"""
    key_memories = get_key_memories()
    
    for idx, memory_text in enumerate(self.memories, 1):
        key_memories.create_memory(
            title=f"{self.name} - Background #{idx}",
            description=memory_text,
            category=MemoryCategory.CHARACTER,
            importance=MemoryImportance.NOTABLE,
            tags=["background", "builtin", self.name.lower()]
        )
```

## How It Works

### Character Creation Flow

```
1. NPC Generated
   ↓
2. ActorSheet Created with memories=[...]
   ↓
3. _register_builtin_memories() called
   ↓
4. Each memory added to Key Memories System
   ↓
5. Memories saved to disk
   ↓
6. Memories now accessible via "memories" command
```

### Example

```python
# NPC generated with memories
nua_sheet = ActorSheet(
    name="Marcus Chen",
    occupation="Street Vendor",
    memories=[
        "Immigrated from Hong Kong at age 15 with his family",
        "Lost parents in a fire, now takes care of younger sister",
        "Learned cooking from his grandmother's traditional recipes",
        "Knows every street vendor and shop owner in the district"
    ]
)

# Automatically registers to Key Memories System:
# → Marcus Chen - Background #1
# → Marcus Chen - Background #2
# → Marcus Chen - Background #3
# → Marcus Chen - Background #4
```

## Memory Structure

Each built-in memory is stored as:

```json
{
    "memory_id": "mem_0_1699123456.789",
    "title": "Marcus Chen - Background #1",
    "description": "Immigrated from Hong Kong at age 15 with his family",
    "full_narrative": "Background memory about Marcus Chen: Immigrated from Hong Kong at age 15 with his family",
    "category": "character",
    "importance": "notable",
    "location": "Downtown",
    "actors_involved": ["Marcus Chen"],
    "tags": ["background", "builtin", "marcus_chen"],
    "turn_number": 0,
    "scene_id": "character_creation"
}
```

## Benefits

### 1. Searchable

```
User: "memories"
Result: Shows all memories including built-in ones

User: "/mem search Marcus"
Result: Shows all Marcus-related memories
```

### 2. Persistent

```
Session 1: NPC created with memories
Session 2: Memories still available
Session 3: Memories still available
```

### 3. LLM Context

```
When LLM generates responses, it can access:
- Built-in memories (character background)
- Discovered memories (gameplay events)
- All in one unified system
```

### 4. Unified System

```
All memories in one place:
- Built-in (from character creation)
- Discovered (from inquiries)
- Created (from narration)
- Manual (from user notes)
```

## Example Output

### Before (Not Persistent)

```
User: "memories"
No memories found matching criteria.

User: "ua" (view Marcus's sheet)
📚 BACKGROUND MEMORIES:
   1. Immigrated from Hong Kong at age 15
   2. Lost parents in a fire
   3. Learned cooking from grandmother
   4. Knows every street vendor

❌ Memories only in actor sheet, not searchable
```

### After (Persistent)

```
User: "memories"

════════════════════════════════════════════════════════════════════
📚 KEY MEMORIES (4 total)
════════════════════════════════════════════════════════════════════

[1] 🟡 Marcus Chen - Background #1 (character)
    Immigrated from Hong Kong at age 15 with his family
    📍 Downtown | 👥 Marcus Chen
    🏷️  background, builtin, marcus_chen

[2] 🟡 Marcus Chen - Background #2 (character)
    Lost parents in a fire, now takes care of younger sister
    📍 Downtown | 👥 Marcus Chen
    🏷️  background, builtin, marcus_chen

[3] 🟡 Marcus Chen - Background #3 (character)
    Learned cooking from his grandmother's traditional recipes
    📍 Downtown | 👥 Marcus Chen
    🏷️  background, builtin, marcus_chen

[4] 🟡 Marcus Chen - Background #4 (character)
    Knows every street vendor and shop owner in the district
    📍 Downtown | 👥 Marcus Chen
    🏷️  background, builtin, marcus_chen

════════════════════════════════════════════════════════════════════

✓ Memories searchable, persistent, and accessible
```

## Search Examples

### Search by Name

```
User: "/mem search Marcus"
Result: Shows all 4 Marcus background memories
```

### Search by Tag

```
User: "/mem search background"
Result: Shows all built-in background memories for all characters
```

### Search by Category

```
User: "memories" → filter by CHARACTER category
Result: Shows all character-related memories
```

## Storage Location

Memories are saved to:
```
simulation_data/
  key_memories/
    {session_id}_memories.json
```

Example file structure:
```json
{
  "memories": [
    {
      "memory_id": "mem_0_1699123456.789",
      "title": "Marcus Chen - Background #1",
      "description": "Immigrated from Hong Kong at age 15...",
      "category": "character",
      "importance": "notable",
      "tags": ["background", "builtin", "marcus_chen"],
      ...
    },
    ...
  ]
}
```

## Integration Points

### 1. Character Creation
- ActorSheet.__init__() calls _register_builtin_memories()
- Memories automatically added to Key Memories System

### 2. NPC Generation
- CreatorAgent generates NPC with memories
- ActorSheet created with memories list
- Memories registered to Key Memories System

### 3. User Actor Creation
- User Actor created with memories
- Memories registered to Key Memories System
- Available via "memories" command

## Error Handling

```python
try:
    key_memories = get_key_memories()
    # Register memories...
except Exception as e:
    # If Key Memories System not initialized, that's okay
    # Memories still in ActorSheet.memories
    pass
```

If the Key Memories System isn't initialized yet (e.g., during testing), memories remain in `ActorSheet.memories` and won't cause errors.

## Files Modified

**`actor_sheet.py`** (lines 229-272)
1. Added call to `_register_builtin_memories()` in `__init__`
2. Added `_register_builtin_memories()` method
3. Registers each memory to Key Memories System
4. Batch saves all memories at once

## Result

✅ **Built-in memories persist to disk** - Saved in Key Memories System  
✅ **Searchable** - Via `memories` and `/mem search` commands  
✅ **Accessible to LLM** - Part of context  
✅ **Unified system** - All memories in one place  
✅ **Session persistent** - Available across sessions  
✅ **Dual display** - In actor sheet AND memories list  

Built-in memories are now part of the persistent Key Memories System!
