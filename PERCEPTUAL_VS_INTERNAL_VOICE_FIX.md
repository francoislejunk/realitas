# Perceptual vs Internal Voice Separation Fix

## The Problem

The perceptual description was giving memory recall RESULTS instead of just describing the physical act of thinking.

**Bad Output:**
```
PERCEPTUAL:
"As you delve into the recesses of your memory, a name and a face begin to coalesce. 
The first name, 'Mila', emerges from your thoughts. You hear Mila's voice in your head, 
vivid and clear. She's the person who made the 1993 rave scene in Berlin unforgettable."

INTERNAL VOICE:
"We were always so much more passionate and dedicated to our dreams when we had 
someone to share them with."
```

**Issue:** The perceptual description is revealing:
- The name "Mila" ❌
- The memory content ❌
- What the character discovers ❌

This is the internal voice's job, NOT the perceptual description's job!

## The Correct Separation

### Perceptual Description (What You See/Do)
- **ONLY** describes physical actions and sensory perceptions
- Body language: closing eyes, pausing, concentrating, furrowing brow
- External observations: what's visible in the room, sounds, smells
- **NEVER** describes memory content, discoveries, or realizations

### Internal Voice (What You Think/Know)
- Reveals memory content and discoveries
- Provides factual knowledge
- Shares reasoning and realizations
- Contains the actual information recalled

## The Solution

Updated both `generate_inquiry_response()` (perceptual) and `generate_inquiry_internal_voice()` (internal voice) methods in `narrator_agent.py` to enforce strict separation and ensure internal voice reveals memory content.

### Changes Made

**File:** `agents/narrator_agent.py`

### Part 1: Perceptual Description (Inquiry Response)

**1. Updated Availability Guidance for Perceptual (lines 3308-3331)**

**EXIST (Memory accessible):**
```python
availability_guidance = f"""
**AVAILABILITY CONTEXT:** The thing being asked about EXISTS and is accessible.
- ONLY describe the PHYSICAL ACT of thinking/concentrating
- Show the character's body language while thinking (closing eyes, pausing, concentrating)
- DO NOT describe what they discover/recall - that's internal voice's job!
- Example: "You pause and close your eyes, concentrating. Your brow furrows slightly as you think."
"""
```

**EXIST_NOT_HERE (Memory exists but fuzzy):**
```python
availability_guidance = f"""
**AVAILABILITY CONTEXT:** The thing being asked about EXISTS but is not accessible right now.
- ONLY describe the PHYSICAL ACT of struggling to think/remember
- Show the character's body language (squinting, hesitating, looking frustrated)
- DO NOT describe the memory being fuzzy - that's internal voice's job!
- Example: "You close your eyes and concentrate, your face tense with effort."
"""
```

**DOES_NOT_EXIST (No memory):**
```python
availability_guidance = f"""
**AVAILABILITY CONTEXT:** The thing being asked about DOES NOT EXIST in this character's life.
- ONLY describe the PHYSICAL ACT of thinking/searching mentally
- Show the character's body language (furrowed brow, blank stare, shaking head)
- DO NOT describe what they discover or don't discover - that's internal voice's job!
- Example: "You pause and think hard, your eyes distant. You shake your head slightly."
"""
```

**2. Added Critical Rules (lines 3346-3353)**

```python
**CRITICAL RULES:**
1. Use 2nd person ("you") for narrative descriptions
2. ONLY describe what can be DIRECTLY PERCEIVED RIGHT NOW (seen, heard, felt, smelled, tasted)
3. For MEMORY RECALL questions: ONLY describe the PHYSICAL ACT of thinking (body language, pausing, concentrating)
4. NEVER describe what the character discovers, recalls, or realizes - that's internal voice's job!
5. ABSOLUTELY NO factual knowledge, suggestions, advice, or reasoning
6. NEVER use words like: "recall", "remember", "might", "could", "should", "need to", "try", "maybe"
7. Just describe the raw sensory information in the present moment - NOTHING ELSE
```

**3. Added Memory Recall Example (lines 3390-3393)**

```python
Question: "I try to remember my best friend"
✓ GOOD: "You pause and close your eyes, concentrating. Your brow furrows slightly as you think."
✗ BAD: "As you delve into the recesses of your memory, a name and a face begin to coalesce. The first name, 'Mila', emerges from your thoughts." ❌ (Memory content - internal voice's job!)
✗ BAD: "You recall your best friend Mila from the rave scene." ❌ (Memory content - internal voice's job!)
```

**4. Added Forbidden Memory Phrases (lines 3400-3405)**

```python
❌ "emerges from your thoughts" (Memory - internal voice!)
❌ "surfaces" (Memory - internal voice!)
❌ "coalesces" (Memory - internal voice!)
❌ "a name and face" (Memory content - internal voice!)
❌ "delve into" (Memory - internal voice!)
❌ "recesses of your memory" (Memory - internal voice!)
❌ "check if" (Advice!)
```

### Part 2: Internal Voice (Inquiry Internal Voice)

**5. Updated Availability Guidance for Internal Voice (lines 3123-3131)**

**EXIST (Memory accessible):**
```python
availability_section = f"""
**AVAILABILITY:** The thing EXISTS and is accessible.
- REVEAL THE ACTUAL MEMORY CONTENT with specific details (names, faces, places, events)
- This is YOUR JOB - the perceptual description only shows physical thinking, YOU reveal what's discovered
- Example: "Mila! That's her name. We met at the rave scene in 1993. She was the one who made it all unforgettable. I can still hear her voice, vivid and clear."
"""
```

**6. Added Division of Labor Note (lines 3160-3163)**

```python
**CRITICAL: DIVISION OF LABOR WITH PERCEPTUAL DESCRIPTION**
- PERCEPTUAL shows: Physical actions (closing eyes, pausing, concentrating)
- YOU reveal: Mental content (what's discovered, recalled, realized)
- For memory recall: PERCEPTUAL shows thinking, YOU reveal what's remembered!
```

**7. Updated Memory Recall Example (lines 3194-3198)**

```python
Action: "I try to remember my best friend"
✓ GOOD: "Mila! That's her name. We met at the rave scene in 1993 - she was the one who made it all unforgettable. I can still hear her voice, vivid and clear. We could try to find her again."
✗ BAD: "We've done this before, right? Why can't we just remember?" ❌ (Generic! Reveal the actual memory!)
```

## Expected Output Now

**Good Output:**
```
PERCEPTUAL:
"You pause and close your eyes, concentrating. Your brow furrows slightly as you think."

INTERNAL VOICE:
"Mila. That's her name. We met at the rave scene in 1993. She was the one who made 
it all unforgettable. We were always so much more passionate when we had someone to 
share our dreams with."
```

**Separation:**
- Perceptual: ONLY physical act of thinking ✓
- Internal Voice: Memory content and discoveries ✓

## Key Principles

### Perceptual Description Should:
✓ Describe body language (closing eyes, pausing, concentrating)
✓ Describe visible actions (looking around, scanning)
✓ Describe sensory perceptions (seeing, hearing, smelling)
✓ Describe lack of perception (don't see, can't hear)

### Perceptual Description Should NEVER:
✗ Reveal memory content
✗ Describe discoveries or realizations
✗ Give factual knowledge
✗ Provide suggestions or advice
✗ Use phrases like "emerges", "surfaces", "coalesces"
✗ Mention names, faces, or specific memories

### Internal Voice Should:
✓ Reveal memory content
✓ Provide factual knowledge
✓ Share discoveries and realizations
✓ Give reasoning and understanding

## Result

✅ **Perceptual = Physical actions only** - Body language, sensory perceptions  
✅ **Internal Voice = Mental content** - Memories, knowledge, discoveries  
✅ **Clear separation** - No overlap between the two  
✅ **Proper narrative flow** - Perceptual shows what you do, internal voice shows what you know  

The perceptual description now correctly describes ONLY the physical act of thinking, while the internal voice reveals what is actually discovered!
