# Waking Up Opening Requirement

## Overview

All simulations now start with the character waking up - establishing the moment of consciousness at the beginning of the story.

## Implementation

### Requirement

**Every initial scene MUST begin with the character's eyes opening.**

Valid opening variations:
- "Your eyes shoot open..."
- "Your eyes slowly open..."
- "Your eyes flutter open..."
- Similar variations establishing the moment of awakening

### Why This Works

1. **Establishes Consciousness**: Creates a clear starting point - the character is becoming aware
2. **Immediate Immersion**: Reader experiences the awakening with the character
3. **Natural Orientation**: Allows sensory details to unfold naturally as the character becomes aware
4. **Universal Starting Point**: Works for any location or situation
5. **Cinematic**: Mirrors how many films and stories begin - with the protagonist waking

### Example Openings

**Warehouse:**
```
Your eyes shoot open to the dim amber glow filtering through cracked skylights. 
You're in the back room of an abandoned warehouse, the air thick with dust and 
the scent of old vinyl. Stacks of crates labeled with faded band stickers 
surround you, and a dusty turntable sits on a rickety table nearby.
```

**Apartment:**
```
Your eyes slowly open, adjusting to the harsh morning light streaming through 
venetian blinds. You're sprawled on a worn couch in your cramped studio 
apartment, the distant rumble of traffic already building outside. An empty 
pizza box sits on the coffee table next to your beeper.
```

**Garage:**
```
Your eyes flutter open as the metallic clang of a dropped wrench echoes through 
the space. You're lying on a creeper beneath a jacked-up sedan, the concrete 
floor cold against your back. The smell of motor oil and gasoline fills your 
nostrils as fluorescent lights buzz overhead.
```

**Alley:**
```
Your eyes shoot open to the wail of distant sirens cutting through the night. 
You're slumped against a brick wall in a narrow alley, neon signs from the 
street casting red and blue shadows across graffiti-covered walls. The taste 
of copper lingers in your mouth.
```

## Technical Implementation

### File Modified
`agents/creator_agent.py` - `_get_initial_scene_prompt()` method

### Changes Made

**1. Added as Requirement #1:**
```python
1. **START WITH WAKING UP:** The opening line MUST begin with the character's 
   eyes opening - either "Your eyes shoot open..." or "Your eyes slowly open..." 
   or similar. This establishes the moment of consciousness at the start of 
   the simulation.
```

**2. Updated Example Format:**
```python
**Example Format (4-6 sentences, using world context details):**

"Your eyes [shoot open/slowly open/flutter open] [immediate sensory detail]. 
You [establish location and immediate situation]. [Sensory detail from world 
context]. [Key exploration opportunities - 2-3 specific things]. [Optional: 
character detail based on personality]. [Final atmospheric touch]."
```

**3. Added Example Opening Lines:**
```python
**Example Opening Lines:**
- "Your eyes shoot open to the harsh glare of fluorescent lights buzzing overhead."
- "Your eyes slowly open, adjusting to the dim amber glow filtering through dusty windows."
- "Your eyes flutter open as the distant wail of sirens cuts through the morning air."
```

**4. Updated JSON Structure:**
```python
"setting": "A concise description (4-6 sentences) that MUST START with 
'Your eyes [shoot/slowly/flutter] open...' followed by the physical 
environment using world context details."
```

## Variations

### Intensity Variations

**Sudden/Jarring:**
- "Your eyes shoot open..."
- "Your eyes snap open..."
- "Your eyes fly open..."

**Gradual/Peaceful:**
- "Your eyes slowly open..."
- "Your eyes drift open..."
- "Your eyes ease open..."

**Disoriented/Confused:**
- "Your eyes flutter open..."
- "Your eyes struggle open..."
- "Your eyes crack open..."

### Context Pairing

The opening should pair with immediate sensory context:

**Visual:**
- "Your eyes shoot open to the harsh glare of fluorescent lights..."
- "Your eyes slowly open, adjusting to the dim amber glow..."

**Auditory:**
- "Your eyes flutter open as the distant wail of sirens cuts through..."
- "Your eyes snap open to the metallic clang of a dropped wrench..."

**Physical Sensation:**
- "Your eyes ease open, the cold concrete floor pressing against your back..."
- "Your eyes struggle open, the taste of copper lingering in your mouth..."

**Combined:**
- "Your eyes shoot open to the harsh glare of fluorescent lights buzzing overhead, the smell of motor oil filling your nostrils."

## Benefits

### Narrative Benefits
1. **Clear Starting Point**: No ambiguity about when the story begins
2. **Immediate Engagement**: Reader/player is immediately in the moment
3. **Natural Discovery**: Character and reader discover the environment together
4. **Consistent Experience**: Every simulation starts the same way structurally

### Immersion Benefits
1. **Second Person Present**: "Your eyes" reinforces the player IS the character
2. **Sensory Grounding**: Eyes opening naturally leads to visual/sensory description
3. **Moment of Awareness**: Captures the transition from unconsciousness to consciousness
4. **Cinematic Quality**: Feels like a film opening shot

### Practical Benefits
1. **LLM Compliance**: Clear, specific instruction that's easy to follow
2. **Consistent Quality**: Reduces variation in opening quality
3. **Natural Flow**: Provides a template that flows naturally into scene description
4. **Flexible**: Works with any location, situation, or character type

## Integration with Other Systems

### Works With:
- **Sensory Perception Requirements**: Eyes opening naturally leads to sensory details
- **Interior/Exterior Consistency**: Establishes perspective from the start
- **Character Personality**: Can reflect personality in HOW eyes open (cautiously, eagerly, etc.)
- **World Context**: Immediate sensory detail can reference world lore
- **Four-Mode Narrative Loop**: Starts in ROAM mode with exploration focus

### Example Integration:

```
Your eyes slowly open, adjusting to the dim amber glow filtering through 
dusty windows. [WAKING UP OPENING]

You're in the back room of an abandoned warehouse, the air thick with the 
scent of dust and old vinyl. [LOCATION + SENSORY]

Sunlight filters through cracked skylights, illuminating stacks of crates 
labeled with faded band stickers. [WORLD CONTEXT - 1990s details]

A dusty turntable sits on a rickety table, its cables tangled like spaghetti. 
[EXPLORATION OPPORTUNITY]

Your fingers twitch toward the turntable—you always test equipment first, 
a habit from years of setting up last-minute gigs. [CHARACTER PERSONALITY]

The distant hum of the city pulses through the walls, a steady rhythm 
waiting to be matched. [ATMOSPHERIC TOUCH]
```

## Summary

Every simulation now begins with the character waking up - a clear, immersive starting point that establishes consciousness and naturally leads into environmental discovery. The requirement is simple, flexible, and enhances both narrative quality and player immersion.

**Result:** Consistent, cinematic openings that immediately engage the player in the moment of awakening.
