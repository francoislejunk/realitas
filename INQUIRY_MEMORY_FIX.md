# Inquiry Memory System Fix

## Problem Identified

The inquiry memory system was showing **redundant and confusing output**:

```
💭 We should avoid the main roads, they're probably watched...
🔵 Memory Saved: Knowledge: What's the best way to get to downtown from here?...

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Knowledge: What's the best way to get to downtown from here?...
When asked 'What's the best way to get to downtown from here?', we recalled: We should avoid the main roads...

💭 Internal Voice:
We should avoid the main roads...
```

**Issues:**
1. Repeated the question twice
2. Said the same thing three times
3. Redundant "When asked X, we recalled Y" wrapper
4. Internal voice shown twice (once standalone, once in memory display)

## Solution Applied

### Three Clear Paths for Inquiries:

**Option 1 - Existing Memory:**
```
💭 I know the #7 bus runs from the warehouse district to downtown. Takes about 15 minutes.
```

**Option 2 - New Memory Created:**
```
💭 I know the #7 bus runs from the warehouse district to downtown. Takes about 15 minutes.

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Downtown Bus Route
I know the #7 bus runs from the warehouse district to downtown.

════════════════════════════════════════════════════════════
```

**Option 3 - No Memory, Don't Know:**
```
💭 I've never been to downtown from here before. Maybe I should ask someone, or look for a bus stop nearby.
```

## Changes Made

### 1. `intent_based_memory_creation.py`

**Line 363-364:** Removed redundant wrapper
```python
# OLD:
memory_title = f"Knowledge: {question[:50]}..."
memory_description = f"When asked '{question}', we recalled: {answer}"

# NEW:
memory_title = f"Downtown Route Knowledge"
memory_description = answer  # Just the knowledge itself
```

**Line 867:** Added `show_internal_voice` parameter
```python
def display_memory_creation(memory_result: dict, narrative_context_manager=None, 
                          actor_name: str = "User Actor", show_internal_voice: bool = False):
```

**Lines 898-906:** Simplified display, conditional internal voice
```python
# Show title and description
print(f"\n📝 {memory_result.get('memory_title', 'Memory')}")
print(f"{memory_result.get('memory_description', '')}")

# Optionally show internal voice (only for perception-based memories, not inquiries)
if show_internal_voice and memory_result.get('internal_voice'):
    print(f"\n💭 Internal Voice:")
    print(f"{memory_result.get('internal_voice', '')}")
```

### 2. `MAIN/redesigned_main.py`

**Line 4626:** Don't show internal voice for inquiry memories (already shown separately)
```python
display_memory_creation(
    memory_result,
    narrative_context_manager=narrative_context_manager,
    actor_name=actor.sheet.name,
    show_internal_voice=False  # Already shown at line 4606
)
```

**Line 4569:** Show internal voice for perception-based memories (not shown separately)
```python
display_memory_creation(
    memory_result,
    narrative_context_manager=narrative_context_manager,
    actor_name=actor.sheet.name,
    show_internal_voice=True  # Perception memories need internal voice shown
)
```

## Result

### Clean, Non-Redundant Output:

**For Inquiries with New Memory:**
```
💭 I know the #7 bus runs from here to downtown. Takes about 15 minutes.

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Downtown Bus Route
I know the #7 bus runs from here to downtown.

════════════════════════════════════════════════════════════
```

**For Inquiries without Memory (Don't Know):**
```
💭 I've never been downtown from here. Maybe I should ask someone or look for a bus stop.
```

**For Perception-Based Memories:**
```
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED (from perception)
════════════════════════════════════════════════════════════

Triggered by: You see a happy family having a picnic together

📝 Loving Mother
You have a loving mother who lives nearby.

💭 Internal Voice:
Man, I really miss my mom. I should go see her soon.

════════════════════════════════════════════════════════════
```

## Key Principles

1. **Internal voice is the PRIMARY response** - what the user actually sees/hears
2. **Memory display is SECONDARY** - shows what was learned/remembered
3. **No redundancy** - never repeat the same information
4. **Clear separation** - memories and thoughts are distinct systems
5. **Context-appropriate** - inquiries vs perception have different display needs
