# BACKUP: Original Inquiry Design (Pre-Dynamic Order System)

## Date: November 21, 2025
## Purpose: Backup of original inquiry generation logic before implementing dynamic order system

---

## Original Design Philosophy

**Fixed Order: Always Perception → Internal Voice**

All inquiry handling used a hardcoded sequence:
1. Generate perceptual description first
2. Display and update scene
3. Generate internal voice second
4. Display internal voice

This was consistent across all inquiry types, regardless of whether the action was physical or mental.

---

## Original Code Patterns

### Pattern 1: Memory Recall (redesigned_main.py ~line 5637)

```python
# Get context for generating narrative
recent_context = narrative_context_manager.get_context_for_llm(
    lookback_events=5,
    importance_threshold="notable"
)
time_context = master_time.get_current_time_context()

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

### Pattern 2: New Inquiry Discovery (redesigned_main.py ~line 5806)

```python
# Generate factual answer (memory content with specific details)
factual_answer = narrator.generate_inquiry_factual_answer(
    user_question=user_input,
    ua_actor=actor,
    scene_description=scene_description,
    narrative_context=recent_context,
    current_time=time_context,
    availability_context=availability_context
)

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

### Pattern 3: Passive Observation (redesigned_main.py ~line 4643)

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

## Original Behavior

### For ALL inquiry types:
1. **Perceptual description generated first**
   - Describes physical manifestation of action
   - Added to scene description
   - Parsed for NPCs
   - Added to narrative context

2. **Internal voice generated second**
   - Has access to perceptual description via scene_description
   - Can reference what was just perceived
   - Displays character's thoughts

3. **Display order**
   - Perceptual description shown first
   - Internal voice shown second with separator

---

## Key Characteristics

### Strengths:
- ✅ Simple and consistent
- ✅ Easy to understand and debug
- ✅ Perceptual always has fresh scene context
- ✅ Internal voice can reference perception

### Limitations:
- ❌ Not optimal for mental actions (thinking should come before noticing)
- ❌ Fixed order doesn't adapt to action type
- ❌ "I try to remember..." shows physical act before memory content

---

## Reversion Instructions

If the new dynamic order system causes issues, revert by:

1. **Remove the import:**
   ```python
   from inquiry_generation_order import generate_inquiry_outputs
   ```

2. **Replace the single call:**
   ```python
   perceptual_description, internal_voice = generate_inquiry_outputs(...)
   ```

3. **With the original two separate calls:**
   ```python
   # Generate perceptual description first
   perceptual_description = narrator.generate_inquiry_response(...)
   
   # [Display and scene update code here]
   
   # Generate internal voice second
   internal_voice = narrator.generate_inquiry_internal_voice(...)
   ```

4. **Restore the full code blocks** from the patterns above at:
   - Line ~5637 (Memory Recall)
   - Line ~5806 (New Inquiry Discovery)
   - Line ~4643 (Passive Observation)

---

## Files to Revert

If reverting, you can safely delete these new files:
- `inquiry_generation_order.py`
- `INQUIRY_GENERATION_ORDER_SYSTEM.md`
- `INTEGRATION_COMPLETE_INQUIRY_ORDER.md`

And restore `redesigned_main.py` to use the original patterns above.

---

## Testing Checklist (Original System)

To verify the original system still works after reversion:

- [ ] "Where am I?" - Shows perception then thought
- [ ] "I try to remember my friend" - Shows perception then thought (even though mental)
- [ ] "Look around" - Shows perception then thought
- [ ] All outputs are coherent
- [ ] No `None` outputs
- [ ] Scene updates correctly
- [ ] NPCs spawn correctly

---

## Change Log

### What Changed in New System:
1. Added `inquiry_generation_order.py` module
2. Modified 3 locations in `redesigned_main.py`
3. Replaced ~70 lines of code per location with ~15 lines
4. Added dynamic order determination based on action type
5. Added context propagation from first to second generation

### What Stayed the Same:
- Display order (always perception → internal voice to user)
- Scene update logic
- NPC parsing
- Narrative context additions
- Time advancement
- Memory creation

---

## Backup Date: November 21, 2025, 8:02 AM UTC+08:00

This backup was created before integrating the dynamic inquiry generation order system.
All original code patterns are preserved above for easy reversion if needed.
