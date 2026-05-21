# Key Memories Actor Sheet Display Fix

## Problem

Key memories were not showing up in the actor sheet despite being created and saved.

## Root Cause

**Two issues:**

1. **Actor sheet was filtering too narrowly**
   - Only looked for memories tagged with `"character_background"`
   - Ignored `DISCOVERY` category memories (learned during gameplay)
   - Required BOTH `"character_background"` AND actor name tags

2. **Inquiry memories weren't tagged with actor name**
   - When creating inquiry memories, only keyword tags were added
   - Actor name tag was missing, so memories couldn't be filtered by actor

## Solution

### 1. Updated Actor Sheet Display Logic (`actor_sheet.py`)

**Before:**
```python
# Only show character_background memories
background_memories = [
    m for m in key_memories_system.memories.values()
    if "character_background" in m.tags and actor_tag in m.tags
]
```

**After:**
```python
# Show ALL memories for this actor (background + discoveries)
all_memories = [
    m for m in key_memories_system.memories.values()
    if actor_tag in m.tags or "character_background" in m.tags
]

# Sort by importance (major > significant > routine) then by timestamp
importance_order = {"major": 0, "significant": 1, "routine": 2}
all_memories.sort(key=lambda m: (
    importance_order.get(m.importance, 3),
    -m.timestamp  # Most recent first within same importance
))
```

**Changes:**
- ✅ Show memories with actor tag **OR** character_background tag (not AND)
- ✅ Include DISCOVERY category memories
- ✅ Sort by importance first, then recency
- ✅ Show up to 5 memories (increased from 3)

### 2. Added Actor Tag to Inquiry Memories (`redesigned_main.py`)

**Before:**
```python
memory_tags = extract_inquiry_keywords(user_input, answer=factual_answer)

key_memories.create_memory(
    title=f"Learned: {extract_inquiry_subject(user_input)}",
    description=factual_answer,
    full_narrative=f"Question: {user_input}\n\nAnswer: {factual_answer}",
    category=MemoryCategory.DISCOVERY,
    importance=MemoryImportance.ROUTINE,
    location=actor.sheet.location,
    tags=memory_tags  # Missing actor tag!
)
```

**After:**
```python
memory_tags = extract_inquiry_keywords(user_input, answer=factual_answer)

# Add actor name tag so memory shows up in actor sheet
actor_tag = actor.sheet.name.lower().replace(" ", "_")
if actor_tag not in memory_tags:
    memory_tags.append(actor_tag)

key_memories.create_memory(
    title=f"Learned: {extract_inquiry_subject(user_input)}",
    description=factual_answer,
    full_narrative=f"Question: {user_input}\n\nAnswer: {factual_answer}",
    category=MemoryCategory.DISCOVERY,
    importance=MemoryImportance.ROUTINE,
    location=actor.sheet.location,
    tags=memory_tags  # Now includes actor tag!
)
```

**Changes:**
- ✅ Generate actor tag from actor name (e.g., "Mara Lennox" → "mara_lennox")
- ✅ Add actor tag to memory tags list
- ✅ Ensures memory is associated with the actor

## Memory Types Now Displayed

The actor sheet now shows:

1. **Character Background Memories**
   - Created during character generation
   - Tagged with `"character_background"`
   - Personality traits, goals, backstory

2. **Discovery Memories**
   - Created when character learns something new
   - Category: `DISCOVERY`
   - Tagged with actor name + keywords

3. **Event Memories**
   - Important events during gameplay
   - Category: `EVENT`
   - Tagged with actor name + event keywords

## Display Priority

Memories are sorted by:
1. **Importance** (major → significant → routine)
2. **Recency** (newest first within same importance)

Shows **top 5 memories** maximum.

## Example Output

```
┌─────────────────────────────────────────────────────────┐
│ 🔑 KEY MEMORIES (Character-Defining) │
│ 1. A "heim" is a Z-Class Residential Stabilization Unit │
│    - specifically the Tempelhof Heim facility at        │
│    Columbiadamm 10, where non-compliant Z-Class donors  │
│    are reclassified into long-term storage.             │
│ 2. Your assistant is Klaus Richter, a junior clerk who  │
│    handles pneumatic tube routing and carbon copy       │
│    distribution for the Z-Classification department.    │
│ 3. Background: You are a meticulous bureaucrat who      │
│    takes pride in maintaining perfect compliance scores │
└─────────────────────────────────────────────────────────┘
```

## Testing

To verify the fix works:

1. **Create a new character**
2. **Ask an inquiry question**: "What is a heim?"
3. **Check actor sheet**: `ua`
4. **Verify memory appears** in KEY MEMORIES section

## Files Modified

- `actor_sheet.py` (lines 753-778) - Updated display logic
- `MAIN/redesigned_main.py` (lines 5868-5888) - Added actor tag to memories

## Benefits

✅ **All important memories now visible** in actor sheet
✅ **Sorted by importance** - major discoveries shown first
✅ **Properly tagged** - memories associated with correct actor
✅ **Comprehensive view** - background + discoveries + events
✅ **Recent first** - within same importance level
