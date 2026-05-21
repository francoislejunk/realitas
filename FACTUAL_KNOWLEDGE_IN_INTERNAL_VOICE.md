# Factual Knowledge Belongs in Internal Voice

## The Problem

When asking "Where am I?" in their own apartment, the system was responding:
- **Narrator:** "You see a cluttered room. Unfamiliar walls, unfamiliar furniture."
- **Internal Voice:** "We don't recognize this place. Maybe we should ask someone."

This broke immersion because the character didn't recognize **their own apartment**!

## The Solution

**Narrator = Camera Lens (Perceptions ONLY)**
- Shows what you see, hear, smell, feel, taste RIGHT NOW
- NO factual knowledge, NO memories, NO reasoning

**Internal Voice = Mind (Factual Knowledge + Suggestions)**
- States what we know about the situation
- Provides suggestions based on that knowledge

## The Correct Flow

### Question: "Where am I?" (in your apartment)

**Narrator (Perceptions Only):**
```
You see a cluttered room. Vinyl records stacked everywhere. 
An answering machine blinking in the corner. The air smells 
of stale cigarettes and cold pizza.
```

**Internal Voice (Factual Knowledge + Suggestions):**
```
This is our apartment. We're home. Everything's where we left it.
```

### Question: "Where am I?" (unfamiliar location)

**Narrator (Perceptions Only):**
```
You scan the room. Unfamiliar walls, unfamiliar furniture. 
Nothing you recognize. The space is small and cluttered.
```

**Internal Voice (Factual Knowledge + Suggestions):**
```
We don't know where we are. We don't recognize this place. 
Maybe we should ask someone or look for a sign.
```

## Key Changes

### Narrator Prompt
**CRITICAL RULE:** ABSOLUTELY NO factual knowledge

**Forbidden:**
- ❌ "This is your apartment"
- ❌ "You're downtown"
- ❌ "You're on Main Street"

**Allowed:**
- ✅ "You see a cluttered room"
- ✅ "You hear traffic outside"
- ✅ "The air smells of cigarettes"

### Internal Voice Prompt
**CRITICAL RULE:** Analyze scene context to determine familiarity

**Required:**
- ✅ If scene says "your apartment" → "This is our apartment"
- ✅ If scene says "unfamiliar" → "We don't recognize this place"
- ✅ Always include suggestion/advice

**Examples:**
```
Scene: "your apartment"
→ "This is our apartment. We're home."

Scene: "a dimly lit room"
→ "We don't know where we are. Maybe we should look for clues."

Scene: "Main Street downtown"
→ "We're on Main Street. We could take the U-Bahn from here."
```

## Files Modified

**`agents/narrator_agent.py`:**
1. **`generate_inquiry_response()`** (lines 3184-3261)
   - Reverted to PURELY PERCEPTUAL
   - NO factual knowledge allowed
   - Only raw sensory perceptions

2. **`generate_inquiry_internal_voice()`** (lines 3070-3133)
   - Now includes factual knowledge
   - Analyzes scene context for familiarity
   - States what we know + suggests what to do

## Result

✅ **Narrator:** Pure camera lens - shows what you perceive  
✅ **Internal Voice:** Mind - knows where you are and what to do  
✅ **Immersion:** Character recognizes their own apartment  
✅ **Consistency:** Same separation as all other systems

The character will now correctly recognize familiar locations through their internal voice, while the narrator just describes what they perceive.
