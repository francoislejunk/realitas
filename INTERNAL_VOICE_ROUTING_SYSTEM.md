# Internal Voice Routing System - Clear Role Definition

## The Problem

**Internal voice is being called from multiple contexts with overlapping purposes:**

1. **Exploration commentary** (ROAM mode)
2. **Intent availability constraints** (EXIST_NOT_HERE, DOES_NOT_EXIST)
3. **Inquiry responses** (answering questions)
4. **Memory recall** (resurfacing memories)
5. **Memory uncovering** (intent-based memories)
6. **Diegetic transitions** (sweeping intents)
7. **Failure awareness** (repeated failures)

**Without clear routing, the system doesn't know:**
- Which context it's in
- What its job is
- What information to prioritize
- How to avoid overlapping with other systems

---

## Solution: Internal Voice Router

### **Central Router Class**

```python
from enum import Enum
from typing import Optional, Dict, Any

class InternalVoiceContext(Enum):
    """Defines the context/purpose of internal voice generation"""
    EXPLORATION = "exploration"              # General ROAM mode commentary
    CONSTRAINT = "constraint"                # Intent availability (can't do action)
    INQUIRY = "inquiry"                      # Answering questions (DEPRECATED - use narrative)
    MEMORY_RECALL = "memory_recall"          # Recalling existing memory
    MEMORY_UNCOVERED = "memory_uncovered"    # New memory discovered
    TRANSITION = "transition"                # Diegetic transition pause
    FAILURE_AWARENESS = "failure_awareness"  # Repeated failure self-criticism
    NONE = "none"                           # No internal voice needed


class InternalVoiceRouter:
    """
    Routes internal voice generation to appropriate handler based on context.
    Ensures clear role definition and prevents overlapping.
    """
    
    def __init__(self, narrator_agent):
        self.narrator = narrator_agent
    
    def generate(
        self,
        context: InternalVoiceContext,
        ua_actor,
        **kwargs
    ) -> Optional[str]:
        """
        Route to appropriate internal voice generator based on context.
        
        Args:
            context: The context/purpose of internal voice
            ua_actor: The User Actor
            **kwargs: Context-specific parameters
            
        Returns:
            Internal voice string or None
        """
        
        # Route to appropriate handler
        if context == InternalVoiceContext.EXPLORATION:
            return self._generate_exploration(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.CONSTRAINT:
            return self._generate_constraint(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.INQUIRY:
            # DEPRECATED - Inquiries should use narrative answers, not internal voice
            raise ValueError("INQUIRY context deprecated - use narrative response instead")
        
        elif context == InternalVoiceContext.MEMORY_RECALL:
            return self._generate_memory_recall(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.MEMORY_UNCOVERED:
            return self._generate_memory_uncovered(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.TRANSITION:
            return self._generate_transition(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.FAILURE_AWARENESS:
            return self._generate_failure_awareness(ua_actor, **kwargs)
        
        elif context == InternalVoiceContext.NONE:
            return None
        
        else:
            raise ValueError(f"Unknown internal voice context: {context}")
    
    # ========================================================================
    # CONTEXT-SPECIFIC GENERATORS
    # ========================================================================
    
    def _generate_exploration(
        self,
        ua_actor,
        action_description: str,
        scene_description: str,
        narrative_context: str,
        success_level: Optional[int] = None,
        outcome_description: Optional[str] = None,
        failure_tracker: Optional['FailureTracker'] = None
    ) -> Optional[str]:
        """
        Generate exploration commentary for ROAM mode.
        
        PURPOSE: Character's thoughts while exploring/observing
        PERSONALITY: Primary driver
        FAILURE AWARENESS: Included if tracker provided
        
        Examples:
        - "We've seen places like this before."
        - "Something doesn't sit right with us."
        - "This should be easy. What could go wrong?"
        """
        
        # Check for failure awareness first
        if failure_tracker:
            consecutive = failure_tracker.get_consecutive_failures(action_description)
            if consecutive >= 2:
                # Escalate to failure awareness context
                return self._generate_failure_awareness(
                    ua_actor,
                    action_description=action_description,
                    consecutive_failures=consecutive,
                    success_level=success_level
                )
        
        # Standard exploration commentary
        return self.narrator.generate_internal_voice(
            ua_actor=ua_actor,
            action_description=action_description,
            scene_description=scene_description,
            narrative_context=narrative_context,
            success_level=success_level,
            outcome_description=outcome_description
        )
    
    def _generate_constraint(
        self,
        ua_actor,
        constraint_type: str,  # "exist_not_here" or "does_not_exist"
        user_intent: str,
        location_hint: Optional[str] = None,
        reason: Optional[str] = None
    ) -> str:
        """
        Generate internal voice for intent availability constraints.
        
        PURPOSE: Explain why action can't be performed (diegetically)
        PERSONALITY: Moderate influence
        CONSTRAINT TYPE: Primary driver
        
        Examples:
        - EXIST_NOT_HERE: "Oh we left our phone at the diner last night..."
        - DOES_NOT_EXIST: "It's been years since we talked to John..."
        """
        
        personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        if constraint_type == "exist_not_here":
            prompt = f"""Generate internal voice explaining why this action can't be done HERE.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**INTENT:** {user_intent}
**LOCATION HINT:** {location_hint or "Unknown"}

**PURPOSE:** Explain where the required item/person is (not here).

**EXAMPLES:**
- "Oh we left our phone at the diner last night, we should hurry and get it back."
- "Right, the laptop is back at the apartment. We'll need to head home first."
- "John's probably at his usual spot downtown. We'd need to go there."

**CRITICAL:**
- Use "we" voice
- 1-2 sentences
- Explain WHERE item/person is
- Personality: {personality}

Respond with ONLY the internal voice."""

        else:  # does_not_exist
            prompt = f"""Generate internal voice explaining why this doesn't exist.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**INTENT:** {user_intent}
**REASON:** {reason or "Unknown"}

**PURPOSE:** Explain why this doesn't exist in the world.

**EXAMPLES:**
- "It's been years since we last got in contact with John... he changed his number."
- "We never had a car. That's just wishful thinking."
- "There's no magic in this world. What am I even thinking?"

**CRITICAL:**
- Use "we" voice
- 1-2 sentences
- Explain WHY it doesn't exist
- Use past tense for memories
- Personality: {personality}

Respond with ONLY the internal voice."""
        
        response = self.narrator.client.chat.completions.create(
            model=self.narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_memory_recall(
        self,
        ua_actor,
        memory_title: str,
        memory_description: str,
        current_context: str
    ) -> str:
        """
        Generate internal voice when recalling existing memory.
        
        PURPOSE: React to remembering something already known
        PERSONALITY: Primary driver
        MEMORY CONTENT: Context
        
        Examples:
        - "Oh right, we learned this before. The U-Bahn is two blocks north."
        - "Yeah, we remember this. Sal's has the best coffee."
        - "Right, we've been here before. Nothing's changed."
        """
        
        personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        prompt = f"""Generate internal voice for recalling an existing memory.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**MEMORY:** {memory_title}
**DETAILS:** {memory_description[:100]}...
**CURRENT CONTEXT:** {current_context[:100]}...

**PURPOSE:** React to remembering something already known.

**PERSONALITY-BASED EXAMPLES:**

Cynical: "Oh right, we learned this before. Not that it helped much."
Optimistic: "Oh right, we learned this before! This could work perfectly."
Analytical: "Oh right, we learned this before. The data suggests..."

**CRITICAL:**
- Use "we" voice
- 1-2 sentences
- Acknowledge recall: "Oh right", "Yeah", "Right"
- Brief reference to memory content
- PERSONALITY DRIVES THE TONE: {personality}

Respond with ONLY the internal voice."""
        
        response = self.narrator.client.chat.completions.create(
            model=self.narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_memory_uncovered(
        self,
        ua_actor,
        memory_title: str,
        memory_description: str,
        trigger: str
    ) -> str:
        """
        Generate internal voice when new memory is uncovered.
        
        PURPOSE: React to discovering/remembering something new
        PERSONALITY: Primary driver
        EMOTIONAL: Higher weight
        
        Examples:
        - "Man, I really miss my mom. I should go see her soon."
        - "I hope Alex is doing okay. We were good together once."
        - "I haven't picked up the guitar in months. Maybe I should."
        """
        
        personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        prompt = f"""Generate internal voice for newly uncovered memory.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**MEMORY:** {memory_title}
**DETAILS:** {memory_description[:150]}...
**TRIGGERED BY:** {trigger}

**PURPOSE:** React to remembering/discovering this memory.

**PERSONALITY-BASED EXAMPLES:**

Cynical: "Great, now I'm thinking about that. Just what I needed."
Optimistic: "Man, I really miss this. I should reconnect with that."
Analytical: "Interesting how this came up. Worth considering."
Emotional: "God, I miss this so much. Why did I let it go?"

**CRITICAL:**
- Use "I" voice (first person, more emotional)
- 1-2 sentences
- Emotional reaction to memory
- Can suggest action ("I should...")
- PERSONALITY DRIVES THE TONE: {personality}

Respond with ONLY the internal voice."""
        
        response = self.narrator.client.chat.completions.create(
            model=self.narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_transition(
        self,
        ua_actor,
        from_action: str,
        to_action: str,
        transition_point: str
    ) -> str:
        """
        Generate internal voice at diegetic transition pause.
        
        PURPOSE: Thoughts between multi-step actions
        PERSONALITY: Moderate influence
        TRANSITION: Context
        
        Examples:
        - "Better eat quick. Got a lot of work waiting at the garage."
        - "Let's get this over with. The sooner the better."
        - "One thing at a time. Focus."
        """
        
        personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        prompt = f"""Generate internal voice at transition between actions.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**FROM:** {from_action}
**TO:** {to_action}
**TRANSITION POINT:** {transition_point}

**PURPOSE:** Thoughts between actions (transitional moment).

**EXAMPLES:**
- "Better eat quick. Got a lot of work waiting."
- "Let's get this over with. The sooner the better."
- "One thing at a time. Focus."

**CRITICAL:**
- Use "we" voice
- 1 sentence only
- Transitional thought
- Can reference next action
- Personality: {personality}

Respond with ONLY the internal voice."""
        
        response = self.narrator.client.chat.completions.create(
            model=self.narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.6,
            max_tokens=80
        )
        
        return response.choices[0].message.content.strip()
    
    def _generate_failure_awareness(
        self,
        ua_actor,
        action_description: str,
        consecutive_failures: int,
        success_level: Optional[int] = None
    ) -> str:
        """
        Generate internal voice with failure awareness.
        
        PURPOSE: Self-criticism after repeated failures
        PERSONALITY: Primary driver
        FAILURE COUNT: Escalation driver
        
        Examples:
        - 2nd: "Twice now. Maybe we need a different approach."
        - 3rd: "Are we really dumb enough to keep doing this?"
        - 4th: "This is insane. Same thing over and over."
        """
        
        personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        # Escalation levels
        if consecutive_failures == 2:
            escalation = "MODERATE - Questioning approach"
        elif consecutive_failures == 3:
            escalation = "HIGH - Self-criticism, exasperation"
        else:  # 4+
            escalation = "EXTREME - Harsh self-criticism, frustration"
        
        prompt = f"""Generate internal voice with failure awareness.

**CHARACTER:** {ua_actor.sheet.name}
**PERSONALITY:** {personality}
**ACTION:** {action_description}
**CONSECUTIVE FAILURES:** {consecutive_failures}
**ESCALATION LEVEL:** {escalation}

**PURPOSE:** Self-aware reaction to repeated failures.

**ESCALATION BY FAILURE COUNT:**

**2nd Failure - MODERATE:**
Cynical: "Twice now. Shocking."
Optimistic: "Okay, clearly we need a different strategy."
Analytical: "Two failures. The pattern suggests this is flawed."

**3rd Failure - HIGH:**
Cynical: "Are we really dumb enough to keep doing this?"
Optimistic: "Okay, we need to seriously rethink this."
Analytical: "Three failures. Continuing is irrational."

**4th+ Failure - EXTREME:**
Cynical: "This is insane. We're idiots."
Optimistic: "This just isn't going to work. Time for something different."
Analytical: "Four failures. 0% success rate. Must abandon."

**CRITICAL:**
- Use "we" voice
- 1-2 sentences
- Escalate frustration based on count: {consecutive_failures}
- PERSONALITY DRIVES THE TONE: {personality}
- Self-criticism increases with failures

Respond with ONLY the internal voice."""
        
        response = self.narrator.client.chat.completions.create(
            model=self.narrator.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            max_tokens=100
        )
        
        return response.choices[0].message.content.strip()
```

---

## Usage Examples

### **1. Exploration (ROAM Mode)**
```python
router = InternalVoiceRouter(narrator)

internal_voice = router.generate(
    context=InternalVoiceContext.EXPLORATION,
    ua_actor=actor,
    action_description="I examine the room",
    scene_description=scene_description,
    narrative_context=recent_narrative,
    success_level=4,
    outcome_description="You notice several interesting details",
    failure_tracker=failure_tracker  # Optional
)
```

### **2. Intent Constraint**
```python
internal_voice = router.generate(
    context=InternalVoiceContext.CONSTRAINT,
    ua_actor=actor,
    constraint_type="exist_not_here",
    user_intent="I want to call my friend",
    location_hint="Phone is at the diner"
)
# Output: "Oh we left our phone at the diner last night..."
```

### **3. Memory Recall**
```python
internal_voice = router.generate(
    context=InternalVoiceContext.MEMORY_RECALL,
    ua_actor=actor,
    memory_title="Downtown U-Bahn Route",
    memory_description="The U-Bahn station is two blocks north...",
    current_context="User asked about getting downtown"
)
# Output: "Oh right, we learned this before. The U-Bahn is two blocks north."
```

### **4. Memory Uncovered**
```python
internal_voice = router.generate(
    context=InternalVoiceContext.MEMORY_UNCOVERED,
    ua_actor=actor,
    memory_title="Loving Mother",
    memory_description="You have a loving mother, Margaret...",
    trigger="User mentioned family"
)
# Output: "Man, I really miss my mom. I should go see her soon."
```

### **5. Transition**
```python
internal_voice = router.generate(
    context=InternalVoiceContext.TRANSITION,
    ua_actor=actor,
    from_action="Eating breakfast",
    to_action="Heading to garage",
    transition_point="After finishing meal"
)
# Output: "Better eat quick. Got a lot of work waiting at the garage."
```

### **6. Failure Awareness**
```python
internal_voice = router.generate(
    context=InternalVoiceContext.FAILURE_AWARENESS,
    ua_actor=actor,
    action_description="I try to pick the lock",
    consecutive_failures=3,
    success_level=1
)
# Output: "Are we really dumb enough to keep doing this? Clearly not working."
```

---

## Integration Points

### **Main Loop - Replace All Internal Voice Calls**

```python
# Initialize router once
internal_voice_router = InternalVoiceRouter(narrator)

# Example: Exploration
if current_mode == SimulationMode.ROAM:
    internal_voice = internal_voice_router.generate(
        context=InternalVoiceContext.EXPLORATION,
        ua_actor=actor,
        action_description=user_input,
        scene_description=scene_description,
        narrative_context=recent_narrative,
        success_level=success_level,
        outcome_description=result,
        failure_tracker=failure_tracker
    )
    
    if internal_voice:
        print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
        print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
        print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}")
```

### **Intent Availability System**

```python
# In intent_availability_system.py
if availability == IntentAvailability.EXIST_NOT_HERE:
    internal_voice = internal_voice_router.generate(
        context=InternalVoiceContext.CONSTRAINT,
        ua_actor=ua_actor,
        constraint_type="exist_not_here",
        user_intent=user_intent,
        location_hint=location_hint
    )
```

### **Memory Systems**

```python
# Memory recall
internal_voice = internal_voice_router.generate(
    context=InternalVoiceContext.MEMORY_RECALL,
    ua_actor=actor,
    memory_title=memory.title,
    memory_description=memory.description,
    current_context=current_situation
)

# Memory uncovered
internal_voice = internal_voice_router.generate(
    context=InternalVoiceContext.MEMORY_UNCOVERED,
    ua_actor=actor,
    memory_title=new_memory.title,
    memory_description=new_memory.description,
    trigger=trigger_description
)
```

---

## Benefits

### **1. Clear Role Definition**
- Each context knows exactly what its job is
- No confusion about purpose
- Explicit context parameter

### **2. No Overlapping**
- Router prevents multiple contexts from firing
- Single entry point for all internal voice
- Context-specific parameters

### **3. Maintainability**
- All internal voice logic in one place
- Easy to add new contexts
- Clear separation of concerns

### **4. Consistency**
- All internal voice uses same router
- Personality enforcement in one place
- Uniform formatting and display

### **5. Debugging**
- Easy to trace which context generated what
- Clear logging of context type
- Simple to test each context independently

---

## Context Priority

**When multiple contexts could apply, priority order:**

1. **CONSTRAINT** - Highest (action blocked)
2. **FAILURE_AWARENESS** - High (3+ failures)
3. **MEMORY_RECALL** - Medium (existing knowledge)
4. **MEMORY_UNCOVERED** - Medium (new memory)
5. **TRANSITION** - Low (between actions)
6. **EXPLORATION** - Lowest (general commentary)

**Example:** If action fails for 3rd time AND it's a constraint, show constraint first, then failure awareness in next action.

---

## Summary

**Problem:** Internal voice called from multiple places with unclear purpose.

**Solution:** `InternalVoiceRouter` class that:
- ✅ Defines explicit contexts (enum)
- ✅ Routes to appropriate handler
- ✅ Prevents overlapping
- ✅ Enforces personality consistently
- ✅ Single entry point for all internal voice

**Result:** Clear, maintainable, non-overlapping internal voice system.
