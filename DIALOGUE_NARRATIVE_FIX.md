# Dialogue Narrative Fix

## Problem Identified

When NPCs responded to conversational inputs, the narrative used **combat-style language** instead of natural dialogue flow:

**Example:**
```
UA: "Hi there Greg, how's your day?"
NUA: *approaches with a friendly nod, ready to share gossip*

Narrative: "Wiry Man overcomes Marcus Carter's question..."
```

**Issues:**
- ❌ NPC doesn't speak actual words back
- ❌ Narrative uses combat language ("overcomes") for casual chat
- ❌ No natural conversational flow

## Root Causes

### 1. **DeciderAgent Not Generating Dialogue**
The DeciderAgent had conversational guidance but wasn't explicitly told to **respond with actual spoken words**.

### 2. **NarratorAgent Using Combat Templates**
The Step 6 narrative used the same templates for dialogue as it did for combat, resulting in adversarial language for friendly conversations.

## Fixes Applied

### Fix 1: DeciderAgent - Explicit Dialogue Response (lines 732-737)

Added **"🗣️ CRITICAL: RESPOND WITH ACTUAL DIALOGUE"** section:

```python
**🗣️ CRITICAL: RESPOND WITH ACTUAL DIALOGUE:**
- If UA spoke to you, YOU MUST SPEAK BACK with actual words
- Include your spoken response in the narrative_description
- Example: "Not bad! Busy morning. How about you?" or "Good to see you. What brings you in?"
- Don't just describe actions - include the WORDS you say
- Your narrative should contain both dialogue AND any accompanying actions
```

**Result:** NPCs now generate responses like:
```
"'Good! Busy morning with the breakfast rush. How about you, Sam?' Greg replies while wiping down the counter."
```

### Fix 2: NarratorAgent - Dialogue Detection (lines 671-674)

Added dialogue detection from metadata:

```python
# Detect if this is a dialogue exchange
proactor_dialogue = proactor_data.get('dialogue_metadata', {})
reactor_dialogue = reactor_data.get('dialogue_metadata', {})
is_dialogue = proactor_dialogue.get('dialogue_detected', False) or reactor_dialogue.get('dialogue_detected', False)
```

### Fix 3: NarratorAgent - Conversational Templates (lines 736-791)

Added dialogue-specific narrative templates:

**For Dialogue Exchanges:**
```python
if is_dialogue:
    # Dialogue exchange - use conversational language
    pure_resolution = (
        f"{proactor_name} {proactor_action}, and {reactor_name} {reactor_action}, "
        f"with {loser}'s {cons_phrase}."
    )
```

**Stalemate (Balanced Conversation):**
```python
if is_dialogue:
    # Dialogue exchange - conversational stalemate
    pure_resolution = (
        f"{proactor_name} {proactor_action}, and {reactor_name} {reactor_action}, "
        f"resulting in a balanced conversational exchange."
    )
```

## Expected Results

### Before Fix:

**Casual Greeting:**
```
UA: "Hi there Greg, how's your day?"
NUA: "approaches with a friendly nod, ready to share gossip"
Narrative: "Wiry Man overcomes Marcus Carter's question..."
```

### After Fix:

**Casual Greeting:**
```
UA: "Hi there Greg, how's your day?"
NUA: "'Not bad! Busy morning. How about you?' Greg says with a friendly smile"
Narrative: "Marcus asks 'Hi there Greg, how's your day?', and Greg responds 'Not bad! Busy morning. How about you?' with a friendly smile, with Marcus's confidence lifting slightly."
```

**Persuasion:**
```
UA: "You should help me with this job - we'll split the profit 50/50"
NUA: "'50/50? I don't know... that seems risky. Make it 60/40 in my favor and we'll talk,' he counters"
Narrative: "Marcus attempts to persuade him with the offer, and Greg counters with his own terms, with Marcus's morale bolstered by the negotiation."
```

**Insult:**
```
UA: "You're pathetic"
NUA: "'Watch your mouth before I throw you out of here,' he snaps back"
Narrative: "Marcus insults him, and Greg snaps back defensively, with Marcus's relationship damaged."
```

## Narrative Flow Examples

### Friendly Dialogue (Additive/SPIRIT):
```
Marcus: "How's business been?"
Greg: "'Slow today, but can't complain. You looking for work?'"

Narrative: "Marcus asks about business, and Greg responds while wiping the counter, with Marcus's spirits lifting from the friendly exchange."
```

### Tense Dialogue (Subtractive/SYMPATHY):
```
Marcus: "I heard you've been talking about me behind my back"
Greg: "'I don't know what you're talking about,' he says defensively"

Narrative: "Marcus confronts him about the rumors, and Greg deflects defensively, with Marcus's trust in him deteriorating."
```

### Persuasion (Additive/SPIRIT):
```
Marcus: "Come on, you know I'm good for it. Just this once?"
Greg: "'Alright, alright. But this is the last time, you hear me?'"

Narrative: "Marcus pleads his case, and Greg reluctantly agrees, with Marcus's confidence bolstered by the successful persuasion."
```

## Integration with Full Dialogue System

This fix completes the dialogue integration:

1. ✅ **InterpreterAgent** - Detects dialogue and estimates weight
2. ✅ **DeciderAgent** - Generates actual spoken responses with conversational goals
3. ✅ **NarratorAgent** - Uses conversational narrative templates
4. ✅ **Exchange System** - Applies UTAS mechanics to dialogue
5. ✅ **Polarity-Aware** - Friendly vs hostile language

## Files Modified

1. **`agents/decider_agent.py`** (lines 732-737)
   - Added explicit dialogue response instructions
   - NPCs now speak actual words in their narrative_description

2. **`agents/narrator_agent.py`** (lines 671-674, 736-791)
   - Added dialogue detection from metadata
   - Added conversational narrative templates
   - Dialogue exchanges use natural flow instead of combat language

## Summary

✅ **NPCs speak actual dialogue** - Include spoken words in responses
✅ **Natural narrative flow** - Conversational templates for dialogue exchanges
✅ **Context-appropriate language** - Friendly chat vs. hostile confrontation
✅ **Full UTAS integration** - Dialogue still uses mechanics but reads naturally

Conversations now feel like **actual conversations**, not combat descriptions! 💬🎭
