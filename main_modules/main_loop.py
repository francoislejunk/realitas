"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
import colorama
import threading
import traceback
try:
    import msvcrt
except Exception:
    msvcrt = None
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path
from logbook.utas_logger import UTASLogger
from actor_sheet import ActorSheet, SFactors, Item, StatusType
from actors import Actor, UserActor, NonUserActor
from agents.conductor_agent import ConductorAgent
from agents.creator_agent import CreatorAgent
from agents.narrator_agent import NarratorAgent
from multi_actor_manager import MultiActorManager, ActorRole
from enhanced_round_manager import EnhancedRoundManager
from enhanced_reporter import EnhancedReporter
from enhanced_dynamic_actor_system import EnhancedDynamicActorSystem, EnhancedDynamicActorDetector
from enhanced_sympathy_system import EnhancedSympathyManager
from enhanced_temporary_recovery_system import EnhancedTemporaryRecoveryIntegrator
from color_utils import Color
from agents.tracker_agent import TrackerAgent
from llm_agents.scene_manager import SceneManager
from llm_agents.encounter_checker import EncounterChecker
from llm_agents.sympathy_initialization import assign_initial_sympathies
from llm_agents.nua_context_system import NUAContextManager
from diegetic_transition_system import DiegeticTransitionSystem, display_diegetic_pause
from dotenv import load_dotenv
from narrative_utils import get_serendipity_descriptor, get_narrative_descriptor, get_success_level_narration
from label_utils import normalize_sfactor_label
from rule_of_3s import RuleOf3Classifier, RuleOf3Category
from survival_system import SurvivalManager, SurvivalNeed
from survival_actions import get_critical_survival_actions
from survival_action_analyzer import survival_analyzer
from time_cycle_system import TimeCycleTracker, TimeOfDay, get_time_display_name
from reactor_time_system import ReactorTimeManager, create_time_expired_result, ActionSpeed, display_time_budget_info
from scene_continuity_validator import continuity_validator
from ally_coordination_system import ally_coordinator
from time_lighting_updater import time_lighting_updater
from world_spatial_integration import handle_world_spatial_command, get_world_context_for_narrator
from persistent_context_manager import get_context_manager
from context_injection_helper import (
    update_context_after_action,
    update_context_after_scene_change,
    update_context_npcs
)
from inventory_manager import InventoryManager
from location_distance_tracker import get_location_tracker, LocationType, TravelMethod
from intent_availability_system import IntentAvailabilitySystem, IntentAvailability
from do_nothing_action import DoNothingAction, check_and_execute_do_nothing
from progression_tracker import ProgressionManager, InteractionType
from progression_integration_helper import process_and_display_progression
from goal_progress_tracker import GoalProgressTracker, process_goal_progress, display_goal_progress_update
from intent_based_memory_creation import IntentBasedMemoryCreator, display_memory_creation
from diegetic_transition_system import DiegeticTransitionSystem, IntentScope, display_diegetic_pause, display_atomic_experience
from enhanced_monetary_system import EnhancedMonetaryProcessor
from WORLD_BUILDER.worldbuilding_rag import WorldbuildingRAGSystem, WorldbuildingCategory
from key_memories_system import initialize_key_memories, get_key_memories, handle_memory_command, MemoryCategory
from mention_system import MentionSystem
from npc_memory_system import initialize_nua_memory_system
from automatic_memory_creation import initialize_automatic_memory_creator
from llm_agents.scene_event_scheduler import SceneEventScheduler
from master_time_coordinator import MasterTimeCoordinator, initialize_master_time_coordinator, get_master_time_coordinator, TimeAdvancementRequest, TimeEventType
from narrative_context_system import NarrativeContextManager
from save_coordinator import SaveCoordinator
from simulation_time_tracker import SimulationTimeTracker
from vessel_selection_system import VesselSelectionSystem
from actors import ActorCategory, get_actor_category, can_graduate_to_mnua
from actors import get_s_trait_outliers, format_outliers_for_narrative
from sensing_bubble_system import (
    SensingBubbleCalculator, 
    SenseType,
    select_priority_senses,
    format_sensing_for_prompt
)
from internal_voice_system import (
    InternalVoiceSystem,
    get_internal_voice_cue,
    should_trigger_voice_cue
)
from agents.internal_voice_interpreter_agent import (
    InternalVoiceInterpreterAgent,
    VoiceInterpretation,
    InternalVoiceFunction
)
from agents.internal_voice_creator_agent import (
    InternalVoiceCreatorAgent,
    get_voice_creator,
    generate_internal_voice as new_generate_internal_voice,
    display_internal_voice
)
from agents.storyteller_agent import (
    StorytellerAgent,
    Spark,
    SparkType,
    display_spark,
    display_exchange_outcomes
)
from reputation_system import (
    ReputationSystem,
    get_reputation_system,
    check_for_title,
    display_title_earned
)
from concrete_detail_tracker import ConcreteDetailTracker
from agents.decider_agent import DeciderAgent
from dialogue_context_system import DialogueContextSystem, DialogueContext
from diegetic_clue_tracker import DiegeticClueTracker, ClueType
from failure_narrative_generator import FailureNarrativeGenerator
from goal_task_system import GoalTaskManager
from nua_life_tracker import NUALifeTracker, NUALifeState
from personality_mood_system import PersonalityGenerator, MoodAnalyzer, CompletePersonalityProfile
from stranger_description_system import StrangerDescriber, get_nua_description, detect_name_introduction, learn_npc_name
from sympathy_behavior_modifier import SympathyBehaviorModifier
from tactical_awareness_system import TacticalAwarenessSystem
from witness_reaction_system import WitnessReactionSystem
from llm_agents.enhanced_narrative_loop import EnhancedNarrativeLoop
from tactical_awareness_system import TacticalAwarenessSystem
from object_registry import get_object_state, set_status, get_status
from failure_narrative_generator import FailureNarrativeGenerator
from sympathy_behavior_modifier import SympathyBehaviorModifier
from pygame_spatial_map import (
    init_pygame_map_for_simulation,
    update_map_actor,
    remove_map_actor,
    get_sensing_data_from_map,
    get_perceivable_actors_for_narrative,
    stop_pygame_map,
    auto_sync_map,
    set_map_context,
    get_map_data_for_rag,
    get_actor_details,
    toggle_auto_zoom,
    toggle_follow_ua,
    get_obstacle_names_for_narrative,
    get_nearby_obstacles
)
from misc import (
    CTX_SUMMARY_MAX_CHARS,
    _create_dynamic_user_actor,
    _create_quick_test_actor,
    _build_reactor_sheet_data,
    _generate_connected_roam_scene,
    _clamp_text,
    _ensure_min_utas_fields,
    _drain_windows_keyboard_buffer,
    _win_readline,
    _convert_ua_to_second_person,
    _ua_display_name,
    get_sensing_calculator,
    get_actor_introduction_with_outliers,
    check_and_award_title,
    _calculate_detailed_success,
    get_nua_life_changes,
    record_nua_last_seen,
    detect_environmental_clues,
    get_tactical_recommendation,
    generate_failure_narrative,
    get_object_status,
    set_object_status,
    update_pygame_map_actors,
    _env_bool,
    SUPPRESS_DEBUG,
    REDESIGNED_VERBOSITY,
    ENABLE_INTENT_AVAILABILITY,
    SPARK_FADE_TURNS,
    SPARK_FADE_HOURS,
)

def _autostart_pmap(tracker) -> None:
    try:
        if not tracker or not getattr(tracker, 'session_id', None):
            return
        from pygame_spatial_map import start_pygame_map, sync_from_spatial_context, sync_world_graph, get_pygame_map
        if start_pygame_map():
            sync_from_spatial_context(session_id=tracker.session_id)
            try:
                sync_world_graph(tracker.session_id)
            except Exception:
                pass
            try:
                _ = get_pygame_map()
            except Exception:
                pass
    except Exception:
        return

# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATED SYSTEMS HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global sensing bubble calculator
_sensing_calculator = None



def init_immersion_systems(storage_dir: Path):
    """
    Initialize additional immersion systems.
    
    Called during simulation startup after core systems.
    """
    global _witness_system, _stranger_describer, _dialogue_context, _personality_generator, _mood_analyzer
    global _nua_life_tracker, _clue_tracker, _tactical_awareness, _failure_narrator, _sympathy_modifier
    
    systems_initialized = []
    
    # 1. Witness Reaction System
    if WITNESS_SYSTEM_AVAILABLE:
        try:
            _witness_system = WitnessReactionSystem()
            systems_initialized.append("Witness Reactions")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Witness system init failed: {e}{Color.RESET}")
    
    # 2. Stranger Description System
    if STRANGER_DESCRIPTION_AVAILABLE:
        try:
            _stranger_describer = StrangerDescriber()
            systems_initialized.append("Stranger Descriptions")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Stranger describer init failed: {e}{Color.RESET}")
    
    # 3. Dialogue Context System
    if DIALOGUE_CONTEXT_AVAILABLE:
        try:
            _dialogue_context = DialogueContextSystem()
            systems_initialized.append("Dialogue Context")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Dialogue context init failed: {e}{Color.RESET}")
    
    # 4. Personality & Mood System
    if PERSONALITY_MOOD_AVAILABLE:
        try:
            _personality_generator = PersonalityGenerator()
            _mood_analyzer = MoodAnalyzer()
            systems_initialized.append("Personality/Mood")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Personality/mood init failed: {e}{Color.RESET}")
    
    # 5. NUA Life Tracker
    if NUA_LIFE_TRACKER_AVAILABLE:
        try:
            _nua_life_tracker = NUALifeTracker(storage_dir=storage_dir)
            systems_initialized.append("NUA Life Tracker")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ NUA life tracker init failed: {e}{Color.RESET}")
    
    # 6. Diegetic Clue Tracker
    if CLUE_TRACKER_AVAILABLE:
        try:
            _clue_tracker = DiegeticClueTracker()
            systems_initialized.append("Clue Tracker")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Clue tracker init failed: {e}{Color.RESET}")
    
    # 7. Tactical Awareness System
    if TACTICAL_AWARENESS_AVAILABLE:
        try:
            _tactical_awareness = TacticalAwarenessSystem()
            systems_initialized.append("Tactical Awareness")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Tactical awareness init failed: {e}{Color.RESET}")
    
    # 8. Failure Narrative Generator
    if FAILURE_NARRATIVE_AVAILABLE:
        try:
            _failure_narrator = FailureNarrativeGenerator()
            systems_initialized.append("Failure Narratives")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Failure narrator init failed: {e}{Color.RESET}")
    
    # 9. Sympathy Behavior Modifier
    if SYMPATHY_MODIFIER_AVAILABLE:
        try:
            _sympathy_modifier = SympathyBehaviorModifier()
            systems_initialized.append("Sympathy Modifier")
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Sympathy modifier init failed: {e}{Color.RESET}")
    
    # 10. Object Registry is module-level, no init needed
    if OBJECT_REGISTRY_AVAILABLE:
        systems_initialized.append("Object Registry")
    
    if systems_initialized:
        print(f"{Color.SUCCESS}✓ Immersion systems ready: {', '.join(systems_initialized)}{Color.RESET}")
    else:
        print(f"{Color.WARNING}⚠️ No additional immersion systems available{Color.RESET}")
    
    return len(systems_initialized)




def main():
    """
    Main function to run the redesigned UTAS simulation with solo exploration
    and automatic SPARK generation.
    """
    _dotenv_path = None
    _dotenv_loaded = None
    _dotenv_error = None
    try:
        _dotenv_path = (Path(__file__).resolve().parent.parent / ".env")
        _dotenv_loaded = load_dotenv(dotenv_path=_dotenv_path, override=True)
    except Exception as e:
        _dotenv_error = e
        try:
            _dotenv_loaded = load_dotenv(override=True)
        except Exception:
            _dotenv_loaded = None

    try:
        _img_debug = _env_bool("VIS_IMAGE_DEBUG", False)
        _img_autogen = _env_bool("VIS_IMAGE_AUTOGEN", True)
        _img_enabled = _env_bool("VIS_IMAGE_ENABLED", True)
        _vid_enabled = _env_bool("VIS_VIDEO_ENABLED", False)
        _model = os.getenv("FAL_IMAGE_MODEL") or ""
        _has_key = bool(os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY"))
        print(
            f"{Color.SYSTEM}🖼️ VIS: env image_enabled={_img_enabled} image_autogen={_img_autogen} image_debug={_img_debug} "
            f"video_enabled={_vid_enabled} model={_model} has_fal_key={_has_key}{Color.RESET}"
        )

        # If the expected vars aren't showing up, emit extra diagnostics.
        if not _img_debug or not _model:
            try:
                _raw_debug = os.getenv("VIS_IMAGE_DEBUG")
                _raw_model = os.getenv("FAL_IMAGE_MODEL")
                _path_str = str(_dotenv_path) if _dotenv_path is not None else ""
                _path_exists = _dotenv_path.exists() if _dotenv_path is not None else False
                _err_str = str(_dotenv_error) if _dotenv_error is not None else ""
                print(
                    f"{Color.WARNING}🖼️ VIS: dotenv path='{_path_str}' exists={_path_exists} loaded={_dotenv_loaded} err='{_err_str}' "
                    f"raw_VIS_IMAGE_DEBUG={_raw_debug!r} raw_FAL_IMAGE_MODEL={_raw_model!r}{Color.RESET}"
                )
            except Exception:
                pass
    except Exception:
        pass

    try:
        if _env_bool("VIS_VIEWER_ENABLED", True) and _env_bool("VIS_IMAGE_ENABLED", True):
            _maybe_start_visualizer_viewer()
            try:
                _host = os.getenv("VIS_VIEWER_HOST") or "127.0.0.1"
                _port = os.getenv("VIS_VIEWER_PORT") or "8765"
                print(f"{Color.SYSTEM}🖼️ VIS: viewer URL http://{_host}:{_port}/{Color.RESET}")
            except Exception:
                pass
    except Exception:
        pass
    colorama.init()
    logger = UTASLogger()
    logger.log_system("UTAS simulation started with redesigned exploration system.")

    tracker = TrackerAgent()
    
    # NOTE: context_manager will be initialized AFTER session selection to use correct session ID
    context_manager = None  # Placeholder - initialized after session is selected/loaded
    
    # FIX BUG #9: Helper function to always get current scene description
    def get_current_scene() -> str:
        """Get the current scene description from persistent context, fallback to scene_description variable."""
        if context_manager and hasattr(context_manager.context, 'current_scene_description') and context_manager.context.current_scene_description:
            return context_manager.context.current_scene_description
        return scene_description if 'scene_description' in locals() or 'scene_description' in globals() else ""
    
    # Quick exchange mode: skip session menu
    if hasattr(__builtins__, 'QUICK_EXCHANGE_MODE') and __builtins__.QUICK_EXCHANGE_MODE:
        selected_session_id = 'new'
        print(f"{Color.SUCCESS}✓ Creating quick test session{Color.RESET}\n")
    else:
        selected_session_id = tracker.display_session_menu()
    
    resuming_session = False
    resume_scene_description = None
    resume_scene_elements = None
    resume_scene_number = None
    
    if selected_session_id == 'quit':
        print(f"{Color.SYSTEM}Goodbye!{Color.RESET}")
        return
    
    # Note: Actor creation, narrator, and conductor moved to after RAG initialization
    actor = None  # Will be initialized after RAG system is loaded
    narrator = None  # Will be initialized after RAG system is loaded
    conductor = None  # Will be initialized after narrator is created
    
    # Initialize monetary processor
    monetary_processor = EnhancedMonetaryProcessor(tracker_agent=tracker)
    
    # Initialize inventory manager
    from openrouter_config import OpenRouterConfig
    inventory_manager = InventoryManager(OpenRouterConfig.create_client())
    
    # Initialize narrative context manager
    storage_dir = Path("./simulation_data/narrative_context")
    storage_dir.mkdir(parents=True, exist_ok=True)
    session_id = getattr(tracker, 'session_id', 'default_session')
    
    from llm_agents.narrative_context_system import NarrativeContextManager, NarrativeEventType, NarrativeImportance
    from llm_agents.identity_manager import IdentityManager, integrate_identity_discovery_with_narrative
    narrative_context_manager = NarrativeContextManager(session_id, storage_dir)
    
    # Initialize root-level narrative context system with concrete details tracker
    from narrative_context_system import NarrativeContextManager as ConcreteDetailsManager
    concrete_details_manager = ConcreteDetailsManager(session_id, storage_dir)
    print(f"{Color.INFO}📝 Initialized Concrete Details Tracker{Color.RESET}")
    
    # Initialize Intent Availability System (No Manifestation)
    print(f"{Color.INFO}🔒 Initializing Intent Availability System...{Color.RESET}")
    intent_system = IntentAvailabilitySystem(storage_dir)
    
    # Initialize Intent-Based Memory Creation System
    print(f"{Color.INFO}💭 Initializing Intent-Based Memory Creation...{Color.RESET}")
    intent_memory_creator = IntentBasedMemoryCreator(storage_dir)
    
    # Initialize Progression Manager (Skill & Sympathy)
    print(f"{Color.INFO}📈 Initializing Progression System...{Color.RESET}")
    progression_manager = ProgressionManager(storage_dir)
    
    # Initialize Goal Progress Tracker
    print(f"{Color.INFO}🎯 Initializing Goal Progress Tracker...{Color.RESET}")
    goal_progress_tracker = GoalProgressTracker()
    
    # Initialize Failure Tracker (for self-aware internal voice)
    print(f"{Color.INFO}🔄 Initializing Failure Tracker...{Color.RESET}")
    from failure_tracker import FailureTracker
    failure_tracker = FailureTracker(max_history=10)
    
    print(f"{Color.SUCCESS}✓ Immersion systems ready (Intent Availability + Memory Creation + Concrete Details + Progression + Goal Tracking + Failure Awareness){Color.RESET}")
    
    # Initialize Diegetic Transition System (will be fully initialized later with openrouter_config)
    transition_system = None
    
    # Initialize WORLD_BUILDER RAG System (Enhanced Worldbuilding RAG)
    print(f"{Color.INFO}📚 Initializing Enhanced Worldbuilding RAG System...{Color.RESET}")
    rag_dir_override = os.getenv("REALITAS_RAG_STORAGE_DIR", "").strip()
    rag_storage_dir = Path(rag_dir_override) if rag_dir_override else Path("./simulation_data/worldbuilding_rag")
    rag_system = WorldbuildingRAGSystem(rag_storage_dir)
    # Lore is loaded from realitas_lore.py - run that file to update worldbuilding
    # python WORLD_BUILDER/realitas_lore.py
    print(f"{Color.SUCCESS}✓ Loaded {len(rag_system.documents)} lore documents from worldbuilding database{Color.RESET}")
    print(f"{Color.SYSTEM}Worldbuilding RAG storage: {rag_storage_dir}{Color.RESET}")
    if len(rag_system.documents) == 0:
        print(f"{Color.WARNING}⚠️  No lore documents found! Build one via: python WORLD_BUILDER/realitas_lore.py{Color.RESET}")
    
    # Extract and set simulation year from RAG worldbuilding
    from worldbuilding_helpers import extract_current_year_from_rag, extract_year_range_from_rag
    from actor_sheet import ActorSheet
    year_range = extract_year_range_from_rag(rag_system)
    if year_range:
        start_year, end_year = year_range
        print(
            f"{Color.INFO}📅 Simulation year range detected: {start_year}-{end_year}. "
            f"Canonical year will be set during vessel creation.{Color.RESET}"
        )
    else:
        current_year = extract_current_year_from_rag(rag_system)
        if current_year:
            ActorSheet.set_simulation_year(current_year)
            print(f"{Color.SUCCESS}✓ Simulation year set to {current_year} from worldbuilding context{Color.RESET}")
        else:
            # No hardcoded fallback - let the vessel selection set the year
            print(f"{Color.WARNING}⚠️  Could not extract year from RAG, year will be set during vessel creation{Color.RESET}")
    
    # Initialize Key Memories System BEFORE vessel selection
    # This ensures initial memories can be saved during character creation
    print(f"{Color.INFO}💭 Initializing Key Memories System...{Color.RESET}")
    memories_storage_dir = Path("./simulation_data/memories")
    key_memories = initialize_key_memories(tracker.session_id, memories_storage_dir)
    print(f"{Color.SUCCESS}✓ Key Memories System ready{Color.RESET}")

    # Initialize Mention System for actor location/mention tracking
    print(f"{Color.INFO}📍 Initializing Mention System...{Color.RESET}")
    mentions_storage_dir = Path("./simulation_data/mentions")
    mentions_storage_dir.mkdir(parents=True, exist_ok=True)
    mention_system = MentionSystem(
        session_id=tracker.session_id,
        storage_directory=mentions_storage_dir
    )
    print(f"{Color.SUCCESS}✓ Mention System ready{Color.RESET}")

    # Initialize CreatorAgent with RAG system and mention system
    print(f"{Color.INFO}🎨 Initializing CreatorAgent with RAG integration...{Color.RESET}")
    scene_creator = CreatorAgent(logger, rag_system=rag_system, mention_system=mention_system)
    print(f"{Color.SUCCESS}✓ CreatorAgent ready with worldbuilding context{Color.RESET}")

    # Initialize NarratorAgent with RAG system and mention system
    print(f"{Color.INFO}📖 Initializing NarratorAgent with RAG integration...{Color.RESET}")
    narrator = NarratorAgent(rag_system=rag_system, mention_system=mention_system)
    print(f"{Color.SUCCESS}✓ NarratorAgent ready with worldbuilding context{Color.RESET}")

    # Initialize ConductorAgent with RAG system and mention system
    print(f"{Color.INFO}🎭 Initializing ConductorAgent with RAG integration...{Color.RESET}")
    conductor = ConductorAgent(logger, "Initial scene loading...", tracker_agent=tracker, rag_system=rag_system, mention_system=mention_system)
    print(f"{Color.SUCCESS}✓ ConductorAgent ready with worldbuilding context{Color.RESET}")

    # Update CreatorAgent with key_memories system for initial memory generation
    scene_creator.key_memories_system = key_memories
    
    # Handle session loading/creation (now that scene_creator exists)
    staged_loaded_npcs = []
    if selected_session_id and selected_session_id != 'new':
        # Try to load existing session
        if tracker.load_session(selected_session_id):
            restored_actors = tracker.restore_actors_from_session()
            if restored_actors and len(restored_actors) >= 1:
                actor = restored_actors[0] if isinstance(restored_actors[0], UserActor) else None
                if actor:
                    print(f"{Color.SUCCESS}✓ Session loaded: {_ua_display_name(actor, ua_actor=actor)}{Color.RESET}")
                    # Extract last scene and runtime resume state
                    try:
                        sim = tracker.session_data.get('simulation_session', {})
                        scenes = sim.get('scenes', [])
                        if scenes:
                            last_scene = scenes[-1]
                            resume_scene_number = last_scene.get('scene_number') or len(scenes)
                            sd = last_scene.get('scene_data', {})
                            resume_scene_elements = sd.get('scene_elements') or {}
                            resume_scene_description = sd.get('scene_description') or None
                        # Prefer runtime_state if present (more up-to-date than scene start snapshot)
                        runtime_state = tracker.get_runtime_resume_state() or {}
                        if runtime_state.get('scene_description'):
                            resume_scene_description = runtime_state.get('scene_description')
                        if runtime_state.get('scene_number'):
                            resume_scene_number = runtime_state.get('scene_number')
                        try:
                            resume_location_label = runtime_state.get('current_location')
                        except Exception:
                            resume_location_label = None
                        resuming_session = bool(resume_scene_description)
                    except Exception:
                        resuming_session = False

                    # Restore saved scene context + NUAs for continuity
                    try:
                        if resuming_session and resume_scene_description:
                            scene_description = resume_scene_description
                            try:
                                tracker.set_current_scene(scene_description, location_label=resume_location_label)
                            except Exception:
                                pass
                            try:
                                loaded_npcs = tracker.load_available_npcs() or []
                            except Exception:
                                loaded_npcs = []
                            try:
                                if loaded_npcs:
                                    # Stage loaded NPCs for later application (available_npcs is initialized later)
                                    staged_loaded_npcs = list(loaded_npcs)
                            except Exception:
                                pass
                    except Exception:
                        pass
                else:
                    print(f"{Color.ERROR}Failed to restore UserActor. Finding new vessel...{Color.RESET}")
                    actor = _create_dynamic_user_actor(scene_creator, rag_system)
                    tracker.start_session([actor])
            else:
                print(f"{Color.ERROR}Failed to restore actors. Finding new vessel...{Color.RESET}")
                actor = _create_dynamic_user_actor(scene_creator, rag_system)
                tracker.start_session([actor])
        else:
            print(f"{Color.ERROR}Failed to load session. Exiting.{Color.RESET}")
            return
    else:
        # Create new session - vessel selection returns actor WITHOUT memories
        actor, vessel_system = _create_dynamic_user_actor(scene_creator, rag_system, return_vessel_system=True)
        
        # Skip session name prompt in quick exchange mode
        if hasattr(__builtins__, 'QUICK_EXCHANGE_MODE') and __builtins__.QUICK_EXCHANGE_MODE:
            tracker.start_session([actor], "Quick Exchange Test")
            print(f"{Color.SUCCESS}✓ Quick test session created with {_ua_display_name(actor, ua_actor=actor)}{Color.RESET}")
        else:
            # Auto-name session from vessel identity (name + occupation)
            try:
                vessel_name = getattr(getattr(actor, 'sheet', None), 'name', None) or 'Unknown Vessel'
                vessel_occ = getattr(getattr(actor, 'sheet', None), 'occupation', None) or 'Unknown Occupation'
                session_name = f"{vessel_name} - {vessel_occ}"
            except Exception:
                session_name = None
            if session_name:
                tracker.start_session([actor], session_name)
                print(f"{Color.SUCCESS}✓ New session '{session_name}' created{Color.RESET}")
            else:
                tracker.start_session([actor])
                print(f"{Color.SUCCESS}✓ New session created with {_ua_display_name(actor, ua_actor=actor)}{Color.RESET}")
        
        # NOW create initial memories (after session naming)
        if vessel_system:
            vessel_system.create_memories_for_actor(actor)
    
    if not hasattr(tracker, 'session_data') or not tracker.session_data:
        print(f"{Color.WARNING}Warning: Tracker not properly initialized. Reinitializing...{Color.RESET}")
        tracker.start_session([actor])
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # CRITICAL FIX: Initialize context_manager AFTER session is loaded/created
    # This ensures we use the CORRECT session ID (not a new UUID)
    # ═══════════════════════════════════════════════════════════════════════════════
    from persistent_context_manager import reset_context_manager, sync_context_with_tracker, get_context_health_report
    reset_context_manager()  # Clear any stale global instance
    context_manager = get_context_manager(session_id=tracker.session_id)
    
    # Show context status
    if context_manager.context.update_count > 0:
        print(f"\n{Color.SUCCESS}[*] RESUMING FROM SAVED CONTEXT:{Color.RESET}")
        print(f"{Color.INFO}   Location: {context_manager.context.current_location}{Color.RESET}")
        print(f"{Color.INFO}   NUAs: {', '.join(context_manager.context.present_nuas) if context_manager.context.present_nuas else 'None'}{Color.RESET}")
        print(f"{Color.INFO}   Updates: {context_manager.context.update_count}{Color.RESET}")
        
        # If resuming session, sync context with tracker's scene description
        if resuming_session and resume_scene_description:
            if not context_manager.context.current_scene_description:
                context_manager.update_scene_description(resume_scene_description)
                print(f"{Color.INFO}   Scene synced from tracker{Color.RESET}")
        
        # Always attempt sync on resume to catch any missing data
        if resuming_session:
            sync_context_with_tracker(tracker)
            
            # Check context health after sync
            health = get_context_health_report()
            if health["status"] == "degraded":
                print(f"{Color.WARNING}⚠️ Context has issues - use '/context' to diagnose{Color.RESET}")
    else:
        print(f"\n{Color.INFO}Starting new session with fresh context{Color.RESET}")

    # Auto-start pygame map after session load/create
    _autostart_pmap(tracker)
    
    # NOTE: Key Memories System was initialized earlier (before vessel selection)
    # so that initial memories can be saved during character creation.
    # Initial memories are created by VesselSelectionSystem._create_initial_memories()
    # during vessel selection (24 memories via InternalVoiceCreatorAgent).
    
    # Initialize NUA Memory System
    print(f"{Color.INFO}🧠 Initializing NUA Memory System...{Color.RESET}")
    try:
        _sid = getattr(tracker, 'session_id', None) if tracker else None
        _sid = str(_sid) if _sid else 'default'
    except Exception:
        _sid = 'default'
    nua_memories_storage_dir = Path("./simulation_data/nua_memories") / _sid
    nua_memory_system = initialize_nua_memory_system(nua_memories_storage_dir)
    print(f"{Color.SUCCESS}✓ NUA Memory System ready (session-scoped){Color.RESET}")
    
    # Initialize Automatic Memory Creator
    print(f"{Color.INFO}✨ Initializing Automatic Memory Creator...{Color.RESET}")
    auto_memory_creator = initialize_automatic_memory_creator()
    print(f"{Color.SUCCESS}✓ Automatic Memory Creator ready{Color.RESET}")
    
    # Initialize Enhanced Four-Mode Narrative Loop (No Push Edition)
    from llm_agents.enhanced_narrative_loop import EnhancedNarrativeLoop, NarrativeMode
    from goal_task_system import GoalTaskManager, GoalImportance
    from openrouter_config import OpenRouterConfig
    from agents.background_simulation_system import BackgroundSimulationSystem, WorldEventType, ObservableEvent
    from agents.population_manager import PopulationManager
    
    # Initialize Goal/Task Manager
    goal_task_manager = GoalTaskManager()
    # Add initial goals from character creation if they exist
    if hasattr(actor.sheet, 'goals') and actor.sheet.goals:
        for goal_desc in actor.sheet.goals:
            goal_task_manager.add_goal(
                description=goal_desc,
                importance=GoalImportance.MAJOR
            )
    
    # Create enhanced narrative loop with no-push design
    narrative_loop = EnhancedNarrativeLoop(
        llm_client=OpenRouterConfig.create_client(),
        goal_task_manager=goal_task_manager
    )
    
    # Initialize identity manager and integrate with narrative system
    identity_manager = IdentityManager(narrative_context_manager)
    narrator = integrate_identity_discovery_with_narrative(narrator, identity_manager)
    
    # Connect narrative context manager to narrator agent and scene creator
    narrator.narrative_context_manager = concrete_details_manager  # Use concrete details manager for narrator
    scene_creator.narrative_context_manager = narrative_context_manager
    # Ensure Interpreter/Narrator under Conductor have access to full narrative context
    try:
        conductor.set_narrative_context_manager(narrative_context_manager)
    except Exception:
        pass

    # Initialize new systems for redesigned simulation
    encounter_checker = EncounterChecker()
    # SparkGenerator removed - using StorytellerAgent's spark system (MOMENTUM, EXCHANGE, CALLBACK) instead
    rule_of_3_classifier = RuleOf3Classifier()
    
    # Initialize Spatial Context System
    from spatial_context_system import get_spatial_manager, Position
    spatial = get_spatial_manager(session_id=tracker.session_id)
    print(f"{Color.INFO}[SPATIAL] Spatial context manager initialized for session: {tracker.session_id}{Color.RESET}")

    try:
        if resuming_session:
            desired_location = None
            try:
                rs = tracker.get_runtime_resume_state() if tracker else None
                if isinstance(rs, dict):
                    desired_location = rs.get('current_location') or rs.get('location')
            except Exception:
                desired_location = None

            try:
                if not desired_location:
                    desired_location = resume_location_label
            except Exception:
                pass

            try:
                if not desired_location:
                    desired_location = getattr(spatial, 'current_location', None)
            except Exception:
                pass

            try:
                if isinstance(desired_location, str):
                    desired_location = desired_location.strip()
            except Exception:
                pass

            if desired_location and desired_location.lower() != 'unknown':
                try:
                    if context_manager and context_manager.context:
                        if (context_manager.context.current_location or '').strip() != desired_location:
                            context_manager.context.current_location = desired_location
                            try:
                                context_manager.context.location_label = desired_location
                            except Exception:
                                pass
                            try:
                                context_manager._save()
                            except Exception:
                                pass
                except Exception:
                    pass
                try:
                    if spatial is not None and getattr(spatial, 'current_location', None) != desired_location:
                        spatial.set_current_location(desired_location)
                except Exception:
                    pass
    except Exception:
        pass

    # Load per-session INUA object registry (persistent object states)
    try:
        from object_registry import load_registry_for_session
        load_registry_for_session(tracker.session_id)
    except Exception:
        pass
    
    # Initialize Master Time Coordinator (replaces individual time systems)
    master_time = initialize_master_time_coordinator(starting_hour=9, starting_minute=0, starting_day=1)
    
    # Initialize Save Coordinator (eliminates save conflicts)
    save_coordinator = initialize_save_coordinator(tracker)
    
    # Scene progression tracking
    scene_number = 1
    scene_id = f"scene_{scene_number}"  # Scene ID for memory creation
    scene_action_count = 0
    scene_start_time = time_tracker.get_current_time() if 'time_tracker' in locals() else None
    scene_conclusion_pending = False
    background_atmosphere = None  # Track current background atmosphere for promotion
    
    # Initialize Background Simulation System
    print(f"{Color.INFO}🌍 Initializing Background Simulation System...{Color.RESET}")
    bg_sim = BackgroundSimulationSystem(
        decider_agent=conductor.decider_agent,
        narrator_agent=narrator,
        tracker_agent=tracker,
        narrative_context_manager=narrative_context_manager
    )

    # Initialize World Persistence System (aftermath, situations, reputation, schedules, objects)
    print(f"{Color.INFO}🌐 Initializing World Persistence System...{Color.RESET}")
    from world_persistence_system import get_extended_world_state_manager, format_situation_for_display
    world_state = get_extended_world_state_manager(
        storage_dir=str(storage_dir / "world_state"),
        rag_system=conductor.decider_agent.rag_system if hasattr(conductor.decider_agent, 'rag_system') else None
    )
    print(f"{Color.SUCCESS}✓ World Persistence ready (aftermath, situations, reputation, schedules, objects){Color.RESET}")
    
    # Initialize New Internal Voice & Storyteller Systems
    # Pass RAG system for worldbuilding context in memories and titles
    rag_for_voice = conductor.decider_agent.rag_system if hasattr(conductor.decider_agent, 'rag_system') else None
    init_new_voice_systems(storage_dir, rag_system=rag_for_voice)
    
    # Initialize Additional Immersion Systems
    print(f"{Color.INFO}🎭 Initializing Additional Immersion Systems...{Color.RESET}")
    init_immersion_systems(storage_dir)

    # Initialize PopulationManager with RAG for setting-appropriate NPCs
    print(f"{Color.INFO}👥 Initializing Population Manager...{Color.RESET}")
    population_manager = PopulationManager(scene_creator, logger, rag_system=rag_for_voice)
    
    # Global actor registry - stores all created Actor objects by name for restoration
    # This allows NPCs to persist across location changes
    global_actor_registry: Dict[str, Actor] = {}
    
    def register_nua(nua, available_npcs_list=None):
        """
        Register a NUA in the global actor registry for persistence.
        Also adds to available_npcs if provided and not already present.
        Also tracks NUA location in world map.
        
        Args:
            nua: The NonUserActor to register
            available_npcs_list: Optional list to add the NUA to
        """
        if nua and hasattr(nua, 'sheet') and hasattr(nua.sheet, 'name'):
            nua_name = nua.sheet.name
            # Register in global registry
            global_actor_registry[nua_name] = nua
            # Add to context manager
            context_manager = get_context_manager()
            if context_manager:
                context_manager.add_nua(nua_name)
            # Add to available_npcs if provided
            if available_npcs_list is not None and nua not in available_npcs_list:
                available_npcs_list.append(nua)
            # Track NUA location in world map
            try:
                location_tracker = get_location_tracker()
                if location_tracker.current_location:
                    location_tracker.add_nua_to_location(nua_name, location_tracker.current_location)
            except Exception:
                pass  # Non-critical
            print(f"{Color.INFO}[REGISTRY] Registered NUA: {nua_name}{Color.RESET}")
    
    # Initialize NUA context manager for escalation tracking
    nua_context_manager = NUAContextManager()
    
    # Initialize actor with survival system
    actor.sheet.survival = SurvivalManager()
    
    # Check for critical survival needs at start
    critical_actions = get_critical_survival_actions(actor.sheet)
    if critical_actions:
        print(f"\n{Color.WARNING}⚠️  CRITICAL SURVIVAL NEEDS DETECTED{Color.RESET}")
        for action_id, action in critical_actions.items():
            print(f"{Color.WARNING}   • {action.name}: {action.description}{Color.RESET}")
        print(f"{Color.WARNING}Consider addressing these needs before continuing.{Color.RESET}\n")

    # Access time systems through Master Time Coordinator (read-only)
    time_tracker = master_time.time_tracker
    simulation_time_tracker = master_time.simulation_tracker
    reactor_time_manager = master_time.reactor_time_manager

    print(f"{Color.SYSTEM}========================================")
    print(f"  Welcome to the UTAS Interactive Demo")
    print(f"  🔄 Redesigned Exploration System")
    print(f"========================================{Color.RESET}")
    
    # Tracker should already be initialized from the session setup above
    
    # Auto-save counter for periodic saves
    auto_save_counter = 0
    auto_save_interval = 5  # Save every 5 actions

    # Create time context for scene introduction using Master Time Coordinator
    time_context = master_time.get_current_time_context()

    if not resuming_session:
        # Generate initial exploration scene (NO NPCs)
        scene_data = scene_creator.start_new_simulation(actor)
        if not scene_data:
            print(f"{Color.ERROR}Failed to generate initial scene. Exiting.{Color.RESET}")
            return
        print(f"{Color.INFO}🎭 Starting in EXPLORATION mode (no opponents){Color.RESET}")
        scene_elements = scene_data.get('scene_elements', {})
        scene_setting = scene_elements.get('setting', scene_data.get('setting', 'Unknown location'))
        # Build minimal turn data to seed the narrative loop for the intro
        try:
            turn_data = {
                'user_input': 'Scene Introduction',
                'scene_description': scene_setting,
                'continuity_check': {'judgment': 'Possible'}
            }
            
            # Get full narrative context for initial scene (if resuming session)
            full_context = None
            if resume_session_id:
                try:
                    full_context = narrative_context_manager.get_context_for_llm(
                        use_all_events=True,  # Search ALL events, not just recent
                        importance_threshold="important"  # Only important+ events (critical + important)
                    )
                    full_context = _merge_contexts(full_context, everlasting_context_text)
                except Exception:
                    full_context = None
            
            # Use the narrator's mode-aware intro generator that leverages the loop
            scene_description = narrator.generate_scene_with_narrative_loop(
                scene_elements=scene_elements,
                nua_name="",  # No NPCs at start
                turn_data=turn_data,
                time_context=time_context,
                narrative_context=full_context  # Pass full context for resumed sessions
            )
        except Exception:
            # Fallback to simple setting text if framed intro fails
            scene_description = scene_setting
        # Persist scene description back into conductor for future scene seeding
        try:
            conductor.scene_description = scene_description
        except Exception:
            pass
        # Persist authoritative scene context to tracker
        try:
            tracker.set_current_scene(scene_description)
        except Exception:
            pass
        
        # SAVE TO PERSISTENT CONTEXT
        context_manager.update_scene_description(scene_description)

        # Continuity facts: seed anchors from the initial authoritative scene text
        _trace_continuity_fact_capture(scene_description, source="scene_intro", base_confidence=0.85)

        try:
            _capture_mentioned_actors_from_text(scene_description, source="scene_intro")
        except Exception:
            pass
        
        # Initialize spatial context for this location - DYNAMIC ANALYSIS
        try:
            from spatial_location_analyzer import analyze_scene_for_spatial
            
            # Extract location name from scene data or description
            location_name = scene_data.get('setting', 'Unknown Location')
            if location_name == 'Unknown Location':
                # Use LLM to extract location name from scene description
                try:
                    from openrouter_config import OpenRouterConfig
                    client = OpenRouterConfig.create_client()
                    
                    prompt = f"""Extract the primary location name from this scene description.

SCENE:
{scene_description[:500]}

Respond with just the location name (2-4 words max), nothing else.

Examples:
- "You stand in the garage..." → "Garage"
- "The diner hums with activity..." → "Diner"
- "You're in Rusty's Repairs..." → "Rusty's Repairs"
- "The abandoned Evergreen Chemical Plant..." → "Evergreen Chemical Plant"

Location name:"""
                    
                    response = client.chat.completions.create(
                        model=OpenRouterConfig.get_model_for_role("coordination"),
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.1,
                        max_tokens=20
                    )
                    
                    extracted_name = response.choices[0].message.content.strip()
                    if extracted_name and len(extracted_name) < 50:
                        location_name = extracted_name
                except Exception as e:
                    print(f"{Color.WARNING}[SPATIAL] Could not extract location name: {e}{Color.RESET}")
                    location_name = "Unknown Location"
            
            print(f"{Color.SYSTEM}[SPATIAL] Analyzing initial location: {location_name}{Color.RESET}")
            
            # Check if location already exists
            analysis = None  # Initialize to None for existing locations
            loc_type = "unknown"  # Default value
            reasoning = ""  # Default value
            
            if spatial.location_exists(location_name):
                print(f"{Color.SYSTEM}[SPATIAL] Location '{location_name}' already exists, reusing existing map{Color.RESET}")
                spatial.set_current_location(location_name)
                # Get dimensions from existing location
                context = spatial.get_current_context()
                width = context.location_dimensions.width
                height = context.location_dimensions.height
            else:
                # Use LLM to analyze scene and determine appropriate dimensions
                analysis = analyze_scene_for_spatial(scene_description, location_name)
                
                width = analysis["width"]
                height = analysis["height"]
                loc_type = analysis["location_type"]
                reasoning = analysis.get("reasoning", "")

                # Create location with analyzed dimensions
                spatial.create_location(
                    location_name=location_name,
                    width=float(width),
                    height=float(height),
                    location_type=loc_type,
                    description=scene_description[:200] if scene_description else "A location",
                    scene_description=scene_description or ""  # Full scene description for LLM layout
                )
                print(f"{Color.SYSTEM}[SPATIAL] Setting current location: {location_name} ({float(width):.1f}x{float(height):.1f}){Color.RESET}")
                spatial.set_current_location(location_name)

            MAP_WIDTH = float(width)
            MAP_HEIGHT = float(height)
            
            # Add UA at entrance of location (or move if already exists)
            print(f"{Color.SYSTEM}[SPATIAL] Adding UA: {_ua_display_name(actor, ua_actor=actor)}{Color.RESET}")
            # Check if actor already exists in spatial system
            existing_pos = spatial.get_actor_position("ua_001")
            if existing_pos:
                # Actor exists, move to new location
                spatial.move_actor("ua_001", Position(MAP_WIDTH / 2, MAP_HEIGHT * 0.15))
                print(f"{Color.SYSTEM}[SPATIAL] Moved existing UA to entrance{Color.RESET}")
            else:
                # Actor doesn't exist, add new
                spatial.add_actor(
                    actor_id="ua_001",
                    actor_name=actor.sheet.name,
                    position=Position(MAP_WIDTH / 2, MAP_HEIGHT * 0.15),
                    is_user_actor=True,
                    occupation=getattr(actor.sheet, 'occupation', '') or ""
                )
                print(f"{Color.SYSTEM}[SPATIAL] Added new UA to spatial system{Color.RESET}")

            # Sync the pygame map AFTER UA is guaranteed to exist in spatial context.
            # Then (INITIAL LOCATION ONLY) reposition UA near a plausible rest spot (bed/bench/straw/etc.)
            # based on the generated layout obstacles.
            try:
                from pygame_spatial_map import sync_from_spatial_context
                sync_from_spatial_context(session_id=tracker.session_id if tracker else None)

                try:
                    context = spatial.get_current_context()
                    dims = context.location_dimensions if context else None
                    if dims and dims.obstacles:
                        rest_keywords = [
                            "bed", "cot", "bunk", "mattress", "pallet", "straw", "hay",
                            "blanket", "couch", "bench", "chair", "stool", "rug", "mat"
                        ]

                        best_obs = None
                        best_score = -1
                        for obs in dims.obstacles.values():
                            name_l = (getattr(obs, 'obstacle_name', '') or '').lower()
                            score = 0
                            for i, kw in enumerate(rest_keywords):
                                if kw in name_l:
                                    score = max(score, 100 - i)
                            if score > best_score and getattr(obs, 'boundary_points', None):
                                best_obs = obs
                                best_score = score

                        if best_obs and best_score > 0:
                            pts = list(best_obs.boundary_points)
                            xs = [p.x for p in pts]
                            ys = [p.y for p in pts]
                            min_x, max_x = min(xs), max(xs)
                            min_y, max_y = min(ys), max(ys)
                            cx = (min_x + max_x) / 2.0
                            cy = (min_y + max_y) / 2.0

                            min_dim = max(1.0, min(float(dims.width), float(dims.height)))
                            offset = max(1.5, min_dim * 0.06)

                            candidate_positions = [
                                Position(max_x + offset, cy),
                                Position(min_x - offset, cy),
                                Position(cx, max_y + offset),
                                Position(cx, min_y - offset),
                                Position(cx + offset, cy + offset),
                                Position(cx - offset, cy + offset),
                                Position(cx + offset, cy - offset),
                                Position(cx - offset, cy - offset),
                            ]

                            ua_new_pos = None
                            for cand in candidate_positions:
                                if dims.is_position_valid(cand):
                                    ua_new_pos = cand
                                    break

                            if ua_new_pos is not None:
                                spatial.move_actor("ua_001", ua_new_pos)
                                print(f"{Color.SYSTEM}[SPATIAL] Moved UA near rest spot: {best_obs.obstacle_name}{Color.RESET}")
                                sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                except Exception:
                    pass
            except Exception:
                pass
            
            # Add zones from LLM suggestions (only for new locations)
            if analysis is not None:
                from spatial_context_system import Obstacle, Zone
                context = spatial.get_current_context()
                
                # For streets, create horizontal bands; for buildings, use position hints
                is_street = loc_type == "exterior" and any(word in location_name.lower() for word in ['street', 'road', 'alley'])
                
                if is_street and len(analysis.get("suggested_zones", [])) >= 2:
                    # Street layout: divide into horizontal bands
                    zones_list = analysis.get("suggested_zones", [])
                    num_zones = min(len(zones_list), 4)
                    band_height = MAP_HEIGHT / num_zones
                    
                    for i, zone_data in enumerate(zones_list[:num_zones]):
                        try:
                            zone_name = zone_data.get("name", f"Zone {i+1}")
                            zone_desc = zone_data.get("description", "")
                            
                            # Create horizontal band
                            y_start = i * band_height
                            y_end = (i + 1) * band_height
                            
                            zone_bounds = [
                                Position(0, y_start),
                                Position(MAP_WIDTH, y_start),
                                Position(MAP_WIDTH, y_end),
                                Position(0, y_end)
                            ]
                            
                            zone = Zone(
                                zone_name=zone_name,
                                zone_type=zone_desc[:50] if zone_desc else "area",
                                boundary_points=zone_bounds
                            )
                            context.location_dimensions.zones[zone_name.lower().replace(" ", "_")] = zone
                            print(f"{Color.SYSTEM}[SPATIAL] Added zone: {zone_name} (band {i+1}/{num_zones}){Color.RESET}")
                        except Exception as e:
                            print(f"{Color.WARNING}[SPATIAL] Could not add zone {zone_data.get('name', 'unknown')}: {e}{Color.RESET}")
                else:
                    # Building layout: use position hints
                    for zone_data in analysis.get("suggested_zones", [])[:4]:
                        try:
                            zone_name = zone_data.get("name", "Area")
                            zone_desc = zone_data.get("description", "")
                            position_hint = zone_data.get("position", "center")
                            
                            # Convert position hint to zone boundaries
                            if position_hint == "front":
                                zone_bounds = [
                                    Position(0, 0),
                                    Position(MAP_WIDTH, 0),
                                    Position(MAP_WIDTH, MAP_HEIGHT*0.3),
                                    Position(0, MAP_HEIGHT*0.3)
                                ]
                            elif position_hint == "back":
                                zone_bounds = [
                                    Position(0, MAP_HEIGHT*0.7),
                                    Position(MAP_WIDTH, MAP_HEIGHT*0.7),
                                    Position(MAP_WIDTH, MAP_HEIGHT),
                                    Position(0, MAP_HEIGHT)
                                ]
                            elif position_hint == "left":
                                zone_bounds = [
                                    Position(0, 0),
                                    Position(MAP_WIDTH*0.3, 0),
                                    Position(MAP_WIDTH*0.3, MAP_HEIGHT),
                                    Position(0, MAP_HEIGHT)
                                ]
                            elif position_hint == "right":
                                zone_bounds = [
                                    Position(MAP_WIDTH*0.7, 0),
                                    Position(MAP_WIDTH, 0),
                                    Position(MAP_WIDTH, MAP_HEIGHT),
                                    Position(MAP_WIDTH*0.7, MAP_HEIGHT)
                                ]
                            else:  # center
                                zone_bounds = [
                                    Position(MAP_WIDTH*0.2, MAP_HEIGHT*0.2),
                                    Position(MAP_WIDTH*0.8, MAP_HEIGHT*0.2),
                                    Position(MAP_WIDTH*0.8, MAP_HEIGHT*0.8),
                                    Position(MAP_WIDTH*0.2, MAP_HEIGHT*0.8)
                                ]
                            
                            zone = Zone(
                                zone_name=zone_name,
                                zone_type=zone_desc[:50] if zone_desc else "area",
                                boundary_points=zone_bounds
                            )
                            context.location_dimensions.zones[zone_name.lower().replace(" ", "_")] = zone
                            print(f"{Color.SYSTEM}[SPATIAL] Added zone: {zone_name}{Color.RESET}")
                        except Exception as e:
                            print(f"{Color.WARNING}[SPATIAL] Could not add zone {zone_data.get('name', 'unknown')}: {e}{Color.RESET}")
                
                # Add obstacles from LLM suggestions
                context = spatial.get_current_context()
                for obs_data in analysis.get("suggested_obstacles", [])[:5]:  # Limit to 5
                    try:
                        obs_name = obs_data.get("name", "Obstacle")
                        obs_type = obs_data.get("type", "furniture")
                        position_hint = obs_data.get("position", "center")
                        blocks_movement = obs_data.get("blocks_movement", True)
                        blocks_los = obs_data.get("blocks_line_of_sight", False)
                        
                        # Convert position hint to coordinates
                        if position_hint == "front":
                            x, y = width/2, height*0.2
                        elif position_hint == "back":
                            x, y = width/2, height*0.8
                        elif position_hint == "left":
                            x, y = width*0.2, height/2
                        elif position_hint == "right":
                            x, y = width*0.8, height/2
                        else:  # center
                            x, y = width/2, height/2
                        
                        # Create small obstacle (2x2 units)
                        obstacle = Obstacle(
                            obstacle_name=obs_name,
                            obstacle_type=obs_type,
                            boundary_points=[
                                Position(x-1, y-1), Position(x+1, y-1),
                                Position(x+1, y+1), Position(x-1, y+1)
                            ],
                            blocks_movement=blocks_movement,
                            blocks_line_of_sight=blocks_los
                        )
                        context.location_dimensions.obstacles[obs_name.lower().replace(" ", "_")] = obstacle
                        print(f"{Color.SYSTEM}[SPATIAL] Added obstacle: {obs_name}{Color.RESET}")
                    except Exception as e:
                        print(f"{Color.WARNING}[SPATIAL] Could not add obstacle {obs_data.get('name', 'unknown')}: {e}{Color.RESET}")
            
            print(f"{Color.SUCCESS}[SPATIAL] ✓ Location '{location_name}' created ({width}x{height} {loc_type}) with UA at center{Color.RESET}")
            if reasoning:
                print(f"{Color.SYSTEM}[SPATIAL] Reasoning: {reasoning}{Color.RESET}")
        except Exception as e:
            import traceback
            print(f"{Color.ERROR}[SPATIAL] ✗ Failed to initialize location: {e}{Color.RESET}")
            print(f"{Color.WARNING}[SPATIAL] Traceback: {traceback.format_exc()}{Color.RESET}")
        
        # Initialize scene continuity tracking
        continuity_validator.update_from_scene(scene_description, time_context)
        continuity_validator.add_npc(actor.sheet.name)  # Add UA to tracking
        
        # Debug: Show Narrative Framing (Mode/Tone/Intent) for validation
        try:
            loop_state = narrator.get_narrative_loop_state()
            mode = loop_state.get('mode', 'unknown') if loop_state else 'unknown'
            tone = loop_state.get('tone', 'unknown') if loop_state else 'unknown'
            intent = loop_state.get('intent', 'unknown') if loop_state else 'unknown'
            print(f"{Color.SYSTEM}🔧 Narrative Framing — Mode: {mode} | Tone: {tone} | Intent: {intent}{Color.RESET}")
        except Exception:
            pass
        # Track scene introduction as narrative event
        scene_context_info = f"exploration_start at {time_context['time_of_day'].value if hasattr(time_context['time_of_day'], 'value') else str(time_context['time_of_day'])} in {scene_data.get('setting', 'unknown')}"
        narrative_context_manager.add_narrative_event(
            event_type=NarrativeEventType.SCENE_TRANSITION,
            narrative_text=scene_description,
            actors_involved=[actor.sheet.name],
            importance=NarrativeImportance.IMPORTANT,
            emotional_tone="atmospheric",
            scene_context=scene_context_info
        )
        tracker.start_scene(
            scene_number=1,
            scene_data=scene_data,
            nua_data=None,  # No NPCs in exploration mode
            scene_description=scene_description
        )
        # Persist initial scene via SaveCoordinator (scene transition-like)
        try:
            req = save_coordinator.create_scene_transition_request({
                'scene_number': scene_number,
                'scene_description': scene_description,
                'scene_elements': scene_elements,
                'time_context': time_context,
                'available_npcs': [],
                'actor_state': {
                    'name': actor.sheet.name,
                    'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()}
                }
            })
            save_coordinator.request_save(req)
        except Exception:
            pass
    else:
        # Resume existing session without generating a new scene
        scene_number = int(resume_scene_number or 1)
        scene_description = resume_scene_description or "Previous scene"
        scene_elements = resume_scene_elements or {}
        print(f"{Color.SUCCESS}⏪ Resuming Session — Scene {scene_number}{Color.RESET}")

        # Ensure map sync happens AFTER we have a real location to display.
        try:
            from pygame_spatial_map import sync_from_spatial_context
            # Best-effort: set spatial current location ONLY if spatial didn't already load one.
            # On resume, resume_location_label can be stale (e.g., context saved before a move).
            try:
                spatial_has_loc = bool(getattr(spatial, 'current_location', None))
            except Exception:
                spatial_has_loc = False
            if (not spatial_has_loc) and resume_location_label and spatial and hasattr(spatial, 'set_current_location'):
                try:
                    spatial.set_current_location(str(resume_location_label).strip())
                except Exception:
                    pass
            sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
        except Exception:
            pass
        
        # Display session resume summary
        try:
            resume_summary = narrative_context_manager.get_context_for_llm(
                lookback_events=10,
                importance_threshold="notable"
            )
            if resume_summary:
                print(f"\n{Color.NARRATIVE}📖 STORY SO FAR:{Color.RESET}")
                print(f"{Color.NARRATIVE}{resume_summary}{Color.RESET}\n")
        except Exception:
            pass
        
        # Embed most recent saved exchange output into the scene description (if any)
        try:
            last_exchange_output = None
            try:
                sim = tracker.session_data.get('simulation_session', {})
                scenes = sim.get('scenes', []) or []
            except Exception:
                scenes = []
            for sc in reversed(scenes):
                for ex in reversed(sc.get('exchanges', []) or []):
                    for rd in reversed(ex.get('rounds', []) or []):
                        for trn in reversed(rd.get('turns', []) or []):
                            rep = trn.get('reporter_output') or {}
                            if isinstance(rep, dict):
                                last_exchange_output = rep.get('formatted_output')
                            if last_exchange_output:
                                break
                        if last_exchange_output:
                            break
                    if last_exchange_output:
                        break
                if last_exchange_output:
                    break
            if last_exchange_output:
                try:
                    scene_description = f"{scene_description}\n\n🗣️ LAST EXCHANGE (SAVED):\n{last_exchange_output}"
                except Exception:
                    pass
        except Exception:
            pass
        
        # Display the scene description (already narrative text)
        try:
            conductor.scene_description = scene_description
        except Exception:
            pass
        # Persist authoritative scene context to tracker on resume
        try:
            tracker.set_current_scene(scene_description)
        except Exception:
            pass
        # Compact resume banner details
        try:
            resume_state = tracker.get_runtime_resume_state() or {}
            last_action = resume_state.get('last_action')
            if last_action:
                preview = (last_action[:160] + '…') if len(last_action) > 160 else last_action
                print(f"{Color.SYSTEM}↩️  Last action: {preview}{Color.RESET}")
            recent_updates = resume_state.get('scene_updates') or []
            if isinstance(recent_updates, list) and recent_updates:
                tips = recent_updates[-2:]
                print(f"{Color.INFO}💡 Resume tip:{Color.RESET}")
                for t in tips:
                    tp = (t[:160] + '…') if isinstance(t, str) and len(t) > 160 else t
                    print(f"{Color.INFO}   • {tp}{Color.RESET}")
        except Exception:
            pass
    
    # Initialize available NPCs list (empty for exploration mode)
    available_npcs = []
    try:
        if resuming_session and staged_loaded_npcs:
            available_npcs.extend(list(staged_loaded_npcs))
            try:
                if actor_registry is not None:
                    for npc in staged_loaded_npcs:
                        try:
                            actor_registry[npc.sheet.name] = npc
                        except Exception:
                            pass
            except Exception:
                pass
            try:
                # context_manager is initialized after session load (reset_context_manager) so it's safe here
                context_manager.set_nuas([npc.sheet.name for npc in staged_loaded_npcs])
            except Exception:
                pass
    except Exception:
        pass

    # Resume fallback: spatial context may have NPCs even if runtime_state didn't serialize them.
    # If the map shows NPCs but available_npcs is empty, hydrate from spatial actor_positions.
    try:
        if resuming_session and not available_npcs:
            try:
                from spatial_context_system import get_spatial_manager
                spatial_tmp = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                ctx_tmp = spatial_tmp.get_current_context() if spatial_tmp else None
            except Exception:
                ctx_tmp = None

            spatial_names: list[str] = []
            try:
                if ctx_tmp and getattr(ctx_tmp, 'actor_positions', None):
                    for _aid, _apos in ctx_tmp.actor_positions.items():
                        try:
                            if getattr(_apos, 'is_user_actor', False):
                                continue
                            nm = getattr(_apos, 'actor_name', None)
                            if nm:
                                spatial_names.append(str(nm))
                        except Exception:
                            continue
            except Exception:
                spatial_names = []

            restored = []
            if spatial_names:
                for nm in spatial_names:
                    try:
                        if actor_registry is not None and nm in actor_registry:
                            restored.append(actor_registry[nm])
                            continue
                    except Exception:
                        pass

                    # Best-effort: regenerate minimal NUA actor so continuity checks pass
                    try:
                        if scene_creator:
                            ctx_str = f"Name: {nm}. Location: {context_manager.context.current_location or 'Unknown'}. Role: Present in scene."
                            nua = scene_creator.generate_nua(ctx_str, scene_description=f"Restoring {nm} from spatial context")
                            try:
                                nua.sheet.name = nm
                            except Exception:
                                pass
                            restored.append(nua)
                    except Exception:
                        continue

            if restored:
                available_npcs.extend(restored)
                try:
                    if actor_registry is not None:
                        for npc in restored:
                            try:
                                actor_registry[npc.sheet.name] = npc
                            except Exception:
                                pass
                except Exception:
                    pass
                try:
                    context_manager.set_nuas([npc.sheet.name for npc in restored])
                except Exception:
                    pass
                try:
                    if tracker is not None:
                        tracker.save_available_npcs(list(available_npcs or []))
                except Exception:
                    pass
    except Exception:
        pass
    available_inuas = []  # Track INUAs for world events (hazards, environmental interactions)
    recent_actions = []
    scene_updates: list[str] = []
    last_action_narrative: Optional[str] = None
    # Initialize scene event scheduler
    scheduler = SceneEventScheduler()
    spark_pending = False
    # SPARK ignore fade state
    spark_active = False
    spark_fade_turns = 0
    spark_bridge_cache: str = ""
    spark_persistence: str = "soft"
    spark_requires_exit_to_clear: bool = False
    spark_min_persist_turns: int = 0
    spark_min_persist_hours: float = 0.0
    # Track last narrative loop mode to avoid noisy mode shift logs
    last_loop_mode: str | None = None
    # Cache for immediate encounter usage
    pending_encounter_action: str | None = None
    pending_target_hint: str | None = None

    everlasting_context_text: str = ""
    _last_everlasting_refresh_wms: int | None = None

    def _merge_contexts(base: str, extra: str, *, max_chars: int = 2400) -> str:
        try:
            b = (base or "").strip()
            e = (extra or "").strip()
            if not e:
                return b
            if max_chars is not None and max_chars > 0:
                e = e[-int(max_chars):]
            if not b:
                return e
            return f"{b}\n\n{e}"
        except Exception:
            return (base or "")
    
    print(f"{Color.SYSTEM}🕘 Time: {time_tracker.get_current_time().format_full()} - {get_time_display_name(time_tracker.get_current_time().get_time_of_day())}{Color.RESET}")
    atmospheric_desc = time_tracker.get_atmospheric_description()
    
    # Get atmospheric description for narrative context (don't display at start)
    lighting_mood = _get_lighting_mood(time_context['time_of_day'])
    time_of_day_str = str(time_context['time_of_day']).lower()
    
    # Store for context but don't print
    if 'night' in time_of_day_str or 'midnight' in time_of_day_str:
        enhanced_atmospheric = f"{atmospheric_desc}"
    else:
        enhanced_atmospheric = f"{atmospheric_desc} {lighting_mood.capitalize()} light fills the scene."
    # Heuristic: schedule an arrival if the starting scene suggests vehicle travel (e.g., trains, buses, planes)
    try:
        # Schedule arrivals only when the scene actually implies a vehicle context
        vehicle = _infer_vehicle(scene_description)
        if vehicle != "unknown":
            scheduler.schedule_arrival('Next stop', 3, simulation_time_tracker.get_total_simulation_time())
    except Exception:
        pass
    
    # Display the scene description (already narrative text)
    # Convert any third-person UA references to second person
    scene_description = _convert_ua_to_second_person(scene_description, actor.sheet.name)
    print(f"\n{Color.SCENE}🎬 SCENE DESCRIPTION:{Color.RESET}")
    print(f"{Color.NARRATIVE}{scene_description}{Color.RESET}")

    try:
        if _env_bool("VIS_IMAGE_DEBUG", False):
            _autogen_bool = _env_bool("VIS_IMAGE_AUTOGEN", True)
            _enabled_bool = _env_bool("VIS_IMAGE_ENABLED", True)
            _model_id = os.getenv("FAL_IMAGE_MODEL") or ""
            _has_key = bool(os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY"))
            print(
                f"{Color.SYSTEM}🖼️ VIS: scene hook reached autogen={_autogen_bool} enabled={_enabled_bool} model={_model_id} has_fal_key={_has_key}{Color.RESET}"
            )
    except Exception:
        pass

    _loc = ""
    try:
        _loc = str(locals().get('current_location') or "")
    except Exception:
        _loc = ""

    try:
        _update_visualizer_context(
            ua_actor=actor,
            scene_description=scene_description,
            current_location=_loc,
            time_context=time_context or {},
            creator_agent=scene_creator if 'scene_creator' in locals() else None,
            seed=None,
        )
    except Exception as e:
        try:
            if _env_bool("VIS_VIDEO_DEBUG", False):
                print(f"{Color.WARNING}🎬 VIS: visualizer context update failed: {e}{Color.RESET}")
        except Exception:
            pass

    try:
        if _vis_autogen_enabled and _env_bool("VIS_VIDEO_ENABLED", False):
            _trigger_realtime_video(
                ua_actor=actor,
                scene_description=scene_description,
                current_location=_loc,
                time_context=time_context or {},
                spoken_line=str(scene_description or ''),
                creator_agent=scene_creator if 'scene_creator' in locals() else None,
                seed=None,
            )
    except Exception:
        pass

    try:
        autogen_enabled = _env_bool("VIS_IMAGE_AUTOGEN", True)
        if autogen_enabled:
            _trigger_realtime_image(
                ua_actor=actor,
                scene_description=scene_description,
                current_location=_loc,
                time_context=time_context or {},
                creator_agent=scene_creator if 'scene_creator' in locals() else None,
                seed=None,
                spoken_line="",
                source="scene_load",
                reason="scene_description",
            )
    except Exception as e:
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: image autogen exception: {e}{Color.RESET}")
        except Exception:
            pass
    
    # Get world context (aftermath, in-progress situations, schedules, objects)
    try:
        npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
        current_hour = time_context.get('hour', 12) if time_context else 12
        current_day = time_context.get('day_of_week', 0) if time_context else 0
        
        # Create schedules for NPCs that don't have them
        for npc in available_npcs:
            world_state.ensure_npc_has_schedule(
                npc_name=npc.sheet.name,
                occupation=getattr(npc.sheet, 'occupation', 'worker'),
                work_location=scene_description[:30]
            )
        
        world_context = world_state.get_full_scene_context(
            scene_description=scene_description,
            present_npcs=npc_names,
            hour=current_hour,
            day_of_week=current_day,
            current_location=scene_description[:50]
        )

        try:
            if hasattr(world_state, 'get_everlasting_context'):
                ev = world_state.get_everlasting_context(
                    present_npcs=npc_names,
                    current_location=scene_description[:50]
                )
                everlasting_context_text = str(ev.get('everlasting_context_text') or "")
            else:
                everlasting_context_text = str(world_context.get('everlasting_context_text') or "")
        except Exception:
            try:
                everlasting_context_text = str(world_context.get('everlasting_context_text') or "")
            except Exception:
                everlasting_context_text = ""
        
        # Display weather
        try:
            weather_info = world_state.get_weather_for_scene()
            if weather_info.get('description'):
                print(f"\n{Color.SYSTEM}🌤️ {weather_info['description']}{Color.RESET}")
        except Exception:
            pass
        
        # Display persistent objects and environment
        if world_context.get('environment_additions'):
            print(f"\n{Color.SYSTEM}📦 {world_context['environment_additions']}{Color.RESET}")
        
        # Display aftermath if any
        if world_context.get('aftermath'):
            print(f"\n{Color.WARNING}📍 {world_context['aftermath']}{Color.RESET}")
        
        # Note any injured NPCs
        if world_context.get('npc_injuries'):
            for npc, injury in world_context['npc_injuries'].items():
                print(f"{Color.WARNING}   {npc} appears {injury}.{Color.RESET}")
        
        # Note unavailable NPCs (not at this location right now)
        if world_context.get('unavailable_npcs'):
            for npc_name, reason in world_context['unavailable_npcs'][:3]:
                print(f"{Color.SYSTEM}   📍 {npc_name} is not here ({reason}){Color.RESET}")
        
        # SPATIAL MEMORY: Record this location visit
        try:
            npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
            world_state.spatial_memory.record_visit(
                location_name=scene_description[:50],
                scene_description=scene_description,
                npcs_present=npc_names
            )
        except Exception:
            pass
        
        # CALENDAR EVENTS: Show any active events
        try:
            calendar_narratives = world_state.calendar_system.get_narrative_additions(
                day_of_week=current_day, hour=current_hour
            )
            for narrative in calendar_narratives[:2]:
                print(f"{Color.INFO}📅 {narrative}{Color.RESET}")
        except Exception:
            pass
        
        # SOUNDS: Display any audible sounds from nearby
        try:
            sounds_desc = world_state.sound_system.get_sounds_description(scene_description[:50])
            if sounds_desc:
                print(f"{Color.INFO}👂 {sounds_desc}{Color.RESET}")
        except Exception:
            pass
    except Exception as e:
        pass  # World context is optional enhancement
    
    print(f"\n{Color.INFO}--- Solo Exploration Mode ---{Color.RESET}")
    initial_time = master_time.time_tracker.get_current_time()
    print(f"{Color.SYSTEM}📊 Time: {initial_time.format_full()}{Color.RESET}")
    
    # QUICK EXCHANGE MODE: Auto-create test NPC
    if hasattr(__builtins__, 'QUICK_EXCHANGE_MODE') and __builtins__.QUICK_EXCHANGE_MODE:
        try:
            print(f"\n{Color.SYSTEM}🎭 Quick Exchange Mode: Creating test NPC...{Color.RESET}")
            
            # Generate NPC using CreatorAgent
            test_npc_context = """Create a mechanic NPC for testing exchanges.
Name: Vince 'Grease' Morrison
Age: 35
Occupation: Mechanic
Setting: Bar/garage setting
Personality: Gruff but fair, protective of his territory
Skills: Mechanics (3), Intimidation (2), Brawling (3)"""
            
            test_npc = scene_creator.generate_nua(
                context=test_npc_context,
                scene_description=scene_description
            )
            
            # Add to available NPCs
            available_npcs.append(test_npc)
            
            # Update scene description to include NPC
            npc_intro = f"\n\n{_ua_display_name(test_npc, ua_actor=actor)}, a {test_npc.sheet.occupation}, is here."
            scene_description = f"{scene_description}{npc_intro}"
            
            print(f"{Color.SUCCESS}✓ Test NPC created: {_ua_display_name(test_npc, ua_actor=actor)}{Color.RESET}")
            print(f"{Color.INFO}Ready for exchange testing!{Color.RESET}\n")
            
        except Exception as e:
            print(f"{Color.WARNING}⚠️  Failed to create test NPC: {e}{Color.RESET}")
            print(f"{Color.INFO}You can manually spawn with: spawn Vince 'Grease' Morrison{Color.RESET}\n")
    
    # AUTO-SPAWN NPCs - DISABLED (Replaced by PopulationManager)
    # try:
    #     from scene_npc_parser import auto_spawn_scene_npcs
    #     spawned_count = auto_spawn_scene_npcs(
    #         scene_description=scene_description,
    #         creator_agent=scene_creator,
    #         available_npcs=available_npcs,
    #         continuity_validator=continuity_validator,
    #         auto_memory_creator=auto_memory_creator,
    #         actor_name=actor.sheet.name,
    #         scene_id=scene_id
    #     )
    #     if spawned_count > 0:
    #         print(f"{Color.SUCCESS}[NPC PARSER] Auto-spawned {spawned_count} NPC(s) from initial scene{Color.RESET}")
    # except Exception as e:
    #     if not SUPPRESS_DEBUG:
    #         print(f"{Color.WARNING}[NPC PARSER] Initial scene auto-spawn failed: {e}{Color.RESET}")
    
    # Save initial atmospheric description to context
    scene_context_info = f"{time_context['time_of_day'].value if hasattr(time_context['time_of_day'], 'value') else str(time_context['time_of_day'])} with {time_context['lighting_condition']} lighting"
    narrative_context_manager.add_narrative_event(
        event_type=NarrativeEventType.TIME_PASSAGE,
        narrative_text=atmospheric_desc,
        actors_involved=[actor.sheet.name],
        importance=NarrativeImportance.ROUTINE,
        emotional_tone="atmospheric",
        scene_context=scene_context_info
    )

    # Initialize travel chunking state (tracks multi-segment journeys)
    travel_chunking = TravelChunkingState(context_manager)
    
    # -------------------------------------------------------------------------
    # HELPER: Execute Post-User Turns (Lower Initiative NPCs)
    # -------------------------------------------------------------------------
    def execute_post_user_turns_if_roam():
        """Execute NPC turns for actors with lower initiative than the UA."""
        nonlocal scene_description, time_context

        # If we intentionally skipped BG sim this loop, do not run post-user turns either
        try:
            if skip_bg_sim:
                return
        except Exception:
            pass
        
        current_sim_mode = encounter_checker.get_current_mode()
        if current_sim_mode != SimulationMode.ROAM or not available_npcs:
            return
            
        try:
            from initiative_system import get_location_initiative_tracker
            init_tracker = get_location_initiative_tracker()
            
            if not init_tracker.has_initiative():
                return
                
            turn_order = init_tracker.get_turn_order()
            
            # Find UA position and count post-user actors
            ua_idx = next((i for i, x in enumerate(turn_order) if x.get('is_user')), -1)
            if ua_idx < 0:
                return
                
            post_user_actors = [e for i, e in enumerate(turn_order) if i > ua_idx and not e.get('is_user')]
            
            if post_user_actors:
                print(f"{Color.SYSTEM}[BG SIM] {len(post_user_actors)} NPC(s) act after you...{Color.RESET}")
                
                # Execute post-user turns
                bg_result = bg_sim.execute_post_user_turns(
                    turn_order,
                    actor,
                    available_npcs,
                    scene_description,
                    time_context
                )
                
                # Handle Interrupt (NUA started an exchange)
                if isinstance(bg_result, dict) and bg_result.get('interrupt'):
                    event = bg_result.get('event', {})
                    initiator = event.get('initiator')
                    
                    # Validate initiator before using
                    if initiator and hasattr(initiator, 'sheet') and hasattr(initiator.sheet, 'name'):
                        print(f"\n{Color.WARNING}🚨 ENCOUNTER TRIGGERED BY {_ua_display_name(initiator, ua_actor=actor).upper()}!{Color.RESET}")
                        
                        # CRITICAL: Seed encounter participants for ENCOUNTER init (avoid empty participants crash)
                        try:
                            encounter_checker.current_context.participants = [initiator]
                            encounter_checker.current_context.trigger_action = event.get('trigger_action', 'background initiative')
                            encounter_checker.current_context.encounter_type = event.get('encounter_type', 'general')
                            # NPC-initiated encounter: force this initiator as Round 1 proactor (override UA-first)
                            encounter_checker.current_context.forced_round_one_proactor = initiator
                        except Exception:
                            pass
                        
                        # Switch mode to ENCOUNTER - clear location initiative
                        encounter_checker.set_mode(SimulationMode.ENCOUNTER)
                        init_tracker.clear()
                        
                        # Setup Round Manager override
                        if hasattr(conductor, 'round_manager'):
                            conductor.round_manager.set_round_one_proactor(initiator)
                    else:
                        print(f"{Color.WARNING}[BG SIM] NUA encounter triggered but initiator invalid{Color.RESET}")
                        
        except Exception as e:
            print(f"{Color.WARNING}[BG SIM] Post-turn error: {e}{Color.RESET}")
    
    # Main simulation loop
    turn_number = 0  # Track turn number for memory creation and tracking
    skip_bg_sim_once = False
    last_inner_voice = None  # Track last inner voice for consistency
    _last_auto_context_sync_turn: int = -999999

    # INITIAL SYNC: Scan UA memories/goals for mentioned actors at startup
    try:
        if not SUPPRESS_DEBUG:
            print(f"{Color.SYSTEM}[MENTION] Initial sync of UA context...{Color.RESET}")
        sync_mentions_from_ua_context(actor)
    except Exception as e:
        if not SUPPRESS_DEBUG:
            print(f"{Color.WARNING}[MENTION] Initial sync failed: {e}{Color.RESET}")

    while True:
        turn_number += 1  # Increment at start of each turn

        # One-shot gate: some commands (e.g. /ctxstats, /everlasting) should not trigger BG sim
        skip_bg_sim = bool(skip_bg_sim_once)
        if skip_bg_sim_once:
            skip_bg_sim_once = False
        
        # AUTO-SYNC PYGAME MAP - Updates actor positions if map is running
        # This ensures the map stays in sync without needing to run /pmap repeatedly
        try:
            auto_sync_map(session_id=tracker.session_id if tracker else None)
        except Exception:
            pass  # Map sync is non-critical
        
        # Check if we should queue a SPARK (only in exploration mode). We will generate it AFTER processing this turn's input.
        # ENHANCED: Only trigger sparks when narrative loop is in SPARK mode (user has shown interest)
        current_mode = encounter_checker.get_current_mode()
        narrative_mode = narrative_loop.state.mode.value if hasattr(narrative_loop, 'state') else 'roam'

        # ============================================================
        # AUTO CONTEXT SYNC (NO MANUAL /context sync REQUIRED)
        # ============================================================
        # If the persistent context is missing critical fields (most importantly location),
        # auto-heal from tracker/spatial/world-map sources and persist immediately.
        # Rate-limited to avoid noisy logs.
        try:
            if (turn_number - _last_auto_context_sync_turn) >= 3:
                from persistent_context_manager import get_context_health_report, sync_context_with_tracker
                rep = get_context_health_report()
                if rep.get('status') in ['degraded', 'error']:
                    _ = sync_context_with_tracker(tracker)
                    _last_auto_context_sync_turn = turn_number
                    # If we restored a better scene/location, reflect it in local variables too.
                    try:
                        ctx2 = context_manager.context
                        if (not scene_description or len((scene_description or '').strip()) < 20) and getattr(ctx2, 'current_scene_description', None):
                            scene_description = str(ctx2.current_scene_description)
                    except Exception:
                        pass
        except Exception:
            pass
        
        if (current_mode == SimulationMode.ROAM and 
            narrative_mode == 'spark' and  # ← NEW: Only when user shows interest
            simulation_time_tracker.should_generate_spark(current_mode.value)):
            spark_pending = True
        
        # Display current status with narrative clock time
        current_time = master_time.time_tracker.get_current_time()
        print(f"\n{Color.SYSTEM}📊 Status: {current_mode.value.upper()} mode | Time: {current_time.format_full()}{Color.RESET}")

        # Refresh everlasting context each turn so newly logged events/memories are immediately available
        try:
            npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
            time_ctx_now = master_time.get_current_time_context() if master_time else {}
            current_hour = time_ctx_now.get('hour', 12) if isinstance(time_ctx_now, dict) else 12
            current_day = time_ctx_now.get('day_of_week', 0) if isinstance(time_ctx_now, dict) else 0

            now_wms = None
            try:
                if isinstance(time_ctx_now, dict):
                    now_wms = time_ctx_now.get('world_minutes_since_start')
                    if now_wms is None:
                        gt = time_ctx_now.get('game_time')
                        if gt is not None:
                            day = int(getattr(gt, 'day', 1) or 1)
                            hour = int(getattr(gt, 'hour', 0) or 0)
                            minute = int(getattr(gt, 'minute', 0) or 0)
                            now_wms = (max(day, 1) - 1) * 1440 + hour * 60 + minute
            except Exception:
                now_wms = None

            if now_wms is None or _last_everlasting_refresh_wms is None or int(now_wms) != int(_last_everlasting_refresh_wms):
                world_context_turn = {}
                try:
                    if hasattr(world_state, 'get_everlasting_context'):
                        world_context_turn = world_state.get_everlasting_context(
                            present_npcs=npc_names,
                            current_location=scene_description[:50]
                        )
                    else:
                        world_context_turn = world_state.get_full_scene_context(
                            scene_description=scene_description,
                            present_npcs=npc_names,
                            hour=current_hour,
                            day_of_week=current_day,
                            current_location=scene_description[:50]
                        )
                except Exception:
                    world_context_turn = {}
                try:
                    everlasting_context_text = str(world_context_turn.get('everlasting_context_text') or "")
                except Exception:
                    everlasting_context_text = ""
                try:
                    if now_wms is not None:
                        _last_everlasting_refresh_wms = int(now_wms)
                except Exception:
                    pass
        except Exception:
            pass
        
        # Display current task
        if hasattr(actor.sheet, 'goal_task_manager') and actor.sheet.goal_task_manager.current_task:
            current_task_display = actor.sheet.goal_task_manager.display_current_task()
            print(f"{Color.INFO}📋 Current Task: {current_task_display}{Color.RESET}")
        
        if available_npcs:
            nua_names = [_ua_display_name(nua, ua_actor=actor) for nua in available_npcs]
            print(f"{Color.INFO}👥 Present: {', '.join(nua_names)}{Color.RESET}")
            
            # Check if user wants to interact with available NUAs
            if (current_mode == SimulationMode.ROAM and 
                len(available_npcs) > 0 and 
                encounter_checker.current_context.mode != SimulationMode.ENCOUNTER):

                # Note: Removed meta "do you want to interact?" prompt
                # User will naturally interact by stating their action
                # This maintains immersion - life doesn't ask permission to interact
                pass
        
        print(f"\n{Color.INFO}Commands: 'ua' (sheet), 'people' (list), 'look' (scene), 'map' (local), '/map' (rich), '/pmap' (pygame), '/dist', 'worldmap', '/travel <loc>', '/nearby'{Color.RESET}")

        # -------------------------------------------------------------------------
        # BACKGROUND SIMULATION: Pre-User Turns (High Initiative NUAs)
        # -------------------------------------------------------------------------
        # NPCs with higher initiative than the UA act BEFORE the user's turn
        roam_turn_order = []
        if current_mode == SimulationMode.ROAM and available_npcs and not skip_bg_sim:
            try:
                from initiative_system import get_location_initiative_tracker
                
                init_tracker = get_location_initiative_tracker()
                
                # Use stored initiative if available, otherwise prepare new order
                if init_tracker.has_initiative():
                    roam_turn_order = init_tracker.get_turn_order()
                    
                    # Count pre-user actors (those before UA in turn order)
                    ua_idx = next((i for i, x in enumerate(roam_turn_order) if x.get('is_user')), len(roam_turn_order))
                    pre_user_actors = [e for i, e in enumerate(roam_turn_order) if i < ua_idx and not e.get('is_user')]
                    
                    if pre_user_actors:
                        print(f"{Color.SYSTEM}[BG SIM] {len(pre_user_actors)} NPC(s) act before you...{Color.RESET}")
                        
                        # Get current location name to ensure NPCs know where they are
                        current_loc = context_manager.context.current_location or "Unknown Location"
                        
                        # Prepend location context to scene description for NUA awareness
                        nua_scene_context = f"**CURRENT LOCATION: {current_loc}**\n\n{scene_description}"
                        
                        # Execute pre-user turns
                        bg_result = bg_sim.execute_pre_user_turns(
                            roam_turn_order, 
                            actor, 
                            available_npcs, 
                            nua_scene_context, 
                            time_context
                        )

                        # Prune departed actors from stored turn order to prevent contradictions
                        try:
                            available_set = set(available_npcs or [])
                            pruned = []
                            for e in roam_turn_order:
                                if e.get('is_user'):
                                    pruned.append(e)
                                else:
                                    a = e.get('actor')
                                    if a in available_set:
                                        pruned.append(e)
                            roam_turn_order = pruned
                            if init_tracker.has_location_initiative(current_loc):
                                init_tracker.set_location_initiative(current_loc, roam_turn_order)
                        except Exception:
                            pass
                        
                        # Handle Interrupt (NUA started an exchange)
                        if isinstance(bg_result, dict) and bg_result.get('interrupt'):
                            event = bg_result.get('event', {})
                            initiator = event.get('initiator')
                            
                            # Validate initiator before using
                            if initiator and hasattr(initiator, 'sheet') and hasattr(initiator.sheet, 'name'):
                                print(f"\n{Color.WARNING}🚨 ENCOUNTER TRIGGERED BY {_ua_display_name(initiator, ua_actor=actor).upper()}!{Color.RESET}")
                                
                                # CRITICAL: Seed encounter participants for ENCOUNTER init (avoid empty participants crash)
                                try:
                                    encounter_checker.current_context.participants = [initiator]
                                    encounter_checker.current_context.trigger_action = event.get('trigger_action', 'background initiative')
                                    encounter_checker.current_context.encounter_type = event.get('encounter_type', 'general')
                                    # NPC-initiated encounter: force initiator as Round 1 proactor (override UA-first)
                                    encounter_checker.current_context.forced_round_one_proactor = initiator
                                except Exception:
                                    pass
                                
                                # Switch mode to ENCOUNTER - clear location initiative
                                encounter_checker.set_mode(SimulationMode.ENCOUNTER)
                                init_tracker.clear()
                                
                                # Setup Round Manager override
                                if hasattr(conductor, 'round_manager'):
                                    conductor.round_manager.set_round_one_proactor(initiator)
                                
                                continue  # Restart loop in ENCOUNTER mode
                            else:
                                print(f"{Color.WARNING}[BG SIM] NUA encounter triggered but initiator invalid{Color.RESET}")
                else:
                    # No stored initiative - this shouldn't happen if _apply_location_move worked
                    # Roll fresh as fallback
                    roam_turn_order = bg_sim.prepare_turn_order(actor, available_npcs)
                    
            except Exception as e:
                print(f"{Color.WARNING}[BG SIM] Pre-turn error: {e}{Color.RESET}")

        # ============================================================
        # WORLD EVENT SIMULATION - Living World Events
        # ============================================================
        # Simulate world events that occur independently of user action:
        # - INUA hazards (machinery failing, objects falling, environmental dangers)
        # - NUA-to-NUA interactions (observable by user)
        # These make the world feel ALIVE, not waiting for user interaction.
        # ============================================================
        if current_mode == SimulationMode.ROAM and not skip_bg_sim:
            try:
                world_events = bg_sim.simulate_world_events(
                    user_actor=actor,
                    available_nuas=available_npcs,
                    available_inuas=available_inuas,
                    scene_description=scene_description,
                    time_context=time_context
                )
                
                # Display and process each world event
                for world_event in world_events:
                    # Display the event with perceptual narrative and internal voice
                    bg_sim.display_observable_event(
                        event=world_event,
                        user_actor=actor,
                        show_internal_voice=True
                    )
                    
                    # Apply mechanical effects (status shifts from hazards, etc.)
                    if world_event.mechanical_effects:
                        # Build actor lookup dict
                        actors_by_name = {actor.sheet.name: actor}
                        for npc in available_npcs:
                            actors_by_name[npc.sheet.name] = npc
                        
                        applied = bg_sim.apply_event_effects(world_event, actors_by_name)
                        if applied:
                            for effect_desc in applied:
                                print(f"{Color.WARNING}⚡ {effect_desc}{Color.RESET}")
                        
                        # Record event in world persistence for aftermath tracking
                        try:
                            from world_persistence_system import AftermathType
                            victim = world_event.mechanical_effects.get('victim')
                            hazard = world_event.mechanical_effects.get('hazard_source', 'Unknown')
                            severity = world_event.mechanical_effects.get('status_shift', {}).get('severity', 2)
                            
                            if victim:
                                world_state.record_hazard_event(
                                    hazard_name=hazard,
                                    victim_name=victim,
                                    location=scene_description[:100],
                                    severity=severity,
                                    effect="injured" if severity >= 2 else "shaken"
                                )
                        except Exception:
                            pass
                    
                    # Check if event escalates to exchange (NUA-to-NUA conflict)
                    if world_event.mechanical_effects.get('escalates_to_exchange'):
                        initiator_name = world_event.mechanical_effects.get('initiator')
                        target_name = world_event.mechanical_effects.get('target')
                        
                        # Find the actors
                        initiator = next((n for n in available_npcs if n.sheet.name == initiator_name), None)
                        target = next((n for n in available_npcs if n.sheet.name == target_name), None)
                        
                        if initiator and target:
                            print(f"\n{Color.WARNING}⚔️ {initiator_name} and {target_name} are about to clash!{Color.RESET}")
                            print(f"{Color.INFO}You can intervene, watch, or leave...{Color.RESET}")
                            
                            # Record conflict in world persistence
                            try:
                                world_state.record_conflict_event(
                                    participants=[initiator_name, target_name],
                                    location=scene_description[:100],
                                    severity=2
                                )
                            except Exception:
                                pass
                    
                    # Check if event requires user response (hazard targeting user)
                    if world_event.requires_user_response:
                        print(f"\n{Color.ERROR}⚠️ You need to react!{Color.RESET}")
                        # This will flow into the normal user input prompt
                        
            except Exception as e:
                print(f"{Color.WARNING}[WORLD SIM] World event simulation error: {e}{Color.RESET}")

        # If we just triggered an encounter and have a pending action, skip prompting and survival handling
        skip_prompt = (encounter_checker.current_context.mode == SimulationMode.ENCOUNTER and pending_encounter_action)

        # Poll pygame map UI actions (non-blocking)
        try:
            from pygame_spatial_map import get_pygame_map
            map_inst = get_pygame_map()
            if map_inst and getattr(map_inst, 'running', False):
                evt = None
                try:
                    evt = map_inst.pop_action()
                except Exception:
                    evt = None

                if evt and isinstance(evt, tuple) and len(evt) >= 2:
                    evt_type, evt_payload = evt[0], evt[1]
                    if evt_type == 'travel_request' and evt_payload:
                        try:
                            destination = str(evt_payload)
                            from spatial_context_system import get_spatial_manager
                            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                            origin = context_manager.context.current_location or "Unknown Location"
                            travel_minutes = calculate_travel_time(origin, destination, spatial)

                            if travel_minutes <= 3:
                                prev_desc = scene_description
                                scene_description = _apply_location_move(
                                    conductor, destination, master_time.get_current_time_context(),
                                    actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                    population_manager=population_manager,
                                    scene_creator=scene_creator,
                                    actor_registry=global_actor_registry
                                )
                                print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                                try:
                                    from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                    clear_layout_cache()
                                    sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                except Exception:
                                    pass
                            else:
                                total_segments = travel_chunking.start_journey(destination, travel_minutes, origin=origin)
                                print(f"{Color.INFO}[TRAVEL] Journey to {destination} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                                print(f"{Color.SYSTEM}Describe your first action as you head toward {destination}...{Color.RESET}")
                            continue
                        except Exception as e:
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.WARNING}[PMAP] Travel request failed: {e}{Color.RESET}")
        except Exception:
            pass

        if not skip_prompt:
            # Note: Survival needs are now automatically detected from user actions
            # No need to display manual survival action menu
            
            # Get user input via unified prompt helper
            user_input = _prompt_action_input(Color.INPUT)

            # If the Windows prompt loop received a pygame travel request, handle it immediately
            if user_input.lower().startswith('__pmap_travel__'):
                try:
                    destination = user_input[len('__pmap_travel__'):].strip()
                    if destination:
                        from spatial_context_system import get_spatial_manager
                        spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                        origin = context_manager.context.current_location or "Unknown Location"
                        travel_minutes = calculate_travel_time(origin, destination, spatial)

                        if travel_minutes <= 3:
                            prev_desc = scene_description
                            scene_description = _apply_location_move(
                                conductor, destination, master_time.get_current_time_context(),
                                actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                population_manager=population_manager,
                                scene_creator=scene_creator,
                                actor_registry=global_actor_registry
                            )
                            print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                            try:
                                from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                clear_layout_cache()
                                sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                            except Exception:
                                pass
                        else:
                            total_segments = travel_chunking.start_journey(destination, travel_minutes, origin=origin)
                            print(f"{Color.INFO}[TRAVEL] Journey to {destination} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                            print(f"{Color.SYSTEM}Describe your first action as you head toward {destination}...{Color.RESET}")
                        continue
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}[PMAP] Travel request failed: {e}{Color.RESET}")
                    continue
            
            # Strict non-turn UI commands (map/roster/debug). These should not go through LLM/action pipelines.
            cmd_l = (user_input or '').strip().lower()

            if _handle_debug_context_commands(user_input):
                continue

            # World map UI (pygame) - strictly non-turn like /pmap
            if cmd_l in ['worldmap', 'world map', 'locations', '/world', '/worldmap', '/nearby']:
                try:
                    from pygame_spatial_map import start_pygame_map, get_pygame_map, sync_world_graph, sync_from_spatial_context

                    if start_pygame_map():
                        # Always sync BOTH layers so TAB toggle never shows an empty mode.
                        sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                        sync_world_graph(tracker.session_id if tracker else None)
                        map_inst = get_pygame_map()
                        try:
                            if map_inst is not None and hasattr(map_inst, 'set_mode'):
                                from pygame_spatial_map import MapMode
                                map_inst.set_mode(MapMode.WORLD)
                        except Exception:
                            pass
                        print(f"{Color.SUCCESS}[MAP] World map opened (TAB toggles LOCAL/WORLD; click node then ENTER to travel){Color.RESET}")
                    else:
                        print(f"{Color.WARNING}[MAP] Failed to start map{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}World map error: {e}{Color.RESET}")

                # Ensure next loop does not run BG sim due to a UI/debug command
                skip_bg_sim_once = True
                continue

            if user_input.lower().startswith('/image'):
                try:
                    raw = (user_input or '').strip()
                    rest = raw[6:].strip() if len(raw) >= 6 else ''

                    arg = (rest.split()[0].lower() if rest else '')
                    if arg in ['on', 'off']:
                        os.environ['VIS_IMAGE_AUTOGEN'] = 'true' if (arg == 'on') else 'false'
                        state = 'ON' if (arg == 'on') else 'OFF'
                        print(f"{Color.SYSTEM}🖼️ Image autogen: {state}{Color.RESET}")
                        skip_bg_sim_once = True
                        continue

                    if not (_vis_context and _vis_context.get('ua_actor') and _vis_context.get('scene_description')):
                        print(f"{Color.WARNING}No visualizer context available yet (need a scene).{Color.RESET}")
                        skip_bg_sim_once = True
                        continue

                    try:
                        _maybe_start_visualizer_viewer()
                    except Exception:
                        pass

                    _trigger_realtime_image(
                        ua_actor=_vis_context.get('ua_actor'),
                        scene_description=_vis_context.get('scene_description') or "",
                        current_location=_vis_context.get('current_location') or "",
                        time_context=_vis_context.get('time_context') or {},
                        creator_agent=_vis_context.get('creator_agent'),
                        seed=_vis_context.get('seed'),
                    )
                    print(f"{Color.SYSTEM}🖼️ Generated image to simulation_data/visualizer/latest.png{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}Image command failed: {e}{Color.RESET}")
                skip_bg_sim_once = True
                continue

            # Handle memory commands first (no time advancement)
            if handle_memory_command(user_input):
                continue
            
            # ============================================================
            # ACTION TYPE DETECTION - Determine if contested/given/fallible/inquiry
            # ============================================================
            # Detect action type EARLY (used later for routing), but continuity should still
            # run for all non-meta actions.
            # ============================================================
            
            def _strict_detect_inquiry_or_action(_user_input, _proactor, _reactor, _retries: int = 3):
                last_error = None
                for attempt in range(1, max(1, int(_retries)) + 1):
                    try:
                        result = conductor.detect_inquiry_or_action(_user_input, _proactor, _reactor)
                        if not isinstance(result, dict):
                            raise ValueError(f"Interpreter returned non-dict: {type(result)}")
                        if not result.get('input_type'):
                            raise ValueError("Interpreter missing required key 'input_type'")
                        return result
                    except Exception as e:
                        last_error = e
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}[INTERPRETER] Classification failed (attempt {attempt}/{_retries}): {e}{Color.RESET}")
                if not SUPPRESS_DEBUG:
                    print(f"{Color.ERROR}[INTERPRETER] Classification failed after {_retries} attempts: {last_error}{Color.RESET}")
                return None

            quick_action_check = None
            if not (user_input.lower() in ['look', 'l', 'examine scene', 'scan', 'ua', 'sheet', 
                                          'people', 'who', 'map', 'show map', 'view map', 'compact map', 
                                          'small map', 'mini map', 'quit', 'exit', 'q', 'story', 'recap'] or user_input.startswith('/')):
                quick_action_check = _strict_detect_inquiry_or_action(user_input, actor, None, _retries=3)
                if quick_action_check is None:
                    print(f"{Color.WARNING}I couldn't reliably interpret that action. Please rephrase and try again.{Color.RESET}")
                    continue
            
            # ============================================================
            # CONTINUITY CHECK - FIRST VALIDATION AFTER INPUT
            # ============================================================
            # Check if the action is physically possible given:
            # - Character's current abilities and equipment
            # - Scene constraints and environment
            # - Physical laws (gravity, human limitations, etc.)
            # - Character state (injuries, exhaustion, etc.)
            # This prevents impossible actions like "I fly" without equipment
            # ============================================================
            
            # Skip continuity check for meta commands
            meta_commands = ['look', 'l', 'examine scene', 'scan', 'ua', 'sheet', 
                           'people', 'who', 'map', 'show map', 'view map', 'compact map', 
                           'small map', 'mini map', 'quit', 'exit', 'q', 'story', 'recap']
            is_meta_command = user_input.lower() in meta_commands or user_input.startswith('/')

            if not is_meta_command:
                try:
                    print(f"\n{Color.SYSTEM}═══ Continuity Check ═══{Color.RESET}")
                    
                    # Check if action is physically possible
                    # Prefer a specific reactor when the input targets an in-scene person (enables distance constraints)
                    continuity_reactor = None
                    try:
                        ul = (user_input or '').lower()
                        if available_npcs and ul:
                            best = None
                            best_score = 0
                            for npc in (available_npcs or []):
                                try:
                                    n = (getattr(getattr(npc, 'sheet', None), 'name', None) or '').strip()
                                    o = (getattr(getattr(npc, 'sheet', None), 'occupation', None) or '').strip()
                                    if not n and not o:
                                        continue
                                    score = 0
                                    if n and n.lower() in ul:
                                        score += 3
                                    else:
                                        # Also match on first name token if present
                                        nt = n.split()[0].lower() if n else ''
                                        if nt and nt in ul:
                                            score += 2
                                    if o and o.lower() in ul:
                                        score += 2
                                    # Light role keyword matching
                                    if any(k in ul for k in ['waitress', 'waiter', 'bartender', 'clerk', 'cashier', 'server']) and o:
                                        if any(k in o.lower() for k in ['waitress', 'waiter', 'bartender', 'clerk', 'cashier', 'server']):
                                            score += 2
                                    if score > best_score:
                                        best_score = score
                                        best = npc
                                except Exception:
                                    continue
                            if best_score > 0:
                                continuity_reactor = best
                    except Exception:
                        continuity_reactor = None

                    # Note: reactor is None for solo actions (checking against environment/physics)
                    try:
                        is_contested = bool(quick_action_check and quick_action_check.get('input_type') == 'contested_action')
                        if is_contested and continuity_reactor is not None and (user_input or '').strip():
                            ul = (user_input or '').lower()
                            needs_touch = any(k in ul for k in (
                                'carry', 'pick up', 'pickup', 'grab', 'drag', 'lift', 'haul', 'shove', 'push', 'pull',
                                'punch', 'hit', 'kick', 'strike', 'wrestle', 'tackle', 'pin', 'choke', 'stab', 'slash',
                                'bite', 'hug', 'hold'
                            ))
                            if needs_touch:
                                # IMPORTANT: exchanges commit movement only at Step 6 (outcome), not Step 1/2/4 (attempts).
                                # Record a pending movement intent and apply it after Step 6 is produced.
                                try:
                                    target_name = str(getattr(getattr(continuity_reactor, 'sheet', None), 'name', '') or '').strip()
                                except Exception:
                                    target_name = ''
                                dest_target = None
                                try:
                                    if quick_action_check and quick_action_check.get('movement_target'):
                                        dest_target = str(quick_action_check.get('movement_target') or '').strip()
                                except Exception:
                                    dest_target = None

                                try:
                                    if target_name:
                                        pending = {
                                            'type': 'contested_touch',
                                            'target_name': target_name,
                                            'destination': dest_target,
                                            'raw_user_input': str(user_input or ''),
                                        }
                                        try:
                                            setattr(encounter_checker.current_context, 'pending_exchange_spatial_intent', pending)
                                        except Exception:
                                            pass
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    continuity_result = conductor.enforce_continuity(
                        user_input=user_input,
                        proactor=actor,
                        reactor=continuity_reactor
                    )
                    
                    judgment = continuity_result.get('judgment', 'Possible')
                    justification = continuity_result.get('justification', '')
                    
                    print(f"{Color.SYSTEM}Judgment: {judgment}{Color.RESET}")
                    if justification:
                        print(f"{Color.SYSTEM}Reason: {justification}{Color.RESET}")
                    
                    # If action is NOT POSSIBLE, generate failure narrative and skip to next turn
                    if judgment == 'Not Possible':
                        print(f"{Color.WARNING}✗ Action is not physically possible{Color.RESET}")
                        
                        # Generate continuity failure narrative
                        try:
                            failure_narrative = narrator.generate_continuity_failure_narrative(
                                actor=actor,
                                attempted_action=user_input,
                                reason=justification,
                                scene_description=scene_description,
                                time_context=master_time.get_current_time_context() if master_time else None
                            )
                            
                            if failure_narrative:
                                print(f"\n{Color.NARRATIVE}{failure_narrative}{Color.RESET}\n")
                        except Exception as e:
                            # Fallback to simple justification if narrative generation fails
                            print(f"\n{Color.NARRATIVE}💭 {justification}{Color.RESET}")

                        # Generate internal voice using the existing unified system (no hardcoded voice text)
                        try:
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=failure_narrative or justification,
                                function_hint="solution",
                                predicament=f"Cannot do: {user_input} - {justification}",
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            display_internal_voice_box(internal_voice)
                        except Exception:
                            pass
                        
                        # Skip to next turn without processing action
                        continue
                    else:
                        print(f"{Color.SUCCESS}✓ Action is possible - proceeding{Color.RESET}")
                        
                except Exception as e:
                    print(f"{Color.WARNING}⚠️  Continuity check failed: {e}{Color.RESET}")
                    # On error, allow action to proceed (fail open for better UX)
                    print(f"{Color.SYSTEM}Proceeding with action...{Color.RESET}")
            
            # On-demand quick commands (no time advancement)
            if user_input.lower() in ['look', 'l', 'examine scene', 'scan']:
                print(f"\n{Color.SCENE} FULL SCENE DESCRIPTION:{Color.RESET}")
                display_scene = _convert_ua_to_second_person(scene_description, actor.sheet.name)
                print(f"{Color.NARRATIVE}{display_scene}{Color.RESET}")
                # Show objects/furniture in the location from the map
                try:
                    obstacle_context = get_obstacle_names_for_narrative()
                    if obstacle_context:
                        print(f"\n{Color.INFO}📦 {obstacle_context}{Color.RESET}")
                except Exception:
                    pass
                continue
            if user_input.lower() in ['ua', 'sheet']:
                print(f"\n{Color.INFO} Your Character Sheet:{Color.RESET}")
                actor.sheet.display_detailed()
                continue
            if user_input.lower() in ['/story', 'story', 'recap', '/recap']:
                print(f"\n{Color.NARRATIVE}📖 STORY RECAP:{Color.RESET}")
                try:
                    story_recap = narrative_context_manager.get_context_for_llm(
                        use_all_events=True,  # Get ALL events from entire session
                        importance_threshold="notable"  # Only notable+ events
                    )
                    if story_recap:
                        print(f"{Color.NARRATIVE}{story_recap}{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}No significant story events yet.{Color.RESET}")
                except Exception as e:
                    print(f"{Color.ERROR}Could not generate story recap: {e}{Color.RESET}")
                continue
            if user_input.lower() in ['people', 'who']:
                if available_npcs:
                    print(f"\n{Color.INFO} People in the area:{Color.RESET}")
                    for n in available_npcs:
                        try:
                            _display_actor_sheet_simple(n.sheet)
                        except Exception:
                            print(f"  - {getattr(n.sheet, 'name', 'Someone')}")
                else:
                    print(f"{Color.INFO}No one else is currently nearby.{Color.RESET}")
                continue
            
            # Display key memories
            if user_input.lower() in ['memories', 'recall', '/mem']:
                print(f"\n{Color.INFO}🔑 KEY MEMORIES:{Color.RESET}")
                try:
                    from key_memories_system import get_key_memories
                    key_memories_system = get_key_memories()
                    
                    # Get all memories for this actor (try multiple tag formats)
                    actor_tag = actor.sheet.name.lower().replace(" ", "_").replace("'", "").replace('"', '')
                    actor_tag_alt = actor.sheet.name.lower().replace(" ", "_")  # Alternative format
                    actor_memories = [
                        m for m in key_memories_system.memories.values()
                        if actor_tag in m.tags or actor_tag_alt in m.tags or "character_background" in m.tags or "initial_memory" in m.tags
                    ]
                    
                    if actor_memories:
                        # Sort by importance then recency
                        importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
                        actor_memories.sort(key=lambda m: (
                            importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
                            -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp
                        ))
                        
                        for i, memory in enumerate(actor_memories, 1):
                            importance_value = memory.importance.value if hasattr(memory.importance, 'value') else memory.importance
                            importance_icon = {"critical": "🔴", "important": "🟡", "notable": "🔵", "routine": "⚪"}.get(importance_value, "📝")
                            print(f"\n{importance_icon} {Color.STATUS}{memory.title}{Color.RESET}")
                            print(f"{Color.NARRATIVE}{memory.description}{Color.RESET}")
                            if hasattr(memory, 'location') and memory.location:
                                print(f"{Color.SYSTEM}Location: {memory.location}{Color.RESET}")
                    else:
                        # Fallback: Try to load from InternalVoiceCreatorAgent storage
                        try:
                            import json
                            mem_file = Path("./simulation_data/memories/internal_voice/created_memories.json")
                            if mem_file.exists():
                                with open(mem_file, 'r', encoding='utf-8') as f:
                                    created_memories = json.load(f)
                                if created_memories:
                                    print(f"{Color.INFO}(Showing memories from initial generation){Color.RESET}")
                                    for category, mems in created_memories.items():
                                        if mems:
                                            print(f"\n{Color.STATUS}📁 {category.upper()}{Color.RESET}")
                                            for mem in mems:
                                                content = mem.get('content', str(mem))
                                                tone = mem.get('emotional_tone', 'neutral')
                                                print(f"{Color.NARRATIVE}  • {content}{Color.RESET}")
                                                print(f"{Color.SYSTEM}    (tone: {tone}){Color.RESET}")
                                else:
                                    print(f"{Color.WARNING}No memories recorded yet.{Color.RESET}")
                            else:
                                print(f"{Color.WARNING}No memories recorded yet.{Color.RESET}")
                        except Exception as fallback_e:
                            print(f"{Color.WARNING}No memories recorded yet.{Color.RESET}")
                except Exception as e:
                    print(f"{Color.ERROR}Could not retrieve memories: {e}{Color.RESET}")
                continue
            
            # Context health check command
            if user_input.lower() in ['/context clear_mentions', '/ctx clear_mentions', 'context clear_mentions', '/ctx clear', '/context clear']:
                try:
                    _clear_mentioned_actors()
                    print(f"{Color.SUCCESS}✓ Cleared mentioned actors{Color.RESET}")
                except Exception as e:
                    print(f"{Color.ERROR}Error clearing mentioned actors: {e}{Color.RESET}")
                continue

            if user_input.lower() in ['/context', '/ctx', 'context']:
                try:
                    from persistent_context_manager import get_context_health_report, sync_context_with_tracker
                    
                    print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                    print(f"{Color.SYSTEM}📋 CONTEXT HEALTH REPORT{Color.RESET}")
                    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")
                    
                    report = get_context_health_report()
                    
                    # Status indicator
                    status_colors = {"healthy": Color.SUCCESS, "warning": Color.WARNING, "degraded": Color.ERROR, "error": Color.ERROR}
                    status_icons = {"healthy": "✅", "warning": "⚠️", "degraded": "🔶", "error": "❌"}
                    status_color = status_colors.get(report["status"], Color.INFO)
                    status_icon = status_icons.get(report["status"], "❓")
                    print(f"\n{status_color}Status: {status_icon} {report['status'].upper()}{Color.RESET}")
                    
                    # Stats
                    stats = report.get("stats", {})
                    if stats:
                        print(f"\n{Color.INFO}📊 Stats:{Color.RESET}")
                        print(f"   Session ID: {stats.get('session_id', 'N/A')}")
                        print(f"   Location: {stats.get('location', 'N/A')}")
                        print(f"   Scene Length: {stats.get('scene_length', 0)} chars")
                        print(f"   NUAs Present: {stats.get('nuas_present', 0)}")
                        print(f"   Recent Events: {stats.get('recent_events', 0)}")
                        print(f"   Recent Narratives: {stats.get('recent_narratives', 0)}")
                        print(f"   Update Count: {stats.get('update_count', 0)}")
                        print(f"   Saved Locations: {stats.get('saved_locations', 0)}")
                        print(f"   Last Updated: {stats.get('last_updated', 'Never')}")
                    
                    # Issues
                    if report.get("issues"):
                        print(f"\n{Color.ERROR}❌ Issues:{Color.RESET}")
                        for issue in report["issues"]:
                            print(f"   • {issue}")
                    
                    # Warnings
                    if report.get("warnings"):
                        print(f"\n{Color.WARNING}⚠️ Warnings:{Color.RESET}")
                        for warning in report["warnings"]:
                            print(f"   • {warning}")
                    
                    # Offer sync if there are issues
                    if report["status"] in ["degraded", "error"]:
                        print(f"\n{Color.INFO}💡 Tip: Use '/context sync' to attempt recovery from tracker{Color.RESET}")

                    # Mentioned actors (debug visibility)
                    try:
                        cm = get_context_manager()
                        mentioned = []
                        try:
                            mentioned = cm.get_mentioned_actors() if cm else []
                        except Exception:
                            mentioned = []
                        print(f"\n{Color.INFO}🧩 Mentioned Actors:{Color.RESET}")
                        if not mentioned:
                            print("   (none)")
                        else:
                            for e in mentioned[:15]:
                                try:
                                    nm = str(e.get('name', '') or '').strip()
                                    if not nm:
                                        continue
                                    try:
                                        tags = list(e.get('location_tags') or [])
                                    except Exception:
                                        tags = []
                                    tags = [str(t).strip() for t in tags if str(t).strip()]
                                    tags_text = ", ".join(tags) if tags else "unknown"
                                    low = nm.lower()
                                    if low.startswith('role:'):
                                        role = nm.split(':', 1)[1].strip() if ':' in nm else nm
                                        if role:
                                            print(f"   - (role) {role} (where: {tags_text})")
                                    else:
                                        print(f"   - {nm} (where: {tags_text})")
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    
                    print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                    
                except Exception as e:
                    print(f"{Color.ERROR}Error getting context report: {e}{Color.RESET}")
                continue
            
            # Context sync command
            if user_input.lower() in ['/context sync', '/ctx sync', 'context sync']:
                try:
                    from persistent_context_manager import sync_context_with_tracker
                    
                    print(f"\n{Color.SYSTEM}🔄 Syncing context with tracker...{Color.RESET}")
                    success = sync_context_with_tracker(tracker)
                    
                    if success:
                        print(f"{Color.SUCCESS}✓ Context sync complete{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}Context sync had issues - check logs above{Color.RESET}")
                        
                except Exception as e:
                    print(f"{Color.ERROR}Error syncing context: {e}{Color.RESET}")
                continue

            # Everlasting context debug commands (no time advancement)
            if user_input.lower() in ['/everlasting', '/ever']:
                try:
                    print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                    print(f"{Color.SYSTEM}🧠 EVERLASTING CONTEXT (DEBUG){Color.RESET}")
                    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}\n")
                    txt = everlasting_context_text
                    try:
                        npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
                        if hasattr(world_state, 'get_everlasting_context'):
                            ev = world_state.get_everlasting_context(
                                present_npcs=npc_names,
                                current_location=scene_description[:50]
                            )
                            txt = str(ev.get('everlasting_context_text') or txt or '')
                    except Exception:
                        pass

                    if txt and str(txt).strip():
                        print(f"{Color.NARRATIVE}{txt}{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}(everlasting_context_text is empty){Color.RESET}")
                    print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}Everlasting debug failed: {e}{Color.RESET}")
                skip_bg_sim_once = True
                continue

            if user_input.lower() in ['/ctxstats', '/everstats']:
                try:
                    npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
                    ev = {}
                    try:
                        if hasattr(world_state, 'get_everlasting_context'):
                            ev = world_state.get_everlasting_context(
                                present_npcs=npc_names,
                                current_location=scene_description[:50]
                            )
                    except Exception:
                        ev = {}

                    recent_events = ev.get('everlasting_recent_world_events') or []
                    recalled = ev.get('everlasting_recalled_memories') or {}

                    print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                    print(f"{Color.SYSTEM}📊 EVERLASTING CONTEXT STATS (DEBUG){Color.RESET}")
                    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")
                    try:
                        print(f"{Color.INFO}Recent world events fetched: {len(list(recent_events))}{Color.RESET}")
                    except Exception:
                        print(f"{Color.INFO}Recent world events fetched: ?{Color.RESET}")

                    try:
                        actor_count = len(list(recalled.keys())) if hasattr(recalled, 'keys') else 0
                        mem_total = 0
                        for _, mems in (recalled or {}).items():
                            try:
                                mem_total += len(list(mems or []))
                            except Exception:
                                pass
                        print(f"{Color.INFO}Actors recalled: {actor_count} | Memories returned: {mem_total}{Color.RESET}")
                    except Exception:
                        pass

                    try:
                        if recent_events:
                            print(f"\n{Color.INFO}Last world events:{Color.RESET}")
                            for e in list(recent_events)[:8]:
                                try:
                                    et = e.get('event_type')
                                    summ = e.get('summary')
                                    if summ:
                                        print(f"  - [{et}] {summ}")
                                except Exception:
                                    continue
                    except Exception:
                        pass
                    print(f"{Color.SYSTEM}{'='*60}{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}Ctx stats failed: {e}{Color.RESET}")
                skip_bg_sim_once = True
                continue
            
            # Meta command to spawn NUA for testing
            if user_input.lower().startswith('/spawn'):
                try:
                    # Parse optional description from command
                    parts = user_input.split(maxsplit=1)
                    nua_description = parts[1] if len(parts) > 1 else None
                    
                    print(f"\n{Color.SYSTEM}🧪 TEST MODE: Spawning NUA...{Color.RESET}")
                    
                    # Create NUA using scene creator
                    # Build context with existing NUAs and description
                    nua_context = f"Existing NUAs: {', '.join([getattr(getattr(n, 'sheet', None), 'name', str(n)) for n in available_npcs])}\n\n{nua_description}"
                    
                    new_nua = scene_creator.generate_nua(
                        context=nua_context,
                        scene_description=scene_description
                    )
                    
                    if new_nua:
                        print(f"{Color.SUCCESS}✓ Spawned NUA: {_ua_display_name(new_nua, ua_actor=actor)} ({new_nua.sheet.occupation}){Color.RESET}")
                        
                        # Register NUA for persistence and add to available NUAs
                        register_nua(new_nua, available_npcs)
                        
                        # Initialize sympathy
                        if hasattr(actor.sheet, 'update_sympathy'):
                            actor.sheet.update_sympathy(new_nua.sheet.name, 1)  # Neutral start
                        
                        # Add to context manager
                        if hasattr(narrative_context_manager, 'add_nua'):
                            narrative_context_manager.add_nua(new_nua.sheet.name)
                        
                        # Update scene description to include the new NUA
                        nua_intro = f"{_ua_display_name(new_nua, ua_actor=actor)}, a {new_nua.sheet.occupation}, is here."
                        scene_description = f"{scene_description}\n\n{nua_intro}"
                        
                        # Update context manager with new scene
                        if hasattr(narrative_context_manager, 'update_scene_description'):
                            narrative_context_manager.update_scene_description(scene_description)
                        
                        # Display NUA summary
                        _display_actor_sheet_simple(new_nua.sheet)
                    else:
                        print(f"{Color.WARNING}Failed to spawn NUA{Color.RESET}")
                        
                except Exception as e:
                    print(f"{Color.WARNING}Error spawning NUA: {e}{Color.RESET}")
                    import traceback as traceback_module
                    traceback_module.print_exc()
                continue

            # Meta command to generate visualizer prompt (no time advancement)
            # Usage:
            #   /shot <slug>
            #   /shot image <slug>
            #   /shot video <slug>
            # Optional dialogue line:
            #   /shot <slug> | "I didn't do it."
            if user_input.lower().startswith('/shot'):
                try:
                    from visualizer_prompt_system import (
                        build_scene_composition_traits,
                        render_final_image_prompt,
                        render_final_video_prompt,
                    )

                    raw = (user_input or '').strip()
                    rest = raw[5:].strip() if len(raw) >= 5 else ''
                    spoken_line = ''
                    if '|' in rest:
                        left, right = rest.split('|', 1)
                        rest = (left or '').strip()
                        spoken_line = (right or '').strip().strip('"').strip("'")

                    mode = 'video'
                    slug = rest
                    if rest:
                        parts = rest.split()
                        if parts and parts[0].lower() in ['image', 'video']:
                            mode = parts[0].lower()
                            slug = ' '.join(parts[1:]).strip()

                    # Video-first workflow: force /shot to produce video prompts (LTX2).
                    if mode != 'video':
                        mode = 'video'

                    if not slug:
                        print(f"{Color.WARNING}Usage: /shot [image|video] <slug> | <optional spoken line>{Color.RESET}")
                        skip_bg_sim_once = True
                        continue

                    tc = None
                    try:
                        tc = master_time.get_current_time_context() if master_time else None
                    except Exception:
                        tc = None

                    traits = build_scene_composition_traits(
                        slug=slug,
                        actor=actor,
                        scene_description=scene_description,
                        current_location=current_location if 'current_location' in locals() else None,
                        time_context=tc,
                        spoken_line=spoken_line,
                        mode=mode,
                        seed=42,
                        creator_agent=scene_creator,
                    )

                    print(f"\n{Color.SYSTEM}🎬 VISUALIZER TRAITS (JSON){Color.RESET}")
                    try:
                        print(traits)
                    except Exception:
                        import json as _json
                        print(_json.dumps(traits, ensure_ascii=False, indent=2))

                    out = render_final_video_prompt(traits=traits, spoken_line=spoken_line)
                    print(f"\n{Color.SYSTEM}🎞️ FINAL VIDEO PROMPT{Color.RESET}")
                    print(out)

                except Exception as e:
                    print(f"{Color.WARNING}Visualizer command failed: {e}{Color.RESET}")
                skip_bg_sim_once = True
                continue

            if user_input.lower().startswith('/video'):
                try:
                    raw = (user_input or '').strip()
                    rest = raw[6:].strip() if len(raw) >= 6 else ''

                    arg = (rest.split()[0].lower() if rest else '')
                    if arg in ['on', 'off']:
                        globals()['_vis_autogen_enabled'] = (arg == 'on')
                        state = 'ON' if globals().get('_vis_autogen_enabled') else 'OFF'
                        print(f"{Color.SYSTEM}🎞️ Video autogen: {state}{Color.RESET}")
                        skip_bg_sim_once = True
                        continue

                    spoken_line = ''
                    if '|' in rest:
                        left, right = rest.split('|', 1)
                        spoken_line = (right or '').strip().strip('"').strip("'")
                    if not spoken_line:
                        spoken_line = str((_vis_context or {}).get('last_spoken_line') or '')

                    if not (_vis_context and _vis_context.get('ua_actor') and _vis_context.get('scene_description')):
                        print(f"{Color.WARNING}No visualizer context available yet (need a scene).{Color.RESET}")
                        skip_bg_sim_once = True
                        continue

                    try:
                        _maybe_start_visualizer_viewer()
                    except Exception:
                        pass

                    _trigger_realtime_video(
                        ua_actor=_vis_context.get('ua_actor'),
                        scene_description=_vis_context.get('scene_description') or "",
                        current_location=_vis_context.get('current_location') or "",
                        time_context=_vis_context.get('time_context') or {},
                        spoken_line=str(spoken_line or ''),
                        creator_agent=_vis_context.get('creator_agent'),
                        seed=_vis_context.get('seed'),
                    )
                    print(f"{Color.SYSTEM}🎬 Generated video to simulation_data/visualizer/latest.mp4{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}Video command failed: {e}{Color.RESET}")
                skip_bg_sim_once = True
                continue
            # Handle /map, /dist, /pos, /move spatial commands (Rich display - local)
            if user_input.lower().startswith('/map') or user_input.lower().startswith('/dist') or user_input.lower().startswith('/pos') or user_input.lower().startswith('/move'):
                try:
                    if handle_spatial_command(user_input, session_id=tracker.session_id):
                        continue
                except Exception as e:
                    print(f"{Color.WARNING}Spatial command error: {e}{Color.RESET}")
                continue
            
            # World map commands now use pygame world mode
            if user_input.lower() in ['worldmap', 'world map', 'locations', '/world', '/worldmap', '/nearby']:
                try:
                    from pygame_spatial_map import start_pygame_map, get_pygame_map, sync_world_graph

                    if start_pygame_map():
                        sync_world_graph()
                        map_inst = get_pygame_map()
                        try:
                            if map_inst is not None and hasattr(map_inst, 'set_mode'):
                                from pygame_spatial_map import MapMode
                                map_inst.set_mode(MapMode.WORLD)
                        except Exception:
                            pass
                        print(f"{Color.SUCCESS}[MAP] World map opened (TAB toggles LOCAL/WORLD; click node then ENTER to travel){Color.RESET}")
                    else:
                        print(f"{Color.WARNING}[MAP] Failed to start map{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}World map error: {e}{Color.RESET}")
                continue

            # World-level travel info commands (text)
            if user_input.lower().startswith('/travel') or user_input.lower() in ['/nuas', '/npcs']:
                try:
                    current_loc = None
                    try:
                        from spatial_context_system import get_spatial_manager
                        spatial = get_spatial_manager(session_id=tracker.session_id)
                        current_loc = getattr(spatial, 'current_location', None)
                    except Exception:
                        current_loc = None

                    if not current_loc:
                        try:
                            current_loc = tracker.current_location if hasattr(tracker, 'current_location') else None
                        except Exception:
                            current_loc = None

                    if not current_loc:
                        current_loc = scene_description.split('\n')[0][:50]

                    if handle_world_spatial_command(user_input, current_loc, session_id=tracker.session_id):
                        continue
                except Exception as e:
                    print(f"{Color.WARNING}World spatial command error: {e}{Color.RESET}")
                continue
            # ALL MAP COMMANDS NOW USE PYGAME MAP
            if user_input.lower() in ['map', 'show map', 'view map', 'compact map', 'small map', 'mini map', 
                                       '/worldmap',
                                       'worldmap compact', 'world map compact', '/worldmap compact']:
                try:
                    from pygame_spatial_map import start_pygame_map, sync_from_spatial_context, get_pygame_map
                    
                    map_inst = get_pygame_map()
                    if map_inst and map_inst.running:
                        sync_from_spatial_context(session_id=tracker.session_id)
                        print(f"{Color.SUCCESS}[MAP] Pygame map synced{Color.RESET}")
                    else:
                        if start_pygame_map():
                            sync_from_spatial_context(session_id=tracker.session_id)
                            print(f"{Color.SUCCESS}[MAP] Pygame spatial map opened{Color.RESET}")
                            print(f"{Color.INFO}Controls: Scroll=Zoom, Middle-drag=Pan, Click=Select{Color.RESET}")
                        else:
                            print(f"{Color.WARNING}[MAP] Failed to start map{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}[MAP] Error: {e}{Color.RESET}")
                continue
            
            # Pygame spatial map commands
            if user_input.lower() in ['/pmap', 'pmap', 'pygame map', '/pygame']:
                try:
                    from pygame_spatial_map import start_pygame_map, sync_from_spatial_context, sync_world_graph, get_pygame_map
                    
                    map_inst = get_pygame_map()
                    if map_inst and map_inst.running:
                        # Already running - just sync
                        sync_from_spatial_context(session_id=tracker.session_id)
                        sync_world_graph(tracker.session_id)
                        print(f"{Color.SUCCESS}[MAP] Pygame map synced with current location{Color.RESET}")
                    else:
                        # Start the map
                        if start_pygame_map():
                            sync_from_spatial_context(session_id=tracker.session_id)
                            sync_world_graph(tracker.session_id)
                            print(f"{Color.SUCCESS}[MAP] Pygame spatial map window opened{Color.RESET}")
                            print(f"{Color.INFO}Controls: Scroll=Zoom, Middle-drag=Pan, Click=Select{Color.RESET}")
                            print(f"{Color.INFO}Keys: V=Vision, H=Hearing, S=Smell, T=Touch, G=Grid, R=Reset{Color.RESET}")
                            print(f"{Color.INFO}Commands: /pmap context <mode> | /pmap info | /pmap follow | /pmap auto{Color.RESET}")
                        else:
                            print(f"{Color.WARNING}[MAP] Failed to start pygame map{Color.RESET}")
                except ImportError:
                    print(f"{Color.WARNING}[MAP] Pygame map not available. Install pygame: pip install pygame{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}[MAP] Pygame map error: {e}{Color.RESET}")
                continue
            
            if user_input.lower() in ['/pmap close', 'pmap close', '/pygame close']:
                try:
                    from pygame_spatial_map import stop_pygame_map
                    stop_pygame_map()
                    print(f"{Color.INFO}[MAP] Pygame map window closed{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}[MAP] Error closing map: {e}{Color.RESET}")
                continue
            
            # Map context commands
            if user_input.lower().startswith('/pmap context '):
                context_arg = user_input[14:].strip().lower()
                if context_arg in ['combat', 'stealth', 'social', 'exploration', 'travel']:
                    set_map_context(context_arg)
                    print(f"{Color.SUCCESS}[MAP] Context set to '{context_arg}'{Color.RESET}")
                else:
                    print(f"{Color.WARNING}[MAP] Valid contexts: combat, stealth, social, exploration, travel{Color.RESET}")
                continue
            
            if user_input.lower() in ['/pmap autozoom', '/pmap auto']:
                toggle_auto_zoom()
                continue
            
            if user_input.lower() in ['/pmap follow', '/pmap center']:
                toggle_follow_ua()
                continue
            
            if user_input.lower() in ['/pmap info', '/pmap data']:
                try:
                    map_data = get_map_data_for_rag()
                    if map_data:
                        print(f"\n{Color.INFO}📍 MAP DATA:{Color.RESET}")
                        print(f"  Location: {map_data.get('location_name', 'Unknown')}")
                        print(f"  Type: {map_data.get('location_type', 'Unknown')}")
                        print(f"  Dimensions: {map_data.get('dimensions', {})}")
                        print(f"  Context: {map_data.get('context', 'exploration')}")
                        print(f"  Actors: {len(map_data.get('actors', {}))}")
                        print(f"  Obstacles: {len(map_data.get('obstacles', {}))}")
                        
                        # Show actor distances
                        distances = map_data.get('actor_distances', {})
                        if distances:
                            print(f"\n  {Color.INFO}Actor Distances:{Color.RESET}")
                            for dist_info in distances.values():
                                print(f"    {dist_info['actor1']} ↔ {dist_info['actor2']}: {dist_info['distance']:.1f}m")
                    else:
                        print(f"{Color.WARNING}[MAP] No map data available. Open map with /pmap first.{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}[MAP] Error getting map data: {e}{Color.RESET}")
                continue
            
            # Clear trail command
            if user_input.lower() in ['/cleartrail', '/cleartrails', 'cleartrail']:
                try:
                    from spatial_context_system import get_spatial_manager
                    from pygame_spatial_map import get_pygame_map
                    
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    spatial.clear_all_trails()
                    
                    # Also clear trails in pygame map state
                    map_inst = get_pygame_map()
                    if map_inst:
                        for actor_obj in map_inst.state.actors.values():
                            actor_obj.trail.clear()
                            actor_obj.trail_distance = 0.0
                    
                    print(f"{Color.SUCCESS}[MAP] All movement trails cleared{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}[MAP] Error clearing trails: {e}{Color.RESET}")
                continue
            
            # On-demand quick commands (no time advancement)
            if user_input.lower() in ['look', 'l', 'examine scene', 'scan']:
                print(f"\n{Color.SCENE} FULL SCENE DESCRIPTION:{Color.RESET}")
                display_scene = _convert_ua_to_second_person(scene_description, actor.sheet.name)
                print(f"{Color.NARRATIVE}{display_scene}{Color.RESET}")
                # Show objects/furniture in the location from the map
                try:
                    obstacle_context = get_obstacle_names_for_narrative()
                    if obstacle_context:
                        print(f"\n{Color.INFO}📦 {obstacle_context}{Color.RESET}")
                except Exception:
                    pass
                # Do not advance time or counters; re-prompt next loop
                continue
            if user_input.lower() in ['ua', 'sheet']:
                print(f"\n{Color.INFO} Your Character Sheet:{Color.RESET}")
                actor.sheet.display_detailed()
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"{Color.SUCCESS}Thanks for playing UTAS!{Color.RESET}")
                # Save on quit
                try:
                    final_snapshot = {
                        'scene_number': scene_number,
                        'scene_description': scene_description,
                        'scene_updates': scene_updates[-5:],
                        'time_context': time_context,
                        'available_npcs': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                        'actor_state': {
                            'name': actor.sheet.name,
                            'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()}
                        }
                    }
                    req = save_coordinator.create_user_quit_request(final_snapshot)
                    save_coordinator.request_save(req)
                    # Flush pending saves to disk
                    save_coordinator.flush_pending_saves()
                except Exception:
                    pass
                break
            
            # Get current location from persistent context (used throughout this turn)
            current_location = context_manager.context.current_location if hasattr(context_manager.context, 'current_location') else None
            
            # ============================================================
            # EXPLICIT MOVEMENT DETECTION - CRITICAL FOR USER AGENCY
            # ============================================================
            # Check if user EXPLICITLY requested movement in their input
            # This prevents the system from moving the user based on narrative descriptions
            # The narrator should ONLY describe movement if this check returns True
            # ============================================================
            explicit_movement_data = None
            try:
                # Pass quick_action_check to leverage LLM classification
                try:
                    explicit_movement_data = conductor.interpreter.detect_explicit_movement(user_input, quick_action_check)
                except TypeError:
                    # Fallback for old signature (if module not reloaded)
                    explicit_movement_data = conductor.interpreter.detect_explicit_movement(user_input)

                # If the user is vague ("go find food") treat it as an in-place search, not movement.
                def _is_vague_need_movement(_inp: str, _tgt: str) -> bool:
                    try:
                        if not _inp:
                            return False
                        t = (_tgt or '').strip().lower()
                        if not t:
                            return False
                        # Generic needs/intents (NOT destinations)
                        vague_targets = {
                            'food', 'water', 'shelter', 'sleep', 'rest', 'help', 'supplies',
                            'medicine', 'medical', 'safety', 'safety place', 'a safe place',
                            'something to eat', 'something to drink'
                        }
                        if t not in vague_targets:
                            return False
                        inp = _inp.lower()
                        # Explicit destination cues = allow movement
                        if inp.startswith('/travel'):
                            return False
                        if any(p in inp for p in (' go to ', ' head to ', ' walk to ', ' travel to ', ' move to ', ' to the ', ' to a ', ' into the ', ' into a ')):
                            return False
                        # Vague searching intent → default to in-place search
                        if any(k in inp for k in ('find', 'look for', 'search for', 'seek')):
                            return True
                        return False
                    except Exception:
                        return False

                try:
                    if explicit_movement_data and explicit_movement_data.get('has_explicit_movement'):
                        tgt = explicit_movement_data.get('target')
                        if _is_vague_need_movement(user_input, str(tgt or '')):
                            explicit_movement_data['has_explicit_movement'] = False
                            explicit_movement_data['target'] = None
                            try:
                                if quick_action_check and quick_action_check.get('explicit_movement'):
                                    quick_action_check['explicit_movement'] = False
                                    quick_action_check['movement_target'] = None
                            except Exception:
                                pass
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.SYSTEM}[MOVEMENT CHECK] Suppressed vague needs-movement; treating as in-place search{Color.RESET}")
                except Exception:
                    pass
                
                if not SUPPRESS_DEBUG:
                    print(f"{Color.SYSTEM}[MOVEMENT CHECK] Explicit movement: {explicit_movement_data.get('has_explicit_movement', False)}{Color.RESET}")
                    if explicit_movement_data.get('has_explicit_movement'):
                        print(f"{Color.SYSTEM}[MOVEMENT CHECK] Type: {explicit_movement_data.get('movement_type')}, Target: {explicit_movement_data.get('target')}{Color.RESET}")
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[MOVEMENT CHECK] Detection failed: {e}{Color.RESET}")
                explicit_movement_data = {"has_explicit_movement": False}
            
            # Skip intent check for meta commands
            meta_commands = ['look', 'l', 'examine scene', 'scan', 'ua', 'sheet', 
                           'people', 'who', 'map', 'show map', 'view map', 'compact map', 
                           'small map', 'mini map', 'quit', 'exit', 'q', 'story', 'recap']
            # Also skip for commands that start with /
            is_meta_command = user_input.lower() in meta_commands or user_input.startswith('/')
            
            # ============================================================
            # ACTION TYPE DETECTION - Already performed earlier
            # ============================================================
            # Strict mode: action type comes exclusively from the earlier interpreter classification.
            if not SUPPRESS_DEBUG and quick_action_check:
                print(f"{Color.SYSTEM}[ACTION TYPE] Quick check: {quick_action_check.get('input_type', 'unknown')}{Color.RESET}")
            
            # ============================================================
            # MAP CONTEXT AUTO-ZOOM - Adjust map based on action type
            # ============================================================
            try:
                if quick_action_check:
                    input_type = quick_action_check.get('input_type', '')
                    fallible_sub = quick_action_check.get('fallible_subtype', '')
                    
                    # Determine map context based on action type
                    if input_type == 'contested_action':
                        set_map_context("combat")  # Zoom in for contested/combat
                    elif fallible_sub in ['social', 'dialogue']:
                        set_map_context("social")  # Tight zoom for conversation
                    elif quick_action_check.get('explicit_movement'):
                        set_map_context("exploration")  # Normal zoom for movement
                    else:
                        set_map_context("exploration")  # Default
            except Exception:
                pass  # Map context is non-critical
            
            # ============================================================
            # DIEGETIC TRANSITION SYSTEM - Prevent Time Skips
            # ============================================================
            # ONLY runs for given/fallible actions
            # Contested actions skip this entirely and proceed to exchange
            # For sweeping intents ("finish breakfast and get to garage"),
            # pauses at diegetic boundaries with inner voice + experience
            # For atomic intents ("open the door"), proceeds to normal flow
            # ============================================================
            
            is_contested = quick_action_check and quick_action_check.get('input_type') == 'contested_action'
            
            if not is_meta_command and not is_contested:
                try:
                    # Initialize transition system if needed
                    if transition_system is None:
                        print(f"{Color.SYSTEM}[DIEGETIC] Initializing transition system...{Color.RESET}")
                        from openrouter_config import OpenRouterConfig
                        transition_system = DiegeticTransitionSystem(
                            llm_client=OpenRouterConfig.create_role_client("narration"),
                            model=OpenRouterConfig.get_model_for_role("narration"),
                            logger=logger
                        )
                        print(f"{Color.SUCCESS}[DIEGETIC] Transition system initialized{Color.RESET}")
                    
                    print(f"{Color.SYSTEM}[DIEGETIC] Analyzing intent scope for: '{user_input}'{Color.RESET}")
                    
                    # Analyze intent scope
                    intent_analysis = transition_system.analyze_intent_scope(
                        user_input=user_input,
                        scene_context=scene_description,
                        actor_personality=actor.sheet.personality_traits
                    )
                    
                    print(f"{Color.SYSTEM}[DIEGETIC] Analysis complete:{Color.RESET}")
                    print(f"{Color.SYSTEM}  Scope: {intent_analysis['scope'].value}{Color.RESET}")
                    print(f"{Color.SYSTEM}  Reasoning: {intent_analysis['reasoning']}{Color.RESET}")
                    print(f"{Color.SYSTEM}  Estimated Steps: {intent_analysis['estimated_steps']}{Color.RESET}")
                    print(f"{Color.SYSTEM}  Needs Breakdown: {intent_analysis['needs_breakdown']}{Color.RESET}")
                    
                    # Handle ONLY sweeping intents with diegetic pause
                    # Atomic intents execute immediately without pause
                    is_travel_like = bool(
                        explicit_movement_data
                        and explicit_movement_data.get('has_explicit_movement')
                        and explicit_movement_data.get('target')
                    )

                    # Local movement targets (objects/features inside the current scene) must NOT be treated as world travel.
                    # If the target is mentioned in the current scene/perceptual/internal voice text OR exists as a zone/obstacle
                    # in the current spatial context, bypass the travel validator entirely.
                    try:
                        if is_travel_like:
                            raw_target = str(explicit_movement_data.get('target') or '').strip()
                            tl = raw_target.lower()
                            tl = tl.strip('"\'')

                            def _looks_like_local_target() -> bool:
                                if not tl:
                                    return False

                                # 0) If the movement target is a PRESENT ACTOR, it is local movement (not world travel)
                                # This prevents actor names (e.g., "Garruk Ironbrow") from being treated as destinations.
                                try:
                                    # UA name
                                    ua_name_l = str(getattr(actor.sheet, 'name', '') or '').strip().lower()
                                    if ua_name_l and (tl == ua_name_l or tl in ua_name_l or ua_name_l in tl):
                                        return True
                                except Exception:
                                    pass

                                try:
                                    for _npc in (available_npcs or []):
                                        nm = str(getattr(getattr(_npc, 'sheet', None), 'name', '') or '').strip().lower()
                                        if not nm:
                                            continue
                                        if tl == nm or tl in nm or nm in tl:
                                            return True
                                except Exception:
                                    pass

                                # 1) Mentioned in the authoritative texts (scene + recent perceptual additions)
                                try:
                                    if tl and tl in (scene_description or '').lower():
                                        return True
                                except Exception:
                                    pass

                                # 2) Mentioned in recent internal voice (debug/grounding: treat as existing concept)
                                try:
                                    if context_manager and hasattr(context_manager, 'get_recent_internal_voices'):
                                        for e in context_manager.get_recent_internal_voices(count=8) or []:
                                            v = str((e or {}).get('voice', '') or '').lower()
                                            if tl and tl in v:
                                                return True
                                except Exception:
                                    pass

                                # 3) Exists as a named obstacle/zone in the current spatial context
                                try:
                                    from spatial_context_system import get_spatial_manager
                                    spatial_tmp = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                    ctx = spatial_tmp.get_current_context() if spatial_tmp else None
                                    dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                                    if dims:
                                        # Prefer exact name matches; fall back to substring match.
                                        obs = getattr(dims, 'obstacles', {}) or {}
                                        zones = getattr(dims, 'zones', {}) or {}
                                        for dct in (obs, zones):
                                            for k, obj in (dct or {}).items():
                                                nm = ''
                                                try:
                                                    nm = str(getattr(obj, 'obstacle_name', None) or getattr(obj, 'zone_name', None) or k or '').strip().lower()
                                                except Exception:
                                                    nm = str(k or '').strip().lower()
                                                if not nm:
                                                    continue
                                                if tl == nm or tl in nm or nm in tl:
                                                    return True
                                except Exception:
                                    pass

                                return False

                            if _looks_like_local_target():
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.SYSTEM}[MOVEMENT] Treating target as LOCAL scene feature (not world travel): {raw_target}{Color.RESET}")
                                is_travel_like = False

                                try:
                                    if explicit_movement_data and explicit_movement_data.get('has_explicit_movement') and explicit_movement_data.get('target'):
                                        tgt_txt = str(explicit_movement_data.get('target') or '').strip()
                                        tgt_l = tgt_txt.lower()

                                        is_floor_change = False
                                        floor_delta = 0
                                        if any(k in tgt_l for k in ('upstairs', 'up stairs', 'up the stairs', 'staircase up', 'stairs up', 'floor 2', 'second floor', 'upper floor', 'go up')):
                                            is_floor_change = True
                                            floor_delta = 1
                                        elif any(k in tgt_l for k in ('downstairs', 'down stairs', 'down the stairs', 'staircase down', 'stairs down', 'basement', 'cellar', 'lower level', 'go down')):
                                            is_floor_change = True
                                            floor_delta = -1

                                        if is_floor_change:
                                            try:
                                                from spatial_context_system import get_spatial_manager
                                                sm = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                                if sm:
                                                    new_loc = sm.change_floor(delta=floor_delta)
                                                    try:
                                                        from pygame_spatial_map import sync_from_spatial_context
                                                        sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                                    except Exception:
                                                        pass
                                                    if new_loc and not SUPPRESS_DEBUG:
                                                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {_ua_display_name(actor, ua_actor=actor)} changed floors → {new_loc}")
                                            except Exception:
                                                pass
                                        else:
                                            from agents.architect_agent import move_actor_on_map
                                            moved = move_actor_on_map(
                                                actor.sheet.name,
                                                tgt_txt,
                                                user_input or '',
                                                session_id=tracker.session_id if tracker else None
                                            )
                                            if moved and not SUPPRESS_DEBUG:
                                                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {_ua_display_name(actor, ua_actor=actor)} moved to '{explicit_movement_data.get('target')}'")
                                except Exception:
                                    pass
                    except Exception:
                        pass

                    # RAG-LOCK: travel destination must exist in the world.
                    if is_travel_like:
                        try:
                            travel_target = str(explicit_movement_data.get('target') or '').strip()
                            if travel_target:
                                rag_sys = None
                                try:
                                    rag_sys = getattr(conductor, 'rag_system', None)
                                except Exception:
                                    rag_sys = None

                                if rag_sys:
                                    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory

                                    def _dest_exists_in_rag(dest: str) -> bool:
                                        dl = dest.lower().strip()
                                        if not dl:
                                            return False
                                        # Per-run generated cities are treated as grounded.
                                        try:
                                            from worldbuilding_helpers import load_generated_cities
                                            for c in load_generated_cities() or []:
                                                if dl == str(c).lower().strip():
                                                    return True
                                        except Exception:
                                            pass
                                        # First try category-filtered retrieval for cities/places.
                                        try:
                                            for cat in (WorldbuildingCategory.CITIES, WorldbuildingCategory.PLACES):
                                                ctx = rag_sys.get_context_for_llm(
                                                    query=dest,
                                                    max_tokens=120,
                                                    category_filter=cat,
                                                    include_related=False,
                                                ) or ''
                                                if dl in ctx.lower():
                                                    return True
                                        except Exception:
                                            pass
                                        # Fallback: scan loaded documents (exact substring match).
                                        try:
                                            docs = getattr(rag_sys, 'documents', {}) or {}
                                            for doc in docs.values():
                                                content = getattr(doc, 'content', '') or ''
                                                if dl in content.lower():
                                                    return True
                                        except Exception:
                                            pass
                                        return False

                                    def _infer_common_destination(user_input_text: str, raw_target: str, current_loc: str) -> str:
                                        """Infer a safe, common destination label from intent.

                                        This is NOT freeform. It only returns a destination from a small allowlist
                                        of "common places" that plausibly exist in most settlements.
                                        """
                                        import re

                                        text = f"{user_input_text} {raw_target}".lower()
                                        text = re.sub(r"\s+", " ", text).strip()

                                        # Canonical labels we are allowed to create/travel to.
                                        # Source of truth is dynamic registry (persisted) + RAG (era-aware).
                                        # We keep a small fallback only.
                                        common_places: dict[str, list[str]] = {}

                                        # 1) Dynamic persisted registry (SQLite/JSON)
                                        try:
                                            from worldbuilding_helpers import load_common_place_types
                                            reg = load_common_place_types() or {}
                                            if isinstance(reg, dict):
                                                for k, v in reg.items():
                                                    kk = str(k).strip().lower()
                                                    if not kk:
                                                        continue
                                                    if isinstance(v, list):
                                                        syns = [str(p).strip().lower() for p in v if str(p).strip()]
                                                    elif isinstance(v, str):
                                                        syns = [p.strip().lower() for p in v.split(',') if p.strip()]
                                                    else:
                                                        syns = []
                                                    if syns:
                                                        common_places[kk] = syns
                                        except Exception:
                                            pass

                                        # 2) RAG CIVILIZATION document
                                        try:
                                            rag_promote: dict[str, list[str]] = {}
                                            civ_ctx = rag_sys.get_context_for_llm(
                                                query="COMMON PLACE TYPES",
                                                max_tokens=450,
                                                category_filter=WorldbuildingCategory.CIVILIZATION,
                                                include_related=False,
                                            ) or ""
                                            for ln in civ_ctx.splitlines():
                                                s = ln.strip()
                                                if not s.startswith(('-', '•', '*')):
                                                    continue
                                                s = s.lstrip('-•*').strip()
                                                if ':' not in s:
                                                    continue
                                                lhs, rhs = s.split(':', 1)
                                                key = lhs.strip().lower()
                                                rhs = rhs.strip()
                                                if not key or not rhs:
                                                    continue
                                                # Split by commas; accept that some synonyms may contain spaces.
                                                syns = [p.strip().lower() for p in rhs.split(',') if p.strip()]
                                                if syns:
                                                    if key in common_places:
                                                        # Merge
                                                        cur = common_places.get(key, [])
                                                        for ss in syns:
                                                            if ss not in cur:
                                                                cur.append(ss)
                                                        common_places[key] = cur
                                                    else:
                                                        common_places[key] = syns

                                                    # Record for auto-promotion to persisted registry
                                                    try:
                                                        rag_promote[key] = list(common_places.get(key) or syns)
                                                    except Exception:
                                                        pass

                                            # Auto-promote: persist any RAG-derived common place types.
                                            try:
                                                if rag_promote:
                                                    from worldbuilding_helpers import register_common_place_type
                                                    for k, v in rag_promote.items():
                                                        try:
                                                            register_common_place_type(k, list(v) if isinstance(v, list) else [])
                                                        except Exception:
                                                            continue

                                                    try:
                                                        _dbg = (__import__('os').getenv('REALITAS_DEBUG_COMMON_PLACE_PROMOTION') or '').strip()
                                                        if _dbg in ('1', 'true', 'True', 'yes', 'YES'):
                                                            _keys = sorted([str(x) for x in rag_promote.keys()])
                                                            print(f"[COMMON PLACE PROMOTION] Promoted {len(_keys)} type(s) from RAG: {_keys}")
                                                    except Exception:
                                                        pass
                                            except Exception:
                                                pass
                                        except Exception:
                                            pass

                                        if not common_places:
                                            common_places = {
                                                "street": ["street", "road", "outside", "exit", "leave"],
                                                "market": ["market", "bazaar", "stalls"],
                                                "food_place": ["food", "eat", "meal", "kitchen"],
                                            }

                                        # Score intent by full input.
                                        scores: dict[str, int] = {k: 0 for k in common_places.keys()}
                                        for label, keys in common_places.items():
                                            for k in keys:
                                                if k in text:
                                                    scores[label] += 2

                                        # Extra intent weighting: if they explicitly ask for food, prefer food_place when available.
                                        if any(w in text for w in ("eat", "food", "restaurant", "kitchen", "cookhouse", "hungry")):
                                            if "food_place" in scores:
                                                scores["food_place"] += 3
                                        # If they explicitly ask to leave/exit, prefer street.
                                        if any(w in text for w in ("leave", "exit", "outside", "head out", "step out")):
                                            scores["street"] += 2

                                        # If they said "street or kitchens" we pick based on best-scoring intent.
                                        best = None
                                        best_score = 0
                                        for k, v in scores.items():
                                            if v > best_score:
                                                best = k
                                                best_score = v

                                        if not best or best_score <= 0:
                                            return ""

                                        # Convert to a readable location label.
                                        # We want one per settlement/city, not one per room.
                                        settlement = ""
                                        try:
                                            settlement = str(getattr(actor.sheet, 'location', '') or '').strip()
                                        except Exception:
                                            settlement = ""
                                        if not settlement:
                                            settlement = "Unknown Settlement"

                                        # Human-readable names (allow RAG keys to remain stable while display stays natural)
                                        display = {
                                            "food_place": "Cookhouse",
                                            "guard_post": "Guard Post",
                                        }.get(best, best.replace('_', ' ').title())

                                        return f"{display} ({settlement})"

                                    inferred_common = False
                                    if not _dest_exists_in_rag(travel_target):
                                        # Intent-based "common places" bridge:
                                        # If the user asked for a generic but plausible place (street/food/etc),
                                        # infer a safe destination label and allow travel instead of denying.
                                        try:
                                            inferred = _infer_common_destination(user_input, travel_target, current_location or "")
                                            if inferred:
                                                explicit_movement_data['target'] = inferred
                                                inferred_common = True
                                                if not SUPPRESS_DEBUG:
                                                    print(f"{Color.SYSTEM}[TRAVEL] Inferred common destination from intent: {inferred}{Color.RESET}")
                                                # Allow the travel to proceed (location creation happens downstream).
                                                travel_target = inferred
                                        except Exception:
                                            pass

                                        # If the target is explicitly mentioned in the current authoritative text,
                                        # treat it as a discovered world location (even if it's not in RAG).
                                        # Example: "a tavern down the road" -> user can travel to "tavern".
                                        try:
                                            tl_tt = travel_target.lower().strip()
                                            if tl_tt and (tl_tt in (scene_description or '').lower()):
                                                from location_distance_tracker import get_location_tracker
                                                from location_distance_tracker import LocationType, TravelMethod

                                                world_tracker = get_location_tracker(tracker.session_id if tracker else None)
                                                origin_loc = (current_location or getattr(actor.sheet, 'location', None) or 'Current Area')

                                                text_l = (scene_description or '').lower()
                                                blocks = 3.0
                                                if any(k in text_l for k in ('next door', 'next-door', 'adjacent')):
                                                    blocks = 1.0
                                                elif any(k in text_l for k in ('down the road', 'nearby', 'a short walk', 'short walk', 'close by')):
                                                    blocks = 3.0
                                                elif any(k in text_l for k in ('across town', 'across the city', 'far', 'distant')):
                                                    blocks = 12.0

                                                dest_type = LocationType.UNKNOWN
                                                if any(k in tl_tt for k in ('tavern', 'inn', 'pub', 'bar')):
                                                    dest_type = LocationType.ENTERTAINMENT
                                                elif any(k in tl_tt for k in ('market', 'bazaar', 'shop', 'store')):
                                                    dest_type = LocationType.COMMERCIAL
                                                elif any(k in tl_tt for k in ('temple', 'abbey', 'church', 'hospital', 'ward')):
                                                    dest_type = LocationType.INSTITUTIONAL
                                                elif any(k in tl_tt for k in ('street', 'road', 'alley', 'plaza')):
                                                    dest_type = LocationType.OUTDOOR

                                                try:
                                                    world_tracker.add_location(travel_target, location_type=dest_type, description='Mentioned in narration')
                                                except Exception:
                                                    pass

                                                try:
                                                    minutes = blocks * 3.0
                                                    world_tracker.record_travel(origin_loc, travel_target, travel_time_minutes=minutes, method=TravelMethod.WALKING, route_description='Mentioned in narration')
                                                except Exception:
                                                    pass

                                                inferred_common = True
                                                if not SUPPRESS_DEBUG:
                                                    print(f"{Color.SYSTEM}[TRAVEL] Promoted narrated destination to discovered world location: {travel_target}{Color.RESET}")
                                        except Exception:
                                            pass

                                    # If we inferred a common destination, treat it as valid by definition (RAG-driven allowlist).
                                    # Otherwise, if we still don't recognize it, deny.
                                    if (not inferred_common) and (not _dest_exists_in_rag(travel_target)):
                                        print(f"{Color.WARNING}═══ Continuity Check ═══{Color.RESET}")
                                        print(f"Judgment: Not Possible")
                                        deny_reason = f"That destination does not exist in this world: {travel_target}"
                                        print(f"Reason: {deny_reason}")
                                        print(f"{Color.ERROR}✗ Travel denied (unknown destination){Color.RESET}")
                                        try:
                                            # Give a small hint of valid destinations without inventing.
                                            cities_ctx = rag_sys.get_context_for_llm(
                                                query="list major cities settlements",
                                                max_tokens=120,
                                                category_filter=WorldbuildingCategory.CITIES,
                                                include_related=False,
                                            ) or ''
                                            if cities_ctx.strip():
                                                print(f"{Color.INFO}Known cities (from lore):{Color.RESET}\n{cities_ctx.strip()}")
                                        except Exception:
                                            pass

                                        # Produce diegetic failure narration + internal voice like other impossible actions.
                                        try:
                                            # Travel-specific failure narrative (avoid the generic "search possessions" framing).
                                            failure_narrative = (
                                                f"You start to move with purpose, then slow. The name {travel_target!r} doesn't match any sign, route, or habit you know. "
                                                f"After a few uncertain steps, you stop and re-check your bearings, realizing you can't set out for a place that you don't even know exists."
                                            )
                                            print(f"\n{Color.NARRATIVE}{failure_narrative}{Color.RESET}\n")
                                        except Exception:
                                            failure_narrative = deny_reason

                                        try:
                                            internal_voice = generate_unified_internal_voice(
                                                actor=actor,
                                                narrator=narrator,
                                                scene_description=scene_description,
                                                user_action=user_input,
                                                action_outcome=f"{failure_narrative}\n\nIMPORTANT: Do not repeat the denied destination name; refer to it generically (e.g., 'that place').",
                                                function_hint="solution",
                                                predicament=f"Cannot travel: unknown destination - {deny_reason}. Do not repeat the denied destination name.",
                                                urgency="normal",
                                                failure_tracker=failure_tracker,
                                                narrative_context_manager=narrative_context_manager
                                            )
                                            display_internal_voice_box(internal_voice)
                                        except Exception:
                                            pass

                                        continue
                        except Exception:
                            pass

                    if intent_analysis['needs_breakdown'] and not is_travel_like:
                        print(f"{Color.WARNING}[DIEGETIC] SWEEPING INTENT DETECTED - Generating pause...{Color.RESET}")
                        
                        # Get recent narrative context instead of full scene to avoid repetition
                        recent_context = narrative_context_manager.get_context_for_llm(
                            lookback_events=3,
                            importance_threshold="routine"
                        )

                        recent_context = _merge_contexts(recent_context, everlasting_context_text, max_chars=1800)
                        
                        pause_data = transition_system.generate_diegetic_pause(
                            user_input=user_input,
                            scene_context=recent_context if recent_context else scene_description[-500:],  # Last 500 chars if no context
                            actor_name=actor.sheet.name,
                            actor_personality=actor.sheet.personality_traits,
                            current_location=current_location or "Unknown Location",
                            previous_inner_voice=last_inner_voice  # Pass previous inner voice for consistency
                        )
                        
                        print(f"{Color.SUCCESS}[DIEGETIC] Pause generated, displaying...{Color.RESET}")
                        
                        # Update last inner voice for consistency
                        last_inner_voice = pause_data.get('inner_voice')
                        
                        # Display pause and wait for next user input
                        display_diegetic_pause(pause_data, actor.sheet.name)
                        
                        # Record this as a narrative event (intent only, not experience to avoid repetition)
                        from narrative_context_system import NarrativeEventType, NarrativeImportance
                        narrative_context_manager.add_narrative_event(
                            event_type=NarrativeEventType.ACTION_SEQUENCE,
                            narrative_text=f"User stated intent: {user_input} (paused for confirmation)",
                            actors_involved=[actor.sheet.name],
                            importance=NarrativeImportance.ROUTINE,  # Keep in context - everything builds on past narration
                            emotional_tone="contemplative",
                            scene_context="diegetic_pause"
                        )
                        
                        print(f"{Color.SUCCESS}[DIEGETIC] Looping back for next user input{Color.RESET}")
                        continue  # Loop back for next user input - SKIP all other processing
                    else:
                        if is_travel_like:
                            print(f"{Color.INFO}[DIEGETIC] Travel intent detected - deferring to Journey system{Color.RESET}")
                        else:
                            print(f"{Color.INFO}[DIEGETIC] Atomic intent - proceeding with normal flow{Color.RESET}")
                    
                except Exception as e:
                    print(f"{Color.ERROR}[DIEGETIC] ERROR: {e}{Color.RESET}")
                    import traceback as traceback_module
                    traceback_module.print_exc()
                    # Continue with normal flow on error
            elif is_contested:
                print(f"{Color.INFO}[DIEGETIC] Contested action detected - skipping diegetic analysis{Color.RESET}")
            
            # ============================================================
            # INQUIRY DETECTION - Questions bypass Intent Availability
            # ============================================================
            # Detect if this is a question/inquiry BEFORE Intent Availability
            # Questions should not be subject to availability checks
            # ============================================================
            
            # Strict mode: only the interpreter decides inquiry vs action.
            # No question-mark heuristics.
            is_inquiry_question = False
            
            # ============================================================
            # INTENT AVAILABILITY CHECK - Prevent Manifestation
            # ============================================================
            # Check if this intent is available NOW, LATER, or NEVER
            # This prevents manifestation and maintains world constraints
            # NOTE: Sweeping intents are handled by diegetic system above
            # NOTE: Inquiries bypass this check
            # ============================================================
            
            # ============================================================
            # PRONOUN RESOLUTION
            # ============================================================
            # Resolve pronoun references (him, her, them) to NPC names
            # before intent processing
            # ============================================================
            
            try:
                from pronoun_resolution import extract_pronoun_from_action, resolve_pronoun_to_npc, replace_pronoun_with_name
                
                pronoun = extract_pronoun_from_action(user_input)
                if pronoun and available_npcs:
                    # Try to resolve pronoun to NPC name
                    npc_name = resolve_pronoun_to_npc(pronoun, available_npcs)
                    
                    if npc_name:
                        # Replace pronoun with NPC name
                        original_input = user_input
                        user_input = replace_pronoun_with_name(user_input, pronoun, npc_name)
                        
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.SYSTEM}[PRONOUN RESOLUTION] '{pronoun}' → '{npc_name}'{Color.RESET}")
                            print(f"{Color.SYSTEM}[RESOLVED ACTION] {user_input}{Color.RESET}")
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[PRONOUN RESOLUTION] Failed: {e}{Color.RESET}")
            
            # ============================================================
            # INPUT ANALYSIS - Must happen BEFORE intent availability check
            # ============================================================
            # In strict mode, we use the interpreter result produced earlier.
            input_analysis_for_survival = quick_action_check
            input_analysis = quick_action_check
            if not SUPPRESS_DEBUG:
                print(f"{Color.SYSTEM}[INPUT ANALYSIS] Using interpreter classification{Color.RESET}")

            is_inquiry_question = (
                input_analysis.get('input_type') == 'inquiry' if input_analysis else False or
                ((input_analysis.get('input_type') == 'fallible_action' if input_analysis else False) and
                 (input_analysis.get('fallible_subtype') in ['mental', 'inquiry'] if input_analysis else False))
            )
            
            # Check if this is an inquiry action BEFORE intent availability
            # Inquiries should skip intent availability and go straight to inquiry processing
            is_inquiry_action_early = (
                (input_analysis.get('input_type') == 'fallible_action' if input_analysis else False) and 
                (input_analysis.get('fallible_subtype') in ['mental', 'inquiry'] if input_analysis else False)
            )
            
            # Skip intent availability for questions and inquiry actions
            if ENABLE_INTENT_AVAILABILITY and not is_meta_command and not is_inquiry_question and not is_contested and not is_inquiry_action_early:
                try:
                    # Get established facts from context with FULL detail
                    established_facts = []
                    
                    # CRITICAL: Add FULL scene description first (not truncated!)
                    if scene_description:
                        established_facts.append(f"SCENE: {scene_description}")
                    
                    # Add objects/furniture in the location from the map
                    try:
                        obstacle_context = get_obstacle_names_for_narrative()
                        if obstacle_context:
                            established_facts.append(f"⚠️ {obstacle_context}")
                    except Exception:
                        pass
                    
                    # Add facts from concrete details tracker
                    if hasattr(narrative_context_manager, 'detail_tracker'):
                        for owner, detail_ids in narrative_context_manager.detail_tracker.details_by_owner.items():
                            for detail_id in detail_ids[:5]:
                                detail = narrative_context_manager.detail_tracker.details.get(detail_id)
                                if detail:
                                    established_facts.append(f"{owner}: {detail.detail_text[:100]}")
                    
                    # Add ALL NUAs present with full details - CRITICAL FACT
                    # This MUST be checked first before saying "no one is here"
                    if available_npcs:
                        npc_list = []
                        for nua in available_npcs:
                            try:
                                from multi_actor_manager import _safe_display_name
                                npc_list.append(f"{_safe_display_name(nua)} ({nua.sheet.occupation})")
                            except Exception:
                                npc_list.append(f"{nua.sheet.name} ({nua.sheet.occupation})")
                        # Insert at beginning so LLM sees it first
                        established_facts.insert(0, f"⚠️ CRITICAL: PEOPLE CURRENTLY PRESENT HERE: {', '.join(npc_list)} - These people are HERE NOW and available for interaction")
                    
                    # Add actor inventory
                    try:
                        if hasattr(actor.sheet, 'inventory') and actor.sheet.inventory:
                            items = [item.name for item in actor.sheet.inventory[:5]]
                            if items:
                                established_facts.append(f"YOUR INVENTORY: {', '.join(items)}")
                    except Exception:
                        pass
                    
                    # Add current goals
                    try:
                        if hasattr(actor.sheet, 'goals') and actor.sheet.goals:
                            goals = actor.sheet.goals[:3]
                            if goals:
                                established_facts.append(f"YOUR GOALS: {'; '.join(goals)}")
                    except Exception:
                        pass
                    
                    # Add current tasks from goal_task_manager
                    try:
                        if hasattr(actor.sheet, 'goal_task_manager') and actor.sheet.goal_task_manager:
                            active_tasks = actor.sheet.goal_task_manager.get_active_tasks()
                            if active_tasks:
                                task_descriptions = [f"{task.description} [{task.priority.value}]" for task in active_tasks[:3]]
                                established_facts.append(f"YOUR ACTIVE TASKS: {'; '.join(task_descriptions)}")
                            
                            # Add current task if set
                            if hasattr(actor.sheet, 'current_task') and actor.sheet.current_task:
                                established_facts.append(f"CURRENT TASK: {actor.sheet.current_task.description}")
                    except Exception:
                        pass
                    
                    # Add actor state facts
                    try:
                        stamina = actor.sheet.statuses[StatusType.STAMINA].value
                        spirit = actor.sheet.statuses[StatusType.SPIRIT].value
                        supply = actor.sheet.statuses[StatusType.SUPPLY].value
                        established_facts.append(f"YOUR STATUS: Stamina {stamina}, Spirit {spirit}, Supply {supply}")
                    except Exception:
                        pass
                    
                    # Add relationships/sympathy with NPCs present
                    try:
                        if available_npcs and hasattr(actor.sheet, 'sympathy'):
                            relationships = []
                            for npc in available_npcs:
                                sympathy_value = actor.sheet.get_sympathy(npc.sheet.name)
                                if sympathy_value != 0:  # Only show non-neutral relationships
                                    relationships.append(f"{npc.sheet.name} ({sympathy_value:+d})")
                            if relationships:
                                established_facts.append(f"RELATIONSHIPS: {', '.join(relationships)}")
                    except Exception:
                        pass
                    
                    # Add key skills (top 5) - for context only, NOT to prevent attempts
                    try:
                        if hasattr(actor.sheet, 'skills') and actor.sheet.skills:
                            skills = sorted(actor.sheet.skills.items(), key=lambda x: x[1], reverse=True)[:5]
                            skill_list = [f"{name} ({value})" for name, value in skills]
                            established_facts.append(f"YOUR SKILLS: {', '.join(skill_list)} (Note: Can attempt actions without these skills)")
                    except Exception:
                        pass
                    
                    # Add current location name if available
                    try:
                        if current_location:
                            established_facts.append(f"LOCATION NAME: {current_location}")
                    except Exception:
                        pass
                    
                    # Add spatial context (zones, exits)
                    try:
                        context = narrative_context_manager.get_current_scene_context()
                        if context:
                            # Add zones
                            if context.zones:
                                zone_names = [zone.name for zone in context.zones[:5]]
                                if zone_names:
                                    established_facts.append(f"AREAS HERE: {', '.join(zone_names)}")
                            # Add exits/doors
                            if context.obstacles:
                                exits = [obs.name for obs in context.obstacles if 'door' in obs.name.lower() or 'exit' in obs.name.lower() or 'gate' in obs.name.lower()]
                                if exits:
                                    established_facts.append(f"EXITS/DOORS: {', '.join(exits[:5])}")
                    except Exception:
                        pass
                    
                    # Get recent narrative for additional context
                    recent_narrative = narrative_context_manager.get_context_for_llm(
                        lookback_events=5,
                        importance_threshold="routine"
                    )
                    recent_narrative = _merge_contexts(recent_narrative, everlasting_context_text, max_chars=1800)
                    
                    # Get current time of day
                    current_time_of_day = time_context.get('time_of_day', 'unknown') if time_context else 'unknown'
                    
                    # Check if this is a simple in-scene action that should skip availability check
                    skip_availability = False
                    user_input_lower = user_input.lower()
                    
                    # Skip for movement within scene (approaching people/objects already present)
                    in_scene_movement_patterns = [
                        'walk over', 'head over', 'approach', 'go to the', 'move to the',
                        'walk to the', 'step toward', 'move toward', 'get close to',
                        'go over to', 'walk up to'
                    ]
                    
                    # Skip for travel actions (leaving current location) - allow travel logic to handle these
                    travel_patterns = [
                        'leave', 'exit', 'go to', 'head to', 'travel to', 'run to', 'sprint to', 
                        'rush to', 'drive to', 'ride to', 'fly to', 'walk to', 'go outside', 
                        'head out', 'step out', 'enter'
                    ]
                    
                    # Skip for basic perceptual actions (looking at things present)
                    perceptual_patterns = [
                        'look at the', 'examine the', 'inspect the', 'check the',
                        'observe the', 'watch the', 'study the'
                    ]
                    
                    # Check if action targets something in current scene description
                    scene_desc_lower = scene_description.lower()
                    
                    # Extract all meaningful words from user input (potential targets)
                    user_words = [w for w in user_input_lower.split() if len(w) > 3]
                    
                    # Check if this is a movement/perceptual action
                    is_in_scene_move = any(pattern in user_input_lower for pattern in in_scene_movement_patterns)
                    is_perception = any(pattern in user_input_lower for pattern in perceptual_patterns)
                    is_travel = any(pattern in user_input_lower for pattern in travel_patterns)
                    
                    if is_in_scene_move or is_perception:
                        # Check if any significant words from the action appear in the scene
                        # This catches "three people" from "You see three people across the room"
                        matching_words = [w for w in user_words if w in scene_desc_lower]
                        
                        # If we find 2+ matching words, it's likely targeting something in the scene
                        if len(matching_words) >= 2:
                            skip_availability = True
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.INFO}[AVAILABILITY SKIP] In-scene action targeting present object/person (matched: {matching_words[:3]}){Color.RESET}")
                    
                    # Always skip availability check for travel/departure actions
                    # The journey system will handle whether the destination is valid or reachable
                    # FIX: Also check explicit_movement_data (smart detection) to catch things like "keep going"
                    if is_travel or (explicit_movement_data and explicit_movement_data.get('has_explicit_movement')):
                        skip_availability = True
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.INFO}[AVAILABILITY SKIP] Travel/Departure action detected - deferring to Journey System{Color.RESET}")
                    
                    # Evaluate intent availability with enhanced context (using current scene)
                    if skip_availability:
                        # Skip availability check - assume EXIST
                        availability_result = {
                            'availability': IntentAvailability.EXIST,
                            'reasoning': 'In-scene action targeting present object/person',
                            'internal_voice': None
                        }
                    else:
                        availability_result = intent_system.evaluate_intent_availability(
                            user_intent=user_input,
                            narrative_context=recent_narrative,
                            scene_context=get_current_scene(),  # FIX BUG #9: Always use current scene
                            established_facts=established_facts,  # Enhanced facts list
                            current_time_of_day=current_time_of_day
                        )
                    
                    # Handle based on availability
                    if not SUPPRESS_DEBUG:
                        print(f"\n{Color.SYSTEM}═══ Intent Availability Check ═══{Color.RESET}")
                        print(f"{Color.SYSTEM}Availability: {availability_result['availability'].value}{Color.RESET}")
                        print(f"{Color.SYSTEM}Reason: {availability_result.get('reasoning', 'No reasoning provided')}{Color.RESET}")
                    
                    # ============================================================
                    # INTENT-BASED MEMORY CREATION
                    # ============================================================
                    # Check if this intent triggers memory creation (family, relationships, etc.)
                    # Creates vessel background memories diegetically based on availability
                    # The function itself has criteria to avoid creating memories too frequently
                    # ============================================================
                    
                    try:
                        created_memories = intent_memory_creator.process_intent_for_memories(
                            user_intent=user_input,
                            availability_result=availability_result,
                            current_location=current_location or "Unknown Location",
                            turn_number=turn_number,
                            scene_id=scene_id
                        )
                        
                        # Display any created memories with internal voice
                        # Also record in narrative context for future LLM calls
                        for memory_result in created_memories:
                            display_memory_creation(
                                memory_result,
                                narrative_context_manager=narrative_context_manager,
                                actor_name=actor.sheet.name
                            )
                            
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Memory creation failed: {e}{Color.RESET}")
                    
                    # Check if this is an inquiry action - inquiries process differently
                    is_inquiry_action = (
                        (input_analysis.get('input_type') == 'fallible_action' if input_analysis else False) and 
                        (input_analysis.get('fallible_subtype') in ['mental', 'inquiry'] if input_analysis else False)
                    )
                    
                    # ALL fallible actions (inquiry, physical, social) use the same 3-phase system:
                    # 1. Perceptual description (what you physically do/try)
                    # 2. Internal voice (mental reaction)
                    # No early exits - all actions get full narrative treatment
                    
                    # Check if this is a movement action - if so, EXIST_NOT_HERE should proceed (it means travel there)
                    # FIX: Use the robust detection from earlier in the loop
                    is_movement_action = False
                    if explicit_movement_data and explicit_movement_data.get('has_explicit_movement'):
                        is_movement_action = True
                    else:
                        is_movement_action = any(word in user_input.lower() for word in [
                            'leave', 'exit', 'go to', 'head to', 'head over to', 'walk to', 'walk over to',
                            'travel to', 'move to', 'enter', 'step out', 'step into', 'go into',
                            'head out', 'walk out', 'run to', 'rush to', 'hurry to'
                        ])
                    
                    if availability_result["availability"] == IntentAvailability.DOES_NOT_EXIST:
                        # Generate unified output for truly unavailable actions (things that don't exist)
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.INFO}[{availability_result['availability'].value.upper()}: Generating perceptual + internal voice]{Color.RESET}\n")
                        
                        # Get context
                        recent_context = narrative_context_manager.get_context_for_llm(
                            lookback_events=5,
                            importance_threshold="notable"
                        )
                        recent_context = _merge_contexts(recent_context, everlasting_context_text)
                        time_context = master_time.get_current_time_context()
                        
                        # Generate perceptual description explaining WHY it doesn't exist
                        perceptual_description = narrator.generate_does_not_exist_narrative(
                            user_intent=user_input,
                            ua_actor=actor,
                            scene_description=scene_description,
                            narrative_context=recent_context,
                            current_time=time_context,
                            reasoning=availability_result.get("reasoning", "No reasoning provided")
                        )
                        
                        # Display perceptual description
                        display_perceptual_description_box(perceptual_description)
                        
                        # Check if this is a playback action (answering machine, cassette, etc.)
                        ui_low = (user_input or "").lower()
                        playback_patterns = [
                            "check the answering machine", "check answering machine", "listen to the answering machine",
                            "listen to answering machine", "play the answering machine", "play answering machine",
                            "check messages", "listen to messages", "check the messages", "listen to the messages",
                            "press play", "hit play", "play the tape", "play tape", "play the cassette",
                            "listen to the tape", "listen to tape", "check what's playing", "see what's playing"
                        ]
                        scene_low = (scene_description or "").lower()
                        device_keywords = ["answering machine", "voicemail", "tape", "cassette", "recorder", "player"]
                        no_messages_keywords = ["no messages", "no new messages", "empty", "blank tape", "erased", "0 new messages"]
                        
                        if any(pat in ui_low for pat in playback_patterns) and any(k in scene_low for k in device_keywords):
                            # This is a playback action - generate actual message content
                            if not any(k in scene_low for k in no_messages_keywords):
                                device_name = "Answering Machine" if "answering machine" in scene_low else "Tape Player"
                                message_content = narrator.generate_media_playback_content(
                                    device_name=device_name,
                                    ua_actor=actor,
                                    scene_description=scene_description,
                                    narrative_context=recent_context,
                                    time_context=time_context
                                )
                                if message_content:
                                    print(f"{Color.NARRATIVE}{message_content}{Color.RESET}\n")
                                    # Update perceptual description to include the message
                                    perceptual_description = f"{perceptual_description}\n\n{message_content}"
                        
                        # CRITICAL: Update scene description with new perceptual information
                        # This ensures continuity checker has the complete scene state on next turn
                        scene_description = f"{scene_description}\n\n{perceptual_description}"
                        
                        # Update conductor's scene description
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
                        # This ensures continuity checker knows about newly revealed objects
                        try:
                            narrative_context_manager.add_narrative_event(
                                event_type=NarrativeEventType.EXPLORATION,
                                narrative_text=perceptual_description,
                                actors_involved=[actor.sheet.name],
                                importance=NarrativeImportance.NOTABLE,
                                emotional_tone="observational",
                                scene_context=f"Inquiry: {user_input[:50]}"
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
                                scene_id=scene_id,
                                mention_system=mention_system
                            )
                        except Exception as e:
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")
                        
                        # Generate internal voice (explains why it doesn't work)
                        internal_voice = generate_unified_internal_voice(
                            actor=actor,
                            narrator=narrator,
                            scene_description=scene_description,
                            user_action=user_input,
                            action_outcome=perceptual_description or "That doesn't seem possible here.",
                            function_hint="solution",  # Suggest alternatives
                            predicament=f"Cannot do: {user_input}",
                            urgency="normal",
                            failure_tracker=failure_tracker,
                            narrative_context_manager=narrative_context_manager
                        )
                        
                        # Display internal voice
                        display_internal_voice_box(internal_voice)
                        
                        # Advance time for the failed attempt/observation
                        # Searching/Checking usually takes a moment
                        req = master_time.create_user_action_request(
                            RuleOf3Category.THREE_SECOND, # Brief check
                            actor.sheet.name,
                            user_input
                        )
                        res = master_time.request_time_advancement(req)
                        
                        if not SUPPRESS_DEBUG:
                            elapsed = simulation_time_tracker.get_simulation_time_display()
                            print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                        
                        # Sync pygame map after movement
                        try:
                            auto_sync_map(session_id=tracker.session_id if tracker else None)
                        except Exception:
                            pass
                        
                        # Execute post-user turns (lower initiative NPCs) before continuing
                        execute_post_user_turns_if_roam()
                        # Skip to next turn
                        continue
                        
                    elif availability_result["availability"] == IntentAvailability.EXIST_NOT_HERE:
                        # Location exists but you're not there - this should trigger travel/movement
                        if is_movement_action:
                            # Movement action to a different location - proceed to location change system
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.SUCCESS}✓ Movement to different location - proceeding with travel{Color.RESET}")
                        else:
                            # Non-movement action targeting something not here - block it
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.INFO}[EXIST_NOT_HERE: Item/person not in current location]{Color.RESET}\n")
                            
                            # Generate narrative explaining it's not here
                            recent_context = narrative_context_manager.get_context_for_llm(
                                lookback_events=5,
                                importance_threshold="notable"
                            )
                            recent_context = _merge_contexts(recent_context, everlasting_context_text)
                            time_context = master_time.get_current_time_context()
                            
                            # Get NUA actions context for perceptual awareness
                            nua_actions = _get_nua_actions_context(tracker, f"actor_{actor.sheet.name.lower().replace(' ', '_')}")
                            
                            perceptual_description = narrator.generate_inquiry_response(
                                user_question=user_input,
                                ua_actor=actor,
                                scene_description=scene_description,
                                narrative_context=recent_context,
                                current_time=time_context,
                                availability_context=availability_result,
                                nua_actions_context=nua_actions
                            )
                            
                            display_perceptual_description_box(perceptual_description)
                            
                            # Update scene description with new perceptual information
                            scene_description = f"{scene_description}\n\n{perceptual_description}"
                            _capture_continuity_facts_from_text(perceptual_description, source="perceptual", base_confidence=0.65)
                            try:
                                _capture_mentioned_actors_from_text(perceptual_description, source="perceptual")
                            except Exception:
                                pass
                            try:
                                conductor.scene_description = scene_description
                            except Exception:
                                pass
                            
                            # Persist to authoritative tracker
                            try:
                                tracker.set_current_scene(scene_description)
                            except Exception:
                                pass
                            
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=perceptual_description or "Uncertain about this...",
                                function_hint="information",  # Trying to figure out what's possible
                                question_content=user_input,
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            
                            display_internal_voice_box(internal_voice)
                            
                            # Save internal voice to narrative context
                            if internal_voice:
                                try:
                                    from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                                    narrative_context_manager.add_narrative_event(
                                        event_type=NarrativeEventType.INTERNAL_VOICE,
                                        narrative_text=f"💭 {internal_voice}",
                                        actors_involved=[actor.sheet.name],
                                        importance=NarrativeImportance.NOTABLE,
                                        emotional_tone="reflective"
                                    )
                                except Exception as save_error:
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.WARNING}Failed to save internal voice to context: {save_error}{Color.RESET}")
                            
                            continue
                        
                    elif availability_result["availability"] == IntentAvailability.EXIST:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.SUCCESS}✓ Intent is available - proceeding with action{Color.RESET}")
                    
                except Exception as e:
                    # If intent checking fails, proceed with action anyway (graceful degradation)
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}Intent check skipped: {e}{Color.RESET}")
            
            # On-demand quick commands (no time advancement)
            if user_input.lower() in ['look', 'l', 'examine scene', 'scan']:
                print(f"\n{Color.SCENE} FULL SCENE DESCRIPTION:{Color.RESET}")
                display_scene = _convert_ua_to_second_person(scene_description, actor.sheet.name)
                print(f"{Color.NARRATIVE}{display_scene}{Color.RESET}")
                # Do not advance time or counters; re-prompt next loop
                continue
            if user_input.lower() in ['ua', 'sheet']:
                print(f"\n{Color.INFO} Your Character Sheet:{Color.RESET}")
                actor.sheet.display_detailed()
                continue
            if user_input.lower() in ['quit', 'exit', 'q']:
                print(f"{Color.SUCCESS}Thanks for playing UTAS!{Color.RESET}")
                # Save on quit
                try:
                    final_snapshot = {
                        'scene_number': scene_number,
                        'scene_description': scene_description,
                        'scene_updates': scene_updates[-5:],
                        'time_context': time_context,
                        'available_npcs': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                        'actor_state': {
                            'name': actor.sheet.name,
                            'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()}
                        }
                    }
                    req = save_coordinator.create_user_quit_request(final_snapshot)
                    save_coordinator.request_save(req)
                    # Flush pending saves to disk
                    save_coordinator.flush_pending_saves()
                except Exception:
                    pass
                break
                
            # Provide full context snapshot to the Interpreter for this turn
            try:
                context_snapshot = _compose_scene_snapshot(
                    scene_description=scene_description,
                    time_context=master_time.get_current_time_context(),
                    last_action_narrative=last_action_narrative,
                    scene_updates=scene_updates,
                )
                # Store on the interpreter so all downstream interpretation calls see it
                conductor.interpreter._ad_hoc_context_snapshot = context_snapshot
            except Exception:
                pass

            # input_analysis_for_survival and input_analysis already created above (before intent availability check)
            
            fulfilled_needs = []
            survival_time_cost = 0.0
            
            # Detect monetary transactions (but don't process yet - wait for action resolution)
            monetary_data = conductor.interpreter_agent.detect_monetary_exchange(
                user_input, actor, scene_description
            )
            
            # For non-contested monetary actions (purchases), check affordability upfront
            if monetary_data.get("transaction_detected") and monetary_data.get("transaction_type") == "Purchase":
                amount = monetary_data.get("amount", 0)
                if amount < 0:  # Spending money
                    supply_status = actor.sheet.statuses[StatusType.SUPPLY]
                    if supply_status.money_amount + amount < 0:
                        insufficient = abs(supply_status.money_amount + amount)
                        print(f"\n{Color.WARNING}⚠️  Cannot afford this purchase!{Color.RESET}")
                        print(f"{Color.WARNING}Need ${insufficient:.2f} more. Current balance: ${supply_status.money_amount:.2f}{Color.RESET}")
                        continue
            
            # Skip survival processing when contested NUA action (will transition to encounter)
            is_contested_nua = (
                (input_analysis_for_survival.get('input_type') == 'contested_action' if input_analysis_for_survival else False) and 
                (input_analysis_for_survival.get('addressed_type') == 'nua' if input_analysis_for_survival else False)
            )
            # Skip survival processing for inquiries and information gathering (they don't take time!)
            is_inquiry = (
                (input_analysis_for_survival.get('input_type') == 'inquiry' if input_analysis_for_survival else False) or
                ((input_analysis_for_survival.get('input_type') == 'fallible_action' if input_analysis_for_survival else False) and 
                 (input_analysis_for_survival.get('fallible_subtype') in ['mental', 'inquiry'] if input_analysis_for_survival else False))
            )
            if not is_inquiry and not is_contested_nua:
                # Primary: LLM-based survival intent detection
                llm_detection = None
                try:
                    llm_detection = conductor.interpreter.detect_survival_intent(user_input, actor)
                except Exception:
                    llm_detection = None
                if llm_detection and llm_detection.get('needs'):
                    # Map string needs to SurvivalNeed enums
                    need_map = {
                        'food': SurvivalNeed.FOOD,
                        'water': SurvivalNeed.WATER,
                        'sleep': SurvivalNeed.SLEEP,
                        'fulfillment': SurvivalNeed.FULFILLMENT,
                    }
                    llm_needs = [need_map[n.lower()] for n in llm_detection['needs'] if isinstance(n, str) and n.lower() in need_map]
                    # Prefer LLM-based consumption intent over heuristics
                    try:
                        consumption = conductor.interpreter.detect_survival_consumption_intent(
                            user_input,
                            scene_context=context_snapshot if 'context_snapshot' in locals() else None
                        )
                    except Exception:
                        consumption = None
                    # If LLM confidently says there is NOT explicit consumption now, drop FOOD/WATER; else fallback heuristic for FOOD only
                    if llm_needs:
                        if consumption and float(consumption.get('confidence', 0)) >= 0.6:
                            # Only treat explicit consumption (action_type == 'consume') as true consumption
                            is_explicit_consumption = bool(consumption.get('consumption_intent', False)) and str(consumption.get('action_type', '')).lower() == 'consume'
                            if not is_explicit_consumption:
                                llm_needs = [n for n in llm_needs if n not in (SurvivalNeed.FOOD, SurvivalNeed.WATER)]
                        else:
                            if not _should_allow_food_fulfillment(user_input):
                                llm_needs = [n for n in llm_needs if n != SurvivalNeed.FOOD]
                    # Use a confidence threshold to trust LLM intent
                    if llm_needs and float(llm_detection.get('confidence', 0)) >= 0.6:
                        fulfilled_needs = llm_needs
                        costs = survival_analyzer.get_action_costs(user_input, fulfilled_needs)
                        if isinstance(llm_detection.get('total_time_hours'), (int, float)) and llm_detection['total_time_hours'] > 0:
                            costs['time_cost'] = float(llm_detection['total_time_hours'])
                        survival_messages = survival_analyzer.process_survival_fulfillment(
                            actor.sheet, user_input, fulfilled_needs, costs, narrative_context_manager
                        )
                        summary = survival_analyzer.get_survival_summary(fulfilled_needs, costs)
                        if summary:
                            print(f"\n{Color.SUCCESS}{summary}{Color.RESET}")
                            for message in survival_messages:
                                print(f"{Color.SUCCESS}   • {message}{Color.RESET}")
                        survival_time_cost = costs['time_cost']
                    else:
                        # Fallback to refined rule-based analyzer
                        fulfilled_needs = survival_analyzer.analyze_action(user_input)
                else:
                    # Fallback if LLM unavailable or returns no needs
                    fulfilled_needs = survival_analyzer.analyze_action(user_input)
                    # Try LLM-based consumption intent even in fallback path; otherwise heuristic for FOOD only
                    try:
                        consumption = conductor.interpreter.detect_survival_consumption_intent(
                            user_input,
                            scene_context=context_snapshot if 'context_snapshot' in locals() else None
                        )
                    except Exception:
                        consumption = None
                    if fulfilled_needs:
                        if consumption and float(consumption.get('confidence', 0)) >= 0.6:
                            # Only treat explicit consumption (action_type == 'consume') as true consumption
                            is_explicit_consumption = bool(consumption.get('consumption_intent', False)) and str(consumption.get('action_type', '')).lower() == 'consume'
                            if not is_explicit_consumption:
                                fulfilled_needs = [n for n in fulfilled_needs if n not in (SurvivalNeed.FOOD, SurvivalNeed.WATER)]
                        else:
                            if not _should_allow_food_fulfillment(user_input):
                                fulfilled_needs = [n for n in fulfilled_needs if n != SurvivalNeed.FOOD]
                
                if fulfilled_needs:
                    # If we didn't already compute costs above, compute and process now
                    if survival_time_cost == 0.0:
                        costs = survival_analyzer.get_action_costs(user_input, fulfilled_needs)
                        survival_messages = survival_analyzer.process_survival_fulfillment(
                            actor.sheet, user_input, fulfilled_needs, costs, narrative_context_manager
                        )
                        summary = survival_analyzer.get_survival_summary(fulfilled_needs, costs)
                        if summary:
                            print(f"\n{Color.SUCCESS}{summary}{Color.RESET}")
                            for message in survival_messages:
                                print(f"{Color.SUCCESS}   • {message}{Color.RESET}")
                        survival_time_cost = costs['time_cost']
                        # Update narrative loop with survival signal
                        try:
                            turn_data = _build_turn_data(
                                user_input=user_input,
                                scene_description=scene_description,
                                current_mode=current_mode,
                                continuity={'judgment': 'Possible'},
                                survival_needs=[n.value for n in fulfilled_needs]
                            )
                            turn_data['narrative_response'] = last_action_narrative
                            narrative_loop.process_turn(
                                turn_data=turn_data,
                                scene_description=scene_description,
                                time_context=time_context,
                                available_npcs=available_npcs
                            )
                        except Exception:
                            pass
                
                # DISABLED: Survival actions no longer automatically advance time
                # Time advancement is now only triggered by actual actions
                # if survival_time_cost > 0:
                #     time_request = master_time.create_survival_action_request(
                #         action_name=f"Survival needs fulfillment",
                #         time_cost_hours=survival_time_cost,
                #         actor_name=actor.sheet.name
                #     )
                #     time_result = master_time.request_time_advancement(time_request)
                #     time_context = master_time.get_current_time_context()
                #     print(f"\n{Color.SYSTEM} Time advanced by {time_result.duration_advanced_hours} hours{Color.RESET}")
                #     print(f"{Color.SYSTEM} Current Time: {time_result.new_time.format_full()}{Color.RESET}")
                #     if time_result.atmospheric_changes['changed']:
                #         print(f"{Color.NARRATIVE} {time_result.atmospheric_changes['new']}{Color.RESET}")
        else:
            # Skipping prompt and survival handling; pending encounter action will be used in encounter loop
            # Don't set user_input here - let the encounter loop handle it
            pass
        
        # Check for survival warnings
        critical_needs = get_critical_survival_actions(actor.sheet)
        if critical_needs:
            print(f"\n{Color.WARNING} SURVIVAL WARNING:{Color.RESET}")
            for action_id, action in critical_needs.items():
                print(f"  🔴 {action.name} needed - {action.description}")
        
        # Determine current mode
        current_mode = encounter_checker.current_context.mode
        
        # No automatic scene transitions - only user-initiated
        
        # Classify action for time tracking ONLY in ROAM and when not skipping prompt
        if current_mode != SimulationMode.ENCOUNTER and not (pending_encounter_action):
            rule_of_3_result = rule_of_3_classifier.classify_action(user_input)
            if isinstance(rule_of_3_result, tuple):
                rule_of_3_category, rule_of_3_reasoning = rule_of_3_result
            else:
                rule_of_3_category = rule_of_3_result
                rule_of_3_reasoning = "Fallback classification"
        
        if current_mode == SimulationMode.ENCOUNTER:
            # ENCOUNTER MODE: Initialize systems once and process contested action
            print(f"\n{Color.SUCCESS}⚔️ ENCOUNER MODE{Color.RESET}")
            
            # Initialize encounter systems (only once per encounter)
            if not hasattr(encounter_checker.current_context, 'systems_initialized'):
                print(f"{Color.SYSTEM}Initializing encounter systems...{Color.RESET}")
                
                # Defensive: some encounter triggers may set ENCOUNTER mode without setting participants.
                # Ensure we have at least one non-user participant before initializing systems.
                participants = getattr(encounter_checker.current_context, 'participants', []) or []
                if len(participants) == 0:
                    seeded = None
                    try:
                        if available_npcs:
                            seeded = available_npcs[0]
                    except Exception:
                        seeded = None
                    if seeded is not None:
                        encounter_checker.current_context.participants = [seeded]
                        participants = [seeded]
                        print(f"{Color.SYSTEM}[ENCOUNTER] Seeded missing participant: {seeded.sheet.name}{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}[ENCOUNTER] No participants available; returning to ROAM mode{Color.RESET}")
                        encounter_checker.current_context.mode = SimulationMode.ROAM
                        current_mode = SimulationMode.ROAM
                        continue
                
                # CONTINUITY ENFORCEMENT: This NPC creation code should NEVER execute
                # because contested actions targeting non-existent NPCs are now blocked earlier
                # Keeping this code for safety/debugging, but it represents a continuity violation if reached
                target_participant = encounter_checker.current_context.participants[0]
                if isinstance(target_participant, dict) and target_participant.get("create_npc"):
                    # CRITICAL WARNING: This should never happen - it means continuity check was bypassed
                    print(f"\n{Color.ERROR}⚠️⚠️⚠️ CONTINUITY VIOLATION DETECTED ⚠️⚠️⚠️{Color.RESET}")
                    print(f"{Color.ERROR}Attempting to create NPC that doesn't exist in scene context!{Color.RESET}")
                    print(f"{Color.ERROR}This represents a manifestation bug - the action should have been blocked earlier.{Color.RESET}")
                    
                    # Create NPC using stored target data
                    npc_type = target_participant["create_npc"]
                    target_name = target_participant.get("target_name", "Unknown Person")
                    user_action = target_participant.get("user_action", "")
                    narrative_context = target_participant.get("narrative_context", "")
                    
                    print(f"\n{Color.INFO}🎭 Creating NUA: {target_name} from target context{Color.RESET}")
                    print(f"{Color.SYSTEM}[DEBUG] Target name: '{target_name}'{Color.RESET}")
                    print(f"{Color.SYSTEM}[DEBUG] User action: '{user_action}'{Color.RESET}")
                    print(f"{Color.SYSTEM}[DEBUG] Narrative context length: {len(narrative_context)} chars{Color.RESET}")
                    if narrative_context:
                        print(f"{Color.SYSTEM}[DEBUG] First 200 chars of context: {narrative_context[:200]}...{Color.RESET}")
                    
                    # Use existing scene_creator (which has RAG system)
                    creator = scene_creator
                    
                    # Build comprehensive prompt using target name, user action, and narrative context
                    if target_name and target_name != "Unknown Person":
                        # CRITICAL: Use narrative context to find information about the target
                        # For example, if narrative context mentions "Marcus - (206) 555-0147. Studio engineer."
                        # we should extract that information and use it
                        npc_prompt = (
                            f"Create an NUA named {target_name} based on the following context:\n\n"
                            f"**User Action:** {user_action}\n"
                            f"**Recent Context (may contain information about {target_name}):**\n{narrative_context[:800]}\n\n"
                            f"**Scene:** {scene_description[:400]}\n\n"
                            f"CRITICAL INSTRUCTIONS:\n"
                            f"1. Search the Recent Context for any mentions of {target_name} (occupation, relationship, contact info, notes about them)\n"
                            f"2. Use that information to create a character that matches what's known about {target_name}\n"
                            f"3. If the context mentions their occupation (e.g., 'studio engineer'), use that exact occupation\n"
                            f"4. If the context mentions their relationship to the user actor, reflect that in personality/demeanor\n"
                            f"5. Make S-factors and skills align with their known occupation and role\n"
                            f"6. If no specific information is found, infer a plausible role from the scene and user action\n"
                            f"7. This character should feel like someone the user actor knows or is trying to contact\n"
                        )
                    else:
                        # Fallback: generic from-scene NPC; infer a plausible role from the scene (no fixed bias)
                        npc_prompt = (
                            f"Create a character that fits this scene. Infer a plausible role and demeanor from the "
                            f"scene description and current mood. Scene: {scene_description[:500]}..."
                        )
                    new_nua = creator.generate_nua(npc_prompt, scene_description)
                    
                    if new_nua:
                        register_nua(new_nua, available_npcs)
                        encounter_checker.current_context.participants = [new_nua]
                        continuity_validator.add_npc(new_nua.sheet.name)  # Track new NUA
                        print(f"{Color.SUCCESS}✓ Created NUA: {new_nua.sheet.name}{Color.RESET}")
                        
                        # AUTO-CREATE KEY MEMORY: First meeting with NUA
                        try:
                            auto_memory_creator.on_nua_first_met(
                                nua_name=new_nua.sheet.name,
                                nua_occupation=new_nua.sheet.occupation,
                                location=scene_description[:100],
                                first_impression=f"Encountered {new_nua.sheet.name} in {scene_description[:50]}...",
                                narrative=last_action_narrative if 'last_action_narrative' in locals() else scene_description[:200],
                                turn_number=turn_counter if 'turn_counter' in locals() else 0,
                                scene_id=current_scene_id if 'current_scene_id' in locals() else "unknown"
                            )
                        except Exception as e:
                            logger.log_error(f"Error creating first meeting memory: {e}")
                    else:
                        print(f"{Color.WARNING}Failed to create NUA, falling back to exploration mode{Color.RESET}")
                        encounter_checker.current_context.mode = SimulationMode.ROAM
                        current_mode = SimulationMode.ROAM  # Update current mode
                        # Generate a connected ROAM scene bridged from the latest encounter context
                        try:
                            scene_description = _generate_connected_roam_scene(
                                narrator,
                                narrative_context_manager,
                                scene_description,
                                last_action_narrative if 'last_action_narrative' in locals() else '',
                                master_time.get_current_time_context()
                            )
                            try:
                                conductor.scene_description = scene_description
                            except Exception:
                                pass
                        except Exception:
                            pass
                
                if current_mode == SimulationMode.ENCOUNTER:  # Recheck after potential fallback
                    # Initialize encounter systems using multi-actor system
                    encounter_checker.current_context.actor_manager = MultiActorManager()
                    encounter_checker.current_context.sympathy_manager = EnhancedSympathyManager(encounter_checker.current_context.actor_manager)
                    encounter_checker.current_context.enhanced_recovery = EnhancedTemporaryRecoveryIntegrator()
                    encounter_checker.current_context.round_manager = EnhancedRoundManager(encounter_checker.current_context.actor_manager, encounter_checker.current_context.enhanced_recovery)
                    encounter_checker.current_context.reporter = EnhancedReporter(encounter_checker.current_context.actor_manager, encounter_checker.current_context.sympathy_manager)
                    # If this encounter was initiated by an NPC, force the NPC to act first on Round 1.
                    try:
                        forced = getattr(encounter_checker.current_context, 'forced_round_one_proactor', None)
                        if forced is not None:
                            encounter_checker.current_context.round_manager.set_round_one_proactor(forced)
                            encounter_checker.current_context.forced_round_one_proactor = None
                    except Exception:
                        pass
                    # Apply optional verbosity override from env
                    try:
                        if REDESIGNED_VERBOSITY:
                            encounter_checker.current_context.reporter.set_verbosity_level(REDESIGNED_VERBOSITY)
                    except Exception:
                        pass
                    
                    # Add all actors to the manager
                    user_id = encounter_checker.current_context.actor_manager.add_actor(actor, ActorRole.USER)
                    
                    # Add initial NPC from encounter
                    npc = encounter_checker.current_context.participants[0]
                    npc_id = encounter_checker.current_context.actor_manager.add_actor(npc, ActorRole.SCENE_PRIMARY)
                    
                    # Add only explicitly selected additional participants (not all bystanders present in the scene)
                    try:
                        extra_parts = list(encounter_checker.current_context.participants[1:] or [])
                    except Exception:
                        extra_parts = []
                    for additional_npc in extra_parts:
                        if additional_npc != npc:
                            encounter_checker.current_context.actor_manager.add_actor(additional_npc, ActorRole.SCENE_SECONDARY)

                    # Ensure encounter actors exist in spatial context so spatial facts/queries include them.
                    try:
                        from spatial_context_system import get_spatial_manager, Position
                        spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                        if spatial:
                            ctx = spatial.get_current_context()
                            dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                            ap = getattr(ctx, 'actor_positions', {}) if ctx else {}

                            def _ensure_actor_on_map(a, *, is_user: bool = False):
                                try:
                                    nm = a.sheet.name if hasattr(a, 'sheet') else str(a)
                                except Exception:
                                    nm = str(a)

                                sid = "ua_001" if is_user else f"nua_{str(nm).lower().replace(' ', '_')}"
                                if sid in ap:
                                    return

                                base_pos = None
                                try:
                                    ua_pos = ap.get('ua_001')
                                    base_pos = getattr(ua_pos, 'position', None) if ua_pos else None
                                except Exception:
                                    base_pos = None

                                if base_pos is not None:
                                    px = float(getattr(base_pos, 'x', 0.0) or 0.0)
                                    py = float(getattr(base_pos, 'y', 0.0) or 0.0)
                                else:
                                    from spatial_context_system import DEFAULT_MAP_WIDTH as _DMW, DEFAULT_MAP_HEIGHT as _DMH
                                    _w = float(getattr(dims, 'width', _DMW) or _DMW) if dims else float(_DMW)
                                    _h = float(getattr(dims, 'height', _DMH) or _DMH) if dims else float(_DMH)
                                    px = _w * 0.5
                                    py = _h * 0.5

                                if not is_user:
                                    px = max(0.0, px + 18.0)
                                    py = max(0.0, py + 8.0)

                                spatial.add_actor(
                                    actor_id=sid,
                                    actor_name=nm,
                                    position=Position(px, py),
                                    is_user_actor=bool(is_user),
                                )

                            _ensure_actor_on_map(actor, is_user=True)
                            _ensure_actor_on_map(npc, is_user=False)
                            for additional_npc in extra_parts:
                                if additional_npc != npc:
                                    _ensure_actor_on_map(additional_npc, is_user=False)
                    except Exception:
                        pass
                    
                    # Initialize sympathy relationships for all actors
                    all_actors = [actor] + [npc] + extra_parts
                    for current_actor in all_actors:
                        encounter_checker.current_context.sympathy_manager.initialize_actor_relationships(current_actor)
                    
                    # Get narrative context for sympathy analysis (CRITICAL for relationships established in memories)
                    sympathy_context = ""
                    try:
                        if narrative_context_manager:
                            sympathy_context = narrative_context_manager.get_context_for_llm(lookback_events=15)
                    except Exception:
                        pass
                        
                    assign_initial_sympathies(all_actors, encounter_checker.current_context.sympathy_manager, context_text=sympathy_context)
                    
                    print(f"{Color.INFO}🎯 UA chose to interact with: {encounter_checker.current_context.participants[0].sheet.name}{Color.RESET}")
                    print(f"{Color.INFO}Processing encounter with {len(all_actors)} total actors...{Color.RESET}")
                    
                    encounter_checker.current_context.systems_initialized = True
            
            # Process contested action if systems are initialized
            if hasattr(encounter_checker.current_context, 'systems_initialized') and encounter_checker.current_context.systems_initialized:
                # Continue with existing encounter processing logic...
                pass
        
        if current_mode != SimulationMode.ENCOUNTER:
            # EXPLORATION MODE: input_analysis already assigned earlier (before intent availability)
            
            # ============================================================
            # JOURNEY CONTINUATION CHECK (MUST BE FIRST - BEFORE ACTION TYPE BRANCHING)
            # ============================================================
            # Check if user is continuing an active journey BEFORE processing action type
            journey_progress = travel_chunking.get_progress()
            if journey_progress:
                destination = journey_progress["destination"]
                current_segment = journey_progress["current_segment"]
                total_segments = journey_progress["total_segments"]
                
                # Check if user input indicates continuing toward destination
                continuing = any(word in user_input.lower() for word in 
                    ["continue", "keep going", "keep walking", "walk", "go", "head", 
                     "proceed", "move", "travel", destination.lower()])
                
                # Also check if it's a generic action that doesn't change destination
                # (e.g., "I look around while walking" should continue the journey)
                is_destination_change = False
                try:
                    from spatial_context_system import get_spatial_manager
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    new_destination = _detect_location_move(user_input, "", spatial_manager=spatial)
                    if new_destination and new_destination.lower() != destination.lower():
                        is_destination_change = True
                        # User changed their mind - cancel current journey
                        print(f"{Color.WARNING}[TRAVEL] Destination changed: {destination} → {new_destination}{Color.RESET}")
                        travel_chunking.cancel_journey()
                except Exception:
                    pass
                
                # CRITICAL: Only advance journey on explicit movement intent, NOT on inquiries or passive actions
                # Inquiries are questions - user is asking something, not moving
                # Passive actions don't indicate movement intent either
                if not is_destination_change and continuing:
                    # Advance to next segment
                    completed, dest = travel_chunking.advance_segment()
                    
                    if completed:
                        # Journey complete - arrive at destination
                        print(f"{Color.SUCCESS}[TRAVEL] Arrived at {dest}!{Color.RESET}")
                        
                        # SAVE NPC names to context BEFORE clearing (for location state persistence)
                        if available_npcs:
                            npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                            context_manager.set_nuas(npc_names)
                        
                        # Clear NPCs and initiative from previous location
                        available_npcs.clear()
                        try:
                            from initiative_system import get_location_initiative_tracker
                            get_location_initiative_tracker().clear()
                        except ImportError:
                            pass
                        
                        # Apply location move
                        prev_desc = scene_description
                        scene_description = _apply_location_move(
                            conductor, dest, master_time.get_current_time_context(),
                            actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                            population_manager=population_manager,
                            scene_creator=scene_creator,
                            actor_registry=global_actor_registry
                        )
                        
                        # Sync pygame map to new location
                        try:
                            from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                            print(f"{Color.SYSTEM}[PMAP] Clearing cache and syncing to new location: {dest}{Color.RESET}")
                            clear_layout_cache()
                            sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                        except Exception as pmap_err:
                            print(f"{Color.WARNING}[PMAP] Sync error on arrival: {pmap_err}{Color.RESET}")
                        
                        # Generate storyteller sparks BEFORE displaying scene (for integration)
                        sparks = generate_location_arrival_sparks(
                            location=dest,
                            scene_description=scene_description,
                            available_npcs=available_npcs,
                            narrative_context_manager=narrative_context_manager,
                            actor=actor,
                            conductor=conductor,
                            display_sparks=False  # We'll display after scene
                        )
                        
                        # Display arrival scene first, then sparks separately for testing clarity
                        print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")

                        try:
                            for spark in (sparks or [])[:3]:
                                if hasattr(spark, 'trigger_description') and spark.trigger_description:
                                    print(f"{Color.STATUS}✨ {spark.trigger_description}{Color.RESET}")
                        except Exception:
                            pass
                        
                        # Generate internal voice for arrival
                        try:
                            # Build spark context for internal voice
                            spark_hints = ""
                            if sparks:
                                spark_hints = " ".join([
                                    s.trigger_description[:100] for s in sparks[:2] 
                                    if hasattr(s, 'trigger_description') and s.trigger_description
                                ])

                            try:
                                scene_desc_for_iv = str(scene_description or "")
                            except Exception:
                                scene_desc_for_iv = ""

                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_desc_for_iv + (f" {spark_hints}" if spark_hints else ""),
                                user_action=f"arriving at {dest}",
                                action_outcome=f"Completed journey to {dest}",
                                function_hint="comment",
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            display_internal_voice_box(internal_voice)
                        except Exception as iv_err:
                            print(f"{Color.WARNING}[ARRIVAL] Could not generate internal voice: {iv_err}{Color.RESET}")
                        
                        # Advance time for final segment
                        req = master_time.create_user_action_request(
                            RuleOf3Category.THREE_MINUTE,
                            actor.sheet.name,
                            user_input
                        )
                        res = master_time.request_time_advancement(req)
                        
                        continue  # Skip to next turn (journey complete)
                    else:
                        # Still traveling - describe this segment
                        # dest now contains the current transitional location (corridor, hallway, etc.)
                        transitional_location = dest or f"Passage toward {destination}"
                        new_segment = current_segment + 1
                        journey_data = travel_chunking.get_progress()
                        cardinal_dir = journey_data.get("direction", "") if journey_data else ""
                        print(f"{Color.INFO}[TRAVEL] Segment {new_segment}/{total_segments}: Now in {transitional_location} (heading {cardinal_dir}){Color.RESET}")
                        
                        # Update spatial context for transitional location
                        try:
                            from spatial_context_system import get_spatial_manager, Position
                            spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                            
                            # Use helper to create transitional context with proper directional zones
                            travel_chunking.create_transitional_context(spatial, transitional_location, destination)
                            
                            # Switch to transitional location
                            spatial.set_current_location(transitional_location)
                            ua_name = actor.sheet.name if hasattr(actor, 'sheet') else "User Actor"
                            spatial.add_actor("ua_001", ua_name, Position(125, 180), is_user_actor=True)
                            
                            # Update context manager
                            if context_manager:
                                context_manager.context.current_location = transitional_location
                                context_manager._save()
                            
                            print(f"{Color.CYAN}🚶 JOURNEY{Color.RESET} Entered: {transitional_location}")
                            
                            # Sync pygame map
                            try:
                                from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                clear_layout_cache()
                                sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                            except Exception:
                                pass
                        except Exception as journey_viz_err:
                            print(f"{Color.WARNING}[JOURNEY] Transitional location error: {journey_viz_err}{Color.RESET}")
                        
                        # Generate perceptual description of this transitional space
                        direction_hint = f" heading {cardinal_dir}" if cardinal_dir else ""
                        segment_desc = narrator.generate_inquiry_response(
                            user_question=f"walking through {transitional_location}{direction_hint} toward {destination} (segment {new_segment} of {total_segments})",
                            ua_actor=actor,
                            scene_description=f"You are passing through {transitional_location},{direction_hint} heading toward {destination}.",
                            narrative_context=_merge_contexts("", everlasting_context_text, max_chars=1200),
                            current_time=master_time.get_current_time_context(),
                            availability_context={'availability': 'exist', 'reasoning': 'Traveling through transitional space'}
                        )
                        
                        print(f"\n{Color.NARRATIVE}{segment_desc}{Color.RESET}\n")
                        
                        # Generate internal voice for transitional segment
                        try:
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=segment_desc,
                                user_action=f"walking through {transitional_location} toward {destination}",
                                action_outcome=f"Continuing journey to {destination} (segment {new_segment}/{total_segments})",
                                function_hint="comment",
                                urgency="calm",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            display_internal_voice_box(internal_voice)
                        except Exception as iv_err:
                            print(f"{Color.WARNING}[TRAVEL] Could not generate internal voice: {iv_err}{Color.RESET}")
                        
                        # Advance time for this segment
                        req = master_time.create_user_action_request(
                            RuleOf3Category.THREE_MINUTE,
                            actor.sheet.name,
                            user_input
                        )
                        res = master_time.request_time_advancement(req)
                        
                        continue  # Skip to next turn (journey continues)
            
            # ============================================================
            # INQUIRY HANDLING - Questions only trigger internal voice
            # ============================================================
            # Use is_inquiry which includes fallback for question patterns
            if is_inquiry:
                print(f"\n{Color.INFO}📋 INQUIRY DETECTED{Color.RESET}")
                print(f"{Color.SYSTEM}Question: {user_input}{Color.RESET}")
                
                # Check memories related to the inquiry
                relevant_memories = []
                memory_strings = []
                try:
                    # Search key memories for relevant information
                    from key_memories_system import get_key_memories
                    key_mem_system = get_key_memories()  # Get the system instance
                    
                    # Use the system's search method
                    relevant_memories = key_mem_system.search_memories(user_input, limit=5)
                    
                    if relevant_memories:
                        print(f"{Color.INFO}💭 Relevant memories found: {len(relevant_memories)}{Color.RESET}")
                        for mem in relevant_memories[:3]:  # Show top 3
                            print(f"{Color.INFO}  - {mem.title}: {mem.description[:80]}...{Color.RESET}")
                        # Convert to strings for voice generator
                        memory_strings = [f"{mem.title}: {mem.description}" for mem in relevant_memories]
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}Memory search failed: {e}{Color.RESET}")
                
                # Get spatial information for location-based queries
                spatial_info = ""
                try:
                    from spatial_context_system import get_spatial_manager
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    if spatial:
                        actor_id = actor.sheet.name if hasattr(actor, 'sheet') else "unknown"
                        print(f"{Color.CYAN}[SPATIAL] Querying for actor '{actor_id}' with query '{user_input}'{Color.RESET}")
                        spatial_info = spatial.get_spatial_info_for_query(actor_id, user_input)
                        if spatial_info:
                            # Add spatial info to memory strings so voice generator can use it
                            memory_strings.insert(0, spatial_info)
                            print(f"{Color.CYAN}[SPATIAL] Found:\n{spatial_info}{Color.RESET}")
                        else:
                            print(f"{Color.WARNING}[SPATIAL] Query returned empty{Color.RESET}")
                    else:
                        print(f"{Color.WARNING}[SPATIAL] No spatial manager available{Color.RESET}")
                except Exception as e:
                    print(f"{Color.WARNING}Spatial query failed: {e}{Color.RESET}")
                
                # Get time information for time-related queries
                query_lower = user_input.lower()
                time_keywords = ['time', 'hour', 'day', 'night', 'morning', 'afternoon', 'evening', 
                                'when', 'long', 'late', 'early', 'shift', 'schedule', 'deadline']
                if any(kw in query_lower for kw in time_keywords):
                    try:
                        if master_time:
                            time_context = master_time.get_current_time_context()
                            if time_context:
                                time_info = f"TIME INFORMATION:\n- Current time: {time_context.get('time_string', 'Unknown')}"
                                if 'day' in time_context:
                                    time_info += f"\n- Day: {time_context.get('day', 'Unknown')}"
                                if 'period' in time_context:
                                    time_info += f"\n- Period: {time_context.get('period', 'Unknown')}"
                                memory_strings.insert(0, time_info)
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Time query failed: {e}{Color.RESET}")
                
                # Get goal/task information for purpose-related queries
                goal_keywords = ['goal', 'task', 'doing', 'supposed', 'mission', 'objective', 'purpose', 'job', 'work']
                if any(kw in query_lower for kw in goal_keywords):
                    try:
                        if hasattr(actor, 'sheet'):
                            goal_info = "CURRENT OBJECTIVES:\n"
                            if hasattr(actor.sheet, 'goal') and actor.sheet.goal:
                                goal_info += f"- Goal: {actor.sheet.goal}\n"
                            if hasattr(actor.sheet, 'current_task') and actor.sheet.current_task:
                                goal_info += f"- Current task: {actor.sheet.current_task}\n"
                            if hasattr(actor.sheet, 'occupation') and actor.sheet.occupation:
                                goal_info += f"- Occupation: {actor.sheet.occupation}\n"
                            if goal_info != "CURRENT OBJECTIVES:\n":
                                memory_strings.insert(0, goal_info)
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Goal query failed: {e}{Color.RESET}")
                
                # Get inventory information for possession-related queries
                inventory_keywords = ['have', 'carry', 'inventory', 'items', 'equipment', 'gear', 'pocket', 'bag']
                if any(kw in query_lower for kw in inventory_keywords):
                    try:
                        if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'inventory'):
                            items = actor.sheet.inventory if actor.sheet.inventory else []
                            if items:
                                inv_info = "INVENTORY:\n- " + "\n- ".join(str(item) for item in items[:10])
                                memory_strings.insert(0, inv_info)
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Inventory query failed: {e}{Color.RESET}")
                
                # Get condition information for status-related queries (diegetic descriptions)
                condition_keywords = ['feel', 'tired', 'hungry', 'health', 'condition', 'status', 'energy', 'stamina', 'hurt']
                if any(kw in query_lower for kw in condition_keywords):
                    try:
                        if hasattr(actor, 'sheet'):
                            cond_parts = []
                            # Describe condition diegetically, not as numbers
                            if hasattr(actor.sheet, 'stamina') and hasattr(actor.sheet, 'max_stamina'):
                                ratio = actor.sheet.stamina / actor.sheet.max_stamina if actor.sheet.max_stamina > 0 else 1
                                if ratio <= 0.25:
                                    cond_parts.append("Body feels drained, muscles screaming for rest")
                                elif ratio <= 0.5:
                                    cond_parts.append("Fatigue settling in, movements slower than usual")
                                elif ratio <= 0.75:
                                    cond_parts.append("Slightly winded but still capable")
                                else:
                                    cond_parts.append("Physically fresh, energy to spare")
                            
                            if hasattr(actor.sheet, 'spirit') and hasattr(actor.sheet, 'max_spirit'):
                                ratio = actor.sheet.spirit / actor.sheet.max_spirit if actor.sheet.max_spirit > 0 else 1
                                if ratio <= 0.25:
                                    cond_parts.append("Mind fraying at the edges, thoughts scattered")
                                elif ratio <= 0.5:
                                    cond_parts.append("Mental strain building, focus wavering")
                                elif ratio <= 0.75:
                                    cond_parts.append("Mind clear enough, some tension underneath")
                                else:
                                    cond_parts.append("Mentally sharp, thoughts flowing freely")
                            
                            if hasattr(actor.sheet, 'needs') and actor.sheet.needs:
                                needs = actor.sheet.needs
                                if hasattr(needs, 'food_hours') and needs.food_hours <= 12:
                                    cond_parts.append("Stomach growling, need to eat soon")
                                if hasattr(needs, 'water_hours') and needs.water_hours <= 6:
                                    cond_parts.append("Throat dry, thirst gnawing")
                                if hasattr(needs, 'sleep_hours') and needs.sleep_hours <= 6:
                                    cond_parts.append("Eyelids heavy, body craving sleep")
                            
                            if cond_parts:
                                cond_info = "CURRENT PHYSICAL/MENTAL STATE:\n- " + "\n- ".join(cond_parts)
                                memory_strings.insert(0, cond_info)
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Condition query failed: {e}{Color.RESET}")
                
                # Display perceptual transition into thought/inquiry
                # Diegetic description of character entering their thoughts (LLM-generated via NarratorAgent)
                try:
                    perceptual_desc = narrator.generate_inquiry_perceptual_description(
                        ua_actor=actor,
                        question=user_input,
                        scene_description=scene_description,
                        time_context=master_time.get_current_time_context() if master_time else None
                    )
                    if perceptual_desc:
                        display_perceptual_description_box(perceptual_desc)
                except Exception as e:
                    # Fallback to simple description
                    display_perceptual_description_box("You close your eyes, entering your thoughts.")
                
                # Generate internal voice using unified system (InternalVoiceCreatorAgent + NarratorAgent fallback)
                internal_voice = generate_unified_internal_voice(
                    actor=actor,
                    narrator=narrator,
                    scene_description=scene_description,
                    user_action=user_input,
                    action_outcome=f"Pondering: {user_input}",
                    function_hint="information",
                    question_content=user_input,
                    urgency="normal",
                    failure_tracker=failure_tracker,
                    narrative_context_manager=narrative_context_manager,
                    available_memories=memory_strings if memory_strings else None
                )
                
                # Display the internal voice
                display_internal_voice_box(internal_voice)
                
                # Save internal voice to narrative context
                if internal_voice:
                    try:
                        from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                        narrative_context_manager.add_narrative_event(
                            event_type=NarrativeEventType.INTERNAL_VOICE,
                            narrative_text=f"💭 {internal_voice}",
                            actors_involved=[actor.sheet.name],
                            importance=NarrativeImportance.NOTABLE,
                            emotional_tone="reflective"
                        )
                    except Exception as save_error:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Failed to save internal voice to context: {save_error}{Color.RESET}")
                
                # Inquiry complete - no action taken, no time advanced
                print(f"\n{Color.INFO}(Inquiry complete - no action taken){Color.RESET}")

                # Allow the world to keep moving: execute post-user turns in ROAM before next prompt.
                try:
                    execute_post_user_turns_if_roam()
                except Exception:
                    pass
                continue

            # If the action is a contested social interaction addressed to a NUA,
            # immediately transition into ENCOUNTER mode using our existing helpers.
            should_start_encounter = False
            if input_analysis and input_analysis.get('input_type') == 'contested_action':
                # Primary: if addressed_to matches a present NPC, start encounter.
                addressed_to = input_analysis.get('addressed_to')
                if addressed_to and available_npcs:
                    try:
                        should_start_encounter = any(
                            getattr(n.sheet, 'name', None) == addressed_to for n in available_npcs
                        )
                    except Exception:
                        should_start_encounter = False

            if should_start_encounter:
                
                # If already in encounter mode, don't re-initialize - just continue
                # The encounter loop handles the actual turn processing
                if current_mode == SimulationMode.ENCOUNTER:
                    # Already in encounter - this action will be processed in the encounter loop
                    # Update the participants if needed, but don't re-init
                    if not SUPPRESS_DEBUG:
                         print(f"{Color.SYSTEM}[ENCOUNTER] Continuing existing encounter...{Color.RESET}")
                    continue
                
                # Record the triggering input and any target hint for immediate use
                pending_encounter_action = user_input
                pending_target_hint = input_analysis.get('addressed_to') if input_analysis else None
                print(f"{Color.SYSTEM}[DEBUG] Extracted addressed_to: '{pending_target_hint}'{Color.RESET}")
                print(f"{Color.SYSTEM}[DEBUG] Full input_analysis: {input_analysis}{Color.RESET}")
                
                # CRITICAL CONTINUITY CHECK: Verify target NPC is accessible before allowing encounter
                # This prevents manifestation - you can't interact with someone who doesn't exist
                # However, we need to distinguish between:
                # 1. Face-to-face interactions (requires NPC physically present)
                # 2. Remote interactions (requires contact info in memories/context)
                
                # Check if this is a remote interaction (call, message, etc.)
                is_remote_interaction = any(word in user_input.lower() for word in [
                    'call', 'phone', 'dial', 'ring', 'message', 'text', 'page', 'contact'
                ])
                
                # For face-to-face interactions, require NPC to be physically present
                if not is_remote_interaction and not available_npcs:
                    print(f"\n{Color.WARNING}⚠️ CONTINUITY VIOLATION: No NPCs physically present{Color.RESET}")
                    
                    # Generate continuity failure narrative
                    try:
                        failure_narrative = narrator.generate_continuity_failure_narrative(
                            actor=actor,
                            attempted_action=user_input,
                            reason=f"There is no one here to interact with. {pending_target_hint or 'The person'} is not present in this location.",
                            scene_description=scene_description,
                            time_context=master_time.get_current_time_context() if master_time else None
                        )
                        
                        if failure_narrative:
                            print(f"\n{Color.NARRATIVE}{failure_narrative}{Color.RESET}")
                    except Exception as e:
                        # Fallback to simple message
                        target_hint = pending_target_hint or "The person you're trying to reach"
                        print(f"\n{Color.NARRATIVE}💭 There's no one here. {target_hint} isn't in this location.{Color.RESET}")

                    # Internal voice for the blocked interaction (use existing unified system)
                    try:
                        internal_voice = generate_unified_internal_voice(
                            actor=actor,
                            narrator=narrator,
                            scene_description=scene_description,
                            user_action=user_input,
                            action_outcome=failure_narrative or "No one here to interact with.",
                            function_hint="solution",
                            predicament=f"Cannot interact: {pending_target_hint or 'target'} not present.",
                            urgency="normal",
                            failure_tracker=failure_tracker,
                            narrative_context_manager=narrative_context_manager
                        )
                        display_internal_voice_box(internal_voice)
                    except Exception:
                        pass
                    
                    # Skip to next turn - action blocked
                    continue
                
                # For remote interactions, check if we have context about the target
                # This will be handled by Intent Availability system later in the flow
                # If no contact info exists, Intent Availability will return DOES_NOT_EXIST
                # and the action will be blocked with appropriate narrative

                # If this contested action implies movement to a new location (e.g., "go to diner and talk to waitress"),
                # check if travel is needed. If it's a long journey, start chunking instead of instant teleport.
                
                # OLD CODE (INSTANT TELEPORTATION - PRESERVED FOR ROLLBACK):
                # try:
                #     from spatial_context_system import get_spatial_manager
                #     spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                #     move_label = _detect_location_move(user_input, spatial_manager=spatial)
                #     if move_label:
                #         prev_desc = scene_description
                #         scene_description = _apply_location_move(
                #             conductor,
                #             move_label,
                #             master_time.get_current_time_context(),
                #             actor,
                #             prev_desc,
                #             narrative_context_manager,
                #             tracker,
                #             available_npcs
                #         )
                #         # CRITICAL: Display the new scene description to the player
                #         print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                # except Exception:
                #     pass
                
                # NEW CODE: Check travel time and use chunking if needed
                try:
                    from spatial_context_system import get_spatial_manager
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    current_location = context_manager.context.current_location or "Unknown Location"
                    move_label = _detect_location_move(user_input, spatial_manager=spatial)
                    
                    if move_label:
                        # Calculate travel time
                        travel_minutes = calculate_travel_time(current_location, move_label, spatial)
                        
                        if travel_minutes <= 3:
                            # Instant move - proceed with location change
                            # SAVE NPC names to context BEFORE clearing (for location state persistence)
                            if available_npcs:
                                npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                                context_manager.set_nuas(npc_names)
                            
                            # Clear NPCs and initiative from previous location BEFORE generating new ones
                            available_npcs.clear()
                            try:
                                from initiative_system import get_location_initiative_tracker
                                get_location_initiative_tracker().clear()
                            except ImportError:
                                pass
                            print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                            
                            prev_desc = scene_description
                            scene_description = _apply_location_move(
                                conductor,
                                move_label,
                                master_time.get_current_time_context(),
                                actor,
                                prev_desc,
                                narrative_context_manager,
                                tracker,
                                available_npcs,
                                population_manager=population_manager,
                                scene_creator=scene_creator,
                                actor_registry=global_actor_registry
                            )
                            print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                        else:
                            # Long journey - start chunking and defer social interaction
                            total_segments = travel_chunking.start_journey(move_label, travel_minutes, origin=current_location)
                            print(f"{Color.INFO}[TRAVEL] Journey to {move_label} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                            print(f"{Color.SYSTEM}You'll need to travel there first. Describe your first action...{Color.RESET}")
                            continue  # Skip social interaction until arrival
                except Exception:
                    pass
                else:
                    # Refresh scene from tracker authoritative source after move
                    try:
                        latest = tracker.get_current_scene()
                        latest_desc = (latest or {}).get('scene_description') if latest else None
                        if latest_desc:
                            scene_description = latest_desc
                            try:
                                conductor.scene_description = scene_description
                            except Exception:
                                pass
                    except Exception:
                        pass

                # Handle encounter based on interaction type
                if available_npcs:
                    # Face-to-face encounter: Select NPC from physically present actors
                    selected = None
                    hint = (pending_target_hint or "").lower()
                    if hint:
                        for n in available_npcs:
                            try:
                                name_lower = n.sheet.name.lower()
                                if any(word and word in name_lower for word in hint.split()):
                                    selected = n
                                    break
                            except Exception:
                                continue
                    if selected is None:
                        # Fallback to first available
                        selected = available_npcs[0]
                    # Initialize encounter with selected reactor
                    encounter_checker.current_context.participants = [selected]
                    encounter_checker.current_context.mode = SimulationMode.ENCOUNTER
                    current_mode = SimulationMode.ENCOUNTER
                    
                    # STORE THE TRIGGERING ACTION - This is the user's initial action that started the encounter
                    if not hasattr(encounter_checker.current_context, 'initial_user_action'):
                        encounter_checker.current_context.initial_user_action = user_input
                        print(f"{Color.SYSTEM}[ENCOUNTER] Stored initial action: '{user_input}'{Color.RESET}")
                    
                    print(f"\n{Color.SUCCESS}⚔️ ENCOUNTER INITIATED{Color.RESET}")
                    print(f"{Color.INFO}Reactor: {_ua_display_name(selected, ua_actor=actor)}{Color.RESET}")
                    try:
                        _display_actor_sheet_simple(selected, {'ua_actor': actor, 'show_outliers': True})
                    except Exception:
                        pass
                    # Proceed directly to encounter branch below (no re-prompt)
                    continue
                elif is_remote_interaction:
                    # Remote interaction: NPC doesn't need to be physically present
                    print(f"\n{Color.INFO}📞 REMOTE INTERACTION ATTEMPT{Color.RESET}")
                    print(f"{Color.SYSTEM}Target: {pending_target_hint or 'Unknown'}{Color.RESET}")
                    print(f"{Color.SYSTEM}Checking if contact information exists...{Color.RESET}")
                    
                    # STORE THE TRIGGERING ACTION
                    pending_encounter_action = user_input
                    print(f"{Color.SYSTEM}[REMOTE] Stored triggering action: '{user_input}'{Color.RESET}")
                    
                    # EXPLICIT AVAILABILITY CHECK (Avoid falling through to generic fallible action)
                    # We check availability here directly so we can start the encounter immediately on success
                    # without generating a separate "Action Result" narrative
                    
                    # Construct availability context
                    # We need to check if the user knows this person/number
                    availability_result = intent_system.evaluate_intent_availability(
                        user_intent=user_input,
                        narrative_context=_merge_contexts(narrative_context_manager.get_context_for_llm(lookback_events=5), everlasting_context_text, max_chars=1800),
                        scene_context=scene_description,
                        established_facts=[f"Target NUA: {pending_target_hint}"],
                        current_time_of_day=time_context.get('time_of_day', 'unknown')
                    )
                    
                    if availability_result['availability'] == IntentAvailability.EXIST:
                        # SUCCESS: Contact info exists -> Start Encounter IMMEDIATELY
                        print(f"{Color.SUCCESS}✓ Contact information found.{Color.RESET}")
                        
                        # Create/Retrieve NPC for the call
                        npc_context = narrative_context_manager.get_context_for_llm(lookback_events=10) if narrative_context_manager else ""
                        npc_context = _merge_contexts(npc_context, everlasting_context_text, max_chars=1800)
                        npc_prompt = (
                            f"Create an NUA named {pending_target_hint} for a PHONE CONVERSATION.\n\n"
                            f"**Context:**\n{npc_context[:800]}\n\n"
                            f"**Scene:** {scene_description[:400]}\n\n"
                            f"CRITICAL INSTRUCTIONS:\n"
                            f"1. This is a PHONE CONVERSATION - they are not physically present\n"
                            f"2. Use known details from context (occupation, relationship)\n"
                        )
                        
                        # Generate NPC
                        phone_npc = scene_creator.generate_nua(npc_prompt, scene_description)
                        
                        if phone_npc:
                            # Initialize Encounter and register for persistence
                            register_nua(phone_npc, available_npcs)
                            encounter_checker.current_context.participants = [phone_npc]
                            encounter_checker.current_context.mode = SimulationMode.ENCOUNTER
                            current_mode = SimulationMode.ENCOUNTER
                            encounter_checker.current_context.is_remote_encounter = True
                            encounter_checker.current_context.remote_encounter_type = "phone_call"
                            encounter_checker.current_context.remote_encounter_description = f"Phone conversation with {_ua_display_name(phone_npc, ua_actor=actor)}"
                            
                            # Clear pending action to avoid double-processing
                            pending_encounter_action = None
                            
                            print(f"{Color.SUCCESS}⚔️ PHONE CONVERSATION ENCOUNTER INITIATED{Color.RESET}")
                            print(f"{Color.INFO}📞 You are now on the phone with {_ua_display_name(phone_npc, ua_actor=actor)}{Color.RESET}")
                            
                            # SKIP fallible action processing - go straight to next loop (encounter)
                            continue
                        else:
                            print(f"{Color.WARNING}Phone rang but no answer... (NPC generation failed){Color.RESET}")
                            continue
                    else:
                        # FAILURE: Contact info not found
                        print(f"{Color.WARNING}✗ {availability_result.get('reasoning', 'Contact info unavailable')}{Color.RESET}")
                        
                        # Clear pending action so we don't loop with it
                        pending_encounter_action = None
                        pending_target_hint = None
                        
                        # Generate failure narrative
                        failure_narrative = narrator.generate_continuity_failure_narrative(
                            actor=actor,
                            attempted_action=user_input,
                            reason=availability_result.get('reasoning', 'You don\'t have their number.'),
                            scene_description=scene_description,
                            time_context=master_time.get_current_time_context() if master_time else None
                        )
                        print(f"\n{Color.NARRATIVE}{failure_narrative}{Color.RESET}\n")

                        # Internal voice for blocked remote interaction (use existing unified system)
                        try:
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=failure_narrative,
                                function_hint="solution",
                                predicament=f"Cannot contact target: {availability_result.get('reasoning', '')}",
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            display_internal_voice_box(internal_voice)
                        except Exception:
                            pass
                        continue

                else:
                    # This shouldn't happen - continuity check should have caught it
                    print(f"{Color.ERROR}⚠️ LOGIC ERROR: Reached encounter init with no NPCs and no remote interaction{Color.RESET}")
                    continue
            
            if input_analysis and input_analysis.get('input_type') == 'passive_action':
                # Handle passive actions (doing nothing, waiting, observing)
                # ALL actions use unified 3-phase system: perceptual + success + internal voice
                # NOTE: Passive actions are purely observational and cannot cause location changes
                print(f"\n{Color.SYSTEM}═══ Action Classification ═══{Color.RESET}")
                print(f"{Color.SYSTEM}Type: PASSIVE ACTION{Color.RESET}")
                print(f"{Color.SYSTEM}Reasoning: {input_analysis.get('reasoning', 'Character chooses to wait/observe') if input_analysis else 'N/A'}{Color.RESET}")
                
                # PHASE 1: Generate perceptual description (NarratorAgent)
                perceptual_description = narrator.generate_inquiry_perceptual_description(
                    ua_actor=actor,
                    question=user_input,
                    scene_description=scene_description,
                    narrative_context=recent_context,
                    time_context=master_time.get_current_time_context() if master_time else None
                )
                
                # Display perceptual description
                display_perceptual_description_box(perceptual_description)
                
                # Update scene description with new perceptual information
                scene_description = f"{scene_description}\n\n{perceptual_description}"
                _capture_continuity_facts_from_text(perceptual_description, source="perceptual", base_confidence=0.65)
                try:
                    _capture_mentioned_actors_from_text(perceptual_description, source="perceptual")
                except Exception:
                    pass
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
                
                # PHASE 3: Generate internal voice (unified system)
                internal_voice = generate_unified_internal_voice(
                    actor=actor,
                    narrator=narrator,
                    scene_description=scene_description,
                    user_action=user_input,
                    action_outcome=perceptual_description,
                    function_hint="comment",
                    urgency="calm",
                    failure_tracker=failure_tracker,
                    narrative_context_manager=narrative_context_manager
                )
                
                display_internal_voice_box(internal_voice)
                
                # Advance time (doing nothing still takes time)
                try:
                    time_request = master_time.create_user_action_request(
                        RuleOf3Category.THREE_MINUTE,
                        actor.sheet.name,
                        user_input
                    )
                    time_result = master_time.request_time_advancement(time_request)
                    print(f"{Color.INFO}⏰ Time: {master_time.time_tracker.get_current_time().format_full()}{Color.RESET}")
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}Time advancement skipped: {e}{Color.RESET}")
                
                # Update time context
                try:
                    time_context = master_time.get_current_time_context()
                except Exception:
                    pass
                
                # Continue to next turn
                continue
            
            if input_analysis and input_analysis.get('input_type') == 'given_action':
                # Handle given actions (trivial, automatic success)
                # ALL actions use unified 3-phase system: perceptual + success + internal voice
                print(f"\n{Color.SYSTEM}═══ Action Classification ═══{Color.RESET}")
                print(f"{Color.SYSTEM}Type: GIVEN ACTION{Color.RESET}")
                print(f"{Color.SYSTEM}Reasoning: {input_analysis.get('reasoning', 'Trivial action with automatic success') if input_analysis else 'Command/Meta-action'}{Color.RESET}")
                
                # Check for location move FIRST - if it's a location change, handle it with chunking
                
                # OLD CODE (INSTANT TELEPORTATION - PRESERVED FOR ROLLBACK):
                # location_changed = False
                # try:
                #     from spatial_context_system import get_spatial_manager
                #     spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                #     move_label = _detect_location_move(user_input, "", spatial_manager=spatial)
                #     if move_label:
                #         print(f"{Color.SYSTEM}[LOCATION] Detected move to: {move_label}{Color.RESET}")
                #         prev_desc = scene_description
                #         scene_description = _apply_location_move(
                #             conductor, move_label, master_time.get_current_time_context(),
                #             actor, prev_desc, narrative_context_manager, tracker, available_npcs
                #         )
                #         # CRITICAL: Display the new scene description to the player
                #         print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                #         
                #         location_changed = True
                #         
                #         # Clear NPCs from previous location
                #         available_npcs.clear()
                #         print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                #         
                #         # Location change already generated narrative, skip to time advancement
                #         # (time advancement happens later in the given action block)
                # except Exception as e:
                #     print(f"{Color.WARNING}[LOCATION] Could not process location change: {e}{Color.RESET}")
                #     location_changed = False
                
                # NEW CODE: Check travel time and use chunking if needed
                location_changed = False
                try:
                    from spatial_context_system import get_spatial_manager
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    current_location = context_manager.context.current_location or "Unknown Location"
                    
                    # ============================================================
                    # JOURNEY CONTINUATION CHECK (MUST BE FIRST)
                    # ============================================================
                    # Check if user is continuing an active journey BEFORE detecting new moves
                    journey_progress = travel_chunking.get_progress()
                    if journey_progress:
                        destination = journey_progress["destination"]
                        current_segment = journey_progress["current_segment"]
                        total_segments = journey_progress["total_segments"]
                        
                        # FIRST: Check if user wants to go somewhere DIFFERENT (destination change)
                        new_destination = _detect_location_move(user_input, "", spatial_manager=spatial)
                        if new_destination and new_destination.lower() != destination.lower():
                            # User changed their mind - cancel current journey and start new one
                            print(f"{Color.WARNING}[TRAVEL] Destination changed: {destination} → {new_destination}{Color.RESET}")
                            travel_chunking.cancel_journey()
                            
                            # Calculate travel time to NEW destination from current position
                            # (We're mid-journey, so estimate from current location)
                            travel_minutes = calculate_travel_time(current_location, new_destination, spatial)
                            
                            if travel_minutes <= 3:
                                # Instant move to new destination
                                print(f"{Color.SYSTEM}[LOCATION] Redirecting to {new_destination} (instant){Color.RESET}")
                                prev_desc = scene_description
                                scene_description = _apply_location_move(
                                    conductor, new_destination, master_time.get_current_time_context(),
                                    actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                    population_manager=population_manager,
                                    scene_creator=scene_creator,
                                    actor_registry=global_actor_registry
                                )
                                print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                            else:
                                # Start new journey to different destination
                                total_segments = travel_chunking.start_journey(new_destination, travel_minutes, origin=current_location)
                                print(f"{Color.INFO}[TRAVEL] New journey to {new_destination} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                                print(f"{Color.SYSTEM}Describe your first action as you head toward {new_destination}...{Color.RESET}")
                            continue
                        
                        # Check if user input indicates continuing toward ORIGINAL destination
                        continuing = any(word in user_input.lower() for word in 
                            ["continue", "keep going", "keep walking", "walk", "go", "head", destination.lower()])
                        
                        if continuing:
                            # Advance to next segment
                            completed, dest = travel_chunking.advance_segment()
                            
                            if completed:
                                # Journey complete - arrive at destination
                                print(f"{Color.SUCCESS}[TRAVEL] Arrived at {dest}!{Color.RESET}")
                                
                                # SAVE NPC names to context BEFORE clearing (for location state persistence)
                                if available_npcs:
                                    npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                                    context_manager.set_nuas(npc_names)
                                
                                # Clear NPCs and initiative from previous location BEFORE generating new ones
                                available_npcs.clear()
                                try:
                                    from initiative_system import get_location_initiative_tracker
                                    get_location_initiative_tracker().clear()
                                except ImportError:
                                    pass
                                print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                                
                                # Generate arrival scene description (will populate new NPCs and roll initiative)
                                prev_desc = scene_description
                                scene_description = _apply_location_move(
                                    conductor, dest, master_time.get_current_time_context(),
                                    actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                    population_manager=population_manager,
                                    scene_creator=scene_creator,
                                    actor_registry=global_actor_registry
                                )
                                
                                # Sync pygame map to new location
                                try:
                                    from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                    print(f"{Color.SYSTEM}[PMAP] Clearing cache and syncing to new location: {dest}{Color.RESET}")
                                    clear_layout_cache()  # Clear old location's cached layout
                                    sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                except Exception as pmap_err:
                                    print(f"{Color.WARNING}[PMAP] Sync error on arrival: {pmap_err}{Color.RESET}")
                                
                                # Generate storyteller sparks BEFORE displaying scene (for integration)
                                sparks = generate_location_arrival_sparks(
                                    location=dest,
                                    scene_description=scene_description,
                                    available_npcs=available_npcs,
                                    narrative_context_manager=narrative_context_manager,
                                    actor=actor,
                                    conductor=conductor,
                                    display_sparks=False  # We'll display after scene
                                )
                                
                                # Display arrival scene first, then sparks separately for testing clarity
                                print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")

                                try:
                                    if _env_bool("VIS_IMAGE_AUTOGEN_JOURNEY", False):
                                        _trigger_realtime_image(
                                            ua_actor=actor,
                                            scene_description=scene_description,
                                            current_location=str(dest or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                            spoken_line="",
                                            source="perceptual",
                                            reason="journey_arrival",
                                        )
                                except Exception:
                                    pass

                                try:
                                    for spark in (sparks or [])[:3]:
                                        if hasattr(spark, 'trigger_description') and spark.trigger_description:
                                            print(f"{Color.STATUS}✨ {spark.trigger_description}{Color.RESET}")
                                except Exception:
                                    pass
                                
                                # Generate internal voice for arrival
                                try:
                                    # Build spark context for internal voice
                                    spark_hints = ""
                                    if sparks:
                                        spark_hints = " ".join([
                                            s.trigger_description[:100] for s in sparks[:2] 
                                            if hasattr(s, 'trigger_description') and s.trigger_description
                                        ])
                                    
                                    internal_voice = generate_unified_internal_voice(
                                        actor=actor,
                                        narrator=narrator,
                                        scene_description=scene_description + (f" {spark_hints}" if spark_hints else ""),
                                        user_action=f"arriving at {dest}",
                                        action_outcome=f"Completed journey to {dest}",
                                        function_hint="comment",
                                        urgency="normal",
                                        failure_tracker=failure_tracker,
                                        narrative_context_manager=narrative_context_manager
                                    )
                                    display_internal_voice_box(internal_voice)
                                except Exception as iv_err:
                                    print(f"{Color.WARNING}[ARRIVAL] Could not generate internal voice: {iv_err}{Color.RESET}")
                                
                                # Advance time for final segment
                                req = master_time.create_user_action_request(
                                    RuleOf3Category.THREE_MINUTE,
                                    actor.sheet.name,
                                    user_input
                                )
                                res = master_time.request_time_advancement(req)
                                
                                continue  # Skip to next turn (journey arrival in given_action)
                            else:
                                # Still traveling - describe this segment
                                # dest now contains the current transitional location (corridor, hallway, etc.)
                                transitional_location = dest or f"Passage toward {destination}"
                                new_segment = current_segment + 1
                                journey_data = travel_chunking.get_progress()
                                cardinal_dir = journey_data.get("direction", "") if journey_data else ""
                                print(f"{Color.INFO}[TRAVEL] Segment {new_segment}/{total_segments}: Now in {transitional_location} (heading {cardinal_dir}){Color.RESET}")
                                
                                # Update spatial context for transitional location
                                try:
                                    from spatial_context_system import get_spatial_manager, Position
                                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                    
                                    # Use helper to create transitional context with proper directional zones
                                    travel_chunking.create_transitional_context(spatial, transitional_location, destination)
                                    
                                    # Switch to transitional location
                                    spatial.set_current_location(transitional_location)
                                    ua_name = actor.sheet.name if hasattr(actor, 'sheet') else "User Actor"
                                    spatial.add_actor("ua_001", ua_name, Position(125, 180), is_user_actor=True)
                                    
                                    # Update context manager
                                    if context_manager:
                                        context_manager.context.current_location = transitional_location
                                        context_manager._save()
                                    
                                    print(f"{Color.CYAN}🚶 JOURNEY{Color.RESET} Entered: {transitional_location}")
                                    
                                    # Sync pygame map
                                    try:
                                        from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                        clear_layout_cache()
                                        sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                    except Exception:
                                        pass
                                except Exception as journey_viz_err:
                                    print(f"{Color.WARNING}[JOURNEY] Transitional location error: {journey_viz_err}{Color.RESET}")
                                
                                # Generate perceptual description of this transitional space
                                direction_hint = f" heading {cardinal_dir}" if cardinal_dir else ""
                                segment_desc = narrator.generate_inquiry_response(
                                    user_question=f"walking through {transitional_location}{direction_hint} toward {destination} (segment {new_segment} of {total_segments})",
                                    ua_actor=actor,
                                    scene_description=f"You are passing through {transitional_location},{direction_hint} heading toward {destination}.",
                                    narrative_context=_merge_contexts("", everlasting_context_text, max_chars=1200),
                                    current_time=master_time.get_current_time_context(),
                                    availability_context={'availability': 'exist', 'reasoning': 'Traveling through transitional space'}
                                )
                                
                                print(f"\n{Color.NARRATIVE}{segment_desc}{Color.RESET}\n")

                                # Optional: generate an image for this journey segment.
                                try:
                                    if _env_bool("VIS_IMAGE_AUTOGEN_JOURNEY", False):
                                        _interval = 1
                                        try:
                                            _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_JOURNEY_INTERVAL") or "1")
                                        except Exception:
                                            _interval = 1
                                        if _interval < 1:
                                            _interval = 1
                                        if (int(new_segment) % _interval) == 0:
                                            _trigger_realtime_image(
                                                ua_actor=actor,
                                                scene_description=str(segment_desc or ''),
                                                current_location=str(transitional_location or ''),
                                                time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                                creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                                seed=None,
                                                spoken_line=str(segment_desc or ''),
                                                source="perceptual",
                                                reason=f"journey_segment_{new_segment}",
                                            )
                                except Exception:
                                    pass
                                except Exception:
                                    pass
                                
                                # Generate internal voice for transitional segment
                                try:
                                    internal_voice = generate_unified_internal_voice(
                                        actor=actor,
                                        narrator=narrator,
                                        scene_description=segment_desc,
                                        user_action=f"walking through {transitional_location} toward {destination}",
                                        action_outcome=f"Continuing journey to {destination} (segment {new_segment}/{total_segments})",
                                        function_hint="comment",
                                        urgency="calm",
                                        failure_tracker=failure_tracker,
                                        narrative_context_manager=narrative_context_manager
                                    )
                                    display_internal_voice_box(internal_voice)
                                except Exception as iv_err:
                                    print(f"{Color.WARNING}[TRAVEL] Could not generate internal voice: {iv_err}{Color.RESET}")
                                
                                # Advance time for this segment
                                req = master_time.create_user_action_request(
                                    RuleOf3Category.THREE_MINUTE,
                                    actor.sheet.name,
                                    user_input
                                )
                                res = master_time.request_time_advancement(req)
                                
                                continue  # Skip to next turn (journey continues)
                        else:
                            # User strayed from path - cancel journey
                            print(f"{Color.WARNING}[TRAVEL] Journey to {destination} cancelled (strayed from path){Color.RESET}")
                            travel_chunking.cancel_journey()
                            # Fall through to normal action processing
                    
                    # ============================================================
                    # NEW LOCATION MOVE DETECTION (only if no active journey)
                    # ============================================================
                    move_label = _detect_location_move(user_input, "", spatial_manager=spatial)
                    
                    if move_label:
                        # Calculate travel time
                        travel_minutes = calculate_travel_time(current_location, move_label, spatial)
                        
                        if travel_minutes <= 3:
                            # Instant move
                            print(f"{Color.SYSTEM}[LOCATION] Moving to {move_label} (instant){Color.RESET}")
                            
                            # SAVE NPC names to context BEFORE clearing (for location state persistence)
                            if available_npcs:
                                npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                                context_manager.set_nuas(npc_names)
                            
                            # Clear NPCs and initiative from previous location BEFORE generating new ones
                            available_npcs.clear()
                            try:
                                from initiative_system import get_location_initiative_tracker
                                get_location_initiative_tracker().clear()
                            except ImportError:
                                pass
                            print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                            
                            prev_desc = scene_description
                            scene_description = _apply_location_move(
                                conductor, move_label, master_time.get_current_time_context(),
                                actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                population_manager=population_manager,
                                scene_creator=scene_creator,
                                actor_registry=global_actor_registry
                            )
                            
                            location_changed = True
                            
                            # Generate storyteller sparks BEFORE displaying scene (for integration)
                            sparks = generate_location_arrival_sparks(
                                location=move_label,
                                scene_description=scene_description,
                                available_npcs=available_npcs,
                                narrative_context_manager=narrative_context_manager,
                                actor=actor,
                                conductor=conductor,
                                display_sparks=False  # We'll display after scene
                            )
                            
                            # Display arrival scene first, then sparks separately for testing clarity
                            print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")

                            try:
                                for spark in (sparks or [])[:3]:
                                    if hasattr(spark, 'trigger_description') and spark.trigger_description:
                                        print(f"{Color.STATUS}✨ {spark.trigger_description}{Color.RESET}")
                            except Exception:
                                pass
                            
                            # Generate internal voice for arrival
                            try:
                                # Build spark context for internal voice
                                spark_hints = ""
                                if sparks:
                                    spark_hints = " ".join([
                                        s.trigger_description[:100] for s in sparks[:2] 
                                        if hasattr(s, 'trigger_description') and s.trigger_description
                                    ])

                                try:
                                    scene_desc_for_iv = str(scene_description or "")
                                except Exception:
                                    scene_desc_for_iv = ""
                                
                                internal_voice = generate_unified_internal_voice(
                                    actor=actor,
                                    narrator=narrator,
                                    scene_description=scene_desc_for_iv + (f" {spark_hints}" if spark_hints else ""),
                                    user_action=f"arriving at {move_label}",
                                    action_outcome=f"Arrived at {move_label}",
                                    function_hint="comment",
                                    urgency="normal",
                                    failure_tracker=failure_tracker,
                                    narrative_context_manager=narrative_context_manager
                                )
                                display_internal_voice_box(internal_voice)
                            except Exception as iv_err:
                                print(f"{Color.WARNING}[ARRIVAL] Could not generate internal voice: {iv_err}{Color.RESET}")
                        else:
                            # Long journey - start chunking
                            total_segments = travel_chunking.start_journey(move_label, travel_minutes, origin=current_location)
                            print(f"{Color.INFO}[TRAVEL] Journey to {move_label} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                            
                            # Generate departure narrative
                            try:
                                departure_narrative = narrator.generate_travel_departure_narrative(
                                    actor_name=actor.sheet.name,
                                    origin=scene_description,
                                    destination=move_label,
                                    travel_time_minutes=travel_minutes,
                                    current_time=master_time.get_current_time_context()
                                )
                                print(f"\n{Color.NARRATIVE}{departure_narrative}{Color.RESET}\n")
                                
                                # CRITICAL: Save to context immediately so next action knows we left
                                if narrative_context_manager:
                                    from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                                    narrative_context_manager.add_narrative_event(
                                        event_type=NarrativeEventType.ACTION_SEQUENCE,
                                        narrative_text=departure_narrative,
                                        actors_involved=[actor.sheet.name],
                                        importance=NarrativeImportance.NOTABLE,
                                        scene_context=f"Departure to {move_label}"
                                    )
                                
                                # Update scene description to reflect departure
                                scene_description = f"{scene_description}\n\n{departure_narrative}"
                                try:
                                    conductor.scene_description = scene_description
                                    tracker.set_current_scene(scene_description)
                                except Exception:
                                    pass
                            except Exception as e:
                                print(f"{Color.WARNING}[TRAVEL] Could not generate departure narrative: {e}{Color.RESET}")
                            
                            # Generate internal voice about the journey (unified system)
                            try:
                                internal_voice = generate_unified_internal_voice(
                                    actor=actor,
                                    narrator=narrator,
                                    scene_description=scene_description,
                                    user_action=f"traveling to {move_label}",
                                    action_outcome=f"Beginning journey to {move_label}",
                                    function_hint="comment",
                                    urgency="normal",
                                    failure_tracker=failure_tracker,
                                    narrative_context_manager=narrative_context_manager
                                )
                                display_internal_voice_box(internal_voice)
                            except Exception as e:
                                print(f"{Color.WARNING}[TRAVEL] Could not generate travel thoughts: {e}{Color.RESET}")
                            
                            print(f"{Color.SYSTEM}Describe your first action as you begin traveling...{Color.RESET}")
                            
                            # ============================================================
                            # JOURNEY START: Move actor TO the exit to show departure
                            # The narrative describes leaving, so actor should be at exit
                            # ============================================================
                            try:
                                current_pos = spatial.get_actor_position("ua_001")
                                if current_pos:
                                    from spatial_context_system import DEFAULT_MAP_WIDTH as _DMW, DEFAULT_MAP_HEIGHT as _DMH
                                    MAP_WIDTH, MAP_HEIGHT = float(_DMW), float(_DMH)
                                    try:
                                        ctx = spatial.get_current_context() if spatial else None
                                        dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                                        if dims:
                                            MAP_WIDTH = float(getattr(dims, 'width', MAP_WIDTH) or MAP_WIDTH)
                                            MAP_HEIGHT = float(getattr(dims, 'height', MAP_HEIGHT) or MAP_HEIGHT)
                                    except Exception:
                                        pass
                                    # current_pos is already a Position object, use .x/.y directly
                                    start_x, start_y = current_pos.x, current_pos.y
                                    
                                    exit_x, exit_y = MAP_WIDTH / 2, MAP_HEIGHT * 0.08
                                    try:
                                        candidates = []
                                        if dims:
                                            for _ok, _o in (getattr(dims, 'obstacles', {}) or {}).items():
                                                try:
                                                    onm = str(getattr(_o, 'obstacle_name', '') or '')
                                                    ot = str(getattr(_o, 'obstacle_type', '') or '')
                                                    pk = str(getattr(_o, 'portal_kind', '') or '')
                                                    cfrom = str(getattr(_o, 'connects_from', '') or '')
                                                    cto = str(getattr(_o, 'connects_to', '') or '')
                                                    is_ext = bool(getattr(_o, 'is_external', False))
                                                    nm_l = onm.lower()
                                                    ot_l = ot.lower()
                                                    pk_l = pk.lower()

                                                    is_doorish = (
                                                        ot_l in ('door', 'exit')
                                                        or any(k in nm_l for k in ('door', 'exit', 'entrance', 'gateway', 'hatch', 'trapdoor', 'grate'))
                                                        or pk_l in ('door', 'exit', 'entrance', 'gateway', 'hatch', 'grate')
                                                        or (pk_l and (is_ext or cto.lower() in ('outside', 'street')))
                                                    )
                                                    if not is_doorish:
                                                        continue

                                                    bps = getattr(_o, 'boundary_points', None) or []
                                                    if not bps:
                                                        continue
                                                    cx = sum(float(getattr(p, 'x', 0.0) or 0.0) for p in bps) / float(len(bps))
                                                    cy = sum(float(getattr(p, 'y', 0.0) or 0.0) for p in bps) / float(len(bps))
                                                    candidates.append((cx, cy))
                                                except Exception:
                                                    continue

                                        if candidates:
                                            def _dist2(px, py):
                                                dx = float(px) - float(start_x)
                                                dy = float(py) - float(start_y)
                                                return (dx * dx) + (dy * dy)
                                            best = min(candidates, key=lambda t: _dist2(t[0], t[1]))
                                            exit_x, exit_y = float(best[0]), float(best[1])
                                    except Exception:
                                        pass
                                    
                                    # Move TO the exit on journey start (95% of the way)
                                    # This matches the narrative which describes leaving the location
                                    new_x = start_x + (exit_x - start_x) * 0.95
                                    new_y = start_y + (exit_y - start_y) * 0.95
                                    
                                    spatial.move_actor("ua_001", Position(new_x, new_y))
                                    print(f"{Color.CYAN}🚶 JOURNEY START{Color.RESET}: ({start_x:.0f},{start_y:.0f}) → ({new_x:.0f},{new_y:.0f}) [AT EXIT]")
                                    
                                    # Sync pygame map - DEBUG
                                    print(f"{Color.INFO}[JOURNEY] Attempting pygame map sync...{Color.RESET}")
                                    try:
                                        from pygame_spatial_map import get_pygame_map, auto_sync_map as sync_map
                                        map_inst = get_pygame_map()
                                        print(f"{Color.INFO}[JOURNEY] Map instance exists: {map_inst is not None}, running: {map_inst.running if map_inst else 'N/A'}{Color.RESET}")
                                        sync_map(session_id=tracker.session_id if tracker else None)
                                    except Exception as sync_err:
                                        import traceback
                                        print(f"{Color.WARNING}[JOURNEY] Sync error: {sync_err}{Color.RESET}")
                                        traceback.print_exc()
                            except Exception as e:
                                print(f"{Color.WARNING}[JOURNEY] Start visualization error: {e}{Color.RESET}")
                            
                            continue  # Skip to next turn for first segment (given_action block)
                            
                except Exception as e:
                    print(f"{Color.WARNING}[LOCATION] Could not process location change: {e}{Color.RESET}")
                    location_changed = False
                
                # Only generate normal narrative if we DIDN'T change location
                if not location_changed:
                    # ============================================================
                    # IN-ROOM MOVEMENT PROCESSING (for given actions)
                    # ============================================================
                    # ARCHITECT handles movement resolution - consolidated logic
                    if input_analysis and input_analysis.get('explicit_movement') and input_analysis.get('movement_target'):
                        try:
                            from agents.architect_agent import resolve_movement_target
                            from spatial_context_system import Position, MovementSpeed
                            
                            target = input_analysis.get('movement_target')
                            # Do not "walk to" vague needs (food/water/etc.). Default is in-place searching.
                            try:
                                if _is_vague_need_movement(user_input, str(target or '')):
                                    target = None
                                    input_analysis['explicit_movement'] = False
                                    input_analysis['movement_target'] = None
                            except Exception:
                                pass
                            if not target:
                                raise Exception("Vague needs-movement suppressed")
                            context = spatial.get_current_context()
                            current_pos = spatial.get_actor_position("ua_001")
                            
                            if context and current_pos:
                                # ARCHITECT: Resolve target to validated coordinates
                                resolved = resolve_movement_target(
                                    target=target,
                                    current_position=(current_pos.x, current_pos.y),
                                    spatial_context=context,
                                    user_input=user_input
                                )
                                
                                if resolved:
                                    new_position = Position(resolved[0], resolved[1])

                                    # Ensure "approach/get near/head to" actually ends within 1.0 unit
                                    # of the matched target actor/obstacle to avoid interaction-distance confusion.
                                    try:
                                        desired_stop_distance = 1.0
                                        target_lower = str(target or '').strip().lower()

                                        target_pos = None
                                        # Match target actor by name substring
                                        try:
                                            for aid, apos in (getattr(context, 'actor_positions', {}) or {}).items():
                                                if str(aid) == "ua_001":
                                                    continue
                                                nm = str(getattr(apos, 'actor_name', '') or '').strip().lower()
                                                if nm and target_lower and (target_lower in nm or nm in target_lower):
                                                    target_pos = getattr(apos, 'position', None)
                                                    break
                                        except Exception:
                                            target_pos = None

                                        # Match target obstacle by name substring
                                        if target_pos is None:
                                            try:
                                                dims = getattr(context, 'location_dimensions', None)
                                                obstacles = getattr(dims, 'obstacles', {}) if dims else {}
                                                for obs_id, obs in (obstacles or {}).items():
                                                    obs_name = str(getattr(obs, 'obstacle_name', obs_id) or '').strip().lower()
                                                    obs_key = str(obs_id or '').strip().lower()
                                                    if not target_lower:
                                                        continue
                                                    if target_lower in obs_name or obs_name in target_lower or target_lower in obs_key or obs_key in target_lower:
                                                        if hasattr(obs, 'boundary_points') and obs.boundary_points:
                                                            cx = sum(p.x for p in obs.boundary_points) / len(obs.boundary_points)
                                                            cy = sum(p.y for p in obs.boundary_points) / len(obs.boundary_points)
                                                            target_pos = Position(cx, cy)
                                                        break
                                            except Exception:
                                                target_pos = None

                                        if target_pos is not None:
                                            try:
                                                dist_to_target = new_position.distance_to(target_pos)
                                            except Exception:
                                                dist_to_target = None

                                            if dist_to_target is not None and dist_to_target > desired_stop_distance:
                                                dx = target_pos.x - current_pos.x
                                                dy = target_pos.y - current_pos.y
                                                dist_from_current = (dx ** 2 + dy ** 2) ** 0.5
                                                if dist_from_current > desired_stop_distance:
                                                    scale = (dist_from_current - desired_stop_distance) / dist_from_current
                                                    new_position = Position(current_pos.x + dx * scale, current_pos.y + dy * scale)
                                    except Exception:
                                        pass
                                    
                                    # Get movement type from input
                                    movement_verbs = ['walk', 'run', 'sprint', 'jog', 'sneak', 'crawl', 'head', 'go', 'move', 'approach']
                                    movement_type = 'walk'
                                    input_lower = user_input.lower()
                                    for verb in movement_verbs:
                                        if verb in input_lower:
                                            if verb in ['head', 'go', 'move', 'approach']:
                                                movement_type = 'walk'
                                            else:
                                                movement_type = verb
                                            break
                                    
                                    # Map movement type to speed
                                    speed_map = {
                                        'crawl': MovementSpeed.CRAWL,
                                        'sneak': MovementSpeed.SNEAK,
                                        'walk': MovementSpeed.WALK,
                                        'jog': MovementSpeed.JOG,
                                        'run': MovementSpeed.RUN,
                                        'sprint': MovementSpeed.SPRINT
                                    }
                                    speed = speed_map.get(movement_type.lower(), MovementSpeed.WALK)
                                    
                                    # Get actor's Swiftness for movement time calculation
                                    from actor_sheet import SFactorType
                                    swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                                    
                                    # Calculate movement time
                                    movement_time_seconds, unit_time = current_pos.calculate_movement_time_with_ut(
                                        new_position, speed, swiftness
                                    )
                                    distance = current_pos.distance_to(new_position)
                                    
                                    # Update position in spatial context
                                    spatial.move_actor("ua_001", new_position)
                                    
                                    # Display movement info
                                    print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {movement_type.capitalize()} to '{target}': ({current_pos.x:.1f}, {current_pos.y:.1f}) → ({new_position.x:.1f}, {new_position.y:.1f})")
                                    print(f"{Color.SYSTEM}[MOVEMENT] Distance: {distance:.1f} units | Time: {movement_time_seconds:.1f}s ({unit_time} UT){Color.RESET}")
                                    
                                    # Sync pygame map to show movement and trail
                                    try:
                                        from pygame_spatial_map import auto_sync_map
                                        auto_sync_map(session_id=tracker.session_id if tracker else None)
                                    except Exception as sync_err:
                                        print(f"{Color.WARNING}[MOVEMENT] Map sync failed: {sync_err}{Color.RESET}")
                        except Exception as e:
                            # Movement suppression is expected for vague needs; only warn for real failures.
                            try:
                                if 'Vague needs-movement suppressed' not in str(e):
                                    print(f"{Color.WARNING}[MOVEMENT] In-room movement failed: {e}{Color.RESET}")
                            except Exception:
                                pass
                    
                    # Get context for narrative generation
                    recent_context = narrative_context_manager.get_context_for_llm(
                        lookback_events=5,
                        importance_threshold="notable"
                    )
                    recent_context = _merge_contexts(recent_context, everlasting_context_text)
                    
                    # Get NUA actions context for perceptual awareness
                    nua_actions = _get_nua_actions_context(tracker, f"actor_{actor.sheet.name.lower().replace(' ', '_')}")
                    
                    # PHASE 1: Generate perceptual description (what you physically do)
                    perceptual_description = narrator.generate_inquiry_response(
                        user_question=user_input,
                        ua_actor=actor,
                        scene_description=scene_description,
                        narrative_context=recent_context,
                        current_time=time_context,
                        availability_context={'availability': 'exist', 'reasoning': 'Given action'},
                        nua_actions_context=nua_actions,
                        explicit_movement=input_analysis.get('explicit_movement', False),
                        movement_target=input_analysis.get('movement_target')
                    )
                    
                    # Display perceptual description
                    display_perceptual_description_box(perceptual_description)
                    
                    # Update scene description with new perceptual information
                    scene_description = f"{scene_description}\n\n{perceptual_description}"
                    _capture_continuity_facts_from_text(perceptual_description, source="perceptual", base_confidence=0.65)
                    try:
                        _capture_mentioned_actors_from_text(perceptual_description, source="perceptual")
                    except Exception:
                        pass
                    try:
                        conductor.scene_description = scene_description
                    except Exception:
                        pass
                    
                    # Persist to authoritative tracker
                    try:
                        tracker.set_current_scene(scene_description)
                    except Exception:
                        pass
                    
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
                            scene_id=scene_id,
                            mention_system=mention_system
                        )
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")
                    
                    # PHASE 2: Success (automatic for given actions)
                    print(f"\n{Color.SUCCESS}✅ AUTOMATIC SUCCESS{Color.RESET}")
                    print(f"{Color.SUCCESS}Result: No roll required - trivial action{Color.RESET}\n")
                    
                    # PHASE 3: Generate internal voice (mental reaction)
                    internal_voice = generate_unified_internal_voice(
                        actor=actor,
                        narrator=narrator,
                        scene_description=scene_description,
                        user_action=user_input,
                        action_outcome=perceptual_description or "Action completed successfully.",
                        function_hint="comment",
                        urgency="calm",  # Trivial action - relaxed tone
                        failure_tracker=failure_tracker,
                        narrative_context_manager=narrative_context_manager
                    )
                    
                    # Display internal voice
                    display_internal_voice_box(internal_voice)
                
                # Update actor tasks for given actions (simple interpretation)
                try:
                    # Create simple interpretation for given actions
                    simple_interpretation = {
                        'action_description': user_input,
                        'action_noun': user_input.split()[0] if user_input.split() else ''
                    }
                    conductor.interpreter.update_actor_tasks(
                        user_action=user_input,
                        actor=actor,
                        action_interpretation=simple_interpretation
                    )
                except Exception as e:
                    logger.log_error(f"Task update failed for given action: {e}")
                
                # Process monetary transaction if detected (show immediately in ROAM)
                if monetary_data.get("transaction_detected"):
                    try:
                        can_proceed, transaction_narrative, consequences = monetary_processor.process_enhanced_transaction(
                            monetary_data=monetary_data,
                            proactor=actor,
                            reactor=None,  # No reactor in ROAM given actions
                            success=True,
                            targeted_status=None
                        )
                        if transaction_narrative:
                            print(f"\n{Color.NARRATIVE}{transaction_narrative}{Color.RESET}")
                    except Exception as e:
                        print(f"{Color.ERROR}Transaction processing error: {e}{Color.RESET}")
                
                # Add minimal time cost for given actions
                # Only add trivial time if no survival time was already applied above
                if survival_time_cost == 0:
                    req = master_time.create_user_action_request(
                        RuleOf3Category.THREE_SECOND,
                        actor.sheet.name,
                        user_input
                    )
                    res = master_time.request_time_advancement(req)
                    if not SUPPRESS_DEBUG:
                        elapsed = simulation_time_tracker.get_simulation_time_display()
                        print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                
                # Sync pygame map after action
                try:
                    auto_sync_map(session_id=tracker.session_id if tracker else None)
                except Exception:
                    pass
                
                # Location change detection already handled at the beginning of given action block
                # No need to check again here
                
                # If this was NOT a location change, we already generated perceptual + internal voice
                # So we should skip the journey narrative section and continue to next turn
                if not location_changed:
                    # Execute post-user turns (lower initiative NPCs) before continuing
                    execute_post_user_turns_if_roam()
                    # Regular given action completed - skip journey processing
                    continue

                # JOURNEY CHUNKING: Check if action needs to be broken into multiple 3-minute segments
                # This only runs for location changes that might be journeys
                from journey_chunking_system import get_journey_chunking_system
                
                chunking_system = get_journey_chunking_system(key_memories_system=key_memories)
                should_chunk = chunking_system.should_chunk_action(
                    user_input=user_input,
                    action_description=user_input  # For given actions, use user_input directly
                )
                
                if should_chunk:
                    print(f"\n{Color.SYSTEM}🚶 JOURNEY DETECTED - Breaking into realistic segments...{Color.RESET}")
                    
                    # Estimate duration
                    estimated_duration = chunking_system._estimate_duration(
                        user_input=user_input,
                        action_description=user_input  # For given actions, use user_input directly
                    )
                    
                    print(f"{Color.SYSTEM}📏 Estimated journey time: {estimated_duration:.1f} minutes{Color.RESET}")
                    
                    # Extract destination (simple heuristic - can be improved)
                    destination = "destination"
                    if " to " in user_input.lower():
                        parts = user_input.lower().split(" to ", 1)
                        if len(parts) > 1:
                            destination = parts[1].strip().rstrip('.,!?')
                    
                    # Create chunks
                    chunks = chunking_system.create_journey_chunks(
                        user_input=user_input,
                        action_description=user_input,  # For given actions, use user_input directly
                        estimated_duration=estimated_duration,
                        current_location=context_manager.context.current_location,
                        destination=destination
                    )
                    
                    print(f"{Color.SYSTEM}📦 Journey broken into {len(chunks)} chunks{Color.RESET}")
                    
                    # Process each chunk
                    for chunk in chunks:
                        print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                        print(f"{Color.SYSTEM}📍 CHUNK {chunk.chunk_number}/{chunk.total_chunks}: {chunk.chunk_type.upper()}{Color.RESET}")
                        print(f"{Color.SYSTEM}⏱️  Duration: {chunk.duration_minutes:.1f} minutes{Color.RESET}")
                        print(f"{Color.SYSTEM}{'='*60}{Color.RESET}\n")
                        
                        # Generate chunk narrative prompt
                        chunk_prompt = chunking_system.generate_chunk_narrative_prompt(
                            chunk=chunk,
                            user_input=user_input,
                            action_description=user_input,  # For given actions, use user_input directly
                            actor_name=actor.sheet.name,
                            scene_description=scene_description,
                            destination=destination  # Pass destination so narrator knows where we're heading
                        )
                        
                        # Generate narrative for this chunk
                        chunk_narrative = narrator.generate_contextual_exploration_action_result_narrative(
                            user_input=user_input,
                            actor=actor,
                            scene_description=chunk_prompt,
                            success_total=3,
                            time_context=time_context
                        )
                        
                        # Display chunk narrative
                        print(f"{Color.NARRATIVE}📖 {chunk_narrative}{Color.RESET}\n")
                        
                        # Generate internal voice for this chunk (thoughts during travel)
                        try:
                            chunk_internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=chunk.location_context,
                                action_context=f"Traveling to {destination} - {chunk.chunk_type} ({chunk.progress_percentage}% complete)",
                                narrative_result=chunk_narrative,
                                mode="roam"
                            )
                            if chunk_internal_voice:
                                display_internal_voice_box(chunk_internal_voice)
                        except Exception:
                            pass  # Internal voice is optional
                        
                        # Advance time
                        time_coordinator.advance_time(
                            duration=chunk.duration_minutes * 60,
                            action_type="travel"
                        )
                        
                        # Update scene description for next chunk
                        if chunk.chunk_type == "arrival":
                            # Update location on final chunk
                            context_manager.context.current_location = destination
                            scene_description = f"You have arrived at {destination}."
                        else:
                            scene_description = chunk.location_context
                        
                        # Small pause between chunks for readability
                        import time
                        time.sleep(0.3)
                    
                    print(f"\n{Color.SUCCESS}✅ Journey complete! You have arrived at {destination}.{Color.RESET}")
                    
                    # Update final scene description
                    contextual_result = f"After a {estimated_duration:.0f}-minute journey, you arrive at {destination}."
                    last_action_narrative = contextual_result
                    scene_updates.append(contextual_result)
                    
                    # Update scene description
                    scene_description = f"{scene_description}\n\n{contextual_result}"
                    try:
                        conductor.scene_description = scene_description
                        tracker.set_current_scene(scene_description)
                    except Exception:
                        pass
                    
                    # Skip normal narrative generation - we already narrated the journey
                    # Continue to next iteration
                    continue
                
                # Initialize contextual_result to prevent UnboundLocalError
                # For location changes, this stays empty since location change has its own narrative
                contextual_result = ""
                
                # NORMAL NARRATIVE (Non-chunked, non-location-change actions)
                # Only run this if we didn't change location (location changes have their own narrative)
                if not location_changed:
                    # Generate contextual narrative for given action using NarratorAgent (treat as strong automatic success)
                    print(f"\n{Color.INFO}📖 ACTION RESULT{Color.RESET}")
                    # Get framing from Four-Mode Narrative Loop
                    turn_data = _build_turn_data(
                        user_input=user_input,
                        scene_description=scene_description,
                        current_mode=current_mode,
                        success_total=3,
                        continuity={'judgment': 'Possible'}
                    )
                    turn_data['narrative_response'] = last_action_narrative
                    framing = narrative_loop.process_turn(
                        turn_data=turn_data,
                        scene_description=scene_description,
                        time_context=time_context,
                        available_npcs=available_npcs
                    )
                    try:
                        new_mode = framing.get('mode') if framing else None
                        if new_mode and new_mode != last_loop_mode:
                            print(f"{Color.SYSTEM}🔀 Mode Shift → {new_mode.upper()} (Tone: {framing.get('tone', 'unknown')}){Color.RESET}")
                            last_loop_mode = new_mode
                    except Exception:
                        pass  # Ignore framing errors
                
                    # FIX BUG #7: Initialize contextual_result to prevent reusing old narratives
                    # NOTE: Location change detection already handled at the beginning of given action block
                    # If we reach here, it's NOT a location change, so generate normal exploration narrative
                    contextual_result = ""
                
                    # For given actions, success_total is always 3 (automatic success)
                    success_total = 3
                
                    # FIX BUG #9: Use current scene context for narrative generation
                    contextual_result = narrator.generate_contextual_exploration_action_result_narrative(
                        user_input=user_input,
                        actor=actor,
                        scene_description=get_current_scene(),
                        success_total=success_total
                    )
                
                    # Display result and parse for NPCs
                    print(f"\n{Color.NARRATIVE}{contextual_result}{Color.RESET}\n")
                
                    # Parse narrative for NPCs
                    from npc_parser_wrapper import parse_narrative_for_npcs
                    parse_narrative_for_npcs(
                        narrative_text=contextual_result,
                        available_npcs=available_npcs,
                        actor_generator=scene_creator,
                        scene_id=scene_id,
                        suppress_debug=SUPPRESS_DEBUG
                    )
                
                    # ============================================================
                    # AUTO-SPAWN MENTIONED NPCs
                    # ============================================================
                    # Parse scene description for named characters and spawn them
                    # This maintains narrative continuity - if the scene mentions
                    # "Linda the waitress", she should exist as an interactable NPC
                    # ============================================================
                
                    try:
                        from scene_npc_parser import auto_spawn_scene_npcs
                        spawned_count = auto_spawn_scene_npcs(
                            scene_description=contextual_result,
                            creator_agent=scene_creator,
                            available_npcs=available_npcs,
                            continuity_validator=continuity_validator,
                            auto_memory_creator=auto_memory_creator,
                            actor_name=actor.sheet.name,
                            scene_id=scene_id,
                            mention_system=mention_system
                        )
                    
                        if spawned_count > 0:
                            print(f"{Color.SUCCESS}[NPC PARSER] Auto-spawned {spawned_count} NPC(s) from scene{Color.RESET}")
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}[NPC PARSER] Auto-spawn failed: {e}{Color.RESET}")
                
                    # ============================================================
                    # PERCEPTION-BASED MEMORY RESURFACING
                    # ============================================================
                    # Check if the narration triggers any memories (seeing families, etc.)
                    # The function itself has criteria to avoid creating memories too frequently
                    # ============================================================
                
                    try:
                        resurfaced_memories = intent_memory_creator.process_narration_for_memories(
                            narration=contextual_result,
                            current_location=current_location or "Unknown Location",
                            turn_number=turn_number,
                            scene_id=scene_id
                        )
                    
                        # Display any resurfaced memories
                        # Also record in narrative context for future LLM calls
                        for memory_result in resurfaced_memories:
                            display_memory_creation(
                                memory_result,
                                narrative_context_manager=narrative_context_manager,
                                actor_name=actor.sheet.name
                            )
                        
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Memory resurfacing failed: {e}{Color.RESET}")
                
                    # Generate internal voice narration for ROAM mode only (when not in encounters)
                    if current_mode == SimulationMode.ROAM:
                        try:
                            # Use unified internal voice system
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=contextual_result,
                                function_hint="comment",  # General action commentary
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                        
                            # Display and save internal voice
                            display_internal_voice_box(internal_voice)
                            
                            if internal_voice:
                                try:
                                    from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                                    narrative_context_manager.add_narrative_event(
                                        event_type=NarrativeEventType.INTERNAL_VOICE,
                                        narrative_text=f"💭 {internal_voice}",
                                        actors_involved=[actor.sheet.name],
                                        importance=NarrativeImportance.NOTABLE,
                                        emotional_tone="reflective"
                                    )
                                except Exception:
                                    pass
                        except Exception as e:
                            # Log internal voice errors for debugging
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.WARNING}Internal voice generation failed: {e}{Color.RESET}")
                
                    last_action_narrative = contextual_result
                    scene_updates.append(contextual_result)
                
                    # UPDATE SCENE DESCRIPTION: Append exploration narrative to maintain context continuity
                    # This ensures NUA creation uses the current narrative state, not stale scene description
                    scene_description = f"{scene_description}\n\n{contextual_result}"
                    try:
                        conductor.scene_description = scene_description
                        tracker.set_current_scene(scene_description)
                    except Exception:
                        pass
                
                # DYNAMIC ACTOR DETECTION: Check narrative for new actor mentions
                try:
                    # Initialize dynamic actor detector if not already done
                    # Note: In ROAM mode, we don't have actor_manager, so we skip this
                    # Dynamic actor creation happens through progressive discovery instead
                    if current_mode == SimulationMode.ENCOUNTER and hasattr(encounter_checker.current_context, 'actor_manager'):
                        if not hasattr(main, '_dynamic_actor_detector'):
                            main._dynamic_actor_detector = EnhancedDynamicActorDetector(encounter_checker.current_context.actor_manager)
                        
                        # Check both user input AND narrative for actor mentions
                        detection = main._dynamic_actor_detector.detect_new_actor_mention(
                            f"{user_input} {contextual_result}"
                        )
                    else:
                        # In ROAM mode, skip dynamic actor detection (use progressive discovery instead)
                        detection = None
                    
                    if detection:
                        actor_type = detection.get('type')
                        actor_name = detection.get('name', 'Unknown')
                        
                        print(f"{Color.SYSTEM}[DYNAMIC ACTOR] Detected {actor_type}: {actor_name}{Color.RESET}")
                        
                        # Create the actor using CreatorAgent
                        if actor_type == 'NUA':
                            # Create NUA character
                            nua_data = scene_creator.generate_nua_character(
                                scene_description=scene_description,
                                ua_name=actor.sheet.name,
                                nua_hint=actor_name
                            )
                            
                            if nua_data:
                                new_nua = NonUserActor(nua_data)
                                actor_manager.add_actor(new_nua, ActorRole.SCENE_SECONDARY)
                                
                                # Add to spatial system
                                try:
                                    from spatial_context_system import get_spatial_manager, Position
                                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                    context = spatial.get_current_context()
                                    if context:
                                        # Place near UA
                                        ua_pos = spatial.get_actor_position("ua_001")
                                        if ua_pos:
                                            nua_x = ua_pos.x + 5  # 5 units away
                                            nua_y = ua_pos.y
                                        else:
                                            nua_x = context.location_dimensions.width / 2
                                            nua_y = context.location_dimensions.height / 2
                                        
                                        spatial.add_actor(
                                            actor_id=f"nua_{new_nua.sheet.name.lower().replace(' ', '_')}",
                                            actor_name=new_nua.sheet.name,
                                            position=Position(nua_x, nua_y),
                                            is_user_actor=False
                                        )
                                        print(f"{Color.SYSTEM}[SPATIAL] Added {new_nua.sheet.name} to map{Color.RESET}")
                                except Exception as e:
                                    print(f"{Color.WARNING}[SPATIAL] Could not add NUA to map: {e}{Color.RESET}")
                                
                                print(f"{Color.SUCCESS}✓ Created NUA: {new_nua.sheet.name}{Color.RESET}")
                        
                        elif actor_type == 'INUA':
                            # Create INUA object
                            inua_data = scene_creator.generate_inua_obstacle(
                                scene_description=scene_description,
                                inua_hint=actor_name
                            )
                            
                            if inua_data:
                                new_inua = InanimateNonUserActor(inua_data)
                                actor_manager.add_actor(new_inua, ActorRole.SCENE_SECONDARY)
                                # Track INUA for world events (hazards, environmental interactions)
                                if new_inua not in available_inuas:
                                    available_inuas.append(new_inua)
                                print(f"{Color.SUCCESS}✓ Created INUA: {new_inua.sheet.name}{Color.RESET}")
                
                except Exception as e:
                    print(f"{Color.WARNING}[DYNAMIC ACTOR] Detection failed: {e}{Color.RESET}")
                
                # PROGRESSIVE DISCOVERY: Check if following clues leads to NUA introduction
                try:
                    if not hasattr(main, '_progressive_discovery'):
                        from progressive_discovery_system import get_progressive_discovery
                        main._progressive_discovery = get_progressive_discovery()
                    
                    introduction_context = main._progressive_discovery.process_turn(
                        user_input, contextual_result
                    )
                    
                    if introduction_context:
                        print(f"{Color.SYSTEM}[DISCOVERY] Clue trail leads to actor introduction!{Color.RESET}")
                        print(f"{Color.SYSTEM}[DISCOVERY] Type: {introduction_context['clue_type']} → {introduction_context['suggested_nua_type']}{Color.RESET}")
                        
                        # Create NUA based on discovery context
                        nua_characteristics = introduction_context.get('nua_characteristics', {})
                        suggested_occupation = nua_characteristics.get('occupation', 'Mysterious Figure')
                        
                        # Build context for NUA creation
                        nua_context = f"""
The user has been following {introduction_context['clue_type']} for {introduction_context['follow_count']} actions.
{introduction_context['narrative_hint']}

Suggested characteristics:
- Occupation: {suggested_occupation}
- Initial state: {nua_characteristics.get('initial_state', 'unaware')}
- Context: {', '.join(nua_characteristics.get('context_hints', []))}

Create a NUA that fits this discovery context."""
                        
                        # Create the NUA
                        from dynamic_actor_system import DynamicActorSystem
                        dynamic_system = DynamicActorSystem(scene_creator)
                        new_nua = dynamic_system.creator.create_dynamic_actor(
                            {'name': suggested_occupation, 'context': nua_context, 'type': 'NUA'},
                            scene_description
                        )
                        
                        if new_nua:
                            # Register NUA for persistence and add to available NPCs
                            register_nua(new_nua, available_npcs)
                            
                            # Display NUA introduction with first impression (outlier)
                            try:
                                from nua_introduction_system import display_llm_nua_introduction, USE_LLM_FOR_INTRODUCTIONS
                                if USE_LLM_FOR_INTRODUCTIONS:
                                    display_llm_nua_introduction(new_nua, "through investigation", narrator)
                                else:
                                    from nua_introduction_system import display_nua_introduction
                                    display_nua_introduction(new_nua, "through investigation")
                            except Exception as e:
                                # Fallback to simple message
                                print(f"{Color.SUCCESS}✓ Discovered through investigation: {new_nua.sheet.name}{Color.RESET}")
                            
                            # Add to spatial map
                            try:
                                from spatial_context_system import get_spatial_manager, Position
                                spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                context = spatial.get_current_context()
                                if context:
                                    # Place NUA near UA (they just discovered them)
                                    ua_pos = spatial.get_actor_position("ua_001")
                                    if ua_pos:
                                        # Place 5-10 units away
                                        import random
                                        offset_x = random.uniform(-10, 10)
                                        offset_y = random.uniform(-10, 10)
                                        nua_pos = Position(ua_pos.x + offset_x, ua_pos.y + offset_y)
                                    else:
                                        # Default position
                                        dims = context.dimensions
                                        nua_pos = Position(dims.width * 0.6, dims.height * 0.6)
                                    
                                    spatial.add_actor(
                                        actor_id=f"nua_{new_nua.sheet.name.lower().replace(' ', '_')}",
                                        actor_name=new_nua.sheet.name,
                                        position=nua_pos,
                                        is_user_actor=False
                                    )
                                    print(f"{Color.SYSTEM}[SPATIAL] Added discovered NUA to map{Color.RESET}")
                            except Exception as e:
                                print(f"{Color.WARNING}[SPATIAL] Could not add NUA to map: {e}{Color.RESET}")
                
                except Exception as e:
                    import traceback
                    print(f"{Color.WARNING}[DISCOVERY] Progressive discovery failed: {e}{Color.RESET}")
                    print(f"{Color.WARNING}[DISCOVERY] Traceback: {traceback.format_exc()}{Color.RESET}")
                
                # MOVEMENT TRACKING: Check if UA moved within location
                # ARCHITECT handles all movement resolution - consolidated logic
                try:
                    from spatial_movement_detector import get_movement_detector
                    from agents.architect_agent import resolve_movement_target
                    from spatial_context_system import get_spatial_manager, Position
                    
                    movement_detector = get_movement_detector()
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    
                    # CRITICAL: Check ONLY user input for movement, NOT narrative
                    movement_data = movement_detector.detect_movement(
                        user_input,  # ONLY user input - never use narrative for movement detection
                        scene_description
                    )
                    
                    if movement_data and movement_data.get("is_movement"):
                        target = movement_data.get("target")
                        movement_type = movement_data.get("movement_type", "walk")
                        
                        # Check if this is a location change
                        is_location_change = _detect_location_move(user_input, contextual_result, spatial_manager=spatial)
                        
                        if is_location_change:
                            print(f"{Color.SYSTEM}[MOVEMENT] Target is a location change - will be handled by location system{Color.RESET}")
                        else:
                            # ARCHITECT: Resolve movement within current location
                            current_pos = spatial.get_actor_position("ua_001")
                            context = spatial.get_current_context()
                            
                            if context and current_pos:
                                # Use Architect's consolidated movement resolver
                                resolved = resolve_movement_target(
                                    target=target,
                                    current_position=(current_pos.x, current_pos.y),
                                    spatial_context=context,
                                    user_input=user_input
                                )
                                
                                if resolved:
                                    new_position = Position(resolved[0], resolved[1])
                                    
                                    # Calculate movement time with Swiftness
                                    from spatial_context_system import MovementSpeed
                                    speed_map = {
                                        'crawl': MovementSpeed.CRAWL,
                                        'sneak': MovementSpeed.SNEAK,
                                        'walk': MovementSpeed.WALK,
                                        'jog': MovementSpeed.JOG,
                                        'run': MovementSpeed.RUN,
                                        'sprint': MovementSpeed.SPRINT
                                    }
                                    speed = speed_map.get(movement_type.lower(), MovementSpeed.WALK)
                                    
                                    # Get actor's Swiftness for movement time calculation
                                    from actor_sheet import SFactorType
                                    swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                                    
                                    # Calculate movement time
                                    movement_time_seconds, unit_time = current_pos.calculate_movement_time_with_ut(
                                        new_position, speed, swiftness
                                    )
                                    distance = current_pos.distance_to(new_position)
                                    
                                    # Update position
                                    spatial.move_actor("ua_001", new_position)
                                    
                                    # Sync pygame map
                                    try:
                                        from pygame_spatial_map import auto_sync_map
                                        auto_sync_map(session_id=tracker.session_id if tracker else None)
                                    except Exception:
                                        pass
                                    
                                    # Display movement info
                                    print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {movement_type.capitalize()} to '{target}': ({current_pos.x:.1f}, {current_pos.y:.1f}) → ({new_position.x:.1f}, {new_position.y:.1f})")
                                    print(f"{Color.SYSTEM}[MOVEMENT] Distance: {distance:.1f} units | Time: {movement_time_seconds:.1f}s ({unit_time} UT) | Speed: {speed.name}{Color.RESET}")
                                    
                                    # Advance time using proper time advancement system
                                    try:
                                        # Determine appropriate Rule of 3 category based on time
                                        if movement_time_seconds <= 10:
                                            time_category = RuleOf3Category.THREE_SECOND
                                        else:
                                            time_category = RuleOf3Category.THREE_MINUTE
                                        
                                        time_request = master_time.create_user_action_request(
                                            time_category,
                                            actor.sheet.name,
                                            f"Movement: {movement_type}"
                                        )
                                        time_result = master_time.request_time_advancement(time_request)
                                        print(f"{Color.SYSTEM}[TIME] Advanced {time_result.duration_advanced_seconds}s{Color.RESET}")
                                    except Exception as e:
                                        print(f"{Color.WARNING}[TIME] Could not advance time: {e}{Color.RESET}")
                            elif context and not current_pos:
                                # Actor not on map yet - add them at entrance
                                dims = context.location_dimensions
                                entrance_pos = Position(dims.width * 0.35, dims.height * 0.15)
                                spatial.add_actor(
                                    actor_id="ua_001",
                                    actor_name=actor.sheet.name,
                                    position=entrance_pos,
                                    is_user_actor=True
                                )
                                print(f"{Color.SYSTEM}[MOVEMENT] Added UA to map at entrance{Color.RESET}")
                
                except Exception as e:
                    import traceback
                    print(f"{Color.WARNING}[MOVEMENT] Tracking failed: {e}{Color.RESET}")
                
                # Location change already handled earlier in the given action block
                # Only append narrative if we DIDN'T change location
                # If we changed location, scene_description is already the new location's full description
                if not location_changed:
                    scene_description = f"{scene_description}\n\n{contextual_result}"
                try:
                    conductor.scene_description = scene_description
                except Exception as e:
                    logger.log_error(f"Failed to update conductor scene_description: {e}")
                
                # SAVE TO PERSISTENT CONTEXT
                context_manager.update_scene_description(scene_description)
                context_manager.add_narrative(contextual_result)
                context_manager.add_event(f"User: {user_input}")
                
                # Check for item acquisition and update inventory
                try:
                    # Given actions are automatic successes (success_total = 3 per ROAM-mode preferences)
                    action_result = {
                        'narrative': contextual_result,
                        'success_calculation': {'total_successes': success_total if 'success_total' in locals() else 3}
                    }
                    skip_inventory_manager = False
                    try:
                        if monetary_data and monetary_data.get('transaction_detected'):
                            creates_item = bool(monetary_data.get('creates_item'))
                            removes_item = bool(monetary_data.get('removes_item'))
                            skip_inventory_manager = creates_item or removes_item
                    except Exception:
                        skip_inventory_manager = False

                    if not skip_inventory_manager:
                        print(f"{Color.SYSTEM}[INVENTORY] Checking for item acquisition in: '{user_input}'{Color.RESET}")
                        inventory_message = inventory_manager.process_action_for_inventory(
                            user_input, action_result, actor.sheet
                        )
                        if inventory_message:
                            print(f"{Color.SUCCESS}{inventory_message}{Color.RESET}")
                        else:
                            print(f"{Color.SYSTEM}[INVENTORY] No item acquisition detected{Color.RESET}")
                except Exception as e:
                    import traceback
                    logger.log_error(f"Inventory management error: {e}")
                    print(f"{Color.WARNING}[INVENTORY] Error: {e}{Color.RESET}")
                    print(f"{Color.WARNING}[INVENTORY] Traceback: {traceback.format_exc()}{Color.RESET}")
                
                # Prune NPCs that departed according to narrative
                try:
                    removed = _prune_npcs_by_outcome_text(available_npcs, [contextual_result])
                    if removed:
                        print(f"{Color.WARNING}👋 Non-User Actors left the scene: {', '.join(removed)}{Color.RESET}")
                        # SAVE TO PERSISTENT CONTEXT (NUAs removed)
                        for nua_name in removed:
                            context_manager.remove_nua(nua_name)
                except Exception:
                    pass
                # Auto-save after action
                try:
                    auto_save_counter += 1
                    if auto_save_counter >= auto_save_interval:
                        try:
                            if tracker is not None:
                                tracker.save_available_npcs(list(available_npcs or []))
                        except Exception:
                            pass
                        snapshot = {
                            'scene_number': scene_number,
                            'scene_description': scene_description,
                            'last_action': contextual_result,
                            'scene_updates': scene_updates[-3:],
                            'time_context': time_context,
                            'available_npc_names': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                            'actor_state': {
                                'name': actor.sheet.name,
                                'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()},
                                'current_task': actor.get_current_task_description() if hasattr(actor, 'get_current_task_description') else 'None',
                                'goals': actor.get_goals_summary() if hasattr(actor, 'get_goals_summary') else 'No goals'
                            }
                        }
                        req = save_coordinator.create_regular_auto_save_request(snapshot)
                        save_coordinator.request_save(req)
                        auto_save_counter = 0
                except Exception:
                    pass
                # Save contextual narrative for continuity
                try:
                    from llm_agents.narrative_context_system import NarrativeEventType as LLMNarrativeEventType, NarrativeImportance as LLMNarrativeImportance
                    narrative_context_manager.add_narrative_event(
                        event_type=LLMNarrativeEventType.EXPLORATION,
                        narrative_text=f"Scene {scene_number}: {actor.sheet.name} → {contextual_result}",
                        actors_involved=[actor.sheet.name],
                        importance=LLMNarrativeImportance.ROUTINE,
                        emotional_tone="routine",
                        scene_context=scene_description
                    )
                except Exception:
                    pass
                # Avoid a second prompt in the same loop iteration
                continue
                
            # Check if this is ANY fallible action (inquiry, physical, social, etc.)
            # ALL fallible actions now use the unified 3-phase system:
            # 1. Perceptual description (what you physically do/try)
            # 2. Success/failure roll
            # 3. Internal voice (mental reaction)
            
            # Route ALL fallible actions through unified system
            is_fallible_action = input_analysis.get('input_type') == 'fallible_action' if input_analysis else False
            # Only mental/inquiry actions trigger memory recall, never physical actions
            is_inquiry = input_analysis.get('fallible_subtype') in ['mental', 'inquiry'] if input_analysis else False
            
            if is_fallible_action:
                # Handle ALL fallible actions with unified 3-phase system
                fallible_subtype = input_analysis.get('fallible_subtype', 'physical') if input_analysis else 'physical'
                
                # === PROCESS MOVEMENT FOR ALL FALLIBLE ACTIONS ===
                # Movement happens BEFORE the action itself (you walk to the cabinet, THEN check it)
                if input_analysis and input_analysis.get('explicit_movement') and input_analysis.get('movement_target'):
                    try:
                        from agents.architect_agent import resolve_movement_target
                        from spatial_context_system import Position, MovementSpeed
                        
                        target = input_analysis.get('movement_target')
                        context = spatial.get_current_context()
                        current_pos = spatial.get_actor_position("ua_001")
                        
                        if context and current_pos:
                            # ARCHITECT: Resolve target to validated coordinates
                            resolved = resolve_movement_target(
                                target=target,
                                current_position=(current_pos.x, current_pos.y),
                                spatial_context=context,
                                user_input=user_input
                            )
                            
                            if resolved:
                                new_position = Position(resolved[0], resolved[1])
                                
                                # Get movement type from input
                                movement_verbs = ['walk', 'run', 'sprint', 'jog', 'sneak', 'crawl', 'head', 'go', 'move', 'approach']
                                movement_type = 'walk'
                                input_lower = user_input.lower()
                                for verb in movement_verbs:
                                    if verb in input_lower:
                                        if verb in ['head', 'go', 'move', 'approach']:
                                            movement_type = 'walk'
                                        else:
                                            movement_type = verb
                                        break
                                
                                # Map movement type to speed
                                speed_map = {
                                    'crawl': MovementSpeed.CRAWL,
                                    'sneak': MovementSpeed.SNEAK,
                                    'walk': MovementSpeed.WALK,
                                    'jog': MovementSpeed.JOG,
                                    'run': MovementSpeed.RUN,
                                    'sprint': MovementSpeed.SPRINT
                                }
                                speed = speed_map.get(movement_type.lower(), MovementSpeed.WALK)
                                
                                # Get actor's Swiftness for movement time calculation
                                from actor_sheet import SFactorType
                                swiftness = actor.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
                                
                                # Calculate movement time
                                movement_time_seconds, unit_time = current_pos.calculate_movement_time_with_ut(
                                    new_position, speed, swiftness
                                )
                                distance = current_pos.distance_to(new_position)
                                
                                # Update position
                                spatial.move_actor("ua_001", new_position)
                                
                                # Display movement info
                                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {movement_type.capitalize()} to '{target}': ({current_pos.x:.1f}, {current_pos.y:.1f}) → ({new_position.x:.1f}, {new_position.y:.1f})")
                                print(f"{Color.SYSTEM}[MOVEMENT] Distance: {distance:.1f} units | Time: {movement_time_seconds:.1f}s ({unit_time} UT){Color.RESET}")
                                
                                # Sync pygame map to show movement and trail
                                try:
                                    from pygame_spatial_map import auto_sync_map
                                    auto_sync_map(session_id=tracker.session_id if tracker else None)
                                except Exception as sync_err:
                                    print(f"{Color.WARNING}[MOVEMENT] Map sync failed: {sync_err}{Color.RESET}")
                    except Exception as e:
                        print(f"{Color.WARNING}[MOVEMENT] Movement processing failed: {e}{Color.RESET}")
                
                if is_inquiry:
                    # INQUIRY path (mental/information gathering)
                    # NOTE: Movement already processed above for ALL fallible actions
                    print(f"\n{Color.INFO}📋 INQUIRY (Information Gathering){Color.RESET}")
                    
                    # Get availability result to determine how to process
                    inquiry_availability = availability_result.get("availability") if 'availability_result' in locals() else IntentAvailability.EXIST
                    
                    # Import inquiry helpers
                    from inquiry_helpers import (
                        check_inquiry_memory,
                        determine_inquiry_difficulty,
                        roll_inquiry_success,
                        check_duplicate_inquiry_memory,
                        process_failed_inquiry,
                        extract_inquiry_subject,
                        extract_inquiry_keywords
                    )
                    
                    # PHASE 1: Check existing memories first (only for inquiries)
                    memory_check = check_inquiry_memory(
                        user_question=user_input,
                        key_memories_system=key_memories,
                        ua_actor=actor
                    )
                    
                    if memory_check and memory_check['found']:
                        # Memory exists - recall it (free, no roll needed)
                        print(f"{Color.SUCCESS}[Memory Recall - No roll needed]{Color.RESET}\n")
                        
                        memory = memory_check['memory']
                        
                        # Get context for generating narrative
                        recent_context = narrative_context_manager.get_context_for_llm(
                            lookback_events=5,
                            importance_threshold="notable"
                        )
                        recent_context = _merge_contexts(recent_context, everlasting_context_text)
                        time_context = master_time.get_current_time_context()
                        
                        # PHASE 1: Generate perceptual description (NarratorAgent)
                        perceptual_description = narrator.generate_inquiry_perceptual_description(
                            ua_actor=actor,
                            question=user_input,
                            scene_description=scene_description,
                            narrative_context=recent_context,
                            time_context=time_context
                        )
                        
                        # Display perceptual description
                        display_perceptual_description_box(perceptual_description)
                        
                        # Update scene description with new perceptual information
                        scene_description = f"{scene_description}\n\n{perceptual_description}"
                        _capture_continuity_facts_from_text(perceptual_description, source="perceptual", base_confidence=0.65)
                        try:
                            _capture_mentioned_actors_from_text(perceptual_description, source="perceptual")
                        except Exception:
                            pass
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
                                scene_id=scene_id,
                                mention_system=mention_system
                            )
                        except Exception as e:
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")
                        
                        # PHASE 2: Generate internal voice (unified system)
                        internal_voice = generate_unified_internal_voice(
                            actor=actor,
                            narrator=narrator,
                            scene_description=scene_description,
                            user_action=user_input,
                            action_outcome=memory.description,
                            function_hint="memory",
                            memory_trigger=user_input,
                            urgency="normal",
                            failure_tracker=failure_tracker,
                            narrative_context_manager=narrative_context_manager
                        )
                        
                        display_internal_voice_box(internal_voice)
                        
                        # Add to narrative context
                        narrative_context_manager.add_narrative_event(
                            event_type=NarrativeEventType.MEMORY_RESURFACING,
                            narrative_text=f"Scene {scene_number}: {actor.sheet.name} recalled: {user_input}",
                            actors_involved=[actor.sheet.name],
                            importance=NarrativeImportance.ROUTINE,
                            emotional_tone="thoughtful",
                            scene_context=scene_description
                        )
                        
                        # Advance time (mental action)
                        req = master_time.create_user_action_request(
                            RuleOf3Category.THREE_SECOND,
                            actor.sheet.name,
                            user_input
                        )
                        res = master_time.request_time_advancement(req)
                        
                        if not SUPPRESS_DEBUG:
                            elapsed = simulation_time_tracker.get_simulation_time_display()
                            print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                        
                        # Sync pygame map after action
                        try:
                            auto_sync_map(session_id=tracker.session_id if tracker else None)
                        except Exception:
                            pass
                        
                        # Execute post-user turns (lower initiative NPCs) before continuing
                        execute_post_user_turns_if_roam()
                        # Memory recalled - done, continue to next turn
                        continue
                    
                    else:
                        # PHASE 2: No memory - treat as fallible action
                        print(f"{Color.WARNING}[No memory found - Processing as fallible action]{Color.RESET}\n")
                        
                        # Use standard fallible action interpretation
                        interpretation_data = conductor.interpret_fallible_action(
                            user_input=user_input,
                            proactor=actor
                        )
                        
                        # Calculate success using standard UTAS formula (same as all fallible actions)
                        from unified_formula import calculate_unified_result
                        from actor_sheet import SFactorType
                        
                        utas = interpretation_data['utas_factors']
                        s_trait_name = utas['s_trait_to_use']
                        s_trait_enum = SFactorType[s_trait_name.upper()]
                        skill_data = utas.get('skill', {})
                        skill_name = skill_data.get('name') if isinstance(skill_data, dict) else None
                        
                        result = calculate_unified_result(
                            actor=actor,
                            s_trait=s_trait_enum,
                            skill_name=skill_name if skill_name and skill_name != 'none' else None,
                            target_actor=None,
                            shift_polarity='Subtractive',
                            targeted_status=None,
                            supplement_val=0,
                            serendipity_override=None,
                            stress_level_override=utas.get('stress_level', 3)
                        )
                        
                        success_total = result['final_result']
                        success = success_total >= 0
                    
                        # Display calculations with success level narration (EXACT SAME FORMAT as exploration actions)
                        print(f"\n{Color.INFO}📊 DETAILED CALCULATIONS{Color.RESET}")
                        print(f"{Color.SYSTEM}S-Trait: {normalize_sfactor_label(s_trait_name)} ({result['positive_components']['s_trait']}){Color.RESET}")
                        print(f"{Color.SYSTEM}Skill: {skill_name if skill_name and skill_name != 'none' else 'N/A'} ({result['positive_components']['skill']}){Color.RESET}")
                        print(f"{Color.SYSTEM}Serendipity: {result['positive_components']['serendipity']}{Color.RESET}")
                        print(f"{Color.SYSTEM}Stress Level: {utas.get('stress_level', 3)}{Color.RESET}")
                        print(f"{Color.SYSTEM}Total Success: {success_total}{Color.RESET}")
                    
                        # Add success level narration
                        success_narration = get_success_level_narration(success_total)
                        print(f"{Color.SUCCESS}🎯 Success Level: {success_narration}{Color.RESET}")
                    
                        if success:
                            # PHASE 3a: SUCCESS - Generate answer and create memory
                            print(f"\n{Color.SUCCESS}[SUCCESS - Learning information]{Color.RESET}\n")
                        
                            # Get context
                            recent_context = narrative_context_manager.get_context_for_llm(
                                lookback_events=5,
                                importance_threshold="notable"
                            )
                            recent_context = _merge_contexts(recent_context, everlasting_context_text)
                            
                            # Generate answer based on availability
                            time_context = master_time.get_current_time_context()
                            
                            # CRITICAL: Add obstacle context so narrator knows what objects exist
                            scene_with_obstacles = scene_description
                            try:
                                obstacle_context = get_obstacle_names_for_narrative()
                                if obstacle_context:
                                    scene_with_obstacles = f"{scene_description}\n\n[OBJECTS IN LOCATION: {obstacle_context}]"
                            except Exception:
                                pass
                            
                            # Pass availability context to narrator
                            availability_context = {
                                'availability': inquiry_availability,
                                'reasoning': availability_result.get('reasoning', '') if 'availability_result' in locals() else ''
                            }
                            
                            # Generate factual answer (memory content with specific details)
                            factual_answer = narrator.generate_inquiry_factual_answer(
                                user_question=user_input,
                                ua_actor=actor,
                                scene_description=scene_with_obstacles,
                                narrative_context=recent_context,
                                current_time=time_context,
                                availability_context=availability_context
                            )
                            
                            # PHASE 1: Generate perceptual description (NarratorAgent)
                            perceptual_description = narrator.generate_inquiry_perceptual_description(
                                ua_actor=actor,
                                question=user_input,
                                scene_description=scene_with_obstacles,
                                narrative_context=recent_context,
                                time_context=time_context
                            )
                            
                            # Display perceptual description
                            display_perceptual_description_box(perceptual_description)
                            
                            # Update scene description with new perceptual information
                            scene_description = f"{scene_description}\n\n{perceptual_description}"
                            _capture_continuity_facts_from_text(perceptual_description, source="perceptual", base_confidence=0.65)
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
                                    scene_id=scene_id,
                                    mention_system=mention_system
                                )
                            except Exception as e:
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")
                            
                            # NOTE: Do NOT run NPC parser on factual_answer - it's memory content, not current scene!
                            # NPCs mentioned in memories are not physically present unless they appear in scene_description
                            
                            # PHASE 2: Generate internal voice (unified system)
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=factual_answer or "Uncertain about this...",
                                function_hint="information",
                                question_content=user_input,
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            
                            display_internal_voice_box(internal_voice)
                            
                            # Check for duplicate before creating memory (only if we have a factual answer)
                            if factual_answer:
                                existing = check_duplicate_inquiry_memory(
                                    question=user_input,
                                    answer=factual_answer,
                                    key_memories_system=key_memories
                                )
                            else:
                                existing = None
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.WARNING}[INQUIRY] No factual answer generated - skipping memory creation{Color.RESET}")
                            
                            if factual_answer and not existing:
                                # Create memory of learned information
                                try:
                                    # Extract keywords from BOTH question and answer (to capture names, places, etc.)
                                    memory_tags = extract_inquiry_keywords(user_input, answer=factual_answer)
                                    
                                    # Add actor name tag so memory shows up in actor sheet
                                    actor_tag = actor.sheet.name.lower().replace(" ", "_")
                                    if actor_tag not in memory_tags:
                                        memory_tags.append(actor_tag)
                                    
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.SYSTEM}[DEBUG] Memory tags extracted: {memory_tags}{Color.RESET}")
                                    
                                    key_memories.create_memory(
                                        title=f"Learned: {extract_inquiry_subject(user_input)}",
                                        description=factual_answer,
                                        full_narrative=f"Question: {user_input}\n\nAnswer: {factual_answer}",
                                        category=MemoryCategory.DISCOVERY,
                                        importance=MemoryImportance.ROUTINE,
                                        location=actor.sheet.location,
                                        tags=memory_tags
                                    )
                                    print(f"{Color.INFO}💾 Information learned and saved to memory{Color.RESET}")

                                    # Best-effort: persist inquiry knowledge into everlasting ContextStore
                                    try:
                                        from context_store import ContextStore, WorldTime
                                        from master_time_coordinator import get_master_time_coordinator
                                        from spatial_context_system import get_spatial_manager
                                        from pathlib import Path as _Path

                                        # Local duplicate guard (best-effort)
                                        try:
                                            _inquiry_key = f"{user_input.strip()}||{factual_answer.strip()}"
                                            if '_last_inquiry_info_learned_key' in locals() and _last_inquiry_info_learned_key == _inquiry_key:
                                                raise Exception('Duplicate inquiry INFO_LEARNED suppressed')
                                            _last_inquiry_info_learned_key = _inquiry_key
                                        except Exception:
                                            pass

                                        spatial = None
                                        session_id = 'default'
                                        location_id = None
                                        try:
                                            _sid = tracker.session_id if tracker else 'default'
                                            spatial = get_spatial_manager(session_id=_sid)
                                            session_id = getattr(spatial, 'session_id', None) or session_id
                                            location_id = getattr(spatial, 'current_location', None)
                                        except Exception:
                                            spatial = None

                                        actor_id = actor.sheet.name
                                        try:
                                            ctx = spatial.get_current_context() if spatial else None
                                            if ctx and getattr(ctx, 'actor_positions', None):
                                                for aid, apos in ctx.actor_positions.items():
                                                    if getattr(apos, 'actor_name', None) == actor.sheet.name:
                                                        actor_id = str(aid)
                                                        break
                                        except Exception:
                                            actor_id = actor.sheet.name

                                        wt = None
                                        try:
                                            tc = get_master_time_coordinator()
                                            time_ctx = tc.get_current_time_context() if tc else None
                                            gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
                                            if gt is not None:
                                                wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                                        except Exception:
                                            wt = None

                                        store = ContextStore(_Path('simulation_data/context/context.db'))
                                        summary = f"INFO LEARNED: {actor.sheet.name} learned answer to inquiry: {extract_inquiry_subject(user_input)}"
                                        event_id = store.log_world_event(
                                            session_id=session_id,
                                            location_id=location_id,
                                            event_type='INFO_LEARNED',
                                            summary=summary,
                                            importance=6,
                                            tags=['info', 'inquiry', 'learned'],
                                            payload={
                                                'actor_id': actor_id,
                                                'actor_ids': [actor_id],
                                                'actor_name': actor.sheet.name,
                                                'actor_names': [actor.sheet.name],
                                                'question': user_input,
                                                'answer': factual_answer,
                                                'tags': memory_tags,
                                            },
                                            world_time=wt
                                        )

                                        try:
                                            if hasattr(store, 'remember'):
                                                store.remember(
                                                    session_id=session_id,
                                                    actor_id=str(actor_id),
                                                    memory_type='info_learned',
                                                    content=f"Learned: {user_input} -> {factual_answer}",
                                                    importance=6,
                                                    pinned=False,
                                                    decay_rate=0.00018,
                                                    source_event_id=int(event_id) if event_id is not None else None,
                                                    world_time=wt
                                                )
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                except Exception as e:
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.WARNING}Memory creation failed: {e}{Color.RESET}")
                            
                            # Add to narrative context (only if we have factual answer)
                            if factual_answer:
                                narrative_context_manager.add_narrative_event(
                                    event_type=NarrativeEventType.MEMORY_CREATION,
                                    narrative_text=f"Scene {scene_number}: {actor.sheet.name} learned: {user_input}",
                                    actors_involved=[actor.sheet.name],
                                    importance=NarrativeImportance.NOTABLE,
                                    emotional_tone="insightful",
                                    scene_context=scene_description
                                )
                            
                            # Time advancement for successful inquiry
                            inquiry_time_scale = RuleOf3Category.THREE_SECOND
                            time_description = "a quick thought"
                            
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.INFO}[INQUIRY TIME] {inquiry_time_scale.name} - {time_description}{Color.RESET}")
                            
                            req = master_time.create_user_action_request(
                                inquiry_time_scale,
                                actor.sheet.name,
                                user_input
                            )
                            res = master_time.request_time_advancement(req)
                            
                            if not SUPPRESS_DEBUG:
                                elapsed = simulation_time_tracker.get_simulation_time_display()
                                print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                            
                            continue
                        
                        else:
                            # PHASE 3b: FAILURE - Uncertain response (no memory created)
                            print(f"{Color.ERROR}Result: FAILURE ✗{Color.RESET}")
                            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
                            print(f"{Color.WARNING}[FAILURE - Information unknown]{Color.RESET}\n")
                            
                            # Generate uncertain response
                            uncertainty = process_failed_inquiry(
                                user_question=user_input,
                                ua_actor=actor,
                                scene_context=scene_description,
                                narrator=narrator
                            )
                            
                            # Display uncertainty (narrator - perceptions only)
                            print(f"{Color.NARRATIVE}{uncertainty}{Color.RESET}\n")
                            
                            # Check for NPCs mentioned in the failed inquiry response
                            try:
                                from scene_npc_parser import auto_spawn_scene_npcs
                                spawned_count = auto_spawn_scene_npcs(
                                    scene_description=uncertainty,  # Parse the uncertainty response for NPCs
                                    creator_agent=scene_creator,
                                    available_npcs=available_npcs,
                                    continuity_validator=continuity_validator,
                                    auto_memory_creator=auto_memory_creator,
                                    actor_name=actor.sheet.name,
                                    scene_id=scene_id,
                                    mention_system=mention_system
                                )
                                if spawned_count > 0:
                                    print(f"{Color.SUCCESS}[NPC PARSER] Auto-spawned {spawned_count} NPC(s) from inquiry response{Color.RESET}")
                            except Exception as e:
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.WARNING}[NPC PARSER] Inquiry response auto-spawn failed: {e}{Color.RESET}")
                            
                            # Generate and display internal voice (suggestions)
                            time_context = master_time.get_current_time_context()
                            recent_context = narrative_context_manager.get_context_for_llm(
                                lookback_events=5,
                                importance_threshold="notable"
                            )
                            recent_context = _merge_contexts(recent_context, everlasting_context_text)
                            
                            # For failed inquiries, generate internal voice about not knowing
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome="Failed to recall or discover this information.",
                                function_hint="information",
                                question_content=user_input,
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            
                            display_internal_voice_box(internal_voice)
                            
                            print(f"{Color.SYSTEM}[No memory created]{Color.RESET}")
                            
                            # Add to narrative context
                            narrative_context_manager.add_narrative_event(
                                event_type=NarrativeEventType.EXPLORATION,
                                narrative_text=f"Scene {scene_number}: {actor.sheet.name} tried to recall: {user_input} (failed)",
                                actors_involved=[actor.sheet.name],
                                importance=NarrativeImportance.ROUTINE,
                                emotional_tone="uncertain",
                                scene_context=scene_description
                            )
                            
                            # ============================================================
                            # TIME ADVANCEMENT - Inquiries use 3TU system like all fallible actions
                            # ============================================================
                            # All inquiries are 3-SECOND (quick mental recall)
                            inquiry_time_scale = RuleOf3Category.THREE_SECOND
                            time_description = "a quick thought"
                            
                            # Advance time using master_time system
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.INFO}[INQUIRY TIME] {inquiry_time_scale.name} - {time_description}{Color.RESET}")
                            
                            req = master_time.create_user_action_request(
                                inquiry_time_scale,
                                actor.sheet.name,
                                user_input
                            )
                            res = master_time.request_time_advancement(req)
                            
                            # Display time advancement
                            if not SUPPRESS_DEBUG:
                                elapsed = simulation_time_tracker.get_simulation_time_display()
                                print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                            
                            # Execute post-user turns (lower initiative NPCs) before continuing
                            execute_post_user_turns_if_roam()
                            # Continue to next turn
                            continue
                
                # ============================================================
                # REALITY-BASED MOVEMENT SYSTEM WITH CHUNKING (NEW)
                # ============================================================
                # OLD CODE (INSTANT TELEPORTATION - PRESERVED FOR ROLLBACK):
                # try:
                #     from spatial_context_system import get_spatial_manager
                #     spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                #     move_label = _detect_location_move(user_input, "", spatial_manager=spatial)
                #     if move_label:
                #         print(f"{Color.SYSTEM}[LOCATION] Detected move to: {move_label}{Color.RESET}")
                #         prev_desc = scene_description
                #         scene_description = _apply_location_move(
                #             conductor, move_label, master_time.get_current_time_context(),
                #             actor, prev_desc, narrative_context_manager, tracker, available_npcs
                #         )
                #         
                #         # CRITICAL: Display the new scene description to the player
                #         print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                #         
                #         # Clear NPCs from previous location
                #         available_npcs.clear()
                #         print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                #         
                #         # Advance time for movement
                #         req = master_time.create_user_action_request(
                #             RuleOf3Category.THREE_MINUTE,
                #             actor.sheet.name,
                #             user_input
                #         )
                #         res = master_time.request_time_advancement(req)
                #         
                #         # Location change already generated narrative, skip to next turn
                #         continue
                # except Exception as e:
                #     print(f"{Color.WARNING}[LOCATION] Could not process location change: {e}{Color.RESET}")
                # ============================================================
                
                # NEW CODE: Check if user is continuing an active journey OR starting a new one
                try:
                    from spatial_context_system import get_spatial_manager
                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                    
                    # Get current location for travel time calculation
                    current_location = context_manager.context.current_location or "Unknown Location"
                    
                    # Check if user is continuing active journey
                    journey_progress = travel_chunking.get_progress()
                    if journey_progress:
                        # User has an active journey - check if they're continuing or straying
                        destination = journey_progress["destination"]
                        current_segment = journey_progress["current_segment"]
                        total_segments = journey_progress["total_segments"]
                        
                        # Check if user input indicates continuing toward destination
                        continuing = any(word in user_input.lower() for word in 
                            ["continue", "keep going", "keep walking", "walk", "go", destination.lower()])
                        
                        if continuing:
                            # Advance to next segment
                            completed, dest = travel_chunking.advance_segment()
                            
                            if completed:
                                # Journey complete - arrive at destination
                                print(f"{Color.SUCCESS}[TRAVEL] Arrived at {dest}!{Color.RESET}")
                                
                                # SAVE NPC names to context BEFORE clearing (for location state persistence)
                                if available_npcs:
                                    npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                                    context_manager.set_nuas(npc_names)
                                
                                # Clear NPCs and initiative from previous location BEFORE generating new ones
                                available_npcs.clear()
                                try:
                                    from initiative_system import get_location_initiative_tracker
                                    get_location_initiative_tracker().clear()
                                except ImportError:
                                    pass
                                print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                                
                                # Generate arrival scene description (will populate new NPCs and roll initiative)
                                prev_desc = scene_description
                                scene_description = _apply_location_move(
                                    conductor, dest, master_time.get_current_time_context(),
                                    actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                    population_manager=population_manager,
                                    scene_creator=scene_creator,
                                    actor_registry=global_actor_registry
                                )
                                
                                # Sync pygame map to new location
                                try:
                                    from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                    print(f"{Color.SYSTEM}[PMAP] Clearing cache and syncing to new location: {dest}{Color.RESET}")
                                    clear_layout_cache()  # Clear old location's cached layout
                                    sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                except Exception as pmap_err:
                                    print(f"{Color.WARNING}[PMAP] Sync error on arrival: {pmap_err}{Color.RESET}")
                                
                                # Generate storyteller sparks BEFORE displaying scene (for integration)
                                sparks = generate_location_arrival_sparks(
                                    location=dest,
                                    scene_description=scene_description,
                                    available_npcs=available_npcs,
                                    narrative_context_manager=narrative_context_manager,
                                    actor=actor,
                                    conductor=conductor,
                                    display_sparks=False  # We'll display after scene
                                )
                                
                                # Display arrival scene first, then sparks separately for testing clarity
                                print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")

                                try:
                                    for spark in (sparks or [])[:3]:
                                        if hasattr(spark, 'trigger_description') and spark.trigger_description:
                                            print(f"{Color.STATUS}✨ {spark.trigger_description}{Color.RESET}")
                                except Exception:
                                    pass
                                
                                # Generate internal voice for arrival
                                try:
                                    # Build spark context for internal voice
                                    spark_hints = ""
                                    if sparks:
                                        spark_hints = " ".join([
                                            s.trigger_description[:100] for s in sparks[:2] 
                                            if hasattr(s, 'trigger_description') and s.trigger_description
                                        ])
                                    
                                    internal_voice = generate_unified_internal_voice(
                                        actor=actor,
                                        narrator=narrator,
                                        scene_description=scene_description + (f" {spark_hints}" if spark_hints else ""),
                                        user_action=f"arriving at {dest}",
                                        action_outcome=f"Completed journey to {dest}",
                                        function_hint="comment",
                                        urgency="normal",
                                        failure_tracker=failure_tracker,
                                        narrative_context_manager=narrative_context_manager
                                    )
                                    display_internal_voice_box(internal_voice)
                                except Exception as iv_err:
                                    print(f"{Color.WARNING}[ARRIVAL] Could not generate internal voice: {iv_err}{Color.RESET}")
                                
                                # Advance time for final segment
                                req = master_time.create_user_action_request(
                                    RuleOf3Category.THREE_MINUTE,
                                    actor.sheet.name,
                                    user_input
                                )
                                res = master_time.request_time_advancement(req)
                                
                                continue  # Skip to next turn (journey arrival in fallible_action)
                            else:
                                # Still traveling - describe this segment
                                # dest now contains the current transitional location
                                transitional_location = dest or f"Passage toward {destination}"
                                new_segment = current_segment + 1
                                journey_data = travel_chunking.get_progress()
                                cardinal_dir = journey_data.get("direction", "") if journey_data else ""
                                print(f"{Color.INFO}[TRAVEL] Segment {new_segment}/{total_segments}: Now in {transitional_location} (heading {cardinal_dir}){Color.RESET}")
                                
                                # ============================================================
                                # UPDATE SPATIAL CONTEXT FOR TRANSITIONAL LOCATION
                                # ============================================================
                                try:
                                    from spatial_context_system import get_spatial_manager, Position
                                    spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                    
                                    # Use helper to create transitional context with proper directional zones
                                    travel_chunking.create_transitional_context(spatial, transitional_location, destination)
                                    
                                    # Switch to transitional location
                                    spatial.set_current_location(transitional_location)
                                    ua_name = actor.sheet.name if hasattr(actor, 'sheet') else "User Actor"
                                    spatial.add_actor("ua_001", ua_name, Position(125, 180), is_user_actor=True)
                                    
                                    # Update context manager
                                    if context_manager:
                                        context_manager.context.current_location = transitional_location
                                        context_manager._save()
                                    
                                    print(f"{Color.CYAN}🚶 JOURNEY{Color.RESET} Entered: {transitional_location}")
                                    
                                    # Sync pygame map
                                    try:
                                        from pygame_spatial_map import sync_from_spatial_context, clear_layout_cache
                                        clear_layout_cache()
                                        sync_from_spatial_context(session_id=tracker.session_id if tracker else None)
                                    except Exception:
                                        pass
                                except Exception as journey_viz_err:
                                    print(f"{Color.WARNING}[JOURNEY] Transitional location error: {journey_viz_err}{Color.RESET}")
                                
                                # Generate perceptual description of this transitional space
                                direction_hint = f" heading {cardinal_dir}" if cardinal_dir else ""
                                segment_desc = narrator.generate_inquiry_response(
                                    user_question=f"walking through {transitional_location}{direction_hint} toward {destination} (segment {new_segment} of {total_segments})",
                                    ua_actor=actor,
                                    scene_description=f"You are passing through {transitional_location},{direction_hint} heading toward {destination}.",
                                    narrative_context="",
                                    current_time=master_time.get_current_time_context(),
                                    availability_context={'availability': 'exist', 'reasoning': 'Traveling through transitional space'}
                                )
                                
                                print(f"\n{Color.NARRATIVE}{segment_desc}{Color.RESET}\n")
                                
                                # Generate internal voice for transitional segment
                                try:
                                    internal_voice = generate_unified_internal_voice(
                                        actor=actor,
                                        narrator=narrator,
                                        scene_description=segment_desc,
                                        user_action=f"walking through {transitional_location} toward {destination}",
                                        action_outcome=f"Continuing journey to {destination} (segment {new_segment}/{total_segments})",
                                        function_hint="comment",
                                        urgency="calm",
                                        failure_tracker=failure_tracker,
                                        narrative_context_manager=narrative_context_manager
                                    )
                                    display_internal_voice_box(internal_voice)
                                except Exception as iv_err:
                                    print(f"{Color.WARNING}[TRAVEL] Could not generate internal voice: {iv_err}{Color.RESET}")
                                
                                # Advance time for this segment
                                req = master_time.create_user_action_request(
                                    RuleOf3Category.THREE_MINUTE,
                                    actor.sheet.name,
                                    user_input
                                )
                                res = master_time.request_time_advancement(req)
                                
                                continue
                        else:
                            # User strayed from path - cancel journey
                            print(f"{Color.WARNING}[TRAVEL] Journey to {destination} cancelled (strayed from path){Color.RESET}")
                            travel_chunking.cancel_journey()
                            # Fall through to normal action processing
                    
                    # Check for NEW location move
                    move_label = _detect_location_move(user_input, "", spatial_manager=spatial)
                    if move_label:
                        # Calculate travel time
                        travel_minutes = calculate_travel_time(current_location, move_label, spatial)
                        
                        if travel_minutes <= 3:
                            # Instant move (same building, adjacent area)
                            print(f"{Color.SYSTEM}[LOCATION] Moving to {move_label} (instant){Color.RESET}")
                            
                            # SAVE NPC names to context BEFORE clearing (for location state persistence)
                            if available_npcs:
                                npc_names = [getattr(n.sheet, 'name', str(n)) for n in available_npcs]
                                context_manager.set_nuas(npc_names)
                            
                            # Clear NPCs and initiative from previous location BEFORE generating new ones
                            available_npcs.clear()
                            try:
                                from initiative_system import get_location_initiative_tracker
                                get_location_initiative_tracker().clear()
                            except ImportError:
                                pass
                            print(f"{Color.SYSTEM}[LOCATION] Cleared NPCs from previous location{Color.RESET}")
                            
                            prev_desc = scene_description
                            scene_description = _apply_location_move(
                                conductor, move_label, master_time.get_current_time_context(),
                                actor, prev_desc, narrative_context_manager, tracker, available_npcs,
                                population_manager=population_manager,
                                scene_creator=scene_creator,
                                actor_registry=global_actor_registry
                            )
                            
                            # Display arrival scene
                            print(f"\n{Color.NARRATIVE}{scene_description}{Color.RESET}\n")
                            
                            # Advance time
                            req = master_time.create_user_action_request(
                                RuleOf3Category.THREE_MINUTE if travel_minutes > 0 else RuleOf3Category.THREE_SECOND,
                                actor.sheet.name,
                                user_input
                            )
                            res = master_time.request_time_advancement(req)
                            
                            continue
                        else:
                            # Long journey - needs chunking
                            total_segments = travel_chunking.start_journey(move_label, travel_minutes, origin=current_location)
                            print(f"{Color.INFO}[TRAVEL] Journey to {move_label} will take {travel_minutes} minutes ({total_segments} segments){Color.RESET}")
                            
                            # Generate departure narrative
                            try:
                                departure_narrative = narrator.generate_travel_departure_narrative(
                                    actor_name=actor.sheet.name,
                                    origin=scene_description,
                                    destination=move_label,
                                    travel_time_minutes=travel_minutes,
                                    current_time=master_time.get_current_time_context()
                                )
                                print(f"\n{Color.NARRATIVE}{departure_narrative}{Color.RESET}\n")
                                
                                # CRITICAL: Save to context immediately so next action knows we left
                                if narrative_context_manager:
                                    from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                                    narrative_context_manager.add_narrative_event(
                                        event_type=NarrativeEventType.ACTION_SEQUENCE,
                                        narrative_text=departure_narrative,
                                        actors_involved=[actor.sheet.name],
                                        importance=NarrativeImportance.NOTABLE,
                                        scene_context=f"Departure to {move_label}"
                                    )
                                
                                # Update scene description to reflect departure
                                scene_description = f"{scene_description}\n\n{departure_narrative}"
                                try:
                                    conductor.scene_description = scene_description
                                    tracker.set_current_scene(scene_description)
                                except Exception:
                                    pass
                            except Exception as e:
                                print(f"{Color.WARNING}[TRAVEL] Could not generate departure narrative: {e}{Color.RESET}")
                            
                            # Generate internal voice about the journey (unified system)
                            try:
                                internal_voice = generate_unified_internal_voice(
                                    actor=actor,
                                    narrator=narrator,
                                    scene_description=scene_description,
                                    user_action=f"traveling to {move_label}",
                                    action_outcome=f"Beginning journey to {move_label}",
                                    function_hint="comment",
                                    urgency="normal",
                                    failure_tracker=failure_tracker,
                                    narrative_context_manager=narrative_context_manager
                                )
                                display_internal_voice_box(internal_voice)
                            except Exception as e:
                                print(f"{Color.WARNING}[TRAVEL] Could not generate travel thoughts: {e}{Color.RESET}")

                            print(f"{Color.SYSTEM}Describe your first action as you begin traveling...{Color.RESET}")
                            
                            # ============================================================
                            # JOURNEY START: Move actor TO the exit to show departure
                            # The narrative describes leaving, so actor should be at exit
                            # ============================================================
                            try:
                                current_pos = spatial.get_actor_position("ua_001")
                                if current_pos:
                                    from spatial_context_system import DEFAULT_MAP_WIDTH as _DMW, DEFAULT_MAP_HEIGHT as _DMH
                                    MAP_WIDTH, MAP_HEIGHT = float(_DMW), float(_DMH)

                                    dims = None
                                    try:
                                        ctx = spatial.get_current_context() if spatial else None
                                        dims = getattr(ctx, 'location_dimensions', None) if ctx else None
                                        if dims:
                                            MAP_WIDTH = float(getattr(dims, 'width', MAP_WIDTH) or MAP_WIDTH)
                                            MAP_HEIGHT = float(getattr(dims, 'height', MAP_HEIGHT) or MAP_HEIGHT)
                                    except Exception:
                                        dims = None

                                    start_x, start_y = current_pos.x, current_pos.y
                                    exit_x, exit_y = MAP_WIDTH / 2, MAP_HEIGHT * 0.08

                                    try:
                                        external_candidates = []
                                        if dims:
                                            for _ok, _o in (getattr(dims, 'obstacles', {}) or {}).items():
                                                try:
                                                    onm = str(getattr(_o, 'obstacle_name', '') or '')
                                                    ot = str(getattr(_o, 'obstacle_type', '') or '')
                                                    pk = str(getattr(_o, 'portal_kind', '') or '')
                                                    cto = str(getattr(_o, 'connects_to', '') or '')
                                                    is_ext = bool(getattr(_o, 'is_external', False))

                                                    nm_l = onm.lower()
                                                    ot_l = ot.lower()
                                                    pk_l = pk.lower()
                                                    cto_l = cto.lower()

                                                    is_explicit_exit = (
                                                        ot_l == 'exit'
                                                        or 'exit' in nm_l
                                                        or 'entrance' in nm_l
                                                        or pk_l in ('exit', 'entrance')
                                                    )
                                                    is_externalish = is_ext or cto_l in ('outside', 'outdoors', 'street', 'exterior')
                                                    if not (is_explicit_exit or is_externalish):
                                                        continue

                                                    bps = getattr(_o, 'boundary_points', None) or []
                                                    if not bps:
                                                        continue
                                                    cx = sum(float(getattr(p, 'x', 0.0) or 0.0) for p in bps) / float(len(bps))
                                                    cy = sum(float(getattr(p, 'y', 0.0) or 0.0) for p in bps) / float(len(bps))
                                                    external_candidates.append((cx, cy))
                                                except Exception:
                                                    continue

                                        if external_candidates:
                                            def _dist2(px, py):
                                                dx = float(px) - float(start_x)
                                                dy = float(py) - float(start_y)
                                                return (dx * dx) + (dy * dy)
                                            best = min(external_candidates, key=lambda t: _dist2(t[0], t[1]))
                                            exit_x, exit_y = float(best[0]), float(best[1])
                                    except Exception:
                                        pass

                                    new_x = start_x + (exit_x - start_x) * 0.95
                                    new_y = start_y + (exit_y - start_y) * 0.95

                                    spatial.move_actor("ua_001", Position(new_x, new_y))
                                    print(f"{Color.CYAN}🚶 JOURNEY START{Color.RESET}: ({start_x:.0f},{start_y:.0f}) → ({new_x:.0f},{new_y:.0f}) [AT EXIT]")

                                    try:
                                        auto_sync_map(session_id=tracker.session_id if tracker else None)
                                    except Exception:
                                        pass
                            except Exception as e:
                                print(f"{Color.WARNING}[JOURNEY] Start visualization error: {e}{Color.RESET}")
                            
                            # Don't process this turn - wait for user to describe first segment
                            continue
                            
                except Exception as e:
                    print(f"{Color.WARNING}[LOCATION] Could not process movement: {e}{Color.RESET}")
                    import traceback
                    traceback.print_exc()
                
                # If we reach here, it's NOT a location change - process as normal physical/social action
                
                # CRITICAL: If we are in ENCOUNTER mode, DO NOT process fallible actions here.
                # They should be handled by the encounter loop.
                if current_mode == SimulationMode.ENCOUNTER:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.SYSTEM}[FALLIBLE ACTION SKIPPED] Mode is ENCOUNTER - action deferred to encounter loop{Color.RESET}")
                    continue

                # Get availability result
                action_availability = availability_result.get("availability") if 'availability_result' in locals() else IntentAvailability.EXIST
                
                # Interpret the action
                interpretation_data = conductor.interpret_fallible_action(
                    user_input=user_input,
                    proactor=actor
                )
                
                # Calculate success using standard UTAS formula
                from unified_formula import calculate_unified_result
                from actor_sheet import SFactorType
                
                utas = interpretation_data['utas_factors']
                s_trait_name = utas['s_trait_to_use']
                s_trait_enum = SFactorType[s_trait_name.upper()]
                skill_data = utas.get('skill', {})
                skill_name = skill_data.get('name') if isinstance(skill_data, dict) else None
                
                result = calculate_unified_result(
                    actor=actor,
                    s_trait=s_trait_enum,
                    skill_name=skill_name if skill_name and skill_name != 'none' else None,
                    target_actor=None,
                    shift_polarity='Subtractive',
                    targeted_status=None,
                    supplement_val=0,
                    serendipity_override=None,
                    stress_level_override=utas.get('stress_level', 3)
                )
                
                success_total = result['final_result']
                success = success_total >= 0
                
                # Display calculations (same format as inquiry block)
                print(f"\n{Color.INFO}📊 DETAILED CALCULATIONS{Color.RESET}")
                print(f"{Color.SYSTEM}S-Trait: {normalize_sfactor_label(s_trait_name)} ({result['positive_components']['s_trait']}){Color.RESET}")
                print(f"{Color.SYSTEM}Skill: {skill_name if skill_name and skill_name != 'none' else 'N/A'} ({result['positive_components']['skill']}){Color.RESET}")
                print(f"{Color.SYSTEM}Serendipity: {result['positive_components']['serendipity']}{Color.RESET}")
                print(f"{Color.SYSTEM}Stress Level: {utas.get('stress_level', 3)}{Color.RESET}")
                print(f"{Color.SYSTEM}Total Success: {success_total}{Color.RESET}")
                
                success_narration = get_success_level_narration(success_total)
                print(f"{Color.SUCCESS}🎯 Success Level: {success_narration}{Color.RESET}\n")
                
                if success:
                    print(f"{Color.SUCCESS}Result: SUCCESS ✓{Color.RESET}")
                    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
                else:
                    print(f"{Color.ERROR}Result: FAILURE ✗{Color.RESET}")
                    print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
                
                # Get context
                recent_context = narrative_context_manager.get_context_for_llm(
                    lookback_events=5,
                    importance_threshold="notable"
                )
                recent_context = _merge_contexts(recent_context, everlasting_context_text)
                time_context = master_time.get_current_time_context()
                
                message_playback_narrative = None
                try:
                    ui_low = (user_input or "").lower()
                    playback_patterns = [
                        "press play", "hit play", "play the answering machine", "play answering machine",
                        "play voicemail", "play the tape", "press the play button", "check messages",
                        "play message", "play messages"
                    ]
                    if any(pat in ui_low for pat in playback_patterns):
                        scene_low = (scene_description or "").lower()
                        device_name = "Answering Machine" if ("answering machine" in ui_low or "answering machine" in scene_low) else "player"
                        presence_keywords = ["answering machine", "voicemail", "tape", "cassette", "recorder"]
                        no_messages_keywords = ["no messages", "no new messages", "empty", "blank tape", "erased", "0 new messages", "no saved messages"]

                        if not any(k in scene_low for k in presence_keywords):
                            perceptual_description = "You press the play button. The tiny speaker clicks, then nothing."
                            display_perceptual_description_box(perceptual_description)
                        elif any(k in scene_low for k in no_messages_keywords):
                            perceptual_description = "You press play. A soft click, a brief whirr, then silence—no messages."
                            display_perceptual_description_box(perceptual_description)
                        else:
                            perceptual_description = f"You press the play button on the {device_name.lower()}."
                            display_perceptual_description_box(perceptual_description)
                            message_playback_narrative = narrator.generate_media_playback_content(
                                device_name=device_name,
                                ua_actor=actor,
                                scene_description=scene_description,
                                narrative_context=recent_context,
                                time_context=time_context
                            )
                            if message_playback_narrative:
                                print(f"{Color.NARRATIVE}{message_playback_narrative}{Color.RESET}\n")
                                try:
                                    import re
                                    actors_involved = [actor.sheet.name]
                                    proper_nouns = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', message_playback_narrative)
                                    for name in proper_nouns:
                                        if name not in actors_involved and len(name) > 1:
                                            actors_involved.append(name)
                                    narrative_context_manager.add_narrative_event(
                                        event_type=NarrativeEventType.DIALOGUE_EXCHANGE,
                                        narrative_text=message_playback_narrative,
                                        actors_involved=actors_involved,
                                        importance=NarrativeImportance.NOTABLE
                                    )
                                except Exception:
                                    pass
                            try:
                                if message_playback_narrative and ('"' in message_playback_narrative or '“' in message_playback_narrative):
                                    resurfaced_memories = intent_memory_creator.process_narration_for_memories(
                                        narration=message_playback_narrative,
                                        current_location=current_location or "Unknown Location",
                                        turn_number=turn_number,
                                        scene_id=scene_id
                                    )
                                    for memory_result in resurfaced_memories:
                                        display_memory_creation(
                                            memory_result,
                                            narrative_context_manager=narrative_context_manager,
                                            actor_name=actor.sheet.name,
                                            show_internal_voice=True
                                        )
                            except Exception as e:
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.WARNING}Memory processing for playback failed: {e}{Color.RESET}")
                    else:
                        # Get NUA actions context for perceptual awareness
                        nua_actions = _get_nua_actions_context(tracker, f"actor_{actor.sheet.name.lower().replace(' ', '_')}")
                        
                        perceptual_description = narrator.generate_inquiry_response(
                            user_question=user_input,
                            ua_actor=actor,
                            scene_description=scene_description,
                            narrative_context=recent_context,
                            current_time=time_context,
                            availability_context=availability_result if 'availability_result' in locals() else None,
                            nua_actions_context=nua_actions
                        )
                        display_perceptual_description_box(perceptual_description)
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}Playback content generation failed: {e}{Color.RESET}")
                
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
                        scene_id=scene_id,
                        mention_system=mention_system
                    )
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}[NPC PARSER] Failed to parse perceptual description: {e}{Color.RESET}")
                
                # Generate internal voice (mental reaction to success/failure)
                outcome_for_internal = message_playback_narrative or perceptual_description
                
                # Determine function hint based on success/failure
                function_hint = "comment"
                urgency = "normal"
                if success_total <= 1:
                    function_hint = "solution"  # Failed - might need to suggest alternatives
                    urgency = "urgent"
                elif success_total >= 4:
                    urgency = "calm"  # Success - satisfied tone
                
                internal_voice = generate_unified_internal_voice(
                    actor=actor,
                    narrator=narrator,
                    scene_description=scene_description,
                    user_action=user_input,
                    action_outcome=outcome_for_internal,
                    function_hint=function_hint,
                    urgency=urgency,
                    failure_tracker=failure_tracker,
                    narrative_context_manager=narrative_context_manager
                )
                
                # Display internal voice
                display_internal_voice_box(internal_voice)
                
                # Advance time (physical actions take time)
                req = master_time.create_user_action_request(
                    RuleOf3Category.THREE_MINUTE,
                    actor.sheet.name,
                    user_input
                )
                res = master_time.request_time_advancement(req)
                
                if not SUPPRESS_DEBUG:
                    elapsed = simulation_time_tracker.get_simulation_time_display()
                    print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                
                # Sync pygame map after action
                try:
                    auto_sync_map(session_id=tracker.session_id if tracker else None)
                except Exception:
                    pass
                
                # CRITICAL: Check if this was a successful remote interaction (phone call)
                # If so, create encounter for the conversation
                if (fallible_subtype == 'social' and 
                    success and 
                    any(word in user_input.lower() for word in ['call', 'phone', 'dial', 'ring']) and
                    pending_target_hint):
                    
                    print(f"\n{Color.SUCCESS}📞 PHONE CONNECTION ESTABLISHED{Color.RESET}")
                    print(f"{Color.INFO}Creating conversation encounter with {pending_target_hint}...{Color.RESET}")
                    
                    # Create NPC for phone conversation using narrative context
                    try:
                        npc_context = narrative_context_manager.get_context_for_llm(lookback_events=10) if narrative_context_manager else ""
                        
                        npc_prompt = (
                            f"Create an NUA named {pending_target_hint} for a PHONE CONVERSATION.\n\n"
                            f"**Context from recent events:**\n{npc_context[:800]}\n\n"
                            f"**Scene:** {scene_description[:400]}\n\n"
                            f"CRITICAL INSTRUCTIONS:\n"
                            f"1. Search the context for information about {pending_target_hint} (occupation, relationship, personality)\n"
                            f"2. This is a PHONE CONVERSATION - they are not physically present\n"
                            f"3. Use any known occupation/role from context (e.g., 'studio engineer')\n"
                            f"4. Reflect their relationship to the user actor in personality/demeanor\n"
                            f"5. Make S-factors and skills align with their known role\n"
                            f"6. This should feel like someone the user actor knows and is calling\n"
                        )
                        
                        phone_npc = scene_creator.generate_nua(npc_prompt, scene_description)
                        
                        if phone_npc:
                            # Register NUA for persistence and add to available NPCs
                            register_nua(phone_npc, available_npcs)
                            
                            # Initialize encounter for phone conversation
                            encounter_checker.current_context.participants = [phone_npc]
                            encounter_checker.current_context.mode = SimulationMode.ENCOUNTER
                            current_mode = SimulationMode.ENCOUNTER
                            
                            # CRITICAL: Mark this as a PHONE CONVERSATION encounter
                            # This prevents the narrator/DeciderAgent from generating face-to-face actions
                            encounter_checker.current_context.is_remote_encounter = True
                            encounter_checker.current_context.remote_encounter_type = "phone_call"
                            encounter_checker.current_context.remote_encounter_description = f"Phone conversation with {phone_npc.sheet.name}"

                            # DO NOT store the "I call X" action as initial_user_action for phone calls
                            # The call action was already processed as a fallible action above

                            # CRITICAL FIX: Clear pending encounter action so it doesn't trigger skip_prompt in next loop
                            # This prevents the encounter loop from re-processing "I call Lena" as the first dialogue turn
                            pending_encounter_action = None

# ... (rest of the code remains the same)
                            print(f"{Color.SUCCESS}⚔️ PHONE CONVERSATION ENCOUNTER INITIATED{Color.RESET}")
                            print(f"{Color.INFO}📞 You are now on the phone with {_ua_display_name(phone_npc, ua_actor=actor)}{Color.RESET}")
                            print(f"{Color.SYSTEM}[REMOTE] This is a phone conversation - no physical presence{Color.RESET}")
                            
                            # Continue to encounter loop (don't advance to next turn)
                            continue
                        else:
                            print(f"{Color.WARNING}Phone rang but no answer...{Color.RESET}")
                    except Exception as e:
                        print(f"{Color.WARNING}Failed to establish phone connection: {e}{Color.RESET}")
                
                # Continue to next turn
                continue
            
            # Fallback: Handle as exploration action with success level narration
            # This code is unreachable because all fallible actions are handled above
            # But kept for safety/future use
            print(f"\n{Color.SYSTEM}═══ Action Classification ═══{Color.RESET}")
            print(f"{Color.SYSTEM}Type: EXPLORATION ACTION{Color.RESET}")
            print(f"{Color.SYSTEM}Reasoning: {input_analysis.get('reasoning', 'Fallible action requiring success calculation') if input_analysis else 'N/A'}{Color.RESET}")
            print(f"\n{Color.INFO}🚶 EXPLORATION ACTION{Color.RESET}")
            
            # Process exploration action as inquiry
            exploration_result = conductor.handle_inquiry(
                user_input, actor, None, time_context
            )
            
            # ============================================================
            # INTENT-BASED MEMORY CREATION FOR EXPLORATION/INQUIRY
            # ============================================================
            # For inquiries, create memories based on the question
            # This allows diegetic discovery of vessel background
            # ============================================================
            try:
                # Create a mock availability result for memory creation
                # Inquiries are always "available_now" since they're just questions
                availability_for_memory = {
                    'availability': 'available_now',
                    'reasoning': 'Inquiry action',
                    'timestamp': time_context.get('timestamp') if time_context else None
                }
                
                created_memories = intent_memory_creator.process_intent_for_memories(
                    user_intent=user_input,
                    availability_result=availability_for_memory,
                    current_location=current_location or "Unknown Location",
                    turn_number=turn_number,
                    scene_id=scene_id
                )
                
                # Display any created memories with internal voice
                for memory_result in created_memories:
                    display_memory_creation(
                        memory_result,
                        narrative_context_manager=narrative_context_manager,
                        actor_name=actor.sheet.name
                    )
                    
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}Memory creation for exploration failed: {e}{Color.RESET}")
            
            if exploration_result:
                # Update actor tasks based on action interpretation
                try:
                    interpretation_data = exploration_result.get('interpretation_data', {})
                    conductor.interpreter.update_actor_tasks(
                        user_action=user_input,
                        actor=actor,
                        action_interpretation=interpretation_data
                    )
                except Exception as e:
                    logger.log_error(f"Task update failed: {e}")
                
                success_data = exploration_result.get('success_data', {})
                narrative_response = exploration_result.get('narrative_response', 'No response generated.')
                
                # Display calculations with success level narration
                print(f"\n{Color.INFO}📊 DETAILED CALCULATIONS{Color.RESET}")
                print(f"{Color.SYSTEM}S-Trait: {normalize_sfactor_label(success_data.get('s_trait_used', 'N/A'))} ({success_data.get('s_trait_value', 0)}){Color.RESET}")
                print(f"{Color.SYSTEM}Skill: {success_data.get('skill_used', 'N/A')} ({success_data.get('skill_value', 0)}){Color.RESET}")
                print(f"{Color.SYSTEM}Serendipity: {success_data.get('serendipity', success_data.get('serendipity_roll', 0))}{Color.RESET}")
                print(f"{Color.SYSTEM}Stress Level: {success_data.get('stress_level', success_data.get('stressor', 1))}{Color.RESET}")
                success_total = success_data.get('total_score', success_data.get('total', 0))
                print(f"{Color.SYSTEM}Total Success: {success_total}{Color.RESET}")
                
                # Add success level narration
                success_narration = get_success_level_narration(success_total)
                print(f"{Color.SUCCESS}🎯 Success Level: {success_narration}{Color.RESET}")
                
                # Apply backfire penalties for ROAM fallible actions
                if success_total < 0:
                    try:
                        exchange_type = exploration_result.get('interpretation_data', {}).get('utas_factors', {}).get('exchange_type', '')
                        if isinstance(exchange_type, str):
                            exchange_type_upper = exchange_type.strip().upper()
                            if exchange_type_upper == 'SPIRIT':
                                actor.sheet.update_status(StatusType.SPIRIT, -1, reason='ROAM backfire (gathering)')
                            elif exchange_type_upper == 'STAMINA':
                                actor.sheet.update_status(StatusType.STAMINA, -1, reason='ROAM backfire (overcoming)')
                    except Exception as e:
                        print(f"{Color.WARNING}Backfire penalty application failed: {e}{Color.RESET}")
                
                # JOURNEY CHUNKING: Check if exploration action needs chunking
                from journey_chunking_system import get_journey_chunking_system
                
                chunking_system = get_journey_chunking_system(key_memories_system=key_memories)
                interpretation_data = exploration_result.get('interpretation_data', {})
                should_chunk = chunking_system.should_chunk_action(
                    user_input=user_input,
                    action_description=interpretation_data.get('action_description', user_input)
                )
                
                if should_chunk:
                    print(f"\n{Color.SYSTEM}🚶 JOURNEY DETECTED - Breaking into realistic segments...{Color.RESET}")
                    
                    # Estimate duration
                    estimated_duration = chunking_system._estimate_duration(
                        user_input=user_input,
                        action_description=interpretation_data.get('action_description', user_input)
                    )
                    
                    print(f"{Color.SYSTEM}📏 Estimated journey time: {estimated_duration:.1f} minutes{Color.RESET}")
                    
                    # Extract destination
                    destination = "destination"
                    if " to " in user_input.lower():
                        parts = user_input.lower().split(" to ", 1)
                        if len(parts) > 1:
                            destination = parts[1].strip().rstrip('.,!?')
                    
                    # Create chunks
                    chunks = chunking_system.create_journey_chunks(
                        user_input=user_input,
                        action_description=interpretation_data.get('action_description', user_input),
                        estimated_duration=estimated_duration,
                        current_location=context_manager.context.current_location,
                        destination=destination
                    )
                    
                    print(f"{Color.SYSTEM}📦 Journey broken into {len(chunks)} chunks{Color.RESET}")
                    
                    # Process each chunk
                    for chunk in chunks:
                        print(f"\n{Color.SYSTEM}{'='*60}{Color.RESET}")
                        print(f"{Color.SYSTEM}[CHUNK {chunk.chunk_number}/{chunk.total_chunks}]: {chunk.chunk_type.upper()}{Color.RESET}")
                        print(f"{Color.SYSTEM}⏱️  Duration: {chunk.duration_minutes:.1f} minutes{Color.RESET}")
                        print(f"{Color.SYSTEM}{'='*60}{Color.RESET}\n")
                        
                        # Generate chunk narrative prompt
                        chunk_prompt = chunking_system.generate_chunk_narrative_prompt(
                            chunk=chunk,
                            user_input=user_input,
                            action_description=interpretation_data.get('action_description', user_input),
                            actor_name=actor.sheet.name,
                            scene_description=scene_description,
                            destination=destination  # Pass destination so narrator knows where we're heading
                        )
                        
                        # Generate narrative for this chunk
                        chunk_narrative = narrator.generate_contextual_exploration_action_result_narrative(
                            user_input=user_input,
                            actor=actor,
                            scene_description=chunk_prompt,
                            success_total=success_total,
                            time_context=time_context
                        )
                        
                        # Display chunk narrative
                        print(f"{Color.NARRATIVE}📖 {chunk_narrative}{Color.RESET}\n")
                        
                        # Generate internal voice for this chunk (thoughts during travel)
                        try:
                            chunk_internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=chunk.location_context,
                                action_context=f"Traveling to {destination} - {chunk.chunk_type} ({chunk.progress_percentage}% complete)",
                                narrative_result=chunk_narrative,
                                mode="roam"
                            )
                            if chunk_internal_voice:
                                display_internal_voice_box(chunk_internal_voice)
                        except Exception:
                            pass  # Internal voice is optional
                        
                        # Advance time
                        time_coordinator.advance_time(
                            duration=chunk.duration_minutes * 60,
                            action_type="travel"
                        )
                        
                        # Update scene description for next chunk
                        if chunk.chunk_type == "arrival":
                            context_manager.context.current_location = destination
                            scene_description = f"You have arrived at {destination}."
                        else:
                            scene_description = chunk.location_context
                        
                        # Small pause between chunks
                        import time
                        time.sleep(0.3)
                    
                    print(f"\n{Color.SUCCESS}✅ Journey complete! You have arrived at {destination}.{Color.RESET}")
                    
                    # Update final scene description
                    contextual_result = f"After a {estimated_duration:.0f}-minute journey, you arrive at {destination}."
                    last_action_narrative = contextual_result
                    scene_updates.append(contextual_result)
                    
                    scene_description = f"{scene_description}\n\n{contextual_result}"
                    try:
                        conductor.scene_description = scene_description
                        tracker.set_current_scene(scene_description)
                    except Exception:
                        pass
                    
                    # Skip normal narrative - already narrated journey
                    continue
                
                # NORMAL NARRATIVE (Non-chunked exploration actions)
                # All fallible actions get full narrative (including mental actions)
                interpretation_data = exploration_result.get('interpretation_data', {})
                
                # NORMAL ACTION: Full narrative
                print(f"\n{Color.INFO}📖 ACTION RESULT{Color.RESET}")
                # Generate contextual narrative for the action outcome in ROAM mode using success total
                # Get framing from Four-Mode Narrative Loop
                turn_data = _build_turn_data(
                    user_input=user_input,
                    scene_description=scene_description,
                    current_mode=current_mode,
                    success_total=success_total,
                    continuity={'judgment': 'Possible'}
                )
                # Add interpretation data for enhanced loop
                turn_data['interpretation_data'] = interpretation_data
                turn_data['narrative_response'] = last_action_narrative
                
                # Process through enhanced narrative loop (no push design)
                framing = narrative_loop.process_turn(
                    turn_data=turn_data,
                    scene_description=scene_description,
                    time_context=time_context,
                    available_npcs=available_npcs
                )
                try:
                    if framing and framing.get('mode_changed'):
                        print(f"{Color.SYSTEM}🔀 Mode Shift → {framing.get('mode', 'unknown').upper()} (Tone: {framing.get('tone', 'unknown')}){Color.RESET}")
                except Exception:
                    pass
                
                # FIX BUG #7: Initialize contextual_result to prevent reusing old narratives
                contextual_result = ""
                
                # FIX BUG #9: Use current scene context for narrative generation
                contextual_result = narrator.generate_contextual_exploration_action_result_narrative(
                    user_input=user_input,
                    actor=actor,
                    scene_description=get_current_scene(),
                    success_total=success_total,
                    time_context=time_context,
                    framing_guidance=framing
                )
                # Display outcome narrative for ALL actions (physical and mental)
                print(f"{Color.NARRATIVE}{contextual_result}{Color.RESET}")
                
                # ============================================================
                # PERCEPTION-BASED MEMORY RESURFACING
                # ============================================================
                # CRITICAL: Only run if NOT an inquiry (inquiries use intent-based)
                # The two memory systems must NEVER both activate in the same turn
                # ============================================================
                
                if not is_inquiry and contextual_result:
                    try:
                        resurfaced_memories = intent_memory_creator.process_narration_for_memories(
                            narration=contextual_result,
                            current_location=current_location or "Unknown Location",
                            turn_number=turn_number,
                            scene_id=scene_id
                        )
                        
                        # Display any resurfaced memories
                        # Also record in narrative context for future LLM calls
                        for memory_result in resurfaced_memories:
                            # Show internal voice for perception-based memories (not shown separately)
                            display_memory_creation(
                                memory_result,
                                narrative_context_manager=narrative_context_manager,
                                actor_name=actor.sheet.name,
                                show_internal_voice=True
                            )
                            
                    except Exception as e:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Memory resurfacing failed: {e}{Color.RESET}")
                
                # Generate internal voice narration for ROAM mode only
                if current_mode == SimulationMode.ROAM:
                    try:
                        # Import success level converter
                        from narrative_utils import get_success_level_numeric
                        
                        # Get recent narrative context for memory recall
                        recent_narrative = narrative_context_manager.get_context_for_llm(
                            lookback_events=10,  # More lookback for inquiries to find relevant memories
                            importance_threshold="routine"
                        )
                        recent_narrative = _merge_contexts(recent_narrative, everlasting_context_text, max_chars=1800)
                        
                        # For inquiries, use two-step process: FACT first, then THOUGHT
                        if is_inquiry:
                            # Get current time context for internal voice
                            current_time_context = simulation_time_tracker.get_simulation_time_display()
                            
                            # STEP 1: Generate FACTUAL KNOWLEDGE (for memory)
                            factual_knowledge = narrator.generate_inquiry_factual_knowledge(
                                ua_actor=actor,
                                question=user_input,
                                scene_description=scene_description,
                                narrative_context=recent_narrative,
                                success_level=get_success_level_numeric(success_total)
                            )
                            
                            # STEP 2: Generate THOUGHT based on fact (or lack thereof)
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=factual_knowledge or "Thinking about this...",
                                function_hint="information",
                                question_content=user_input,
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                            
                            # STEP 3: Create/retrieve memory with internal voice (if knowledge exists)
                            if factual_knowledge:
                                try:
                                    memory_result = intent_memory_creator.create_memory_from_inquiry_answer(
                                        question=user_input,
                                        answer=factual_knowledge,  # FACT, not thought
                                        current_location=current_location or "Unknown Location",
                                        turn_number=turn_number,
                                        scene_id=scene_id,
                                        internal_voice=internal_voice  # Pass internal voice to accompany memory
                                    )
                                    
                                    if memory_result:
                                        is_existing = memory_result.get('is_existing', False)
                                        
                                        # Display appropriate message
                                        if is_existing:
                                            print(f"\n{Color.INFO}💡 Recalled existing knowledge{Color.RESET}")
                                        
                                        # Display memory with internal voice
                                        display_memory_creation(
                                            memory_result,
                                            narrative_context_manager=narrative_context_manager,
                                            actor_name=actor.sheet.name,
                                            show_internal_voice=True  # Show internal voice to acknowledge memory
                                        )
                                except Exception as e:
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.WARNING}Memory creation from factual knowledge failed: {e}{Color.RESET}")
                        else:
                            # Use unified internal voice system
                            internal_voice = generate_unified_internal_voice(
                                actor=actor,
                                narrator=narrator,
                                scene_description=scene_description,
                                user_action=user_input,
                                action_outcome=contextual_result,
                                function_hint="comment",
                                urgency="normal",
                                failure_tracker=failure_tracker,
                                narrative_context_manager=narrative_context_manager
                            )
                        
                        if internal_voice:
                            # For inquiries, internal voice is shown with memory
                            # For normal actions, show it separately
                            if not is_inquiry or not factual_knowledge:
                                display_internal_voice_box(internal_voice)
                            
                            # Record internal voice in narrative context
                            try:
                                from llm_agents.narrative_context_system import NarrativeEventType, NarrativeImportance
                                narrative_context_manager.add_narrative_event(
                                    event_type=NarrativeEventType.INTERNAL_VOICE,
                                    narrative_text=f"💭 {internal_voice}",
                                    actors_involved=[actor.sheet.name],
                                    importance=NarrativeImportance.NOTABLE,
                                    emotional_tone="reflective"
                                )
                            except Exception:
                                pass
                    except Exception as e:
                        # Log internal voice errors for debugging
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.WARNING}Internal voice generation failed: {e}{Color.RESET}")
                
                # Track for snapshot integration
                last_action_narrative = contextual_result
                scene_updates.append(contextual_result)
                
                # CRITICAL: Always update scene_description with action results
                # This creates a cumulative narrative that NEVER loses context
                scene_description = f"{scene_description}\n\n{contextual_result}"
                try:
                    conductor.scene_description = scene_description
                except Exception as e:
                    logger.log_error(f"Failed to update conductor scene_description: {e}")
                
                # Check for item acquisition and update inventory (fallible actions)
                # Skip for inquiries - questions don't acquire items
                if not is_inquiry:
                    try:
                        action_result = {
                            'narrative': contextual_result,
                            'success_calculation': {'total_successes': success_total}
                        }
                        skip_inventory_manager = False
                        try:
                            if monetary_data and monetary_data.get('transaction_detected'):
                                creates_item = bool(monetary_data.get('creates_item'))
                                removes_item = bool(monetary_data.get('removes_item'))
                                skip_inventory_manager = creates_item or removes_item
                        except Exception:
                            skip_inventory_manager = False

                        if not skip_inventory_manager:
                            print(f"{Color.SYSTEM}[INVENTORY] Checking for item acquisition in: '{user_input}'{Color.RESET}")
                            inventory_message = inventory_manager.process_action_for_inventory(
                                user_input, action_result, actor.sheet
                            )
                            if inventory_message:
                                print(f"{Color.SUCCESS}{inventory_message}{Color.RESET}")
                            else:
                                print(f"{Color.SYSTEM}[INVENTORY] No item acquisition detected{Color.RESET}")
                    except Exception as e:
                        logger.log_error(f"Inventory management error: {e}")
                
                # ACTION-TO-WORLD LINKING: Persist world changes from user actions
                try:
                    world_changes = world_state.process_user_action(
                        action_text=user_input,
                        location=scene_description[:50],
                        actor_name=actor.sheet.name
                    )
                    for change in world_changes:
                        if change.get('message'):
                            print(f"{Color.INFO}{change['message']}{Color.RESET}")
                except Exception:
                    pass  # World linking is optional enhancement
                
                # ============================================================
                # TIME ADVANCEMENT - CRITICAL
                # ============================================================
                # EVERY action must advance time - no exceptions
                # Physical actions = 3 seconds, Mental actions = 3 seconds
                # ============================================================
                try:
                    from master_time_coordinator import TimeAdvancementRequest, TimeEventType
                    
                    # Determine time category (all fallible actions are 3 seconds minimum)
                    time_category = RuleOf3Category.THREE_SECOND
                    
                    # Create time advancement request
                    time_request = TimeAdvancementRequest(
                        event_type=TimeEventType.USER_ACTION,
                        rule_of_3_category=time_category,
                        requester_system="exploration_action",
                        actor_name=actor.sheet.name,
                        description=user_input
                    )
                    
                    # Advance time through master coordinator
                    time_result = master_time.request_time_advancement(time_request)
                    
                    if not SUPPRESS_DEBUG:
                        elapsed = simulation_time_tracker.get_simulation_time_display()
                        print(f"{Color.SYSTEM}⏰ Time advanced: +{time_result.duration_advanced_seconds}s | Clock: {time_result.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                    
                    # WORLD TIME PASSAGE: Simulate weather and NPC activities
                    try:
                        hours_passed = time_result.duration_advanced_seconds / 3600.0
                        if hours_passed > 0.01:  # Only simulate if meaningful time passed
                            known_npc_names = [npc.sheet.name for npc in available_npcs] if available_npcs else []
                            time_sim = world_state.simulate_time_passage(
                                hours_passed=hours_passed,
                                known_npcs=known_npc_names
                            )
                            
                            # Display weather changes
                            if time_sim.get('weather_change'):
                                print(f"{Color.INFO}🌤️ {time_sim['weather_change']}{Color.RESET}")
                    except Exception:
                        pass  # Time simulation is optional
                except Exception as e:
                    logger.log_system(f"Time advancement error: {e}")
                
                # Check for goal progress (LLM-based dynamic evaluation)
                try:
                    from narrative_utils import get_success_level_numeric
                    success_level = get_success_level_numeric(success_total)
                    
                    # Record attempt in failure tracker
                    failure_tracker.record_attempt(
                        action_description=user_input,
                        success=(success_level >= 3)  # 3+ is success
                    )
                    
                    # Get recent narrative context
                    recent_narrative = narrative_context_manager.get_context_for_llm(
                        lookback_events=3,
                        importance_threshold="routine"
                    )
                    
                    progress_info = process_goal_progress(
                        tracker=goal_progress_tracker,
                        actor=actor,
                        action_description=user_input,
                        action_result=contextual_result,
                        success_level=success_level,
                        narrative_context=recent_narrative
                    )
                    
                    if progress_info:
                        display_goal_progress_update(progress_info, actor.sheet.name)
                        
                        # If goal completed, trigger SPARK for celebration/reflection
                        if progress_info.get("goal_completed"):
                            spark_active = True
                            spark_persistence = "hard"
                            spark_min_persist_turns = 2
                            spark_requires_exit_to_clear = True
                            print(f"{Color.INFO}✨ SPARK activated for goal completion{Color.RESET}")
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}Goal progress check failed: {e}{Color.RESET}")
                
                # PROGRESSIVE DISCOVERY: Check if following clues leads to NUA introduction
                try:
                    if not hasattr(main, '_progressive_discovery'):
                        from progressive_discovery_system import get_progressive_discovery
                        main._progressive_discovery = get_progressive_discovery()
                    
                    introduction_context = main._progressive_discovery.process_turn(
                        user_input, contextual_result
                    )
                    
                    if introduction_context:
                        print(f"{Color.SYSTEM}[DISCOVERY] Clue trail leads to actor introduction!{Color.RESET}")
                        print(f"{Color.SYSTEM}[DISCOVERY] Type: {introduction_context['clue_type']} → {introduction_context['suggested_nua_type']}{Color.RESET}")
                        
                        # Create NUA based on discovery context
                        nua_characteristics = introduction_context.get('nua_characteristics', {})
                        suggested_occupation = nua_characteristics.get('occupation', 'Mysterious Figure')
                        
                        # Build context for NUA creation
                        nua_context = f"""
The user has been following {introduction_context['clue_type']} for {introduction_context['follow_count']} actions.
{introduction_context['narrative_hint']}

Suggested characteristics:
- Occupation: {suggested_occupation}
- Initial state: {nua_characteristics.get('initial_state', 'unaware')}
- Context: {', '.join(nua_characteristics.get('context_hints', []))}

Create a NUA that fits this discovery context."""
                        
                        # Create the NUA
                        from dynamic_actor_system import DynamicActorSystem
                        dynamic_system = DynamicActorSystem(scene_creator)
                        new_nua = dynamic_system.creator.create_dynamic_actor(
                            {'name': suggested_occupation, 'context': nua_context, 'type': 'NUA'},
                            scene_description
                        )
                        
                        if new_nua:
                            # Register NUA for persistence and add to available NPCs
                            register_nua(new_nua, available_npcs)
                            
                            # Display NUA introduction with first impression (outlier)
                            try:
                                from nua_introduction_system import display_llm_nua_introduction, USE_LLM_FOR_INTRODUCTIONS
                                if USE_LLM_FOR_INTRODUCTIONS:
                                    display_llm_nua_introduction(new_nua, "through investigation", narrator)
                                else:
                                    from nua_introduction_system import display_nua_introduction
                                    display_nua_introduction(new_nua, "through investigation")
                            except Exception as e:
                                # Fallback to simple message
                                print(f"{Color.SUCCESS}✓ Discovered through investigation: {new_nua.sheet.name}{Color.RESET}")
                            
                            # Add to spatial map
                            try:
                                from spatial_context_system import get_spatial_manager, Position
                                spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                nua_pos = Position(x=40.0, y=10.0)  # Place near player
                                spatial.add_actor(new_nua.sheet.name, nua_pos)
                                print(f"{Color.SYSTEM}[SPATIAL] Added {new_nua.sheet.name} to map{Color.RESET}")
                            except Exception as e:
                                if not SUPPRESS_DEBUG:
                                    print(f"{Color.WARNING}[SPATIAL] Could not add NUA to map: {e}{Color.RESET}")
                            
                            # SAVE TO PERSISTENT CONTEXT (new NUA)
                            try:
                                context_manager.add_nua(new_nua.sheet.name, new_nua.sheet.occupation)
                            except Exception:
                                pass
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}[DISCOVERY] Progressive discovery check failed: {e}{Color.RESET}")
                
                # Prune NPCs that departed according to narrative
                try:
                    removed = _prune_npcs_by_outcome_text(available_npcs, [contextual_result])
                    if removed:
                        print(f"{Color.WARNING}👋 Non-User Actors left the scene: {', '.join(removed)}{Color.RESET}")
                        # SAVE TO PERSISTENT CONTEXT (NUAs removed)
                        for nua_name in removed:
                            context_manager.remove_nua(nua_name)
                except Exception:
                    pass
                # Auto-save after action
                try:
                    auto_save_counter += 1
                    if auto_save_counter >= auto_save_interval:
                        try:
                            if tracker is not None:
                                tracker.save_available_npcs(list(available_npcs or []))
                        except Exception:
                            pass
                        snapshot = {
                            'scene_number': scene_number,
                            'scene_description': scene_description,
                            'last_action': contextual_result,
                            'scene_updates': scene_updates[-3:],
                            'time_context': time_context,
                            'available_npc_names': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                            'actor_state': {
                                'name': actor.sheet.name,
                                'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()},
                                'current_task': actor.get_current_task_description() if hasattr(actor, 'get_current_task_description') else 'None',
                                'goals': actor.get_goals_summary() if hasattr(actor, 'get_goals_summary') else 'No goals'
                            }
                        }
                        req = save_coordinator.create_regular_auto_save_request(snapshot)
                        save_coordinator.request_save(req)
                        auto_save_counter = 0
                except Exception:
                    pass
                # Save contextual narrative for continuity (must happen before continue)
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.EXPLORATION,
                    narrative_text=f"Scene {scene_number}: {actor.sheet.name} {success_narration} → {contextual_result}",
                    actors_involved=[actor.sheet.name],
                    importance=NarrativeImportance.NOTABLE,
                    emotional_tone="exploratory",
                    scene_context=scene_description  # Preserve actual scene/spatial context
                )
                # Execute post-user turns (lower initiative NPCs) before continuing
                execute_post_user_turns_if_roam()
                # Avoid a second prompt in the same loop iteration
                continue
                    
        
        # Continue with encounter processing if in encounter mode and systems initialized
        if (current_mode == SimulationMode.ENCOUNTER and 
            hasattr(encounter_checker.current_context, 'systems_initialized') and 
            encounter_checker.current_context.systems_initialized):
            
            # Initialize contested exchange system
            from exchange_system import Exchange
            
            print(f"\n{Color.INFO}🎯 CONTESTED ACTION ATTEMPTED{Color.RESET}")
            print(f"═══════════════════════════════════════════════════════════════")
            print(f"{Color.INFO}⚔️ CONTESTED ACTION DETECTED{Color.RESET}")
            
            # Start contested exchange loop using multi-actor system
            exchange_in_progress = True
            turn_number = 1
            # Tracker integration: record contested exchanges for save/resume
            _tracker_exchange_started = False
            _tracker_current_turn_started = False
            _tracker_turn_reactor_fallback = None
            _tracker_last_exchange_winner = None
            _tracker_last_exchange_final_state = 'resolved'
            # Scene evaluation state (persists through the encounter)
            encounter_eval = {
                'consecutive_stalemates': 0,
                'dominance_streak_actor': None,
                'dominance_streak': 0,
                'turn_shifts_this_round': 0,
                'rounds_without_effect': 0
            }
            # Track last exchange for NUA proaction continuity
            last_exchange_context = None
            
            # Create initial turn queue with initiative for all actors (only top 4 act per turn order)
            # Use start_round() so recovery and round tracking are applied
            turn_queue_data = encounter_checker.current_context.round_manager.start_round()
            turn_queue = turn_queue_data.get('turn_queue', [])
            
            # Tracker: start exchange + round
            try:
                # Start exchange once per ENCOUNTER entry
                if tracker and not _tracker_exchange_started:
                    current_scene = None
                    try:
                        if hasattr(tracker, '_get_current_scene'):
                            current_scene = tracker._get_current_scene()
                    except Exception:
                        current_scene = None
                    exchange_number = 1
                    try:
                        if current_scene and isinstance(current_scene.get('exchanges'), list):
                            exchange_number = len(current_scene.get('exchanges') or []) + 1
                    except Exception:
                        exchange_number = 1
                    participants = []
                    try:
                        parts = getattr(encounter_checker.current_context, 'participants', []) or []
                        # Ensure UA is present
                        if actor and actor not in parts:
                            parts = [actor] + list(parts)
                        for p in parts:
                            try:
                                if p and getattr(getattr(p, 'sheet', None), 'name', None):
                                    participants.append(tracker.make_actor_id(p.sheet.name))
                            except Exception:
                                continue
                    except Exception:
                        participants = []
                    if actor and hasattr(getattr(actor, 'sheet', None), 'name'):
                        ua_id = tracker.make_actor_id(actor.sheet.name)
                        if ua_id not in participants:
                            participants.insert(0, ua_id)
                    tracker.start_exchange(exchange_number=exchange_number, participants=participants)
                    _tracker_exchange_started = True
            except Exception:
                pass
            try:
                if tracker and _tracker_exchange_started:
                    rm = encounter_checker.current_context.round_manager
                    tracker.start_round(round_number=getattr(rm, 'round_number', 1), initiative_data=turn_queue_data)
            except Exception:
                pass
            
            # CRITICAL: On Round 1, the encounter initiator (User Actor) ALWAYS goes first
            # This overrides initiative for the first round only
            if encounter_checker.current_context.round_manager.round_number == 1:
                # Find the User Actor in the turn queue
                ua_index = None
                for i, entry in enumerate(turn_queue):
                    if entry['actor'].is_user_actor:
                        ua_index = i
                        break
                
                # If UA is not first, move them to the front
                if ua_index is not None and ua_index > 0:
                    ua_entry = turn_queue.pop(ua_index)
                    turn_queue.insert(0, ua_entry)
                    print(f"{Color.SYSTEM}[ROUND 1 OVERRIDE] User Actor goes first (initiated encounter){Color.RESET}")
                    
                    # Update the turn queue in the data structure
                    turn_queue_data['turn_queue'] = turn_queue
            
            # Display banner and report the turn queue
            try:
                print(f"{Color.INFO}📣 New Turn Order Rolled (Round {encounter_checker.current_context.round_manager.round_number}){Color.RESET}")
            except Exception:
                print(f"{Color.INFO}📣 New Turn Order Rolled{Color.RESET}")
            # Enable enhanced queue display options
            try:
                turn_queue_data['label_roles_in_queue'] = True
                turn_queue_data['use_primary_reactor_label'] = True
                turn_queue_data['show_initiative_breakdown'] = True
            except Exception:
                pass
            encounter_checker.current_context.reporter.report_turn_queue_results(turn_queue_data)

            # No-progress guard (only for non-UA proactors)
            _np_last_token = None
            _np_same_count = 0

            while exchange_in_progress:
                print(f"\n{Color.SYSTEM}═══ TURN {turn_number} ═══{Color.RESET}")
                _tracker_current_turn_started = False
                _tracker_turn_reactor_fallback = None
                
                # Get current proactor from turn queue system (max 4 actors act per turn order)
                rm = encounter_checker.current_context.round_manager
                
                # Check if this is a grouped NUA turn
                is_grouped_turn = rm.is_current_turn_grouped()
                if is_grouped_turn:
                    group_members = rm.get_current_group_members()
                    print(f"\n{Color.WARNING}🎯 GROUPED NPC TURN: {len(group_members)} NPCs act together{Color.RESET}")
                    for npc in group_members:
                        print(f"  • {npc.sheet.name}")
                    print()
                
                proactor = rm.get_current_proactor()

                # BRANCH SELECTION DEBUG: which path will be taken this turn
                try:
                    _dbg_is_ua = getattr(proactor, "is_user_actor", False)
                    _dbg_is_inanim = getattr(proactor, "is_inanimate", False)
                    _dbg_name = getattr(getattr(proactor, "sheet", None), "name", "Unknown")
                    _dbg_group = " (GROUPED)" if is_grouped_turn else ""
                    print(f"{Color.SYSTEM}BRANCH DEBUG: proactor={_dbg_name}{_dbg_group} is_user_actor={_dbg_is_ua} is_inanimate={_dbg_is_inanim}{Color.RESET}")
                    _dbg_branch = "UA input loop" if _dbg_is_ua else ("INUA branch" if _dbg_is_inanim else f"NUA proactor chain{_dbg_group}")
                    print(f"{Color.SYSTEM}BRANCH CHOICE: {_dbg_branch}{Color.RESET}")
                except Exception:
                    pass

                # No-progress detection: skip when UA is about to enter input loop
                try:
                    token = (rm.round_number, getattr(rm, 'turn_queue_position', -1), getattr(proactor.sheet, 'name', 'Unknown'))
                    if getattr(proactor, 'is_user_actor', False):
                        _np_last_token = None
                        _np_same_count = 0
                    else:
                        if token == _np_last_token:
                            _np_same_count += 1
                            if _np_same_count > 3:
                                print(f"{Color.WARNING}⚠ Detected no progress in turn loop; auto-advancing queue...{Color.RESET}")
                                try:
                                    _ = rm.advance_turn_queue()
                                except Exception:
                                    pass
                                _np_last_token = None
                                _np_same_count = 0
                                # Continue to refresh proactor and header
                                continue
                        else:
                            _np_last_token = token
                            _np_same_count = 1
                except Exception:
                    pass
                
                print(f"{Color.SYSTEM}Current Proactor: {proactor.sheet.name}{Color.RESET}")
                # BRANCH SELECTION DEBUG (redundant): ensure visibility immediately after Current Proactor line
                try:
                    _dbg_is_ua = getattr(proactor, "is_user_actor", False)
                    _dbg_is_inanim = getattr(proactor, "is_inanimate", False)
                    _dbg_name = getattr(getattr(proactor, "sheet", None), "name", "Unknown")
                    print(f"{Color.SYSTEM}BRANCH DEBUG (post-proactor): proactor={_dbg_name} is_user_actor={_dbg_is_ua} is_inanimate={_dbg_is_inanim}{Color.RESET}")
                    _dbg_branch = "UA input loop" if _dbg_is_ua else ("INUA branch" if _dbg_is_inanim else "NUA proactor chain")
                    print(f"{Color.SYSTEM}BRANCH CHOICE (post-proactor): {_dbg_branch}{Color.RESET}")
                except Exception:
                    pass
                print(f"{Color.SYSTEM}Turn Queue Position: {encounter_checker.current_context.round_manager.turn_queue_position + 1}/{min(4, len(turn_queue))}{Color.RESET}")
                try:
                    print(f"{Color.SYSTEM}DEBUG: After header; proceeding to action selection...{Color.RESET}")
                except Exception:
                    pass
                
                # Determine reactor dynamically based on proactor's target or use fallback
                reactor = None
                if proactor.is_user_actor:
                    reactor = None  # Will be determined by target detection
                else:
                    # For NPC proactors, use next actor in queue as fallback
                    reactor_position = (encounter_checker.current_context.round_manager.turn_queue_position + 1) % len(turn_queue)
                    reactor = turn_queue[reactor_position]['actor']
                
                # Tracker: start turn (use fallback reactor if unknown yet)
                try:
                    if tracker and _tracker_exchange_started and not _tracker_current_turn_started:
                        _tracker_turn_reactor_fallback = reactor
                        if _tracker_turn_reactor_fallback is None:
                            try:
                                if len(turn_queue) > 1:
                                    _tracker_turn_reactor_fallback = turn_queue[1].get('actor')
                            except Exception:
                                _tracker_turn_reactor_fallback = None
                        if _tracker_turn_reactor_fallback is None:
                            _tracker_turn_reactor_fallback = proactor
                        tracker.start_turn(turn_number=turn_number, proactor=proactor, reactor=_tracker_turn_reactor_fallback)
                        _tracker_current_turn_started = True
                except Exception:
                    pass
                try:
                    rn = getattr(getattr(reactor, 'sheet', None), 'name', 'None') if reactor else 'None'
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.SYSTEM}DEBUG: Reactor preview set to: {rn}{Color.RESET}")
                except Exception:
                    pass
                
                # Get proactor action with full calculation display
                proactor_action_data = None
                user_input = None
                # Lightweight timing buckets (ms)
                nua_proaction_ms = 0
                nua_reaction_ms = 0
                exchange_ms = 0
                reporting_ms = 0
                # NUA FAST-PATH: handle NUA proactor immediately to avoid getting stuck before later branches
                if not getattr(proactor, 'is_user_actor', False):
                    try:
                        print(f"{Color.SYSTEM}DEBUG: NUA FAST-PATH ENTER{Color.RESET}")
                    except Exception:
                        pass
                    
                    # GROUPED NUA HANDLING: Process all NPCs in the group
                    if is_grouped_turn:
                        group_members = rm.get_current_group_members()
                        print(f"\n{Color.INFO}Processing grouped NPC actions...{Color.RESET}")
                        
                        # Determine reactor for the group
                        try:
                            if reactor is None:
                                reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                                reactor = turn_queue[reactor_position]['actor']
                        except Exception:
                            pass
                        
                        # Get actions and calculate success for each group member
                        group_results = []
                        for group_npc in group_members:
                            print(f"\n{Color.SYSTEM}→ {_ua_display_name(group_npc, ua_actor=actor)}'s action in group{Color.RESET}")
                            
                            try:
                                # Get action for this group member with group context
                                group_action_data = conductor.determine_nua_proaction(
                                    proactor=group_npc,
                                    reactor=reactor,
                                    context_guidance=context_guidance if 'context_guidance' in locals() else None,
                                    group_members=group_members,
                                    last_exchange_context=last_exchange_context if 'last_exchange_context' in locals() else None
                                )
                                
                                if group_action_data and group_action_data.get('narrative_description'):
                                    print(f"  {_ua_display_name(group_npc, ua_actor=actor)}: {group_action_data['narrative_description']}")
                                    
                                    # Calculate success for this NPC
                                    proactor_success = _calculate_detailed_success(
                                        actor=group_npc,
                                        action_data=group_action_data,
                                        target_actor=reactor
                                    )
                                    
                                    group_results.append({
                                        'npc': group_npc,
                                        'action': group_action_data,
                                        'success': proactor_success
                                    })
                                else:
                                    print(f"  {Color.WARNING}No action generated for {_ua_display_name(group_npc, ua_actor=actor)}{Color.RESET}")
                            except Exception as e:
                                print(f"  {Color.WARNING}Error getting action for {_ua_display_name(group_npc, ua_actor=actor)}: {e}{Color.RESET}")
                        
                        # If we got valid actions, process the grouped exchange
                        if group_results:
                            # Calculate overwhelm penalty for reactor
                            overwhelm_penalty = (len(group_members) - 1) * 2
                            print(f"\n{Color.WARNING}⚠️ Reactor faces OVERWHELM PENALTY: +{overwhelm_penalty} stress{Color.RESET}")
                            
                            # Get reactor's defense action
                            try:
                                reactor_action_data = conductor.determine_nua_reaction(
                                    reactor=reactor,
                                    proactor=group_members[0],
                                    proactor_action_data=group_results[0]['action']
                                )
                            except Exception as e:
                                print(f"{Color.WARNING}Error getting reactor action: {e}{Color.RESET}")
                                reactor_action_data = None
                            
                            # Calculate reactor's defense with overwhelm penalty
                            if reactor_action_data:
                                reactor_success = _calculate_detailed_success(
                                    actor=reactor,
                                    action_data=reactor_action_data,
                                    target_actor=group_members[0],
                                    additional_stress=overwhelm_penalty
                                )
                            else:
                                # Fallback: use base defense with overwhelm
                                reactor_success = 0 - overwhelm_penalty
                            
                            print(f"\n{Color.INFO}Reactor Defense: {reactor_success:+d} (with overwhelm penalty){Color.RESET}")
                            
                            # Determine outcomes and apply shifts
                            for result in group_results:
                                outcome = result['success'] - reactor_success
                                
                                if outcome > 0:
                                    print(f"  ✓ {_ua_display_name(result['npc'], ua_actor=actor)}'s attack succeeds! ({result['success']:+d} vs {reactor_success:+d})")
                                    # Apply status shift to reactor
                                    try:
                                        shift_magnitude = result['action'].get('shift_magnitude', -2)
                                        status_to_shift = result['action'].get('status_to_shift', 'STAMINA')
                                        # Apply shift logic here
                                    except Exception as e:
                                        print(f"    {Color.WARNING}Error applying shift: {e}{Color.RESET}")
                                else:
                                    print(f"  ✗ {_ua_display_name(result['npc'], ua_actor=actor)}'s attack fails! ({result['success']:+d} vs {reactor_success:+d})")
                                
                                # ARCHITECT: Extract and apply movement from grouped NUA action
                                try:
                                    from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                                    npc_narrative = result['action'].get('narrative_description', '')
                                    if npc_narrative:
                                        movement_target = extract_movement_from_narrative(npc_narrative)
                                        if movement_target:
                                            if move_actor_on_map(result['npc'].sheet.name, movement_target, npc_narrative):
                                                print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {_ua_display_name(result['npc'], ua_actor=actor)} moved to '{movement_target}'")
                                except Exception:
                                    pass  # Movement is enhancement, not critical
                            
                            # Generate cohesive group narrative
                            try:
                                group_narrative = narrator.generate_grouped_action_narrative(
                                    group_results=group_results,
                                    reactor=reactor,
                                    reactor_success=reactor_success,
                                    reactor_action_data=reactor_action_data,
                                    time_context=master_time.get_current_time_context() if 'master_time' in locals() else None,
                                    framing_guidance=framing_guidance if 'framing_guidance' in locals() else None
                                )
                                
                                print(f"\n{Color.NARRATIVE}📖 {group_narrative}{Color.RESET}")
                            except Exception as e:
                                print(f"\n{Color.WARNING}Error generating group narrative: {e}{Color.RESET}")
                        
                        # After processing all group members, advance turn and continue
                        try:
                            _ = rm.advance_turn_queue()
                        except Exception:
                            pass
                        continue
                    
                    # SINGLE NUA: Normal processing
                    # Ensure reactor exists
                    try:
                        if reactor is None:
                            rm = encounter_checker.current_context.round_manager
                            reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                            reactor = turn_queue[reactor_position]['actor']
                    except Exception:
                        reactor = reactor
                    # Build minimal guidance (reuse later richer context if available)
                    try:
                        context_snapshot = _compose_scene_snapshot(
                            scene_description=scene_description,
                            time_context=master_time.get_current_time_context(),
                            last_action_narrative=last_action_narrative,
                            scene_updates=scene_updates,
                        )
                    except Exception:
                        context_snapshot = None
                    try:
                        pro_nua_ctx = nua_context_manager.get_or_create_context(getattr(proactor.sheet, 'name', 'NPC'))
                        g = pro_nua_ctx.get_nua_response_guidance()
                        try:
                            history = pro_nua_ctx.get_turn_history_summary()
                        except Exception:
                            history = ''
                        try:
                            loop_state = narrator.get_narrative_loop_state() or {}
                        except Exception:
                            loop_state = {}
                        context_guidance = {
                            'escalation_level': g.get('escalation_level', 2),
                            'recommended_action_type': g.get('recommended_action_type', 'social_response'),
                            'response_intensity': g.get('response_intensity', 1),
                            'context_summary': _clamp_text((g.get('context_summary') or '') + (f"\nHistory: {history}" if history else '')),
                            'narrative_mode': loop_state.get('mode'),
                            'narrative_tone': loop_state.get('tone'),
                            'narrative_intent': loop_state.get('intent'),
                        }
                    except Exception:
                        context_guidance = {'context_summary': context_snapshot or ''}
                    
                    # CRITICAL: Add remote encounter context if this is a phone call (FAST PATH)
                    try:
                        has_remote_flag = hasattr(encounter_checker.current_context, 'is_remote_encounter')
                        is_remote_value = getattr(encounter_checker.current_context, 'is_remote_encounter', False) if has_remote_flag else False
                        print(f"{Color.SYSTEM}[REMOTE DEBUG FAST PATH] has_remote_encounter flag: {has_remote_flag}, value: {is_remote_value}{Color.RESET}")
                        
                        if hasattr(encounter_checker.current_context, 'is_remote_encounter') and encounter_checker.current_context.is_remote_encounter:
                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', 'phone_call')
                            remote_desc = getattr(encounter_checker.current_context, 'remote_encounter_description', 'Remote conversation')
                            print(f"{Color.SUCCESS}[REMOTE DEBUG FAST PATH] Phone call context ACTIVE - adding to guidance{Color.RESET}")
                            
                            if isinstance(context_guidance, dict):
                                context_guidance['is_remote_encounter'] = True
                                context_guidance['remote_encounter_type'] = remote_type
                                context_guidance['remote_constraint'] = (
                                    f"CRITICAL CONSTRAINT: This is a {remote_type.upper().replace('_', ' ')}. "
                                    f"The actors are NOT physically present with each other. "
                                    f"Actions MUST be limited to what can be done over the phone: "
                                    f"speaking, listening, asking questions, sharing information, making plans, ending the call. "
                                    f"FORBIDDEN: Any physical actions like 'approaches', 'walks to', 'touches', 'hands over', etc. "
                                    f"Context: {remote_desc}"
                                )
                                context_guidance['context_summary'] = (
                                    f"[PHONE CALL - NO PHYSICAL PRESENCE]\n{context_guidance.get('context_summary', '')}"
                                )
                    except Exception as e:
                        print(f"{Color.WARNING}[REMOTE FAST PATH] Failed to add remote context: {e}{Color.RESET}")
                    
                    # Call Decider for NUA proaction
                    import time as time_module
                    _t0 = time_module.time()  # Initialize timing before try block
                    try:
                        try:
                            rm_dbg = encounter_checker.current_context.round_manager
                            qlen = len(getattr(rm_dbg, 'current_turn_queue', []) or [])
                            pos = getattr(rm_dbg, 'turn_queue_position', 0) + 1
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.SYSTEM}NUA PROACTOR CALL (FAST): proactor={getattr(proactor.sheet,'name','?')} reactor={getattr(getattr(reactor,'sheet',None),'name','?')} pos={pos}/{max(1, qlen)}{Color.RESET}")
                        except Exception:
                            pass
                        # DEBUG: Check if last_exchange_context exists
                        has_last_exchange = 'last_exchange_context' in locals() and last_exchange_context is not None
                        if has_last_exchange:
                            print(f"{Color.SUCCESS}[FAST PATH DEBUG] Passing last_exchange_context to proaction{Color.RESET}")
                            print(f"{Color.SYSTEM}[FAST PATH DEBUG] Last exchange summary: {last_exchange_context.get('proactor_name', '?')} -> {last_exchange_context.get('reactor_name', '?')}{Color.RESET}")
                        else:
                            print(f"{Color.WARNING}[FAST PATH DEBUG] NO last_exchange_context available!{Color.RESET}")
                        
                        proactor_action_data = conductor.determine_nua_proaction(
                            proactor=proactor,
                            reactor=reactor,
                            context_guidance=context_guidance,
                            last_exchange_context=last_exchange_context if has_last_exchange else None
                        ) or {}

                        # FAST-PATH preflight validation and bounded re-prompt (proactor)
                        try:
                            from response_normalizer import ResponseNormalizer
                            def _validate_or_reprompt_fast_proactor(data: dict, guidance):
                                attempts = 0
                                last_err = None
                                # Determine is_user_actor for sensory perspective
                                proactor_is_ua = getattr(proactor, 'is_user_actor', False)
                                for attempts in range(0, 2 + 1):
                                    try:
                                        _ = ResponseNormalizer.normalize_proactor_action_response(data, proactor.sheet.name, "takes action", proactor_is_ua)
                                        return data, attempts, None
                                    except Exception as ex:
                                        last_err = str(ex)
                                        if attempts >= 2:
                                            break
                                        fix_note = (
                                            "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory PROACTOR UTAS fields. "
                                            f"Error: {last_err}. Provide ONLY the missing fields; keep all other fields unchanged."
                                        )
                                        new_guidance = (guidance or '')
                                        try:
                                            # Append fix note if guidance is a dict-like
                                            if isinstance(new_guidance, dict):
                                                new_guidance = dict(new_guidance)
                                                new_guidance['repair_note'] = (new_guidance.get('repair_note') or '') + fix_note
                                            else:
                                                new_guidance = (new_guidance or '') + fix_note
                                        except Exception:
                                            pass
                                        try:
                                            data = conductor.determine_nua_proaction(
                                                proactor=proactor,
                                                reactor=reactor,
                                                context_guidance=new_guidance,
                                                last_exchange_context=last_exchange_context if 'last_exchange_context' in locals() else None
                                            ) or {}
                                        except Exception:
                                            break
                                return None, attempts, last_err or "Unknown validation error"

                            proactor_action_data, fast_p_attempts, fast_p_err = _validate_or_reprompt_fast_proactor(proactor_action_data, context_guidance if 'context_guidance' in locals() else None)
                        except Exception:
                            fast_p_attempts, fast_p_err = 0, None

                        # Ensure UTAS completeness for proactor (only if validation succeeded)
                        if proactor_action_data:
                            proactor_action_data = _ensure_min_utas_fields(proactor_action_data, proactor)
                        nua_proaction_ms = int((time_module.time() - _t0) * 1000)
                        try:
                            dbg_keys = list(proactor_action_data.keys()) if isinstance(proactor_action_data, dict) else []
                            dbg_has_narr = bool(proactor_action_data.get('narrative_description')) if isinstance(proactor_action_data, dict) else False
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.SYSTEM}DEBUG: Decider (FAST) result keys: {dbg_keys}{Color.RESET}")
                                print(f"{Color.SYSTEM}DEBUG: Decider (FAST) has narrative_description: {dbg_has_narr}{Color.RESET}")
                        except Exception:
                            pass
                    except Exception as e:
                        print(f"{Color.ERROR}NUA fast-path error: {e}{Color.RESET}")
                        proactor_action_data = {}
                    # If still no action, advance immediately to avoid stall
                    if not proactor_action_data or not proactor_action_data.get('narrative_description'):
                        try:
                            if fast_p_err:
                                print(f"{Color.WARNING}⚠ No NUA action generated (FAST) for {getattr(proactor.sheet,'name','NPC')} after re-prompts ({fast_p_attempts}). Reason: {fast_p_err}{Color.RESET}")
                            else:
                                print(f"{Color.WARNING}⚠ No NUA action generated (FAST) for {getattr(proactor.sheet,'name','NPC')}; advancing turn{Color.RESET}")
                        except Exception:
                            pass
                        try:
                            rm = encounter_checker.current_context.round_manager
                            _ = rm.advance_turn_queue()
                        except Exception:
                            pass
                        try:
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.SYSTEM}DEBUG: Skipping Steps 2-6 due to missing NUA proaction (FAST){Color.RESET}")
                        except Exception:
                            pass
                        continue
                    # Provide a safe raw input proxy for downstream reporting
                    user_input = (
                        proactor_action_data.get('raw_action')
                        or proactor_action_data.get('narrative_description')
                        or f"{getattr(proactor.sheet,'name','NPC')} acts."
                    )
                    try:
                        if not SUPPRESS_DEBUG:
                            print(f"{Color.SYSTEM}DEBUG: NUA FAST-PATH EXIT with action.{Color.RESET}")
                    except Exception:
                        pass

                    # Immediately run contested exchange (Steps 1–6) for NUA fast-path
                    try:
                        # Ensure a reactor exists (prefer UA if present, else next in queue)
                        if reactor is None:
                            try:
                                rm = encounter_checker.current_context.round_manager
                                detected = rm.find_reactor_by_target_detection(user_input, scene_description)
                                if detected:
                                    reactor = detected
                                else:
                                    reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                                    reactor = turn_queue[reactor_position]['actor']
                            except Exception:
                                # Last resort: first non-UA participant
                                try:
                                    parts = getattr(encounter_checker.current_context, 'participants', []) or []
                                    reactor = next((p for p in parts if not getattr(p, 'is_user_actor', False)), None)
                                except Exception:
                                    reactor = reactor

                        # REPORTER STEP 1: Proactor interpretation (NUA)
                        try:
                            proactor_for_report = dict(proactor_action_data)
                            proactor_for_report['name'] = proactor.sheet.name
                            proactor_for_report['is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            proactor_for_report['raw_input'] = proactor_action_data.get('raw_action', user_input or 'N/A')
                            encounter_checker.current_context.reporter.report_step1_proactor_interpretation(proactor_for_report)
                            try:
                                if (not getattr(proactor, 'is_user_actor', False)) and (not getattr(proactor, 'is_inanimate', False)):
                                    _display_actor_sheet_simple(proactor.sheet)
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}Step 1 (FAST) reporting error: {e}{Color.RESET}")

                        # ARCHITECT: Extract and apply movement from NUA proactor action (FAST path)
                        # NUAs may move as part of any action type (given, fallible, contested)
                        try:
                            from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                            proactor_narrative = proactor_action_data.get('narrative_description', '')
                            if proactor_narrative and not getattr(proactor, 'is_user_actor', False):
                                movement_target = extract_movement_from_narrative(proactor_narrative)
                                if movement_target:
                                    if move_actor_on_map(proactor.sheet.name, movement_target, proactor_narrative):
                                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {proactor.sheet.name} moved to '{movement_target}'")
                        except Exception:
                            pass  # Movement is enhancement, not critical

                        # Build reaction guidance only if reactor is NUA
                        try:
                            if not getattr(reactor, 'is_user_actor', False):
                                r_ctx = nua_context_manager.get_or_create_context(getattr(reactor.sheet, 'name', 'NPC'))
                                rg = r_ctx.get_nua_response_guidance()
                                try:
                                    r_hist = r_ctx.get_turn_history_summary()
                                except Exception:
                                    r_hist = ''
                                try:
                                    loop_state = narrator.get_narrative_loop_state() or {}
                                except Exception:
                                    loop_state = {}
                                reaction_guidance = {
                                    'escalation_level': rg.get('escalation_level', 2),
                                    'recommended_action_type': rg.get('recommended_action_type', 'social_response'),
                                    'response_intensity': rg.get('response_intensity', 1),
                                    'context_summary': _clamp_text((rg.get('context_summary') or '') + (f"\nHistory: {r_hist}" if r_hist else '')),
                                    'narrative_mode': loop_state.get('mode'),
                                    'narrative_tone': loop_state.get('tone'),
                                    'narrative_intent': loop_state.get('intent'),
                                }
                            else:
                                reaction_guidance = None
                        except Exception:
                            reaction_guidance = None

                        # Generate reactor action
                        try:
                            if getattr(reactor, 'is_user_actor', False):
                                # UA Reactor Prompt Mode: let the user enter their reaction
                                # First, show Step 2 (proactor's action narrative)
                                try:
                                    proactor_for_step2 = dict(proactor_action_data)
                                    proactor_for_step2['name'] = proactor.sheet.name
                                    proactor_for_step2['is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                                    proactor_for_step2['actor'] = proactor
                                    proactor_for_step2['reactor_actor'] = reactor
                                    proactor_for_step2['ua_actor'] = (proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None))
                                    proactor_for_step2['reactor_name'] = reactor.sheet.name
                                    proactor_for_step2['reactor_is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                                    proactor_for_step2['success_calculation'] = dict(proactor_success_data) if isinstance(proactor_success_data, dict) else {}
                                    proactor_for_step2['utas_factors'] = proactor_action_data.get('utas_factors', {})
                                    proactor_for_step2['attempt_narrative'] = (
                                        proactor_action_data.get('attempt_narrative')
                                        or proactor_action_data.get('narrative_description')
                                        or ''
                                    )
                                    encounter_checker.current_context.reporter.report_step2_proactor_success(proactor_for_step2)
                                except Exception as e:
                                    print(f"{Color.ERROR}Step 2 reporting error: {e}{Color.RESET}")
                                
                                # Then prompt for reactor response
                                try:
                                    print(f"{Color.INFO}🗣️ Your turn to REACT as {reactor.sheet.name}{Color.RESET}")
                                    print(f"{Color.INFO}⏳ Awaiting reactor response — Steps 3–6 will be generated after your input or when time expires.{Color.RESET}")
                                except Exception:
                                    pass
                                # Initialize per-turn reactor timer based on proactor action speed/context
                                try:
                                    reactor_time_manager = ReactorTimeManager()
                                    time_info = reactor_time_manager.calculate_time_budget(proactor_action_data)
                                    display_time_budget_info(time_info, show_details=True)
                                except Exception:
                                    reactor_time_manager = None
                                reactor_action_data = None
                                # Simple input loop with minimal quick commands
                                while not reactor_action_data:
                                    try:
                                        ua_react_input = _prompt_action_input(Color.PROMPT)
                                    except KeyboardInterrupt:
                                        # Treat Ctrl+C as running out of time to keep flow consistent
                                        print(f"{Color.WARNING}⏳ Reaction interrupted — treating as time expired.{Color.RESET}")
                                        reactor_action_data = {
                                            'narrative_description': "hesitates and fails to respond before the window closes",
                                            'utas_factors': {
                                                'status_to_shift': 'SPIRIT',
                                                's_trait_to_use': 'STURDINESS',
                                                'stress_level': 3,
                                                'shift_type': 'Temporary',
                                                'shift_polarity': 'Subtractive'
                                            },
                                            'success_calculation': {'total': 0},
                                            'time_expired': True
                                        }
                                        break
                                    if not isinstance(ua_react_input, str):
                                        continue
                                    ui_lower = ua_react_input.strip().lower()
                                    # Detect inquiry vs action (strict mode: use interpreter only, no heuristics)
                                    is_inquiry = False
                                    try:
                                        det = _strict_detect_inquiry_or_action(ua_react_input, actor, proactor, _retries=3)
                                        is_inquiry = bool(
                                            det and (
                                                det.get('input_type') == 'inquiry' or
                                                (det.get('input_type') == 'fallible_action' and det.get('fallible_subtype') in ['mental', 'inquiry'])
                                            )
                                        )
                                    except Exception:
                                        is_inquiry = False
                                    if ui_lower in ['look', 'l', 'examine scene', 'scan']:
                                        print(f"\n{Color.SCENE}🎬 FULL SCENE DESCRIPTION:{Color.RESET}")
                                        print(f"{Color.NARRATIVE}{scene_description}{Color.RESET}")
                                        # Consume minimal time for quick look
                                        try:
                                            if reactor_time_manager:
                                                reactor_time_manager.consume_inquiry_time('simple', ua_react_input)
                                                rem = reactor_time_manager.get_time_status()
                                                print(f"{Color.SYSTEM}⏱️ Time remaining: {rem['remaining']} (inquiries {rem['inquiries_made']}/{rem['max_inquiries']}){Color.RESET}")
                                                if not reactor_time_manager.has_time_remaining():
                                                    print(f"{Color.WARNING}⏳ Time expired while gathering info!{Color.RESET}")
                                                    reactor_action_data = {
                                                        'narrative_description': "hesitates and fails to respond before the window closes",
                                                        'utas_factors': {
                                                            'status_to_shift': 'SPIRIT',
                                                            's_trait_to_use': 'STURDINESS',
                                                            'stress_level': 3,
                                                            'shift_type': 'Temporary',
                                                            'shift_polarity': 'Subtractive'
                                                        },
                                                        'success_calculation': {'total': 0},
                                                        'time_expired': True
                                                    }
                                                    break
                                        except Exception:
                                            pass
                                        continue

                                    # Check for disengagement (User as Reactor)
                                    if _detect_disengage_intent(ua_react_input):
                                        enc_type = getattr(encounter_checker.current_context, 'encounter_type', 'general')
                                        # Check if PROACTOR (the NPC) allows disengagement
                                        escalation_value = 1
                                        try:
                                            nua_name = proactor.sheet.name
                                            if 'nua_context_manager' in locals():
                                                nua_ctx = nua_context_manager.get_or_create_context(nua_name)
                                                escalation_value = nua_ctx.escalation_level.value
                                        except Exception:
                                            pass
                                            
                                        allows = _nua_allows_disengage(proactor, enc_type, escalation_value)
                                        
                                        if allows:
                                            # Natural end
                                            try:
                                                rn = proactor.sheet.name
                                                print(f"{Color.NARRATIVE}{rn} nods, accepting your departure. The interaction ends naturally.{Color.RESET}")
                                                
                                                # Log outcome
                                                narrative_context_manager.add_narrative_event(
                                                    event_type=NarrativeEventType.ACTION_OUTCOME,
                                                    narrative_text=f"Scene {scene_number}: {reactor.sheet.name} ends the interaction; {rn} disengages.",
                                                    actors_involved=[reactor.sheet.name, rn],
                                                    importance=NarrativeImportance.ROUTINE,
                                                    emotional_tone="neutral",
                                                    scene_context=f"Scene {scene_number} natural disengagement ({enc_type})"
                                                )
                                            except Exception:
                                                pass
                                            
                                            exchange_in_progress = False
                                            reactor_action_data = {'DISENGAGE': True}
                                            break
                                        else:
                                            # Denied
                                            try:
                                                rn = proactor.sheet.name
                                                print(f"{Color.WARNING}{rn} prevents you from leaving — the situation is too tense.{Color.RESET}")
                                            except Exception:
                                                pass

                                    if ui_lower in ['ua', 'sheet']:
                                        print(f"\n{Color.INFO}📋 Your Character Sheet:{Color.RESET}")
                                        try:
                                            reactor.sheet.display_detailed()
                                        except Exception:
                                            pass
                                        # Consume minimal time for quick sheet glance
                                        try:
                                            if reactor_time_manager:
                                                reactor_time_manager.consume_inquiry_time('simple', ua_react_input)
                                                rem = reactor_time_manager.get_time_status()
                                                print(f"{Color.SYSTEM}⏱️ Time remaining: {rem['remaining']} (inquiries {rem['inquiries_made']}/{rem['max_inquiries']}){Color.RESET}")
                                                if not reactor_time_manager.has_time_remaining():
                                                    print(f"{Color.WARNING}⏳ Time expired while gathering info!{Color.RESET}")
                                                    reactor_action_data = {
                                                        'narrative_description': "hesitates and fails to respond before the window closes",
                                                        'utas_factors': {
                                                            'status_to_shift': 'SPIRIT',
                                                            's_trait_to_use': 'STURDINESS',
                                                            'stress_level': 3,
                                                            'shift_type': 'Temporary',
                                                            'shift_polarity': 'Subtractive'
                                                        },
                                                        'success_calculation': {'total': 0},
                                                        'time_expired': True
                                                    }
                                                    break
                                        except Exception:
                                            pass
                                        continue
                                    if ui_lower in ['npc', 'npcs', 'nua']:
                                        if available_npcs:
                                            print(f"\n{Color.INFO}👥 Non-User Actors in the area:{Color.RESET}")
                                            for n in available_npcs:
                                                try:
                                                    _display_actor_sheet_simple(n.sheet)
                                                except Exception:
                                                    print(f"  - {getattr(n.sheet, 'name', 'Unknown')}")
                                        else:
                                            print(f"{Color.INFO}No Non-User Actors are currently nearby.{Color.RESET}")
                                        # Consume minimal time for listing
                                        try:
                                            if reactor_time_manager:
                                                reactor_time_manager.consume_inquiry_time('simple', ua_react_input)
                                                rem = reactor_time_manager.get_time_status()
                                                print(f"{Color.SYSTEM}⏱️ Time remaining: {rem['remaining']} (inquiries {rem['inquiries_made']}/{rem['max_inquiries']}){Color.RESET}")
                                                if not reactor_time_manager.has_time_remaining():
                                                    print(f"{Color.WARNING}⏳ Time expired while gathering info!{Color.RESET}")
                                                    reactor_action_data = {
                                                        'narrative_description': "hesitates and fails to respond before the window closes",
                                                        'utas_factors': {
                                                            'status_to_shift': 'SPIRIT',
                                                            's_trait_to_use': 'STURDINESS',
                                                            'stress_level': 3,
                                                            'shift_type': 'Temporary',
                                                            'shift_polarity': 'Subtractive'
                                                        },
                                                        'success_calculation': {'total': 0},
                                                        'time_expired': True
                                                    }
                                                    break
                                        except Exception:
                                            pass
                                        continue
                                    # If it's an inquiry, answer and consume time
                                    if is_inquiry:
                                        try:
                                            resp = conductor.handle_inquiry(ua_react_input, proactor=reactor, reactor=proactor)
                                            if isinstance(resp, dict) and resp.get('narrative_response'):
                                                print(f"{Color.NARRATIVE}{resp.get('narrative_response')}{Color.RESET}")
                                        except Exception:
                                            pass
                                        try:
                                            if reactor_time_manager:
                                                complexity = reactor_time_manager.classify_inquiry_complexity(ua_react_input)
                                                reactor_time_manager.consume_inquiry_time(complexity, ua_react_input)
                                                rem = reactor_time_manager.get_time_status()
                                                print(f"{Color.SYSTEM}⏱️ Time remaining: {rem['remaining']} (inquiries {rem['inquiries_made']}/{rem['max_inquiries']}){Color.RESET}")
                                                if not reactor_time_manager.has_time_remaining():
                                                    print(f"{Color.WARNING}⏳ Time expired while asking questions!{Color.RESET}")
                                                    reactor_action_data = {
                                                        'narrative_description': "hesitates and fails to respond before the window closes",
                                                        'utas_factors': {
                                                            'status_to_shift': 'SPIRIT',
                                                            's_trait_to_use': 'STURDINESS',
                                                            'stress_level': 3,
                                                            'shift_type': 'Temporary',
                                                            'shift_polarity': 'Subtractive'
                                                        },
                                                        'success_calculation': {'total': 0},
                                                        'time_expired': True
                                                    }
                                                    break
                                        except Exception:
                                            pass
                                        continue
                                    # If no time remains, auto-fail before interpreting action
                                    try:
                                        if reactor_time_manager and not reactor_time_manager.has_time_remaining():
                                            print(f"{Color.WARNING}⏳ Time expired before you could react!{Color.RESET}")
                                            reactor_action_data = {
                                                'narrative_description': "hesitates and fails to respond before the window closes",
                                                'utas_factors': {
                                                    'status_to_shift': 'SPIRIT',
                                                    's_trait_to_use': 'STURDINESS',
                                                    'stress_level': 3,
                                                    'shift_type': 'Temporary',
                                                    'shift_polarity': 'Subtractive'
                                                },
                                                'success_calculation': {'total': 0},
                                                'time_expired': True
                                            }
                                            break
                                    except Exception:
                                        pass
                                    # Conversion helper: if input doesn't target an NUA, convert to contested action
                                    try:
                                        tgt = conductor.detect_target_type(ua_react_input, scene_description)
                                        is_nua_target = bool(tgt and str(tgt.get('target_type', '')).lower() == 'nua')
                                    except Exception:
                                        is_nua_target = False
                                    # FIX BUG #17: NEVER convert user actions - respect their exact intent
                                    # The conversion system was changing "I smile and nod" into "strategic move to lower guard"
                                    # This violates user agency and changes action meaning
                                    # Disabled conversion - user's action is their action, period.
                                    # if not is_nua_target:
                                    #     try:
                                    #         conv = conductor.convert_situation_to_contested_action(
                                    #             user_input=ua_react_input,
                                    #             reactor=reactor,
                                    #             proactor=proactor,
                                    #             scene_description=scene_description
                                    #         )
                                    #     except Exception as e:
                                    #         conv = None
                                    #     if conv and conv.get('converted_action'):
                                    #         try:
                                    #             print(f"{Color.INFO}↪ Converting your reaction into a contested maneuver against {proactor.sheet.name}:{Color.RESET}")
                                    #             if conv.get('bridge_narrative'):
                                    #                 print(f"{Color.NARRATIVE}{conv.get('bridge_narrative')}{Color.RESET}")
                                    #         except Exception:
                                    #             pass
                                    #         ua_react_input = conv.get('converted_action')
                                    # Interpret UA reactor input as a fallible contested action
                                    try:
                                        reactor_action_data = conductor.interpret_fallible_action(ua_react_input, reactor)
                                        # Ensure UTAS completeness for reactor
                                        reactor_action_data = _ensure_min_utas_fields(reactor_action_data, reactor)
                                        # CRITICAL USER AGENCY: Preserve the user's exact reactor action text.
                                        try:
                                            if isinstance(reactor_action_data, dict):
                                                # Preserve interpreter-cleaned text separately for reporting.
                                                try:
                                                    reactor_action_data['interpreted_user_action'] = (
                                                        reactor_action_data.get('interpreted_user_action')
                                                        or reactor_action_data.get('action_description')
                                                        or reactor_action_data.get('narrative_description')
                                                    )
                                                except Exception:
                                                    pass
                                                reactor_action_data['raw_user_action'] = ua_react_input
                                                reactor_action_data['action_description'] = ua_react_input
                                                reactor_action_data['narrative_description'] = ua_react_input
                                        except Exception:
                                            pass

                                        # UA perceptual attempt narration (paraphrase-only) for display.
                                        try:
                                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)
                                            if isinstance(reactor_action_data, dict) and 'narrator' in locals() and narrator:
                                                reactor_action_data['ua_attempt_text'] = narrator.generate_ua_action_perceptual_narrative(
                                                    user_input=ua_react_input,
                                                    scene_description=scene_description,
                                                    is_remote_encounter=is_remote,
                                                    remote_encounter_type=remote_type,
                                                    session_id=getattr(tracker, 'session_id', None) if tracker else None,
                                                )
                                        except Exception:
                                            pass
                                    except Exception as e:
                                        print(f"{Color.WARNING}⚠️ Could not interpret your reaction: {e}{Color.RESET}")
                                        reactor_action_data = None
                                # Debug keys
                                try:
                                    r_keys = list(reactor_action_data.keys()) if isinstance(reactor_action_data, dict) else []
                                    r_has_narr = bool(reactor_action_data.get('narrative_description')) if isinstance(reactor_action_data, dict) else False
                                    print(f"{Color.SYSTEM}DEBUG: Reactor (FAST, UA) result keys: {r_keys}{Color.RESET}")
                                    print(f"{Color.SYSTEM}DEBUG: Reactor (FAST, UA) has narrative_description: {r_has_narr}{Color.RESET}")
                                except Exception:
                                    pass
                            else:
                                # NUA/INUA Reactor handled by Decider
                                try:
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.SYSTEM}NUA REACTOR CALL (FAST): proactor={proactor.sheet.name} reactor={reactor.sheet.name}{Color.RESET}")
                                except Exception:
                                    pass
                                import time as time_module
                                _t1 = time_module.time()
                                reactor_action_data = conductor.determine_nua_reaction(
                                    proactor=proactor,
                                    proactor_action_data=proactor_action_data,
                                    reactor=reactor,
                                    context_guidance=reaction_guidance
                                ) or {}
                                # Ensure UTAS completeness for reactor
                                reactor_action_data = _ensure_min_utas_fields(reactor_action_data, reactor)
                                # Ensure Step 4 has a perceptual narrative for the reactor
                                try:
                                    if isinstance(reactor_action_data, dict):
                                        _existing_attempt = reactor_action_data.get('attempt_narrative') or reactor_action_data.get('narrative_description')
                                        if (not _existing_attempt or not str(_existing_attempt).strip()) and 'narrator' in locals() and narrator and not getattr(reactor, 'is_user_actor', False):
                                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)
                                            reactor_action_data['attempt_narrative'] = narrator.generate_nua_action_perceptual_narrative(
                                                actor=reactor,
                                                action_data=reactor_action_data,
                                                scene_description=scene_description,
                                                is_remote_encounter=is_remote,
                                                remote_encounter_type=remote_type,
                                                session_id=getattr(tracker, 'session_id', None) if tracker else None,
                                            )
                                except Exception:
                                    pass
                                nua_reaction_ms = int((time_module.time() - _t1) * 1000)
                                try:
                                    r_keys = list(reactor_action_data.keys()) if isinstance(reactor_action_data, dict) else []
                                    r_has_narr = bool(reactor_action_data.get('narrative_description')) if isinstance(reactor_action_data, dict) else False
                                    if not SUPPRESS_DEBUG:
                                        print(f"{Color.SYSTEM}DEBUG: Reactor (FAST) result keys: {r_keys}{Color.RESET}")
                                        print(f"{Color.SYSTEM}DEBUG: Reactor (FAST) has narrative_description: {r_has_narr}{Color.RESET}")
                                except Exception:
                                    pass
                        except Exception as e:
                            print(f"{Color.ERROR}NUA reaction generation error (FAST): {e}{Color.RESET}")
                            reactor_action_data = {}

                        # Check for special flow control actions (e.g., disengagement)
                        if reactor_action_data and reactor_action_data.get('DISENGAGE'):
                            continue

                        # Preflight validation + bounded re-prompt (no defaults, symmetric)
                        from response_normalizer import ResponseNormalizer
                        def _validate_or_reprompt(role: str, data: dict, guidance: str, max_retries: int = 2):
                            attempts = 0
                            last_err = None
                            # Determine is_user_actor for sensory perspective
                            proactor_is_ua = getattr(proactor, 'is_user_actor', False)
                            reactor_is_ua = getattr(reactor, 'is_user_actor', False)
                            for attempts in range(0, max_retries + 1):
                                try:
                                    if role == 'proactor':
                                        _ = ResponseNormalizer.normalize_proactor_action_response(data, proactor.sheet.name, "takes action", proactor_is_ua)
                                    else:
                                        _ = ResponseNormalizer.normalize_reactor_response(data, reactor.sheet.name, "reacts defensively", reactor_is_ua)
                                    return data, attempts, None
                                except Exception as ex:
                                    last_err = str(ex)
                                    if attempts >= max_retries:
                                        break
                                    # Re-prompt interpreter with targeted repair note; keep choices unchanged
                                    if role == 'reactor':
                                        fix_note = (
                                            "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory REACTOR UTAS fields. "
                                            f"Error: {last_err}. Provide ONLY the missing fields; keep all previously provided fields unchanged. "
                                            "MANDATORY: Include 'shift_polarity' explicitly as 'Additive' or 'Subtractive' (no numbers, no blanks). "\
                                            "Also ensure 'status_to_shift' is one of SPIRIT, STAMINA, SUPPLY, SYMPATHY. "
                                            "Use this minimal schema for the missing fields (exact key names, JSON only):\n"
                                            "{\n  \"action_description\": \"...\",\n  \"narrative_description\": \"...\",\n  \"utas_factors\": {\n    \"s_trait_to_use\": \"STURDINESS\",\n    \"skill\": \"Customer Service\",\n    \"endowment\": null,\n    \"supplement_val\": 0,\n    \"status_to_shift\": \"SPIRIT\",\n    \"shift_polarity\": \"Additive\",\n    \"stress_level\": 1,\n    \"has_secondary_effect\": false\n  }\n}"
                                        )
                                    else:
                                        fix_note = (
                                            "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory UTAS fields. "
                                            f"Error: {last_err}. Provide ONLY the missing fields, keep all previously provided fields unchanged."
                                        )
                                    new_guidance = (guidance or '') + fix_note
                                    try:
                                        if role == 'proactor':
                                            data = conductor.determine_nua_proaction(
                                                proactor=proactor,
                                                reactor=reactor,
                                                context_guidance=new_guidance,
                                                last_exchange_context=last_exchange_context if 'last_exchange_context' in locals() else None
                                            ) or {}
                                        else:
                                            data = conductor.determine_nua_reaction(
                                                proactor=proactor,
                                                reactor=reactor,
                                                context_guidance=new_guidance
                                            ) or {}
                                    except Exception as _:
                                        # If re-prompt fails hard, break out and abort
                                        break
                            return None, attempts, last_err or "Unknown validation error"

                        # Validate Proactor and Reactor symmetrically
                        p_valid, p_attempts, p_err = _validate_or_reprompt('proactor', proactor_action_data, (context_guidance if 'context_guidance' in locals() else None))
                        r_valid, r_attempts, r_err = _validate_or_reprompt(
                            'reactor',
                            reactor_action_data,
                            (reaction_guidance if 'reaction_guidance' in locals() else (context_guidance if 'context_guidance' in locals() else None))
                        )

                        if p_valid is None or r_valid is None:
                            # Abort this exchange, surface clear reason, do not proceed to mechanics
                            exchange_ms = 0
                            result = {
                                'proactor_results': {},
                                'reactor_results': {},
                                'outcome_results': {
                                    'exchange_aborted': True,
                                    'abort_reason': (
                                        (f"Proactor invalid: {p_err}. " if p_valid is None else "") +
                                        (f"Reactor invalid: {r_err}." if r_valid is None else "")
                                    ).strip(),
                                    're_prompt_attempts': {
                                        'proactor': p_attempts if p_valid is None else p_attempts,
                                        'reactor': r_attempts if r_valid is None else r_attempts
                                    },
                                    'status_shifts': [],
                                    'applied_self_effects': []
                                }
                            }
                        else:
                            # Use validated (potentially repaired) payloads going into Exchange
                            proactor_action_data = p_valid
                            reactor_action_data = r_valid
                            # Execute exchange
                            try:
                                from exchange_system import Exchange
                                import time as time_module
                                _t2 = time_module.time()
                                exch = Exchange(
                                    proactor=proactor,
                                    reactor=reactor,
                                    proactor_action_data=proactor_action_data,
                                    reactor_action_data=reactor_action_data,
                                    recovery_integrator=encounter_checker.current_context.enhanced_recovery
                                )
                                result = exch.execute(is_inua_exchange=getattr(reactor, 'is_inanimate', False))
                                exchange_ms = int((time_module.time() - _t2) * 1000)
                                
                                # Process witness reactions to the exchange
                                witnesses = [npc for npc in available_npcs if npc != proactor and npc != reactor]
                                if witnesses:
                                    witness_reactions = exch.process_witness_reactions(witnesses, scene_description, result)
                                    # Display witness reactions to show simulation effect
                                    if witness_reactions and _witness_system:
                                        _witness_system.display_witness_reactions(witness_reactions)
                                    # Handle behavioral changes from reactions
                                    for reaction in witness_reactions:
                                        if reaction['behavioral_change'] == 'leave_scene':
                                            witness = next((w for w in witnesses if w.sheet.name == reaction['witness']), None)
                                            if witness and witness in available_npcs:
                                                available_npcs.remove(witness)
                                                continuity_validator.mark_npc_departed(witness.sheet.name)
                                
                            except Exception as e:
                                print(f"{Color.ERROR}Exchange execution error (FAST): {e}{Color.RESET}")
                                import traceback as traceback_module
                                traceback_module.print_exc()
                                # Advance to avoid stall
                                try:
                                    rm = encounter_checker.current_context.round_manager
                                    _ = rm.advance_turn_queue()
                                except Exception:
                                    pass
                                continue

                        # Extract results
                        proactor_success_data = result.get('proactor_results', {})
                        reactor_success_data = result.get('reactor_results', {})
                        exchange_outcome = result.get('outcome_results', {})
                        
                        # Process monetary transaction if detected (after exchange resolution)
                        # Transaction narrative will be appended to Step 6 narrative
                        transaction_narrative = ""
                        if monetary_data.get("transaction_detected"):
                            try:
                                # Determine if proactor succeeded
                                proactor_total = proactor_success_data.get('total', 0)
                                reactor_total = reactor_success_data.get('total', 0)
                                proactor_succeeded = proactor_total > reactor_total
                                
                                # Get targeted status to avoid duplicate sympathy shifts
                                targeted_status = proactor_action_data.get('utas_factors', {}).get('status_to_shift')
                                
                                can_proceed, transaction_narrative, consequences = monetary_processor.process_enhanced_transaction(
                                    monetary_data=monetary_data,
                                    proactor=proactor,
                                    reactor=reactor,
                                    success=proactor_succeeded,
                                    targeted_status=targeted_status
                                )
                            except Exception as e:
                                print(f"{Color.ERROR}Transaction processing error: {e}{Color.RESET}")

                        # Reporter Steps 2–5
                        try:
                            import time as time_module
                            _t3 = time_module.time()
                            # Step 2
                            proactor_for_step2 = dict(proactor_action_data)
                            proactor_for_step2['name'] = proactor.sheet.name
                            proactor_for_step2['is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            proactor_for_step2['actor'] = proactor
                            proactor_for_step2['reactor_actor'] = reactor
                            proactor_for_step2['ua_actor'] = (proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None))
                            # Pass reactor info for UA pronoun conversion
                            proactor_for_step2['reactor_name'] = reactor.sheet.name
                            proactor_for_step2['reactor_is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            scalc = dict(proactor_success_data) if isinstance(proactor_success_data, dict) else {}
                            if 'total' not in scalc:
                                scalc['total'] = scalc.get('final_result', scalc.get('success', 0))
                            # Normalize component keys for EnhancedReporter fallback
                            # (Removed legacy defaults that injected zeros.)
                            # Normalize component keys for EnhancedReporter fallback (no defaults)
                            try:
                                uf = proactor_action_data.get('utas_factors', {}) if isinstance(proactor_action_data, dict) else {}
                                if 's_trait_value' not in scalc:
                                    if scalc.get('s_trait_val') is not None:
                                        scalc['s_trait_value'] = scalc.get('s_trait_val')
                                    elif uf.get('s_trait_value') is not None:
                                        scalc['s_trait_value'] = uf.get('s_trait_value')
                                if 'skill_value' not in scalc:
                                    if scalc.get('skill_val') is not None:
                                        scalc['skill_value'] = scalc.get('skill_val')
                                    else:
                                        sk = uf.get('skill')
                                        if isinstance(sk, dict) and sk.get('value') is not None:
                                            scalc['skill_value'] = sk.get('value')
                                if 'endowment_value' not in scalc:
                                    if scalc.get('endowment_val') is not None:
                                        scalc['endowment_value'] = scalc.get('endowment_val')
                                    else:
                                        sp = uf.get('endowment')
                                        if isinstance(sp, dict) and sp.get('value') is not None:
                                            scalc['endowment_value'] = sp.get('value')
                                if 'supplement_value' not in scalc:
                                    su = uf.get('supplement')
                                    if isinstance(su, dict) and su.get('value') is not None:
                                        scalc['supplement_value'] = su.get('value')
                            except Exception:
                                pass
                            proactor_for_step2['success_calculation'] = scalc
                            proactor_for_step2['utas_factors'] = proactor_action_data.get('utas_factors', {})
                            proactor_for_step2['attempt_narrative'] = (
                                proactor_action_data.get('attempt_narrative')
                                or proactor_action_data.get('narrative_description')
                                or ''
                            )
                            encounter_checker.current_context.reporter.report_step2_proactor_success(proactor_for_step2)

                            try:
                                ua_for_vis = proactor_for_step2.get('ua_actor')
                                if ua_for_vis is not None:
                                    _update_visualizer_context(
                                        ua_actor=ua_for_vis,
                                        scene_description=scene_description,
                                        current_location=str(current_location or ''),
                                        time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                        creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                        seed=None,
                                    )
                                    if _vis_autogen_enabled and _env_bool("VIS_VIDEO_ENABLED", False):
                                        _trigger_realtime_video(
                                            ua_actor=ua_for_vis,
                                            scene_description=scene_description,
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            spoken_line=str(proactor_action_data.get('narrative_description', '') or ''),
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                        )
                                    try:
                                        if _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                            _interval = 2
                                            try:
                                                _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                            except Exception:
                                                _interval = 2
                                            if _interval < 1:
                                                _interval = 1
                                            if (2 % _interval) == 0:
                                                _trigger_realtime_image(
                                                    ua_actor=ua_for_vis,
                                                    scene_description=scene_description,
                                                    current_location=str(current_location or ''),
                                                    time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                                    creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                                    seed=None,
                                                    spoken_line=str(proactor_action_data.get('narrative_description', '') or ''),
                                                    source="perceptual",
                                                    reason="exchange_step2",
                                                )
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                _capture_dialogue_continuity_facts(
                                    proactor_action_data.get('narrative_description', ''),
                                    speaker=proactor.sheet.name,
                                    source="exchange_step2_dialogue",
                                    base_confidence=0.65
                                )
                            except Exception:
                                pass
                            try:
                                _trace_continuity_fact_capture(
                                    proactor_action_data.get('narrative_description', ''),
                                    source="exchange_step2",
                                    base_confidence=0.70
                                )
                            except Exception:
                                pass
                            try:
                                _capture_mentioned_actors_from_text(
                                    proactor_action_data.get('narrative_description', ''),
                                    source="exchange_step2"
                                )
                            except Exception:
                                pass

                            # Step 3
                            proactor_summary = f"{proactor.sheet.name}: {proactor_action_data.get('narrative_description', 'Proactor attempted an action.')}"
                            reactor_for_report = dict(reactor_action_data)
                            reactor_for_report['name'] = reactor.sheet.name
                            reactor_for_report['is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            encounter_checker.current_context.reporter.report_step3_reactor_interpretation(reactor_for_report, proactor_summary)

                            # ARCHITECT: Extract and apply movement from reactor action (FAST path)
                            # Reactors (NUA/MNUA) may move as part of their reaction (dodge, retreat, approach)
                            try:
                                from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                                reactor_narrative = reactor_action_data.get('narrative_description', '')
                                if reactor_narrative and not getattr(reactor, 'is_user_actor', False):
                                    movement_target = extract_movement_from_narrative(reactor_narrative)
                                    if movement_target:
                                        if move_actor_on_map(reactor.sheet.name, movement_target, reactor_narrative):
                                            print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {reactor.sheet.name} moved to '{movement_target}'")
                            except Exception:
                                pass  # Movement is enhancement, not critical

                            # Step 4
                            reactor_for_step4 = dict(reactor_action_data)
                            reactor_for_step4['name'] = reactor.sheet.name
                            reactor_for_step4['is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            reactor_for_step4['actor'] = reactor
                            reactor_for_step4['ua_actor'] = (proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None))
                            # Pass proactor info for UA pronoun conversion
                            reactor_for_step4['proactor_name'] = proactor.sheet.name
                            reactor_for_step4['proactor_is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            rcalc = dict(reactor_success_data) if isinstance(reactor_success_data, dict) else {}
                            if 'total' not in rcalc:
                                rcalc['total'] = rcalc.get('final_result', rcalc.get('success', 0))
                            # Normalize component keys for EnhancedReporter fallback (reactor; no defaults)
                            try:
                                uf_r = reactor_action_data.get('utas_factors', {}) if isinstance(reactor_action_data, dict) else {}
                                if 's_trait_value' not in rcalc:
                                    if rcalc.get('s_trait_val') is not None:
                                        rcalc['s_trait_value'] = rcalc.get('s_trait_val')
                                    elif uf_r.get('s_trait_value') is not None:
                                        rcalc['s_trait_value'] = uf_r.get('s_trait_value')
                                if 'skill_value' not in rcalc:
                                    if rcalc.get('skill_val') is not None:
                                        rcalc['skill_value'] = rcalc.get('skill_val')
                                    else:
                                        sk_r = uf_r.get('skill')
                                        if isinstance(sk_r, dict) and sk_r.get('value') is not None:
                                            rcalc['skill_value'] = sk_r.get('value')
                                if 'endowment_value' not in rcalc:
                                    if rcalc.get('endowment_val') is not None:
                                        rcalc['endowment_value'] = rcalc.get('endowment_val')
                                    else:
                                        sp_r = uf_r.get('endowment')
                                        if isinstance(sp_r, dict) and sp_r.get('value') is not None:
                                            rcalc['endowment_value'] = sp_r.get('value')
                                if 'supplement_value' not in rcalc:
                                    su_r = uf_r.get('supplement')
                                    if isinstance(su_r, dict) and su_r.get('value') is not None:
                                        rcalc['supplement_value'] = su_r.get('value')
                            except Exception:
                                pass
                            # (Removed legacy defaults that injected zeros.)
                            reactor_for_step4['success_calculation'] = rcalc
                            reactor_for_step4['utas_factors'] = reactor_action_data.get('utas_factors', {})
                            reactor_for_step4['attempt_narrative'] = (
                                reactor_action_data.get('attempt_narrative')
                                or reactor_action_data.get('narrative_description')
                                or ''
                            )
                            encounter_checker.current_context.reporter.report_step4_reactor_success(reactor_for_step4)

                            try:
                                ua_for_vis = reactor_for_step4.get('ua_actor')
                                if ua_for_vis is not None:
                                    _update_visualizer_context(
                                        ua_actor=ua_for_vis,
                                        scene_description=scene_description,
                                        current_location=str(current_location or ''),
                                        time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                        creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                        seed=None,
                                    )
                                    if _env_bool("VIS_VIDEO_ENABLED", False):
                                        _trigger_realtime_video(
                                            ua_actor=ua_for_vis,
                                            scene_description=scene_description,
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            spoken_line=str(reactor_action_data.get('narrative_description', '') or ''),
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                        )
                                    try:
                                        if _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                            _interval = 2
                                            try:
                                                _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                            except Exception:
                                                _interval = 2
                                            if _interval < 1:
                                                _interval = 1
                                            if (4 % _interval) == 0:
                                                _trigger_realtime_image(
                                                    ua_actor=ua_for_vis,
                                                    scene_description=scene_description,
                                                    current_location=str(current_location or ''),
                                                    time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                                    creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                                    seed=None,
                                                    spoken_line=str(reactor_action_data.get('narrative_description', '') or ''),
                                                    source="perceptual",
                                                    reason="exchange_step4",
                                                )
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                _capture_dialogue_continuity_facts(
                                    reactor_action_data.get('narrative_description', ''),
                                    speaker=reactor.sheet.name,
                                    source="exchange_step4_dialogue",
                                    base_confidence=0.65
                                )
                            except Exception:
                                pass
                            try:
                                _trace_continuity_fact_capture(
                                    reactor_action_data.get('narrative_description', ''),
                                    source="exchange_step4",
                                    base_confidence=0.70
                                )
                            except Exception:
                                pass
                            try:
                                _capture_mentioned_actors_from_text(
                                    reactor_action_data.get('narrative_description', ''),
                                    source="exchange_step4"
                                )
                            except Exception:
                                pass

                            # Step 5
                            # FIX BUG #1: Get success values directly from exchange result
                            pro_total = result.get('proactor_success', scalc.get('total', 0))
                            rea_total = result.get('reactor_success', rcalc.get('total', 0))
                            outcome_for_reporter = {
                                'proactor_successes': pro_total,
                                'reactor_successes': rea_total,
                                'margin': (pro_total - rea_total),
                                'proactor_name': proactor.sheet.name,
                                'reactor_name': reactor.sheet.name,
                                'stress_context': exchange_outcome.get('stress_context', ''),
                                'shift_calc_formula': exchange_outcome.get('shift_calc_formula') or exchange_outcome.get('shift_calc', ''),
                                'status_shifts': exchange_outcome.get('status_shifts', []),
                                'applied_self_effects': exchange_outcome.get('applied_self_effects', []),
                            }
                            encounter_checker.current_context.reporter.report_step5_final_outcome(outcome_for_reporter)
                            # Conclude timing for reporting and print summary line
                            reporting_ms = int((time_module.time() - _t3) * 1000)
                            try:
                                print(f"{Color.SYSTEM}⏱️ Performance — Proaction: {nua_proaction_ms}ms | Reaction: {nua_reaction_ms}ms | Exchange: {exchange_ms}ms | Reporting: {reporting_ms}ms{Color.RESET}")
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}FAST reporter steps 2–5 error: {e}{Color.RESET}")

                        # Step 6
                        # FIX BUG #4: Initialize variables before try block to prevent NameError
                        step6_outcome_data = {}
                        final_narrative = ''
                        
                        try:
                            step6_outcome_data = outcome_for_reporter
                        except NameError:
                            # FIX BUG #1: Get success values directly from exchange result
                            step6_outcome_data = {
                                'proactor_successes': result.get('proactor_success', proactor_success_data.get('total', 0) if isinstance(proactor_success_data, dict) else 0),
                                'reactor_successes': result.get('reactor_success', reactor_success_data.get('total', 0) if isinstance(reactor_success_data, dict) else 0),
                                'status_shifts': exchange_outcome.get('status_shifts', []) if isinstance(exchange_outcome, dict) else []
                            }
                        try:
                            # Ensure names and UA flags are present for Step 6 narrative generation
                            pro_for_step6 = dict(proactor_action_data)
                            pro_for_step6.setdefault('name', getattr(getattr(proactor, 'sheet', None), 'name', ''))
                            pro_for_step6.setdefault('is_user_actor', getattr(proactor, 'is_user_actor', False))
                            pro_for_step6.setdefault('actor', proactor)
                            rea_for_step6 = dict(reactor_action_data)
                            rea_for_step6.setdefault('name', getattr(getattr(reactor, 'sheet', None), 'name', ''))
                            rea_for_step6.setdefault('is_user_actor', getattr(reactor, 'is_user_actor', False))
                            rea_for_step6.setdefault('actor', reactor)
                            # FIX BUG #9: Use current scene context for exchange narrative
                            # Pass remote encounter flags to prevent physical presence narratives during phone calls
                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)

                            ua_for_step6 = proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None)
                            
                            try:
                                from spatial_context_system import build_spatial_facts
                                _sf = build_spatial_facts(session_id=getattr(tracker, 'session_id', None) if tracker else None)
                                _scene_ctx = scene_description
                                if isinstance(_sf, str) and _sf.strip():
                                    _scene_ctx = f"{scene_description}\n\n{_sf.strip()}"
                            except Exception:
                                _scene_ctx = scene_description

                            final_narrative = encounter_checker.current_context.reporter.report_step6_narrative_outcome(
                                proactor_data=pro_for_step6,
                                reactor_data=rea_for_step6,
                                outcome_data=step6_outcome_data,
                                narrator_agent=narrator,
                                scene_context=_scene_ctx,
                                is_remote_encounter=is_remote,
                                remote_encounter_type=remote_type,
                                ua_actor=ua_for_step6
                            )

                            try:
                                if ua_for_step6 is not None:
                                    _update_visualizer_context(
                                        ua_actor=ua_for_step6,
                                        scene_description=_scene_ctx,
                                        current_location=str(current_location or ''),
                                        time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                        creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                        seed=None,
                                    )
                                    if _env_bool("VIS_VIDEO_ENABLED", False):
                                        _trigger_realtime_video(
                                            ua_actor=ua_for_step6,
                                            scene_description=_scene_ctx,
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            spoken_line=str(final_narrative or ''),
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                        )
                                    try:
                                        if _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                            _interval = 2
                                            try:
                                                _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                            except Exception:
                                                _interval = 2
                                            if _interval < 1:
                                                _interval = 1
                                            if (6 % _interval) == 0:
                                                _trigger_realtime_image(
                                                    ua_actor=ua_for_step6,
                                                    scene_description=_scene_ctx,
                                                    current_location=str(current_location or ''),
                                                    time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                                    creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                                    seed=None,
                                                    spoken_line=str(final_narrative or ''),
                                                    source="perceptual",
                                                    reason="exchange_step6",
                                                )
                                    except Exception:
                                        pass
                            except Exception:
                                pass
                            try:
                                _apply_narrative_item_gains_to_ua(final_narrative, ua_for_step6)
                            except Exception:
                                pass

                            # Continuity facts: capture stable anchors from exchange outcome narration
                            try:
                                _trace_continuity_fact_capture(final_narrative, source="exchange_step6", base_confidence=0.75)
                            except Exception:
                                pass

                            try:
                                _capture_mentioned_actors_from_text(final_narrative, source="exchange_step6")
                            except Exception:
                                pass

                            # Append transaction narrative if present
                            if transaction_narrative:
                                print(f"{Color.NARRATIVE}{transaction_narrative}{Color.RESET}")
                                try:
                                    _capture_continuity_facts_from_text(transaction_narrative, source="exchange_transaction", base_confidence=0.70)
                                except Exception:
                                    pass
                            
                            # STRANGER SYSTEM: Detect if any NPC introduced themselves in the narrative
                            if STRANGER_DESCRIPTION_AVAILABLE and detect_name_introduction and final_narrative:
                                try:
                                    learned = detect_name_introduction(final_narrative, available_npcs)
                                    if learned:
                                        print(f"{Color.SUCCESS}[NAME LEARNED] You now know: {', '.join(learned)}{Color.RESET}")
                                except Exception:
                                    pass

                            # Promote any mentioned world destinations from the exchange narration/dialogue.
                            try:
                                _promote_world_destinations_from_text(final_narrative, source='exchange_step6')
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}FAST Step 6 reporting error: {e}{Color.RESET}")
                            final_narrative = ''
                        
                        # Tracker: complete turn with narrative output
                        try:
                            if tracker and _tracker_exchange_started and _tracker_current_turn_started:
                                out_text = final_narrative or ''
                                try:
                                    if transaction_narrative:
                                        out_text = (out_text + "\n" + str(transaction_narrative)).strip()
                                except Exception:
                                    pass
                                tracker.complete_turn(
                                    proactor=proactor,
                                    reactor=(reactor if reactor is not None else (_tracker_turn_reactor_fallback if _tracker_turn_reactor_fallback is not None else proactor)),
                                    reporter_output=out_text
                                )
                        except Exception:
                            pass
                        
                        # ═══════════════════════════════════════════════════════════════════
                        # DIALOGUE TRACKING - Record exchange for conversation continuity
                        # This ensures NPCs remember what was said in previous turns
                        # ═══════════════════════════════════════════════════════════════════
                        try:
                            proactor_name = getattr(getattr(proactor, 'sheet', None), 'name', 'Unknown')
                            reactor_name = getattr(getattr(reactor, 'sheet', None), 'name', 'Unknown')
                            proactor_statement = proactor_action_data.get('narrative_description', '') if isinstance(proactor_action_data, dict) else ''
                            reactor_statement = reactor_action_data.get('narrative_description', '') if isinstance(reactor_action_data, dict) else ''
                            
                            # Determine statement type based on action
                            proactor_action_desc = proactor_action_data.get('action_description', '').lower() if isinstance(proactor_action_data, dict) else ''
                            statement_type = 'statement'
                            if any(word in proactor_action_desc for word in ['ask', 'question', 'inquire']):
                                statement_type = 'question'
                            elif any(word in proactor_action_desc for word in ['threaten', 'warn', 'intimidate']):
                                statement_type = 'threat'
                            elif any(word in proactor_action_desc for word in ['promise', 'swear', 'vow']):
                                statement_type = 'promise'
                            
                            # Track proactor's statement
                            if proactor_statement:
                                track_dialogue_exchange(proactor_name, reactor_name, proactor_statement, statement_type)
                            
                            # Track reactor's response
                            if reactor_statement:
                                track_dialogue_exchange(reactor_name, proactor_name, reactor_statement, 'statement')
                        except Exception:
                            pass  # Dialogue tracking is enhancement, not critical
                        
                        # Progressive Skill Revelation - Reveal skills/endowments used in this exchange
                        try:
                            from skill_revelation_system import auto_reveal_from_action_data, PROGRESSIVE_REVELATION_ENABLED
                            if PROGRESSIVE_REVELATION_ENABLED:
                                # Reveal proactor's abilities (only for NPCs)
                                if not getattr(proactor, 'is_user_actor', False):
                                    auto_reveal_from_action_data(proactor, proactor_action_data)
                                
                                # Reveal reactor's abilities (only for NPCs)
                                if not getattr(reactor, 'is_user_actor', False):
                                    auto_reveal_from_action_data(reactor, reactor_action_data)
                        except Exception as e:
                            # Silently fail - revelation is optional
                            pass

                        # Turn summary (optional)
                        # FIX BUG #4: Initialize variables before use to prevent NameError
                        if 'step6_outcome_data' not in locals():
                            step6_outcome_data = {}
                        if 'final_narrative' not in locals():
                            final_narrative = ''
                        
                        # Store last exchange context for next NUA proaction
                        try:
                            last_exchange_context = {
                                'proactor_name': proactor.sheet.name,
                                'reactor_name': reactor.sheet.name,
                                'proactor_action': proactor_action_data.get('narrative_description', 'acted'),
                                'reactor_action': reactor_action_data.get('narrative_description', 'reacted'),
                                'outcome_narrative': final_narrative,
                                'winner': exchange_outcome.get('winner', 'unknown') if isinstance(exchange_outcome, dict) else 'unknown',
                                'status_shifts': exchange_outcome.get('status_shifts', []) if isinstance(exchange_outcome, dict) else [],
                            }
                        except Exception:
                            last_exchange_context = None
                        
                        # ARCHITECT: Extract and apply movement from exchange narratives
                        # NUAs/MNUAs may move as part of their exchange actions (approach, retreat, etc.)
                        try:
                            from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                            
                            # Check proactor narrative for movement
                            proactor_narrative = proactor_action_data.get('narrative_description', '')
                            proactor_movement = extract_movement_from_narrative(proactor_narrative)
                            if proactor_movement and not getattr(proactor, 'is_user_actor', False):
                                if move_actor_on_map(proactor.sheet.name, proactor_movement, proactor_narrative):
                                    print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {proactor.sheet.name} moved to '{proactor_movement}'")
                            
                            # Check reactor narrative for movement
                            reactor_narrative = reactor_action_data.get('narrative_description', '')
                            reactor_movement = extract_movement_from_narrative(reactor_narrative)
                            if reactor_movement and not getattr(reactor, 'is_user_actor', False):
                                if move_actor_on_map(reactor.sheet.name, reactor_movement, reactor_narrative):
                                    print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {reactor.sheet.name} moved to '{reactor_movement}'")
                        except Exception:
                            pass  # Movement is enhancement, not critical
                        
                        try:
                            turn_summary_data = {
                                'turn_queue_data': turn_queue_data if 'turn_queue_data' in locals() else None,
                                'proactor_data': (lambda d: (d.update({'name': ("You" if getattr(proactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(proactor))}) or d))(dict(proactor_action_data)),
                                'reactor_data': (lambda d: (d.update({'name': ("You" if getattr(reactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(reactor))}) or d))(dict(reactor_action_data)),
                                'outcome_data': step6_outcome_data,
                                'final_narrative': final_narrative,
                            }
                            encounter_checker.current_context.reporter.report_full_turn(turn_summary_data, narrator_agent=narrator)
                        except Exception:
                            pass

                        # Advance the queue explicitly and handle end-of-round
                        try:
                            rm = encounter_checker.current_context.round_manager
                            old_pos = rm.turn_queue_position
                            queue_cycle_complete = rm.advance_turn_queue()
                            new_pos = rm.turn_queue_position
                            
                            # Debug: Show queue advancement
                            if not SUPPRESS_DEBUG:
                                old_actor = turn_queue[old_pos]['actor'].sheet.name if old_pos < len(turn_queue) else '?'
                                new_actor = turn_queue[new_pos]['actor'].sheet.name if new_pos < len(turn_queue) else '?'
                                print(f"{Color.SYSTEM}ADVANCE QUEUE: pos {old_pos+1}->{new_pos+1} | {old_actor} -> {new_actor}{Color.RESET}")
                            
                            if queue_cycle_complete:
                                print(f"\n{Color.SUCCESS}🔄 Turn cycle completed - Starting new round{Color.RESET}")
                                turn_number += 1  # Increment turn number when cycle completes
                                
                                # End the completed round (apply lasting shifts, check deaths, decay effects)
                                try:
                                    rm.end_round()
                                except Exception as e:
                                    print(f"{Color.WARNING}End round processing error: {e}{Color.RESET}")
                                
                                # Reset reactor time manager for next cycle
                                try:
                                    reactor_time_manager = ReactorTimeManager()
                                except Exception:
                                    pass
                                # Start new round (applies temporary recovery + rolls initiative)
                                print(f"{Color.SYSTEM}🎲 Starting new round (applying recovery + rolling initiative)...{Color.RESET}")
                                new_turn_queue_data = rm.start_round()
                                turn_queue = new_turn_queue_data.get('turn_queue', [])
                                recovery_events = new_turn_queue_data.get('recovery_events', [])
                                
                                # Tracker: record new round
                                try:
                                    if tracker and _tracker_exchange_started:
                                        tracker.start_round(round_number=getattr(rm, 'round_number', 1), initiative_data=new_turn_queue_data)
                                except Exception:
                                    pass
                                
                                # Display recovery events
                                if recovery_events:
                                    print(f"\n{Color.SUCCESS}💚 TEMPORARY RECOVERY{Color.RESET}")
                                    for event in recovery_events:
                                        actor_name = event.get('actor_name', 'Unknown')
                                        status = event.get('status_name', event.get('status_type', 'Unknown'))
                                        amount = event.get('recovery_amount', event.get('amount', 0))
                                        new_value = event.get('new_value', 0)
                                        if amount > 0:  # Only show actual recovery, not KO events
                                            print(f"{Color.SUCCESS}  • {actor_name}: {status} +{amount} → {new_value}{Color.RESET}")
                                
                                # Display turn order with calculation breakdown
                                print(f"\n{Color.INFO}🎲 INITIATIVE ORDER{Color.RESET}")
                                actor_initiatives = new_turn_queue_data.get('actor_initiatives', {})
                                for i, turn_data in enumerate(turn_queue):
                                    actor_name = turn_data['actor'].sheet.name
                                    initiative = turn_data.get('initiative_score', 0)
                                    
                                    # Get breakdown data
                                    breakdown = actor_initiatives.get(actor_name, {})
                                    swiftness = breakdown.get('swiftness', 0)
                                    status_mod = breakdown.get('status_modifier', 0)
                                    serendipity = breakdown.get('serendipity', 0)
                                    role_bonus = breakdown.get('role_bonus', 0)
                                    
                                    # Format breakdown
                                    breakdown_str = f"Swift:{swiftness} + Status:{status_mod} + Luck:{serendipity:+d} + Role:{role_bonus:+d}"
                                    
                                    print(f"{Color.SYSTEM}{i+1}. {actor_name} (Initiative: {initiative}) [{breakdown_str}]{Color.RESET}")
                        except Exception as e:
                            if not SUPPRESS_DEBUG:
                                print(f"{Color.ERROR}Queue advance error: {e}{Color.RESET}")
                        
                        # After NUA fast-path completes, continue to next turn
                        # The queue has advanced, so next iteration will process the next actor
                        continue
                    except Exception as e:
                        print(f"{Color.ERROR}NUA FAST-PATH processing error: {e}{Color.RESET}")
                        import traceback as traceback_module
                        traceback_module.print_exc()
                elif proactor.is_user_actor:
                    # User Actor turn - use stored initial action if this is first turn, otherwise prompt
                    # FIX BUG #16: Clear ALL action variables to prevent persistence between rounds
                    user_input = None
                    
                    while not proactor_action_data:
                        # Check for stored initial action from encounter trigger (ONLY on first turn, ONLY ONCE)
                        if hasattr(encounter_checker.current_context, 'initial_user_action') and encounter_checker.current_context.initial_user_action:
                            user_input = encounter_checker.current_context.initial_user_action
                            encounter_checker.current_context.initial_user_action = None  # Clear after use
                            print(f"{Color.SYSTEM}[ENCOUNTER] Using stored initial action: '{user_input}'{Color.RESET}")
                        elif (pending_encounter_action and 
                              turn_number == 1 and 
                              not hasattr(encounter_checker.current_context, 'pending_action_used') and
                              not (hasattr(encounter_checker.current_context, 'is_remote_encounter') and encounter_checker.current_context.is_remote_encounter)):
                            # Only use pending action on the VERY FIRST turn AND only if not already used AND NOT a remote encounter (phone/device)
                            user_input = pending_encounter_action
                            encounter_checker.current_context.pending_action_used = True  # Mark as used
                            print(f"{Color.SYSTEM}[ENCOUNTER] Using pending action: '{user_input}'{Color.RESET}")
                        else:
                            # For phone encounters, show "answered the phone" message before first prompt
                            if (hasattr(encounter_checker.current_context, 'is_remote_encounter') and 
                                encounter_checker.current_context.is_remote_encounter and
                                encounter_checker.current_context.remote_encounter_type == "phone_call" and
                                not hasattr(encounter_checker.current_context, 'phone_answered_shown')):
                                npc_name = encounter_checker.current_context.participants[0].sheet.name
                                print(f"\n{Color.SUCCESS}✓ {npc_name} answered the phone{Color.RESET}")
                                encounter_checker.current_context.phone_answered_shown = True
                            
                            # Always prompt for new input in subsequent turns
                            user_input = _prompt_action_input(Color.PROMPT)
                        # On-demand quick commands (no time advancement in encounter)
                        ui_lower = user_input.strip().lower()
                        if _handle_debug_context_commands(user_input):
                            continue
                        if ui_lower in ['look', 'l', 'examine scene', 'scan']:
                            print(f"\n{Color.SCENE}🎬 FULL SCENE DESCRIPTION:{Color.RESET}")
                            print(f"{Color.NARRATIVE}{scene_description}{Color.RESET}")
                            continue
                        if ui_lower in ['ua', 'sheet']:
                            print(f"\n{Color.INFO}📋 Your Character Sheet:{Color.RESET}")
                            proactor.sheet.display_detailed()
                            continue
                        if ui_lower in ['npc', 'npcs', 'nua']:
                            if available_npcs:
                                print(f"\n{Color.INFO}👥 Non-User Actors in the area:{Color.RESET}")
                                for n in available_npcs:
                                    try:
                                        _display_actor_sheet_simple(n.sheet)
                                    except Exception:
                                        print(f"  - {getattr(n.sheet, 'name', 'Unknown')}")
                            else:
                                print(f"{Color.INFO}No Non-User Actors are currently nearby.{Color.RESET}")
                            continue
                        
                        # Pre-select reactor for continuity based on target detection
                        reactor_candidate = reactor
                        if reactor_candidate is None:
                            try:
                                rm = encounter_checker.current_context.round_manager
                                detected = rm.find_reactor_by_target_detection(user_input, scene_description)
                                if detected:
                                    reactor_candidate = detected
                                else:
                                    # Prefer participant[0] if present
                                    part = None
                                    try:
                                        part = encounter_checker.current_context.participants[0]
                                    except Exception:
                                        part = None
                                    if part is not None and getattr(part, 'is_user_actor', False) is False:
                                        reactor_candidate = part
                                    else:
                                        # Fallback to next in queue
                                        reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                                        reactor_candidate = turn_queue[reactor_position]['actor']
                            except Exception:
                                try:
                                    rm = encounter_checker.current_context.round_manager
                                    reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                                    reactor_candidate = turn_queue[reactor_position]['actor']
                                except Exception:
                                    reactor_candidate = reactor

                        # SAFETY: Reactor must never be the UA. If selection yields UA (or None), choose a non-user participant.
                        try:
                            if reactor_candidate is None or getattr(reactor_candidate, 'is_user_actor', False):
                                # Prefer encounter participants
                                chosen = None
                                try:
                                    participants = getattr(encounter_checker.current_context, 'participants', []) or []
                                    for p in participants:
                                        if p is not None and not getattr(p, 'is_user_actor', False):
                                            chosen = p
                                            break
                                except Exception:
                                    chosen = None
                                # Otherwise choose first non-user actor in turn queue
                                if chosen is None:
                                    try:
                                        for entry in (turn_queue or []):
                                            a = entry.get('actor') if isinstance(entry, dict) else None
                                            if a is not None and not getattr(a, 'is_user_actor', False):
                                                chosen = a
                                                break
                                    except Exception:
                                        chosen = None
                                if chosen is not None:
                                    reactor_candidate = chosen
                        except Exception:
                            pass

                        # Early disengagement intent: allow natural end (e.g., finishing an order)
                        try:
                            if _detect_disengage_intent(user_input):
                                enc_type = getattr(encounter_checker.current_context, 'encounter_type', 'general')
                                # Get escalation level from NUA context
                                escalation_value = 1  # Default to PEACEFUL
                                try:
                                    reactor_name = getattr(getattr(reactor_candidate, 'sheet', None), 'name', None)
                                    if reactor_name and 'nua_context_manager' in locals():
                                        nua_ctx = nua_context_manager.get_or_create_context(reactor_name)
                                        escalation_value = nua_ctx.escalation_level.value
                                except Exception:
                                    pass
                                allows = _nua_allows_disengage(reactor_candidate, enc_type, escalation_value)
                                if allows:
                                    # Natural end narration for service/social contexts
                                    try:
                                        rn = getattr(getattr(reactor_candidate, 'sheet', None), 'name', 'NPC') if reactor_candidate else 'NPC'
                                        print(f"{Color.NARRATIVE}{rn} nods, acknowledging the close of the exchange. They turn to their task, and the immediate tension dissolves.{Color.RESET}")
                                    except Exception:
                                        pass
                                    # Log and end encounter cleanly
                                    try:
                                        narrative_context_manager.add_narrative_event(
                                            event_type=NarrativeEventType.ACTION_OUTCOME,
                                            narrative_text=f"Scene {scene_number}: {actor.sheet.name} ends the interaction; counterpart disengages.",
                                            actors_involved=[actor.sheet.name, getattr(getattr(reactor_candidate, 'sheet', None), 'name', 'NPC')],
                                            importance=NarrativeImportance.ROUTINE,
                                            emotional_tone="neutral",
                                            scene_context=f"Scene {scene_number} natural disengagement ({enc_type})"
                                        )
                                    except Exception:
                                        pass
                                    exchange_in_progress = False
                                    break
                                else:
                                    # Reactor chooses to keep the UA engaged (e.g., guard, hostile role)
                                    try:
                                        rn = getattr(getattr(reactor_candidate, 'sheet', None), 'name', 'NPC') if reactor_candidate else 'NPC'
                                        print(f"{Color.WARNING}{rn} steps in to hold your attention — the exchange isn’t over yet.{Color.RESET}")
                                    except Exception:
                                        pass
                        except Exception:
                            pass

                        # CHECK EXCHANGE COMPLETION: Proper ending conditions
                        try:
                            from exchange_completion_checker import get_completion_checker
                            completion_checker = get_completion_checker()
                            
                            # Check if exchange should continue
                            last_input_for_disengage = None
                            try:
                                if _detect_disengage_intent(user_input):
                                    last_input_for_disengage = user_input
                            except Exception:
                                last_input_for_disengage = None
                            should_continue, reason = completion_checker.should_exchange_continue(
                                proactor, reactor_candidate, last_input_for_disengage
                            )
                            
                            if not should_continue:
                                # Exchange ends due to incapacitation, death, or disengagement
                                print(f"{Color.SYSTEM}{completion_checker.format_ending_message(reason)}{Color.RESET}")
                                exchange_in_progress = False
                                break
                            
                            # Check if NPC wants to disengage (if reactor is NPC)
                            if not reactor_candidate.sheet.name.startswith("ua_"):
                                wants_to_disengage, npc_reason = completion_checker.check_npc_wants_to_disengage(
                                    reactor_candidate,
                                    []  # TODO: Pass exchange history if available
                                )
                                
                                if wants_to_disengage:
                                    print(f"{Color.SYSTEM}{completion_checker.format_ending_message(npc_reason)}{Color.RESET}")
                                    exchange_in_progress = False
                                    break
                        
                        except Exception as e:
                            print(f"{Color.WARNING}[EXCHANGE] Completion check failed: {e}{Color.RESET}")

                        # If UA naturally disengaged, break outer encounter loop immediately
                        if not exchange_in_progress:
                            break

                        # Ensure authoritative scene is loaded before continuity and contested flow
                        try:
                            latest = tracker.get_current_scene()
                            latest_desc = (latest or {}).get('scene_description') if latest else None
                            if latest_desc:
                                scene_description = latest_desc
                                try:
                                    conductor.scene_description = scene_description
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # Classify action type first
                        input_analysis = _strict_detect_inquiry_or_action(user_input, proactor, reactor_candidate, _retries=3)
                        if input_analysis is None:
                            print(f"{Color.WARNING}I couldn't reliably interpret that action. Please rephrase and try again.{Color.RESET}")
                            continue

                        # Ensure inquiries remain inquiries during exchanges.
                        # Some interpreter paths may return input_type='inquiry' instead of fallible_action+subtype.
                        # Normalize here so the fallible→contested override does not convert inquiries into exchanges.
                        try:
                            if input_analysis.get('input_type') == 'inquiry':
                                input_analysis['input_type'] = 'fallible_action'
                                input_analysis['fallible_subtype'] = 'inquiry'
                                # Internal inquiry should not be treated as addressed dialogue.
                                input_analysis['addressed_to'] = None
                                input_analysis['addressed_type'] = None
                        except Exception:
                            pass

                        # INQUIRY IN ENCOUNTER MODE: do NOT consume an encounter turn.
                        # Treat as internal information-gathering (like ROAM) unless an explicit target was provided.
                        try:
                            is_inquiry = bool(
                                input_analysis and (
                                    (input_analysis.get('input_type') == 'fallible_action' and input_analysis.get('fallible_subtype') in ['mental', 'inquiry'])
                                )
                            )
                            if is_inquiry:
                                try:
                                    # Prefer the existing inquiry handler for consistent output framing.
                                    resp = conductor.handle_inquiry(user_input, proactor=proactor, reactor=reactor_candidate)
                                    if isinstance(resp, dict) and resp.get('narrative_response'):
                                        print(f"{Color.NARRATIVE}{resp.get('narrative_response')}{Color.RESET}")
                                except Exception:
                                    # Fallback: use internal voice style response if inquiry handler fails.
                                    try:
                                        time_ctx = master_time.get_current_time_context() if master_time else None
                                        answer = narrator.generate_inquiry_response(
                                            user_question=user_input,
                                            ua_actor=proactor,
                                            scene_description=scene_description,
                                            narrative_context="",
                                            current_time=time_ctx,
                                        )
                                        print(f"{Color.NARRATIVE}{answer}{Color.RESET}")
                                        internal_voice = generate_unified_internal_voice(
                                            actor=proactor,
                                            narrator=narrator,
                                            scene_description=scene_description,
                                            user_action=user_input,
                                            action_outcome=answer,
                                            function_hint="information",
                                            question_content=user_input,
                                            urgency="normal",
                                            narrative_context_manager=narrative_context_manager,
                                        )
                                        display_internal_voice_box(internal_voice)
                                    except Exception:
                                        pass

                                # Do not advance encounter queue; re-prompt same proactor.
                                continue
                        except Exception:
                            pass

                        try:
                            target_name = input_analysis.get('addressed_to')
                            if target_name:
                                picked = None
                                try:
                                    participants = getattr(encounter_checker.current_context, 'participants', []) or []
                                    for p in participants:
                                        if p is None:
                                            continue
                                        if getattr(getattr(p, 'sheet', None), 'name', None) == target_name and not getattr(p, 'is_user_actor', False):
                                            picked = p
                                            break
                                except Exception:
                                    picked = None
                                if picked is None:
                                    try:
                                        for entry in (turn_queue or []):
                                            a = entry.get('actor') if isinstance(entry, dict) else None
                                            if a is None:
                                                continue
                                            if getattr(getattr(a, 'sheet', None), 'name', None) == target_name and not getattr(a, 'is_user_actor', False):
                                                picked = a
                                                break
                                    except Exception:
                                        picked = None
                                if picked is not None:
                                    reactor_candidate = picked
                        except Exception:
                            pass
                        
                        # Handle passive actions in encounter mode (defensive stance)
                        if input_analysis and input_analysis.get('input_type') == 'passive_action':
                            print(f"\n{Color.SYSTEM}═══ Action Classification ═══{Color.RESET}")
                            print(f"{Color.SYSTEM}Type: PASSIVE ACTION (Defensive Stance){Color.RESET}")
                            print(f"{Color.SYSTEM}Reasoning: {input_analysis.get('reasoning', 'Character takes defensive stance') if input_analysis else 'N/A'}{Color.RESET}")
                            
                            passive_narratives = [
                                f"You take a defensive stance, watching your opponent carefully.",
                                f"You hold your ground, observing their movements.",
                                f"You pause, assessing the situation before acting.",
                                f"You wait, letting them make the next move."
                            ]
                            import random
                            narrative = random.choice(passive_narratives)
                            print(f"\n{Color.NARRATIVE}{narrative}{Color.RESET}")
                            print(f"{Color.INFO}💭 You take a defensive stance, observing...{Color.RESET}")
                            
                            # Advance turn (passive action counts as UA's turn)
                            try:
                                rm = encounter_checker.current_context.round_manager
                                rm.advance_turn_queue()
                            except Exception:
                                pass
                            
                            # Continue to next turn
                            continue

                        if input_analysis and (input_analysis.get('input_type') == 'fallible_action' and
                            input_analysis.get('fallible_subtype') not in ['mental', 'inquiry']):
                            input_analysis['input_type'] = 'contested_action'
                        
                        # Process user action through contested action flow
                        continuity_data = conductor.enforce_continuity(user_input, proactor, reactor_candidate)
                        
                        # Display continuity check result
                        if continuity_data:
                            judgment = continuity_data.get('judgment', 'Unknown')
                            justification = continuity_data.get('justification', 'No justification provided')
                            print(f"\n{Color.INFO}🔍 Continuity Check: {judgment}{Color.RESET}")
                            if judgment == 'Not Possible':
                                # Generate perceptual description (what you physically experience)
                                failure_narrative = narrator.generate_continuity_failure_narrative(
                                    actor=proactor,
                                    attempted_action=user_input,
                                    reason=justification,
                                    scene_description=scene_description,
                                    time_context=master_time.get_current_time_context() if master_time else None
                                )
                                print(failure_narrative)
                                
                                # Generate internal voice (mental reaction to failure)
                                internal_voice = generate_unified_internal_voice(
                                    actor=proactor,
                                    narrator=narrator,
                                    scene_description=scene_description,
                                    user_action=user_input,
                                    action_outcome=failure_narrative,
                                    function_hint="solution",  # Suggest alternatives
                                    predicament=f"Cannot do: {user_input} - {justification}",
                                    urgency="normal"
                                )
                                
                                display_internal_voice_box(internal_voice)
                        
                        if continuity_data and continuity_data.get('judgment') == 'Possible':
                            # Check action type for proper processing
                            # Bind the selected reactor for this action
                            reactor = reactor_candidate
                            
                            # Detect monetary transactions in encounter mode (but don't process yet)
                            monetary_data = conductor.interpreter_agent.detect_monetary_exchange(
                                user_input, proactor, scene_description
                            )
                            
                            # For non-contested monetary actions (purchases), check affordability upfront.
                            # Do NOT run affordability checks on contested actions (dialogue can mention buying).
                            if (input_analysis and input_analysis.get('input_type') == 'given_action' and
                                monetary_data.get("transaction_detected") and monetary_data.get("transaction_type") == "Purchase"):
                                amount = monetary_data.get("amount", 0)
                                if amount < 0:  # Spending money
                                    supply_status = proactor.sheet.statuses[StatusType.SUPPLY]
                                    if supply_status.money_amount + amount < 0:
                                        insufficient = abs(supply_status.money_amount + amount)
                                        print(f"\n{Color.WARNING}⚠️  Cannot afford this purchase!{Color.RESET}")
                                        print(f"{Color.WARNING}Need ${insufficient:.2f} more. Current balance: ${supply_status.money_amount:.2f}{Color.RESET}")
                                        continue
                            
                            if input_analysis and input_analysis.get('input_type') == 'given_action':
                                # Handle given actions (trivial, automatic success)
                                print(f"\n{Color.SUCCESS}✅ GIVEN ACTION (AUTOMATIC SUCCESS){Color.RESET}")
                                print(f"{Color.INFO}Action: {user_input}{Color.RESET}")
                                print(f"{Color.SUCCESS}Result: Automatic success - no roll required{Color.RESET}")
                                
                                # Process monetary transaction if detected (will show after turn in encounter mode)
                                # Note: For given actions in encounter, no narrative is generated, so transaction won't display
                                if monetary_data.get("transaction_detected"):
                                    try:
                                        can_proceed, transaction_narrative, consequences = monetary_processor.process_enhanced_transaction(
                                            monetary_data=monetary_data,
                                            proactor=proactor,
                                            reactor=reactor,
                                            success=True,
                                            targeted_status=None
                                        )
                                    except Exception as e:
                                        print(f"{Color.ERROR}Transaction processing error: {e}{Color.RESET}")
                                
                                # Process survival needs (LLM-first with fallback)
                                survival_needs = []
                                llm_detection = None
                                try:
                                    llm_detection = conductor.interpreter.detect_survival_intent(user_input, actor)
                                except Exception:
                                    llm_detection = None
                                if llm_detection and llm_detection.get('needs'):
                                    need_map = {
                                        'food': SurvivalNeed.FOOD,
                                        'water': SurvivalNeed.WATER,
                                        'sleep': SurvivalNeed.SLEEP,
                                        'fulfillment': SurvivalNeed.FULFILLMENT,
                                    }
                                    llm_needs = [need_map[n.lower()] for n in llm_detection['needs'] if isinstance(n, str) and n.lower() in need_map]
                                    if llm_needs and float(llm_detection.get('confidence', 0)) >= 0.6:
                                        survival_needs = llm_needs
                                if not survival_needs:
                                    survival_needs = survival_analyzer.analyze_action(user_input)
                                if survival_needs:
                                    # Determine costs and process fulfillment
                                    costs = survival_analyzer.get_action_costs(user_input, survival_needs)
                                    # If the LLM provided a time estimate, prefer it for reporting only (we do not advance survival time in encounters)
                                    if llm_detection and isinstance(llm_detection.get('total_time_hours'), (int, float)) and llm_detection['total_time_hours'] > 0:
                                        costs['time_cost'] = float(llm_detection['total_time_hours'])
                                    survival_messages = survival_analyzer.process_survival_fulfillment(
                                        actor.sheet, user_input, survival_needs, costs, narrative_context_manager
                                    )
                                    # Display summary
                                    survival_summary = survival_analyzer.get_survival_summary(survival_needs, costs)
                                    print(f"\n{Color.INFO}🍃 SURVIVAL NEEDS ADDRESSED{Color.RESET}")
                                    print(f"{Color.INFO}{survival_summary}{Color.RESET}")
                                    for message in survival_messages:
                                        print(f"{Color.SUCCESS}   • {message}{Color.RESET}")
                                    # Update narrative loop with survival signal (Encounter given-action)
                                    try:
                                        turn_data = _build_turn_data(
                                            user_input=user_input,
                                            scene_description=scene_description,
                                            current_mode=current_mode,
                                            continuity={'judgment': 'Possible'},
                                            survival_needs=[n.value for n in survival_needs]
                                        )
                                        turn_data['narrative_response'] = last_action_narrative
                                        framing = narrative_loop.process_turn(
                                            turn_data=turn_data,
                                            scene_description=scene_description,
                                            time_context=time_context,
                                            available_npcs=available_npcs
                                        )
                                        try:
                                            if framing and framing.get('mode_changed'):
                                                print(f"{Color.SYSTEM}🔀 Mode Shift → {framing.get('mode', 'unknown').upper()} (Tone: {framing.get('tone', 'unknown')}){Color.RESET}")
                                        except Exception:
                                            pass
                                    except Exception:
                                        pass
                                
                                # Add minimal time cost for given actions (use 3-second category for trivial actions)
                                req = master_time.create_user_action_request(
                                    RuleOf3Category.THREE_SECOND,
                                    actor.sheet.name,
                                    user_input
                                )
                                res = master_time.request_time_advancement(req)
                                if not SUPPRESS_DEBUG:
                                    elapsed = simulation_time_tracker.get_simulation_time_display()
                                    print(f"{Color.SYSTEM}⏰ Time advanced: +{res.duration_advanced_seconds}s | Clock: {res.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                                
                                # Transaction already processed above (integrated into narrative if applicable)
                                
                                # Track narrative event
                                narrative_context_manager.add_narrative_event(
                                    event_type=NarrativeEventType.ACTION_OUTCOME,
                                    narrative_text=f"Scene {scene_number}: {actor.sheet.name}: {user_input} → Automatic success",
                                    actors_involved=[actor.sheet.name],
                                    importance=NarrativeImportance.ROUTINE,
                                    emotional_tone="routine"
                                )
                                
                                # Advance to next actor in the turn queue and break to outer loop
                                try:
                                    rm = encounter_checker.current_context.round_manager
                                    _ = rm.advance_turn_queue()
                                except Exception:
                                    pass
                                # Note: Do NOT increment scene_action_count here.
                                # Encounter turns are tracked by turn_number; scene_action_count
                                # is reserved for exploration actions only.
                                break
                                
                            elif input_analysis and input_analysis.get('input_type') == 'contested_action':
                                # Handle contested actions (require full UTAS calculation against NUA)
                                print(f"\n{Color.INFO}⚔️ CONTESTED ACTION{Color.RESET}")
                                print(f"{Color.INFO}Action: {user_input}{Color.RESET}")
                                print(f"{Color.WARNING}This action requires a contested exchange with a Non-User Actor{Color.RESET}")
                                
                                # Break out of the input loop to proceed with contested exchange
                                proactor_action_data = conductor.interpret_fallible_action(user_input, proactor)
                                # CRITICAL USER AGENCY: Preserve the user's exact proactor action text.
                                try:
                                    if isinstance(proactor_action_data, dict):
                                        # Preserve interpreter-cleaned text separately for reporting.
                                        try:
                                            proactor_action_data['interpreted_user_action'] = (
                                                proactor_action_data.get('interpreted_user_action')
                                                or proactor_action_data.get('action_description')
                                                or proactor_action_data.get('narrative_description')
                                            )
                                        except Exception:
                                            pass
                                        proactor_action_data['raw_user_action'] = user_input
                                        proactor_action_data['action_description'] = user_input
                                        proactor_action_data['narrative_description'] = user_input
                                except Exception:
                                    pass
                                # Add continuity data to proactor_action_data for reporter
                                if continuity_data:
                                    proactor_action_data['continuity_check'] = continuity_data
                                
                                # Update actor tasks for contested actions
                                try:
                                    conductor.interpreter.update_actor_tasks(
                                        user_action=user_input,
                                        actor=proactor,
                                        action_interpretation=proactor_action_data
                                    )
                                except Exception as e:
                                    logger.log_error(f"Task update failed for contested action: {e}")
                                
                                # Ensure UTAS completeness for proactor
                                proactor_action_data = _ensure_min_utas_fields(proactor_action_data, proactor)

                                # UA perceptual attempt narration (paraphrase-only). This is for display only
                                # and must never introduce new actions or dialogue beyond the user's input.
                                try:
                                    is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                    remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)
                                    if isinstance(proactor_action_data, dict) and 'narrator' in locals() and narrator:
                                        proactor_action_data['ua_attempt_text'] = narrator.generate_ua_action_perceptual_narrative(
                                            user_input=user_input,
                                            scene_description=scene_description,
                                            is_remote_encounter=is_remote,
                                            remote_encounter_type=remote_type,
                                            session_id=getattr(tracker, 'session_id', None) if tracker else None,
                                        )
                                except Exception:
                                    pass
                                break
                                
                            elif input_analysis.get('input_type') == 'fallible_action':
                                # Handle fallible actions with full calculation display
                                fallible_subtype = input_analysis.get('fallible_subtype', 'physical')
                                
                                if fallible_subtype in ['mental', 'inquiry']:
                                    print(f"\n{Color.INFO}📋 INQUIRY (Information Gathering){Color.RESET}")
                                    
                                    # Import inquiry helpers
                                    from inquiry_helpers import (
                                        check_inquiry_memory,
                                        determine_inquiry_difficulty,
                                        roll_inquiry_success,
                                        check_duplicate_inquiry_memory,
                                        process_failed_inquiry,
                                        extract_inquiry_subject,
                                        extract_inquiry_keywords
                                    )
                                    
                                    # PHASE 1: Check existing memories first
                                    memory_check = check_inquiry_memory(
                                        user_question=user_input,
                                        key_memories_system=key_memories,
                                        ua_actor=proactor
                                    )
                                    
                                    if memory_check and memory_check['found']:
                                        # Memory exists - recall it (free, no roll needed)
                                        print(f"{Color.SUCCESS}[Memory Recall - No roll needed]{Color.RESET}\n")
                                        
                                        # Display internal voice recalling memory
                                        memory = memory_check['memory']
                                        internal_voice = f"Oh right, we learned this before. {memory.description[:100]}..."
                                        print(f"\n{Color.SYSTEM}{'─' * 70}{Color.RESET}")
                                        print(f"{Color.INTERNAL_VOICE}💭 {internal_voice}{Color.RESET}")
                                        print(f"{Color.SYSTEM}{'─' * 70}{Color.RESET}\n")
                                        
                                        # Display perceptual transition into thought/inquiry
                                        try:
                                            perceptual_desc = narrator.generate_inquiry_perceptual_description(
                                                ua_actor=actor,
                                                question=user_input,
                                                scene_description=scene_description,
                                                time_context=master_time.get_current_time_context() if master_time else None
                                            )
                                            if perceptual_desc:
                                                display_perceptual_description_box(perceptual_desc)
                                        except Exception as e:
                                            # Fallback to simple description
                                            display_perceptual_description_box("You close your eyes, entering your thoughts.")
                                        
                                        # Display full answer from memory
                                        print(f"{Color.NARRATIVE}{memory.description}{Color.RESET}")
                                        
                                        # Add to narrative context
                                        narrative_context_manager.add_narrative_event(
                                            event_type=NarrativeEventType.MEMORY_RESURFACING,
                                            narrative_text=f"Scene {scene_number}: {proactor.sheet.name} recalled: {user_input}",
                                            actors_involved=[proactor.sheet.name],
                                            importance=NarrativeImportance.ROUTINE,
                                            emotional_tone="thoughtful",
                                            scene_context=scene_description
                                        )
                                    
                                    else:
                                        # PHASE 2: No memory - roll for success
                                        print(f"{Color.WARNING}[No memory found - Rolling for success]{Color.RESET}\n")
                                        
                                        # Determine difficulty
                                        difficulty = determine_inquiry_difficulty(user_input, scene_description)
                                        
                                        # Roll for success (Swiftness + Spirit + Serendipity)
                                        roll_result = roll_inquiry_success(
                                            user_question=user_input,
                                            ua_actor=proactor,
                                            scene_context=scene_description,
                                            difficulty=difficulty
                                        )
                                        
                                        # Display roll breakdown
                                        print(f"{Color.INFO}🎲 MENTAL ACTION ROLL{Color.RESET}")
                                        print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}")
                                        breakdown = roll_result['breakdown']
                                        try:
                                            s_trait_v = breakdown.get('s_trait', 0)
                                            ser_v = breakdown.get('serendipity', 0)
                                            diff_v = breakdown.get('difficulty', '?')
                                            print(f"Smarts: {s_trait_v} + Luck: {int(ser_v):+d} = {roll_result.get('total')}")
                                            print(f"Difficulty: {diff_v}")
                                        except Exception:
                                            print(f"Roll Total: {roll_result.get('total')}")
                                            try:
                                                print(f"Difficulty: {breakdown.get('difficulty', '?')}")
                                            except Exception:
                                                pass
                                        
                                        if roll_result['success']:
                                            # PHASE 3a: SUCCESS - Generate answer and create memory
                                            print(f"{Color.SUCCESS}Result: SUCCESS ✓{Color.RESET}")
                                            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
                                            print(f"{Color.SUCCESS}[SUCCESS - Learning information]{Color.RESET}\n")
                                            
                                            # Get context
                                            recent_context = narrative_context_manager.get_context_for_llm(
                                                lookback_events=5,
                                                importance_threshold="notable"
                                            )
                                            recent_context = _merge_contexts(recent_context, everlasting_context_text)
                                            
                                            # Generate answer
                                            time_context = master_time.get_current_time_context()
                                            answer = narrator.generate_inquiry_response(
                                                user_question=user_input,
                                                ua_actor=proactor,
                                                scene_description=scene_description,
                                                narrative_context=recent_context,
                                                current_time=time_context
                                            )
                                            
                                            # Display narrative answer
                                            print(f"{Color.NARRATIVE}{answer}{Color.RESET}\n")
                                            
                                            # Generate and display internal voice reaction
                                            internal_voice = generate_unified_internal_voice(
                                                actor=proactor,
                                                narrator=narrator,
                                                scene_description=scene_description,
                                                user_action=user_input,
                                                action_outcome=answer,
                                                function_hint="information",
                                                question_content=user_input,
                                                urgency="normal",
                                                narrative_context_manager=narrative_context_manager
                                            )
                                            
                                            display_internal_voice_box(internal_voice)
                                            
                                            # Check for duplicate before creating memory
                                            existing = check_duplicate_inquiry_memory(
                                                question=user_input,
                                                answer=answer,
                                                key_memories_system=key_memories
                                            )
                                            
                                            if not existing:
                                                # Create memory of learned information
                                                try:
                                                    key_memories.create_memory(
                                                        title=f"Learned: {extract_inquiry_subject(user_input)}",
                                                        description=answer,
                                                        full_narrative=f"Question: {user_input}\n\nAnswer: {answer}",
                                                        category=MemoryCategory.DISCOVERY,
                                                        importance=MemoryImportance.ROUTINE,
                                                        location=proactor.sheet.location,
                                                        tags=extract_inquiry_keywords(user_input)
                                                    )
                                                    print(f"{Color.INFO}💾 Information learned and saved to memory{Color.RESET}")
                                                except Exception as e:
                                                    if not SUPPRESS_DEBUG:
                                                        print(f"{Color.WARNING}Memory creation failed: {e}{Color.RESET}")
                                            
                                            # Add to narrative context
                                            narrative_context_manager.add_narrative_event(
                                                event_type=NarrativeEventType.MEMORY_CREATION,
                                                narrative_text=f"Scene {scene_number}: {proactor.sheet.name} learned: {user_input}",
                                                actors_involved=[proactor.sheet.name],
                                                importance=NarrativeImportance.NOTABLE,
                                                emotional_tone="insightful",
                                                scene_context=scene_description
                                            )
                                        
                                        else:
                                            # PHASE 3b: FAILURE - Uncertain response (no memory created)
                                            print(f"{Color.ERROR}Result: FAILURE ✗{Color.RESET}")
                                            print(f"{Color.SYSTEM}{'═' * 70}{Color.RESET}\n")
                                            print(f"{Color.WARNING}[FAILURE - Information unknown]{Color.RESET}\n")
                                            
                                            # Generate uncertain response
                                            uncertainty = process_failed_inquiry(
                                                user_question=user_input,
                                                ua_actor=proactor,
                                                scene_context=scene_description,
                                                narrator=narrator
                                            )
                                            
                                            # Display uncertainty
                                            print(f"{Color.NARRATIVE}{uncertainty}{Color.RESET}\n")
                                            print(f"{Color.SYSTEM}[No memory created]{Color.RESET}")
                                            
                                            # Add to narrative context
                                            narrative_context_manager.add_narrative_event(
                                                event_type=NarrativeEventType.EXPLORATION,
                                                narrative_text=f"Scene {scene_number}: {proactor.sheet.name} tried to recall: {user_input} (failed)",
                                                actors_involved=[proactor.sheet.name],
                                                importance=NarrativeImportance.ROUTINE,
                                                emotional_tone="uncertain",
                                                scene_context=scene_description
                                            )
                                    
                                    # Continue to next turn without contested exchange
                                    queue_cycle_complete = encounter_checker.current_context.round_manager.advance_turn_queue()
                                    
                                    if queue_cycle_complete:
                                        print(f"\n{Color.SUCCESS}🔄 Turn cycle completed - Starting new round{Color.RESET}")
                                        
                                        # End the completed round (apply lasting shifts, check deaths, decay effects)
                                        try:
                                            encounter_checker.current_context.round_manager.end_round()
                                        except Exception as e:
                                            print(f"{Color.WARNING}End round processing error: {e}{Color.RESET}")
                                        
                                        # Reset reactor time manager for next cycle
                                        reactor_time_manager = ReactorTimeManager()
                                        
                                        # Start new round (applies temporary recovery + rolls initiative)
                                        print(f"{Color.SYSTEM}🎲 Starting new round (applying recovery + rolling initiative)...{Color.RESET}")
                                        new_turn_queue_data = encounter_checker.current_context.round_manager.start_round()
                                        turn_queue = new_turn_queue_data.get('turn_queue', [])
                                        recovery_events = new_turn_queue_data.get('recovery_events', [])
                                        
                                        # Display recovery events
                                        if recovery_events:
                                            print(f"\n{Color.SUCCESS}💚 TEMPORARY RECOVERY{Color.RESET}")
                                            for event in recovery_events:
                                                actor_name = event.get('actor_name', 'Unknown')
                                                status = event.get('status_name', event.get('status_type', 'Unknown'))
                                                amount = event.get('recovery_amount', event.get('amount', 0))
                                                new_value = event.get('new_value', 0)
                                                if amount > 0:  # Only show actual recovery, not KO events
                                                    print(f"{Color.SUCCESS}  • {actor_name}: {status} +{amount} → {new_value}{Color.RESET}")
                                        
                                        # Display turn order with calculation breakdown
                                        print(f"\n{Color.INFO}🎲 INITIATIVE ORDER{Color.RESET}")
                                        actor_initiatives = new_turn_queue_data.get('actor_initiatives', {})
                                        for i, turn_data in enumerate(turn_queue):
                                            actor_name = turn_data['actor'].sheet.name
                                            initiative = turn_data.get('initiative_score', 0)
                                            
                                            # Get breakdown data
                                            breakdown = actor_initiatives.get(actor_name, {})
                                            swiftness = breakdown.get('swiftness', 0)
                                            status_mod = breakdown.get('status_modifier', 0)
                                            serendipity = breakdown.get('serendipity', 0)
                                            role_bonus = breakdown.get('role_bonus', 0)
                                            
                                            # Format breakdown
                                            breakdown_str = f"Swift:{swiftness} + Status:{status_mod} + Luck:{serendipity:+d} + Role:{role_bonus:+d}"
                                            
                                            print(f"{Color.SYSTEM}{i+1}. {actor_name} (Initiative: {initiative}) [{breakdown_str}]{Color.RESET}")
                                    
                                    # Break inner loop so outer loop refreshes current proactor
                                    break
                                
                            else:
                                # Fallback for unrecognized input types - treat as fallible situation overcoming
                                print(f"\n{Color.WARNING}⚠️ UNRECOGNIZED INPUT TYPE: {input_analysis.get('input_type', 'unknown')}{Color.RESET}")
                                print(f"{Color.INFO}Treating as fallible action (situation overcoming){Color.RESET}")
                                
                                # Break out of the input loop to proceed with contested exchange
                                proactor_action_data = conductor.interpret_fallible_action(user_input, proactor)
                                # Add continuity data to proactor_action_data for reporter
                                if continuity_data:
                                    proactor_action_data['continuity_check'] = continuity_data
                                break
                        
                        else:
                            # Continuity check failed - ask for different input
                            if continuity_data:
                                reason_text = (
                                    continuity_data.get('justification')
                                    or continuity_data.get('reasoning')
                                    or 'Action not possible in current context'
                                )
                            else:
                                reason_text = 'Action not possible in current context (continuity check failed)'
                            print(f"{Color.WARNING}⚠️ {reason_text}{Color.RESET}")
                            continue
                    
                    # If proactor is NUA and no action yet, generate via DeciderAgent
                    try:
                        print(f"{Color.SYSTEM}DEBUG: NUA gate check is_ua={getattr(proactor,'is_user_actor', False)} proactor_action_data_empty={not bool(proactor_action_data)}{Color.RESET}")
                    except Exception:
                        pass
                    if (not getattr(proactor, 'is_user_actor', False)) and not proactor_action_data:
                        try:
                            print(f"{Color.SYSTEM}DEBUG: ENTER NUA PROACTOR CHAIN{Color.RESET}")
                        except Exception:
                            pass
                        try:
                            # Ensure we have a reactor; default to next in queue if not set earlier
                            if reactor is None:
                                try:
                                    rm = encounter_checker.current_context.round_manager
                                    reactor_position = (rm.turn_queue_position + 1) % len(turn_queue)
                                    reactor = turn_queue[reactor_position]['actor']
                                except Exception:
                                    # Fallback to first non-UA participant
                                    try:
                                        parts = getattr(encounter_checker.current_context, 'participants', []) or []
                                        reactor = next((p for p in parts if getattr(p, 'is_user_actor', False) is False), None)
                                    except Exception:
                                        reactor = None
                            # Build a context snapshot to guide the decision
                            try:
                                context_snapshot = _compose_scene_snapshot(
                                    scene_description=scene_description,
                                    time_context=master_time.get_current_time_context(),
                                    last_action_narrative=last_action_narrative,
                                    scene_updates=scene_updates,
                                )
                                try:
                                    conductor.interpreter._ad_hoc_context_snapshot = context_snapshot
                                except Exception:
                                    pass
                            except Exception:
                                context_snapshot = None
                            # Merge escalation guidance from NUAContextManager
                            try:
                                pro_nua_ctx = nua_context_manager.get_or_create_context(getattr(proactor.sheet, 'name', 'NPC'))
                                g = pro_nua_ctx.get_nua_response_guidance()
                                # Include recent history and narrative loop framing
                                try:
                                    history = pro_nua_ctx.get_turn_history_summary()
                                except Exception:
                                    history = ''
                                try:
                                    loop_state = narrator.get_narrative_loop_state() or {}
                                except Exception:
                                    loop_state = {}
                                context_guidance = {
                                    'escalation_level': g.get('escalation_level', 2),
                                    'recommended_action_type': g.get('recommended_action_type', 'social_response'),
                                    'response_intensity': g.get('response_intensity', 1),
                                    'context_summary': (g.get('context_summary') or '') + (f"\nHistory: {history}" if history else ''),
                                    'narrative_mode': loop_state.get('mode'),
                                    'narrative_tone': loop_state.get('tone'),
                                    'narrative_intent': loop_state.get('intent'),
                                }
                            except Exception:
                                # Fallback to basic snapshot-only guidance
                                context_guidance = {'context_summary': context_snapshot or ''}
                            
                            # CRITICAL: Add remote encounter context if this is a phone call
                            # This prevents the DeciderAgent from generating face-to-face actions
                            try:
                                # DEBUG: Check if remote flags are present
                                has_remote_flag = hasattr(encounter_checker.current_context, 'is_remote_encounter')
                                is_remote_value = getattr(encounter_checker.current_context, 'is_remote_encounter', False) if has_remote_flag else False
                                print(f"{Color.SYSTEM}[REMOTE DEBUG] has_remote_encounter flag: {has_remote_flag}, value: {is_remote_value}{Color.RESET}")
                                
                                if hasattr(encounter_checker.current_context, 'is_remote_encounter') and encounter_checker.current_context.is_remote_encounter:
                                    remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', 'phone_call')
                                    remote_desc = getattr(encounter_checker.current_context, 'remote_encounter_description', 'Remote conversation')
                                    print(f"{Color.SUCCESS}[REMOTE DEBUG] Phone call context ACTIVE - adding to guidance{Color.RESET}")
                                    
                                    # Add remote context to guidance
                                    if isinstance(context_guidance, dict):
                                        context_guidance['is_remote_encounter'] = True
                                        context_guidance['remote_encounter_type'] = remote_type
                                        context_guidance['remote_constraint'] = (
                                            f"CRITICAL CONSTRAINT: This is a {remote_type.upper().replace('_', ' ')}. "
                                            f"The actors are NOT physically present with each other. "
                                            f"Actions MUST be limited to what can be done over the phone: "
                                            f"speaking, listening, asking questions, sharing information, making plans, ending the call. "
                                            f"FORBIDDEN: Any physical actions like 'approaches', 'walks to', 'touches', 'hands over', etc. "
                                            f"Context: {remote_desc}"
                                        )
                                        # Also add to context_summary for visibility
                                        context_guidance['context_summary'] = (
                                            f"[PHONE CALL - NO PHYSICAL PRESENCE]\n{context_guidance.get('context_summary', '')}"
                                        )
                                    
                                    print(f"{Color.SYSTEM}[REMOTE] Added phone call constraint to DeciderAgent context{Color.RESET}")
                            except Exception as e:
                                print(f"{Color.WARNING}[REMOTE] Failed to add remote context: {e}{Color.RESET}")
                            
                            # Determine NUA proaction with escalation guidance (with retry loop for continuity)
                            # DEBUG: Log call context before NUA proaction is determined
                            try:
                                rm_dbg = encounter_checker.current_context.round_manager
                                qlen = len(getattr(rm_dbg, 'current_turn_queue', []) or [])
                                pos = getattr(rm_dbg, 'turn_queue_position', 0) + 1
                                print(f"{Color.SYSTEM}NUA PROACTOR CALL: proactor={getattr(proactor.sheet,'name','?')} reactor={getattr(getattr(reactor,'sheet',None),'name','?')} pos={pos}/{max(1, qlen)}{Color.RESET}")
                            except Exception:
                                pass
                            
                            # Retry loop for continuity validation
                            max_retries = 2
                            new_guidance = context_guidance
                            proactor_action_data = {}
                            for attempt in range(0, max_retries + 1):
                                proactor_action_data = conductor.determine_nua_proaction(
                                    proactor=proactor,
                                    reactor=reactor,
                                    context_guidance=new_guidance,
                                    last_exchange_context=last_exchange_context if 'last_exchange_context' in locals() else None
                                ) or {}
                                
                                # CRITICAL: Validate proactor action with continuity checker
                                # This ensures NUA-generated actions respect physical possibility during exchanges
                                if proactor_action_data and proactor_action_data.get('narrative_description'):
                                    try:
                                        action_text = proactor_action_data.get('narrative_description', '')
                                        proactor_name = proactor.sheet.name

                                        def _normalize_for_repeat_check(t: str) -> str:
                                            try:
                                                t = str(t or '').lower()
                                                t = re.sub(r"\s+", " ", t).strip()
                                                t = re.sub(r"[^a-z0-9\s\"']+", "", t)
                                                t = re.sub(r"\s+", " ", t).strip()
                                                return t
                                            except Exception:
                                                return str(t or '').lower().strip()

                                        def _extract_last_quote(t: str) -> str:
                                            try:
                                                t = str(t or '')
                                                quotes = re.findall(r"\"([^\"]+)\"", t)
                                                if quotes:
                                                    return str(quotes[-1] or '').strip()
                                            except Exception:
                                                pass
                                            return ""

                                        def _soft_repetition_detected(new_text: str, last_ctx: dict):
                                            try:
                                                if not last_ctx or not isinstance(last_ctx, dict):
                                                    return False, ""
                                                new_norm = _normalize_for_repeat_check(new_text)
                                                if not new_norm:
                                                    return False, ""

                                                last_outcome = _normalize_for_repeat_check(last_ctx.get('outcome_narrative', ''))
                                                last_pro = _normalize_for_repeat_check(last_ctx.get('proactor_action', ''))
                                                last_rea = _normalize_for_repeat_check(last_ctx.get('reactor_action', ''))

                                                last_combo = " ".join([x for x in [last_outcome, last_pro, last_rea] if x])
                                                if not last_combo:
                                                    return False, ""

                                                # Hard reject only when it's mostly repetition.
                                                try:
                                                    from difflib import SequenceMatcher
                                                    sim = SequenceMatcher(None, new_norm, last_combo).ratio()
                                                except Exception:
                                                    sim = 0.0

                                                # Quote-level soft check: allow reuse IF there's meaningful additional content.
                                                last_quote = _extract_last_quote(last_ctx.get('reactor_action', '')) or _extract_last_quote(last_ctx.get('proactor_action', ''))
                                                last_quote_norm = _normalize_for_repeat_check(last_quote)
                                                if last_quote_norm and last_quote_norm in new_norm:
                                                    # If the new text is basically just re-saying the quote, reject.
                                                    extra_len = max(0, len(new_norm) - len(last_quote_norm))
                                                    if extra_len < 35:
                                                        return True, "Repeated the last quoted line without adding a new beat"

                                                if sim >= 0.82:
                                                    return True, f"Too similar to last exchange (similarity={sim:.2f})"
                                                return False, ""
                                            except Exception:
                                                return False, ""
                                        
                                        # FIRST: Check if this is a remote encounter and validate physical impossibility
                                        is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                        physical_action_blocked = False
                                        
                                        if is_remote:
                                            # Check for physical proximity actions that are impossible over phone
                                            action_lower = action_text.lower()
                                            
                                            # Phone-specific actions that ARE allowed (exceptions)
                                            phone_allowed_phrases = [
                                                'pick up', 'picks up', 'picking up',  # picking up phone
                                                'hang up', 'hangs up', 'hanging up',  # hanging up phone
                                                'answer', 'answers', 'answering',     # answering phone
                                                'dial', 'dials', 'dialing',           # dialing phone
                                                'phone rings', 'phone ring',          # phone ringing
                                                'hold the phone', 'holds the phone'   # holding phone
                                            ]
                                            
                                            # Check if action contains phone-allowed phrases
                                            is_phone_action = any(phrase in action_lower for phrase in phone_allowed_phrases)
                                            
                                            if not is_phone_action:
                                                # Only check for physical violations if it's NOT a phone-specific action
                                                physical_keywords = [
                                                    'approach', 'walk', 'step', 'move toward', 'come closer',
                                                    'touch', 'grab', 'hand', 'give', 'take', 'reach',
                                                    'push', 'pull', 'hit', 'strike', 'punch', 'kick',
                                                    'embrace', 'hug', 'kiss', 'pat', 'tap'
                                                ]
                                                if any(keyword in action_lower for keyword in physical_keywords):
                                                    physical_action_blocked = True
                                                    issues = [f"REMOTE ENCOUNTER VIOLATION: Physical action '{action_text[:50]}...' cannot be performed during a phone call"]
                                        
                                        # SECOND: Check narrative consistency (location, time, NPC presence)
                                        if not physical_action_blocked:
                                            is_valid, issues = continuity_validator.validate_narrative(
                                                narrative=action_text,
                                                action=action_text,
                                                actor_name=proactor_name
                                            )
                                        else:
                                            is_valid = False
                                        
                                        if not is_valid and issues:
                                            # Continuity violation detected - retry with feedback
                                            if attempt < max_retries:
                                                print(f"{Color.WARNING}⚠️ CONTINUITY VIOLATION (Proactor) - Attempt {attempt + 1}/{max_retries + 1}{Color.RESET}")
                                                print(f"{Color.WARNING}Action: {action_text[:100]}...{Color.RESET}")
                                                for issue in issues:
                                                    print(f"{Color.WARNING}Issue: {issue}{Color.RESET}")
                                                
                                                # Build feedback for regeneration
                                                issues_summary = '; '.join(issues)
                                                continuity_feedback = f"""
CONTINUITY VIOLATION DETECTED - REGENERATION REQUIRED

Previous narrative failed validation:
"{action_text[:200]}..."

Violation reasons:
{issues_summary}

CRITICAL INSTRUCTIONS FOR REGENERATION:
- This is a {'PHONE CALL - actors are in SEPARATE LOCATIONS' if is_remote else 'face-to-face encounter'}
- {'FORBIDDEN: Any physical proximity actions (approaching, touching, gestures visible to other person)' if is_remote else 'Ensure action respects current scene context'}
- {'REQUIRED: Only describe what can be heard over the phone (voice, tone, words, background sounds)' if is_remote else 'Ensure NPCs mentioned are actually present in the scene'}
- Generate a NEW action that avoids these violations

Regenerate the action now with these corrections applied.
"""
                                                
                                                # Add feedback to guidance for next attempt
                                                if isinstance(new_guidance, dict):
                                                    new_guidance = dict(new_guidance)
                                                    new_guidance['continuity_feedback'] = continuity_feedback
                                                else:
                                                    new_guidance = (new_guidance or '') + "\n\n" + continuity_feedback
                                                
                                                print(f"{Color.SYSTEM}Regenerating with continuity feedback...{Color.RESET}")
                                                continue  # Retry generation
                                            else:
                                                # Max retries exceeded - show error and skip
                                                print(f"{Color.ERROR}⚠️ CONTINUITY VIOLATION (Proactor) - Max retries exceeded{Color.RESET}")
                                                print(f"{Color.ERROR}Action: {action_text[:100]}...{Color.RESET}")
                                                for issue in issues:
                                                    print(f"{Color.ERROR}Issue: {issue}{Color.RESET}")
                                                
                                                # Generate diegetic explanation for player
                                                try:
                                                    issues_summary = '; '.join(issues)
                                                    diegetic_explanation = narrator.generate_inquiry_response(
                                                        user_input=action_text,
                                                        scene_description=scene_description,
                                                        actor=proactor,
                                                        context=f"The action '{action_text}' cannot be performed because: {issues_summary}"
                                                    )
                                                    print(f"\n{Color.NARRATIVE}{diegetic_explanation}{Color.RESET}\n")
                                                except Exception:
                                                    print(f"\n{Color.NARRATIVE}The action cannot be completed as intended.{Color.RESET}\n")
                                                
                                                # Clear the action data to skip this turn
                                                proactor_action_data = {}
                                                
                                                # Advance turn queue and continue
                                                try:
                                                    rm = encounter_checker.current_context.round_manager
                                                    _ = rm.advance_turn_queue()
                                                except Exception:
                                                    pass
                                                break  # Exit retry loop
                                        else:
                                            # Soft repetition check (continuity beyond physical possibility)
                                            try:
                                                last_ctx = last_exchange_context if 'last_exchange_context' in locals() else None
                                                rep, rep_reason = _soft_repetition_detected(action_text, last_ctx)
                                                if rep and attempt < max_retries:
                                                    print(f"{Color.WARNING}⚠️ REPETITION DETECTED (Proactor) - Attempt {attempt + 1}/{max_retries + 1}{Color.RESET}")
                                                    print(f"{Color.WARNING}Reason: {rep_reason}{Color.RESET}")
                                                    repetition_feedback = f"""
REPETITION DETECTED - REGENERATION REQUIRED

Your last output was too repetitive and did not advance the scene.

Reason: {rep_reason}

CRITICAL INSTRUCTIONS FOR REGENERATION:
- You MAY reuse a short phrase from the last exchange, but you MUST add meaningful NEW content afterward.
- Add a NEW conversational beat: a new line, a new question, a new boundary, a new offer, or a new consequence.
- Do NOT restate the Step 6 narrative.
- Do NOT repeat the last line of dialogue verbatim unless immediately followed by substantial new content.
"""
                                                    if isinstance(new_guidance, dict):
                                                        new_guidance = dict(new_guidance)
                                                        # Use repair_note since DeciderAgent already surfaces this field.
                                                        new_guidance['repair_note'] = (str(new_guidance.get('repair_note') or '') + "\n" + repetition_feedback).strip()
                                                    else:
                                                        new_guidance = (new_guidance or '') + "\n\n" + repetition_feedback
                                                    print(f"{Color.SYSTEM}Regenerating with repetition feedback...{Color.RESET}")
                                                    continue
                                            except Exception as e:
                                                print(f"{Color.WARNING}[CONTINUITY] Proactor repetition check failed: {e}{Color.RESET}")

                                            # Validation passed - break out of retry loop
                                            break
                                    except Exception as e:
                                        print(f"{Color.WARNING}[CONTINUITY] Proactor validation failed: {e}{Color.RESET}")
                                        # On error, allow action to proceed (fail-open for robustness)
                                        break  # Exit retry loop on exception
                            
                            # Generate perceptual narrative from action decision
                            if proactor_action_data and proactor_action_data.get('narrative_description'):
                                try:
                                    # Pass remote encounter context to narrator
                                    is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                    remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)
                                    
                                    perceptual_narrative = narrator.generate_nua_action_perceptual_narrative(
                                        actor=proactor,
                                        action_data=proactor_action_data,
                                        scene_description=scene_description,
                                        is_proactor=True,
                                        is_remote_encounter=is_remote,
                                        remote_encounter_type=remote_type,
                                        session_id=getattr(tracker, 'session_id', None) if tracker else None,
                                    )
                                    proactor_action_data['narrative_description'] = perceptual_narrative
                                except Exception as e:
                                    print(f"{Color.WARNING}[NARRATOR] Failed to generate perceptual narrative: {e}{Color.RESET}")
                                    # Keep original narrative_description from DeciderAgent
                            
                            # Provide a safe raw input proxy for downstream reporting
                            user_input = (
                                proactor_action_data.get('raw_action')
                                or proactor_action_data.get('narrative_description')
                                or f"{proactor.sheet.name} acts."
                            )
                            # Diagnostics: capture Decider output structure to troubleshoot no-progress turns
                            try:
                                dbg_keys = list(proactor_action_data.keys()) if isinstance(proactor_action_data, dict) else []
                                dbg_has_narr = bool(proactor_action_data.get('narrative_description')) if isinstance(proactor_action_data, dict) else False
                                print(f"{Color.SYSTEM}DEBUG: Decider result keys: {dbg_keys}{Color.RESET}")
                                print(f"{Color.SYSTEM}DEBUG: Decider has narrative_description: {dbg_has_narr}{Color.RESET}")
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}NUA proaction generation error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise
                        # If NUA produced no action, advance the queue immediately to prevent no-progress loops
                        if not proactor_action_data or not proactor_action_data.get('narrative_description'):
                            try:
                                print(f"{Color.WARNING}⚠ No NUA action generated for {proactor.sheet.name}; advancing turn{Color.RESET}")
                            except Exception:
                                pass
                            try:
                                rm = encounter_checker.current_context.round_manager
                                _ = rm.advance_turn_queue()
                            except Exception as e:
                                print(f"{Color.ERROR}Failed to advance turn queue after missing NUA action: {e}{Color.RESET}")
                                import traceback as traceback_module
                                traceback_module.print_exc()
                                raise
                            # Make it explicit why Steps 2–6 won't run for this turn
                            try:
                                print(f"{Color.SYSTEM}DEBUG: Skipping Steps 2-6 due to missing NUA proaction{Color.RESET}")
                            except Exception:
                                pass
                            # Refresh outer loop with next proactor
                            continue
                    
                    # Process the contested exchange if we have proactor action data
                    if proactor_action_data:
                        # 1) Determine reactor based on target detection, fallback to next in queue
                        if reactor is None:
                            try:
                                rm = encounter_checker.current_context.round_manager
                                # Build a rich context snapshot so target detection considers recent developments
                                try:
                                    context_snapshot = _compose_scene_snapshot(
                                        scene_description=scene_description,
                                        time_context=master_time.get_current_time_context(),
                                        last_action_narrative=(last_action_narrative or proactor_action_data.get('narrative_description') or ''),
                                        scene_updates=scene_updates,
                                    )
                                    # Also propagate to the Interpreter for any downstream prompts in this turn
                                    try:
                                        conductor.interpreter._ad_hoc_context_snapshot = context_snapshot
                                    except Exception:
                                        pass
                                except Exception:
                                    context_snapshot = scene_description
                                detected = rm.find_reactor_by_target_detection(user_input, context_snapshot)
                                if detected:
                                    reactor = detected
                                    try:
                                        if hasattr(rm, 'ensure_actor_in_turn_queue') and rm.ensure_actor_in_turn_queue(reactor):
                                            print(f"{Color.INFO}🎯 Targeted actor promoted into turn queue: {getattr(getattr(reactor, 'sheet', None), 'name', 'NPC')}{Color.RESET}")
                                    except Exception:
                                        pass
                                else:
                                    reactor_position = (encounter_checker.current_context.round_manager.turn_queue_position + 1) % len(turn_queue)
                                    reactor = turn_queue[reactor_position]['actor']
                            except Exception:
                                reactor_position = (encounter_checker.current_context.round_manager.turn_queue_position + 1) % len(turn_queue)
                                reactor = turn_queue[reactor_position]['actor']

                        # REPORTER STEP 1: Proactor interpretation
                        try:
                            proactor_for_report = dict(proactor_action_data)
                            proactor_for_report['name'] = proactor.sheet.name
                            proactor_for_report['is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            proactor_for_report['raw_input'] = proactor_action_data.get('raw_action', user_input or 'N/A')
                            encounter_checker.current_context.reporter.report_step1_proactor_interpretation(proactor_for_report)
                            # Display actor sheet only for NUA proactors (avoid UA redundancy and INUA)
                            try:
                                if (not getattr(proactor, 'is_user_actor', False)) and (not getattr(proactor, 'is_inanimate', False)):
                                    _display_actor_sheet_simple(proactor.sheet)
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}Step 1 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise

                        # ARCHITECT: Extract and apply movement from NUA proactor action (N2N path)
                        # NUAs may move as part of any action type (given, fallible, contested)
                        try:
                            from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                            proactor_narrative = proactor_action_data.get('narrative_description', '')
                            if proactor_narrative and not getattr(proactor, 'is_user_actor', False):
                                movement_target = extract_movement_from_narrative(proactor_narrative)
                                if movement_target:
                                    if move_actor_on_map(proactor.sheet.name, movement_target, proactor_narrative):
                                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {proactor.sheet.name} moved to '{movement_target}'")
                        except Exception:
                            pass  # Movement is enhancement, not critical

                        # 2) Generate reactor action data via decision agent
                        # Provide escalation guidance to the reactor NUA (if reactor is NUA)
                        try:
                            if not getattr(reactor, 'is_user_actor', False):
                                r_ctx = nua_context_manager.get_or_create_context(getattr(reactor.sheet, 'name', 'NPC'))
                                rg = r_ctx.get_nua_response_guidance()
                                try:
                                    r_hist = r_ctx.get_turn_history_summary()
                                except Exception:
                                    r_hist = ''
                                try:
                                    loop_state = narrator.get_narrative_loop_state() or {}
                                except Exception:
                                    loop_state = {}
                                try:
                                    recent_narrative = narrative_context_manager.get_context_for_llm(
                                        lookback_events=5,
                                        importance_threshold="notable"
                                    )
                                except Exception:
                                    recent_narrative = ''
                                reaction_guidance = {
                                    'escalation_level': rg.get('escalation_level', 2),
                                    'recommended_action_type': rg.get('recommended_action_type', 'social_response'),
                                    'response_intensity': rg.get('response_intensity', 1),
                                    'context_summary': (rg.get('context_summary') or '') + (f"\nHistory: {r_hist}" if r_hist else '') + (f"\n\nRecent Narrative Context:\n{recent_narrative}" if recent_narrative else ''),
                                    'narrative_mode': loop_state.get('mode'),
                                    'narrative_tone': loop_state.get('tone'),
                                    'narrative_intent': loop_state.get('intent'),
                                }
                            else:
                                reaction_guidance = None
                        except Exception:
                            reaction_guidance = None
                        
                        # CRITICAL: Add remote encounter context to reactor guidance as well
                        try:
                            # DEBUG: Check if remote flags are present for reactor
                            has_remote_flag_reactor = hasattr(encounter_checker.current_context, 'is_remote_encounter')
                            is_remote_value_reactor = getattr(encounter_checker.current_context, 'is_remote_encounter', False) if has_remote_flag_reactor else False
                            print(f"{Color.SYSTEM}[REMOTE DEBUG REACTOR] has_remote_encounter flag: {has_remote_flag_reactor}, value: {is_remote_value_reactor}{Color.RESET}")
                            
                            if hasattr(encounter_checker.current_context, 'is_remote_encounter') and encounter_checker.current_context.is_remote_encounter:
                                remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', 'phone_call')
                                remote_desc = getattr(encounter_checker.current_context, 'remote_encounter_description', 'Remote conversation')
                                print(f"{Color.SUCCESS}[REMOTE DEBUG REACTOR] Phone call context ACTIVE - adding to reactor guidance{Color.RESET}")
                                
                                # Add remote context to reactor guidance
                                if reaction_guidance is None:
                                    reaction_guidance = {}
                                
                                if isinstance(reaction_guidance, dict):
                                    reaction_guidance['is_remote_encounter'] = True
                                    reaction_guidance['remote_encounter_type'] = remote_type
                                    reaction_guidance['remote_constraint'] = (
                                        f"CRITICAL CONSTRAINT: This is a {remote_type.upper().replace('_', ' ')}. "
                                        f"The actors are NOT physically present with each other. "
                                        f"Actions MUST be limited to what can be done over the phone: "
                                        f"speaking, listening, asking questions, sharing information, making plans, ending the call. "
                                        f"FORBIDDEN: Any physical actions like 'approaches', 'walks to', 'touches', 'hands over', etc. "
                                        f"Context: {remote_desc}"
                                    )
                                    # Also add to context_summary for visibility
                                    reaction_guidance['context_summary'] = (
                                        f"[PHONE CALL - NO PHYSICAL PRESENCE]\n{reaction_guidance.get('context_summary', '')}"
                                    )
                                
                                print(f"{Color.SYSTEM}[REMOTE] Added phone call constraint to reactor DeciderAgent context{Color.RESET}")
                        except Exception as e:
                            print(f"{Color.WARNING}[REMOTE] Failed to add remote context to reactor: {e}{Color.RESET}")

                        try:
                            # DEBUG: Log call context before NUA reaction is determined
                            try:
                                print(f"{Color.SYSTEM}NUA REACTOR CALL: proactor={proactor.sheet.name} reactor={reactor.sheet.name}{Color.RESET}")
                            except Exception:
                                pass

                            # Bounded re-prompt loop for reactor generation to handle missing UTAS fields
                            max_retries = 2
                            last_err = None
                            new_guidance = reaction_guidance
                            reactor_action_data = {}
                            for attempt in range(0, max_retries + 1):
                                try:
                                    reactor_action_data = conductor.determine_nua_reaction(
                                        proactor=proactor,
                                        proactor_action_data=proactor_action_data,
                                        reactor=reactor,
                                        context_guidance=new_guidance
                                    ) or {}
                                    
                                    # CRITICAL: Validate reactor action with continuity checker
                                    # This ensures NUA-generated reactions respect physical possibility during exchanges
                                    if reactor_action_data and reactor_action_data.get('narrative_description'):
                                        try:
                                            action_text = reactor_action_data.get('narrative_description', '')
                                            reactor_name = reactor.sheet.name
                                            
                                            # FIRST: Check if this is a remote encounter and validate physical impossibility
                                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                            physical_action_blocked = False
                                            
                                            if is_remote:
                                                # Use LLM to semantically check if action violates remote encounter physics
                                                try:
                                                    from openrouter_config import create_role_client, OpenRouterConfig
                                                    client = create_role_client("coordination")
                                                    
                                                    validation_prompt = f"""This is a PHONE CALL. Two people are in SEPARATE LOCATIONS talking on the phone.

Action to validate: "{action_text}"

CRITICAL RULE: Only flag actions that require PHYSICAL PROXIMITY to the OTHER PERSON.

✅ ALLOWED (person can do these in their own location):
- Picking up ANY object in their location (phone, CD player, book, cup, etc.)
- Speaking, listening, hearing, talking
- Emotional reactions (smiling, frowning, sighing, laughing)
- Moving around their own space
- ANY interaction with objects near them
- Gestures, body language (even if other person can't see)

❌ FORBIDDEN (requires being in same location as other person):
- Touching the OTHER PERSON
- Handing something TO the other person
- Taking something FROM the other person
- Moving TOWARD the other person
- Physical contact with the other person

Question: Does this action require the person to be in the SAME PHYSICAL LOCATION as the other person?
Answer ONLY "YES" (forbidden) or "NO" (allowed)."""

                                                    response = client.chat.completions.create(
                                                        model=OpenRouterConfig.get_model_for_role("coordination"),
                                                        messages=[{"role": "user", "content": validation_prompt}],
                                                        temperature=0.1,
                                                        max_tokens=10
                                                    )
                                                    
                                                    result = response.choices[0].message.content.strip().upper()
                                                    if result == "YES":
                                                        physical_action_blocked = True
                                                        issues = [f"REMOTE ENCOUNTER VIOLATION: Physical action '{action_text[:50]}...' cannot be performed during a phone call"]
                                                except Exception as e:
                                                    # Fallback: if LLM check fails, allow the action
                                                    print(f"{Color.WARNING}[CONTINUITY] Remote validation failed, allowing action: {e}{Color.RESET}")
                                                    physical_action_blocked = False
                                            
                                            # SECOND: Check narrative consistency (location, time, NPC presence)
                                            if not physical_action_blocked:
                                                # Refresh continuity tracker from the latest scene context.
                                                # Without this, continuity_validator can carry a stale location
                                                # (e.g., "road") into an indoor scene like a tavern.
                                                try:
                                                    continuity_validator.update_from_scene(
                                                        scene_description,
                                                        master_time.get_current_time_context() if 'master_time' in locals() else None
                                                    )
                                                except Exception:
                                                    pass
                                                is_valid, issues = continuity_validator.validate_narrative(
                                                    narrative=action_text,
                                                    action=action_text,
                                                    actor_name=reactor_name
                                                )
                                            else:
                                                is_valid = False
                                            
                                            if not is_valid and issues:
                                                # Continuity violation detected - retry with feedback
                                                if attempt < max_retries:
                                                    print(f"{Color.WARNING}⚠️ CONTINUITY VIOLATION (Reactor) - Attempt {attempt + 1}/{max_retries + 1}{Color.RESET}")
                                                    print(f"{Color.WARNING}Action: {action_text[:100]}...{Color.RESET}")
                                                    for issue in issues:
                                                        print(f"{Color.WARNING}Issue: {issue}{Color.RESET}")
                                                    
                                                    # Build feedback for regeneration
                                                    issues_summary = '; '.join(issues)
                                                    continuity_feedback = f"""
CONTINUITY VIOLATION DETECTED - REGENERATION REQUIRED

Previous narrative failed validation:
"{action_text[:200]}..."

Violation reasons:
{issues_summary}

CRITICAL INSTRUCTIONS FOR REGENERATION:
- This is a {'PHONE CALL - actors are in SEPARATE LOCATIONS' if is_remote else 'face-to-face encounter'}
- {'FORBIDDEN: Any physical proximity actions (approaching, touching, gestures visible to other person)' if is_remote else 'Ensure action respects current scene context'}
- {'REQUIRED: Only describe what can be heard over the phone (voice, tone, words, background sounds)' if is_remote else 'Ensure NPCs mentioned are actually present in the scene'}
- Generate a NEW reaction that avoids these violations

Regenerate the reaction now with these corrections applied.
"""
                                                    
                                                    # Add feedback to guidance for next attempt
                                                    if isinstance(new_guidance, dict):
                                                        new_guidance = dict(new_guidance)
                                                        new_guidance['continuity_feedback'] = continuity_feedback
                                                    else:
                                                        new_guidance = (new_guidance or '') + "\n\n" + continuity_feedback
                                                    
                                                    print(f"{Color.SYSTEM}Regenerating with continuity feedback...{Color.RESET}")
                                                    continue  # Retry generation
                                                else:
                                                    # Max retries exceeded - show error and skip
                                                    print(f"{Color.ERROR}⚠️ CONTINUITY VIOLATION (Reactor) - Max retries exceeded{Color.RESET}")
                                                    print(f"{Color.ERROR}Action: {action_text[:100]}...{Color.RESET}")
                                                    for issue in issues:
                                                        print(f"{Color.ERROR}Issue: {issue}{Color.RESET}")
                                                    
                                                    # Generate diegetic explanation for player
                                                    try:
                                                        issues_summary = '; '.join(issues)
                                                        diegetic_explanation = narrator.generate_inquiry_response(
                                                            user_input=action_text,
                                                            scene_description=scene_description,
                                                            actor=reactor,
                                                            context=f"The action '{action_text}' cannot be performed because: {issues_summary}"
                                                        )
                                                        print(f"\n{Color.NARRATIVE}{diegetic_explanation}{Color.RESET}\n")
                                                    except Exception:
                                                        print(f"\n{Color.NARRATIVE}The reaction cannot be completed as intended.{Color.RESET}\n")
                                                    
                                                    # Clear the action data to skip this reaction
                                                    reactor_action_data = {}
                                                    break  # Exit retry loop
                                                # Break out of retry loop since continuity failed
                                                break
                                        except Exception as e:
                                            print(f"{Color.WARNING}[CONTINUITY] Reactor validation failed: {e}{Color.RESET}")
                                            # On error, allow action to proceed (fail-open for robustness)
                                    
                                    # Generate perceptual narrative from reaction decision
                                    if reactor_action_data and reactor_action_data.get('narrative_description'):
                                        try:
                                            # Pass remote encounter context to narrator
                                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)
                                            
                                            perceptual_narrative = narrator.generate_nua_action_perceptual_narrative(
                                                actor=reactor,
                                                action_data=reactor_action_data,
                                                scene_description=scene_description,
                                                is_proactor=False,
                                                is_remote_encounter=is_remote,
                                                remote_encounter_type=remote_type,
                                                session_id=getattr(tracker, 'session_id', None) if tracker else None,
                                            )
                                            reactor_action_data['narrative_description'] = perceptual_narrative
                                        except Exception as e:
                                            print(f"{Color.WARNING}[NARRATOR] Failed to generate perceptual narrative: {e}{Color.RESET}")
                                            # Keep original narrative_description from DeciderAgent
                                    
                                    # If we got here without exception, keep payload (later validation will still run)
                                    break
                                except Exception as ex:
                                    last_err = str(ex)
                                    if attempt >= max_retries:
                                        print(f"{Color.WARNING}⚠️ NUA reactor generation failed after retries. Reason: {last_err}{Color.RESET}")
                                        reactor_action_data = {}
                                        break
                                    # Add explicit repair note for reactor
                                    fix_note = (
                                        "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory REACTOR UTAS fields. "
                                        f"Error: {last_err}. Provide ONLY the missing fields; keep all previously provided fields unchanged. "
                                        "MANDATORY: Include 'shift_polarity' explicitly as 'Additive' or 'Subtractive'. "
                                        "Also ensure 'status_to_shift' is one of SPIRIT, STAMINA, SUPPLY, SYMPATHY. "
                                        "Use this minimal schema for the missing fields (exact key names, JSON only):\n"
                                        "{\n  \"action_description\": \"...\",\n  \"narrative_description\": \"...\",\n  \"utas_factors\": {\n    \"s_trait_to_use\": \"STURDINESS\",\n    \"skill\": \"Customer Service\",\n    \"super\": null,\n    \"supplement_val\": 0,\n    \"status_to_shift\": \"SPIRIT\",\n    \"shift_polarity\": \"Additive\",\n    \"stress_level\": 1,\n    \"has_secondary_effect\": false\n  }\n}"
                                    )
                                    try:
                                        if isinstance(new_guidance, dict):
                                            ng = dict(new_guidance)
                                            ng['repair_note'] = (ng.get('repair_note') or '') + fix_note
                                            # Ensure the repair note is also visible in context_summary
                                            ng['context_summary'] = (ng.get('context_summary') or '') + "\n" + fix_note
                                            new_guidance = ng
                                        else:
                                            new_guidance = {
                                                'context_summary': (new_guidance or ''),
                                                'repair_note': fix_note
                                            }
                                    except Exception:
                                        pass

                            # DEBUG: Symmetric reactor result inspection
                            try:
                                r_keys = list(reactor_action_data.keys()) if isinstance(reactor_action_data, dict) else []
                                r_has_narr = bool(reactor_action_data.get('narrative_description')) if isinstance(reactor_action_data, dict) else False
                                print(f"{Color.SYSTEM}DEBUG: Reactor Decider result keys: {r_keys}{Color.RESET}")
                                print(f"{Color.SYSTEM}DEBUG: Reactor has narrative_description: {r_has_narr}{Color.RESET}")
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}NUA reaction generation error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            # Do not raise; allow late validation to handle abort cleanly
                            reactor_action_data = {}

                        # 3) Execute exchange (with preflight validation + bounded re-prompt)
                        from response_normalizer import ResponseNormalizer
                        def _validate_or_reprompt_late(role: str, data: dict, guidance: str, max_retries: int = 2):
                            attempts = 0
                            last_err = None
                            # Determine is_user_actor for sensory perspective
                            proactor_is_ua = getattr(proactor, 'is_user_actor', False)
                            reactor_is_ua = getattr(reactor, 'is_user_actor', False)
                            for attempts in range(0, max_retries + 1):
                                try:
                                    if role == 'proactor':
                                        _ = ResponseNormalizer.normalize_proactor_action_response(data, proactor.sheet.name, "takes action", proactor_is_ua)
                                    else:
                                        _ = ResponseNormalizer.normalize_reactor_response(data, reactor.sheet.name, "reacts defensively", reactor_is_ua)
                                    return data, attempts, None
                                except Exception as ex:
                                    last_err = str(ex)
                                    if attempts >= max_retries:
                                        break
                                    # Build targeted repair note and merge with guidance (dict or str)
                                    if role == 'reactor':
                                        fix_note = (
                                            "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory REACTOR UTAS fields. "
                                            f"Error: {last_err}. Provide ONLY the missing fields; keep all previously provided fields unchanged. "
                                            "MANDATORY: Include 'shift_polarity' explicitly as 'Additive' or 'Subtractive' (no numbers, no blanks). "
                                            "Example: \"shift_polarity\": \"Additive\". Also ensure 'status_to_shift' is one of SPIRIT, STAMINA, SUPPLY, SYMPATHY."
                                        )
                                    else:
                                        fix_note = (
                                            "\nREPAIR INSTRUCTIONS: The previous interpretation was missing mandatory UTAS fields. "
                                            f"Error: {last_err}. Provide ONLY the missing fields, keep all previously provided fields unchanged."
                                        )
                                    try:
                                        if isinstance(guidance, dict):
                                            ng = dict(guidance)
                                            ng['repair_note'] = (ng.get('repair_note') or '') + fix_note
                                            ng['context_summary'] = (ng.get('context_summary') or '') + "\n" + fix_note
                                            new_guidance = ng
                                        else:
                                            new_guidance = {
                                                'context_summary': (guidance or ''),
                                                'repair_note': fix_note
                                            }
                                    except Exception:
                                        new_guidance = {'repair_note': fix_note}
                                    try:
                                        if role == 'proactor':
                                            data = conductor.determine_nua_proaction(
                                                proactor=proactor,
                                                reactor=reactor,
                                                context_guidance=new_guidance,
                                                last_exchange_context=last_exchange_context if 'last_exchange_context' in locals() else None
                                            ) or {}
                                        else:
                                            data = conductor.determine_nua_reaction(
                                                proactor=proactor,
                                                reactor=reactor,
                                                context_guidance=new_guidance
                                            ) or {}
                                    except Exception:
                                        # Keep looping to allow next retry attempt
                                        data = {}
                                        continue
                            return None, attempts, last_err or "Unknown validation error"

                        p_valid, p_attempts, p_err = _validate_or_reprompt_late('proactor', proactor_action_data, (context_guidance if 'context_guidance' in locals() else None))
                        r_valid, r_attempts, r_err = _validate_or_reprompt_late(
                            'reactor',
                            reactor_action_data,
                            (reaction_guidance if 'reaction_guidance' in locals() else (context_guidance if 'context_guidance' in locals() else None))
                        )

                        if p_valid is None or r_valid is None:
                            result = {
                                'proactor_results': {},
                                'reactor_results': {},
                                'outcome_results': {
                                    'exchange_aborted': True,
                                    'abort_reason': (
                                        (f"Proactor invalid: {p_err}. " if p_valid is None else "") +
                                        (f"Reactor invalid: {r_err}." if r_valid is None else "")
                                    ).strip(),
                                    're_prompt_attempts': {
                                        'proactor': p_attempts if p_valid is None else p_attempts,
                                        'reactor': r_attempts if r_valid is None else r_attempts
                                    },
                                    'status_shifts': [],
                                    'applied_self_effects': []
                                }
                            }
                        else:
                            proactor_action_data = p_valid
                            reactor_action_data = r_valid
                            try:
                                from exchange_system import Exchange
                                exch = Exchange(
                                    proactor=proactor,
                                    reactor=reactor,
                                    proactor_action_data=proactor_action_data,
                                    reactor_action_data=reactor_action_data,
                                    recovery_integrator=encounter_checker.current_context.enhanced_recovery
                                )
                                result = exch.execute(is_inua_exchange=getattr(reactor, 'is_inanimate', False))
                                
                                # Process witness reactions to the exchange
                                witnesses = [npc for npc in available_npcs if npc != proactor and npc != reactor]
                                if witnesses:
                                    witness_reactions = exch.process_witness_reactions(witnesses, scene_description, result)
                                    # Display witness reactions to show simulation effect
                                    if witness_reactions and _witness_system:
                                        _witness_system.display_witness_reactions(witness_reactions)
                                    # Handle behavioral changes from reactions
                                    for reaction in witness_reactions:
                                        if reaction['behavioral_change'] == 'leave_scene':
                                            witness = next((w for w in witnesses if w.sheet.name == reaction['witness']), None)
                                            if witness and witness in available_npcs:
                                                available_npcs.remove(witness)
                                                continuity_validator.mark_npc_departed(witness.sheet.name)
                                
                            except Exception as e:
                                print(f"{Color.ERROR}Exchange execution error: {e}{Color.RESET}")
                                import traceback as traceback_module
                                traceback_module.print_exc()
                                raise

                        # 4) Extract success data and outcome
                        proactor_success_data = result.get('proactor_results', {})
                        reactor_success_data = result.get('reactor_results', {})
                        exchange_outcome = result.get('outcome_results', {})
                        
                        # Process monetary transaction if detected (after exchange resolution)
                        # Transaction narrative will be shown after Step 6 final narrative
                        transaction_narrative = ""
                        if monetary_data.get("transaction_detected"):
                            try:
                                # Determine if proactor succeeded
                                proactor_total = proactor_success_data.get('total', 0)
                                reactor_total = reactor_success_data.get('total', 0)
                                proactor_succeeded = proactor_total > reactor_total
                                
                                # Get targeted status to avoid duplicate sympathy shifts
                                targeted_status = proactor_action_data.get('utas_factors', {}).get('status_to_shift')
                                
                                can_proceed, transaction_narrative, consequences = monetary_processor.process_enhanced_transaction(
                                    monetary_data=monetary_data,
                                    proactor=proactor,
                                    reactor=reactor,
                                    success=proactor_succeeded,
                                    targeted_status=targeted_status
                                )
                            except Exception as e:
                                print(f"{Color.ERROR}Transaction processing error: {e}{Color.RESET}")

                        # REPORTER STEP 2: Proactor success calculation & narrative
                        try:
                            proactor_for_step2 = dict(proactor_action_data)
                            proactor_for_step2['name'] = proactor.sheet.name
                            proactor_for_step2['is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            proactor_for_step2['actor'] = proactor
                            proactor_for_step2['reactor_actor'] = reactor
                            proactor_for_step2['ua_actor'] = (proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None))
                            # Pass reactor info for UA pronoun conversion
                            proactor_for_step2['reactor_name'] = reactor.sheet.name
                            proactor_for_step2['reactor_is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            # Map Exchange results to reporter schema (no forced defaults)
                            scalc = dict(proactor_success_data) if isinstance(proactor_success_data, dict) else {}
                            proactor_for_step2['success_calculation'] = scalc
                            # Include factors for N2N attempt summary
                            proactor_for_step2['utas_factors'] = proactor_action_data.get('utas_factors', {})
                            # Ensure narrative is available to EnhancedReporter Step 2
                            proactor_for_step2['attempt_narrative'] = (
                                proactor_action_data.get('attempt_narrative')
                                or proactor_action_data.get('narrative_description')
                                or ''
                            )
                            encounter_checker.current_context.reporter.report_step2_proactor_success(proactor_for_step2)
                            # Detailed breakdown handled by EnhancedReporter; avoid duplicate custom prints

                            try:
                                ua_for_vis = proactor_for_step2.get('ua_actor')
                                if ua_for_vis is not None and _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                    _interval = 2
                                    try:
                                        _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                    except Exception:
                                        _interval = 2
                                    if _interval < 1:
                                        _interval = 1
                                    if (2 % _interval) == 0:
                                        _trigger_realtime_image(
                                            ua_actor=ua_for_vis,
                                            scene_description=scene_description,
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                            spoken_line=str(proactor_action_data.get('narrative_description', '') or ''),
                                            source="perceptual",
                                            reason="exchange_step2",
                                        )
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}Step 2 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise

                        # REPORTER STEP 3: Reactor interpretation (use proactor summary)
                        try:
                            proactor_summary = f"{proactor.sheet.name}: {proactor_action_data.get('narrative_description', 'Proactor attempted an action.')}"
                            reactor_for_report = dict(reactor_action_data)
                            reactor_for_report['name'] = reactor.sheet.name
                            reactor_for_report['is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            # Display actor sheet only for NUA reactors (avoid UA redundancy and INUA)
                            try:
                                if (not getattr(reactor, 'is_user_actor', False)) and (not getattr(reactor, 'is_inanimate', False)):
                                    _display_actor_sheet_simple(reactor.sheet)
                            except Exception:
                                pass
                            encounter_checker.current_context.reporter.report_step3_reactor_interpretation(reactor_for_report, proactor_summary)
                        except Exception as e:
                            print(f"{Color.ERROR}Step 3 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise

                        # ARCHITECT: Extract and apply movement from reactor action (N2N path)
                        # Reactors (NUA/MNUA) may move as part of their reaction (dodge, retreat, approach)
                        try:
                            from agents.architect_agent import move_actor_on_map, extract_movement_from_narrative
                            reactor_narrative = reactor_action_data.get('narrative_description', '')
                            if reactor_narrative and not getattr(reactor, 'is_user_actor', False):
                                movement_target = extract_movement_from_narrative(reactor_narrative)
                                if movement_target:
                                    if move_actor_on_map(reactor.sheet.name, movement_target, reactor_narrative):
                                        print(f"{Color.CYAN}🏛️ ARCHITECT{Color.RESET} {reactor.sheet.name} moved to '{movement_target}'")
                        except Exception:
                            pass  # Movement is enhancement, not critical

                        # Consolidated end-of-turn summary (Output.md-style)
                        # FIX BUG #4: Initialize variables before use to prevent NameError
                        if 'step6_outcome_data' not in locals():
                            step6_outcome_data = {}
                        if 'final_narrative' not in locals():
                            final_narrative = ''
                        
                        try:
                            turn_summary_data = {
                                'turn_queue_data': turn_queue_data if 'turn_queue_data' in locals() else None,
                                'proactor_data': (lambda d: (d.update({'name': ("You" if getattr(proactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(proactor))}) or d))(dict(proactor_action_data)),
                                'reactor_data': (lambda d: (d.update({'name': ("You" if getattr(reactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(reactor))}) or d))(dict(reactor_action_data)),
                                'outcome_data': step6_outcome_data,
                                'final_narrative': final_narrative,
                            }
                            encounter_checker.current_context.reporter.report_full_turn(turn_summary_data, narrator_agent=narrator)
                        except Exception as e:
                            print(f"{Color.ERROR}Turn summary reporting error: {e}{Color.RESET}")
                        
                        # ============================================================
                        # TIME ADVANCEMENT - CRITICAL
                        # ============================================================
                        # EVERY exchange turn must advance time - no exceptions
                        # Contested actions = 3 seconds per turn
                        # ============================================================
                        try:
                            from master_time_coordinator import TimeAdvancementRequest, TimeEventType
                            
                            # Exchange turns are 3 seconds
                            time_category = RuleOf3Category.THREE_SECOND
                            
                            # Create time advancement request
                            time_request = TimeAdvancementRequest(
                                event_type=TimeEventType.ENCOUNTER_TURN,
                                rule_of_3_category=time_category,
                                requester_system="exchange_turn",
                                actor_name=proactor.sheet.name,
                                description=f"Exchange turn: {user_input}"
                            )
                            
                            # Advance time through master coordinator
                            time_result = master_time.request_time_advancement(time_request)
                            
                            if not SUPPRESS_DEBUG:
                                elapsed = simulation_time_tracker.get_simulation_time_display()
                                print(f"{Color.SYSTEM}⏰ Time advanced: +{time_result.duration_advanced_seconds}s | Clock: {time_result.new_time.format_full()} | Elapsed: {elapsed}{Color.RESET}")
                        except Exception as e:
                            logger.log_system(f"Time advancement error (exchange): {e}")
                            if not SUPPRESS_DEBUG:
                                import traceback as traceback_module
                                traceback_module.print_exc()

                        # REPORTER STEP 4: Reactor success calculation & narrative
                        try:
                            reactor_for_step4 = dict(reactor_action_data)
                            reactor_for_step4['name'] = ("You" if getattr(reactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(reactor))
                            reactor_for_step4['is_user_actor'] = getattr(reactor, 'is_user_actor', False)
                            reactor_for_step4['actor'] = reactor
                            reactor_for_step4['ua_actor'] = (proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None))
                            # Pass proactor info for UA pronoun conversion
                            reactor_for_step4['proactor_name'] = proactor.sheet.name
                            reactor_for_step4['proactor_is_user_actor'] = getattr(proactor, 'is_user_actor', False)
                            # Map Exchange results to reporter schema (no forced defaults)
                            rcalc = dict(reactor_success_data) if isinstance(reactor_success_data, dict) else {}
                            reactor_for_step4['success_calculation'] = rcalc
                            # Include factors for N2N reaction summary
                            reactor_for_step4['utas_factors'] = reactor_action_data.get('utas_factors', {})
                            # Ensure narrative is available to EnhancedReporter Step 4
                            reactor_for_step4['attempt_narrative'] = (
                                reactor_action_data.get('attempt_narrative')
                                or reactor_action_data.get('narrative_description')
                                or ''
                            )
                            encounter_checker.current_context.reporter.report_step4_reactor_success(reactor_for_step4)
                            # Detailed breakdown handled by EnhancedReporter; avoid duplicate custom prints

                            try:
                                ua_for_vis = reactor_for_step4.get('ua_actor')
                                if ua_for_vis is not None and _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                    _interval = 2
                                    try:
                                        _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                    except Exception:
                                        _interval = 2
                                    if _interval < 1:
                                        _interval = 1
                                    if (4 % _interval) == 0:
                                        _trigger_realtime_image(
                                            ua_actor=ua_for_vis,
                                            scene_description=scene_description,
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                            spoken_line=str(reactor_action_data.get('narrative_description', '') or ''),
                                            source="perceptual",
                                            reason="exchange_step4",
                                        )
                            except Exception:
                                pass
                        except Exception as e:
                            print(f"{Color.ERROR}Step 4 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise

                        # REPORTER STEP 5: Final outcome & status updates
                        try:
                            # FIX BUG #1: Get success values directly from exchange result
                            pro_total = result.get('proactor_success', proactor_success_data.get('total', proactor_success_data.get('final_result', proactor_success_data.get('success', 0))) if isinstance(proactor_success_data, dict) else 0)
                            rea_total = result.get('reactor_success', reactor_success_data.get('total', reactor_success_data.get('final_result', reactor_success_data.get('success', 0))) if isinstance(reactor_success_data, dict) else 0)
                            outcome_for_reporter = {
                                'proactor_successes': pro_total,
                                'reactor_successes': rea_total,
                                'margin': (pro_total - rea_total),
                                'proactor_name': proactor.sheet.name,
                                'reactor_name': reactor.sheet.name,
                                'stress_context': exchange_outcome.get('stress_context', ''),
                                'shift_calc_formula': exchange_outcome.get('shift_calc_formula') or exchange_outcome.get('shift_calc', ''),
                                'status_shifts': exchange_outcome.get('status_shifts', []),
                                'applied_self_effects': exchange_outcome.get('applied_self_effects', []),
                                'exchange_aborted': exchange_outcome.get('exchange_aborted', False),
                                'abort_reason': exchange_outcome.get('abort_reason'),
                                're_prompt_attempts': exchange_outcome.get('re_prompt_attempts', {})
                            }
                            encounter_checker.current_context.reporter.report_step5_final_outcome(outcome_for_reporter)
                            # Outcome analysis handled by EnhancedReporter; avoid duplicate custom prints
                        except Exception as e:
                            print(f"{Color.ERROR}Step 5 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise

                        # 5) Generate final narrative (use EnhancedReporter step 6 synthesis)
                        # Note: reporter.step6 expects structured proactor/reactor/outcome data and the narrator agent
                        # FIX BUG #4: Initialize variables before try block to prevent NameError
                        step6_outcome_data = {}
                        final_narrative = ''
                        
                        try:
                            # Prefer the enriched Step 5 payload so Step 6 has explicit totals
                            try:
                                step6_outcome_data = outcome_for_reporter  # from Step 5 block above
                            except NameError:
                                # Fallback: compose minimal payload with totals and shifts
                                # FIX BUG #1: Get success values directly from exchange result
                                try:
                                    p_total = result.get('proactor_success', proactor_success_data.get('total', proactor_success_data.get('final_result', proactor_success_data.get('success', 0))) if isinstance(proactor_success_data, dict) else 0)
                                except Exception:
                                    p_total = 0
                                try:
                                    r_total = result.get('reactor_success', reactor_success_data.get('total', reactor_success_data.get('final_result', reactor_success_data.get('success', 0))) if isinstance(reactor_success_data, dict) else 0)
                                except Exception:
                                    r_total = 0
                                step6_outcome_data = {
                                    'proactor_successes': p_total,
                                    'reactor_successes': r_total,
                                    'status_shifts': exchange_outcome.get('status_shifts', []) if isinstance(exchange_outcome, dict) else []
                                }
                            # Ensure names are present for Step 6
                            pro_for_step6 = dict(proactor_action_data)
                            rea_for_step6 = dict(reactor_action_data)
                            pro_for_step6.setdefault('name', getattr(getattr(proactor, 'sheet', None), 'name', ''))
                            rea_for_step6.setdefault('name', getattr(getattr(reactor, 'sheet', None), 'name', ''))
                            pro_for_step6.setdefault('is_user_actor', getattr(proactor, 'is_user_actor', False))
                            rea_for_step6.setdefault('is_user_actor', getattr(reactor, 'is_user_actor', False))
                            pro_for_step6.setdefault('actor', proactor)
                            rea_for_step6.setdefault('actor', reactor)
                            
                            # FIX BUG #9: Use current scene context for exchange narrative
                            # Pass remote encounter flags to prevent physical presence narratives during phone calls
                            is_remote = getattr(encounter_checker.current_context, 'is_remote_encounter', False)
                            remote_type = getattr(encounter_checker.current_context, 'remote_encounter_type', None)

                            ua_for_step6 = proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None)
                            
                            final_narrative = encounter_checker.current_context.reporter.report_step6_narrative_outcome(
                                proactor_data=pro_for_step6,
                                reactor_data=rea_for_step6,
                                outcome_data=step6_outcome_data,
                                narrator_agent=narrator,
                                scene_context=get_current_scene(),
                                is_remote_encounter=is_remote,
                                remote_encounter_type=remote_type,
                                ua_actor=ua_for_step6
                            )

                            # Apply any deferred spatial movement intent ONLY after Step 6 (outcome) is committed.
                            try:
                                pending_intent = getattr(encounter_checker.current_context, 'pending_exchange_spatial_intent', None)
                            except Exception:
                                pending_intent = None

                            try:
                                if isinstance(pending_intent, dict) and not step6_outcome_data.get('exchange_aborted'):
                                    from spatial_context_system import get_spatial_manager, Position
                                    from agents.architect_agent import resolve_movement_target
                                    from pygame_spatial_map import auto_sync_map

                                    spatial_tmp = get_spatial_manager(session_id=getattr(tracker, 'session_id', None) if tracker else None)
                                    ctx_tmp = spatial_tmp.get_current_context() if spatial_tmp else None
                                    ua_pos = spatial_tmp.get_actor_position('ua_001') if spatial_tmp else None
                                    if spatial_tmp and ctx_tmp and ua_pos:
                                        target_name = str(pending_intent.get('target_name') or '').strip()
                                        dest_target = str(pending_intent.get('destination') or '').strip()

                                        # Resolve the destination first if present; else just approach the target.
                                        dest_pos = None
                                        if dest_target:
                                            dest = resolve_movement_target(
                                                target=dest_target,
                                                current_position=(ua_pos.x, ua_pos.y),
                                                spatial_context=ctx_tmp,
                                                user_input=str(pending_intent.get('raw_user_input') or '')
                                            )
                                            if dest:
                                                dest_pos = Position(float(dest[0]), float(dest[1]))

                                        # Resolve target actor_id by name in the current context.
                                        target_actor_id = None
                                        if target_name:
                                            try:
                                                tnl = target_name.lower()
                                                for _aid, _ap in (getattr(ctx_tmp, 'actor_positions', {}) or {}).items():
                                                    try:
                                                        anm = str(getattr(_ap, 'actor_name', '') or '').strip().lower()
                                                    except Exception:
                                                        anm = ''
                                                    if not anm:
                                                        continue
                                                    if tnl in anm or anm in tnl:
                                                        target_actor_id = _aid
                                                        break
                                            except Exception:
                                                target_actor_id = None

                                        if dest_pos is None and target_name:
                                            # Approach the target at ~1.5 units if no destination.
                                            dest = resolve_movement_target(
                                                target=target_name,
                                                current_position=(ua_pos.x, ua_pos.y),
                                                spatial_context=ctx_tmp,
                                                user_input=str(pending_intent.get('raw_user_input') or '')
                                            )
                                            if dest:
                                                dest_pos = Position(float(dest[0]), float(dest[1]))

                                        if dest_pos is not None:
                                            try:
                                                spatial_tmp.move_actor('ua_001', dest_pos)
                                            except Exception:
                                                pass

                                            if target_actor_id and target_actor_id != 'ua_001':
                                                try:
                                                    h = float(getattr(ctx_tmp.location_dimensions, 'height', dest_pos.y + 0.6) or (dest_pos.y + 0.6))
                                                except Exception:
                                                    h = float(dest_pos.y + 0.6)
                                                try:
                                                    spatial_tmp.move_actor(target_actor_id, Position(dest_pos.x, min(dest_pos.y + 0.6, h)))
                                                except Exception:
                                                    try:
                                                        spatial_tmp.move_actor(target_actor_id, dest_pos)
                                                    except Exception:
                                                        pass

                                            try:
                                                auto_sync_map(session_id=getattr(tracker, 'session_id', None) if tracker else None)
                                            except Exception:
                                                pass

                                    try:
                                        setattr(encounter_checker.current_context, 'pending_exchange_spatial_intent', None)
                                    except Exception:
                                        pass
                            except Exception:
                                try:
                                    setattr(encounter_checker.current_context, 'pending_exchange_spatial_intent', None)
                                except Exception:
                                    pass

                            try:
                                if ua_for_step6 is not None and _env_bool("VIS_IMAGE_AUTOGEN_EXCHANGE", False):
                                    _interval = 2
                                    try:
                                        _interval = int(os.getenv("VIS_IMAGE_AUTOGEN_EXCHANGE_INTERVAL") or "2")
                                    except Exception:
                                        _interval = 2
                                    if _interval < 1:
                                        _interval = 1
                                    if (6 % _interval) == 0:
                                        _trigger_realtime_image(
                                            ua_actor=ua_for_step6,
                                            scene_description=get_current_scene(),
                                            current_location=str(current_location or ''),
                                            time_context=master_time.get_current_time_context() if 'master_time' in locals() and master_time else {},
                                            creator_agent=scene_creator if 'scene_creator' in locals() else None,
                                            seed=None,
                                            spoken_line=str(final_narrative or ''),
                                            source="perceptual",
                                            reason="exchange_step6",
                                        )
                            except Exception:
                                pass
                            try:
                                _apply_narrative_item_gains_to_ua(final_narrative, ua_for_step6)
                            except Exception:
                                pass
                            # Append transaction narrative if present
                            if transaction_narrative:
                                print(f"{Color.NARRATIVE}{transaction_narrative}{Color.RESET}")
                            
                            # STRANGER SYSTEM: Detect if any NPC introduced themselves in the narrative
                            if STRANGER_DESCRIPTION_AVAILABLE and detect_name_introduction and final_narrative:
                                try:
                                    learned = detect_name_introduction(final_narrative, available_npcs)
                                    if learned:
                                        print(f"{Color.SUCCESS}[NAME LEARNED] You now know: {', '.join(learned)}{Color.RESET}")
                                except Exception:
                                    pass
                        except Exception as e:
                            print(f"{Color.ERROR}Step 6 reporting error: {e}{Color.RESET}")
                            import traceback as traceback_module
                            traceback_module.print_exc()
                            raise
                        # Consolidated end-of-turn summary (Output.md-style)
                        # FIX BUG #4: Initialize variables before use to prevent NameError
                        if 'step6_outcome_data' not in locals():
                            step6_outcome_data = {}
                        if 'final_narrative' not in locals():
                            final_narrative = ''
                        
                        try:
                            turn_summary_data = {
                                'turn_queue_data': turn_queue_data if 'turn_queue_data' in locals() else None,
                                'proactor_data': (lambda d: (d.update({'name': ("You" if getattr(proactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(proactor))}) or d))(dict(proactor_action_data)),
                                'reactor_data': (lambda d: (d.update({'name': ("You" if getattr(reactor, 'is_user_actor', False) else __import__('multi_actor_manager')._safe_display_name(reactor))}) or d))(dict(reactor_action_data)),
                                'outcome_data': step6_outcome_data,
                                'final_narrative': final_narrative,
                            }
                            encounter_checker.current_context.reporter.report_full_turn(turn_summary_data, narrator_agent=narrator)
                        except Exception:
                            pass
                        # Update narrative loop with contested outcome snapshot
                        try:
                            outcome_data = {
                                'proactor_success': proactor_success_data.get('total', proactor_success_data.get('final_result', 0)) if isinstance(proactor_success_data, dict) else 0,
                                'reactor_success': reactor_success_data.get('total', reactor_success_data.get('final_result', 0)) if isinstance(reactor_success_data, dict) else 0,
                            }
                            # Provide a safe user_input for NUA path
                            safe_input = user_input or proactor_action_data.get('narrative_description') or proactor_action_data.get('raw_action') or ''
                            turn_data = _build_turn_data(
                                user_input=safe_input,
                                scene_description=scene_description,
                                current_mode=current_mode,
                                continuity={'judgment': 'Possible'},
                                outcome_data=outcome_data
                            )
                            turn_data['narrative_response'] = last_action_narrative
                            framing2 = narrative_loop.process_turn(
                                turn_data=turn_data,
                                scene_description=scene_description,
                                time_context=time_context,
                                available_npcs=available_npcs
                            )
                            try:
                                if framing2 and framing2.get('mode_changed'):
                                    print(f"{Color.SYSTEM}🔀 Mode Shift → {framing2.get('mode', 'unknown').upper()} (Tone: {framing2.get('tone', 'unknown')}){Color.RESET}")
                            except Exception:
                                pass
                        except Exception:
                            pass
                        # Track encounter narrative for snapshot integration
                        last_action_narrative = final_narrative
                        scene_updates.append(final_narrative)
                        
                        # Store last exchange context for next NUA proaction (UA proactor path)
                        try:
                            last_exchange_context = {
                                'proactor_name': proactor.sheet.name,
                                'reactor_name': reactor.sheet.name,
                                'proactor_action': proactor_action_data.get('narrative_description', 'acted'),
                                'reactor_action': reactor_action_data.get('narrative_description', 'reacted'),
                                'outcome_narrative': final_narrative,
                                'winner': exchange_outcome.get('winner', 'unknown') if isinstance(exchange_outcome, dict) else 'unknown',
                                'status_shifts': exchange_outcome.get('status_shifts', []) if isinstance(exchange_outcome, dict) else [],
                            }
                        except Exception:
                            last_exchange_context = None
                        
                        # Track narrative event with full context
                        narrative_context_manager.add_narrative_event(
                            event_type=NarrativeEventType.DIALOGUE_EXCHANGE,
                            narrative_text=final_narrative,
                            actors_involved=[proactor.sheet.name, reactor.sheet.name],
                            importance=NarrativeImportance.IMPORTANT,
                            emotional_tone="dramatic",
                            scene_context=f"Scene {scene_number} contested exchange"
                        )
                        
                        # ═══════════════════════════════════════════════════════════
                        # NUA MEMORY RECORDING - Track significant interactions
                        # ═══════════════════════════════════════════════════════════
                        try:
                            # Get exchange data for memory classification
                            exch_winner = exchange_outcome.get('winner') if isinstance(exchange_outcome, dict) else None
                            exchange_type = proactor_action_data.get('utas_factors', {}).get('exchange_type', '').upper()
                            shift_polarity = proactor_action_data.get('utas_factors', {}).get('shift_polarity', '').lower()
                            action_description = proactor_action_data.get('narrative_description', '')
                            
                            # Determine which actor is NUA (only record for NUAs, not UAs)
                            proactor_is_nua = not getattr(proactor, 'is_user_actor', False)
                            reactor_is_nua = not getattr(reactor, 'is_user_actor', False)
                            
                            # 1. THREAT DETECTION - Record if UA threatened NUA
                            if reactor_is_nua and exchange_type == 'SPIRIT' and shift_polarity == 'subtractive':
                                # Check for threatening keywords or intimidation
                                threat_keywords = ['threaten', 'intimidate', 'weapon', 'gun', 'knife', 'hurt', 'kill', 'attack']
                                is_threat = any(keyword in action_description.lower() for keyword in threat_keywords)
                                
                                if is_threat and exch_winner == 'proactor':
                                    nua_memory_system.record_threat(
                                        nua_name=reactor.sheet.name,
                                        threatener_name=proactor.sheet.name,
                                        threat_description=action_description[:100]
                                    )
                            
                            # 2. HELP DETECTION - Record if UA helped NUA
                            if reactor_is_nua and shift_polarity == 'additive':
                                # Check for helpful actions
                                help_keywords = ['help', 'heal', 'give', 'assist', 'support', 'aid', 'protect', 'save']
                                is_help = any(keyword in action_description.lower() for keyword in help_keywords)
                                
                                if is_help and exch_winner == 'proactor':
                                    nua_memory_system.record_help(
                                        nua_name=reactor.sheet.name,
                                        helper_name=proactor.sheet.name,
                                        help_description=action_description[:100]
                                    )
                            
                            # 3. VIOLENCE DETECTION - Record if UA attacked NUA or vice versa
                            if exchange_type == 'STAMINA' and shift_polarity == 'subtractive':
                                # Physical violence occurred
                                if reactor_is_nua and exch_winner == 'proactor':
                                    # UA attacked NUA - record as violence received
                                    nua_memory_system.record_event(
                                        nua_name=reactor.sheet.name,
                                        event_type="violence_received",
                                        description=f"{proactor.sheet.name} attacked: {action_description[:80]}",
                                        actors_involved=[proactor.sheet.name],
                                        importance=4,
                                        emotional_impact="traumatized"
                                    )
                                
                                # Check for witnesses (other NUAs in scene)
                                for npc in available_npcs:
                                    if npc.sheet.name != proactor.sheet.name and npc.sheet.name != reactor.sheet.name:
                                        # This NUA witnessed the violence
                                        nua_memory_system.record_witnessed_violence(
                                            nua_name=npc.sheet.name,
                                            perpetrator_name=proactor.sheet.name,
                                            victim_name=reactor.sheet.name,
                                            violence_description=action_description[:80]
                                        )
                            
                            # 4. CONVERSATION DETECTION - Record significant dialogue
                            dialogue_metadata = proactor_action_data.get('dialogue_metadata', {})
                            if dialogue_metadata.get('dialogue_detected'):
                                dialogue_intent = dialogue_metadata.get('dialogue_intent', 'None')
                                # Only record non-trivial conversations
                                significant_intents = ['Inquiry', 'Persuasion', 'Negotiation', 'Story', 'Command']
                                
                                if reactor_is_nua:
                                    if dialogue_intent in significant_intents:
                                        nua_memory_system.record_conversation(
                                            nua_name=reactor.sheet.name,
                                            other_actor=proactor.sheet.name,
                                            topic=dialogue_intent,
                                            key_points=action_description[:80]
                                        )
                                    # Always-on: keep a lightweight summary so small talk still accumulates continuity
                                    try:
                                        _desc = (action_description or '').strip()
                                        if _desc:
                                            nua_memory_system.record_event(
                                                nua_name=reactor.sheet.name,
                                                event_type='conversation_summary',
                                                description=f"Chatted with {proactor.sheet.name}: {_desc[:160]}",
                                                actors_involved=[proactor.sheet.name],
                                                importance=1,
                                                emotional_impact='neutral'
                                            )
                                    except Exception:
                                        pass

                                if proactor_is_nua:
                                    # Also remember what the NUA said/did during dialogue with the other actor
                                    try:
                                        _desc = (action_description or '').strip()
                                        if _desc:
                                            nua_memory_system.record_event(
                                                nua_name=proactor.sheet.name,
                                                event_type='conversation_summary',
                                                description=f"Chatted with {reactor.sheet.name}: {_desc[:160]}",
                                                actors_involved=[reactor.sheet.name],
                                                importance=1,
                                                emotional_impact='neutral'
                                            )
                                    except Exception:
                                        pass

                            try:
                                # 5. GENERAL EXCHANGE OUTCOME MEMORY (broad coverage)
                                # Record a concise outcome memory for any NUA participant, so recent events can be recalled
                                # with high fidelity (and decay later in npc_memory_system).
                                try:
                                    _ad = (action_description or '').strip()
                                    _ad_clip = _ad[:220]
                                    _winner = exch_winner
                                    _etype = exchange_type
                                    _pol = shift_polarity

                                    # Pull a salient "what was used" hint (often an item name) when available.
                                    _supp = ''
                                    try:
                                        _uf = proactor_action_data.get('utas_factors', {}) if isinstance(proactor_action_data, dict) else {}
                                        _supp = str(_uf.get('supplement') or '').strip()
                                        if _supp.lower() in ('none', 'null'):
                                            _supp = ''
                                    except Exception:
                                        _supp = ''

                                    _supp_txt = f" Used: {_supp}." if _supp else ''

                                    # Light semantic classification for better recall behavior.
                                    _txt_l = _ad.lower()
                                    _is_trade = any(k in _txt_l for k in ('buy', 'bought', 'sell', 'sold', 'pay', 'paid', 'price', 'coin', 'soldi', 'ducat', 'ducats', 'trade', 'barter'))
                                    _is_gift = any(k in _txt_l for k in ('gift', 'give', 'gave', 'hand', 'handed', 'offer', 'offered'))
                                    _is_theft = any(k in _txt_l for k in ('steal', 'stole', 'rob', 'robbed', 'pickpocket', 'took'))
                                    _is_promise = any(k in _txt_l for k in ('promise', 'agree', 'deal', 'bargain', 'swear'))

                                    _mem_type = 'exchange_summary'
                                    _impact = 'neutral'
                                    _imp = 2

                                    # Supply shifts are usually item/money related (good anchor for remembering purchases/gifts/loss).
                                    if _etype == 'SUPPLY':
                                        if _pol == 'additive':
                                            _mem_type = 'supply_gain'
                                            _impact = 'relieved'
                                            _imp = 3
                                            if _is_trade:
                                                _mem_type = 'purchase_or_trade'
                                            elif _is_gift:
                                                _mem_type = 'gift_received'
                                        elif _pol == 'subtractive':
                                            _mem_type = 'supply_loss'
                                            _impact = 'angry'
                                            _imp = 3
                                            if _is_theft:
                                                _mem_type = 'theft_or_robbery'
                                                _imp = 4
                                    elif _etype == 'STAMINA' and _pol == 'subtractive':
                                        _mem_type = 'violence'
                                        _impact = 'fearful'
                                        _imp = 4
                                    elif _etype in ('SPIRIT', 'SYMPATHY'):
                                        _mem_type = 'social_exchange'
                                        _impact = 'uneasy' if _pol == 'subtractive' else 'calm'
                                        _imp = 2
                                        if _is_promise:
                                            _mem_type = 'promise_or_deal'
                                            _imp = 3

                                    # Compose an outcome line that preserves details (names/items) while staying compact.
                                    def _mk_exchange_memory_line(self_name: str, other_name: str) -> str:
                                        base = f"Exchange with {other_name}: {_ad_clip}" if _ad_clip else f"Exchange with {other_name}."
                                        outc = f" Outcome: winner={_winner}, type={_etype}, polarity={_pol}."
                                        return (base + _supp_txt + outc)[:360]

                                    # Record for reactor NUA (memory about proactor)
                                    if reactor_is_nua:
                                        try:
                                            nua_memory_system.record_event(
                                                nua_name=reactor.sheet.name,
                                                event_type=_mem_type,
                                                description=_mk_exchange_memory_line(reactor.sheet.name, proactor.sheet.name),
                                                actors_involved=[proactor.sheet.name],
                                                importance=_imp,
                                                emotional_impact=_impact,
                                            )
                                        except Exception:
                                            pass

                                    # Record for proactor NUA (memory about reactor)
                                    if proactor_is_nua:
                                        try:
                                            nua_memory_system.record_event(
                                                nua_name=proactor.sheet.name,
                                                event_type=_mem_type,
                                                description=_mk_exchange_memory_line(proactor.sheet.name, reactor.sheet.name),
                                                actors_involved=[reactor.sheet.name],
                                                importance=_imp,
                                                emotional_impact=_impact,
                                            )
                                        except Exception:
                                            pass
                                except Exception:
                                    pass

                                from pathlib import Path as _Path
                                from context_store import ContextStore, WorldTime
                                from spatial_context_system import get_spatial_manager
                                spatial = get_spatial_manager(session_id=tracker.session_id if tracker else None)
                                ctx = spatial.get_current_context() if spatial else None
                                actor_positions = getattr(ctx, 'actor_positions', None) if ctx else None

                                def _resolve_spatial_actor_id(_actor) -> str:
                                    try:
                                        _name = getattr(getattr(_actor, 'sheet', None), 'name', None)
                                        if not _name or not actor_positions:
                                            return ''
                                        for _aid, _apos in actor_positions.items():
                                            if getattr(_apos, 'actor_name', None) == _name:
                                                return str(_aid)
                                    except Exception:
                                        return ''
                                    return ''

                                proactor_sid = _resolve_spatial_actor_id(proactor)
                                reactor_sid = _resolve_spatial_actor_id(reactor)

                                if proactor_sid or reactor_sid:
                                    store = ContextStore(Path('simulation_data/context/context.db'))
                                    gt = None
                                    try:
                                        gt = master_time.get_current_time_context().get('game_time') if master_time else None
                                    except Exception:
                                        gt = None
                                    wt = None
                                    try:
                                        if gt is not None:
                                            wt = WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
                                    except Exception:
                                        wt = None

                                    location_id = None
                                    try:
                                        location_id = getattr(spatial, 'current_location', None)
                                    except Exception:
                                        location_id = None

                                    raw_step6 = (final_narrative or '').strip()
                                    pro_line = (proactor_action_data.get('narrative_description', '') if isinstance(proactor_action_data, dict) else '').strip()
                                    rea_line = (reactor_action_data.get('narrative_description', '') if isinstance(reactor_action_data, dict) else '').strip()

                                    def _clip(s: str, n: int) -> str:
                                        try:
                                            s = (s or '').strip()
                                            return (s[:n] + '…') if len(s) > n else s
                                        except Exception:
                                            return ''

                                    event_summary = _clip(raw_step6 or f"{proactor.sheet.name} interacted with {reactor.sheet.name}.", 220)
                                    payload = {
                                        'actor_ids': [x for x in [proactor_sid, reactor_sid] if x],
                                        'actor_names': [proactor.sheet.name, reactor.sheet.name],
                                        'exchange_type': exchange_type,
                                        'winner': exch_winner,
                                        'step6_narrative': _clip(raw_step6, 1200),
                                    }
                                    event_id = store.log_world_event(
                                        session_id=tracker.session_id if tracker else 'default',
                                        event_type='DIALOGUE_EXCHANGE',
                                        summary=event_summary,
                                        location_id=location_id,
                                        importance=6,
                                        tags=['exchange', 'dialogue'],
                                        payload=payload,
                                        world_time=wt,
                                    )

                                    if proactor_sid:
                                        store.remember(
                                            session_id=tracker.session_id if tracker else 'default',
                                            actor_id=proactor_sid,
                                            memory_type='DIALOGUE_EXCHANGE_SUMMARY',
                                            content=_clip(f"With {reactor.sheet.name}: {raw_step6 or pro_line}", 360),
                                            importance=6,
                                            source_event_id=event_id,
                                            world_time=wt,
                                        )
                                        store.remember(
                                            session_id=tracker.session_id if tracker else 'default',
                                            actor_id=proactor_sid,
                                            memory_type='DIALOGUE_EXCHANGE_RAW',
                                            content=_clip(f"You: {pro_line}\nThem: {rea_line}\nOutcome: {raw_step6}", 1200),
                                            importance=4,
                                            source_event_id=event_id,
                                            world_time=wt,
                                        )

                                    if reactor_sid:
                                        store.remember(
                                            session_id=tracker.session_id if tracker else 'default',
                                            actor_id=reactor_sid,
                                            memory_type='DIALOGUE_EXCHANGE_SUMMARY',
                                            content=_clip(f"With {proactor.sheet.name}: {raw_step6 or pro_line}", 360),
                                            importance=6,
                                            source_event_id=event_id,
                                            world_time=wt,
                                        )
                                        store.remember(
                                            session_id=tracker.session_id if tracker else 'default',
                                            actor_id=reactor_sid,
                                            memory_type='DIALOGUE_EXCHANGE_RAW',
                                            content=_clip(f"Them: {pro_line}\nYou: {rea_line}\nOutcome: {raw_step6}", 1200),
                                            importance=4,
                                            source_event_id=event_id,
                                            world_time=wt,
                                        )
                            except Exception:
                                pass
                        
                        except Exception as e:
                            # Silently fail - memory recording shouldn't break the simulation
                            print(f"{Color.WARNING}⚠️ NUA memory recording error: {e}{Color.RESET}")
                        
                        # ═══════════════════════════════════════════════════════════
                        # REPUTATION TITLE CHECK - Award titles for significant actions
                        # ═══════════════════════════════════════════════════════════
                        try:
                            if NEW_VOICE_SYSTEM_AVAILABLE and _reputation_system is not None:
                                # Get witnesses (other actors in scene)
                                witness_names = [
                                    npc.sheet.name for npc in available_npcs 
                                    if hasattr(npc, 'sheet') and npc.sheet.name not in [proactor.sheet.name, reactor.sheet.name]
                                ]
                                
                                # Check if proactor earned a title
                                action_desc = proactor_action_data.get('narrative_description', user_input)
                                outcome_desc = final_narrative[:200] if final_narrative else "Action completed"
                                
                                check_and_award_title(
                                    actor_name=proactor.sheet.name,
                                    action_description=action_desc,
                                    action_outcome=outcome_desc,
                                    location=current_location or "Unknown",
                                    witnesses=witness_names + [reactor.sheet.name],
                                    context=f"Exchange type: {exchange_type}, Winner: {exch_winner}"
                                )
                                
                                # Check if reactor earned a title (for defensive actions, etc.)
                                if reactor_action_data:
                                    reactor_desc = reactor_action_data.get('narrative_description', '')
                                    if reactor_desc:
                                        check_and_award_title(
                                            actor_name=reactor.sheet.name,
                                            action_description=reactor_desc,
                                            action_outcome=outcome_desc,
                                            location=current_location or "Unknown",
                                            witnesses=witness_names + [proactor.sheet.name],
                                            context=f"Exchange type: {exchange_type}, Winner: {exch_winner}"
                                        )
                        except Exception:
                            pass  # Title checking is optional, don't break on failure
                        
                        # Process monetary transaction for contested actions (only if proactor won)
                        if monetary_data.get("transaction_detected"):
                            exch_winner = exchange_outcome.get('winner') if isinstance(exchange_outcome, dict) else None
                            # Only process monetary exchange if proactor won (theft succeeds, etc.)
                            if exch_winner == 'proactor':
                                _, monetary_message = conductor.interpreter_agent.process_monetary_transaction(
                                    monetary_data, proactor, reactor
                                )
                        
                        # Update scene evaluation metrics from this exchange
                        try:
                            exch_winner = exchange_outcome.get('winner') if isinstance(exchange_outcome, dict) else None
                            success_diff = int(exchange_outcome.get('success_difference', 0)) if isinstance(exchange_outcome, dict) else 0
                            final_shift_amount = int(exchange_outcome.get('final_shift_amount', 0)) if isinstance(exchange_outcome, dict) else 0
                            status_shifted = (exchange_outcome.get('status_shifted') if isinstance(exchange_outcome, dict) else None) or ''
                            updated_reactor_status = exchange_outcome.get('updated_reactor_status') if isinstance(exchange_outcome, dict) else None
                            updated_proactor_status = exchange_outcome.get('updated_proactor_status') if isinstance(exchange_outcome, dict) else None

                            # Stalemate tracking
                            if success_diff == 0:
                                encounter_eval['consecutive_stalemates'] += 1
                            else:
                                encounter_eval['consecutive_stalemates'] = 0

                            # Dominance streak tracking (decisive margin >= 5)
                            if exch_winner in ('proactor', 'reactor') and abs(success_diff) >= 5:
                                dom_actor = proactor.sheet.name if exch_winner == 'proactor' else reactor.sheet.name
                                if encounter_eval['dominance_streak_actor'] == dom_actor:
                                    encounter_eval['dominance_streak'] += 1
                                else:
                                    encounter_eval['dominance_streak_actor'] = dom_actor
                                    encounter_eval['dominance_streak'] = 1
                            elif exch_winner in ('proactor', 'reactor'):
                                # Winning but not decisive resets streak
                                encounter_eval['dominance_streak_actor'] = None
                                encounter_eval['dominance_streak'] = 0

                            # Per-round shift accumulation (any non-zero applied shift)
                            if isinstance(final_shift_amount, int) and final_shift_amount != 0:
                                encounter_eval['turn_shifts_this_round'] += abs(final_shift_amount)
                        except Exception:
                            pass

                        # Per-turn scene evaluation (always display) with richer heuristics
                        try:
                            rm = encounter_checker.current_context.round_manager
                            end_reason = None
                            # Terminal resolution (e.g., death) check
                            if hasattr(rm, 'is_contest_resolved') and rm.is_contest_resolved():
                                end_reason = "terminal condition detected"
                            # NOTE: SUPPLY reaching 0 is NOT a terminal condition
                            # It just means the actor is broke/out of resources
                            # Only end if there's a true terminal condition (death, unconscious, etc.)
                            if end_reason:
                                print(f"{Color.SUCCESS}🧭 Scene Evaluation: END — {end_reason}{Color.RESET}")
                                exchange_in_progress = False
                            else:
                                try:
                                    queue_len = len(turn_queue) if turn_queue else len(getattr(rm, 'current_turn_queue', []) or [])
                                    pos = (rm.turn_queue_position + 1) if queue_len else 0
                                    print(f"{Color.INFO}🧭 Scene Evaluation: CONTINUE (Round {rm.round_number}, Turn {pos}/{max(1, queue_len)}){Color.RESET}")
                                except Exception:
                                    print(f"{Color.INFO}🧭 Scene Evaluation: CONTINUE{Color.RESET}")
                        except Exception:
                            pass
                        
                        # Record escalation turn for NUA context tracking (only if not time-expired)
                        if not reactor_action_data.get('time_expired', False):
                            try:
                                rm = encounter_checker.current_context.round_manager
                                # Determine which actor is NUA and map UA vs NUA data accordingly
                                if getattr(proactor, 'is_user_actor', False):
                                    # UA proactor vs NUA reactor
                                    nua_name = getattr(getattr(reactor, 'sheet', None), 'name', 'NPC')
                                    ua_data = proactor_action_data
                                    nua_data = reactor_action_data
                                else:
                                    # NUA proactor vs UA reactor
                                    nua_name = getattr(getattr(proactor, 'sheet', None), 'name', 'NPC')
                                    ua_data = reactor_action_data
                                    nua_data = proactor_action_data
                                nua_context_manager.record_interaction(
                                    nua_name,
                                    ua_data,
                                    nua_data,
                                    rm.round_number
                                )
                            except Exception:
                                pass
                        else:
                            print(f"{Color.SYSTEM}⏰ Escalation tracking skipped due to time expiration{Color.RESET}")
                        
                        # End-of-exchange conditions: scheduled arrival exit only
                        try:
                            if proactor_action_data.get('time_expired', False) or reactor_action_data.get('time_expired', False):
                                # Do not end the encounter on time expiry; advance to next actor
                                # Advance queue and continue loop
                                _ = encounter_checker.current_context.round_manager.advance_turn_queue()
                                continue
                        except Exception:
                            pass

                        # Auto-end if UA becomes unconscious
                        try:
                            ua_stamina = actor.sheet.statuses[StatusType.STAMINA].value
                            ua_spirit = actor.sheet.statuses[StatusType.SPIRIT].value
                            if ua_stamina <= 0 or ua_spirit <= 0:
                                print(f"{Color.WARNING}😴 You have been knocked unconscious!{Color.RESET}")
                                print(f"{Color.INFO}🛌 Ending encounter and returning to ROAM mode for recovery.{Color.RESET}")
                                exchange_in_progress = False
                                continue
                        except Exception:
                            pass
                        
                        # Auto-end if all opposing NUAs are unconscious
                        try:
                            participants = getattr(encounter_checker.current_context, 'participants', []) or []
                            non_user_participants = [p for p in participants if not getattr(p, 'is_user_actor', False)]
                            if non_user_participants:
                                all_ko = True
                                for p in non_user_participants:
                                    st = p.sheet.statuses[StatusType.STAMINA].value
                                    sp = p.sheet.statuses[StatusType.SPIRIT].value
                                    if st > 0 and sp > 0:
                                        all_ko = False
                                        break
                                if all_ko:
                                    print(f"{Color.INFO}🛌 All opposing NUAs are unconscious. Ending encounter and returning to ROAM.{Color.RESET}")
                                    exchange_in_progress = False
                                    # Preserve them in available_npcs for recovery in ROAM
                                    for p in non_user_participants:
                                        if p not in available_npcs:
                                            available_npcs.append(p)
                                    continue
                        except Exception:
                            pass

                        # Check for scheduled arrivals during the encounter
                        try:
                            # Process scheduled arrivals cautiously: only narrate in ROAM or genuine vehicle scenes
                            due_events = scheduler.check_due(simulation_time_tracker.get_total_simulation_time())
                            for ev in due_events:
                                if ev.get('type') == 'arrival':
                                    label = ev.get('label', 'destination')
                                    vehicle = _infer_vehicle(scene_description)
                                    # If we're in an encounter or the scene has no vehicle context, postpone the arrival
                                    if encounter_checker.current_context.mode != SimulationMode.ROAM or vehicle == 'unknown':
                                        scheduler.reschedule_arrival(label or 'Next stop', 3, simulation_time_tracker.get_total_simulation_time())
                                        continue
                                    print()
                                    _print_arrival_opening(vehicle, label)
                                    # Ask the user naturally using the unified prompt
                                    user_arrival_action = _prompt_action_input(Color.INPUT)
                                    intent = _detect_exit_intent(user_arrival_action)
                                    # Determine effective exit given vehicle rules, and narrate centrally
                                    should_exit = (intent == 'exit') or (vehicle in ('plane', 'cab') and intent != 'exit')
                                    _print_arrival_followup(vehicle, intent)
                                    if should_exit:
                                        exchange_in_progress = False
                                        break
                                    else:
                                        scheduler.reschedule_arrival(label or 'Next stop', 3, simulation_time_tracker.get_total_simulation_time())
                            if not exchange_in_progress:
                                continue
                        except Exception:
                            pass

                        # Check for turn cycle completion
                        queue_cycle_complete = encounter_checker.current_context.round_manager.advance_turn_queue()
                        if queue_cycle_complete:
                            # Completed a full pass from top to bottom
                            turn_number += 1
                            print(f"\n{Color.SUCCESS}🔄 Turn cycle completed - Starting new round{Color.RESET}")
                            
                            # End the completed round (apply lasting shifts, check deaths, decay effects)
                            try:
                                encounter_checker.current_context.round_manager.end_round()
                            except Exception as e:
                                print(f"{Color.WARNING}End round processing error: {e}{Color.RESET}")
                            
                            # Reset reactor time manager for next cycle
                            reactor_time_manager = ReactorTimeManager()
                            
                            # Round-level scene evaluation
                            # NOTE: Exchanges should NOT auto-end based on arbitrary conditions
                            # Exchanges should end when:
                            # 1. User explicitly ends ("I say goodbye and leave")
                            # 2. NPC chooses to disengage (based on goals/satisfaction)
                            # 3. Knockout/incapacitation (handled elsewhere)
                            # 4. External interruption occurs
                            # Let participants decide when to end, don't force it

                            # If still in progress, roll initiative for a new round
                            if exchange_in_progress:
                                # FIX BUG #16: Clear pending action cache when starting new round
                                pending_encounter_action = None
                                
                                # Start a new round: rolls new initiative and applies recovery
                                print(f"{Color.SYSTEM}🎲 Rolling new initiative for next round...{Color.RESET}")
                                new_turn_queue_data = encounter_checker.current_context.round_manager.start_round()
                                turn_queue = new_turn_queue_data['turn_queue']
                                
                                # Tracker: record new round
                                try:
                                    if tracker and _tracker_exchange_started:
                                        rm = encounter_checker.current_context.round_manager
                                        tracker.start_round(round_number=getattr(rm, 'round_number', 1), initiative_data=new_turn_queue_data)
                                except Exception:
                                    pass
                                # Reset per-round accumulators
                                encounter_eval['turn_shifts_this_round'] = 0

                                # Display banner and new turn order (use reporter for consistency)
                                try:
                                    print(f"{Color.INFO}📣 New Turn Order Rolled (Round {new_turn_queue_data.get('round_number', '?')}){Color.RESET}")
                                except Exception:
                                    print(f"{Color.INFO}📣 New Turn Order Rolled{Color.RESET}")
                                # Enable enhanced queue display options for refreshed queue
                                try:
                                    new_turn_queue_data['label_roles_in_queue'] = True
                                    new_turn_queue_data['use_primary_reactor_label'] = True
                                    new_turn_queue_data['show_initiative_breakdown'] = True
                                except Exception:
                                    pass
                                encounter_checker.current_context.reporter.report_turn_queue_results(new_turn_queue_data)
                                
                                # Request coordinated round completion save
                                round_save_request = save_coordinator.create_round_completion_request({
                                    'round_participants': [p.sheet.name for p in encounter_checker.current_context.participants],
                                    'new_turn_order': [
                                        {
                                            'position': i + 1,
                                            'actor_name': item['actor_name'],
                                            'initiative_score': item['initiative_score']
                                        } for i, item in enumerate(turn_queue)
                                    ],
                                    'scene_number': scene_number,
                                    'total_turns': turn_number
                                })
                                save_coordinator.request_save(round_save_request)
                                
                                # Continue encounter with new initiative order
                                continue
                            else:
                                # Encounter ended due to disengagement heuristic; proceed to end handling
                                continue
                        else:
                            # Proceed to next actor in current round
                            continue
            
            # Tracker: conclude exchange when encounter ends
            try:
                if tracker and _tracker_exchange_started:
                    tracker.conclude_exchange(
                        winner=_tracker_last_exchange_winner,
                        final_state=_tracker_last_exchange_final_state,
                        scene_transition=bool(scene_conclusion_pending)
                    )
            except Exception:
                pass

            # If encounter loop has ended, reset to ROAM and then process any deferred scene transition
            _end_encounter(encounter_checker, available_npcs)
            if scene_conclusion_pending:
                print(f"\n{Color.SUCCESS}🎬 Scene {scene_number} Concluded (after encounter){Color.RESET}")
                if scene_start_time:
                    scene_duration = time_tracker.get_current_time().hours_since(scene_start_time)
                    print(f"{Color.SYSTEM}⏱️  Scene Duration: {scene_duration:.1f} hours{Color.RESET}")
                print(f"{Color.SYSTEM}📊 Actions in Scene: {scene_action_count}{Color.RESET}")
                
                # Save scene conclusion to narrative context
                narrative_context_manager.add_narrative_event(
                    event_type=NarrativeEventType.SCENE_TRANSITION,
                    narrative_text=f"Scene {scene_number} concluded after {scene_action_count} actions. Duration: {scene_duration:.1f}h" if scene_start_time else f"Scene {scene_number} concluded after {scene_action_count} actions.",
                    actors_involved=[actor.sheet.name],
                    importance=NarrativeImportance.MAJOR,
                    emotional_tone="transitional",
                    scene_context=f"Scene {scene_number} conclusion"
                )
                
                # Request coordinated scene transition save
                transition_save_request = save_coordinator.create_scene_transition_request({
                    'from_scene': scene_number,
                    'to_scene': scene_number + 1,
                    'scene_duration': scene_duration if scene_start_time else 0,
                    'final_action_count': scene_action_count,
                    'time_context': {
                        'scene_start': scene_start_time.format_full() if scene_start_time else 'unknown',
                        'scene_end': time_tracker.get_current_time().format_full()
                    },
                    'transition_reason': 'user_deferred_after_encounter'
                })
                save_coordinator.request_save(transition_save_request)
                
                # Transition to next scene
                scene_number += 1
                scene_id = f"scene_{scene_number}"  # Update scene ID
                scene_action_count = 0
                scene_start_time = time_tracker.get_current_time()
                scene_conclusion_pending = False
                
                # Generate new scene
                print(f"\n{Color.SYSTEM}Generating next scene...{Color.RESET}")
                try:
                    # Save current location's NUAs before leaving
                    if available_npcs:
                        current_nua_names = [npc.sheet.name for npc in available_npcs if hasattr(npc, 'sheet')]
                        context_manager = get_context_manager()
                        if context_manager and current_nua_names:
                            context_manager.set_nuas(current_nua_names)
                            print(f"{Color.INFO}[PERSISTENCE] Saved {len(current_nua_names)} NUA(s) at current location{Color.RESET}")
                    
                    # Leaving the place: reset available NPCs for the new location
                    available_npcs = []
                    scene_description, _ = conductor.generate_new_scene(
                        actor, scene_number, "post_encounter"
                    )
                    
                    # LOGICAL POPULATION STEP
                    print(f"{Color.SYSTEM}Populating scene with logical actors...{Color.RESET}")
                    try:
                         # Combine RAG context and Narrative Memory context
                         rag_ctx = rag_system.get_context_for_llm(query=scene_description[:100]) if rag_system else ""
                         mem_ctx = narrative_context_manager.get_context_for_llm(lookback_events=5, importance_threshold="notable") if narrative_context_manager else ""
                         combined_context = f"World Context: {rag_ctx}\n\nRecent Memories/Events: {mem_ctx}"

                         population_data = population_manager.generate_scene_population(
                             scene_description, 
                             master_time.get_current_time_context(),
                             combined_context
                         )
                         
                         # Log scene type
                         scene_type = population_data.get('scene_type', 'unknown')
                         print(f"{Color.INFO}Scene Type Identified: {scene_type.upper()}{Color.RESET}")
                         
                         # Populate actors
                         new_actors, background_atmosphere = population_manager.populate_actors(population_data)
                         
                         if new_actors:
                             available_npcs.extend(new_actors)
                             print(f"{Color.SUCCESS}Added {len(new_actors)} independent NPCs to the scene.{Color.RESET}")
                         
                         if background_atmosphere:
                             print(f"{Color.SYSTEM}Background Atmosphere: {background_atmosphere[:50]}...{Color.RESET}")
                             
                         # REFINE SCENE DESCRIPTION WITH POPULATION
                         if new_actors or background_atmosphere:
                             print(f"{Color.SYSTEM}Refining scene description...{Color.RESET}")
                             scene_description = narrator.refine_scene_with_population(
                                 scene_description, 
                                 new_actors, 
                                 background_atmosphere
                             )
                                 
                    except Exception as pop_err:
                        print(f"{Color.WARNING}Population failed: {pop_err}{Color.RESET}")

                    print(f"{Color.SUCCESS}Successfully generated Scene {scene_number}{Color.RESET}")
                    try:
                        conductor.scene_description = scene_description
                    except Exception:
                        pass
                    # Record new scene start
                    try:
                        tracker.start_scene(scene_number=scene_number, scene_data={}, nua_data=None, scene_description=scene_description)
                        # Save the new scene start as part of transition
                        start_req = save_coordinator.create_scene_transition_request({
                            'scene_number': scene_number,
                            'scene_description': scene_description,
                            'time_context': time_context,
                            'transition_phase': 'scene_start',
                            'available_npc_names': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                            'actor_state': {
                                'name': actor.sheet.name,
                                'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()}
                            }
                        })
                        save_coordinator.request_save(start_req)
                    except Exception:
                        pass
                    # Heuristic: schedule an arrival if the new scene suggests vehicle travel
                    try:
                        # Re-scan the scene for vehicle context and schedule if applicable
                        vehicle2 = _infer_vehicle(scene_description)
                        if vehicle2 != 'unknown':
                            scheduler.schedule_arrival('Next stop', 3, simulation_time_tracker.get_total_simulation_time())
                    except Exception:
                        pass
                    continue
                except Exception as e:
                    print(f"{Color.ERROR}Failed to generate new scene: {e}{Color.RESET}")
                    print(f"{Color.WARNING}Continuing in current scene...{Color.RESET}")
                    scene_number -= 1
                    scene_action_count += 1
        
        # Passive SPARK fade: if active, decrement turn counter and/or check time deadline; cancel on engagement
        try:
            if spark_active and encounter_checker.get_current_mode() == SimulationMode.ROAM:
                # Detect engagement by name addressing or encounter start
                engaged = False
                try:
                    # input_analysis_for_survival was computed earlier for the same user_input
                    addressed_to = (input_analysis_for_survival or {}).get('addressed_to') if 'input_analysis_for_survival' in locals() else None
                    if isinstance(addressed_to, str) and 'spark_target_name' in locals() and spark_target_name:
                        engaged = addressed_to.strip().lower() == spark_target_name.strip().lower()
                except Exception:
                    engaged = False
                if encounter_checker.get_current_mode() == SimulationMode.ENCOUNTER:
                    engaged = True
                if engaged:
                    spark_active = False
                    spark_fade_turns = 0
                else:
                    # Decrement turns, check time threshold
                    spark_fade_turns = max(0, spark_fade_turns - 1)
                    now_hours = simulation_time_tracker.get_total_simulation_time()
                    if spark_fade_turns <= 0 or (('spark_fade_deadline' in locals()) and now_hours >= spark_fade_deadline):
                        # Fade out and clear
                        scene_description = _fade_spark_back_to_roam(
                            narrator,
                            narrative_context_manager,
                            scene_description,
                            spark_bridge_cache,
                            master_time.get_current_time_context()
                        )
                        try:
                            conductor.scene_description = scene_description
                        except Exception:
                            pass
                        spark_active = False
                        spark_fade_turns = 0
        except Exception:
            pass
        
        # After processing the user input for this loop, if a SPARK is pending and we're still in ROAM, generate it now.
        # Uses StorytellerAgent's 3 spark types: MOMENTUM, EXCHANGE, CALLBACK
        if spark_pending and encounter_checker.get_current_mode() == SimulationMode.ROAM:
            print(f"\n{Color.WARNING}⚡ SPARK GENERATION TRIGGERED{Color.RESET}")
            print(f"{Color.SYSTEM}Time since last SPARK: {int(simulation_time_tracker.get_time_since_last_spark())}s{Color.RESET}")
            
            if NEW_VOICE_SYSTEM_AVAILABLE and _storyteller is not None:
                try:
                    # Gather NUA info for storyteller
                    nua_dicts = [
                        {"name": npc.sheet.name, "occupation": getattr(npc.sheet, 'occupation', ''), 
                         "description": getattr(npc.sheet, 'description', '')}
                        for npc in available_npcs if hasattr(npc, 'sheet')
                    ]
                    recent_events = []
                    if narrative_context_manager:
                        if hasattr(narrative_context_manager, 'get_recent_narratives'):
                            recent_events = narrative_context_manager.get_recent_narratives(count=5)
                        elif hasattr(narrative_context_manager, 'get_recent_events'):
                            recent_events = narrative_context_manager.get_recent_events(count=5)
                    
                    # Get RAG context for worldbuilding
                    spark_rag_context = ""
                    if hasattr(conductor.decider_agent, 'rag_system') and conductor.decider_agent.rag_system:
                        try:
                            rag_results = conductor.decider_agent.rag_system.query(f"location {actor.sheet.location} setting atmosphere", top_k=2)
                            if rag_results:
                                spark_rag_context = "\n".join([r.get('content', '')[:200] for r in rag_results[:2]])
                        except Exception:
                            pass
                    
                    # Use StorytellerAgent for spark generation (MOMENTUM, EXCHANGE, CALLBACK)
                    sparks = get_storyteller_sparks(
                        location=actor.sheet.location or "Current Location",
                        location_description=scene_description[:500],
                        available_nuas=nua_dicts,
                        recent_narrative=recent_events,
                        actor_goal=actor.sheet.goals[0] if hasattr(actor.sheet, 'goals') and actor.sheet.goals else "",
                        actor_task=actor.sheet.get_current_task_description() if hasattr(actor.sheet, 'get_current_task_description') else "",
                        rag_context=spark_rag_context
                    )
                    
                    # Process generated sparks
                    if sparks:
                        for spark in sparks[:3]:
                            # Display spark trigger
                            if hasattr(spark, 'trigger_description') and spark.trigger_description:
                                spark_type_name = spark.spark_type.value.upper() if hasattr(spark, 'spark_type') else 'SPARK'
                                print(f"\n{Color.SUCCESS}✨ {spark_type_name} SPARK{Color.RESET}")
                                print(f"{Color.STATUS}{spark.trigger_description}{Color.RESET}")
                                
                                # Display spark using storyteller's display function
                                try:
                                    display_spark(spark)
                                except Exception:
                                    pass
                        
                        simulation_time_tracker.mark_spark_generated()
                        spark_active = True
                        spark_fade_turns = SPARK_FADE_TURNS
                        spark_fade_deadline = simulation_time_tracker.get_total_simulation_time() + SPARK_FADE_HOURS
                        
                except Exception as e:
                    if not SUPPRESS_DEBUG:
                        print(f"{Color.WARNING}⚠️ Storyteller spark generation failed: {e}{Color.RESET}")
            
            spark_pending = False

        # Check for critical survival warnings
        critical_actions = get_critical_survival_actions(actor.sheet)
        if critical_actions:
            print(f"\n{Color.WARNING}⚠️  CRITICAL SURVIVAL WARNINGS{Color.RESET}")
            for action_id, action in critical_actions.items():
                print(f"{Color.WARNING}   • {action.name}: {action.description}{Color.RESET}")
            print(f"{Color.WARNING}Address these needs soon to avoid status penalties.{Color.RESET}\n")
        
        # Scene header before user input (concise)
        print()
        if not last_action_narrative:
            print(f"{Color.SYSTEM}(No recent action result to display){Color.RESET}")
        # Do not auto-print sheets; users can type 'ua' or 'npc'
        
        # Note: Survival needs are now automatically detected from user actions
        # No need to display manual survival action menu
        
        # -------------------------------------------------------------------------
        # BACKGROUND SIMULATION: Pre-User Turns (High Initiative NUAs)
        # -------------------------------------------------------------------------
        # Use the persistent location initiative tracker instead of re-rolling every turn
        roam_turn_order = []
        current_mode = encounter_checker.get_current_mode()
        print(f"{Color.SYSTEM}[BG SIM DEBUG] Mode: {current_mode}, NPCs: {len(available_npcs) if available_npcs else 0}{Color.RESET}")
        
        if current_mode == SimulationMode.ROAM and available_npcs:
            try:
                from initiative_system import get_location_initiative_tracker
                
                init_tracker = get_location_initiative_tracker()
                
                # Use stored initiative if available, otherwise prepare new order
                if init_tracker.has_initiative():
                    roam_turn_order = init_tracker.get_turn_order()
                    print(f"{Color.SYSTEM}[BG SIM DEBUG] Using stored initiative: {len(roam_turn_order)} entries{Color.RESET}")
                else:
                    # Fallback: roll initiative if not set (shouldn't happen normally)
                    print(f"{Color.WARNING}[BG SIM DEBUG] No stored initiative - rolling fresh{Color.RESET}")
                    roam_turn_order = bg_sim.prepare_turn_order(actor, available_npcs)
                
                # Count pre-user actors
                pre_user_count = sum(1 for e in roam_turn_order if not e.get('is_user', False) and roam_turn_order.index(e) < next((i for i, x in enumerate(roam_turn_order) if x.get('is_user')), len(roam_turn_order)))
                print(f"{Color.SYSTEM}[BG SIM DEBUG] Executing {pre_user_count} pre-user turns...{Color.RESET}")
                
                # Execute pre-user turns (NPCs with higher initiative than UA)
                bg_result = bg_sim.execute_pre_user_turns(
                    roam_turn_order, 
                    actor, 
                    available_npcs, 
                    scene_description, 
                    time_context
                )
                print(f"{Color.SYSTEM}[BG SIM DEBUG] Pre-user result: {bg_result}{Color.RESET}")
                
                # Handle Interrupt (NUA started an exchange)
                if isinstance(bg_result, dict) and bg_result.get('interrupt'):
                    event = bg_result.get('event', {})
                    initiator = event.get('initiator')
                    
                    # Validate initiator before using
                    if initiator and hasattr(initiator, 'sheet') and hasattr(initiator.sheet, 'name'):
                        print(f"\n{Color.WARNING}🚨 ENCOUNTER TRIGGERED BY {initiator.sheet.name.upper()}!{Color.RESET}")
                        
                        # CRITICAL: Seed encounter participants for ENCOUNTER init (avoid empty participants crash)
                        try:
                            encounter_checker.current_context.participants = [initiator]
                            encounter_checker.current_context.trigger_action = event.get('trigger_action', 'background initiative')
                            encounter_checker.current_context.encounter_type = event.get('encounter_type', 'general')
                        except Exception:
                            pass
                        
                        # Switch mode to ENCOUNTER - clear location initiative
                        encounter_checker.set_mode(SimulationMode.ENCOUNTER)
                        init_tracker.clear()  # Encounter has its own initiative system
                        
                        # Setup Round Manager override
                        if hasattr(conductor, 'round_manager'):
                            conductor.round_manager.set_round_one_proactor(initiator)
                        
                        # Restart loop to enter ENCOUNTER mode immediately
                        continue
                    else:
                        print(f"{Color.WARNING}[BG SIM] NUA encounter triggered but initiator invalid{Color.RESET}")
                    
            except Exception as e:
                print(f"{Color.WARNING}[BG SIM] Pre-turn error: {e}{Color.RESET}")
        
        # Get user input via unified prompt helper
        user_input = _prompt_action_input(Color.INPUT)
        if user_input.lower() in ['quit', 'exit', 'q']:
            print(f"{Color.SUCCESS}Thanks for playing UTAS!{Color.RESET}")
            break

        if _handle_debug_context_commands(user_input):
            continue
            
        # BACKGROUND ACTOR PROMOTION CHECK
        # If user interacts with someone in the background atmosphere, promote them to foreground
        if background_atmosphere:
             try:
                 promoted_actor = population_manager.promote_background_actor(user_input, background_atmosphere, scene_description)
                 if promoted_actor:
                     # Register NUA for persistence and add to available NPCs
                     register_nua(promoted_actor, available_npcs)
                     print(f"{Color.SUCCESS}Interaction established: {promoted_actor.sheet.name} ({promoted_actor.sheet.occupation}){Color.RESET}")
                     # Refresh present names for downstream context
                     present_names = [getattr(getattr(n, 'sheet', None), 'name', 'NPC') for n in (available_npcs or [])]
             except Exception as e:
                 print(f"{Color.WARNING}Background promotion check failed: {e}{Color.RESET}")
        
        # LLM-first survival intent detection with regex fallback, gated to actions (not inquiries)
        input_analysis_for_survival = quick_action_check
        fulfilled_needs = []
        survival_time_cost = 0.0
        if input_analysis_for_survival.get('input_type') != 'inquiry':
            llm_detection = None
            try:
                llm_detection = conductor.interpreter.detect_survival_intent(user_input, actor)
            except Exception:
                llm_detection = None
            if llm_detection and llm_detection.get('needs'):
                need_map = {
                    'food': SurvivalNeed.FOOD,
                    'water': SurvivalNeed.WATER,
                    'sleep': SurvivalNeed.SLEEP,
                    'fulfillment': SurvivalNeed.FULFILLMENT,
                }
                llm_needs = [need_map[n.lower()] for n in llm_detection['needs'] if isinstance(n, str) and n.lower() in need_map]
                if llm_needs and float(llm_detection.get('confidence', 0)) >= 0.6:
                    fulfilled_needs = llm_needs
                    costs = survival_analyzer.get_action_costs(user_input, fulfilled_needs)
                    if isinstance(llm_detection.get('total_time_hours'), (int, float)) and llm_detection['total_time_hours'] > 0:
                        costs['time_cost'] = float(llm_detection['total_time_hours'])
                    survival_messages = survival_analyzer.process_survival_fulfillment(
                        actor.sheet, user_input, fulfilled_needs, costs, narrative_context_manager
                    )
                    summary = survival_analyzer.get_survival_summary(fulfilled_needs, costs)
                    if summary:
                        print(f"\n{Color.SUCCESS}{summary}{Color.RESET}")
                        for message in survival_messages:
                            print(f"{Color.SUCCESS}   • {message}{Color.RESET}")
                    survival_time_cost = costs['time_cost']
                else:
                    fulfilled_needs = survival_analyzer.analyze_action(user_input)
            else:
                fulfilled_needs = survival_analyzer.analyze_action(user_input)

            if fulfilled_needs:
                if survival_time_cost == 0.0:
                    costs = survival_analyzer.get_action_costs(user_input, fulfilled_needs)
                    survival_messages = survival_analyzer.process_survival_fulfillment(
                        actor.sheet, user_input, fulfilled_needs, costs, narrative_context_manager
                    )
                    summary = survival_analyzer.get_survival_summary(fulfilled_needs, costs)
                    if summary:
                        print(f"\n{Color.SUCCESS}{summary}{Color.RESET}")
                        for message in survival_messages:
                            print(f"{Color.SUCCESS}   • {message}{Color.RESET}")
                    survival_time_cost = costs['time_cost']
                    # Update narrative loop with survival signal
                    try:
                        turn_data = _build_turn_data(
                            user_input=user_input,
                            scene_description=scene_description,
                            current_mode=current_mode,
                            continuity={'judgment': 'Possible'},
                            survival_needs=[n.value for n in fulfilled_needs]
                        )
                        turn_data['narrative_response'] = last_action_narrative
                        narrative_loop.process_turn(
                            turn_data=turn_data,
                            scene_description=scene_description,
                            time_context=time_context,
                            available_npcs=available_npcs
                        )
                    except Exception:
                        pass

                # DISABLED: Survival actions no longer automatically advance time
                # Time advancement is now only triggered by actual actions
                # if survival_time_cost > 0:
                #     time_request = master_time.create_survival_action_request(
                #         action_name=f"Survival needs fulfillment",
                #         time_cost_hours=survival_time_cost,
                #         actor_name=actor.sheet.name
                #     )
                #     time_result = master_time.request_time_advancement(time_request)
                #     time_context = master_time.get_current_time_context()
                #     print(f"\n{Color.SYSTEM}🕘 Time advanced by {time_result.duration_advanced_hours} hours{Color.RESET}")
                #     print(f"{Color.SYSTEM}🕘 Current Time: {time_result.new_time.format_full()}{Color.RESET}")
                #     if time_result.atmospheric_changes['changed']:
                #         print(f"{Color.NARRATIVE}🌆 {time_result.atmospheric_changes['new']}{Color.RESET}")
        
        # Check for survival warnings
        critical_needs = get_critical_survival_actions(actor.sheet)
        if critical_needs:
            print(f"\n{Color.WARNING}⚠️ SURVIVAL WARNING:{Color.RESET}")
            for action_id, action in critical_needs.items():
                print(f"  🔴 {action.name} needed - {action.description}")
        
        # No automatic scene transitions - only user-initiated
        
        # Classify action for time tracking
        rule_of_3_result = rule_of_3_classifier.classify_action(user_input)
        if isinstance(rule_of_3_result, tuple):
            rule_of_3_category, rule_of_3_reasoning = rule_of_3_result
        else:
            rule_of_3_category = rule_of_3_result
            rule_of_3_reasoning = "Fallback classification"
        
        # Request coordinated time advancement for user action
        time_request = master_time.create_user_action_request(
            rule_of_3_category=rule_of_3_category,
            actor_name=actor.sheet.name,
            action_description=user_input[:50]  # Truncated description
        )
        time_result = master_time.request_time_advancement(time_request)
        
        # Update scene lighting if time changed significantly
        time_context = master_time.get_current_time_context()
        scene_description = time_lighting_updater.update_scene_for_time(
            scene_description, time_context
        )
        
        # Record action in recent actions for SPARK context
        recent_actions.append({
            'action': user_input,
            'timestamp': simulation_time_tracker.get_total_simulation_time(),
            'mode': current_mode.value,
            'scene': scene_number
        })
        
        # Keep only last 5 actions
        if len(recent_actions) > 5:
            recent_actions.pop(0)
        
        # Increment scene action count ONLY for exploration mode
        if current_mode != SimulationMode.ENCOUNTER:
            scene_action_count += 1
            
        # -------------------------------------------------------------------------
        # BACKGROUND SIMULATION: Post-User Turns (Low Initiative NUAs)
        # -------------------------------------------------------------------------
        if encounter_checker.get_current_mode() == SimulationMode.ROAM and roam_turn_order:
            try:
                bg_result = bg_sim.execute_post_user_turns(
                    roam_turn_order, 
                    actor, 
                    available_npcs, 
                    scene_description, 
                    time_context
                )
                
                # Handle Interrupt (NUA started an exchange)
                if isinstance(bg_result, dict) and bg_result.get('interrupt'):
                    event = bg_result.get('event', {})
                    initiator = event.get('initiator')
                    
                    # Validate initiator before using
                    if initiator and hasattr(initiator, 'sheet') and hasattr(initiator.sheet, 'name'):
                        print(f"\n{Color.WARNING}🚨 ENCOUNTER TRIGGERED BY {initiator.sheet.name.upper()}!{Color.RESET}")
                        
                        # CRITICAL: Seed encounter participants for ENCOUNTER init (avoid empty participants crash)
                        try:
                            encounter_checker.current_context.participants = [initiator]
                            encounter_checker.current_context.trigger_action = event.get('trigger_action', 'background initiative')
                            encounter_checker.current_context.encounter_type = event.get('encounter_type', 'general')
                        except Exception:
                            pass
                        
                        # Switch mode to ENCOUNTER
                        encounter_checker.set_mode(SimulationMode.ENCOUNTER)
                        
                        # Setup Round Manager override
                        if hasattr(conductor, 'round_manager'):
                            conductor.round_manager.set_round_one_proactor(initiator)
                        
                        # Restart loop to enter ENCOUNTER mode immediately
                        continue
                    else:
                        print(f"{Color.WARNING}[BG SIM] NUA encounter triggered but initiator invalid{Color.RESET}")
                    
            except Exception as e:
                print(f"{Color.WARNING}[BG SIM] Post-turn error: {e}{Color.RESET}")
        
        # Auto-save functionality using Save Coordinator
        auto_save_counter += 1
        if auto_save_counter >= auto_save_interval:
            # Request coordinated auto-save
            try:
                if tracker is not None:
                    tracker.save_available_npcs(list(available_npcs or []))
            except Exception:
                pass
            save_request = save_coordinator.create_regular_auto_save_request({
                'scene_number': scene_number,
                'scene_action_count': scene_action_count,
                'actor_state': actor.sheet.to_dict() if hasattr(actor.sheet, 'to_dict') else {},
                'time_context': {
                    'current_time': time_tracker.get_current_time().format_full(),
                    'simulation_time': simulation_time_tracker.get_total_simulation_time(),
                    'time_of_day': str(time_context.get('time_of_day', 'unknown'))
                },
                'available_npcs_count': len(available_npcs)
            })
            
            success = save_coordinator.request_save(save_request)
            if success:
                auto_save_counter = 0  # Reset counter
            else:
                print(f"{Color.WARNING}⚠️ Auto-save request failed to queue{Color.RESET}")
        
        # Check for unconscious actors and advance recovery time
        _check_unconscious_actor_recovery(actor, time_tracker, available_npcs, scene_description, narrator)
        
        # Check for manual scene transition triggers (user-initiated only)
        user_input_lower = user_input.lower()
        if user_input_lower in ['move on', 'leave', 'go elsewhere', 'next scene']:
            # Do not allow scene transition during an active encounter; defer instead
            if current_mode == SimulationMode.ENCOUNTER:
                print(f"{Color.WARNING}⚠️ Cannot conclude the scene during an active encounter. Your request has been noted and will be applied after the encounter resolves.{Color.RESET}")
                scene_conclusion_pending = True
                # Skip immediate transition handling
                continue
            print(f"\n{Color.SUCCESS}🎬 Scene {scene_number} Concluded{Color.RESET}")
            if scene_start_time:
                scene_duration = time_tracker.get_current_time().hours_since(scene_start_time)
                print(f"{Color.SYSTEM}⏱️  Scene Duration: {scene_duration:.1f} hours{Color.RESET}")
            print(f"{Color.SYSTEM}📊 Actions in Scene: {scene_action_count}{Color.RESET}")
            
            # Save scene conclusion to narrative context
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.SCENE_TRANSITION,
                narrative_text=f"Scene {scene_number} concluded after {scene_action_count} actions. Duration: {scene_duration:.1f}h" if scene_start_time else f"Scene {scene_number} concluded after {scene_action_count} actions.",
                actors_involved=[actor.sheet.name],
                importance=NarrativeImportance.MAJOR,
                emotional_tone="transitional",
                scene_context=f"Scene {scene_number} conclusion"
            )
            
            # Request coordinated scene transition save
            transition_save_request = save_coordinator.create_scene_transition_request({
                'from_scene': scene_number,
                'to_scene': scene_number + 1,
                'scene_duration': scene_duration if scene_start_time else 0,
                'final_action_count': scene_action_count,
                'time_context': {
                    'scene_start': scene_start_time.format_full() if scene_start_time else 'unknown',
                    'scene_end': time_tracker.get_current_time().format_full()
                },
                'transition_reason': 'user_initiated'
            })
            save_coordinator.request_save(transition_save_request)
            
            # Transition to next scene
            scene_number += 1
            scene_id = f"scene_{scene_number}"  # Update scene ID
            scene_action_count = 0
            scene_start_time = time_tracker.get_current_time()
            scene_conclusion_pending = False
            
            # Generate new scene
            print(f"\n{Color.SYSTEM}Generating next scene...{Color.RESET}")
            
            try:
                # Save current location's NUAs before leaving
                if available_npcs:
                    current_nua_names = [npc.sheet.name for npc in available_npcs if hasattr(npc, 'sheet')]
                    context_manager = get_context_manager()
                    if context_manager and current_nua_names:
                        context_manager.set_nuas(current_nua_names)
                        print(f"{Color.INFO}[PERSISTENCE] Saved {len(current_nua_names)} NUA(s) at current location{Color.RESET}")
                
                # Leaving the place: reset available NPCs for the new location
                available_npcs = []
                scene_description, available_npcs = conductor.generate_new_scene(
                    actor, scene_number, "user_initiated"
                )
                print(f"{Color.SUCCESS}Successfully generated Scene {scene_number}{Color.RESET}")
                
                # Auto-detect ally groups among NPCs
                if available_npcs:
                    try:
                        ally_coordinator.auto_detect_ally_groups(available_npcs)
                    except Exception:
                        pass
                
                try:
                    conductor.scene_description = scene_description
                except Exception:
                    pass
                # Record new scene start
                try:
                    tracker.start_scene(scene_number=scene_number, scene_data={}, nua_data=None, scene_description=scene_description)
                    # Save the new scene start as part of transition
                    start_req = save_coordinator.create_scene_transition_request({
                        'scene_number': scene_number,
                        'scene_description': scene_description,
                        'time_context': time_context,
                        'transition_phase': 'scene_start',
                        'available_npc_names': [getattr(n.sheet, 'name', str(getattr(n, 'name', 'NPC'))) for n in (available_npcs or [])],
                        'actor_state': {
                            'name': actor.sheet.name,
                            'statuses': {str(st.name): {'value': st_obj.value, 'descriptor': get_status_descriptor(st_obj.value)} for st, st_obj in actor.sheet.statuses.items()}
                        }
                    })
                    save_coordinator.request_save(start_req)
                except Exception:
                    pass
                # Debug: Show Narrative Framing (Mode/Tone/Intent) for validation after new scene
                try:
                    loop_state = narrator.get_narrative_loop_state()
                    mode = loop_state.get('mode', 'unknown') if loop_state else 'unknown'
                    tone = loop_state.get('tone', 'unknown') if loop_state else 'unknown'
                    intent = loop_state.get('intent', 'unknown') if loop_state else 'unknown'
                    print(f"{Color.SYSTEM}🔧 Narrative Framing — Mode: {mode} | Tone: {tone} | Intent: {intent}{Color.RESET}")
                except Exception:
                    pass
                # Heuristic: schedule an arrival if the new scene suggests vehicle travel
                try:
                    vehicle3 = _infer_vehicle(scene_description)
                    if vehicle3 != 'unknown':
                        scheduler.schedule_arrival('Next stop', 3, simulation_time_tracker.get_total_simulation_time())
                except Exception:
                    pass
                continue
            except Exception as e:
                print(f"{Color.ERROR}Failed to generate new scene: {e}{Color.RESET}")
                print(f"{Color.WARNING}Continuing in current scene...{Color.RESET}")
                scene_number -= 1
                scene_action_count += 1
        
        # -------------------------------------------------------------------------
        # BACKGROUND SIMULATION: Post-User Turns (Lower Initiative NUAs)
        # -------------------------------------------------------------------------
        # Execute actions for NUAs that act AFTER the user
        # Only if we are still in ROAM mode and didn't just change scenes (check available_npcs validity)
        if roam_turn_order and encounter_checker.get_current_mode() == SimulationMode.ROAM:
            try:
                # Only process actors who are still present (e.g. didn't leave or user didn't leave them)
                valid_turn_order = [
                    entry for entry in roam_turn_order 
                    if entry.get('is_user') or entry.get('actor') in available_npcs
                ]
                
                if valid_turn_order:
                    bg_result_post = bg_sim.execute_post_user_turns(
                        valid_turn_order, 
                        actor, 
                        available_npcs, 
                        scene_description, 
                        time_context
                    )
                    
                    # Handle Interrupt (NUA started an exchange late in the turn)
                    if isinstance(bg_result_post, dict) and bg_result_post.get('interrupt'):
                        event = bg_result_post.get('event', {})
                        initiator = event.get('initiator')
                        
                        # Validate initiator before using
                        if initiator and hasattr(initiator, 'sheet') and hasattr(initiator.sheet, 'name'):
                            print(f"\n{Color.WARNING}🚨 ENCOUNTER TRIGGERED BY {initiator.sheet.name.upper()}!{Color.RESET}")
                            
                            # CRITICAL: Seed encounter participants for ENCOUNTER init (avoid empty participants crash)
                            try:
                                encounter_checker.current_context.participants = [initiator]
                                encounter_checker.current_context.trigger_action = event.get('trigger_action', 'background initiative')
                                encounter_checker.current_context.encounter_type = event.get('encounter_type', 'general')
                            except Exception:
                                pass
                            
                            # Switch mode to ENCOUNTER
                            encounter_checker.set_mode(SimulationMode.ENCOUNTER)
                            
                            # Setup Round Manager override
                            if hasattr(conductor, 'round_manager'):
                                conductor.round_manager.set_round_one_proactor(initiator)
                            
                            # We don't continue/restart loop here because we need to finish loop cleanup
                            # But the mode is set for NEXT iteration
                        else:
                            print(f"{Color.WARNING}[BG SIM] NUA encounter triggered but initiator invalid{Color.RESET}")
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[BG SIM] Post-turn error: {e}{Color.RESET}")

        # Update time display with enhanced atmospheric descriptions
        current_clock_time = master_time.time_tracker.get_current_time()
        elapsed_time = simulation_time_tracker.get_simulation_time_display()
        print(f"\n{Color.SYSTEM}🕘 Time: {current_clock_time.format_full()} | Elapsed: {elapsed_time}{Color.RESET}")
        
        # Get atmospheric time description for narrative context (don't display)
        current_atmospheric = time_tracker.get_atmospheric_description()
        lighting_condition = time_context.get('lighting_condition', 'natural light')
        time_of_day = time_context.get('time_of_day', 'unknown')
        lighting_mood = _get_lighting_mood(time_of_day)
        
        # Create enhanced time narrative with atmospheric details
        atmospheric_details = f"{current_atmospheric} with {lighting_condition} creating {lighting_mood} lighting"
        time_narrative = f"Time progressed to {current_clock_time.format_full()}. {atmospheric_details}"
        scene_context_info = f"{time_context['time_of_day'].value if hasattr(time_context['time_of_day'], 'value') else str(time_context['time_of_day'])} - {time_context['lighting_condition']} lighting, {time_context['atmospheric_description']}"
        narrative_context_manager.add_narrative_event(
            event_type=NarrativeEventType.TIME_PASSAGE,
            narrative_text=time_narrative,
            actors_involved=[actor.sheet.name],
            importance=NarrativeImportance.ROUTINE,
            emotional_tone="neutral",
            scene_context=scene_context_info
        )
    
    # Request coordinated final save and flush all pending saves
    final_save_request = save_coordinator.create_user_quit_request({
        'total_scenes': scene_number,
        'total_actions': auto_save_counter + (scene_action_count if scene_action_count > 0 else 0),
        'final_time': time_tracker.get_current_time().format_full(),
        'session_duration': simulation_time_tracker.get_total_simulation_time(),
        'completion_status': 'user_quit'
    })
    
    save_coordinator.request_save(final_save_request)
    
    # Flush all pending saves before exit
    print(f"\n{Color.SYSTEM}💾 Processing final saves...{Color.RESET}")
    final_results = save_coordinator.flush_pending_saves()
    
    if final_results:
        print(f"{Color.SUCCESS}✓ All saves completed successfully{Color.RESET}")
    else:
        print(f"{Color.WARNING}⚠️ Some saves may have failed{Color.RESET}")
    
    # End session
    print(f"\n{Color.SYSTEM}Session ended. Thank you for playing!{Color.RESET}")
    tracker.end_session()


if __name__ == "__main__":
    # Check for quick exchange test flag
    if "--quick-exchange" in sys.argv:
        print(f"\n{Color.HEADER}{'='*60}{Color.RESET}")
        print(f"{Color.HEADER}QUICK EXCHANGE TEST MODE{Color.RESET}")
        print(f"{Color.HEADER}{'='*60}{Color.RESET}\n")
        print(f"{Color.INFO}Skipping character creation...{Color.RESET}")
        print(f"{Color.INFO}Loading pre-made test scenario...{Color.RESET}\n")
        
        # Set quick exchange flag
        import builtins
        builtins.QUICK_EXCHANGE_MODE = True
    
    main()
 

