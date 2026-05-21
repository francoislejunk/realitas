# URGENT: MiniMax M2 Model Switch Needed

## Critical Problem

**MiniMax M2 completely ignores system prompt instructions** and always puts its thinking process in the `reasoning` field with nothing in `content`.

### Evidence:
```
[DEBUG EXTRACT] content exists: False, reasoning exists: True
[DEBUG EXTRACT] reasoning preview: The user asks: "Generate a FACTUAL ANSWER..."
[WARNING] Content empty - attempting to extract answer from reasoning field
[ERROR] Reasoning field contains thinking process, not answer - returning fallback
```

**Output shown to user:**
```
The user asks:
"Generate a FACTUAL ANSWER to this memory recall/inquiry question.

Alright, let's tackle this query. The user is asking, "What is a Heim?"...
First, I'll check the character's inventory...
Next, I'll scan the room...
```

## Root Cause

**MiniMax M2's reasoning mode is designed to expose thinking** - it's a feature, not a bug. The model is working as intended, but it's incompatible with our use case where we need clean, direct outputs.

## Immediate Fix Applied

Added meta-commentary filter to `_extract_response_content()`:
- Detects patterns like "The user asks:", "I need to", "Let me", etc.
- Returns `None` when thinking process detected
- Triggers fallback responses (generic text)

**This is a band-aid, not a solution.**

## Recommended Solution: Switch Models

### Current Configuration
**File:** `openrouter_config.py` (line 23)
```python
"narration": "minimax/minimax-m2",  # NarratorAgent - core immersion
```

### Recommended Alternatives

#### Option 1: Claude 3.5 Sonnet (Best for narrative)
```python
"narration": "anthropic/claude-3.5-sonnet",
```
**Pros:**
- Excellent at following instructions
- Clean, direct outputs
- Strong narrative generation
- No reasoning leaks

**Cons:**
- More expensive than MiniMax M2
- Slower response time

#### Option 2: GPT-4 Turbo (Balanced)
```python
"narration": "openai/gpt-4-turbo",
```
**Pros:**
- Reliable instruction following
- Fast response time
- Good narrative quality
- Widely tested

**Cons:**
- Moderate cost
- Less creative than Claude

#### Option 3: Gemini Pro 1.5 (Budget-friendly)
```python
"narration": "google/gemini-pro-1.5",
```
**Pros:**
- Lower cost
- Good instruction following
- Fast response time

**Cons:**
- Less consistent than Claude/GPT-4
- May need more prompt tuning

## How to Switch Models

### Step 1: Edit openrouter_config.py
```python
ROLE_MODELS = {
    # TIER 1: Critical narrative agents
    "narration": "anthropic/claude-3.5-sonnet",  # Changed from minimax/minimax-m2
    "spark_generation": "anthropic/claude-3.5-sonnet",
    "decision_making": "anthropic/claude-3.5-sonnet",
    # ... rest of config
}
```

### Step 2: Test the change
```bash
python MAIN/redesigned_main.py
```

Ask: "What is a Heim?"

### Step 3: Verify output
Should see:
```
[DEBUG EXTRACT] content exists: True, reasoning exists: False
[FACTUAL ANSWER] Generated: A Heim is a Civic Retention Facility...
```

**No more thinking process!**

## Why MiniMax M2 Doesn't Work

MiniMax M2 is a **reasoning model** designed for:
- Math problems
- Code generation
- Complex analysis
- Showing work/thinking

It's **NOT designed for**:
- Clean narrative output
- Immersive storytelling
- Direct answers without explanation

The `reasoning` field is **intentionally exposed** to show how the model thinks. This is great for debugging AI reasoning, but terrible for user-facing narrative.

## Impact of Not Switching

If we keep MiniMax M2:
- ❌ Users see thinking process instead of answers
- ❌ Immersion broken by meta-commentary
- ❌ Internal voice shows "We need to write..." instead of actual thoughts
- ❌ Perceptual descriptions show analysis instead of sensory details
- ❌ Every inquiry shows "The user asks..." preamble

## Impact of Switching

With Claude/GPT-4/Gemini:
- ✅ Clean, direct answers
- ✅ Immersive narrative
- ✅ Proper internal voice
- ✅ Pure perceptual descriptions
- ✅ No meta-commentary

## Cost Comparison (per 1M tokens)

| Model | Input | Output | Quality |
|-------|-------|--------|---------|
| MiniMax M2 | $0.15 | $0.60 | ❌ Exposes thinking |
| Claude 3.5 Sonnet | $3.00 | $15.00 | ✅ Clean output |
| GPT-4 Turbo | $10.00 | $30.00 | ✅ Clean output |
| Gemini Pro 1.5 | $1.25 | $5.00 | ✅ Clean output |

**Recommendation:** Start with **Claude 3.5 Sonnet** for best quality, or **Gemini Pro 1.5** for budget-conscious option.

## Testing Checklist After Switch

- [ ] Ask "What is a Heim?" → Get clean answer
- [ ] Check internal voice → No "We need to write..." text
- [ ] Check perceptual descriptions → No analysis
- [ ] Verify debug logs show `content exists: True`
- [ ] Confirm no `[ERROR] Reasoning field contains thinking process`
- [ ] Test multiple inquiries for consistency

## Rollback Plan

If new model has issues:
1. Edit `openrouter_config.py`
2. Change back to `"minimax/minimax-m2"`
3. Restart simulation

## Bottom Line

**MiniMax M2 is fundamentally incompatible with our narrative system.** The meta-commentary filter is a temporary workaround, but the only real solution is to switch to a model designed for clean, direct output.

**Action Required:** Update `openrouter_config.py` line 23 to use Claude 3.5 Sonnet or another recommended model.
