# Internal Voice Critical Fixes - Two Major Issues

## Issue #1: Inquiry System Confusion - Comments Instead of Answers

### **Problem**
When users ask questions (inquiries), they're getting **internal voice commentary** instead of **actual answers**.

**Example of Current Broken Behavior:**
```
User: "What's the best way to get downtown?"

Current (WRONG):
💭 We should probably figure out how to get downtown...
[No actual answer provided]

Expected (CORRECT):
The U-Bahn station is just two blocks north. Line 3 runs straight 
downtown and takes about 15 minutes. Alternatively, we could walk, 
but that'd take close to an hour.
```

### **Root Cause**
The inquiry system has **role confusion**:

1. **Mental Actions (fallible_subtype: "mental")** in `interpreter_agent.py`
   - Classified as "information gathering"
   - Generates action narrative via `interpret_fallible_action()`
   - Then triggers **internal voice commentary** (not answers)

2. **No Dedicated Inquiry Response System**
   - No `generate_inquiry_response()` method being called
   - Internal voice is commenting on the question, not answering it

### **What Should Happen**

**Questions should get ANSWERS (narrative description), not commentary:**

```python
# Current (WRONG):
if fallible_subtype == 'mental':
    narrative_response = conductor.interpret_fallible_action(user_input, proactor)
    # Then internal voice comments on it
    internal_voice = narrator.generate_internal_voice(...)  # "We should figure this out..."

# Should be (CORRECT):
if fallible_subtype == 'mental':
    # Generate ANSWER using narrator's inquiry response
    inquiry_answer = narrator.generate_inquiry_response(
        user_question=user_input,
        scene_context=scene_description,
        character_knowledge=character_knowledge,
        recent_context=recent_narrative
    )
    # Display answer (narrative, not internal voice)
    print(f"{Color.NARRATIVE}{inquiry_answer}{Color.RESET}")
```

### **Fix Required - Complete Memory-Based Inquiry System**

**File:** `redesigned_main.py` (lines ~6699-6723)

**The inquiry system needs THREE phases:**
1. **Check memories first** (free if known)
2. **Roll for success** if no memory (can fail!)
3. **Create memory** when learning new info (avoid duplicates)

**Current Code:**
```python
if fallible_subtype == 'mental':
    print(f"\n{Color.INFO}📋 FALLIBLE ACTION (MENTAL){Color.RESET}")
    
    # Generate narrative for the information gathering action
    try:
        proactor_action_data = conductor.interpret_fallible_action(user_input, proactor)
        narrative_response = proactor_action_data.get('narrative_description', user_input)
    except Exception as e:
        logger.log_error(f"Failed to interpret information gathering action: {e}")
        narrative_response = f"{proactor.sheet.name} attempts to {user_input}"
    
    # Display the action narrative
    print(f"{Color.NARRATIVE}{narrative_response}{Color.RESET}")
```

**Should Be (Complete 3-Phase System):**
```python
if fallible_subtype == 'mental':
    print(f"\n{Color.INFO}📋 INQUIRY (Information Gathering){Color.RESET}")
    
    # PHASE 1: Check existing memories first
    memory_check = check_inquiry_memory(
        user_question=user_input,
        key_memories_system=key_memories,
        ua_actor=proactor
    )
    
    if memory_check and memory_check['found']:
        # Memory exists - recall it (free, no roll needed)
        print(f"{Color.SUCCESS}[Memory Recall - No roll needed]{Color.RESET}\n")
        
        # Display internal voice recalling memory
        memory = memory_check['memory']
        internal_voice = f"Oh right, we learned this before. {memory.description[:100]}..."
        print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
        print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
        print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}\n")
        
        # Display full answer from memory
        print(f"{Color.NARRATIVE}{memory.description}{Color.RESET}")
        
    else:
        # PHASE 2: No memory - roll for success
        print(f"{Color.WARNING}[No memory found - Rolling for success]{Color.RESET}\n")
        
        # Determine difficulty
        difficulty = determine_inquiry_difficulty(user_input, scene_description)
        
        # Roll for success (Swiftness + Spirit + Serendipity)
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
            # PHASE 3a: SUCCESS - Generate answer and create memory
            print(f"{Color.SUCCESS}Result: SUCCESS ✓{Color.RESET}")
            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
            print(f"{Color.SUCCESS}[SUCCESS - Learning information]{Color.RESET}\n")
            
            # Get context
            recent_context = narrative_context_manager.get_context_for_llm(
                lookback_events=5,
                importance_threshold="notable"
            )
            
            # Generate answer
            answer = narrator.generate_inquiry_response(
                user_question=user_input,
                ua_actor=proactor,
                scene_description=scene_description,
                narrative_context=recent_context,
                current_time=master_time.get_current_time_context()
            )
            
            # Display answer
            print(f"{Color.NARRATIVE}{answer}{Color.RESET}\n")
            
            # Check for duplicate before creating memory
            existing = check_duplicate_inquiry_memory(
                question=user_input,
                answer=answer,
                key_memories_system=key_memories
            )
            
            if not existing:
                # Create memory of learned information
                key_memories.create_memory(
                    title=f"Learned: {extract_inquiry_subject(user_input)}",
                    description=answer,
                    full_narrative=f"Question: {user_input}\n\nAnswer: {answer}",
                    category=MemoryCategory.DISCOVERY,
                    importance=MemoryImportance.ROUTINE,
                    location=proactor.sheet.current_location,
                    tags=extract_inquiry_keywords(user_input)
                )
                print(f"{Color.INFO}💾 Information learned and saved to memory{Color.RESET}")
        
        else:
            # PHASE 3b: FAILURE - Uncertain response (no memory created)
            print(f"{Color.ERROR}Result: FAILURE ✗{Color.RESET}")
            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
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
        narrative_text=f"Scene {scene_number}: {proactor.sheet.name}: {user_input}",
        actors_involved=[proactor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="investigative"
    )
    
    # Continue to next turn
    queue_cycle_complete = encounter_checker.current_context.round_manager.advance_turn_queue()
    # ... rest of turn advancement
```

**See `INQUIRY_MEMORY_SYSTEM.md` for complete implementation details including all helper functions.**

**Then add the method to NarratorAgent:**

**File:** `narrator_agent.py`

```python
def generate_inquiry_response(
    self,
    user_question: str,
    ua_actor,
    scene_description: str,
    narrative_context: str,
    current_time: Dict[str, Any]
) -> str:
    """
    Generate narrative ANSWER to user's inquiry/question.
    
    This is NOT internal voice - this is descriptive narrative that answers
    the question from the character's knowledge and perspective.
    
    Args:
        user_question: The question being asked
        ua_actor: The User Actor asking
        scene_description: Current scene
        narrative_context: Recent events
        current_time: Current time context
        
    Returns:
        Narrative answer (2-4 sentences)
    """
    ua_name = ua_actor.sheet.name
    internal_personality = ua_actor.sheet.personality_traits.get("internal", "Observant")
    
    prompt = f"""Generate a narrative ANSWER to {ua_name}'s question.

**CHARACTER:** {ua_name}
**QUESTION:** {user_question}

**CURRENT SCENE:**
{scene_description}

**RECENT CONTEXT:**
{narrative_context[:300] if narrative_context else "No recent context"}

**TIME:** {current_time.get('time_of_day', 'Unknown')}

**INSTRUCTIONS:**
Generate a 2-4 sentence narrative ANSWER to the question.

**CRITICAL:**
- This is NOT internal voice - use descriptive narrative
- ANSWER the question based on character's knowledge and scene context
- Use 2nd person ("you") for narrative descriptions
- Provide concrete, useful information when possible
- If character doesn't know, describe what they CAN observe/deduce
- Keep it grounded in the scene and character's perspective

**EXAMPLES:**

Question: "What's the best way to get downtown?"
Answer: "You recall the U-Bahn station is just two blocks north from here. Line 3 runs straight downtown and takes about 15 minutes during off-peak hours. Alternatively, you could walk, but that'd take close to an hour through the busy streets."

Question: "Do I know anyone who could help?"
Answer: "You think through your contacts. Vince at the garage owes you a favor from last month - he's got connections with the racing crowd. There's also Lena, though you haven't talked to her in weeks after that argument."

Question: "What time is it?"
Answer: "You glance at your watch. It's around 3:15 PM - the afternoon sun is starting to dip lower in the sky, casting long shadows across the street."

Question: "Can I hear anything unusual?"
Answer: "You pause and listen carefully. The usual city sounds - distant traffic, muffled conversations from nearby apartments. Nothing immediately stands out as unusual, though there's a faint mechanical hum coming from somewhere below."

**IMPORTANT:**
- Answer based on what the character WOULD know
- Don't invent major plot points or people
- Stay consistent with established context
- Provide actionable information when possible

Respond with ONLY the narrative answer (no quotes, no preamble)."""

    try:
        response = self.client.chat.completions.create(
            model=OpenRouterConfig.get_model_for_role("narration"),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=200
        )
        
        answer = response.choices[0].message.content.strip()
        return answer if answer else "You consider the question carefully, but no clear answer comes to mind."
        
    except Exception as e:
        self.logger.error(f"Error generating inquiry response: {e}")
        return "You pause to think about that."
```

---

## Issue #2: Internal Voice Losing Personality Over Time

### **Problem**
Internal voice starts with personality but becomes **generic and bland** the longer the simulation runs.

**Example:**
```
Early simulation (GOOD):
💭 We've seen worse. This is nothing we can't handle.

Later simulation (BAD - Generic):
💭 We should probably check that out.
💭 This seems interesting.
💭 We need to be careful here.
```

### **Root Cause**

**The internal personality is being IGNORED by the LLM over time.**

Looking at the prompt in `narrator_agent.py` (lines 2730-2815):

```python
**ACTOR PERSONALITY:**
- Internal: {internal_personality}
- External: {external_personality}

# ... lots of other instructions ...

**CRITICAL REQUIREMENTS:**
- Based on {ua_name}'s internal personality: {internal_personality}
```

**The problem:** Personality is mentioned but not **ENFORCED**. The LLM sees it once at the top, then forgets it among all the other instructions.

### **Why This Matters**

**You created internal/external personalities specifically to drive the internal voice!**

From your request:
> "the internal personality should be the DRIVING FORCE on how the internal voice narrates things to the user its the sole reason we created the internal and external personalities so that they can bring life to the UA"

**Current prompt treats personality as a suggestion, not a requirement.**

### **Fix Required**

**File:** `narrator_agent.py` (lines 2730-2815)

**Restructure the prompt to make personality THE PRIMARY DRIVER:**

```python
base_prompt = f"""You are generating {ua_name}'s internal thoughts during a ROAM mode action.

**═══════════════════════════════════════════════════════════════**
**CRITICAL: PERSONALITY IS THE DRIVING FORCE**
**═══════════════════════════════════════════════════════════════**

**{ua_name}'s INTERNAL PERSONALITY (THIS DEFINES HOW THEY THINK):**
{internal_personality}

**EVERY THOUGHT MUST REFLECT THIS PERSONALITY.**
- If personality is "Cynical and distrustful" → thoughts are cynical and distrustful
- If personality is "Optimistic and hopeful" → thoughts are optimistic and hopeful
- If personality is "Analytical and methodical" → thoughts are analytical and methodical
- If personality is "Impulsive and emotional" → thoughts are impulsive and emotional

**THIS IS NON-NEGOTIABLE. THE PERSONALITY DEFINES THE VOICE.**

**═══════════════════════════════════════════════════════════════**

**CURRENT STATE:**
- Stamina: {current_stamina}/10 | Spirit: {current_spirit}/10 | Supply: {current_supply}/10
- Current Task: {current_task if current_task else "None"}
- Key Items: {', '.join(inventory_items) if inventory_items else "None"}
- Relationships: {', '.join(relationships) if relationships else "None"}

**CURRENT ACTION:**
{action_description}

**SCENE:**
{scene_description[:300]}...

**RECENT CONTEXT:**
{narrative_context[:200] if narrative_context else "No recent context"}

**OUTCOME:**
{outcome_description if outcome_description else "Action in progress"}
{f"Success Level: {self._get_success_descriptor(success_level)}" if success_level else ""}

**═══════════════════════════════════════════════════════════════**
**HOW TO GENERATE THE INTERNAL VOICE:**
**═══════════════════════════════════════════════════════════════**

1. **READ THE INTERNAL PERSONALITY AGAIN:** {internal_personality}

2. **ASK: How would someone with THIS personality think about THIS action?**

3. **GENERATE THOUGHT that EMBODIES that personality**

**EXAMPLES BY PERSONALITY TYPE:**

**Cynical and distrustful:**
- "We've seen this before. Never ends well."
- "Sure, this looks safe. Until it isn't."
- "They're probably lying. They always are."

**Optimistic and hopeful:**
- "This could actually work out. We've got a good feeling."
- "Things are looking up. Finally catching a break."
- "We can make this happen. Just need to stay positive."

**Analytical and methodical:**
- "Let's think this through. Three possible approaches."
- "The pattern suggests this is the optimal route."
- "We need more data before committing to this."

**Impulsive and emotional:**
- "Screw it. Let's just do it."
- "This feels right. Going with our gut."
- "Can't think straight. Too much going on."

**Cautious and paranoid:**
- "Something's off. We should be careful."
- "What if this is a trap? Better check twice."
- "Too quiet. That's never a good sign."

**Confident and bold:**
- "We've got this. No problem."
- "Easy. We've handled worse."
- "Let's show them how it's done."

**═══════════════════════════════════════════════════════════════**

**TECHNICAL REQUIREMENTS:**
- Use "we", "us", "our" (NOT "you" or "I")
- 1-2 sentences maximum
- Directly relevant to current action
- Can suggest solutions or be wrong sometimes
- Keep memories vague and general

**BUT ABOVE ALL: EMBODY THE INTERNAL PERSONALITY IN EVERY WORD.**

**═══════════════════════════════════════════════════════════════**

**FINAL CHECK BEFORE RESPONDING:**
1. Does this thought sound like someone who is: {internal_personality}?
2. If NO → Rewrite it to match the personality
3. If YES → Respond with the thought

**═══════════════════════════════════════════════════════════════**

Respond with ONLY the internal voice narration (no quotes, no preamble). Return empty if no meaningful internal reaction is needed."""
```

### **Additional Enforcement: Add Personality Examples to System Message**

**Also update the system message to reinforce personality:**

```python
system_message = f"""You are the internal voice of {ua_name}.

Your SOLE PURPOSE is to think like someone with this personality:
{internal_personality}

EVERY thought you generate MUST reflect this personality.
This is not optional. This is your core function.

Use "we", "us", "our" voice. Keep it brief (1-2 sentences).
But NEVER compromise on personality consistency."""
```

---

## Summary of Fixes

### **Fix #1: Inquiry Responses**
- **Problem:** Questions get commentary instead of answers
- **Solution:** Create `generate_inquiry_response()` method in NarratorAgent
- **Result:** Questions get narrative answers, not internal voice comments

### **Fix #2: Personality Enforcement**
- **Problem:** Internal voice becomes generic over time
- **Solution:** Restructure prompt to make personality THE PRIMARY DRIVER
- **Result:** Every internal voice thought embodies the character's internal personality

---

## Implementation Priority

**BOTH fixes are critical:**

1. **Fix #1** - Users can't get information (breaks gameplay)
2. **Fix #2** - Internal voice loses its purpose (breaks immersion)

**Recommended order:**
1. Fix #2 first (personality enforcement) - affects all internal voice
2. Fix #1 second (inquiry responses) - affects specific inquiry flow

Both should be implemented together for complete fix.

---

## Testing After Fixes

### **Test #1: Inquiry Responses**
```
User: "What's the best way to get downtown?"
Expected: Narrative answer describing U-Bahn, walking routes, etc.
NOT: Internal voice comment like "We should figure that out..."
```

### **Test #2: Personality Consistency**
```
Character with "Cynical and distrustful" personality:

Early: "We've seen this before. Never ends well."
Later: "Sure, this looks safe. Until it isn't."
Even Later: "They're probably lying. They always are."

ALL should sound cynical and distrustful, not generic.
```

---

## Root Philosophy

**Internal Voice exists to make the character FEEL ALIVE through their unique perspective.**

- **Inquiries** should get ANSWERS (narrative), not commentary
- **Personality** should be the DRIVING FORCE of how thoughts are expressed
- **Consistency** should be maintained throughout the entire simulation

The internal personality is not just metadata - it's the **soul of the internal voice**.
