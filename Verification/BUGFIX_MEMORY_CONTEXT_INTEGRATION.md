# Bug Fix: Memory Context Integration

## Problem

**Critical Issue:** Memories and LLM agents (interpreter, narrator) weren't sharing context, causing contradictions and unrealistic behavior.

**Example:**
```
Memory says: "The subway is a 10-minute walk away"
Interpreter says: "Getting to subway could be done in 3 minutes"
Result: Character TELEPORTS to subway (unrealistic!)
```

**Root Cause:** The `get_context_for_llm()` method in `narrative_context_system.py` only included:
- Recent narrative events
- Active plot threads
- Character development

**It did NOT include memories!** This meant LLM agents had no knowledge of established facts.

---

## Solution

### Part 1: Add Memory Retrieval Method

**File:** `key_memories_system.py` (Lines 324-361)

Added `get_memories_for_llm()` method to format memories for LLM context:

```python
def get_memories_for_llm(
    self,
    limit: int = 10,
    min_importance: Optional[MemoryImportance] = MemoryImportance.NOTABLE
) -> str:
    """
    Get formatted memory context for LLM prompts.
    Returns recent important memories as a formatted string.
    """
    # Get memories above importance threshold
    filtered = []
    importance_order = [MemoryImportance.ROUTINE, MemoryImportance.NOTABLE, 
                      MemoryImportance.IMPORTANT, MemoryImportance.CRITICAL]
    
    for memory in self.memories.values():
        try:
            mem_idx = importance_order.index(memory.importance)
            min_idx = importance_order.index(min_importance)
            if mem_idx >= min_idx:
                filtered.append(memory)
        except (ValueError, AttributeError):
            continue
    
    if not filtered:
        return ""
    
    # Sort by timestamp (newest first) and limit
    filtered.sort(key=lambda m: m.timestamp, reverse=True)
    filtered = filtered[:limit]
    
    # Build context string
    context_parts = ["**RELEVANT MEMORIES:**"]
    for memory in filtered:
        context_parts.append(f"- {memory.title}: {memory.description}")
        if memory.tags:
            context_parts.append(f"  Tags: {', '.join(memory.tags)}")
    
    return "\n".join(context_parts)
```

---

### Part 2: Update Narrative Context System

**File:** `llm_agents/narrative_context_system.py` (Lines 541-577)

Updated `get_context_for_llm()` to include memories FIRST (before narrative events):

```python
def get_context_for_llm(self, lookback_events: int = 5, importance_threshold: str = "notable", key_memories_system=None) -> str:
    """Generate intelligent narrative context for LLM prompts, including memories"""
    try:
        # Convert importance threshold to enum
        threshold_map = {
            "critical": NarrativeImportance.CRITICAL,
            "important": NarrativeImportance.IMPORTANT,
            "notable": NarrativeImportance.NOTABLE,
            "routine": NarrativeImportance.ROUTINE
        }
        min_importance = threshold_map.get(importance_threshold.lower(), NarrativeImportance.NOTABLE)
        
        # Build context string
        context_parts = []
        
        # FIRST: Include memories (most important for consistency)
        if key_memories_system:
            try:
                from key_memories_system import MemoryImportance as MemImp
                # Map narrative importance to memory importance
                mem_importance_map = {
                    NarrativeImportance.ROUTINE: MemImp.ROUTINE,
                    NarrativeImportance.NOTABLE: MemImp.NOTABLE,
                    NarrativeImportance.IMPORTANT: MemImp.IMPORTANT,
                    NarrativeImportance.CRITICAL: MemImp.CRITICAL
                }
                mem_importance = mem_importance_map.get(min_importance, MemImp.NOTABLE)
                
                memories_context = key_memories_system.get_memories_for_llm(
                    limit=10,
                    min_importance=mem_importance
                )
                if memories_context:
                    context_parts.append(memories_context)
                    context_parts.append("")
            except Exception as e:
                self.logger.error(f"Error getting memories for LLM context: {e}")
        
        # Then add recent narrative events...
        [rest of method]
```

**Why memories FIRST?**
- Memories are established facts
- Narrative events should respect memory knowledge
- Prevents contradictions

---

### Part 3: Update Interpreter Agent

**File:** `agents/interpreter_agent.py`

**A. Add key_memories_system to __init__** (Line 30):
```python
def __init__(self, logger: 'UTASLogger', scene_description: str, tracker_agent=None, actor_manager=None, key_memories_system=None):
    self.logger = UTASLogger()
    self.scene_description = scene_description
    self.tracker_agent = tracker_agent
    self.key_memories_system = key_memories_system  # For memory-aware context
    [...]
```

**B. Pass key_memories_system to get_context_for_llm** (Lines 1879-1882):
```python
context_data = self.narrative_context_manager.get_context_for_llm(
    lookback_events=5,
    importance_threshold="notable",
    key_memories_system=self.key_memories_system  # Include memories for consistency
)
```

**Updated in 3 places:**
- Line 285 (interpret_user_action)
- Line 1879 (detect_inquiry_or_action)
- Line 2493 (interpret_reactor_action)

---

### Part 4: Update Conductor Agent

**File:** `agents/conductor_agent.py` (Lines 18-41)

**A. Add key_memories_system parameter:**
```python
def __init__(self, logger: UTASLogger, scene_description: str, recovery_integrator=None, 
             tracker_agent=None, actor_manager=None, rag_system=None, key_memories_system=None):
    [...]
    self.key_memories_system = key_memories_system
```

**B. Pass to InterpreterAgent:**
```python
self.interpreter_agent = InterpreterAgent(logger, scene_description, tracker_agent, actor_manager, key_memories_system)
```

---

## Integration Flow

### Before Fix:
```
User: "I go to the subway"

Interpreter Agent:
- Gets scene description
- Gets narrative events
- NO MEMORY CONTEXT ❌
- Estimates: "3 minutes to subway"

Result: Contradicts memory (10-minute walk)
```

### After Fix:
```
User: "I go to the subway"

Interpreter Agent:
- Gets scene description
- Gets MEMORIES FIRST ✅
  **RELEVANT MEMORIES:**
  - Downtown Subway Route: The subway is a 10-minute walk away
- Gets narrative events
- Estimates: "10 minutes to subway"

Result: Consistent with memory!
```

---

## Expected Context Format

When LLM agents receive context, they now see:

```
**RELEVANT MEMORIES:**
- Downtown Subway Route: The subway is a 10-minute walk away
  Tags: subway, downtown, walk, station
- Guard's Schedule: The guard changes shifts at 6 PM
  Tags: guard, shift, schedule, evening

**RECENT NARRATIVE CONTEXT:**
Event 1: You asked about getting downtown
  Actors: Your Character
  Tone: curious
  Mode: ROAM

Event 2: You examined the map
  Actors: Your Character
  Tone: focused
  Mode: ROAM

**ACTIVE PLOT THREADS:**
- Find the underground rave: Searching for the secret location

**CHARACTER DEVELOPMENT:**
- Your Character: Determined but cautious
```

---

## Benefits

### 1. Consistency
✅ LLM agents respect established facts
✅ No contradictions between memory and narration
✅ Realistic time/distance estimates

### 2. Continuity
✅ Agents remember what character knows
✅ Decisions based on accumulated knowledge
✅ Narrative builds on previous events

### 3. Realism
✅ No teleportation
✅ Proper time progression (3-second units)
✅ Logical action sequences

### 4. Immersion
✅ World feels consistent
✅ Character knowledge matters
✅ Memories have real impact

---

## Testing

### Test 1: Distance Consistency
```
1. Ask: "How far is the subway?"
   → Memory created: "10-minute walk"

2. Say: "I go to the subway"
   → Interpreter sees memory
   → Estimates 10 minutes (not 3!)
   → Time advances realistically
```

### Test 2: Schedule Consistency
```
1. Learn: "Guard changes shifts at 6 PM"
   → Memory created

2. Later: "I sneak past the guard"
   → Interpreter sees memory
   → Checks current time
   → Adjusts difficulty based on shift change
```

### Test 3: Knowledge Consistency
```
1. Learn: "The back door is always unlocked"
   → Memory created

2. Later: "I try to enter the building"
   → Narrator sees memory
   → Mentions back door option
   → Consistent with known facts
```

---

## Files Modified

1. **key_memories_system.py**
   - Added `get_memories_for_llm()` method

2. **llm_agents/narrative_context_system.py**
   - Updated `get_context_for_llm()` to include memories
   - Memories added FIRST for priority

3. **agents/interpreter_agent.py**
   - Added `key_memories_system` parameter to `__init__`
   - Updated 3 calls to `get_context_for_llm()`

4. **agents/conductor_agent.py**
   - Added `key_memories_system` parameter to `__init__`
   - Passed to `InterpreterAgent`

---

## Next Steps

**In main simulation file (redesigned_main.py):**

When initializing ConductorAgent, pass key_memories_system:

```python
conductor = ConductorAgent(
    logger=logger,
    scene_description=scene_description,
    recovery_integrator=recovery_integrator,
    tracker_agent=tracker_agent,
    actor_manager=actor_manager,
    rag_system=rag_system,
    key_memories_system=key_memories  # ADD THIS
)
```

---

## Status

✅ Memory retrieval method added
✅ Narrative context system updated
✅ Interpreter agent updated
✅ Conductor agent updated
⏳ **PENDING:** Update main simulation file to pass key_memories_system

**Once main file is updated, all LLM agents will have memory-aware context!**
