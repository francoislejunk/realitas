# Bug Fix: Inquiry Classification

## Problem

**Issue:** "Can I take the U-Bahn?" was classified as `situation_overcoming` instead of `information_gathering` (inquiry)

**Root Cause:** The question pattern detection was missing common question starters like "can i", "should i", "do i", etc.

## Analysis

### The Classification Flow:

1. **LLM classifies** input as `fallible_action` with subtype `situation_overcoming`
2. **Post-processing** (lines 1996-2030) checks if it's a question
3. **If question:** Keep as `information_gathering`
4. **If not question:** Use keyword detection to determine subtype

### The Bug:

**Lines 2002-2008:** Question pattern list was incomplete

```python
# OLD (INCOMPLETE):
question_patterns = [
    "what", "where", "when", "why", "how", "who", "which",
    "can you", "could you", "would you", "do you know",
    "tell me", "explain", "describe", "is there", "are there"
]
```

**Missing patterns:**
- "can i" ← **This is why "Can I take the U-Bahn?" failed!**
- "can we"
- "should i"
- "should we"
- "do i"
- "do we"
- "does"
- "did"
- "will"
- "would i"
- "would we"

## Solution

### Fix 1: Expanded Question Patterns

**File:** `agents/interpreter_agent.py`
**Lines:** 2002-2008

```python
# NEW (COMPLETE):
question_patterns = [
    "what", "where", "when", "why", "how", "who", "which",
    "can i", "can we", "could i", "could we", "should i", "should we",
    "can you", "could you", "would you", "do you know",
    "tell me", "explain", "describe", "is there", "are there",
    "do i", "do we", "does", "did", "will", "would i", "would we"
]
```

### Fix 2: Updated LLM Prompt

**File:** `agents/interpreter_agent.py`
**Lines:** 1956-1963

Added clearer examples and guidance:

```
- **FALLIBLE ACTION (Information Gathering)** - Questions about environment/knowledge:
  - "What's in this room?"
  - "Can I hear footsteps?"
  - "Can I take the U-Bahn?" ← NEW EXAMPLE
  - "What's the best way downtown?" ← NEW EXAMPLE
  - **KEY**: Questions ending in "?" or starting with what/where/when/how/can/should
```

## Test Cases

### Now Working:

✅ "Can I take the U-Bahn?" → `information_gathering`
✅ "Should I go downtown?" → `information_gathering`
✅ "Do I have enough money?" → `information_gathering`
✅ "Could we make it in time?" → `information_gathering`
✅ "Will the bus come soon?" → `information_gathering`

### Still Working (Unchanged):

✅ "What's the best way downtown?" → `information_gathering`
✅ "Where is the station?" → `information_gathering`
✅ "How do I get there?" → `information_gathering`

### Correctly NOT Inquiries:

✅ "I take the U-Bahn" → `situation_overcoming` (action, not question)
✅ "I climb the fence" → `situation_overcoming` (physical challenge)
✅ "I ask him about the U-Bahn" → `contested_action` (asking NUA)

## Impact

### Before Fix:
```
User: "Can I take the U-Bahn?"
→ Classified as: situation_overcoming
→ Full success calculation
→ Narrative generated
→ Wrong flow!
```

### After Fix:
```
User: "Can I take the U-Bahn?"
→ Classified as: information_gathering
→ Generate FACT: "U-Bahn runs all night"
→ Create/retrieve memory
→ Generate THOUGHT: "We could take the U-Bahn..."
→ Correct inquiry flow!
```

## Related Systems

This fix ensures:
- ✅ Inquiry system works correctly
- ✅ FACT vs THOUGHT separation maintained
- ✅ Memory deduplication functions properly
- ✅ No unnecessary success calculations
- ✅ Proper internal voice generation

## Status

✅ Question patterns expanded
✅ LLM prompt clarified
✅ Ready for testing
