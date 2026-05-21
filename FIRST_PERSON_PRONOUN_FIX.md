# First Person Pronoun Fix - NUA Reactor Responses

## Problem Identified

NUA (Non-User Actor) reactor responses were being generated in **first person** instead of **third person**:

**Example of broken output:**
```
"narrative_description": "I see a call incoming from Evelyn 'Eva' Martinez. I pick up the smart tablet and swipe to accept the call, 'Hi Eva, how can I help you today?' I say with a friendly tone, ensuring the camera on the tablet is properly aligned to face me."
```

This breaks immersion because:
- NPCs should be described from an external perspective (third person)
- The narrative should use the character's name, not "I/me/my"
- Consistent with the rest of the simulation's narrative style

## Root Cause

The prompt in `determine_nua_reaction()` method (`agents/decider_agent.py`) was using **second person pronouns** that caused the LLM to respond in first person:

**Problematic phrases:**
- Line 1161: "**you** MUST respond with dialogue"
- Line 1162: "**Your** narrative_description MUST start..."
- Line 1165: "the exact words **you say**"

These second-person instructions caused the LLM to adopt a first-person perspective when generating the NUA's response.

## Solution Applied

### File: `agents/decider_agent.py`

**Method: `determine_nua_reaction()` (lines 870-1241)**

### Changes Made:

**1. Updated Absolute Requirement Section (lines 1160-1166):**

**Before:**
```python
**🚨 ABSOLUTE REQUIREMENT FOR narrative_description FIELD:**
- If the proactor spoke dialogue (quoted words), you MUST respond with dialogue (quoted words)
- Your narrative_description MUST start with quoted dialogue: "'[words]' [name] [action]"
- WRONG: "Marcus smiles and reciprocates" ❌
- RIGHT: "'Hey, Jet! What's up?' Marcus says with a grin, returning the high five" ✅
- Include the exact words you say in quotation marks FIRST, then any actions
```

**After:**
```python
**🚨 ABSOLUTE REQUIREMENT FOR narrative_description FIELD:**
- If the proactor spoke dialogue (quoted words), {reactor.sheet.name} MUST respond with dialogue (quoted words)
- The narrative_description MUST start with quoted dialogue: "'[{reactor.sheet.name}'s words]' {reactor.sheet.name} [action]"
- WRONG: "Marcus smiles and reciprocates" ❌
- RIGHT: "'Hey, Jet! What's up?' Marcus says with a grin, returning the high five" ✅
- Include the exact words {reactor.sheet.name} says in quotation marks FIRST, then any actions
- **CRITICAL: Write in THIRD PERSON using {reactor.sheet.name}'s name - NEVER use first person (I, me, my)**
```

**2. Updated Example in INUA Section (line 1307):**

**Before:**
```python
"narrative_description": "I see a call incoming from Evelyn 'Eva' Martinez. I pick up the smart tablet and swipe to accept the call, 'Hi Eva, how can I help you today?' I say with a friendly tone, ensuring the camera on the tablet is properly aligned to face me.",
```

**After:**
```python
"narrative_description": "Maria sees the call incoming from Evelyn 'Eva' Martinez. She picks up the smart tablet and swipes to accept the call. 'Hi Eva, how can I help you today?' Maria says with a friendly tone, ensuring the camera on the tablet is properly aligned to face her.",
```

## Key Changes

1. **Replaced "you/your"** with **"{reactor.sheet.name}"** throughout instructions
2. **Added explicit third person requirement**: "NEVER use first person (I, me, my)"
3. **Fixed example** to show correct third person format
4. **Clarified pronoun usage**: "she/her" instead of "I/me"

## Expected Result

**Before (Broken):**
```json
{
  "narrative_description": "I see a call incoming. I pick up the tablet. 'Hi Eva, how can I help you?' I say with a friendly tone."
}
```

**After (Fixed):**
```json
{
  "narrative_description": "Maria sees the call incoming. She picks up the tablet. 'Hi Eva, how can I help you?' Maria says with a friendly tone."
}
```

## Why This Works

1. **Explicit Third Person Instruction**: Added "NEVER use first person (I, me, my)"
2. **Character Name Substitution**: Changed "you/your" to "{reactor.sheet.name}"
3. **Corrected Example**: Shows proper third person format with character name
4. **Consistent Perspective**: Matches the rest of the simulation's narrative style

## Related Context

This issue was separate from the earlier fix where line 1166 already stated:
```python
- **CRITICAL: Write in THIRD PERSON using {reactor.sheet.name}'s name - NEVER use first person (I, me, my)**
```

However, the instructions above it (lines 1161-1165) were still using "you/your", which contradicted this requirement. The fix ensures **all instructions** consistently enforce third person perspective.

## Testing

To verify the fix works:

1. Start a simulation with an NUA
2. Perform an action that requires NUA reaction (e.g., "I call Maria")
3. Check the debug output for `narrative_description`
4. Should see: "Maria sees..." / "She picks up..." (NOT "I see..." / "I pick up...")
5. Dialogue should be: "'Hi Eva...' Maria says" (NOT "'Hi Eva...' I say")

## Status

✅ **FIXED** - NUA reactor responses should now consistently use third person perspective with character names.
