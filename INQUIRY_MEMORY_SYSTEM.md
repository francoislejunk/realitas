# Inquiry Memory System - Complete Design

## Overview

Inquiries (mental actions) need a **multi-layered system** that:
1. **Checks existing memories first** (free info if already known)
2. **Rolls for success** if no memory exists (can fail!)
3. **Creates memory** when new info is learned (avoids duplicates)

## The Problem

**Current system:**
- Inquiries generate internal voice commentary instead of answers
- No memory checking before answering
- No success/failure mechanics
- No memory creation after learning info
- Can duplicate information

**What should happen:**
```
User: "What's the best way to get downtown?"

Step 1: Check memories for "downtown", "transportation", "U-Bahn"
Step 2a: If memory exists → Recall it (free, instant)
Step 2b: If no memory → Roll for success
Step 3a: If success → Generate answer + create memory
Step 3b: If failure → "You're not sure..." (no memory created)
```

---

## System Architecture

### **Phase 1: Memory Check (Free)**

**Check if character already knows this information:**

```python
def check_inquiry_memory(
    user_question: str,
    key_memories_system,
    ua_actor
) -> Optional[Dict[str, Any]]:
    """
    Check if character already knows the answer from memories.
    
    Returns:
        Memory dict if found, None if no relevant memory
    """
    # Extract keywords from question
    keywords = extract_inquiry_keywords(user_question)
    
    # Search memories for relevant information
    relevant_memories = key_memories_system.search_memories(
        query=user_question,
        limit=5
    )
    
    # Filter for DISCOVERY category (learned information)
    info_memories = [
        m for m in relevant_memories 
        if m.category == MemoryCategory.DISCOVERY
    ]
    
    if info_memories:
        # Found relevant memory - return it
        best_match = info_memories[0]
        return {
            'found': True,
            'memory': best_match,
            'answer': best_match.description,
            'source': 'memory_recall'
        }
    
    return None
```

**Display:**
```
User: "What's the best way to get downtown?"

[Memory Check: Found relevant memory]

💭 Internal Voice:
Oh right, we learned this before. The U-Bahn station is just two blocks north.

[Memory Recalled - No roll needed]
```

---

### **Phase 2: Success Roll (If No Memory)**

**If no memory exists, roll to see if character can figure it out:**

```python
def roll_inquiry_success(
    user_question: str,
    ua_actor,
    scene_context: str,
    difficulty: int = 3  # Default difficulty
) -> Dict[str, Any]:
    """
    Roll to determine if character successfully learns the information.
    
    Uses UTAS mechanics:
    - Swiftness (for quick thinking)
    - Spirit (for mental clarity)
    - Serendipity (luck)
    
    Returns:
        Success data with roll breakdown
    """
    # Get relevant stats
    swiftness = ua_actor.sheet.get_trait_value('swiftness')
    spirit_status = ua_actor.sheet.statuses.get(StatusType.SPIRIT)
    spirit_value = spirit_status.value if spirit_status else 5
    
    # Calculate success
    base_roll = swiftness + spirit_value
    serendipity = random.randint(-2, 2)  # Luck factor
    
    total = base_roll + serendipity
    success = total >= difficulty
    
    return {
        'success': success,
        'total': total,
        'breakdown': {
            'swiftness': swiftness,
            'spirit': spirit_value,
            'serendipity': serendipity,
            'difficulty': difficulty
        }
    }
```

**Display:**
```
User: "What's the best way to get downtown?"

[No memory found - Rolling for success]

🎲 INQUIRY ROLL
═══════════════════════════════════════
Swiftness: 3 + Spirit: 7 + Luck: +1 = 11
Difficulty: 8
Result: SUCCESS ✓
═══════════════════════════════════════
```

---

### **Phase 3a: Success - Generate Answer + Create Memory**

**If roll succeeds, generate answer and save as memory:**

```python
def process_successful_inquiry(
    user_question: str,
    ua_actor,
    scene_context: str,
    narrative_context: str,
    key_memories_system
) -> str:
    """
    Generate answer for successful inquiry and create memory.
    
    Returns:
        Narrative answer text
    """
    # Generate answer using narrator
    answer = narrator.generate_inquiry_response(
        user_question=user_question,
        ua_actor=ua_actor,
        scene_description=scene_context,
        narrative_context=narrative_context
    )
    
    # Check for duplicate memory before creating
    existing = check_duplicate_inquiry_memory(
        question=user_question,
        answer=answer,
        key_memories_system=key_memories_system
    )
    
    if not existing:
        # Create memory of learned information
        memory_id = key_memories_system.create_memory(
            title=f"Learned: {extract_inquiry_subject(user_question)}",
            description=answer,
            full_narrative=f"Question: {user_question}\n\nAnswer: {answer}",
            category=MemoryCategory.DISCOVERY,
            importance=MemoryImportance.ROUTINE,
            location=ua_actor.sheet.current_location,
            tags=extract_inquiry_keywords(user_question)
        )
        
        print(f"{Color.INFO}💾 Information learned and saved to memory{Color.RESET}")
    
    return answer
```

**Display:**
```
[SUCCESS - Learning information]

You think through what you know about the area. The U-Bahn station 
is just two blocks north from here. Line 3 runs straight downtown 
and takes about 15 minutes during off-peak hours. Alternatively, 
you could walk, but that'd take close to an hour through the busy streets.

💾 Information learned and saved to memory
```

---

### **Phase 3b: Failure - Uncertain Response**

**If roll fails, character doesn't know:**

```python
def process_failed_inquiry(
    user_question: str,
    ua_actor,
    scene_context: str
) -> str:
    """
    Generate uncertain response for failed inquiry.
    
    Returns:
        Narrative expressing uncertainty
    """
    # Generate uncertain response
    uncertainty_responses = [
        "You try to recall, but nothing concrete comes to mind.",
        "You're not entirely sure about that.",
        "You think you might know, but you can't quite remember.",
        "The information eludes you at the moment.",
        "You draw a blank trying to figure that out."
    ]
    
    # Use LLM for more contextual uncertainty
    prompt = f"""Generate a brief narrative expressing that {ua_actor.sheet.name} doesn't know the answer to this question.

Question: {user_question}
Scene: {scene_context}

Generate 1-2 sentences showing uncertainty or lack of knowledge.
Use 2nd person ("you").

Examples:
- "You try to recall the route, but the details are fuzzy. You'd need to ask someone or check a map."
- "You're not familiar enough with this area to know for sure."
- "You think you've heard something about it, but can't remember the specifics."

Respond with ONLY the uncertainty narrative."""
    
    response = narrator.client.chat.completions.create(
        model=OpenRouterConfig.get_model_for_role("narration"),
        messages=[{"role": "user", "content": prompt}],
        temperature=0.6,
        max_tokens=100
    )
    
    return response.choices[0].message.content.strip()
```

**Display:**
```
[FAILURE - Information unknown]

You try to recall the route, but the details are fuzzy. You'd need 
to ask someone or check a map to be sure.

[No memory created]
```

---

## Memory Deduplication

**Prevent duplicate memories from similar inquiries:**

```python
def check_duplicate_inquiry_memory(
    question: str,
    answer: str,
    key_memories_system
) -> Optional[KeyMemory]:
    """
    Check if similar information already exists in memories.
    
    Returns:
        Existing memory if duplicate found, None otherwise
    """
    # Extract keywords from question and answer
    keywords = extract_inquiry_keywords(question) + extract_inquiry_keywords(answer)
    
    # Search existing DISCOVERY memories
    existing_memories = [
        m for m in key_memories_system.memories.values()
        if m.category == MemoryCategory.DISCOVERY
    ]
    
    # Check for semantic similarity
    for memory in existing_memories:
        # Simple keyword overlap check
        memory_keywords = set(memory.tags + memory.title.lower().split())
        question_keywords = set(keywords)
        
        overlap = len(memory_keywords & question_keywords)
        similarity = overlap / max(len(memory_keywords), len(question_keywords))
        
        if similarity > 0.5:  # 50% keyword overlap
            return memory
    
    return None
```

---

## Complete Flow Integration

**File:** `redesigned_main.py`

```python
if fallible_subtype == 'mental':
    print(f"\n{Color.INFO}📋 INQUIRY (Information Gathering){Color.RESET}")
    
    # PHASE 1: Check existing memories
    memory_check = check_inquiry_memory(
        user_question=user_input,
        key_memories_system=key_memories,
        ua_actor=proactor
    )
    
    if memory_check and memory_check['found']:
        # Memory exists - recall it (free, no roll)
        print(f"{Color.SUCCESS}[Memory Recall - No roll needed]{Color.RESET}\n")
        
        # Display internal voice recalling memory
        memory = memory_check['memory']
        internal_voice = f"Oh right, we learned this before. {memory.description[:100]}..."
        print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
        print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
        print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}\n")
        
        # Display full answer
        print(f"{Color.NARRATIVE}{memory.description}{Color.RESET}")
        
        # Add to narrative context
        narrative_context_manager.add_narrative_event(
            event_type=NarrativeEventType.INFORMATION_GATHERING,
            narrative_text=f"Scene {scene_number}: {proactor.sheet.name} recalled: {user_input}",
            actors_involved=[proactor.sheet.name],
            importance=NarrativeImportance.ROUTINE,
            emotional_tone="thoughtful"
        )
    
    else:
        # PHASE 2: No memory - roll for success
        print(f"{Color.WARNING}[No memory found - Rolling for success]{Color.RESET}\n")
        
        # Determine difficulty based on question complexity
        difficulty = determine_inquiry_difficulty(user_input, scene_description)
        
        # Roll for success
        roll_result = roll_inquiry_success(
            user_question=user_input,
            ua_actor=proactor,
            scene_context=scene_description,
            difficulty=difficulty
        )
        
        # Display roll breakdown
        print(f"{Color.INFO}🎲 INQUIRY ROLL{Color.RESET}")
        print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
        breakdown = roll_result['breakdown']
        print(f"Swiftness: {breakdown['swiftness']} + Spirit: {breakdown['spirit']} + Luck: {breakdown['serendipity']:+d} = {roll_result['total']}")
        print(f"Difficulty: {breakdown['difficulty']}")
        
        if roll_result['success']:
            print(f"{Color.SUCCESS}Result: SUCCESS ✓{Color.RESET}")
            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
            
            # PHASE 3a: Success - generate answer and create memory
            print(f"{Color.SUCCESS}[SUCCESS - Learning information]{Color.RESET}\n")
            
            # Get recent context
            recent_context = narrative_context_manager.get_context_for_llm(
                lookback_events=5,
                importance_threshold="notable"
            )
            
            # Generate answer
            answer = process_successful_inquiry(
                user_question=user_input,
                ua_actor=proactor,
                scene_context=scene_description,
                narrative_context=recent_context,
                key_memories_system=key_memories
            )
            
            # Display answer
            print(f"{Color.NARRATIVE}{answer}{Color.RESET}\n")
            
            # Add to narrative context
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.INFORMATION_GATHERING,
                narrative_text=f"Scene {scene_number}: {proactor.sheet.name} learned: {user_input} → {answer}",
                actors_involved=[proactor.sheet.name],
                importance=NarrativeImportance.NOTABLE,
                emotional_tone="insightful"
            )
        
        else:
            print(f"{Color.ERROR}Result: FAILURE ✗{Color.RESET}")
            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
            
            # PHASE 3b: Failure - uncertain response
            print(f"{Color.WARNING}[FAILURE - Information unknown]{Color.RESET}\n")
            
            # Generate uncertain response
            uncertainty = process_failed_inquiry(
                user_question=user_input,
                ua_actor=proactor,
                scene_context=scene_description
            )
            
            # Display uncertainty
            print(f"{Color.NARRATIVE}{uncertainty}{Color.RESET}\n")
            print(f"{Color.SYSTEM}[No memory created]{Color.RESET}")
            
            # Add to narrative context
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.INFORMATION_GATHERING,
                narrative_text=f"Scene {scene_number}: {proactor.sheet.name} tried to recall: {user_input} (failed)",
                actors_involved=[proactor.sheet.name],
                importance=NarrativeImportance.ROUTINE,
                emotional_tone="uncertain"
            )
    
    # Continue to next turn
    queue_cycle_complete = encounter_checker.current_context.round_manager.advance_turn_queue()
    # ... rest of turn advancement logic
```

---

## Helper Functions

### **Extract Keywords**
```python
def extract_inquiry_keywords(text: str) -> List[str]:
    """Extract relevant keywords from inquiry text"""
    # Remove question words
    question_words = {'what', 'where', 'when', 'how', 'who', 'why', 'can', 'should', 'is', 'are', 'the', 'a', 'an'}
    
    words = text.lower().split()
    keywords = [w for w in words if w not in question_words and len(w) > 2]
    
    return keywords[:5]  # Top 5 keywords
```

### **Determine Difficulty**
```python
def determine_inquiry_difficulty(question: str, scene_context: str) -> int:
    """
    Determine difficulty of inquiry based on complexity.
    
    Returns:
        Difficulty value (3-10)
    """
    # Simple questions (location, time, basic info)
    simple_patterns = ['where is', 'what time', 'how far', 'which way']
    if any(pattern in question.lower() for pattern in simple_patterns):
        return 3  # Easy
    
    # Medium questions (requires thinking)
    medium_patterns = ['how do', 'what should', 'can i', 'is there']
    if any(pattern in question.lower() for pattern in medium_patterns):
        return 5  # Medium
    
    # Complex questions (requires deep knowledge)
    complex_patterns = ['why did', 'what caused', 'how does', 'what if']
    if any(pattern in question.lower() for pattern in complex_patterns):
        return 7  # Hard
    
    return 5  # Default medium
```

---

## Benefits

1. **Memory Integration** - Recalls known information instantly
2. **Success/Failure** - Not all inquiries succeed (realistic)
3. **Learning System** - Creates memories of learned info
4. **No Duplicates** - Checks for existing memories before creating
5. **Diegetic** - Uses internal voice for memory recall
6. **UTAS Mechanics** - Uses existing stat system for rolls

---

## Example Scenarios

### **Scenario 1: Known Information**
```
User: "What's the best way to get downtown?"

[Memory Check: Found relevant memory from 2 days ago]

💭 Oh right, we learned this before. The U-Bahn station is just two blocks north.

The U-Bahn station is just two blocks north. Line 3 runs straight downtown 
and takes about 15 minutes during off-peak hours.

[Memory Recalled - No roll needed]
```

### **Scenario 2: Successful Learning**
```
User: "Where can I find spare parts around here?"

[No memory found - Rolling for success]

🎲 INQUIRY ROLL
Swiftness: 3 + Spirit: 7 + Luck: +1 = 11
Difficulty: 5
Result: SUCCESS ✓

[SUCCESS - Learning information]

You think through what you've seen in the area. There's a junkyard about 
three blocks east, past the old factory. They usually have automotive parts 
and electronics. Alternatively, there's a hardware store on Main Street, 
though their selection is more limited.

💾 Information learned and saved to memory
```

### **Scenario 3: Failed Inquiry**
```
User: "What's the security code for the warehouse?"

[No memory found - Rolling for success]

🎲 INQUIRY ROLL
Swiftness: 3 + Spirit: 4 + Luck: -2 = 5
Difficulty: 8
Result: FAILURE ✗

[FAILURE - Information unknown]

You try to recall if you've ever heard the code, but nothing comes to mind. 
You'd need to find someone who knows or look for it written down somewhere.

[No memory created]
```

---

## Implementation Priority

1. **Phase 1** - Memory checking (prevents redundant rolls)
2. **Phase 2** - Success rolling (adds challenge)
3. **Phase 3a** - Answer generation + memory creation (learning)
4. **Phase 3b** - Failure handling (realism)
5. **Deduplication** - Prevent duplicate memories

All phases work together to create a realistic information-gathering system.
