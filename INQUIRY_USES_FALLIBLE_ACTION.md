# Inquiry System Now Uses Standard Fallible Action System

## The Simplification

Mental inquiries are just **fallible actions** - they should use the exact same interpretation and calculation system as everything else.

## What Changed

### Before (Custom System):
```python
# Custom inquiry-specific roll
roll_result = roll_inquiry_success(
    user_question=user_input,
    ua_actor=actor,
    scene_context=scene_description,
    difficulty=difficulty  # Hardcoded difficulty determination
)
# Always used SMARTS, always used difficulty mapping
```

### After (Standard Fallible Action):
```python
# Use standard fallible action interpretation
interpretation_data = conductor.interpret_fallible_action(
    user_input=user_input,
    proactor=actor
)

# Use standard UTAS calculation (same as all fallible actions)
result = calculate_unified_result(
    actor=actor,
    s_trait=s_trait_enum,  # LLM determines which S-trait
    skill_name=skill_name,  # LLM determines if skill applies
    stress_level_override=utas.get('stress_level', 3)  # LLM determines stress
)
```

## Benefits

### 1. **LLM Determines S-Trait**
Instead of always using SMARTS, the LLM can choose the appropriate S-trait:
- **Smarts:** "What's the chemical formula for water?"
- **Shadow:** "Where's the hidden entrance?"
- **Sociability:** "Who would know about this?"
- **Swiftness:** "What's the quickest route?"

### 2. **LLM Determines Stress Level**
Instead of hardcoded difficulty patterns, the LLM analyzes complexity:
- Simple question → Stress 1-2
- Medium question → Stress 3-4
- Complex question → Stress 5+

### 3. **Skills Can Apply**
If the character has relevant skills, they apply:
- "Where's the nearest hospital?" + Local Knowledge skill
- "What's wrong with this engine?" + Mechanics skill
- "Who runs this neighborhood?" + Streetwise skill

### 4. **Consistent With Everything Else**
- Same interpretation process
- Same calculation formula
- Same success determination
- Same display format

## The Flow Now

### 1. Check Memory
```
User: "Where am I?"
System: [Checks key memories]
→ If found: Display memory + internal voice
→ If not found: Continue to fallible action
```

### 2. Interpret as Fallible Action
```
System: [Calls interpret_fallible_action()]
LLM analyzes:
- S-trait: Smarts (reasoning about location)
- Skill: None
- Stress: 3 (medium complexity)
- Exchange type: Spirit (mental action)
```

### 3. Calculate Success
```
🎲 MENTAL ACTION ROLL
Smarts: 3 + Skill: 0 + Endowment: 0 + Supplement: 0 + Luck: +1
Stress: +0 + Status: +0 + Sympathy: +0
Total: 4
Stress Level: 3 (Success if Total ≥ 0)
Result: SUCCESS ✓
```

### 4. Generate Response
```
NARRATOR (Perceptions):
"You scan the room. Unfamiliar walls, unfamiliar furniture..."

💭 INTERNAL VOICE (Memory + Suggestion):
"We don't recognize this place. Maybe we should ask someone..."
```

## Code Removed

We can now **remove** these custom inquiry functions:
- ❌ `roll_inquiry_success()` - Use `interpret_fallible_action()` instead
- ❌ `determine_inquiry_difficulty()` - LLM determines stress level
- ⚠️ Keep `check_inquiry_memory()` - Still needed for memory check
- ⚠️ Keep `process_failed_inquiry()` - Still needed for failure narrative

## Files Modified

**`MAIN/redesigned_main.py`** (lines 4631-4679):
- Removed custom `roll_inquiry_success()` call
- Added `interpret_fallible_action()` call
- Uses standard `calculate_unified_result()`
- Same display format as all fallible actions

## Result

✅ **Simpler code** - Reuses existing system  
✅ **More flexible** - LLM chooses appropriate S-trait  
✅ **Skills apply** - Relevant skills help with inquiries  
✅ **Consistent** - Same mechanics as all other actions  
✅ **Better stress determination** - LLM analyzes complexity

Mental inquiries are now just **another type of fallible action**, using the exact same system as everything else.
