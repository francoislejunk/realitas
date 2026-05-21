# MiniMax M2 Accommodation Strategy

## Overview

Refactored the system to properly handle MiniMax M2's reasoning model architecture, which puts thinking process in `message.reasoning` and often leaves `message.content` empty.

**Provider:** Using `novita/fp8` for optimized MiniMax M2 inference (configured in `openrouter_config.py`)

## Solution: Smart Reasoning Parser

### What It Does

The `_extract_response_content()` method now intelligently parses the reasoning field to extract the actual answer while filtering out meta-commentary and thinking process.

### Algorithm

1. **Split reasoning into lines**
2. **Group lines into content blocks** (separated by blank lines)
3. **Filter out meta-commentary** using pattern matching
4. **Extract substantial content** (lines > 20 chars without meta-patterns)
5. **Return the last valid block** (usually the conclusion/answer)

### Meta-Commentary Patterns Filtered

The parser skips lines containing:
- "The user asks:", "The user is asking"
- "I need to", "Let me", "Let's"
- "Alright,", "Okay,", "First,", "Next,"
- "Since the rules", "Looking at"
- "We need to", "The question:", "The task:"
- "I'll", "I should", "I must"
- "Based on the context"
- "probably", "might be", "perhaps", "alternatively"

### Example Processing

**Input (from reasoning field):**
```
The user asks: "What is a Heim?"

Alright, let's tackle this query. First, I'll check the character's inventory.
Next, I'll scan the room for any documents.

A Heim is a Civic Retention Facility located at Warschauer Straße 47, 
where non-compliant donors are reclassified into long-term storage.
```

**Output (extracted):**
```
A Heim is a Civic Retention Facility located at Warschauer Straße 47, 
where non-compliant donors are reclassified into long-term storage.
```

## Implementation Details

### File Modified
`agents/narrator_agent.py` - `_extract_response_content()` method (lines 87-197)

### Key Features

1. **Preserves content field priority**
   - Always checks `message.content` first
   - Only parses reasoning if content is empty

2. **Block-based parsing**
   - Groups consecutive lines into content blocks
   - Separates blocks by blank lines
   - Evaluates each block independently

3. **Pattern-based filtering**
   - Checks each line against meta-indicators
   - Skips lines with thinking process markers
   - Only keeps substantial content (> 20 chars)

4. **Smart candidate selection**
   - Collects all valid content blocks
   - Filters blocks < 30 chars (too short to be answers)
   - Returns the **last** valid block (conclusion)

5. **Fallback handling**
   - Returns `None` if no valid candidates found
   - Triggers existing fallback responses in calling methods

### Debug Output

```
[DEBUG EXTRACT] content exists: False, reasoning exists: True
[MINIMAX M2] Extracting answer from reasoning field...
[MINIMAX M2] Extracted answer: A Heim is a Civic Retention Facility...
```

Or if extraction fails:
```
[MINIMAX M2] Could not extract clean answer from reasoning - using fallback
```

## Benefits

✅ **No model switching needed** - Works with MiniMax M2 as-is
✅ **Automatic extraction** - Intelligently finds the answer
✅ **Filters meta-commentary** - Removes thinking process
✅ **Preserves fallbacks** - Returns None if extraction fails
✅ **Debug visibility** - Shows what's being extracted

## Limitations

⚠️ **Not perfect** - May occasionally extract wrong content
⚠️ **Heuristic-based** - Relies on pattern matching
⚠️ **May miss answers** - If answer contains meta-patterns
⚠️ **Requires tuning** - May need to adjust patterns over time

## Testing Checklist

After this refactor, verify:
- [ ] Ask "What is a Heim?" → Get clean answer
- [ ] Ask "What is a Zed?" → Get clean answer
- [ ] Check internal voice → No meta-commentary
- [ ] Check perceptual descriptions → No analysis
- [ ] Monitor `[MINIMAX M2]` debug logs
- [ ] Verify fallback triggers when extraction fails

## Future Improvements

### Pattern Refinement
Add more meta-indicators as they're discovered:
```python
meta_indicators = [
    # ... existing patterns ...
    "This means",
    "In other words",
    "To summarize",
    "The answer is",  # Sometimes precedes actual answer
]
```

### Confidence Scoring
Rate extracted candidates by quality:
```python
def score_candidate(text):
    score = len(text)  # Longer is better
    if text.startswith('"'):  # Quoted text is good
        score += 50
    if any(meta in text.lower() for meta in meta_indicators):
        score -= 100  # Penalize meta-commentary
    return score
```

### Answer Markers
Look for explicit answer markers:
```python
if "The answer:" in reasoning:
    return reasoning.split("The answer:")[1].strip()
```

### Multi-pass Extraction
Try multiple strategies:
1. Look for explicit markers
2. Parse by blocks (current approach)
3. Take last N sentences
4. Use regex patterns

## Rollback Plan

If this approach causes issues:

1. **Revert to simple fallback:**
```python
if hasattr(message, 'reasoning') and message.reasoning:
    return message.reasoning.strip()  # Return raw reasoning
```

2. **Or return None to always use fallbacks:**
```python
if hasattr(message, 'reasoning') and message.reasoning:
    return None  # Always trigger fallback responses
```

## Related Files

- `agents/narrator_agent.py` - Main extraction logic
- `INQUIRY_OUTPUT_FIX.md` - Original inquiry fix documentation
- `MINIMAX_M2_REASONING_LEAK_FIX.md` - Previous fix attempt
- `URGENT_MODEL_SWITCH_NEEDED.md` - Alternative solution (not used)

## Key Insight

**MiniMax M2's reasoning field contains both thinking AND answer** - we just need to parse it intelligently to extract the answer portion while discarding the thinking portion.

This is more robust than trying to force the model to change its behavior via prompts, which it consistently ignores.
