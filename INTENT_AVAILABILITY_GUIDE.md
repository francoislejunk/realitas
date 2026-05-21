# Intent Availability System - No Manifestation

## The Problem: Manifestation

**Manifestation** is when user intents are automatically granted without realistic world constraints. This destroys immersion:

❌ **Bad:** User says "I want to go to a diner" → System immediately creates a diner  
❌ **Bad:** User says "I want to visit my friend" → System creates a friend that never existed  
❌ **Bad:** User says "I want to use magic" → System grants magic powers in a realistic world

## The Solution: Three-Way Classification

Every user intent is classified into one of three categories:

### 1. **AVAILABLE NOW** - Push Through With Action
The intent CAN be pursued immediately. Find the most diegetic and logical way it can occur.

**Example:**
- **User Intent:** "I want to check on my car"
- **Context:** Car was previously mentioned, parked in garage
- **Response:** "You head down to the garage where your Lamborghini is parked. The keys are in your pocket."

### 2. **AVAILABLE LATER** - Save for Later
The intent is VALID but timing/circumstances prevent it RIGHT NOW. Save it for later opportunity narration or Sparks.

**Example:**
- **User Intent:** "I want to go to the nearest diner"
- **Context:** It's 3am, too early for restaurants
- **Response:** "You check the time and realize it's way too early for any nearby restaurant to be open. The sun hasn't even risen yet. You'll need to wait a few hours."
- **Later:** In opportunity narration: "Time has passed quickly and you realize you might finally be able to look for a place to eat."

### 3. **AVAILABLE NEVER** - Doesn't Exist
The intent references something that doesn't exist in the established world.

**Example:**
- **User Intent:** "I want to meet up with my childhood friends"
- **Context:** No childhood friends ever mentioned
- **Response:** "Your memories rush back like a tidal wave - you haven't had contact with childhood friends in years. That part of your life is long gone."

---

## Classification Logic

### If Intent IS Supported by Context
**50/50 split between AVAILABLE NOW and AVAILABLE LATER**

Context support means:
- The thing/person was previously mentioned
- It exists in established facts
- It's consistent with the world

**Example:**
- Intent: "I want to visit the diner"
- Context: Diner was mentioned earlier
- Result: 50% chance NOW, 50% chance LATER (never NEVER)

### If Intent is NOT Supported by Context
**1/3 chance each for NOW, LATER, or NEVER**

No context support means:
- Never mentioned before
- Not in established facts
- New element being introduced

**Example:**
- Intent: "I want to visit my childhood friend"
- Context: No friend ever mentioned
- Result: 33% NOW (friend exists!), 33% LATER (friend exists but unavailable), 33% NEVER (no such friend)

---

## Integration Pattern

### Step 1: Evaluate Intent Availability

```python
from intent_availability_system import IntentAvailabilitySystem
from pathlib import Path

# Initialize system
intent_system = IntentAvailabilitySystem(Path("./sessions"))

# Evaluate user intent
result = intent_system.evaluate_intent_availability(
    user_intent="I want to go to the diner",
    narrative_context=recent_narrative_history,
    scene_context=current_scene_description,
    established_facts=list_of_established_facts,
    current_time_of_day="evening"  # Optional but helpful
)

# Result contains:
# - availability: AVAILABLE_NOW, AVAILABLE_LATER, or AVAILABLE_NEVER
# - diegetic_explanation: Narrative explanation
# - action_path: How to proceed (if NOW)
# - deferral_trigger: When to bring up again (if LATER)
```

### Step 2: Handle Each Case

```python
from intent_availability_system import IntentAvailability

if result["availability"] == IntentAvailability.AVAILABLE_NOW:
    # Proceed with the action
    print(result["diegetic_explanation"])
    # Continue to action interpretation and execution
    
elif result["availability"] == IntentAvailability.AVAILABLE_LATER:
    # Explain why not now, save for later
    print(result["diegetic_explanation"])
    # Intent is automatically saved in deferred_intents
    # Will be brought up in opportunity narration
    
elif result["availability"] == IntentAvailability.AVAILABLE_NEVER:
    # Explain that this doesn't exist
    print(result["diegetic_explanation"])
    # Prompt user for a different action
```

### Step 3: Opportunity Narration Integration

When generating opportunity narration, include deferred intents:

```python
# Get hints for deferred intents
opportunity_hints = intent_system.get_opportunity_narration_hints()

# Include in opportunity narration prompt
opportunity_prompt = f"""
{opportunity_hints}

Generate opportunity narration that might include:
- Bringing up one of the deferred intents if timing is now appropriate
- New opportunities based on current scene
- Subtle nudges toward goals

[Rest of prompt...]
"""

# After using a deferred intent in narration
intent_system.mark_intent_triggered(intent_index=0)
```

---

## Example Flow

### Scenario 1: Supported Intent (Diner Exists)

**User:** "I want to go to the diner"  
**Context:** Joe's Diner was mentioned earlier

**System Evaluation:**
- Checks context → Diner IS mentioned
- 50/50 choice → Rolls AVAILABLE_LATER (it's 3am)

**Output:**
```
You check the time and realize it's way too early for any nearby restaurant 
to be open. Even Joe's Diner, which usually opens early, won't be serving 
for another few hours. The streets are still dark and empty.
```

**Later (Opportunity Narration):**
```
Time has passed quickly as you've been walking. The sun is rising now, and 
you notice the familiar neon sign of Joe's Diner flickering to life down 
the street. The smell of fresh coffee drifts through the morning air.
```

### Scenario 2: Unsupported Intent (Friend Never Mentioned)

**User:** "I want to visit my childhood friend Sarah"  
**Context:** No Sarah ever mentioned

**System Evaluation:**
- Checks context → Sarah NOT mentioned
- 1/3 random → Rolls AVAILABLE_NEVER

**Output:**
```
Your memories rush back like a tidal wave. Sarah... you haven't thought 
about her in years. You lost touch after high school when she moved away. 
You don't even know where she is now, or if she'd want to hear from you 
after all this time. That part of your life is long gone.
```

### Scenario 3: Unsupported Intent (Lucky Roll)

**User:** "I want to find a mechanic"  
**Context:** No mechanic ever mentioned

**System Evaluation:**
- Checks context → Mechanic NOT mentioned
- 1/3 random → Rolls AVAILABLE_NOW (lucky!)

**Output:**
```
You remember seeing a small auto shop a few blocks back. The sign read 
"Tony's Garage" - looked like a family-owned place. It's worth a shot. 
You head back in that direction.
```

---

## Key Features

### 1. Diegetic Explanations
All responses are narratively explained, never meta:
- ✅ "The sun hasn't risen yet, restaurants won't be open for hours"
- ❌ "This action is not available right now"

### 2. Deferred Intent Tracking
AVAILABLE_LATER intents are saved and can be brought up later:
```python
deferred = intent_system.get_deferred_intents(triggered_only=True)
# Returns list of intents waiting for the right moment
```

### 3. Probabilistic Fairness
- Supported intents: 50/50 (fair chance for NOW vs LATER)
- Unsupported intents: 1/3 each (equal opportunity for all outcomes)

### 4. Context-Aware
System checks:
- Narrative history
- Established facts
- Scene context
- Time of day
- Logical constraints

---

## Integration Checklist

When integrating into main simulation:

- [ ] Initialize `IntentAvailabilitySystem` at simulation start
- [ ] Call `evaluate_intent_availability()` for each user intent
- [ ] Handle all three availability cases (NOW, LATER, NEVER)
- [ ] Include deferred intents in opportunity narration prompts
- [ ] Mark intents as triggered when used in narration
- [ ] Pass comprehensive context (narrative, facts, time)
- [ ] Use diegetic explanations in all responses

---

## Benefits

### Prevents Manifestation
- World doesn't bend to user wishes
- Realistic constraints enforced
- Immersion maintained

### Adds Realism
- Things take time
- Not everything is available immediately
- Some things don't exist

### Creates Anticipation
- Deferred intents build anticipation
- Opportunity narration feels rewarding
- Player agency preserved (intent wasn't rejected, just deferred)

### Maintains Flexibility
- 1/3 chance for unsupported intents means surprises
- World can expand organically
- Not overly restrictive

---

## Common Patterns

### Restaurant/Food
- **Supported + Right Time** → AVAILABLE_NOW
- **Supported + Wrong Time** → AVAILABLE_LATER (too early/late)
- **Unsupported** → 1/3 chance (might find one, might wait, might not exist nearby)

### People/Relationships
- **Supported (mentioned before)** → NOW or LATER (available vs busy)
- **Unsupported** → NEVER (no such person) or NOW (lucky encounter) or LATER (exists but not available)

### Locations
- **Supported** → NOW (can go there) or LATER (closed/far)
- **Unsupported** → 1/3 chance each

### Objects/Possessions
- **Supported (established)** → NOW (have it) or LATER (need to get it)
- **Unsupported** → NEVER (don't own it) or NOW (find it) or LATER (can acquire it)

---

## Summary

The Intent Availability System prevents manifestation by:

1. **Checking context** - Does this exist in the established world?
2. **Probabilistic selection** - Fair chance distribution (50/50 or 1/3)
3. **Diegetic explanation** - Everything explained narratively
4. **Deferred tracking** - LATER intents saved for opportunity narration

**Result:** Realistic world with constraints, no manifestation, perfect immersion.
