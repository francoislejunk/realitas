# Realitas Neo - Comprehensive System Test

## Test Sequence

This document provides a complete test sequence to verify all systems in Realitas Neo are working correctly.

---

## 1. INQUIRY SYSTEM

### Test 1.1: First Inquiry (New Memory)
**Input:** `What's the best way to get downtown?`

**Expected:**
- ✅ Classified as `information_gathering`
- ✅ Success calculation shown
- ✅ FACT generated (declarative statement)
- ✅ Memory created with keywords
- ✅ Internal voice shown (suggestion with could/should/maybe)
- ✅ Display: "🔍 MEMORY UNCOVERED"
- ✅ Memory and internal voice shown together

**Verify:**
- [ ] No full narrative generated
- [ ] Memory is a FACT, not a thought
- [ ] Internal voice is a THOUGHT, not a fact
- [ ] No duplication

### Test 1.2: Second Inquiry (Existing Memory)
**Input:** `Can I take the U-Bahn?`

**Expected:**
- ✅ Keyword match found (u-bahn)
- ✅ Existing memory retrieved
- ✅ Display: "💡 Recalled existing knowledge"
- ✅ Same FACT shown
- ✅ NEW internal voice (context-aware)

**Verify:**
- [ ] No duplicate memory created
- [ ] Internal voice is different from first time
- [ ] Memory content unchanged

### Test 1.3: Inquiry Without Knowledge
**Input:** `What's in the sewers?`

**Expected:**
- ✅ LLM returns "UNKNOWN"
- ✅ No memory created
- ✅ Internal voice admits lack of knowledge
- ✅ Suggests alternatives

**Verify:**
- [ ] No memory box shown
- [ ] Only internal voice displayed
- [ ] Suggestion to find information

---

## 2. MEMORY SYSTEMS

### Test 2.1: Intent-Based Memory (Before Narration)
**Input:** `I want to call my mom`

**Expected:**
- ✅ Intent trigger detected: FAMILY (mother)
- ✅ Memory created BEFORE narration
- ✅ Display: "🔍 MEMORY UNCOVERED"
- ✅ Internal voice shown

**Verify:**
- [ ] Memory created first
- [ ] Narration uses memory knowledge
- [ ] No perception-based memory also triggered

### Test 2.2: Perception-Based Memory (After Narration)
**Input:** `I look around the room`

**Expected:**
- ✅ Narration generated first
- ✅ If emotional trigger in narration → memory resurfaces
- ✅ Display: "✨ MEMORY RESURFACED"
- ✅ Shows "Triggered by: [narration excerpt]"
- ✅ Internal voice in memory box

**Verify:**
- [ ] Narration shown first
- [ ] Memory triggered by narration content
- [ ] No intent-based memory also triggered

### Test 2.3: Two Systems Never Both Fire
**Input:** Any inquiry

**Expected:**
- ✅ Intent-based fires (inquiry)
- ✅ Perception-based SKIPPED (no narration)

**Verify:**
- [ ] Only one memory system activated
- [ ] No duplicate memory displays

---

## 3. GIVEN ACTIONS (ROAM Mode)

### Test 3.1: Simple Given Action
**Input:** `I walk to the corner store`

**Expected:**
- ✅ Classified as `given_action`
- ✅ Success = 3 (automatic)
- ✅ Contextual narrative generated
- ✅ Internal voice shown
- ✅ Time advances (3-MINUTE scale)

**Verify:**
- [ ] No success calculation shown
- [ ] Narrative is contextual
- [ ] Internal voice reflects action
- [ ] Time updated

### Test 3.2: Given Action with Perception Memory
**Input:** `I walk past a family having dinner`

**Expected:**
- ✅ Narrative generated
- ✅ Emotional trigger detected (FAMILY)
- ✅ Memory resurfaces
- ✅ Display: "✨ MEMORY RESURFACED"

**Verify:**
- [ ] Narration first, then memory
- [ ] Memory triggered by narration
- [ ] Internal voice in memory box

---

## 4. FALLIBLE ACTIONS (ROAM Mode)

### Test 4.1: Situation Overcoming
**Input:** `I try to climb over the fence`

**Expected:**
- ✅ Classified as `situation_overcoming`
- ✅ Success calculation shown
- ✅ S-Trait, skill, serendipity calculated
- ✅ Contextual narrative based on success
- ✅ Internal voice shown
- ✅ Backfire if success < 0

**Verify:**
- [ ] Full calculation display
- [ ] Narrative matches success level
- [ ] Internal voice reflects outcome
- [ ] Backfire applies status penalty if failed

### Test 4.2: Information Gathering (Non-Inquiry)
**Input:** `I search the desk for clues`

**Expected:**
- ✅ Classified as `information_gathering`
- ✅ Success calculation shown
- ✅ Narrative describes findings
- ✅ Internal voice shown

**Verify:**
- [ ] Not treated as inquiry
- [ ] Full narrative generated
- [ ] Success affects quality of findings

---

## 5. EXCHANGES (SPARK/PRESSURE Mode)

### Test 5.1: Contested Exchange
**Input:** `I try to convince the guard to let me pass`

**Expected:**
- ✅ Exchange system activated
- ✅ Proactor vs Reactor calculation
- ✅ Both actors' success calculated
- ✅ Winner determined
- ✅ Self-effects applied
- ✅ Sympathy modifier included
- ✅ Outcome narrative generated

**Verify:**
- [ ] Both calculations shown
- [ ] Self-effects displayed
- [ ] Sympathy affects difficulty
- [ ] Winner/loser determined
- [ ] Status changes applied

### Test 5.2: Combat Exchange
**Input:** `I punch the guard`

**Expected:**
- ✅ Combat exchange
- ✅ Damage calculation
- ✅ Self-effects (stamina cost)
- ✅ Reactor takes damage if proactor wins
- ✅ Knockout check if stamina ≤ 0

**Verify:**
- [ ] Damage applied correctly
- [ ] Self-effects mandatory
- [ ] Knockout triggers if needed
- [ ] Status recovery on next turn

---

## 6. GOAL PROGRESS SYSTEM

### Test 6.1: Goal-Related Action
**Input:** Action related to character's goal

**Expected:**
- ✅ Goal progress updated
- ✅ Display: "📈 Goal Progress: X% → Y%"
- ✅ Reason shown
- ✅ Progress bar updated

**Verify:**
- [ ] Progress calculation correct
- [ ] Reason makes sense
- [ ] Percentage updated

### Test 6.2: Unrelated Action
**Input:** Action unrelated to goal

**Expected:**
- ✅ Goal progress: 0% change
- ✅ Reason explains why no progress

**Verify:**
- [ ] No progress made
- [ ] Reason provided

---

## 7. SYMPATHY SYSTEM

### Test 7.1: Additive Action on Friend
**Input:** `I help my friend carry boxes`

**Expected:**
- ✅ Positive sympathy (+2) becomes negative bonus (-2)
- ✅ Action easier
- ✅ Success calculation shows sympathy modifier

**Verify:**
- [ ] Sympathy modifier correct
- [ ] Difficulty reduced
- [ ] Explanation shown

### Test 7.2: Subtractive Action on Enemy
**Input:** `I punch the enemy`

**Expected:**
- ✅ Negative sympathy (-2) stays negative (-2)
- ✅ Action easier
- ✅ Success calculation shows sympathy modifier

**Verify:**
- [ ] Sympathy modifier correct
- [ ] Difficulty reduced
- [ ] Explanation shown

---

## 8. PROGRESSION SYSTEM

### Test 8.1: Skill Progression
**Input:** Multiple actions using same skill with success 4+

**Expected:**
- ✅ After 10 extraordinary uses → 10% roll
- ✅ If success: "📈 SKILL PROGRESSION!"
- ✅ Skill increases by 1
- ✅ Actor sheet updated

**Verify:**
- [ ] Tracks extraordinary uses
- [ ] Progression roll occurs
- [ ] Skill updated if successful

### Test 8.2: Sympathy Progression
**Input:** 10 interactions with same NUA

**Expected:**
- ✅ Tracks interaction types (FRIENDLY/HOSTILE/NEUTRAL)
- ✅ After 10 → Count majority
- ✅ If majority clear → 50% roll
- ✅ Sympathy shifts ±1

**Verify:**
- [ ] Interactions tracked
- [ ] Majority determined
- [ ] Sympathy updated if roll succeeds

---

## 9. FOUR-MODE NARRATIVE LOOP

### Test 9.1: ROAM Mode
**Input:** Exploration action

**Expected:**
- ✅ Mode: ROAM
- ✅ Framing guidance provided
- ✅ Narrative reflects exploration tone

**Verify:**
- [ ] Mode displayed correctly
- [ ] Tone appropriate

### Test 9.2: SPARK Mode
**Input:** NUA encounter

**Expected:**
- ✅ Mode shifts to SPARK
- ✅ Display: "🔀 Mode Shift → SPARK"
- ✅ Narrative reflects encounter

**Verify:**
- [ ] Mode shift announced
- [ ] Tone changes

### Test 9.3: PRESSURE Mode
**Input:** Contested action

**Expected:**
- ✅ Mode: PRESSURE
- ✅ Narrative reflects tension

**Verify:**
- [ ] Mode appropriate
- [ ] Tone escalated

### Test 9.4: OUTCOME Mode
**Input:** Resolution of conflict

**Expected:**
- ✅ Mode: OUTCOME
- ✅ Narrative wraps up situation

**Verify:**
- [ ] Mode appropriate
- [ ] Resolution clear

---

## 10. TIME TRACKING (RULE OF 3s)

### Test 10.1: 3 Seconds
**Input:** Quick action (look, speak)

**Expected:**
- ✅ Time: +3 seconds
- ✅ Display updated

**Verify:**
- [ ] Time incremented correctly

### Test 10.2: 3 Minutes
**Input:** Standard action (walk, search)

**Expected:**
- ✅ Time: +3 minutes
- ✅ Display updated

**Verify:**
- [ ] Time incremented correctly

### Test 10.3: Sleep
**Input:** `I sleep`

**Expected:**
- ✅ Time: +8 hours
- ✅ Status recovery
- ✅ Display updated

**Verify:**
- [ ] Time advanced
- [ ] Statuses recovered

---

## 11. NUA LIVING WORLD

### Test 11.1: First Encounter
**Input:** Meet NUA for first time

**Expected:**
- ✅ NUA state recorded
- ✅ Initial sympathy assigned

**Verify:**
- [ ] State saved
- [ ] Sympathy set

### Test 11.2: Reunion (Hours Later)
**Input:** Meet same NUA after hours

**Expected:**
- ✅ Time difference calculated
- ✅ Observable changes shown
- ✅ Reunion narrative generated

**Verify:**
- [ ] Changes appropriate for time passed
- [ ] Narrative mentions changes

---

## 12. CONCRETE DETAILS TRACKER

### Test 12.1: First Mention
**Input:** Action mentioning specific detail (car model, clothing)

**Expected:**
- ✅ Detail tracked
- ✅ Stored with keywords

**Verify:**
- [ ] Detail saved
- [ ] Keywords indexed

### Test 12.2: Consistency Check
**Input:** Action referencing same detail later

**Expected:**
- ✅ Detail retrieved
- ✅ Narrative consistent

**Verify:**
- [ ] Same detail used
- [ ] No contradictions

---

## 13. WORLDBUILDING RAG

### Test 13.1: Scene Generation
**Input:** New scene created

**Expected:**
- ✅ RAG system consulted
- ✅ 1990s appropriate details
- ✅ No anachronisms

**Verify:**
- [ ] Period-accurate
- [ ] Lore-consistent
- [ ] No sci-fi/supernatural

---

## 14. ACTOR SHEET DISPLAY

### Test 14.1: View Sheet
**Input:** `ua`

**Expected:**
- ✅ S-Factors shown with descriptors
- ✅ Skills shown with descriptors
- ✅ Statuses shown with descriptors
- ✅ Inventory listed
- ✅ Goals shown with progress

**Verify:**
- [ ] Narrative descriptors used (not numbers)
- [ ] All sections present
- [ ] Formatting clean

---

## 15. MEMORY COMMANDS

### Test 15.1: View Memories
**Input:** `memories`

**Expected:**
- ✅ All memories listed
- ✅ Categorized by importance
- ✅ Timestamps shown

**Verify:**
- [ ] All memories present
- [ ] Organized clearly

### Test 15.2: Recall Specific Memory
**Input:** `recall 1` or `/mem 1`

**Expected:**
- ✅ Full memory displayed
- ✅ All details shown

**Verify:**
- [ ] Complete information
- [ ] Readable format

---

## Test Checklist Summary

### Core Systems
- [ ] Inquiry system (FACT vs THOUGHT)
- [ ] Two memory systems (never both)
- [ ] Memory deduplication (keywords)
- [ ] Given actions
- [ ] Fallible actions
- [ ] Exchanges

### Advanced Systems
- [ ] Goal progress
- [ ] Sympathy modifiers
- [ ] Skill progression
- [ ] Sympathy progression
- [ ] Four-mode narrative loop
- [ ] Time tracking (Rule of 3s)

### World Systems
- [ ] NUA living world
- [ ] Concrete details tracker
- [ ] Worldbuilding RAG
- [ ] 1990s authenticity

### UI/Display
- [ ] Actor sheet (narrative descriptors)
- [ ] Memory commands
- [ ] Status display
- [ ] Progress indicators

---

## How to Test

1. **Start new session:** `n`
2. **Run through each test** in order
3. **Check each verification point**
4. **Note any failures** in a separate document
5. **Test edge cases** (failures, backfires, knockouts)
6. **Verify persistence** (save/load, memory recall)

---

## Success Criteria

**System is working if:**
- ✅ All core systems function correctly
- ✅ No duplicate memories created
- ✅ FACT vs THOUGHT separation maintained
- ✅ Two memory systems never both fire
- ✅ Internal voice always accompanies memories
- ✅ Sympathy affects difficulty correctly
- ✅ Progression tracks properly
- ✅ Time advances correctly
- ✅ 1990s authenticity maintained
- ✅ No crashes or errors
