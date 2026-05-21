# Internal Voice Suggests, Never Instructs

## The Principle

The internal voice **suggests possibilities** with "could", it **never instructs** with "should", "need to", "have to", or "must".

The user decides what to do - the internal voice just offers ideas.

## Forbidden Words

❌ **NEVER USE:**
- "should" - Too instructive
- "need to" - Too commanding
- "have to" - Too demanding
- "must" - Too forceful
- "let's" - Too directive

✅ **ALWAYS USE:**
- "could" - Suggests possibility
- "might" - Offers option
- "maybe" - Presents idea

## Examples: Instructions vs. Suggestions

### Example 1: Calling Friend

❌ **INSTRUCTING (Bad):**
```
"We should call Sarah about that party."
"We need to call Sarah."
"Let's call Sarah."
```

✅ **SUGGESTING (Good):**
```
"We could call Sarah about that party we're planning."
```

### Example 2: Getting Items

❌ **INSTRUCTING (Bad):**
```
"We need to grab those demo tapes."
"We should get the demo tapes now."
"Let's grab those tapes."
```

✅ **SUGGESTING (Good):**
```
"We could grab those demo tapes for the gig tonight - they're on the shelf by the turntable."
```

### Example 3: Finding Rest

❌ **INSTRUCTING (Bad):**
```
"We need to find somewhere safe to rest."
"We should look for a place to rest."
"We have to rest before we collapse."
```

✅ **SUGGESTING (Good):**
```
"We could look for somewhere safe to rest before we collapse."
```

### Example 4: Asking for Information

❌ **INSTRUCTING (Bad):**
```
"We should ask Mike about the deal."
"We need to talk to Mike."
"Let's ask Mike."
```

✅ **SUGGESTING (Good):**
```
"We could ask Mike about that deal we're investigating."
```

### Example 5: Taking Transportation

❌ **INSTRUCTING (Bad):**
```
"We need to hurry."
"We should take the U-Bahn."
"We have to leave now."
```

✅ **SUGGESTING (Good):**
```
"We could take the U-Bahn if we want to make that 3pm meeting."
```

## The Difference

### Instructions (Bad)
- Tell the user what to do
- Remove player agency
- Feel like commands
- Break immersion

### Suggestions (Good)
- Present possibilities
- Preserve player choice
- Feel like helpful ideas
- Maintain immersion

## Personality + Suggestions

Even with different personalities, always use "could":

**Cynical:**
```
"We could try asking around, but it probably won't help."
```

**Optimistic:**
```
"We could approach this head-on. This could work out."
```

**Analytical:**
```
"We could approach this methodically, or we could try the direct route."
```

**Impulsive:**
```
"We could just go for it. No time to overthink."
```

**Cautious:**
```
"We could think this through carefully. Or we could wait and see."
```

## Implementation

### Prompt Addition
```python
**CRITICAL: NEVER INSTRUCT - ONLY SUGGEST POSSIBILITIES**
- Use "could" to suggest options (NOT "should", "need to", "have to", "must")
- Present possibilities, not commands
- The user decides what to do - you just offer ideas
```

### System Message (Priority #1)
```python
"CRITICAL: (1) NEVER INSTRUCT - use 'could' to suggest possibilities, 
NEVER 'should/need to/have to/must'. Present options, not commands."
```

### Examples Updated
All examples now show:
- ✓ GOOD: Uses "could"
- ✗ BAD: Uses "should/need to" (marked as instructing)

## File Modified

**`agents/narrator_agent.py`** - `generate_inquiry_internal_voice()` (lines 3132-3214)

## Result

✅ **Suggests Possibilities** - Uses "could" to offer options  
✅ **Preserves Agency** - User decides what to do  
✅ **Non-Directive** - Presents ideas, not commands  
✅ **Immersive** - Feels like helpful thoughts, not instructions  

The internal voice now suggests what the character **could** do, never tells them what they **should** do.
