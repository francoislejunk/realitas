# SPARK Fade Narration & Selection Logic

## 1. SPARK Fade Narration (When Urgency Passes)

### **YES - We narrate when SPARKs fade**

**Implementation**: `_fade_spark_back_to_roam()` (redesigned_main.py line 211)

### How It Works

**Trigger Conditions:**
- `spark_fade_turns <= 0` (turn limit reached)
- OR `now_hours >= spark_fade_deadline` (time limit reached)

**What Happens:**
1. System detects SPARK persistence expired
2. Calls `_fade_spark_back_to_roam()`
3. **Narrator generates fade narrative** showing natural resolution
4. Scene description updates to reflect SPARK is gone
5. Returns to normal ROAM mode

### Fade Narrative Examples

#### **Actor Arrival - LOW Urgency (1 turn)**
```
Turn 1: Street vendor waves at you from his cart, mentions sister's case
[UA ignores, searches warehouse instead]

FADE NARRATION:
"The street vendor shrugs and returns to arranging his wares. The moment 
recedes and the environment settles back into its usual rhythm."
```

#### **Actor Arrival - MEDIUM Urgency (2 turns)**
```
Turn 1: Nervous informant approaches, whispers about sister
[UA ignores, continues investigation]

Turn 2: Informant still waiting, glancing nervously at door
[UA still ignores]

FADE NARRATION:
"The nervous informant shakes his head, disappointed, and hurries out 
of the diner. Whatever information he had is gone with him. The moment 
recedes and the environment settles back into its usual rhythm."
```

#### **Actor Arrival - HIGH Urgency (3+ turns, may escalate)**
```
Turn 1: Bloodied man stumbles from alley, gasps about sister being moved tonight
[UA ignores, continues searching]

Turn 2: Man's breathing becomes labored, he's losing consciousness
[UA still ignores]

Turn 3: Man stops breathing
[UA still ignores]

FADE NARRATION:
"The man lies still on the pavement. A few passersby gather, someone 
calls for an ambulance. Whatever urgent information he had died with 
him. The moment recedes and the environment settles back into its 
usual rhythm."
```

#### **Incident - LOW Urgency**
```
Turn 1: Notice suspicious van parked (matching witness description)
[UA ignores, investigates building instead]

FADE NARRATION:
"The van remains parked where you noticed it, but your attention has 
moved elsewhere. The moment recedes and the environment settles back 
into its usual rhythm."
```

#### **Incident - HIGH Urgency (escalates)**
```
Turn 1: Gunshots from warehouse, figures dragging someone to van
[UA ignores, walks away]

Turn 2: Van engine starts, tires screech
[UA still ignoring]

Turn 3: Van speeds off into the night
[UA still ignoring]

FADE NARRATION:
"The van's taillights disappear around the corner. Whatever was 
happening at that warehouse is over now, and you weren't part of it. 
The moment recedes and the environment settles back into its usual 
rhythm."
```

#### **Eureka - MEDIUM Urgency**
```
Turn 1: Realize all disappearances on 15th, next one in 3 days
[UA ignores, focuses on other leads]

Turn 2: Pattern still in your mind but not acted upon
[UA still not acting]

FADE NARRATION:
"The pattern you noticed fades from immediate concern as other matters 
demand your attention. The 15th will come whether you act on this 
insight or not. The moment recedes and the environment settles back 
into its usual rhythm."
```

### Key Features of Fade Narration

✅ **Diegetic**: Shows natural world consequences
✅ **Non-punishing**: Describes what happened, doesn't scold UA
✅ **Consequence-aware**: HIGH urgency shows realistic outcomes (man dies, van escapes)
✅ **Closure**: Provides narrative closure so UA can move on
✅ **Optional**: Even after fade, UA could still pursue related leads later

---

## 2. How LLM Selects SPARK Type and Urgency

### **Context-Based Selection**

The LLM analyzes the current context to choose appropriate SPARK type and urgency:

### SPARK Type Selection

**Factors Considered:**
- UA's current goal
- Recent UA actions
- Scene setting
- Present NPCs
- Narrative tone

**Decision Logic:**

#### **Choose ACTOR ARRIVAL when:**
- UA's goal requires **information** from someone
- UA's goal needs **help or allies**
- UA's goal involves **confrontation** with someone
- Scene has room for new person to arrive naturally
- **Example**: Detective needs informant for missing sister case

#### **Choose INCIDENT when:**
- UA's goal involves **investigating events**
- UA's goal requires **following leads**
- UA's goal needs **responding to situations**
- Scene has ongoing or potential activity
- **Example**: Detective investigating warehouse where sister was last seen

#### **Choose EUREKA when:**
- UA has been **gathering clues/information**
- UA has pieces that could **connect into insight**
- Enough time has passed for **reflection/realization**
- UA's recent actions suggest pattern recognition
- **Example**: Detective reviewing notes, notices pattern in dates

### Urgency Level Selection

**Factors Considered:**
- Narrative tone (CALM/WARMING/HOT)
- Time elapsed in simulation
- UA's goal progress
- Recent action intensity
- Story pacing needs

**Decision Logic:**

#### **Choose LOW urgency when:**
- Narrative tone is CALM
- No immediate time pressure in story
- UA has been exploring casually
- SPARK is supplementary opportunity
- **Example**: Casual conversation opportunity, static clue

#### **Choose MEDIUM urgency when:**
- Narrative tone is WARMING
- Some time sensitivity exists
- UA has been actively investigating
- SPARK advances plot meaningfully
- **Example**: Informant who can't stay long, ongoing activity

#### **Choose HIGH urgency when:**
- Narrative tone is HOT
- Immediate stakes or deadline exists
- UA's goal has critical moment
- Story needs dramatic escalation
- **Example**: Injured person, active crisis, time-critical deadline

### Context Examples

#### **Context → ACTOR ARRIVAL, MEDIUM urgency**
```
Scene: Diner at night
UA Goal: Find missing sister
Recent Actions: Asking questions, showing photo
Narrative Tone: WARMING
Time Elapsed: 120 seconds

LLM Decision:
- Type: ACTOR ARRIVAL (goal needs information from person)
- Urgency: MEDIUM (warming tone, some time pressure)
- Result: "Nervous informant approaches with information"
```

#### **Context → INCIDENT, HIGH urgency**
```
Scene: Warehouse district
UA Goal: Find missing sister
Recent Actions: Following van, investigating building
Narrative Tone: HOT
Time Elapsed: 150 seconds

LLM Decision:
- Type: INCIDENT (goal involves investigating events)
- Urgency: HIGH (hot tone, immediate stakes)
- Result: "Gunshots from warehouse, figures dragging someone"
```

#### **Context → EUREKA, LOW urgency**
```
Scene: Detective's office
UA Goal: Find missing sister
Recent Actions: Reviewing notes, examining evidence
Narrative Tone: CALM
Time Elapsed: 100 seconds

LLM Decision:
- Type: EUREKA (UA gathering clues, time for insight)
- Urgency: LOW (calm tone, no immediate pressure)
- Result: "Notice pattern in disappearance dates"
```

### Guidance Added to LLM Prompt

**Lines 89-99 in spark_generator.py:**

```
**HOW TO CHOOSE SPARK TYPE:**
- ACTOR ARRIVAL: When the UA's goal requires information, help, or confrontation from another person
- INCIDENT: When the UA's goal involves investigating events, following leads, or responding to situations
- EUREKA: When the UA has been gathering clues/information and could make a breakthrough realization

**HOW TO CHOOSE URGENCY LEVEL:**
- LOW: Gentle opportunity, no time pressure, can be revisited later
- MEDIUM: Notable situation with some time sensitivity
- HIGH: Urgent situation with immediate stakes or deadline

Consider: Recent UA actions, narrative tone, goal progress, and time elapsed. 
Match urgency to the natural flow of the story.
```

---

## Summary

### **1. Fade Narration**
✅ **YES - Always narrated** when SPARK persistence expires
✅ **Diegetic** - Shows natural world consequences
✅ **Closure** - Provides narrative resolution
✅ **Consequence-aware** - HIGH urgency shows realistic outcomes

### **2. Selection Logic**
✅ **Context-driven** - LLM analyzes current situation
✅ **Goal-focused** - Type matches what goal needs
✅ **Tone-aware** - Urgency matches narrative intensity
✅ **Story-paced** - Considers time elapsed and action flow

The system ensures SPARKs feel natural, contextually appropriate, and provide meaningful (but optional) opportunities for goal advancement!
