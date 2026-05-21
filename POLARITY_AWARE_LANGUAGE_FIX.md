# Polarity-Aware Language Fix

## Problem Identified

The formula narrative was using **adversarial language** ("overcomes", "defeats") for **friendly/cooperative exchanges**:

**Example:**
```
Marcus asks: "How's your day?"
Wiry Man responds warmly with gossip

OLD OUTPUT:
"Wiry Man overcomes Marcus Carter's question, with Marcus Carter's SPIRIT experiencing a Superb Boost"
```

**Issues:**
- ❌ "Overcomes" is combative for a friendly chat
- ❌ Same language used for punching someone and asking how their day is
- ❌ Breaks immersion for positive social interactions

## Root Cause

`utas_narrative_formula.py` line 328: LLM prompt always used adversarial language regardless of action intent:
```python
- Show how {winner}'s superior execution overcomes {loser}'s attempt
```

This was hardcoded for **all exchanges**, treating friendly greetings the same as hostile attacks.

## Fix Applied

### 1. **Pass Shift Polarity to Formula Generator** (lines 515-523)

```python
# Get shift polarity from outcome_data to determine friendly vs hostile language
action_polarity = outcome_data.get('shift_polarity', 'Subtractive')
is_friendly = action_polarity == 'Additive'

# Use enhanced LLM generation with attempt narratives as context
outcome_resolution = self._generate_outcome_resolution_llm(
    proactor_successes, reactor_successes, proactor_name, reactor_name,
    proactor_action, reactor_action, affected_status,
    proactor_attempt, reactor_attempt, is_friendly  # ← NEW PARAMETER
)
```

### 2. **Updated Method Signature** (line 255)

```python
def _generate_outcome_resolution_llm(self, proactor_successes: int, reactor_successes: int, 
                                    proactor_name: str, reactor_name: str, 
                                    proactor_action: str, reactor_action: str,
                                    affected_status: str = "STAMINA",
                                    proactor_attempt: str = None, reactor_attempt: str = None,
                                    is_friendly: bool = False) -> str:  # ← NEW PARAMETER
```

### 3. **Polarity-Aware LLM Prompt** (lines 314-330)

**For Friendly/Additive Actions:**
```python
**INTERACTION STYLE: FRIENDLY/COOPERATIVE**
- Use warm, positive language: "warmly receives", "connects with", "resonates with", "builds upon"
- Avoid adversarial terms: NO "overcomes", "defeats", "fails against"
- Frame as mutual exchange: "responds to", "reciprocates", "engages with"
- Winner succeeds in connecting/helping, loser benefits from the interaction
- Status changes are POSITIVE (boosts, improvements, strengthening)
```

**For Hostile/Subtractive Actions:**
```python
**INTERACTION STYLE: HOSTILE/ADVERSARIAL**
- Use competitive language: "overcomes", "defeats", "falters against", "proves insufficient"
- Frame as conflict: winner dominates, loser is overcome
- Status changes are NEGATIVE (penalties, damage, weakening)
```

## Expected Results

### Before Fix:

**Friendly Greeting:**
```
Marcus: "How's your day?"
Wiry Man: *shares gossip warmly*

Narrative: "Wiry Man overcomes Marcus Carter's question" ❌
```

**Hostile Attack:**
```
John: *punches Mara*
Mara: *dodges*

Narrative: "Mara overcomes John's punch" ✅ (correct for hostile)
```

### After Fix:

**Friendly Greeting:**
```
Marcus: "How's your day?"
Wiry Man: *shares gossip warmly*

Narrative: "Wiry Man warmly responds to Marcus Carter's question, connecting through shared conversation" ✅
```

**Hostile Attack:**
```
John: *punches Mara*
Mara: *dodges*

Narrative: "Mara overcomes John's punch" ✅ (still correct for hostile)
```

## Language Examples by Polarity

### Friendly/Additive (Boost):
- "warmly receives"
- "connects with"
- "resonates with"
- "builds upon"
- "responds to"
- "reciprocates"
- "engages with"
- "shares with"

### Hostile/Subtractive (Penalty):
- "overcomes"
- "defeats"
- "falters against"
- "proves insufficient"
- "dominates"
- "overwhelms"
- "crushes"

## Integration with Dialogue System

This fix is **critical for dialogue as UTAS action** because:

**Persuasion (Additive/SPIRIT):**
```
OLD: "NUA overcomes UA's persuasion attempt"
NEW: "NUA warmly receives UA's persuasion, connecting with the argument"
```

**Encouragement (Additive/SPIRIT):**
```
OLD: "NUA overcomes UA's encouragement"
NEW: "NUA responds to UA's encouragement, building confidence"
```

**Insult (Subtractive/SYMPATHY):**
```
OLD: "NUA overcomes UA's insult" ✅ (correct - still adversarial)
NEW: "NUA overcomes UA's insult" ✅ (unchanged - appropriate)
```

## Files Modified

1. **`utas_narrative_formula.py`** (lines 250-349, 515-523)
   - Added `is_friendly` parameter to `_generate_outcome_resolution_llm()`
   - Added polarity detection from `outcome_data`
   - Added conditional interaction style prompts
   - LLM now generates appropriate language based on action intent

## Summary

✅ **Polarity detection** - System checks if action is Additive (friendly) or Subtractive (hostile)
✅ **Friendly language** - Cooperative actions use warm, positive verbs
✅ **Hostile language** - Adversarial actions use competitive verbs
✅ **Dialogue integration** - Works seamlessly with dialogue as UTAS action
✅ **Immersion preserved** - Narrative matches the social context of the interaction

The formula narrative now properly reflects whether you're **making friends or making enemies**! 🎉
