# NarratorAgent - Grouped NUA Narrative System ✅

## What Was Added

The NarratorAgent now generates **cohesive group narratives** for grouped NPC turns, replacing individual action descriptions with coordinated assault narratives.

## New Method: `generate_grouped_action_narrative()`

### **Location:** `narrator_agent.py` lines 657-785

### **Signature:**
```python
def generate_grouped_action_narrative(
    self,
    group_results: list,           # List of {'npc', 'action', 'success'} for each group member
    reactor: Actor,                 # The defender
    reactor_success: int,           # Reactor's single defense roll
    reactor_action_data: Dict = None,
    time_context: Optional[Dict] = None,
    framing_guidance: Optional[Dict] = None
) -> str:
```

---

## How It Works

### **Input Data Structure:**

```python
group_results = [
    {
        'npc': <Bandit A Actor>,
        'action': {
            'narrative_description': 'attempts to circle behind...',
            'shift_magnitude': -2,
            ...
        },
        'success': +5
    },
    {
        'npc': <Bandit B Actor>,
        'action': {
            'narrative_description': 'lunges forward with a feint...',
            'shift_magnitude': -2,
            ...
        },
        'success': +3
    },
    {
        'npc': <Bandit C Actor>,
        'action': {
            'narrative_description': 'moves to block the exit...',
            'shift_magnitude': -3,
            ...
        },
        'success': +8
    }
]

reactor = <Detective Actor>
reactor_success = +2  # Single defense roll with overwhelm penalty
```

---

### **Processing Steps:**

**1. Calculate Individual Outcomes:**
```python
for result in group_results:
    outcome = result['success'] - reactor_success
    hit = outcome > 0
    
# Example:
# Bandit A: +5 vs +2 = +3 ✓ HIT
# Bandit B: +3 vs +2 = +1 ✓ HIT
# Bandit C: +8 vs +2 = +6 ✓ HIT
```

**2. Build LLM Prompt:**
```python
prompt = f"""
You are a master combat narrator creating a cohesive narrative for a GROUPED NPC ATTACK.

**SCENARIO:**
3 NPCs are attacking Detective simultaneously in a coordinated assault.

**GROUP MEMBERS & ACTIONS:**
- Bandit A attempts to circle behind while allies distract
- Bandit B lunges forward with a feint, drawing attention
- Bandit C moves to block the exit while allies engage

**REACTOR:**
Detective defends against the coordinated attack (overwhelm penalty: +4 stress)

**OUTCOME:**
- Reactor Defense Roll: +2
- Successful Hits: 3/3
- Failed Attacks: 0/3

**DETAILED RESULTS:**
- Bandit A: +5 vs +2 = ✓ HIT
- Bandit B: +3 vs +2 = ✓ HIT
- Bandit C: +8 vs +2 = ✓ HIT

**YOUR TASK:**
Write a cohesive 3-4 sentence narrative that:
1. Opens with group coordination
2. Describes individual actions
3. Shows reactor's response
4. Delivers the outcome
"""
```

**3. Generate Cohesive Narrative:**
```
The three bandits move as one, their coordination honed by countless ambushes. 
Bandit A circles left while Bandit B rushes forward with aggressive feints, 
splitting the Detective's attention. As the Detective turns to block Bandit B's 
strike, Bandit C slips in from the right - all three attacks find their mark 
before the Detective can recover, leaving them reeling from the coordinated assault.
```

---

## Example Outputs

### **Example 1: All Attacks Hit (3/3)**

**Input:**
- 3 Bandits attack Detective
- Reactor defense: +2 (overwhelmed)
- All 3 attackers succeed

**Output:**
```
The three bandits coordinate their assault with deadly precision. Bandit A circles 
behind, drawing your attention with aggressive posturing, while Bandit B rushes in 
from the left with a vicious swing. You pivot to block Bandit B, but Bandit C 
exploits the opening - all three attacks land before you can recover, leaving you 
staggered and bleeding from multiple wounds.
```

---

### **Example 2: Partial Success (2/3 Hit)**

**Input:**
- 3 Guards attack Thief
- Reactor defense: +5 (good roll despite overwhelm)
- 2 attackers succeed, 1 fails

**Output:**
```
The guards work in practiced unison, attempting to surround and subdue the thief. 
Guard A lunges with a grapple while Guard B swings his baton from the right. The 
thief manages to duck under Guard B's swing, but Guard A's grip finds purchase on 
their arm. Guard C's follow-up strike connects solidly with the thief's shoulder, 
the coordinated assault taking its toll despite their desperate evasion.
```

---

### **Example 3: All Attacks Blocked (0/3)**

**Input:**
- 3 Thugs attack Martial Artist
- Reactor defense: +12 (excellent roll)
- All 3 attackers fail

**Output:**
```
The three thugs rush in together, attempting to overwhelm through sheer numbers. 
Thug A swings high while Thug B goes low, and Thug C circles for a flanking strike. 
But you read their coordination like an open book - a spinning dodge carries you 
past Thug A's fist, a low sweep trips Thug B, and a sharp elbow check stops Thug C 
cold. All three attacks fail to connect as you flow through their assault with 
practiced ease.
```

---

### **Example 4: Mixed Results (1/2 Hit)**

**Input:**
- 2 Soldiers attack Rebel
- Reactor defense: +4
- 1 attacker succeeds, 1 fails

**Output:**
```
The two soldiers coordinate their attack with military precision. Soldier A provides 
covering fire while Soldier B advances with his rifle raised. You manage to dive 
behind cover, avoiding Soldier A's shots, but Soldier B is faster than expected - 
his rifle butt catches you in the ribs as you roll, driving the air from your lungs.
```

---

## Key Features

### **1. Cohesive Group Narrative**
- ✅ Single flowing description (not 3 separate actions)
- ✅ Shows coordination and teamwork
- ✅ Weaves individual actions together naturally

### **2. Tactical Storytelling**
- ✅ Emphasizes flanking, distraction, combined assault
- ✅ Shows cause and effect (one distracts, another strikes)
- ✅ Makes coordination feel intentional and strategic

### **3. Perspective-Aware**
- ✅ Second person ("you") if reactor is UA
- ✅ Third person for all NPCs
- ✅ Maintains immersion

### **4. Outcome Clarity**
- ✅ Clearly shows which attacks hit
- ✅ Clearly shows which attacks missed
- ✅ Explains why (good defense, bad positioning, etc.)

### **5. No Mechanical Language**
- ✅ No "-2 STAMINA" or "shift_magnitude"
- ✅ Describes physical impacts (cuts, bruises, exhaustion)
- ✅ Maintains narrative immersion

---

## LLM Prompt Guidelines

The prompt instructs the LLM to:

### **Structure:**
1. **Open with coordination:** "The bandits move as one..."
2. **Individual actions:** "A circles left, B rushes forward, C blocks the exit..."
3. **Reactor response:** "You manage to block B's attack..."
4. **Outcome:** "...but A and C's strikes find their mark"

### **Tone:**
- Dynamic and tactical
- Emphasize teamwork
- Show challenge of multiple attackers
- Make hits impactful, misses close calls

### **Critical Rules:**
- DO NOT use mechanical terms
- DO describe physical/emotional impacts
- Show cause and effect
- Make coordination feel natural

---

## Integration with Main Loop

### **Current Main Loop (Simplified):**

```python
if is_grouped_turn:
    group_members = rm.get_current_group_members()
    
    # Get all group actions
    group_results = []
    for npc in group_members:
        action_data = conductor.determine_nua_proaction(
            proactor=npc,
            reactor=reactor,
            group_members=group_members
        )
        
        proactor_success = calculate_success(npc, action_data, reactor)
        
        group_results.append({
            'npc': npc,
            'action': action_data,
            'success': proactor_success
        })
    
    # Reactor defends ONCE with overwhelm penalty
    overwhelm_penalty = (len(group_members) - 1) * 2
    reactor_action = conductor.determine_nua_reaction(...)
    reactor_success = calculate_success(
        reactor, 
        reactor_action, 
        group_members[0],
        additional_stress=overwhelm_penalty
    )
    
    # Generate COHESIVE narrative for entire group
    narrative = narrator.generate_grouped_action_narrative(
        group_results=group_results,
        reactor=reactor,
        reactor_success=reactor_success,
        time_context=master_time.get_current_time_context(),
        framing_guidance=framing_guidance
    )
    
    print(f"\n{narrative}")
    
    # Apply status shifts for successful attacks
    for result in group_results:
        outcome = result['success'] - reactor_success
        if outcome > 0:
            apply_status_shift(reactor, result['action'])
```

---

## Comparison: Before vs After

### **BEFORE (Individual Narratives):**

```
→ Bandit A's action in group
  Bandit A: attempts to circle behind the Detective while his allies distract

→ Bandit B's action in group
  Bandit B: lunges forward with a feint, drawing the Detective's attention

→ Bandit C's action in group
  Bandit C: moves to block the exit while his allies engage
```

**Problems:**
- ❌ Reads like a list
- ❌ No sense of coordination
- ❌ No outcome clarity
- ❌ Doesn't feel like a group attack

---

### **AFTER (Cohesive Narrative):**

```
The three bandits coordinate their assault with deadly precision. Bandit A circles 
behind, drawing your attention with aggressive posturing, while Bandit B rushes in 
from the left with a vicious swing. You pivot to block Bandit B, but Bandit C 
exploits the opening - all three attacks land before you can recover, leaving you 
staggered and bleeding from multiple wounds.
```

**Benefits:**
- ✅ Flows naturally
- ✅ Shows coordination
- ✅ Clear outcomes
- ✅ Feels like a coordinated assault

---

## Fallback Behavior

If LLM call fails, the method provides a simple fallback:

```python
# Fallback: Simple descriptive narrative
if hit_count == group_count:
    result_desc = f"All {group_count} attacks find their mark"
elif hit_count == 0:
    result_desc = f"{reactor_name_cap} manages to block all {group_count} attacks"
else:
    result_desc = f"{hit_count} of the {group_count} attacks hit home"

group_list = ', '.join(group_names[:-1]) + f" and {group_names[-1]}"

return f"{group_list} coordinate their assault against {reactor_name}. {result_desc} despite {'your' if reactor_is_ua else 'their'} desperate defense."
```

**Example Fallback:**
```
Bandit A, Bandit B and Bandit C coordinate their assault against you. 
2 of the 3 attacks hit home despite your desperate defense.
```

---

## Benefits

### **1. Narrative Immersion**
- ✅ Reads like a story, not a combat log
- ✅ Emphasizes teamwork and tactics
- ✅ Makes grouped turns feel special

### **2. Clarity**
- ✅ Clear which attacks hit/missed
- ✅ Shows why (coordination, overwhelm, good defense)
- ✅ Maintains mechanical accuracy

### **3. Efficiency**
- ✅ One narrative instead of 3+ separate descriptions
- ✅ Faster to read and understand
- ✅ Less repetitive

### **4. Tactical Depth**
- ✅ Shows flanking, distraction, combined assault
- ✅ Makes coordination meaningful
- ✅ Rewards/punishes tactical positioning

---

## Summary

### **What Changed:**
- ✅ Added `generate_grouped_action_narrative()` method
- ✅ Generates cohesive narratives for grouped NPC turns
- ✅ Replaces individual action lists with flowing combat description
- ✅ Shows coordination, tactics, and outcomes clearly

### **How It Works:**
1. Receives all group actions and outcomes
2. Builds LLM prompt with coordination context
3. Generates 3-4 sentence cohesive narrative
4. Shows which attacks hit/missed and why

### **Benefits:**
- More immersive storytelling
- Clearer outcomes
- Emphasizes teamwork
- Feels like coordinated assault

The NarratorAgent now creates compelling group combat narratives! 🎯
