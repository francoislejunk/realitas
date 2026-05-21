"""
Internal Voice Exchange Integration

Integration functions for the Internal Voice Exchange System with the main simulation loop.
This replaces the old Internal Voice system with the new exchange-based morality compass.
"""

from typing import Optional, Dict, Any, Tuple
from internal_voice_exchange_system import (
    get_internal_voice_exchange_system,
    InternalVoiceExchange,
    SpiritImpactDirection,
    PersonalityConflict,
    UAInputType
)


class Color:
    """Console colors for output formatting"""
    SYSTEM = '\033[96m'       # Cyan
    INTERNAL_VOICE = '\033[95m'  # Magenta
    UA_RESPONSE = '\033[92m'  # Green
    SPIRIT = '\033[93m'       # Yellow
    RESET = '\033[0m'
    HEADER = '\033[94m'       # Blue
    WARNING = '\033[91m'      # Red
    PERCEPTUAL = '\033[37m'   # Dim white — physical action descriptions


def check_and_trigger_internal_voice_exchange(
    actor,
    action_description: str,
    scene_context: str,
    is_extreme_scenario: bool = False
) -> Optional[InternalVoiceExchange]:
    """
    Check if action should trigger an Internal Voice exchange.
    Called AFTER the action is committed - this triggers the realization.
    """
    iv_system = get_internal_voice_exchange_system()
    
    # Check if this should trigger based on completed action
    should_trigger = iv_system.should_trigger_internal_voice_exchange(
        actor=actor,
        action_description=action_description,
        scene_context=scene_context,
        is_extreme_scenario=is_extreme_scenario
    )
    
    if not should_trigger:
        return None
    
    # Get personality info for conflict detection
    internal_personality = ""
    external_personality = ""
    
    if hasattr(actor, 'sheet'):
        if hasattr(actor.sheet, 'personality_traits'):
            internal_personality = actor.sheet.personality_traits.get('internal', '')
            external_personality = actor.sheet.personality_traits.get('external', '')
        elif hasattr(actor.sheet, 'personality_profile') and hasattr(actor.sheet.personality_profile, 'internal'):
            internal_personality = getattr(actor.sheet.personality_profile, 'internal', '')
            external_personality = getattr(actor.sheet.personality_profile, 'external', '')
    
    # Detect the specific conflict from the completed action
    conflict = iv_system.detect_personality_conflict(
        actor=actor,
        action_description=action_description,
        internal_personality=internal_personality,
        external_personality=external_personality
    )
    
    if not conflict:
        return None
    
    # Generate the 6-step exchange
    exchange = iv_system.generate_6_step_internal_voice_exchange(
        actor=actor,
        completed_action=action_description,
        action_result=scene_context,
        conflict=conflict
    )
    
    return exchange


def run_6_step_internal_voice_conversation(
    exchange: InternalVoiceExchange,
    prompt_func=None
) -> InternalVoiceExchange:
    """
    Run the 6-step Internal Voice conversation.
    Steps 1,3,5 are Internal Voice (contextual responses)
    Steps 2,4,6 are UA (free-form input)
    
    The IV at steps 3 and 5 reacts to what the UA said in the previous turn.
    
    Returns the completed exchange with all turns filled in.
    """
    iv_system = get_internal_voice_exchange_system()

    if prompt_func is None:
        # Use narrative display input if running, otherwise fall back to terminal
        try:
            from pygame_narrative_display import make_input_func
            prompt_func = make_input_func()
        except ImportError:
            prompt_func = input

    # Step 1: IV Opening (pre-written)
    print(f"\n{Color.INTERNAL_VOICE}Inner Voice: {exchange.turns[0].content}{Color.RESET}")
    # Mirror Step 1 to display
    try:
        from pygame_narrative_display import send_display_separator, send_iv_exchange_iv
        send_display_separator()
        send_iv_exchange_iv(exchange.turns[0].content)
    except ImportError:
        pass
    
    # ── Step 2: UA Initial Response ──────────────────────────────────────────
    try:
        ua_step_2 = prompt_func(f"{Color.UA_RESPONSE}> {Color.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        ua_step_2 = "..."

    step2_type, _ = iv_system.classify_ua_input(ua_step_2)
    exchange.turns[1].content = ua_step_2
    exchange.turns[1].input_type = step2_type

    step2_percept = ""
    if step2_type in (UAInputType.PHYSICAL_ACTION, UAInputType.MIXED):
        step2_percept = iv_system.generate_perceptual_description(
            ua_step_2,
            scene_context=getattr(exchange, 'completed_action', ''),
            actor=getattr(exchange, 'actor', None)
        )
        exchange.turns[1].perceptual_description = step2_percept
        if step2_percept:
            print(f"\n{Color.PERCEPTUAL}{step2_percept}{Color.RESET}")
            try:
                from pygame_narrative_display import send_perceptual as _sp
                _sp(step2_percept)
            except ImportError:
                pass

    # ── Step 3: IV reacts to UA's step 2 ────────────────────────────────────
    exchange.turns[2].content = iv_system.generate_step_3_response(
        exchange,
        ua_step_2,
        input_type=step2_type,
        perceptual_description=step2_percept
    )
    print(f"\n{Color.INTERNAL_VOICE}Inner Voice: {exchange.turns[2].content}{Color.RESET}")
    try:
        from pygame_narrative_display import send_iv_exchange_iv as _siv
        _siv(exchange.turns[2].content)
    except ImportError:
        pass

    # ── Step 4: UA Debates/Defends ───────────────────────────────────────────
    try:
        ua_step_4 = prompt_func(f"{Color.UA_RESPONSE}> {Color.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        ua_step_4 = "..."

    step4_type, _ = iv_system.classify_ua_input(ua_step_4)
    exchange.turns[3].content = ua_step_4
    exchange.turns[3].input_type = step4_type

    step4_percept = ""
    if step4_type in (UAInputType.PHYSICAL_ACTION, UAInputType.MIXED):
        step4_percept = iv_system.generate_perceptual_description(
            ua_step_4,
            scene_context=getattr(exchange, 'completed_action', ''),
            actor=getattr(exchange, 'actor', None)
        )
        exchange.turns[3].perceptual_description = step4_percept
        if step4_percept:
            print(f"\n{Color.PERCEPTUAL}{step4_percept}{Color.RESET}")
            try:
                from pygame_narrative_display import send_perceptual as _sp
                _sp(step4_percept)
            except ImportError:
                pass

    # ── Step 5: IV delivers truth ────────────────────────────────────────────
    exchange.turns[4].content = iv_system.generate_step_5_response(
        exchange,
        ua_step_4,
        input_type=step4_type,
        perceptual_description=step4_percept
    )
    print(f"\n{Color.INTERNAL_VOICE}Inner Voice: {exchange.turns[4].content}{Color.RESET}")
    try:
        from pygame_narrative_display import send_iv_exchange_iv as _siv
        _siv(exchange.turns[4].content)
    except ImportError:
        pass

    # ── Step 6: UA Final Position ────────────────────────────────────────────
    try:
        ua_step_6 = prompt_func(f"{Color.UA_RESPONSE}> {Color.RESET}").strip()
    except (KeyboardInterrupt, EOFError):
        ua_step_6 = "..."

    step6_type, _ = iv_system.classify_ua_input(ua_step_6)
    exchange.turns[5].content = ua_step_6
    exchange.turns[5].input_type = step6_type

    step6_percept = ""
    if step6_type in (UAInputType.PHYSICAL_ACTION, UAInputType.MIXED):
        step6_percept = iv_system.generate_perceptual_description(
            ua_step_6,
            scene_context=getattr(exchange, 'completed_action', ''),
            actor=getattr(exchange, 'actor', None)
        )
        exchange.turns[5].perceptual_description = step6_percept
        if step6_percept:
            print(f"\n{Color.PERCEPTUAL}{step6_percept}{Color.RESET}")
            try:
                from pygame_narrative_display import send_perceptual as _sp
                _sp(step6_percept)
            except ImportError:
                pass

    return exchange


def display_spirit_impact(exchange: InternalVoiceExchange, spirit_status: Dict[str, Any], outcome: str = ""):
    """Display the spirit impact after exchange completion with success check results"""
    from internal_voice_exchange_system import PersonalityConflictType

    conflict_type = getattr(exchange, 'conflict_type', None)
    is_for_internal = conflict_type == PersonalityConflictType.FOR_INTERNAL

    if exchange.spirit_impact == SpiritImpactDirection.POSITIVE:
        impact_color = Color.SYSTEM
    elif exchange.spirit_impact == SpiritImpactDirection.NEGATIVE:
        impact_color = Color.WARNING
    else:
        impact_color = Color.SYSTEM

    print(f"\n{impact_color}{spirit_status['description']}{Color.RESET}")


def get_spirit_status_display(actor) -> str:
    """Get a formatted spirit status string for display"""
    iv_system = get_internal_voice_exchange_system()
    actor_id = getattr(actor, 'id', None) or getattr(actor.sheet, 'name', 'ua')
    
    spirit_status = iv_system.get_spirit_status(actor_id)
    
    level = spirit_status['level']
    if level >= 5:
        symbol = "✨"
    elif level >= 0:
        symbol = "🌟"
    elif level >= -5:
        symbol = "⛈️"
    else:
        symbol = "💀"
    
    return f"{symbol} Spirit: {spirit_status['description']} ({level:.1f})"


def format_internal_voice_for_exchange_context(
    actor,
    action_description: str
) -> Optional[str]:
    """
    Format Internal Voice context for inclusion in exchange processing.
    This is called when an exchange involves the UA to provide Internal Voice perspective.
    """
    iv_system = get_internal_voice_exchange_system()
    actor_id = getattr(actor, 'id', None) or getattr(actor.sheet, 'name', 'ua')
    
    spirit_status = iv_system.get_spirit_status(actor_id)
    
    # Only include if spirit is significantly affected
    if abs(spirit_status['level']) >= 3:
        return f"Internal Voice (Spirit State): {spirit_status['description']}"
    
    return None


def run_internal_voice_exchange_flow(
    actor,
    completed_action: str,
    action_result: str,
    is_extreme_scenario: bool = False,
    prompt_func=None
) -> Optional[Tuple[str, float]]:
    """
    Complete flow for running a post-action Internal Voice realization exchange.
    This runs AFTER the action is committed - the Internal Voice speaks of what was done.
    The exchange IS the realization process itself.
    
    Returns (narrative_result, spirit_impact) if exchange occurred, None otherwise.
    
    Args:
        actor: The UA actor
        completed_action: Description of the action that was committed
        action_result: Result/outcome of the action
        is_extreme_scenario: Whether this was an extreme scenario
        prompt_func: Optional function to get user input (defaults to built-in input)
    """
    # Check if we should trigger based on completed action
    exchange = check_and_trigger_internal_voice_exchange(
        actor=actor,
        action_description=completed_action,
        scene_context=action_result,
        is_extreme_scenario=is_extreme_scenario
    )
    
    if not exchange:
        return None
    
    # Run the 6-step conversation
    exchange = run_6_step_internal_voice_conversation(exchange, prompt_func)
    
    # Process the completed exchange
    iv_system = get_internal_voice_exchange_system()
    actor_id = getattr(actor, 'id', None) or getattr(actor.sheet, 'name', 'ua')
    narrative, impact, outcome = iv_system.process_completed_exchange(actor_id, exchange)
    
    # Display spirit impact
    spirit_status = iv_system.get_spirit_status(actor_id)
    display_spirit_impact(exchange, spirit_status, outcome)
    
    return narrative, impact


# Integration with existing internal voice functions for backwards compatibility
def generate_internal_voice_morality_compass(
    actor,
    action_description: str,
    scene_context: str,
    narrator=None,
    is_extreme_scenario: bool = False
) -> Optional[str]:
    """
    New unified function to generate Internal Voice as morality compass.
    Replaces the old generate_unified_internal_voice for personality-based triggers.
    """
    # Check if this should trigger an exchange
    exchange = check_and_trigger_internal_voice_exchange(
        actor=actor,
        action_description=action_description,
        scene_context=scene_context,
        is_extreme_scenario=is_extreme_scenario
    )
    
    if exchange and exchange.turns:
        # Return the first voice prompt for display
        return exchange.turns[0].content
    
    return None
