# Inquiry Generation Order System

## Overview

The **Inquiry Generation Order System** intelligently determines whether to generate **perceptual description** or **internal voice** first based on whether the user's action is **physical** or **mental**.

## Philosophy

### Physical Actions → Perception First
**"See, then think"**

When you perform a physical action or ask about the external world:
1. **First:** Generate perceptual description (what you see/hear/feel)
2. **Then:** Generate internal voice (your thoughts about what you perceived)

**Why?** Physical actions involve interacting with the external world first, then processing that information mentally.

### Mental Actions → Thought First
**"Think, then notice"**

When you perform a mental action like recalling a memory:
1. **First:** Generate internal voice (the memory/thought itself)
2. **Then:** Generate perceptual description (physical manifestation of thinking)

**Why?** Mental actions happen internally first, then manifest physically (furrowed brow, closed eyes, etc.).

## Examples

### Physical Actions (Perception → Thought)

#### "Where am I?"
```
1. PERCEPTION: "You see a cramped BSU legal office. Dented metal file cabinets, 
   a manual typewriter humming, a CRT monitor blinking."
2. THOUGHT: "This is our office at the BSU headquarters. We could check those 
   files for the case documents."
```

#### "What's that sound?"
```
1. PERCEPTION: "You hear a rhythmic thumping from the floor above. Footsteps, 
   heavy and deliberate."
2. THOUGHT: "Someone's upstairs. Could be the security patrol making rounds."
```

#### "Who is that person?"
```
1. PERCEPTION: "You see a woman in a dark jacket standing by the entrance. 
   She's watching the building, hands in pockets."
2. THOUGHT: "Don't recognize her. Never seen her before. We should stay alert."
```

### Mental Actions (Thought → Perception)

#### "I try to remember my best friend"
```
1. THOUGHT: "Mila! That's her name. We met at the rave scene in 1993. 
   She was the one who made it all unforgettable."
2. PERCEPTION: "You close your eyes, concentrating. Your brow furrows slightly 
   as the memory surfaces."
```

#### "What did I do last week?"
```
1. THOUGHT: "Last week we were investigating the Tempelhof Heim facility. 
   We found those classified documents about the Z-Class donors."
2. PERCEPTION: "You pause, thinking. Your fingers tap the desk absently as you 
   recall the events."
```

#### "Think about the plan"
```
1. THOUGHT: "We need to get those files without triggering the audit. 
   Klaus could help with the pneumatic tube routing."
2. PERCEPTION: "You lean back in your chair, staring at the ceiling. 
   Your hand moves to your chin, thinking."
```

## Implementation

### Core Function: `determine_generation_order()`

```python
def determine_generation_order(
    user_input: str,
    fallible_subtype: str,
    input_analysis: dict = None
) -> GenerationOrder:
    """
    Returns: "perception_first" or "thought_first"
    """
```

### Detection Logic

1. **Check fallible_subtype**
   - `'mental'` or `'inquiry'` → Analyze further
   - `'physical'` or `'social'` → Always perception first

2. **For mental/inquiry actions, check keywords:**

   **Memory keywords** (→ thought first):
   - remember, recall, think about, think of
   - try to remember, what did i, what was
   - my memory, i forgot, trying to recall

   **Perception keywords** (→ perception first):
   - where am i, what is this place
   - what's that, who is that
   - what time, check time, look at
   - read, listen, hear, see, smell, feel

3. **Default for mental/inquiry:** thought first

### Helper Function: `generate_inquiry_outputs()`

Generates both outputs in the correct order and returns them as a tuple:

```python
perceptual_description, internal_voice = generate_inquiry_outputs(
    narrator=narrator,
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    time_context=time_context,
    availability_context=availability_context,
    factual_knowledge=factual_answer,
    fallible_subtype='inquiry'
)
```

**Key feature:** Whichever is generated first is passed as context to the second generation, ensuring coherence.

## Benefits

### 1. **More Natural Flow**
- Physical actions feel more grounded (see → think)
- Mental actions feel more introspective (think → notice)

### 2. **Better Context**
- Second generation has context from first
- Internal voice can reference what was just perceived
- Perceptual description can show physical manifestation of thought

### 3. **Improved Coherence**
- Outputs are contextually linked
- No contradictions between perception and thought
- More immersive experience

### 4. **Backend Only**
- User sees same output format
- No UI changes needed
- Transparent improvement

## Integration Points

### Current Code Locations

The system should be integrated at these points in `redesigned_main.py`:

1. **Memory Recall** (lines ~5637-5709)
   - Currently: perception → internal
   - Should use: `generate_inquiry_outputs()` with dynamic order

2. **New Inquiry Discovery** (lines ~5813-5873)
   - Currently: perception → internal
   - Should use: `generate_inquiry_outputs()` with dynamic order

3. **Failed Inquiry** (lines ~6008-6050)
   - Currently: only internal voice
   - Should use: `generate_inquiry_outputs()` with dynamic order

4. **Observation Actions** (lines ~4644-4675)
   - Currently: perception → internal
   - Should use: `generate_inquiry_outputs()` with dynamic order

## Usage Example

### Before (Hardcoded Order):
```python
# Always perception first
perceptual_description = narrator.generate_inquiry_response(...)
print(perceptual_description)

internal_voice = narrator.generate_inquiry_internal_voice(...)
print(internal_voice)
```

### After (Dynamic Order):
```python
from inquiry_generation_order import generate_inquiry_outputs

# Automatically determines correct order
perceptual_description, internal_voice = generate_inquiry_outputs(
    narrator=narrator,
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    time_context=time_context,
    availability_context=availability_context,
    factual_knowledge=factual_answer,
    fallible_subtype=fallible_subtype
)

# Display in standard order (perception always shown first to user)
print(perceptual_description)
print(internal_voice)
```

## Display Order vs Generation Order

**Important distinction:**

- **Generation order:** Backend - which is generated first (for context)
- **Display order:** Frontend - always show perception then internal voice

**User always sees:**
```
[Perceptual description]

═══════════════════════
💭 INTERNAL VOICE
═══════════════════════
[Internal voice]
```

**But backend generates in optimal order for context.**

## Testing

### Test Cases

1. **"Where am I?"** → Should generate perception first
2. **"I try to remember my friend"** → Should generate thought first
3. **"What's that sound?"** → Should generate perception first
4. **"What did I do yesterday?"** → Should generate thought first
5. **"Check the time"** → Should generate perception first
6. **"Think about the plan"** → Should generate thought first

### Verification

Check debug logs for generation order:
```
[INQUIRY ORDER] Determined order: thought_first
[INQUIRY] Generating internal voice first...
[INQUIRY] Generating perceptual description second...
```

## Future Enhancements

1. **ML-based detection:** Train model to detect physical vs mental intent
2. **Context-aware ordering:** Consider recent actions and scene state
3. **Hybrid actions:** Some actions might need interleaved generation
4. **User preferences:** Allow override for specific action types

## Files

- **`inquiry_generation_order.py`** - Core system implementation
- **`INQUIRY_GENERATION_ORDER_SYSTEM.md`** - This documentation
- **Integration needed in:** `redesigned_main.py` (inquiry handling sections)

## Status

✅ System designed and implemented
✅ **Integration complete** - Integrated into main loop
📋 Testing required

### Integration Locations

The dynamic generation order system has been integrated at:

1. **Memory Recall** (`redesigned_main.py` ~line 5637)
   - Uses `generate_inquiry_outputs()` with `fallible_subtype='inquiry'`
   - Automatically determines order based on question type

2. **New Inquiry Discovery** (`redesigned_main.py` ~line 5806)
   - Uses `generate_inquiry_outputs()` with `fallible_subtype='inquiry'`
   - Handles successful inquiry learning

3. **Passive Observation** (`redesigned_main.py` ~line 4643)
   - Uses `generate_inquiry_outputs()` with `fallible_subtype='physical'`
   - Always perception-first for physical observation

### Next Steps

- Test with various inquiry types
- Monitor generation order in debug logs
- Verify context propagation between outputs
- Ensure no regressions in existing functionality
