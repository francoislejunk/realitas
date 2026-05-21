# Internal Voice - Complete Guide & All Roles

## What is Internal Voice?

**Internal Voice** is the character's internal thoughts and mental commentary that appears during gameplay. It uses **"we" voice** (2nd person plural) to make you feel like YOU are the character thinking, not being told by an external narrator.

**Visual Format:**
```
──────────────────────────────────────────────────────────────────────
💭 We've seen places like this before. Reminds us of that ice cream 
   store Dad used to take us to.
──────────────────────────────────────────────────────────────────────
```

**Display:** Bold Cyan color with separator lines above and below

## Purpose in the Simulation

### Core Purpose
**Diegetic Character Expression** - Internal Voice makes the simulation feel like you're BEING a character who thinks, not WATCHING a character being described.

### Key Functions

1. **Immersion** - Makes you feel like the character's thoughts are YOUR thoughts
2. **Personality** - Expresses character's unique perspective and traits
3. **Memory** - Recalls relevant past experiences naturally
4. **Guidance** - Suggests solutions and next steps (but can be wrong!)
5. **Awareness** - Notes needs, dangers, and opportunities
6. **Constraint Explanation** - Explains why actions can't be performed (diegetically)

## All Roles of Internal Voice

### 1. **Exploration Commentary (ROAM Mode)**

**When:** During solo exploration and observation  
**Purpose:** Character's reactions to environment  
**File:** `narrator_agent.py` - `generate_internal_voice()` method

**Examples:**
```
💭 We've seen places like this before. Reminds us of that ice cream store Dad used to take us to.

💭 Something about this alley doesn't sit right. Too quiet.

💭 The engine's purring now. Feels good to fix something with our own hands.
```

**Context Used:**
- Character personality traits
- Current status levels (stamina, spirit, supply)
- Active goals/tasks
- Inventory items
- Relationships with NPCs
- Recent narrative events

**Characteristics:**
- 1-2 sentences maximum
- Uses "we", "us", "our"
- Only appears in ROAM mode (disappears during conversations)
- Can recall memories
- Can suggest solutions
- Can be wrong sometimes

---

### 2. **Intent Availability Constraints (NEW)**

**When:** User tries an action that can't be performed  
**Purpose:** Explain location or existence constraints diegetically  
**File:** `intent_availability_system.py` - `_generate_diegetic_explanation()` method

**Three Types:**

#### A. **EXIST** - Action proceeds normally
- No internal voice needed
- Action continues

#### B. **EXIST (NOT HERE)** - Location constraint
**Purpose:** Explain why action can't be done at current location

**Examples:**
```
💭 Oh we left our phone at the diner last night, we should hurry and 
   get it back before someone takes it.

💭 Right, the laptop is back at the apartment. We'll need to head 
   home first.

💭 John's probably at his usual spot downtown. We'd need to go there 
   to talk to him.
```

**Characteristics:**
- Explains WHERE the required item/person is
- Creates exploration goal
- Saves as deferred intent for future opportunities
- Uses "we" voice

#### C. **DOES NOT EXIST** - Existence constraint
**Purpose:** Explain why something doesn't exist in the world

**Examples:**
```
💭 It's been years since we last got in contact with John... he 
   changed his number a few years back.

💭 We never had a car. That's just wishful thinking.

💭 There's no magic in this world. What am I even thinking?
```

**Characteristics:**
- Recalls memories or realizations
- Uses past tense for memories
- Gentle but clear
- Explains absence through character knowledge

---

### 3. **Inquiry Responses (Mental Actions)**

**When:** User asks questions about the world  
**Purpose:** Answer questions from character's perspective  
**File:** `narrator_agent.py` - `generate_inquiry_internal_voice()` method

**Examples:**
```
User: "What's the best way to get downtown?"
💭 We can take the U-Bahn from here, it's quicker than walking...

User: "Do I know anyone who could help?"
💭 Maybe Vince at the garage? He owes us a favor from last month.

User: "What time is it?"
💭 Should be around 3 PM by now. Sun's getting lower.
```

**Characteristics:**
- Answers based on character knowledge
- References memories when relevant
- Can admit lack of knowledge
- 1-2 sentences
- Uses "we" voice

---

### 4. **Memory Uncovering**

**When:** Intent-based memory system discovers character background  
**Purpose:** Reveal character memories through internal thoughts  
**File:** `intent_based_memory_creation.py`

**Examples:**
```
User: "I want to go to my childhood home"
[Memory system triggers]

💭 We haven't been back there since Mom passed. Wonder if the old 
   oak tree is still standing...

🔍 MEMORY UNCOVERED
═══════════════════════════════════════
📝 Childhood Home Memory
[Memory details]
💭 Internal Voice: [Memory-based thought]
═══════════════════════════════════════
```

**Characteristics:**
- Triggered by user intents
- Reveals character backstory
- Creates emotional connections
- Probabilistic (not every time)

---

### 5. **Diegetic Transition Pauses**

**When:** User gives sweeping intent that would skip time  
**Purpose:** Pause at diegetic boundaries with character thoughts  
**File:** `diegetic_transition_system.py`

**Examples:**
```
User: "I finish breakfast and head to the garage"
[System detects sweeping intent]

💭 Better eat quick. Got a lot of work waiting at the garage today.

[Experience of eating breakfast]

[Pause before transition to garage]
```

**Characteristics:**
- Prevents time skips
- Provides character thoughts at transitions
- Maintains immersion during multi-step actions

---

### 6. **Solution Suggestions (Enhanced)**

**When:** During exploration, character suggests approaches  
**Purpose:** Proactive problem-solving from character's perspective  
**File:** `narrator_agent.py` - `generate_internal_voice()` method

**Examples:**
```
💭 Maybe we should check the back entrance. Worth a shot.

💭 We need to eat soon. Getting light-headed.

💭 Should probably avoid that guy. Looks like he's had a rough day.

💭 This'll be quick. In and out, no problem. (narrator note: it won't be)

💭 Pretty sure Mike mentioned something about this place. Or was it Tony?
```

**Characteristics:**
- Suggests next steps
- Offers reminders about needs
- Makes educated guesses
- **Can be wrong** - overconfident, misremembering, misjudging
- Reflects real internal dialogue

---

## Technical Architecture

### Where Internal Voice is Generated

1. **NarratorAgent** (`narrator_agent.py`)
   - `generate_internal_voice()` - Main exploration commentary
   - `generate_inquiry_internal_voice()` - Inquiry responses

2. **IntentAvailabilitySystem** (`intent_availability_system.py`)
   - `_generate_diegetic_explanation()` - Constraint explanations

3. **IntentBasedMemoryCreation** (`intent_based_memory_creation.py`)
   - Memory uncovering internal voice

4. **DiegeticTransitionSystem** (`diegetic_transition_system.py`)
   - Transition pause internal voice

### Integration Points in Main Loop

**File:** `redesigned_main.py`

1. **After Given Actions** (~line 3368-3390)
2. **After Exploration Actions** (~line 3830-3852)
3. **During Intent Availability Checks** (when action blocked)
4. **During Inquiry Processing** (mental actions)
5. **During Memory Uncovering** (intent-based memories)
6. **During Diegetic Transitions** (sweeping intents)

### Display Format

```python
# Standard Internal Voice Display
print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}")
```

**Color:** Bold Cyan (`Color.INTERNAL_VOICE`)  
**Separator:** 70 dashes above and below  
**Emoji:** 💭 thought bubble

---

## Design Philosophy

### "We" Not "You"
- **"We"** = Character thinking (immersive)
- **"You"** = Narrator describing (external)

Using "we" makes you feel like YOU are the character thinking these thoughts, not being told what to think.

### ROAM Mode Only (Exploration Commentary)
Internal Voice **disappears during conversations** (ENCOUNTER mode) because:
- Real internal monologue quiets during social interaction
- Prevents "schizophrenic" narration
- Focus should be on the conversation
- More realistic and immersive

**Exception:** Constraint explanations (EXIST_NOT_HERE, DOES_NOT_EXIST) can appear anytime because they're explaining why an action can't happen.

### Fallible and Human
Internal Voice can be:
- **Wrong** - "This'll be quick" (narrator: it won't be)
- **Uncertain** - "Pretty sure Mike mentioned this... or was it Tony?"
- **Overconfident** - Making assumptions that turn out false
- **Forgetful** - Misremembering details

This makes it feel like real human thinking, not omniscient narration.

### Subtle, Not Chatty
- 1-2 sentences maximum
- Only when there's something worth noting
- Can return empty if nothing stands out
- Temperature: 0.7 for moderate creativity
- Max tokens: 100 to keep brief

---

## Comparison: Narrative vs Internal Voice

| Feature | Regular Narrative | Internal Voice |
|---------|------------------|----------------|
| **Color** | Magenta | Bold Cyan |
| **Separators** | None | Lines above & below |
| **Emoji** | None | 💭 |
| **Pronouns** | "you" | "we", "us", "our" |
| **Content** | External events | Internal thoughts |
| **Perspective** | What happens | What character thinks |
| **When** | Always | Varies by role |
| **Purpose** | Describe world | Express character |

**Example:**

**Regular Narrative (Magenta):**
```
You push through the door of Vinyl Revival. The morning air is sharp 
with exhaust and fresh asphalt. A crumpled flyer lies near the curb.
```

**Internal Voice (Bold Cyan):**
```
──────────────────────────────────────────────────────────────────────
💭 We know this place. Used to come here every Saturday before the 
   rent got too damn high.
──────────────────────────────────────────────────────────────────────
```

---

## Summary of All Roles

1. **Exploration Commentary** - Character's thoughts during ROAM mode
2. **Intent Constraints** - Explains why actions can't be performed (EXIST_NOT_HERE, DOES_NOT_EXIST)
3. **Inquiry Responses** - Answers questions from character's perspective
4. **Memory Uncovering** - Reveals character backstory through thoughts
5. **Diegetic Transitions** - Thoughts during multi-step action pauses
6. **Solution Suggestions** - Proactive problem-solving (can be wrong)

## Core Purpose

**Internal Voice makes the simulation feel like you're BEING a character who thinks, not WATCHING a character being described.**

All explanations, constraints, and commentary come from the character's perspective using "we" voice, creating deep immersion and making the world feel like it exists through the character's eyes and thoughts.
