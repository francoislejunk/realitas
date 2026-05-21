# Quick Reversion Guide: Return to Original Inquiry System

## If the new dynamic order system causes issues, follow these steps:

---

## Step 1: Identify the Problem

Common issues that might require reversion:
- ❌ Outputs are incoherent or contradictory
- ❌ `None` outputs appearing
- ❌ Import errors with `inquiry_generation_order`
- ❌ Generation order feels wrong
- ❌ Context propagation causing issues

---

## Step 2: Locate the 3 Modified Sections

The new system was integrated at these 3 locations in `redesigned_main.py`:

### Location 1: Memory Recall (~line 5637)
Look for:
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
```

### Location 2: New Inquiry Discovery (~line 5806)
Look for:
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
```

### Location 3: Passive Observation (~line 4643)
Look for:
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
```

---

## Step 3: Revert Each Location

### For Location 1 (Memory Recall):

**REMOVE:**
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
    narrator=narrator,
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    time_context=time_context,
    availability_context={'availability': IntentAvailability.EXIST, 'reasoning': 'Memory recalled'},
    factual_knowledge=memory.description,
    fallible_subtype='inquiry'
)
```

**REPLACE WITH:**
```python
# Generate perceptual description (physical act of remembering)
perceptual_description = narrator.generate_inquiry_response(
    user_question=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    availability_context={'availability': IntentAvailability.EXIST, 'reasoning': 'Memory recalled'}
)

# Display perceptual description
print(f"{Color.NARRATIVE}{perceptual_description}{Color.RESET}\n")

# Update scene description with new perceptual information
scene_description = f"{scene_description}\n\n{perceptual_description}"
try:
    conductor.scene_description = scene_description
except Exception:
    pass

# Persist to authoritative tracker
try:
    tracker.set_current_scene(scene_description)
except Exception:
    pass

# CRITICAL: Add perceptual description to narrative context
try:
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.EXPLORATION,
        narrative_text=perceptual_description,
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="observational",
        scene_context=f"Memory recall: {user_input[:50]}"
    )
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}[CONTEXT] Failed to add perceptual description to narrative context: {e}{Color.RESET}")

# Parse perceptual description for NPCs
try:
    from scene_npc_parser import auto_spawn_scene_npcs
    auto_spawn_scene_npcs(
        scene_description=perceptual_description,
        creator_agent=scene_creator,
        available_npcs=available_npcs,
        continuity_validator=continuity_validator,
        auto_memory_creator=auto_memory_creator,
        actor_name=actor.sheet.name,
        scene_id=scene_id
    )
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")

# Generate internal voice revealing the memory content
internal_voice = narrator.generate_inquiry_internal_voice(
    ua_actor=actor,
    question=user_input,
    scene_description=scene_description,
    narrative_context=recent_context,
    factual_knowledge=memory.description,  # Pass the full memory content
    time_context=time_context,
    availability_context={'availability': IntentAvailability.EXIST, 'reasoning': 'Memory recalled'}
)
```

**NOTE:** Keep the display code that comes after (it wasn't changed).

---

### For Location 2 (New Inquiry Discovery):

**REMOVE:**
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
    narrator=narrator,
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    time_context=time_context,
    availability_context=availability_context,
    factual_knowledge=factual_answer,
    fallible_subtype='inquiry'
)
```

**REPLACE WITH:**
```python
# Generate perceptual description (physical act of thinking)
perceptual_description = narrator.generate_inquiry_response(
    user_question=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    availability_context=availability_context
)

# Display perceptual description
print(f"{Color.NARRATIVE}{perceptual_description}{Color.RESET}\n")

# Update scene description with new perceptual information
scene_description = f"{scene_description}\n\n{perceptual_description}"
try:
    conductor.scene_description = scene_description
except Exception:
    pass

# Persist to authoritative tracker
try:
    tracker.set_current_scene(scene_description)
except Exception:
    pass

# CRITICAL: Add perceptual description to narrative context
try:
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.EXPLORATION,
        narrative_text=perceptual_description,
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.NOTABLE,
        emotional_tone="observational",
        scene_context=f"Failed inquiry: {user_input[:50]}"
    )
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}[CONTEXT] Failed to add perceptual description to narrative context: {e}{Color.RESET}")

# Parse perceptual description for NPCs
try:
    from scene_npc_parser import auto_spawn_scene_npcs
    auto_spawn_scene_npcs(
        scene_description=perceptual_description,
        creator_agent=scene_creator,
        available_npcs=available_npcs,
        continuity_validator=continuity_validator,
        auto_memory_creator=auto_memory_creator,
        actor_name=actor.sheet.name,
        scene_id=scene_id
    )
except Exception as e:
    if not SUPPRESS_DEBUG:
        print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")

# NOTE: Do NOT run NPC parser on factual_answer - it's memory content, not current scene!
# NPCs mentioned in memories are not physically present unless they appear in scene_description

# Generate and display internal voice reaction
internal_voice = narrator.generate_inquiry_internal_voice(
    ua_actor=actor,
    question=user_input,
    scene_description=scene_description,
    narrative_context=recent_context,
    factual_knowledge=factual_answer,  # Pass the factual answer with specific details
    time_context=time_context,
    availability_context=availability_context,
    perceptual_description=perceptual_description
)
```

---

### For Location 3 (Passive Observation):

**REMOVE:**
```python
# Use dynamic generation order system
from inquiry_generation_order import generate_inquiry_outputs

perceptual_description, internal_voice = generate_inquiry_outputs(
    narrator=narrator,
    user_input=user_input,
    actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    time_context=time_context,
    availability_context={'availability': 'exist', 'reasoning': 'Passive observation'},
    factual_knowledge="Observed surroundings",
    fallible_subtype='physical'  # Observation is physical action
)
```

**REPLACE WITH:**
```python
# PHASE 1: Generate perceptual description (what you physically do)
perceptual_description = narrator.generate_inquiry_response(
    user_question=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    availability_context={'availability': 'exist', 'reasoning': 'Passive observation'}
)

# Display perceptual description
print(f"\n{Color.NARRATIVE}{perceptual_description}{Color.RESET}\n")

# Update scene description with new perceptual information
scene_description = f"{scene_description}\n\n{perceptual_description}"
try:
    conductor.scene_description = scene_description
except Exception:
    pass

# Persist to authoritative tracker
try:
    tracker.set_current_scene(scene_description)
except Exception:
    pass

# PHASE 2: Success (automatic for passive actions)
print(f"{Color.SUCCESS}✅ AUTOMATIC SUCCESS{Color.RESET}")
print(f"{Color.SUCCESS}Result: Observation complete{Color.RESET}\n")

# PHASE 3: Generate internal voice (mental reaction)
internal_voice = narrator.generate_inquiry_internal_voice(
    ua_actor=actor,
    question=user_input,
    scene_description=scene_description,
    narrative_context=recent_context,
    factual_knowledge="Observed surroundings",
    time_context=time_context,
    availability_context={'availability': 'exist', 'reasoning': 'Passive observation'},
    perceptual_description=perceptual_description
)
```

---

## Step 4: Delete New Files (Optional)

If you want to fully clean up, you can delete:
- `inquiry_generation_order.py`
- `INQUIRY_GENERATION_ORDER_SYSTEM.md`
- `INTEGRATION_COMPLETE_INQUIRY_ORDER.md`

**Keep these for reference:**
- `BACKUP_ORIGINAL_INQUIRY_DESIGN.md` (this backup)
- `REVERT_TO_ORIGINAL_INQUIRY.md` (this guide)

---

## Step 5: Test After Reversion

Run these tests to verify the original system is working:

1. Start a new game
2. Test: "Where am I?" - Should show perception then thought
3. Test: "I try to remember my friend" - Should show perception then thought
4. Test: "Look around" - Should show perception then thought
5. Verify no errors in console
6. Verify outputs are coherent

---

## Quick Checklist

- [ ] Located all 3 modified sections
- [ ] Reverted Location 1 (Memory Recall)
- [ ] Reverted Location 2 (New Inquiry Discovery)
- [ ] Reverted Location 3 (Passive Observation)
- [ ] Tested basic inquiries
- [ ] Verified no errors
- [ ] (Optional) Deleted new files

---

## Need Help?

If you encounter issues during reversion:
1. Check `BACKUP_ORIGINAL_INQUIRY_DESIGN.md` for complete original code
2. Search for "Use dynamic generation order system" to find all locations
3. Make sure to restore ALL the code between generation calls (display, scene update, NPC parsing)
4. The display code at the end (showing internal voice) should stay the same

---

## Reversion Completed?

Once reverted, the system will:
- ✅ Always generate perception first
- ✅ Always generate internal voice second
- ✅ Work exactly as it did before
- ✅ Have no dependency on `inquiry_generation_order.py`

The original system was stable and working - this reversion will restore that stability.
