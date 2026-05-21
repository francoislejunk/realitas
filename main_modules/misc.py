"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module

def _ua_display_name(actor, ua_actor=None) -> str:
    """
    Get a display name for a User Actor, with optional comparison to another actor.
    
    Args:
        actor: The actor to get display name for
        ua_actor: Optional UA actor for comparison
        
    Returns:
        Formatted display name string
    """
    try:
        name = getattr(actor.sheet, 'name', 'Unknown') if hasattr(actor, 'sheet') else str(actor)
        occupation = getattr(actor.sheet, 'occupation', '') if hasattr(actor, 'sheet') else ''
        
        if occupation:
            return f"{name} ({occupation})"
        return name
    except Exception:
        return str(actor)


def get_sensing_calculator():
    """Get or create the sensing bubble calculator"""
    global _sensing_calculator
    if _sensing_calculator is None:
        _sensing_calculator = SensingBubbleCalculator()
    return _sensing_calculator




def get_actor_introduction_with_outliers(actor, include_category: bool = True) -> str:
    """
    Get a formatted introduction for an actor including S-trait outliers.
    
    This is called when ANY actor (NUA, MNUA, INUA) is introduced.
    """
    try:
        # Get S-trait outliers
        outliers = format_outliers_for_narrative(actor)
        
        # Get actor category
        category = get_actor_category(actor)
        category_prefix = ""
        if include_category and category == ActorCategory.MNUA:
            category_prefix = "[MAJOR] "
        
        # Get basic info
        name = getattr(actor.sheet, 'name', 'Unknown') if hasattr(actor, 'sheet') else str(actor)
        occupation = getattr(actor.sheet, 'occupation', '') if hasattr(actor, 'sheet') else ''
        
        # Build introduction
        parts = [category_prefix + name]
        if occupation:
            parts.append(f"({occupation})")
        if outliers:
            parts.append(f"- {outliers}")
        
        return " ".join(parts)
    except Exception:
        return str(actor)




def check_mnua_graduation(actor, interaction_count: int = 0) -> bool:
    """
    Check if an NUA should graduate to MNUA status.
    
    Called after significant interactions.
    """
    try:
        from actors import graduate_to_mnua
        
        if can_graduate_to_mnua(actor, interaction_count=interaction_count):
            if graduate_to_mnua(actor):
                return True
    except Exception:
        return False

    return False


# ═══════════════════════════════════════════════════════════════════════════════
# NEW INTERNAL VOICE & STORYTELLER HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global instances for new systems
_voice_interpreter: 'InternalVoiceInterpreterAgent' = None
_voice_creator: 'InternalVoiceCreatorAgent' = None
_storyteller: 'StorytellerAgent' = None
_reputation_system: 'ReputationSystem' = None

# Global instances for additional immersion systems
_witness_system: 'WitnessReactionSystem' = None
_stranger_describer: 'StrangerDescriber' = None
_dialogue_context: 'DialogueContextSystem' = None
_personality_generator: 'PersonalityGenerator' = None
_mood_analyzer: 'MoodAnalyzer' = None
_nua_life_tracker: 'NUALifeTracker' = None
_clue_tracker: 'DiegeticClueTracker' = None
_tactical_awareness: 'TacticalAwarenessSystem' = None
_failure_narrator: 'FailureNarrativeGenerator' = None
_sympathy_modifier: 'SympathyBehaviorModifier' = None




def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default




def check_and_award_title(
    actor_name: str,
    action_description: str,
    action_outcome: str,
    location: str,
    witnesses: List[str] = None,
    context: str = "",
    max_retries: int = 2
) -> Optional['Title']:
    """
    Check if an action deserves a reputation title with retry handling.
    
    Returns Title if earned, None otherwise.
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE or _reputation_system is None:
        return None
    
    for attempt in range(max_retries):
        try:
            title = _reputation_system.detect_title_worthy_action(
                actor_name=actor_name,
                action_description=action_description,
                action_outcome=action_outcome,
                location=location,
                witnesses=witnesses,
                context=context
            )
            
            if title:
                display_title_earned(title, actor_name)
            
            return title
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{Color.WARNING}⚠️ Title check attempt {attempt + 1} failed: {e}{Color.RESET}")
                time.sleep(0.5)
            else:
                print(f"{Color.WARNING}⚠️ Title check failed after {max_retries} attempts{Color.RESET}")
    
    return None




def _calculate_detailed_success(*, actor, action_data: dict, target_actor=None, additional_stress: int = 0) -> int:
    try:
        if isinstance(action_data, dict):
            sc = action_data.get('success_calculation')
            if isinstance(sc, dict):
                for k in ('total', 'final_result', 'total_successes'):
                    if k in sc:
                        try:
                            return int(sc.get(k) or 0)
                        except Exception:
                            pass

        from unified_formula import calculate_unified_result
        from actor_sheet import SFactorType, StatusType

        utas = {}
        try:
            if isinstance(action_data, dict):
                utas = action_data.get('utas_factors') or {}
        except Exception:
            utas = {}

        s_trait_name = None
        try:
            s_trait_name = utas.get('s_trait_to_use') or utas.get('s_trait')
        except Exception:
            s_trait_name = None
        if not s_trait_name:
            s_trait_enum = SFactorType.STURDINESS
        else:
            try:
                s_trait_enum = SFactorType[str(s_trait_name).upper()]
            except Exception:
                s_trait_enum = SFactorType.STURDINESS

        skill_name = None
        try:
            skill_data = utas.get('skill', {})
            if isinstance(skill_data, dict):
                skill_name = skill_data.get('name')
            elif isinstance(skill_data, str):
                skill_name = skill_data
        except Exception:
            skill_name = None
        if skill_name and str(skill_name).lower() in ('none', 'null', 'n/a'):
            skill_name = None

        endowment_name = None
        try:
            endowment_data = utas.get('endowment', {})
            if isinstance(endowment_data, dict):
                endowment_name = endowment_data.get('name')
            elif isinstance(endowment_data, str):
                endowment_name = endowment_data
        except Exception:
            endowment_name = None
        if endowment_name and str(endowment_name).lower() in ('none', 'null', 'n/a'):
            endowment_name = None

        stress_level = 3
        try:
            stress_level = int(utas.get('stress_level', 3) or 3)
        except Exception:
            stress_level = 3
        try:
            stress_level = int(stress_level) + int(additional_stress or 0)
        except Exception:
            pass

        shift_polarity = 'Subtractive'
        try:
            shift_polarity = str(utas.get('shift_polarity') or shift_polarity)
        except Exception:
            shift_polarity = 'Subtractive'

        targeted_status = None
        try:
            st_name = utas.get('status_to_shift')
            if st_name:
                targeted_status = StatusType[str(st_name).upper()]
        except Exception:
            targeted_status = None

        supplement_val = 0
        try:
            sup_data = utas.get('supplement', {})
            if isinstance(sup_data, dict):
                supplement_val = int(sup_data.get('value') or 0)
            elif isinstance(sup_data, int):
                supplement_val = int(sup_data)
        except Exception:
            supplement_val = 0

        result = calculate_unified_result(
            actor=actor,
            s_trait=s_trait_enum,
            skill_name=skill_name,
            target_actor=target_actor,
            shift_polarity=shift_polarity,
            targeted_status=targeted_status,
            supplement_val=int(supplement_val or 0),
            serendipity_override=None,
            stress_level_override=stress_level,
            endowment_name=endowment_name
        )
        try:
            score = int(result.get('final_result', 0) or 0)
        except Exception:
            score = 0
        try:
            if isinstance(action_data, dict):
                action_data['success_calculation'] = {'total': score}
        except Exception:
            pass
        return score
    except Exception:
        return 0




def get_nua_life_changes(nua_name: str, time_since_last_seen: int) -> List[Dict]:
    """
    Get observable changes in an NUA since last seen.
    
    Args:
        nua_name: Name of the NUA
        time_since_last_seen: Minutes since last encounter
        
    Returns list of observable changes (appearance, mood, possessions, etc.)
    """
    if not NUA_LIFE_TRACKER_AVAILABLE or _nua_life_tracker is None:
        return []
    
    try:
        return _nua_life_tracker.get_observable_changes(nua_name, time_since_last_seen)
    except Exception:
        return []




def record_nua_last_seen(nua_name: str, location: str, activity: str = None):
    """
    Record when and where an NUA was last seen.
    """
    if not NUA_LIFE_TRACKER_AVAILABLE or _nua_life_tracker is None:
        return
    
    try:
        _nua_life_tracker.record_last_seen(nua_name, location, activity)
    except Exception:
        pass




def detect_environmental_clues(narrative: str) -> List[Dict]:
    """
    Detect environmental clues in narrative that imply NPC presence.
    
    Returns list of detected clues with types and implications.
    """
    if not CLUE_TRACKER_AVAILABLE or _clue_tracker is None:
        return []
    
    try:
        return _clue_tracker.detect_clues(narrative)
    except Exception:
        return []




def get_tactical_recommendation(npc, enemies: List, allies: List, scene_description: str) -> Dict:
    """
    Get tactical recommendation for an NPC in combat.
    
    Returns dict with recommended action, reasoning, etc.
    """
    if not TACTICAL_AWARENESS_AVAILABLE or _tactical_awareness is None:
        return {}
    
    try:
        return _tactical_awareness.assess_tactical_situation(npc, enemies, allies, scene_description)
    except Exception:
        return {}




def generate_failure_narrative(action: str, failure_reason: str, actor, context: str) -> str:
    """
    Generate a narrative description for a failed action.
    
    Returns narrative string.
    """
    if not FAILURE_NARRATIVE_AVAILABLE or _failure_narrator is None:
        return f"The attempt fails."
    
    try:
        return _failure_narrator.generate_failure_narrative(action, failure_reason, actor, context)
    except Exception:
        return f"The attempt fails."




def get_object_status(object_name: str, status_type: str, default: int = 3) -> int:
    """
    Get status value for an INUA (object).
    """
    if not OBJECT_REGISTRY_AVAILABLE:
        return default
    
    try:
        return get_status(object_name, status_type, default)
    except Exception:
        return default




def set_object_status(object_name: str, status_type: str, value: int):
    """
    Set status value for an INUA (object).
    """
    if not OBJECT_REGISTRY_AVAILABLE:
        return
    
    try:
        set_status(object_name, status_type, value)
    except Exception:
        pass




def update_pygame_map_actors(actor, available_npcs=None):
    """
    Update pygame map with current actor positions.
    
    Called after each action.
    """
    try:
        from pygame_spatial_map import get_pygame_map
        
        map_inst = get_pygame_map()
        if not map_inst or not map_inst.running:
            return
        
        # Update UA position
        if hasattr(actor, 'sheet'):
            ua_pos = getattr(actor, 'position', None)
            if ua_pos:
                update_map_actor(
                    actor_id="ua_001",
                    name=actor.sheet.name,
                    x=ua_pos.x if hasattr(ua_pos, 'x') else ua_pos[0],
                    y=ua_pos.y if hasattr(ua_pos, 'y') else ua_pos[1],
                    actor_type="ua"
                )
        
        # Update NUA positions
        if available_npcs:
            for i, npc in enumerate(available_npcs):
                if hasattr(npc, 'sheet'):
                    npc_pos = getattr(npc, 'position', None)
                    if npc_pos:
                        # Determine actor type
                        category = get_actor_category(npc)
                        actor_type = "mnua" if category == ActorCategory.MNUA else "nua"
                        
                        update_map_actor(
                            actor_id=f"nua_{i:03d}",
                            name=npc.sheet.name,
                            x=npc_pos.x if hasattr(npc_pos, 'x') else npc_pos[0],
                            y=npc_pos.y if hasattr(npc_pos, 'y') else npc_pos[1],
                            actor_type=actor_type,
                            occupation=getattr(npc.sheet, 'occupation', '')
                        )
    except Exception:
        pass  # Map updates are non-critical


# Runtime toggles for redesigned main (non-invasive)
# Suppress verbose DEBUG prints emitted in this file when true
SUPPRESS_DEBUG = os.getenv("REDESIGNED_SUPPRESS_DEBUG", "false").strip().lower() == "true"
# Optional reporter verbosity (e.g., "minimal", "normal", "verbose")
REDESIGNED_VERBOSITY = os.getenv("REDESIGNED_VERBOSITY", "").strip().lower()
# Enable Intent Availability System (ENABLED by default with improved context)
ENABLE_INTENT_AVAILABILITY = os.getenv("ENABLE_INTENT_AVAILABILITY", "true").strip().lower() == "true"
# SPARK fade controls (hybrid policy: whichever comes first)
SPARK_FADE_TURNS = int(os.getenv("SPARK_FADE_TURNS", "2"))
SPARK_FADE_HOURS = float(os.getenv("SPARK_FADE_HOURS", "0.1667"))

# Context summary character limit
CTX_SUMMARY_MAX_CHARS = 1200

# Import new systems
from llm_agents.encounter_checker import EncounterChecker, SimulationMode
from simulation_time_tracker import SimulationTimeTracker

# Import WORLD_BUILDER systems - Using Consolidated Worldbuilding RAG
from WORLD_BUILDER.worldbuilding_rag import WorldbuildingRAGSystem, WorldbuildingCategory
# Note: Lore is loaded from realitas_lore.py - run that file to update worldbuilding
# Run: python WORLD_BUILDER/realitas_lore.py to load/update lore

# Import Key Memories System
from key_memories_system import (
    initialize_key_memories,
    get_key_memories,
    handle_memory_command,
    MemoryCategory,
    MemoryImportance
)

# Import Mention System
from mention_system import MentionSystem

# Import NUA Memory System
from npc_memory_system import (
    initialize_nua_memory_system,
    get_nua_memory_system
)

# Import Automatic Memory Creation
from automatic_memory_creation import (
    initialize_automatic_memory_creator,
    get_automatic_memory_creator
)

# Import Vessel Selection System
from vessel_selection_system import create_vessel_selection_system
# SparkGenerator removed - using StorytellerAgent's spark system (MOMENTUM, EXCHANGE, CALLBACK) instead
from llm_agents.scene_event_scheduler import SceneEventScheduler
from master_time_coordinator import initialize_master_time_coordinator, get_master_time_coordinator, TimeEventType
from save_coordinator import initialize_save_coordinator, get_save_coordinator
from enhanced_monetary_system import EnhancedMonetaryProcessor

# Import Narrative Context System (needed by helper functions)
from narrative_context_system import NarrativeEventType, NarrativeImportance




def _create_quick_test_actor():
    """Create a pre-made test actor for quick exchange testing."""
    from actor_sheet import SFactorType
    
    # Create S-Factors with values in constructor
    s_factors = SFactors(
        swiftness=3,
        sociability=4,
        sturdiness=3,
        smarts=3,
        shadow=2
    )
    
    # Create personality traits
    personality_traits = {
        "internal": "eager to test the system",
        "external": "methodical and observant"
    }
    
    # Create goals
    goals = ["Test all exchange mechanics", "Verify system functionality"]
    
    # Create ActorSheet with all required parameters
    sheet = ActorSheet(
        name="Test User",
        age=30,
        location="Test Bar",
        occupation="Tester",
        s_factors=s_factors,
        personality_traits=personality_traits,
        goals=goals
    )
    
    # Set skills
    sheet.skills = {
        "Persuasion": 2,
        "Intimidation": 1,
        "Brawling": 2
    }
    
    # Set statuses
    sheet.statuses[StatusType.STAMINA].value = 3
    sheet.statuses[StatusType.SPIRIT].value = 3
    sheet.statuses[StatusType.SUPPLY].value = 3
    
    # Add inventory
    sheet.inventory = [
        Item("Leather Jacket", "Worn but sturdy", supplement_bonus=1)
    ]
    
    actor = UserActor(sheet)
    actor.is_user_actor = True
    
    print(f"{Color.SUCCESS}✓ Quick test actor created: {_ua_display_name(actor, ua_actor=actor)}{Color.RESET}")
    return actor




def _create_dynamic_user_actor(scene_creator, rag_system=None, return_vessel_system=False):
    """Create UserActor with vessel selection (3 choices).
    
    Args:
        scene_creator: The scene creator instance
        rag_system: Optional RAG system for occupation diversity
        return_vessel_system: If True, returns (actor, vessel_system) tuple for deferred memory creation
    
    Returns:
        UserActor if return_vessel_system is False
        (UserActor, VesselSelectionSystem) tuple if return_vessel_system is True
    """
    # Check for quick exchange mode
    if hasattr(__builtins__, 'QUICK_EXCHANGE_MODE') and __builtins__.QUICK_EXCHANGE_MODE:
        actor = _create_quick_test_actor()
        return (actor, None) if return_vessel_system else actor
    
    try:
        # Clear actor registry before vessel selection to prevent unselected vessels from appearing in relationships
        from actor_sheet import ActorSheet
        ActorSheet.clear_registry()
        
        # Initialize vessel selection system with RAG for occupation diversity
        vessel_system = create_vessel_selection_system(scene_creator, Path("./simulation_data"), rag_system)
        
        # Generate, display, and select vessel (memories created separately now)
        actor = vessel_system.select_vessel()
        
        # Clear registry again and re-register only the selected vessel
        ActorSheet.clear_registry()
        actor.sheet._actor_registry[actor.sheet.name] = actor.sheet
        
        return (actor, vessel_system) if return_vessel_system else actor
    except Exception as e:
        # Fallback to single random vessel if selection fails
        print(f"{Color.WARNING}Vessel selection failed: {e}{Color.RESET}")
        print(f"{Color.INFO}Generating random vessel...{Color.RESET}")
        
        # Clear registry before fallback generation
        from actor_sheet import ActorSheet
        ActorSheet.clear_registry()
        
        actor = scene_creator.generate_user_actor()
        print(f"{Color.SUCCESS}✓ Your vessel awakens: {_ua_display_name(actor, ua_actor=actor)} ({actor.sheet.occupation}){Color.RESET}")
        
        # Note: Initial memories will be generated after key_memories system is initialized
        
        return (actor, None) if return_vessel_system else actor




def _build_reactor_sheet_data(actor):
    """Build comprehensive actor sheet data for reactor display."""
    from narrative_utils import get_narrative_descriptor, get_status_descriptor
    from actor_sheet import StatusType, SFactorType
    
    personality_internal = getattr(actor.sheet, 'personality_traits', {}).get('internal', 'N/A')
    personality_external = getattr(actor.sheet, 'personality_traits', {}).get('external', 'N/A')
    
    occupation = getattr(actor.sheet, 'occupation', 'N/A')
    affiliation = getattr(actor.sheet, 'affiliation', 'N/A')
    
    s_factors = {}
    for s_factor_type in [SFactorType.SWIFTNESS, SFactorType.SOCIABILITY, SFactorType.STURDINESS, SFactorType.SMARTS, SFactorType.SHADOW]:
        value = actor.sheet.s_factors.get_factor(s_factor_type)
        s_factors[s_factor_type.name.lower()] = value
    
    skills = dict(actor.sheet.skills)
    
    endowments = getattr(actor.sheet, 'endowments', {})
    
    statuses = {}
    for status_type in [StatusType.STAMINA, StatusType.SPIRIT, StatusType.SUPPLY]:
        status_data = actor.sheet.statuses.get(status_type)
        if status_data:
            status_dict = {
                'value': status_data.value,
                'modifier': status_data.get_modifier()
            }
            if status_type == StatusType.SUPPLY and hasattr(status_data, 'money_amount'):
                status_dict['money_amount'] = status_data.money_amount
            statuses[status_type.name.lower()] = status_dict
    
    supplements = {}
    if hasattr(actor.sheet, 'inventory'):
        for item in actor.sheet.inventory:
            if hasattr(item, 'supplement_bonus') and item.supplement_bonus > 0:
                supplements[item.name] = item.supplement_bonus
    
    sympathies = getattr(actor.sheet, 'sympathies', {})
    
    life_goal = getattr(actor.sheet, 'goals', ['N/A'])[0] if hasattr(actor.sheet, 'goals') and actor.sheet.goals else 'N/A'
    
    return {
        'personality_internal': personality_internal,
        'personality_external': personality_external,
        'occupation': occupation,
        'affiliation': affiliation,
        's_factors': s_factors,
        'skills': skills,
        'endowments': endowments,
        'supplements': supplements,
        'statuses': statuses,
        'sympathies': sympathies,
        'life_goal': life_goal
    }




def _generate_connected_roam_scene(narrator, narrative_context_manager, scene_description: str, last_action_narrative: str, time_context: dict) -> str:
    """Generate a ROAM scene description that is explicitly connected to the most recent encounter context.
    Falls back to the existing scene description on failure.
    """
    try:
        # Build a minimal turn snapshot to seed framing
        turn_data = {
            'user_input': 'Encounter resolved',
            'scene_description': scene_description,
            'continuity_check': {'judgment': 'Possible'}
        }
        # Use enhanced narrative loop if available, fallback to narrator's loop
        if 'narrative_loop' in locals() or 'narrative_loop' in globals():
            framing = narrative_loop.process_turn(
                turn_data=turn_data,
                scene_description=scene_description,
                time_context=time_context,
                available_npcs=[]
            )
        else:
            framing = narrator.narrative_loop.process_turn(turn_data, time_context=time_context)
    except Exception:
        framing = None

    # Transition bridge uses last action if available
    bridge = last_action_narrative.strip() if isinstance(last_action_narrative, str) and last_action_narrative.strip() else "The immediate tension eases and the surroundings settle back into focus."

    # Compose elements for a connected scene refresh
    scene_elements = {
        'setting': scene_description or 'The current location',
        'transition_bridge': bridge,
        'ua_goal': 'Continue objectives based on prior events',
        'conflict': 'Open exploration'
    }

    try:
        new_desc = narrator.generate_scene_with_narrative_loop(
            scene_elements=scene_elements,
            nua_name="",
            turn_data=turn_data,
            time_context=time_context,
        )
        # Record transition into the narrative context
        try:
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.SCENE_TRANSITION,
                narrative_text=f"Encounter resolved → {bridge}",
                actors_involved=[],
                importance=NarrativeImportance.NOTABLE,
                emotional_tone="transitional",
                scene_context="Return to ROAM"
            )
        except Exception:
            pass
        return new_desc
    except Exception:
        return scene_description



def _clamp_text(text: str, limit: int = CTX_SUMMARY_MAX_CHARS) -> str:
    try:
        s = str(text)
        if len(s) <= limit:
            return s
        head = s[: int(limit * 0.7)]
        tail = s[-int(limit * 0.3) :]
        return head + "\n...\n" + tail
    except Exception:
        return text



def _ensure_min_utas_fields(action_data: dict, actor) -> dict:
    """Ensure required UTAS fields exist using safe defaults.
    Does not alter narrative fields. Uses actor sheet to resolve numeric values where possible.
    """
    if not isinstance(action_data, dict):
        action_data = {}
    utas = action_data.setdefault('utas_factors', {}) if isinstance(action_data.get('utas_factors'), dict) else action_data.setdefault('utas_factors', {})

    # Defaults
    utas.setdefault('exchange_type', 'contested')
    utas.setdefault('status_to_shift', 'SPIRIT')
    s_trait_label = str(utas.get('s_trait_to_use') or 'SHADOW').strip().upper()
    utas['s_trait_to_use'] = s_trait_label

    # Resolve s_trait_value from actor sheet
    try:
        from actor_sheet import SFactorType
        mapping = {
            'SWIFTNESS': SFactorType.SWIFTNESS,
            'SOCIABILITY': SFactorType.SOCIABILITY,
            'STURDINESS': SFactorType.STURDINESS,
            'SMARTS': SFactorType.SMARTS,
            'SHADOW': SFactorType.SHADOW,
        }
        s_type = mapping.get(s_trait_label, SFactorType.SHADOW)
        if hasattr(actor, 'sheet') and hasattr(actor.sheet, 's_factors'):
            utas['s_trait_value'] = int(actor.sheet.s_factors.get_factor(s_type))
    except Exception:
        utas.setdefault('s_trait_value', 1)

    # Skill
    skill = utas.get('skill')
    if not isinstance(skill, dict):
        skill = {'name': 'none', 'value': 0}
    else:
        skill.setdefault('name', 'none')
        try:
            if skill['name'] != 'none' and hasattr(actor.sheet, 'skills'):
                skill['value'] = int(actor.sheet.skills.get(skill['name'], 0))
            else:
                skill.setdefault('value', 0)
        except Exception:
            skill.setdefault('value', 0)
    utas['skill'] = skill

    # Endowment
    endowment = utas.get('endowment')
    if not isinstance(endowment, dict):
        endowment = {'name': 'none', 'value': 0}
    else:
        endowment.setdefault('name', 'none')
        try:
            if endowment['name'] != 'none' and hasattr(actor.sheet, 'endowments'):
                endowment['value'] = int(actor.sheet.endowments.get(endowment['name'], 0))
            else:
                endowment.setdefault('value', 0)
        except Exception:
            endowment.setdefault('value', 0)
    utas['endowment'] = endowment

    # Supplement
    supplement = utas.get('supplement')
    if not isinstance(supplement, dict):
        supplement = {'name': 'none', 'value': 0}
    else:
        supplement.setdefault('name', 'none')
        try:
            if supplement['name'] == 'none':
                supplement.setdefault('value', 0)
            else:
                # Conservative: derive total supplement bonus if available
                if hasattr(actor.sheet, 'get_total_supplement_bonus'):
                    supplement['value'] = int(actor.sheet.get_total_supplement_bonus())
                else:
                    supplement.setdefault('value', 0)
        except Exception:
            supplement.setdefault('value', 0)
    utas['supplement'] = supplement

    # Stress and shift
    try:
        utas['stress_level'] = int(utas.get('stress_level', 3))
    except Exception:
        utas['stress_level'] = 3
    utas.setdefault('shift_type', 'Temporary')
    utas.setdefault('shift_polarity', 'Subtractive')

    return action_data



def _drain_windows_keyboard_buffer():
    """Drain stray keypresses on Windows consoles to prevent pre-typed input leaking into next prompt."""
    if os.name == 'nt' and msvcrt:
        while msvcrt.kbhit():
            try:
                msvcrt.getwch()
            except Exception:
                try:
                    msvcrt.getch()
                except Exception:
                    break



def _win_readline() -> str:
    """Custom line reader for Windows consoles using msvcrt for robust echo and prompt control."""
    if not (os.name == 'nt' and msvcrt and sys.stdin.isatty()):
        return input()
    buf = []
    while True:
        # While waiting for console input, allow pygame map actions to be processed
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
                        return f"__PMAP_TRAVEL__ {str(evt_payload)}"
        except Exception:
            pass

        if not msvcrt.kbhit():
            time.sleep(0.03)
            continue

        ch = msvcrt.getwch()
        # Enter / Return
        if ch in ('\r', '\n'):
            print("")  # Move to next line after enter
            break
        # Ctrl-C
        if ch == '\x03':
            raise KeyboardInterrupt
        # Backspace handling
        if ch in ('\b', '\x08'):
            if buf:
                buf.pop()
                # Erase last character from console
                sys.stdout.write('\b \b')
                sys.stdout.flush()
            continue
        # Printable char
        buf.append(ch)
        sys.stdout.write(ch)
        sys.stdout.flush()
    return ''.join(buf)



def _convert_ua_to_second_person(text: str, ua_name: str) -> str:
    """
    Convert any third-person UA references to second person for immersion.
    
    Args:
        text: The narrative text to convert
        ua_name: The UA's full name
        
    Returns:
        Text with UA references converted to second person
    """
    if not text or not ua_name:
        return text
    
    import re
    
    # Get first name for matching
    first_name = ua_name.split()[0] if ' ' in ua_name else ua_name
    
    # Patterns to replace (case-insensitive)
    # Pattern 1: "Name verb" → "You verb"
    text = re.sub(rf'\b{re.escape(ua_name)}\s+(pushes|walks|stands|sits|enters|exits|looks|examines|takes|gives|speaks|says|asks|runs|moves|goes|comes|leaves|arrives|departs)',
                  r'You \1', text, flags=re.IGNORECASE)
    text = re.sub(rf'\b{re.escape(first_name)}\s+(pushes|walks|stands|sits|enters|exits|looks|examines|takes|gives|speaks|says|asks|runs|moves|goes|comes|leaves|arrives|departs)',
                  r'You \1', text, flags=re.IGNORECASE)
    
    # Pattern 2: "Name's" → "Your"
    text = re.sub(rf'\b{re.escape(ua_name)}\'s\b', 'Your', text, flags=re.IGNORECASE)
    text = re.sub(rf'\b{re.escape(first_name)}\'s\b', 'Your', text, flags=re.IGNORECASE)
    
    # Pattern 3: "Name" at start of sentence → "You"
    text = re.sub(rf'(^|\.|\n)\s*{re.escape(ua_name)}\s+', r'\1 You ', text, flags=re.IGNORECASE)
    text = re.sub(rf'(^|\.|\n)\s*{re.escape(first_name)}\s+', r'\1 You ', text, flags=re.IGNORECASE)
    
    # Pattern 4: Pronouns - "him/his/he" → "you/your/you"
    text = re.sub(r'\bhim\b', 'you', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhis\b', 'your', text, flags=re.IGNORECASE)
    text = re.sub(r'\bhe\s+(pushes|walks|stands|sits|enters|exits|looks|examines|takes|gives|speaks|says|asks|runs|moves|goes|comes|leaves|arrives|departs)',
                  r'you \1', text, flags=re.IGNORECASE)
    
    # Pattern 5: "behind him" → "behind you", "around him" → "around you"
    text = re.sub(r'\b(behind|around|near|beside|with|for|to)\s+him\b', r'\1 you', text, flags=re.IGNORECASE)
    
    return text




def _apply_narrative_item_gains_to_ua(narrative_text: str, ua_actor) -> None:
    try:
        if not isinstance(narrative_text, str) or not narrative_text.strip():
            return
        if ua_actor is None or not hasattr(ua_actor, 'sheet'):
            return

        from actor_sheet import Item
        import re

        txt = narrative_text

        patterns = [
            r"\b(?:hands|gives|passes|slips|presses|offers)\s+you\s+(?:a|an|the)\s+([^\.,;\n]+)",
            r"\b(?:sets|drops|places)\s+(?:a|an|the)\s+([^\.,;\n]+)\s+near\s+your\s+(?:hand|palm|feet)",
        ]

        gained = []
        for pat in patterns:
            for m in re.finditer(pat, txt, flags=re.IGNORECASE):
                item_name = (m.group(1) or '').strip()
                if not item_name:
                    continue
                low = item_name.lower()
                # Money is handled via SUPPLY.money_amount; do not add money containers as inventory items.
                if any(k in low for k in ['coin', 'coins', 'money', 'cash', 'pouch', 'bag of coins', 'silver', 'gold']):
                    continue
                item_name = item_name.strip("\"' ").strip()
                if item_name:
                    gained.append(item_name)

        if not gained:
            return

        existing_lower = set()
        try:
            for it in getattr(ua_actor.sheet, 'inventory', []) or []:
                existing_lower.add(str(getattr(it, 'name', '') or '').lower())
        except Exception:
            existing_lower = set()

        for item_name in gained:
            if item_name.lower() in existing_lower:
                continue
            try:
                ua_actor.sheet.inventory.append(
                    Item(name=item_name, description="Received during an exchange.", supplement_bonus=0)
                )
                existing_lower.add(item_name.lower())
                print(f"{Color.SUCCESS}📦 Added to inventory: {item_name}{Color.RESET}")
            except Exception:
                pass
    except Exception:
        return



def _prompt_action_input(question_color) -> str:
    """Unified, deterministic prompt for user actions.
    Ensures:
    - Output flushed
    - Windows keyboard buffer drained
    - Question printed and flushed
    - Visible '> ' printed and flushed
    - Minimal stabilization delay before input()
    """
    sys.stdout.flush()
    _drain_windows_keyboard_buffer()
    # Print question and prompt on the same line to avoid line-feed races
    try:
        print(f"\n{question_color}(What do you want to do?){Color.RESET}: ", end="", flush=True)
    except Exception:
        sys.stdout.write(f"\n(What do you want to do?): ")
        sys.stdout.flush()
    # Use robust Windows reader when available to ensure prompt visibility and echo
    if os.name == 'nt' and msvcrt and sys.stdin.isatty():
        user_input = _win_readline().strip()
    else:
        user_input = input().strip()
    return user_input



def _summarize_scene_text(text: str, max_sentences: int = 2, max_chars: int = 500) -> str:
    """Lightweight scene summarizer: take the first few sentences and trim to max chars.
    This avoids an LLM call and keeps the loop snappy."""
    if not text:
        return ""
    # Split on sentence boundaries
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    summary = " ".join(sentences[:max_sentences]).strip()
    if len(summary) > max_chars:
        summary = summary[: max_chars - 1].rstrip() + "…"
    return summary



def _compose_scene_snapshot(scene_description: str,
                            time_context: dict,
                            last_action_narrative: Optional[str],
                            scene_updates: Optional[list[str]],
                            max_update_count: int = 2) -> str:
    """Compose a concise scene snapshot that integrates the latest action result.
    - Summarizes the current scene
    - Adds the most recent action result (if any)
    - Optionally includes up to N recent short updates for continuity"""
    summary = _summarize_scene_text(scene_description, max_sentences=2, max_chars=500)
    parts = []
    if summary:
        parts.append(summary)

    # Integrate last action result
    if last_action_narrative:
        parts.append(f"Recent development: {last_action_narrative}")

    # Include up to N recent compact updates
    if scene_updates:
        recent = scene_updates[-max_update_count:]
        if recent:
            parts.append("Updates:")
            for upd in recent:
                parts.append(f"  • {upd}")

    return "\n\n".join(parts)



def _select_next_reactor(available_npcs, actor):
    """Select the next reactor when multiple NPCs are available"""
    if not available_npcs:
        return None

    def _display_npc_name(npc_obj) -> str:
        try:
            npc_name = getattr(getattr(npc_obj, 'sheet', None), 'name', None)
            if not npc_name:
                return str(npc_obj)
            try:
                from stranger_description_system import known_actors_tracker
                if known_actors_tracker is not None and known_actors_tracker.is_name_known(str(npc_name)):
                    return str(npc_name)
            except Exception:
                pass
            try:
                return str(get_stranger_description(npc_obj, ua_actor=actor))
            except Exception:
                return str(npc_name)
        except Exception:
            return "someone"
    
    if len(available_npcs) == 1:
        # If only one, ensure they are conscious
        only_npc = available_npcs[0]
        st = only_npc.sheet.statuses[StatusType.STAMINA].value
        sp = only_npc.sheet.statuses[StatusType.SPIRIT].value
        if st <= 0 or sp <= 0:
            print(f"{Color.WARNING}⚠️ {_display_npc_name(only_npc)} is unconscious and cannot be engaged right now{Color.RESET}")
            return None
        return only_npc
    
    # Multiple NUAs available - present choice to user
    print(f"\n{Color.INFO}👥 Multiple People Available for Interaction:{Color.RESET}")
    conscious_indices = []
    for i, nua in enumerate(available_npcs, 1):
        # Get basic info about the NUA
        occupation = getattr(nua.sheet, 'occupation', 'Unknown')
        affiliation = getattr(nua.sheet, 'affiliation', 'Unknown')
        st = nua.sheet.statuses[StatusType.STAMINA].value
        sp = nua.sheet.statuses[StatusType.SPIRIT].value
        tag = " (unconscious)" if (st <= 0 or sp <= 0) else ""
        if tag == "":
            conscious_indices.append(i)
        print(f"  {i}. {_display_npc_name(nua)}{tag} - {occupation} ({affiliation})")
    
    print(f"  {len(available_npcs) + 1}. Continue exploring without interacting")
    
    if not conscious_indices:
        print(f"{Color.INFO}All available people are currently unconscious. You can continue exploring until someone recovers.{Color.RESET}")
        return None
    
    while True:
        try:
            choice = input(f"\n{Color.INPUT}Choose who to interact with (1-{len(available_npcs) + 1}): {Color.RESET}").strip()
            choice_num = int(choice)
            
            if 1 <= choice_num <= len(available_npcs):
                if choice_num not in conscious_indices:
                    print(f"{Color.WARNING}That person is unconscious and cannot be engaged. Please choose someone conscious or continue exploring.{Color.RESET}")
                    continue
                else:
                    selected_npc = available_npcs[choice_num - 1]
                    print(f"\n{Color.SUCCESS}🎯 Selected: {_display_npc_name(selected_npc)}{Color.RESET}")
                    return selected_npc
            elif choice_num == len(available_npcs) + 1:
                print(f"\n{Color.INFO}🚶 Continuing exploration without interaction{Color.RESET}")
                return None
            else:
                print(f"{Color.WARNING}Invalid choice. Please select 1-{len(available_npcs) + 1}.{Color.RESET}")
        except ValueError:
            print(f"{Color.WARNING}Please enter a valid number.{Color.RESET}")



def _handle_encounter_transition(available_npcs, actor, encounter_context):
    """Handle transition from exploration to encounter mode with reactor selection"""
    if not available_npcs:
        return False
    
    # Select reactor from available NPCs
    selected_reactor = _select_next_reactor(available_npcs, actor)
    
    if selected_reactor:
        # Set up encounter with selected reactor using EncounterChecker context
        encounter_context.current_context.participants = [selected_reactor]
        encounter_context.current_context.mode = SimulationMode.ENCOUNTER
        
        print(f"\n{Color.SUCCESS}⚔️ ENCOUNTER INITIATED{Color.RESET}")
        try:
            reactor_disp = None
            try:
                from stranger_description_system import known_actors_tracker
                reactor_name = getattr(getattr(selected_reactor, 'sheet', None), 'name', None)
                if reactor_name and known_actors_tracker is not None and known_actors_tracker.is_name_known(str(reactor_name)):
                    reactor_disp = str(reactor_name)
            except Exception:
                reactor_disp = None
            if not reactor_disp:
                reactor_disp = str(get_stranger_description(selected_reactor, ua_actor=actor))
        except Exception:
            reactor_disp = getattr(getattr(selected_reactor, 'sheet', None), 'name', 'Someone')
        print(f"{Color.INFO}Reactor: {reactor_disp}{Color.RESET}")
        # Show concise NUA summary on encounter start
        try:
            _display_actor_sheet_simple(selected_reactor, {'ua_actor': actor, 'show_outliers': True})
        except Exception:
            pass
        return True
    
    return False



def _end_encounter(encounter_checker, available_npcs):
    """Reset encounter state and return to ROAM mode, preserving NUAs for exploration."""
    try:
        ctx = encounter_checker.current_context
        # Preserve NUA participants in available_npcs for continued interaction
        participants = getattr(ctx, 'participants', []) or []
        for p in participants:
            try:
                if hasattr(p, 'is_user_actor') and not p.is_user_actor:
                    if p not in available_npcs:
                        available_npcs.append(p)
            except Exception:
                # Ignore non-actor placeholders (e.g., creation dicts)
                pass
        # Tear down encounter-specific systems
        for attr in ['actor_manager', 'sympathy_manager', 'enhanced_recovery', 'round_manager', 'reporter', 'systems_initialized']:
            if hasattr(ctx, attr):
                try:
                    delattr(ctx, attr)
                except Exception:
                    try:
                        setattr(ctx, attr, None)
                    except Exception:
                        pass
        # Clear participants and switch mode
        ctx.participants = []
        ctx.mode = SimulationMode.ROAM
        
        # CRITICAL: Clear remote encounter flags if this was a phone call
        # This prevents phone conversation constraints from leaking into future encounters
        if hasattr(ctx, 'is_remote_encounter'):
            try:
                delattr(ctx, 'is_remote_encounter')
            except Exception:
                try:
                    setattr(ctx, 'is_remote_encounter', False)
                except Exception:
                    pass
        if hasattr(ctx, 'remote_encounter_type'):
            try:
                delattr(ctx, 'remote_encounter_type')
            except Exception:
                pass
        if hasattr(ctx, 'remote_encounter_description'):
            try:
                delattr(ctx, 'remote_encounter_description')
            except Exception:
                pass
        
        print(f"{Color.SYSTEM}Returning to ROAM mode...{Color.RESET}")
    except Exception as e:
        print(f"{Color.WARNING}Encounter cleanup issue: {e}{Color.RESET}")
        try:
            encounter_checker.current_context.mode = SimulationMode.ROAM
        except Exception:
            pass



def _infer_vehicle(scene_text: str) -> str:
    """Heuristically infer vehicle type from scene text."""
    txt = (scene_text or "").lower()
    if any(k in txt for k in ["subway", "metro", "underground", "tube"]):
        return "train"
    if any(k in txt for k in ["train", "tram"]):
        return "train"
    if any(k in txt for k in ["bus", "coach"]):
        return "bus"
    if any(k in txt for k in ["cab", "taxi"]):
        return "cab"
    if any(k in txt for k in ["plane", "airport", "airplane", "flight", "airline"]):
        return "plane"
    return "unknown"



def _print_forced_exit(vehicle: str):
    """Narrate a forced exit for vehicles where staying is unrealistic (plane, cab)."""
    if vehicle == "plane":
        print(f"{Color.NARRATIVE}A flight attendant leans in with practiced patience: \"This is your stop.\" The aisle presses forward, and airport staff angle you to the door. You step out into the jet bridge as the cabin thins behind you.{Color.RESET}")
    elif vehicle == "cab":
        print(f"{Color.NARRATIVE}The driver taps the meter and unlocks the door, chin jutting to the curb. A horn sounds behind you. \"End of the line, pal.\" You climb out as the cab rolls off.{Color.RESET}")
    else:
        print(f"{Color.NARRATIVE}You’re ushered out as the vehicle readies to depart, the world outside reclaiming your attention.{Color.RESET}")



def _detect_exit_intent(user_text: str) -> str:
    """Very light heuristic to detect whether the user exits ('exit') or stays ('stay')."""
    t = (user_text or "").lower().strip()
    exit_keywords = [
        'get off', 'step off', 'step out', 'exit', 'leave', 'disembark', 'alight', 'hop off', 'get out',
        'onto the platform', 'onto platform', 'onto curb', 'out of the cab', 'out the cab', 'out of bus',
        'walk onto', 'rush out', 'dash out'
    ]
    stay_keywords = [
        'stay', 'remain', 'keep riding', 'keep talking', 'stay seated', 'don\'t get off', 'continue on', 'ride on'
    ]
    if any(k in t for k in exit_keywords):
        return 'exit'
    if any(k in t for k in stay_keywords):
        return 'stay'



def _detect_disengage_intent(user_text: str) -> bool:
    """Detect if the UA is signaling a desire to end the interaction/encounter.
    Examples: "that's all", "i'm done ordering", "that'll be it", "thanks, we're done",
    "i walk away", "i leave", "head out", "we're done here".
    """
    t = (user_text or '').lower().strip()
    disengage_phrases = [
        "that's all", "that is all", "that'll be all", "that will be all", "that'll be it", "that will be it",
        "i'm done", "im done", "i am done", "i'm finished", "im finished", "we're done here", "were done here",
        "i'm done ordering", "im done ordering", "i finished ordering", "i'm finished ordering",
        "no, that's all", "no thats all", "that should be it", "that should do it",
        "i leave", "i walk away", "walk away", "head out", "head off", "i bail", "i step away",
        "thanks, that's all", "thanks thats all", "thanks that'll be all", "thank you, that's all",
        "i have to go", "i gotta go", "i need to go", "i should go", "i must go", "have to go now", "gotta go now", "need to go now",
        "goodbye", "good bye", "bye", "bye bye", "see you", "see ya", "talk to you later", "talk later", "catch you later", "later"
    ]
    # Require phrase boundaries to reduce false positives
    return any(phrase in t for phrase in disengage_phrases)



def _nua_allows_disengage(reactor_actor, encounter_type: str, escalation_level: int = 1) -> bool:
    """Simple policy: in social/trade encounters, service roles allow exit.
    Service roles include waitstaff, cashier, clerk, bartender, barista, receptionist, server, host/hostess.
    In combat encounters, deny by default.
    Escalation levels: 1=PEACEFUL, 2=TENSE, 3=HOSTILE, 4=VIOLENT, 5=LETHAL
    """
    # Block disengage at HOSTILE (3) or higher escalation
    if escalation_level >= 3:
        return False
    
    try:
        enc = (encounter_type or '').lower()
    except Exception:
        enc = ''
    if enc in ('combat', 'stealth'):
        return False
    # Default allow in social/trade/general unless explicit hostile role
    occ = ''
    try:
        occ = (getattr(getattr(reactor_actor, 'sheet', None), 'occupation', '') or '').lower()
    except Exception:
        occ = ''
    service_keywords = [
        'waitress', 'waiter', 'server', 'cashier', 'clerk', 'bartender', 'barista', 'receptionist', 'hostess', 'host', 'attendant'
    ]
    hostile_keywords = ['enforcer', 'thug', 'guard', 'gang', 'assassin', 'soldier']
    if any(k in occ for k in hostile_keywords):
        return False
    if any(k in occ for k in service_keywords):
        return True
    # For unknown occupations in social/trade/general, lean permissive
    return enc in ('social', 'trade', 'general')

from typing import Optional, Dict, Any

# ============================================================
# TRAVEL TIME & CHUNKING SYSTEM
# ============================================================



def _should_allow_food_fulfillment(user_text: str) -> bool:
    """Return True only if the text clearly expresses ordering or consuming food/drink.
    Prevents passive phrases like 'sit and wait' from triggering Food fulfillment.
    """
    t = (user_text or '').lower()
    # Food/drink vocabulary
    items = [
        'coffee','tea','milkshake','shake','burger','cheeseburger','sandwich','fries','salad','soup',
        'soda','cola','coke','water','beer','wine','steak','omelet','omelette',
        'pancakes','waffle','toast','eggs','bacon','hash browns','hashbrowns'
    ]
    # Request/ordering phrases require item nouns to avoid false positives like 'have a seat'
    request_phrases = [
        'order', 'place an order',
        "i'll have", 'i will have', "i'd like", 'i would like',
        'can i get', 'may i have', 'could i get', 'let me get',
        'get a', 'grab a', 'have a', 'buy', 'purchase'
    ]
    # Consumption verbs require an item noun or a clear direct-object referent
    consume_verbs = ['eat', 'drink']
    if any(cv in t for cv in consume_verbs) and any(it in t for it in items):
        return True
    if any(p in t for p in request_phrases) and any(it in t for it in items):
        return True
    # Minimal polite cue with clear item
    if 'please' in t and any(it in t for it in items):
        return True
    # Otherwise, do not treat as food ordering/consumption
    return False



def _build_turn_data(
    user_input: str,
    scene_description: str,
    current_mode,
    success_total: int | None = None,
    continuity: dict | None = None,
    inquiry: bool = False,
    outcome_data: dict | None = None,
    survival_needs: list | None = None
) -> dict:
    """Construct a robust turn_data dict for FourModeNarrativeLoop.process_turn().

    Fields are aligned with llm_agents/narrative_loop_system.py signal detectors:
    - user_input: raw user text
    - scene_description: current scene context
    - continuity_check: {'judgment': 'Possible'|'Not Possible'}
    - success_calculation: include 'total_successes' compatible value
    - inquiry_type: flag for inquiry turns
    - mode: current simulation mode as string
    - outcome_data: optional exchange outcome snapshot
    - survival_summary: optional list of needs just fulfilled
    """
    td = {
        'user_input': user_input or '',
        'scene_description': scene_description or '',
        'mode': current_mode.value if hasattr(current_mode, 'value') else str(current_mode),
    }
    if continuity is not None:
        td['continuity_check'] = continuity
    if success_total is not None:
        td['success_calculation'] = {
            # Provide a field used by signal detector for friction/closure checks
            'total_successes': max(0, int(success_total))
        }
    if inquiry:
        td['inquiry_type'] = True
    if outcome_data is not None:
        td['outcome_snapshot'] = {
            'pro_success': outcome_data.get('proactor_success', 0),
            're_success': outcome_data.get('reactor_success', 0)
        }
    if survival_needs:
        td['survival_summary'] = list(survival_needs)
    return td



def _prune_npcs_by_outcome_text(available_npcs, recent_texts):
    """Remove NUAs that have clearly departed the scene based on recent narrative text.
    Heuristics: if a NUA's name appears near leave/depart/board/disappear verbs, we prune them.
    Returns a list of names that were removed.
    """
    if not recent_texts or not available_npcs:
        return []
    text_blob = " \n".join([t.lower() for t in recent_texts if isinstance(t, str)])
    if not text_blob:
        return []
    leaving_keywords = [
        "leaves", "walks away", "heads off", "drives off", "rides off", "runs off",
        "boards", "gets on", "gets into", "hops on", "steps onto",
        "exits", "leaves the", "storms out", "goes away", "disappears", "vanishes"
    ]
    to_remove = []
    for nua in list(available_npcs):
        try:
            name = getattr(nua.sheet, 'name', str(getattr(nua, 'name', '')))
            if not name:
                continue
            name_l = name.lower()
            if name_l in text_blob and any(k in text_blob for k in leaving_keywords):
                to_remove.append(nua)
        except Exception:
            continue
    removed_names = []
    for nua in to_remove:
        try:
            removed_names.append(getattr(nua.sheet, 'name', 'Unknown'))
            available_npcs.remove(nua)
        except Exception:
            pass
    return removed_names




def _check_unconscious_actor_recovery(actor, time_tracker, available_npcs, scene_description="", narrator=None):
    """KO-aware recovery for unconscious actors during ROAM.
    Guarantees at least 1 missed turn when dropping to 0, then 20% chance per loop to recover from 0.
    """
    import random
    
    # Check all actors (UA and NPCs) for unconscious status
    all_actors = [actor] + available_npcs
    
    for current_actor in all_actors:
        stamina = current_actor.sheet.statuses.get(StatusType.STAMINA)
        spirit = current_actor.sheet.statuses.get(StatusType.SPIRIT)
        if not stamina or not spirit:
            continue
        
        is_unconscious = (stamina.value <= 0 or spirit.value <= 0) and not current_actor.sheet.is_dead()
        if not is_unconscious:
            continue
        
        print(f"\n{Color.WARNING}😴 {_ua_display_name(current_actor, ua_actor=actor)} is unconscious{Color.RESET}")
        
        # Respect knockout duration (set when first hitting 0 in actor_sheet.update_status)
        ko_remaining = current_actor.sheet.get_knockout_turns_remaining()
        if ko_remaining > 0:
            current_actor.sheet.decrement_knockout_turns()
            print(f"{Color.SYSTEM}⏳ Knockout turns remaining: {current_actor.sheet.get_knockout_turns_remaining()}{Color.RESET}")
            continue
        
        # After guaranteed miss, 20% chance per loop to recover from 0 → 1
        if random.random() < 0.20:
            # Track which statuses were depleted for recovery narrative
            depleted_statuses = []
            if stamina.value <= 0:
                current_actor.sheet.update_status(StatusType.STAMINA, 1, "KO recovery chance (ROAM)")
                depleted_statuses.append("STAMINA")
            if spirit.value <= 0:
                current_actor.sheet.update_status(StatusType.SPIRIT, 1, "KO recovery chance (ROAM)")
                depleted_statuses.append("SPIRIT")
            
            # Generate recovery scene narrative for User Actor only
            if current_actor.sheet.is_user_actor and depleted_statuses and narrator and scene_description:
                print(f"\n{Color.SUCCESS}✨ {_ua_display_name(current_actor, ua_actor=actor)} regains consciousness!{Color.RESET}")
                
                # Generate perceptual description (what you physically experience)
                recovery_scene = narrator.generate_recovery_scene(
                    actor=current_actor,
                    original_scene=scene_description,
                    depleted_statuses=depleted_statuses,
                    time_context=master_time.get_current_time_context() if master_time else None
                )
                print(f"\n{Color.NARRATIVE}{recovery_scene}{Color.RESET}\n")
                
                # Generate internal voice (mental reaction to recovery)
                internal_voice = generate_unified_internal_voice(
                    actor=current_actor,
                    narrator=narrator,
                    scene_description=recovery_scene,
                    user_action="regaining consciousness",
                    action_outcome="Recovered from unconsciousness",
                    function_hint="comment",
                    urgency="calm"
                )
                
                display_internal_voice_box(internal_voice)
            elif current_actor.sheet.is_user_actor and depleted_statuses:
                # Fallback if narrator not available
                print(f"\n{Color.SUCCESS}✨ {_ua_display_name(current_actor, ua_actor=actor)} regains consciousness!{Color.RESET}")
        else:
            print(f"{Color.SYSTEM}… No recovery this turn (20% chance){Color.RESET}")



def _build_comprehensive_outcome_data(proactor, reactor, proactor_action_data, reactor_action_data, exchange_results, proactor_success_data=None, reactor_success_data=None):
    """Build comprehensive outcome data for Step 5 reporting."""
    from narrative_utils import get_narrative_descriptor, get_status_descriptor
    
    if isinstance(exchange_results, tuple) and len(exchange_results) == 3:
        proactor_results, reactor_results, outcome_results = exchange_results
        proactor_successes = proactor_success_data.get('total', 0) if proactor_success_data else proactor_action_data.get('success_calculation', {}).get('total', 0)
        reactor_successes = reactor_success_data.get('total', 0) if reactor_success_data else reactor_action_data.get('success_calculation', {}).get('total', 0)
    elif isinstance(exchange_results, dict):
        proactor_successes = exchange_results.get('proactor_success', 0)
        reactor_successes = exchange_results.get('reactor_success', 0)
        outcome_results = exchange_results
        proactor_results = exchange_results.get('proactor_results', {})
        reactor_results = exchange_results.get('reactor_results', {})
    else:
        proactor_successes = proactor_success_data.get('total', 0) if proactor_success_data else proactor_action_data.get('success_calculation', {}).get('total', 0)
        reactor_successes = reactor_success_data.get('total', 0) if reactor_success_data else reactor_action_data.get('success_calculation', {}).get('total', 0)
        proactor_results = {}
        reactor_results = {}
        outcome_results = {}
    
    margin = proactor_successes - reactor_successes
    
    outcome_data = {
        'proactor_successes': proactor_successes,
        'reactor_successes': reactor_successes,
        'margin': margin,
        'proactor_name': proactor.sheet.name,
        'reactor_name': reactor.sheet.name,
        'status_shifts': [],
        'applied_self_effects': []
    }
    
    stress_level = proactor_action_data.get('utas_factors', {}).get('stress_level', 3)
    if stress_level != 3:
        stress_desc = get_narrative_descriptor(stress_level)
        outcome_data['stress_context'] = f"The {proactor.sheet.name}'s action was Stress Level {stress_level} ({stress_desc}), making it {'easier' if stress_level < 3 else 'harder'} for you to react against."
    
    final_shift_amount = outcome_results.get('final_shift_amount', 0)
    if final_shift_amount != 0:
        target_status = outcome_results.get('status_shifted')
        winner = outcome_results.get('winner', 'draw')
        
        if winner == 'proactor':
            affected_actor = reactor
            affected_name = reactor.sheet.name
            original_status = outcome_results.get('original_reactor_status', 0)
            new_status = outcome_results.get('updated_reactor_status', 0)
        elif winner == 'reactor':
            affected_actor = proactor
            affected_name = proactor.sheet.name
            original_status = outcome_results.get('original_proactor_status', 0)
            new_status = outcome_results.get('updated_proactor_status', 0)
        else:
            affected_actor = None
            affected_name = None
            original_status = 0
            new_status = 0
        
        if affected_actor and original_status != new_status:
            shift_type = outcome_results.get('shift_type')
            shift_polarity = outcome_results.get('shift_polarity')
            
            outcome_data['status_shifts'].append({
                'actor_name': affected_name,
                'status_type': target_status,
                'description': f"The {winner}'s victory results in a {shift_type}, {shift_polarity} shift to {affected_name}'s {target_status}.",
                'shift_value': final_shift_amount,
                'original_value': original_status,
                'new_value': new_status,
                'original_descriptor': get_status_descriptor(original_status),
                'new_descriptor': get_status_descriptor(new_status)
            })
    
    applied_effects = outcome_results.get('applied_effects', [])
    if applied_effects:
        for effect in applied_effects:
            original_status = effect.get('original_status', 0)
            new_status = effect.get('updated_status', 0)
            shift_amount = new_status - original_status
            
            outcome_data['applied_self_effects'].append({
                'actor_name': proactor.sheet.name,
                'trigger': effect.get('prefix', 'Due to the action'),
                'status_name': effect.get('status_shifted'),
                'description': effect.get('description', 'Status effect applied'),
                'shift_type': effect.get('shift_type'),
                'shift_polarity': effect.get('shift_polarity'),
                'shift_value': effect.get('shift_magnitude', abs(shift_amount)),
                'original_value': original_status,
                'new_value': new_status,
                'original_descriptor': effect.get('original_status_desc', 'Unknown'),
                'new_descriptor': effect.get('updated_status_desc', 'Unknown')
            })
    
    return outcome_data



