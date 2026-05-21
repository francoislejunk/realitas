"""
Scene Management System for UTAS Simulation

Provides scene completion detection, graceful transitions, and dynamic scene flow management.
"""

from typing import Dict, List, Optional, Tuple, Any
from enum import Enum
import json
from openrouter_config import create_role_client, OpenRouterConfig
from actors import UserActor, NonUserActor
from actor_sheet import StatusType
from color_utils import Color
from json_utils import extract_and_parse_json


class SceneCompletionReason(Enum):
    """Reasons why a scene might be considered complete."""
    GOAL_ACHIEVED = "goal_achieved"
    CONFLICT_RESOLVED = "conflict_resolved"
    NATURAL_CONCLUSION = "natural_conclusion"
    LOCATION_EXHAUSTED = "location_exhausted"
    TIME_PROGRESSION = "time_progression"
    STORY_BEAT_COMPLETE = "story_beat_complete"
    USER_CHOICE = "user_choice"


class SceneTransitionType(Enum):
    """Types of scene transitions available."""
    CONTINUE_CURRENT = "continue_current"
    NEW_LOCATION = "new_location"
    NEW_ACTORS = "new_actors"
    # TIME_SKIP removed - real-time simulation only (sleep/unconscious are handled separately)
    STORY_PROGRESSION = "story_progression"


class SceneManager:
    """Manages scene completion detection and graceful transitions."""
    
    def __init__(self):
        self.client = create_role_client("coordination")
        self.current_scene_data = None
        self.scene_history = []
        self.turn_count = 0
        self.last_evaluation = None
        self.accumulative_narrative = ""
        self.turn_narratives = []
    
    def start_scene_tracking(self, scene_data: Dict[str, Any], scene_description: str):
        """Initialize tracking for a new scene."""
        self.current_scene_data = {
            "scene_data": scene_data,
            "description": scene_description,
            "start_turn": self.turn_count,
            "goals_status": {},
            "conflicts_status": {},
            "narrative_beats": []
        }
        self.turn_count = 0
        self.accumulative_narrative = scene_description
        self.turn_narratives = []
    
    def increment_turn(self):
        """Track turn progression within the scene."""
        self.turn_count += 1
    
    def add_turn_narrative(self, turn_narrative: str):
        """Add a turn's narrative to the accumulative scene story."""
        self.turn_narratives.append(turn_narrative)
        self._update_accumulative_narrative()
    
    def _update_accumulative_narrative(self):
        """Synthesize all turn narratives into a cohesive scene story."""
        if not self.turn_narratives:
            return
        
        # Build prompt for narrative synthesis
        scene_start = self.current_scene_data.get("description", "") if self.current_scene_data else ""
        turns_text = "\n".join([f"Turn {i+1}: {narrative}" for i, narrative in enumerate(self.turn_narratives)])
        
        synthesis_prompt = f"""Synthesize the following scene progression into a cohesive narrative story.
        
**Scene Opening:**
{scene_start}

**Turn-by-Turn Events:**
{turns_text}

Create a flowing narrative that weaves these events together into a single cohesive story. Focus on:
- Maintaining narrative flow and continuity
- Preserving key action outcomes and character developments
- Creating a natural story progression
- Avoiding repetitive phrasing

Return only the synthesized narrative, no additional formatting or commentary."""

        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": synthesis_prompt}],
                temperature=0.4
            )
            
            self.accumulative_narrative = response.choices[0].message.content.strip()
            
        except Exception as e:
            # Fallback: simple concatenation if LLM synthesis fails
            self.accumulative_narrative = f"{scene_start}\n\n" + " ".join(self.turn_narratives)
    
    def get_scene_final_narrative(self) -> str:
        """Get the complete scene narrative for evaluation purposes."""
        return self.accumulative_narrative
    
    def evaluate_scene_completion(self, user_actor: UserActor, current_opponent: Optional[Any], 
                                recent_actions: List[str], scene_description: str) -> Dict[str, Any]:
        """
        Evaluate whether the current scene should end and transition to a new one.
        
        Args:
            user_actor: The user's character
            current_opponent: Current NUA/INUA opponent (if any)
            recent_actions: List of recent user actions for context
            scene_description: Current scene description
            
        Returns:
            Dictionary with completion evaluation results
        """
        prompt = self._build_scene_evaluation_prompt(
            user_actor, current_opponent, recent_actions, scene_description
        )
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            response_text = response.choices[0].message.content
            evaluation_data = extract_and_parse_json(response_text)
            
            if evaluation_data:
                self.last_evaluation = evaluation_data
                return evaluation_data
            else:
                return self._create_default_evaluation()
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Scene evaluation failed: {e}{Color.RESET}")
            return self._create_default_evaluation()
    
    def _build_scene_evaluation_prompt(self, user_actor: UserActor, current_opponent: Optional[Any], 
                                     recent_actions: List[str], scene_description: str) -> str:
        """Build the LLM prompt for scene completion evaluation."""
        
        opponent_info = "None (narrative scene)"
        if current_opponent:
            opponent_info = f"{current_opponent.sheet.name} ({current_opponent.sheet.occupation})"
        
        recent_actions_text = "\n".join([f"- {action}" for action in recent_actions[-5:]])
        
        return f"""You are a scene completion evaluator for a narrative simulation. Analyze whether the current scene should continue or transition to a new scene.

**Scene Narrative (Complete Story So Far):**
{self.get_scene_final_narrative()}

**User Actor:**
- Name: {user_actor.name}
- Goals: {', '.join(user_actor.sheet.goals)}
- Current Stamina: {user_actor.sheet.statuses[StatusType.STAMINA].value}
- Current Spirit: {user_actor.sheet.statuses[StatusType.SPIRIT].value}

**Current Opponent:** {opponent_info}

**Turn Count in Scene:** {self.turn_count}

**Evaluation Criteria:**
Determine if the scene should end based on:
1. **Goal Achievement**: Has the user actor achieved their scene goal?
2. **Conflict Resolution**: Has the main conflict been resolved (won/lost/negotiated)?
3. **Pursuit/Chase Outcomes**: Has a chase ended (target escaped, lost, caught, or abandoned)?
4. **Natural Conclusion**: Has the scene reached a natural stopping point?
5. **Location Exhausted**: Has the current location been fully explored/utilized?
6. **Story Progression**: Would transitioning advance the narrative meaningfully?
7. **Turn Count**: Has the scene gone on too long (>15 turns suggests transition)?

**Response Format:**
Provide a JSON object with your evaluation:

{{
    "scene_should_end": true/false,
    "completion_reason": "goal_achieved|conflict_resolved|pursuit_ended|natural_conclusion|location_exhausted|time_progression|story_beat_complete",
    "confidence": 0.0-1.0,
    "justification": "Detailed explanation of why the scene should/shouldn't end",
    "suggested_transition": "continue_current|new_location|new_actors|time_skip|story_progression",
    "transition_description": "Brief description of what the next scene could be",
    "goals_achieved": ["list", "of", "achieved", "goals"],
    "remaining_potential": "What story potential remains in current scene"
}}

**Examples:**
- If user achieved their goal (found the item, defeated opponent, reached destination) → scene_should_end: true
- If conflict is resolved but location has more potential → scene_should_end: false  
- If user was chasing someone and they escaped/were lost → scene_should_end: true, completion_reason: "pursuit_ended"
- If user was being pursued and successfully evaded → scene_should_end: true, completion_reason: "pursuit_ended"
- If chase is ongoing with clear progress/direction → scene_should_end: false
- If scene has been going >12 turns with repetitive actions → scene_should_end: true
- If new story elements could be introduced in same location → scene_should_end: false

Respond with ONLY the JSON object, no additional text."""

    def _create_default_evaluation(self) -> Dict[str, Any]:
        """Create a default evaluation when LLM fails."""
        return {
            "scene_should_end": False,
            "completion_reason": None,
            "confidence": 0.5,
            "justification": "Default evaluation due to LLM failure",
            "suggested_transition": "continue_current",
            "transition_description": "Continue with current scene",
            "goals_achieved": [],
            "remaining_potential": "Unknown - evaluation failed"
        }
    
    def prompt_user_for_transition(self, evaluation: Dict[str, Any]) -> str:
        """
        Present scene transition options to the user and get their choice.
        
        Args:
            evaluation: Scene evaluation results from evaluate_scene_completion
            
        Returns:
            User's choice: 'continue', 'transition', or 'auto'
        """
        print(f"\n{Color.SYSTEM}=== SCENE TRANSITION EVALUATION ==={Color.RESET}")
        print(f"{Color.INFO}📊 Scene Analysis:{Color.RESET}")
        print(f"  • Turn Count: {self.turn_count}")
        print(f"  • Completion Confidence: {evaluation.get('confidence', 0.5):.1%}")
        print(f"  • Evaluation: {evaluation.get('justification', 'No justification available')}")
        
        if evaluation.get('goals_achieved'):
            print(f"  • Goals Achieved: {', '.join(evaluation['goals_achieved'])}")
        
        print(f"  • Remaining Potential: {evaluation.get('remaining_potential', 'Unknown')}")
        
        if evaluation.get('scene_should_end', False):
            print(f"\n{Color.SUCCESS}✅ Recommended: Scene Transition{Color.RESET}")
            print(f"  • Reason: {evaluation.get('completion_reason', 'Unknown')}")
            print(f"  • Suggested: {evaluation.get('transition_description', 'New scene')}")
        else:
            print(f"\n{Color.INFO}🔄 Recommended: Continue Current Scene{Color.RESET}")
        
        print(f"\n{Color.SYSTEM}Choose your preference:{Color.RESET}")
        print(f"  {Color.SUCCESS}[1] Continue current scene{Color.RESET}")
        print(f"  {Color.WARNING}[2] Transition to new scene{Color.RESET}")
        print(f"  {Color.INFO}[3] Auto-decide based on evaluation{Color.RESET}")
        
        while True:
            choice = input(f"\n{Color.SYSTEM}Your choice (1-3): {Color.RESET}").strip()
            
            if choice == '1':
                return 'continue'
            elif choice == '2':
                return 'transition'
            elif choice == '3':
                return 'auto'
            else:
                print(f"{Color.ERROR}Invalid choice. Please enter 1, 2, or 3.{Color.RESET}")
    
    def should_evaluate_scene(self, recent_narrative: str = "") -> bool:
        """
        Determine if it's time to evaluate scene completion.
        
        Args:
            recent_narrative: The most recent action narrative to check for transition triggers
        
        Returns:
            True if scene should be evaluated for completion
        """
        # Regular turn-based evaluation
        if (self.turn_count >= 5 and self.turn_count % 3 == 0) or self.turn_count >= 15:
            return True
        
        # LLM-based immediate transition detection
        if recent_narrative and len(recent_narrative.strip()) > 10:
            return self._analyze_narrative_for_transition_triggers(recent_narrative)
        
        return False
    
    def _analyze_narrative_for_transition_triggers(self, narrative: str) -> bool:
        """
        Use LLM to analyze narrative for scene transition triggers.
        
        Args:
            narrative: The action narrative to analyze
            
        Returns:
            True if the narrative suggests a scene transition should occur
        """
        prompt = f"""
        Analyze this action narrative to determine if it suggests the scene should transition to a new location or situation.

        **NARRATIVE TO ANALYZE:**
        "{narrative}"

        **TRANSITION INDICATORS TO LOOK FOR:**
        - Character successfully escaping/fleeing from current location
        - Character moving to a significantly different location
        - Character completing a major objective that changes the scene context
        - Character entering a new area or environment
        - Situation resolving in a way that naturally leads to a new scene
        - Character departing, leaving, or exiting the current scene

        **NOT TRANSITION INDICATORS:**
        - Minor movements within the same general area
        - Temporary actions that don't change location
        - Failed attempts or partial successes
        - Actions that keep the character in the same scene context

        Respond with a JSON object:
        {{
            "should_transition": true/false,
            "confidence": "high/medium/low",
            "reason": "Brief explanation of why this does/doesn't suggest a transition"
        }}
        """
        
        try:
            from openrouter_config import OpenRouterConfig
            model = OpenRouterConfig.get_model_for_role("decision_making")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            from json_utils import extract_and_parse_json
            analysis = extract_and_parse_json(response_text)
            
            if analysis and isinstance(analysis, dict):
                should_transition = analysis.get('should_transition', False)
                confidence = analysis.get('confidence', 'low')
                reason = analysis.get('reason', 'No reason provided')
                
                print(f"{Color.INFO}🔍 Transition Analysis: {should_transition} (confidence: {confidence}) - {reason}{Color.RESET}")
                
                # Only trigger immediate evaluation for high confidence transitions
                if should_transition and confidence == 'high':
                    print(f"{Color.SUCCESS}✓ High-confidence transition detected - triggering scene evaluation{Color.RESET}")
                    return True
                    
        except Exception as e:
            print(f"{Color.WARNING}Scene transition analysis failed: {e}{Color.RESET}")
        
        return False
    
    def get_scene_statistics(self) -> Dict[str, Any]:
        """Get current scene statistics for display."""
        return {
            "turn_count": self.turn_count,
            "scene_duration": "Long" if self.turn_count > 12 else "Medium" if self.turn_count > 6 else "Short",
            "last_evaluation": self.last_evaluation,
            "scene_active": self.current_scene_data is not None
        }
    
    def record_scene_transition(self, transition_type: str, reason: str, new_scene_data: Dict[str, Any]):
        """Record a scene transition in the history."""
        if self.current_scene_data:
            transition_record = {
                "old_scene": self.current_scene_data,
                "transition_type": transition_type,
                "reason": reason,
                "turn_count": self.turn_count,
                "new_scene_preview": new_scene_data.get('scene_elements', {}).get('setting', 'Unknown')
            }
            self.scene_history.append(transition_record)
        
        self.start_scene_tracking(new_scene_data, new_scene_data.get('description', ''))
    
    def transition_scene(self, proactor: UserActor, reactor: Optional[Any], evaluation: Dict[str, Any]) -> Tuple[str, UserActor, Optional[Any]]:
        """
        Execute scene transition with narrative generation and dynamic setup.
        
        Args:
            proactor: The user's character
            reactor: Current opponent/NPC (if any)
            evaluation: Scene evaluation results
            
        Returns:
            Tuple of (new_scene_description, updated_proactor, new_reactor_or_none)
        """
        from agents.narrator_agent import NarratorAgent
        from agents.creator_agent import CreatorAgent
        from dynamic_actor_system import DynamicActorSystem
        import random
        
        # Create narrator for transition narrative
        narrator = NarratorAgent()
        
        # Generate transition narrative based on evaluation
        transition_type = evaluation.get('suggested_transition', 'new_location')
        completion_reason = evaluation.get('completion_reason', 'natural_conclusion')
        
        print(f"\n{Color.SUCCESS}🎬 SCENE TRANSITION{Color.RESET}")
        print(f"  Reason: {completion_reason}")
        print(f"  Type: {transition_type}")
        
        # Generate transition narrative with Four-Mode Narrative Loop framing
        framing_guidance = None
        try:
            turn_data = {
                'user_input': 'Scene Transition',
                'continuity_check': {'judgment': 'Possible'},
                'scene_description': self.get_scene_final_narrative(),
                'outcome_data': {
                    'transition_type': evaluation.get('suggested_transition'),
                    'completion_reason': evaluation.get('completion_reason')
                }
            }
            framing_guidance = narrator.narrative_loop.process_turn(turn_data)
        except Exception:
            framing_guidance = None

        transition_narrative = narrator.generate_scene_transition_narrative(
            proactor, reactor, evaluation, self.get_scene_final_narrative(), framing_guidance=framing_guidance
        )
        
        print(f"\n{Color.NARRATIVE}{transition_narrative}{Color.RESET}")
        
        # Context-aware scene setup based on transition narrative
        new_reactor = None
        
        # Use LLM to analyze transition context for character continuity
        context_analysis = self._analyze_transition_context(transition_narrative, proactor, reactor)
        
        if context_analysis.get('preserve_reactor', False) and reactor:
            new_reactor = reactor
            print(f"\n{Color.INFO}🎭 {context_analysis.get('continuity_reason', 'Continuing with current character')}{Color.RESET}")
        else:
            # Use LLM decision for NPC creation
            should_create_npc = (
                transition_type in ['new_location', 'story_progression'] and 
                context_analysis.get('needs_new_npc', False)
            )
            
            if should_create_npc:
                try:
                    print(f"\n{Color.SYSTEM}🎭 Setting up new scene dynamics...{Color.RESET}")
                    
                    # Create dynamic actor system for NPC generation
                    from logbook.utas_logger import UTASLogger
                    logger = UTASLogger()
                    creator = CreatorAgent(logger)
                    dynamic_system = DynamicActorSystem(creator)
                    
                    # Generate contextual NPC based on transition narrative
                    npc_context = f"Scene: {transition_narrative}. Create an appropriate character for this new location/situation."
                    potential_npc = dynamic_system.creator.create_dynamic_actor(
                        {"name": "Scene Character", "context": npc_context}, 
                        transition_narrative
                    )
                    
                    if potential_npc:
                        new_reactor = potential_npc
                        print(f"  {Color.SUCCESS}✓ New character introduced: {potential_npc.sheet.name}{Color.RESET}")
                        
                        # Establish sympathy if it's a NUA
                        if hasattr(potential_npc, 'is_inanimate') and not potential_npc.is_inanimate:
                            from llm_agents.sympathy_initialization import assign_initial_sympathies
                            assign_initial_sympathies([proactor, potential_npc])
                            print(f"  {Color.INFO}Sympathy relationship established{Color.RESET}")
                    else:
                        print(f"  {Color.WARNING}No new character created for this scene{Color.RESET}")
                        
                except Exception as e:
                    print(f"  {Color.WARNING}Could not create scene character: {str(e)}{Color.RESET}")
        
        # Generate scene goals/objectives using LLM analysis
        objectives = context_analysis.get('scene_objectives', 'New scene objectives available through exploration and interaction')
        print(f"\n{Color.INFO}🎯 {objectives}{Color.RESET}")
        
        # Record the transition
        self.record_scene_transition(
            transition_type, 
            completion_reason, 
            {"description": transition_narrative, "new_npc": new_reactor.sheet.name if new_reactor else None}
        )
        
        # Return new scene context with potential new reactor
        return transition_narrative, proactor, new_reactor
    
    def _analyze_transition_context(self, transition_narrative: str, proactor: UserActor, reactor: Optional[Any]) -> Dict[str, Any]:
        """
        Use LLM to analyze transition context for character continuity and scene setup decisions.
        
        Args:
            transition_narrative: The generated transition narrative
            proactor: The user's character
            reactor: Current opponent/NPC (if any)
            
        Returns:
            Dictionary with analysis results for scene setup
        """
        reactor_name = reactor.sheet.name if reactor else "none"
        
        prompt = f"""
        Analyze this scene transition for character continuity and setup decisions.
        
        **TRANSITION NARRATIVE:**
        {transition_narrative}
        
        **CURRENT CHARACTERS:**
        - Proactor: {proactor.sheet.name}
        - Reactor: {reactor_name}
        
        **ANALYSIS QUESTIONS:**
        1. Should the current reactor continue in the new scene? (e.g., being taken somewhere, following, captured)
        2. Does this transition suggest new NPCs are needed? (e.g., entering populated areas, new locations with inhabitants)
        3. What are the logical objectives/goals for this new scene?
        
        **RESPONSE FORMAT:**
        Provide a JSON object with your analysis:
        {{
            "preserve_reactor": true/false,
            "continuity_reason": "Brief explanation of why reactor should/shouldn't continue",
            "needs_new_npc": true/false,
            "npc_reasoning": "Why new NPCs are/aren't needed",
            "scene_objectives": "Specific objectives for this new scene context"
        }}
        
        **EXAMPLES:**
        - Hideout/questioning: preserve_reactor=true, needs_new_npc=false, objectives="Interrogate captive, extract information"
        - Market entrance: preserve_reactor=false, needs_new_npc=true, objectives="Explore market, find merchants, gather information"
        - Private escape: preserve_reactor=false, needs_new_npc=false, objectives="Plan next move, rest and recover"
        """
        
        try:
            model = OpenRouterConfig.get_model_for_role("decision_making")
            response = self.client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract and parse JSON
            from json_utils import extract_and_parse_json
            analysis = extract_and_parse_json(response_text)
            
            if analysis and isinstance(analysis, dict):
                return analysis
                
        except Exception as e:
            print(f"  {Color.WARNING}LLM context analysis failed: {str(e)}{Color.RESET}")
        
        # Fallback analysis
        return {
            "preserve_reactor": reactor is not None,
            "continuity_reason": "Continuing with current character by default",
            "needs_new_npc": False,
            "npc_reasoning": "No new NPCs needed by default",
            "scene_objectives": "New scene objectives available through exploration and interaction"
        }
    
    def get_transition_context(self) -> Dict[str, Any]:
        """Get context about the last scene transition for narrative continuity."""
        if not self.scene_history:
            return {}
        
        last_transition = self.scene_history[-1]
        return {
            "previous_scene_setting": last_transition["old_scene"]["scene_data"].get("scene_elements", {}).get("setting", ""),
            "transition_reason": last_transition["reason"],
            "transition_type": last_transition["transition_type"],
            "turn_count": last_transition["turn_count"]
        }
