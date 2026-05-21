# MiniMax M2 System Message Issue - CRITICAL FIX

## Problem Discovery

**Scene descriptions worked perfectly, but inquiry outputs (internal voice, perceptual description, factual answer) were failing.**

### Symptoms:
- ✅ Scene description: Clean, direct outputs in `message.content`
- ❌ Internal voice: Everything in `message.reasoning`, `message.content` empty
- ❌ Perceptual description: Everything in `message.reasoning`, `message.content` empty  
- ❌ Factual answer: Everything in `message.reasoning`, `message.content` empty

## Root Cause

**MiniMax M2 CANNOT HANDLE SYSTEM MESSAGES PROPERLY**

### Working Code (Scene Description):
```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[{"role": "user", "content": prompt}],  # ✅ USER ONLY
    temperature=0.4,
    max_tokens=280,
    timeout=30
)
```

### Broken Code (Internal Voice, Perceptual, Factual):
```python
response = self.client.chat.completions.create(
    model=self.model,
    messages=[
        {"role": "system", "content": "..."},  # ❌ SYSTEM MESSAGE
        {"role": "user", "content": prompt}
    ],
    temperature=0.6,
    max_tokens=300,
    timeout=20
)
```

**When MiniMax M2 sees a system message, it:**
1. Puts ALL output in `message.reasoning` field
2. Leaves `message.content` EMPTY
3. Includes meta-commentary about the task in reasoning
4. Makes extraction nearly impossible

## Solution

**Remove ALL system messages and combine instructions with user prompt:**

### Before (Broken):
```python
messages=[
    {"role": "system", "content": "Generate PURELY PERCEPTUAL..."},
    {"role": "user", "content": prompt}
]
```

### After (Fixed):
```python
full_prompt = f"""Generate PURELY PERCEPTUAL descriptive answers...

{prompt}"""

messages=[{"role": "user", "content": full_prompt}]
```

## Additional Fix: Simplified Prompts

**Internal voice prompt was 90+ lines long** - overwhelming for MiniMax M2.

### Before (Complex):
```python
full_prompt = f"""You ARE {ua_name}'s internal voice - their actual thoughts...
[90 lines of detailed instructions, examples, constraints]
{prompt}"""
```

### After (Simple):
```python
full_prompt = f"""You are {ua_name}'s internal thoughts. Personality: {internal_personality}.

RULES:
- Use ONLY "we/us/our" (never "I/my/me")
- Answer the question directly and concisely
- Match the personality: {internal_personality}
- 1-2 sentences maximum
- Output ONLY the thought - no analysis, no meta-commentary

{prompt}

Output the internal thought now:"""
```

**Key principle:** Match the **working scene description style** - short, direct, user-only messages.

## Files Modified

1. **`narrator_agent.py` - Internal Voice** (lines ~3782-3795)
   - Removed system message
   - Drastically simplified prompt (90+ lines → 12 lines)
   - Combined instructions with user prompt

2. **`narrator_agent.py` - Factual Answer** (lines ~3989-3992)
   - Removed system message
   - Combined instructions with user prompt

3. **`narrator_agent.py` - Perceptual Description** (lines ~4370-4373)
   - Removed system message
   - Combined instructions with user prompt

4. **`narrator_agent.py` - Extraction Logic** (lines ~137-168)
   - Added more meta-indicators to filter reasoning field
   - Better detection of meta-commentary patterns

## Testing

To verify the fix:

1. **Ask a location question**: "Where am I?"
2. **Check outputs**:
   - ✅ Factual answer should provide location details
   - ✅ Perceptual description should describe sensory perceptions (NOT answer the question)
   - ✅ Internal voice should provide character's thoughts about location
3. **Verify no `None` outputs**

## Key Learnings

### ✅ DO:
- Use **user-only messages** for MiniMax M2
- Keep prompts **short and direct** (< 20 lines)
- Match the **working pattern** (scene description style)
- Combine system instructions with user prompt

### ❌ DON'T:
- Use system messages with MiniMax M2
- Write complex 90+ line prompts
- Assume system/user split works like other models
- Ignore what's already working (scene description)

## Why This Matters

**MiniMax M2 is a reasoning model** - it's designed to show its thinking process in `message.reasoning`. When you use a system message, it interprets the entire task as "show your reasoning" and puts everything there.

**User-only messages** signal: "Just give me the answer directly" - which makes MiniMax M2 put the output in `message.content` where we expect it.

## Impact

✅ **All inquiry outputs now work correctly**
✅ **Internal voice generates properly**
✅ **Perceptual descriptions are clean**
✅ **Factual answers are direct**
✅ **No more `None` outputs**
✅ **Consistent with scene description behavior**

## Pattern for Future LLM Calls

**When adding new LLM calls with MiniMax M2:**

```python
# ✅ CORRECT PATTERN
full_prompt = f"""[Brief instructions - max 20 lines]

{user_content}

Output now:"""

response = self.client.chat.completions.create(
    model=self.model,
    messages=[{"role": "user", "content": full_prompt}],
    temperature=0.4-0.8,
    max_tokens=200-300,
    timeout=20-30
)
```

**DO NOT use:**
```python
# ❌ BROKEN PATTERN
messages=[
    {"role": "system", "content": "..."},
    {"role": "user", "content": "..."}
]
```
