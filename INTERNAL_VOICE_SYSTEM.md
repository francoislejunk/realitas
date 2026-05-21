# Internal Voice System

## Overview

The Internal Voice system provides subtle, personality-driven narration during ROAM mode that makes the user feel like THEY are thinking the thoughts, not being told by an external narrator. **NOW ENHANCED:** The internal voice proactively suggests solutions, offers reminders, and can sometimes be wrong - just like real internal dialogue.

## Philosophy

**"We" not "You"**
- Uses 2nd person plural ("we", "us", "our") instead of "you"
- Creates the feeling that the character IS the user thinking
- Not an external narrator telling you what happens
- More immersive and diegetic

**ROAM Mode Only**
- Only appears during exploration/ROAM mode (SimulationMode.ROAM)
- Disappears completely during encounters/social interactions (SimulationMode.ENCOUNTER)
- When talking to someone, the internal voice goes silent (no schizophrenic tendencies)

**Subtle, Not Chatty**
- 1-2 sentences maximum
- Only reacts when there's something worth noting
- Can return empty if nothing stands out
- Temperature set to 0.7 for moderate creativity
- Max tokens: 100 to keep it brief

**Personality-Driven**
- Based on UA's internal personality traits
- Reflects character's unique perspective
- Consistent with established characterization

**Memory Recall**
- Can naturally recall relevant memories
- Example: "Like when Dad used to bring us to that ice cream store"
- Uses recent narrative context for continuity

**Solution-Oriented (NEW)**
- Suggests possible solutions or next steps
- Offers reminders about tasks or needs
- Makes educated guesses about situations
- **Can be wrong sometimes** - overconfident, misremembering, or misjudging
- Reflects how real internal dialogue works - helpful but fallible

## Implementation

### Architecture

**No Separate Agent**
- Added as method to existing `NarratorAgent`
- `generate_internal_voice()` method handles all internal voice generation
- Maintains single responsibility: all narration through one agent

### Integration Points

**1. Given Actions (Automatic Success)**
- Location: `redesigned_main.py` line ~3368-3390
- Triggers after main narrative generation
- Success level: 3 (automatic success)

**2. Exploration Actions (Fallible)**
- Location: `redesigned_main.py` line ~3830-3852
- Triggers after main narrative generation
- Success level: Calculated from success_total

### Code Flow

```python
# After main narrative is generated
if current_mode == NarrativeMode.ROAM:
    try:
        # Get recent narrative for memory recall
        recent_narrative = narrative_context_manager.get_context_for_llm(
            lookback_events=3,
            importance_threshold="routine"
        )
        
        # Generate internal voice
        internal_voice = narrator.generate_internal_voice(
            ua_actor=actor,
            action_description=user_input,
            scene_description=scene_description,
            narrative_context=recent_narrative,
            success_level=success_level,
            outcome_description=contextual_result
        )
        
        # Display if generated with distinctive formatting
        if internal_voice:
            print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
            print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
            print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}")
    except Exception:
        # Silently fail - internal voice is optional
        pass
```

## Examples

### Good Internal Voice Examples

**Visual Format:**
```
──────────────────────────────────────────────────────────────────────
💭 We've seen places like this before. Reminds us of that ice cream store Dad used to take us to.
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 The engine's purring now. Feels good to fix something with our own hands.
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 Something about this alley doesn't sit right. Too quiet.
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 Maybe we should check the back entrance. Worth a shot.
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 We need to eat soon. Getting light-headed.
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 This'll be quick. In and out, no problem. (narrator note: it won't be)
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 Pretty sure Mike mentioned something about this place. Or was it Tony?
──────────────────────────────────────────────────────────────────────

──────────────────────────────────────────────────────────────────────
💭 Should probably avoid that guy. Looks like he's had a rough day.
──────────────────────────────────────────────────────────────────────
```

**Note:** Internal voice appears in **bold cyan** color with separator lines to clearly distinguish it from regular narrative (which is magenta).

**Types of Internal Voice:**
1. **Observations:** Noticing details about the environment
2. **Memories:** Recalling relevant past experiences
3. **Intuitions:** Gut feelings about situations
4. **Solutions:** Suggesting possible approaches or actions
5. **Reminders:** Noting needs or tasks (hunger, supplies, goals)
6. **Warnings:** Cautioning about potential dangers
7. **Wrong Guesses:** Overconfident or incorrect assessments
8. **Misremembering:** Uncertain or confused recollections

### Bad Examples (What NOT to Do)

```
❌ You walk into the arcade and look around.
   (Wrong person - "you" instead of "we")

❌ I'm feeling nervous about this.
   (Wrong person - "I" instead of "we")

❌ We walk in, look around, notice the games, feel the nostalgia, remember childhood, think about the future...
   (Too chatty - way too many thoughts)

❌ The arcade is full of games.
   (External description, not internal thought)
```

## Parameters

### NarratorAgent.generate_internal_voice()

**Arguments:**
- `ua_actor`: The User Actor (for personality traits)
- `action_description`: What the UA is doing (user input)
- `scene_description`: Current scene context
- `narrative_context`: Recent events for memory recall
- `success_level`: Optional success level (1-5)
- `outcome_description`: Optional outcome narrative

**Context Extracted from UA Actor:**
- **Current State**: Stamina, Spirit, Supply levels (for need-based reminders)
- **Current Task**: Active goal/task from goal system (for task-relevant suggestions)
- **Inventory**: Top 3 items carried (for solution suggestions)
- **Relationships**: Key sympathy values with NPCs (for social awareness)
- **Personality**: Internal/external traits (for consistent voice)

**Returns:**
- `str`: Internal voice narration (1-2 sentences)
- `None`: If no meaningful reaction needed

### LLM Settings

- **Temperature**: 0.7 (moderate creativity for personality)
- **Max Tokens**: 100 (keeps it brief)
- **Model**: Uses "narration" role model (Venice Dolphin)

## Design Decisions

### Why Not a Separate Agent?

**Single Responsibility**: NarratorAgent already owns all narrative generation. Adding internal voice as a method maintains this responsibility.

**Simpler Integration**: Just call a different method based on mode, no extra agent initialization.

**Shared Context**: Both narration types can access same narrative utilities and context.

**Less Overhead**: No extra agent to initialize or manage.

### Why 2nd Person Plural?

**Immersion**: "We" feels like you're part of the character, not observing them.

**Characterization**: Gives the narrator personality (the UA's internal personality).

**Diegetic**: Everything is in the "user" voice, so they don't have to remember everything.

**Natural**: Matches how people actually think ("We've been here before" vs "I've been here before").

### Why ROAM Mode Only?

**Realism**: Internal voices quiet down during social interactions.

**No Schizophrenia**: Don't want character having internal monologue while talking to someone.

**Focus**: During exchanges, focus should be on the interaction, not internal thoughts.

**Natural**: Matches real life - you think more when alone than when engaged with others.

## Testing

### Manual Testing

1. Start simulation in ROAM mode
2. Perform exploration actions
3. Check for 💭 internal voice after narrative
4. Verify it uses "we", "us", "our"
5. Verify it's 1-2 sentences max
6. Verify it reflects character personality

### Edge Cases

- **Empty Response**: System handles None gracefully
- **LLM Failure**: Silently fails, doesn't break simulation
- **Mode Switch**: Only appears in ROAM, disappears in ENCOUNTER
- **Memory Recall**: Uses recent narrative context when available

## Future Enhancements

### Possible Improvements

1. **Memory System Integration**: Could integrate with full memory system for deeper recall
2. ~~**Emotional State**: Could reflect current status levels (tired, hurt, etc.)~~ ✅ **IMPLEMENTED**
3. ~~**Goal Awareness**: Could reference current tasks/goals~~ ✅ **IMPLEMENTED**
4. ~~**Relationship Awareness**: Could mention sympathies with NPCs~~ ✅ **IMPLEMENTED**
5. **Contextual Solutions**: Could suggest more specific solutions based on available items/skills
6. **Learning from Mistakes**: Could reference past failures when suggesting solutions

### Temperature Tuning

Current setting: 0.7
- **Lower (0.5-0.6)**: More consistent, less creative
- **Higher (0.8-0.9)**: More varied, more creative
- Monitor for chattiness and adjust if needed

## Troubleshooting

### Internal Voice Not Appearing

1. Check if in ROAM mode (not ENCOUNTER)
2. Check if LLM call succeeded (look for errors)
3. Check if response was too short (<10 chars)
4. Check if narrative_context_manager is initialized

### Internal Voice Too Chatty

1. Reduce temperature (currently 0.7)
2. Reduce max_tokens (currently 100)
3. Enhance prompt with stricter brevity requirements

### Wrong Perspective (Using "You" or "I")

1. Check LLM prompt emphasizes "we", "us", "our"
2. Check system message reinforces 2nd person plural
3. May need to add post-processing to filter/correct

## Summary

The Internal Voice system enhances immersion by providing subtle, personality-driven thoughts during ROAM mode exploration. It uses 2nd person plural perspective to make the user feel like THEY are the character thinking, not being told by an external narrator. 

**Enhanced with solution-oriented thinking:** The internal voice now proactively suggests solutions, offers reminders about needs and tasks, and makes educated guesses - sometimes being wrong, just like real internal dialogue. It draws on the character's current state (stamina, spirit, supply), active goals, inventory items, and relationships to provide contextually relevant thoughts.

The system is integrated into NarratorAgent and only activates during ROAM mode, disappearing during social interactions for realism.
