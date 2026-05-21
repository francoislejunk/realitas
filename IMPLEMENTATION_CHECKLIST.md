# Implementation Checklist - No Manifestation + Concrete Details

## Quick Start Integration

### Step 1: Initialize Systems at Simulation Start

```python
from pathlib import Path
from intent_availability_system import IntentAvailabilitySystem
from narrative_context_system import NarrativeContextManager

# In your main simulation initialization
intent_system = IntentAvailabilitySystem(Path("./sessions"))
narrative_context = NarrativeContextManager(
    session_id=current_session_id,
    storage_directory=Path("./sessions")
)
```

### Step 2: Process User Intent (Before Action Execution)

```python
# When user enters an intent/action
user_input = "I want to go to the diner"

# CRITICAL: Check intent availability FIRST
result = intent_system.evaluate_intent_availability(
    user_intent=user_input,
    narrative_context=get_recent_narrative(),  # Last 5-10 turns
    scene_context=current_scene_description,
    established_facts=get_established_facts(),  # List of known facts
    current_time_of_day=get_current_time()     # Optional but helpful
)

# Handle based on availability
if result["availability"] == IntentAvailability.AVAILABLE_NOW:
    # Proceed to action interpretation and execution
    print(result["diegetic_explanation"])
    proceed_with_action(user_input)
    
elif result["availability"] == IntentAvailability.AVAILABLE_LATER:
    # Show explanation, intent is auto-saved for later
    print(result["diegetic_explanation"])
    prompt_for_different_action()
    
elif result["availability"] == IntentAvailability.AVAILABLE_NEVER:
    # Show explanation, prompt for different action
    print(result["diegetic_explanation"])
    prompt_for_different_action()
```

### Step 3: Extract and Store Concrete Details

```python
# After generating any narrative (scene descriptions, action outcomes, etc.)
narrative_text = generated_narrative

# Extract concrete details from narrative
# Option A: Manual extraction for critical details
if "car" in narrative_text.lower():
    narrative_context.add_concrete_detail(
        category="vehicle",
        owner=character_name,
        detail_text="Extract exact car description from narrative",
        keywords=["car", "vehicle", "model", "color"],
        scene_id=current_scene_id
    )

# Option B: Use automatic extraction (future enhancement)
# narrative_context.detail_tracker.extract_and_store_details_from_narrative(
#     narrative_text, active_actors, scene_id
# )
```

### Step 4: Include Context in LLM Prompts

```python
# When generating narrative with LLM
active_actors = [proactor.name, reactor.name]

# Get context with concrete details
context = narrative_context.get_narrative_context_for_llm(
    scene_id=current_scene_id,
    active_actors=active_actors  # CRITICAL: Always include this
)

# Build prompt with context
prompt = f"""
{context}

Generate narrative for the following action: {user_action}

**CRITICAL REQUIREMENTS:**
1. Maintain consistency with all established concrete details above
2. Use diegetic, logical explanations
3. Do not introduce contradictory details

Generate the narrative:
"""

# Generate with LLM
narrative = llm.generate(prompt)
```

### Step 5: Opportunity Narration Integration

```python
# When generating opportunity narration
deferred_hints = intent_system.get_opportunity_narration_hints()

opportunity_prompt = f"""
{deferred_hints}

{context}

Generate opportunity narration that:
- May bring up deferred intents if timing is appropriate
- Provides new opportunities based on current scene
- Maintains all concrete details

Generate:
"""

# After using a deferred intent in narration
intent_system.mark_intent_triggered(intent_index=0)
```

---

## Complete Integration Checklist

### Initial Setup
- [ ] Import `IntentAvailabilitySystem` and `NarrativeContextManager`
- [ ] Initialize both systems at simulation start
- [ ] Set up session storage directory

### For Each User Intent
- [ ] Call `evaluate_intent_availability()` BEFORE action execution
- [ ] Pass comprehensive context (narrative, facts, time)
- [ ] Handle all three availability cases (NOW, LATER, NEVER)
- [ ] Use diegetic explanations in responses

### For Each Narrative Generation
- [ ] Get context with `get_narrative_context_for_llm()`
- [ ] ALWAYS pass `active_actors` parameter
- [ ] Include context at top of LLM prompt
- [ ] Add enforcement instructions to prompt

### After Each Narrative Generation
- [ ] Extract concrete details from narrative
- [ ] Store details with `add_concrete_detail()`
- [ ] Be specific with detail descriptions
- [ ] Use comprehensive keywords

### For Opportunity Narration
- [ ] Get deferred intents with `get_opportunity_narration_hints()`
- [ ] Include hints in opportunity narration prompt
- [ ] Mark intents as triggered when used

### Maintenance
- [ ] Verify details are being stored (check storage directory)
- [ ] Monitor deferred intents list
- [ ] Ensure context is being included in prompts
- [ ] Test consistency across scenes

---

## Common Integration Points

### In Main Simulation Loop

```python
# At start of simulation
intent_system = IntentAvailabilitySystem(Path("./sessions"))
narrative_context = NarrativeContextManager(session_id, Path("./sessions"))

while simulation_running:
    # Get user input
    user_input = get_user_input()
    
    # Check intent availability
    availability = intent_system.evaluate_intent_availability(
        user_intent=user_input,
        narrative_context=get_recent_narrative(),
        scene_context=current_scene,
        established_facts=established_facts,
        current_time_of_day=current_time
    )
    
    if availability["availability"] == IntentAvailability.AVAILABLE_NOW:
        # Get context with concrete details
        context = narrative_context.get_narrative_context_for_llm(
            scene_id=scene_id,
            active_actors=get_active_actors()
        )
        
        # Generate narrative with context
        narrative = generate_narrative_with_llm(user_input, context)
        
        # Extract and store new concrete details
        extract_and_store_details(narrative, get_active_actors(), scene_id)
        
    elif availability["availability"] == IntentAvailability.AVAILABLE_LATER:
        # Show explanation (intent auto-saved)
        print(availability["diegetic_explanation"])
        
    else:  # AVAILABLE_NEVER
        # Show explanation
        print(availability["diegetic_explanation"])
```

### In Scene Transition

```python
# When transitioning to new scene
new_scene_context = narrative_context.get_narrative_context_for_llm(
    scene_id=new_scene_id,
    active_actors=actors_in_new_scene
)

# Include deferred intents for opportunity narration
deferred_hints = intent_system.get_opportunity_narration_hints()

scene_prompt = f"""
{new_scene_context}

{deferred_hints}

Generate scene transition that:
- Maintains all concrete details
- May bring up deferred intents if appropriate
- Provides natural scene progression
"""
```

### In Continuity Check

```python
# When checking action continuity
# Intent availability can inform continuity decisions

continuity_context = f"""
Intent Availability: {availability["availability"].value}
Reason: {availability["diegetic_explanation"]}

Concrete Details:
{narrative_context.get_concrete_details_for_actor(actor_name, scene_id)}

Check if this action is continuous with established world...
"""
```

---

## Testing Your Integration

### Test 1: Supported Intent
```python
# Set up: Mention a car in scene 1
# Test: User says "I want to drive my car" in scene 2
# Expected: AVAILABLE_NOW or AVAILABLE_LATER (50/50)
# Expected: Car details maintained in narrative
```

### Test 2: Unsupported Intent
```python
# Set up: Never mention any friends
# Test: User says "I want to call my friend"
# Expected: 1/3 chance each for NOW, LATER, NEVER
# Expected: Diegetic explanation for result
```

### Test 3: Concrete Detail Consistency
```python
# Set up: Character drives red Lamborghini in scene 1
# Test: Generate narrative in scene 5
# Expected: Context includes "red Lamborghini"
# Expected: Narrative maintains same car
```

### Test 4: Deferred Intent Retrieval
```python
# Set up: Intent marked AVAILABLE_LATER
# Test: Generate opportunity narration
# Expected: Deferred intent appears in hints
# Expected: Can be brought up in narration
```

---

## Troubleshooting

### Problem: Intents always AVAILABLE_NOW
**Solution:** Check that you're passing established_facts correctly. Empty facts list means no context support.

### Problem: Concrete details not appearing in context
**Solution:** Verify you're passing `active_actors` parameter to `get_narrative_context_for_llm()`.

### Problem: Details changing between scenes
**Solution:** Check that context is being included in LLM prompts with enforcement instructions.

### Problem: Deferred intents not appearing
**Solution:** Verify intents are being saved (check storage directory) and that you're calling `get_opportunity_narration_hints()`.

---

## Performance Considerations

### LLM Calls
- Intent availability: 1-2 LLM calls per user intent
- Context generation: No LLM calls (retrieval only)
- Diegetic explanation: 1 LLM call per intent

### Storage
- Concrete details: Saved to disk every 10 events
- Deferred intents: Saved immediately when deferred
- Both use JSON format for easy inspection

### Optimization
- Context caching: 5-minute cache for narrative context
- Keyword indexing: Fast detail lookup by keywords
- Lazy loading: Details loaded only when needed

---

## Summary

**Two systems, one goal: Perfect immersion**

1. **Intent Availability** → Prevents manifestation
2. **Concrete Details** → Prevents inconsistency

**Integration is simple:**
1. Check intent availability before action
2. Get context with concrete details for LLM
3. Store new details after narrative generation
4. Include deferred intents in opportunity narration

**Result:**
- ✅ Realistic world (has constraints)
- ✅ Consistent details (car stays same)
- ✅ Coherent narrative (makes sense)
- ✅ Perfect immersion (feels real)
