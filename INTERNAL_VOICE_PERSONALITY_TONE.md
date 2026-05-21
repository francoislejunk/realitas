# Internal Voice Tone Matches Internal Personality

## The Issue

Internal voice had a generic "helpful friend" tone regardless of the character's internal personality.

## The Fix

**Tone MUST match internal personality** - every word should sound like someone with that personality.

## Personality-Driven Tone Examples

### Cynical Character
```
"Great, another problem. Of course this would happen now. We should've 
known better than to trust that guy. Let's just get this over with."
```

### Optimistic Character
```
"This could work out. We've got what we need. Things are looking up - 
we just need to stay positive and keep pushing forward."
```

### Analytical Character
```
"The data suggests we should approach this methodically. Based on the 
pattern, our best option is to analyze the variables before proceeding."
```

### Impulsive Character
```
"Screw it, let's just go for it. No time to overthink this - we'll 
figure it out as we go. What's the worst that could happen?"
```

### Cautious Character
```
"We should think this through carefully before acting. Better safe 
than sorry. Let's make sure we're not missing anything important."
```

### Sarcastic Character
```
"Oh wonderful, exactly what we needed. This'll be fun. I'm sure 
nothing could possibly go wrong with this brilliant plan."
```

### Earnest Character
```
"We really need to focus here. This matters. Let's give it everything 
we've got and make sure we do this right."
```

## Implementation

### Prompt Addition
```python
**CRITICAL: TONE MUST MATCH INTERNAL PERSONALITY**
The way you communicate MUST reflect: {internal_personality}

Examples of how personality affects tone:
- CYNICAL: "Great, another problem. Of course this would happen now."
- OPTIMISTIC: "This could work out. We've got what we need."
- ANALYTICAL: "The data suggests we should approach this methodically."
- IMPULSIVE: "Screw it, let's just go for it. No time to overthink."
- CAUTIOUS: "We should think this through carefully before acting."
- SARCASTIC: "Oh wonderful, exactly what we needed. This'll be fun."
- EARNEST: "We really need to focus here. This matters."
```

### System Message Update
```python
"CRITICAL: (1) TONE must match personality '{internal_personality}' - 
cynical=cynical tone, optimistic=optimistic tone, etc. (2) Use context 
to be SPECIFIC. Every word must sound like someone who is {internal_personality}."
```

### Format Requirements
```
**TONE:** MUST match internal personality: {internal_personality}
- NOT generic "helpful friend" - match the CHARACTER'S personality
- Cynical character = cynical tone
- Optimistic character = optimistic tone
- Analytical character = analytical tone

**CRITICAL:** Every word must sound like someone who is {internal_personality}
```

## File Modified

**`agents/narrator_agent.py`** - `generate_inquiry_internal_voice()` (lines 3129-3203)

## Result

✅ **Personality-Driven Tone** - Matches internal personality  
✅ **Immersive** - Sounds like the character's actual thoughts  
✅ **Consistent** - Maintains personality throughout  
✅ **Not Generic** - Each character sounds unique  

The internal voice now speaks with the character's personality, not a generic helpful tone.
