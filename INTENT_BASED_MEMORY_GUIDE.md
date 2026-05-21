# Intent-Based Memory Creation System

## Overview

The Intent-Based Memory Creation System builds the vessel's background **diegetically** through user actions and the Intent Availability System. Instead of pre-defining the character's entire history, memories are created organically as the user mentions family, relationships, locations, and other background elements during play.

## Philosophy

**"The vessel only knows what they've remembered."**

At the start, the user knows only the barebones of their vessel. As they play and mention things from their past, the system:
1. Detects memory triggers (family, relationships, locations, etc.)
2. Uses Intent Availability to determine the nature of the memory
3. Creates an appropriate memory and stores it
4. Relays the memory diegetically through internal voice narration

## How It Works

### 1. Memory Trigger Detection

The system detects when the user mentions:

- **FAMILY** - mother, father, sister, brother, parents, siblings, relatives
- **RELATIONSHIP** - friend, girlfriend, boyfriend, partner, spouse, ex
- **LOCATION** - childhood home, favorite place, hometown, old neighborhood
- **POSSESSION** - car, house, apartment, cherished item, heirloom
- **SKILL** - learned ability, training, expertise
- **OCCUPATION** - job, career, former work, profession
- **BACKSTORY** - past event, history, origin
- **TRAUMA** - painful memory, loss, regret
- **ACHIEVEMENT** - accomplishment, success, proud moment
- **HABIT** - routine, regular activity, usual behavior

### 2. Intent Availability Integration

The system uses the Intent Availability classification to determine the **nature** of the memory:

#### AVAILABLE_NOW → Positive/Accessible Memory
- This thing exists and is accessible
- Creates warm, present-tense memories
- Examples:
  - Family: "You have a loving mother who lives nearby"
  - Location: "You know a great diner on 5th Street"
  - Possession: "You own a reliable car"

#### AVAILABLE_LATER → Distant/Strained Memory
- This exists but isn't accessible right now
- Creates complicated, distant memories
- Examples:
  - Family: "You have a sister but you haven't spoken in years"
  - Location: "You used to go to a bar downtown, but it might be closed"
  - Possession: "You had a motorcycle but sold it last year"

#### AVAILABLE_NEVER → Absent/Lost Memory
- This doesn't exist or is permanently gone
- Creates absence, loss, or never-had memories
- Examples:
  - Family: "You never knew your father"
  - Location: "You've never had a place to call home"
  - Possession: "You've never owned a car"

### 3. Internal Voice Narration

After creating a memory, the system generates an **internal voice** thought that:
- Reflects the memory naturally
- Uses first person ("I")
- Feels like genuine inner monologue
- Matches the emotional tone

## Example Flows

### Example 1: Family (AVAILABLE_NOW)

**User Action:**
```
"I want to call my mom"
```

**System Process:**
1. Intent Availability: AVAILABLE_NOW (50/50 chance with no prior context)
2. Memory Trigger Detected: FAMILY (mother)
3. Memory Created: "You have a loving mother, Margaret, who lives in the suburbs and worries about you"
4. Internal Voice: "I should call mom soon. She worries when I don't check in."

**Display:**
```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED
═══════════════════════════════════════════════════════════

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs. 
She's always been supportive, even when times were tough. 
You know she worries when you don't check in.

💭 Internal Voice:
I should call mom soon. She worries when I don't check in.

═══════════════════════════════════════════════════════════
```

### Example 2: Family (AVAILABLE_LATER)

**User Action:**
```
"I wonder how my sister is doing"
```

**System Process:**
1. Intent Availability: AVAILABLE_LATER (50/50 chance with no prior context)
2. Memory Trigger Detected: FAMILY (sister)
3. Memory Created: "You have an estranged sister, Sarah, who moved to California years ago after a falling out"
4. Internal Voice: "I wonder how Sarah's doing. Maybe I'll reach out someday."

**Display:**
```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED
═══════════════════════════════════════════════════════════

📝 Estranged Sister
You have an estranged sister, Sarah, who moved to California 
years ago after a falling out. You haven't spoken in years, 
but sometimes you wonder how she's doing.

💭 Internal Voice:
I wonder how Sarah's doing. Maybe I'll reach out someday.

═══════════════════════════════════════════════════════════
```

### Example 3: Family (AVAILABLE_NEVER)

**User Action:**
```
"I wish I knew my father"
```

**System Process:**
1. Intent Availability: AVAILABLE_NEVER (1/3 chance with no prior context)
2. Memory Trigger Detected: FAMILY (father)
3. Memory Created: "You never knew your father. He left before you were born, and your mother never talked about him"
4. Internal Voice: "I've been alone for so long. Family is just a word to me."

**Display:**
```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED
═══════════════════════════════════════════════════════════

📝 Unknown Father
You never knew your father. He left before you were born, 
and your mother never talked about him. It's a void you've 
learned to live with.

💭 Internal Voice:
I've been alone for so long. Family is just a word to me.

═══════════════════════════════════════════════════════════
```

### Example 4: Location (AVAILABLE_NOW)

**User Action:**
```
"I head to my favorite diner"
```

**System Process:**
1. Intent Availability: AVAILABLE_NOW (context supports this)
2. Memory Trigger Detected: LOCATION (favorite diner)
3. Memory Created: "You know a great diner called Sal's Place on 5th Street. You've been going there for years"
4. Internal Voice: "Sal's always has the best coffee. Good place to think."

**Display:**
```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED
═══════════════════════════════════════════════════════════

📝 Sal's Diner
You know a great diner called Sal's Place on 5th Street. 
You've been going there for years. The owner, Sal, knows 
your usual order by heart.

💭 Internal Voice:
Sal's always has the best coffee. Good place to think.

═══════════════════════════════════════════════════════════
```

## Integration Points

### Main Loop Integration

Located in `MAIN/redesigned_main.py` after Intent Availability check:

```python
# After intent availability evaluation
try:
    created_memories = intent_memory_creator.process_intent_for_memories(
        user_intent=user_input,
        availability_result=availability_result,
        current_location=current_location or "Unknown Location",
        turn_number=turn_number,
        scene_id=scene_id
    )
    
    # Display any created memories with internal voice
    for memory_result in created_memories:
        display_memory_creation(memory_result)
        
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}Memory creation failed: {e}{Color.RESET}")
```

### Memory Storage

Memories are stored in the Key Memories System:
- **Location:** `./simulation_data/memories/{session_id}_memories.json`
- **Categories:** RELATIONSHIP, LOCATION, ITEM, BACKSTORY, etc.
- **Importance:** NOTABLE, IMPORTANT, CRITICAL
- **Persistent:** Saved between sessions

### Topic Tracking

To prevent duplicate memories:
- **Location:** `./simulation_data/intent_memories/topics.json`
- **Format:** `{trigger_type}:{trigger_context}` (e.g., "family:mother")
- **Behavior:** Once a memory is created for a topic, it won't be created again

## Benefits

### 1. Organic Character Development
- Background emerges through play, not pre-definition
- Feels natural and discovered
- Player learns about their character alongside the simulation

### 2. Diegetic Storytelling
- Memories revealed through internal voice
- No meta-game character creation screens
- Immersive and narrative-focused

### 3. Intent-Driven
- Memories reflect what the player is interested in
- No forced backstory elements
- Player agency in character history

### 4. Availability-Aware
- Positive memories for AVAILABLE_NOW
- Complicated memories for AVAILABLE_LATER
- Absence/loss memories for AVAILABLE_NEVER
- Creates realistic, nuanced backgrounds

### 5. Persistent
- Memories saved between sessions
- Can be reviewed with `/mem` commands
- Builds over time

## Technical Details

### Files

1. **`intent_based_memory_creation.py`** - Core system
   - `IntentBasedMemoryCreator` class
   - Memory trigger detection
   - Memory creation logic
   - Internal voice generation

2. **`MAIN/redesigned_main.py`** - Integration
   - Initialization (line ~1914)
   - Processing (line ~2808)
   - Display integration

### Key Methods

#### `detect_memory_triggers(user_intent: str)`
- Analyzes user intent for memory triggers
- Returns list of detected triggers with context
- Uses LLM for intelligent detection

#### `create_memory_from_intent(trigger, availability, ...)`
- Creates memory based on trigger and availability
- Generates internal voice narration
- Stores in key memories system
- Returns memory result with all details

#### `process_intent_for_memories(user_intent, availability_result, ...)`
- Complete pipeline: detect → create → store
- Returns list of created memories
- Handles multiple triggers in one intent

#### `display_memory_creation(memory_result)`
- Formats and displays memory creation
- Shows title, description, and internal voice
- Uses color-coded output

## Design Considerations

### Avoiding Duplicates
- Tracks created topics in `topics.json`
- Won't create multiple memories for same topic
- Example: Once "mother" memory exists, won't create another

### Multiple Triggers
- One intent can trigger multiple memories
- Example: "I want to visit my mom at her house" → Family + Location
- Each trigger processed separately

### Confidence Thresholds
- Only creates memories for high-confidence triggers
- Avoids false positives
- Example: "I go to the store" doesn't trigger location memory

### Emotional Consistency
- Internal voice matches memory tone
- Positive memories → hopeful thoughts
- Negative memories → resigned thoughts
- Maintains emotional coherence

## Future Enhancements

### Potential Additions

1. **Memory Conflicts**
   - Detect when new memories contradict old ones
   - Ask user to resolve or merge

2. **Memory Depth**
   - Allow expanding on existing memories
   - "Tell me more about your mother" → adds details

3. **Memory Triggers from Narration**
   - Not just user actions
   - Scene descriptions trigger memories
   - Example: "You see a happy family" → triggers family memory

4. **Memory Influence**
   - Memories affect decision-making
   - Sympathies influenced by relationship memories
   - Skills influenced by training memories

## Conclusion

The Intent-Based Memory Creation System provides a **diegetic, organic, player-driven** way to build the vessel's background. By integrating with the Intent Availability System, it creates memories that feel natural, realistic, and meaningful while maintaining narrative consistency and player agency.

**The vessel's past emerges through their present actions.**
