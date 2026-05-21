# Inquiry System - Complete Fixes

## All Issues Fixed

### 1. ✅ Mental Action Formula - Using Standard UTAS Calculation
**Problem:** Mental actions used simplified formula instead of standard UTAS.

**Fixed:**
- Changed from `swiftness + spirit + serendipity` 
- To: `(smarts + skill + super + supplement + serendipity) - (stress + status + sympathy)`
- Uses `SFactorType.SMARTS` (not the non-existent SPIRIT)
- File: `inquiry_helpers.py` line 157

### 2. ✅ Narrator/Internal Voice Separation - Perceptions vs Suggestions
**Problem:** Narrator was providing suggestions and advice (internal voice's job).

**Fixed:**
- **Narrator:** ONLY describes present sensory perceptions
  - ✅ "You see...", "You hear...", "You don't recognize..."
  - ❌ NEVER: "You recall...", "You should...", "Maybe you..."
  
- **Internal Voice:** Recalls memories AND suggests actions
  - ✅ "We recall...", "We remember...", "We could...", "We should..."
  - Required structure: [Memory] + [Suggestion]

**Files Modified:**
- `agents/narrator_agent.py` - `generate_inquiry_response()` (lines 3169-3264)
- `agents/narrator_agent.py` - `generate_inquiry_internal_voice()` (lines 3033-3150)

### 3. ✅ Failed Inquiry Perceptions - No Suggestions
**Problem:** `process_failed_inquiry()` was generating suggestions in narrator text.

**Fixed:**
- Changed to ONLY describe lack of perception/knowledge
- ✅ "You try to focus. Nothing comes to mind. You don't know."
- ❌ NEVER: "You'd need to ask someone or check a map."

**File Modified:**
- `inquiry_helpers.py` - `process_failed_inquiry()` (lines 235-299)

### 4. ✅ Failed Inquiry Internal Voice - Always Triggers
**Problem:** When inquiry failed, internal voice wasn't generated.

**Fixed:**
- Added internal voice generation for failed inquiries
- Now shows both narrator (perceptions) AND internal voice (suggestions)
- Internal voice provides suggestions when knowledge is lacking

**File Modified:**
- `MAIN/redesigned_main.py` (lines 4752-4772)

### 5. ✅ AttributeError Fix - SFactorType.SPIRIT
**Problem:** Code tried to use non-existent `SFactorType.SPIRIT`.

**Fixed:**
- Changed to `SFactorType.SMARTS` (correct S-Factor for mental actions)
- Updated display to show "Smarts" instead of "Spirit"

**Files Modified:**
- `inquiry_helpers.py` line 157
- `MAIN/redesigned_main.py` line 4651

## Complete Flow Now

### Successful Inquiry:
```
📖 INQUIRY DETECTED
[Memory check - found!]

NARRATOR (Perceptions):
"You recall the U-Bahn station two blocks north. Line 3 runs downtown."

💭 INTERNAL VOICE (Memory + Suggestion):
"We remember Line 3 runs every 15 minutes. We could take that - it's faster than walking."

🔍 MEMORY UNCOVERED
[Memory details]
```

### Failed Inquiry:
```
📖 INQUIRY DETECTED
[No memory found - Rolling for success]

🎲 MENTAL ACTION ROLL
Smarts: 3 + Skill: 0 + Super: 0 + Supplement: 0 + Luck: -1
Stress: +2 + Status: +0 + Sympathy: +0
Total: 0
Difficulty: 5 (Success if Total ≥ 0)

Result: FAILURE ✗

NARRATOR (Perceptions Only):
"You try to focus. Nothing comes to mind. You don't know."

💭 INTERNAL VOICE (Suggestions):
"We don't know this area. We've never been here before. Maybe we should ask someone or look for landmarks."

[No memory created]
```

## Files Modified Summary

1. **`inquiry_helpers.py`**
   - `roll_inquiry_success()` - Uses unified formula with SMARTS
   - `process_failed_inquiry()` - Perceptions only, no suggestions

2. **`agents/narrator_agent.py`**
   - `generate_inquiry_response()` - Present perceptions only
   - `generate_inquiry_internal_voice()` - Memory + suggestion structure

3. **`MAIN/redesigned_main.py`**
   - Display shows "Smarts" not "Spirit"
   - Failed inquiries now generate internal voice

4. **`MENTAL_ACTION_FORMULA_FIX.md`**
   - Updated documentation

5. **`NARRATOR_INTERNAL_VOICE_SEPARATION.md`**
   - Complete separation guide

## Key Principles

### Narrator = Camera Lens
- Shows ONLY what is perceived RIGHT NOW
- No memories, no reasoning, no suggestions
- Present moment sensory information only

### Internal Voice = Mind
- Recalls memories: "We remember...", "We recall..."
- Suggests actions: "We could...", "We should...", "Maybe we..."
- ALWAYS includes both memory AND suggestion

### Mental Actions = Smarts
- Use `SFactorType.SMARTS` for intelligence/reasoning
- Standard UTAS formula applies
- Same calculation as all other actions

## Result

✅ All inquiry system issues resolved  
✅ Clean separation between narrator and internal voice  
✅ Failed inquiries now provide suggestions via internal voice  
✅ Mental actions use correct S-Factor and formula  
✅ No more AttributeErrors  
✅ Consistent with UTAS design philosophy
