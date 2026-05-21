# Concrete Detail Tracking System - Usage Guide

## Critical Importance

**THE PROBLEM:** If a character drives a Lamborghini in one scene and then drives a Toyota in the next scene, immersion is COMPLETELY DESTROYED. The same applies to:
- Brand names (Rolex watch → Casio watch)
- Clothing (leather jacket → denim jacket)
- Physical traits (scar on left cheek → no scar)
- Weapons (Colt .45 → Glock 9mm)
- Any other specific detail

**THE SOLUTION:** The Concrete Detail Tracker system stores EVERY specific detail mentioned and ensures it remains consistent across ALL scenes.

---

## How It Works

### 1. Automatic Integration

The `ConcreteDetailTracker` is now integrated into `NarrativeContextManager`. When you use the narrative context system, concrete details are automatically included in LLM prompts.

### 2. Detail Categories

The system tracks these categories:
- **VEHICLE**: Car models, motorcycles, boats, etc.
- **CLOTHING**: What characters wear
- **WEAPON**: Specific weapons and tools
- **LOCATION**: Named places
- **BRAND**: Brand names (watches, phones, sunglasses, etc.)
- **PHYSICAL_TRAIT**: Scars, tattoos, distinctive features
- **POSSESSION**: Items characters own/carry
- **BUILDING**: Specific buildings/establishments
- **RELATIONSHIP**: Specific relationship details
- **BACKSTORY**: Established backstory facts

### 3. Adding Details

#### Method 1: Programmatic Addition
```python
# Add a vehicle detail
narrative_context.add_concrete_detail(
    category="vehicle",
    owner="Marcus Callahan",
    detail_text="1987 Lamborghini Countach, red with black interior, custom exhaust",
    keywords=["car", "vehicle", "lamborghini", "countach", "red"],
    scene_id="scene_001"
)

# Add a clothing detail
narrative_context.add_concrete_detail(
    category="clothing",
    owner="Marcus Callahan",
    detail_text="Worn leather racing jacket with sponsor patches from his glory days",
    keywords=["jacket", "leather", "racing", "clothing"],
    scene_id="scene_001"
)

# Add a brand detail
narrative_context.add_concrete_detail(
    category="brand",
    owner="Mike",
    detail_text="Rolex Submariner watch, scratched but functional",
    keywords=["watch", "rolex", "submariner"],
    scene_id="scene_001"
)
```

#### Method 2: Extraction from Narrative (Future Enhancement)
The system includes a method `extract_and_store_details_from_narrative()` that can automatically detect and store details from narrative text. This can be enhanced with better pattern matching or LLM extraction.

---

## Integration with LLM Prompts

### Getting Context for LLM

When generating narrative, ALWAYS include concrete details:

```python
# Get context with concrete details
context = narrative_context.get_narrative_context_for_llm(
    lookback_events=15,
    scene_id="scene_002",
    active_actors=["Marcus Callahan", "Mike"]  # CRITICAL: Include all active actors
)

# This context will include:
# **ESTABLISHED CONCRETE DETAILS FOR MARCUS CALLAHAN:**
# (These details MUST remain consistent in all narration)
#
# **VEHICLE:**
# - 1987 Lamborghini Countach, red with black interior, custom exhaust
#   (Mentioned in current scene)
#
# **CLOTHING:**
# - Worn leather racing jacket with sponsor patches from his glory days
```

### In Your LLM Prompts

```python
prompt = f"""
{context}

Generate narrative for the following action...

**CRITICAL REQUIREMENT:** You MUST maintain consistency with all established concrete details above. 
If Marcus Callahan's car is mentioned, it MUST be the 1987 Lamborghini Countach. 
If his clothing is mentioned, it MUST be the worn leather racing jacket.
DO NOT introduce new details that contradict established ones.
"""
```

---

## Best Practices

### 1. Add Details Early
When a specific detail is first mentioned in the narrative, immediately add it to the tracker:

```python
# After generating initial scene
if "Lamborghini" in scene_description:
    narrative_context.add_concrete_detail(
        category="vehicle",
        owner=user_actor.name,
        detail_text="Extract the exact vehicle description from scene",
        keywords=["car", "lamborghini", "vehicle"],
        scene_id=current_scene_id
    )
```

### 2. Always Include Active Actors
When getting context for LLM, ALWAYS pass the list of active actors:

```python
# GOOD
context = narrative_context.get_narrative_context_for_llm(
    scene_id=scene_id,
    active_actors=[proactor.name, reactor.name]
)

# BAD - Missing active_actors
context = narrative_context.get_narrative_context_for_llm(
    scene_id=scene_id
)
```

### 3. Be Specific with Details
```python
# GOOD - Very specific
detail_text="1987 Lamborghini Countach, red with black leather interior, custom titanium exhaust, minor dent on passenger door"

# BAD - Too vague
detail_text="A red sports car"
```

### 4. Use Comprehensive Keywords
```python
# GOOD - Multiple relevant keywords
keywords=["car", "vehicle", "lamborghini", "countach", "red", "sports car", "exotic"]

# BAD - Too few keywords
keywords=["car"]
```

---

## Example Integration in Main Loop

```python
# In your main simulation loop

# 1. Initialize narrative context with detail tracking
narrative_context = NarrativeContextManager(
    session_id=session_id,
    storage_directory=Path("./sessions")
)

# 2. When generating initial scene
scene_description = creator_agent.generate_scene(...)

# 3. Extract and store any concrete details mentioned
# (This can be automated or done manually for critical details)
if "car" in scene_description.lower():
    # Extract the car detail and store it
    narrative_context.add_concrete_detail(
        category="vehicle",
        owner=user_actor.name,
        detail_text="[Extract exact description from scene]",
        keywords=["car", "vehicle", ...],
        scene_id=current_scene_id
    )

# 4. When generating narrative for actions
active_actors = [proactor.name, reactor.name]
context = narrative_context.get_narrative_context_for_llm(
    scene_id=current_scene_id,
    active_actors=active_actors
)

# 5. Include context in LLM prompt
narrative_prompt = f"""
{context}

[Your narrative generation instructions]

**CRITICAL:** Maintain consistency with all established concrete details above.
"""

# 6. Generate narrative with LLM
narrative = llm.generate(narrative_prompt)

# 7. Add the narrative event (which updates the context)
narrative_context.add_narrative_event(
    event_type=NarrativeEventType.ACTION_OUTCOME,
    narrative_text=narrative,
    actors_involved=active_actors,
    scene_context=scene_description
)
```

---

## Verification

To verify details are being tracked:

```python
# Get all details for an actor
details = narrative_context.detail_tracker.get_details_for_owner("Marcus Callahan")

for detail in details:
    print(f"{detail.category.value}: {detail.detail_text}")
    print(f"  First mentioned: {detail.first_mentioned}")
    print(f"  Mention count: {detail.mention_count}")
    print(f"  Scenes: {detail.scene_ids}")
```

---

## Common Pitfalls to Avoid

### ❌ DON'T: Forget to pass active_actors
```python
context = narrative_context.get_narrative_context_for_llm(scene_id=scene_id)
# Missing active_actors means no concrete details in context!
```

### ❌ DON'T: Add vague details
```python
narrative_context.add_concrete_detail(
    category="vehicle",
    owner="Marcus",
    detail_text="a car",  # TOO VAGUE!
    keywords=["car"]
)
```

### ❌ DON'T: Ignore the context in prompts
```python
# Getting context but not using it
context = narrative_context.get_narrative_context_for_llm(...)
prompt = "Generate narrative..."  # Context not included!
```

### ✅ DO: Be thorough and specific
```python
narrative_context.add_concrete_detail(
    category="vehicle",
    owner="Marcus Callahan",
    detail_text="1987 Lamborghini Countach LP5000 QV, Rosso red with black leather interior, custom titanium exhaust system, minor dent on passenger door from a racing incident, license plate 'RUSTY87'",
    keywords=["car", "vehicle", "lamborghini", "countach", "red", "sports car", "exotic", "racing"]
)
```

---

## Future Enhancements

1. **Automatic LLM Extraction**: Use LLM to automatically extract concrete details from narrative text
2. **Contradiction Detection**: Alert when new narrative contradicts established details
3. **Detail Importance Weighting**: Track which details are most frequently referenced
4. **Cross-Reference Validation**: Ensure details remain consistent across multiple mentions

---

## Summary

**The Golden Rule:** If it's specific, track it. If it's tracked, maintain it. ALWAYS.

Every time a character's car, clothing, weapon, or any other specific detail is mentioned:
1. Add it to the tracker
2. Include it in LLM context
3. Enforce consistency in prompts
4. Verify it's being maintained

This system ensures that if Marcus drives a Lamborghini in scene 1, he drives the SAME Lamborghini in scene 2, 3, 4, and every scene thereafter. No exceptions.
