# Fake Signal Fixes - Integration Guide

## Overview
This document explains how to integrate all the fake signal prevention systems into the UTAS simulation.

---

## ✅ CRITICAL FIXES (Completed - Needs Integration)

### 1. **Witness Reaction System** (`witness_reaction_system.py`)
**Prevents:** NPCs ignoring violence/murder

**Integration Points:**
```python
# In exchange_system.py after exchange resolution:
from witness_reaction_system import witness_system

# After determining winner and applying status shifts:
if event_is_violent:  # violence, murder, theft
    witnesses = [npc for npc in available_npcs if npc != proactor and npc != reactor]
    reactions = witness_system.process_witness_reactions(
        event_type="violence",  # or "murder", "theft", "threat"
        perpetrator=proactor,
        victim=reactor,
        witnesses=witnesses,
        severity=abs(final_shift_amount),  # Use shift magnitude as severity
        scene_description=scene_description
    )
    
    # Apply sympathy shifts from reactions
    for reaction in reactions:
        witness = next(w for w in witnesses if w.sheet.name == reaction['witness'])
        witness.sheet.update_sympathy(proactor.sheet.name, reaction['sympathy_shifts']['perpetrator'])
        if reactor:
            witness.sheet.update_sympathy(reactor.sheet.name, reaction['sympathy_shifts']['victim'])
    
    # Display reactions
    witness_system.display_witness_reactions(reactions)
    
    # Handle behavioral changes
    for reaction in reactions:
        if reaction['behavioral_change'] == 'leave_scene':
            witness = next(w for w in witnesses if w.sheet.name == reaction['witness'])
            available_npcs.remove(witness)
            continuity_validator.mark_npc_departed(witness.sheet.name)
        elif reaction['behavioral_change'] == 'join_combat_against_perpetrator':
            # Add witness to encounter against proactor
            pass
```

---

### 2. **Scene Continuity Validator** (`scene_continuity_validator.py`)
**Prevents:** Location/time/NPC inconsistencies

**Integration Points:**
```python
# In MAIN/redesigned_main.py at simulation start:
from scene_continuity_validator import continuity_validator

# After scene generation:
continuity_validator.update_from_scene(scene_description, time_context)

# Add all NPCs to tracking:
for npc in available_npcs:
    continuity_validator.add_npc(npc.sheet.name)

# Before generating any narrative:
is_valid, issues = continuity_validator.validate_narrative(
    narrative=generated_narrative,
    action=user_input,
    actor_name=actor.sheet.name
)

if not is_valid:
    continuity_validator.display_continuity_warnings(issues)
    # Optionally: regenerate narrative with continuity context

# Add continuity context to LLM prompts:
continuity_context = continuity_validator.get_continuity_context()
# Include in narrator/interpreter prompts

# After NPCs leave/die:
continuity_validator.mark_npc_departed(npc_name)
continuity_validator.mark_npc_dead(npc_name)
continuity_validator.mark_npc_unconscious(npc_name)
```

---

### 3. **Ally Coordination System** (`ally_coordination_system.py`)
**Prevents:** NPCs not helping wounded allies

**Integration Points:**
```python
# In agents/decider_agent.py before NUA action decision:
from ally_coordination_system import ally_coordinator

# Register ally groups at encounter start:
if encounter_has_multiple_npcs:
    ally_coordinator.register_ally_group(
        group_name="guards",
        members=[guard1, guard2, guard3]
    )

# Before NUA decides action:
assistance_needed = ally_coordinator.check_ally_assistance_needed(
    actor=nua,
    all_actors=all_actors_in_scene,
    current_situation=scene_description
)

if assistance_needed:
    # Override NUA's normal action with assistance action
    ally_coordinator.display_coordination_action(assistance_needed)
    # Use assistance action instead of normal decision
    return assistance_needed

# Check group morale for flee decisions:
if ally_coordinator.should_group_flee("guards", threat_level=4):
    # All guards flee together
    pass
```

---

### 4. **Actor State Filter** (`actor_state_filter.py`)
**Prevents:** Dead/unconscious actors taking actions

**Integration Points:**
```python
# In MAIN/redesigned_main.py and enhanced_round_manager.py:
from actor_state_filter import actor_state_filter

# At start of each turn:
state = actor_state_filter.check_actor_state(current_actor)
if state == 'dead':
    print(f"Skipping {current_actor.sheet.name}'s turn (dead)")
    continue
elif state == 'unconscious':
    print(f"Skipping {current_actor.sheet.name}'s turn (unconscious)")
    continue

# Filter turn queue:
filtered_queue = actor_state_filter.filter_turn_queue(turn_queue)

# After status changes (in exchange_system.py):
actor_state_filter.check_for_death_triggers(actor)

# Before allowing action:
if not actor_state_filter.can_actor_take_action(actor):
    actor_state_filter.display_actor_state_warning(actor, attempted_action)
    continue

# Add state context to narratives:
state_context = actor_state_filter.get_state_narrative_context(actor)
# Include in narrator prompts
```

---

## 🟠 HIGH PRIORITY FIXES (In Progress)

### 5. **Dialogue Context System** (To be created)
**Prevents:** Conversation context loss

**Plan:**
- Track conversation history per NPC pair
- Maintain topic continuity
- Reference previous statements
- Track promises/threats made

### 6. **Sympathy Behavior Modifier** (To be created)
**Prevents:** Sympathy not affecting NPC decisions

**Plan:**
- Inject sympathy context into DeciderAgent prompts
- Modify action selection based on sympathy
- Enemies refuse help, friends offer assistance
- Sympathy affects dialogue tone

### 7. **Inventory Transfer System** (Already created in `enhanced_monetary_system.py`)
**Status:** ✅ Complete
- Items automatically added on purchase
- Items removed on sale
- Items transferred on theft

### 8. **Time/Lighting Consistency** (Partially in `scene_continuity_validator.py`)
**Status:** ✅ Partially complete
- Continuity validator checks time/lighting
- Need to add automatic scene updates when time advances

---

## 🟡 MEDIUM PRIORITY FIXES (Planned)

### 9. **Tactical Awareness System**
- NPCs take cover when shot at
- NPCs flee when outmatched
- NPCs use terrain advantages
- NPCs call for backup

### 10. **Economic Awareness** (Partially in `enhanced_monetary_system.py`)
**Status:** ✅ Partially complete
- Contextual pricing implemented
- Need NPC reactions to payment amounts

### 11. **Mode Transition Improvements**
- Better SPARK detection
- Smoother PRESSURE escalation
- Proper OUTCOME closure

### 12. **Memory System Enhancement**
- NPC remembers past interactions
- References previous events
- Tracks relationship history

---

## 🟢 LOW PRIORITY FIXES (Planned)

### 13. **Narrative Perspective Consistency**
**Status:** ✅ Already fixed (Memory shows this was completed)
- All narratives use third-person with actor names

### 14. **Tone Consistency**
- Match narrative tone to scene tension
- Serious scenes stay serious
- Horror scenes maintain atmosphere

### 15. **Dynamic Actor Justification**
- NPCs appear with narrative reason
- Personalities match scene
- Logical presence explanation

---

## Implementation Priority

### Phase 1: CRITICAL (Immediate)
1. Integrate WitnessReactionSystem into exchange_system.py
2. Integrate ActorStateFilter into main loop and round manager
3. Integrate SceneContinuityValidator into narrative generation
4. Integrate AllyCoordinationSystem into decider_agent.py

### Phase 2: HIGH (Next)
5. Create DialogueContextSystem
6. Create SympathyBehaviorModifier
7. Complete Time/Lighting auto-updates

### Phase 3: MEDIUM (After Phase 2)
8. Create TacticalAwarenessSystem
9. Enhance EconomicAwareness
10. Improve ModeTransitions
11. Enhance MemorySystem

### Phase 4: LOW (Polish)
12. Tone consistency checks
13. Dynamic actor justification

---

## Testing Checklist

After integration, test these scenarios:

### CRITICAL Tests:
- [ ] NPC witnesses murder and reacts (screams, flees, intervenes)
- [ ] Dead actor removed from turn queue
- [ ] Unconscious actor skips turns
- [ ] Indoor scene doesn't mention outdoor elements
- [ ] NPC helps wounded ally in combat
- [ ] Departed NPC doesn't appear in narrative

### HIGH Tests:
- [ ] Extended conversation maintains context
- [ ] Enemy NPC refuses to help
- [ ] Friend NPC offers assistance
- [ ] Purchased item appears in inventory
- [ ] Time advances and lighting updates

### MEDIUM Tests:
- [ ] NPC flees when outmatched
- [ ] NPC takes cover when shot at
- [ ] Friendly vendor gives discount
- [ ] SPARK mode triggers on tension
- [ ] NPC remembers previous threat

---

## Notes

- All systems are designed to work independently
- Integration can be done incrementally
- Each system has global instance for easy access
- Display methods included for debugging
- Systems track their own state for consistency

