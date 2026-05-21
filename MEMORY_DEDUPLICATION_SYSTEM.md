# Memory Deduplication & Internal Voice System

## Problem Solved

### **Issue 1: Redundant Memories**
Without deduplication:
```
Turn 1: "What's the best way downtown?"
→ Creates memory: "U-Bahn runs all night" [tags: u-bahn, downtown]

Turn 5: "Can I take the U-Bahn?"
→ Creates DUPLICATE memory: "U-Bahn runs all night" [tags: u-bahn]

Turn 10: "Where's the U-Bahn station?"
→ Creates ANOTHER duplicate: "U-Bahn runs all night" [tags: u-bahn, station]
```

### **Issue 2: Missing Internal Voice**
Memories need acknowledgment so users know they exist:
```
❌ BAD:
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════
📝 Knowledge: U-Bahn Downtown
The U-Bahn runs all night from the station two blocks over.
════════════════════════════════════════════════════════════
(No internal voice - user might miss the memory)

✅ GOOD:
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════
📝 Knowledge: U-Bahn Downtown
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
We could take the U-Bahn. It's faster than walking.
════════════════════════════════════════════════════════════
```

---

## Solution Implemented

### **1. Keyword Extraction**

**Method:** `_extract_memory_keywords(text)`

Extracts key nouns/concepts from questions and answers:

```python
Question: "What's the best way to get downtown?"
Keywords: ['downtown']

Answer: "The U-Bahn runs all night from the station two blocks over"
Keywords: ['u-bahn', 'runs', 'night', 'station', 'blocks', 'over']

Combined: ['downtown', 'u-bahn', 'runs', 'night', 'station']
```

**Stopwords filtered:** the, a, an, is, are, was, were, to, from, in, on, at, what, where, when, how, why, who, which, best, way, get

**Limit:** Top 5 keywords to avoid over-tagging

### **2. Existing Memory Check**

**Method:** `_check_existing_memory(keywords)`

Searches all memories for matching keywords in tags:

```python
Keywords: ['u-bahn', 'downtown']

Existing memories:
- Memory 1: tags=['inquiry_knowledge', 'u-bahn', 'downtown', 'station']
  → MATCH! Return this memory

- Memory 2: tags=['inquiry_knowledge', 'bus', 'route']
  → No match
```

### **3. Create or Retrieve**

**Flow:**

```python
if existing_memory_found:
    # Return existing memory with NEW internal voice
    return {
        "memory_id": existing.id,
        "memory_title": existing.title,
        "memory_description": existing.description,
        "internal_voice": new_internal_voice,  # Fresh thought
        "trigger_type": "INQUIRY_RETRIEVAL",  # Not creation
        "is_existing": True
    }
else:
    # Create NEW memory with keywords
    tags = ["inquiry_knowledge", "automatic"] + keywords
    memory_id = create_memory(tags=tags, ...)
    return {
        "memory_id": memory_id,
        "memory_title": title,
        "memory_description": description,
        "internal_voice": internal_voice,
        "trigger_type": "INQUIRY_KNOWLEDGE",
        "is_existing": False,
        "keywords": keywords
    }
```

### **4. Display Handling**

**New Memory:**
```
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Knowledge: U-Bahn Downtown Station
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
We could take the U-Bahn. It's faster than walking.

════════════════════════════════════════════════════════════
```

**Existing Memory:**
```
💡 Recalled existing knowledge

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════

📝 Knowledge: U-Bahn Downtown Station
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
We could hop on the U-Bahn, but who knows if they're watching the stations.

════════════════════════════════════════════════════════════
```

**Note:** Internal voice is ALWAYS fresh, even for existing memories. The thought adapts to current context.

---

## Implementation Details

### **File: `intent_based_memory_creation.py`**

**Lines 328-346:** `_extract_memory_keywords()`
- Extracts keywords from text
- Filters stopwords
- Returns top 5 keywords

**Lines 348-375:** `_check_existing_memory()`
- Searches all memories for keyword matches
- Returns existing memory if found

**Lines 377-492:** `create_memory_from_inquiry_answer()`
- Extracts keywords from question + answer
- Checks for existing memory
- Returns existing OR creates new
- Includes internal voice in both cases

### **File: `MAIN/redesigned_main.py`**

**Lines 4590-4638:** Inquiry processing
```python
# STEP 1: Generate FACT
factual_knowledge = narrator.generate_inquiry_factual_knowledge(...)

# STEP 2: Generate THOUGHT
internal_voice = narrator.generate_inquiry_internal_voice(
    factual_knowledge=factual_knowledge  # Inform thought with fact
)

# STEP 3: Create/retrieve memory WITH internal voice
memory_result = intent_memory_creator.create_memory_from_inquiry_answer(
    answer=factual_knowledge,
    internal_voice=internal_voice  # Include thought
)

# Display with appropriate message
if memory_result.get('is_existing'):
    print("💡 Recalled existing knowledge")

display_memory_creation(memory_result, show_internal_voice=True)
```

**Lines 4649-4653:** Prevent duplicate display
```python
if internal_voice:
    # For inquiries with memory, internal voice shown in memory box
    # Only show separately if no memory created
    if not is_inquiry or not factual_knowledge:
        print(f"💭 {internal_voice}")
```

---

## Benefits

### **1. No Redundant Memories**
✅ U-Bahn mentioned 10 times → 1 memory created
✅ Keywords enable smart retrieval
✅ Consistent knowledge base

### **2. Always Acknowledged**
✅ Every memory has internal voice
✅ User sees character's reaction
✅ Better awareness of knowledge

### **3. Context-Aware Thoughts**
✅ Same memory, different thoughts
✅ Thoughts adapt to current situation
✅ Feels natural and dynamic

### **4. Smart Retrieval**
✅ Keyword-based matching
✅ Finds related memories
✅ Avoids exact-match limitations

---

## Examples

### **First Inquiry:**
```
User: "What's the best way to get downtown?"

Keywords: ['downtown', 'u-bahn', 'runs', 'night', 'station']
Existing: None
Action: CREATE new memory

Output:
════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════
📝 Knowledge: Downtown U-Bahn Runs
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
We could take the U-Bahn. It's faster than walking.
════════════════════════════════════════════════════════════
```

### **Second Inquiry (Related):**
```
User: "Can I take the U-Bahn?"

Keywords: ['u-bahn']
Existing: Found memory with tag 'u-bahn'
Action: RETRIEVE existing memory

Output:
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

### **Third Inquiry (Different Context):**
```
User: "Where's the nearest U-Bahn station?"

Keywords: ['nearest', 'u-bahn', 'station']
Existing: Found memory with tags 'u-bahn', 'station'
Action: RETRIEVE existing memory

Output:
💡 Recalled existing knowledge

════════════════════════════════════════════════════════════
🔍 MEMORY UNCOVERED
════════════════════════════════════════════════════════════
📝 Knowledge: Downtown U-Bahn Runs
The U-Bahn runs all night from the station two blocks over.

💭 Internal Voice:
Two blocks over. We know where it is.
════════════════════════════════════════════════════════════
```

---

## Future Enhancements

### **1. Semantic Similarity**
Instead of exact keyword matching, use embeddings:
- "U-Bahn" matches "subway", "metro", "train"
- "downtown" matches "city center", "central district"

### **2. Memory Consolidation**
Merge related memories over time:
- Memory 1: "U-Bahn runs all night"
- Memory 2: "U-Bahn costs 2.50 euros"
- → Consolidated: "U-Bahn Info: Runs all night, costs 2.50 euros"

### **3. Confidence Scoring**
Track how often memory is accessed:
- High confidence → Show immediately
- Low confidence → "I think..." phrasing

### **4. Memory Decay**
Old, unused memories become less accessible:
- Recent: "The U-Bahn runs all night"
- Old: "I vaguely remember something about the U-Bahn..."

---

## Testing Checklist

- [ ] First inquiry creates new memory with keywords
- [ ] Second inquiry with same keywords retrieves existing
- [ ] Both show internal voice
- [ ] Existing memory shows "💡 Recalled existing knowledge"
- [ ] Internal voice is different each time (context-aware)
- [ ] Keywords properly extracted from questions
- [ ] Keywords properly extracted from answers
- [ ] No duplicate memories created
- [ ] Memory tags include all keywords
- [ ] Stopwords filtered correctly
