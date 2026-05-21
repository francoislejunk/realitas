# Intent Availability System Redesign - Internal Voice Edition

## Overview

Replaced the old "Available Now/Available Later/Unavailable Ever" system with a more diegetic **"Exist/Exist (not here)/Does not exist"** classification that uses **Internal Voice** instead of narrator explanations.

## Problem with Old System

The old system used narrator descriptions to explain why actions couldn't be performed:
- ❌ "You check the time and realize it's way too early..."
- ❌ "Your memories rush back like a tidal wave..."
- ❌ Meta-level explanations that break immersion

## New System: Diegetic Internal Voice

All explanations now use the character's **Internal Voice** (first-person thoughts in "we" voice):
- ✅ "Oh we left our phone at the diner last night..."
- ✅ "It's been years since we last got in contact with John..."
- ✅ Character-driven reasoning that maintains immersion

## Three Classifications

### 1. **EXIST** (replaces "Available Now")
- Action can be performed here and now
- **No internal voice needed** - action continues normally
- System proceeds with the action

**Example:**
- User: "I want to search the room"
- Scene: Room with various objects
- Result: EXIST → Action proceeds

### 2. **EXIST (NOT HERE)** (replaces "Available Later")
- Action is valid but cannot be performed at current location
- **Internal Voice explains** where the required item/person is
- Creates opportunity for player to go to the right location

**Examples:**

**Phone at diner:**
- User: "I want to call my friend"
- Internal Voice: "Oh we left our phone at the diner last night, we should hurry and get it back before someone takes it."

**Laptop at home:**
- User: "I want to check my email"
- Internal Voice: "Right, the laptop is back at the apartment. We'll need to head home first."

**Person elsewhere:**
- User: "I want to talk to John"
- Internal Voice: "John's probably at his usual spot downtown. We'd need to go there to talk to him."

### 3. **DOES NOT EXIST** (replaces "Unavailable Ever")
- Action references something that doesn't exist in the world
- **Internal Voice explains** through memories or realizations
- Character recalls why this isn't possible

**Examples:**

**Lost contact:**
- User: "I want to call my best friend"
- Internal Voice: "It's been years since we last got in contact with John... he changed his number a few years back."

**Never had item:**
- User: "I want to drive my car"
- Internal Voice: "We never had a car. That's just wishful thinking."

**Impossible action:**
- User: "I want to use my magic powers"
- Internal Voice: "There's no magic in this world. What am I even thinking?"

## Technical Implementation

### File Modified
`intent_availability_system.py`

### Key Changes

#### 1. Updated Enum (lines 26-30)
```python
class IntentAvailability(Enum):
    """Classification of intent availability - Diegetic naming"""
    EXIST = "exist"  # Action can be performed here and now
    EXIST_NOT_HERE = "exist_not_here"  # Action is valid but not at current location
    DOES_NOT_EXIST = "does_not_exist"  # Action references something that doesn't exist
```

#### 2. Location-Based Logic (lines 192-259)
- Changed from timing-based to location-based constraints
- 50/50 split between EXIST and EXIST_NOT_HERE for supported intents
- 1/3 chance each for unsupported intents

#### 3. Internal Voice Generation (lines 279-361)
- Generates character thoughts instead of narrator descriptions
- Uses "we" voice for first-person internal monologue
- Returns `null` for EXIST (no explanation needed)
- Returns internal voice string for EXIST_NOT_HERE and DOES_NOT_EXIST

#### 4. Response Structure
```json
{
  "availability": "exist_not_here",
  "internal_voice": "Oh we left our phone at the diner last night...",
  "action_path": null,
  "location_hint": "Diner",
  "emotional_tone": "concerned"
}
```

### LLM Prompt Structure

**For EXIST:**
- No internal voice needed
- Action proceeds normally

**For EXIST_NOT_HERE:**
- Character realizes what's missing
- Explains where item/person is located
- Uses "we" voice: "We left our phone..."

**For DOES_NOT_EXIST:**
- Character recalls memories
- Explains why this doesn't exist
- Uses past tense: "It's been years since..."

## Benefits

### 1. **Diegetic Immersion**
- Character's thoughts, not narrator telling
- Maintains first-person perspective
- Feels like natural internal reasoning

### 2. **Location-Based Logic**
- More intuitive than timing-based
- Clear spatial relationships
- Encourages exploration

### 3. **Character-Driven**
- Reveals character memories and knowledge
- Builds character history organically
- Creates emotional connections

### 4. **Gameplay Clarity**
- EXIST_NOT_HERE creates clear objectives
- Player knows where to go
- Deferred intents tracked for future opportunities

## Integration with Main Loop

When intent availability is checked:

1. **EXIST** → Continue with action normally
2. **EXIST_NOT_HERE** → Display internal voice, save deferred intent, prompt for new action
3. **DOES_NOT_EXIST** → Display internal voice, prompt for new action

### Display Format

**EXIST_NOT_HERE:**
```
💭 Internal Voice:
Oh we left our phone at the diner last night, we should hurry and get it back before someone takes it.

[Action blocked - location constraint]
```

**DOES_NOT_EXIST:**
```
💭 Internal Voice:
It's been years since we last got in contact with John... he changed his number a few years back.

[Action not possible - doesn't exist]
```

## Deferred Intent Tracking

EXIST_NOT_HERE intents are saved for future opportunities:

```json
{
  "intent": "I want to call my friend",
  "internal_voice": "Oh we left our phone at the diner...",
  "location_hint": "Diner",
  "deferred_at": "2025-01-06T12:30:00",
  "triggered": false
}
```

When player reaches the diner, system can remind them:
- "Oh right, we left our phone here last night."

## Design Philosophy

**The character's internal voice is the primary interface for world constraints.**

- No meta-level narrator explanations
- All reasoning comes from character's perspective
- Memories and realizations feel organic
- Location constraints create exploration goals
- Existence constraints build world consistency

The system now feels like **playing a character who thinks**, not **being told by a narrator**.

## Testing Scenarios

✅ **"I want to call my friend"** → EXIST_NOT_HERE: "We left our phone at the diner..."  
✅ **"I want to search the room"** → EXIST: Action proceeds  
✅ **"I want to use my laptop"** → EXIST_NOT_HERE: "The laptop is back at the apartment..."  
✅ **"I want to talk to my sister"** → DOES_NOT_EXIST: "We don't have a sister..."  
✅ **"I want to drive my car"** → DOES_NOT_EXIST: "We never had a car..."  
✅ **"I want to cast a spell"** → DOES_NOT_EXIST: "There's no magic in this world..."

## Voice Guidelines

### "We" Voice
- Use "we" for character's internal thoughts
- Example: "We should head to the diner"
- Feels like character thinking to themselves

### Past Tense for Memories
- Use past tense when recalling events
- Example: "We left our phone there last night"
- Example: "It's been years since we talked to John"

### Present Tense for Realizations
- Use present tense for current thoughts
- Example: "We need to go home first"
- Example: "John's probably downtown"

### Emotional Authenticity
- Concerned: "We should hurry before someone takes it"
- Resigned: "That's just wishful thinking"
- Nostalgic: "It's been years since..."
- Practical: "We'll need to head home first"

The internal voice should feel like a real person thinking, not a game system explaining mechanics.
