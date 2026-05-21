# Memory Creation Based on Intent Availability

## The New Logic

Memory creation is now **directly tied** to the intent availability system:

### EXIST → Create Memory About the Thing
- **The thing exists and is accessible**
- Create memory describing it
- Example: "You have a loving mother, Margaret, who lives nearby"

### EXIST_NOT_HERE → Create Memory About Why Not Here
- **The thing exists but is unavailable**
- Create memory explaining the constraint/distance
- Example: "You have a sister, Sarah, but she moved to California years ago"

### DOES_NOT_EXIST → NO Memory Created
- **We don't know anything about it**
- No memory is created
- The character has no knowledge of this

## The Flow

```
User: "I want to call my sister"
↓
Intent Availability Check
↓
┌─────────────────────────────────────────┐
│ EXIST                                   │
│ → Create memory: "You have a sister..." │
│ → Allow action to proceed               │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ EXIST_NOT_HERE                          │
│ → Create memory: "You had a sister but  │
│    she moved away..."                   │
│ → Block action with explanation         │
└─────────────────────────────────────────┘

┌─────────────────────────────────────────┐
│ DOES_NOT_EXIST                          │
│ → NO memory created                     │
│ → Block action: "You don't have a       │
│    sister"                              │
└─────────────────────────────────────────┘
```

## Examples by Availability

### EXIST Examples

**Family:**
```
Memory: "You have a loving mother, Margaret, who lives in the suburbs. 
She calls every Sunday."
Internal Voice: "I should call mom soon. She worries when I don't check in."
```

**Location:**
```
Memory: "You know Joe's Diner on 5th Street. Best coffee in town, open 24/7."
Internal Voice: "Joe's is just a few blocks away. Could grab a coffee there."
```

**Possession:**
```
Memory: "You own a reliable '98 Honda Civic, parked outside your apartment."
Internal Voice: "The Honda's been good to me. Should probably change the oil soon."
```

**Relationship:**
```
Memory: "You have a close friend named Jake who works at the garage downtown."
Internal Voice: "Jake would help with this. He's always got my back."
```

### EXIST_NOT_HERE Examples

**Family:**
```
Memory: "You have a sister, Sarah, who moved to California years ago after 
the argument. You haven't spoken since."
Internal Voice: "I wonder how Sarah's doing. Maybe I'll reach out someday."
```

**Location:**
```
Memory: "You used to go to Murphy's Bar downtown, but it closed last year 
after the fire."
Internal Voice: "I miss Murphy's. That place had character. Nothing like it now."
```

**Possession:**
```
Memory: "You had a motorcycle but sold it last year to pay rent."
Internal Voice: "I miss that bike. Freedom on two wheels. Had to let it go."
```

**Relationship:**
```
Memory: "You had a best friend, Marcus, but lost touch after he moved to Seattle."
Internal Voice: "Marcus would know what to do. Wish we'd stayed in touch."
```

### DOES_NOT_EXIST Examples

**No memory created!**

The character simply doesn't know anything about this. The system will block the action with a diegetic explanation, but no memory is added to the character sheet.

## Implementation

### File Modified: `intent_based_memory_creation.py`

**Lines 170-173:** Early return for DOES_NOT_EXIST
```python
# DOES_NOT_EXIST → No memory created
if availability == IntentAvailability.DOES_NOT_EXIST:
    self.logger.info(f"Intent does not exist - no memory created")
    return None
```

**Lines 198-216:** Updated prompt guidelines
```python
**If EXIST:**
- Create memory about the thing (it exists and is accessible)
- This thing exists and can be interacted with

**If EXIST_NOT_HERE:**
- Create memory about why it's not here (exists but unavailable)
- Explain the constraint or distance

**NOTE:** DOES_NOT_EXIST should never reach this function - no memory 
is created in that case.
```

**Lines 228-242:** Updated examples
- EXIST examples show accessible things
- EXIST_NOT_HERE examples explain constraints
- No DOES_NOT_EXIST examples (no memory created)

## Key Benefits

### 1. Logical Consistency
- Memory creation matches availability
- No contradictions between memory and constraints

### 2. Clear Semantics
- EXIST = thing exists → create memory
- EXIST_NOT_HERE = thing exists but unavailable → create memory with constraint
- DOES_NOT_EXIST = no knowledge → no memory

### 3. Immersive Explanations
- EXIST_NOT_HERE memories explain WHY something isn't available
- "Your sister moved to California" is more immersive than just "not available"

### 4. Character Development
- Memories build character backstory naturally
- Constraints have narrative reasons
- Character knowledge grows organically

## Result

✅ **EXIST** → Memory created about accessible thing  
✅ **EXIST_NOT_HERE** → Memory created explaining constraint  
✅ **DOES_NOT_EXIST** → No memory created (no knowledge)  
✅ **Logical Consistency** → Memory matches availability  
✅ **Immersive** → Constraints have narrative explanations  

Memory creation is now directly tied to intent availability, ensuring consistency and immersion.
