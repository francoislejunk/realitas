# Internal Voice & Storyteller System Integration Guide

## Overview

This document describes the new Internal Voice and Storyteller systems implemented for Realitas Neo.

## New Systems Created

### 1. Reputation System (`reputation_system.py`)

**Purpose:** Track titles and reputation for all actors (UA, NUA, MNUA, INUA).

**Key Features:**
- Titles earned through notable actions
- Visible to all actors (public reputation)
- Affects NUA behavior and initial sympathy
- Categories: heroic, villainous, professional, social, notorious, respected, mysterious, local
- Rarity levels: common, uncommon, rare, legendary

**Usage:**
```python
from reputation_system import get_reputation_system, check_for_title, display_title_earned

# Check if action earns a title
title = check_for_title(
    actor_name="Marcus",
    action_description="Saved a child from a burning building",
    action_outcome="The child was rescued safely",
    location="Downtown Apartment",
    witnesses=["Firefighter", "Mother"],
    context="House fire emergency"
)

if title:
    display_title_earned(title, "Marcus")
```

### 2. Personality & Mood System (`personality_mood_system.py`)

**Purpose:** Provide OCEAN (Big Five), MBTI, and dynamic mood tracking.

**Key Features:**
- **OCEAN Profile:** Openness, Conscientiousness, Extraversion, Agreeableness, Neuroticism (1-10 scale)
- **MBTI Type:** 16 personality types with cognitive style descriptions
- **Mood System:** Dynamic emotional state that changes based on context
  - Primary mood (calm, anxious, excited, angry, sad, fearful, happy, focused, confused, suspicious)
  - Intensity (subtle, moderate, strong, overwhelming)
  - Stress, energy, confidence levels

**Usage:**
```python
from personality_mood_system import PersonalityGenerator, CompletePersonalityProfile

# Generate personality for new actor
generator = PersonalityGenerator()
profile = generator.generate_personality(
    actor_name="Alex",
    occupation="Private Investigator",
    backstory="Former cop turned PI after corruption scandal",
    existing_traits={"internal": "Cynical", "external": "Professional"}
)

# Set on actor sheet
actor.sheet.set_personality_profile(profile)

# Update mood based on context
actor.sheet.update_mood(scene_description, recent_events)

# Get personality prompt for internal voice
prompt_section = actor.sheet.get_personality_prompt_section()
```

### 3. Internal Voice Interpreter Agent (`agents/internal_voice_interpreter_agent.py`)

**Purpose:** Determine what type of internal voice response is most relevant.

**Four Functions:**
1. **INFORMATION** - Answer questions (logic or conceptual)
2. **SOLUTION** - Suggest actions for predicaments
3. **MEMORY** - Recall/create memories
4. **COMMENT** - Personality-driven flavor (default)

**Usage:**
```python
from agents.internal_voice_interpreter_agent import get_voice_interpreter, interpret_for_voice

interpreter = get_voice_interpreter()
interpretation = interpreter.interpret_situation(
    scene_description="You're in a dark alley",
    user_action="Who is my best friend?",
    action_outcome="",
    actor_state={"stamina": 4, "spirit": 3, "mood": "anxious"},
    personality_context=personality_prompt,
    current_goal="Find the truth",
    is_inquiry=True
)

# Result: interpretation.primary_function = INFORMATION
# interpretation.question_type = LOGIC
```

### 4. Internal Voice Creator Agent (`agents/internal_voice_creator_agent.py`)

**Purpose:** Generate the actual internal voice content.

**Key Features:**
- Generates content for all four functions
- Anti-repetition system (tracks used phrases)
- Memory creation/recall with 10+ categories
- Personality-driven output
- Urgency matching (calm, normal, urgent, frantic)

**Memory Categories:**
- family, job, friends, trauma, achievement, relationship
- location, childhood, education, loss, secret, regret

**Usage:**
```python
from agents.internal_voice_creator_agent import get_voice_creator, display_internal_voice

creator = get_voice_creator()
voice_result = creator.generate_voice(
    interpretation=interpretation,
    scene_description=scene_description,
    user_action=user_action,
    action_outcome=action_outcome,
    personality_prompt=personality_prompt,
    actor_name="Alex",
    current_goal="Find the truth"
)

display_internal_voice(voice_result)
# Output: 💡 Jake. We've been friends since high school. He's the only one I trust.
```

### 5. Storyteller Agent (`agents/storyteller_agent.py`)

**Purpose:** Silent orchestrator that generates narrative sparks on location changes.

**Spark Types:**
1. **MOMENTUM** - Goal/task opportunities (radio announcements, signs, overheard conversations)
2. **EXCHANGE** - Encounter opportunities with clear outcomes (NUA interactions, confrontations)
3. **CALLBACK** - Long-term effects of past actions (rare)

**Key Features:**
- Triggers on location changes
- Generates 0-3 sparks per location
- Maintains light/heavy balance (1:1 ratio)
- Prioritizes NUA recurrence over creation
- Tracks past actions for callbacks
- **Exchange sparks have clear reward/punishment outcomes**

**Exchange Spark Outcomes:**
Every exchange spark includes explicit potential outcomes:
- **Success Reward** - What UA gains on success (item, money, information, favor)
- **Success Relationship** - How sympathy changes on success (+1 to +3 sympathy)
- **Failure Punishment** - What UA loses on failure (injury, money, reputation)
- **Failure Relationship** - How sympathy changes on failure (-1 to -3 sympathy)
- **Ignore Consequence** - What happens if UA doesn't engage (missed opportunity, escalation)

**Usage:**
```python
from agents.storyteller_agent import get_storyteller, display_sparks, display_exchange_outcomes

storyteller = get_storyteller()

# On location change
sparks = storyteller.on_location_change(
    new_location="Downtown Supermarket",
    location_description="A busy supermarket...",
    actor_goal="Find out who killed my brother",
    actor_task="Talk to witnesses",
    available_nuas=[{"name": "Store Manager", "occupation": "Manager"}],
    recent_narrative=["You left your apartment", "You took the bus"]
)

# Display sparks (just the trigger, not metadata)
display_sparks(sparks)

# Display sparks with outcomes visible (for debugging or explicit display)
display_sparks(sparks, show_outcomes=True)

# Or display outcomes for a specific exchange spark
for spark in sparks:
    if spark.spark_type == SparkType.EXCHANGE:
        display_exchange_outcomes(spark)
        # Shows:
        # ┌─────────────────────────────────────────────────────────┐
        # │ 💫 POTENTIAL OUTCOMES (LIGHT)                          │
        # ├─────────────────────────────────────────────────────────┤
        # │ ✓ SUCCESS:
        # │   💰 Gains $20 and vendor's gratitude
        # │   💚 +1 sympathy, potential discount later
        # │ ✗ FAILURE:
        # │   💸 Wastes time, vendor annoyed
        # │   💔 -1 sympathy
        # │ ○ IGNORE:
        # │   🚶 Vendor struggles alone, no consequence
        # └─────────────────────────────────────────────────────────┘

# Record action for potential callback
storyteller.record_action(
    action_description="Killed a man in front of his son",
    outcome="The man died, the son escaped",
    location="Warehouse District",
    involved_actors=["Victim", "Son"],
    severity="extreme"  # High callback potential
)
```

## Integration Points in Main Loop

### 1. Initialization

```python
# In redesigned_main.py initialization section

from personality_mood_system import PersonalityGenerator
from reputation_system import get_reputation_system
from agents.internal_voice_interpreter_agent import get_voice_interpreter
from agents.internal_voice_creator_agent import get_voice_creator
from agents.storyteller_agent import get_storyteller
from agents.narrator_agent import NarratorAgent

# CRITICAL: Disable NarratorAgent's internal voice to prevent overlap
# The new InternalVoiceCreatorAgent will handle all internal voice generation
NarratorAgent.disable_internal_voice()

# Initialize systems
personality_generator = PersonalityGenerator()
reputation_system = get_reputation_system(storage_dir)
voice_interpreter = get_voice_interpreter()
voice_creator = get_voice_creator(storage_dir)
storyteller = get_storyteller(storage_dir)

# Generate personality for UA
ua_personality = personality_generator.generate_personality(
    actor_name=user_actor.sheet.name,
    occupation=user_actor.sheet.occupation,
    backstory=backstory_text,
    existing_traits=user_actor.sheet.personality_traits
)
user_actor.sheet.set_personality_profile(ua_personality)

# Create initial memories
# NOTE: This is now AUTOMATICALLY called in vessel_selection_system.py
# when a UA is selected. No manual call needed.
# The VesselSelectionSystem._create_initial_memories() method handles this.
voice_creator.create_initial_memories(
    actor_name=user_actor.sheet.name,
    personality_prompt=user_actor.sheet.get_personality_prompt_section(),
    backstory=backstory_text
)
```

**AUTOMATIC INTEGRATION:** As of the latest update, `create_initial_memories()` is automatically
called when a vessel is selected in `vessel_selection_system.py`. This generates 24 memories
(2 per category across 12 categories) based on the actor's personality, occupation, and backstory.

### 2. On Location Change

```python
# When UA enters a new location
if location_changed:
    sparks = storyteller.on_location_change(
        new_location=new_location_name,
        location_description=scene_description,
        actor_goal=user_actor.sheet.goals[0] if user_actor.sheet.goals else "",
        actor_task=user_actor.sheet.get_current_task_description(),
        available_nuas=[nua.to_dict() for nua in available_npcs],
        recent_narrative=recent_events
    )
    
    # Display sparks naturally in narrative
    for spark in sparks:
        print(f"\n{Color.STATUS}{spark.trigger_description}{Color.RESET}")
```

### 3. Internal Voice Generation (Every Turn)

```python
# After action processing, generate internal voice

# Update mood based on context
user_actor.sheet.update_mood(scene_description, recent_events)

# Interpret what voice function to use
interpretation = voice_interpreter.interpret_situation(
    scene_description=scene_description,
    user_action=user_input,
    action_outcome=narrative_result,
    actor_state=user_actor.sheet.get_current_mood(),
    personality_context=user_actor.sheet.get_personality_prompt_section(),
    current_goal=user_actor.sheet.goals[0] if user_actor.sheet.goals else "",
    current_task=user_actor.sheet.get_current_task_description(),
    is_inquiry=is_inquiry
)

# Generate voice content
voice_result = voice_creator.generate_voice(
    interpretation=interpretation,
    scene_description=scene_description,
    user_action=user_input,
    action_outcome=narrative_result,
    personality_prompt=user_actor.sheet.get_personality_prompt_section(),
    actor_name=user_actor.sheet.name,
    current_goal=user_actor.sheet.goals[0] if user_actor.sheet.goals else ""
)

# Display internal voice
display_internal_voice(voice_result)
```

### 4. Title/Reputation Checking

```python
# After significant actions
from reputation_system import check_for_title, display_title_earned

title = check_for_title(
    actor_name=proactor.sheet.name,
    action_description=action_description,
    action_outcome=outcome_narrative,
    location=current_location,
    witnesses=[nua.sheet.name for nua in present_nuas],
    context=scene_description
)

if title:
    display_title_earned(title, proactor.sheet.name)
    proactor.sheet.add_title(title.name)
```

### 5. Recording Actions for Callbacks

```python
# After significant actions (especially violent/impactful ones)
storyteller.record_action(
    action_description=action_description,
    outcome=outcome_narrative,
    location=current_location,
    involved_actors=[nua.sheet.name for nua in involved_nuas],
    severity=determine_severity(action_type, outcome)
)
```

## Display Integration

### Actor Sheet Display

The `display_detailed()` method in ActorSheet now includes:
- Personality profile (OCEAN, MBTI, Mood)
- Titles and reputation

Call `actor.sheet.display_personality_and_titles()` to show these sections.

## Files Created

1. `reputation_system.py` - Title and reputation tracking
2. `personality_mood_system.py` - OCEAN, MBTI, and mood system
3. `agents/internal_voice_interpreter_agent.py` - Voice function interpreter
4. `agents/internal_voice_creator_agent.py` - Voice content generator
5. `agents/storyteller_agent.py` - Spark system and silent orchestrator

## Files Modified

1. `actor_sheet.py` - Added personality profile, titles, and related methods

## Key Design Principles

1. **Internal Voice Always Present** - Never silent, always reflects personality
2. **First Person PLURAL** - Always use "we", "our", "us" - NEVER "I", "my", "me"
3. **Personality Always Evident** - OCEAN, MBTI, and mood affect all voice output
4. **No Repetition** - Track used phrases and functions to avoid repetition
5. **Silent Orchestration** - Storyteller works invisibly, only shows triggers
6. **User Agency** - User action trumps all sparks and suggestions
7. **Balance** - Light and heavy situations maintain 1:1 ratio
8. **Recurrence Over Creation** - Prioritize bringing back known NUAs
9. **Diegetic Delivery** - All information delivered through narrative, not UI
10. **No Overlap** - Disable NarratorAgent internal voice when using InternalVoiceCreatorAgent

## Disabling NarratorAgent Internal Voice

To prevent overlap between the old NarratorAgent internal voice and the new InternalVoiceCreatorAgent:

```python
from agents.narrator_agent import NarratorAgent

# Disable the old system
NarratorAgent.disable_internal_voice()

# To re-enable if needed
NarratorAgent.enable_internal_voice()
```

When disabled, `generate_inquiry_internal_voice()` returns `None` instead of generating content.

## Integration in redesigned_main.py

The new systems are fully integrated into the main simulation loop:

### Initialization (automatic)
```python
# Called during simulation startup after World Persistence System
# RAG system is passed for worldbuilding context
rag_system = conductor.decider_agent.rag_system
init_new_voice_systems(storage_dir, rag_system=rag_system)
```

This initializes:
- `InternalVoiceInterpreterAgent` - Determines voice type needed
- `InternalVoiceCreatorAgent` - Generates voice content (uses RAG for setting-appropriate memories)
- `StorytellerAgent` - Generates narrative sparks (uses RAG for worldbuilding context)
- `ReputationSystem` - Tracks titles and reputation (uses RAG for setting-appropriate titles)
- Disables legacy NarratorAgent internal voice

### RAG Integration

All new systems are timeline-agnostic and rely on the RAG worldbuilding system:

- **InternalVoiceCreatorAgent**: Uses RAG when creating initial memories to ensure they fit the setting
- **StorytellerAgent**: Receives RAG context for location-appropriate sparks
- **ReputationSystem**: Uses RAG when generating titles to match the setting's culture

### Helper Functions Available

```python
# Generate internal voice with retry handling
voice_result = generate_new_internal_voice(
    actor, scene_description, user_action, action_outcome,
    current_goal, current_task, available_memories, max_retries=3
)

# Check and award reputation titles
title = check_and_award_title(
    actor_name, action_description, action_outcome,
    location, witnesses, context, max_retries=2
)

# Get storyteller sparks for location
sparks = get_storyteller_sparks(
    location, location_description, available_nuas,
    recent_narrative, actor_goal, actor_task, rag_context, max_retries=2
)

# Get reputation context for NUA perception
context = get_reputation_context(observer_name, target_name)

# Get sympathy modifier from reputation
modifier = get_reputation_sympathy_modifier(observer_name, target_name)
```

### Automatic Triggers

1. **Location Change** → Storyteller sparks generated
2. **Significant Exchange** → Reputation title check for both actors
3. **Vessel Selection** → Initial memories created (24 memories)

### Retry Handling

All new systems use exponential backoff retry:
- Internal voice: 3 retries with 0.5s, 1s, 1.5s delays
- Title checks: 2 retries with 0.5s delay
- Storyteller sparks: 2 retries with 0.5s delay

Failures are graceful - the simulation continues without the feature.
