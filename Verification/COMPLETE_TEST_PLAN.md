# Complete Test Plan - Realitas Neo

## Overview

Comprehensive testing guide covering all major systems with specific test cases and verification steps.

---

## PART 1: INQUIRY SYSTEM

### Test 1: First Inquiry (New Memory)
```
Input: "What's the best way to get downtown?"

Expected:
✅ Classified as information_gathering
✅ 🧠 LLM factual knowledge response shown
✅ Memory created
✅ Display: "🔍 MEMORY UNCOVERED"
✅ FACT shown (declarative statement)
✅ Internal voice shown (suggestion)

Verify:
[ ] FACT answers the specific question
[ ] Not random scene description
[ ] Internal voice uses could/should/maybe
[ ] Memory and voice shown together
```

### Test 2: Second Inquiry (Recall)
```
Input: "Can I take the subway?"

Expected:
✅ Keyword match found
✅ Display: "💡 Recalled existing knowledge"
✅ Display: "💡 MEMORY RECALLED"
✅ Same FACT shown
✅ NEW internal voice

Verify:
[ ] No duplicate memory created
[ ] Different internal voice
[ ] "RECALLED" not "UNCOVERED"
```

### Test 3: Unknown Information
```
Input: "What's in the sewers?"

Expected:
✅ 🧠 LLM response: "UNKNOWN"
✅ ⚠️ Knowledge rejected
✅ No memory created
✅ Only internal voice shown

Verify:
[ ] No memory box
[ ] Voice admits lack of knowledge
```

---

## PART 2: EXCHANGE SYSTEM

### Test 4: Basic Social Exchange
```
Input: "I try to convince the guard to let me pass"

Expected:
✅ Contested action detected
✅ Proactor calculation shown
✅ Reactor calculation shown
✅ Winner determined
✅ Self-effects for both actors
✅ Outcome narrative

Verify:
[ ] Both calculations complete
[ ] All factors included (S-trait, skill, serendipity, stress, status, sympathy)
[ ] Self-effects severity 1-4
[ ] Narrative matches winner
```

### Test 5: Combat Exchange
```
Input: "I punch the guard"

Expected:
✅ Combat exchange
✅ Damage = margin of success
✅ Stamina reduced
✅ Self-effects include stamina cost
✅ Knockout if stamina ≤ 0

Verify:
[ ] Damage calculation correct
[ ] Attacker has stamina cost
[ ] Knockout triggers properly
[ ] Recovery begins next turn
```

### Test 6: Sympathy Modifier
```
Setup: Friend with sympathy +3

Input: "I help Marcus up"

Expected:
✅ Sympathy modifier: -3 (easier)
✅ Explanation: "Helping friend is easier"

Input: "I punch Marcus"

Expected:
✅ Sympathy modifier: +3 (harder)
✅ Explanation: "Attacking friend is harder"

Verify:
[ ] Positive sympathy helps additive actions
[ ] Positive sympathy hinders subtractive actions
[ ] Modifiers shown in calculation
```

### Test 7: Knockout and Recovery
```
Turn 1: "I punch the thug" → Stamina 10 → 3
Turn 2: "I punch the thug again" → Stamina 3 → -2

Expected:
✅ 💀 KNOCKOUT!
✅ Initiative lost
✅ Next turn: +1 recovery
✅ Continues until stamina > 0

Verify:
[ ] Knockout at stamina ≤ 0
[ ] Recovery +1 per turn
[ ] Consciousness when stamina > 0
```

---

## PART 3: MEMORY SYSTEMS

### Test 8: Intent-Based Memory
```
Input: "I want to call my mom"

Expected:
✅ Intent trigger: FAMILY
✅ Memory created BEFORE narration
✅ Display: "🔍 MEMORY UNCOVERED"
✅ Narration uses memory

Verify:
[ ] Memory first, narration second
[ ] No perception memory also fires
```

### Test 9: Perception-Based Memory
```
Input: "I look around the room"

Expected:
✅ Narration first
✅ If trigger in narration → memory resurfaces
✅ Display: "✨ MEMORY RESURFACED"
✅ Shows "Triggered by: [excerpt]"

Verify:
[ ] Narration first, memory second
[ ] No intent memory also fires
```

### Test 10: Memory Deduplication
```
Input: "I remember my childhood home"
Input: "I think about my old house"

Expected:
✅ First creates memory
✅ Second retrieves existing
✅ Keywords match (childhood, home, house)
✅ Only 1 memory created

Verify:
[ ] Keyword matching works
[ ] No duplicate memories
[ ] Check with "memories" command
```

---

## PART 4: ACTION CLASSIFICATION

### Test 11: Given Actions
```
Input: "I walk to the door"
Input: "I sit down"
Input: "Hello"

Expected:
✅ Classified as given_action
✅ Automatic success
✅ No calculations
✅ Simple narrative

Verify:
[ ] No UTAS calculation
[ ] Immediate success
[ ] Brief narrative
```

### Test 12: Fallible Actions
```
Input: "I climb the fence"

Expected:
✅ Classified as fallible_action
✅ Subtype: situation_overcoming
✅ UTAS calculation shown
✅ Success/failure narrative

Verify:
[ ] Full calculation
[ ] S-trait, skill, serendipity
[ ] Outcome based on success level
```

### Test 13: Contested Actions
```
Input: "I ask the guard about the warehouse"

Expected:
✅ Classified as contested_action
✅ Reactor identified: Guard
✅ Exchange system activated

Verify:
[ ] NUA detected
[ ] Exchange calculations
[ ] Both actors involved
```

---

## PART 5: GOAL PROGRESS

### Test 14: Goal-Related Action
```
Setup: Goal "Find my missing sister"

Input: "I ask around about missing persons"

Expected:
✅ Goal progress updated
✅ Display: "📈 Goal Progress: 0% → 5%"
✅ Reason shown
✅ Progress bar updated

Verify:
[ ] Progress increases
[ ] Reason explains connection
[ ] Displayed clearly
```

### Test 15: Unrelated Action
```
Input: "I buy a sandwich"

Expected:
✅ Goal progress: 0% → 0%
✅ Reason: "Not related to goal"

Verify:
[ ] No progress change
[ ] Reason explains why
```

---

## PART 6: PROGRESSION SYSTEM

### Test 16: Skill Progression
```
Setup: Use same skill 10 times with success 4+

Expected:
✅ After 10th use: Progression roll
✅ If success: "📈 SKILL PROGRESSION!"
✅ Skill increases by 1
✅ Counter resets

Verify:
[ ] Tracks extraordinary uses
[ ] Roll occurs at 10
[ ] Skill updated if successful
```

### Test 17: Sympathy Progression
```
Setup: 10 interactions with same NUA

Expected:
✅ Tracks FRIENDLY/HOSTILE/NEUTRAL
✅ After 10: Majority determined
✅ If clear majority: 50% roll
✅ Sympathy shifts ±1

Verify:
[ ] Interaction types tracked
[ ] Majority calculated
[ ] Sympathy updated if roll succeeds
```

---

## PART 7: NARRATIVE MODES

### Test 18: ROAM Mode
```
State: No active goals, no NPCs

Expected:
✅ Exploration focus
✅ Scene description rich
✅ Opportunities listed
✅ Calm tone

Verify:
[ ] Mode indicator: ROAM
[ ] Exploration opportunities shown
```

### Test 19: SPARK Mode
```
State: NPC present, no conflict

Expected:
✅ Social focus
✅ NPC description
✅ Interaction opportunities
✅ Engaging tone

Verify:
[ ] Mode indicator: SPARK
[ ] NPC details shown
```

### Test 20: PRESSURE Mode
```
State: Active conflict/challenge

Expected:
✅ Tension focus
✅ Stakes emphasized
✅ Urgent tone
✅ Consequences clear

Verify:
[ ] Mode indicator: PRESSURE
[ ] Tension in narrative
```

### Test 21: RESOLVE Mode
```
State: After major event

Expected:
✅ Reflection focus
✅ Consequences shown
✅ Calm/contemplative tone
✅ Transition to next mode

Verify:
[ ] Mode indicator: RESOLVE
[ ] Aftermath described
```

---

## PART 8: STRESS AND STATUS

### Test 22: Stress Accumulation
```
Turn 1: Stressful action → Stress +1
Turn 2: Another stressful action → Stress +2
Turn 3: Rest → Stress -1

Expected:
✅ Stress increases with actions
✅ Affects success calculation
✅ Decreases with rest

Verify:
[ ] Stress modifier shown
[ ] Affects total success
[ ] Recovery works
```

### Test 23: Status Effects
```
Input: "I sprint across the rooftop"

Expected:
✅ Self-effect: "Winded" (Severity 2)
✅ Status penalty applied
✅ Affects next action
✅ Recovers over time

Verify:
[ ] Status shown in calculation
[ ] Penalty applied correctly
[ ] Recovery at turn start
```

---

## PART 9: SUPPLEMENTS AND ENDOWMENTS

### Test 24: Using Supplement
```
Input: "I use my lockpick to open the door"

Expected:
✅ Supplement bonus applied
✅ Durability decreases
✅ Narrative mentions item
✅ Removed if durability = 0

Verify:
[ ] Bonus in calculation
[ ] Durability tracked
[ ] Item consumption
```

### Test 25: Using Endowment
```
Input: "I use my enhanced strength to break the door"

Expected:
✅ Endowment bonus applied
✅ No durability loss
✅ Narrative describes ability

Verify:
[ ] Bonus in calculation
[ ] No consumption
[ ] Special ability described
```

---

## PART 10: EDGE CASES

### Test 26: Empty Input
```
Input: ""

Expected:
✅ Error message or prompt
✅ No crash

Verify:
[ ] Graceful handling
```

### Test 27: Invalid Command
```
Input: "asdfghjkl"

Expected:
✅ Treated as action or error
✅ No crash

Verify:
[ ] Graceful handling
```

### Test 28: Very Long Input
```
Input: [500+ character action]

Expected:
✅ Processed or truncated
✅ No crash

Verify:
[ ] Handles long input
```

---

## QUICK TEST SEQUENCE

For rapid verification, run this sequence:

```
1. "What's the best way downtown?" → New inquiry memory
2. "Can I take the subway?" → Recall existing memory
3. "memories" → Verify only 1 memory
4. "I try to convince the guard" → Social exchange
5. "I punch the guard" → Combat exchange
6. "I want to call my mom" → Intent memory
7. "I look around" → Perception memory (maybe)
8. "I walk to the door" → Given action
9. "I climb the fence" → Fallible action
10. "ua" → Check character sheet updates
```

---

## STATUS

✅ All major systems covered
✅ Specific test cases defined
✅ Verification checklists included
✅ Quick test sequence provided
✅ Ready for comprehensive testing
