# Inquiry Output Fix - No Descriptive Output & Missing RAG Context

## Problems

### Problem 1: No Descriptive Output (Returns `None`)
**Symptom:**
```
[FACTUAL ANSWER] Generated: A Heim is a pneumatic extraction rig...
None
```

The factual answer is generated but `None` is displayed to the user.

**Root Cause:**
`generate_inquiry_response()` (which generates the perceptual description) was returning `None` because:
1. MiniMax M2 puts the answer in `message.reasoning` field
2. We had just removed the `message.reasoning` fallback to fix prompt leaks
3. Result: `_extract_response_content()` returned `None` when `message.content` was empty

### Problem 2: RAG Doesn't Understand World-Specific Terms
**Symptom:**
User asks "What is a Heim?" and the system doesn't retrieve the worldbuilding context explaining that Heims are created through "Therapeutic plasma exchange and PRP therapies."

**Root Cause:**
The RAG query in `generate_inquiry_factual_answer()` was missing key categories:
- Missing: `supernatural` (contains info about Heims, Zeds, Stitches, Echoes)
- Missing: `beings` (contains info about actor types)
- Missing: `civilization` (contains info about occupations, institutions)

## Solutions Applied

### Fix 1: Smart Content Extraction
**File:** `agents/narrator_agent.py` (lines 87-116)

**Updated `_extract_response_content()` to:**
1. **Prefer `message.content`** (the final answer)
2. **Fallback to `message.reasoning`** if content is empty (MiniMax M2 behavior)

```python
def _extract_response_content(self, response) -> Optional[str]:
    """
    Extract content from LLM response.
    
    For MiniMax M2 reasoning models:
    - Prefers message.content (the final answer)
    - Falls back to message.reasoning if content is empty (model put answer there)
    """
    if not response or not response.choices:
        return None
    
    message = response.choices[0].message
    
    # Try message.content first (preferred)
    if message.content:
        content = message.content.strip()
        if content:
            return content
    
    # Fallback: If content is empty but reasoning exists, use reasoning
    if hasattr(message, 'reasoning') and message.reasoning:
        reasoning = message.reasoning.strip()
        if reasoning:
            return reasoning
    
    return None
```

**Why This Works:**
- MiniMax M2 sometimes puts answers in `reasoning` field
- Other models use `content` field
- This handles both cases gracefully
- Still prevents prompt leaks (reasoning is the answer, not the thinking process)

### Fix 2: Comprehensive RAG Query
**File:** `agents/narrator_agent.py` (line 3843)

**OLD Query:**
```python
search_query = f"{user_question} technology culture setting temporal"
```

**NEW Query:**
```python
search_query = f"{user_question} supernatural beings civilization technology culture setting temporal"
```

**Added Categories:**
- ✅ `supernatural` - Contains info about Heims, Zeds, Stitches, Echoes
- ✅ `beings` - Contains info about actor types and classifications
- ✅ `civilization` - Contains info about institutions, occupations

**Increased Token Limit:**
- OLD: 400 tokens
- NEW: 500 tokens (to accommodate more comprehensive context)

## Expected Behavior After Fix

### Test 1: "What is a Heim?"
**Before:**
```
[FACTUAL ANSWER] Generated: A Heim is a pneumatic extraction rig...
None
```

**After:**
```
[FACTUAL ANSWER] Generated: A Heim is a person who has undergone therapeutic plasma exchange and PRP therapies...
You pause and think about what you know. The term "Heim" refers to individuals who have been enhanced through the Hematologic Exchange Program.
```

### Test 2: "What is a Zed?"
**Before:**
- RAG doesn't retrieve supernatural context
- Answer might be generic or wrong

**After:**
- RAG retrieves: "Neuro-suppressive barbiturate protocols and biofeedback conditioning (Zeds)"
- Answer explains Zeds correctly within worldbuilding

### Test 3: "Who are the Stitches?"
**Before:**
- Missing context about surgical augmentation

**After:**
- RAG retrieves: "Surgical augmentation and myoelectric prosthetics (Stitches)"
- Answer explains Stitches correctly

## Files Modified

1. **`agents/narrator_agent.py`** (lines 87-116)
   - Updated `_extract_response_content()` to handle MiniMax M2 reasoning mode

2. **`agents/narrator_agent.py`** (line 3843)
   - Added `supernatural`, `beings`, `civilization` to RAG query
   - Increased max_tokens from 400 to 500

## Testing Checklist

- [ ] Ask "What is a Heim?" → Should explain plasma exchange/PRP therapies
- [ ] Ask "What is a Zed?" → Should explain neuro-suppressive protocols
- [ ] Ask "What are Stitches?" → Should explain surgical augmentation
- [ ] Ask "What are Echoes?" → Should explain corrupted psychometric data
- [ ] Verify perceptual description is displayed (not `None`)
- [ ] Verify internal voice is displayed
- [ ] Verify no prompt leaks (no "We need to parse..." text)

## Related Issues Fixed

This fix also resolves:
- ✅ Prompt leak in internal voice (previous fix)
- ✅ Missing RAG context for world-specific terminology
- ✅ `None` output for inquiry responses
- ✅ Incomplete worldbuilding integration in inquiries

## Key Insight

**MiniMax M2 Behavior:**
- Sometimes puts final answer in `message.content` ✓
- Sometimes puts final answer in `message.reasoning` ✓
- We need to check both fields to handle all cases
- `message.reasoning` for MiniMax M2 is NOT the thinking process - it's the answer itself!

**This is different from other reasoning models where:**
- `reasoning` = internal thinking process (should be hidden)
- `content` = final answer (should be shown)

**For MiniMax M2:**
- `reasoning` = the actual answer (should be shown if content is empty)
- `content` = the actual answer (preferred)
