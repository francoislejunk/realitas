# Internal Voice Now Context-Aware and Targeted

## The Problem

Internal voice was giving **generic** comments that broke immersion:
```
Action: "I try to remember my best friend's name"
Output: "We've done this before, right? Why can't we just remember?"
```

This is generic and unhelpful - it doesn't use the character's:
- Current goals
- Current task
- Status levels
- Relationships
- Inventory
- Personality traits
- Recent memories

## The Solution

Internal voice now receives **full character context** to provide **specific, targeted** responses.

## Context Now Provided

### 1. Goals & Tasks
```python
current_goals = ua_actor.sheet.goals[:3]  # Top 3 goals
current_task = ua_actor.sheet.goal_task_manager.current_task.description
```

### 2. Status Levels
```python
current_stamina = 3/10
current_spirit = 2/10  # Low!
current_supply = 5/10
```

### 3. Inventory
```python
inventory_items = ["Toolkit", "Demo Tapes", "Notebook"]
```

### 4. Relationships
```python
relationships = ["Mike (+3)", "Sarah (-2)", "Alex (+1)"]
```

### 5. Personality Traits
```python
internal_personality = "Cynical and analytical"
external_personality = "Calm and composed"
```

### 6. Recent Context
```python
narrative_context = "Last 400 characters of recent events and memories"
```

## Examples: Generic vs. Targeted

### Example 1: Remembering Name

**Generic (Bad):**
```
"We've done this before, right? Why can't we just remember?"
```

**Targeted (Good):**
```
Goal: "Reconnect with old friends"
→ "Her name is Sarah. We've known her since high school. She lives 
across town now, but we still meet up every few weeks at that coffee 
shop on Main Street. We should call her about that party we're planning."
```

### Example 2: Where Am I?

**Generic (Bad):**
```
"This is our apartment. We're home."
```

**Targeted (Good):**
```
Task: "Prepare for tonight's gig"
→ "This is our apartment. We're home. The vinyl collection is ours. 
We need to grab those demo tapes for the gig tonight - they're on 
the shelf by the turntable."
```

### Example 3: Unfamiliar Location

**Generic (Bad):**
```
"We don't recognize this place."
```

**Targeted (Good):**
```
Spirit: 2/10, Goal: "Find safe place to rest"
→ "We don't recognize this place. Never been here before. We're 
exhausted - spirit is low. We need to find somewhere safe to rest 
before we collapse."
```

### Example 4: Looking Around Bar

**Generic (Bad):**
```
"This is a bar. There are people here."
```

**Targeted (Good):**
```
Relationship: Mike +3, Task: "Find information about the deal"
→ "This is Joe's Bar. Mike the bartender knows us - he might have 
heard something about that deal we're investigating. Those guys in 
the corner look suspicious though."
```

### Example 5: Examining Device

**Generic (Bad):**
```
"It's a radio."
```

**Targeted (Good):**
```
Inventory: "Toolkit", Goal: "Repair the radio"
→ "It's some kind of radio transmitter. Old Soviet design, probably 
from the 70s. We've got our toolkit - we could try repairing it. 
That's what we came here to do anyway."
```

### Example 6: Getting Downtown

**Generic (Bad):**
```
"Take the train."
```

**Targeted (Good):**
```
Task: "Meet contact at 3pm", Time: "2:45pm"
→ "The U-Bahn station is two blocks north. Line 3 runs downtown 
every 15 minutes. It's 2:45 - we need to hurry if we're going to 
make that 3pm meeting with our contact."
```

## Key Principles

### ✅ DO: Be Specific
- Reference current goals/tasks
- Mention low status levels
- Use relationships in reasoning
- Suggest using inventory items
- Connect to personality traits
- Reference recent events

### ❌ DON'T: Be Generic
- Avoid vague statements
- Don't ignore context
- Don't give generic advice
- Don't forget character situation

## Implementation

### File Modified: `agents/narrator_agent.py`

**Method: `generate_inquiry_internal_voice()`** (lines 3064-3196)

**Added Context Extraction:**
```python
# Get current goals and tasks
current_goals = ua_actor.sheet.goals[:3]
current_task = ua_actor.sheet.goal_task_manager.current_task.description

# Get current status
current_stamina = stamina_status.value
current_spirit = spirit_status.value
current_supply = supply_status.value

# Get key inventory items
inventory_items = [item.name for item in ua_actor.sheet.inventory[:3]]

# Get key relationships
relationships = [f"{npc_name} ({sympathy_status.value:+d})" 
                for npc_name, sympathy_status in ua_actor.sheet.sympathy.items()[:3]]
```

**Updated Prompt:**
```python
**CURRENT GOALS:**
- {goal_1}
- {goal_2}

**CURRENT TASK:** {current_task}

**STATUS:** Stamina: {stamina}/10 | Spirit: {spirit}/10 | Supply: {supply}/10

**KEY ITEMS:** {inventory_items}

**RELATIONSHIPS:** {relationships}

**RECENT CONTEXT:**
{narrative_context[:400]}
```

**Updated System Message:**
```
CRITICAL: Use the provided context (goals, tasks, status, relationships, 
inventory) to be SPECIFIC, not generic. Reference current goals when 
relevant, mention low status, use relationships, suggest using inventory 
items. Avoid generic comments.
```

## Result

✅ **Specific Comments** - References goals, tasks, status  
✅ **Immersive** - Feels like character's actual thoughts  
✅ **Helpful** - Provides targeted, relevant information  
✅ **Context-Aware** - Uses all available character data  
✅ **Personality-Driven** - Matches internal personality  

The internal voice now acts like a **personal assistant who knows the character's full situation**, not just a generic helper.
