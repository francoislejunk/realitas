# NPC Parser Should Run on ALL Narrative Outputs

## The Principle

**NPCs can be mentioned in ANY narrative output**, therefore the NPC parser should run after **every narrative generation**.

## Current State

NPC parser currently runs:
1. ✅ Initial scene setup
2. ✅ Scene transitions
3. ✅ Inquiry responses (successful)
4. ✅ Inquiry responses (failed)
5. ✅ Exploration action results (physical fallible)
6. ❌ **MISSING:** Many other narrative outputs

## All Narrative Generation Points

### Where Narrator Generates Text

1. **Scene Generation**
   - `generate_scene_with_narrative_loop()` - Initial scenes, transitions, SPARK events
   
2. **Action Results**
   - `generate_contextual_exploration_action_result_narrative()` - Exploration actions
   - `generate_grouped_action_narrative()` - Grouped combat actions
   
3. **Inquiry Responses**
   - `generate_inquiry_response()` - Successful inquiry answers
   - `generate_inquiry_internal_voice()` - Internal voice thoughts
   - `process_failed_inquiry()` - Failed inquiry uncertainty
   
4. **Internal Voice**
   - `generate_internal_voice()` - General internal thoughts
   - `generate_inquiry_factual_knowledge()` - Factual knowledge extraction

5. **Contested Actions**
   - Exchange narratives
   - Combat results
   - Social interaction outcomes

## The Solution

### Helper Module: `npc_parser_wrapper.py`

Created a wrapper function that can be called after any narrative output:

```python
from npc_parser_wrapper import parse_narrative_for_npcs

# After generating any narrative
narrative_text = narrator.generate_something(...)
print(narrative_text)

# Parse for NPCs
parse_narrative_for_npcs(
    narrative_text=narrative_text,
    available_npcs=available_npcs,
    actor_generator=actor_generator,
    scene_id=scene_id,
    suppress_debug=SUPPRESS_DEBUG
)
```

### Implementation Strategy

**Option 1: Explicit Calls (Current)**
- Add `parse_narrative_for_npcs()` after each narrative output
- Pros: Clear, explicit, easy to debug
- Cons: Must remember to add it everywhere

**Option 2: Wrapper Function**
- Create `display_narrative_with_npc_parsing()` that combines display + parsing
- Pros: Single call, can't forget
- Cons: Requires refactoring all display calls

**Option 3: Narrator Method Wrapper**
- Wrap narrator methods to auto-parse output
- Pros: Automatic, no manual calls needed
- Cons: Complex, harder to debug

## Recommended Approach

Use **Option 1** (explicit calls) for now because:
1. Clear and debuggable
2. Can selectively disable for performance
3. Easy to see where parsing happens
4. No complex refactoring needed

## Critical Locations to Add NPC Parsing

### High Priority (NPCs likely to appear)

1. **Exploration Action Results** ✅ DONE
   ```python
   contextual_result = narrator.generate_contextual_exploration_action_result_narrative(...)
   print(contextual_result)
   parse_narrative_for_npcs(contextual_result, ...)
   ```

2. **Scene Transitions** ✅ DONE
   ```python
   scene_description = narrator.generate_scene_with_narrative_loop(...)
   print(scene_description)
   parse_narrative_for_npcs(scene_description, ...)
   ```

3. **Inquiry Responses** ✅ DONE
   ```python
   answer = narrator.generate_inquiry_response(...)
   print(answer)
   parse_narrative_for_npcs(answer, ...)
   ```

4. **Grouped Action Narratives** ⚠️ TODO
   ```python
   group_narrative = narrator.generate_grouped_action_narrative(...)
   print(group_narrative)
   parse_narrative_for_npcs(group_narrative, ...)
   ```

### Medium Priority

5. **SPARK Events** ⚠️ TODO
   - SPARKs can introduce new NPCs
   
6. **Exchange Results** ⚠️ TODO
   - Combat/social exchanges may mention bystanders

### Low Priority

7. **Internal Voice** (Usually doesn't introduce new NPCs)
8. **Status Updates** (System messages, not narrative)

## Example Scenarios

### Scenario 1: Exploration Action
```
User: "I look around the bar"

Narrator: "You scan the dimly lit bar. A bartender polishes glasses 
behind the counter. Two men in suits sit in the corner booth, 
speaking in hushed tones."

[NPC PARSER] Detected 3 NPC(s)
✓ Created NUA: Bartender
✓ Created NUA: Man in Suit #1
✓ Created NUA: Man in Suit #2

User: "I approach the bartender"
System: ✓ Processes encounter
```

### Scenario 2: SPARK Event
```
SPARK: "A woman bursts through the door, looking panicked"

[NPC PARSER] Detected 1 NPC
✓ Created NUA: Panicked Woman

User: "I ask her what's wrong"
System: ✓ Processes encounter
```

### Scenario 3: Combat Result
```
Exchange Result: "You punch the guard. He stumbles back. 
His partner reaches for his radio."

[NPC PARSER] Detected 1 NPC
✓ Created NUA: Guard's Partner

User: "I tackle the partner"
System: ✓ Processes encounter
```

## Files Modified

1. **`npc_parser_wrapper.py`** (NEW)
   - Helper functions for parsing narrative
   - `parse_narrative_for_npcs()` - Main parsing function
   - `display_narrative_with_npc_parsing()` - Combined display + parse

2. **`MAIN/redesigned_main.py`**
   - Added NPC parsing after inquiry responses (lines 4706-4719, 4788-4801)
   - Added NPC parsing after exploration actions (lines 4091-4099)
   - TODO: Add to grouped actions, SPARKs, exchanges

## Next Steps

1. ✅ Create `npc_parser_wrapper.py` helper module
2. ✅ Add parsing to inquiry responses
3. ✅ Add parsing to exploration actions
4. ⚠️ Add parsing to grouped action narratives
5. ⚠️ Add parsing to SPARK events
6. ⚠️ Add parsing to exchange results
7. ⚠️ Test with various scenarios

## Result

Once complete, NPCs will be automatically detected and spawned from **any narrative output**, ensuring players can always interact with mentioned characters regardless of how they were introduced.
