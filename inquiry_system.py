
import random
from typing import Dict, Any, Tuple, Optional
from actor_sheet import ActorSheet, SFactorType, StatusType
from narrative_utils import get_narrative_descriptor
from numeric_utils import extract_numeric_value

class InquiryCalculator:
    """Handles inquiry success calculations using the UTAS formula."""
    
    def __init__(self):
        self.logger = None

    def _get_interpreter(self):
        try:
            from agents.interpreter_agent import InterpreterAgent
            return InterpreterAgent(logger=None, scene_description="", tracker_agent=None, actor_manager=None, key_memories_system=None, rag_system=None)
        except Exception:
            return None

    def _strict_call(self, fn, retries: int = 3):
        last = None
        for _i in range(max(1, int(retries))):
            try:
                out = fn()
                if out is None:
                    raise ValueError("Interpreter returned None")
                return out
            except Exception as e:
                last = e
        raise last if last else RuntimeError("Interpreter call failed")
    
    def calculate_inquiry_success(self, actor: 'Actor', inquiry: str, scene_context: str = "") -> Dict[str, Any]:
        """
        Calculate fallible action success using: Relevant S-trait + relevant skill + endowment + serendipity roll - Stressor
        
        Returns:
            Dict containing:
            - success_level: int (1, 2, 3+)
            - s_trait_type: SFactorType (the S-trait used)
            - s_trait_value: int
            - skill_value: int
            - skill_name: str
            - endowment_value: int
            - endowment_name: str
            - serendipity_roll: int
            - serendipity_breakdown: str
            - stressor: int
            - total_score: int
            - breakdown: str (detailed calculation)
            - self_effects_applied: list (effects applied due to failure)
        """
        
        # Determine the most appropriate S-trait for this fallible action
        s_trait_type = self._determine_relevant_s_trait(inquiry, scene_context)
        s_trait_value = actor.sheet.s_factors.get_factor(s_trait_type)
        
        skill_name, skill_value = self._determine_relevant_skill(actor, inquiry)
        
        endowment_name, endowment_value = self._determine_relevant_endowment(actor, inquiry)
        
        serendipity_roll, serendipity_breakdown = self._roll_serendipity()
        
        stressor = self._determine_inquiry_stressor(inquiry, scene_context)
        
        from unified_formula import calculate_unified_result
        
        unified_result = calculate_unified_result(
            actor=actor,
            s_trait=s_trait_type,
            skill_name=skill_name,
            target_actor=None,
            shift_polarity='Subtractive',
            targeted_status=None,
            supplement_val=0,
            serendipity_override=serendipity_roll,
            stress_level_override=stressor + 3
        )
        
        total_score = unified_result['final_result']
        
        # Determine success level based on total score
        if total_score <= 0:
            if total_score == 0:
                success_level = 0  # Failure
            else:
                success_level = -1  # Catastrophic failure/backfire
        else:
            success_level = total_score  # Positive success levels
        
        breakdown = self._create_calculation_breakdown(
            s_trait_value, skill_name, skill_value, endowment_name, endowment_value,
            serendipity_roll, serendipity_breakdown, stressor, total_score, s_trait_type, success_level
        )
        
        # Apply self-effects for backfire failures (success_level < 0)
        self_effects_applied = []
        if success_level < 0:
            self_effects_applied = self._apply_failure_self_effects(actor, success_level, inquiry)
        
        return {
            'success_level': success_level,
            's_trait_type': s_trait_type,
            's_trait_value': s_trait_value,
            'skill_value': skill_value,
            'skill_name': skill_name,
            'endowment_value': endowment_value,
            'endowment_name': endowment_name,
            'serendipity_roll': serendipity_roll,
            'serendipity_breakdown': serendipity_breakdown,
            'stressor': stressor,
            'total_score': total_score,
            'breakdown': breakdown,
            'self_effects_applied': self_effects_applied
        }
    
    def _determine_relevant_skill(self, actor: 'Actor', inquiry: str) -> Tuple[str, int]:
        """
        Determine the most relevant skill for the inquiry using LLM analysis.
        Falls back to heuristic skill selection if LLM fails.
        """
        interpreter = self._get_interpreter()
        if interpreter is None:
            raise RuntimeError("InterpreterAgent unavailable")

        skill_result = self._strict_call(lambda: interpreter.determine_skill_for_action(inquiry, list(actor.sheet.skills.keys())), retries=3)
        if isinstance(skill_result, dict) and 'skill' in skill_result:
            skill_name = skill_result['skill']
            if skill_name != "No relevant skill" and skill_name in actor.sheet.skills:
                skill_value = actor.sheet.skills.get(skill_name, 0)
                return skill_name, skill_value

        raise ValueError("Interpreter did not return a usable skill")
    
    def _heuristic_skill_selection(self, actor: 'Actor', inquiry: str) -> Tuple[str, int]:
        """
        Dynamic skill selection that uses the actor's highest available skill.
        This avoids hardcoded patterns and works with any skill set.
        """
        # Check if actor has any skills at all
        if not actor.sheet.skills or all(value == 0 for value in actor.sheet.skills.values()):
            return "No relevant skill", 0
        
        # Simply use the actor's highest skill - this is more flexible and works
        # with any skill names without requiring hardcoded pattern matching
        best_skill = max(actor.sheet.skills.keys(), key=lambda k: actor.sheet.skills[k])
        best_value = actor.sheet.skills[best_skill]
        
        if best_value > 0:
            return best_skill, best_value
        else:
            return "No relevant skill", 0
    
    def _determine_relevant_endowment(self, actor: 'Actor', inquiry: str) -> Tuple[str, int]:
        """
        Determine the most relevant endowment for the inquiry using LLM analysis.
        Falls back to highest endowment if LLM fails.
        """
        interpreter = self._get_interpreter()
        if interpreter is None:
            raise RuntimeError("InterpreterAgent unavailable")

        available = list(actor.sheet.endowments.keys()) if actor.sheet.endowments else []
        endowment_result = self._strict_call(lambda: interpreter.determine_best_endowment(inquiry, available), retries=3)
        if isinstance(endowment_result, dict) and 'endowment' in endowment_result:
            endowment_name = endowment_result['endowment']
            endowment_value = actor.sheet.endowments.get(endowment_name, 0) if actor.sheet.endowments else 0
            return endowment_name, endowment_value

        raise ValueError("Interpreter did not return a usable endowment")
    
    def _determine_relevant_s_trait(self, inquiry: str, scene_context: str = "") -> SFactorType:
        """
        Determine the most appropriate S-trait for the fallible action using LLM analysis.
        Falls back to heuristic analysis if LLM is unavailable.
        """
        interpreter = self._get_interpreter()
        if interpreter is None:
            raise RuntimeError("InterpreterAgent unavailable")

        s_trait_result = self._strict_call(lambda: interpreter.determine_s_trait_for_action(inquiry, scene_context), retries=3)
        if isinstance(s_trait_result, dict) and 's_trait' in s_trait_result:
            return s_trait_result['s_trait']

        raise ValueError("Interpreter did not return a usable s_trait")
    
    def _heuristic_s_trait_selection(self, inquiry: str, scene_context: str = "") -> SFactorType:
        """
        Heuristic S-trait selection using natural language processing.
        Analyzes semantic patterns without hard-coded word lists.
        """
        inquiry_lower = inquiry.lower()
        
        # Use simple pattern matching for basic categorization
        # This is a minimal fallback - the LLM should handle most cases
        
        # Physical action patterns
        if any(pattern in inquiry_lower for pattern in ['climb', 'lift', 'break', 'force', 'strength']):
            return SFactorType.STURDINESS
            
        # Mental/analytical patterns  
        if any(pattern in inquiry_lower for pattern in ['solve', 'analyze', 'figure', 'calculate', 'think', 'remember', 'recall', 'password', 'code']):
            return SFactorType.SMARTS
            
        # Social interaction patterns
        if any(pattern in inquiry_lower for pattern in ['convince', 'persuade', 'talk', 'negotiate', 'charm']):
            return SFactorType.SOCIABILITY
            
        # Speed/agility patterns
        if any(pattern in inquiry_lower for pattern in ['dodge', 'quick', 'fast', 'react', 'escape']):
            return SFactorType.SWIFTNESS
            
        # Default to SHADOW for perception-based actions and unknowns
        return SFactorType.SHADOW
    
    def _roll_serendipity(self) -> Tuple[int, str]:
        """Roll serendipity: 2D6-7 (range -5 to +5)."""
        die1 = random.randint(1, 6)
        die2 = random.randint(1, 6)
        total = die1 + die2
        serendipity = total - 7
        
        breakdown = f"2D6-7 -> {die1}+{die2}-7 = {serendipity:+d}"
        return serendipity, breakdown
    
    def _determine_inquiry_stressor(self, inquiry: str, scene_context: str = "") -> int:
        """
        Determine the stressor (difficulty) of the inquiry using LLM analysis.
        Falls back to base difficulty if LLM fails.
        """
        interpreter = self._get_interpreter()
        if interpreter is None:
            raise RuntimeError("InterpreterAgent unavailable")

        difficulty_result = self._strict_call(lambda: interpreter.determine_action_difficulty(inquiry, scene_context), retries=3)
        if isinstance(difficulty_result, dict) and 'difficulty' in difficulty_result:
            try:
                return max(1, min(5, int(difficulty_result['difficulty'])))
            except Exception:
                pass

        raise ValueError("Interpreter did not return a usable difficulty")
    
    def _create_calculation_breakdown(self, s_trait_value: int, skill_name: str, skill_value: int,
                                    endowment_name: str, endowment_value: int, serendipity_roll: int,
                                    serendipity_breakdown: str, stressor: int, total_score: int, s_trait_type: SFactorType, success_level: int) -> str:
        """Create a detailed breakdown of the calculation with clean visual formatting."""
        
        breakdown_parts = []
        
        s_trait_desc = get_narrative_descriptor(s_trait_value)
        s_trait_name = s_trait_type.name.title()
        breakdown_parts.append(f"{s_trait_name} ({s_trait_value})")
        
        if skill_value > 0:
            skill_desc = get_narrative_descriptor(skill_value)
            breakdown_parts.append(f"{skill_name.title()} ({skill_value})")
        else:
            breakdown_parts.append(f"No relevant skill (0)")
        
        if endowment_value > 0:
            endowment_desc = get_narrative_descriptor(endowment_value)
            breakdown_parts.append(f"{endowment_name.title()} ({endowment_value})")
        else:
            breakdown_parts.append(f"No relevant endowment (0)")
        
        breakdown_parts.append(f"Serendipity ({serendipity_roll})")
        
        stressor_desc = get_narrative_descriptor(stressor)
        breakdown_parts.append(f"Action Stressor ({stressor})")
        
        # Keep the original formula structure but with cleaner visual formatting
        positive_parts = breakdown_parts[:-1]  # All except stressor
        negative_part = breakdown_parts[-1]    # Stressor
        
        # Use existing narrative descriptor system for positive success levels
        if success_level > 0:
            success_desc = get_narrative_descriptor(min(success_level, 5))
        elif success_level == 0:
            success_desc = "Failure"
        else:
            success_desc = "Catastrophic Failure"
        
        # Format with emoji headers and success level
        calculation = " + ".join(positive_parts) + f" - {negative_part} = {total_score}"
        
        return f"📊 DETAILED CALCULATIONS\n{calculation}\nSuccess Level: {success_level} ({success_desc} Success)"
    
    def _apply_failure_self_effects(self, actor: 'Actor', success_level: int, inquiry: str) -> list:
        """
        Apply self-effects when single-actor actions fail.
        Based on UTAS design philosophy that failed actions have consequences.
        
        Args:
            actor: The actor who failed the action
            success_level: The failure level (0 = failure, -1 = catastrophic failure)
            inquiry: The original action attempted
            
        Returns:
            List of applied self-effects with details
        """
        from severity_validation import SeverityValidator
        from exchange_system import round_half_away_from_zero
        from narrative_utils import get_status_descriptor
        
        applied_effects = []
        
        # Simple rule: backfire (success_level < 0) = -1 shift to stamina or spirit
        condition = "Backfire"
        target_status = self._determine_failure_status_target(inquiry)
        final_shift = -1  # Simple -1 shift for all backfires
        
        # Apply the effect
        try:
            original_status = actor.sheet.statuses[target_status].value
            original_status_desc = get_status_descriptor(original_status)
            
            # Apply the status change
            actor.sheet.update_status(target_status, final_shift, reason=condition)
            updated_status = actor.sheet.statuses[target_status].value
            updated_status_desc = get_status_descriptor(updated_status)
            
            applied_effects.append({
                'actor_name': actor.sheet.name,
                'trigger': condition,
                'status_name': target_status.name,
                'original_status': original_status,
                'updated_status': updated_status,
                'shift_amount': final_shift,
                'shift_type': 'Temporary',
                'description': f"{condition}: {target_status.name} {original_status_desc} → {updated_status_desc}"
            })
            
            print(f"\n🔥 BACKFIRE CONSEQUENCE APPLIED")
            print(f"   {condition}: {actor.sheet.name}'s {target_status.name} {original_status} → {updated_status} ({final_shift:+d})")
            
        except Exception as e:
            print(f"Error applying failure self-effect: {e}")
        
        return applied_effects
    
    def _determine_failure_status_target(self, inquiry: str) -> StatusType:
        """
        Determine which status should be affected by action failure.
        Based on the type of action attempted.
        """
        inquiry_lower = inquiry.lower()
        
        # Physical actions typically affect STAMINA
        if any(pattern in inquiry_lower for pattern in ['climb', 'jump', 'run', 'lift', 'break', 'force', 'physical']):
            return StatusType.STAMINA
            
        # Mental actions typically affect SPIRIT  
        if any(pattern in inquiry_lower for pattern in ['solve', 'analyze', 'figure', 'calculate', 'think', 'remember', 'focus']):
            return StatusType.SPIRIT
            
        # Social actions typically affect SPIRIT (confidence/morale)
        if any(pattern in inquiry_lower for pattern in ['convince', 'persuade', 'talk', 'negotiate', 'charm']):
            return StatusType.SPIRIT
            
        # Stealth/perception actions typically affect SPIRIT (focus/concentration)
        if any(pattern in inquiry_lower for pattern in ['sneak', 'hide', 'look', 'search', 'listen', 'watch']):
            return StatusType.SPIRIT
            
        # Default to STAMINA for general physical exertion
        return StatusType.STAMINA


class InquiryNarrativeGenerator:
    """Generates narrative responses based on inquiry success levels."""
    
    def __init__(self, narrator_agent):
        self.narrator = narrator_agent

    def _spatial_facts_block(self, session_id: Optional[str] = None) -> str:
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                return f"""

AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):
{sf.strip()}
""".rstrip()
        except Exception:
            return ""
    
    def generate_narrative_response(self, inquiry: str, success_data: Dict[str, Any], 
                                  scene_description: str, proactor: 'Actor', reactor: 'Actor', time_context: Optional[Dict[str, Any]] = None,
                                  framing_guidance: Optional[Dict[str, Any]] = None,
                                  session_id: Optional[str] = None) -> str:
        """
        Generate narrative response based on success level and action type.
        
        Success levels:
        1 = minimal success (struggle/difficulty)
        2 = moderate success (partial achievement)  
        3+ = high success (clear achievement)
        """
        
        success_level = success_data['success_level']
        
        # Detect if this is situation overcoming vs information gathering
        action_type = self._detect_action_type(inquiry)
        
        if success_level <= 1:
            return self._generate_minimal_response(inquiry, scene_description, proactor, reactor, time_context, framing_guidance, action_type, session_id)
        elif success_level == 2:
            return self._generate_moderate_response(inquiry, scene_description, proactor, reactor, time_context, framing_guidance, action_type, session_id)
        else:
            return self._generate_detailed_response(inquiry, scene_description, proactor, reactor, time_context, framing_guidance, action_type, session_id)
    
    def _detect_action_type(self, inquiry: str) -> str:
        """Detect if inquiry is information gathering or situation overcoming."""
        return 'mental'
    
    def _generate_minimal_response(self, inquiry: str, scene_description: str, 
                                 proactor: 'Actor', reactor: 'Actor', time_context: Optional[Dict[str, Any]] = None,
                                 framing_guidance: Optional[Dict[str, Any]] = None, action_type: str = 'mental',
                                 session_id: Optional[str] = None) -> str:
        """Generate minimal information response (success level 1)."""

        spatial_facts_section = self._spatial_facts_block(session_id=session_id)
        if spatial_facts_section:
            spatial_facts_section = f"\n\n{spatial_facts_section}"
        
        if action_type == 'physical':
            prompt = f"""
        You are narrating a UTAS simulation action attempt with MINIMAL SUCCESS (Level 1).
        
        **ACTION SUCCESS LEVEL: 1 (Struggle/Difficulty)**
        
        **GUIDELINES FOR LEVEL 1 ACTION RESPONSES:**
        - Character struggles with the action but makes minimal progress
        - Show difficulty, strain, or partial failure
        - Use phrases like "you struggle to...", "with great effort...", "barely manage to..."
        - Keep responses brief (1-2 sentences)
        - Show the character attempting but facing significant challenges
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **ACTION ATTEMPT:** "{inquiry}"
        
        **EXAMPLE LEVEL 1 ACTION RESPONSES:**
        - "You struggle against the rough stone, your fingers barely finding purchase as you attempt to climb."
        - "With great effort, you manage to move the heavy object only slightly, sweat beading on your forehead."
        - "You fumble with the lock mechanism, your hands shaking as you make little progress."
        
        Generate a single narrative showing {proactor.sheet.name} attempting the action with minimal success. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators.
        """
        else:
            prompt = f"""
        You are narrating a UTAS simulation inquiry response with MINIMAL SUCCESS (Level 1).
        
        **INQUIRY SUCCESS LEVEL: 1 (Almost No Information)**
        
        **GUIDELINES FOR LEVEL 1 RESPONSES:**
        - Provide almost no useful information
        - Character struggles to perceive or understand
        - Vague, uncertain observations only
        - Use phrases like "you think you might...", "perhaps...", "it's hard to tell..."
        - Keep responses very brief (1-2 sentences)
        - Never give direct answers or clear information
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **INQUIRY:** "{inquiry}"
        
        **EXAMPLE LEVEL 1 RESPONSES:**
        - "You strain to make out details, but the shadows seem to shift and blur your vision."
        - "Something catches your attention briefly, but you can't quite focus on what it might be."
        - "You think you sense movement, but it could just be your imagination."
        
        Generate a Level 1 (minimal) narrative response. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators. Respond with ONLY the narrative text.
        """
        
        response = self.narrator._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
        
        if not response:
            return f"{proactor.sheet.name} strains to perceive more, but the details remain frustratingly unclear."
        
        return response.strip()
    
    def _generate_moderate_response(self, inquiry: str, scene_description: str,
                                  proactor: 'Actor', reactor: 'Actor', time_context: Optional[Dict[str, Any]] = None,
                                  framing_guidance: Optional[Dict[str, Any]] = None, action_type: str = 'mental',
                                  session_id: Optional[str] = None) -> str:
        """Generate moderate information response (success level 2)."""

        spatial_facts_section = self._spatial_facts_block(session_id=session_id)
        if spatial_facts_section:
            spatial_facts_section = f"\n\n{spatial_facts_section}"
        
        if action_type == 'physical':
            prompt = f"""
        You are narrating a UTAS simulation action attempt with MODERATE SUCCESS (Level 2).
        
        **ACTION SUCCESS LEVEL: 2 (Partial Success)**
        
        **GUIDELINES FOR LEVEL 2 ACTION RESPONSES:**
        - Character makes noticeable progress but faces some challenges
        - Show partial success with minor setbacks or complications
        - Use phrases like "you manage to...", "with some effort...", "you succeed but..."
        - Moderate length responses (2-3 sentences)
        - Show progress while hinting at remaining difficulties
        - Character achieves part of their goal
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **ACTION ATTEMPT:** "{inquiry}"
        
        **EXAMPLE LEVEL 2 ACTION RESPONSES:**
        - "You manage to climb halfway up the wall before your grip starts to slip, forcing you to find a more secure handhold."
        - "With some effort, you successfully move the heavy object several feet, though it takes more strength than expected."
        - "You pick the lock mechanism with moderate success, hearing several clicks, but one final tumbler remains stubborn."
        
        Generate a single narrative showing {proactor.sheet.name} attempting the action with moderate success. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators.
        """
        else:
            prompt = f"""
        You are narrating a UTAS simulation inquiry response with MODERATE SUCCESS (Level 2).
        
        **INQUIRY SUCCESS LEVEL: 2 (Some Information)**
        
        **GUIDELINES FOR LEVEL 2 RESPONSES:**
        - Provide some useful but incomplete information
        - Character perceives basic details but misses nuances
        - Mix certainty with uncertainty
        - Use phrases like "you notice...", "it appears...", "you can make out..."
        - Moderate length responses (2-3 sentences)
        - Give partial answers, leave some mystery
        - Never reveal intentions or complete picture
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **INQUIRY:** "{inquiry}"
        
        **EXAMPLE LEVEL 2 RESPONSES:**
        - "You can make out three figures in the clearing, each carrying what appears to be weapons, though their exact nature is unclear from this distance."
        - "The room seems to have stone walls with several doorways, but the lighting makes it difficult to see what lies beyond them."
        - "You notice the person's posture is tense and their hand rests near their belt, suggesting they might be prepared for something."
        
        Generate a Level 2 (moderate) narrative response. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators. Respond with ONLY the narrative text.
        """
        
        response = self.narrator._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
        
        if not response:
            return f"{proactor.sheet.name} observes the scene, picking up some details but missing the complete picture."
        
        return response.strip()
    
    def _generate_detailed_response(self, inquiry: str, scene_description: str,
                                  proactor: 'Actor', reactor: 'Actor', time_context: Optional[Dict[str, Any]] = None,
                                  framing_guidance: Optional[Dict[str, Any]] = None, action_type: str = 'mental',
                                  session_id: Optional[str] = None) -> str:
        """Generate detailed information response (success level 3+)."""

        spatial_facts_section = self._spatial_facts_block(session_id=session_id)
        if spatial_facts_section:
            spatial_facts_section = f"\n\n{spatial_facts_section}"
        
        if action_type == 'physical':
            prompt = f"""
        You are narrating a UTAS simulation action attempt with HIGH SUCCESS (Level 3+).
        
        **ACTION SUCCESS LEVEL: 3+ (Complete Success)**
        
        **GUIDELINES FOR LEVEL 3+ ACTION RESPONSES:**
        - Character achieves their goal with impressive skill and efficiency
        - Show mastery, grace, and confidence in execution
        - Use phrases like "you expertly...", "with practiced ease...", "flawlessly..."
        - Longer responses (3-4 sentences) with vivid action details
        - Character overcomes challenges with style and competence
        - May include beneficial side effects or bonus outcomes
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **ACTION ATTEMPT:** "{inquiry}"
        
        **EXAMPLE LEVEL 3+ ACTION RESPONSES:**
        - "You scale the wall with practiced ease, your fingers finding perfect handholds as you flow upward like water, reaching the top in moments with barely a sound. Your efficient movement conserves energy while your confident grip never wavers, leaving you perfectly positioned and ready for whatever comes next."
        - "With expert technique, you lift and maneuver the heavy object exactly where you need it, your body mechanics flawless as you leverage your strength efficiently. The task that might challenge others becomes almost effortless under your skilled approach, completed with time and energy to spare."
        
        Generate a single narrative showing {proactor.sheet.name} attempting the action with complete success. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators.
        """
        else:
            prompt = f"""
        You are narrating a UTAS simulation inquiry response with HIGH SUCCESS (Level 3+).
        
        **INQUIRY SUCCESS LEVEL: 3+ (Maximum Possible Information)**
        
        **GUIDELINES FOR LEVEL 3+ RESPONSES:**
        - Provide all possible information that could be perceived through the senses
        - Rich, detailed observations with great specificity
        - Character perceives subtle details and nuances
        - CRITICAL: Always speak in "possibilities" and observations, NEVER direct facts
        - NEVER reveal direct intentions, thoughts, or motivations
        - Use phrases like "suggests...", "indicates...", "gives the impression...", "appears to be..."
        - Longer responses (3-4 sentences) with vivid sensory details
        - Leave interpretation up to the reader - provide evidence, not conclusions
        
        **CURRENT SCENE:** {scene_description}{spatial_facts_section}
        **CHARACTER:** {proactor.sheet.name}
        **INQUIRY:** "{inquiry}"
        
        **EXAMPLE LEVEL 3+ RESPONSES:**
        - "Your keen observation reveals three individuals positioned strategically around the clearing - one crouched behind the large oak with what appears to be a crossbow, another standing near the path's bend wielding a curved blade that catches the moonlight, and a third figure partially concealed by brush whose stance suggests they're holding a staff or club. Their coordinated positioning and the way they keep glancing at each other suggests this might be a planned arrangement."
        - "The chamber's details become crystal clear: rough-hewn stone walls bearing tool marks that indicate hasty construction, three doorways - north, east, and west - with the eastern passage showing signs of recent foot traffic in the dust, while flickering torchlight reveals scratches on the northern door's frame that could indicate frequent use or perhaps struggle."
        
        Generate a Level 3+ (detailed) narrative response. Provide ONLY ONE narrative option, no alternatives or "(OR)" separators. Respond with ONLY the narrative text.
        """
        
        response = self.narrator._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
        
        if not response:
            return f"{proactor.sheet.name} takes in every detail of the scene, their heightened perception revealing subtle nuances and possibilities that paint a comprehensive picture of the situation."
        
        return response.strip()
