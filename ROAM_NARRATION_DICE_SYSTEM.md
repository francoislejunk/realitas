# ROAM Mode Narration - 66/34 Dice System

## Problem Identified

**ALL action result narrations in ROAM mode were including opportunities**, which:
- ❌ Overwhelms the user with too many options
- ❌ Makes every action feel like a menu of choices
- ❌ Distracts from the natural flow of exploration
- ❌ Creates decision fatigue

## Solution: Two-Version Narration System

### **66% - DESCRIPTIVE Narration**
**Pure description of what happened**
- Describes action results and immediate effects
- Shows impact on environment, people, or character
- NO exploration hooks or opportunities
- Clean, focused narrative

### **34% - OPPORTUNITY Narration**
**Includes exploration hooks**
- Describes action results PLUS hints at new paths
- Weaves opportunities naturally into narrative
- Uses phrases like "you notice...", "nearby...", "you hear..."
- Creates branch points for player

## Implementation

### Dice Roll (narrator_agent.py line 1638)

```python
# Roll dice: 66% descriptive, 34% opportunities
include_opportunities = random.random() < 0.34
```

**How it works:**
- `random.random()` generates 0.0 to 1.0
- If < 0.34 (34% chance): `include_opportunities = True`
- If >= 0.34 (66% chance): `include_opportunities = False`

### Two Prompt Versions

Both versions share:
- ✅ 2-3 sentences, 40-60 words
- ✅ First sentence references user's action
- ✅ Scene consistency enforcement
- ✅ Success/failure/backfire handling
- ✅ 1980s atmosphere

**Key Difference:**

**DESCRIPTIVE (66%):**
```
- FOCUS ONLY on describing what happened and its immediate effects.
- DO NOT suggest new opportunities or hooks.
- Describe ONLY the action's results and effects.
- Do NOT include phrases like "you notice", "you could", "nearby".
```

**OPPORTUNITY (34%):**
```
- INCLUDE subtle exploration opportunities or hooks.
- Weave opportunities naturally into the narrative.
- Use phrases like "you notice...", "nearby...", "you hear...".
- Hint at new opportunities to explore.
```

## Examples

### Scenario: "I search the office"

#### **DESCRIPTIVE Narration (66% chance)**

**Success:**
```
You methodically search the office, checking drawers and filing cabinets. 
Most are empty, but you find a few old receipts and a dusty ledger from 
1982. The room yields little of immediate value.
```

**What it does:**
- ✅ Describes what happened (searched office)
- ✅ Shows results (found receipts and ledger)
- ✅ States outcome (little value)
- ❌ NO hooks for next action
- ❌ NO "you notice" phrases

**User feels:** "Okay, I searched. What do I want to do next?"

---

#### **OPPORTUNITY Narration (34% chance)**

**Success:**
```
You methodically search the office, checking drawers and filing cabinets. 
Most are empty, but you find a dusty ledger from 1982. As you flip through 
it, you notice fresh fingerprints on one page, and hear a phone ringing 
down the hall.
```

**What it does:**
- ✅ Describes what happened (searched office)
- ✅ Shows results (found ledger)
- ✅ Hints at opportunities (fingerprints, phone)
- ✅ Uses "you notice" and "you hear"

**User feels:** "Interesting! I could check those fingerprints, or answer that phone, or do something else."

---

### Scenario: "I examine the van"

#### **DESCRIPTIVE Narration (66% chance)**

**Success:**
```
You circle the van, examining its exterior carefully. The license plate 
matches the witness description, and there are fresh scratches along the 
driver's side door. The vehicle is locked and appears unoccupied.
```

**What it does:**
- ✅ Describes examination
- ✅ Shows findings (plate matches, scratches, locked)
- ✅ States current state (unoccupied)
- ❌ NO suggestions for next steps

**User feels:** "Got it. The van is here and locked. What should I do about it?"

---

#### **OPPORTUNITY Narration (34% chance)**

**Success:**
```
You circle the van, examining its exterior carefully. The license plate 
matches the witness description, and fresh scratches mar the driver's door. 
Through the tinted windows, you notice a briefcase on the back seat, and 
catch the faint smell of cigarette smoke still lingering nearby.
```

**What it does:**
- ✅ Describes examination
- ✅ Shows findings (plate, scratches)
- ✅ Hints at opportunities (briefcase visible, smoke smell)
- ✅ Uses "you notice" and sensory details

**User feels:** "Interesting! I could try to see that briefcase better, follow the smoke smell, or do something else."

---

### Scenario: "I rest for a moment"

#### **DESCRIPTIVE Narration (66% chance)**

**Success:**
```
You lean against the warehouse wall and take a breath. The cool night air 
helps clear your head, and you feel your energy returning slightly. After 
a few minutes, you're ready to continue.
```

**What it does:**
- ✅ Describes resting
- ✅ Shows effect (energy returning)
- ✅ States readiness (ready to continue)
- ❌ NO environmental hooks

**User feels:** "Okay, I rested. Now what?"

---

#### **OPPORTUNITY Narration (34% chance)**

**Success:**
```
You lean against the warehouse wall and take a breath. The cool night air 
helps clear your head, and from this vantage point you notice the loading 
dock door is slightly ajar, with fresh tire tracks leading toward it.
```

**What it does:**
- ✅ Describes resting
- ✅ Shows effect (clear head)
- ✅ Hints at opportunity (ajar door, tire tracks)
- ✅ Uses "you notice"

**User feels:** "Interesting! I could check that door, or do something else."

---

## Comparison Table

| Aspect | **DESCRIPTIVE (66%)** | **OPPORTUNITY (34%)** |
|--------|----------------------|----------------------|
| **Focus** | What happened | What happened + what's available |
| **Length** | 2-3 sentences | 2-3 sentences |
| **Hooks** | None | 1-2 subtle hooks |
| **Phrases** | Avoids "notice", "could", "nearby" | Uses "notice", "hear", "nearby" |
| **Feel** | Clean, focused | Exploratory, branching |
| **User Response** | "What do I want to do?" | "Interesting options here!" |
| **Frequency** | Most of the time | Occasionally |

## Benefits

### **For User Experience:**
✅ **Reduced overwhelm** - Not every action presents a menu
✅ **Natural pacing** - Opportunities feel special when they appear
✅ **Player agency** - User decides direction without constant prompting
✅ **Breathing room** - Descriptive narrations let story breathe

### **For Narrative Flow:**
✅ **Variety** - Mix of focused and exploratory narrations
✅ **Rhythm** - 66/34 split creates natural ebb and flow
✅ **Surprise** - Opportunities feel discovered, not forced
✅ **Immersion** - Less "gamey" feeling

### **For Exploration:**
✅ **Meaningful hooks** - When opportunities appear, they matter
✅ **SPARK synergy** - Opportunities complement SPARKs (goal-focused)
✅ **Player-driven** - User explores because they want to, not because prompted
✅ **Less fatigue** - Fewer decisions to make per action

## How It Feels in Play

### **Typical ROAM Session:**

```
Action 1: "I search the warehouse"
→ DESCRIPTIVE (66%): "You search methodically. Most crates are empty."

Action 2: "I check the office"
→ DESCRIPTIVE (66%): "The office is dusty and abandoned. Nothing of note."

Action 3: "I examine the loading dock"
→ OPPORTUNITY (34%): "The loading dock is quiet, but you notice fresh tire 
   tracks and hear voices from the alley beyond."

Action 4: "I follow the voices"
→ DESCRIPTIVE (66%): "You move toward the alley carefully. The voices grow 
   louder as you approach."

Action 5: "I peek around the corner"
→ DESCRIPTIVE (66%): "You peer into the alley. Two figures stand by a van, 
   arguing in hushed tones."

Action 6: "I listen to their conversation"
→ OPPORTUNITY (34%): "You strain to hear their words. One mentions 'the 
   shipment tonight,' and you notice the van's license plate matches your 
   sister's case. A payphone nearby offers a chance to call for backup."
```

**Result:**
- Clean exploration flow
- Opportunities feel earned/discovered
- User drives the investigation
- Not overwhelmed with constant choices

## Technical Details

### Random Seed
- Uses Python's `random.random()`
- No seed set = truly random each time
- Could add seed for testing/debugging if needed

### Probability Distribution
- 66% descriptive = 2 out of 3 actions (roughly)
- 34% opportunity = 1 out of 3 actions (roughly)
- Over 10 actions: ~6-7 descriptive, ~3-4 with opportunities

### Both UA and NUA
- System works for both User Actors (second person)
- And Non-User Actors (third person)
- Same 66/34 split for both

## Future Considerations

### Potential Adjustments

**Could make probability dynamic:**
```python
# Example: Increase opportunity chance in SPARK mode
if narrative_mode == 'spark':
    opportunity_chance = 0.50  # 50% in SPARK mode
else:
    opportunity_chance = 0.34  # 34% in ROAM mode

include_opportunities = random.random() < opportunity_chance
```

**Could track recent history:**
```python
# Example: Ensure at least 1 opportunity every 5 actions
if last_5_actions_all_descriptive:
    include_opportunities = True  # Force opportunity
else:
    include_opportunities = random.random() < 0.34
```

**Current implementation:** Simple 66/34 split, no dynamic adjustment

## Summary

✅ **Implemented** 66/34 dice roll system
✅ **Two versions** of ROAM narration (descriptive vs opportunity)
✅ **Reduces overwhelm** by making opportunities occasional, not constant
✅ **Maintains quality** - both versions are well-crafted narratives
✅ **Player agency** - user explores naturally, not prompted constantly
✅ **Better pacing** - opportunities feel special when they appear

The system creates a more natural, less overwhelming exploration experience while still providing meaningful hooks when appropriate!
