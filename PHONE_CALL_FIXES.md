# Phone Call System Fixes

## Issues Identified

### Issue 1: Physical Gestures During Phone Calls
**Problem:** NUA dialogue during phone calls included physical descriptions like "while leaning in with an enthusiastic expression, hands gesturing to emphasize points"

**Root Cause:** The DeciderAgent was not receiving explicit constraints about remote encounters, so it generated physical actions that are impossible during phone calls.

### Issue 2: Missing NUA Name in Dialogue
**Problem:** Dialogue appeared as "says '[words]' while..." without the actor name at the beginning, making it unclear who was speaking.

**Root Cause:** The NarratorAgent dialogue format examples showed the old format "'[words]' Name says" which doesn't put the actor name first.

---

## Solutions Implemented

### Fix 1: DeciderAgent Remote Encounter Constraints

**File:** `agents/decider_agent.py`

**Changes:**
1. Added explicit remote encounter context section (lines 524-542)
2. Checks `context_guidance.get('is_remote_encounter')` 
3. Displays prominent warning: "🚨 **CRITICAL: PHONE CALL - NO PHYSICAL PRESENCE** 🚨"
4. Lists forbidden words: "approach", "walk", "gesture", "lean", "touch", "hand", "facial expression", "eyes", "smile", "nod"
5. Provides correct format: `"says '[words]' in a [tone] voice"`
6. Provides wrong format examples: `"says '[words]' while leaning in"`

**Integration:**
- Remote context is inserted into the main prompt at line 568
- Appears prominently before character decision-making section
- Uses the `is_remote_encounter`, `remote_encounter_type`, and `remote_constraint` fields from `context_guidance`

**Updated Dialogue Examples (lines 695-707):**
- Added separate formats for IN-PERSON vs PHONE CALLS
- IN-PERSON: `'says "[words]" while [physical action]'`
- PHONE: `'says "[words]" in a [tone] voice'` (NO physical actions!)
- Explicit note: "For phone calls: Physical actions are IMPOSSIBLE - use verbal actions only"

### Fix 2: NarratorAgent Name-First Format

**File:** `agents/narrator_agent.py`

**Changes:**

**A. Strengthened Phone Call Constraints (lines 4112-4120):**
- Added 🚨 emoji for visibility
- Changed "FORBIDDEN" to "ABSOLUTELY FORBIDDEN"
- Added comprehensive list of forbidden words
- Added explicit format examples:
  - CORRECT: `"{actor_name} says '[words]' in a [tone] voice"`
  - WRONG: `"says '[words]' while [any physical action]"`

**B. Fixed Dialogue Format Requirements (lines 4133-4147):**
- **NEW Rule #1:** "Actor name FIRST - ALWAYS start with {actor_name} at the beginning"
- **Updated Dialogue Format:**
  - CORRECT: `"{actor_name} says '[exact words]' [optional: while/with physical action]"`
  - Example: `"Eva says 'There's this underground rave tonight—you should come!' with her eyes bright with excitement."`
  - Example (phone): `"Marcus says 'I've been thinking about that project' in an enthusiastic voice."`
  - WRONG: `"'[words]' {actor_name} says"` (actor name must come FIRST!)
  - WRONG: `"says '[words]' while..."` (missing actor name at start!)

---

## Expected Behavior After Fixes

### Before (WRONG):
```
says "I've been thinking, Alex, we should collaborate on an upcoming rave event. 
I've got some great ideas for the music lineup and the setup. What do you think 
about helping to organize it together?" while leaning in with an enthusiastic 
expression, hands gesturing to emphasize points
```

**Problems:**
- ❌ No actor name (who is speaking?)
- ❌ Physical gestures during phone call (impossible!)

### After (CORRECT):
```
Jonas Keller says "I've been thinking, Alex, we should collaborate on an upcoming 
rave event. I've got some great ideas for the music lineup and the setup. What do 
you think about helping to organize it together?" in an enthusiastic voice
```

**Fixed:**
- ✅ Actor name appears first (Jonas Keller)
- ✅ No physical descriptions during phone call
- ✅ Only auditory description ("in an enthusiastic voice")

---

## Technical Flow

### How Remote Encounter Context is Passed

**1. Main Loop (redesigned_main.py lines 8896-8922):**
```python
if encounter_checker.current_context.is_remote_encounter:
    context_guidance['is_remote_encounter'] = True
    context_guidance['remote_encounter_type'] = 'phone_call'
    context_guidance['remote_constraint'] = "CRITICAL CONSTRAINT: This is a PHONE CALL..."
    context_guidance['context_summary'] = "[PHONE CALL - NO PHYSICAL PRESENCE]\n..."
```

**2. DeciderAgent (decider_agent.py lines 524-542):**
```python
if context_guidance and context_guidance.get('is_remote_encounter'):
    remote_context = """
    🚨 **CRITICAL: PHONE CALL - NO PHYSICAL PRESENCE** 🚨
    - You are NOT physically present with {reactor.sheet.name}
    - FORBIDDEN WORDS: "approach", "walk", "gesture", "lean", etc.
    """
```

**3. NarratorAgent (narrator_agent.py lines 4110-4120):**
```python
if is_remote_encounter and remote_encounter_type == "phone_call":
    remote_context = """
    **🚨 CRITICAL CONTEXT: PHONE CONVERSATION 🚨**
    - ABSOLUTELY FORBIDDEN: "approaches", "walks", "gestures", "lean", etc.
    - CORRECT FORMAT: "{actor_name} says '[words]' in a [tone] voice"
    """
```

---

## Testing Checklist

Test phone call scenarios to verify:

- [ ] NUA dialogue starts with actor name (e.g., "Jonas Keller says...")
- [ ] No physical descriptions during phone calls (no "leaning", "gesturing", "smiling")
- [ ] Only auditory descriptions (voice tone, background sounds)
- [ ] Actor name is always clear and visible
- [ ] Dialogue format is consistent: "{Name} says '[words]' in a [tone] voice"

---

## Files Modified

1. **agents/decider_agent.py**
   - Lines 524-542: Added remote encounter context section
   - Line 568: Integrated remote context into prompt
   - Lines 695-707: Updated dialogue format examples for phone calls

2. **agents/narrator_agent.py**
   - Lines 4112-4120: Strengthened phone call constraints
   - Lines 4133-4147: Fixed dialogue format to put actor name first
   - Lines 4182-4245: **NEW** - Added post-processing safety layer

---

## Post-Processing Safety Layer

**File:** `agents/narrator_agent.py` (lines 4190-4245)

Added `_fix_narrative_issues()` method that runs AFTER LLM generation to catch and fix issues:

### Fix 1: Missing Actor Name
- Detects narratives starting with "says" or dialogue quotes
- Extracts dialogue and rebuilds with actor name first
- Example: `"says 'Hello'"` → `"Jonas Keller says 'Hello'"`

### Fix 2: Physical Actions During Phone Calls
Uses regex patterns to remove forbidden physical descriptions:
- `while leaning/gesturing/showing/approaching/walking`
- `with enthusiastic/friendly expression`
- `with his/her/their eyes/hands/face`
- `hands gesturing`
- `leaning in`
- `showing sketches/notes/notebook`

### Fix 3: Add Voice Tone
If phone call narrative lacks tone description, adds appropriate tone:
- Excited words → "in an enthusiastic voice"
- Thoughtful words → "in a thoughtful voice"
- Default → "over the phone"

### Why This Is Necessary
Even with strong prompt constraints, LLMs sometimes ignore instructions. The post-processing layer provides a **safety net** that guarantees correct output format regardless of LLM compliance.

---

## Status

✅ **COMPLETE** - Both issues addressed with:
1. ✅ Strengthened DeciderAgent prompts
2. ✅ Strengthened NarratorAgent prompts  
3. ✅ Post-processing safety layer for guaranteed compliance
