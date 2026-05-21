# Journey Chunking System Integration Guide

## Problem Statement

**BEFORE:** User says "I head to a nearby restaurant" → System narrates instant teleportation
**AFTER:** User says "I head to a nearby restaurant" → System narrates 3-4 chunks showing the journey

## The Rule of 3's Principle

Every action that takes more than 5 minutes should be broken into **3-minute narrative chunks**:

- **10-minute walk** = 3-4 chunks
- **30-minute drive** = 10 chunks  
- **5-minute action** = 1 chunk (no chunking needed)

## How It Works

### 1. Detection Phase
```python
from journey_chunking_system import get_journey_chunking_system

chunking_system = get_journey_chunking_system()

# Check if action needs chunking
should_chunk = chunking_system.should_chunk_action(
    user_input="I head to a nearby restaurant",
    action_description="Derek heads to a nearby restaurant to talk to the waitress"
)

# Returns True if:
# - Action involves travel (walk, drive, head to, etc.)
# - Estimated duration > 5 minutes
```

### 2. Duration Estimation
```python
# System estimates duration using LLM + keywords
estimated_duration = chunking_system._estimate_duration(
    user_input="I head to a nearby restaurant",
    action_description="Derek heads to a nearby restaurant"
)

# Returns: 10.0 (minutes)
```

### 3. Chunk Creation
```python
# Break journey into chunks
chunks = chunking_system.create_journey_chunks(
    user_input="I head to a nearby restaurant",
    action_description="Derek heads to a nearby restaurant",
    estimated_duration=10.0,
    current_location="Rusty Wrench Auto Shop",
    destination="Nearby Restaurant"
)

# Returns: [
#   JourneyChunk(chunk_number=1, chunk_type="departure", ...),
#   JourneyChunk(chunk_number=2, chunk_type="transit", ...),
#   JourneyChunk(chunk_number=3, chunk_type="transit", ...),
#   JourneyChunk(chunk_number=4, chunk_type="arrival", ...)
# ]
```

### 4. Narrative Generation (Per Chunk)
```python
for chunk in chunks:
    # Generate narrative prompt for this chunk
    chunk_prompt = chunking_system.generate_chunk_narrative_prompt(
        chunk=chunk,
        user_input=user_input,
        action_description=action_description,
        actor_name=actor.sheet.name,
        scene_description=scene_description
    )
    
    # Use NarratorAgent to generate narrative
    chunk_narrative = narrator.generate_exploration_action_result_narrative(
        user_input=user_input,
        actor=actor,
        scene_description=chunk_prompt,  # Use chunk prompt as context
        success_total=success_total,
        time_context=time_context
    )
    
    # Display chunk narrative
    print(f"\n📖 JOURNEY CHUNK {chunk.chunk_number}/{chunk.total_chunks}")
    print(chunk_narrative)
    
    # Advance time by chunk duration
    time_coordinator.advance_time(
        duration=chunk.duration_minutes * 60,  # Convert to seconds
        action_type="travel"
    )
    
    # Update scene description for next chunk
    scene_description = chunk.location_context
```

## Integration into redesigned_main.py

### Location: After action interpretation, before narrative generation

```python
# EXISTING CODE (around line 3400)
action_result = interpreter.interpret_user_action(
    user_input=user_input,
    actor=user_actor,
    scene_description=scene_description,
    present_nuas=available_npcs,
    visible_objects=visible_objects,
    accessible_paths=accessible_paths
)

# NEW CODE - Check for journey chunking
from journey_chunking_system import get_journey_chunking_system

chunking_system = get_journey_chunking_system()
should_chunk = chunking_system.should_chunk_action(
    user_input=user_input,
    action_description=action_result['action_description']
)

if should_chunk:
    print(f"\n🚶 JOURNEY DETECTED - Breaking into realistic segments...")
    
    # Estimate duration
    estimated_duration = chunking_system._estimate_duration(
        user_input=user_input,
        action_description=action_result['action_description']
    )
    
    print(f"📏 Estimated journey time: {estimated_duration:.1f} minutes")
    
    # Extract destination from action
    # TODO: Add destination extraction logic
    destination = "destination"  # Placeholder
    
    # Create chunks
    chunks = chunking_system.create_journey_chunks(
        user_input=user_input,
        action_description=action_result['action_description'],
        estimated_duration=estimated_duration,
        current_location=persistent_context.current_location,
        destination=destination
    )
    
    print(f"📦 Journey broken into {len(chunks)} chunks")
    
    # Process each chunk
    for chunk in chunks:
        print(f"\n{'='*60}")
        print(f"📍 CHUNK {chunk.chunk_number}/{chunk.total_chunks}: {chunk.chunk_type.upper()}")
        print(f"⏱️  Duration: {chunk.duration_minutes:.1f} minutes")
        print(f"{'='*60}\n")
        
        # Generate chunk narrative prompt
        chunk_prompt = chunking_system.generate_chunk_narrative_prompt(
            chunk=chunk,
            user_input=user_input,
            action_description=action_result['action_description'],
            actor_name=user_actor.sheet.name,
            scene_description=scene_description
        )
        
        # Generate narrative for this chunk
        chunk_narrative = narrator.generate_exploration_action_result_narrative(
            user_input=user_input,
            actor=user_actor,
            scene_description=chunk_prompt,
            success_total=action_result.get('success_total', 3),
            time_context=time_context
        )
        
        # Display chunk narrative
        print(f"📖 {chunk_narrative}\n")
        
        # Advance time
        time_coordinator.advance_time(
            duration=chunk.duration_minutes * 60,
            action_type="travel"
        )
        
        # Update scene description for next chunk
        if chunk.chunk_type == "arrival":
            # Update location on final chunk
            persistent_context.current_location = destination
            scene_description = f"You have arrived at {destination}."
        else:
            scene_description = chunk.location_context
        
        # Small pause between chunks for readability
        import time
        time.sleep(0.5)
    
    print(f"\n✅ Journey complete! You have arrived at {destination}.")
    
    # Skip normal narrative generation - we already narrated the journey
    continue

# EXISTING CODE - Normal narrative generation for non-chunked actions
else:
    # Generate normal exploration narrative
    narrative = narrator.generate_exploration_action_result_narrative(...)
```

## Example Output

### User Input:
```
"I head to a nearby restaurant to talk to the waitress"
```

### System Output:
```
🚶 JOURNEY DETECTED - Breaking into realistic segments...
📏 Estimated journey time: 10.0 minutes
📦 Journey broken into 4 chunks

============================================================
📍 CHUNK 1/4: DEPARTURE
⏱️  Duration: 3.0 minutes
============================================================

📖 You step out of the Rusty Wrench Auto Shop, the cool autumn air 
hitting your face as you lock the door behind you. The street is 
quiet this morning, with only a few cars passing by. You start 
walking east toward the commercial district.

============================================================
📍 CHUNK 2/4: TRANSIT
⏱️  Duration: 3.0 minutes
============================================================

📖 You pass a row of small businesses—a laundromat, a pawn shop, 
a boarded-up storefront. A homeless man sits on the corner with 
a cardboard sign. The smell of exhaust mixes with the scent of 
fresh bread from a nearby bakery.

============================================================
📍 CHUNK 3/4: TRANSIT
⏱️  Duration: 3.0 minutes
============================================================

📖 The commercial district comes into view—more foot traffic here, 
people heading to work or grabbing morning coffee. You spot a few 
restaurants ahead, their neon signs flickering in the daylight. 
One catches your eye: "Rosie's Diner."

============================================================
📍 CHUNK 4/4: ARRIVAL
⏱️  Duration: 1.0 minutes
============================================================

📖 You approach Rosie's Diner, its chrome exterior gleaming in 
the morning sun. Through the windows you can see a few customers 
at the counter. You push through the door, a bell chiming overhead, 
and the smell of coffee and bacon greets you.

✅ Journey complete! You have arrived at Rosie's Diner.
```

## Benefits

1. **No More Teleportation** - Every journey is experienced
2. **Temporal Realism** - Time advances realistically
3. **Immersive Detail** - Players see the world between locations
4. **Opportunities** - Can encounter things during transit
5. **Rule of 3's Compliance** - Respects 3-minute narrative chunks

## Edge Cases

### Short Actions (< 5 minutes)
- **Don't chunk** - Narrate normally
- Example: "I walk across the street" → Single narrative

### Very Long Actions (> 60 minutes)
- **Chunk into many segments** - 20+ chunks for 60-minute drive
- Consider asking user if they want to skip/fast-forward

### Interrupted Journeys
- **Handle mid-journey encounters** - NUA appears during chunk 3
- Pause journey, handle encounter, resume journey

### Player Cancellation
- **Allow cancellation** - "Actually, I change my mind"
- Only advance time for completed chunks

## Testing Checklist

- [ ] Short walk (5 min) → 2 chunks
- [ ] Medium walk (10 min) → 3-4 chunks
- [ ] Long drive (30 min) → 10 chunks
- [ ] Very short action (2 min) → No chunking
- [ ] Verify time advances correctly per chunk
- [ ] Verify location updates on final chunk
- [ ] Verify scene description updates between chunks

## Files Modified

1. **`journey_chunking_system.py`** - New file, core system
2. **`redesigned_main.py`** - Integration point after action interpretation
3. **`JOURNEY_CHUNKING_INTEGRATION.md`** - This guide

## Next Steps

1. ✅ Create journey chunking system
2. ✅ Write integration guide
3. ⚠️ Integrate into redesigned_main.py
4. ⚠️ Add destination extraction logic
5. ⚠️ Test with various journey types
6. ⚠️ Handle edge cases (interruptions, cancellations)
7. ⚠️ Add user preference for auto-chunking vs manual

---

**Remember: The Rule of 3's means NO TELEPORTATION. Every journey is experienced in 3-minute chunks.**
