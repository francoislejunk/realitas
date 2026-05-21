# Complete Dialogue Integration - Three-Type System

## Overview

The UTAS system now fully supports **three distinct exchange types** with proper detection, generation, and narrative flow:

1. **Pure Action** - Physical actions without dialogue
2. **Pure Dialogue** - Conversational exchanges without physical actions  
3. **Action + Dialogue** - Speaking while performing actions

## Complete Implementation Chain

### 1. InterpreterAgent (Detection & Metadata)

**Added `dialogue_only` field to dialogue_metadata:**

```json
"dialogue_metadata": {
    "dialogue_detected": true/false,
    "dialogue_intent": "SmallTalk/Inquiry/Persuasion/Threat/Insult/Command/Story/None",
    "dialogue_weight": 3,
    "talk_time_seconds": 9,
    "can_affect_status": true/false,
    "apply_shift": true/false,
    "dialogue_only": true/false  // NEW: true = pure dialogue, false = action + dialogue
}
```

**Classification Guidance (lines 257-261):**
- **Pure Dialogue (dialogue_only=true):** ONLY speaking, no physical action
  - Examples: "How's your day?", "I think we should leave", "Your mom's a bitch"
- **Action + Dialogue (dialogue_only=false):** Speaking WHILE doing something
  - Examples: "Get out!" *while pushing*, "You can do this!" *while helping*

### 2. DeciderAgent (NUA Response Generation)

**Added dialogue type guidance (lines 739-744):**

```
**DIALOGUE TYPE IN YOUR RESPONSE:**
- Pure Dialogue Response: If you're ONLY speaking (no physical action), set dialogue_only=true
  - Example: "'Good! How about you?' he asks" → dialogue_only=true
- Action + Dialogue Response: If you're speaking WHILE doing something, set dialogue_only=false
  - Example: "'Get out!' he shouts while pushing them toward the door" → dialogue_only=false
```

**Critical Instruction (lines 732-737):**
- NPCs MUST respond with actual spoken words
- Include dialogue in narrative_description
- Blend speech with any physical actions

### 3. NarratorAgent (Narrative Generation)

**Three-type detection (lines 671-684):**

```python
# Detect dialogue and action types
has_dialogue = proactor_dialogue.get('dialogue_detected', False) or reactor_dialogue.get('dialogue_detected', False)

# Determine if actions contain physical components
proactor_has_physical = not proactor_dialogue.get('dialogue_only', False)
reactor_has_physical = not reactor_dialogue.get('dialogue_only', False)

# Determine exchange type
is_pure_dialogue = has_dialogue and not (proactor_has_physical or reactor_has_physical)
is_action_with_dialogue = has_dialogue and (proactor_has_physical or reactor_has_physical)
is_pure_action = not has_dialogue
```

**Type-specific narrative templates (lines 744-833):**
- Pure dialogue → Conversational flow
- Action + dialogue → Blended narrative
- Pure action → Traditional combat/action

## Complete Flow Examples

### Example 1: Pure Dialogue (Casual Greeting)

**User Input:**
```
"Hey Greg, how's your day?"
```

**InterpreterAgent Output:**
```json
{
  "narrative_description": "asks 'Hey Greg, how's your day?'",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "SmallTalk",
    "dialogue_weight": 1,
    "dialogue_only": true,  // ← Pure dialogue
    "apply_shift": false
  }
}
```

**DeciderAgent Output (NUA):**
```json
{
  "narrative_description": "responds 'Not bad! Busy morning. How about you?' with a friendly smile",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_weight": 2,
    "dialogue_only": true  // ← Pure dialogue response
  }
}
```

**NarratorAgent Output:**
```
Marcus asks "Hey Greg, how's your day?", and Greg responds "Not bad! Busy morning. How about you?" with a friendly smile, resulting in a balanced conversational exchange.
```

### Example 2: Action + Dialogue (Threat)

**User Input:**
```
"Get out of my way!" *while pushing him*
```

**InterpreterAgent Output:**
```json
{
  "narrative_description": "shouts 'Get out of my way!' while pushing him forcefully",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "Threat",
    "dialogue_weight": 1,
    "dialogue_only": false,  // ← Action + dialogue
    "apply_shift": true
  }
}
```

**DeciderAgent Output (NUA):**
```json
{
  "narrative_description": "shouts 'Make me!' while bracing himself against the push",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_weight": 1,
    "dialogue_only": false  // ← Action + dialogue response
  }
}
```

**NarratorAgent Output:**
```
Marcus shouts "Get out of my way!" while pushing, overwhelming Greg's defiant resistance, as his physical strength wavers.
```

### Example 3: Pure Action (Combat)

**User Input:**
```
I punch him in the face
```

**InterpreterAgent Output:**
```json
{
  "narrative_description": "throws a punch at his face",
  "dialogue_metadata": null  // No dialogue
}
```

**DeciderAgent Output (NUA):**
```json
{
  "narrative_description": "dodges and counters with a swift jab",
  "dialogue_metadata": null  // No dialogue
}
```

**NarratorAgent Output:**
```
Marcus's punch proves insufficient against Greg's dodge and counter as his physical endurance wavers.
```

### Example 4: Action + Dialogue (Encouragement)

**User Input:**
```
"You can do this!" *while steadying the ladder*
```

**InterpreterAgent Output:**
```json
{
  "narrative_description": "encourages 'You can do this!' while steadying the ladder",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_intent": "Encouragement",
    "dialogue_weight": 1,
    "dialogue_only": false,  // ← Action + dialogue
    "apply_shift": true,
    "shift_polarity": "Additive"
  }
}
```

**DeciderAgent Output (NUA):**
```json
{
  "narrative_description": "responds 'Thanks, I needed that!' while climbing with renewed confidence",
  "dialogue_metadata": {
    "dialogue_detected": true,
    "dialogue_weight": 1,
    "dialogue_only": false  // ← Action + dialogue response
  }
}
```

**NarratorAgent Output:**
```
Marcus encourages "You can do this!" while steadying the ladder, and Greg responds "Thanks, I needed that!" while climbing with renewed confidence, with Marcus's morale bolstered.
```

## Detection Matrix

| Input Type | dialogue_detected | dialogue_only | Physical Action | Narrative Style |
|------------|------------------|---------------|-----------------|-----------------|
| "How's your day?" | true | true | false | Conversational |
| "Get out!" *pushes* | true | false | true | Blended |
| *punches* | false | N/A | true | Combat/Action |
| "You can do this!" *helps* | true | false | true | Blended |

## Files Modified

1. **`agents/interpreter_agent.py`**
   - Added `dialogue_only` field to dialogue_metadata (lines 329, 2073)
   - Added dialogue type classification guidance (lines 257-261)

2. **`agents/decider_agent.py`**
   - Added dialogue type guidance for NUA responses (lines 739-744)
   - NPCs now specify dialogue_only in their responses

3. **`agents/narrator_agent.py`**
   - Added three-type detection logic (lines 671-684)
   - Added type-specific narrative templates (lines 744-833)
   - Pure dialogue, action+dialogue, and pure action each use appropriate language

## Benefits

✅ **Accurate Detection** - System knows if it's pure dialogue, action+dialogue, or pure action
✅ **Appropriate Narrative** - Each type uses fitting language and flow
✅ **Natural Conversations** - Pure dialogue reads like actual conversation
✅ **Blended Actions** - Action+dialogue seamlessly combines both elements
✅ **Full UTAS Integration** - All types still use complete UTAS mechanics
✅ **NPC Agency** - NPCs respond with appropriate type (dialogue or action+dialogue)

## Testing Checklist

- [ ] Pure dialogue: "Hello" → Conversational narrative
- [ ] Pure action: *punch* → Combat narrative
- [ ] Action + dialogue (threat): "Back off!" *draws weapon* → Blended narrative
- [ ] Action + dialogue (help): "You got this!" *assists* → Blended narrative
- [ ] NPC pure dialogue response → Spoken words only
- [ ] NPC action + dialogue response → Speech with physical action
- [ ] Polarity detection works for all three types
- [ ] Status shifts apply correctly for all types

## Summary

The three-type dialogue system is now **fully integrated** across the entire UTAS pipeline:

1. **InterpreterAgent** detects and classifies dialogue type
2. **DeciderAgent** generates appropriate NPC responses with type metadata
3. **NarratorAgent** uses type-specific narrative templates
4. **Exchange System** applies UTAS mechanics to all types
5. **Polarity-aware** language for friendly vs hostile in all types

Conversations, combat, and blended scenarios all flow naturally! 🎭⚔️💬
