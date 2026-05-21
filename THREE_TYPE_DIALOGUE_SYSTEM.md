# Three-Type Dialogue System

## Overview

The narrator now handles **three distinct exchange types** with appropriate narrative flow:

1. **Pure Action** - Physical actions without dialogue
2. **Pure Dialogue** - Conversational exchanges without physical actions
3. **Action + Dialogue** - Speaking while performing actions

## Implementation

### Detection Logic (lines 671-684)

```python
# Detect dialogue and action types
proactor_dialogue = proactor_data.get('dialogue_metadata', {})
reactor_dialogue = reactor_data.get('dialogue_metadata', {})
has_dialogue = proactor_dialogue.get('dialogue_detected', False) or reactor_dialogue.get('dialogue_detected', False)

# Determine if actions contain physical components (not just pure dialogue)
proactor_has_physical = 'dialogue_only' not in proactor_action.lower() and not proactor_dialogue.get('dialogue_only', False)
reactor_has_physical = 'dialogue_only' not in reactor_action.lower() and not reactor_dialogue.get('dialogue_only', False)

# Determine exchange type
is_pure_dialogue = has_dialogue and not (proactor_has_physical or reactor_has_physical)
is_action_with_dialogue = has_dialogue and (proactor_has_physical or reactor_has_physical)
is_pure_action = not has_dialogue
```

### Narrative Templates

The narrator now uses different templates based on exchange type:

## Type 1: Pure Action

**No dialogue detected** - Traditional combat/action narrative

### Examples:

**Hostile Action (Proactor Wins):**
```
John's punch proves insufficient against Mara's dodge as their physical endurance wavers.
```

**Friendly Action (Reactor Wins):**
```
Mara's helping hand warmly receives John's request, and John's confidence lifts slightly.
```

**Stalemate:**
```
John's attack clashes evenly with Mara's defense, resulting in a stalemate.
```

## Type 2: Pure Dialogue

**Dialogue detected, no physical actions** - Conversational flow

### Examples:

**Casual Conversation (Proactor Wins):**
```
Marcus asks "How's your day?", and Greg responds "Not bad! Busy morning. How about you?", with Marcus's spirits lifting.
```

**Persuasion (Reactor Wins):**
```
Marcus attempts to persuade him with the offer, and Greg counters "50/50? Make it 60/40 in my favor", with Marcus's confidence bolstered.
```

**Balanced Exchange (Stalemate):**
```
Marcus asks about the job, and Greg shares what he knows, resulting in a balanced conversational exchange.
```

## Type 3: Action + Dialogue

**Dialogue + physical actions** - Blended narrative

### Examples:

**Threatening While Drawing Weapon (Hostile, Proactor Wins):**
```
John shouts "Back off!" while drawing his pistol, overwhelming Mara's attempt to stand her ground, as her psychological state is shattered.
```

**Encouraging While Helping (Friendly, Reactor Wins):**
```
Marcus says "You can do this!" while steadying the ladder, and Greg climbs confidently with the support, with Marcus's morale bolstered.
```

**Negotiating While Blocking Path (Hostile, Stalemate):**
```
Marcus demands "Let me through!" while blocking the doorway, and Greg refuses "Not until you pay up" while holding his ground, resulting in a balanced exchange.
```

## Narrative Flow Patterns

### Pure Dialogue Pattern:
```
{proactor_name} {proactor_action}, and {reactor_name} {reactor_action}, with {loser}'s {consequence}.
```

**Example:**
```
Marcus asks "How's your day?", and Greg responds "Good! How about you?", with Marcus's spirits lifting.
```

### Action + Dialogue Pattern (Friendly):
```
{proactor_name} {proactor_action}, and {reactor_name} {reactor_action}, with {loser}'s {consequence}.
```

**Example:**
```
Marcus offers help while extending his hand, and Greg accepts gratefully while shaking it, with Marcus's confidence bolstered.
```

### Action + Dialogue Pattern (Hostile):
```
{proactor_name} {proactor_action}, overwhelming {reactor_name}'s {reactor_action}, as their {consequence}.
```

**Example:**
```
John threatens "Get out!" while shoving Marcus, overwhelming Marcus's attempt to resist, as his physical endurance wavers.
```

### Pure Action Pattern (Hostile):
```
{reactor_name}'s {reactor_action} proves insufficient against {proactor_name}'s {proactor_action} as their {consequence}.
```

**Example:**
```
Mara's dodge proves insufficient against John's punch as her physical endurance wavers.
```

## Complete Examples by Type

### Example 1: Pure Dialogue (Casual Chat)

**Input:**
- UA: "Hey Greg, how's business?"
- NUA: "'Slow today, but can't complain. You looking for work?' he asks"

**Narrative:**
```
Marcus asks "Hey Greg, how's business?", and Greg responds "Slow today, but can't complain. You looking for work?", with Marcus's spirits lifting from the friendly exchange.
```

### Example 2: Pure Action (Combat)

**Input:**
- UA: *punches him in the face*
- NUA: *dodges and counters*

**Narrative:**
```
Greg's dodge and counter proves insufficient against Marcus's punch as his physical endurance wavers.
```

### Example 3: Action + Dialogue (Threat)

**Input:**
- UA: "Get out of my way!" *while pushing*
- NUA: "'Make me!' he shouts back while bracing himself"

**Narrative:**
```
Marcus shouts "Get out of my way!" while pushing, overwhelming Greg's defiant stance, as his physical strength wavers.
```

### Example 4: Action + Dialogue (Encouragement)

**Input:**
- UA: "You can do this!" *while steadying the ladder*
- NUA: "'Thanks, I needed that' he says while climbing confidently"

**Narrative:**
```
Marcus encourages "You can do this!" while steadying the ladder, and Greg climbs confidently with the support, with Marcus's morale bolstered.
```

### Example 5: Action + Dialogue (Negotiation)

**Input:**
- UA: "I'll pay you 100 credits" *while placing money on counter*
- NUA: "'Make it 150' he counters while sliding it back"

**Narrative:**
```
Marcus offers "I'll pay you 100 credits" while placing money on the counter, but Greg counters "Make it 150" while sliding it back, causing Marcus's confidence to waver.
```

## Detection Criteria

### Pure Dialogue:
- ✅ `dialogue_detected: true`
- ✅ No physical action verbs (punch, kick, grab, push, etc.)
- ✅ Action description contains only speech and minimal gestures

### Pure Action:
- ✅ `dialogue_detected: false`
- ✅ Physical action verbs present
- ✅ No quoted speech

### Action + Dialogue:
- ✅ `dialogue_detected: true`
- ✅ Physical action verbs present
- ✅ Quoted speech + action description

## Benefits

1. **Natural Flow** - Each type uses appropriate narrative style
2. **Context-Aware** - Detects what kind of exchange is happening
3. **Immersive** - Conversations read like conversations, combat reads like combat
4. **Flexible** - Handles mixed scenarios (threatening while drawing weapon)
5. **Consistent** - Still uses UTAS mechanics for all types

## Files Modified

**`agents/narrator_agent.py`** (lines 671-833)
- Added three-type detection logic
- Added type-specific narrative templates
- Handles pure dialogue, pure action, and mixed exchanges

## Summary

✅ **Pure Action** - Traditional combat/action narrative
✅ **Pure Dialogue** - Conversational flow with natural language
✅ **Action + Dialogue** - Blended narrative for complex scenarios
✅ **Automatic Detection** - System determines type from metadata
✅ **Appropriate Language** - Each type uses fitting narrative style

The system now seamlessly handles any combination of dialogue and action! 🎭⚔️💬
