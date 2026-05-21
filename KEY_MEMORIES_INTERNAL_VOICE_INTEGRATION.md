# Key Memories Integration with Internal Voice

## Overview

Integrated the **key memories system** with the **internal voice generation** to make character thoughts more personalized and grounded in their established background.

## What Was Added

### Location: `agents/narrator_agent.py` lines 3039-3067

Added key memories context extraction in `generate_internal_voice()` method:

```python
# Get key background memories for character context
key_memories_context = ""
try:
    from key_memories_system import get_key_memories
    key_memories_system = get_key_memories()
    
    # Get character-defining background memories
    actor_tag = ua_actor.sheet.name.lower().replace(" ", "_")
    background_memories = [
        m for m in key_memories_system.memories.values()
        if "character_background" in m.tags and actor_tag in m.tags
    ]
    
    if background_memories:
        # Sort by importance and take top 3
        importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
        background_memories.sort(key=lambda m: (
            importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
            -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp
        ))
        
        memory_summaries = []
        for mem in background_memories[:3]:
            memory_summaries.append(f"- {mem.description}")
        
        key_memories_context = "\n**KEY BACKGROUND MEMORIES (Character-Defining):**\n" + "\n".join(memory_summaries) + "\n"
except Exception:
    # If memories unavailable, continue without them
    pass
```

### Prompt Integration: Line 3156

Added memories to the LLM prompt context:

```python
**CURRENT STATE:**
- Stamina: {current_stamina}/10 | Spirit: {current_spirit}/10 | Supply: {current_supply}/10
- Current Task: {current_task if current_task else "None"}
- Key Items: {', '.join(inventory_items) if inventory_items else "None"}
- Relationships: {', '.join(relationships) if relationships else "None"}

{key_memories_context}  # ← NEW: Character-defining memories
**CURRENT ACTION:**
```

### Instruction Update: Line 3182

Added explicit instruction to reference memories:

```python
- **Can reference KEY BACKGROUND MEMORIES when relevant** - These define who the character is
```

## Benefits

### 1. **Character Consistency**
Internal voice now reflects the character's established background:
- Marta's thoughts can reference her mentor Fräulein Weber
- Can recall the disappearance of her brother Lukas
- Can think about the mysterious margin notes incident

### 2. **Deeper Immersion**
Thoughts feel more authentic because they're grounded in actual character history:
- "Like when Fräulein Weber taught us to read carbon copies..."
- "Just like Lukas before he vanished..."
- "Those margin notes... still don't understand how we wrote them before seeing the files..."

### 3. **Natural Memory Recall**
Characters can naturally reference their defining moments when relevant to current situations:
- Examining documents → Recalls mentor's training
- Seeing crowds → Thinks of brother's disappearance
- Finding anomalies → Remembers the pattern incident

### 4. **Personality + History**
Internal voice now combines:
- **Personality traits** (how they think)
- **Background memories** (what they've experienced)
- **Current state** (stamina, spirit, supply)
- **Current task** (what they're trying to do)
- **Relationships** (who they know)

## Example Output

**Before (without memories):**
```
💭 We should check this document carefully. Something feels off.
```

**After (with memories):**
```
💭 We should check this document carefully—just like Fräulein Weber taught us. 
   The ink sits wrong in the grain. Something feels off.
```

## Technical Details

**Memory Filtering:**
- Only includes `character_background` memories (not inquiry/discovery memories)
- Filters by actor name tag
- Sorts by importance (critical > important > notable > routine)
- Takes top 3 most important memories

**Error Handling:**
- Gracefully continues if key memories system unavailable
- No crashes if memories can't be loaded
- Silent failure with empty context

**Context Size:**
- Adds ~100-300 characters to prompt (3 memory descriptions)
- Minimal token overhead
- Only includes essential background info

## Integration Points

This enhancement works with:
- ✅ **ROAM mode** - All exploration actions
- ✅ **Personality system** - Memories + personality = authentic thoughts
- ✅ **Failure tracker** - Can reference past failures in context of memories
- ✅ **Task system** - Memories inform how character approaches tasks
- ✅ **Relationship system** - Memories about people affect thoughts about them

## Future Enhancements

Could also integrate memories into:
- **Inquiry responses** - Reference memories when answering questions
- **Narrative descriptions** - Mention memories when describing scenes
- **NPC dialogue** - NPCs reference shared memories
- **Decision making** - Memories influence choices

## Testing

To verify the integration:
1. Start simulation with character that has 3 background memories
2. Perform actions related to memory themes
3. Check if internal voice references memories naturally
4. Example: If memory mentions "mentor", examine a document and see if thoughts reference training

## Result

Internal voice is now **character-aware**, drawing from established background to create more authentic, personalized thoughts that reflect who the character actually is.
