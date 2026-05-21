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

def get_storyteller_sparks(
    location: str,
    location_description: str,
    available_nuas: List[Dict],
    recent_narrative: List[str],
    actor_goal: str = "",
    actor_task: str = "",
    rag_context: str = "",
    max_retries: int = 2
) -> List['Spark']:
    """
    Get storyteller sparks for the current location with retry handling.
    
    Returns list of Spark objects.
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE or _storyteller is None:
        return []
    
    for attempt in range(max_retries):
        try:
            sparks = _storyteller.on_location_change(
                new_location=location,
                location_description=location_description,
                actor_goal=actor_goal,
                actor_task=actor_task,
                available_nuas=available_nuas,
                recent_narrative=recent_narrative,
                rag_context=rag_context
            )
            
            return sparks or []
            
        except Exception as e:
            if attempt < max_retries - 1:
                print(f"{Color.WARNING}⚠️ Storyteller spark generation attempt {attempt + 1} failed: {e}{Color.RESET}")
                time.sleep(0.5)
            else:
                print(f"{Color.WARNING}⚠️ Storyteller sparks failed after {max_retries} attempts{Color.RESET}")
    
    return []




def _sanitize_spark_text_for_setting(t: str) -> str:
    """Best-effort guardrail: remove/replace obvious anachronisms in spark text."""
    try:
        s = str(t or '')
    except Exception:
        return ''
    if not s:
        return ''

    sl = s.lower()
    # Quick rejection of modern tech / terminology that breaks the setting.
    # Keep this short and pattern-based.
    try:
        import re
    except Exception:
        re = None

    replacements = {
        'television': 'notice board',
        'tv': 'notice board',
        'screen': 'placard',
        'broadcast': 'announcement',
        'emergency alert': 'urgent notice',
        'alert': 'notice',
        'scorched-earth strike': 'raid',
        'strike': 'attack',
        'scheduled for noon': 'set for midday',
    }

    # If the text contains strongly modern tokens, rewrite them.
    if any(k in sl for k in ['television', ' tv ', 'broadcast', 'emergency alert', 'screen flicker', 'scorched-earth strike']):
        out = s
        for k, v in replacements.items():
            try:
                if re is not None:
                    out = re.sub(rf"\b{re.escape(k)}\b", v, out, flags=re.IGNORECASE)
                else:
                    out = out.replace(k, v).replace(k.title(), v)
            except Exception:
                continue
        return out

    return s




def generate_location_arrival_sparks(
    location: str,
    scene_description: str,
    available_npcs: List,
    narrative_context_manager,
    actor,
    conductor=None,
    display_sparks: bool = True
) -> List:
    """
    Generate storyteller sparks when arriving at a new location during gameplay.
    
    Called ONLY when the character actively moves:
    - Instant moves (≤3 min travel)
    - Chunked journey completion
    
    NOT called on session restore or initial spawn (no actual movement occurred).
    
    Args:
        location: Name of the new location
        scene_description: Description of the scene
        available_npcs: List of NPC actors present
        narrative_context_manager: For getting recent narrative
        actor: The user actor
        conductor: Optional conductor for RAG access
        display_sparks: Whether to print spark descriptions (default True)
        
    Returns:
        List of Spark objects generated
    """
    if not NEW_VOICE_SYSTEM_AVAILABLE:
        print(f"{Color.WARNING}[SPARKS] NEW_VOICE_SYSTEM_AVAILABLE is False{Color.RESET}")
        return []
    if _storyteller is None:
        print(f"{Color.WARNING}[SPARKS] _storyteller is None{Color.RESET}")
        return []
    
    try:
        scene_description = str(scene_description or "")
    except Exception:
        scene_description = ""

    print(f"{Color.INFO}[SPARKS] Generating sparks for arrival at {location}...{Color.RESET}")
    
    try:
        # Build NUA dicts (use masked display labels to avoid leaking true names before discovery)
        try:
            from multi_actor_manager import _safe_display_name
        except Exception:
            _safe_display_name = None

        nua_dicts = []
        for npc in (available_npcs or []):
            if not hasattr(npc, 'sheet'):
                continue
            try:
                if _safe_display_name is not None:
                    disp_name = _safe_display_name(npc)
                else:
                    disp_name = str(getattr(npc.sheet, 'name', '') or '').strip() or str(npc)
            except Exception:
                disp_name = str(getattr(npc.sheet, 'name', '') or '').strip() or str(npc)

            nua_dicts.append({
                "name": disp_name,
                "occupation": getattr(npc.sheet, 'occupation', ''),
                "description": getattr(npc.sheet, 'description', '')
            })
        
        # Get recent narrative
        recent_events = []
        if narrative_context_manager:
            try:
                # Try get_recent_narratives first (persistent_context_manager)
                if hasattr(narrative_context_manager, 'get_recent_narratives'):
                    recent_events = narrative_context_manager.get_recent_narratives(count=5)
                # Fall back to get_recent_events
                elif hasattr(narrative_context_manager, 'get_recent_events'):
                    recent_events = narrative_context_manager.get_recent_events(count=5)
            except Exception:
                pass

        # Hard guarantee: never pass None into storyteller (it may subscript the list)
        try:
            if recent_events is None:
                recent_events = []
            elif not isinstance(recent_events, list):
                recent_events = list(recent_events) if recent_events else []
        except Exception:
            recent_events = []
        
        # Get RAG context if available - MUST include TEMPORAL for era-appropriate sparks
        spark_rag_context = ""
        if conductor and hasattr(conductor, 'decider_agent') and hasattr(conductor.decider_agent, 'rag_system') and conductor.decider_agent.rag_system:
            try:
                rag_system = conductor.decider_agent.rag_system
                context_parts = []
                
                # CRITICAL: Get TEMPORAL context first for era-appropriate sparks
                from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
                temporal_ctx = rag_system.get_context_for_llm(
                    query="time period era setting year world",
                    max_tokens=200,
                    category_filter=WorldbuildingCategory.TEMPORAL
                )
                if temporal_ctx:
                    context_parts.append(f"**TIME PERIOD & ERA (CRITICAL):**\n{temporal_ctx}")
                
                # Get location-specific context
                location_ctx = rag_system.get_context_for_llm(
                    query=f"location {location} setting atmosphere",
                    max_tokens=200
                )
                if location_ctx:
                    context_parts.append(location_ctx)
                
                spark_rag_context = "\n\n".join(context_parts)
            except Exception as e:
                print(f"{Color.WARNING}[SPARKS] RAG context error: {e}{Color.RESET}")
        
        # Generate sparks
        sparks = get_storyteller_sparks(
            location=location,
            location_description=(scene_description or "")[:500],
            available_nuas=nua_dicts,
            recent_narrative=recent_events,
            actor_goal=actor.sheet.goals[0] if hasattr(actor.sheet, 'goals') and actor.sheet.goals else "",
            actor_task=actor.sheet.get_current_task_description() if hasattr(actor.sheet, 'get_current_task_description') else "",
            rag_context=spark_rag_context
        )
        
        # Display sparks (max 3) if requested
        if display_sparks:
            for spark in sparks[:3]:
                if hasattr(spark, 'trigger_description') and spark.trigger_description:
                    trigger_text = _sanitize_spark_text_for_setting(str(spark.trigger_description))
                    try:
                        from stranger_description_system import known_actors_tracker, get_nua_definite_description
                        for npc in (available_npcs or []):
                            try:
                                npc_name = getattr(getattr(npc, 'sheet', None), 'name', None)
                                if not npc_name:
                                    continue
                                if known_actors_tracker.is_name_known(npc_name):
                                    continue
                                replacement = get_nua_definite_description(npc, ua_actor=actor)
                                if replacement and replacement != npc_name:
                                    trigger_text = trigger_text.replace(npc_name, replacement)
                            except Exception:
                                continue
                    except Exception:
                        pass
                    print(f"\n{Color.STATUS}✨ {trigger_text}{Color.RESET}")
        
        print(f"{Color.INFO}[SPARKS] Generated {len(sparks)} spark(s){Color.RESET}")
        return sparks
        
    except Exception as e:
        print(f"{Color.WARNING}[SPARKS] Error generating sparks: {e}{Color.RESET}")
        return []




def get_spark_scene_integration(sparks: List) -> str:
    """
    Integrate spark trigger descriptions directly into the scene description.
    
    Args:
        sparks: List of Spark objects
        
    Returns:
        Full spark descriptions as additional scene paragraphs
    """
    if not sparks:
        return ""
    
    # Include full spark trigger descriptions as part of the scene
    spark_texts = []
    for spark in sparks[:3]:  # Max 3 sparks
        if hasattr(spark, 'trigger_description') and spark.trigger_description:
            spark_texts.append(_sanitize_spark_text_for_setting(str(spark.trigger_description)))
    
    if not spark_texts:
        return ""

    # Best-effort: avoid leaking unknown NPC real names in spark text
    try:
        from stranger_description_system import known_actors_tracker, get_nua_definite_description
        # Attempt to use globally available NPC list if present in scope via runtime_state/context
        # If we can't resolve NPC objects, we leave spark text unchanged.
        available_npcs = None
        try:
            if 'runtime_state' in globals() and getattr(runtime_state, 'available_npcs', None) is not None:
                available_npcs = list(getattr(runtime_state, 'available_npcs') or [])
        except Exception:
            available_npcs = None

        if available_npcs:
            ua_actor = None
            try:
                if 'runtime_state' in globals() and getattr(runtime_state, 'current_actor', None) is not None:
                    ua_actor = getattr(runtime_state, 'current_actor')
            except Exception:
                ua_actor = None

            sanitized = []
            for t in spark_texts:
                tt = str(t)
                for npc in (available_npcs or []):
                    try:
                        npc_name = getattr(getattr(npc, 'sheet', None), 'name', None)
                        if not npc_name:
                            continue
                        if known_actors_tracker.is_name_known(npc_name):
                            continue
                        replacement = get_nua_definite_description(npc, ua_actor=ua_actor)
                        if replacement and replacement != npc_name:
                            tt = tt.replace(npc_name, replacement)
                    except Exception:
                        continue
                sanitized.append(tt)
            spark_texts = sanitized
    except Exception:
        pass
    
    # Join sparks as additional scene paragraphs
    return "\n\n" + "\n\n".join(spark_texts)




def _fade_spark_back_to_roam(narrator, narrative_context_manager, scene_description: str, spark_bridge: str, time_context: dict) -> str:
    """Create a short, connected narrative line to gracefully recede a SPARK when ignored."""
    try:
        bridge = (spark_bridge or '').strip()
        fade_line = bridge + (" " if bridge else "") + "The moment recedes and the environment settles back into its usual rhythm."
        scene_elements = {
            'setting': scene_description or 'The current location',
            'transition_bridge': fade_line,
            'ua_goal': 'Continue objectives based on prior events',
            'conflict': 'Open exploration'
        }
        new_desc = narrator.generate_scene_with_narrative_loop(
            scene_elements=scene_elements,
            nua_name="",
            turn_data={'user_input': 'SPARK Ignored', 'scene_description': scene_description, 'continuity_check': {'judgment': 'Possible'}},
            time_context=time_context,
        )
        try:
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.SCENE_TRANSITION,
                narrative_text=f"SPARK ignored → {fade_line[:120]}",
                actors_involved=[],
                importance=NarrativeImportance.ROUTINE,
                emotional_tone="neutral",
                scene_context="SPARK fade"
            )
        except Exception:
            pass
        return new_desc
    except Exception:
        return scene_description



def _integrate_spark_into_scene(narrator, narrative_context_manager, scene_description: str, spark_data: dict, time_context: dict) -> str:
    try:
        bridge = (spark_data.get('spark_narrative') or '').strip()
        scene_update = spark_data.get('scene_update') or ''
        scene_elements = {
            'setting': scene_description or 'The current location',
            'transition_bridge': bridge or 'A new opportunity emerges in the periphery.',
            'ua_goal': 'Continue objectives based on prior events',
            'conflict': ''  # No explicit conflict label - let narrative flow naturally
        }
        # Generate a connected update; append the explicit scene update provided by the SPARK
        new_base = narrator.generate_scene_with_narrative_loop(
            scene_elements=scene_elements,
            nua_name="",
            turn_data={'user_input': 'SPARK Introduction', 'scene_description': scene_description, 'continuity_check': {'judgment': 'Possible'}},
            time_context=time_context,
        )
        connected = (new_base.strip() + ("\n\n" + scene_update.strip() if isinstance(scene_update, str) and scene_update.strip() else '')).strip()
        try:
            narrative_context_manager.add_narrative_event(
                event_type=NarrativeEventType.SCENE_TRANSITION,
                narrative_text=f"SPARK introduced → {bridge[:120]}" if bridge else "SPARK introduced",
                actors_involved=[],
                importance=NarrativeImportance.NOTABLE,
                emotional_tone="transitional",
                scene_context="SPARK integration"
            )
        except Exception:
            pass
        return connected
    except Exception:
        # Fallback: simple append to ensure continuity minimally
        try:
            upd = spark_data.get('scene_update') or ''
            if isinstance(upd, str) and upd.strip():
                return f"{scene_description}\n\n{upd}"
        except Exception:
            pass
        return scene_description

# Lightweight clamp for long context strings passed to LLMs
CTX_SUMMARY_MAX_CHARS = int(os.getenv("REDESIGNED_CTX_SUMMARY_MAX_CHARS", "1200"))


