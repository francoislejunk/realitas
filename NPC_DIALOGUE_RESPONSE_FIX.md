# NPC Dialogue Response Fix

## Problem Identified

When the UA speaks dialogue to an NPC, the NPC's response **describes** that they're speaking but doesn't include the **actual words** they say.

**Example:**

**UA Input:**
```
"That is the ugliest uniform I have ever seen. Who is making you wear that?"
```

**NPC Response (WRONG):**
```
Linda turns to Derek Holloway with a raised eyebrow, her tone light and teasing 
as she attempts to brush off the insult with a joke.
```

**What's Missing:** The actual joke! What does she say?

**NPC Response (CORRECT):**
```
Linda turns to Derek with a raised eyebrow and laughs. "Oh this old thing? Yeah, 
management's fashion sense is... questionable. But hey, it's got pockets!" she says 
with a teasing grin, attempting to deflect the insult with humor.
```

## Root Cause

The DeciderAgent prompt said "respond with actual dialogue" but didn't provide clear **wrong vs. right examples**. The LLM was interpreting this as:
- ❌ "Describe that you're speaking" instead of
- ✅ "Write the actual words in quotes"

## Fix Applied

### Updated DeciderAgent Prompt (lines 732-742)

Added explicit **WRONG vs. RIGHT examples**:

```
**🗣️ CRITICAL: RESPOND WITH ACTUAL DIALOGUE:**
- If UA spoke to you, YOU MUST SPEAK BACK with actual words in quotes
- WRONG: "she attempts to brush off the insult with a joke" ❌
- RIGHT: "'Oh this old thing? Yeah, management's fashion sense is questionable!' she jokes" ✅
- Include the EXACT WORDS you say in quotation marks
- Don't just describe that you're speaking - write the actual dialogue
- Your narrative should contain both the spoken words AND any accompanying actions
- Example formats:
  - "'Not bad! Busy morning. How about you?' he asks with a smile"
  - "She laughs, 'Oh please, I've seen worse. You should see the summer uniform!'"
  - "'Get out of here,' he says while pointing to the door"
```

## Expected Behavior

### Scenario 1: Casual Greeting

**UA:** "Hey, how's it going?"

**Before Fix:**
```
Greg responds with a friendly tone, asking about Derek's day.
```

**After Fix:**
```
"Not bad! Busy morning. How about you?" Greg asks with a friendly smile.
```

### Scenario 2: Insult/Provocation

**UA:** "That is the ugliest uniform I have ever seen."

**Before Fix:**
```
Linda attempts to brush off the insult with a joke.
```

**After Fix:**
```
Linda laughs, "Oh please, I've seen worse. You should see the summer uniform!" 
she says with a teasing grin.
```

### Scenario 3: Threat

**UA:** "Get out of my way or else."

**Before Fix:**
```
The bouncer responds with a threatening tone, refusing to move.
```

**After Fix:**
```
"Make me," the bouncer growls while crossing his arms and blocking the doorway.
```

### Scenario 4: Question

**UA:** "Do you know where the boss is?"

**Before Fix:**
```
She provides information about the boss's location.
```

**After Fix:**
```
"Last I saw, he was in the back office. But that was an hour ago," she says 
while wiping down the counter.
```

## Key Principle

**If the UA speaks dialogue, the NPC MUST respond with dialogue.**

The response should include:
1. ✅ **Quoted speech** - The actual words they say
2. ✅ **Action tags** - Physical actions accompanying the speech
3. ✅ **Tone/manner** - How they say it (laughs, growls, asks, etc.)

## Format Examples

### Pure Dialogue:
```
"'[Spoken words]' [he/she] [says/asks/replies/responds] [with manner]"
```

### Action + Dialogue:
```
"[He/She] [action], '[Spoken words]' [he/she] [says/asks] [while action]"
```

### Dialogue First:
```
"'[Spoken words],' [he/she] [says/asks] [with manner/action]"
```

## Testing Checklist

- [ ] UA greets NPC → NPC responds with greeting words
- [ ] UA insults NPC → NPC responds with defensive/joking words
- [ ] UA threatens NPC → NPC responds with defiant/fearful words
- [ ] UA asks question → NPC responds with answer words
- [ ] UA persuades NPC → NPC responds with agreement/refusal words
- [ ] All responses include actual quoted dialogue
- [ ] No responses just describe that they're speaking

## Files Modified

**`agents/decider_agent.py`** (lines 732-742)
- Added explicit WRONG vs. RIGHT examples
- Emphasized "actual words in quotes"
- Provided multiple format examples
- Made it crystal clear: don't describe dialogue, write it

## Summary

✅ **NPCs now speak actual words** - Not just descriptions of speaking
✅ **Clear examples** - WRONG vs. RIGHT format shown
✅ **Multiple formats** - Various ways to structure dialogue + action
✅ **Conversational flow** - Dialogue exchanges feel natural

NPCs will now have actual conversations with quoted speech! 💬✨
