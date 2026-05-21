# NUA Dialogue Enhancement - Adding Personality to Proactions

## Problem Identified

NUA proactor actions were appearing as minimal, personality-less descriptions:

**Example:**
```
Jonas Keller tries to strike up a conversation with Jasper Monroe about the mixtape project
```

This lacks personality, character voice, and actual dialogue. The user already has the system capability to generate dialogue but it wasn't being applied to NUA proactions.

## Root Cause

The `DeciderAgent.determine_nua_proaction()` prompt was not **requiring** dialogue for social actions. It only asked for "a brief, dynamic description of the ATTEMPTED action" without mandating actual quoted words.

**File:** `agents/decider_agent.py` line 673

## Solution Implemented

Enhanced the `narrative_description` field requirements in the NUA proaction prompt to **mandate dialogue for social actions**.

### Changes Made:

**1. Added Dialogue Requirement Section (lines 675-685)**

```python
**DIALOGUE REQUIREMENT FOR SOCIAL ACTIONS:**
- If this is a social/conversational action (talking, persuading, intimidating, greeting, asking, etc.), 
  you MUST include actual quoted dialogue
- Format: 'says "[exact words in quotes]" while [physical action/expression]'
- Example: 'says "Hey, you got a minute? I wanted to talk about that mixtape project" while approaching 
  {reactor.sheet.name} with a friendly smile'
- Example: 'says "Back off before this gets ugly" while stepping forward aggressively toward {reactor.sheet.name}'
- The dialogue should reflect their personality, goals, and relationship with the target

**PHYSICAL ACTION FORMAT:**
- For non-dialogue actions: 'attempts to lunge at {reactor.sheet.name} with a dagger' or 
  'tries to dodge {reactor.sheet.name}'s incoming strike'
```

**2. Added Complete Example (lines 792-821)**

Provided a full JSON example showing exactly how to format a social action with dialogue:

```json
{
    "action_noun": "Approach",
    "narrative_description": "says \"Hey, you got a minute? I wanted to talk about that mixtape project\" while approaching {reactor.sheet.name} with a friendly smile",
    "character_motivation": "{proactor.sheet.name} wants to collaborate on the mixtape and sees this as an opportunity to advance their music goals while building a connection.",
    ...
}
```

**3. Updated Checklist (line 826)**

Added explicit dialogue check:
```
3. **Dialogue Requirement:** If this is a social action, did you include actual quoted dialogue?
```

## Expected Behavior Now

### Before:
```
Jonas Keller tries to strike up a conversation with Jasper Monroe about the mixtape project
```

### After:
```
"Hey, you got a minute? I wanted to talk about that mixtape project" Jonas says while 
approaching you with a friendly smile, his eyes bright with creative energy
```

## Benefits

✅ **Personality** - NPCs now speak with their own voice  
✅ **Immersion** - Dialogue makes characters feel alive  
✅ **Character Expression** - Words reflect personality, goals, and relationships  
✅ **Consistency** - Matches the existing reactor dialogue system  
✅ **Engagement** - Players get immediate sense of NPC character

## Technical Details

**File Modified:** `agents/decider_agent.py`
- Lines 673-685: Added dialogue requirement section
- Lines 792-821: Added complete example
- Line 826: Updated checklist

**System Flow:**
1. DeciderAgent generates action with dialogue in `narrative_description`
2. NarratorAgent transforms it into perceptual narrative via `generate_nua_action_perceptual_narrative()`
3. Dialogue is preserved and enhanced in final output

## Note on Reactor Actions

The reactor prompt (lines 1065-1094, 1270-1276) **already had** strong dialogue requirements. This change brings proactor actions up to the same standard.

## Testing

Test with various social NUA proactions:
- Greetings and introductions
- Persuasion attempts
- Intimidation
- Casual conversation
- Negotiations
- Emotional appeals

Each should now include actual quoted dialogue that reflects the NPC's personality and goals.
