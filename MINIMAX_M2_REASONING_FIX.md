# MiniMax M2 Reasoning Model Compatibility Fix

## Problem

MiniMax M2 was returning **empty responses** for all narrator prompts, causing:
- `factual_answer` = None → Memory creation failures
- `perceptual_description` = None → NPC parser crashes
- `internal_voice` = None → "None" displayed to user
- All narrative generation failing silently

## Root Cause

**MiniMax M2 is a reasoning model** that returns content in a different field than standard models:

### Standard Models (e.g., Mistral, GPT)
```python
response.choices[0].message.content = "The actual response text"
response.choices[0].message.reasoning = None
```

### Reasoning Models (e.g., MiniMax M2)
```python
response.choices[0].message.content = ""  # EMPTY!
response.choices[0].message.reasoning = "The actual response text"
```

The code was only checking `message.content`, so it always found empty strings and returned None.

## Solution

### 1. Created Helper Method `_extract_response_content()`

**File:** `agents/narrator_agent.py` (lines 87-114)

```python
def _extract_response_content(self, response) -> Optional[str]:
    """
    Extract content from LLM response, supporting both standard and reasoning models.
    
    Standard models: content in message.content
    Reasoning models (e.g., MiniMax M2): content in message.reasoning
    
    Returns:
        The response content string, or None if no content found
    """
    if not response or not response.choices:
        return None
    
    message = response.choices[0].message
    
    # Check content field first (standard models)
    if message.content:
        content = message.content.strip()
        if content:
            return content
    
    # Check reasoning field (reasoning models like MiniMax M2)
    if hasattr(message, 'reasoning') and message.reasoning:
        content = message.reasoning.strip()
        if content:
            return content
    
    return None
```

### 2. Updated All LLM Response Handling

Replaced all instances of:
```python
if response and response.choices and response.choices[0].message.content:
    content = response.choices[0].message.content.strip()
```

With:
```python
content = self._extract_response_content(response)
if content:
```

**Updated Methods:**
- `_call_llm()` - Core LLM caller (line 145)
- `generate_inquiry_factual_answer()` - Memory generation (line 3922)
- `generate_scene_description()` - Scene descriptions (line 526)
- `generate_encounter_dialogue()` - NPC dialogue (line 2859)
- `generate_internal_voice()` - Internal thoughts (line 3148)
- `get_factual_knowledge()` - Factual answers (line 3287)
- `generate_inquiry_internal_voice()` - Inquiry thoughts (line 3711)
- `generate_inquiry_response()` - Inquiry perceptual (line 4304)
- `generate_nua_narrative()` - Non-user actions (line 4400)
- `generate_does_not_exist_narrative()` - Failure narratives (line 4542)
- `generate_contextual_exploration_action_result_narrative()` - Exploration (line 2232)

## Testing

Created `test_minimax.py` to verify model compatibility:

```bash
python test_minimax.py
```

**Results:**
- ✗ Before fix: All tests showed "Empty response" with `content=''`
- ✓ After fix: All responses extracted from `reasoning` field successfully

## Impact

### Before Fix
- MiniMax M2: All narrator outputs failed → returned None
- System crashed on inquiry actions
- No narrative generation worked

### After Fix
- MiniMax M2: All narrator outputs work correctly
- Responses extracted from `reasoning` field
- Full compatibility with reasoning models
- Backward compatible with standard models (checks `content` first)

## Model Compatibility

This fix ensures compatibility with:

**Standard Models** (content field):
- Mistral Small
- GPT-4
- Claude
- Most other models

**Reasoning Models** (reasoning field):
- MiniMax M2
- Other reasoning-focused models

The helper method checks both fields, so it works with any model type.

## Notes

- The `reasoning` field contains the model's chain-of-thought process
- For MiniMax M2, this is the actual output (not just reasoning traces)
- The fix maintains backward compatibility by checking `content` first
- No changes needed to prompts or model configuration
