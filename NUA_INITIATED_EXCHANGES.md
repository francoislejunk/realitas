# NUA-Initiated Exchanges in SPARK Mode

## Overview

Enhanced the SPARK mode in the Four-Mode Narrative Loop to allow NUAs to initiate exchanges with the UA, creating more dynamic and unpredictable storytelling.

## The Enhancement

When SPARK mode introduces an NUA-related situation, there's now a **50/50 split** between two types of encounters:

### 1. Observational Situation (50%)

**What It Is:**
- NUA does something interesting nearby
- UA can choose to engage or just watch
- UA maintains full agency

**Examples:**
- NUA arguing with someone
- NUA having an accident
- NUA performing or working
- NUA discovering something

**Player Experience:**
```
🎯 SPARK DETECTED

Through the warehouse window, you see a woman in her 50s arguing 
with a man in a suit. She's waving a clipboard, pointing at 
something on the page. The man shakes his head and walks away.

She stands there for a moment, looking frustrated, then pulls 
out a photo - you can't see it clearly, but it looks like a 
missing person poster.
```

**UA Choices:**
- Approach and interact
- Keep watching
- Ignore and continue
- Leave the area

### 2. Forced Exchange (50%)

**What It Is:**
- NUA directly approaches/confronts UA
- UA must respond (triggers contested action)
- Creates immediate dramatic tension
- Still diegetic (NUA has reason to engage)

**Examples:**
- NUA asks urgent question
- NUA makes demand
- NUA needs immediate help
- NUA confronts UA about something

**Player Experience:**
```
🎯 SPARK DETECTED → CONTESTED ACTION INITIATED

As you examine the bulletin board, you hear the warehouse door 
creak open. A woman in her 50s enters, carrying a clipboard. 
She freezes when she sees you.

"You're not supposed to be here," she says, walking directly 
toward you. Her tone isn't angry - it's afraid. She stops a 
few feet away, staring at the photo in your hand.

"That's... that's your sister, isn't it?" She looks around 
nervously. "We need to talk. Now."

She's waiting for your response.
```

**UA Must Respond:**
- Answer questions
- Make demands
- Try to leave
- Threaten or intimidate

## Design Philosophy

### Why 50/50?

**Variety:** Prevents predictability - sometimes you control the pace, sometimes the world acts on you

**Agency Balance:** 
- 50% maintains full player agency (observational)
- 50% creates dramatic pressure (forced)

**Realistic:** In real life, sometimes people approach you directly, sometimes you observe from a distance

**Tension:** Forced exchanges create immediate stakes without feeling artificial

### Why Still Diegetic?

Even forced exchanges are **narratively justified**:
- NUA has a reason to approach
- Situation makes sense in context
- Not random or meta
- Feels like natural story progression

### Integration with SPARK Mode

**SPARK Mode Purpose:** Gentle nudge into purpose

**How NUA Exchanges Fit:**
- **Observational:** Presents opportunity (classic SPARK)
- **Forced:** Creates immediate purpose (stronger SPARK)
- Both relate to UA's goals
- Both feel organic and story-driven

## Implementation

### File Modified

**`llm_agents/narrative_loop_system.py`**

Enhanced the SPARK mode guidance in `_get_narrative_guidance()`:

```python
elif self.current_state.mode == NarrativeMode.SPARK:
    guidance = ("**SPARK MODE - Introduce Potential Missions:**\n"
               "- Casually introduce 2-3 potential missions/goals through:\n"
               "  * NUA dialogue ('I heard the warehouse is hiring')\n"
               "  * Environmental cues (wanted poster, broken fence, overheard conversation)\n"
               "  * Opportunities that align with character interests\n"
               "  * **NUA-INITIATED SITUATIONS** (50% observational, 50% forced exchange):\n"
               "    - Observational: NUA does something interesting nearby (argument, accident, performance)\n"
               "      → UA can choose to engage or just watch\n"
               "    - Forced Exchange: NUA directly approaches/confronts UA (asks question, makes demand, needs help)\n"
               "      → UA must respond, triggering contested action\n"
               "- Frame as interesting possibilities, not obligations\n"
               "- Let the player choose which spark to pursue\n"
               "- Nudge toward purpose without forcing or showing mechanics")
```

### How It Works

1. **Narrative Loop** detects SPARK mode readiness
2. **Narrator Agent** receives SPARK mode guidance
3. **LLM** generates NUA situation based on guidance
4. **50/50 Decision** made during generation:
   - Observational: NUA acts nearby, UA observes
   - Forced: NUA approaches UA directly
5. **Result:**
   - Observational → ROAM continues with new opportunity
   - Forced → Triggers contested action/exchange

## Examples in Context

### Scenario: Detective searching for missing sister

#### Observational SPARK (50%)

```
You've been searching the warehouse for about 15 minutes when 
you hear voices outside. Through a grimy window, you see a 
woman in her 50s talking on a payphone. She keeps glancing 
at the warehouse nervously.

"I told you, someone's been asking questions," she says into 
the phone. "About the girl who disappeared. Yes, THAT girl."

She hangs up and lights a cigarette, pacing back and forth.

What do you want to do?
```

**UA maintains agency** - can approach, watch, ignore, etc.

---

#### Forced Exchange SPARK (50%)

```
You're examining the bulletin board when you hear footsteps 
behind you. You turn to see a woman in her 50s standing in 
the doorway, blocking your exit.

"I know why you're here," she says, her voice shaking. She 
holds up a photo - your sister's face stares back at you. 
"I've been waiting for someone to come looking for her."

She takes a step closer. "But you need to leave. Now. Before 
they come back."

She's staring at you, waiting for your answer.

═══ CONTESTED ACTION INITIATED ═══
What do you want to do?
```

**UA must respond** - triggers exchange system immediately.

## Benefits

### For Players

1. **Unpredictability:** Never know if you'll control the pace or be forced to react
2. **Dramatic Tension:** Forced exchanges create immediate stakes
3. **Agency Preserved:** Still have choices even in forced exchanges
4. **Natural Flow:** Feels like real story progression, not game mechanics

### For Storytelling

1. **Variety:** Two distinct types of NUA encounters
2. **Pacing Control:** Can speed up or slow down story naturally
3. **Character Development:** NUAs feel more alive and proactive
4. **Goal Alignment:** Both types push toward UA's goals

### For Simulation

1. **Living World:** NUAs don't just wait for UA to act
2. **Diegetic:** All interactions justified by story
3. **Balanced:** 50/50 split prevents either type from dominating
4. **Scalable:** Can adjust ratio if needed (currently 50/50)

## Future Enhancements

### Possible Adjustments

1. **Dynamic Ratio:** Adjust 50/50 based on:
   - UA's personality (bold vs cautious)
   - Current tone (calm vs hot)
   - Story momentum
   - Time pressure

2. **Intensity Levels:**
   - Soft forced exchange: "Excuse me, can I ask you something?"
   - Hard forced exchange: "Don't move. We need to talk."

3. **Group Dynamics:**
   - Multiple NUAs approaching together
   - NUA asking for help with another NUA

4. **Context Awareness:**
   - More forced exchanges in PRESSURE mode
   - More observational in ROAM mode
   - Balanced in SPARK mode

## Summary

The NUA-Initiated Exchange system enhances SPARK mode by:

✅ **Adding variety** - 50% observational, 50% forced
✅ **Creating tension** - Forced exchanges demand immediate response
✅ **Maintaining agency** - UA still chooses how to respond
✅ **Staying diegetic** - All interactions narratively justified
✅ **Balancing control** - Sometimes you act, sometimes world acts on you

This makes the simulation feel more alive and unpredictable while maintaining the invisible scaffolding philosophy of the Four-Mode Narrative Loop.
