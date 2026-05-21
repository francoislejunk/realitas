from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional

from logbook.utas_logger import UTASLogger
from exchange_system import Exchange
from .narrator_agent import NarratorAgent
from .interpreter_agent import InterpreterAgent
from agents.decider_agent import DeciderAgent

if TYPE_CHECKING:
    from actors import Actor

class ConductorAgent:
    """
    The coordinating Conductor agent, responsible for orchestrating the simulation 
    turn by turn using specialized interpretation and decision agents.
    """

    def __init__(self, logger: UTASLogger, scene_description: str, recovery_integrator=None, tracker_agent=None, actor_manager=None, rag_system=None, key_memories_system=None, fact_system=None, mention_system=None):
        """
        Initialize the ConductorAgent with required dependencies.

        Args:
            logger: The UTAS logger instance
            scene_description: Current scene description
            recovery_integrator: Optional recovery integrator for health/status management
            tracker_agent: Optional tracker agent for state management
            actor_manager: Optional actor manager for NPC management
            rag_system: Optional RAG system for worldbuilding context
            key_memories_system: Optional key memories system for memory-aware context
            fact_system: Optional fact system for canonical fact tracking
            mention_system: Optional mention system for actor mention tracking
        """
        self.logger = logger
        self.scene_description = scene_description
        self.recovery_integrator = recovery_integrator
        self.tracker_agent = tracker_agent
        self.actor_manager = actor_manager
        self.rag_system = rag_system
        self.key_memories_system = key_memories_system
        self.fact_system = fact_system  # For canonical facts
        self.mention_system = mention_system  # For actor mention tracking

        self.narrator = NarratorAgent(rag_system=rag_system, key_memories_system=key_memories_system, mention_system=mention_system)

        self.interpreter_agent = InterpreterAgent(logger, scene_description, tracker_agent, actor_manager, key_memories_system, rag_system, fact_system, mention_system)
        self.decider_agent = DeciderAgent(logger, scene_description, tracker_agent, rag_system=rag_system, narrative_context_manager=None)  # Will be set externally

        print("Coordinating Conductor initialized with specialized agents.")

    def roll_for_initiative(self, actor1: 'Actor', actor2: 'Actor') -> Tuple['Actor', 'Actor']:
        """
        Delegates initiative rolling to the interpretation agent.
        """
        return self.interpreter_agent.roll_for_initiative(actor1, actor2)

    def enforce_continuity(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Optional[Dict[str, Any]]:
        """
        Delegates continuity checking to the interpretation agent.
        """
        return self.interpreter_agent.enforce_continuity(user_input, proactor, reactor)

    def interpret_user_action(self, user_input: str, proactor: 'Actor') -> Optional[Dict[str, Any]]:
        """
        Delegates user action interpretation to the interpretation agent.
        """
        return self.interpreter_agent.interpret_user_action(user_input, proactor)

    def interpret_fallible_action(self, user_input: str, proactor: 'Actor') -> Optional[Dict[str, Any]]:
        """Delegates fallible (non-given) action interpretation to InterpreterAgent.
        This method is referenced by redesigned_main.py and must exist to avoid AttributeError.
        """
        return self.interpreter_agent.interpret_fallible_action(user_input, proactor)

    def interpret_nua_action(self, nua_action_string: str, proactor: 'Actor') -> Optional[Dict[str, Any]]:
        """
        Delegates NUA action interpretation to the interpretation agent.
        This is used when an NUA's action (like a reaction) is a simple string and needs to be converted to the full structured format.
        """
        return self.interpreter_agent.interpret_user_action(nua_action_string, proactor)

    def determine_nua_proaction(self, proactor: 'Actor', reactor: 'Actor', context_guidance: Dict = None, group_members: list = None, last_exchange_context: Dict = None) -> Optional[Dict[str, Any]]:
        """
        Delegates NUA proaction determination to the decision agent.
        INUAs don't take proactive actions - they only react.

        Args:
            proactor: The actor taking the action
            reactor: The target of the action
            context_guidance: Context and escalation guidance
            group_members: List of actors acting together in a grouped turn
            last_exchange_context: Recent exchange data for continuity
        """
        if hasattr(proactor, 'is_inanimate') and proactor.is_inanimate:
            return None
        raw = self.decider_agent.determine_nua_proaction(proactor, reactor, context_guidance, group_members=group_members, last_exchange_context=last_exchange_context)
        # Centralize normalization/repair in Interpreter for Proactor as well
        try:
            result = self.interpreter_agent.validate_and_repair_proactor(raw or {}, proactor, reactor, context_guidance)

            # Extract facts from dialogue
            if self.fact_system and result and isinstance(result, dict):
                dialogue = result.get('dialogue')
                if dialogue:
                    proactor_name = getattr(proactor.sheet, 'name', 'Unknown') if hasattr(proactor, 'sheet') else str(proactor)
                    reactor_name = getattr(reactor.sheet, 'name', 'Unknown') if hasattr(reactor, 'sheet') else str(reactor)
                    turn_num = context_guidance.get('turn_number', 0) if context_guidance else 0
                    scene_id = context_guidance.get('scene_id', '') if context_guidance else ''

                    self._extract_dialogue_facts(dialogue, proactor_name, reactor_name, turn_num, scene_id)

            # Extract mentions from dialogue
            if self.mention_system and result and isinstance(result, dict):
                dialogue = result.get('dialogue')
                if dialogue:
                    proactor_name = getattr(proactor.sheet, 'name', 'Unknown') if hasattr(proactor, 'sheet') else str(proactor)
                    reactor_name = getattr(reactor.sheet, 'name', 'Unknown') if hasattr(reactor, 'sheet') else str(reactor)
                    turn_num = context_guidance.get('turn_number', 0) if context_guidance else 0
                    scene_id = context_guidance.get('scene_id', '') if context_guidance else ''

                    self._extract_dialogue_mentions(dialogue, proactor_name, reactor_name, turn_num, scene_id)

            return result
        except Exception:
            return raw or {}

    def determine_nua_reaction(self, proactor: 'Actor', proactor_action_data: Dict[str, Any], reactor: 'Actor', context_guidance: Optional[Dict[str, Any]] = None) -> Optional[Dict[str, Any]]:
        """
        Delegates NUA reaction determination to the decision agent.
        For INUAs, this generates passive resistance/response based on their properties.
        """
        if hasattr(reactor, 'is_inanimate') and reactor.is_inanimate:
            return self.decider_agent.determine_inua_reaction(proactor, proactor_action_data, reactor)
        raw = self.decider_agent.determine_nua_reaction(proactor, proactor_action_data, reactor, context_guidance)
        # Centralize normalization/repair in Interpreter
        try:
            guidance = context_guidance
            try:
                if not isinstance(guidance, dict):
                    guidance = {}
                else:
                    guidance = dict(guidance)

                expects_dialogue = False
                try:
                    dm = (proactor_action_data.get('dialogue_metadata') or {}) if isinstance(proactor_action_data, dict) else {}
                    if isinstance(dm, dict):
                        expects_dialogue = bool(dm.get('dialogue_weight', 0) or dm.get('dialogue_only', False))
                except Exception:
                    expects_dialogue = False

                guidance['expects_dialogue'] = expects_dialogue

                # Best-effort carry proactor's question/dialogue text forward so reactor repair can stay coherent.
                try:
                    nd = (proactor_action_data.get('narrative_description') or '') if isinstance(proactor_action_data, dict) else ''
                    nd = str(nd or '').strip()
                    guidance['proactor_question'] = nd if expects_dialogue else (guidance.get('proactor_question') or '')
                except Exception:
                    pass
            except Exception:
                guidance = context_guidance

            result = self.interpreter_agent.validate_and_repair_reactor(raw or {}, proactor, reactor, guidance)

            # Extract facts from reactor dialogue
            if self.fact_system and result and isinstance(result, dict):
                dialogue = result.get('dialogue')
                if dialogue:
                    reactor_name = getattr(reactor.sheet, 'name', 'Unknown') if hasattr(reactor, 'sheet') else str(reactor)
                    proactor_name = getattr(proactor.sheet, 'name', 'Unknown') if hasattr(proactor, 'sheet') else str(proactor)
                    turn_num = guidance.get('turn_number', 0) if guidance else 0
                    scene_id = guidance.get('scene_id', '') if guidance else ''

                    self._extract_dialogue_facts(dialogue, reactor_name, proactor_name, turn_num, scene_id)

            # Extract mentions from reactor dialogue
            if self.mention_system and result and isinstance(result, dict):
                dialogue = result.get('dialogue')
                if dialogue:
                    reactor_name = getattr(reactor.sheet, 'name', 'Unknown') if hasattr(reactor, 'sheet') else str(reactor)
                    proactor_name = getattr(proactor.sheet, 'name', 'Unknown') if hasattr(proactor, 'sheet') else str(proactor)
                    turn_num = guidance.get('turn_number', 0) if guidance else 0
                    scene_id = guidance.get('scene_id', '') if guidance else ''

                    self._extract_dialogue_mentions(dialogue, reactor_name, proactor_name, turn_num, scene_id)

            return result
        except Exception:
            return raw or {}

    def detect_inquiry_or_action(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]:
        """
        Delegates inquiry/action detection to the interpretation agent.
        """
        return self.interpreter_agent.detect_inquiry_or_action(user_input, proactor, reactor)
    
    def detect_existing_actor_reference(self, user_input: str, existing_actors: list) -> Optional[Dict[str, Any]]:
        """
        Detect if user input refers to an existing actor.
        Delegates to the InterpreterAgent.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
            
        Returns:
            Dict with existing actor reference data if found, None otherwise
        """
        return self.interpreter_agent.detect_existing_actor_reference(user_input, existing_actors)

    def detect_new_actor_mention(self, user_input: str, existing_actors: list) -> Optional[Dict[str, Any]]:
        """
        Detect if user input mentions a new actor that should be created.
        Delegates to the InterpreterAgent.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
            
        Returns:
            Dict with actor creation data if new actor detected, None otherwise
        """
        return self.interpreter_agent.detect_new_actor_mention(user_input, existing_actors)
    
    def detect_target_type(self, user_input: str, scene_description: str = "") -> Dict[str, Any]:
        """
        Determine if the user's action is targeting an NUA (animate) or INUA (inanimate).
        Delegates to the InterpreterAgent.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context for better analysis
            
        Returns:
            Dict with target_type ('nua' or 'inua'), confidence, reasoning, and detected_target
        """
        return self.interpreter_agent.detect_target_type(user_input, scene_description)
    
    def is_targeting_nua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an NUA (animate being).
        Delegates to the InterpreterAgent.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting NUA, False if targeting INUA
        """
        return self.interpreter_agent.is_targeting_nua(user_input, scene_description)
    
    def is_targeting_inua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an INUA (inanimate object).
        Delegates to the InterpreterAgent.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting INUA, False if targeting NUA
        """
        return self.interpreter_agent.is_targeting_inua(user_input, scene_description)
    
    def enforce_sensory_perception(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Optional[Dict[str, Any]]:
        """
        Delegates sensory perception checking to the interpretation agent.
        """
        return self.interpreter_agent.enforce_sensory_perception(user_input, proactor, reactor)

    def handle_inquiry(self, user_input: str, proactor: 'Actor', reactor: 'Actor', time_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Handles inquiry with success-based narrative generation using comprehensive UTAS interpretation.
        Returns both calculation data and narrative response.
        """
        # Use InterpreterAgent's comprehensive fallible action interpretation
        try:
            interpretation_data = self.interpreter_agent.interpret_fallible_action(user_input, proactor)
        except Exception:
            interpretation_data = None
        
        # Convert interpretation data to success_data format for compatibility (be defensive)
        utas_factors = {}
        if isinstance(interpretation_data, dict):
            utas_factors = interpretation_data.get('utas_factors') or {}
        
        # Calculate success using unified formula with interpreted data
        from unified_formula import calculate_unified_result
        from actor_sheet import SFactorType
        
        # Map S-trait name to enum (robust to casing/missing)
        s_trait_map = {
            'Swiftness': SFactorType.SWIFTNESS,
            'Sociability': SFactorType.SOCIABILITY,
            'Sturdiness': SFactorType.STURDINESS,
            'Smarts': SFactorType.SMARTS,
            'Shadow': SFactorType.SHADOW,
        }
        s_label = str(utas_factors.get('s_trait_to_use', 'Smarts')).strip().title()
        s_trait_type = s_trait_map.get(s_label, SFactorType.SHADOW)

        skill_data = utas_factors.get('skill') or {}
        skill_name = skill_data.get('name')
        if not skill_name or str(skill_name).lower() == 'none':
            skill_name = None

        supp_data = utas_factors.get('supplement') or {}
        supp_name = supp_data.get('name')
        supplement_val = supp_data.get('value', 0) if supp_name and str(supp_name).lower() != 'none' else 0
        
        # Roll serendipity
        import random
        serendipity_roll = random.randint(1, 6)
        
        unified_result = calculate_unified_result(
            actor=proactor,
            s_trait=s_trait_type,
            skill_name=skill_name,
            target_actor=None,
            shift_polarity='Subtractive',
            targeted_status=None,
            supplement_val=supplement_val,
            serendipity_override=serendipity_roll,
            stress_level_override=(
                (lambda v: v if isinstance(v, int) else int(v))(
                    utas_factors.get('stress_level', 0)
                ) + 3
            )
        )
        
        total_score = unified_result['final_result']
        
        # Determine success level
        if total_score <= 0:
            success_level = 0 if total_score == 0 else -1
        else:
            success_level = total_score
        
        # Create success_data in expected format (include display-friendly aliases)
        reverse_s_trait_map = {
            SFactorType.SWIFTNESS: 'Swiftness',
            SFactorType.SOCIABILITY: 'Sociability',
            SFactorType.STURDINESS: 'Sturdiness',
            SFactorType.SMARTS: 'Smarts',
            SFactorType.SHADOW: 'Shadow',
        }
        s_trait_used_label = utas_factors.get('s_trait_to_use') or reverse_s_trait_map.get(s_trait_type, 'Shadow')
        # Safely resolve s-trait numeric value
        try:
            s_trait_value_num = int(utas_factors.get('s_trait_value'))
        except Exception:
            try:
                s_factor_obj = proactor.sheet.s_factors[s_trait_type]
                s_trait_value_num = int(getattr(s_factor_obj, 'value', 1))
            except Exception:
                s_trait_value_num = 1
        # Safely resolve skill numeric value
        try:
            skill_value_num = int((utas_factors.get('skill') or {}).get('value', 0))
        except Exception:
            skill_value_num = 0
        # Safely resolve endowment fields
        endowment_data = utas_factors.get('endowment') or {}
        endowment_name = endowment_data.get('name') if str(endowment_data.get('name', 'None')).lower() != 'none' else 'none'
        try:
            endowment_value_num = int(endowment_data.get('value', 0))
        except Exception:
            endowment_value_num = 0
        # Safely resolve stress level
        try:
            stress_level_num = int(utas_factors.get('stress_level', 0))
        except Exception:
            stress_level_num = 0
        success_data = {
            'success_level': success_level,
            's_trait_type': s_trait_type,
            's_trait_value': s_trait_value_num,
            # Display-friendly field expected by exploration output
            's_trait_used': s_trait_used_label,
            'skill_name': skill_name or 'none',
            'skill_value': skill_value_num,
            # Display-friendly field expected by exploration output
            'skill_used': skill_name or 'none',
            'endowment_name': endowment_name,
            'endowment_value': endowment_value_num,
            'serendipity_roll': serendipity_roll,
            # Display-friendly alias used by exploration output
            'serendipity': serendipity_roll,
            'serendipity_breakdown': f"Serendipity Roll: {serendipity_roll}",
            'stressor': stress_level_num,
            # Display-friendly alias used by exploration output
            'stress_level': stress_level_num,
            'total_score': total_score,
            # Common 'total' alias for consistency with other paths
            'total': total_score,
            'breakdown': f"📊 COMPREHENSIVE UTAS ANALYSIS\n{(interpretation_data or {}).get('action_description', user_input)}\n\nS-Trait ({s_trait_used_label}): {s_trait_value_num}\nSkill ({skill_name or 'none'}): {skill_value_num}\nEndowment ({endowment_name}): {endowment_value_num}\nSupplement ({(supp_data.get('name') if supp_data else 'None') or 'None'}): {supplement_val}\nSerendipity: {serendipity_roll}\nStress: {stress_level_num}\nTotal: {total_score}",
            'self_effects_applied': []
        }
        
        # Process inquiry through narrative loop for context tracking
        turn_data = {
            'user_input': user_input,
            'continuity_check': {'judgment': 'Possible'},
            'success_calculation': success_data,
            'inquiry_type': True,
            'interpretation_data': interpretation_data
        }
        
        # Process turn through narrative loop to update narrative state and get framing guidance
        framing = self.narrator.narrative_loop.process_turn(turn_data, time_context=time_context)
        
        from inquiry_system import InquiryNarrativeGenerator
        narrative_generator = InquiryNarrativeGenerator(self.narrator)
        narrative_response = narrative_generator.generate_narrative_response(
            user_input, success_data, self.scene_description, proactor, reactor, time_context,
            framing_guidance=framing,
            session_id=getattr(self.tracker_agent, 'session_id', None) if self.tracker_agent else None,
        )
        
        return {
            'success_data': success_data,
            'narrative_response': narrative_response,
            'interpretation_data': interpretation_data
        }

    def resolve_turn(self, proactor: 'Actor', reactor: 'Actor', proactor_action_data: Dict[str, Any], reactor_action_data: Dict[str, Any]) -> 'Exchange':
        """Creates and executes an exchange, then returns the exchange object."""
        exchange = Exchange(
            proactor=proactor, 
            reactor=reactor, 
            proactor_action_data=proactor_action_data,
            reactor_action_data=reactor_action_data,
            recovery_integrator=self.recovery_integrator
        )
        return exchange.execute()

    def classify_rule_of_3s(self, user_input: str, proactor: 'Actor', reactor: 'Actor'):
        """
        Delegates Rule of 3's temporal classification to the interpretation agent.
        """
        return self.interpreter_agent.classify_rule_of_3s(user_input, proactor, reactor)

    def convert_situation_to_contested_action(self, user_input: str, reactor: 'Actor', proactor: 'Actor', scene_description: str) -> Optional[Dict[str, Any]]:
        """
        Intelligently converts situation overcoming actions into contested actions during exchanges.
        
        Args:
            user_input: Original environmental action
            reactor: The actor attempting the action
            proactor: The opponent in the exchange
            scene_description: Current scene context
            
        Returns:
            Dict with 'converted_action', 'bridge_narrative' or None if conversion fails
        """
        conversion_prompt = f"""
You are converting an environmental action into a contested action during combat/exchange.

**ORIGINAL ACTION:** "{user_input}"
**REACTOR (Acting):** {reactor.sheet.name}
**PROACTOR (Opponent):** {proactor.sheet.name}
**SCENE CONTEXT:** {scene_description}

**CONVERSION TASK:**
Transform the environmental action into a contested maneuver against the opponent. The action should:
1. Maintain the core intent of the original action
2. Make the opponent the primary obstacle/target
3. Create tactical advantage or defensive positioning
4. Feel natural and immersive

**CONVERSION EXAMPLES:**
- "I climb the wall" → "I use the wall to gain height advantage over {proactor.sheet.name}"
- "I pick the lock" → "I try to reach the door lock while keeping {proactor.sheet.name} at bay"
- "I search the room" → "I scan for anything useful while staying defensive against {proactor.sheet.name}"
- "I sneak past" → "I try to outmaneuver {proactor.sheet.name} using stealth"

**RESPONSE FORMAT (JSON):**
{{
    "converted_action": "The new contested action targeting the opponent",
    "bridge_narrative": "Brief explanation of how the environmental action becomes contested (1-2 sentences)",
    "conversion_success": true
}}

If the action cannot be reasonably converted, respond with {{"conversion_success": false}}.
"""
        
        try:
            result = self.interpreter_agent._call_llm_for_json(conversion_prompt)
            if result and result.get('conversion_success'):
                return {
                    'converted_action': result.get('converted_action', user_input),
                    'bridge_narrative': result.get('bridge_narrative', 'The environmental action becomes a contested maneuver.')
                }
        except Exception as e:
            print(f"Conversion LLM error: {e}")
        
        # Fallback conversion patterns
        fallback_conversions = {
            'climb': f"use the terrain to gain tactical advantage over {proactor.sheet.name}",
            'jump': f"leap to a better position while evading {proactor.sheet.name}",
            'search': f"look for useful items while staying defensive against {proactor.sheet.name}",
            'hide': f"use cover to outmaneuver {proactor.sheet.name}",
            'sneak': f"try to outflank {proactor.sheet.name} using stealth",
            'pick': f"attempt to manipulate the environment while keeping {proactor.sheet.name} at bay",
            'open': f"try to access the area while defending against {proactor.sheet.name}",
            'move': f"reposition tactically against {proactor.sheet.name}"
        }
        
        user_lower = user_input.lower()
        for keyword, conversion in fallback_conversions.items():
            if keyword in user_lower:
                return {
                    'converted_action': f"I {conversion}",
                    'bridge_narrative': f"The environmental maneuver becomes a tactical move against {proactor.sheet.name}."
                }
        
        return None

    def generate_final_narrative(
        self,
        proactor_action_data: Dict[str, Any],
        reactor_action_data: Dict[str, Any],
        outcome_data: Dict[str, Any],
        proactor: 'Actor',
        reactor: 'Actor',
        proactor_success_data: Dict[str, Any],
        reactor_success_data: Dict[str, Any],
        time_context: Optional[Dict[str, Any]] = None,
        framing_guidance: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate the final Step 6 narrative using a framed, validated one-line preface
        plus the deterministic UTAS outcome narrative.

        Mechanics and outcomes remain deterministic; the preface is purely tonal and
        validated to avoid contradictions or generic fluff.
        """
        # 1) Ensure we have framing from the Four-Mode Narrative Loop
        framing = framing_guidance
        if framing is None:
            try:
                # Build a minimal turn snapshot focused on outcome; keep it generic and safe
                turn_data = {
                    'user_input': 'Contested exchange resolved',
                    'scene_description': self.scene_description,
                    'continuity_check': {'judgment': 'Possible'},
                    'outcome_data': {
                        'proactor_success': outcome_data.get('proactor_success', 0),
                        'reactor_success': outcome_data.get('reactor_success', 0),
                        'targeted_status': outcome_data.get('targeted_status') or outcome_data.get('status_name')
                    }
                }
                framing = self.narrator.narrative_loop.process_turn(turn_data, time_context=time_context)
            except Exception:
                framing = None

        # 2) Generate a one-line, framed preface (LLM) and validate
        try:
            preface = self.narrator.generate_framed_preface(
                scene_description=self.scene_description,
                time_context=time_context,
                framing_guidance=framing,
            )
        except Exception:
            preface = ""

        # 3) Generate the deterministic Step 6 narrative (no LLM)
        # Determine which actor is the UA for stranger description system
        ua_actor = proactor if getattr(proactor, 'is_user_actor', False) else (reactor if getattr(reactor, 'is_user_actor', False) else None)
        core_outcome = self.narrator.generate_step6_turn_narrative(
            proactor_action_data,
            reactor_action_data,
            outcome_data,
            ua_actor=ua_actor,
        )

        # 4) Integrate preface + deterministic outcome safely
        try:
            final_text = self.narrator.integrate_preface_with_outcome(preface, core_outcome)
        except Exception:
            final_text = core_outcome

        return final_text

    def generate_scene_description(self, scene_data: Dict[str, Any], scene_type: str, time_context: Dict[str, Any]) -> str:
        """
        Generate a scene description using the narrator agent.
        
        Args:
            scene_data: Scene data from scene creator
            scene_type: Type of scene (e.g., "exploration opportunity")
            time_context: Current time context
            
        Returns:
            Generated scene description string
        """
        return self.narrator.generate_scene_description(scene_data, scene_type, time_context)
    
    def generate_new_scene(self, actor: 'Actor', scene_number: int, outcome: str) -> Tuple[str, list]:
        """
        Generate a new scene introduction with Four-Mode framing.

        Returns a tuple (scene_description, available_npcs). Currently introduces no
        NPCs by default; downstream systems (e.g., SPARK generator, dynamic actor
        system) may add NPCs organically.
        """
        # Build lightweight scene elements; we use the last known scene_description as seed
        scene_elements = {
            'setting': self.scene_description or f"New scene {scene_number}",
            'transition_bridge': f"Transition outcome: {outcome}",
            'ua_goal': 'Continue objectives based on prior events',
            'conflict': 'TBD via exploration or SPARK'
        }

        # Frame the introduction via narrative loop
        try:
            turn_data = {
                'user_input': 'Scene Introduction',
                'scene_description': scene_elements['setting'],
                'continuity_check': {'judgment': 'Possible'}
            }
            scene_description = self.narrator.generate_scene_with_narrative_loop(
                scene_elements=scene_elements,
                nua_name="",
                turn_data=turn_data,
                time_context=None,
            )
        except Exception:
            # Fallback to basic setting text
            scene_description = scene_elements['setting']

        # No default NPCs introduced at this stage
        return scene_description, []

    def _get_actor_facts(self, actor_name: str, max_facts: int = 10) -> str:
        """
        Retrieve formatted fact context for an actor for LLM prompts.

        Args:
            actor_name: Name of the actor to get facts about
            max_facts: Maximum number of facts to retrieve

        Returns:
            Formatted string of facts
        """
        if not self.fact_system:
            return ""

        try:
            context = self.fact_system.get_fact_context(actor_name, max_facts=max_facts)
            if context:
                return f"\n{context}\n"
            return ""
        except Exception as e:
            self.logger.log_system(f"WARNING: Could not fetch facts for {actor_name}: {e}")
            return ""

    def _extract_dialogue_facts(self, dialogue: str, speaker_name: str,
                                target_name: str = None,
                                turn_number: int = 0, scene_id: str = ""):
        """
        Extract facts from NPC dialogue using simple heuristic patterns.

        This is a lightweight extraction system that looks for common patterns:
        - "I'm [occupation]" -> occupation fact
        - "I'm [name]'s [relationship]" -> relationship fact
        - Mentions of possessions, locations, etc.

        For more sophisticated extraction, could integrate LLM-based parsing.

        Args:
            dialogue: The spoken dialogue text
            speaker_name: Name of the actor speaking
            target_name: Name of the target (if any)
            turn_number: Current turn number
            scene_id: Current scene ID
        """
        if not self.fact_system or not dialogue:
            return

        try:
            from fact_system import FactType, FactAuthority

            dialogue_lower = dialogue.lower()

            # Pattern: "I'm [occupation]" or "I am [occupation]"
            occupation_patterns = [
                "i'm a ", "i'm an ", "i am a ", "i am an ",
                "i work as ", "my job is "
            ]
            for pattern in occupation_patterns:
                if pattern in dialogue_lower:
                    # Extract potential occupation (simple word extraction)
                    idx = dialogue_lower.find(pattern)
                    after_pattern = dialogue[idx + len(pattern):].split()[0:3]  # Get next 1-3 words
                    occupation = " ".join(after_pattern).strip(".,!?")

                    if occupation and len(occupation) > 2:
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_IDENTITY,
                            subject=speaker_name,
                            predicate="occupation",
                            value=occupation,
                            authority=FactAuthority.DIALOGUE_MENTIONED,
                            source=f"dialogue_{speaker_name}",
                            tags=[speaker_name.lower(), "occupation", "dialogue"],
                            turn_number=turn_number,
                            scene_id=scene_id,
                            context=dialogue
                        )
                        break

            # Pattern: "I'm [name]'s [relationship]" -> relationship fact
            relationship_patterns = ["sister", "brother", "friend", "partner", "colleague"]
            for rel_word in relationship_patterns:
                if rel_word in dialogue_lower:
                    # Look for possessive patterns
                    for word in dialogue.split():
                        if "'s" in word or "s'" in word:
                            potential_name = word.replace("'s", "").replace("s'", "").strip(".,!?")
                            if potential_name and len(potential_name) > 2:
                                self.fact_system.establish_fact(
                                    fact_type=FactType.RELATIONSHIP,
                                    subject=speaker_name,
                                    predicate=rel_word,
                                    object=potential_name,
                                    authority=FactAuthority.DIALOGUE_MENTIONED,
                                    source=f"dialogue_{speaker_name}",
                                    tags=[speaker_name.lower(), potential_name.lower(), rel_word, "dialogue"],
                                    turn_number=turn_number,
                                    scene_id=scene_id,
                                    context=dialogue
                                )
                                break

            self.logger.log_system(f"Extracted dialogue facts from {speaker_name}")

        except Exception as e:
            self.logger.log_system(f"Error extracting dialogue facts: {e}")

    def _validate_action_against_facts(self, action_data: Dict[str, Any],
                                      actor_name: str) -> Optional[str]:
        """
        Validate an action's dialogue or description against established facts.

        Returns warning message if potential contradiction detected, None otherwise.

        Args:
            action_data: Action data dictionary
            actor_name: Name of the actor performing the action

        Returns:
            Warning message string if contradiction found, None otherwise
        """
        if not self.fact_system:
            return None

        try:
            # Get dialogue or action description
            text_to_validate = action_data.get('dialogue') or action_data.get('action_description', '')

            if not text_to_validate:
                return None

            # Get actor facts
            actor_facts = self.fact_system.query_facts(subject=actor_name)

            if not actor_facts:
                return None

            # Simple contradiction check: look for conflicting occupation mentions
            text_lower = text_to_validate.lower()

            for fact in actor_facts:
                if fact.predicate == "occupation":
                    # Check if different occupation is explicitly mentioned
                    occupation_lower = str(fact.value).lower()

                    # Only flag if they explicitly state a DIFFERENT occupation
                    explicit_patterns = ["i'm a ", "i'm an ", "i am a ", "i am an ", "i work as ", "my job is "]

                    for pattern in explicit_patterns:
                        if pattern in text_lower:
                            # Extract what comes after pattern
                            idx = text_lower.find(pattern)
                            after_pattern = text_to_validate[idx + len(pattern):].split()[0:3]
                            stated_occupation = " ".join(after_pattern).strip(".,!?").lower()

                            # Check if stated occupation differs from established
                            if stated_occupation and occupation_lower not in stated_occupation and stated_occupation not in occupation_lower:
                                return f"WARNING: Potential contradiction - {actor_name}'s established occupation is {fact.value}"

            return None

        except Exception as e:
            self.logger.log_system(f"Error validating action against facts: {e}")
            return None

    def _get_actor_mention_context(self, actor_name: str, max_mentions: int = 5) -> str:
        """
        Get formatted mention context for an actor to inject into prompts.

        Shows where actor was last mentioned to prevent contradictions
        and enable NPCs to reference known locations.

        Args:
            actor_name: Name of the actor to query mentions for
            max_mentions: Maximum number of mentions to include (default: 5)

        Returns:
            Formatted mention context string, or empty string if no mentions
        """
        if not self.mention_system:
            return ""

        try:
            location, confidence = self.mention_system.get_last_known_location(actor_name)
            if location:
                return f"\n**MENTION HISTORY:** {actor_name} was last mentioned at {location} (confidence: {confidence.value})\n"
            return ""
        except Exception as e:
            self.logger.log_system(f"WARNING: Could not fetch mentions for {actor_name}: {e}")
            return ""

    def _extract_dialogue_mentions(self, dialogue: str, speaker_name: str,
                                   target_name: str = None,
                                   turn_number: int = 0, scene_id: str = ""):
        """
        Extract actor mentions from NPC dialogue using heuristic patterns.

        Looks for common patterns:
        - "I saw [Actor] at [Location]" -> ELSEWHERE_CURRENT or ELSEWHERE_PAST
        - "[Actor] is at [Location]" -> ELSEWHERE_CURRENT
        - "[Actor] was at [Location]" -> ELSEWHERE_PAST
        - "I heard [Actor]..." -> RUMOR
        - "[Actor] left for [Location]" -> DEPARTING mention

        Args:
            dialogue: The spoken dialogue text
            speaker_name: Name of the actor speaking
            target_name: Name of the target (if any)
            turn_number: Current turn number
            scene_id: Current scene ID
        """
        if not self.mention_system or not dialogue:
            return

        try:
            from mention_system import MentionType, MentionSource, PresenceConfidence

            dialogue_lower = dialogue.lower()

            # Pattern 1: "I saw [Actor] at [Location]"
            if "i saw" in dialogue_lower or "saw" in dialogue_lower:
                # Extract potential actor and location
                # This is a simple heuristic - could be improved with NER
                words = dialogue.split()
                for i, word in enumerate(words):
                    if word.lower() in ["saw", "spotted", "noticed"]:
                        # Look ahead for actor name (capitalized word)
                        if i + 1 < len(words) and words[i + 1][0].isupper():
                            potential_actor = words[i + 1].strip(".,!?")
                            # Look for "at [Location]"
                            if i + 3 < len(words) and words[i + 2].lower() == "at":
                                location = words[i + 3].strip(".,!?")
                                if len(location) > 2:
                                    self.mention_system.record_mention(
                                        actor_name=potential_actor,
                                        mention_type=MentionType.ELSEWHERE_CURRENT,
                                        source=MentionSource.NPC_DIALOGUE,
                                        context=dialogue,
                                        location=location,
                                        location_confidence=PresenceConfidence.MEDIUM,
                                        turn_number=turn_number,
                                        scene_id=scene_id
                                    )
                                    self.logger.log_system(f"Recorded ELSEWHERE_CURRENT mention: {potential_actor} at {location} (from {speaker_name}'s dialogue)")

            # Pattern 2: "[Actor] is at [Location]"
            if " is at " in dialogue_lower:
                parts = dialogue.split(" is at ")
                if len(parts) == 2:
                    potential_actor = parts[0].split()[-1].strip(".,!?")  # Last word before "is at"
                    location = parts[1].split()[0].strip(".,!?")  # First word after "is at"
                    if potential_actor[0].isupper() and len(location) > 2:
                        self.mention_system.record_mention(
                            actor_name=potential_actor,
                            mention_type=MentionType.ELSEWHERE_CURRENT,
                            source=MentionSource.NPC_DIALOGUE,
                            context=dialogue,
                            location=location,
                            location_confidence=PresenceConfidence.HIGH,
                            turn_number=turn_number,
                            scene_id=scene_id
                        )
                        self.logger.log_system(f"Recorded ELSEWHERE_CURRENT mention: {potential_actor} at {location} (from {speaker_name}'s dialogue)")

            # Pattern 3: "[Actor] was at [Location]"
            if " was at " in dialogue_lower:
                parts = dialogue.split(" was at ")
                if len(parts) == 2:
                    potential_actor = parts[0].split()[-1].strip(".,!?")
                    location = parts[1].split()[0].strip(".,!?")
                    if potential_actor[0].isupper() and len(location) > 2:
                        self.mention_system.record_mention(
                            actor_name=potential_actor,
                            mention_type=MentionType.ELSEWHERE_PAST,
                            source=MentionSource.NPC_DIALOGUE,
                            context=dialogue,
                            location=location,
                            location_confidence=PresenceConfidence.MEDIUM,
                            turn_number=turn_number,
                            scene_id=scene_id
                        )
                        self.logger.log_system(f"Recorded ELSEWHERE_PAST mention: {potential_actor} at {location} (from {speaker_name}'s dialogue)")

            # Pattern 4: "I heard [Actor]..." -> RUMOR
            if "i heard" in dialogue_lower or "heard that" in dialogue_lower:
                words = dialogue.split()
                for i, word in enumerate(words):
                    if word.lower() in ["heard"]:
                        # Look ahead for actor name
                        if i + 1 < len(words) and words[i + 1][0].isupper():
                            potential_actor = words[i + 1].strip(".,!?")
                            # Record as rumor (location unknown)
                            self.mention_system.record_mention(
                                actor_name=potential_actor,
                                mention_type=MentionType.RUMOR,
                                source=MentionSource.NPC_DIALOGUE,
                                context=dialogue,
                                location_confidence=PresenceConfidence.LOW,
                                turn_number=turn_number,
                                scene_id=scene_id
                            )
                            self.logger.log_system(f"Recorded RUMOR mention: {potential_actor} (from {speaker_name}'s dialogue)")

            # Pattern 5: "[Actor] left for [Location]" -> DEPARTING
            if " left for " in dialogue_lower or " went to " in dialogue_lower:
                patterns = [" left for ", " went to ", " headed to ", " going to "]
                for pattern in patterns:
                    if pattern in dialogue_lower:
                        parts = dialogue.split(pattern)
                        if len(parts) == 2:
                            potential_actor = parts[0].split()[-1].strip(".,!?")
                            destination = parts[1].split()[0].strip(".,!?")
                            if potential_actor[0].isupper() and len(destination) > 2:
                                self.mention_system.record_departure(
                                    actor_name=potential_actor,
                                    origin="Unknown",  # Origin not mentioned in dialogue
                                    destination=destination,
                                    context=dialogue,
                                    source=MentionSource.NPC_DIALOGUE,
                                    turn_number=turn_number,
                                    scene_id=scene_id
                                )
                                self.logger.log_system(f"Recorded DEPARTING mention: {potential_actor} to {destination} (from {speaker_name}'s dialogue)")
                                break

            self.logger.log_system(f"Extracted dialogue mentions from {speaker_name}")

        except Exception as e:
            self.logger.log_system(f"Error extracting dialogue mentions: {e}")

    @property
    def interpreter(self):
        """Provide access to the interpretation agent for Rule of 3's context management"""
        return self.interpreter_agent

    @property
    def scene_description(self) -> str:
        """Current scene description synchronized across Conductor and child agents."""
        return getattr(self, "_scene_description", "")

    @scene_description.setter
    def scene_description(self, value: str) -> None:
        """Update scene description and propagate to Interpreter/Decider/Narrator."""
        self._scene_description = value
        # Best-effort propagation; guard each in case of partial init
        try:
            if hasattr(self, 'interpreter_agent') and self.interpreter_agent:
                self.interpreter_agent.scene_description = value
        except Exception:
            pass
        try:
            if hasattr(self, 'decider_agent') and self.decider_agent:
                self.decider_agent.scene_description = value
        except Exception:
            pass
        try:
            if hasattr(self, 'narrator') and self.narrator:
                # Some narrators track scene text for framing helpers
                self.narrator.scene_description = value
        except Exception:
            pass

    def set_narrative_context_manager(self, narrative_context_manager) -> None:
        """Inject a NarrativeContextManager into child agents so the Interpreter has full context."""
        try:
            if hasattr(self, 'interpreter_agent') and self.interpreter_agent:
                self.interpreter_agent.narrative_context_manager = narrative_context_manager
        except Exception:
            pass
        try:
            if hasattr(self, 'narrator') and self.narrator:
                self.narrator.narrative_context_manager = narrative_context_manager
        except Exception:
            pass
