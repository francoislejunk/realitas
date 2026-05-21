# Inquiry System: FACT vs THOUGHT Fix

## The Critical Distinction

### **MEMORY = FACT (What you KNOW)**
Declarative statements of knowledge:
- "The #7 bus runs from here to downtown every 20 minutes"
- "There's a subway entrance two blocks east on Maple Street"
- "Last time I took the back alleys through the industrial district"
- "The U-Bahn runs all night from the station two blocks over"

### **INTERNAL VOICE = THOUGHT (What you COULD do)**
Suggestions and reasoning:
- "We could take the U-Bahn from the station two blocks over. It's faster."
- "We should avoid the main roads, they're probably watched"
- "Maybe we should ask someone, or look for a bus stop"
- "Let's try the back alleys. Less obvious that way."

## The Problem

The old system was:
1. Generating THOUGHT first ("We should avoid main roads...")
2. Using that THOUGHT as the memory
3. Result: Memory contained suggestions instead of facts

## The Solution

### **New Three-Step Process:**

**STEP 1: Generate FACTUAL KNOWLEDGE**
- LLM generates declarative facts
- Example: "The U-Bahn runs all night from the station two blocks over"
- If character doesn't know → Returns None

**STEP 2: Create MEMORY from FACT**
- Store the fact as a memory
- Display memory box with fact only
- No internal voice in memory display

**STEP 3: Generate THOUGHT based on FACT**
- LLM generates suggestion/reasoning
- Uses the fact (if exists) to inform the thought
- Example: "We could take the U-Bahn. It's still running."
- Display internal voice separately

## Implementation

### **1. New Method: `generate_inquiry_factual_knowledge()`**
**File:** `agents/narrator_agent.py` (lines 2758-2847)

Generates FACTS only:
- Lower temperature (0.4) for more factual responses
- Explicit examples of facts vs suggestions
- Returns None if character doesn't know
- Returns "UNKNOWN" if no knowledge available

**Prompt emphasizes:**
- ✅ GOOD: "The #7 bus runs every 20 minutes"
- ❌ BAD: "We should take the bus"

### **2. Updated Method: `generate_inquiry_internal_voice()`**
**File:** `agents/narrator_agent.py` (lines 2849-2947)

Generates THOUGHTS only:
- Takes `factual_knowledge` parameter
- Uses "could", "should", "maybe", "let's"
- Based on fact if provided, or admits lack of knowledge

**Prompt emphasizes:**
- ✅ GOOD: "We could take the U-Bahn. It's faster."
- ❌ BAD: "The #7 bus runs every 20 minutes"

### **3. Updated Memory Creation**
**File:** `intent_based_memory_creation.py` (lines 328-411)

- Now expects FACTS, not thoughts
- Filters out suggestion words: "we could", "we should", "let's", "maybe"
- Sets `internal_voice` to None (generated separately)
- More specific memory titles

### **4. Main Loop Integration**
**File:** `MAIN/redesigned_main.py` (lines 4588-4642)

**New flow:**
```python
# STEP 1: Generate FACT
factual_knowledge = narrator.generate_inquiry_factual_knowledge(...)

# STEP 2: Create memory from FACT
if factual_knowledge:
    memory_result = intent_memory_creator.create_memory_from_inquiry_answer(
        answer=factual_knowledge  # FACT, not thought
    )
    display_memory_creation(memory_result, show_internal_voice=False)

# STEP 3: Generate THOUGHT based on fact
internal_voice = narrator.generate_inquiry_internal_voice(
    factual_knowledge=factual_knowledge  # Pass fact to inform thought
)
print(f"💭 {internal_voice}")
```

## Expected Output

### **Option 1: Character Knows (Has Fact)**

```
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Route Knowledge: What's the best way to get downtown?
The U-Bahn runs all night from the station two blocks over. Takes about 15 minutes to downtown.

════════════════════════════════════════════════════════════

💭 We could take the U-Bahn from the station two blocks over. It's faster than walking, and we've got better things to do than wander the streets.
```

### **Option 2: Character Doesn't Know (No Fact)**

```
💭 We've never been downtown from here before. Maybe we should ask someone, or look for a bus stop nearby.
```

## Key Principles

1. **Memory = FACT** - Declarative knowledge statements
2. **Internal Voice = THOUGHT** - Suggestions using "could/should/maybe"
3. **Generate FACT first** - Then create thought based on it
4. **Separate display** - Memory shows fact, internal voice shows thought
5. **No duplication** - Each piece of information shown once

## Benefits

✅ **Clear distinction** between knowledge and reasoning
✅ **Memories are facts** that can be referenced consistently
✅ **Thoughts are suggestions** that feel natural and character-driven
✅ **No redundancy** - fact and thought serve different purposes
✅ **Diegetic** - character discovers facts, then reasons about them
