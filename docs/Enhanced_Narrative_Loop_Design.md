# Enhanced Four-Mode Narrative Loop - Design Document

## Core Philosophy: Reality Doesn't Push

### The Problem with "Push"
The original system had subtle "pushy" elements:
- Meander tolerance that "surfaces a soft Spark" after inactivity
- Mission systems that suggest what players "should" do
- Arbitrary timers that force mode transitions
- **Reality acting like it's sentient**

### The Solution: Observe and Respond
Reality is NOT sentient. It doesn't push you toward anything. The world responds to YOUR intent, not the other way around.

---

## Key Enhancements

### 1. **User Intent Interpreter**
**What it does:** Reads what the user WANTS from their actions, not what we want them to want.

**How it works:**
```python
UserIntent:
  - primary_want: What they're trying to accomplish NOW
  - exploration_focus: What they're investigating
  - social_target: Who they're engaging with
  - movement_direction: Where they're going
  - avoidance_pattern: What they're avoiding
  - confidence: How clear the intent is (0.0-1.0)
```

**Example:**
- User types: "I look around the garage"
- System interprets: `primary_want=None, exploration_focus="garage", confidence=0.4`
- Result: ROAM mode, no push, just describe what they find

- User types: "I need to find tools to fix my car"
- System interprets: `primary_want="Fix car", confidence=0.9`
- Result: SPARK mode, acknowledge their interest

### 2. **Context Awareness**
**What it tracks:**
- **Spatial:** Location, visible places, accessible paths, atmosphere
- **Temporal:** Time of day, weather, season, time pressure (from fiction, not arbitrary)
- **Social:** Present NPCs, their emotional states, social atmosphere
- **Environmental:** Ambient sounds, visible objects, hazards, opportunities
- **Fiction State:** Unresolved threads, recent events

**Why it matters:**
- Narration responds to REALITY, not game state
- Opportunities come from what's actually there, not arbitrary spawns
- Pressure comes from fiction (storm approaching, NPC getting impatient), not timers

### 3. **Task vs Goal Distinction**
**Goals (Life-Defining):**
- Long-term, resistant to change
- Require major life events to modify
- Example: "Find my missing sister"
- Importance levels: LIFE_DEFINING, MAJOR, MODERATE

**Tasks (Immediate/Dynamic):**
- Short-term, update based on user actions
- Reflect current priorities
- Example: "Get rest", "Find food", "Investigate the garage"
- Priority levels: CRITICAL, HIGH, MODERATE, LOW
- Categories: SURVIVAL, GOAL_RELATED, SOCIAL, EXPLORATION, MAINTENANCE, REACTIVE

**Integration:**
- Tasks are inferred from user actions (rule-based + LLM)
- Goals only change with significant events
- Current task shown in framing guidance
- NO automatic task assignment - only interpretation of what user is doing

### 4. **Mode Transitions (No Push)**

#### ROAM → SPARK
**Trigger:** User shows clear intent (confidence ≥ 0.6)
**NOT:** Arbitrary "meander tolerance" timer
**Example:** User types "I want to talk to that mechanic" → SPARK mode

#### SPARK → PRESSURE
**Trigger:** Fiction naturally presents obstacles (environmental pressure > 0.7 OR social pressure > 0.7)
**NOT:** Forced conflict or arbitrary difficulty
**Example:** Mechanic is busy, storm approaching, shop closing soon

#### PRESSURE → OUTCOME
**Trigger:** Natural resolution point (unresolved threads = 0)
**NOT:** Arbitrary completion timer
**Example:** User successfully gets the information they wanted

#### OUTCOME → ROAM
**Trigger:** After 1 turn of resolution/reflection
**NOT:** Forced back to exploration
**Example:** User processes what happened, decides next move

### 5. **Diegetic Momentum (Reality-Based)**

**What it measures:**
- **Scene Energy:** How static/dynamic is the situation (from user actions)
- **Character Motivation:** Goal clarity from user behavior
- **Environmental Pressure:** Time-sensitive factors IN THE FICTION
- **Social Dynamics:** NPC patience and reactions (from their state, not arbitrary)
- **Location Context:** Busy vs quiet, safe vs dangerous (from scene description)

**What it DOESN'T use:**
- ❌ Arbitrary timers
- ❌ "You've been here too long" counters
- ❌ Forced escalation
- ❌ Gamey mechanics

**Example:**
```
Scene: "The garage is closing in 30 minutes" (mentioned in scene description)
→ Environmental pressure = 0.8 (from fiction, not arbitrary)
→ Tone shifts to WARMING
→ Narration mentions the approaching deadline naturally
```

### 6. **Invisible Scaffolding**

**What the user NEVER sees:**
- Mode names (ROAM, SPARK, PRESSURE, OUTCOME)
- Confidence scores
- Momentum values
- Task priorities
- Goal importance levels

**What the user DOES see:**
- Natural scene descriptions
- Diegetic cues (NPCs talking, environmental details)
- Consequences of their actions
- Opportunities that exist in the fiction

**Example Output:**
```
❌ BAD: "You've entered SPARK mode. Mission available: Talk to mechanic."
✅ GOOD: "The mechanic glances up from his work, wiping grease from his hands."
```

### 7. **Conflict-Optional (Kishōtenketsu)**

**Traditional Story Structure:**
- Setup → Conflict → Resolution
- Forces combat/confrontation

**Kishōtenketsu Structure:**
- Ki (Introduction) → Shō (Development) → Ten (Twist) → Ketsu (Conclusion)
- Twist can be perspective shift, revelation, or recontextualization
- NO forced conflict

**Example:**
```
User explores abandoned warehouse (ROAM)
User notices strange symbols on wall (SPARK)
PRESSURE options:
  - Traditional: "Armed guards appear!"
  - Kishōtenketsu: "You realize the symbols are a map to something else"
```

---

## Integration with Existing Systems

### With InterpreterAgent
- Enhanced loop receives `action_interpretation` from InterpreterAgent
- Uses it to inform intent interpretation
- NO duplicate LLM calls when interpretation exists

### With NarratorAgent
- Framing guidance passed to narrator
- Narrator uses mode/tone/context to color narration
- All structure remains invisible to user

### With GoalTaskManager
- Enhanced loop tracks current task and goals
- Updates tasks based on user actions (rule-based inference)
- Goals only change with significant events (conservative)

### With DiegeticMomentumTracker
- Enhanced loop uses existing momentum tracker
- Momentum informs mode transitions
- All momentum is fiction-based, not arbitrary

---

## Usage Example

```python
from llm_agents.enhanced_narrative_loop import EnhancedNarrativeLoop
from goal_task_system import GoalTaskManager

# Initialize
goal_task_manager = GoalTaskManager()
narrative_loop = EnhancedNarrativeLoop(llm_client, goal_task_manager)

# Process turn
turn_data = {
    'user_input': "I look around the garage",
    'scene_description': scene_description,
    'interpretation_data': interpreter_result
}

framing = narrative_loop.process_turn(
    turn_data,
    scene_description,
    time_context,
    available_npcs
)

# Use framing in narrator
narrative = narrator.generate_exploration_action_result_narrative(
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    success_total=success_total,
    time_context=time_context,
    framing_guidance=framing  # ← Enhanced framing
)
```

---

## Framing Guidance Structure

```python
{
    # Mode state
    'mode': 'roam',  # roam/spark/pressure/outcome
    'tone': 'calm',  # calm/warming/hot
    'mode_changed': False,
    'mode_reasoning': "User is exploring without clear direction",
    'scene_type': 'doing',  # doing/reflecting
    
    # User intent (what they WANT)
    'user_intent': {
        'primary_want': None,  # or "Fix car", etc.
        'exploration_focus': "garage",
        'social_target': None,
        'confidence': 0.4,
        'is_clear': False,
        'is_drifting': True
    },
    
    # Context (what IS)
    'context': {
        'location': "Rusty's garage",
        'time': 'morning',
        'weather': 'clear',
        'atmosphere': 'peaceful',
        'present_npcs': [],
        'opportunities': ['tool bench', 'car parts', 'bulletin board'],
        'summary': "Location: Rusty's garage | Time: morning, clear"
    },
    
    # Momentum (fiction state)
    'momentum': {
        'scene_energy': 0.4,
        'character_motivation': 0.3,
        'environmental_pressure': 0.2,
        'social_dynamics': 0.0,
        'location_context': 0.5
    },
    
    # Narrative guidance (for narrator)
    'narrative_guidance': "**ROAM MODE - Respond to User Exploration:**...",
    'diegetic_cues': [
        "User is exploring without clear direction",
        "Visible opportunities: tool bench, car parts, bulletin board"
    ],
    
    # Task/Goal state
    'current_task': None,
    'active_goals': ["Pay off racing debts"]
}
```

---

## Benefits

### For Users
- ✅ Feels completely natural and rule-free
- ✅ No artificial pushing or forcing
- ✅ World responds to their intent
- ✅ Can drift or pursue goals freely
- ✅ Conflict is optional, not forced

### For Narration
- ✅ Rich context for generating responses
- ✅ Clear guidance on tone and framing
- ✅ Diegetic cues for natural storytelling
- ✅ Mode structure invisible to user

### For System
- ✅ Clean separation of concerns
- ✅ Observable user behavior
- ✅ Fiction-based momentum
- ✅ Task/Goal distinction
- ✅ Full context awareness

---

## Migration Path

1. **Phase 1:** Test enhanced loop alongside existing loop
2. **Phase 2:** Update narrator to use enhanced framing
3. **Phase 3:** Integrate with main simulation loop
4. **Phase 4:** Remove old narrative loop system
5. **Phase 5:** Refine based on user feedback

---

## Key Takeaways

**Reality doesn't push you - it responds to you.**

- User intent drives everything
- Context provides reality awareness
- Momentum comes from fiction, not timers
- Tasks reflect what user is doing
- Goals are life-defining and resistant
- Modes are observational, not prescriptive
- Everything is invisible scaffolding
- Conflict is optional via Kishōtenketsu

**The system observes and responds. It never pushes.**
