# SPARKs vs OPPORTUNITIES - System Clarification

## The Confusion

Currently, we have **THREE different concepts** using similar terminology:

1. **Spark Generator** (`spark_generator.py`) - Time-based NUA introduction system
2. **Narrative Loop SPARK Mode** (`narrative_loop_system.py`) - Story beat for presenting prompts
3. **Opportunities** - Embedded narrative hooks (NOT YET FORMALIZED)

These need to be **clearly separated and renamed** for clarity.

---

## PROPOSED SYSTEM ARCHITECTURE

### 1. **SPARKS** (Goal-Driven Events)

**File**: `spark_generator.py`
**Purpose**: Push the UA's GOAL forward through diegetic events
**Trigger**: After 90+ seconds in ROAM mode (time-based)

**Three Types of SPARKs:**

#### A. **Actor Arrival SPARK**
```
A nervous informant approaches you at the diner, glancing nervously 
at the door. "Detective," he whispers, "I have information about 
your sister's case. But we can't talk here."
```
- **What**: New NUA arrives
- **Goal Relevance**: Direct connection to finding sister
- **UA Choice**: Talk to him, ignore, leave
- **NUA-Initiated Exchange**: 50% chance this becomes a forced exchange (NUA demands response)

#### B. **Incident SPARK**
```
Through the warehouse window, you see two figures arguing near a 
black van - the same model witnesses described near your sister's 
last known location. One of them pulls out a briefcase.
```
- **What**: Event happens nearby
- **Goal Relevance**: Potential lead on sister's case
- **UA Choice**: Investigate, watch, ignore

#### C. **Eureka SPARK**
```
As you review your notes, a pattern suddenly clicks - the dates of 
the disappearances all fall on the 15th. Your sister vanished on 
March 15th. The next 15th is in three days.
```
- **What**: Realization/discovery over time
- **Goal Relevance**: Breakthrough in investigation
- **UA Choice**: Act on it, file it away, dismiss it

**Key Characteristics:**
- ✅ **Goal-focused**: Always relates to UA's long-term GOAL
- ✅ **Diegetic**: Natural narrative events, not meta prompts
- ✅ **Optional**: UA can always ignore (except forced exchanges)
- ✅ **Strategic**: Offers meaningful progress toward goal
- ✅ **Time-triggered**: Appears after 90+ seconds of exploration

**NUA-Initiated Exchange System:**

When a SPARK involves an NUA, there's a **50/50 split**:

**50% - Observational Situation:**
- NUA does something interesting nearby
- UA can choose to engage or just watch
- Examples: NUA arguing with someone, NUA having accident, NUA performing
- UA maintains full agency

**50% - Forced Exchange:**
- NUA directly approaches/confronts UA
- UA must respond (triggers contested action)
- Examples: NUA asks question, makes demand, needs help urgently
- Creates immediate dramatic tension
- Still diegetic (NUA has reason to engage)

---

### 2. **OPPORTUNITIES** (Exploration Hooks)

**File**: NEW - `opportunity_embedder.py` (to be created)
**Purpose**: Create pathways for exploration and discovery
**Location**: Embedded in narrations (scene descriptions, action results)

**Where Opportunities Appear:**

#### A. **Initial Scene Descriptions**
```
The abandoned warehouse stretches before you, its rusted metal 
doors hanging ajar. Broken windows line the second floor, and 
you notice fresh tire tracks in the mud leading around back.
```
- **Opportunities**: 
  - Investigate the open doors
  - Check the second floor windows
  - Follow the tire tracks
  - Search the perimeter

#### B. **Action Result Narrations (ROAM mode)**
```
You search the office. Dust-covered filing cabinets line the walls, 
most drawers hanging open and empty. But one cabinet in the corner 
is locked, and you notice scratches around the keyhole - recent ones.
```
- **Opportunities**:
  - Try to pick the lock
  - Force the cabinet open
  - Look for the key
  - Leave it alone

#### C. **Environmental Details**
```
The diner is quiet at this hour. A waitress refills coffee at the 
counter. In the corner booth, a man in a fedora keeps checking his 
watch. The payphone near the restrooms has an "Out of Order" sign, 
but you hear it ring once.
```
- **Opportunities**:
  - Talk to the waitress
  - Observe the man in the booth
  - Check the payphone
  - Order food

**Key Characteristics:**
- ✅ **Exploration-focused**: Tactical, immediate possibilities
- ✅ **Embedded**: Part of narrative description, not separate events
- ✅ **Optional**: UA can pursue any, all, or none
- ✅ **Tactical**: About "what can I do here?" not "how do I achieve my goal?"
- ✅ **Narration-triggered**: Appears in scene/action descriptions

---

### 3. **NARRATIVE LOOP SPARK MODE** (Story Beat)

**File**: `narrative_loop_system.py`
**Purpose**: Story structure beat for presenting gentle prompts
**Rename To**: **"PROMPT MODE"** (to avoid confusion)

**What It Does:**
- Guides narrator to present gentle nudges
- Transitions from ROAM (exploration) to PROMPT (gentle direction)
- NOT the same as SPARK events from spark_generator.py

**Proposed Rename:**
```python
class NarrativeMode(Enum):
    ROAM = "roam"        # Drift-friendly exploration
    PROMPT = "prompt"    # Gentle nudge into purpose (RENAMED from SPARK)
    PRESSURE = "pressure" # Heightened stakes
    OUTCOME = "outcome"   # Natural resolution
```

**Why Rename:**
- Avoids confusion with SPARK events
- Clarifies it's about narrative pacing, not specific events
- "PROMPT" better describes "gentle nudge" function

---

## COMPARISON TABLE

| Feature | **SPARKS** | **OPPORTUNITIES** | **PROMPT MODE** |
|---------|-----------|------------------|-----------------|
| **Purpose** | Push GOAL forward | Create exploration paths | Story pacing beat |
| **Focus** | Strategic (goals) | Tactical (exploration) | Structural (narrative) |
| **Trigger** | 90+ seconds in ROAM | Every narration | Soft signals detected |
| **Location** | Separate event | Embedded in text | Narrator guidance |
| **Type** | Actor/Incident/Eureka | Environmental details | Story beat |
| **Goal Relevance** | Always high | Variable | N/A (structural) |
| **Example** | "Informant approaches" | "You notice a locked door" | [Narrator: present gentle prompt] |

---

## IMPLEMENTATION CHANGES NEEDED

### 1. **Rename Narrative Loop SPARK Mode**

**File**: `narrative_loop_system.py`

```python
# OLD
class NarrativeMode(Enum):
    ROAM = "roam"
    SPARK = "spark"      # ❌ CONFUSING
    PRESSURE = "pressure"
    OUTCOME = "outcome"

# NEW
class NarrativeMode(Enum):
    ROAM = "roam"
    PROMPT = "prompt"    # ✅ CLEAR - gentle narrative nudge
    PRESSURE = "pressure"
    OUTCOME = "outcome"
```

**Update all references:**
- `NarrativeMode.SPARK` → `NarrativeMode.PROMPT`
- `"spark"` → `"prompt"` in mode descriptions
- Comments about "spark readiness" → "prompt readiness"

### 2. **Clarify Spark Generator Terminology**

**File**: `spark_generator.py`

**Update prompt to specify three SPARK types:**
```python
**SPARK TYPES:**
1. **ACTOR ARRIVAL**: A new NUA arrives on scene with goal-relevant purpose
2. **INCIDENT**: An event happens nearby that relates to the UA's goal
3. **EUREKA MOMENT**: A realization or discovery that opens new avenues

All SPARKs must:
- Relate directly to the UA's GOAL (not tasks)
- Be diegetic narrative events
- Offer optional interaction
- Provide strategic value
```

**Update response format:**
```json
{
    "spark_narrative": "...",
    "spark_category": "actor_arrival/incident/eureka",  // NEW
    "goal_relevance": "How this relates to UA's goal",  // NEW
    "nua_character": {...},  // Only for actor_arrival
    "scene_update": "...",
    "ua_options": [...],
    "urgency_level": "low/medium/high"
}
```

### 3. **Create Opportunity Embedder System**

**New File**: `opportunity_embedder.py`

```python
class OpportunityEmbedder:
    """
    Embeds exploration opportunities into narrative descriptions.
    Opportunities are tactical hooks that suggest what the UA could
    do in their current environment.
    """
    
    def embed_opportunities_in_scene(self, scene_description: str) -> str:
        """Add exploration hooks to initial scene description"""
        pass
    
    def embed_opportunities_in_narration(self, action_result: str) -> str:
        """Add exploration hooks to action result narrations"""
        pass
    
    def _generate_environmental_opportunities(self, context: Dict) -> List[str]:
        """Generate tactical opportunities based on environment"""
        # Examples:
        # - "You notice..."
        # - "In the corner..."
        # - "You hear..."
        # - "Available nearby..."
        pass
```

**Integration Points:**
- **CreatorAgent**: Embed opportunities in initial scene descriptions
- **NarratorAgent**: Embed opportunities in ROAM mode action results
- **ConductorAgent**: Coordinate opportunity embedding

### 4. **Update Narrator Agent**

**File**: `narrator_agent.py`

**Add opportunity embedding to ROAM narrations:**
```python
def generate_roam_narration(self, action_result, scene_context):
    """Generate narration for ROAM mode with embedded opportunities"""
    
    # Generate base narration
    narration = self._generate_base_narration(action_result)
    
    # Embed opportunities (tactical hooks)
    narration_with_opportunities = opportunity_embedder.embed_opportunities_in_narration(
        narration, 
        scene_context
    )
    
    return narration_with_opportunities
```

---

## EXAMPLES IN PRACTICE

### Scenario: Detective searching for missing sister

#### **ROAM Mode - Exploration with Opportunities**

**User Action**: "I search the warehouse"

**Narration** (with embedded OPPORTUNITIES):
```
You move through the warehouse carefully, your footsteps echoing 
in the vast space. Most of the crates are empty, covered in years 
of dust. But in the back corner, you notice:

- A newer-looking padlock on one of the storage rooms
- Fresh oil stains on the concrete floor
- A bulletin board with faded notices, one dated just last week
- A staircase leading to what looks like an office on the second floor

The air smells of rust and something else - cigarette smoke, recent.
```

**Opportunities Embedded**:
- Investigate the padlocked room
- Examine the oil stains
- Read the bulletin board
- Check the second floor office
- Follow the cigarette smell

**UA Choice**: Can pursue any, all, or none

---

#### **SPARK Event - Goal-Driven (Actor Arrival)**

**Trigger**: 90+ seconds of exploration

**Example 1: Observational Situation (50% chance)**
```
🎯 SPARK DETECTED

Through the warehouse window, you see a woman in her 50s arguing 
with a man in a suit. She's waving a clipboard, pointing at 
something on the page. The man shakes his head and walks away.

She stands there for a moment, looking frustrated, then pulls 
out a photo - you can't see it clearly, but it looks like a 
missing person poster.
```

**SPARK Type**: Actor Arrival (Observational)
**Goal Relevance**: She might know about disappearances
**UA Choice**: 
- Approach her and ask about the photo
- Keep watching from a distance
- Ignore and continue searching
- Leave the area

---

**Example 2: Forced Exchange (50% chance)**
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

**SPARK Type**: Actor Arrival (Forced Exchange)
**Goal Relevance**: She knows about sister's disappearance
**UA Must Respond**: Triggers contested action
**UA Choice**: 
- Answer her questions
- Demand she explain first
- Try to leave
- Threaten her

---

#### **PROMPT Mode - Narrative Beat**

**Narrative Loop State**: ROAM → PROMPT transition

**What Narrator Does** (invisible to UA):
```
[Internal: Narrative mode = PROMPT]
[Guidance: Present gentle nudge toward character's interests]
[Tone: WARMING - building tension]
```

**Result in Narration**:
```
The warehouse feels different now. You've been here for almost 
two hours, and while you've found traces of activity, nothing 
concrete. The sun is setting outside, and you remember the 
informant's words: "They meet when it gets dark."

You could keep searching, or...
```

**This is NOT a SPARK** - it's narrative pacing guidance for the narrator.

---

## SUMMARY

### **SPARKS** (spark_generator.py)
- **What**: Goal-driven events (actor/incident/eureka)
- **When**: After 90+ seconds in ROAM
- **Why**: Push GOAL forward strategically
- **How**: Diegetic narrative events
- **Example**: "Informant approaches with sister info"

### **OPPORTUNITIES** (opportunity_embedder.py - NEW)
- **What**: Exploration hooks embedded in narrations
- **When**: Every scene description and action result
- **Why**: Create tactical pathways for exploration
- **How**: Environmental details in narrative text
- **Example**: "You notice a locked door in the corner"

### **PROMPT MODE** (narrative_loop_system.py - RENAMED)
- **What**: Story beat for narrative pacing
- **When**: Soft signals detected (want/friction/etc)
- **Why**: Guide narrator to present gentle nudges
- **How**: Internal guidance for narrator agent
- **Example**: [Narrator: present gentle prompt] (invisible to UA)

---

## ACTION ITEMS

1. ✅ **Rename** NarrativeMode.SPARK → NarrativeMode.PROMPT
2. ✅ **Clarify** spark_generator.py to specify three SPARK types
3. ✅ **Create** opportunity_embedder.py system
4. ✅ **Update** narrator_agent.py to embed opportunities
5. ✅ **Document** clear distinctions between all three systems

This separation ensures:
- No confusion between systems
- Clear purpose for each component
- Proper goal vs. exploration distinction
- Diegetic, optional player agency maintained
