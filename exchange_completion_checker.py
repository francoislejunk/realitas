"""
Exchange Completion Checker

Determines when exchanges should naturally end based on actor states and intent.
Prevents premature endings while respecting incapacitation and explicit disengagement.
"""

from typing import Tuple, Optional, List, Dict, Any
from actor_sheet import StatusType
import json
import re

try:
    from stranger_description_system import known_actors_tracker, get_nua_definite_description
except Exception:
    known_actors_tracker = None
    get_nua_definite_description = None


class ExchangeCompletionChecker:
    """
    Checks if an exchange should continue or end naturally.
    
    Exchanges end ONLY when:
    1. Actor is incapacitated (STAMINA/SPIRIT = 0)
    2. Actor dies
    3. Actor explicitly disengages
    4. Both actors mutually agree to end
    """
    
    def __init__(self):
        """Initialize the exchange completion checker."""
        # LLM client for dynamic intent detection (lazy-loaded)
        self._llm_client = None
        
        # Fallback keywords only used if LLM fails
        self._fallback_disengagement_keywords = [
            'i leave', 'i walk away', "i'm done", 'goodbye', 'bye',
            'i back off', 'i step back', 'i disengage', 'i flee', 'i run away',
            'i retreat', 'i exit', 'i quit', "that's enough",
            'i end this', 'i surrender', 'i give up'
        ]
    
    def _get_llm_client(self):
        """Lazy-load LLM client using centralized OpenRouter config."""
        if self._llm_client is None:
            try:
                from openrouter_config import create_openrouter_client
                self._llm_client = create_openrouter_client()
            except Exception:
                pass
        return self._llm_client
    
    def _detect_disengagement_intent_llm(self, user_input: str, reactor_name: str) -> Tuple[bool, str]:
        """
        Use LLM to detect if user input expresses intent to disengage from the current interaction.
        
        This is smarter than keyword matching because it understands context:
        - "I run over to help" = NOT disengaging (approaching)
        - "I run away" = disengaging (fleeing)
        - "I leave to get supplies" = disengaging (departing)
        - "I stop to think" = NOT disengaging (pausing)
        - "Stop! I surrender" = disengaging (giving up)
        """
        client = self._get_llm_client()
        if not client:
            return self._fallback_keyword_check(user_input)
        
        try:
            from openrouter_config import OpenRouterConfig
            
            prompt = f"""Analyze this player action to determine if they are trying to DISENGAGE from their current interaction with {reactor_name}.

Player action: "{user_input}"

DISENGAGING means the player wants to:
- Leave/exit the current scene or conversation
- Flee/retreat/run away FROM the other person
- End the interaction (goodbye, I'm done, etc.)
- Surrender or give up

NOT DISENGAGING means the player wants to:
- Continue interacting (even if moving within the scene)
- Approach or help someone
- Take an action directed AT the other person
- Run TOWARD something (not away)

Respond with ONLY a JSON object:
{{"is_disengaging": true/false, "reason": "brief explanation"}}"""

            response = client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100,
                temperature=0.1
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Parse JSON
            json_match = re.search(r'\{[^}]+\}', result_text)
            if json_match:
                result = json.loads(json_match.group())
                is_disengaging = result.get('is_disengaging', False)
                reason = result.get('reason', 'LLM detected disengagement intent')
                return (is_disengaging, reason)
            
        except Exception as e:
            print(f"[DISENGAGE CHECK] LLM failed: {e}, using fallback")
        
        # Fallback to keyword check
        return self._fallback_keyword_check(user_input)
    
    def _fallback_keyword_check(self, user_input: str) -> Tuple[bool, str]:
        """Fallback keyword-based disengagement check."""
        user_input_lower = user_input.lower()
        for keyword in self._fallback_disengagement_keywords:
            if keyword in user_input_lower:
                return (True, f"Keyword match: '{keyword}'")
        return (False, "No disengagement detected")
    
    def should_exchange_continue(
        self, 
        proactor, 
        reactor, 
        last_user_input: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Determine if exchange should continue based on actor states and intent.
        
        Args:
            proactor: The acting actor
            reactor: The reacting actor
            last_user_input: The last action taken (to check for disengagement)
            
        Returns:
            (bool, str): (should_continue, reason)
        """

        def _display_name(_actor) -> str:
            try:
                name = getattr(getattr(_actor, 'sheet', None), 'name', None)
                if not name:
                    return str(_actor)
                if known_actors_tracker is None or get_nua_definite_description is None:
                    return str(name)
                try:
                    if known_actors_tracker.is_name_known(str(name)):
                        return str(name)
                except Exception:
                    return str(name)
                try:
                    replacement = get_nua_definite_description(_actor, ua_actor=None)
                    if replacement:
                        return str(replacement)
                except Exception:
                    pass
                return str(name)
            except Exception:
                return "someone"

        pro_disp = _display_name(proactor)
        rea_disp = _display_name(reactor)

        # Check proactor incapacitation
        if proactor.sheet.statuses[StatusType.STAMINA].value <= 0:
            return (False, f"{pro_disp} is unconscious (STAMINA depleted)")
        
        if proactor.sheet.statuses[StatusType.SPIRIT].value <= 0:
            return (False, f"{pro_disp} is broken (SPIRIT depleted)")
        
        # Check reactor incapacitation
        if reactor.sheet.statuses[StatusType.STAMINA].value <= 0:
            return (False, f"{rea_disp} is unconscious (STAMINA depleted)")
        
        if reactor.sheet.statuses[StatusType.SPIRIT].value <= 0:
            return (False, f"{rea_disp} is broken (SPIRIT depleted)")
        
        # Check for death
        if hasattr(proactor.sheet, 'is_dead') and proactor.sheet.is_dead():
            return (False, f"{pro_disp} is dead")
        
        if hasattr(reactor.sheet, 'is_dead') and reactor.sheet.is_dead():
            return (False, f"{rea_disp} is dead")
        
        # Check for explicit disengagement in last action using LLM
        if last_user_input:
            reactor_name = getattr(getattr(reactor, 'sheet', None), 'name', 'the other person')
            is_disengaging, reason = self._detect_disengagement_intent_llm(last_user_input, reactor_name)
            if is_disengaging:
                return (False, f"{pro_disp} disengages")
        
        # Default: Continue
        return (True, "Exchange continues")
    
    def check_npc_wants_to_disengage(
        self,
        npc,
        exchange_history: List[Dict[str, Any]],
        min_turns: int = 2
    ) -> Tuple[bool, str]:
        """
        Check if NPC wants to disengage based on situation.
        
        NPCs may disengage when:
        - SPIRIT is very low (demoralized)
        - They've been losing consistently
        - Their personality suggests retreat (cowardly, pragmatic)
        
        Args:
            npc: The NPC actor
            exchange_history: History of exchange turns
            min_turns: Minimum turns before NPC can disengage
            
        Returns:
            (bool, str): (wants_to_disengage, reason)
        """

        def _display_name(_actor) -> str:
            try:
                name = getattr(getattr(_actor, 'sheet', None), 'name', None)
                if not name:
                    return str(_actor)
                if known_actors_tracker is None or get_nua_definite_description is None:
                    return str(name)
                try:
                    if known_actors_tracker.is_name_known(str(name)):
                        return str(name)
                except Exception:
                    return str(name)
                try:
                    replacement = get_nua_definite_description(_actor, ua_actor=None)
                    if replacement:
                        return str(replacement)
                except Exception:
                    pass
                return str(name)
            except Exception:
                return "someone"

        npc_disp = _display_name(npc)
        # Don't allow disengagement too early
        if len(exchange_history) < min_turns:
            return (False, "Too early to disengage")
        
        # Check SPIRIT level
        spirit = npc.sheet.statuses[StatusType.SPIRIT]
        spirit_percent = spirit.value / spirit.max_value if spirit.max_value > 0 else 0
        
        # Very low SPIRIT = demoralized
        if spirit_percent < 0.2:
            return (True, f"{npc_disp} is demoralized and retreats")
        
        # Check personality traits for cowardice
        personality = npc.sheet.personality_traits
        if isinstance(personality, dict):
            internal = personality.get('internal', '').lower()
            external = personality.get('external', '').lower()
            
            cowardly_traits = ['cowardly', 'timid', 'fearful', 'cautious', 'nervous']
            if any(trait in internal or trait in external for trait in cowardly_traits):
                if spirit_percent < 0.4:
                    return (True, f"{npc_disp} loses nerve and backs away")
        
        # Check if consistently losing
        if len(exchange_history) >= 3:
            recent_losses = 0
            for turn in exchange_history[-3:]:
                if turn.get('winner') != npc.sheet.name:
                    recent_losses += 1
            
            if recent_losses >= 3 and spirit_percent < 0.5:
                return (True, f"{npc_disp} realizes they're outmatched and withdraws")
        
        # Default: Continue fighting
        return (False, "NPC continues")
    
    def format_ending_message(self, reason: str) -> str:
        """Format a narrative ending message based on the reason."""
        if "unconscious" in reason.lower():
            return f"💤 {reason}. The exchange ends."
        elif "broken" in reason.lower():
            return f"💔 {reason}. The exchange ends."
        elif "dead" in reason.lower():
            return f"☠️  {reason}. The exchange ends."
        elif "disengage" in reason.lower() or "retreat" in reason.lower():
            return f"🚶 {reason}."
        elif "demoralized" in reason.lower() or "outmatched" in reason.lower():
            return f"😰 {reason}."
        else:
            return f"⚔️  {reason}."


# Global instance
_completion_checker_instance = None

def get_completion_checker() -> ExchangeCompletionChecker:
    """Get or create the global completion checker instance."""
    global _completion_checker_instance
    if _completion_checker_instance is None:
        _completion_checker_instance = ExchangeCompletionChecker()
    return _completion_checker_instance
