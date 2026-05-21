# NPC Pronoun System

## The Problem

Users want to reference NPCs by pronouns:
```
"I talk to him"
"I approach her"
"I give them the key"
```

Without pronoun tracking, the system gets confused and can't resolve who "him", "her", or "them" refers to.

## The Solution

**Every NPC is assigned pronouns (he/him, she/her, they/them)** which allows the system to resolve pronoun references.

## Implementation

### 1. ActorSheet Pronouns Field

**File: `actor_sheet.py`** (lines 174, 184-185)

Added `pronouns` parameter to ActorSheet:
```python
def __init__(self, ..., pronouns: Optional[str] = None):
    # Pronouns for pronoun resolution (he/him, she/her, they/them)
    self.pronouns = pronouns if pronouns is not None else "they/them"
```

**Default:** `"they/them"` if not specified

### 2. NPC Generation with Pronouns

**File: `agents/creator_agent.py`** (lines 727, 744, 886)

Updated NUA generation to include pronouns:

**Prompt Requirements:**
```python
**Requirements:**
- Name: Appropriate for the context
- Age: Character's age
- Location: Geographic location
- Pronouns: Character's pronouns (he/him, she/her, they/them)  # NEW
- Occupation: Role/job
...
```

**JSON Response:**
```json
{
    "name": "Character Name",
    "age": 35,
    "location": "New York",
    "pronouns": "he/him",  // NEW
    "occupation": "Character Role",
    ...
}
```

**ActorSheet Creation:**
```python
nua_sheet = ActorSheet(
    name=nua_data['name'],
    ...
    pronouns=nua_data.get('pronouns', 'they/them')  # Extract from generated data
)
```

### 3. Pronoun Resolution System

**File: `pronoun_resolution.py`** (NEW)

Helper functions for resolving pronouns:

#### `get_pronoun_forms(pronouns: str)`
Returns all forms of a pronoun set:
```python
get_pronoun_forms("he/him")
→ ("he", "him", "his", "his", "himself")

get_pronoun_forms("she/her")
→ ("she", "her", "her", "hers", "herself")

get_pronoun_forms("they/them")
→ ("they", "them", "their", "theirs", "themselves")
```

#### `resolve_pronoun_to_npc(pronoun, available_npcs, recent_npc_name)`
Resolves a pronoun to an NPC name:
```python
resolve_pronoun_to_npc("him", available_npcs)
→ "Marcus"  # If Marcus has pronouns "he/him"

resolve_pronoun_to_npc("her", available_npcs)
→ "Sarah"  # If Sarah has pronouns "she/her"
```

**Logic:**
1. Maps pronoun to base form (e.g., "him" → "he/him")
2. Finds NPCs with matching pronouns
3. If one match, returns that NPC
4. If multiple matches, prefers recently mentioned NPC
5. If no match, returns None

#### `extract_pronoun_from_action(action: str)`
Extracts pronoun from user action:
```python
extract_pronoun_from_action("I talk to him")
→ "him"

extract_pronoun_from_action("I approach her")
→ "her"
```

#### `replace_pronoun_with_name(action, pronoun, npc_name)`
Replaces pronoun with NPC name:
```python
replace_pronoun_with_name("I talk to him", "him", "Marcus")
→ "I talk to Marcus"

replace_pronoun_with_name("I approach her", "her", "Sarah")
→ "I approach Sarah"
```

## Usage Flow

### Example 1: Single NPC

```
Scene: "A bartender wipes down the counter."

[NPC PARSER] Detected: Bartender
[NPC GENERATION] Created: Mike (pronouns: "he/him")

User: "I talk to him"
↓
[PRONOUN RESOLUTION]
1. Extract pronoun: "him"
2. Find NPCs with "he/him": [Mike]
3. Resolve to: "Mike"
4. Replace: "I talk to Mike"
↓
System: ✓ Processes conversation with Mike
```

### Example 2: Multiple NPCs

```
Scene: "A waitress approaches. A security guard stands by the door."

[NPC PARSER] Detected: Waitress, Security Guard
[NPC GENERATION] 
- Created: Linda (pronouns: "she/her")
- Created: Marcus (pronouns: "he/him")

User: "I talk to her"
↓
[PRONOUN RESOLUTION]
1. Extract pronoun: "her"
2. Find NPCs with "she/her": [Linda]
3. Resolve to: "Linda"
4. Replace: "I talk to Linda"
↓
System: ✓ Processes conversation with Linda

User: "I approach him"
↓
[PRONOUN RESOLUTION]
1. Extract pronoun: "him"
2. Find NPCs with "he/him": [Marcus]
3. Resolve to: "Marcus"
4. Replace: "I approach Marcus"
↓
System: ✓ Processes encounter with Marcus
```

### Example 3: Ambiguous Reference

```
Scene: "Two men in suits sit in the corner booth."

[NPC PARSER] Detected: Man in Suit #1, Man in Suit #2
[NPC GENERATION]
- Created: Man in Suit #1 (pronouns: "he/him")
- Created: Man in Suit #2 (pronouns: "he/him")

User: "I talk to him"
↓
[PRONOUN RESOLUTION]
1. Extract pronoun: "him"
2. Find NPCs with "he/him": [Man in Suit #1, Man in Suit #2]
3. Ambiguous! Use most recent or first match
4. Resolve to: "Man in Suit #1"
5. Replace: "I talk to Man in Suit #1"
↓
System: ✓ Processes conversation (may not be the intended NPC)
```

**Note:** For ambiguous cases, the system should ideally ask for clarification, but defaults to first/recent match.

## Supported Pronouns

### he/him
- Subject: he
- Object: him
- Possessive: his
- Possessive pronoun: his
- Reflexive: himself

### she/her
- Subject: she
- Object: her
- Possessive: her
- Possessive pronoun: hers
- Reflexive: herself

### they/them
- Subject: they
- Object: them
- Possessive: their
- Possessive pronoun: theirs
- Reflexive: themselves

## Integration Points

### Where to Add Pronoun Resolution

**In action processing** (before intent parsing):

```python
# Extract pronoun from action
pronoun = extract_pronoun_from_action(user_input)

if pronoun:
    # Resolve to NPC name
    npc_name = resolve_pronoun_to_npc(pronoun, available_npcs, recent_npc_name)
    
    if npc_name:
        # Replace pronoun with name
        user_input = replace_pronoun_with_name(user_input, pronoun, npc_name)
        print(f"[PRONOUN RESOLUTION] Resolved '{pronoun}' → '{npc_name}'")
```

**Location:** Early in action processing, before intent interpretation

## Benefits

✅ **Natural Language** - Users can say "him" instead of full names  
✅ **Immersive** - Feels more like natural conversation  
✅ **Automatic** - NPCs get pronouns assigned during generation  
✅ **Flexible** - Supports he/him, she/her, they/them  
✅ **Resolves References** - System knows who "him" or "her" refers to  

## Files Modified

1. **`actor_sheet.py`** (lines 174, 184-185)
   - Added `pronouns` parameter to ActorSheet
   - Default: "they/them"

2. **`agents/creator_agent.py`** (lines 727, 744, 886)
   - Updated NUA generation prompt to include pronouns
   - Extract pronouns from generated data
   - Pass to ActorSheet creation

3. **`pronoun_resolution.py`** (NEW)
   - Pronoun resolution helper functions
   - Extract, resolve, and replace pronouns

## Next Steps

⚠️ **TODO:** Integrate pronoun resolution into main action processing loop
- Add pronoun extraction before intent parsing
- Resolve pronouns to NPC names
- Replace pronouns in user input
- Log resolution for debugging

## Result

NPCs now have pronouns assigned automatically, enabling natural pronoun references like "I talk to him" or "I approach her" without confusion.
