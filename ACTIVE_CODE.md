# ACTIVE CODE - Realitas Neo

This document lists all **actively used** code files in the Realitas Neo simulation.
Dead code has been moved to the `TRASH BIN/` folder.

**Last Updated:** December 12, 2025 (RAG + Regeneration complete)

---

## 📁 Main Entry Point

| File | Purpose |
|------|---------|
| `MAIN/redesigned_main.py` | **Primary entry point** - Main simulation loop |

---

## 🤖 Agents (`agents/`)

| File | Purpose | RAG Integration |
|------|---------|-----------------|
| `conductor_agent.py` | Orchestrates exchanges and scene management | ✅ Yes |
| `creator_agent.py` | Creates scenes, NPCs, vessels | ✅ Yes |
| `narrator_agent.py` | Generates all narrative descriptions | ✅ Yes (extensive) |
| `interpreter_agent.py` | Interprets user actions into UTAS format | ✅ Yes |
| `decider_agent.py` | NUA decision making and reactions | ✅ Yes |
| `tracker_agent.py` | Session and state tracking | N/A |
| `storyteller_agent.py` | Silent orchestrator, Spark generation | ✅ Receives RAG context |
| `background_simulation_system.py` | NUA autonomous actions in ROAM mode | ✅ Yes |
| `internal_voice_interpreter_agent.py` | Interprets internal voice triggers | N/A (classifier only) |
| `internal_voice_creator_agent.py` | Creates internal voice content | ✅ Yes |
| `architect_agent.py` | Spatial layout generation | ✅ Yes |

| `population_manager.py` | Scene population roster | ✅ Yes |

---

## 🧠 LLM Agents (`llm_agents/`)

| File | Purpose | RAG Integration |
|------|---------|-----------------|
| `target_detection_system.py` | NUA/INUA target classification | N/A |
| `encounter_checker.py` | Dynamic encounter detection | N/A |
| `scene_manager.py` | Scene synthesis and management | ✅ Yes |
| `narrative_loop_system.py` | Four-mode narrative analysis | N/A |
| `nua_context_system.py` | Action classification and escalation | N/A |
| `sympathy_initialization.py` | Relationship generation | N/A |
| `utas_narrative_formula.py` | Formula-based narrative outcomes | N/A |
| `narrative_context_system.py` | Narrative context management | N/A |
| `identity_manager.py` | Identity discovery integration | N/A |

---

## 👤 Actor System

| File | Purpose |
|------|---------|
| `actors.py` | Actor, UserActor, NonUserActor, ActorCategory |
| `actor_sheet.py` | ActorSheet, SFactors, Item, StatusType |
| `actor_state_filter.py` | Actor state filtering |
| `actor_placement_system.py` | Actor placement in spatial system |
| `multi_actor_manager.py` | MultiActorManager, ActorRole |

---

## ⚔️ Exchange/Combat System

| File | Purpose |
|------|---------|
| `exchange_system.py` | Core exchange mechanics |
| `exchange_completion_checker.py` | LLM-based disengagement detection |
| `enhanced_round_manager.py` | Turn order and round management |
| `enhanced_reporter.py` | Outcome display and reporting |
| `response_normalizer.py` | Normalizes LLM responses, sensory perspective |
| `unified_formula.py` | Unified UTAS calculation formula |
| `initiative_system.py` | Initiative and turn order |

---

## 🗺️ Spatial System

| File | Purpose |
|------|---------|
| `pygame_spatial_map.py` | **Primary map system** - Pygame visualization |
| `spatial_context_system.py` | SpatialContextManager, Position, Zone, Obstacle |
| `world_spatial_integration.py` | World spatial commands |
| `location_distance_tracker.py` | Location tracking and travel |
| `spatial_location_analyzer.py` | Location analysis |
| `spatial_position_resolver.py` | Position resolution |
| `spatial_movement_detector.py` | Movement detection |
| `llm_layout_generator.py` | LLM-based layout generation |
| `layout_generator.py` | Layout generation utilities |
| `rich_spatial_display.py` | Rich spatial display |

---

## ⏰ Time System

| File | Purpose |
|------|---------|
| `rule_of_3s.py` | RuleOf3Classifier (3-second/3-minute/sleep) |
| `time_cycle_system.py` | TimeCycleTracker, TimeOfDay |
| `reactor_time_system.py` | ReactorTimeManager, ActionSpeed |
| `time_lighting_updater.py` | Time-based lighting |
| `master_time_coordinator.py` | Master time coordination |
| `simulation_time_tracker.py` | Simulation time tracking |

---

## 💭 Immersion Systems

| File | Purpose |
|------|---------|
| `intent_availability_system.py` | No Manifestation system |
| `intent_based_memory_creation.py` | Memory creation from intent |
| `do_nothing_action.py` | Do nothing action handling |
| `progression_tracker.py` | Skill & sympathy progression |
| `progression_integration_helper.py` | Progression integration |
| `goal_progress_tracker.py` | Goal progress tracking |
| `goal_task_system.py` | Goal and task management |
| `diegetic_transition_system.py` | Diegetic transitions |
| `sensing_bubble_system.py` | Sensory perception bubbles |
| `sensory_constants.py` | Sensory distance thresholds |
| `internal_voice_system.py` | Legacy internal voice (fallback) |

---

## 👥 NPC Systems

| File | Purpose |
|------|---------|
| `witness_reaction_system.py` | NPCs react to violence |
| `stranger_description_system.py` | Describe unknown NPCs |
| `dialogue_context_system.py` | Conversation history |
| `personality_mood_system.py` | OCEAN/MBTI + mood |
| `nua_life_tracker.py` | NPCs live lives when not present |
| `diegetic_clue_tracker.py` | Environmental clues |
| `tactical_awareness_system.py` | Smart combat decisions |
| `sympathy_behavior_modifier.py` | Sympathy-based behavior |
| `nua_introduction_system.py` | NUA introduction handling |
| `npc_memory_system.py` | NPC memory system |
| `npc_parser_wrapper.py` | NPC parsing utilities |
| `scene_npc_parser.py` | Scene NPC parsing |

---

## 🌍 World Systems

| File | Purpose |
|------|---------|
| `WORLD_BUILDER/worldbuilding_rag_system.py` | **RAG System** - Single source of lore |
| `WORLD_BUILDER/worldbuilding_rag.py` | RAG categories and queries |
| `world_persistence_system.py` | World state persistence |
| `object_registry.py` | INUA object states |
| `concrete_detail_tracker.py` | Consistent detail tracking |
| `scene_continuity_validator.py` | Scene continuity validation |

---

## 💰 Economy & Inventory

| File | Purpose |
|------|---------|
| `enhanced_monetary_system.py` | Currency and transactions |
| `inventory_manager.py` | Inventory management |
| `supply_utils.py` | Supply utilities |
| `economic_awareness_enhancer.py` | Economic awareness |

---

## ❤️ Status & Survival

| File | Purpose |
|------|---------|
| `survival_system.py` | SurvivalManager, SurvivalNeed |
| `survival_actions.py` | Survival action definitions |
| `survival_action_analyzer.py` | Survival action analysis |
| `enhanced_sympathy_system.py` | Sympathy management |
| `enhanced_temporary_recovery_system.py` | Temporary recovery |
| `enhanced_dynamic_actor_system.py` | Dynamic actor management |

---

## 🎭 Reputation & Progression

| File | Purpose |
|------|---------|
| `reputation_system.py` | Reputation and titles |
| `skill_revelation_system.py` | Skill revelation |
| `progressive_discovery_system.py` | Progressive discovery |

---

## 📝 Context & Memory

| File | Purpose |
|------|---------|
| `persistent_context_manager.py` | Never lose context |
| `context_injection_helper.py` | Context injection |
| `narrative_context_system.py` | Narrative context (root level) |
| `key_memories_system.py` | Key memories storage |
| `automatic_memory_creation.py` | Automatic memory creation |

---

## 🔧 Utilities

| File | Purpose |
|------|---------|
| `openrouter_config.py` | LLM client configuration |
| `color_utils.py` | Console color utilities |
| `json_utils.py` | JSON parsing utilities |
| `numeric_utils.py` | Numeric utilities |
| `label_utils.py` | Label normalization |
| `narrative_utils.py` | Narrative utilities |
| `storage_utils.py` | Storage utilities |
| `pronoun_resolution.py` | Pronoun resolution |
| `worldbuilding_helpers.py` | Worldbuilding helpers |

---

## 🎮 Other Active Systems

| File | Purpose |
|------|---------|
| `vessel_selection_system.py` | Character/vessel selection |
| `inquiry_system.py` | Inquiry handling |
| `inquiry_helpers.py` | Inquiry utilities |
| `inquiry_generation_order.py` | Inquiry generation |
| `failure_narrative_generator.py` | Failure narratives |
| `failure_tracker.py` | Failure tracking |
| `journey_chunking_system.py` | Travel chunking |
| `ally_coordination_system.py` | Ally coordination |
| `mode_transition_enhancer.py` | Mode transitions |
| `tone_consistency_validator.py` | Tone validation |
| `severity_validation.py` | Severity validation |
| `action_type_detector.py` | Action type detection |
| `dynamic_actor_justification.py` | Dynamic actor justification |
| `dynamic_actor_system.py` | Dynamic actor system |
| `encounter_checker.py` | Encounter checking |
| `partial_action_system.py` | Partial action handling |
| `outlier_stats_display.py` | Outlier stats display |
| `save_coordinator.py` | Save coordination |
| `config.py` | Configuration |

---

## 🗑️ Dead Code (Moved to TRASH BIN)

The following files have been moved to `TRASH BIN/` as they are no longer used:

| File | Reason |
|------|--------|
| `spark_generator.py` | Superseded by `agents/storyteller_agent.py` |
| `round_manager.py` | Superseded by `enhanced_round_manager.py` |
| `reporter.py` | Superseded by `enhanced_reporter.py` |
| `spatial_map_display.py` | Superseded by `pygame_spatial_map.py` |
| `spatial_display_integration.py` | Superseded by `pygame_spatial_map.py` |
| `utas_narrative_formula.py` (root) | Duplicate of `llm_agents/utas_narrative_formula.py` |
| `sympathy_initialization.py` (root) | Duplicate of `llm_agents/sympathy_initialization.py` |
| `nua_context_system.py` (root) | Duplicate of `llm_agents/nua_context_system.py` |

---

## 📌 Key Principles

1. **RAG is the single source of truth** for all worldbuilding/lore
2. **No hardcoded time periods, settings, or lore** in any active code
3. **All narrative outputs** use UA sensory perspective
4. **Never invent dialogue** for the user
5. **Concrete details** are tracked for consistency
6. **Regeneration on violations** - Sweeping actions and describing-not-thinking trigger retries

---

## 🔄 Maintenance

When adding new files:
1. Add them to the appropriate section above
2. Indicate RAG integration status
3. If replacing old code, move old code to TRASH BIN

When deprecating files:
1. Move to TRASH BIN folder
2. Add to "Dead Code" section above
3. Update any imports that referenced the old file
