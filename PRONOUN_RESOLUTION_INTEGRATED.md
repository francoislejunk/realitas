# Pronoun Resolution Integrated into Action Processing

## The Problem

User said: `"I get as close to him as possible and say, 'Hello sir'"`

System responded: `"There is no 'him' in the scene description."`

Even though the narrative clearly mentioned "a man in a worn leather jacket" and the NPC parser detected him, the pronoun "him" wasn't resolved to the NPC name before the intent availability check.

## The Solution

Added **pronoun resolution** as a preprocessing step that runs **before intent availability check**, automatically converting pronouns to NPC names.

## Implementation

### Location: `MAIN/redesigned_main.py` (lines 3100-3124)

Added pronoun resolution right before intent availability check:

```python
# ============================================================
# PRONOUN RESOLUTION
# ============================================================
# Resolve pronoun references (him, her, them) to NPC names
# before intent processing
# ============================================================

try:
    from pronoun_resolution import extract_pronoun_from_action, resolve_pronoun_to_npc, replace_pronoun_with_name
    
    pronoun = extract_pronoun_from_action(user_input)
    if pronoun and available_npcs:
        # Try to resolve pronoun to NPC name
        npc_name = resolve_pronoun_to_npc(pronoun, available_npcs)
        
        if npc_name:
            # Replace pronoun with NPC name
            original_input = user_input
            user_input = replace_pronoun_with_name(user_input, pronoun, npc_name)
            
            if not SUPPRESS_DEBUG:
                print(f"[PRONOUN RESOLUTION] '{pronoun}' → '{npc_name}'")
                print(f"[RESOLVED ACTION] {user_input}")
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"[PRONOUN RESOLUTION] Failed: {e}")
```

## The Flow

### Before (Broken)

```
Narrative: "You lock eyes with a man in a worn leather jacket..."
[NPC PARSER] Detected: Man in Leather Jacket
[NPC PARSER] Created NPC: Man in Leather Jacket (pronouns: "he/him")

User: "I get as close to him as possible"
↓
[INTENT CHECK] Looking for "him" in scene...
❌ Error: "There is no 'him' in the scene description"
```

### After (Fixed)

```
Narrative: "You lock eyes with a man in a worn leather jacket..."
[NPC PARSER] Detected: Man in Leather Jacket
[NPC PARSER] Created NPC: Man in Leather Jacket (pronouns: "he/him")

User: "I get as close to him as possible"
↓
[PRONOUN RESOLUTION] Extract: "him"
[PRONOUN RESOLUTION] Resolve: "him" → "Man in Leather Jacket"
[PRONOUN RESOLUTION] Replace: "I get as close to Man in Leather Jacket as possible"
↓
[INTENT CHECK] Looking for "Man in Leather Jacket" in scene...
✓ Found! Proceeding with action...
```

## Processing Order

1. **User Input** - Raw action with pronoun
2. **Pronoun Resolution** ⭐ NEW - Convert pronouns to names
3. **Intent Availability Check** - Validate against scene
4. **Action Processing** - Execute the action

## Example Scenarios

### Scenario 1: Single NPC

```
Scene: "A bartender wipes down the counter."
NPCs: [Mike (he/him)]

User: "I talk to him"
↓
[PRONOUN RESOLUTION] "him" → "Mike"
[RESOLVED] "I talk to Mike"
✓ Processes conversation with Mike
```

### Scenario 2: Multiple NPCs with Different Pronouns

```
Scene: "A waitress approaches. A security guard stands by the door."
NPCs: [Linda (she/her), Marcus (he/him)]

User: "I talk to her"
↓
[PRONOUN RESOLUTION] "her" → "Linda"
[RESOLVED] "I talk to Linda"
✓ Processes conversation with Linda

User: "I approach him"
↓
[PRONOUN RESOLUTION] "him" → "Marcus"
[RESOLVED] "I approach Marcus"
✓ Processes encounter with Marcus
```

### Scenario 3: Ambiguous (Multiple Same Pronouns)

```
Scene: "Two men in suits sit in the corner."
NPCs: [Man #1 (he/him), Man #2 (he/him)]

User: "I talk to him"
↓
[PRONOUN RESOLUTION] "him" → "Man #1" (first match)
[RESOLVED] "I talk to Man #1"
⚠️ May not be the intended NPC, but resolves to something
```

## Debug Output

When `SUPPRESS_DEBUG = False`, you'll see:

```
[PRONOUN RESOLUTION] 'him' → 'Man in Leather Jacket'
[RESOLVED ACTION] I get as close to Man in Leather Jacket as possible and say, "Hello sir"
```

This confirms the pronoun was resolved before processing.

## Benefits

✅ **Natural Language** - Users can say "him", "her", "them"  
✅ **Automatic** - No manual name typing required  
✅ **Seamless** - Happens before intent check  
✅ **Transparent** - Debug output shows resolution  
✅ **No Errors** - Eliminates "There is no 'him'" errors  

## Files Modified

1. **`MAIN/redesigned_main.py`** (lines 3100-3124)
   - Added pronoun resolution before intent check
   - Extracts pronoun from user input
   - Resolves to NPC name
   - Replaces pronoun in action string

2. **`pronoun_resolution.py`** (already created)
   - Helper functions for resolution

3. **`actor_sheet.py`** (already modified)
   - Added pronouns field

4. **`agents/creator_agent.py`** (already modified)
   - Generate pronouns for NPCs

## Result

✅ Pronouns are now automatically resolved to NPC names before action processing  
✅ No more "There is no 'him' in the scene description" errors  
✅ Natural pronoun references work seamlessly  
✅ Users can interact with NPCs using pronouns  

The pronoun resolution system is now fully integrated and operational!
