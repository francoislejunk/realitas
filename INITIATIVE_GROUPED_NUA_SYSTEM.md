# Initiative System - Grouped NUA Ties

## Problem Identified

**OLD SYSTEM:**
- ALL actors (UA and NUA) used tie-breakers for initiative
- Tie-breakers: Swiftness → Random
- NUAs with tied initiative acted one-by-one in arbitrary order
- Created artificial separation between NPCs who should coordinate

**Issues:**
- ❌ NPCs with same initiative acted separately, not together
- ❌ Tie-breaker order felt arbitrary for NPCs
- ❌ Didn't reflect coordinated NPC behavior
- ❌ Made combat feel more "gamey" than natural

## NEW SYSTEM: Grouped NUA Ties

### Core Principle

**UA gets tie-breakers, NUAs act together when tied**

### Rules

#### **1. UA (User Actor) - Uses Tie-Breakers**
When UA ties with another actor on initiative:
1. Compare **Swiftness** S-Factor
2. If still tied, use **Random** roll
3. UA acts individually in determined order

#### **2. NUA (Non-User Actors) - NO Tie-Breakers**
When NUAs tie with each other on initiative:
1. **NO Swiftness comparison**
2. **NO Random roll**
3. **All tied NUAs act together** in the same turn
4. They collectively decide their actions
5. Group persists until new initiative is rolled

## Implementation

### File: `enhanced_round_manager.py`

#### **1. NUA Sorting (Lines 167-173)**

**OLD:**
```python
def nua_sort_key(actor):
    initiative = actor_initiatives[actor.sheet.name]['initiative_score']
    swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
    return (-initiative, -swiftness, random.random())  # Tie-breakers
```

**NEW:**
```python
def nua_sort_key(actor):
    initiative = actor_initiatives[actor.sheet.name]['initiative_score']
    return -initiative  # Only initiative, no tie-breakers
```

**Result:** NUAs with same initiative stay together

---

#### **2. Final Queue Sorting (Lines 188-204)**

**OLD:**
```python
def queue_sort_key(actor):
    initiative = actor_initiatives[actor.sheet.name]['initiative_score']
    swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
    return (-initiative, -swiftness, random.random())  # All actors get tie-breakers
```

**NEW:**
```python
def queue_sort_key(actor):
    initiative = actor_initiatives[actor.sheet.name]['initiative_score']
    is_ua = getattr(actor, 'is_user_actor', False)
    
    if is_ua:
        # UA gets tie-breakers: initiative, then swiftness, then random
        swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
        return (-initiative, -swiftness, random.random())
    else:
        # NUA only sorts by initiative (no tie-breakers)
        # Use actor name as stable secondary sort
        return (-initiative, actor.sheet.name)
```

**Result:** UA uses tie-breakers, NUAs don't

---

#### **3. Turn Queue Building (Lines 221-277)**

**NEW: Grouped Entry System**

```python
# Group actors by initiative score
initiative_groups = {}
for actor in queue_candidates:
    init_score = actor_initiatives[actor.sheet.name]['initiative_score']
    if init_score not in initiative_groups:
        initiative_groups[init_score] = []
    initiative_groups[init_score].append(actor)

# Build turn queue with grouped entries
for init_score in sorted(initiative_groups.keys(), reverse=True):
    actors_at_this_init = initiative_groups[init_score]
    
    nua_actors_tied = [a for a in actors_at_this_init if not is_user_actor(a)]
    ua_actors_tied = [a for a in actors_at_this_init if is_user_actor(a)]
    
    # UA actors added individually
    for ua in ua_actors_tied:
        turn_queue.append({
            'actor': ua,
            'is_grouped': False,
            'group_members': None
        })
    
    # NUA actors grouped if tied
    if len(nua_actors_tied) > 1:
        # Multiple NUAs tied - create GROUP entry
        turn_queue.append({
            'actor_name': f"Group of {len(nua_actors_tied)} NPCs",
            'actor': nua_actors_tied[0],  # Primary for compatibility
            'is_grouped': True,
            'group_members': nua_actors_tied  # All tied NUAs
        })
    elif len(nua_actors_tied) == 1:
        # Single NUA - add individually
        turn_queue.append({
            'actor': nua_actors_tied[0],
            'is_grouped': False,
            'group_members': None
        })
```

**Result:** Turn queue entries can now represent groups of NPCs

---

#### **4. Tie-Breaker Detection (Lines 312-362)**

**NEW: Distinguishes UA vs NUA ties**

```python
def _detect_queue_tie_breakers(self, queue_candidates, actor_initiatives):
    tie_breakers = []
    nua_groups = []
    
    for i in range(len(queue_candidates) - 1):
        current_actor = queue_candidates[i]
        next_actor = queue_candidates[i + 1]
        
        if current_initiative == next_initiative:
            current_is_ua = is_user_actor(current_actor)
            next_is_ua = is_user_actor(next_actor)
            
            if current_is_ua or next_is_ua:
                # UA involved - use tie-breaker
                tie_breakers.append({
                    'resolution_method': 'swiftness' or 'random',
                    'involves_ua': True
                })
            else:
                # NUA vs NUA - grouped action
                nua_groups.append({
                    'actors': [current, next],
                    'resolution': 'grouped_action',
                    'note': 'These NPCs act simultaneously'
                })
    
    return {
        'tie_breakers': tie_breakers,
        'nua_groups': nua_groups
    }
```

**Result:** System tracks which ties use breakers vs grouping

---

## Examples

### Scenario 1: Two Bandits Tie

**Initiative Rolls:**
- UA (Detective): Initiative 15
- Bandit A: Initiative 12
- Bandit B: Initiative 12
- Bandit C: Initiative 10

**OLD SYSTEM:**
```
Turn Order:
1. Detective (15)
2. Bandit A (12, Swiftness 3) ← Tie-breaker
3. Bandit B (12, Swiftness 2) ← Tie-breaker
4. Bandit C (10)

Bandit A acts → Bandit B acts → Bandit C acts
(One by one, separate turns)
```

**NEW SYSTEM:**
```
Turn Order:
1. Detective (15)
2. Bandit A & B (12) ← GROUPED
3. Bandit C (10)

Bandit A & B act TOGETHER in same turn:
- Both decide actions simultaneously
- Coordinated attack/defense
- Natural NPC cooperation
```

---

### Scenario 2: UA Ties with NUA

**Initiative Rolls:**
- UA (Detective): Initiative 14
- Guard A: Initiative 14
- Guard B: Initiative 11

**OLD SYSTEM:**
```
Turn Order:
1. Detective (14, Swiftness 4) ← Tie-breaker
2. Guard A (14, Swiftness 3) ← Tie-breaker
3. Guard B (11)
```

**NEW SYSTEM:**
```
Turn Order:
1. Detective (14, Swiftness 4) ← UA uses tie-breaker
2. Guard A (14, Swiftness 3) ← UA won tie-breaker
3. Guard B (11)

Detective acts first due to higher Swiftness
(UA still uses tie-breakers normally)
```

---

### Scenario 3: Three NPCs Tie

**Initiative Rolls:**
- UA (Detective): Initiative 16
- Thug A: Initiative 13
- Thug B: Initiative 13
- Thug C: Initiative 13

**OLD SYSTEM:**
```
Turn Order:
1. Detective (16)
2. Thug A (13, Swiftness 3, Random 0.8) ← Tie-breakers
3. Thug B (13, Swiftness 3, Random 0.5) ← Tie-breakers
4. Thug C (13, Swiftness 3, Random 0.2) ← Tie-breakers

Each thug acts separately in random order
```

**NEW SYSTEM:**
```
Turn Order:
1. Detective (16)
2. Thugs A, B, & C (13) ← ALL GROUPED

All three thugs act TOGETHER:
- Coordinate their attack
- Surround the detective
- Natural gang behavior
```

---

### Scenario 4: Mixed Ties

**Initiative Rolls:**
- UA (Detective): Initiative 15
- Ally (Partner): Initiative 15
- Enemy A: Initiative 12
- Enemy B: Initiative 12

**NEW SYSTEM:**
```
Turn Order:
1. Detective (15, Swiftness 4) ← UA tie-breaker
2. Partner (15, Swiftness 3) ← Lost tie-breaker to UA
3. Enemy A & B (12) ← GROUPED

- Detective vs Partner: Tie-breaker used (UA involved)
- Enemy A vs Enemy B: Grouped (both NUAs)
```

---

## Turn Queue Structure

### Individual Entry
```python
{
    'position': 1,
    'actor_name': 'Detective Sarah',
    'actor': <Actor object>,
    'initiative_score': 15,
    'is_user_actor': True,
    'is_grouped': False,
    'group_members': None
}
```

### Grouped Entry
```python
{
    'position': 2,
    'actor_name': 'Group of 3 NPCs',
    'actor': <Actor object>,  # Primary actor for compatibility
    'initiative_score': 12,
    'is_user_actor': False,
    'is_grouped': True,
    'group_members': [<Bandit A>, <Bandit B>, <Bandit C>]
}
```

---

## How Grouped Actions Work

### When It's a Grouped NUA Turn:

**1. System Detects Group**
```python
if turn_entry['is_grouped']:
    group_members = turn_entry['group_members']
    # All members act together
```

**2. Collective Decision Making**
```
Instead of:
- Bandit A decides action
- Execute Bandit A action
- Bandit B decides action
- Execute Bandit B action

Do:
- All bandits decide actions together
- Execute all actions simultaneously
- Resolve as coordinated effort
```

**3. Narrative Presentation**
```
OLD: "Bandit A swings at you. Bandit B flanks left."
NEW: "The bandits coordinate their attack - one swings while 
     another flanks left, working together."
```

---

## Benefits

### **1. More Realistic NPC Behavior**
✅ NPCs with same initiative naturally coordinate
✅ Gang/group tactics feel organic
✅ No arbitrary "who goes first" among allies

### **2. Faster Combat Resolution**
✅ Multiple NPCs act in one turn
✅ Less back-and-forth for tied NPCs
✅ Streamlined group encounters

### **3. Strategic Depth**
✅ Grouped NPCs can coordinate attacks
✅ Flanking and teamwork emerge naturally
✅ Player faces coordinated threats

### **4. Less "Gamey" Feel**
✅ No random tie-breakers for NPCs
✅ Natural group behavior
✅ Feels more like fiction, less like mechanics

### **5. UA Maintains Agency**
✅ UA still uses tie-breakers (player advantage)
✅ UA can break ties with Swiftness investment
✅ Player choices matter for initiative

---

## Edge Cases

### **What if 4+ NPCs tie?**
All act together in the same turn. No limit on group size.

### **What if UA ties with a grouped NPC?**
UA uses tie-breaker against the group's initiative score.

### **What if grouped NPCs have different actions?**
Each NPC in the group can choose their own action, but they all act simultaneously in the same turn.

### **What if a grouped NPC dies mid-turn?**
Group continues with remaining members. Dead NPC's action is skipped.

### **Does grouping persist across rounds?**
No. Initiative is re-rolled each round, so groups may change.

---

## Integration with Main Loop

### Detection in Main Loop

```python
# In redesigned_main.py or wherever turns are processed

current_turn = turn_queue[turn_position]

if current_turn['is_grouped']:
    # Grouped NUA turn
    group_members = current_turn['group_members']
    
    print(f"\n🎯 GROUP TURN: {len(group_members)} NPCs act together")
    
    for npc in group_members:
        # Get each NPC's intended action
        # Could use DeciderAgent for each
        pass
    
    # Execute all actions together
    # Resolve as coordinated effort
    
else:
    # Individual actor turn (UA or single NUA)
    actor = current_turn['actor']
    # Normal turn processing
```

---

## Summary

### **What Changed:**

**OLD:**
- All actors use tie-breakers (swiftness → random)
- NPCs act one-by-one even when tied
- Arbitrary order for tied NPCs

**NEW:**
- ✅ **UA uses tie-breakers** (swiftness → random)
- ✅ **NUAs with tied initiative act together** (no tie-breakers)
- ✅ **Grouped NUA entries** in turn queue
- ✅ **Coordinated NPC behavior** emerges naturally
- ✅ **Persists until new initiative roll**

### **Benefits:**
- More realistic NPC coordination
- Faster combat with grouped actions
- Less "gamey" arbitrary ordering
- Strategic depth from NPC teamwork
- UA maintains tie-breaker advantage

The system creates more natural, coordinated NPC behavior while preserving player agency through UA tie-breakers!
