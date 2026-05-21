# Key Memories Implementation for All Actors

## Overview

Every actor (UA and NUA) now gets exactly **3 character-defining key memories** generated during creation. These memories:
- Appear at the bottom of actor sheets
- Are stored in the KeyMemoriesSystem
- Show up with the `memories` command
- Help define who the character is

## What Are Key Memories?

Character-defining memories that shaped who the actor is. Examples:
- **Childhood trauma**: "At age 12, witnessed their father arrested for filing incorrect paperwork - learned that precision saves lives"
- **Strong connection**: "Still wears their father's union badge from the 1960s strikes"
- **Defining habit**: "Every morning, arranges their desk items in the exact same order before starting work"
- **Loss or achievement**: "Lost their best friend in a workplace accident that management covered up"
- **Secret carried**: "Maintains a secret ledger of favors owed and debts to collect"

## Implementation

### 1. Actor Sheet Display

**File:** `actor_sheet.py`

Added `key_memories` field and display section:

```python
# In __init__
self.key_memories: List[str] = []  # Exactly 3 character-defining memories

# In display_detailed() - at bottom of sheet
print(f"🔑 KEY MEMORIES (Character-Defining)")
for i, memory in enumerate(self.key_memories, 1):
    print(f"{i}. {memory}")
```

**Display Example:**
```
┌─────────────────────────────────────────────────────────┐
│ 🎭 Lena Voss           │ 💼 PDP Containment Officer      │
│ 🎂 Age: 28 • 📍 Location: Berlin 1970                   │
│ ═══════════════════════════════════════════════════════ │
...
├─────────────────────────────────────────────────────────┤
│ 🔑 KEY MEMORIES (Character-Defining)                    │
│ 1. At age 12, witnessed father arrested for filing     │
│    incorrect paperwork - learned precision saves lives  │
│ 2. Keeps hidden collection of "misclassified"          │
│    documents that should have been destroyed            │
│ 3. Every morning, arranges desk items in exact same    │
│    order before starting work                           │
└─────────────────────────────────────────────────────────┘
```

### 2. Memory Generation

**File:** `key_memory_generator.py` (NEW)

LLM-powered generation of exactly 3 memories:

```python
def generate_key_memories(
    actor_name, age, occupation,
    personality_internal, personality_external,
    location, rag_system
) -> List[str]:
    # Generates 3 character-defining memories
    # Uses worldbuilding context from RAG
    # Returns list of exactly 3 memory strings
```

**Features:**
- Uses RAG worldbuilding context for period-appropriate details
- Considers character's age, occupation, personality, location
- Ensures variety (trauma, connection, habit, etc.)
- Falls back gracefully if LLM fails

### 3. CreatorAgent Integration

**File:** `agents/creator_agent.py`

Added `_add_key_memories_to_actor()` method:

```python
def _add_key_memories_to_actor(self, actor_sheet: ActorSheet):
    # Generate 3 memories
    memories = generate_key_memories(...)
    
    # Store in actor sheet (for display)
    actor_sheet.key_memories = memories
    
    # Store in KeyMemoriesSystem (for 'memories' command)
    for i, memory in enumerate(memories, 1):
        self.key_memories_system.create_memory(
            title=f"{actor_sheet.name} - Background #{i}",
            description=memory,
            category=MemoryCategory.DISCOVERY,
            importance=MemoryImportance.NOTABLE,
            tags=["character_background", "defining_memory"]
        )
```

**Called After:**
- UA creation (line 382)
- NUA creation (line 218)

### 4. Memories Command Integration

The memories are automatically available via the existing `memories` command because they're stored in KeyMemoriesSystem with the tag `character_background`.

**Usage:**
```
(What do you want to do?): memories

══════════════════════════════════════════════════════════
💭 YOUR MEMORIES (5)
══════════════════════════════════════════════════════════

⚪ NOTABLE EVENTS:
     [1] Lena Voss - Background #1
       discovery • Nov 21, 2025
       At age 12, witnessed father arrested for filing incorrect
       paperwork - learned precision saves lives

     [2] Lena Voss - Background #2
       discovery • Nov 21, 2025
       Keeps hidden collection of "misclassified" documents that
       should have been destroyed

     [3] Lena Voss - Background #3
       discovery • Nov 21, 2025
       Every morning, arranges desk items in exact same order
       before starting work
```

## Files Modified

1. **`actor_sheet.py`**
   - Added `key_memories: List[str]` field
   - Added KEY MEMORIES display section at bottom of sheet
   - Word-wrapping for long memories

2. **`key_memory_generator.py`** (NEW)
   - `generate_key_memories()` - LLM-powered generation
   - `generate_fallback_memories()` - Fallback if LLM fails
   - Supports both standard and reasoning models (MiniMax M2)

3. **`agents/creator_agent.py`**
   - Added import: `from key_memory_generator import generate_key_memories`
   - Added `_add_key_memories_to_actor()` method
   - Called after UA creation (line 382)
   - Called after NUA creation (line 218)

## Testing

1. **Create new character**:
   - Start new simulation
   - Character is generated with 3 key memories

2. **View actor sheet**:
   ```
   (What do you want to do?): ua
   ```
   - Scroll to bottom to see KEY MEMORIES section

3. **View via memories command**:
   ```
   (What do you want to do?): memories
   ```
   - See character background memories listed

4. **View NPC sheet**:
   ```
   (What do you want to do?): people
   (Select NPC)
   ```
   - NPC also has 3 key memories

## Benefits

1. **Character Depth** - Every actor has a rich backstory from creation
2. **Narrative Consistency** - Memories inform how character behaves
3. **Player Immersion** - Understanding character motivations
4. **LLM Context** - Memories available to narrator/conductor for better roleplay
5. **Worldbuilding Integration** - Memories reflect the 1970s setting

## Notes

- Memories are generated **once** at character creation
- Exactly **3 memories** - no more, no less
- Stored in **two places**:
  - `actor_sheet.key_memories` (for display)
  - `KeyMemoriesSystem` (for memories command)
- Uses **RAG worldbuilding** for period-appropriate details
- Works for **both UA and NUA**
