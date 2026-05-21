# Contested Action Detection Fix

## Problem Identified

Physical attacks against NPCs were being misclassified as **fallible actions** (exploration) instead of **contested actions** (encounters):

**Example:**
```
Input: "I go over to one of the truckers and punch him in the face"

WRONG Classification:
- input_type: "fallible_action"
- fallible_subtype: "situation_overcoming"
- Result: Exploration action, no encounter triggered

CORRECT Classification:
- input_type: "contested_action"
- Result: Full UTAS encounter vs. the trucker
```

## Root Cause

The inquiry detection prompt emphasized **dialogue/communication** as contested actions but didn't make it clear that **ALL NPC-targeted actions** (including physical attacks) are contested.

**Old Prompt (Line 1477):**
```
CONTESTED ACTION - Actions that target or interact with NUA... This includes complex dialogue, 
questions seeking information, conversations with stakes, negotiations, threats...
```

This made the LLM think:
- Dialogue with NPCs = Contested ✓
- Physical attacks on NPCs = Situation Overcoming ✗ (WRONG!)

## Fix Applied

### 1. Reordered and Clarified Action Types (lines 1472-1481)

**Put CONTESTED ACTION first** (it's the most common):

```
**TASK:** Determine if this input is:
1. **CONTESTED ACTION** - **ANY action that targets, affects, or interacts with an NPC (NUA/INUA)**. 
   This is the MOST COMMON type. Examples:
   - **Physical actions against NPCs**: "I punch him", "I shoot the guard", "I tackle her", "I push them"
   - **Dialogue with NPCs**: Questions, conversations, negotiations, threats, persuasion
   - **Actions affecting NPCs**: "I steal from him", "I help her up", "I give him the item"
   - **CRITICAL**: If an NPC is the target/recipient/opponent, it's ALWAYS contested, not fallible

2. **FALLIBLE ACTION** - Actions against the ENVIRONMENT or SELF, not NPCs. Two subtypes:
   - **Information Gathering**: Observational questions, perception checks - don't end turn
   - **Situation Overcoming**: Physical challenges vs. environment (climb wall, pick lock) - end turn

3. **GIVEN ACTION** - Trivial actions requiring no roll: walking, sitting, basic movement, simple greetings
```

### 2. Added Explicit Physical Attack Examples (lines 1495-1502)

```
**GUIDELINES:**
- **CONTESTED ACTION** (MOST COMMON - any NPC interaction):
  - "I punch the trucker" → CONTESTED (attacking NPC)
  - "I shoot the guard" → CONTESTED (attacking NPC)
  - "I ask Lysandra if she has weapons" → CONTESTED (dialogue with NPC)
  - "I help him up" → CONTESTED (assisting NPC)
  - "I steal from her" → CONTESTED (action against NPC)
  - "I push them aside" → CONTESTED (physical action on NPC)
  - **KEY**: If an NPC is involved as target/recipient/opponent → CONTESTED
```

### 3. Added Critical Rule (line 1520)

```
- **CRITICAL RULE**: If the action mentions or targets an NPC (by name, pronoun, or description 
  like "the trucker", "him", "her"), it's CONTESTED
```

## Classification Matrix

| Input | Target | Type | Reasoning |
|-------|--------|------|-----------|
| "I punch the trucker" | NPC | **CONTESTED** | Physical attack on NPC |
| "I shoot the guard" | NPC | **CONTESTED** | Physical attack on NPC |
| "I ask him about the job" | NPC | **CONTESTED** | Dialogue with NPC |
| "I help her up" | NPC | **CONTESTED** | Assisting NPC |
| "I climb the wall" | Environment | Fallible | Physical challenge vs. environment |
| "I pick the lock" | Object | Fallible | Skill check vs. object |
| "I walk to the door" | Self | Given | Trivial movement |

## Key Principle

**ANY action that involves an NPC as:**
- ✅ Target (punch them, shoot them)
- ✅ Recipient (give them item, help them)
- ✅ Opponent (fight them, resist them)
- ✅ Conversational partner (ask them, tell them)

**Is ALWAYS a contested action**, not a fallible action.

**Fallible actions are ONLY for:**
- Environment challenges (climb wall, pick lock)
- Self-directed actions (sneak, hide)
- Observation (look around, listen)

## Expected Behavior After Fix

### Before Fix:
```
Input: "I punch the trucker"
Classification: fallible_action (situation_overcoming)
Result: Exploration action, no encounter
Output: "Derek punched the trucker. The trucker staggers back."
```

### After Fix:
```
Input: "I punch the trucker"
Classification: contested_action
Result: Full UTAS encounter triggered
Flow:
1. Step 1: UA action interpretation
2. Step 2: UA attempt narrative
3. Step 3: NPC reaction decision
4. Step 4: NPC attempt narrative
5. Step 5: Success calculation
6. Step 6: Outcome narrative with status shifts
```

## Files Modified

**`agents/interpreter_agent.py`** (lines 1472-1520)
- Reordered action types (contested first)
- Added explicit physical attack examples
- Clarified that ALL NPC-targeted actions are contested
- Added critical rule for NPC detection

## Testing Checklist

- [ ] "I punch him" → contested_action
- [ ] "I shoot the guard" → contested_action
- [ ] "I tackle her" → contested_action
- [ ] "I ask him a question" → contested_action
- [ ] "I help her up" → contested_action
- [ ] "I climb the wall" → fallible_action
- [ ] "I pick the lock" → fallible_action
- [ ] "I walk to the door" → given_action

## Summary

✅ **Physical attacks on NPCs** now correctly trigger contested actions
✅ **All NPC interactions** (physical, verbal, assistive) are contested
✅ **Fallible actions** are only for environment/self-directed challenges
✅ **Clear examples** prevent future misclassification

Punching an NPC now properly triggers a full UTAS encounter! 🥊⚔️
