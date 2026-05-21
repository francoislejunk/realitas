# Friendly Action Narrative Fix

## Problem Identified

When a **friendly/cooperative action** (like a high-five) succeeded, the narrative was displaying:
- ❌ "mental composure crumbles" (negative language)
- ❌ "Null Impact" (incorrect status description)
- ❌ Generic combat language for friendly interactions

**Example Issue:**
```
Dylan Cole's high-five → Lena reciprocates
Result: Dylan's SYMPATHY +2 (1 → 3)
Narrative: "mental composure crumbles" ← WRONG!
```

## Root Causes

### 1. **No Polarity Detection in Narrator**
`narrator_agent.py` line 667-690: Consequence phrases were **always negative** (crumbles, wavers, weakens), regardless of whether the action was friendly (Additive) or hostile (Subtractive).

### 2. **No Polarity-Aware Narrative Templates**
Lines 692-708: Narrative templates used adversarial language ("falters against", "proves insufficient") even for friendly actions.

### 3. **Missing SYMPATHY in Consequence Phrases**
The consequence dictionary only had STAMINA, SPIRIT, SUPPLY - missing SYMPATHY entirely.

### 4. **Data Key Mismatch in Formula Generator**
`utas_narrative_formula.py` lines 462-467: Looking for `'actor_name'` but actual key is `'actor'`
Line 479: Looking for `'shift_value'` but actual key is `'delta'`

This caused the system to think there was no status shift, resulting in "Null Impact".

## Fixes Applied

### Fix 1: Added Polarity Detection (`narrator_agent.py` lines 667-669)

```python
# Detect shift polarity (Additive = friendly/helpful, Subtractive = harmful)
shift_polarity = outcome_data.get('shift_polarity', 'Subtractive')
is_additive = shift_polarity == 'Additive'
```

### Fix 2: Polarity-Aware Consequence Phrases (lines 671-719)

**Additive (Friendly) Consequences:**
```python
'STAMINA': {
    'close': 'physical vitality is slightly restored',
    'clear': 'body feels reinvigorated',
    'overwhelming': 'physical strength is significantly renewed',
},
'SPIRIT': {
    'close': 'confidence lifts slightly',
    'clear': 'morale is bolstered',
    'overwhelming': 'spirits are greatly uplifted',
},
'SYMPATHY': {
    'close': 'rapport improves slightly',
    'clear': 'connection strengthens',
    'overwhelming': 'bond deepens significantly',
}
```

**Subtractive (Hostile) Consequences:**
```python
'STAMINA': {
    'close': 'physical endurance wavers',
    'clear': 'body weakens under the strain',
    'overwhelming': 'physical strength is severely compromised',
},
'SPIRIT': {
    'close': 'grasp of their wits loosens',
    'clear': 'mental composure crumbles',
    'overwhelming': 'psychological state is shattered',
},
'SYMPATHY': {
    'close': 'rapport deteriorates slightly',
    'clear': 'relationship is damaged',
    'overwhelming': 'bond is severely fractured',
}
```

### Fix 3: Polarity-Aware Narrative Templates (lines 729-768)

**Friendly Action Success:**
```python
if is_additive:
    pure_resolution = (
        f"{proactor_name}'s {proactor_action} connects warmly with {reactor_name}'s {reactor_action}, "
        f"and {loser}'s {cons_phrase}."
    )
```

**Hostile Action Success:**
```python
else:
    pure_resolution = (
        f"{reactor_name}'s {reactor_action} proves insufficient against {proactor_name}'s {proactor_action} "
        f"as their {cons_phrase}."
    )
```

**Friendly Stalemate:**
```python
if is_additive:
    pure_resolution = (
        f"{proactor_name}'s {proactor_action} and {reactor_name}'s {reactor_action} meet in mutual understanding, "
        f"resulting in a balanced exchange."
    )
```

### Fix 4: Data Key Compatibility (`utas_narrative_formula.py`)

**Lines 462-467: Support both key formats**
```python
damage_shift = next((shift for shift in status_shifts 
                   if shift.get('actor_name') == reactor_name or shift.get('actor') == reactor_name), {})
```

**Lines 479-488: Support both key formats**
```python
# Support both 'shift_value' and 'delta' keys for compatibility
shift_value = damage_shift.get('shift_value') or damage_shift.get('delta', 0)

# Support both 'status_type' and 'status' keys
affected_status = damage_shift.get('status_type') or damage_shift.get('status', 'STAMINA')
```

## Expected Results

### Before Fix:
```
Dylan Cole's high-five → Lena reciprocates
Dylan's SYMPATHY: 1 → 3 (+2)
Narrative: "mental composure crumbles" ❌
Formula: "Null Impact" ❌
```

### After Fix:
```
Dylan Cole's high-five → Lena reciprocates
Dylan's SYMPATHY: 1 → 3 (+2)
Narrative: "connection strengthens" ✅
Formula: "Minor SYMPATHY Boost" ✅
```

## Test Cases

### Test 1: Friendly High-Five
- **Action:** "I give them a high-five"
- **Polarity:** Additive
- **Status:** SYMPATHY
- **Expected:** "connects warmly", "rapport improves", "Boost"

### Test 2: Encouragement
- **Action:** "You can do this! I believe in you!"
- **Polarity:** Additive
- **Status:** SPIRIT
- **Expected:** "morale is bolstered", "Boost"

### Test 3: Insult
- **Action:** "Your mom's a bitch"
- **Polarity:** Subtractive
- **Status:** SYMPATHY
- **Expected:** "relationship is damaged", "Penalty"

### Test 4: Physical Attack
- **Action:** "I punch them"
- **Polarity:** Subtractive
- **Status:** STAMINA
- **Expected:** "body weakens", "Penalty"

### Test 5: Healing/Help
- **Action:** "I bandage their wounds"
- **Polarity:** Additive
- **Status:** STAMINA
- **Expected:** "physical vitality is restored", "Boost"

## Files Modified

1. **`agents/narrator_agent.py`** (lines 667-768)
   - Added polarity detection
   - Added Additive consequence phrases
   - Added SYMPATHY to consequence dictionary
   - Added polarity-aware narrative templates

2. **`utas_narrative_formula.py`** (lines 462-488)
   - Added support for both 'actor' and 'actor_name' keys
   - Added support for both 'delta' and 'shift_value' keys
   - Added support for both 'status' and 'status_type' keys

## Integration with Dialogue System

This fix is **critical for dialogue as UTAS action** because:
- Persuasion attempts (Additive/SPIRIT) now show positive language
- Insults (Subtractive/SYMPATHY) show negative language
- Encouragement (Additive/SPIRIT) shows morale boost
- Rapport building (Additive/SYMPATHY) shows connection strengthening

**Example Dialogue Outcomes:**

**Persuasion Success:**
```
UA: "You should trust me - I've never let you down"
Result: NUA's SPIRIT +2
Narrative: "morale is bolstered" ✅
```

**Insult Success:**
```
UA: "You're pathetic"
Result: NUA's SYMPATHY -2
Narrative: "relationship is damaged" ✅
```

**Encouragement Success:**
```
UA: "You're doing great!"
Result: NUA's SPIRIT +1
Narrative: "confidence lifts slightly" ✅
```

## Summary

✅ **Polarity detection** - System now checks if action is Additive or Subtractive
✅ **Friendly language** - Positive actions use warm, supportive language
✅ **Hostile language** - Negative actions use adversarial language
✅ **SYMPATHY support** - Added consequence phrases for relationship changes
✅ **Data compatibility** - Fixed key mismatches causing "Null Impact"
✅ **Dialogue integration** - Works seamlessly with dialogue as UTAS action

The narrative system now properly reflects the **intent and outcome** of both friendly and hostile actions!
