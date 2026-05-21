# Internal Voice Context Integration

## Overview

All internal voice narration (from memories, memory resurfacing, and regular internal thoughts) is now **automatically recorded in the narrative context system**. This ensures that the vessel's internal thoughts are available to all future LLM calls, creating better continuity and character consistency.

## What Gets Recorded

### 1. Memory Creation (Intent-Based)

**When:** User mentions something that triggers a new memory
**Example:** "I want to call my mom"

**Recorded:**
```
Event Type: MEMORY_CREATION
Importance: IMPORTANT
Text: 📝 Loving Mother: You have a loving mother, Margaret...
      💭 I should call mom soon. She worries when I don't check in.
```

### 2. Memory Resurfacing (Perception-Based)

**When:** Narration triggers an existing memory
**Example:** "You see a happy family having a picnic"

**Recorded:**
```
Event Type: MEMORY_RESURFACING
Importance: NOTABLE
Text: 💭 Mother: Man, I really miss my mom. I should go see her soon.
```

### 3. Regular Internal Voice (ROAM Mode)

**When:** Generated during exploration actions in ROAM mode
**Example:** After exploring a location

**Recorded:**
```
Event Type: INTERNAL_VOICE
Importance: NOTABLE
Text: 💭 This place feels familiar somehow. Like I've been here before.
```

## Why This Matters

### 1. Character Consistency

**Before:**
- LLMs don't know about previous internal thoughts
- Character might contradict their own feelings
- No memory of emotional reactions

**After:**
- LLMs see all previous internal thoughts
- Character maintains consistent emotional state
- Reactions build on previous feelings

### 2. Narrative Continuity

**Before:**
```
Turn 5: Internal voice: "I really miss my mom"
Turn 10: Narration: "You feel completely alone in the world"
```
**Problem:** Contradicts established feelings

**After:**
```
Turn 5: Internal voice: "I really miss my mom" (recorded in context)
Turn 10: Narration: "Despite missing your mom, you press forward"
```
**Result:** Acknowledges established feelings

### 3. Emotional Depth

**Before:**
- Each internal voice is isolated
- No emotional throughline
- Feels disconnected

**After:**
- Internal voices build on each other
- Emotional arc develops naturally
- Feels cohesive and meaningful

## Technical Implementation

### New Event Types

Added to `narrative_context_system.py`:
```python
class NarrativeEventType(Enum):
    # ... existing types ...
    INTERNAL_VOICE = "internal_voice"  # Vessel's internal thoughts
    MEMORY_CREATION = "memory_creation"  # Background memory created
    MEMORY_RESURFACING = "memory_resurfacing"  # Existing memory resurfaced
```

### Display Function Enhancement

Updated `display_memory_creation()` in `intent_based_memory_creation.py`:
```python
def display_memory_creation(memory_result: Dict[str, Any], 
                          narrative_context_manager=None, 
                          actor_name: str = "Vessel"):
    # ... display logic ...
    
    # Record in narrative context if manager provided
    if narrative_context_manager:
        if is_resurfacing:
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.MEMORY_RESURFACING,
                narrative_text=f"💭 {trigger_context}: {internal_voice}",
                actors_involved=[actor_name],
                importance=NarrativeImportance.NOTABLE,
                emotional_tone=emotional_tone
            )
        else:
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.MEMORY_CREATION,
                narrative_text=f"📝 {memory_title}: {memory_desc}\n💭 {internal_voice}",
                actors_involved=[actor_name],
                importance=NarrativeImportance.IMPORTANT,
                emotional_tone=emotional_tone
            )
```

### Main Loop Integration

**Location 1: Intent-Based Memories (line ~2820)**
```python
for memory_result in created_memories:
    display_memory_creation(
        memory_result,
        narrative_context_manager=narrative_context_manager,
        actor_name=actor.sheet.name
    )
```

**Location 2: Perception-Based Memories - Given Actions (line ~3603)**
```python
for memory_result in resurfaced_memories:
    display_memory_creation(
        memory_result,
        narrative_context_manager=narrative_context_manager,
        actor_name=actor.sheet.name
    )
```

**Location 3: Perception-Based Memories - Fallible Exploration (line ~4231)**
```python
for memory_result in resurfaced_memories:
    display_memory_creation(
        memory_result,
        narrative_context_manager=narrative_context_manager,
        actor_name=actor.sheet.name
    )
```

**Location 4: Regular Internal Voice - Given Actions (line ~3636)**
```python
if internal_voice:
    print(f"💭 {internal_voice}")
    
    # Record in narrative context
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.INTERNAL_VOICE,
        narrative_text=f"💭 {internal_voice}",
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="reflective"
    )
```

**Location 5: Regular Internal Voice - Fallible Exploration (line ~4275)**
```python
if internal_voice:
    print(f"💭 {internal_voice}")
    
    # Record in narrative context
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.INTERNAL_VOICE,
        narrative_text=f"💭 {internal_voice}",
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="reflective"
    )
```

## Example Context Flow

### Turn 5: Memory Created
```
User: "I want to call my mom"
→ Memory created: "Loving Mother"
→ Internal voice: "I should call mom soon. She worries."
→ Recorded in context as MEMORY_CREATION (IMPORTANT)
```

### Turn 10: Memory Resurfaces
```
Narration: "You see a happy family having a picnic"
→ Memory resurfaces: "Mother"
→ Internal voice: "Man, I really miss my mom."
→ Recorded in context as MEMORY_RESURFACING (NOTABLE)
```

### Turn 15: Regular Internal Voice
```
Action: "I explore the park"
→ Internal voice: "This park reminds me of home. Of mom."
→ Recorded in context as INTERNAL_VOICE (NOTABLE)
```

### Turn 20: LLM Uses Context

When generating new narration, the LLM sees:
```
Recent Context:
- Turn 5: 📝 Loving Mother: You have a loving mother...
         💭 I should call mom soon. She worries.
- Turn 10: 💭 Mother: Man, I really miss my mom.
- Turn 15: 💭 This park reminds me of home. Of mom.
```

**Result:** New narration acknowledges the vessel's feelings about their mother, creating emotional continuity.

## Benefits

### 1. Smarter LLMs
- LLMs see complete emotional history
- Generate more consistent responses
- Understand character's internal state

### 2. Better Storytelling
- Emotional arcs develop naturally
- Internal thoughts build on each other
- Character feels more alive

### 3. Reduced Contradictions
- System knows what vessel has thought/felt
- Prevents contradictory narration
- Maintains character consistency

### 4. Richer Context
- Internal voice adds depth to context
- Provides emotional subtext
- Enhances narrative understanding

## Storage

All internal voice events are stored in:
```
./simulation_data/narrative_context/{session_id}_context.json
```

**Persistence:**
- Saved automatically every 10 events
- Available across entire session
- Can be retrieved with `get_context_for_llm()`

## Context Retrieval

LLMs retrieve internal voice context through:
```python
recent_narrative = narrative_context_manager.get_context_for_llm(
    lookback_events=5,
    importance_threshold="notable"
)
```

**Returns:**
- Last 5 events with importance ≥ NOTABLE
- Includes all internal voice events
- Formatted for LLM consumption

## Design Philosophy

**"The vessel's thoughts are part of their story."**

Internal voice isn't just flavor text—it's a critical part of the narrative that should inform all future storytelling. By recording these thoughts in the narrative context, we ensure that:

1. The vessel's emotional journey is tracked
2. Character consistency is maintained
3. LLMs have complete context for decisions
4. The story feels cohesive and meaningful

## Conclusion

By integrating internal voice narration into the narrative context system, we create a **richer, more consistent, emotionally coherent** simulation where the vessel's thoughts are not just displayed to the player, but actively inform the ongoing story.

**The vessel's inner life shapes their outer story.**
