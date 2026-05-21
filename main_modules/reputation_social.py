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

def get_reputation_context(observer_name: str, target_name: str) -> str:
    """
    Get reputation context for how one actor perceives another.
    
    Returns formatted reputation string.
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE or _reputation_system is None:
        return ""
    
    try:
        return _reputation_system.get_reputation_context_for_nua(observer_name, target_name)
    except Exception:
        return ""




def get_reputation_sympathy_modifier(observer_name: str, target_name: str) -> int:
    """
    Get sympathy modifier based on reputation.
    
    Returns integer modifier (-3 to +3).
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE or _reputation_system is None:
        return 0
    
    try:
        return _reputation_system.get_initial_sympathy_modifier(observer_name, target_name)
    except Exception:
        return 0


# ═══════════════════════════════════════════════════════════════════════════════
# ADDITIONAL IMMERSION SYSTEM HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════



def process_witness_reactions(event_type: str, perpetrator, victim, witnesses: List, severity: int, scene_description: str) -> List[Dict]:
    """
    Process NPC reactions to witnessed events (violence, murder, theft, etc.).
    
    Returns list of reaction dicts with behavior modifications.
    """
    if not WITNESS_SYSTEM_AVAILABLE or _witness_system is None:
        return []
    
    try:
        return _witness_system.process_witness_reactions(
            event_type=event_type,
            perpetrator=perpetrator,
            victim=victim,
            witnesses=witnesses,
            severity=severity,
            scene_description=scene_description
        )
    except Exception as e:
        print(f"{Color.WARNING}⚠️ Witness reaction processing failed: {e}{Color.RESET}")
        return []




def get_stranger_description(nua, ua_actor, relationship_value: int = 0) -> str:
    """
    Get a diegetic description for an unknown NPC (by appearance, not name).
    
    Returns description string like "a dark-haired waitress" instead of "Jane".
    """
    if not STRANGER_DESCRIPTION_AVAILABLE:
        # Fallback to name
        return nua.sheet.name if hasattr(nua, 'sheet') else str(nua)
    
    try:
        return get_nua_description(nua, ua_actor, relationship_value)
    except Exception:
        return nua.sheet.name if hasattr(nua, 'sheet') else str(nua)




def get_actor_mood_context(actor) -> str:
    """
    Get personality and mood context for an actor (for internal voice).
    
    Returns formatted personality/mood string.
    """
    if not PERSONALITY_MOOD_AVAILABLE or _mood_analyzer is None:
        return ""
    
    try:
        actor_name = actor.sheet.name if hasattr(actor, 'sheet') else str(actor)
        # Get current mood state if tracked
        return _mood_analyzer.get_mood_description(actor_name) if hasattr(_mood_analyzer, 'get_mood_description') else ""
    except Exception:
        return ""




def update_actor_mood(actor, context: str, event_type: str = None):
    """
    Update an actor's mood based on context/events.
    """
    if not PERSONALITY_MOOD_AVAILABLE or _mood_analyzer is None:
        return
    
    try:
        actor_name = actor.sheet.name if hasattr(actor, 'sheet') else str(actor)
        if hasattr(_mood_analyzer, 'analyze_mood_change'):
            _mood_analyzer.analyze_mood_change(actor_name, context, event_type)
    except Exception:
        pass




def get_sympathy_behavior_mod(npc, target, base_sympathy: int) -> Dict:
    """
    Get behavior modification based on sympathy level.
    
    Returns dict with behavior adjustments.
    """
    if not SYMPATHY_MODIFIER_AVAILABLE or _sympathy_modifier is None:
        return {}
    
    try:
        return _sympathy_modifier.get_behavior_modification(npc, target, base_sympathy)
    except Exception:
        return {}




def _get_lighting_mood(time_of_day):
    """Get lighting mood description based on time of day"""
    if hasattr(time_of_day, 'value'):
        time_str = time_of_day.value.lower()
    else:
        time_str = str(time_of_day).lower()
    
    lighting_moods = {
        'dawn': 'soft golden',
        'morning': 'bright and clear',
        'midday': 'brilliant and intense',
        'afternoon': 'warm and steady',
        'dusk': 'amber and fading',
        'evening': 'gentle twilight',
        'night': 'dim and mysterious',
        'midnight': 'deep shadows and moonlight'
    }
    
    for time_period, mood in lighting_moods.items():
        if time_period in time_str:
            return mood
    
    return 'natural'


