# Real-Time Simulation Design - No Time Skipping

## Core Philosophy

**The simulation should feel like LIVING, not watching highlights.**

### The Problem with 3-Hour Snapshots

❌ **Old System:**
- Actions classified as 3-SECOND, 3-MINUTE, or **3-HOUR**
- 3-HOUR meant "skip 3 hours of time"
- Travel = instant teleportation in narrative
- Plane ride = "You arrive at destination" (skipped the whole flight)
- Car ride to mall = "You're now at the mall" (skipped the journey)

**Result:** Feels like living in 3-hour snapshots, not real life.

### The New Reality

✅ **New System:**
- Remove 3-HOUR time skipping entirely
- **ONLY exception:** Sleeping or being unconscious (knocked out)
- Travel is LIVED, not skipped
- Car rides are EXPERIENCED
- Plane rides are EXPERIENCED
- Every moment is simulated

**Result:** Feels like living in real-time.

---

## What Changes

### 1. Remove THREE_HOUR Category

**Before:**
```python
class RuleOf3Category(Enum):
    THREE_SECOND = "3_second"   # Combat, reflexes
    THREE_MINUTE = "3_minute"   # Conversations, brief activities
    THREE_HOUR = "3_hour"       # ❌ REMOVE THIS
```

**After:**
```python
class RuleOf3Category(Enum):
    THREE_SECOND = "3_second"   # Combat, reflexes  
    THREE_MINUTE = "3_minute"   # Conversations, brief activities
    # THREE_HOUR removed - no time skipping except sleep/unconscious
```

### 2. Travel Becomes Real-Time Experience

**Before (3-HOUR system):**
```
User: "I want to drive to the mall"
System: *Classifies as 3-HOUR*
System: *Skips 3 hours*
Narrative: "After a long drive, you arrive at the mall..."
```

**After (Real-Time system):**
```
User: "I want to drive to the mall"
System: *Classifies as 3-MINUTE*
Narrative: "You start the engine and pull out onto the street. 
           The city traffic is moderate today..."

[User experiences the drive]
- Can look around during drive
- Can have conversations
- Can listen to radio
- Can notice things on the road
- Can change destination mid-drive

Eventually: "You see the mall parking lot ahead..."
```

### 3. Plane Rides Become Experiences

**Before:**
```
User: "I board the plane"
System: *Skips entire flight*
Narrative: "Hours later, you land at your destination..."
```

**After:**
```
User: "I board the plane"
Narrative: "You find your seat and settle in. The plane begins to taxi..."

[User experiences the flight]
- Can sleep (ONLY valid time skip)
- Can talk to passengers
- Can read, work, think
- Can look out window
- Can order drinks
- Can use bathroom

If user sleeps: "You drift off to sleep... [time skip during sleep] ...you wake as the plane begins descent"
If user stays awake: Experience continues in real-time
```

---

## Sleep/Unconscious: The ONLY Time Skip

### Valid Time Skips

**1. Intentional Sleep**
```
User: "I go to sleep"
System: Processes sleep action
Narrative: "You drift off to sleep..."
[TIME SKIP DURING SLEEP]
Narrative: "...you wake up [X hours later], feeling [rested/groggy/etc]"
```

**2. Knocked Unconscious**
```
Combat: User gets knocked out
Narrative: "Everything goes black..."
[TIME SKIP DURING UNCONSCIOUSNESS]
Narrative: "...you slowly regain consciousness. [Time has passed]"
```

**3. Drugged/Sedated**
```
User gets drugged
Narrative: "Your vision blurs and fades..."
[TIME SKIP DURING UNCONSCIOUSNESS]
Narrative: "...you wake with a pounding headache. Hours have passed."
```

### Invalid Time Skips (Now Lived Instead)

❌ **Travel** - Now experienced in real-time
❌ **"Long" activities** - Now broken into manageable chunks
❌ **Waiting** - Now actually simulated (can do things while waiting)
❌ **"Hours pass"** - Not allowed unless sleeping

---

## Implementation Changes Needed

### File: `rule_of_3s.py`

**Remove:**
- `RuleOf3Category.THREE_HOUR` enum value
- All THREE_HOUR keywords and logic
- THREE_HOUR transition triggers
- THREE_HOUR narrative guidance

**Update:**
- LLM classification prompt (remove 3-hour option)
- Fallback keywords (remove 3-hour keywords)
- Transition logic (remove 3-hour transitions)

### File: `reactor_time_system.py`

**Remove:**
- THREE_HOUR time mapping (line 75)
- THREE_HOUR time budget calculations

### File: `simulation_time_tracker.py`

**Remove:**
- THREE_HOUR time mapping
- Any logic that advances time by hours (except sleep)

### File: `master_time_coordinator.py`

**Remove:**
- THREE_HOUR duration mapping
- Any 3-hour time advancement logic

### File: `llm_agents/scene_manager.py`

**Remove:**
- `SceneTransitionType.TIME_SKIP` enum value
- Any time-skip transition logic

---

## New Travel System Design

### Concept: Chunked Real-Time Travel

Travel is broken into **experiential chunks** that feel real:

**Example: 2-Hour Car Ride**

Instead of:
```
"After a 2-hour drive, you arrive..."
```

Do this:
```
Turn 1: "You start the car and pull onto the highway. Traffic is light."
Turn 2: "You've been driving for about 20 minutes. The city skyline fades behind you."
Turn 3: "An hour into the drive, you notice a rest stop ahead. [User can stop or continue]"
Turn 4: "The landscape has changed to rolling hills. Your destination is getting closer."
Turn 5: "You see the exit for the mall. Almost there."
Turn 6: "You pull into the mall parking lot."
```

**Key Points:**
- Each turn = a few minutes of real experience
- User can interact during travel (change radio, stop, talk, etc.)
- Time passes naturally, not in jumps
- Feels like actually traveling

### Concept: Plane Ride with Sleep Option

**User Stays Awake:**
```
Turn 1: "You board and find your seat. The plane begins to taxi."
Turn 2: "The plane takes off. You feel the familiar pressure as you climb."
Turn 3: "The seatbelt sign turns off. A flight attendant offers drinks."
Turn 4: [User can: read, work, talk to neighbor, look out window, etc.]
Turn 5: "The pilot announces you're beginning descent."
Turn 6: "The plane touches down smoothly."
```

**User Sleeps:**
```
Turn 1: "You board and find your seat."
Turn 2: User: "I try to sleep"
Turn 3: "You drift off to sleep..." [TIME SKIP] "...you wake as the plane begins descent. 3 hours have passed."
```

---

## Benefits of Real-Time Simulation

### 1. **Immersion**
- Feels like living, not watching highlights
- Every moment is experienced
- No jarring time jumps

### 2. **Agency**
- User can make decisions during travel
- Can change plans mid-journey
- Can interact with environment continuously

### 3. **Realism**
- Time flows naturally
- Matches how real life works
- No "teleportation" feeling

### 4. **Narrative Richness**
- More opportunities for events
- Can have conversations during travel
- Can notice things along the way
- Random encounters possible

### 5. **Consistency**
- Time advancement is predictable
- No confusion about "how much time passed"
- Clear cause and effect

---

## Edge Cases

### "But what about really long trips?"

**Solution: Break into manageable chunks with sleep opportunities**

Example: 8-hour road trip
```
Hour 1-2: Drive, experience scenery, maybe stop for gas
Hour 2-3: User: "I'm getting tired, I'll pull over and nap"
         [SLEEP TIME SKIP - 2 hours]
Hour 5-6: Continue driving, more scenery
Hour 6-7: Stop for food (experienced in real-time)
Hour 7-8: Final stretch, arrive at destination
```

**Key:** User CHOOSES when to sleep/skip time, not automatic

### "What about boring waiting?"

**Solution: Waiting is an opportunity for action**

Instead of:
```
"You wait 3 hours for the meeting..."
```

Do this:
```
User: "I wait for the meeting"
System: "You have about 3 hours until the meeting. What do you do?"
Options:
- Explore the area
- Get coffee
- Review notes
- People watch
- Take a nap (TIME SKIP if chosen)
- etc.
```

**Key:** Waiting time becomes gameplay time

---

## Migration Strategy

### Phase 1: Remove THREE_HOUR Category
- Update enums
- Remove from classification logic
- Update LLM prompts

### Phase 2: Reclassify Travel Actions
- Travel actions now = THREE_MINUTE
- Break long travel into chunks
- Add sleep opportunities

### Phase 3: Update Time Advancement
- Remove 3-hour time jumps
- Keep only sleep/unconscious skips
- Update time tracking

### Phase 4: Test & Refine
- Test various travel scenarios
- Ensure smooth experience
- Adjust chunk sizes as needed

---

## Summary

**Old Way:**
- 3-HOUR category for travel/extended activities
- Time skips everywhere
- Feels like highlights reel

**New Way:**
- Only 3-SECOND and 3-MINUTE categories
- Travel is experienced in real-time chunks
- ONLY time skip = sleep/unconscious
- Feels like living

**Result:**
✅ Immersive real-time simulation
✅ User agency preserved
✅ Natural time flow
✅ No jarring jumps
✅ Every moment matters

**The simulation is no longer a series of snapshots. It's a continuous lived experience.**
