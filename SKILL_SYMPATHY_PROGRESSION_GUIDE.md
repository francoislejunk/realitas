# Skill & Sympathy Progression System - Complete Guide

## Overview

A comprehensive progression system that tracks **organic growth** through actual use - no XP points, just realistic improvement through practice and interaction.

### Two Systems:

1. **Skill Progression** - Skills improve through extraordinary performance
2. **Sympathy Progression** - Relationships evolve through interactions

---

## Skill Progression System

### Philosophy

**Practice makes perfect** - but only exceptional practice leads to growth.

- No XP grinding
- Only **extraordinary successes** (level 4+) count
- After **10 extraordinary uses**, **10% chance** to increase by 1
- Realistic, gradual improvement

### How It Works

**Success Levels:**
- 1 = Minimal/Failed
- 2 = Subpar
- 3 = Average
- **4 = Extraordinary** ← Counts for progression
- **5 = Superb/Critical** ← Counts for progression

**Progression Formula:**
```
1. Track extraordinary uses (success level 4+)
2. After 10 extraordinary uses → Roll for progression
3. 10% chance → Skill increases by 1
4. Reset counter (whether successful or not)
```

**Example:**
```
Turn 1: Shoot gun (success 4) → 1/10 extraordinary uses
Turn 5: Shoot gun (success 5) → 2/10 extraordinary uses
Turn 12: Shoot gun (success 4) → 3/10 extraordinary uses
...
Turn 45: Shoot gun (success 4) → 10/10 extraordinary uses
→ Roll for progression (10% chance)
→ SUCCESS! Gun Shooting: 2 → 3
→ Counter resets to 0/10
```

### Implementation

**File: `progression_tracker.py`**

**Class: `SkillProgressionTracker`**

**Key Methods:**
```python
# Record a skill use
result = tracker.record_skill_use(
    skill_name="Gun Shooting",
    success_level=4,  # Extraordinary
    action_description="I shoot the target"
)

# Returns progression result if skill increased
if result and result['increased']:
    print(f"Skill {result['skill_name']} increased!")
    # Actually increase the skill on actor sheet
    actor.sheet.skills[skill_name] += 1
```

**Storage:**
- Saved to: `./simulation_data/narrative_context/progression/skills/{actor_name}_skills.json`
- Persists between sessions
- Tracks usage history and progression events

---

## Sympathy Progression System

### Philosophy

**Relationships are dynamic** - they change based on how you treat people.

- Three ways sympathy can shift
- Organic relationship evolution
- Makes friends and enemies matter

### Three Methods of Sympathy Change

#### **Method 1: Direct Targeting**

Sympathy is the **target status** of the action.

**Examples:**
- "I try to befriend the guard" → Direct sympathy increase attempt
- "I intimidate the merchant" → Direct sympathy decrease attempt

**Implementation:**
```python
sympathy_tracker.record_direct_sympathy_change(
    actor1="Player",
    actor2="Guard",
    change_amount=+1,  # or -1
    reason="Successful befriending attempt"
)
```

**Effect:** Immediate sympathy change (if action succeeds)

---

#### **Method 2: Indirect Effect**

Sympathy is **not the target** but is **affected as a side effect**.

**Examples:**
- "I stab the guard" → Target: Stamina, Side effect: Sympathy decreases
- "I heal the merchant" → Target: Stamina, Side effect: Sympathy increases

**Logic:**
```python
if action_polarity == "Subtractive" and success:
    sympathy -= 1  # Harming someone decreases sympathy
elif action_polarity == "Additive" and success:
    sympathy += 1  # Helping someone increases sympathy
```

**Implementation:**
```python
sympathy_tracker.record_indirect_sympathy_effect(
    proactor="Player",
    reactor="Guard",
    action_description="I stab the guard",
    action_polarity="Subtractive",
    success=True
)
```

**Effect:** Automatic sympathy adjustment based on action type

---

#### **Method 3: Interaction Tracking**

Tracks **10 interactions**, then rolls for progression based on **majority lean**.

**How It Works:**
```
1. Track each interaction as FRIENDLY, HOSTILE, or NEUTRAL
2. After 10 interactions → Count majority
3. If majority is clear → 50/50 roll for sympathy shift
4. If roll succeeds → Sympathy changes by ±1
5. Reset counter
```

**Classification:**
- **FRIENDLY**: help, assist, heal, give, share, compliment, etc.
- **HOSTILE**: attack, hit, stab, shoot, threaten, insult, etc.
- **NEUTRAL**: Everything else

**Example:**
```
Interaction 1: "I help the guard" → FRIENDLY (1F, 0H)
Interaction 2: "I talk to the guard" → NEUTRAL (1F, 0H)
Interaction 3: "I give guard money" → FRIENDLY (2F, 0H)
Interaction 4: "I insult the guard" → HOSTILE (2F, 1H)
...
Interaction 10: "I assist the guard" → FRIENDLY (7F, 2H, 1N)

→ Majority: FRIENDLY (7 > 2)
→ Roll for progression (50% chance)
→ SUCCESS! Sympathy with Guard: +1 → +2
→ Counter resets
```

**Implementation:**
```python
# Classify interaction
interaction_type = sympathy_tracker.classify_interaction_type(
    action_description="I help the guard",
    action_polarity="Additive",
    success=True
)

# Record interaction
result = sympathy_tracker.record_interaction(
    actor1="Player",
    actor2="Guard",
    interaction_type=interaction_type,
    action_description="I help the guard"
)

if result and result['changed']:
    print(f"Sympathy changed: {result['change_amount']}")
    # Actually change sympathy on actor sheet
    actor.sheet.sympathies["Guard"] += result['change_amount']
```

**Storage:**
- Saved to: `./simulation_data/narrative_context/progression/sympathy/sympathy_progression.json`
- Persists between sessions
- Tracks interaction history and sympathy changes

---

## Integration into Main Simulation

### Setup (Already Done)

**1. Import (line 65-66):**
```python
from progression_tracker import ProgressionManager, InteractionType
from progression_integration_helper import process_and_display_progression
```

**2. Initialize (line 1924-1926):**
```python
# Initialize Progression Manager (Skill & Sympathy)
print(f"{Color.INFO}📈 Initializing Progression System...{Color.RESET}")
progression_manager = ProgressionManager(storage_dir)
```

### Integration Points

**After Every Action with Success Calculation:**

```python
# After calculating success
success_value = _calculate_detailed_success(actor, action_data, target_actor)

# Get action details
skill_used = action_data.get('skill_used', 'Unknown')
action_description = action_data.get('action_description', user_input)
action_polarity = action_data.get('shift_polarity', 'Neutral')

# Process progression
try:
    process_and_display_progression(
        progression_manager=progression_manager,
        proactor_name=proactor.sheet.name,
        reactor_name=reactor.sheet.name if reactor else None,
        skill_used=skill_used,
        success_value=success_value,
        action_description=action_description,
        action_polarity=action_polarity,
        proactor_actor=proactor,
        reactor_actor=reactor
    )
except Exception as e:
    print(f"{Color.WARNING}Progression tracking skipped: {e}{Color.RESET}")
```

**This will:**
1. Track skill usage
2. Check for skill progression
3. Record sympathy indirect effects
4. Track interactions
5. Check for sympathy progression
6. Display all progression results
7. Actually update actor sheets

---

## Display Examples

### Skill Progression

**Close to Progression:**
```
💪 You're getting better at Gun Shooting... (progression roll: Progression roll failed (10% chance))
```

**Successful Progression:**
```
📈 SKILL PROGRESSION!
Your Gun Shooting skill has increased by 1!
Reason: After 10 extraordinary uses
✓ Gun Shooting: 2 → 3
```

### Sympathy Changes

**Indirect Effect:**
```
💔 Sympathy decreased with Guard
Reason: Subtractive action: I stab the guard
Sympathy: +2 → +1
```

**Interaction Tracking (Close):**
```
🤝 Your relationship with Guard is evolving... (Progression roll failed (50% chance))
```

**Successful Progression:**
```
💚 SYMPATHY PROGRESSION!
Your relationship with Guard has increased!
Reason: Majority friendly interactions (7 friendly, 2 hostile)
✓ Sympathy: +1 → +2
```

---

## Benefits

### **1. Organic Growth**
- No artificial XP systems
- Skills improve through actual use
- Relationships evolve naturally

### **2. Meaningful Practice**
- Only exceptional performance counts
- Encourages skill mastery
- Rewards excellence

### **3. Dynamic Relationships**
- Every action affects relationships
- Friends and enemies matter
- Realistic social dynamics

### **4. Strategic Depth**
- Choose actions carefully
- Build relationships intentionally
- Long-term consequences

### **5. Immersive**
- Feels like real skill development
- Natural relationship progression
- No meta-gaming

---

## Technical Details

### Skill Progression

**Tracking:**
- Extraordinary uses stored per skill
- Progression history maintained
- Persistent across sessions

**Progression Chance:**
- 10% after 10 extraordinary uses
- Random but fair
- Prevents guaranteed grinding

**Reset:**
- Counter resets after 10 uses (whether successful or not)
- Prevents infinite accumulation
- Keeps progression rare

### Sympathy Progression

**Three Independent Systems:**
1. Direct targeting - Immediate effect
2. Indirect effect - Automatic side effect
3. Interaction tracking - Long-term progression

**Interaction Classification:**
- Keyword-based detection
- Polarity-based fallback
- Neutral as default

**Progression Chance:**
- 50% after 10 interactions (if majority clear)
- Balanced probability
- Requires consistent behavior

**Limits:**
- Sympathy capped at -5 to +5
- Prevents extreme values
- Maintains balance

---

## File Structure

```
progression_tracker.py
├── SkillProgressionTracker
│   ├── record_skill_use()
│   ├── get_skill_progress()
│   └── Storage: {actor}_skills.json
│
├── SympathyProgressionTracker
│   ├── record_direct_sympathy_change()
│   ├── record_indirect_sympathy_effect()
│   ├── record_interaction()
│   ├── classify_interaction_type()
│   ├── get_sympathy_progress()
│   └── Storage: sympathy_progression.json
│
└── ProgressionManager
    ├── get_skill_tracker()
    ├── process_action_result()
    └── Unified interface

progression_integration_helper.py
├── process_and_display_progression()
├── display_progression_status()
└── display_sympathy_progression_status()
```

---

## Summary

**Skill Progression:**
- ✅ 10 extraordinary uses → 10% chance → +1 skill
- ✅ Realistic growth through excellence
- ✅ Persistent tracking

**Sympathy Progression:**
- ✅ Direct targeting (immediate)
- ✅ Indirect effects (automatic)
- ✅ Interaction tracking (long-term)
- ✅ 10 interactions → majority → 50% chance → ±1 sympathy

**Integration:**
- ✅ Initialized in main
- ✅ Helper functions ready
- ✅ Just call after success calculation

**Result:**
- Organic skill development
- Dynamic relationships
- Meaningful progression
- Perfect immersion

**Your skills and relationships now grow naturally through play!** 📈✨
