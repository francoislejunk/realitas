# 🚨 CRITICAL MISSING CONTEXT INTEGRATIONS

## Status: URGENT - These are breaking immersion RIGHT NOW

Based on comprehensive audit of all context systems and their integration points.

---

## ❌ **1. Concrete Details NOT Fed to NarratorAgent**

### Problem:
- ConcreteDetailTracker exists and tracks details
- `get_concrete_details_for_actor()` method exists
- **BUT:** NarratorAgent prompts DON'T include concrete details
- **Result:** Car changes from Lamborghini to Toyota, clothing inconsistent

### Where to Fix:
**File:** `agents/narrator_agent.py`

**Methods Missing Concrete Details:**
1. `generate_step6_turn_narrative()` - Line ~900
2. `generate_exploration_action_result_narrative()` - Line ~1400
3. `generate_location_transition()` - Line ~1600
4. `generate_scene_with_narrative_loop()` - Line ~1700

### How to Fix:
```python
# In each method, BEFORE calling LLM:

# Get concrete details for all active actors
concrete_context = ""
if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
    try:
        # Get details for UA
        ua_details = self.narrative_context_manager.get_concrete_details_for_actor(
            actor.sheet.name,
            scene_id="current"
        )
        
        # Get details for any NUAs present
        for nua in present_nuas:
            nua_details = self.narrative_context_manager.get_concrete_details_for_actor(
                nua.sheet.name,
                scene_id="current"
            )
            if nua_details:
                concrete_context += f"\n{nua_details}\n"
        
        if ua_details:
            concrete_context = f"\n{ua_details}\n{concrete_context}"
    except Exception as e:
        pass

# Add to prompt FIRST (before any other context):
prompt = f"""
{concrete_context}

**CRITICAL:** Maintain consistency with all established concrete details above.
Do not introduce contradictory details.

{rest_of_prompt}
"""
```

---

## ❌ **2. Deceased NUAs NOT Checked Before Scene Population**

### Problem:
- `tracker.record_nua_death()` saves deaths
- `tracker.is_nua_alive()` checks if alive
- **BUT:** Scene population doesn't check before creating NUAs
- **Result:** Dead NUAs can resurrect

### Where to Fix:
**File:** `scene_population_system.py`

**Method:** `populate_scene()` - Line ~140

### How to Fix:
```python
def populate_scene(self, scene_description: str, time_of_day: str = "day", 
                   tracker=None) -> List[NonUserActor]:
    """Generate all potential NUAs for a scene BEFORE narration"""
    
    # ... existing population code ...
    
    # CRITICAL: Filter out deceased NUAs
    if tracker:
        generated_nuas = [
            nua for nua in generated_nuas 
            if tracker.is_nua_alive(nua.sheet.name)
        ]
        
        removed_count = len(generated_nuas_before) - len(generated_nuas)
        if removed_count > 0:
            print(f"[POPULATION] Filtered out {removed_count} deceased NUAs")
    
    return generated_nuas
```

**Also Fix:** `redesigned_main.py` - Pass tracker to population:
```python
available_npcs = populate_scene_with_nuas(
    creator_agent=creator,
    scene_description=scene_description,
    time_context=time_context,
    full_population=True,
    tracker=tracker  # ADD THIS
)
```

---

## ❌ **3. NUA State History NOT Matched with Memories**

### Problem:
- `tracker.get_nua_state_history()` returns full state
- `nua_memory_system.get_memories_for_nua()` returns memories
- **BUT:** No validation that memories match state
- **Result:** NUA behavior inconsistent with their history

### Where to Fix:
**File:** `agents/decider_agent.py`

**Methods:** `determine_nua_proaction()` and `determine_nua_reaction()`

### How to Fix:
```python
# In both methods, AFTER getting NUA memories:

# Get NUA state history for consistency check
nua_state = None
if hasattr(self, 'tracker_agent') and self.tracker_agent:
    nua_state = self.tracker_agent.get_nua_state_history(proactor.sheet.name)

# Validate memory consistency
if nua_state and nua_state['status'] == 'alive':
    # Check sympathy matches
    tracked_sympathy = nua_state['state']['sympathy'].get(reactor.sheet.name, {})
    current_sympathy = proactor.sheet.sympathy.get(reactor.sheet.name)
    
    if tracked_sympathy and current_sympathy:
        if abs(tracked_sympathy['value'] - current_sympathy.value) > 2:
            print(f"[WARNING] Sympathy mismatch for {proactor.sheet.name}")
            # Use tracked value as source of truth
            current_sympathy.value = tracked_sympathy['value']

# Add state context to prompt:
state_context = ""
if nua_state:
    state_context = f"""
**NUA STATE HISTORY:**
Last known location: {nua_state.get('location', 'Unknown')}
Current sympathy toward {reactor.sheet.name}: {tracked_sympathy.get('value', 0)}
Status: {nua_state['status']}

Your behavior MUST be consistent with this history.
"""
```

---

## ❌ **4. Spatial Context NOT Fed to Distance Calculations**

### Problem:
- `spatial_context_system.py` tracks positions
- Distance matters for combat/interaction
- **BUT:** Not used in exchange system
- **Result:** Actors can interact from impossible distances

### Where to Fix:
**File:** `exchange_system.py` or wherever distance checks happen

### How to Fix:
```python
# Before exchange resolution:
if hasattr(self, 'spatial_manager') and self.spatial_manager:
    proactor_pos = self.spatial_manager.get_actor_position(proactor.sheet.name)
    reactor_pos = self.spatial_manager.get_actor_position(reactor.sheet.name)
    
    if proactor_pos and reactor_pos:
        distance = self.spatial_manager.calculate_distance(proactor_pos, reactor_pos)
        
        # Check if action is possible at this distance
        if action_requires_touch and distance > 2:
            print(f"[SPATIAL] Action impossible - distance {distance} too far")
            # Modify success or prevent action
```

---

## ❌ **5. UA Goals NOT Fed to InterpreterAgent**

### Problem:
- `goal_task_manager` tracks UA goals
- Goals should inform action interpretation
- **BUT:** InterpreterAgent doesn't see goals
- **Result:** Actions interpreted without goal context

### Where to Fix:
**File:** `agents/interpreter_agent.py`

**Method:** `interpret_user_action()` - Line ~200

### How to Fix:
```python
# Get UA goals
goal_context = ""
if hasattr(actor.sheet, 'goal_task_manager'):
    try:
        goals = actor.sheet.goal_task_manager.goals
        if goals:
            goal_context = "\n**USER ACTOR GOALS:**\n"
            for goal in goals[:3]:  # Top 3 goals
                progress = int(goal.progress * 100)
                goal_context += f"- {goal.description} ({progress}% complete, {goal.importance})\n"
            goal_context += "\nInterpret the action in context of these goals.\n"
    except Exception:
        pass

# Add to prompt:
prompt = f"""
{goal_context}

Interpret this action: {user_input}
...
"""
```

---

## ❌ **6. PersistentContext NOT Loaded on Session Resume**

### Problem:
- `PersistentContextManager` saves context
- **BUT:** May not be loaded properly on resume
- **Result:** Context lost between sessions

### Where to Fix:
**File:** `MAIN/redesigned_main.py`

**Location:** Session resume section - Line ~1950

### How to Fix:
```python
if resuming_session:
    # ... existing resume code ...
    
    # CRITICAL: Load persistent context
    try:
        from persistent_context_manager import get_context_manager
        context_manager = get_context_manager()
        persistent_context = context_manager.get_context()
        
        # Restore context to variables
        if persistent_context:
            scene_description = persistent_context.current_scene_description or resume_scene_description
            current_location = persistent_context.current_location
            present_nuas = persistent_context.present_nuas
            
            print(f"[CONTEXT] Restored persistent context:")
            print(f"  Location: {current_location}")
            print(f"  NUAs: {len(present_nuas)}")
    except Exception as e:
        print(f"[WARNING] Could not load persistent context: {e}")
```

---

## ❌ **7. Scene Description NOT Updated After Exploration**

### Problem:
- Exploration actions generate new narrative
- **BUT:** `scene_description` variable not updated
- **Result:** NUA creation uses stale scene (ALREADY FIXED in this session!)

### Status: ✅ **FIXED**
- Added scene_description update after exploration actions
- Line 3469 in redesigned_main.py

---

## ❌ **8. Available NPCs NOT Cleared on Location Change**

### Problem:
- Location changes should clear old NUAs
- **BUT:** May just append new ones
- **Result:** NUA overlap between locations

### Status: ✅ **FIXED**
- Created `replace_scene_npcs()` helper function
- Updated integration guide

---

## ❌ **9. RAG World Lore NOT Fed to Scene Population**

### Problem:
- RAG system has world lore
- Scene population should use it
- **BUT:** Not integrated
- **Result:** NUAs don't match world lore

### Where to Fix:
**File:** `scene_population_system.py`

**Method:** `populate_scene()` - Line ~160

### How to Fix:
```python
def populate_scene(self, scene_description: str, time_of_day: str = "day",
                   rag_system=None) -> List[NonUserActor]:
    """Generate NUAs with world lore context"""
    
    # Get world lore context
    rag_context = ""
    if rag_system:
        try:
            search_query = f"{scene_type} {time_of_day} 1990s"
            rag_context = rag_system.get_context_for_llm(
                query=search_query,
                max_tokens=400
            )
        except Exception:
            pass
    
    # Add to NUA generation prompt:
    nua_prompt = f"""
{rag_context}

Create a {role.role_type} for this scene:
Scene: {scene_description[:300]}
...
"""
```

---

## ❌ **10. Time Context NOT Validated**

### Problem:
- Time advances with actions
- **BUT:** No validation of time logic
- **Result:** Time paradoxes possible

### Where to Fix:
**File:** `master_time_coordinator.py` or wherever time advances

### How to Fix:
```python
# Before advancing time:
def advance_time(self, duration: float, action_type: str):
    """Advance time with validation"""
    
    # Validate time advancement
    if duration < 0:
        raise ValueError("Cannot go backwards in time")
    
    if duration > 480:  # 8 hours
        print(f"[WARNING] Large time jump: {duration} minutes")
        # Require explicit confirmation for large jumps
    
    # Check for time paradoxes
    current_time = self.get_current_time()
    new_time = current_time + duration
    
    # Validate against session timeline
    # ...
```

---

## PRIORITY ORDER

### **CRITICAL (Fix Immediately):**
1. ✅ Concrete details to NarratorAgent
2. ✅ Deceased NUA checking in population
3. ✅ NUA state/memory consistency validation

### **HIGH (Fix Soon):**
4. ⚠️ Spatial context to distance checks
5. ⚠️ UA goals to InterpreterAgent
6. ⚠️ PersistentContext loading on resume

### **MEDIUM (Fix When Possible):**
7. ⚠️ RAG lore to scene population
8. ⚠️ Time validation
9. ⚠️ Memory-based NUA behavior verification

---

## TESTING CHECKLIST

After fixing each integration:

- [ ] **Concrete Details:** Change car, verify consistency maintained
- [ ] **Dead NUAs:** Kill NUA, change location, verify they don't reappear
- [ ] **State/Memory:** Check NUA behavior matches their memories
- [ ] **Spatial:** Try to interact from far away, verify distance check
- [ ] **Goals:** Give UA goal, verify actions interpreted in context
- [ ] **Resume:** Save/quit/resume, verify context restored
- [ ] **RAG:** Check NUAs match world lore
- [ ] **Time:** Verify time advances logically
- [ ] **Location Change:** Verify old NUAs cleared
- [ ] **Scene Update:** Verify scene description updates

---

## IMPLEMENTATION NOTES

### **Pattern to Follow:**
```python
# 1. Check if context system exists
if hasattr(self, 'context_system') and self.context_system:
    try:
        # 2. Get context
        context = self.context_system.get_context(...)
        
        # 3. Format for LLM
        context_str = format_context(context)
        
        # 4. Add to prompt FIRST
        prompt = f"{context_str}\n\n{rest_of_prompt}"
        
        # 5. Call LLM
        response = self.client.chat.completions.create(...)
    except Exception as e:
        # 6. Log but don't break
        print(f"[WARNING] Context error: {e}")
```

### **Always:**
- ✅ Add context FIRST in prompts
- ✅ Use try/except to prevent breaks
- ✅ Log when context is missing
- ✅ Verify context before using
- ✅ Save context after changes

---

## CONCLUSION

**These missing integrations are CRITICAL.**

Without them:
- ❌ Details contradict (car changes)
- ❌ Dead NUAs resurrect
- ❌ NUA behavior inconsistent
- ❌ Spatial impossibilities
- ❌ Actions lack goal context
- ❌ Context lost on resume

**Fix these FIRST before adding new features.**

Context is EVERYTHING. If it's not fed properly, the simulation breaks.
