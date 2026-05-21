# Complete System Test Sequence - Realitas Neo

## Overview
This is a comprehensive test sequence to verify EVERY system in Realitas Neo is working correctly.

**Instructions:**
1. Start simulation: `python MAIN/redesigned_main.py`
2. Create new session (n)
3. Select any character
4. Follow the test sequence below IN ORDER
5. Check that each expected result occurs

---

## PART 1: INQUIRY SYSTEM

### Test 1.1: First Inquiry (New Memory)
```
Input: What's the best way to get downtown?

Expected Results:
✅ Classified as information_gathering
✅ 🧠 LLM factual knowledge response shown
✅ Memory created
✅ Display: "🔍 MEMORY UNCOVERED"
✅ Factual knowledge (declarative statement)
✅ Internal voice (suggestion with could/should/maybe)
✅ Memory box shows both fact and thought

Verify:
[ ] FACT answers the specific question
[ ] NOT random scene description
[ ] Internal voice is separate from fact
[ ] No full narrative generated (inquiry doesn't advance time)
```

### Test 1.2: Second Inquiry (Memory Recall)
```
Input: Can I take the subway?

Expected Results:
✅ Classified as information_gathering
✅ Keyword match found (subway, downtown)
✅ Display: "💡 Recalled existing knowledge"
✅ Display: "💡 MEMORY RECALLED" (not UNCOVERED)
✅ Same FACT shown
✅ NEW internal voice (different from first)

Verify:
[ ] No duplicate memory created
[ ] "RECALLED" not "UNCOVERED"
[ ] Different internal voice
[ ] Same factual knowledge
```

### Test 1.3: Check Memories
```
Input: memories

Expected Results:
✅ Shows list of all memories
✅ Only 1 memory about downtown/subway
✅ Memory has title and description
✅ Tags shown (subway, downtown, etc.)

Verify:
[ ] Only 1 memory (not 2 or 3)
[ ] Memory deduplication worked
```

### Test 1.4: Unknown Information Inquiry
```
Input: What's in the sewers?

Expected Results:
✅ Classified as information_gathering
✅ 🧠 LLM response: "UNKNOWN"
✅ ⚠️ Knowledge rejected
✅ No memory created
✅ Only internal voice shown

Verify:
[ ] No memory box
[ ] Internal voice admits lack of knowledge
[ ] Suggests finding information
```

---

## PART 2: GIVEN ACTIONS (Automatic Success)

### Test 2.1: Simple Movement
```
Input: I walk to the door

Expected Results:
✅ Classified as given_action
✅ Automatic success (no calculations)
✅ Brief narrative
✅ Time advances ~3 seconds
✅ No UTAS calculation shown

Verify:
[ ] No success calculation
[ ] Immediate success
[ ] Simple narrative
```

### Test 2.2: Simple Interaction
```
Input: I sit down

Expected Results:
✅ Classified as given_action
✅ Automatic success
✅ Brief narrative
✅ Time advances ~3 seconds

Verify:
[ ] No calculations
[ ] Quick narrative
```

---

## PART 3: FALLIBLE ACTIONS (Exploration)

### Test 3.1: Situation Overcoming
```
Input: I climb over the fence

Expected Results:
✅ Classified as fallible_action
✅ Subtype: situation_overcoming
✅ UTAS calculation shown:
   - S-Trait (Swiftness or Sturdiness)
   - Skill (Climbing or Athletics)
   - Serendipity
   - Stress
   - Status
   - Total Success
✅ Success level narration
✅ Contextual narrative
✅ Time advances ~3 minutes

Verify:
[ ] Full calculation displayed
[ ] Success/failure based on total
[ ] Narrative matches success level
```

### Test 3.2: Information Gathering (Physical)
```
Input: I search the room for clues

Expected Results:
✅ Classified as fallible_action
✅ Subtype: information_gathering
✅ UTAS calculation shown
✅ Success determines what you find
✅ Narrative describes findings

Verify:
[ ] Calculation shown
[ ] Findings match success level
```

---

## PART 4: MEMORY CONTEXT INTEGRATION

### Test 4.1: Memory Consistency (Time)
```
Setup: Memory says "subway is 10-minute walk"

Input: I go to the subway

Expected Results:
✅ Narrator sees memory
✅ Time estimate matches memory (10 minutes)
✅ NO teleportation
✅ Journey shown (if journey chunking active)

Verify:
[ ] Time matches memory
[ ] No contradiction
[ ] Narrator respects established fact
```

### Test 4.2: Memory Consistency (Location)
```
Setup: Memory about specific location

Input: Action referencing that location

Expected Results:
✅ Narrator references memory
✅ Details match established facts
✅ No contradictions

Verify:
[ ] Consistent with memory
[ ] Same location details
```

---

## PART 5: CONTESTED ACTIONS (Exchanges)

### Test 5.1: Social Exchange
```
Input: I try to convince the guard to let me pass

Expected Results:
✅ Classified as contested_action
✅ Reactor identified: Guard
✅ Exchange system activated

PROACTOR CALCULATION:
✅ S-Trait: Sociability
✅ Skill: Persuasion
✅ Serendipity
✅ Stress
✅ Status
✅ Sympathy modifier (if relationship exists)
✅ Total Success

REACTOR CALCULATION:
✅ S-Trait: Sturdiness or Smarts
✅ Skill: Resist Persuasion
✅ Serendipity
✅ Stress
✅ Status
✅ Sympathy modifier
✅ Total Success

EXCHANGE RESULT:
✅ Winner determined (higher total)
✅ Margin calculated
✅ Self-effects for BOTH actors
✅ Outcome narrative

Verify:
[ ] Both calculations shown
[ ] Winner determined correctly
[ ] Self-effects mandatory (not "N/A")
[ ] Narrative matches outcome
[ ] Sympathy affects difficulty
```

### Test 5.2: Combat Exchange
```
Input: I punch the guard

Expected Results:
✅ Combat exchange
✅ Proactor calculation (Sturdiness)
✅ Reactor calculation (Swiftness for defense)
✅ Damage = margin of success
✅ Stamina reduced
✅ Self-effects include stamina cost for attacker
✅ Knockout if stamina ≤ 0

Verify:
[ ] Damage calculation correct
[ ] Attacker has stamina cost
[ ] Defender takes damage if hit
[ ] Knockout triggers if needed
```

### Test 5.3: Check Actor Sheets
```
Input: ua

Expected Results:
✅ Shows your character sheet
✅ Status changes from exchange
✅ Self-effects applied
✅ Stamina/Spirit/Supply updated

Input: people

Expected Results:
✅ Shows NPCs present
✅ Their status changes shown
✅ Self-effects applied to them

Verify:
[ ] Status changes visible
[ ] Self-effects applied
[ ] Both actors affected
```

---

## PART 6: SELF-EFFECTS SYSTEM

### Test 6.1: Proactor Self-Effects
```
Input: Any proactor action (yours)

Expected Results:
✅ Self-effects ALWAYS present
✅ Never "N/A"
✅ Severity 1-4
✅ Magnitude appropriate
✅ Description explains cost

Verify:
[ ] Self-effects shown
[ ] Not empty or "N/A"
[ ] Severity valid (1-4)
```

### Test 6.2: Reactor Self-Effects
```
Input: Action that triggers NPC reaction

Expected Results:
✅ NPC (reactor) has self-effects
✅ Describes their effort/cost
✅ Applied to their status

Verify:
[ ] Reactor self-effects present
[ ] Applied correctly
```

---

## PART 7: SYMPATHY SYSTEM

### Test 7.1: Helping Friend (Positive Sympathy)
```
Setup: Establish positive relationship with NPC

Input: I help [NPC name] up

Expected Results:
✅ Sympathy modifier shown
✅ Positive sympathy makes helping EASIER
✅ Modifier is negative (reduces difficulty)
✅ Explanation shown

Verify:
[ ] Sympathy affects calculation
[ ] Helping friend is easier
[ ] Modifier shown in calculation
```

### Test 7.2: Attacking Enemy (Negative Sympathy)
```
Setup: Establish negative relationship with NPC

Input: I punch [NPC name]

Expected Results:
✅ Sympathy modifier shown
✅ Negative sympathy makes attacking EASIER
✅ Modifier stays negative
✅ Explanation shown

Verify:
[ ] Sympathy affects calculation
[ ] Attacking enemy is easier
```

### Test 7.3: Attacking Friend (Positive Sympathy)
```
Setup: Positive relationship with NPC

Input: I punch [NPC name]

Expected Results:
✅ Sympathy modifier shown
✅ Positive sympathy makes attacking HARDER
✅ Modifier stays positive (penalty)
✅ Explanation shown

Verify:
[ ] Sympathy affects calculation
[ ] Attacking friend is harder
```

---

## PART 8: STATUS RECOVERY SYSTEM

### Test 8.1: Temporary Recovery
```
Setup: Take damage in exchange

Expected Results:
✅ Status reduced (Stamina/Spirit/Supply)
✅ Next turn: +1 recovery shown
✅ Recovery happens at initiative roll
✅ Recovers to lowest affected status

Verify:
[ ] Recovery +1 per turn
[ ] Happens automatically
[ ] Targets lowest status
```

### Test 8.2: Knockout and Recovery
```
Setup: Reduce NPC stamina to ≤ 0

Expected Results:
✅ 💀 KNOCKOUT! displayed
✅ NPC loses initiative
✅ Next turn: +1 recovery
✅ Continues until stamina > 0
✅ Consciousness regained

Verify:
[ ] Knockout triggers
[ ] Recovery automatic
[ ] Consciousness returns
```

---

## PART 9: GOAL PROGRESS SYSTEM

### Test 9.1: Goal-Related Action
```
Input: Action related to character's goal

Expected Results:
✅ Goal progress updated
✅ Display: "📈 Goal Progress: X% → Y%"
✅ Reason shown
✅ Progress bar updated

Verify:
[ ] Progress increases
[ ] Reason explains connection
[ ] Percentage shown
```

### Test 9.2: Unrelated Action
```
Input: Action NOT related to goal

Expected Results:
✅ Goal progress: X% → X% (no change)
✅ Reason: "Not related to goal"

Verify:
[ ] No progress change
[ ] Reason shown
```

---

## PART 10: SKILL PROGRESSION

### Test 10.1: Skill Use Tracking
```
Setup: Use same skill multiple times with success 4+

Expected Results:
✅ System tracks extraordinary uses
✅ After 10 uses: Progression roll
✅ If success: "📈 SKILL PROGRESSION!"
✅ Skill increases by 1

Verify:
[ ] Tracks uses
[ ] Roll at 10 uses
[ ] Skill increases if roll succeeds
```

---

## PART 11: NARRATIVE MODES

### Test 11.1: ROAM Mode
```
State: No NPCs, no conflict

Expected Results:
✅ Mode indicator: ROAM
✅ Exploration focus
✅ Scene description rich
✅ Calm tone

Verify:
[ ] ROAM mode shown
[ ] Exploration opportunities
```

### Test 11.2: SPARK Mode
```
State: NPC present, no conflict

Expected Results:
✅ Mode indicator: SPARK
✅ Social focus
✅ NPC description
✅ Interaction opportunities

Verify:
[ ] SPARK mode shown
[ ] NPC details
```

### Test 11.3: PRESSURE Mode
```
State: Active conflict/challenge

Expected Results:
✅ Mode indicator: PRESSURE
✅ Tension focus
✅ Stakes emphasized
✅ Urgent tone

Verify:
[ ] PRESSURE mode shown
[ ] Tension in narrative
```

---

## PART 12: TIME PROGRESSION

### Test 12.1: 3-Second Actions
```
Input: I look around

Expected Results:
✅ Time advances ~3 seconds
✅ Time display updates
✅ Quick action

Verify:
[ ] 3-second increment
[ ] Time shown
```

### Test 12.2: 3-Minute Actions
```
Input: I search the room

Expected Results:
✅ Time advances ~3 minutes
✅ Time display updates
✅ Moderate action

Verify:
[ ] 3-minute increment
[ ] Time shown
```

### Test 12.3: Sleep (Time Skip)
```
Input: I go to sleep

Expected Results:
✅ Time advances 2-8 hours
✅ Sleep category detected
✅ Time skip shown

Verify:
[ ] Hours pass (not minutes)
[ ] Sleep detected
```

---

## PART 13: SPATIAL SYSTEM

### Test 13.1: Zone Tracking
```
Input: map

Expected Results:
✅ Shows current zones
✅ Shows obstacles (doors, etc.)
✅ Spatial layout

Verify:
[ ] Zones listed
[ ] Obstacles shown
```

### Test 13.2: Movement Between Zones
```
Input: I go to [zone name]

Expected Results:
✅ Movement detected
✅ Location updates
✅ New zone description

Verify:
[ ] Location changed
[ ] New description
```

---

## PART 14: INTENT AVAILABILITY SYSTEM

### Test 14.1: Available Now
```
Input: Action supported by context

Expected Results:
✅ Intent classified as AVAILABLE_NOW
✅ Action proceeds immediately
✅ Diegetic explanation

Verify:
[ ] Action allowed
[ ] Explanation given
```

### Test 14.2: Available Later
```
Input: Action not immediately available

Expected Results:
✅ Intent classified as AVAILABLE_LATER
✅ Diegetic explanation
✅ Opportunity created

Verify:
[ ] Delayed but possible
[ ] Explanation given
```

### Test 14.3: Available Never
```
Input: Action that doesn't fit character/world

Expected Results:
✅ Intent classified as AVAILABLE_NEVER
✅ Diegetic explanation
✅ Respects established facts

Verify:
[ ] Action blocked
[ ] Explanation makes sense
```

---

## PART 15: CONCRETE DETAILS TRACKING

### Test 15.1: First Mention
```
Setup: Mention specific detail (car model, clothing, etc.)

Expected Results:
✅ Detail tracked
✅ Stored in concrete details system

Verify:
[ ] Detail recorded
```

### Test 15.2: Consistency Check
```
Setup: Reference same detail later

Expected Results:
✅ Same detail referenced
✅ No contradiction
✅ Narrator uses established detail

Verify:
[ ] Detail consistent
[ ] No changes
```

---

## PART 16: NUA MEMORY SYSTEM

### Test 16.1: NPC Remembers Interaction
```
Setup: Interact with NPC

Expected Results:
✅ NPC memory created
✅ Interaction recorded
✅ Affects future interactions

Verify:
[ ] Memory stored
[ ] NPC references it later
```

---

## PART 17: RULE OF 3'S SYSTEM

### Test 17.1: Time Scale Detection
```
Various inputs to test time scales

Expected Results:
✅ 3-SECOND: Combat, reflexes
✅ 3-MINUTE: Most actions
✅ SLEEP: Sleep actions

Verify:
[ ] Correct time scale
[ ] Appropriate duration
```

---

## PART 18: JOURNEY CHUNKING (If Active)

### Test 18.1: Long Journey
```
Input: I drive across town

Expected Results:
✅ Journey detected
✅ Multiple chunks shown
✅ Progressive narrative
✅ No teleportation

Verify:
[ ] Journey shown
[ ] Multiple segments
[ ] Realistic time
```

---

## QUICK VERIFICATION CHECKLIST

After running all tests, verify:

### Core Systems:
- [ ] Inquiry system (questions work)
- [ ] Memory creation (facts stored)
- [ ] Memory recall (existing retrieved)
- [ ] Memory deduplication (no duplicates)
- [ ] Given actions (automatic success)
- [ ] Fallible actions (calculations shown)
- [ ] Contested actions (exchanges work)

### Exchange Systems:
- [ ] Social exchanges (persuasion, etc.)
- [ ] Combat exchanges (damage, knockout)
- [ ] Self-effects (always present)
- [ ] Sympathy modifiers (affect difficulty)
- [ ] Winner determination (correct)

### Status Systems:
- [ ] Status changes (applied correctly)
- [ ] Temporary recovery (+1 per turn)
- [ ] Knockout (triggers at stamina ≤ 0)
- [ ] Recovery (automatic)

### Progression Systems:
- [ ] Goal progress (tracks correctly)
- [ ] Skill progression (tracks uses)

### Context Systems:
- [ ] Memories feed to narrator
- [ ] Memories feed to interpreter
- [ ] Concrete details tracked
- [ ] Narrative consistency

### Time Systems:
- [ ] 3-second actions
- [ ] 3-minute actions
- [ ] Sleep time skip
- [ ] Time display updates

### Spatial Systems:
- [ ] Zone tracking
- [ ] Movement detection
- [ ] Location updates

---

## EXPECTED TOTAL TIME

This complete test sequence should take approximately **30-45 minutes** to run through thoroughly.

---

## NOTES

- Run tests IN ORDER (some depend on previous tests)
- Check EVERY expected result
- Mark checkboxes as you verify
- Note any failures or unexpected behavior
- Test with DIFFERENT characters for variety

---

## STATUS

✅ Complete test sequence defined
✅ Covers ALL major systems
✅ Includes verification steps
✅ Ready for comprehensive testing
