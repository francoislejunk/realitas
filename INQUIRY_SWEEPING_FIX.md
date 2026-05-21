# Inquiry Sweeping Classification Fix

## The Problem

Memory recall inquiries like "I try to remember my bestfriend" were being classified as **SWEEPING** (complex, multi-step) instead of **ATOMIC** (simple, single-step), causing an unnecessary diegetic pause.

**Bad Output:**
```
[DIEGETIC] Analysis complete:
  Scope: sweeping
  Reasoning: The action involves a complex, multi-step process of recalling memories, 
             which cannot be executed in a simple 3-second or 3-minute action.
  Estimated Steps: 1
  Needs Breakdown: True
[DIEGETIC] SWEEPING INTENT DETECTED - Generating pause...

══════════════════════════════════════════════════════════════════════
💭 INTERNAL VOICE
══════════════════════════════════════════════════════════════════════
We need to be careful with this memory...
══════════════════════════════════════════════════════════════════════

What do you do?
[DIEGETIC] Looping back for next user input
```

**Issue:** The inquiry never actually executes - it just generates a pause and loops back!

## Why This Happened

The diegetic transition system's `analyze_intent_scope()` method only checked for **questions** (ending with "?" or starting with question words), but NOT for **inquiry actions** (mental recall attempts like "I try to remember").

**Code Flow:**
```
1. User: "I try to remember my bestfriend"
2. Diegetic system checks: Is it a question? NO (no "?", doesn't start with "what/where/etc")
3. Diegetic system checks: Is it combat? NO
4. Diegetic system checks: Is it simple action? NO (doesn't match "open", "close", etc)
5. Default: Must be SWEEPING (complex) ❌ WRONG!
6. Generate diegetic pause and loop back
7. Inquiry never executes
```

## The Solution

Added inquiry action patterns to the diegetic system so memory recall is recognized as ATOMIC.

**File:** `diegetic_transition_system.py` (lines 78-104)

### Changes Made

**1. Added Inquiry Patterns (lines 78-83)**

```python
# Memory recall/inquiry patterns (mental actions, not physical)
inquiry_patterns = [
    "try to remember", "try to recall", "trying to remember", "trying to recall",
    "think about", "think back", "reminisce", "recall", "remember",
    "search my memory", "dig through"
]
```

**2. Check for Inquiry Actions (lines 94-95)**

```python
# Check if this is a memory recall/inquiry action
is_inquiry_action = any(pattern in user_input_lower for pattern in inquiry_patterns)
```

**3. Bypass Diegetic Pause for Inquiries (lines 97-104)**

```python
if is_question or is_inquiry_action:
    # This is an inquiry/mental action - return atomic to bypass diegetic pause
    return {
        "scope": IntentScope.ATOMIC,
        "reasoning": "This is a question/inquiry/mental action, not a physical action",
        "estimated_steps": 0,
        "needs_breakdown": False
    }
```

## Correct Flow Now

```
1. User: "I try to remember my bestfriend"
2. Diegetic system checks: Is it a question? NO
3. Diegetic system checks: Is it inquiry action? YES (contains "try to remember") ✓
4. Return ATOMIC scope
5. Bypass diegetic pause
6. Execute inquiry immediately ✓
7. Generate perceptual description (physical thinking)
8. Generate internal voice (memory content)
9. Advance time by 3 seconds
10. Continue
```

## Expected Output Now

```
[DIEGETIC] Analysis complete:
  Scope: atomic
  Reasoning: This is a question/inquiry/mental action, not a physical action
  Estimated Steps: 0
  Needs Breakdown: False

PERCEPTUAL:
"You pause and close your eyes, concentrating. Your brow furrows slightly as you think."

INTERNAL VOICE:
"Mila! That's her name. We met at the rave scene in 1993..."

⏰ Time advanced: +3s | Clock: Day 1, 9:00:03 AM
```

## Inquiry Patterns Recognized

The following patterns now bypass the diegetic pause:

**Memory Recall:**
- "try to remember"
- "try to recall"
- "trying to remember"
- "trying to recall"
- "remember"
- "recall"

**Mental Actions:**
- "think about"
- "think back"
- "reminisce"
- "search my memory"
- "dig through"

## Result

✅ **Inquiries classified as ATOMIC** - No diegetic pause  
✅ **Immediate execution** - No loop back  
✅ **Proper flow** - Perceptual → Internal Voice → Time advancement  
✅ **Consistent with 3TU** - Mental actions are 3-SECOND (atomic)  

Memory recall inquiries now execute immediately without unnecessary pauses!
