# The Two Memory Systems

## CRITICAL RULE: NEVER BOTH IN SAME TURN

The simulation has **TWO SEPARATE MEMORY SYSTEMS** that must never conflict or both activate in the same turn.

---

## **System 1: INTENT-BASED (Before Narration)**

### **Trigger:**
User's intent or action

### **When It Runs:**
- **BEFORE** narration is generated
- During action interpretation phase

### **Flow:**
1. Detect intent trigger in user input
2. Generate FACTUAL KNOWLEDGE about character's background/knowledge
3. Store as memory
4. Use fact to generate narration/internal voice

### **Examples:**

**Inquiry:**
```
User: "What's the best way to get downtown?"
→ Generate FACT: "The U-Bahn runs all night from the station two blocks over"
→ Store as memory
→ Generate THOUGHT: "We could take the U-Bahn. It's faster."
```

**Intent Trigger:**
```
User: "I want to call my mom"
→ Detect trigger: FAMILY (mother)
→ Generate FACT: "You have a loving mother, Margaret, who lives in the suburbs"
→ Store as memory
→ Generate narration incorporating this knowledge
```

### **Trigger Types:**
- FAMILY
- RELATIONSHIP
- LOCATION
- POSSESSION
- SKILL
- OCCUPATION
- BACKSTORY
- TRAUMA
- ACHIEVEMENT
- HABIT
- **INQUIRY** (questions)

### **Display:**
```
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Route Knowledge: What's the best way downtown?
The U-Bahn runs all night from the station two blocks over.

════════════════════════════════════════════════════════════

💭 We could take the U-Bahn. It's faster.
```

---

## **System 2: PERCEPTION-BASED (After Narration)**

### **Trigger:**
Content of the narration itself

### **When It Runs:**
- **AFTER** narration is generated
- During narration processing phase

### **Flow:**
1. Generate narration first
2. Analyze narration for emotional triggers
3. Resurface existing memories OR create new ones
4. Display memory with "Triggered by: [narration excerpt]"

### **Examples:**

**Perception Trigger:**
```
Narration: "You see a happy family having a picnic together"
→ Detect trigger: FAMILY (seeing happy family)
→ Emotional tone: POSITIVE/NOSTALGIC
→ Resurface memory: "Loving Mother"
→ Display: "Triggered by: You see a happy family having a picnic"
→ Internal voice: "Man, I really miss my mom. I should go see her soon."
```

**Scene Description:**
```
Narration: "The old warehouse brings back memories of late nights..."
→ Detect trigger: LOCATION (warehouse)
→ Resurface memory: "First Rave Experience"
→ Display memory with context
```

### **Emotional Tone Matching:**
- POSITIVE/NOSTALGIC scenes → AVAILABLE_NOW (positive memory)
- MELANCHOLIC/WISTFUL scenes → AVAILABLE_LATER (distant memory)
- PAINFUL/TRIGGERING scenes → AVAILABLE_NEVER (loss memory)

### **Display:**
```
════════════════════════════════════════════════════════════
✨ MEMORY RESURFACED
════════════════════════════════════════════════════════════

Triggered by: You see a happy family having a picnic together

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.

💭 Internal Voice:
Man, I really miss my mom. I should go see her soon.

════════════════════════════════════════════════════════════
```

---

## **Key Differences:**

| Aspect | Intent-Based | Perception-Based |
|--------|-------------|------------------|
| **Timing** | Before narration | After narration |
| **Trigger** | User's action/intent | Narration content |
| **Purpose** | Build character knowledge | Resurface emotional memories |
| **Display** | "MEMORY UNCOVERED" | "MEMORY RESURFACED" |
| **Internal Voice** | Shown separately | Shown in memory box |
| **Triggered By** | Not shown | Shows narration excerpt |

---

## **Implementation Safeguards:**

### **In Main Loop (redesigned_main.py):**

```python
# Line 4553: PERCEPTION-BASED (only if NOT inquiry)
if not is_inquiry and contextual_result:
    resurfaced_memories = intent_memory_creator.process_narration_for_memories(...)
    # Display perception-based memories

# Line 4589: INTENT-BASED (only for inquiries)
if is_inquiry:
    factual_knowledge = narrator.generate_inquiry_factual_knowledge(...)
    if factual_knowledge:
        memory_result = intent_memory_creator.create_memory_from_inquiry_answer(...)
        # Display intent-based memory
```

### **The Guard:**
```python
if not is_inquiry and contextual_result:
    # Perception-based runs
```

This ensures:
- ✅ Inquiries use intent-based (no narration to analyze)
- ✅ Normal actions use perception-based (narration exists)
- ✅ Never both in same turn

---

## **Why This Matters:**

### **Without Separation:**
- ❌ Both systems fire → duplicate memories
- ❌ Conflicting memory types → confusion
- ❌ Memory spam → player overwhelmed

### **With Separation:**
- ✅ Clean, single memory per turn
- ✅ Appropriate system for context
- ✅ Clear purpose for each memory
- ✅ Better player experience

---

## **Future Expansion:**

The intent-based pattern (FACT first, then narration) should eventually apply to:

1. **Given Actions** - Generate fact about what happened, then narrate
2. **Fallible Situation Overcoming** - Generate fact about outcome, then narrate
3. **Exchanges** - Generate fact about what occurred, then narrate

This ensures all memories are **FACTS** (declarative knowledge) that can be used to generate **NARRATION** (interpretations/descriptions).

---

## **Testing Checklist:**

- [ ] Inquiry creates intent-based memory only
- [ ] Normal action with emotional narration creates perception-based memory only
- [ ] Never both memories in same turn
- [ ] Intent-based shows "MEMORY UNCOVERED"
- [ ] Perception-based shows "MEMORY RESURFACED"
- [ ] Perception-based shows "Triggered by:" line
- [ ] Intent-based shows internal voice separately
- [ ] Perception-based shows internal voice in box
