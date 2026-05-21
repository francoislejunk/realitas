# Enhanced Narrative Loop - Integration Guide

## Quick Start

### 1. Import the Enhanced Loop

```python
from llm_agents.enhanced_narrative_loop import EnhancedNarrativeLoop
from goal_task_system import GoalTaskManager
```

### 2. Initialize in Main

```python
# In main.py, after creating conductor/narrator/etc.

# Create goal/task manager for the user actor
goal_task_manager = GoalTaskManager()

# Add initial goals (from character creation)
goal_task_manager.add_goal(
    description="Pay off racing debts",
    importance=GoalImportance.MAJOR
)

# Create enhanced narrative loop
enhanced_loop = EnhancedNarrativeLoop(
    llm_client=client,  # Your OpenRouter client
    goal_task_manager=goal_task_manager
)
```

### 3. Process Turns

```python
# In your main game loop, after user input

# Build turn data
turn_data = {
    'user_input': user_input,
    'scene_description': scene_description,
    'interpretation_data': interpretation_result,  # From InterpreterAgent
    'narrative_response': last_narrative,  # Previous turn's narrative
    'success_calculation': success_data  # If applicable
}

# Process through enhanced loop
framing = enhanced_loop.process_turn(
    turn_data=turn_data,
    scene_description=scene_description,
    time_context=time_context,
    available_npcs=available_npcs
)

# Use framing in narrator
narrative = narrator.generate_exploration_action_result_narrative(
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    success_total=success_total,
    time_context=time_context,
    framing_guidance=framing  # ← Pass enhanced framing
)
```

### 4. Update Narrator to Use Enhanced Framing

The narrator should check for enhanced framing and use it:

```python
# In narrator_agent.py

def generate_exploration_action_result_narrative(
    self,
    user_input: str,
    actor: UserActor,
    scene_description: str,
    success_total: int,
    time_context: Optional[Dict[str, Any]] = None,
    framing_guidance: Optional[Dict[str, Any]] = None,
) -> str:
    # Extract enhanced framing if available
    mode = framing_guidance.get('mode', 'roam') if framing_guidance else 'roam'
    tone = framing_guidance.get('tone', 'calm') if framing_guidance else 'calm'
    user_intent = framing_guidance.get('user_intent', {}) if framing_guidance else {}
    context = framing_guidance.get('context', {}) if framing_guidance else {}
    narrative_guidance = framing_guidance.get('narrative_guidance', '') if framing_guidance else ''
    diegetic_cues = framing_guidance.get('diegetic_cues', []) if framing_guidance else []
    
    # Build enhanced prompt
    prompt = f"""
You are a master storyteller crafting an exploration action RESULT in a modern 1980s setting.

**Narrative Guidance:**
{narrative_guidance}

**User Intent:**
- Primary want: {user_intent.get('primary_want', 'Unknown')}
- Confidence: {user_intent.get('confidence', 0.5):.1f}
- Is drifting: {user_intent.get('is_drifting', False)}

**Context:**
{context.get('summary', 'Unknown context')}

**Diegetic Cues:**
{chr(10).join(f'- {cue}' for cue in diegetic_cues)}

**Character:** {actor.sheet.name} ({actor.sheet.occupation})
**Action:** {user_input}
**Outcome:** {get_success_level_narration(success_total)}

Write a concise, immersive paragraph in SECOND PERSON using "you".
- Length: 2–3 sentences, about 40–60 words total
- The FIRST sentence must explicitly reference the user's action
- Focus ONLY on what happens as a direct result of this specific action
- Do NOT re-describe the scene or repeat environmental details already established
- Use the narrative guidance to frame your response appropriately
- Respond to user intent - don't push them toward goals they haven't shown

Respond with ONLY the narrative.
"""
    
    # Call LLM with enhanced prompt
    # ... rest of implementation
```

---

## Display Mode (Optional Debug)

You can optionally display the current mode for debugging:

```python
# After processing turn
if DEBUG_MODE:
    state = enhanced_loop.get_current_state()
    print(f"🔀 Mode: {state['mode'].upper()} (Tone: {state['tone']})")
    if state['user_intent']['primary_want']:
        print(f"🎯 Intent: {state['user_intent']['primary_want']}")
```

**Example output:**
```
🔀 Mode: ROAM (Tone: calm)
```

---

## Task Updates

The enhanced loop automatically tracks tasks based on user actions. You can access them:

```python
# Get current task
current_task = goal_task_manager.current_task
if current_task:
    print(f"→ Current task: {current_task.description}")

# Get all active tasks
active_tasks = goal_task_manager.get_active_tasks()
for task in active_tasks:
    print(f"  [{task.priority.value}] {task.description}")

# Get goals
for goal in goal_task_manager.goals:
    print(f"  [{goal.importance.value}] {goal.description} ({int(goal.progress * 100)}%)")
```

---

## Updating Goals

Goals should only change with significant events:

```python
# When a major event happens
if significant_event_occurred:
    # Check if goal should change
    from goal_task_system import GoalTaskInterpreter
    
    interpreter = GoalTaskInterpreter(client, model)
    assessment = interpreter.assess_goal_change(
        event_description="User found their missing sister",
        goal=goal_task_manager.goals[0],
        current_context=scene_description
    )
    
    if assessment['should_change'] and assessment['confidence'] > 0.7:
        # Update goal
        goal_task_manager.update_goal(
            goal_index=0,
            new_description=assessment['new_description'],
            new_progress=assessment['new_progress']
        )
```

---

## Context Tracking

The enhanced loop automatically tracks context. You can access it:

```python
# Get context summary
context_summary = enhanced_loop.state.context.get_summary()
print(f"📍 {context_summary}")

# Access specific context elements
location = enhanced_loop.state.context.current_location
npcs = enhanced_loop.state.context.present_npcs
opportunities = enhanced_loop.state.context.opportunities
```

---

## Migration from Old Loop

### Old System
```python
# Old narrative_loop_system.py
framing = narrative_loop.process_turn(turn_data, time_context, available_npcs)
```

### New System
```python
# New enhanced_narrative_loop.py
framing = enhanced_loop.process_turn(
    turn_data,
    scene_description,  # ← Now required
    time_context,
    available_npcs
)
```

### Key Differences

| Feature | Old Loop | Enhanced Loop |
|---------|----------|---------------|
| **Intent** | Inferred from signals | Explicitly interpreted |
| **Context** | Limited | Full spatial/temporal/social |
| **Tasks** | Not tracked | Automatically tracked |
| **Goals** | Not tracked | Life-defining, resistant |
| **Push** | Meander tolerance | NO PUSH |
| **Momentum** | Signal-based | Diegetic reality-based |

---

## Testing

### Test 1: Drifting Behavior
```python
# User types vague actions
user_input = "I look around"

# Expected:
# - Mode: ROAM
# - Intent: is_drifting=True, confidence<0.4
# - Narrative: Describes what they see, no push
```

### Test 2: Clear Intent
```python
# User types specific action
user_input = "I need to find tools to fix my car"

# Expected:
# - Mode: SPARK (if was in ROAM)
# - Intent: primary_want="Fix car", confidence>0.7
# - Narrative: Acknowledges their interest, provides info
```

### Test 3: Natural Obstacles
```python
# Scene has natural pressure
scene_description = "The garage is closing in 30 minutes..."

# Expected:
# - Environmental pressure: 0.8
# - Tone: WARMING or HOT
# - Mode: PRESSURE (if in SPARK)
# - Narrative: Mentions deadline naturally
```

### Test 4: No Artificial Push
```python
# User drifts for multiple turns
for i in range(5):
    user_input = "I wander around"
    framing = enhanced_loop.process_turn(...)

# Expected:
# - Mode stays ROAM
# - NO automatic SPARK mode
# - NO "you should do something" messages
# - Just describes what they find each time
```

---

## Troubleshooting

### Issue: Mode not transitioning
**Check:**
- Is user intent confidence high enough? (≥0.6 for SPARK)
- Is environmental/social pressure high enough? (≥0.7 for PRESSURE)
- Are unresolved threads cleared? (for OUTCOME)

### Issue: Too much push
**Check:**
- Is narrative guidance being followed?
- Is narrator using diegetic cues correctly?
- Are opportunities coming from context, not invented?

### Issue: Tasks not updating
**Check:**
- Is action_interpretation being passed to enhanced loop?
- Is GoalTaskManager initialized?
- Are task inference keywords matching user actions?

---

## Best Practices

1. **Always pass scene_description** - Context tracking needs it
2. **Include action_interpretation** - Avoids duplicate LLM calls
3. **Use framing in narrator** - Don't ignore the guidance
4. **Don't override mode** - Let the system observe naturally
5. **Trust the no-push design** - Resist adding artificial prompts
6. **Update goals conservatively** - Only with major events
7. **Let tasks update automatically** - Rule-based inference works

---

## Summary

The enhanced narrative loop provides:
- ✅ User intent interpretation (what they WANT)
- ✅ Full context awareness (what IS)
- ✅ Task/Goal distinction (immediate vs life-defining)
- ✅ No push (reality responds, doesn't push)
- ✅ Diegetic momentum (fiction-based, not arbitrary)
- ✅ Invisible scaffolding (structure never shown)
- ✅ Conflict-optional (Kishōtenketsu support)

**Integration is simple: Initialize, process turns, use framing.**

The system observes and responds. It never pushes.
