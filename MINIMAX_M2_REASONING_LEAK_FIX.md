# MiniMax M2 Reasoning Leak Fix

## Problem

MiniMax M2 was outputting its **thinking process** instead of the **final answer**:

```
[DEBUG EXTRACT] content exists: False, reasoning exists: True
[DEBUG EXTRACT] reasoning preview: Okay, the user is asking about the definition of "Heim"...
[WARNING] Using reasoning as fallback - content was empty
```

**Output shown to user:**
```
I need to carefully analyze the context and generate a response that follows the strict guidelines. Let me break this down:

1. **The Question**: "What is a Heim?" - This is asking for information...
2. **Current Scene**: I'm in a cramped BSU legal office...
[... entire thinking process exposed ...]
```

## Root Cause

MiniMax M2 reasoning model behavior:
- Puts **thinking process** in `message.reasoning` field
- Puts **nothing** in `message.content` field
- Our fallback was returning the thinking process to users

## Solution

Added explicit instructions to **all system prompts** to output the final answer directly without including the thinking process.

### Changes Made

#### 1. Factual Answer Generation
**File:** `agents/narrator_agent.py` (line 3927)

**Added to system message:**
```python
"CRITICAL: Output ONLY the final answer directly - do not include your thinking process, analysis, or reasoning. Just provide the factual answer immediately."
```

#### 2. Perceptual Description Generation  
**File:** `agents/narrator_agent.py` (line 4306)

**Added to system message:**
```python
"CRITICAL: Output the narrative directly - do not include your thinking process or analysis."
```

#### 3. Internal Voice Generation
**File:** `agents/narrator_agent.py` (line 3711)

**Added to system message:**
```python
"OUTPUT ONLY THE RAW THOUGHT DIRECTLY - no meta-commentary, no analysis, no alternatives, no questions about whether it matches personality, no thinking process about how to respond. Just output the character's actual thought immediately."
```

## How It Works

### Before Fix:
1. User asks: "What is a Heim?"
2. MiniMax M2 thinks: "Okay, let me analyze this question..."
3. MiniMax M2 puts thinking in `reasoning`, nothing in `content`
4. We return `reasoning` → User sees thinking process ❌

### After Fix:
1. User asks: "What is a Heim?"
2. System prompt: "Output ONLY the final answer directly"
3. MiniMax M2 puts answer in `content` (hopefully)
4. We return `content` → User sees answer ✓

## Fallback Strategy

The fallback to `message.reasoning` is **still in place** because:
- Some calls might still put the answer there
- Better to show something than nothing
- Debug logs will show when fallback is used

**Debug output helps us monitor:**
```
[DEBUG EXTRACT] content exists: True/False, reasoning exists: True/False
[DEBUG EXTRACT] content preview: ...
[DEBUG EXTRACT] reasoning preview: ...
[WARNING] Using reasoning as fallback - content was empty
```

## Expected Behavior After Fix

### Test 1: "What is a Heim?"
**Before:**
```
I need to carefully analyze the context... [thinking process]
```

**After:**
```
You pause and concentrate. You recall that a Heim is a Civic Retention Facility where non-compliant donors are reclassified into long-term storage.
```

### Test 2: Internal Voice
**Before:**
```
This is a complex request. We need to respond as Lina's internal voice... [meta-analysis]
```

**After:**
```
We know what a Heim is. It's where they take people who don't comply. We've seen the files.
```

## Testing Checklist

After this fix, verify:
- [ ] Ask "What is a Heim?" → Get clean answer, no thinking process
- [ ] Ask "What is a Zed?" → Get clean answer, no meta-commentary  
- [ ] Check internal voice → No "We need to respond..." text
- [ ] Check perceptual descriptions → No analysis shown
- [ ] Monitor debug logs → See if `content` is now populated
- [ ] Check if `[WARNING] Using reasoning as fallback` still appears

## If Problem Persists

If MiniMax M2 **still** puts thinking in `reasoning` and nothing in `content`:

### Option A: Parse the reasoning field
Extract just the final answer from the thinking process:
```python
if "The answer:" in reasoning:
    return reasoning.split("The answer:")[1].strip()
```

### Option B: Switch models
Use a different model that properly separates thinking from output:
- `anthropic/claude-3.5-sonnet`
- `openai/gpt-4-turbo`
- `google/gemini-pro-1.5`

### Option C: Increase temperature
Higher temperature might make the model less "analytical":
```python
temperature=1.0  # More creative, less analytical
```

## Files Modified

1. **`agents/narrator_agent.py`** (line 3927)
   - Added "Output ONLY the final answer" to factual answer system message

2. **`agents/narrator_agent.py`** (line 4306)
   - Added "Output directly" to perceptual description system message

3. **`agents/narrator_agent.py`** (line 3711)
   - Added "OUTPUT ONLY THE RAW THOUGHT DIRECTLY" to internal voice system message

## Related Issues

This fix addresses:
- ✅ Reasoning process leaking to users
- ✅ Meta-commentary in internal voice
- ✅ Analysis text in perceptual descriptions
- ✅ "Let me break this down" type responses

## Key Insight

**MiniMax M2's reasoning field is NOT always the final answer** - sometimes it's the thinking process. We need to **explicitly instruct** the model to put the answer in `content` by telling it not to include its thinking process in the output.

This is different from other models where the separation is automatic.
