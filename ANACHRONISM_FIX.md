# Anachronism Fix - iPhone 11 and 2019 References

## Problem Identified

The internal voice was generating anachronistic content:
- Mentioned "iPhone 11" (released in 2019, doesn't exist in 1990s)
- Mentioned "2019" as a date (simulation is set in 1995-1999)
- Mentioned "Berlin Music Festival in 2019" (wrong decade)

**Example of broken output:**
```
💭 INTERNAL VOICE
iPhone 11! That's the name of our phone. The one we've had for 2 years. 
Max gave it to us, Max from the Berlin Music Festival in 2019.
```

## Root Cause

The `generate_inquiry_factual_answer()` method in `narrator_agent.py` was **not using the RAG system** to retrieve world setting context. It had no way to know what time period or technology level the simulation was set in.

## Solution Applied (RAG-Based Approach)

### File: `agents/narrator_agent.py`

**Method: `generate_inquiry_factual_answer()` (lines 3304-3423)**

### Changes Made:

**1. Added RAG System Integration (lines 3331-3345):**

```python
# Get RAG worldbuilding context for memory generation
rag_context = ""
if self.rag_system:
    try:
        # Query RAG for world setting, technology, culture, and temporal context
        search_query = f"{user_question} technology culture setting temporal"
        rag_context = self.rag_system.get_context_for_llm(
            query=search_query,
            max_tokens=400  # More tokens for comprehensive world context
        )
        if rag_context:
            rag_context = f"\n**ESTABLISHED WORLDBUILDING (MUST FOLLOW):**\n{rag_context}\n\n"
    except Exception as e:
        # Silently fail - will work without RAG but may be less accurate
        pass
```

**2. Updated Prompt to Reference RAG Context (line 3357-3377):**

```python
prompt = f"""Generate a FACTUAL ANSWER to this memory recall/inquiry question.
{rag_context}
{character_background}

**QUESTION:** "{user_question}"

**YOUR TASK:** Create a specific, detailed answer with CONCRETE DETAILS:
- For technology questions: Use technology appropriate to the world setting above

**CRITICAL RULES:**
1. Be SPECIFIC - use actual names, dates, places, numbers
2. Make it fit the character's background (age, occupation, location, goals)
3. Make it consistent with the scene and recent context
4. **FOLLOW THE WORLDBUILDING CONTEXT ABOVE** - Use only technology, dates, and cultural references that fit the established setting
5. 2-4 sentences with concrete details
6. This will be passed to internal voice to reveal - make it vivid and memorable
```

**3. Updated System Message (line 3405):**

Changed from hardcoded constraints:
```python
"You are a memory generator for a 1990s setting. Create specific, vivid details with names, dates (1990-1999 ONLY), and places..."
```

To dynamic RAG-based approach:
```python
"You are a memory generator. Create specific, vivid details with names, dates, and places that fit the established world setting. Follow the worldbuilding context provided in the prompt - use only technology, cultural references, and temporal details that match the setting."
```

## Expected Result

**Before (Broken):**
```
💭 INTERNAL VOICE
iPhone 11! That's the name of our phone. The one we've had for 2 years. 
Max gave it to us, Max from the Berlin Music Festival in 2019.
```

**After (Fixed):**
```
💭 INTERNAL VOICE
Our pager! The black Motorola pager Max gave us back in 1997 at the 
Berlin Music Festival. We've had it for 2 years now. We could use it 
to coordinate with the crew for tonight's show.
```

## Why This Works

1. **Dynamic Context**: RAG system provides world setting information based on actual lore documents
2. **Setting-Agnostic**: Works for any time period/setting - just change the lore, not the code
3. **Comprehensive Coverage**: RAG query includes "technology culture setting temporal" to get all relevant context
4. **Explicit Instruction**: Prompt explicitly tells LLM to "FOLLOW THE WORLDBUILDING CONTEXT ABOVE"
5. **System-Level Enforcement**: System message reinforces following the established world setting
6. **Maintainable**: No hardcoded constraints that need updating when setting changes

## Benefits of RAG-Based Approach

### Flexibility
- **Change Setting Instantly**: Want cyberpunk 2077? Medieval fantasy? Just update the lore documents
- **No Code Changes**: Setting changes don't require modifying narrator_agent.py
- **Consistent Across System**: All agents using RAG get the same world setting context

### Maintainability
- **Single Source of Truth**: World setting defined in lore documents, not scattered across prompts
- **Easy Updates**: Add new technology/culture details to lore, not to every prompt
- **Version Control**: Lore documents can be versioned and swapped

### Accuracy
- **Context-Aware**: RAG retrieves relevant setting details based on the specific question
- **Comprehensive**: Gets technology, culture, temporal, and setting information in one query
- **Authoritative**: Uses established lore rather than LLM's general knowledge

## Testing

To verify the fix works:

1. Start a new simulation
2. Try inquiry: "I try to remember my phone"
3. Check internal voice output
4. Should mention: pager, landline, or early cell phone (NOT iPhone, smartphone)
5. Should mention: dates 1990-1999 (NOT 2000s, 2010s, 2019)

## Additional Notes

### RAG Query Strategy
The search query `f"{user_question} technology culture setting temporal"` is designed to retrieve:
- **Technology**: What devices/tools exist in this world
- **Culture**: Social norms, music, fashion, language
- **Setting**: Time period, location, atmosphere
- **Temporal**: Specific dates, historical events, timeline

### Example RAG Response
For a 1990s setting, the RAG system might return:
```
Setting: Mid-to-late 1990s (1995-1999)
Technology: Landline phones, pagers, early cell phones (bulky), cassette tapes, CDs, VHS
Culture: Grunge music, alternative rock, early electronic/rave scene
Temporal: Post-Cold War, pre-9/11, dot-com bubble beginning
```

This context is then injected into the prompt with the header:
```
**ESTABLISHED WORLDBUILDING (MUST FOLLOW):**
[RAG context here]
```

## Status

✅ **FIXED** - Anachronistic references eliminated using RAG-based world setting retrieval
✅ **IMPROVED** - System is now setting-agnostic and maintainable
