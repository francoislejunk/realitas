# Preserve UA Dialogue Fix

## Problem Identified

When the UA speaks dialogue, the **InterpreterAgent paraphrases it** instead of preserving the actual quoted words. This causes two critical issues:

1. **NUA never sees the actual dialogue** - Can't respond to exact words
2. **NUA doesn't know dialogue is expected** - Generates descriptions instead of speech

### Example

**UA Input:**
```
"What the fuck! Who is forcing you to wear those hideous uniforms?"
```

**InterpreterAgent Output (WRONG):**
```
Derek Malone strides up to the waitress with a confrontational tone, his voice sharp 
as he demands to know who is forcing her to wear what he deems 'hideous uniforms.'
```

**What NUA Sees:** A paraphrased description
**What NUA Needs:** The actual quoted dialogue

**InterpreterAgent Output (CORRECT):**
```
Derek Malone strides up to the waitress and says, "What the fuck! Who is forcing you 
to wear those hideous uniforms?" His voice is sharp and confrontational, causing 
nearby patrons to glance over.
```

## Root Cause

The InterpreterAgent's `narrative_description` field was generating **rich, immersive descriptions** but treating dialogue as something to **paraphrase** rather than **preserve verbatim**.

The prompt said:
```
"narrative_description": "Rich, immersive description of the action"
```

The LLM interpreted this as:
- ✅ Make it immersive
- ❌ Paraphrase dialogue for narrative flow

## Fix Applied

### Updated InterpreterAgent Prompt (lines 299, 2052)

Added explicit instruction to preserve quoted dialogue:

```json
"narrative_description": "Rich, immersive description of the action. **CRITICAL: If the user 
input contains dialogue (quoted speech), you MUST include the EXACT quoted words in this 
description. Do not paraphrase dialogue - preserve it verbatim in quotation marks.**"
```

Applied to **both** prompts:
1. User action interpretation (line 299)
2. Fallible action interpretation (line 2052)

## Expected Behavior

### Scenario 1: Casual Dialogue

**UA Input:**
```
"Hey, how's it going?"
```

**Before Fix:**
```
Derek approaches the bartender and asks about his day in a friendly manner.
```

**After Fix:**
```
Derek approaches the bartender and says, "Hey, how's it going?" with a friendly smile.
```

### Scenario 2: Aggressive Dialogue

**UA Input:**
```
"What the fuck! Who is forcing you to wear those hideous uniforms?"
```

**Before Fix:**
```
Derek strides up with a confrontational tone, demanding to know who is forcing her to wear 
what he deems 'hideous uniforms.'
```

**After Fix:**
```
Derek strides up to the waitress and says, "What the fuck! Who is forcing you to wear those 
hideous uniforms?" His voice is sharp and confrontational.
```

### Scenario 3: Threat

**UA Input:**
```
"Get out of my way or I'll make you move."
```

**Before Fix:**
```
Derek threatens the bouncer, warning him to move aside or face consequences.
```

**After Fix:**
```
Derek steps forward and says, "Get out of my way or I'll make you move," his tone menacing.
```

### Scenario 4: Question

**UA Input:**
```
"Do you know where the boss is?"
```

**Before Fix:**
```
Derek asks the waitress about the boss's location.
```

**After Fix:**
```
Derek approaches the waitress and asks, "Do you know where the boss is?"
```

## Why This Matters

### 1. NUA Can See Exact Words
The DeciderAgent receives the actual dialogue and can craft an appropriate response:

**NUA Sees:**
```
"What the fuck! Who is forcing you to wear those hideous uniforms?"
```

**NUA Can Respond:**
```
"'Whoa, easy there! It's just the company policy,' she says defensively while taking a step back."
```

### 2. NUA Knows Dialogue is Expected
When the NUA sees quoted speech in the proactor's action, it knows to respond with quoted speech.

### 3. Maintains Exact Tone and Wording
Paraphrasing loses:
- Profanity intensity ("What the fuck" vs. "demands to know")
- Exact phrasing
- Conversational style
- Emotional weight

## Key Principle

**Dialogue is sacred - preserve it verbatim.**

When the UA speaks:
1. ✅ Include the exact quoted words
2. ✅ Add narrative context around it
3. ❌ Never paraphrase or summarize dialogue

## Format Examples

### Pure Dialogue:
```
[Actor] says, "[Exact quoted words]" [with manner/tone]
```

### Action + Dialogue:
```
[Actor] [action] and says, "[Exact quoted words]" [additional context]
```

### Dialogue First:
```
"[Exact quoted words]," [Actor] says [with manner/action]
```

## Testing Checklist

- [ ] UA says "Hello" → Preserved as "Hello"
- [ ] UA says "What the fuck!" → Preserved as "What the fuck!"
- [ ] UA says "Get out" → Preserved as "Get out"
- [ ] UA asks "Where is he?" → Preserved as "Where is he?"
- [ ] All dialogue appears in quotation marks
- [ ] No paraphrasing of dialogue content
- [ ] NUA can see exact words to respond to

## Files Modified

**`agents/interpreter_agent.py`** (lines 299, 2052)
- Added critical instruction to preserve quoted dialogue
- Applied to both user action and fallible action prompts
- Emphasized "EXACT quoted words" and "verbatim"

## Summary

✅ **UA dialogue preserved verbatim** - No more paraphrasing
✅ **NUA sees exact words** - Can craft appropriate responses
✅ **Dialogue triggers dialogue** - NUA knows to respond with speech
✅ **Tone and intensity maintained** - Profanity, emotion, style preserved

The InterpreterAgent now treats dialogue as sacred text to preserve, not prose to paraphrase! 💬✨
