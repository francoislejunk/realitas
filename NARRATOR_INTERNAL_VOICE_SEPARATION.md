# Narrator vs Internal Voice Separation

## Problem Identified

The narrator was bleeding into the internal voice's territory by providing **suggestions and advice** in inquiry responses.

### Example of the Problem

**User Question:** "Where am I?"

**Narrator Output (WRONG):**
```
You scan the room, but the unfamiliar surroundings offer no clues. 
You can't quite place where you are, so you might need to ask someone 
or look for a sign that gives you a hint.
```

**Issues:**
- ❌ "you might need to" - Suggestion (internal voice's job)
- ❌ "ask someone" - Advice (internal voice's job)
- ❌ "look for a sign" - Suggestion (internal voice's job)

## Clear Separation of Responsibilities

### Narrator's ONLY Job
**DESCRIBE what is perceived RIGHT NOW (present moment only)**

✅ **What to Include:**
- Present sensory perceptions: "You see...", "You hear...", "You smell..."
- Direct observations NOW: "The room is...", "There are...", "It's..."
- Lack of perception: "You don't see...", "You can't hear...", "Nothing visible..."

✅ **Correct Example:**
```
You scan the room. Unfamiliar walls, unfamiliar furniture. 
Nothing you recognize. The space is small and cluttered.
```

❌ **What NOT to Include:**
- Memories: "You recall...", "You remember..." (Internal voice's job!)
- Past perceptions: "You've seen...", "You know..." (Internal voice's job!)

### Internal Voice's ONLY Job
**RECALL memories and SUGGEST what to do**

✅ **What to Include:**
- Memories: "We recall...", "We remember...", "We've seen..."
- Knowledge: "We know...", "We learned..."
- Suggestions: "We could...", "We should..."
- Reasoning: "Maybe we...", "Let's try..."
- Advice: "We need to...", "We might want to..."
- Deduction: "This probably means...", "We should consider..."

✅ **Correct Example:**
```
We don't know where we are. We don't recall being here before. 
Maybe we should ask someone, or look for a sign that gives us a clue.
```

## Forbidden Phrases in Narrator

The narrator must **NEVER** use these phrases:

### Memory Words (Internal Voice Territory):
❌ "you recall"
❌ "you remember"
❌ "you've seen"
❌ "you know"

### Suggestion/Advice Words (Internal Voice Territory):
❌ "you might need to"
❌ "you could try"
❌ "you should"
❌ "maybe you"
❌ "try to"
❌ "look for"
❌ "ask someone"
❌ "find out"
❌ "check if"

These are **ALL internal voice territory**.

## Complete Example Flow

### User Question: "Where am I?"

**Narrator (Present Perceptions ONLY):**
```
You scan the room. Unfamiliar walls, unfamiliar furniture. 
Nothing you recognize. The space is small and cluttered.
```

**Internal Voice (Memories + Suggestions):**
```
We don't know where we are. We don't recall being here before. 
Maybe we should ask someone, or look for a sign that gives us a clue.
```

### User Question: "What's the best way to get downtown?"

**Narrator (Present Perceptions ONLY):**
```
You look around. You see a street sign pointing north. 
Traffic flows steadily in both directions.
```

**Internal Voice (Memories + Reasoning):**
```
We recall the U-Bahn station two blocks north. Line 3 runs downtown. 
We could take that - it's faster than walking.
```

### User Question: "Where can I find spare parts?"

**Narrator (Present Perceptions ONLY):**
```
You scan the area. Industrial buildings line the street. 
You don't see any obvious shops or stores nearby.
```

**Internal Voice (Memories + Advice):**
```
We recall seeing a junkyard three blocks east, past the old factory. 
That's probably our best bet for spare parts. Let's check there first.
```

## Implementation

### Updated Narrator Prompt

**Key Changes:**
1. **REMOVED memory words** - "recall", "remember", "know" now forbidden
2. Added explicit **FORBIDDEN PHRASES** list (memory + suggestion words)
3. Added **WHAT TO INCLUDE / WHAT TO EXCLUDE** sections
4. Added the exact problematic output as a BAD example
5. Strengthened system message to ban memory AND suggestion words
6. Made rules more explicit and forceful

**New System Message:**
```
Generate PURELY PERCEPTUAL narrative answers. ONLY describe what is 
seen/heard/felt/smelled/tasted RIGHT NOW. ABSOLUTELY NO memories, 
suggestions, advice, or reasoning. NEVER use: 'recall', 'remember', 
'might', 'could', 'should', 'need to', 'try', 'maybe'. 
Just raw sensory perceptions in the present moment. 2-4 sentences.
```

### Internal Voice Enhanced

The internal voice prompt was updated to **REQUIRE both memory AND suggestion**:

**New Structure Requirement:**
```
[Memory/Knowledge statement] + [Suggestion/Advice]
```

**Key Changes:**
1. **ALWAYS include both parts** - Memory statement + Suggestion
2. **Memory words required:** "We recall", "We remember", "We know", "We don't know"
3. **Suggestion words required:** "We could", "We should", "Maybe we", "Let's"
4. **2-3 sentences** (was 1-2, now requires both parts)
5. **Examples show BAD outputs** that lack suggestions

**New System Message:**
```
Generate internal voice with BOTH memory recall AND suggestions. 
Structure: [Memory statement using 'we recall/remember/know/don't know'] + 
[Suggestion using 'we could/should/maybe/let's']. 
ALWAYS include both parts. 2-3 sentences.
```

**Fallback Updated:**
- Old: "We're not sure about that."
- New: "We don't know. Maybe we should ask someone or look around for clues."

## Files Modified

**`agents/narrator_agent.py`:**
- `generate_inquiry_response()` method (lines 3169-3264) - Narrator perceptions only
- `generate_inquiry_internal_voice()` method (lines 3033-3150) - Internal voice with required memory + suggestion structure

## Result

**Narrator:** ONLY describes present sensory perceptions (what you see/hear/feel RIGHT NOW)  
**Internal Voice:** Recalls memories AND suggests what to do with that information

**Clean separation:**
- Narrator = Camera lens (present moment only)
- Internal Voice = Mind (memories + reasoning + suggestions)

**No bleeding. No confusion.**
