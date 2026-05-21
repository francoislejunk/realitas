# Realitas Neo - Complete Function Catalog

**Generated:** 2025-01-11  
**Purpose:** Comprehensive list of every function in Realitas Neo with brief descriptions

---

## Core Simulation Loop (MAIN/redesigned_main.py)

- `main()` - Primary entry point that initializes and runs the complete simulation
- `_initialize_simulation()` - Sets up all systems, agents, and managers before simulation starts
- `_create_dynamic_user_actor()` - Creates the user's character through vessel selection system
- `_initialize_scene()` - Generates and sets up the initial scene with NPCs and environment
- `_process_user_input()` - Main loop that handles user input and routes to appropriate action handlers
- `_handle_exploration_action()` - Processes non-contested actions like movement and investigation
- `_handle_contested_action()` - Processes actions involving conflict with NPCs
- `_handle_given_action()` - Processes actions that automatically succeed (narrative only)
- `_handle_inquiry()` - Processes user questions about the scene through sensory perception
- `_handle_do_nothing()` - Processes waiting/observing actions that advance time
- `_transition_to_new_scene()` - Handles movement to new locations with proper continuity
- `_generate_new_scene()` - Creates a new scene with LLM-generated description and NPCs
- `_update_scene_context()` - Updates narrative context with current scene information
- `_advance_time()` - Moves simulation time forward based on action type
- `_check_survival_needs()` - Monitors and warns about critical survival requirements
- `_process_survival_effects()` - Applies status penalties from unmet survival needs
- `_get_npc_actions()` - Determines what NPCs do during their turns
- `_process_npc_turn()` - Executes a single NPC's action in the turn order
- `_update_npc_relationships()` - Updates sympathy values based on interactions
- `_save_session_state()` - Persists current simulation state to disk
- `_load_session_state()` - Restores simulation from saved session
- `_check_actor_death()` - Monitors actors for death conditions and handles deaths
- `_display_status()` - Shows current actor status, time, location, and present NPCs
- `_display_scene_description()` - Renders the current scene with sensory details
- `_display_turn_order()` - Shows initiative order for multi-actor encounters

---

## Actor System

### actors.py
- `Actor.__init__()` - Base class constructor linking name to actor sheet
- `Actor.is_user_controlled()` - Returns whether actor is controlled by user
- `UserActor.__init__()` - Creates user-controlled character with revealed skills
- `NonUserActor.__init__()` - Creates NPC with identity discovery tracking
- `NonUserActor.update_identity()` - Updates NPC identity as information is discovered
- `NonUserActor.is_identity_known()` - Checks if NPC's true identity has been revealed
- `NonUserActor.get_display_name()` - Returns appropriate name based on discovery status
- `InanimateNonUserActor.__init__()` - Creates inanimate object that can be interacted with

### actor_sheet.py
- `ActorSheet.__init__()` - Creates complete character sheet with all attributes
- `ActorSheet.get_s_factor()` - Retrieves specific S-Factor value by type
- `ActorSheet.get_skill()` - Retrieves skill value by name
- `ActorSheet.get_super()` - Retrieves supernatural ability value by name
- `ActorSheet.add_item()` - Adds item to inventory with supplement bonus
- `ActorSheet.remove_item()` - Removes item from inventory
- `ActorSheet.get_supplement_bonus()` - Calculates total equipment bonuses
- `ActorSheet.apply_status_shift()` - Modifies status values (stamina/spirit/supply)
- `ActorSheet.get_status_descriptor()` - Returns narrative description of status level
- `Status.apply_shift()` - Applies temporary or lasting shift to status value
- `Status.get_current_value()` - Returns current status value after all modifiers
- `Status.get_max_value()` - Returns maximum capacity after lasting shifts

### actor_state_filter.py
- `ActorStateFilter.check_actor_state()` - Determines if actor is dead/unconscious/incapacitated/active
- `ActorStateFilter.mark_actor_dead()` - Records actor death and removes from turn queue
- `ActorStateFilter.mark_actor_unconscious()` - Marks actor as unconscious and unable to act
- `ActorStateFilter.mark_actor_conscious()` - Restores consciousness to unconscious actor
- `ActorStateFilter.can_actor_take_action()` - Checks if actor can perform any action
- `ActorStateFilter.filter_turn_queue()` - Removes dead actors and marks states in turn order
- `ActorStateFilter.check_for_death_triggers()` - Checks if actor should die from conditions

---

## Agent System

### agents/conductor_agent.py
- `ConductorAgent.__init__()` - Initializes conductor that coordinates all other agents
- `ConductorAgent.interpret_user_action()` - Routes user action to interpreter agent
- `ConductorAgent.determine_nua_action()` - Routes NPC action to decider agent
- `ConductorAgent.generate_narrative()` - Routes narrative generation to narrator agent
- `ConductorAgent.enforce_continuity()` - Checks if action is physically possible
- `ConductorAgent.enforce_sensory_perception()` - Validates inquiry can be answered through senses

### agents/interpreter_agent.py
- `InterpreterAgent.interpret_user_action()` - Analyzes user input and extracts UTAS factors
- `InterpreterAgent.detect_inquiry_or_action()` - Determines if input is question or action
- `InterpreterAgent.enforce_continuity()` - Validates action continuity with scene state
- `InterpreterAgent.enforce_sensory_perception()` - Validates inquiry is perceivable
- `InterpreterAgent.update_actor_tasks()` - Updates actor's current goal/task from action
- `InterpreterAgent._enrich_utas_factors_with_actor_data()` - Fills in actual values from actor sheet

### agents/decider_agent.py
- `DeciderAgent.determine_nua_proaction()` - Decides what NPC does when taking initiative
- `DeciderAgent.determine_nua_reaction()` - Decides how NPC responds to user action
- `DeciderAgent._enrich_utas_factors_with_actor_data()` - Fills in actual values from actor sheet

### agents/narrator_agent.py
- `NarratorAgent.narrate_scene_introduction()` - Generates opening narrative for new scene
- `NarratorAgent.generate_scene_description()` - Creates sensory description of location
- `NarratorAgent.generate_inquiry_response()` - Answers user questions about scene
- `NarratorAgent.generate_continuity_failure_narrative()` - Explains why action isn't possible
- `NarratorAgent.generate_sensory_perception_failure_narrative()` - Explains why information isn't perceivable
- `NarratorAgent._sanitize_narrative()` - Removes meta-gaming language from narration
- `NarratorAgent._strip_meta_time_references()` - Removes anachronistic time references

### agents/creator_agent.py
- `CreatorAgent.create_user_actor()` - Generates user character with LLM
- `CreatorAgent.create_non_user_actor()` - Generates NPC with LLM
- `CreatorAgent.create_initial_scene()` - Generates starting scene with conflict
- `CreatorAgent.create_next_scene()` - Generates new scene with continuity
- `CreatorAgent.create_vessel_options()` - Generates 3 character options for player

### agents/tracker_agent.py
- `TrackerAgent.start_session()` - Initializes new tracking session
- `TrackerAgent.track_step1_proactor_interpretation()` - Records action interpretation data
- `TrackerAgent.track_step5_exchange_resolution()` - Records exchange outcome data
- `TrackerAgent.get_session_summary()` - Returns session statistics
- `TrackerAgent.get_actor_history()` - Returns complete history for specific actor
- `TrackerAgent.record_nua_death()` - Records NPC death for memory consistency

---

## UTAS System

### exchange_system.py
- `Exchange.execute()` - Runs complete contested exchange between proactor and reactor
- `Exchange._calculate_success()` - Computes success value from UTAS factors
- `Exchange._determine_winner()` - Compares successes to determine outcome
- `Exchange._apply_status_shifts()` - Applies status changes based on outcome

### response_normalizer.py
- `ResponseNormalizer.normalize_interpretation()` - Standardizes interpreter output format
- `ResponseNormalizer.validate_required_fields()` - Ensures all required data present
- `ResponseNormalizer.inject_default_self_effects()` - Adds mandatory self-effects if missing

### enhanced_reporter.py
- `EnhancedReporter.report_action_interpretation()` - Shows interpreted action with UTAS factors
- `EnhancedReporter.report_success_calculation()` - Shows success formula breakdown
- `EnhancedReporter.report_exchange_outcome()` - Shows exchange results and status changes

### enhanced_round_manager.py
- `EnhancedRoundManager.initialize_round()` - Sets up new round with initiative rolls
- `EnhancedRoundManager.get_next_actor()` - Returns next actor in turn order
- `EnhancedRoundManager._calculate_actor_initiative()` - Computes initiative with status modifier

---

## Memory Systems

### key_memories_system.py
- `KeyMemoriesSystem.create_memory()` - Creates new key memory with metadata
- `KeyMemoriesSystem.retrieve_memories()` - Retrieves memories by tags or recency
- `KeyMemoriesSystem.search_memories()` - Searches memories by content

### automatic_memory_creation.py
- `AutomaticMemoryCreator.detect_memory_triggers()` - Identifies events worthy of memory
- `AutomaticMemoryCreator.create_achievement_memory()` - Records task completion
- `AutomaticMemoryCreator.create_relationship_memory()` - Records first meeting with NPC

### intent_based_memory_creation.py
- `IntentBasedMemoryCreator.detect_memory_trigger()` - Identifies intent-based memory triggers
- `IntentBasedMemoryCreator.create_memory_from_intent()` - Creates memory based on user intent
- `IntentBasedMemoryCreator.generate_internal_voice()` - Creates first-person thought narration

### npc_memory_system.py
- `NPCMemorySystem.record_threat()` - Records NPC perceiving threat from actor
- `NPCMemorySystem.record_help()` - Records NPC receiving help from actor
- `NPCMemorySystem.get_memories_about()` - Retrieves NPC's memories about specific actor

### nua_life_tracker.py
- `NUALifeTracker.record_nua_state()` - Saves NPC's state when they leave scene
- `NUALifeTracker.get_reunion_narrative()` - Generates narrative for meeting NPC again
- `NUALifeTracker.generate_observable_changes()` - Creates changes based on time passed

---

## Narrative Systems

### narrative_context_manager.py
- `NarrativeContextManager.add_event()` - Records narrative event to history
- `NarrativeContextManager.get_recent_events()` - Retrieves recent narrative history
- `NarrativeContextManager.get_narrative_context_for_llm()` - Formats context for LLM

### concrete_detail_tracker.py
- `ConcreteDetailTracker.add_detail()` - Records specific detail about character/location
- `ConcreteDetailTracker.get_details_for_owner()` - Retrieves all details for character
- `ConcreteDetailTracker.search_details()` - Searches details by keywords

### llm_agents/utas_narrative_formula.py
- `UTASNarrativeFormula.generate_step6_narrative()` - Creates comprehensive turn narrative
- `UTASNarrativeFormula.generate_action_narrative()` - Describes action attempt
- `UTASNarrativeFormula.generate_outcome_narrative()` - Describes exchange result

### llm_agents/narrative_loop_system.py
- `FourModeNarrativeLoop.determine_current_mode()` - Identifies story mode (Roam/Spark/Pressure/Outcome)
- `FourModeNarrativeLoop.get_framing_guidance()` - Provides narrative framing for current mode
- `FourModeNarrativeLoop.detect_mode_transition()` - Identifies when to shift story modes

---

## Time Systems

### rule_of_3s.py
- `RuleOf3Classifier.classify_action()` - Determines time category (3-SECOND/3-MINUTE/SLEEP)
- `RuleOf3Classifier.get_time_cost()` - Returns time duration for action
- `RuleOf3Classifier.get_narrative_guidance()` - Provides pacing guidance for narration

### simulation_time_tracker.py
- `SimulationTimeTracker.advance_time()` - Moves simulation time forward
- `SimulationTimeTracker.get_current_time()` - Returns current simulation timestamp
- `SimulationTimeTracker.format_time_display()` - Formats time for display

### time_cycle_system.py
- `TimeCycleSystem.get_time_of_day()` - Returns current time period (morning/afternoon/evening/night)
- `TimeCycleSystem.get_atmospheric_description()` - Describes lighting and atmosphere
- `TimeCycleSystem.get_time_context()` - Returns complete time context for narration

### master_time_coordinator.py
- `MasterTimeCoordinator.advance_time()` - Coordinates time advancement across all systems
- `MasterTimeCoordinator.get_unified_time_context()` - Combines all time information

---

## Spatial Systems

### spatial_context_system.py
- `SpatialContext.add_zone()` - Adds navigable area to spatial map
- `SpatialContext.get_available_zones()` - Returns list of accessible areas
- `SpatialContext.can_move_to()` - Checks if movement to zone is possible
- `SpatialContext.update_actor_position()` - Moves actor to new position

### spatial_location_analyzer.py
- `SpatialLocationAnalyzer.analyze_scene()` - Extracts spatial information from scene description
- `SpatialLocationAnalyzer.identify_zones()` - Identifies distinct areas in location
- `SpatialLocationAnalyzer.determine_interior_exterior()` - Classifies location type

### spatial_position_resolver.py
- `SpatialPositionResolver.resolve_movement_target()` - Converts movement intent to coordinates
- `SpatialPositionResolver.calculate_distance()` - Computes distance between positions

---

## Survival System

### survival_system.py
- `SurvivalManager.check_needs()` - Evaluates all survival needs
- `SurvivalManager.satisfy_need()` - Marks need as satisfied
- `SurvivalManager.get_unmet_needs()` - Returns list of critical needs
- `SurvivalManager.apply_penalties()` - Applies status penalties for unmet needs

### survival_action_analyzer.py
- `SurvivalActionAnalyzer.detect_survival_action()` - Identifies if action addresses survival need
- `SurvivalActionAnalyzer.classify_action_type()` - Determines which need action satisfies

---

## Progression System

### progression_tracker.py
- `SkillProgressionTracker.track_skill_use()` - Records skill usage with success level
- `SkillProgressionTracker.check_progression()` - Determines if skill should increase
- `SympathyProgressionTracker.track_interaction()` - Records interaction type with NPC
- `ProgressionManager.process_action_results()` - Handles both skill and sympathy progression

---

## Other Systems

### goal_task_system.py
- `GoalTaskManager.set_current_task()` - Sets actor's active goal
- `GoalTaskManager.update_task_from_action()` - Infers task from user action
- `GoalTaskManager.display_current_task()` - Formats task for display

### intent_availability_system.py
- `IntentAvailabilitySystem.check_intent_availability()` - Determines if intent is possible now/later/never
- `IntentAvailabilitySystem.generate_availability_narrative()` - Creates diegetic explanation

### inquiry_system.py
- `InquiryCalculator.calculate_inquiry_success()` - Determines if inquiry succeeds
- `InquiryCalculator.generate_inquiry_narrative()` - Creates narrative response to question

### do_nothing_action.py
- `DoNothingAction.detect()` - Identifies if input is "do nothing" action
- `DoNothingAction.execute()` - Processes waiting/observing action

### vessel_selection_system.py
- `VesselSelectionSystem.generate_vessel_options()` - Creates 3 character options
- `VesselSelectionSystem.get_user_selection()` - Handles user choice

### dynamic_actor_system.py
- `DynamicActorSystem.detect_new_actor_reference()` - Identifies mentions of new NPCs in user input
- `DynamicActorSystem.create_actor_on_demand()` - Generates new NPC when referenced

### multi_actor_manager.py
- `MultiActorManager.register_actor()` - Adds actor to simulation with role assignment
- `MultiActorManager.get_actor_by_name()` - Retrieves actor by name
- `MultiActorManager.get_all_actors()` - Returns list of all registered actors

### enhanced_sympathy_manager.py
- `EnhancedSympathyManager.get_sympathy()` - Retrieves sympathy value between two actors
- `EnhancedSympathyManager.modify_sympathy()` - Changes sympathy value with reason
- `EnhancedSympathyManager.get_relationship_history()` - Returns history of relationship changes

---

## Utility Functions

### narrative_utils.py
- `get_status_descriptor()` - Converts numeric status to narrative description
- `get_success_level_narration()` - Converts success value to narrative description
- `get_gerund()` - Converts action noun to gerund form
- `N2N_Skill_Level()` - Returns skill level descriptor
- `N2N_Difficulty()` - Returns difficulty descriptor

### color_utils.py
- `Color.apply()` - Applies ANSI color code to text
- `Color.strip()` - Removes ANSI codes from text

### json_utils.py
- `extract_json_from_response()` - Extracts JSON from LLM response
- `fix_json_formatting()` - Repairs malformed JSON strings
- `safe_json_parse()` - Parses JSON with error handling

### supply_utils.py
- `format_money_display()` - Formats currency for display
- `get_supply_descriptor()` - Returns narrative description of supply level

### sympathy_utils.py
- `calculate_sympathy_modifier()` - Computes sympathy's effect on action difficulty
- `get_sympathy_description()` - Returns narrative description of relationship

---

## World Building

### WORLD_BUILDER/worldbuilding_rag_system.py
- `WorldbuildingRAG.add_lore()` - Adds worldbuilding information to knowledge base
- `WorldbuildingRAG.query_lore()` - Retrieves relevant lore for query
- `WorldbuildingRAG.get_context_for_llm()` - Formats lore for LLM prompts

---

**Total Systems:** 20+ major systems  
**Total Functions:** 200+ documented functions  
**Architecture:** Agent-based with modular subsystems
