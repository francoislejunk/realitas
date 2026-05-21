# Perception-Based Memory Resurfacing

## Overview

The Intent-Based Memory Creation System now supports **perception-based memory resurfacing** - when the vessel perceives something in the environment (through narration), it can trigger memories from their past.

## Philosophy

**"What you see reminds you of what you've lived."**

Memories don't just come from user actions - they also resurface when the vessel:
- Sees a happy family → Remembers their own family
- Hears music → Remembers learning an instrument
- Passes a familiar-looking place → Remembers a location from their past
- Witnesses romance → Remembers a relationship

## How It Works

### 1. Narration Generated

The simulation generates narrative descriptions:
```
"You see a happy family having a picnic together in the park. 
The children are laughing, the parents relaxed and smiling."
```

### 2. Memory Trigger Detection

System analyzes narration for strong triggers:
- **FAMILY** - Seeing families, parents with children
- **RELATIONSHIP** - Seeing couples, friends together
- **LOCATION** - Familiar-looking places, nostalgic settings
- **POSSESSION** - Items that remind of cherished possessions
- **SKILL** - Seeing someone perform a skill
- **OCCUPATION** - Work environments, professional settings
- **BACKSTORY** - Situations echoing past experiences
- **TRAUMA** - Triggering situations
- **ACHIEVEMENT** - Success reminding of accomplishments
- **HABIT** - Routines reminding of own habits

### 3. Emotional Tone Analysis

System determines the emotional tone:
- **POSITIVE/NOSTALGIC** → Creates positive memory (AVAILABLE_NOW)
- **MELANCHOLIC/WISTFUL** → Creates distant memory (AVAILABLE_LATER)
- **PAINFUL/TRIGGERING** → Creates loss/absence memory (AVAILABLE_NEVER)

### 4. Memory Resurfaces

Memory is created and displayed with internal voice:
```
═══════════════════════════════════════════════════════════
✨ MEMORY RESURFACED
═══════════════════════════════════════════════════════════

Triggered by: You see a happy family having a picnic together

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.
She's always been supportive, even when times were tough.
You know she worries when you don't check in.

💭 Internal Voice:
Man, I really miss my mom. I should go see her soon.

═══════════════════════════════════════════════════════════
```

## Example Scenarios

### Scenario 1: Seeing a Happy Family (Positive Trigger)

**Narration:**
```
You see a happy family having a picnic together in the park.
The children are laughing, the parents relaxed and smiling.
```

**Trigger Detected:** FAMILY (seeing happy family)
**Emotional Tone:** POSITIVE/NOSTALGIC
**Availability:** AVAILABLE_NOW

**Memory Resurfaced:**
```
✨ MEMORY RESURFACED
Triggered by: You see a happy family having a picnic together

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.

💭 Internal Voice:
Man, I really miss my mom. I should go see her soon.
```

---

### Scenario 2: Seeing a Couple (Melancholic Trigger)

**Narration:**
```
A couple walks by, holding hands and laughing together.
They look so happy, so in sync with each other.
```

**Trigger Detected:** RELATIONSHIP (seeing couple)
**Emotional Tone:** MELANCHOLIC/WISTFUL
**Availability:** AVAILABLE_LATER

**Memory Resurfaced:**
```
✨ MEMORY RESURFACED
Triggered by: A couple walks by, holding hands and laughing

📝 Lost Love
You had a serious relationship with Alex, but it ended badly.
You haven't spoken in over a year, but sometimes you wonder.

💭 Internal Voice:
I hope Alex is doing okay. We were good together once.
```

---

### Scenario 3: Seeing What You Never Had (Painful Trigger)

**Narration:**
```
You watch the family from a distance. The father lifts his 
daughter onto his shoulders, and she squeals with delight.
```

**Trigger Detected:** FAMILY (father-daughter moment)
**Emotional Tone:** PAINFUL/TRIGGERING
**Availability:** AVAILABLE_NEVER

**Memory Resurfaced:**
```
✨ MEMORY RESURFACED
Triggered by: The father lifts his daughter onto his shoulders

📝 Unknown Father
You never knew your father. He left before you were born,
and your mother never talked about him. It's a void you've
learned to live with.

💭 Internal Voice:
I've been alone for so long. Family is just a word to me.
```

---

### Scenario 4: Hearing Music (Skill Trigger)

**Narration:**
```
You hear someone playing guitar beautifully from an open window.
The melody is haunting and skillful, each note perfectly placed.
```

**Trigger Detected:** SKILL (hearing guitar)
**Emotional Tone:** POSITIVE/NOSTALGIC
**Availability:** AVAILABLE_NOW

**Memory Resurfaced:**
```
✨ MEMORY RESURFACED
Triggered by: You hear someone playing guitar beautifully

📝 Guitar Lessons
You learned to play guitar from your uncle when you were young.
He taught you everything he knew, every summer for years.

💭 Internal Voice:
I haven't picked up the guitar in months. Maybe I should.
```

---

### Scenario 5: Passing a Diner (Location Trigger)

**Narration:**
```
You pass an old-style diner with red vinyl booths visible
through the window. The smell of coffee drifts out.
```

**Trigger Detected:** LOCATION (familiar-looking diner)
**Emotional Tone:** POSITIVE/NOSTALGIC
**Availability:** AVAILABLE_NOW

**Memory Resurfaced:**
```
✨ MEMORY RESURFACED
Triggered by: You pass an old-style diner with red vinyl booths

📝 Sal's Diner
You know a great diner called Sal's Place on 5th Street.
You've been going there for years. Sal knows your order by heart.

💭 Internal Voice:
Sal's always has the best coffee. Good place to think.
```

## Technical Implementation

### Detection Method

```python
def detect_memory_triggers_from_narration(self, narration: str) -> List[Dict[str, Any]]:
    """
    Detect if narration contains triggers for memory resurfacing.
    
    Returns:
        List of triggers with confidence >= 0.7
    """
```

**Requirements:**
- **High confidence** (>= 0.7) triggers only
- **Specific and evocative** narration elements
- **Strong emotional resonance**

### Emotional Tone Classification

```python
def _determine_narration_availability(self, trigger: Dict, narration: str) -> IntentAvailability:
    """
    Determine availability based on emotional tone.
    
    - POSITIVE/NOSTALGIC → AVAILABLE_NOW
    - MELANCHOLIC/WISTFUL → AVAILABLE_LATER
    - PAINFUL/TRIGGERING → AVAILABLE_NEVER
    """
```

### Processing Pipeline

```python
def process_narration_for_memories(self,
                                  narration: str,
                                  current_location: str,
                                  turn_number: int,
                                  scene_id: str) -> List[Dict[str, Any]]:
    """
    Complete pipeline for perception-based memory resurfacing.
    
    1. Detect triggers from narration
    2. Determine emotional tone
    3. Create memories
    4. Mark as perception-triggered
    """
```

## Integration Points

### Main Loop Integration

Located in `MAIN/redesigned_main.py`:

**After Given Actions (line ~3587):**
```python
# After narration is displayed
try:
    resurfaced_memories = intent_memory_creator.process_narration_for_memories(
        narration=contextual_result,
        current_location=current_location or "Unknown Location",
        turn_number=turn_number,
        scene_id=scene_id
    )
    
    for memory_result in resurfaced_memories:
        display_memory_creation(memory_result)
        
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}Memory resurfacing failed: {e}{Color.RESET}")
```

**After Fallible Exploration (line ~4210):**
Same integration pattern.

## Display Format

### First Time (New Memory)

```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED (from perception)
═══════════════════════════════════════════════════════════

Triggered by: [Narration excerpt that triggered it]

📝 [Memory Title]
[Memory description]

💭 Internal Voice:
[First-person thought]

═══════════════════════════════════════════════════════════
```

### Subsequent Times (Resurfacing)

```
═══════════════════════════════════════════════════════════
✨ MEMORY RESURFACED
═══════════════════════════════════════════════════════════

Triggered by: [Narration excerpt that triggered it]

💭 [Memory Topic]
[New internal voice reaction]

═══════════════════════════════════════════════════════════
```

**Key Difference:**
- **First time**: Full memory details shown (title, description, internal voice)
- **Subsequent times**: Only new internal voice shown (memory already known)

### Intent-Triggered Memory

```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED
═══════════════════════════════════════════════════════════

📝 [Memory Title]
[Memory description]

💭 Internal Voice:
[First-person thought]

═══════════════════════════════════════════════════════════
```

## Trigger Strength Guidelines

### STRONG TRIGGERS (Will Resurface Memory)

- **Specific and evocative**: "A happy family having a picnic"
- **Emotionally resonant**: "The father lifts his daughter onto his shoulders"
- **Sensory details**: "You hear someone playing guitar beautifully"
- **Nostalgic elements**: "An old-style diner with red vinyl booths"

### WEAK TRIGGERS (Won't Resurface Memory)

- **Generic descriptions**: "You walk down the street"
- **Non-specific**: "The guard stands there"
- **Mundane details**: "It's a sunny day"
- **Mechanical descriptions**: "You enter the room"

## Benefits

### 1. Organic Discovery
- Memories emerge naturally from experience
- No forced backstory dumps
- Feels like genuine reminiscence

### 2. Emotional Resonance
- Memories tied to emotional moments
- Creates meaningful character depth
- Enhances immersion

### 3. Environmental Storytelling
- World triggers character development
- Narration becomes more meaningful
- Every scene can reveal backstory

### 4. Dual Trigger System
- **Intent-based**: User mentions something
- **Perception-based**: World shows something
- Comprehensive memory creation

### 5. Contextual Appropriateness
- Positive scenes → positive memories
- Melancholic scenes → distant memories
- Painful scenes → loss memories
- Tone-matched and realistic

## Design Considerations

### Resurfacing vs. Creating

**IMPORTANT: Perception-based memories can resurface multiple times!**

Unlike intent-based memories (which are created once), perception-based memories can trigger repeatedly:

**First Time Seeing Happy Family:**
```
✨ NEW MEMORY CREATED (from perception)

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.
She's always been supportive, even when times were tough.

💭 Internal Voice:
I should call mom soon. She worries when I don't check in.
```

**Second Time Seeing Happy Family (Later in Session):**
```
✨ MEMORY RESURFACED

💭 Mother
Man, I really miss my mom. I should go see her soon.
```

**Third Time Seeing Happy Family (Even Later):**
```
✨ MEMORY RESURFACED

💭 Mother
Seeing them together makes me think of mom. I need to call her.
```

**Why This Works:**
- Real people are reminded of their loved ones multiple times
- Each reminder generates a fresh emotional reaction
- Doesn't spam full memory details (just internal voice)
- Feels natural and realistic

### Frequency Control

**High Confidence Threshold (0.7+):**
- Prevents memory spam
- Only strong triggers create memories
- Maintains special feeling

**Smart Resurfacing:**
- First time: Full memory details
- Subsequent times: Just internal voice
- New reaction each time
- No duplicate memory entries

### Emotional Consistency

**Tone Matching:**
- Happy family → Happy memory
- Lost love → Melancholic memory
- Missing father → Painful memory
- Maintains emotional coherence

### Narrative Flow

**Non-Intrusive:**
- Memories appear after narration
- Don't interrupt action flow
- Feel like natural pauses for reflection

## Example Play Session

```
Turn 1: "I walk through the park"

Narration:
"You stroll through the park on a sunny afternoon. Families 
are scattered across the grass, children playing, parents 
watching. A couple walks by, holding hands."

✨ MEMORY RESURFACED
Triggered by: Families scattered across the grass

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.

💭 Internal Voice:
Man, I really miss my mom. I should go see her soon.

---

Turn 5: "I sit on a bench"

Narration:
"You settle onto a weathered park bench. An old man nearby 
feeds pigeons, humming a tune you half-remember."

✨ MEMORY RESURFACED
Triggered by: An old man humming a tune

📝 Grandfather's Songs
Your grandfather used to hum old songs while working in his 
garage. You'd sit and watch him for hours.

💭 Internal Voice:
Grandpa always knew how to make things feel peaceful.
```

## Conclusion

Perception-based memory resurfacing creates a **living, breathing character** whose past emerges naturally from their present experiences. The world doesn't just exist around the vessel - it **reminds them** of who they are and where they came from.

**What you see shapes who you remember being.**
