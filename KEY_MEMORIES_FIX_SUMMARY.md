# Key Memories System - Fixed

## Problem Identified

The key memories system had a **mismatch between enum values and display code**:

- **MemoryImportance enum** uses: `critical`, `important`, `notable`, `routine`
- **Display code** was checking for: `major`, `significant`, `routine`

This caused memories to never display properly on the actor sheet or in the memories command.

## Fixes Applied

### 1. Actor Sheet Display (`actor_sheet.py` lines 770-775)

**Before:**
```python
importance_order = {"major": 0, "significant": 1, "routine": 2}
all_memories.sort(key=lambda m: (
    importance_order.get(m.importance, 3),
    -m.timestamp
))
```

**After:**
```python
importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
all_memories.sort(key=lambda m: (
    importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
    -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp
))
```

### 2. Memories Command Display (`MAIN/redesigned_main.py` lines 3231-3239)

**Before:**
```python
importance_order = {"major": 0, "significant": 1, "routine": 2}
actor_memories.sort(key=lambda m: (
    importance_order.get(m.importance, 3),
    -m.timestamp
))

for i, memory in enumerate(actor_memories, 1):
    importance_icon = {"major": "⭐", "significant": "✨", "routine": "💡"}.get(memory.importance, "📝")
```

**After:**
```python
importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
actor_memories.sort(key=lambda m: (
    importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
    -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp
))

for i, memory in enumerate(actor_memories, 1):
    importance_value = memory.importance.value if hasattr(memory.importance, 'value') else memory.importance
    importance_icon = {"critical": "🔴", "important": "🟡", "notable": "🔵", "routine": "⚪"}.get(importance_value, "📝")
```

## What Was Already Correct

✅ **Memory Creation** - `creator_agent.py` correctly uses `MemoryImportance.NOTABLE`, etc.
✅ **Memory Storage** - `key_memories_system.py` properly stores enum values
✅ **Memory Tags** - Correct tags: `character_background`, `defining_memory`, actor name
✅ **Memory Filtering** - Actor sheet correctly filters by tags

## Result

Memories will now:
- ✅ Display correctly on actor sheet
- ✅ Show proper importance icons (🔴 critical, 🟡 important, 🔵 notable, ⚪ routine)
- ✅ Sort by importance then recency
- ✅ Work with both enum and string values (defensive coding)

## Testing

To verify the fix:
1. Start simulation with existing character
2. Type `memories` or `/mem` to view memories
3. Check actor sheet with detailed display
4. Memories should now appear with correct icons and sorting
