# Internal Voice as Flexible Helpful Assistant

## The Problem

The internal voice was too rigid and structured:
```
Action: "I try to remember my best friend's name"
Output: "We've done this before, right? Why can't we just remember?"
```

This is **worthless** - it doesn't provide the actual information!

## The Solution

**Internal Voice = Helpful Personal Assistant**

Think of it like a personal ChatGPT that:
- States relevant facts
- Recalls memories
- Suggests actions
- Makes observations
- Provides reasoning

**NOT** a rigid structure of "memory + suggestion". Include whatever is **RELEVANT**.

## The New Approach

### Flexible Components (All Optional)

✓ **Facts** - If there are relevant facts to state  
✓ **Memories** - If there's something to recall  
✓ **Suggestions** - If there's a clear action to recommend  
✓ **Observations** - If there's something important to note  
✓ **Reasoning** - If explanation helps  

**Key:** Not everything needs to appear. Just what's useful.

## Examples

### Before (Rigid & Unhelpful)
```
Action: "I try to remember my best friend's name"
❌ "We've done this before, right? Why can't we just remember?"
```

### After (Flexible & Helpful)
```
Action: "I try to remember my best friend's name"
✅ "Her name is Sarah. We've known her since high school. She lives 
across town now, but we still meet up every few weeks at that coffee 
shop on Main Street."
```

### More Examples

**Question: "Where am I?"** (in your apartment)
```
✅ "This is our apartment. We're home. The vinyl collection is ours, 
the answering machine has been blinking for days."
```

**Action: "I look around the bar"**
```
✅ "This is Joe's Bar - we've been here a few times. The bartender 
is Mike, he knows us. Those guys in the corner look like trouble though."
```

**Action: "I examine the device"**
```
✅ "It's some kind of radio transmitter. Old Soviet design, probably 
from the 70s. We could try tuning it to see if it still works."
```

**Question: "How do I get downtown?"**
```
✅ "The U-Bahn station is two blocks north. Line 3 runs downtown 
every 15 minutes. Faster than walking, and it's getting late."
```

## Key Changes

### 1. Removed Rigid Structure

**Before:**
- MUST include memory statement
- MUST include suggestion
- Exactly 2-3 sentences

**After:**
- Include what's relevant
- 2-5 sentences (whatever is needed)
- Natural conversational flow

### 2. Increased Flexibility

**Before:**
```
**STRUCTURE:**
[Memory/Knowledge statement] + [Suggestion/Advice]
```

**After:**
```
**FLEXIBILITY:** Include whatever is RELEVANT:
- Facts (if there are relevant facts)
- Memories (if there's something to recall)
- Suggestions (if there's a clear action)
- Observations (if something important)
- Reasoning (if explanation helps)
```

### 3. Removed Hard-Coded Truncation

**Before:**
```python
max_tokens=200
# Hard-coded sentence limit in display
```

**After:**
```python
max_tokens=300  # Allow longer responses
return internal_voice  # Return full response, no truncation
```

### 4. Updated Tone

**Before:** Structured, formulaic  
**After:** Helpful, informative, practical - like a knowledgeable friend

## Implementation

### File Modified: `agents/narrator_agent.py`

**Method: `generate_inquiry_internal_voice()`** (lines 3070-3148)

**Changes:**
1. Rewrote prompt to emphasize flexibility
2. Removed rigid structure requirements
3. Added examples showing helpful information provision
4. Increased max_tokens from 200 to 300
5. Removed truncation - returns full response
6. Updated system message to emphasize "helpful personal assistant"

**New Prompt Structure:**
```python
**YOUR ROLE:** You are the character's internal voice - a helpful assistant that:
- States relevant facts and knowledge
- Recalls memories when relevant
- Suggests actions when appropriate
- Makes observations when useful
- Provides context and reasoning

**FLEXIBILITY:** Include whatever is RELEVANT. Not everything needs to appear.
```

## Two Internal Voice Methods

### 1. `generate_inquiry_internal_voice()` ✅ UPDATED
- Used for inquiry/question responses
- Now flexible and helpful
- Provides relevant information

### 2. `generate_internal_voice()` ⚠️ DIFFERENT PURPOSE
- Used for general ROAM mode actions
- Has different structure (personality-driven, failure tracking)
- Focuses on subtle reactions and observations
- 1-2 sentences maximum
- NOT the same as inquiry internal voice

**Note:** These serve different purposes and should remain separate.

## Result

✅ **Helpful Information** - Provides actual facts and memories  
✅ **Flexible Structure** - Includes what's relevant, not rigid format  
✅ **Natural Flow** - Conversational, like a knowledgeable friend  
✅ **No Truncation** - Full response displayed  
✅ **Longer Responses** - 2-5 sentences when needed  

The internal voice now acts like a **personal assistant** that helps the player by providing relevant information, not just following a rigid structure.
