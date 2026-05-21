# Internal Voice Enhancement: Solution-Oriented Thinking

## Overview

Enhanced the internal voice system to be more like real internal dialogue - not just commenting on situations, but actively suggesting solutions, offering reminders, and sometimes being wrong.

## What Changed

### 1. Context-Aware Thinking

The internal voice now has access to:
- **Current State**: Stamina, Spirit, Supply levels
- **Current Task**: Active goals from goal system
- **Inventory**: Top 3 items carried
- **Relationships**: Key sympathy values with NPCs
- **Personality**: Internal/external traits

### 2. New Types of Internal Voice

**Before (Passive Observation):**
- ✓ "We've seen places like this before."
- ✓ "Something doesn't sit right with us."
- ✓ "Reminds us of that ice cream store."

**Now (Active Problem-Solving):**
- ✓ "Maybe we should check the back entrance. Worth a shot."
- ✓ "We need to eat soon. Getting light-headed."
- ✓ "Should probably avoid that guy. Looks like he's had a rough day."
- ✓ "This'll be quick. In and out, no problem." (overconfident - might be wrong!)
- ✓ "Pretty sure Mike mentioned something about this place. Or was it Tony?" (misremembering)

### 3. Eight Types of Internal Voice

1. **Observations** - Noticing environmental details
2. **Memories** - Recalling relevant past experiences
3. **Intuitions** - Gut feelings about situations
4. **Solutions** - Suggesting possible approaches
5. **Reminders** - Noting needs or tasks
6. **Warnings** - Cautioning about dangers
7. **Wrong Guesses** - Overconfident or incorrect assessments
8. **Misremembering** - Uncertain or confused recollections

## Implementation Details

### Code Changes

**File: `agents/narrator_agent.py`**

**Lines 2619-2638:** Added context extraction
```python
# Extract current state for solution-oriented thinking
current_stamina = ua_actor.sheet.statuses.get("stamina", 5).current_value
current_spirit = ua_actor.sheet.statuses.get("spirit", 5).current_value
current_supply = ua_actor.sheet.statuses.get("supply", 5).current_value

# Get current task/goal if available
current_task = ""
if hasattr(ua_actor.sheet, 'goal_task_manager'):
    current_task = ua_actor.sheet.goal_task_manager.current_task.description

# Get top inventory items
inventory_items = [item.name for item in ua_actor.sheet.inventory[:3]]

# Get key relationships (sympathy)
relationships = []
for npc_name, sympathy_status in list(ua_actor.sheet.sympathy.items())[:3]:
    relationships.append(f"{npc_name} ({sympathy_status.current_value:+d})")
```

**Lines 2647-2651:** Added state context to prompt
```python
**CURRENT STATE:**
- Stamina: {current_stamina}/10 | Spirit: {current_spirit}/10 | Supply: {current_supply}/10
- Current Task: {current_task if current_task else "None"}
- Key Items: {', '.join(inventory_items) if inventory_items else "None"}
- Relationships: {', '.join(relationships) if relationships else "None"}
```

**Lines 2675-2689:** Added solution-oriented instructions
```python
- **NEW: Can suggest solutions, reminders, or next steps based on situation**
- **NEW: Can be wrong sometimes - just like real internal dialogue**

**TYPES OF INTERNAL VOICE:**
1. **Observations:** "We've seen places like this before."
2. **Memories:** "Reminds us of that ice cream store Dad used to take us to."
3. **Intuitions:** "Something about this doesn't sit right with us."
4. **Solutions:** "Maybe we should check the back door. Or was it the side entrance?"
5. **Reminders:** "We need to remember to grab supplies before heading out."
6. **Warnings:** "We should probably avoid that guy. He looks like trouble."
7. **Wrong Guesses:** "This should be easy. What could go wrong?" (when it's actually risky)
8. **Misremembering:** "Pretty sure the shop closes at 8. Or was it 9?"
```

**Line 2719:** Updated system message
```python
"content": "You are generating the internal voice of a character. Use 2nd person plural ('we', 'us', 'our'). Keep it brief and subtle - just 1-2 sentences. Make it feel like the character's own thoughts. The internal voice can suggest solutions, offer reminders, or make guesses - and sometimes be wrong, just like real internal dialogue."
```

### Documentation Updates

**File: `INTERNAL_VOICE_SYSTEM.md`**

- Added "Solution-Oriented" philosophy section
- Added 8 new example internal voices showing solutions/reminders
- Added "Types of Internal Voice" breakdown
- Updated parameters section with context extraction details
- Marked implemented features in future enhancements

## Example Scenarios

### Scenario 1: Low Supply
**Context:** Supply at 2/10, no food in inventory
**Internal Voice:** "We need to eat soon. Getting light-headed."

### Scenario 2: Approaching Danger
**Context:** Entering dark alley, low stamina
**Internal Voice:** "Should probably avoid that guy. Looks like he's had a rough day."

### Scenario 3: Problem-Solving
**Context:** Locked door, wrench in inventory
**Internal Voice:** "Maybe we should check the back entrance. Worth a shot."

### Scenario 4: Overconfident (Wrong)
**Context:** Approaching difficult situation, high spirit
**Internal Voice:** "This'll be quick. In and out, no problem."
**Reality:** Actually very difficult, character underestimated

### Scenario 5: Misremembering
**Context:** Trying to recall NPC conversation
**Internal Voice:** "Pretty sure Mike mentioned something about this place. Or was it Tony?"

### Scenario 6: Task Reminder
**Context:** Current task is "Find food", passing restaurant
**Internal Voice:** "We should probably grab something to eat while we're here."

### Scenario 7: Relationship Awareness
**Context:** Sympathy with Guard is -3, considering talking to them
**Internal Voice:** "Guard's not gonna be happy to see us. Maybe we should take the long way around."

### Scenario 8: Inventory Suggestion
**Context:** Locked door, lockpick in inventory
**Internal Voice:** "We've got that lockpick. Could give it a shot."

## Benefits

### 1. More Realistic Internal Dialogue
Real people don't just observe - they problem-solve, remind themselves of things, and make guesses (sometimes wrong).

### 2. Enhanced Immersion
Feels more like YOU thinking, not a narrator describing your thoughts.

### 3. Helpful Guidance
Subtly reminds players of:
- Current needs (hunger, fatigue)
- Available resources (inventory items)
- Active goals (current tasks)
- Social dynamics (relationships)

### 4. Natural Fallibility
Sometimes being wrong makes it feel MORE real:
- Overconfidence before difficult situations
- Misremembering details
- Uncertain guesses

### 5. Character Personality
Solution suggestions reflect internal personality:
- Cautious character: More warnings
- Bold character: More confident (sometimes overconfident)
- Analytical character: More strategic suggestions

## Technical Notes

### No Extra LLM Calls
- Uses existing internal voice generation
- Just enhanced prompt with more context
- Same temperature (0.7) and token limit (100)

### Graceful Degradation
- If context unavailable, falls back to basic observations
- If LLM fails, silently returns None
- Doesn't break simulation flow

### Still Subtle
- Still 1-2 sentences maximum
- Still only appears in ROAM mode
- Still disappears during social interactions
- Can still return empty if nothing noteworthy

## Future Enhancements

### Possible Additions
1. **Skill-Based Suggestions**: "We're pretty good with locks. Should be able to handle this."
2. **Memory Integration**: Reference specific past events from memory system
3. **Learning from Mistakes**: "Last time we tried this, it didn't go well. Maybe a different approach?"
4. **Contextual Item Use**: "That crowbar might come in handy here."

## Summary

The internal voice is now a more active participant in the character's thinking process - not just commenting on the situation, but trying to help solve problems, remember important things, and navigate challenges. And just like real internal dialogue, it's sometimes helpful, sometimes wrong, but always feels authentic.

**Result:** More immersive, more helpful, more realistic internal dialogue that feels like YOUR thoughts, not a narrator's observations.
