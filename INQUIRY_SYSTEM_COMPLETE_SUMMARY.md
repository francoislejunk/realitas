# Inquiry System - Complete Implementation Summary

## Overview

The inquiry system has been completely redesigned to properly separate **FACTS** (memories) from **THOUGHTS** (internal voice), prevent redundant memories, and ensure all memories are acknowledged with internal voice.

---

## The Three Core Principles

### **1. FACT vs THOUGHT Separation**

**MEMORY = FACT (What you KNOW)**
- Declarative statements
- "The U-Bahn runs all night from the station two blocks over"
- "There's a subway entrance two blocks east on Maple Street"
- Stored permanently, referenced later

**INTERNAL VOICE = THOUGHT (What you COULD do)**
- Suggestions and reasoning
- "We could take the U-Bahn. It's faster than walking."
- "Maybe we should ask someone, or look for a bus stop"
- Generated fresh each time, context-aware

### **2. Two Memory Systems (Never Both)**

**INTENT-BASED (Before Narration)**
- Triggers on user intent/action
- Generates FACT first, then uses it for narration
- Used for: Inquiries, intent triggers
- Display: "MEMORY UNCOVERED"

**PERCEPTION-BASED (After Narration)**
- Triggers on narration content
- Analyzes emotional tone, resurfaces memories
- Used for: Normal actions with emotional narration
- Display: "MEMORY RESURFACED" + "Triggered by:"

**CRITICAL:** Guard at line 4553 ensures they never both fire:
```python
if not is_inquiry and contextual_result:
    # Perception-based only runs if NOT inquiry
```

### **3. Deduplication via Keywords**

**Keyword Extraction:**
- Extracts 5 key nouns from question + answer
- Filters stopwords (the, a, what, where, etc.)
- Tags memory with keywords

**Existing Memory Check:**
- Searches all memories for matching keywords
- Returns existing memory if found
- Prevents duplicates while allowing retrieval

---

## Complete Flow

### **Inquiry Processing (Lines 4590-4638)**

```
User: "What's the best way to get downtown?"

STEP 1: Generate FACTUAL KNOWLEDGE
├─ LLM call: generate_inquiry_factual_knowledge()
├─ Prompt emphasizes FACTS, not suggestions
├─ Temperature: 0.4 (more factual)
└─ Output: "The U-Bahn runs all night from the station two blocks over"

STEP 2: Generate THOUGHT
├─ LLM call: generate_inquiry_internal_voice()
├─ Prompt emphasizes THOUGHTS with could/should/maybe
├─ Receives factual_knowledge to inform thought
├─ Temperature: 0.6 (more creative)
└─ Output: "We could take the U-Bahn. It's faster than walking."

STEP 3: Create/Retrieve Memory
├─ Extract keywords: ['downtown', 'u-bahn', 'runs', 'night', 'station']
├─ Check existing memories with these keywords
├─ If found: Return existing with NEW internal voice
├─ If not: Create new memory with keywords as tags
└─ Include internal voice in memory data

STEP 4: Display
├─ If existing: Show "💡 Recalled existing knowledge"
├─ Display memory box with FACT
├─ Display internal voice (THOUGHT) in memory box
└─ Internal voice NOT shown separately (prevents duplication)
```

---

## Key Files & Changes

### **1. agents/narrator_agent.py**

**Lines 2758-2847:** `generate_inquiry_factual_knowledge()`
- NEW method for generating FACTS
- Lower temperature (0.4)
- Explicit examples of facts vs suggestions
- Returns None if character doesn't know

**Lines 2849-2947:** `generate_inquiry_internal_voice()`
- UPDATED to accept `factual_knowledge` parameter
- Generates THOUGHTS based on fact
- Uses could/should/maybe language
- Higher temperature (0.6)

### **2. intent_based_memory_creation.py**

**Lines 328-346:** `_extract_memory_keywords()`
- NEW method for keyword extraction
- Filters stopwords
- Returns top 5 keywords

**Lines 348-375:** `_check_existing_memory()`
- NEW method for duplicate detection
- Searches memories by keyword tags
- Returns existing memory if found

**Lines 377-492:** `create_memory_from_inquiry_answer()`
- UPDATED to accept `internal_voice` parameter
- Extracts keywords from question + answer
- Checks for existing memory first
- Returns existing OR creates new
- Always includes internal voice
- Tags memory with keywords

### **3. MAIN/redesigned_main.py**

**Lines 4553:** Perception-based guard
```python
if not is_inquiry and contextual_result:
    # Only run perception-based if NOT inquiry
```

**Lines 4590-4638:** Inquiry processing
- Generate FACT first
- Generate THOUGHT based on fact
- Create/retrieve memory with internal voice
- Display with appropriate message

**Lines 4649-4653:** Prevent duplicate internal voice
```python
if not is_inquiry or not factual_knowledge:
    print(f"💭 {internal_voice}")
# For inquiries with memory, already shown in memory box
```

---

## Output Examples

### **First Time (New Memory)**

```
User: "What's the best way to get downtown?"

📊 DETAILED CALCULATIONS
[Success calculation display]

📖 INQUIRY RESPONSE

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Knowledge: Downtown U-Bahn Runs
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
We could take the U-Bahn. It's faster than walking, and we've got better things to do than wander the streets.

════════════════════════════════════════════════════════════
```

### **Second Time (Existing Memory)**

```
User: "Can I take the U-Bahn?"

📊 DETAILED CALCULATIONS
[Success calculation display]

📖 INQUIRY RESPONSE

💡 Recalled existing knowledge

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Knowledge: Downtown U-Bahn Runs
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
Yeah, the U-Bahn's still running. Should be safe enough.

════════════════════════════════════════════════════════════
```

### **No Knowledge**

```
User: "What's the best route through the sewers?"

📊 DETAILED CALCULATIONS
[Success calculation display]

📖 INQUIRY RESPONSE

💭 We've never been in the sewers. Maybe we should ask someone who knows the area, or find a map.
```

---

## Benefits Achieved

### **✅ Clear Separation**
- Memories are FACTS (declarative knowledge)
- Internal voice is THOUGHTS (suggestions/reasoning)
- No confusion between the two

### **✅ No Redundancy**
- Keywords prevent duplicate memories
- Same topic mentioned 10 times → 1 memory
- Smart retrieval via keyword matching

### **✅ Always Acknowledged**
- Every memory has internal voice
- User sees character's reaction
- Better awareness of knowledge

### **✅ Context-Aware**
- Same memory, different thoughts each time
- Thoughts adapt to current situation
- Feels natural and dynamic

### **✅ Two Systems Never Conflict**
- Intent-based for inquiries
- Perception-based for normal actions
- Guard prevents both from firing

---

## Testing Results

From terminal output:

**Question:** "What's the best way to get downtown?"

**FACT Generated:**
```
The U-Bahn runs all night from the station two blocks over.
```
✅ Declarative statement
✅ No suggestion words

**THOUGHT Generated:**
```
We could hop on the U-Bahn, but who knows if they're keeping an eye on those stations. 
Maybe we should stick to the shadows, find our own way.
```
✅ Uses "could" and "maybe"
✅ Based on the fact
✅ Character-driven reasoning

**Memory Stored:**
```
📝 Route Knowledge: What's the best way to get downtown?
The U-Bahn runs all night from the station two blocks over.
```
✅ FACT stored, not thought
✅ Can be referenced later

**Memory Recall:**
```
[1] Route Knowledge: What's the best way to get downtown?
    The U-Bahn runs all night from the station two blocks over.
```
✅ Persistent knowledge
✅ Consistent fact

---

## Future Applications

This FACT-first pattern should be extended to:

### **1. Given Actions**
```
Current: Generate narrative → Maybe create memory
Better: Generate FACT → Store memory → Generate narrative using fact
```

### **2. Fallible Situation Overcoming**
```
Current: Generate outcome narrative → Maybe create memory
Better: Generate FACT about outcome → Store memory → Generate narrative
```

### **3. Exchanges (Combat)**
```
Current: Generate exchange narrative → Maybe create memory
Better: Generate FACT about what happened → Store memory → Generate narrative
```

**Benefit:** All memories become consistent FACTS that can inform future narration, rather than flowery descriptions that are hard to reference.

---

## Documentation Files

1. **INQUIRY_FACT_VS_THOUGHT_FIX.md** - Explains FACT vs THOUGHT distinction
2. **TWO_MEMORY_SYSTEMS.md** - Explains intent-based vs perception-based
3. **MEMORY_DEDUPLICATION_SYSTEM.md** - Explains keyword-based deduplication
4. **INQUIRY_SYSTEM_COMPLETE_SUMMARY.md** - This file, complete overview

---

## Status: ✅ COMPLETE

All three issues resolved:
- ✅ FACT vs THOUGHT separation implemented
- ✅ Two memory systems properly guarded
- ✅ Deduplication via keywords working
- ✅ Internal voice always accompanies memories
- ✅ Tested and verified in terminal output
