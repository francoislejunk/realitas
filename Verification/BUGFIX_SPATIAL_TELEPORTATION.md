# Bug Fix: Spatial Teleportation (Narrator Jumping Locations)

## Problem

**Issue:** Narrator says "You step onto the subway platform" when character was just in the apartment - **skipping the entire journey!**

**Example:**
```
Current Location: Studio apartment
User: "I go to the subway"

Narrator (WRONG):
"You step onto the subway platform..."

Should Be:
"You leave the apartment, heading out into the street. The evening air is cool..."
[Journey chunks showing the 10-minute walk]
"...finally, you descend the stairs to the subway platform."
```

---

## Root Causes

### Cause 1: Narrator Doesn't Know Current Location
The narrator receives:
- Action description: "go to the subway"
- UTAS factors (skill, S-trait, etc.)
- Success level

**But NOT:**
- Current location
- Destination
- Spatial context

### Cause 2: Journey Chunking Not Integrated with Narrator
The journey chunking system exists (`journey_chunking_system.py`) but:
- ✅ It detects when actions need chunking
- ✅ It calculates journey segments
- ❌ **It doesn't tell the narrator to use them!**

The narrator generates narrative for the ACTION but doesn't know:
- Where you're starting from
- Where you're going
- What journey chunks to narrate

---

## The Two-Part Problem

### Part A: Time Estimation (✅ FIXED)
- Interpreter thinking "3 minutes" when memory says "10 minutes"
- **Fixed by:** Memory context integration

### Part B: Spatial Jumping (❌ STILL BROKEN)
- Narrator jumping from apartment to subway platform
- **Needs:** Spatial context + journey chunk integration

---

## Solution

### Step 1: Pass Spatial Context to Narrator

**File:** `agents/narrator_agent.py`

Update `_build_action_narrative()` to receive spatial context:

```python
def _build_action_narrative(
    self, 
    proactor_data: Dict[str, Any], 
    reactor_data: Dict[str, Any], 
    time_context: Optional[Dict[str, Any]] = None, 
    framing_guidance: Optional[Dict[str, Any]] = None,
    spatial_context: Optional[Dict[str, Any]] = None  # NEW
) -> str:
```

**Spatial context should include:**
```python
spatial_context = {
    'current_location': "Studio apartment",
    'destination': "Subway station",
    'journey_chunks': [
        {
            'chunk_number': 1,
            'narrative_focus': "Leaving apartment, entering street",
            'location_context': "Apartment building exterior"
        },
        {
            'chunk_number': 2,
            'narrative_focus': "Walking through neighborhood",
            'location_context': "City streets"
        },
        {
            'chunk_number': 3,
            'narrative_focus': "Approaching subway entrance",
            'location_context': "Near subway station"
        },
        {
            'chunk_number': 4,
            'narrative_focus': "Descending to platform",
            'location_context': "Subway platform"
        }
    ],
    'current_chunk': 1,  # Which chunk we're narrating
    'is_journey': True
}
```

### Step 2: Update Narrator Prompt

Add spatial awareness to the narrator prompt:

```python
# In _build_action_narrative()

if spatial_context and spatial_context.get('is_journey'):
    current_loc = spatial_context.get('current_location', 'unknown')
    destination = spatial_context.get('destination', 'unknown')
    chunk = spatial_context.get('journey_chunks', [])[spatial_context.get('current_chunk', 1) - 1]
    
    spatial_instruction = f"""
**SPATIAL CONTEXT (CRITICAL):**
- **Current Location:** {current_loc}
- **Destination:** {destination}
- **Journey Chunk:** {chunk['chunk_number']} of {len(spatial_context['journey_chunks'])}
- **This Chunk Focus:** {chunk['narrative_focus']}
- **Location Context:** {chunk['location_context']}

**SPATIAL RULES:**
1. **START WHERE YOU ARE:** Begin narrative at current location
2. **SHOW THE JOURNEY:** Describe movement through space
3. **NO TELEPORTATION:** Never jump to destination instantly
4. **CHUNK FOCUS:** Focus on THIS chunk's narrative focus
5. **PROGRESSIVE MOVEMENT:** Show progress toward destination

Example (Chunk 1 of 4):
❌ "You step onto the subway platform..." (TELEPORTATION!)
✅ "You leave the apartment, stepping out into the cool evening air. The street is quiet..."
"""
else:
    spatial_instruction = ""

# Add to prompt
prompt = f"""
{spatial_instruction}

**Your Mechanical Details:**
[rest of prompt...]
"""
```

### Step 3: Integrate Journey Chunking with Main Loop

**File:** `MAIN/redesigned_main.py`

When journey chunking is detected, pass chunks to narrator:

```python
# After journey chunking detection (around line 4398)
if should_chunk:
    chunks = chunking_system.generate_journey_chunks(
        user_input=user_input,
        action_description=interpretation_data.get('narrative_description', user_input),
        estimated_duration=estimated_duration
    )
    
    # Narrate EACH chunk
    for i, chunk in enumerate(chunks, 1):
        spatial_context = {
            'current_location': current_location,
            'destination': destination,  # Extract from user input
            'journey_chunks': chunks,
            'current_chunk': i,
            'is_journey': True
        }
        
        # Generate narrative for THIS chunk
        chunk_narrative = narrator.generate_exploration_narrative(
            actor=actor,
            action_description=user_input,
            scene_description=scene_description,
            success_data=success_data,
            spatial_context=spatial_context  # Pass spatial context
        )
        
        print(f"\n{Color.NARRATIVE}{chunk_narrative}{Color.RESET}")
        
        # Update location after each chunk
        if i == len(chunks):
            current_location = destination  # Arrived!
        else:
            current_location = chunk['location_context']  # Intermediate location
        
        # Advance time by chunk duration
        time_passed = chunk['duration_minutes'] * 60  # Convert to seconds
        # [time advancement code...]
```

---

## Expected Behavior After Fix

### Example 1: Going to Subway (10-minute walk)

**User:** "I go to the subway"

**Chunk 1 (0-3 min):**
```
You leave the apartment, stepping out into the cool evening air. 
The street is quiet, lit by the occasional streetlamp. You start 
walking toward the subway station, your footsteps echoing on the 
pavement.

⏱️ Time: 3 minutes elapsed
📍 Location: City streets
```

**Chunk 2 (3-6 min):**
```
You continue walking through the neighborhood. A few people pass by, 
heading home for the evening. The subway entrance is still a few 
blocks away, but you're making steady progress.

⏱️ Time: 6 minutes elapsed
📍 Location: Approaching subway area
```

**Chunk 3 (6-9 min):**
```
The subway entrance comes into view ahead. You can see the familiar 
blue sign marking the station. You pick up your pace slightly, eager 
to get out of the cold.

⏱️ Time: 9 minutes elapsed
📍 Location: Near subway entrance
```

**Chunk 4 (9-10 min):**
```
You descend the stairs into the subway station. The air is warmer 
down here, and you can hear the distant rumble of a train. You step 
onto the platform, checking the arrival board.

⏱️ Time: 10 minutes elapsed
📍 Location: Subway platform ✅ ARRIVED
```

### Example 2: Crossing the Room (3 seconds)

**User:** "I walk to the window"

**No Chunking Needed** (< 5 minutes):
```
You cross the room to the window, your footsteps soft on the carpet. 
Outside, the city lights twinkle in the darkness.

⏱️ Time: 3 seconds elapsed
📍 Location: By the window
```

---

## Benefits

### 1. No More Teleportation
✅ Always show the journey
✅ Never jump locations instantly
✅ Maintain spatial continuity

### 2. Realistic Time Progression
✅ 3-minute chunks for long journeys
✅ 3-second units for short movements
✅ Time matches distance

### 3. Immersive Narration
✅ Experience the journey
✅ See the world between locations
✅ Feel the passage of time

### 4. Spatial Awareness
✅ Always know where you are
✅ Clear location transitions
✅ Logical movement through space

---

## Implementation Checklist

### Phase 1: Narrator Updates
- [ ] Add `spatial_context` parameter to `_build_action_narrative()`
- [ ] Add spatial instructions to narrator prompt
- [ ] Handle journey chunks in narrative generation
- [ ] Test with simple movement ("walk to door")

### Phase 2: Main Loop Integration
- [ ] Extract destination from user input
- [ ] Pass spatial context to narrator
- [ ] Iterate through journey chunks
- [ ] Update location after each chunk
- [ ] Advance time correctly

### Phase 3: Journey Chunking Enhancement
- [ ] Ensure chunking system detects all travel actions
- [ ] Verify chunk generation is realistic
- [ ] Test with various distances (5 min, 10 min, 30 min, 1 hour)

### Phase 4: Memory Integration
- [ ] Narrator sees memories about locations
- [ ] Narrator sees memories about travel times
- [ ] Consistent with established facts

---

## Test Cases

### Test 1: Short Walk (5 minutes)
```
Input: "I head to the corner store"
Expected: 2 chunks (3 min + 2 min)
Verify: No teleportation, shows journey
```

### Test 2: Medium Walk (10 minutes)
```
Input: "I go to the subway"
Expected: 4 chunks (3 + 3 + 3 + 1 min)
Verify: Progressive movement, arrives at end
```

### Test 3: Long Journey (30 minutes)
```
Input: "I drive across town"
Expected: 10 chunks (3 min each)
Verify: Shows driving experience, traffic, landmarks
```

### Test 4: Very Short Movement (3 seconds)
```
Input: "I walk to the window"
Expected: No chunking, single narrative
Verify: Immediate, no journey chunks
```

### Test 5: Memory Consistency
```
Setup: Memory says "subway is 10-minute walk"
Input: "I go to the subway"
Expected: 4 chunks totaling 10 minutes
Verify: Matches memory, no contradiction
```

---

## Status

✅ Journey chunking system exists
✅ Memory context integration complete (time estimates)
⏳ **PENDING:** Spatial context integration with narrator
⏳ **PENDING:** Journey chunk iteration in main loop
⏳ **PENDING:** Location tracking between chunks

**This is the final piece to prevent teleportation!**
