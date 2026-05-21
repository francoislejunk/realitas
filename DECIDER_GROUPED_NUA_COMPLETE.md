# DeciderAgent - Grouped NUA Integration Complete ✅

## What Was Added

The DeciderAgent now understands grouped NUA turns and generates coordinated actions.

## Changes Made

### 1. **DeciderAgent Method Signature** (`decider_agent.py` line 175)

**OLD:**
```python
def determine_nua_proaction(self, proactor: 'Actor', reactor: 'Actor', context_guidance: Dict = None):
```

**NEW:**
```python
def determine_nua_proaction(self, proactor: 'Actor', reactor: 'Actor', context_guidance: Dict = None, group_members: list = None):
    """
    Args:
        proactor: The actor taking the action
        reactor: The target of the action
        context_guidance: Context and escalation guidance
        group_members: List of NPCs acting together (if this is a grouped turn)
    """
```

---

### 2. **Grouped NUA Context Section** (`decider_agent.py` lines 406-426)

**NEW Prompt Section:**
```python
# Build grouped NUA context if applicable
grouped_context = ""
if group_members and len(group_members) > 1:
    group_names = [npc.sheet.name for npc in group_members]
    grouped_context = f"""
    
    🎯 **GROUPED NPC TURN - COORDINATED ACTION:**
    This NPC is acting as part of a coordinated group with tied initiative.
    **Group Members:** {', '.join(group_names)}
    
    **COORDINATION GUIDELINES:**
    - This NPC's action should complement the group's overall strategy
    - Consider how this action works with what other group members might do
    - Coordinated attacks (flanking, distraction, combined assault)
    - Coordinated defense (covering allies, forming defensive line)
    - Tactical positioning (surrounding target, blocking escape routes)
    - Support actions (one attacks while others provide cover/distraction)
    
    **IMPORTANT:** You are deciding THIS NPC's action only, but be aware they are part of a coordinated effort.
    The group acts together because they have the same initiative - make the action feel like part of a team strategy.
    """
```

**Inserted into main prompt at line 436:**
```python
prompt = f"""
    You are the NUA Decision Agent...
    
    **CHARACTER-FIRST DECISION MAKING:**
    🎭 **PERSONALITY DRIVES ACTION:** ...
    🎯 **GOALS MATTER:** ...
    🔄 **AVOID REPETITION:** ...
    🎲 **EMBRACE VARIETY:** ...
    {grouped_context}  # ← NEW: Grouped NUA guidance
    {escalation_context}
    ...
"""
```

---

### 3. **Main Loop Integration** (`redesigned_main.py` lines 2779-2794)

**NEW: Pass group_members to DeciderAgent:**
```python
# Get action for this group member with group context
group_action_data = conductor.determine_nua_proaction(
    proactor=group_npc,
    reactor=reactor,
    context_guidance=context_guidance,
    group_members=group_members  # ← NEW: Pass group context
)

if group_action_data and group_action_data.get('narrative_description'):
    print(f"  {group_npc.sheet.name}: {group_action_data['narrative_description']}")
```

---

## How It Works

### Example: Three Bandits with Tied Initiative

**Initiative:** Detective (15), Bandit A (12), Bandit B (12), Bandit C (12)

**Turn Queue:**
```
1. Detective (15)
2. [Bandit A, Bandit B, Bandit C] (12) ← GROUPED
```

### When Grouped Turn Activates:

**1. Main Loop Detects Group:**
```
🎯 GROUPED NPC TURN: 3 NPCs act together
  • Bandit A
  • Bandit B
  • Bandit C

Processing grouped NPC actions...
```

**2. For Each NPC in Group:**

**Bandit A's Turn:**
```
→ Bandit A's action in group

DeciderAgent receives:
- proactor: Bandit A
- reactor: Detective
- group_members: [Bandit A, Bandit B, Bandit C]

LLM sees:
🎯 GROUPED NPC TURN - COORDINATED ACTION:
This NPC is acting as part of a coordinated group with tied initiative.
Group Members: Bandit A, Bandit B, Bandit C

COORDINATION GUIDELINES:
- This NPC's action should complement the group's overall strategy
- Consider coordinated attacks (flanking, distraction, combined assault)
- Tactical positioning (surrounding target, blocking escape routes)

LLM generates:
  Bandit A: attempts to circle behind the Detective while his allies distract
```

**Bandit B's Turn:**
```
→ Bandit B's action in group

DeciderAgent receives:
- proactor: Bandit B
- reactor: Detective
- group_members: [Bandit A, Bandit B, Bandit C]

LLM sees same coordination context

LLM generates:
  Bandit B: lunges forward with a feint, drawing the Detective's attention
```

**Bandit C's Turn:**
```
→ Bandit C's action in group

DeciderAgent receives:
- proactor: Bandit C
- reactor: Detective
- group_members: [Bandit A, Bandit B, Bandit C]

LLM sees same coordination context

LLM generates:
  Bandit C: moves to block the exit while his allies engage
```

---

## Coordination Examples

### Coordinated Attack (Flanking)
```
🎯 GROUPED NPC TURN: 2 NPCs act together
  • Thug A
  • Thug B

→ Thug A's action in group
  Thug A: attempts to grab the Detective's attention with aggressive posturing

→ Thug B's action in group
  Thug B: circles around to attack from behind while his partner distracts
```

### Coordinated Defense
```
🎯 GROUPED NPC TURN: 3 NPCs act together
  • Guard A
  • Guard B
  • Guard C

→ Guard A's action in group
  Guard A: takes a defensive stance in front of the entrance

→ Guard B's action in group
  Guard B: positions to Guard A's left, forming a defensive line

→ Guard C's action in group
  Guard C: covers the right flank, completing the defensive formation
```

### Support Actions
```
🎯 GROUPED NPC TURN: 2 NPCs act together
  • Soldier A
  • Medic B

→ Soldier A's action in group
  Soldier A: provides covering fire while his ally tends to the wounded

→ Medic B's action in group
  Medic B: rushes to the wounded ally under Soldier A's covering fire
```

---

## LLM Prompt Context

When `group_members` is provided, the LLM receives:

```
🎯 **GROUPED NPC TURN - COORDINATED ACTION:**
This NPC is acting as part of a coordinated group with tied initiative.
**Group Members:** Bandit A, Bandit B, Bandit C

**COORDINATION GUIDELINES:**
- This NPC's action should complement the group's overall strategy
- Consider how this action works with what other group members might do
- Coordinated attacks (flanking, distraction, combined assault)
- Coordinated defense (covering allies, forming defensive line)
- Tactical positioning (surrounding target, blocking escape routes)
- Support actions (one attacks while others provide cover/distraction)

**IMPORTANT:** You are deciding THIS NPC's action only, but be aware they are part of a coordinated effort.
The group acts together because they have the same initiative - make the action feel like part of a team strategy.
```

This guidance appears **before** the escalation context and character analysis, ensuring the LLM prioritizes coordination.

---

## Benefits

### ✅ **Coordinated NPC Tactics**
- NPCs with tied initiative naturally work together
- Flanking, distraction, and combined assaults emerge
- Defensive formations and support actions

### ✅ **Narrative Coherence**
- Actions feel like part of a team strategy
- No arbitrary "who goes first" among allies
- Natural gang/group behavior

### ✅ **Strategic Depth**
- Players face coordinated threats
- Grouped NPCs can execute complex tactics
- More challenging and realistic combat

### ✅ **Character Authenticity**
- Each NPC still acts according to personality
- Coordination doesn't override character traits
- Group strategy emerges from individual actions

---

## Integration Status

### ✅ **Complete:**
- DeciderAgent accepts `group_members` parameter
- Grouped NUA context added to LLM prompt
- Main loop passes group context to DeciderAgent
- Actions generated with coordination awareness

### ⚠️ **Current Limitations:**
- Actions processed sequentially (not truly simultaneous)
- No combined narrative for group actions yet
- Each NPC's action displayed separately

### 🔮 **Future Enhancements:**
1. **Combined Narrative:** Generate single cohesive description for group
2. **Simultaneous Resolution:** Resolve all group actions at once
3. **Group Strategy:** Pre-determine overall group strategy before individual actions
4. **Dynamic Roles:** Assign roles (attacker, flanker, support) within group

---

## Testing

### Test Case: Two Guards Coordinate

**Setup:**
```python
# Initiative: Detective (15), Guard A (13), Guard B (13)
# Guards tie, form group
```

**Expected Output:**
```
🎯 GROUPED NPC TURN: 2 NPCs act together
  • Guard A
  • Guard B

Processing grouped NPC actions...

→ Guard A's action in group
  Guard A: attempts to grab the Detective's weapon arm

→ Guard B's action in group
  Guard B: moves to restrain the Detective from behind while Guard A distracts
```

**LLM Context for Guard B:**
```
🎯 GROUPED NPC TURN - COORDINATED ACTION:
Group Members: Guard A, Guard B

COORDINATION GUIDELINES:
- This NPC's action should complement the group's overall strategy
- Consider coordinated attacks (flanking, distraction, combined assault)
```

**Result:** Guard B's action naturally complements Guard A's, creating coordinated restraint attempt.

---

## Summary

### **What Changed:**
- ✅ DeciderAgent accepts `group_members` parameter
- ✅ LLM receives grouped NUA coordination context
- ✅ Main loop passes group info to DeciderAgent
- ✅ NPCs generate coordinated actions when grouped

### **How It Works:**
1. Main loop detects grouped turn
2. For each NPC in group:
   - Call DeciderAgent with `group_members` list
   - LLM sees coordination guidelines
   - LLM generates action that complements group strategy
3. All actions feel coordinated and tactical

### **Benefits:**
- More realistic NPC coordination
- Strategic depth from group tactics
- Natural emergence of flanking, support, defense
- Character authenticity maintained

The DeciderAgent now generates intelligent, coordinated actions for grouped NPCs! 🎯
