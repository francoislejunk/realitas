# Phone Call Fix: Prompt-First Approach

## Philosophy

**Fix at the source, not with post-processing.**

Instead of complex regex patterns to strip physical actions, we strengthen the DeciderAgent prompt to **mandate dialogue-only format** for phone calls. Post-processing is only a minimal safety net.

---

## DeciderAgent Prompt Changes

### Location: `agents/decider_agent.py` lines 531-557

### New Prompt Structure:

```
🚨🚨🚨 **ABSOLUTE REQUIREMENT: PHONE CALL - DIALOGUE ONLY** 🚨🚨🚨

**YOU ARE ON A PHONE CALL. YOU CANNOT DO PHYSICAL ACTIONS.**

**MANDATORY FORMAT FOR narrative_description:**
- MUST start with: "says '[exact dialogue in quotes]'"
- MUST end with: "in a [tone] voice"
- NOTHING ELSE IS ALLOWED

**CORRECT EXAMPLES:**
✅ "says 'Hey, I was thinking about that project we discussed' in a thoughtful voice"
✅ "says 'I'd love to help you with that!' in an enthusiastic voice"
✅ "says 'Can we meet up later to talk about this?' in a casual voice"

**ABSOLUTELY FORBIDDEN - DO NOT USE:**
❌ "walks towards..." (YOU CANNOT WALK ON A PHONE CALL)
❌ "approaches..." (YOU CANNOT APPROACH ON A PHONE CALL)
❌ "gestures..." (THEY CANNOT SEE YOU)
❌ "smiles..." (THEY CANNOT SEE YOU)
❌ "picks up..." (NOT RELEVANT TO PHONE CONVERSATION)
❌ "while [any physical action]" (NO PHYSICAL ACTIONS ALLOWED)
❌ "with [any expression]" (THEY CANNOT SEE YOUR FACE)

**IF YOU GENERATE ANYTHING OTHER THAN DIALOGUE, THE SYSTEM WILL FAIL.**
**ONLY DIALOGUE. ONLY VOICE TONE. NOTHING ELSE.**
```

### Dialogue Format Section (lines 715-732):

```
📞 **IF THIS IS A PHONE CALL (see warning above):**
- ONLY FORMAT: 'says "[exact words in quotes]" in a [tone] voice'
- EXAMPLES:
  ✅ 'says "Hey, you got a minute? I wanted to talk about that mixtape project" in an enthusiastic voice'
  ✅ 'says "Back off before this gets ugly" in a threatening tone'
  ✅ 'says "I've been thinking about your offer" in a thoughtful voice'
- FORBIDDEN: ANY physical actions, movements, gestures, or expressions

👥 **IF THIS IS IN-PERSON:**
- FORMAT: 'says "[exact words in quotes]" while [physical action/expression]'
- EXAMPLES:
  ✅ 'says "Hey, you got a minute?" while approaching {reactor.sheet.name} with a friendly smile'
  ✅ 'says "Back off before this gets ugly" while stepping forward aggressively'

**NON-DIALOGUE ACTIONS (IN-PERSON ONLY):**
- 'attempts to lunge at {reactor.sheet.name} with a dagger'
- 'tries to dodge {reactor.sheet.name}'s incoming strike'
- PHONE CALLS: Non-dialogue actions are IMPOSSIBLE - you can ONLY speak
```

---

## Minimal Post-Processing Safety Net

### Location: `agents/narrator_agent.py` lines 4212-4217

**Old approach:** Complex regex patterns to strip physical actions, detect verbs, etc.

**New approach:** Simple validation check

```python
# Fix 2: Phone calls - minimal safety net (prompt should handle this)
if is_remote and remote_type == "phone_call":
    # Safety check: if narrative doesn't contain "says" with dialogue, it's broken
    if not re.search(r'says\s+["\']', narrative, re.IGNORECASE):
        print(f"{Color.WARNING}[POST-PROCESS] Phone call missing dialogue format: '{narrative}' - DeciderAgent prompt failed!{Color.RESET}")
        narrative = f"{actor_name} speaks over the phone."
```

**What it does:**
- Checks if narrative has `says "..."` or `says '...'`
- If missing → prompt failed, use placeholder
- If present → trust the prompt worked correctly

**What it doesn't do:**
- ❌ No complex regex to strip physical actions
- ❌ No verb detection
- ❌ No pattern matching for "while/with"
- ❌ No tone inference from dialogue content

---

## Benefits

### 1. **Simpler Code**
- Removed 30+ lines of complex regex patterns
- Removed physical action verb list
- Removed tone inference logic

### 2. **Clearer Intent**
- Prompt explicitly shows what's allowed vs forbidden
- Uses emojis and formatting for visibility
- Provides concrete examples of correct/wrong format

### 3. **Better Debugging**
- Warning message shows when prompt fails
- Can see exact broken narrative in logs
- Easy to identify if LLM is ignoring instructions

### 4. **More Maintainable**
- Changes to format only need prompt updates
- No need to maintain regex pattern lists
- Post-processing is minimal and obvious

---

## Testing

### Expected Behavior:

**Input from DeciderAgent (phone call):**
```
"says 'Hey, I was thinking about that project' in a thoughtful voice"
```

**After post-processing:**
```
"Jonas Keller says 'Hey, I was thinking about that project' in a thoughtful voice"
```
(Only actor name added)

### Failure Case:

**Input from DeciderAgent (phone call - BROKEN):**
```
"walks towards the notebook on the crate"
```

**After post-processing:**
```
"Jonas Keller speaks over the phone."
```
(Replaced with placeholder + warning logged)

---

## Files Modified

1. **agents/decider_agent.py**
   - Lines 531-557: Strengthened remote encounter prompt
   - Lines 715-732: Updated dialogue format examples

2. **agents/narrator_agent.py**
   - Lines 4212-4217: Simplified to minimal safety check
   - Removed: Complex regex patterns, verb detection, tone inference

---

## Philosophy Summary

**Before:** "The LLM will ignore prompts, so we need complex post-processing to fix everything"

**After:** "Make the prompt crystal clear with examples, then trust it. Only catch catastrophic failures."

This is cleaner, more maintainable, and easier to debug.
