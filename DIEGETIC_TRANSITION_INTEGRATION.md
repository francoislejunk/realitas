# Diegetic Transition System - Integration Guide

## Philosophy

**The system is NOT a narrator. It's an EXPERIENCE DESCRIBER.**

- **Narrator:** God-view, narrates everything, completes actions for user
- **Experience Describer:** Limited to user's senses, pauses at boundaries, waits for confirmation

## The Problem

**Current Behavior (BAD):**
```
User: "I finish breakfast and get to the garage"
System: "You finish your cereal, get dressed, get on the elevator, and walk to your car."
```
**Problems:**
- Time skip (10 floors)
- Stole multiple actions (getting dressed, elevator, walking)
- No user agency

## The Solution

**New Behavior (GOOD):**
```
User: "I finish breakfast and get to the garage"

💭 INNER VOICE
═══════════════════════════════════════════════════════════
Last time you left without brushing your teeth you scared people. 
Imagine leaving without even getting dressed.

👁️  EXPERIENCE
═══════════════════════════════════════════════════════════
You finish your breakfast, feel satiated after all that cereal, milk 
and sugar like a happy kid before going to school. On your way to 
getting ready to leave your place to get to the garage, now you're 
wondering what to do next to get prepared before leaving.

What do you do?
═══════════════════════════════════════════════════════════
```

**Benefits:**
- ✅ No time skip - paused at natural boundary
- ✅ Inner voice provides context/suggestion
- ✅ User maintains agency
- ✅ System teaches itself not to steal actions

## Two Types of Intent

### 1. Atomic Intent (Fits in 3TU)

**Examples:**
- "I open the door in front of me"
- "I pick up the phone"
- "I say 'Hello' to the guard"
- "I walk to the elevator"

**Handling:**
Just describe the experience - no breakdown needed.

```
User: "I open the door in front of me"

👁️  EXPERIENCE
═══════════════════════════════════════════════════════════
You extend your arm and feel as your hand grasps the coldness of 
the metal doorknob. As it turns, the door gives way to the light 
of the room ahead, slowly presenting the silhouette of an older 
man you've never seen before. A man with a scar across his face, 
reeking of beer, staring at you.

What do you do?
═══════════════════════════════════════════════════════════
```

### 2. Sweeping Intent (Spans Multiple 3TU)

**Examples:**
- "I finish breakfast and get to the garage" (10 floors!)
- "I get ready to leave" (dress, teeth, keys, etc.)
- "I investigate the area" (multiple locations)
- "I go get some food" (find place, order, eat)

**Handling:**
Break down with inner voice + experience description, pause at first boundary.

## Implementation

### Step 1: Analyze Intent Scope

```python
from diegetic_transition_system import DiegeticTransitionSystem

# Initialize
transition_system = DiegeticTransitionSystem(client, model, logger)

# Analyze user input
analysis = transition_system.analyze_intent_scope(
    user_input=user_input,
    scene_context=scene_description,
    actor_personality=actor.sheet.personality_traits
)

# Returns:
# {
#     "scope": IntentScope.ATOMIC or IntentScope.SWEEPING,
#     "reasoning": "explanation",
#     "estimated_steps": 1-5,
#     "needs_breakdown": True/False
# }
```

### Step 2: Handle Based on Scope

```python
if analysis['needs_breakdown']:
    # SWEEPING INTENT - Generate diegetic pause
    pause_data = transition_system.generate_diegetic_pause(
        user_input=user_input,
        scene_context=scene_description,
        actor_name=actor.sheet.name,
        actor_personality=actor.sheet.personality_traits,
        current_location=current_location
    )
    
    # Display and wait for next input
    from diegetic_transition_system import display_diegetic_pause
    display_diegetic_pause(pause_data, actor.sheet.name)
    
    # Loop back to get next user input
    continue
    
else:
    # ATOMIC INTENT - Just describe the experience
    experience = transition_system.generate_atomic_experience(
        user_input=user_input,
        scene_context=scene_description,
        actor_name=actor.sheet.name,
        current_location=current_location
    )
    
    from diegetic_transition_system import display_atomic_experience
    display_atomic_experience(experience)
    
    # Proceed with normal action resolution
    # (continuity check, interpretation, etc.)
```

## Integration Points in Main Loop

**Location in `redesigned_main.py`:**

After intent availability check, before action interpretation:

```python
# Around line 2800-2900 (after intent availability, before interpretation)

# Check if intent needs diegetic breakdown
from diegetic_transition_system import DiegeticTransitionSystem

if not hasattr(main_state, 'transition_system'):
    main_state.transition_system = DiegeticTransitionSystem(
        llm_client=openrouter_config.create_role_client("narration"),
        model=openrouter_config.get_model_for_role("narration"),
        logger=logger
    )

# Analyze intent scope
intent_analysis = main_state.transition_system.analyze_intent_scope(
    user_input=user_input,
    scene_context=scene_description,
    actor_personality=actor.sheet.personality_traits
)

if intent_analysis['needs_breakdown']:
    # Generate diegetic pause
    pause_data = main_state.transition_system.generate_diegetic_pause(
        user_input=user_input,
        scene_context=scene_description,
        actor_name=actor.sheet.name,
        actor_personality=actor.sheet.personality_traits,
        current_location=current_location
    )
    
    # Display and loop back
    from diegetic_transition_system import display_diegetic_pause
    display_diegetic_pause(pause_data, actor.sheet.name)
    continue  # Get next user input

# Otherwise, proceed with normal flow
```

## Inner Voice Guidelines

**When to Show:**
- Sweeping intents that need breakdown
- Memory/context relevant to current situation
- Suggestions based on past experience
- Commentary reflecting personality

**When to Stay Silent:**
- During NUA conversations (mostly)
- Atomic actions (usually)
- When user is focused on dialogue

**Tone:**
- First person ("I", "my", "me")
- Reflects internal personality trait
- 1-2 sentences maximum
- Can be sarcastic, thoughtful, worried, etc.

**Examples:**
```
Sarcastic: "Last time I left without brushing my teeth, I scared people."
Thoughtful: "The garage is ten floors down. Better get ready first."
Worried: "I should probably grab my keys before heading out."
Practical: "Getting dressed first would be a good idea."
```

## Experience Description Guidelines

**What to Describe:**
- ✅ What user SEES (visual details in immediate view)
- ✅ What user HEARS (sounds around them)
- ✅ What user FEELS (physical sensations, emotions)
- ✅ What user SMELLS (scents in the air)
- ✅ What user TASTES (if relevant)

**What NOT to Describe:**
- ❌ What's happening elsewhere
- ❌ Other characters' thoughts
- ❌ Future actions
- ❌ Multiple completed steps
- ❌ God-view narration

**Structure:**
1. Complete the FIRST step (if any)
2. Describe immediate sensory experience
3. Pause at natural boundary
4. End with wondering what to do next

**Length:** 2-4 sentences

## Testing Examples

### Example 1: Sweeping Intent

**Input:** "I finish breakfast and get to the garage"

**Expected Output:**
```
💭 INNER VOICE
Last time you left without brushing your teeth you scared people. 
Imagine leaving without even getting dressed.

👁️  EXPERIENCE
You finish your breakfast, feel satiated after all that cereal, milk 
and sugar like a happy kid before going to school. On your way to 
getting ready to leave your place to get to the garage, now you're 
wondering what to do next to get prepared before leaving.

What do you do?
```

### Example 2: Atomic Intent

**Input:** "I open the door in front of me"

**Expected Output:**
```
👁️  EXPERIENCE
You extend your arm and feel as your hand grasps the coldness of 
the metal doorknob. As it turns, the door gives way to the light 
of the room ahead, slowly presenting the silhouette of an older 
man you've never seen before. A man with a scar across his face, 
reeking of beer, staring at you.

What do you do?
```

### Example 3: Sweeping Intent (Getting Ready)

**Input:** "I get ready to leave"

**Expected Output:**
```
💭 INNER VOICE
Keys, wallet, phone. The holy trinity of not being stranded.

👁️  EXPERIENCE
You stand up from the table, feeling the need to prepare for 
departure. Your eyes scan the apartment, taking inventory of 
what needs to be done before you can step out that door. The 
question now is where to start.

What do you do?
```

## Benefits

1. **No Time Skips:** System pauses at natural boundaries
2. **User Agency:** Never steals actions from user
3. **Inner Voice:** Adds personality and context
4. **Immersive:** Focus on sensory experience
5. **Self-Teaching:** System learns not to narrate through time
6. **Diegetic:** Everything happens within the world's logic

## Critical Rules

1. **NEVER complete multiple steps without user confirmation**
2. **ALWAYS pause at diegetic boundaries**
3. **ONLY describe what user can perceive**
4. **NO God-view narration**
5. **NO time skips**
6. **WAIT for user decision at each boundary**

This system ensures the simulation feels like living moment-to-moment, not watching a movie of your life.
