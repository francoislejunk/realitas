# Memory Resurfacing Behavior

## Overview

Perception-based memories can **resurface multiple times** throughout the simulation. This creates a realistic experience where the vessel is repeatedly reminded of their past when they see relevant triggers in the world.

## The Problem We Solved

**Original Behavior:**
- Vessel sees happy family → Memory created: "Loving Mother"
- Vessel sees another happy family later → Nothing happens (duplicate prevention)
- **Issue**: Real people are reminded of loved ones multiple times, not just once

**New Behavior:**
- Vessel sees happy family → Memory created: "Loving Mother" (full details)
- Vessel sees another happy family later → Memory resurfaces with NEW internal voice
- Vessel sees yet another happy family → Memory resurfaces again with DIFFERENT internal voice
- **Result**: Realistic, repeated emotional reactions

## How It Works

### First Time (Memory Creation)

**Trigger:** Vessel sees happy family having picnic

**Display:**
```
═══════════════════════════════════════════════════════════
✨ NEW MEMORY CREATED (from perception)
═══════════════════════════════════════════════════════════

Triggered by: You see a happy family having a picnic together

📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs.
She's always been supportive, even when times were tough.
You know she worries when you don't check in.

💭 Internal Voice:
I should call mom soon. She worries when I don't check in.

═══════════════════════════════════════════════════════════
```

**What Happened:**
- System detected FAMILY trigger
- No existing memory for "mother"
- Created new memory in Key Memories System
- Generated internal voice
- Tracked topic to recognize future triggers

---

### Second Time (Memory Resurfacing)

**Trigger:** Vessel sees another family at a restaurant

**Display:**
```
═══════════════════════════════════════════════════════════
✨ MEMORY RESURFACED
═══════════════════════════════════════════════════════════

Triggered by: A family sits together at a nearby table, laughing

💭 Mother
Man, I really miss my mom. I should go see her soon.

═══════════════════════════════════════════════════════════
```

**What Happened:**
- System detected FAMILY trigger
- Found existing memory for "mother"
- Generated NEW internal voice (different from first time)
- Did NOT create duplicate memory
- Showed simplified display (just internal voice)

---

### Third Time (Another Resurfacing)

**Trigger:** Vessel passes playground with families

**Display:**
```
═══════════════════════════════════════════════════════════
✨ MEMORY RESURFACED
═══════════════════════════════════════════════════════════

Triggered by: Families play with their children at the playground

💭 Mother
Seeing them together makes me think of mom. I need to call her.

═══════════════════════════════════════════════════════════
```

**What Happened:**
- System detected FAMILY trigger again
- Found existing memory for "mother"
- Generated ANOTHER new internal voice (different from both previous)
- Still no duplicate memory
- Fresh emotional reaction

## Key Differences

### Intent-Based Memories (Created Once)

**User Action:** "I want to call my mom"
- Creates memory ONCE
- Won't create again if user says "I want to call my mom" later
- **Reason**: User explicitly mentioning something should establish it once

### Perception-Based Memories (Can Resurface)

**Narration:** "You see a happy family"
- Creates memory FIRST time
- Resurfaces with new internal voice EVERY subsequent time
- **Reason**: Seeing reminders repeatedly is realistic human behavior

## Display Differences

### First Time (Full Details)

```
✨ NEW MEMORY CREATED (from perception)

📝 [Title]
[Full description]

💭 Internal Voice:
[Thought]
```

**Shows:**
- Full memory title
- Complete description
- Internal voice
- All details

### Subsequent Times (Simplified)

```
✨ MEMORY RESURFACED

💭 [Topic]
[New internal voice only]
```

**Shows:**
- Memory topic (e.g., "Mother")
- NEW internal voice only
- No repeated description
- Clean and non-intrusive

## Technical Implementation

### Method: `process_narration_for_memories()`

```python
for trigger in triggers:
    topic_key = f"{trigger_type}:{trigger_context.lower()}"
    memory_exists = topic_key in self.created_memory_topics
    
    if memory_exists:
        # RESURFACE with new internal voice
        memory_result = self._resurface_existing_memory(...)
        memory_result["is_resurfacing"] = True
    else:
        # CREATE new memory
        memory_result = self.create_memory_from_intent(...)
        memory_result["is_resurfacing"] = False
```

### Method: `_resurface_existing_memory()`

Generates a **new internal voice** for an existing memory:
- Takes the trigger and narration
- Generates fresh emotional reaction
- Returns simplified result (no full memory details)
- Does NOT create duplicate in Key Memories System

## Benefits

### 1. Realistic Emotional Experience
Real people are reminded of loved ones multiple times throughout their day. This captures that experience.

### 2. Non-Intrusive
Only shows internal voice on subsequent triggers, not full memory details. Keeps it clean.

### 3. Fresh Reactions
Each resurfacing generates a NEW internal voice, so it doesn't feel repetitive.

### 4. No Spam
Still requires high-confidence triggers (0.7+), so not every mention triggers resurfacing.

### 5. Natural Storytelling
Creates ongoing emotional connection to the vessel's past throughout the simulation.

## Example Play Session

**Turn 5:**
```
Narration: "You see a happy family having a picnic in the park."

✨ NEW MEMORY CREATED (from perception)
📝 Loving Mother
You have a loving mother, Margaret, who lives in the suburbs...
💭 Internal Voice: I should call mom soon. She worries.
```

**Turn 23:**
```
Narration: "A family walks by, the children laughing and playing."

✨ MEMORY RESURFACED
💭 Mother
Man, I really miss my mom. I should go see her soon.
```

**Turn 47:**
```
Narration: "You pass a mother helping her daughter tie her shoes."

✨ MEMORY RESURFACED
💭 Mother
Seeing them together makes me think of mom. I need to call her.
```

**Turn 89:**
```
Narration: "Families gather for a community event in the square."

✨ MEMORY RESURFACED
💭 Mother
I wonder what mom's doing right now. Probably worrying about me.
```

## Design Philosophy

**"Memories don't just happen once. They echo."**

The vessel's past isn't just discovered once and forgotten. It resurfaces naturally throughout their journey, creating an ongoing emotional connection to who they are and where they came from.

Each reminder is a moment of reflection, a pause to remember, a connection to their history. This makes the character feel **alive** and **human**.

## Conclusion

By allowing perception-based memories to resurface multiple times with fresh internal voices, we create a **realistic, emotionally resonant experience** where the vessel's past is an **ongoing presence** in their present, not just a one-time revelation.

**The past doesn't just inform the present—it echoes through it.**
