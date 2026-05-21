# Investigation Report: Hardcoded Wake Up Description

## Issue Summary
Check if wake up scenes use dynamic internal voice instead of hardcoded text. Verify generate_inquiry_internal_voice() is called with proper context for opening scenes.

## Root Cause Analysis

### Problem Location
**agents/creator_agent.py:3178** in the `_get_initial_scene_prompt()` method.

### The Issue
The wake-up scene opening is **HARDCODED** in the LLM prompt template:

```python
1.  **START WITH WAKING UP:** The opening line MUST begin with the character's
    eyes opening - either "Your eyes shoot open..." or "Your eyes slowly open..."
    or similar. This establishes the moment of consciousness at the start of the
    simulation.
```

This means:
1. ❌ **Fixed formula**: Always uses "Your eyes [shoot/slowly/flutter] open..."
2. ❌ **No personality variation**: Doesn't adapt to UA's personality traits
3. ❌ **No internal voice**: Doesn't use the internal voice system
4. ❌ **No situational variation**: Same pattern regardless of context

### Current Example Format (Line 3216)
```
"Your eyes [shoot open/slowly open/flutter open] [immediate sensory detail].
You [look around/see/notice] [active perception of location]. [Sensory detail
from world context]. [Key exploration opportunities - 2-3 specific things].
[Optional: character detail based on personality]. [Final atmospheric touch]."
```

## What SHOULD Happen

### Internal Voice System
The system has `generate_inquiry_internal_voice_thought()` at **agents/narrator_agent.py:4193**, but this is for **inquiry responses**, not scene openings.

### Missing Component
There's **NO EQUIVALENT** system for generating dynamic, personality-driven scene opening narration. The wake-up description should:

1. **Use personality traits** to vary the opening
2. **Use internal voice** to reflect how the character perceives awakening
3. **Use S-factors** to influence the tone (Sturdiness → groggily, Swiftness → alertly, etc.)
4. **Use current state** (exhausted, energized, injured, etc.)

## Impact

### Current Behavior:
Every character wakes up with generic "Your eyes [verb] open..." regardless of:
- Their personality (anxious vs confident)
- Their physical state (exhausted vs rested)
- Their S-factors (high Swiftness → alert, low Sturdiness → sluggish)
- The situation (danger vs safety)

### Expected Behavior:
**High Swiftness + Alert personality:**
> "Your eyes snap open. You're instantly aware of your surroundings, muscles tensed and ready."

**Low Sturdiness + Exhausted:**
> "Consciousness returns slowly, reluctantly. You force your eyes open, fighting the weight of exhaustion."

**High Shadow + Paranoid:**
> "Your eyes dart open. Something's wrong. You scan the shadows before moving."

## Proposed Solution

### Option 1: Dynamic Wake-Up Generator (Recommended)
Create a new NarratorAgent method:

```python
def generate_scene_opening_narration(
    self,
    ua_actor,
    scene_description: str,
    opening_context: str = "waking_up"
) -> str:
    """
    Generate dynamic, personality-driven scene opening.

    Args:
        ua_actor: The User Actor
        scene_description: The location/scene context
        opening_context: Type of opening ("waking_up", "arriving", "transitioning")

    Returns:
        Personalized opening narration
    """
```

### Option 2: Parameterize Creator Prompt
Modify `_get_initial_scene_prompt()` to:
1. Analyze UA's personality traits and S-factors
2. Generate custom wake-up style instructions
3. Pass to LLM as dynamic prompt modification

### Option 3: Post-Process Scene Output
After scene generation, replace generic opening with dynamic version:
1. Detect "Your eyes [verb] open" pattern
2. Call internal voice system to generate replacement
3. Splice in personalized version

## Implementation Recommendation

**Priority: MEDIUM-HIGH** (affects immersion and character identity)

### Recommended Approach: Option 1 + Integration

1. Create `generate_scene_opening_narration()` in NarratorAgent
2. Modify scene generation to call this FIRST
3. Use result as opening constraint in scene prompt
4. Ensure consistency between personality and environment

### Integration Points:
- **agents/creator_agent.py** - Scene generation
- **agents/narrator_agent.py** - Opening narration generator
- **agents/internal_voice_interpreter_agent.py** - Personality integration

## Testing Recommendations

Test different UA profiles:

### High Swiftness + Low Sturdiness:
Should wake quickly but feel uncomfortable/anxious

### High Sturdiness + Low Swiftness:
Should wake slowly but comfortably/steadily

### High Shadow + Paranoid trait:
Should wake suspiciously, checking surroundings

### Exhausted status (low STAMINA):
Should struggle to wake, regardless of S-factors

## Related Systems

### Internal Voice System
- Currently only used for inquiries
- Should expand to scene narration
- Needs personality-to-prose mapping

### Personality Traits
- `internal` and `external` personality
- S-factors influence physical/mental state
- Current status (exhausted, injured, etc.)

### Scene Generation
- Currently template-based
- Should integrate dynamic opening
- Maintain second-person, present-tense consistency

## Files Affected
- **agents/creator_agent.py** (line 3178, scene prompt)
- **agents/narrator_agent.py** (new method needed)
- **agents/internal_voice_interpreter_agent.py** (personality mapping)

## Status
**INVESTIGATION COMPLETE** - Confirmed hardcoded, needs dynamic system

## Verdict
The wake-up description is **definitely hardcoded** and does NOT use the internal voice system. This is a missed opportunity for:
- Character differentiation
- Immersive personality expression
- Situational awareness reflection
- State-based narration (tired vs alert)

### Recommendation:
**IMPLEMENT** dynamic scene opening narration system with personality integration.

**Priority Level:** MEDIUM-HIGH (enhances immersion significantly)
