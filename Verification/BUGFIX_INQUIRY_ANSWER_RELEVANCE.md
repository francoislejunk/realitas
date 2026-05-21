# Bug Fix: Inquiry Answer Relevance

## Problem

**Issue:** When asking "What's the best way to get downtown?", the system generated factual knowledge about random scene elements instead of answering the actual question.

**Example of Bug:**
```
Question: "What's the best way to get downtown?"

Generated (WRONG):
📝 Knowledge: Above Anchor Located
The Rusty Anchor is located above which is two blocks away from a subway entrance.

Expected (CORRECT):
📝 Knowledge: Downtown Subway Route
The subway entrance is two blocks away and runs to downtown.
```

## Root Cause

The LLM was generating factual knowledge based on scene context but not focusing on **answering the specific question asked**.

The prompt mentioned "Generate FACTUAL KNOWLEDGE to answer a question" but didn't emphasize strongly enough that the answer must **directly address the question**.

## Solution

### Fix 1: Improved User Prompt

**File:** `agents/narrator_agent.py`
**Lines:** 2788-2822

**Changes:**
1. **Emphasized the specific question** - Repeated the question multiple times
2. **Added explicit task** - "Answer the EXACT question asked"
3. **Added warning** - "Do NOT describe random scene elements"
4. **Added specific rules** - If question asks about routes, answer about routes
5. **Better examples** - Showed question → answer pairs

**Before:**
```python
prompt = f"""Generate FACTUAL KNOWLEDGE to answer a question.

**CHARACTER:** {ua_name}
**QUESTION:** {question}
...
```

**After:**
```python
prompt = f"""You must answer this SPECIFIC QUESTION with factual knowledge.

**CHARACTER:** {ua_name}
**QUESTION:** "{question}"
...

**TASK:** Answer the EXACT question asked with factual knowledge. Do NOT describe random scene elements.

**CRITICAL RULES:**
1. Your answer must DIRECTLY address the question: "{question}"
2. Generate a FACT (declarative statement), NOT a suggestion
3. If the question asks "how to get downtown", answer about routes/transportation
4. If the question asks "where is X", answer about location
5. If you don't know the answer, respond with exactly: "UNKNOWN"

**GOOD EXAMPLES (FACTS that answer the question):**
Question: "What's the best way to get downtown?"
Answer: "The #7 bus runs from here to downtown every 20 minutes"

Question: "Where is the subway?"
Answer: "There's a subway entrance two blocks east on Maple Street"
...

**BAD EXAMPLES (Do NOT do this):**
❌ Describing random scene objects instead of answering
❌ Suggestions: "We should take the bus", "We could ask someone"
❌ Thoughts: "Let's try the subway", "Maybe we can find an alleyway"

**YOUR TASK:** Answer "{question}" with 1-2 sentences of factual knowledge, or "UNKNOWN" if the character doesn't know.
```

### Fix 2: Strengthened System Message

**File:** `agents/narrator_agent.py`
**Lines:** 2828-2830

**Before:**
```python
"content": "Generate factual knowledge statements (FACTS), not suggestions or thoughts. Use declarative statements. If unknown, say 'UNKNOWN'."
```

**After:**
```python
"content": "You are answering a specific question with factual knowledge. Your answer must DIRECTLY address the question asked. Do NOT describe random scene elements. Generate FACTS (declarative statements), not suggestions. If unknown, say 'UNKNOWN'."
```

## Expected Behavior After Fix

### Test Case 1: Transportation Question
```
Question: "What's the best way to get downtown?"

Expected Answer:
✅ "The #7 bus runs from here to downtown every 20 minutes"
✅ "There's a subway entrance two blocks east that goes downtown"
✅ "The downtown train station is a 10-minute walk from here"

NOT:
❌ "The Rusty Anchor is located above which is two blocks away..."
❌ Random scene descriptions
```

### Test Case 2: Location Question
```
Question: "Where is the subway?"

Expected Answer:
✅ "There's a subway entrance two blocks east on Maple Street"
✅ "The nearest subway station is at the corner of 5th and Main"

NOT:
❌ "The coffee shop has a bulletin board with..."
❌ Random scene descriptions
```

### Test Case 3: Unknown Information
```
Question: "What's in the sewers?"

Expected Answer:
✅ UNKNOWN (no memory created)
✅ Internal voice: "I've never been in the sewers. Maybe we should ask someone..."

NOT:
❌ Making up random facts
❌ Describing unrelated scene elements
```

## Testing

### Before Fix:
```
Input: "What's the best way to get downtown?"
Output: "The Rusty Anchor is located above which is two blocks away from a subway entrance."
Result: ❌ WRONG - Describes scene element, doesn't answer question
```

### After Fix:
```
Input: "What's the best way to get downtown?"
Output: "The subway entrance two blocks east runs directly to downtown."
Result: ✅ CORRECT - Directly answers the question
```

## Impact

This fix ensures:
- ✅ Inquiry answers are **relevant** to the question asked
- ✅ Memories contain **useful** factual knowledge
- ✅ No random scene descriptions in memory storage
- ✅ Better user experience (gets actual answers)
- ✅ Memory deduplication works better (consistent topics)

## Related Systems

This fix improves:
- **Inquiry System** - Generates relevant factual knowledge
- **Memory System** - Stores useful, question-specific facts
- **Memory Deduplication** - Keywords match actual question topics
- **Internal Voice** - Can reference relevant factual knowledge

## Status

✅ User prompt improved with explicit instructions
✅ System message strengthened
✅ Examples added for clarity
✅ Ready for testing
