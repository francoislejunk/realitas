# Inquiry System None Handling Fix

## Problem

The inquiry system was crashing with `AttributeError: 'NoneType' object has no attribute 'lower'` when `factual_answer` was `None`. This occurred when:

1. LLM failed to generate a factual answer for memory recall inquiries
2. The code attempted to process the None value without checking
3. Multiple functions (`extract_inquiry_keywords`, `check_duplicate_inquiry_memory`) didn't handle None inputs

## Root Cause

The `generate_inquiry_factual_answer()` method in NarratorAgent was returning `None` instead of the fallback string `"No specific memory available."` when the LLM call failed. This caused downstream crashes in:

1. `inquiry_helpers.extract_inquiry_keywords()` - line 35: `text.lower().split()`
2. `inquiry_helpers.check_duplicate_inquiry_memory()` - line 281: `extract_inquiry_keywords(answer)`
3. Memory creation code in main.py - line 5847

## Fixes Applied

### 1. Added None Check in `extract_inquiry_keywords()`

**File:** `inquiry_helpers.py` (lines 34-36)

```python
# Handle None text
if not text:
    return []
```

This prevents the crash when text is None by returning an empty list.

### 2. Added None Check in `check_duplicate_inquiry_memory()`

**File:** `inquiry_helpers.py` (lines 283-285)

```python
# Handle None answer
if not answer:
    return None
```

This prevents processing when answer is None and returns None (no duplicate found).

### 3. Added Conditional Memory Creation in Main Loop

**File:** `MAIN/redesigned_main.py` (lines 5844-5856)

```python
# Check for duplicate before creating memory (only if we have a factual answer)
if factual_answer:
    existing = check_duplicate_inquiry_memory(
        question=user_input,
        answer=factual_answer,
        key_memories_system=key_memories
    )
else:
    existing = None
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}[INQUIRY] No factual answer generated - skipping memory creation{Color.RESET}")

if factual_answer and not existing:
    # Create memory...
```

Only creates memories when factual_answer exists.

### 4. Added Conditional Narrative Event

**File:** `MAIN/redesigned_main.py` (lines 5879-5888)

```python
# Add to narrative context (only if we have factual answer)
if factual_answer:
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.MEMORY_CREATION,
        narrative_text=f"Scene {scene_number}: {actor.sheet.name} learned: {user_input}",
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="insightful",
        scene_context=scene_description
    )
```

Only adds narrative event when factual_answer exists.

### 5. Added Debug Output for Factual Answer Generation

**File:** `agents/narrator_agent.py` (lines 3880-3903)

Added debug logging to diagnose LLM failures:
- `[FACTUAL ANSWER] Calling LLM with model: {model}` - Before LLM call
- `[FACTUAL ANSWER] Generated: {answer}...` - On success
- `[FACTUAL ANSWER] Empty response from LLM` - On empty response
- `⚠️ Factual answer generation failed: {error}` - On exception

## Impact

### Before Fix
- System crashed when LLM failed to generate factual answer
- No graceful degradation
- User experience interrupted

### After Fix
- System gracefully handles None factual answers
- Skips memory creation when no answer available
- Continues simulation without crash
- Debug output helps diagnose LLM issues

## Testing

To verify the fix:

1. Run simulation with inquiry action (e.g., "I try to recall my best friend")
2. If LLM fails, system should:
   - Display warning: `[INQUIRY] No factual answer generated - skipping memory creation`
   - Continue without crash
   - Show debug output indicating LLM failure
3. If LLM succeeds, system should:
   - Display: `[FACTUAL ANSWER] Generated: {answer}...`
   - Create memory normally
   - Continue as expected

## Related Issue

The underlying issue is that **MiniMax M2 model** may be failing to respond to certain prompts. The debug output will help identify:
- Whether the model is timing out
- Whether the response is empty
- What specific errors are occurring

This fix ensures the system remains stable while we investigate MiniMax compatibility.
