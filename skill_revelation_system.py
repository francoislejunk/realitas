"""
Skill Revelation System - Progressive Discovery of NUA Abilities

This system handles the gradual revelation of NUA skills and endowments as they're used,
providing immersive narrative feedback when abilities are discovered.
"""

from color_utils import Color
from typing import TYPE_CHECKING

try:
    from context_store import ContextStore, WorldTime
except Exception:
    ContextStore = None
    WorldTime = None

try:
    from master_time_coordinator import get_master_time_coordinator
except Exception:
    get_master_time_coordinator = None

try:
    from spatial_context_system import get_spatial_manager
except Exception:
    get_spatial_manager = None

from pathlib import Path

if TYPE_CHECKING:
    from actors import Actor


_last_logged_revelation_key: str | None = None


def _sr_get_world_time_safe() -> 'WorldTime | None':
    try:
        if get_master_time_coordinator is None or WorldTime is None:
            return None
        tc = get_master_time_coordinator()
        time_ctx = tc.get_current_time_context() if tc else None
        gt = time_ctx.get('game_time') if isinstance(time_ctx, dict) else None
        if gt is None:
            return None
        return WorldTime(day=getattr(gt, 'day', 1), hour=getattr(gt, 'hour', 0), minute=getattr(gt, 'minute', 0))
    except Exception:
        return None


def _sr_try_get_session_location_and_user() -> tuple[str, str | None, str | None, str | None]:
    """Returns (session_id, location_id, user_actor_id, user_actor_name) best-effort."""
    session_id = 'default'
    location_id = None
    user_actor_id = None
    user_actor_name = None
    try:
        if get_spatial_manager is None:
            return session_id, location_id, user_actor_id, user_actor_name
        spatial = get_spatial_manager()
        session_id = getattr(spatial, 'session_id', None) or session_id
        location_id = getattr(spatial, 'current_location', None)
        ctx = spatial.get_current_context() if spatial else None
        if ctx and getattr(ctx, 'actor_positions', None):
            for aid, apos in ctx.actor_positions.items():
                if getattr(apos, 'is_user_actor', False):
                    user_actor_id = str(aid)
                    user_actor_name = getattr(apos, 'actor_name', None)
                    break
    except Exception:
        pass
    return session_id, location_id, user_actor_id, user_actor_name


def _sr_try_resolve_actor_id_by_name(actor_name: str) -> str:
    try:
        if not actor_name or get_spatial_manager is None:
            return actor_name
        spatial = get_spatial_manager()
        ctx = spatial.get_current_context() if spatial else None
        if ctx and getattr(ctx, 'actor_positions', None):
            for aid, apos in ctx.actor_positions.items():
                if getattr(apos, 'actor_name', None) == actor_name:
                    return str(aid)
    except Exception:
        pass
    return actor_name


def _sr_log_revelation(*, target_actor_name: str, kind: str, ability_name: str, ability_level: int, context: str) -> None:
    global _last_logged_revelation_key
    try:
        if ContextStore is None:
            return

        session_id, location_id, ua_id, ua_name = _sr_try_get_session_location_and_user()
        target_id = _sr_try_resolve_actor_id_by_name(target_actor_name)

        # Prefer UA memory seeding ("you notice")
        observer_id = ua_id or 'ua_001'
        observer_name = ua_name or 'User'

        wt = _sr_get_world_time_safe()
        store = ContextStore(Path('simulation_data/context/context.db'))
        summary = f"INFO LEARNED: {observer_name} noticed {target_actor_name} revealed {kind} {ability_name} (level {ability_level})"

        key = f"{kind}||{target_actor_name}||{ability_name}||{ability_level}||{observer_id}"
        if key == _last_logged_revelation_key:
            return
        _last_logged_revelation_key = key

        event_id = store.log_world_event(
            session_id=session_id,
            location_id=location_id,
            event_type='INFO_LEARNED',
            summary=summary,
            importance=6,
            tags=['info', 'discovery', 'ability', kind],
            payload={
                'actor_ids': [observer_id, target_id],
                'actor_names': [observer_name, target_actor_name],
                'observer_id': observer_id,
                'observer_name': observer_name,
                'target_actor_id': target_id,
                'target_actor_name': target_actor_name,
                'revelation_kind': kind,
                'ability_name': ability_name,
                'ability_level': int(ability_level),
                'context': context,
            },
            world_time=wt
        )

        try:
            if hasattr(store, 'remember'):
                store.remember(
                    session_id=session_id,
                    actor_id=str(observer_id),
                    memory_type='info_learned',
                    content=summary,
                    importance=6,
                    pinned=False,
                    decay_rate=0.00018,
                    source_event_id=int(event_id) if event_id is not None else None,
                    world_time=wt
                )
        except Exception:
            pass
    except Exception:
        return

def reveal_skill_with_narrative(actor: 'Actor', skill_name: str, context: str = "") -> None:
    """
    Reveals a skill and displays a narrative discovery notification.
    
    Args:
        actor: The actor whose skill is being revealed
        skill_name: Name of the skill being revealed
        context: Optional context about how it was revealed (e.g., "during combat")
    """
    # Check if this is the first revelation
    was_revealed = actor.sheet.reveal_skill(skill_name)
    
    if was_revealed:
        # Get the skill level for the narrative
        skill_level = actor.sheet.skills.get(skill_name, 0)
        from narrative_utils import get_narrative_descriptor
        skill_desc = get_narrative_descriptor(skill_level)
        
        # Display discovery notification
        context_text = f" {context}" if context else ""
        print(f"\n{Color.NARRATIVE}💡 You notice {actor.sheet.name} is skilled at {skill_name} ({skill_desc}){context_text}!{Color.RESET}\n")

        # Best-effort: persist as INFO_LEARNED + seed observer long-term memory
        try:
            _sr_log_revelation(
                target_actor_name=actor.sheet.name,
                kind='skill',
                ability_name=skill_name,
                ability_level=int(skill_level),
                context=context
            )
        except Exception:
            pass


def reveal_endowment_with_narrative(actor: 'Actor', endowment_name: str, context: str = "") -> None:
    """
    Reveals an endowment ability and displays a narrative discovery notification.
    
    Args:
        actor: The actor whose endowment is being revealed
        endowment_name: Name of the endowment being revealed
        context: Optional context about how it was revealed
    """
    # Check if this is the first revelation
    was_revealed = actor.sheet.reveal_endowment(endowment_name)
    
    if was_revealed:
        # Get the endowment level for the narrative
        endowment_level = actor.sheet.endowments.get(endowment_name, 0)
        from narrative_utils import get_narrative_descriptor
        endowment_desc = get_narrative_descriptor(endowment_level)
        
        # Display discovery notification
        context_text = f" {context}" if context else""
        print(f"\n{Color.NARRATIVE}✨ You discover {actor.sheet.name} has {endowment_name} ({endowment_desc}){context_text}!{Color.RESET}\n")

        # Best-effort: persist as INFO_LEARNED + seed observer long-term memory
        try:
            _sr_log_revelation(
                target_actor_name=actor.sheet.name,
                kind='endowment',
                ability_name=endowment_name,
                ability_level=int(endowment_level),
                context=context
            )
        except Exception:
            pass


def reveal_used_abilities(actor: 'Actor', skill_used: str = None, endowment_used: str = None, context: str = "") -> None:
    """
    Convenience function to reveal abilities that were just used in an action.
    
    Args:
        actor: The actor who used the abilities
        skill_used: Name of skill that was used (if any)
        endowment_used: Name of endowment that was used (if any)
        context: Context of the action (e.g., "during their attack", "while defending")
    """
    if skill_used and skill_used in actor.sheet.skills:
        reveal_skill_with_narrative(actor, skill_used, context)
    
    if endowment_used and endowment_used in actor.sheet.endowments:
        reveal_endowment_with_narrative(actor, endowment_used, context)


def auto_reveal_from_action_data(actor: 'Actor', action_data: dict) -> None:
    """
    Automatically reveals skills/endowments based on action interpretation data.
    
    Args:
        actor: The actor who took the action
        action_data: The interpreted action data containing skill/endowment information
    """
    # Extract skill and endowment from action data
    skill = action_data.get('skill')
    endowment_ability = action_data.get('endowment')
    action_desc = action_data.get('action_description', '')
    
    # Determine context
    if 'attack' in action_desc.lower() or 'strike' in action_desc.lower():
        context = "during their attack"
    elif 'defend' in action_desc.lower() or 'block' in action_desc.lower():
        context = "while defending"
    elif 'move' in action_desc.lower() or 'dodge' in action_desc.lower():
        context = "while moving"
    else:
        context = "in action"
    
    # Reveal used abilities
    reveal_used_abilities(actor, skill, endowment_ability, context)


# Global flag to enable/disable progressive revelation
PROGRESSIVE_REVELATION_ENABLED = True

def set_progressive_revelation(enabled: bool) -> None:
    """Enable or disable the progressive revelation system globally."""
    global PROGRESSIVE_REVELATION_ENABLED
    PROGRESSIVE_REVELATION_ENABLED = enabled

def is_progressive_revelation_enabled() -> bool:
    """Check if progressive revelation is currently enabled."""
    return PROGRESSIVE_REVELATION_ENABLED
