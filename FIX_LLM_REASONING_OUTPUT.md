# Fix LLM Reasoning Output Issue

## Problem Identified

The LLM was outputting **reasoning/thinking text** along with the actual content for:
- **Perceptual descriptions** (inquiry responses)
- **Internal voice** (inquiry thoughts)

But **scene descriptions** were working perfectly - just clean output, no reasoning.

## Root Cause

1. **Reasoning model behavior**: The model (likely DeepSeek R1 or similar) wants to "think out loud"
2. **Long, complex prompts**: The perceptual/internal voice prompts were very detailed, triggering reasoning mode
3. **Missing explicit anti-reasoning instructions**: Scene description worked because it was simpler and more direct

## Solution Applied

### 1. Added Explicit Anti-Reasoning Instructions

**Both prompts now end with:**
```
**CRITICAL OUTPUT INSTRUCTION:**
DO NOT include ANY reasoning, thinking, analysis, or explanation.
DO NOT say things like "Let me think..." or "Based on..." or "Considering..."
Return ONLY the final [description/thought] text - nothing else.
```

### 2. Added Strong System Messages

**Perceptual Description (Line 4374):**
```python
{"role": "system", "content": "You generate perceptual descriptions. Output ONLY the final description text. DO NOT include reasoning, thinking, or explanations. Just output the description directly."}
```

**Internal Voice (Line 3792):**
```python
{"role": "system", "content": "You ARE the character's internal voice. Output ONLY the character's actual thought in first-person plural ('we', 'us', 'our'). DO NOT include reasoning, analysis, alternatives, or meta-commentary. Just output the raw thought directly - 1-2 sentences maximum."}
```

### 3. Changed Message Structure

**Before:**
```python
messages=[{"role": "user", "content": prompt}]
```

**After:**
```python
messages=[
    {"role": "system", "content": "Strong anti-reasoning instruction"},
    {"role": "user", "content": prompt}
]
```

## Changes Made

### File: `agents/narrator_agent.py`

**Perceptual Description (`generate_inquiry_response`):**
- **Lines 4363-4366**: Added CRITICAL OUTPUT INSTRUCTION section
- **Lines 4373-4376**: Added system message with anti-reasoning directive

**Internal Voice (`generate_inquiry_internal_voice`):**
- **Lines 3780-3784**: Added CRITICAL OUTPUT INSTRUCTION section
- **Lines 3791-3794**: Added system message with anti-reasoning directive

## Why This Works

1. **System message sets the role**: Tells the LLM it's a generator, not a reasoner
2. **Explicit prohibition**: Lists specific phrases to avoid ("Let me think...", "Based on...", etc.)
3. **Clear output format**: States exactly what to return ("ONLY the final text - nothing else")
4. **Matches scene description pattern**: Scene description already had simple, direct instructions

## Expected Result

**Before (with reasoning):**
```
Let me analyze this inquiry. Based on the scene description, I can see that...
[reasoning text]
[reasoning text]
Final answer: You see a worn notebook on the table.
```

**After (clean output):**
```
You see a worn notebook on the table.
```

## Testing Recommendations

1. Test various inquiry types:
   - Simple questions ("What do I see?")
   - Complex questions ("What's written in the notebook?")
   - Memory recall questions ("Who is my best friend?")

2. Verify output is clean:
   - No "Let me think..." or "Based on..."
   - No "Considering..." or "This matches..."
   - No alternatives like "Or perhaps..." or "Better option:"
   - Just the final perceptual description or internal voice

3. Check both systems:
   - Perceptual description should be 2-4 sentences of sensory perception
   - Internal voice should be 1-2 sentences of character thought

## Result

Both perceptual description and internal voice should now produce **clean, direct output** just like scene description - no reasoning, no meta-commentary, just the final result.
