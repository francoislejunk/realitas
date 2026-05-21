# COMPREHENSIVE CONTEXT AUDIT - REALITAS NEO

## ⚠️ CRITICAL: Context is EVERYTHING

**If context is misused, it DESTROYS the simulation.**

This audit tracks EVERY piece of context, where it's saved, and where it MUST be fed.

---

## Context Systems Overview

### 1. **PersistentContextManager** (`persistent_context_manager.py`)
**Saves:** Complete scene/location state
**Storage:** `simulation_data/context/context_{session_id}.json`

**Data Tracked:**
- ✅ `current_location` - Where UA is
- ✅ `current_scene_description` - Full scene text
- ✅ `location_label` - Type of location (diner, street, etc.)
- ✅ `present_nuas` - List of NUA names in scene
- ✅ `available_nua_ids` - Actor IDs for reconstruction
- ✅ `recent_events` - Last 10 events
- ✅ `recent_narratives` - Last 5 narrations
- ✅ `opportunities` - Available actions/paths
- ✅ `visible_objects` - Items in scene
- ✅ `accessible_paths` - Exits/directions
- ✅ `time_of_day`, `weather`, `season`
- ✅ `narrative_mode` - ROAM/ENCOUNTER
- ✅ `user_last_action`, `user_last_intent`

**WHERE IT MUST BE FED:**
- [ ] **NarratorAgent** - Scene generation
- [ ] **InterpreterAgent** - Action interpretation
- [ ] **DeciderAgent** - NUA decision making
- [ ] **ConductorAgent** - Scene transitions
- [ ] **CreatorAgent** - NUA generation
- [ ] **Scene population** - Pre-generate correct NUAs
- [ ] **Intent availability** - Check what's possible

---

### 2. **TrackerAgent** (`agents/tracker_agent.py`)
**Saves:** Session data, turn history, actor states
**Storage:** `simulation_data/sessions/session_{session_id}.json`

**Data Tracked:**
- ✅ `runtime_state.scene_description` - Current scene
- ✅ `runtime_state.current_location` - Location label
- ✅ `runtime_state.available_npcs` - Full NUA actor sheets
- ✅ `runtime_state.deceased_nuas` - Dead NUAs (permanent)
- ✅ `initial_actors` - Starting actor sheets
- ✅ `scenes` - All scene data
- ✅ `session_statistics` - Turn counts, success rates
- ✅ Turn-by-turn data (all 6 UTAS steps)

**WHERE IT MUST BE FED:**
- [ ] **Scene resume** - Load last scene description
- [ ] **NUA population** - Load available_npcs
- [ ] **Death checking** - Prevent dead NUA resurrection
- [ ] **State history** - NUA consistency checks
- [ ] **Memory system** - Match memories to states
- [ ] **Statistics display** - Show progress

---

### 3. **NarrativeContextManager** (`narrative_context_system.py`)
**Saves:** Narrative events, concrete details, established facts
**Storage:** `simulation_data/narrative_context/narrative_context_{session_id}.json`

**Data Tracked:**
- ✅ **Narrative Events** - Turn-by-turn story beats
- ✅ **Concrete Details** - Specific facts (car models, clothing, etc.)
- ✅ **Detail Categories** - VEHICLE, CLOTHING, WEAPON, LOCATION, etc.
- ✅ **Owner indexing** - Who owns/has what
- ✅ **Keyword matching** - Semantic search
- ✅ **Mention tracking** - How often details referenced

**WHERE IT MUST BE FED:**
- [ ] **NarratorAgent** - MUST include concrete details in prompts
- [ ] **DeciderAgent** - NUA must know established facts
- [ ] **InterpreterAgent** - Validate actions against facts
- [ ] **Continuity checks** - Verify consistency
- [ ] **Scene generation** - Include established details

---

### 4. **SpatialContextSystem** (`spatial_context_system.py`)
**Saves:** Location maps, positions, obstacles, zones
**Storage:** `sessions/{session_id}/spatial_context.json`

**Data Tracked:**
- ✅ **Locations** - All visited places with dimensions
- ✅ **Actor positions** - X,Y coordinates for all actors
- ✅ **Obstacles** - Walls, furniture, barriers
- ✅ **Zones** - Areas within locations
- ✅ **Exits** - Connections between locations
- ✅ **Movement history** - Where actors have been

**WHERE IT MUST BE FED:**
- [ ] **Distance calculations** - Combat range checks
- [ ] **Movement validation** - Can actor reach target?
- [ ] **Scene description** - Spatial relationships
- [ ] **NUA positioning** - Where NPCs are
- [ ] **Obstacle detection** - Line of sight, cover

---

### 5. **NUA Memory System** (`npc_memory_system.py`)
**Saves:** NUA memories of interactions
**Storage:** `simulation_data/nua_memories/nua_memories.json`

**Data Tracked:**
- ✅ **Threat memories** - Who threatened them
- ✅ **Help memories** - Who helped them
- ✅ **Violence memories** - Combat encounters
- ✅ **Conversation memories** - Dialogue history
- ✅ **Sympathy changes** - Relationship shifts
- ✅ **Timestamps** - When events occurred

**WHERE IT MUST BE FED:**
- [ ] **DeciderAgent** - NUA decision making
- [ ] **NUA behavior** - Consistent reactions
- [ ] **Sympathy initialization** - Starting relationships
- [ ] **Dialogue generation** - Reference past conversations
- [ ] **Threat assessment** - Remember enemies

---

### 6. **User Actor Memories** (`automatic_memory_creation.py`)
**Saves:** UA key memories
**Storage:** `simulation_data/memories/{session_id}_memories.json`

**Data Tracked:**
- ✅ **First meetings** - NUA introductions
- ✅ **Combat victories/defeats**
- ✅ **Task completions**
- ✅ **Discoveries** - Items, locations, revelations
- ✅ **Relationship milestones**
- ✅ **Deaths** - Who died, how, when

**WHERE IT MUST BE FED:**
- [ ] **NarratorAgent** - Reference past events
- [ ] **InterpreterAgent** - Context for actions
- [ ] **Memory recall commands** - `/mem` display
- [ ] **Investigation** - Detective work
- [ ] **Relationship context** - Why UA knows someone

---

### 7. **Concrete Detail Tracker** (part of NarrativeContextManager)
**Saves:** Specific unchangeable facts
**Storage:** Within `narrative_context_{session_id}.json`

**Data Tracked:**
- ✅ **VEHICLE** - Car models, motorcycles
- ✅ **CLOTHING** - What characters wear
- ✅ **WEAPON** - Specific weapons/tools
- ✅ **LOCATION** - Named places
- ✅ **BRAND** - Watches, phones, brands
- ✅ **PHYSICAL_TRAIT** - Scars, tattoos
- ✅ **POSSESSION** - Items owned
- ✅ **BUILDING** - Specific buildings
- ✅ **RELATIONSHIP** - Relationship facts
- ✅ **BACKSTORY** - Established history

**WHERE IT MUST BE FED:**
- [ ] **NarratorAgent** - FIRST in context, MUST remain consistent
- [ ] **DeciderAgent** - NUA knows established facts
- [ ] **Scene generation** - Include existing details
- [ ] **Continuity validation** - Check for contradictions

---

### 8. **NUA Life Tracker** (`nua_life_tracker.py`)
**Saves:** NUA states when not present
**Storage:** `simulation_data/narrative_context/nua_lives/nua_life_states.json`

**Data Tracked:**
- ✅ **Last seen timestamp**
- ✅ **Last location**
- ✅ **Last activity**
- ✅ **Appearance** - Clothing, grooming
- ✅ **Possessions** - Items they had
- ✅ **Mood** - Emotional state
- ✅ **Ongoing activities**
- ✅ **Life events**

**WHERE IT MUST BE FED:**
- [ ] **NUA reunion** - Generate observable changes
- [ ] **Time-based changes** - What changed since last seen
- [ ] **NUA generation** - Consistent appearance
- [ ] **Dialogue** - Reference their life events

---

### 9. **RAG Worldbuilding System** (`WORLD_BUILDER/lore_rag_system.py`)
**Saves:** World lore, factions, locations, culture
**Storage:** `WORLD_BUILDER/worldbuilding_data/`

**Data Tracked:**
- ✅ **Geography** - World structure
- ✅ **History** - Timeline, events
- ✅ **Factions** - Organizations, gangs
- ✅ **Culture** - Customs, traditions
- ✅ **Locations** - POIs, landmarks
- ✅ **NPCs** - Major characters
- ✅ **Economics** - Resources, trade
- ✅ **Technology** - 1990s tech level

**WHERE IT MUST BE FED:**
- [ ] **CreatorAgent** - Scene generation
- [ ] **NUA generation** - Character creation
- [ ] **NarratorAgent** - World-consistent narration
- [ ] **Location generation** - New places
- [ ] **Faction behavior** - Organizational actions

---

### 10. **Goal/Task Manager** (part of ActorSheet)
**Saves:** UA goals and tasks
**Storage:** Within actor sheet in session data

**Data Tracked:**
- ✅ **Goals** - Major objectives
- ✅ **Sub-goals** - Intermediate steps
- ✅ **Tasks** - Specific actions
- ✅ **Progress** - Completion percentage
- ✅ **Importance** - Priority levels
- ✅ **Created turn** - When goal added
- ✅ **Last modified** - When updated

**WHERE IT MUST BE FED:**
- [ ] **InterpreterAgent** - Interpret actions in context of goals
- [ ] **NarratorAgent** - Reference goals in narration
- [ ] **Task completion** - Automatic memory creation
- [ ] **Progress tracking** - Update percentages
- [ ] **Goal display** - Show to player

---

## CRITICAL INTEGRATION POINTS

### 🔴 **Scene Generation** (NarratorAgent, CreatorAgent)
**MUST INCLUDE:**
1. ✅ Current location from PersistentContext
2. ✅ Present NUAs from PersistentContext
3. ✅ Recent events from NarrativeContext
4. ✅ Concrete details from ConcreteDetailTracker
5. ✅ Time/weather from PersistentContext
6. ✅ Spatial layout from SpatialContext
7. ✅ World lore from RAG
8. ✅ Opportunities from PersistentContext

### 🔴 **NUA Decision Making** (DeciderAgent)
**MUST INCLUDE:**
1. ✅ NUA memories from NUAMemorySystem
2. ✅ NUA state history from TrackerAgent
3. ✅ Concrete details from ConcreteDetailTracker
4. ✅ Spatial positions from SpatialContext
5. ✅ Recent events from NarrativeContext
6. ✅ Sympathy values from ActorSheet
7. ✅ UA goals from GoalTaskManager
8. ✅ Established facts from NarrativeContext

### 🔴 **Action Interpretation** (InterpreterAgent)
**MUST INCLUDE:**
1. ✅ Current scene from PersistentContext
2. ✅ Present NUAs from PersistentContext
3. ✅ Visible objects from PersistentContext
4. ✅ Accessible paths from PersistentContext
5. ✅ Recent events from NarrativeContext
6. ✅ Concrete details from ConcreteDetailTracker
7. ✅ Spatial context from SpatialContext
8. ✅ UA goals from GoalTaskManager

### 🔴 **Scene Population** (ScenePopulator)
**MUST INCLUDE:**
1. ✅ Location type from PersistentContext
2. ✅ Time of day from PersistentContext
3. ✅ Deceased NUAs from TrackerAgent (exclude them!)
4. ✅ World lore from RAG
5. ✅ Scene description for context
6. ✅ Existing NUAs from TrackerAgent (don't duplicate)

### 🔴 **Continuity Validation**
**MUST CHECK:**
1. ✅ Concrete details consistency
2. ✅ Dead NUAs don't reappear
3. ✅ NUA memories match state
4. ✅ Spatial positions valid
5. ✅ Time progression logical
6. ✅ Established facts maintained

---

## CONTEXT FEEDING CHECKLIST

### **Every LLM Call Must Include:**

#### NarratorAgent Methods:
- [ ] `generate_scene_with_narrative_loop()` - ALL context
- [ ] `generate_step6_turn_narrative()` - Recent events, concrete details
- [ ] `generate_exploration_action_result_narrative()` - Scene, objects, paths
- [ ] `generate_internal_voice()` - Goals, recent events, memories
- [ ] `generate_location_transition()` - Spatial, concrete details

#### DeciderAgent Methods:
- [ ] `determine_nua_proaction()` - NUA memories, state, concrete details
- [ ] `determine_nua_reaction()` - NUA memories, spatial, recent events
- [ ] Both must have UA sheet HIDDEN (no meta-gaming)

#### InterpreterAgent Methods:
- [ ] `interpret_user_action()` - Scene, NUAs, objects, paths, goals
- [ ] `detect_inquiry_or_action()` - Scene context
- [ ] `generate_inquiry_response()` - All relevant context

#### CreatorAgent Methods:
- [ ] `generate_initial_scene()` - World lore, UA goals
- [ ] `generate_nua()` - Scene, world lore, concrete details
- [ ] `generate_scene_description()` - Spatial, concrete details

---

## CONTEXT SAVE TRIGGERS

### **When to Save Each Context:**

**PersistentContext - Save After:**
- ✅ Every scene change
- ✅ Every location move
- ✅ Every NUA enters/leaves
- ✅ Every user action
- ✅ Every narrative generation
- ✅ Every mode change (ROAM ↔ ENCOUNTER)

**TrackerAgent - Save After:**
- ✅ Every turn completion
- ✅ Every scene transition
- ✅ Every NUA death
- ✅ Every status change
- ✅ Auto-save every 5 turns
- ✅ Session end

**NarrativeContext - Save After:**
- ✅ Every narrative event
- ✅ Every concrete detail added
- ✅ Every turn completion

**SpatialContext - Save After:**
- ✅ Every actor movement
- ✅ Every location change
- ✅ Every obstacle added/removed
- ✅ Every zone update

**NUA Memories - Save After:**
- ✅ Every threat
- ✅ Every help action
- ✅ Every violence
- ✅ Every conversation
- ✅ Every sympathy change

**UA Memories - Save After:**
- ✅ Every first meeting
- ✅ Every combat end
- ✅ Every task completion
- ✅ Every discovery
- ✅ Every death

---

## CRITICAL BUGS TO PREVENT

### ❌ **Context Bleed**
**Problem:** Old location context bleeds into new location
**Solution:** Clear PersistentContext on location change

### ❌ **Dead NUA Resurrection**
**Problem:** Deceased NUA reappears in scene
**Solution:** Check `tracker.is_nua_alive()` before creating

### ❌ **Concrete Detail Contradiction**
**Problem:** Car changes from Lamborghini to Toyota
**Solution:** Always include concrete details FIRST in prompts

### ❌ **Memory Mismatch**
**Problem:** NUA behavior doesn't match their memories
**Solution:** Always feed NUA memories to DeciderAgent

### ❌ **Spatial Impossibility**
**Problem:** Actor teleports or moves through walls
**Solution:** Validate movement with SpatialContext

### ❌ **Goal Amnesia**
**Problem:** UA actions don't align with their goals
**Solution:** Include goals in InterpreterAgent context

### ❌ **Time Paradox**
**Problem:** Events happen out of order
**Solution:** Include timeline in all context

### ❌ **NUA Overlap**
**Problem:** Multiple locations' NUAs in one scene
**Solution:** Clear available_npcs before populating new location

---

## VERIFICATION COMMANDS

### **Check Context Integrity:**
```python
# 1. Verify PersistentContext loaded
assert persistent_context.current_location != "unknown"
assert len(persistent_context.present_nuas) >= 0

# 2. Verify TrackerAgent state
assert tracker.is_nua_alive(nua_name) before creating NUA
assert tracker.get_nua_state_history(nua_name) is not None

# 3. Verify NarrativeContext
concrete_details = narrative_context.get_concrete_details_for_actor(actor_name)
assert len(concrete_details) > 0 if actor has established details

# 4. Verify SpatialContext
position = spatial.get_actor_position(actor_name)
assert position is not None if actor in scene

# 5. Verify NUA Memories
memories = nua_memory_system.get_memories_for_nua(nua_name)
assert memories match nua behavior

# 6. Verify available_npcs
assert no dead NUAs in available_npcs
assert no duplicate NUAs in available_npcs
```

---

## IMPLEMENTATION PRIORITY

### **Phase 1: Critical Context (DO FIRST)**
1. ✅ Ensure TrackerAgent saves/loads available_npcs
2. ✅ Ensure TrackerAgent tracks deceased_nuas
3. ✅ Ensure PersistentContext saves after every change
4. ✅ Ensure ConcreteDetailTracker feeds to NarratorAgent

### **Phase 2: NUA Consistency**
1. ⚠️ Feed NUA memories to DeciderAgent
2. ⚠️ Feed NUA state history to DeciderAgent
3. ⚠️ Check is_nua_alive() before NUA creation
4. ⚠️ Match NUA behavior to memories

### **Phase 3: Spatial & Goals**
1. ⚠️ Feed SpatialContext to all agents
2. ⚠️ Feed UA goals to InterpreterAgent
3. ⚠️ Validate movement with spatial system
4. ⚠️ Update goal progress automatically

### **Phase 4: World Lore**
1. ⚠️ Feed RAG context to CreatorAgent
2. ⚠️ Feed RAG context to NarratorAgent
3. ⚠️ Ensure world consistency
4. ⚠️ Category cleanup (remove redundant categories)

---

## NEXT STEPS

1. **Audit every LLM prompt** - Verify context inclusion
2. **Add context verification** - Assert statements before LLM calls
3. **Test context persistence** - Save/load cycles
4. **Test context feeding** - Verify LLM receives correct data
5. **Test edge cases** - Dead NUAs, location changes, time skips
6. **Document missing integrations** - Where context isn't fed yet
7. **Implement missing integrations** - Fill the gaps

---

## CONCLUSION

**Context is EVERYTHING. If any piece is missing or misused, the simulation breaks.**

This audit provides a complete map of:
- ✅ What context exists
- ✅ Where it's saved
- ✅ Where it MUST be fed
- ✅ When to save it
- ✅ How to verify it

**Use this as the definitive reference for all context integration work.**
