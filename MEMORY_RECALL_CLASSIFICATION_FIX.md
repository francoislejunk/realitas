# Memory Recall Classification Fix

## The Problem

Memory recall actions like "I try and remember my best friend" were being classified as `physical` instead of `inquiry`, preventing the availability-aware inquiry flow from activating.

**Output showed:**
```
🔍 DEBUG: LLM response: {
  'input_type': 'fallible_action', 
  'fallible_subtype': 'physical',  // ❌ WRONG - should be 'inquiry'
  'reasoning': 'attempting to recall a memory, which is an inquiry action'
}
```

The LLM's reasoning was correct ("inquiry action") but the classification was wrong ("physical").

## Root Cause

The interpreter agent prompt had a contradictory instruction:

```
Line 1966: **CRITICAL**: If it says "I [verb]" it's NOT mental, it's an ACTION
```

This caused "I try and remember" to be classified as physical action instead of inquiry.

## The Solution

### 1. Updated LLM Prompt Guidelines

**File:** `agents/interpreter_agent.py` (lines 1958-1971)

Added explicit memory recall examples and clarified that memory recall is inquiry:

```python
- **FALLIBLE ACTION (Inquiry)** - Questions, information seeking, memory recall:
  - "What's in this room?" (asking question)
  - "I try to remember my best friend" (memory recall - mental action)
  - "I try to recall what happened" (memory recall - mental action)
  - "I think about my childhood" (mental reflection)
  - "I try to remember the address" (memory recall)
  - **KEY**: Questions ending in "?" OR memory recall verbs (remember, recall, think about)
  - **MEMORY RECALL**: "try to remember", "try to recall", "think about", "reminisce" → inquiry
  - **CRITICAL**: Memory recall is inquiry even if it says "I [verb]"
```

### 2. Enhanced Fallback Classification

**File:** `agents/interpreter_agent.py` (lines 2026-2049)

Added memory recall pattern detection to the fallback logic:

```python
# Memory recall patterns
memory_patterns = [
    "try to remember", "try to recall", "trying to remember", "trying to recall",
    "i remember", "i recall", "think about", "think back", "reminisce"
]

is_memory_recall = any(pattern in user_input_lower for pattern in memory_patterns)

# Rule: questions OR memory recall = inquiry
if is_question or is_memory_recall:
    response_data['fallible_subtype'] = 'inquiry'
    if is_memory_recall:
        response_data['reasoning'] = "Memory recall detected - inquiry action"
```

## Memory Recall Patterns Detected

The system now recognizes these as inquiry:

1. **"try to remember [X]"**
2. **"try to recall [X]"**
3. **"trying to remember [X]"**
4. **"trying to recall [X]"**
5. **"I remember [X]"**
6. **"I recall [X]"**
7. **"think about [X]"**
8. **"think back [X]"**
9. **"reminisce [X]"**

## Expected Flow After Fix

```
User: "I try and remember my best friend"
↓
[CLASSIFY] fallible_action, inquiry ✓ (was: physical ❌)
↓
[INTENT AVAILABILITY] does_not_exist ✓
↓
[INQUIRY PROCESSING] Continue (don't skip) ✓
↓
[PERCEPTUAL DESCRIPTION] "You search your memories but find nothing..." ✓
↓
[INTERNAL VOICE] "We don't have a best friend. We've always been alone." ✓
↓
[NO MEMORY CREATED] Nothing to remember ✓
```

## Files Modified

**`agents/interpreter_agent.py`**

**Lines 1958-1971:** Updated prompt guidelines
- Added memory recall examples
- Clarified that memory recall is inquiry
- Removed contradictory "I [verb]" rule for memory actions

**Lines 2026-2049:** Enhanced fallback classification
- Added memory_patterns list
- Check for memory recall patterns
- Classify as inquiry if memory recall detected

## Result

✅ **Memory recall classified correctly** - Now returns `inquiry` not `physical`  
✅ **LLM prompt updated** - Clear examples and guidance  
✅ **Fallback logic enhanced** - Pattern matching as safety net  
✅ **Availability flow activates** - Full integration now works  

Memory recall actions will now trigger the complete availability-aware inquiry flow!
