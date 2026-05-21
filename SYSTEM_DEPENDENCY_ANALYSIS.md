# System Dependency Analysis for redesigned_main.py

This document analyzes all systems used in the main simulation loop to identify:
1. Active systems and their purpose
2. Redundant or deprecated systems
3. Integration gaps
4. Flow correctness

---

## 1. CORE AGENTS (Essential - All Active)

| File | Purpose | Status |
|------|---------|--------|
| `agents/conductor_agent.py` | Orchestrates all agent interactions | ✅ ACTIVE |
| `agents/creator_agent.py` | Creates actors, scenes, memories | ✅ ACTIVE |
| `agents/narrator_agent.py` | Generates narrative descriptions | ✅ ACTIVE |
| `agents/tracker_agent.py` | Session persistence, actor tracking | ✅ ACTIVE |
| `agents/decider_agent.py` | NUA decision making (via Conductor) | ✅ ACTIVE |
| `agents/interpreter_agent.py` | Action interpretation (via Conductor) | ✅ ACTIVE |

---

## 2. NEW INTERNAL VOICE & STORYTELLER SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `agents/internal_voice_interpreter_agent.py` | Determines voice function type | ✅ NEW - ACTIVE |
| `agents/internal_voice_creator_agent.py` | Generates voice content | ✅ NEW - ACTIVE |
| `agents/storyteller_agent.py` | Generates narrative sparks | ✅ NEW - ACTIVE |
| `reputation_system.py` | Title-based reputation tracking | ✅ NEW - ACTIVE |

### Potential Redundancy:
| File | Purpose | Status |
|------|---------|--------|
| `internal_voice_system.py` | Legacy internal voice | ⚠️ LEGACY - Being replaced |

**Recommendation:** The legacy `internal_voice_system.py` is still imported but should be fully replaced by the new agents. Currently used as fallback.

---

## 3. MEMORY SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `key_memories_system.py` | UA persistent memories | ✅ ACTIVE |
| `npc_memory_system.py` | NUA memory persistence | ✅ ACTIVE |
| `automatic_memory_creation.py` | Auto-generates memories from events | ✅ ACTIVE |
| `intent_based_memory_creation.py` | Creates memories from intents | ✅ ACTIVE |

### Potential Redundancy:
- `automatic_memory_creation.py` and `intent_based_memory_creation.py` may overlap
- Both create memories but from different triggers

**Recommendation:** Review if both are needed or can be consolidated.

---

## 4. SPATIAL & MAP SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `pygame_spatial_map.py` | Visual map display, actor positions | ✅ ACTIVE |
| `spatial_context_system.py` | Spatial state management | ✅ ACTIVE |
| `agents/architect_agent.py` | Layout generation, movement | ✅ ACTIVE |
| `location_distance_tracker.py` | Travel time calculations | ✅ ACTIVE |
| `sensing_bubble_system.py` | Perception range calculations | ✅ ACTIVE |
| `spatial_movement_detector.py` | Movement detection | ✅ ACTIVE |
| `spatial_location_analyzer.py` | Scene spatial analysis | ✅ ACTIVE |

### Disabled/Deprecated:
| File | Purpose | Status |
|------|---------|--------|
| `spatial_map_display.py` | Old text-based map | ❌ DISABLED |
| `spatial_display_integration.py` | Old map integration | ❌ DISABLED |
| `world_map_visualizer.py` | Old world map | ❌ DISABLED |

**Recommendation:** The disabled files can be removed if pygame_spatial_map fully replaces them.

---

## 5. TIME SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `master_time_coordinator.py` | Central time management | ✅ ACTIVE |
| `time_cycle_system.py` | Day/night cycle | ✅ ACTIVE |
| `simulation_time_tracker.py` | Simulation time tracking | ✅ ACTIVE |
| `reactor_time_system.py` | Reaction time budgets | ✅ ACTIVE |
| `time_lighting_updater.py` | Lighting based on time | ✅ ACTIVE |

**Status:** Well-organized with master_time_coordinator as central authority.

---

## 6. NARRATIVE & CONTEXT SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `llm_agents/narrative_context_system.py` | LLM narrative context | ✅ ACTIVE |
| `narrative_context_system.py` | Concrete details tracking | ✅ ACTIVE |
| `persistent_context_manager.py` | Session context persistence | ✅ ACTIVE |
| `context_injection_helper.py` | Context updates | ✅ ACTIVE |
| `llm_agents/nua_context_system.py` | NUA context management | ✅ ACTIVE |
| `narrative_utils.py` | Narrative helper functions | ✅ ACTIVE |

### Potential Confusion:
- Two files named `narrative_context_system.py` (one in root, one in llm_agents)
- They serve different purposes but naming is confusing

**Recommendation:** Rename root-level one to `concrete_details_manager.py` for clarity.

---

## 7. ACTOR SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `actors.py` | Actor classes (UA, NUA, MNUA, INUA) | ✅ ACTIVE |
| `actor_sheet.py` | Character sheet data | ✅ ACTIVE |
| `multi_actor_manager.py` | Multi-actor coordination | ✅ ACTIVE |
| `enhanced_dynamic_actor_system.py` | Dynamic actor creation | ✅ ACTIVE |
| `dynamic_actor_system.py` | Basic dynamic actors | ⚠️ LEGACY |
| `nua_introduction_system.py` | NUA introductions | ✅ ACTIVE |
| `agents/population_manager.py` | Scene population | ✅ ACTIVE |

### Potential Redundancy:
- `dynamic_actor_system.py` vs `enhanced_dynamic_actor_system.py`

**Recommendation:** Check if legacy `dynamic_actor_system.py` is still needed.

---

## 8. EXCHANGE & COMBAT SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `exchange_system.py` | Exchange mechanics | ✅ ACTIVE |
| `unified_formula.py` | Success calculations | ✅ ACTIVE |
| `exchange_completion_checker.py` | Exchange state tracking | ✅ ACTIVE |
| `enhanced_round_manager.py` | Round management | ✅ ACTIVE |
| `enhanced_reporter.py` | Exchange reporting | ✅ ACTIVE |
| `enhanced_sympathy_system.py` | Sympathy mechanics | ✅ ACTIVE |
| `enhanced_temporary_recovery_system.py` | Recovery mechanics | ✅ ACTIVE |
| `ally_coordination_system.py` | Ally behavior | ✅ ACTIVE |
| `initiative_system.py` | Turn order | ✅ ACTIVE |

---

## 9. WORLDBUILDING & RAG

| File | Purpose | Status |
|------|---------|--------|
| `WORLD_BUILDER/worldbuilding_rag.py` | RAG system | ✅ ACTIVE |
| `WORLD_BUILDER/realitas_lore.py` | Lore content | ✅ ACTIVE |
| `worldbuilding_helpers.py` | RAG helper functions | ✅ ACTIVE |
| `world_persistence_system.py` | World state persistence | ✅ ACTIVE |
| `world_spatial_integration.py` | World/spatial integration | ✅ ACTIVE |

---

## 10. IMMERSION SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `intent_availability_system.py` | Action availability | ✅ ACTIVE |
| `do_nothing_action.py` | Idle actions | ✅ ACTIVE |
| `progression_tracker.py` | Skill progression | ✅ ACTIVE |
| `goal_progress_tracker.py` | Goal tracking | ✅ ACTIVE |
| `goal_task_system.py` | Goal/task management | ✅ ACTIVE |
| `diegetic_transition_system.py` | Scene transitions | ✅ ACTIVE |
| `progressive_discovery_system.py` | Progressive revelation | ✅ ACTIVE |
| `skill_revelation_system.py` | Skill discovery | ✅ ACTIVE |
| `failure_tracker.py` | Failure awareness | ✅ ACTIVE |

---

## 11. VESSEL SELECTION

| File | Purpose | Status |
|------|---------|--------|
| `vessel_selection_system.py` | Character selection at start | ✅ ACTIVE |

---

## 12. UTILITY SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `color_utils.py` | Console colors | ✅ ACTIVE |
| `label_utils.py` | Label normalization | ✅ ACTIVE |
| `json_utils.py` | JSON parsing | ✅ ACTIVE |
| `openrouter_config.py` | LLM configuration | ✅ ACTIVE |
| `response_normalizer.py` | Response cleaning | ✅ ACTIVE |
| `save_coordinator.py` | Save conflict prevention | ✅ ACTIVE |
| `scene_continuity_validator.py` | Scene consistency | ✅ ACTIVE |
| `scene_npc_parser.py` | NPC extraction from scenes | ✅ ACTIVE |
| `inquiry_helpers.py` | Inquiry processing | ✅ ACTIVE |
| `inquiry_generation_order.py` | Inquiry ordering | ✅ ACTIVE |

---

## 13. SURVIVAL SYSTEM

| File | Purpose | Status |
|------|---------|--------|
| `survival_system.py` | Survival needs | ✅ ACTIVE |
| `survival_actions.py` | Survival action generation | ✅ ACTIVE |
| `survival_action_analyzer.py` | Survival action analysis | ✅ ACTIVE |

---

## 14. JOURNEY/TRAVEL

| File | Purpose | Status |
|------|---------|--------|
| `journey_chunking_system.py` | Long travel segmentation | ✅ ACTIVE |
| `rule_of_3s.py` | Action classification | ✅ ACTIVE |

---

## 15. ENCOUNTER/SPARK SYSTEMS

| File | Purpose | Status |
|------|---------|--------|
| `llm_agents/encounter_checker.py` | Encounter detection | ✅ ACTIVE |
| `llm_agents/spark_generator.py` | Spark generation | ✅ ACTIVE |
| `llm_agents/scene_event_scheduler.py` | Event scheduling | ✅ ACTIVE |
| `agents/background_simulation_system.py` | Background events | ✅ ACTIVE |

---

## 16. MONETARY SYSTEM

| File | Purpose | Status |
|------|---------|--------|
| `enhanced_monetary_system.py` | Money handling | ✅ ACTIVE |
| `inventory_manager.py` | Inventory management | ✅ ACTIVE |

---

## 17. IDENTITY SYSTEM

| File | Purpose | Status |
|------|---------|--------|
| `llm_agents/identity_manager.py` | Identity discovery | ✅ ACTIVE |
| `llm_agents/enhanced_narrative_loop.py` | Narrative mode management | ✅ ACTIVE |

---

# SUMMARY OF ISSUES

## Files to Consider Removing (Disabled/Deprecated):
1. `spatial_map_display.py` - Replaced by pygame_spatial_map
2. `spatial_display_integration.py` - Replaced by pygame_spatial_map
3. `world_map_visualizer.py` - Replaced by pygame_spatial_map

## Files with Potential Redundancy:
1. `internal_voice_system.py` - Being replaced by new voice agents
2. `dynamic_actor_system.py` - May be replaced by enhanced version
3. `automatic_memory_creation.py` vs `intent_based_memory_creation.py` - Overlap?

## Naming Confusion:
1. Two `narrative_context_system.py` files (root vs llm_agents)

## Integration Gaps:
1. ✅ FIXED: New voice systems now have RAG integration
2. ✅ FIXED: Reputation system now has RAG integration
3. ✅ FIXED: Storyteller receives RAG context

## Flow Verification:
The initialization order in main() is correct:
1. TrackerAgent (session management)
2. Context managers
3. RAG System (worldbuilding)
4. CreatorAgent, NarratorAgent, ConductorAgent (with RAG)
5. Session loading/creation
6. Memory systems
7. Narrative systems
8. Spatial systems
9. Time systems
10. World persistence
11. New voice/storyteller systems (with RAG)
12. Population manager

---

# SYSTEMS NOT INTEGRATED (Should Consider)

These systems exist but are NOT imported in redesigned_main.py:

## HIGH PRIORITY - Should Integrate

| File | Purpose | Why Important |
|------|---------|---------------|
| `witness_reaction_system.py` | NPCs react to violence/murder/theft | Prevents fake signals where NPCs ignore shocking events |
| `stranger_description_system.py` | Describe unknown NPCs by appearance | More immersive - don't use names for strangers |
| `dialogue_context_system.py` | Track conversation history/topics | Prevents NPCs forgetting conversations |
| `personality_mood_system.py` | OCEAN/MBTI + dynamic mood | Already designed for internal voice - should connect to new voice agents |
| `nua_life_tracker.py` | NPCs live lives when not present | Observable changes when you meet them again |
| `diegetic_clue_tracker.py` | Environmental clues imply NPC presence | Progressive discovery mechanics |

## MEDIUM PRIORITY - Could Enhance

| File | Purpose | Why Useful |
|------|---------|------------|
| `tactical_awareness_system.py` | NPCs make smart combat decisions | Take cover, flee when outmatched, use terrain |
| `object_registry.py` | Track INUA (object) states | Persistent object status tracking |
| `failure_narrative_generator.py` | Generate failure-specific narratives | Better failure descriptions |
| `sympathy_behavior_modifier.py` | Modify NPC behavior based on sympathy | More nuanced NPC reactions |

## LOW PRIORITY - Utility/Niche

| File | Purpose | Status |
|------|---------|--------|
| `action_type_detector.py` | Classify action types | May be used internally by other systems |
| `actor_state_filter.py` | Filter actor states | Utility |
| `concrete_detail_tracker.py` | Track concrete details | May overlap with narrative_context_system |
| `economic_awareness_enhancer.py` | Economic context | Niche use case |
| `inquiry_system.py` | Inquiry handling | May be replaced by inquiry_helpers |
| `layout_generator.py` / `llm_layout_generator.py` | Layout generation | May be replaced by architect_agent |
| `mode_transition_enhancer.py` | Mode transitions | May be integrated elsewhere |
| `partial_action_system.py` | Partial actions | Niche use case |
| `rule_of_3s_realtime.py` | Real-time Rule of 3s | May be integrated in rule_of_3s |

---

# RECOMMENDATIONS

## High Priority:
1. **Remove disabled map files** if pygame_spatial_map is stable
2. **Fully migrate from legacy internal_voice_system.py** to new agents
3. **Rename root narrative_context_system.py** to avoid confusion
4. **Integrate witness_reaction_system.py** - Critical for realistic NPC behavior
5. **Integrate stranger_description_system.py** - Already referenced in narrator prompts
6. **Connect personality_mood_system.py to new voice agents** - Designed for this purpose

## Medium Priority:
1. Review `automatic_memory_creation.py` vs `intent_based_memory_creation.py` for consolidation
2. Review `dynamic_actor_system.py` vs `enhanced_dynamic_actor_system.py`
3. Integrate `dialogue_context_system.py` for conversation continuity
4. Integrate `nua_life_tracker.py` for living world feel
5. Integrate `diegetic_clue_tracker.py` for progressive discovery

## Low Priority:
1. Consider consolidating utility imports at top of file
2. Reduce inline imports for cleaner code
3. Review tactical_awareness_system.py for combat scenarios
