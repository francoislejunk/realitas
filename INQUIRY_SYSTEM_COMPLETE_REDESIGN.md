# Inquiry System Complete Redesign - Summary

## The Two Critical Problems

### **Problem #1: Inquiries Give Commentary Instead of Answers**
- User asks question → Gets internal voice comment, not answer
- Example: "What's downtown?" → 💭 "We should figure that out..." (WRONG)
- Should get: Narrative answer describing routes, locations, etc. (RIGHT)

### **Problem #2: No Memory Integration**
- Every inquiry rolls fresh, even for known information
- No memory creation when learning new info
- Can duplicate information across multiple inquiries
- Character doesn't "remember" what they learned

---

## The Complete Solution

### **3-Phase Inquiry System**

#### **Phase 1: Memory Check (Free)**
- Check if character already knows this from previous inquiries
- If memory exists → Recall it instantly (no roll needed)
- Display internal voice: "Oh right, we learned this before..."
- Display full answer from memory

#### **Phase 2: Success Roll (If No Memory)**
- No memory found → Roll to see if character can figure it out
- Uses UTAS mechanics: Swiftness + Spirit + Serendipity vs Difficulty
- Display roll breakdown with calculation
- Success or failure determines next phase

#### **Phase 3a: Success - Answer + Memory**
- Roll succeeds → Generate narrative answer
- Check for duplicate memories (avoid redundancy)
- Create new DISCOVERY memory with learned information
- Display: "💾 Information learned and saved to memory"

#### **Phase 3b: Failure - Uncertainty**
- Roll fails → Character doesn't know
- Generate uncertain response: "You're not sure about that..."
- No memory created (didn't learn anything)
- Character can try again later or ask someone

---

## Example Flows

### **Scenario 1: Known Information (Memory Recall)**
```
User: "What's the best way to get downtown?"

[Memory Check: Found relevant memory from 2 days ago]

💭 Oh right, we learned this before. The U-Bahn station is just two blocks north.

The U-Bahn station is just two blocks north. Line 3 runs straight downtown 
and takes about 15 minutes during off-peak hours. Alternatively, you could 
walk, but that'd take close to an hour through the busy streets.

[Memory Recalled - No roll needed]
```

### **Scenario 2: New Information (Successful Learning)**
```
User: "Where can I find spare parts around here?"

[No memory found - Rolling for success]

🎲 INQUIRY ROLL
═══════════════════════════════════════
Swiftness: 3 + Spirit: 7 + Luck: +1 = 11
Difficulty: 5
Result: SUCCESS ✓
═══════════════════════════════════════

[SUCCESS - Learning information]

You think through what you've seen in the area. There's a junkyard about 
three blocks east, past the old factory. They usually have automotive parts 
and electronics. Alternatively, there's a hardware store on Main Street, 
though their selection is more limited.

💾 Information learned and saved to memory
```

### **Scenario 3: Failed Inquiry (Don't Know)**
```
User: "What's the security code for the warehouse?"

[No memory found - Rolling for success]

🎲 INQUIRY ROLL
═══════════════════════════════════════
Swiftness: 3 + Spirit: 4 + Luck: -2 = 5
Difficulty: 8
Result: FAILURE ✗
═══════════════════════════════════════

[FAILURE - Information unknown]

You try to recall if you've ever heard the code, but nothing comes to mind. 
You'd need to find someone who knows or look for it written down somewhere.

[No memory created]
```

---

## Key Features

### **1. Memory Integration**
- Checks `KeyMemoriesSystem` for DISCOVERY category memories
- Searches by keywords from question
- Instant recall if memory exists (free, no cost)

### **2. Success/Failure Mechanics**
- Not all inquiries succeed (realistic)
- Uses existing UTAS stats (Swiftness, Spirit, Serendipity)
- Difficulty varies by question complexity (3-10)
- Roll breakdown displayed for transparency

### **3. Memory Creation**
- Successful inquiries create DISCOVERY memories
- Stores question + answer for future reference
- Tags with keywords for easy searching
- ROUTINE importance (not cluttering with critical memories)

### **4. Deduplication**
- Checks for similar memories before creating
- Uses keyword overlap (50% similarity threshold)
- Prevents duplicate memories from similar questions
- Keeps memory system clean

### **5. Internal Voice Integration**
- Memory recall uses internal voice: "Oh right, we learned this before..."
- Maintains diegetic immersion
- Personality-driven (Fix #2 applies here too)

---

## Implementation Files

### **Main Changes**
1. **`redesigned_main.py`** - Replace mental action handling (lines ~6699-6723)
2. **`narrator_agent.py`** - Add `generate_inquiry_response()` method
3. **Helper functions** - Add inquiry utility functions

### **Helper Functions Needed**
```python
# Memory checking
check_inquiry_memory(question, key_memories, ua_actor)

# Success rolling
roll_inquiry_success(question, ua_actor, scene_context, difficulty)
determine_inquiry_difficulty(question, scene_context)

# Answer generation
process_successful_inquiry(question, ua_actor, scene, context, key_memories)
process_failed_inquiry(question, ua_actor, scene_context)

# Memory management
check_duplicate_inquiry_memory(question, answer, key_memories)
extract_inquiry_keywords(text)
extract_inquiry_subject(question)
```

---

## Integration with Fix #2 (Personality)

**Internal voice for memory recall MUST use personality:**

```python
# When recalling memory
internal_personality = ua_actor.sheet.personality_traits.get("internal")

# Cynical personality:
"Oh right, we learned this before. Not that it helped much."

# Optimistic personality:
"Oh right, we learned this before! This could work out perfectly."

# Analytical personality:
"Oh right, we learned this before. The data suggests Line 3 is optimal."
```

**Personality applies to ALL internal voice, including memory recall.**

---

## Benefits

### **Gameplay**
- ✅ Questions get actual answers, not commentary
- ✅ Known information is instant (no redundant rolls)
- ✅ Learning feels meaningful (creates memories)
- ✅ Failure is possible (adds challenge)

### **Immersion**
- ✅ Memory recall uses internal voice (diegetic)
- ✅ Character "remembers" what they learned
- ✅ No meta-level system messages
- ✅ Personality-driven throughout

### **System**
- ✅ Uses existing UTAS mechanics (Swiftness, Spirit)
- ✅ Integrates with KeyMemoriesSystem
- ✅ Prevents duplicate memories
- ✅ Clean, maintainable code

---

## Testing Checklist

### **Phase 1: Memory Recall**
- [ ] Ask question about known info → Recalls memory instantly
- [ ] Internal voice says "Oh right, we learned this before..."
- [ ] No roll displayed
- [ ] Full answer shown from memory

### **Phase 2: Success Roll**
- [ ] Ask new question → Displays roll breakdown
- [ ] Swiftness + Spirit + Serendipity calculated correctly
- [ ] Difficulty appropriate to question complexity
- [ ] Success/failure determined correctly

### **Phase 3a: Successful Learning**
- [ ] Success → Generates narrative answer
- [ ] Answer is relevant and useful
- [ ] Memory created with DISCOVERY category
- [ ] "💾 Information learned" message shown
- [ ] No duplicate memory if similar question asked again

### **Phase 3b: Failed Inquiry**
- [ ] Failure → Generates uncertain response
- [ ] Response indicates lack of knowledge
- [ ] No memory created
- [ ] Can ask again later

### **Personality Integration**
- [ ] Internal voice reflects character personality
- [ ] Cynical character sounds cynical
- [ ] Optimistic character sounds optimistic
- [ ] Personality consistent across all inquiries

---

## Priority

**CRITICAL - Both fixes needed together:**

1. **Fix #1 (Inquiry System)** - Without this, questions don't work
2. **Fix #2 (Personality)** - Without this, internal voice is generic

**Implement both simultaneously for complete solution.**

---

## Documentation

- **Complete design:** `INQUIRY_MEMORY_SYSTEM.md`
- **Critical fixes:** `INTERNAL_VOICE_CRITICAL_FIXES.md`
- **This summary:** `INQUIRY_SYSTEM_COMPLETE_REDESIGN.md`

All three documents work together to provide the complete solution.
