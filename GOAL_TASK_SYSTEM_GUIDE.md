# Goal and Task System Guide

## Overview

The Goal/Task system provides a hierarchical structure for character motivation and immediate priorities:

- **GOALS**: Long-term, life-defining objectives that require substantial events to change
- **TASKS**: Short-term, immediate needs that update dynamically based on user actions

## Key Concepts

### Goals

Goals represent the character's core motivations and life direction. They are:

- **Persistent**: Resist change and require significant narrative events to modify
- **Progress-tracked**: Have a 0-100% completion metric
- **Hierarchical**: Can have sub-goals that break down the main objective
- **Importance-weighted**: Categorized by how resistant they are to change

#### Goal Importance Levels

1. **LIFE_DEFINING** (Highest resistance to change)
   - Core identity and purpose
   - Examples: "Find my kidnapped sister", "Avenge my family's death", "Protect my homeland"
   - Only changes with extreme circumstances:
     - Goal is definitively achieved
     - Goal becomes permanently impossible
     - Character experiences life-altering trauma that fundamentally changes their identity
   
2. **MAJOR** (High resistance to change)
   - Significant life objectives
   - Examples: "Build a successful business", "Become a master swordsman", "Earn redemption"
   - Changes when:
     - Goal is achieved
     - Goal becomes clearly impossible
     - Character has strong reason to abandon (but not lightly)

3. **MODERATE** (Moderate resistance to change)
   - Important but flexible objectives
   - Examples: "Learn a new skill", "Make new friends", "Explore the city"
   - Changes when:
     - Goal is achieved
     - Goal becomes irrelevant to current situation
     - Character's priorities shift meaningfully

### Tasks

Tasks represent immediate priorities and everyday needs. They are:

- **Dynamic**: Change frequently based on user actions and context
- **Categorized**: Organized by type (survival, goal-related, social, etc.)
- **Prioritized**: Ranked by urgency (critical, high, moderate, low)
- **Completable**: Can be marked as done and removed from the list

#### Task Categories

- **SURVIVAL**: Food, water, sleep, shelter, immediate safety
- **GOAL_RELATED**: Actions that directly advance a long-term goal
- **SOCIAL**: Relationship maintenance, social obligations, conversations
- **EXPLORATION**: Investigation, discovery, learning about the world
- **MAINTENANCE**: Equipment care, health management, resource management
- **REACTIVE**: Immediate responses to events (e.g., "Respond to the alarm")

#### Task Priorities

- **CRITICAL**: Survival needs, immediate danger (must be addressed now)
- **HIGH**: Important but not life-threatening (should be addressed soon)
- **MODERATE**: Should be addressed when convenient
- **LOW**: Can be deferred indefinitely

## How It Works

### 1. Goal Creation

Goals are typically created during character creation or major story events:

```python
# Add a life-defining goal
actor.add_goal(
    description="Find my missing sister Emily",
    importance=GoalImportance.LIFE_DEFINING,
    sub_goals=["Track down leads", "Gather evidence", "Locate her"]
)
```

### 2. Dynamic Task Interpretation

After each user action, the Interpreter Agent analyzes the action to:

1. **Infer Intent**: What is the user trying to accomplish?
2. **Update Current Task**: Should the focus shift based on this action?
3. **Add New Tasks**: Are there new priorities that emerged?
4. **Complete Tasks**: Did this action accomplish any existing tasks?

Example flow:

```
User Action: "I search the abandoned warehouse for clues"

Interpreter Analysis:
- Inferred Intent: "Investigate the warehouse for evidence related to sister's disappearance"
- Current Task Update: → "Search the warehouse for clues"
- Category: GOAL_RELATED (advances the "Find my sister" goal)
- Priority: HIGH
```

### 3. Task Updates

Tasks update dynamically:

```
User Action: "I'm hungry, I look for food"

Interpreter Analysis:
- Inferred Intent: "Address hunger by finding food"
- Current Task Update: → "Find food"
- Category: SURVIVAL
- Priority: CRITICAL (if very hungry) or HIGH (if moderately hungry)
```

### 4. Goal Change Assessment

Goals only change when significant events occur:

```
Event: "You find your sister's body in the warehouse"

Goal Assessment:
- Current Goal: "Find my missing sister Emily" [LIFE_DEFINING]
- Should Change: YES
- Change Type: MODIFY
- New Goal: "Find and bring to justice those who killed Emily"
- Justification: "The original goal is no longer achievable, but the core 
  motivation (protecting/honoring sister) transforms into a new goal"
```

## Integration with Simulation

### In the Interpreter Agent

The Interpreter Agent now includes task interpretation:

```python
# After interpreting a user action
interpreter.update_actor_tasks(user_action, actor)
```

This automatically:
1. Analyzes the action for intent
2. Updates the current task if needed
3. Adds new tasks that emerge
4. Completes tasks that were accomplished

### In the Actor Sheet

The actor sheet displays:
- Primary goal with progress percentage
- Current active task
- All goals and tasks in detailed view

```python
# Access goal/task information
current_task = actor.get_current_task_description()
goals_summary = actor.get_goals_summary()
tasks_summary = actor.get_tasks_summary()
```

## Examples

### Example 1: Detective Story

**Character**: Detective Sarah Chen

**Life-Defining Goal**: "Rescue my kidnapped sister Emily from the trafficking ring"
- Progress: 35%
- Sub-goals: Track kidnappers, Gather evidence, Find Emily's location

**Current Task**: "Interview the witness at the docks" [CRITICAL, GOAL_RELATED]

**Other Active Tasks**:
- "Find food and rest" [HIGH, SURVIVAL]
- "Repair damaged equipment" [LOW, MAINTENANCE]

**User Actions and Task Updates**:

1. User: "I go to the docks to meet the witness"
   - Current Task: → "Interview the witness at the docks" (no change, already current)
   
2. User: "I ask the witness about the shipping manifests"
   - Current Task: → "Investigate shipping manifests" (refined focus)
   - New Task Added: "Obtain copies of shipping records" [HIGH, GOAL_RELATED]
   
3. User: "I'm exhausted, I need to eat and sleep"
   - Current Task: → "Find food and rest" (priority shift to survival)
   - Task Completed: "Interview the witness at the docks" (accomplished)

### Example 2: Survival Scenario

**Character**: John Smith, Survivor

**Major Goal**: "Survive the apocalypse"
- Progress: 20%

**Current Task**: "Find clean water" [CRITICAL, SURVIVAL]

**User Actions**:

1. User: "I search the abandoned houses for supplies"
   - Current Task: → "Search for supplies" (broader than just water)
   - Category: SURVIVAL
   
2. User: "I find a water purification tablet"
   - Task Completed: "Find clean water" (accomplished)
   - Current Task: → "Find shelter for the night" (next priority)

### Example 3: Goal Change Event

**Character**: Warrior seeking revenge

**Original Goal**: "Find the man who killed my father" [LIFE_DEFINING]

**Event**: "You discover the man who killed your father was actually protecting you from your father's dark cult"

**Goal Assessment**:
- Should Change: YES (major revelation)
- Change Type: ABANDON
- New Goal: "Escape from the cult that my father led" [LIFE_DEFINING]
- Justification: "The original goal is no longer valid given the truth. The core motivation (justice/protection) redirects to a new threat."

## Best Practices

### For Goal Design

1. **Make life-defining goals personal and emotional**
   - Good: "Save my daughter from the disease"
   - Bad: "Complete the main quest"

2. **Connect goals to character identity**
   - Goals should reflect who the character is at their core
   - Life-defining goals should feel like "this is what I live for"

3. **Use sub-goals to track progress**
   - Break down complex goals into achievable milestones
   - Each sub-goal completed = progress toward main goal

### For Task Management

1. **Let tasks emerge naturally from actions**
   - Don't pre-define all tasks
   - Let the Interpreter infer tasks from user behavior

2. **Use appropriate priorities**
   - CRITICAL: Life or death, immediate danger
   - HIGH: Important but can wait a few turns
   - MODERATE: Should do eventually
   - LOW: Nice to have

3. **Complete tasks when accomplished**
   - Don't let task lists grow indefinitely
   - Mark tasks complete to show progress

### For Goal Changes

1. **Be conservative with life-defining goals**
   - These should almost never change
   - Only extreme events warrant changes

2. **Require narrative justification**
   - Goal changes should make sense in the story
   - Document why the change is happening

3. **Transform rather than abandon when possible**
   - "Find my sister" → "Avenge my sister" (transforms)
   - Better than just abandoning the goal entirely

## API Reference

### ActorSheet Methods

```python
# Goal Management
actor.add_goal(description, importance, sub_goals=None)
actor.update_goal_progress(goal_index, progress)
actor.get_goals_summary()

# Task Management
actor.add_task(description, priority, category, related_goal=None)
actor.set_current_task(task)
actor.complete_task(task)
actor.get_current_task_description()
actor.get_tasks_summary()

# Goal/Task Manager Access
actor.goal_task_manager.goals  # List of Goal objects
actor.goal_task_manager.tasks  # List of Task objects
actor.goal_task_manager.current_task  # Current Task object
```

### Interpreter Agent Methods

```python
# Dynamic task interpretation
interpreter.update_actor_tasks(user_action, actor)

# Goal change assessment (for major events)
interpreter.goal_task_interpreter.assess_goal_change(
    event_description, goal, current_context
)
```

## Testing

Run the test suite to see the system in action:

```bash
python test_goal_task_system.py
```

This demonstrates:
- Creating goals with different importance levels
- Managing tasks with priorities and categories
- Completing tasks and tracking progress
- Multiple goals and task organization

## Future Enhancements

Potential additions to the system:

1. **Goal Dependencies**: Goals that unlock other goals
2. **Task Deadlines**: Time-sensitive tasks
3. **Task Chains**: Tasks that lead to other tasks
4. **Goal Conflicts**: Competing goals that create tension
5. **NPC Goals**: NPCs with their own goal/task systems
6. **Goal Sharing**: Multiple characters working toward the same goal
