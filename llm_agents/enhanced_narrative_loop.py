"""
Enhanced Four-Mode Narrative Loop - Reality Doesn't Push Edition

Core Philosophy:
- Reality is NOT sentient - it doesn't push you toward anything
- The world responds to YOUR intent, not the other way around
- Mode transitions happen FROM user behavior, not TO user behavior
- Diegetic momentum comes from fiction state, not arbitrary timers
- Task vs Goal distinction: Tasks are immediate/dynamic, Goals are life-defining/resistant

Design Principles:
1. **No Push**: The system never forces direction. It observes and responds.
2. **User Intent Interpreter**: Reads what the user WANTS from their actions
3. **Context Awareness**: Tracks spatial, temporal, social, and environmental state
4. **Invisible Scaffolding**: Story beats guide narration, never shown to user
5. **Conflict-Optional**: Kishōtenketsu twists for variety without forcing combat
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass, field
import json

# Import existing systems
from .diegetic_momentum_tracker import DiegeticMomentumTracker, MomentumFactor
from goal_task_system import GoalTaskManager, TaskPriority, TaskCategory, GoalImportance


class NarrativeMode(Enum):
    """Four narrative modes - purely observational, never prescriptive"""
    ROAM = "roam"        # User is exploring/drifting without clear goal
    SPARK = "spark"      # User has shown interest in something specific
    PRESSURE = "pressure" # User is encountering obstacles/complications
    OUTCOME = "outcome"   # User has reached natural resolution point


class NarrativeTone(Enum):
    """Tone for coloring narration - describes fiction state, not player state"""
    CALM = "calm"        # Environment is peaceful, low stakes
    WARMING = "warming"  # Environment is building tension
    HOT = "hot"         # Environment has high stakes


@dataclass
class UserIntent:
    """
    Interpreted user intent from their actions.
    This is what the USER wants, not what the system wants them to do.
    """
    primary_want: Optional[str] = None  # What they're trying to accomplish NOW
    exploration_focus: Optional[str] = None  # What they're investigating
    social_target: Optional[str] = None  # Who they're engaging with
    movement_direction: Optional[str] = None  # Where they're going
    avoidance_pattern: Optional[str] = None  # What they're avoiding
    confidence: float = 0.5  # How clear the intent is (0.0-1.0)
    
    def is_clear(self) -> bool:
        """Check if user has clear intent"""
        return self.confidence >= 0.6 and self.primary_want is not None
    
    def is_drifting(self) -> bool:
        """Check if user is drifting without clear direction"""
        return self.confidence < 0.4 and self.primary_want is None


@dataclass
class ContextState:
    """
    Complete context awareness - spatial, temporal, social, environmental.
    This is the REALITY the user exists in, not a game state.
    """
    # Spatial context
    current_location: str = "unknown location"
    visible_locations: List[str] = field(default_factory=list)
    accessible_paths: List[str] = field(default_factory=list)
    location_atmosphere: str = "neutral"
    
    # Temporal context
    time_of_day: str = "unknown"
    weather: str = "clear"
    season: str = "unknown"
    time_pressure: float = 0.0  # 0.0 = no pressure, 1.0 = urgent deadline
    
    # Social context
    present_npcs: List[str] = field(default_factory=list)
    npc_states: Dict[str, str] = field(default_factory=dict)  # name -> emotional state
    social_atmosphere: str = "neutral"  # friendly, tense, hostile, etc.
    
    # Environmental context
    ambient_sounds: List[str] = field(default_factory=list)
    visible_objects: List[str] = field(default_factory=list)
    environmental_hazards: List[str] = field(default_factory=list)
    opportunities: List[str] = field(default_factory=list)
    
    # Fiction state
    unresolved_threads: List[str] = field(default_factory=list)
    recent_events: List[str] = field(default_factory=list)
    
    def get_summary(self) -> str:
        """Get human-readable context summary"""
        lines = []
        lines.append(f"Location: {self.current_location}")
        if self.present_npcs:
            lines.append(f"Present: {', '.join(self.present_npcs)}")
        if self.time_of_day != "unknown":
            lines.append(f"Time: {self.time_of_day}, {self.weather}")
        if self.opportunities:
            lines.append(f"Opportunities: {', '.join(self.opportunities[:3])}")
        return " | ".join(lines)


@dataclass
class NarrativeState:
    """Current narrative state - what IS, not what should be"""
    mode: NarrativeMode = NarrativeMode.ROAM
    tone: NarrativeTone = NarrativeTone.CALM
    user_intent: UserIntent = field(default_factory=UserIntent)
    context: ContextState = field(default_factory=ContextState)
    
    # Tracking
    last_mode_change: datetime = field(default_factory=datetime.now)
    turns_in_current_mode: int = 0
    last_significant_action: Optional[str] = None
    
    # Scene-sequel tracking
    last_scene_type: str = "doing"  # "doing" or "reflecting"
    consecutive_reflective_turns: int = 0
    
    def increment_turn(self):
        """Increment turn counter"""
        self.turns_in_current_mode += 1


class UserIntentInterpreter:
    """
    Interprets user intent from their actions.
    This reads what the user WANTS, not what we want them to want.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
    
    def interpret_intent(self, user_action: str, context: ContextState, 
                        action_interpretation: Dict[str, Any] = None) -> UserIntent:
        """
        Interpret what the user wants from their action.
        
        Args:
            user_action: What the user typed
            context: Current reality state
            action_interpretation: Optional existing interpretation from InterpreterAgent
        
        Returns:
            UserIntent object describing what the user is trying to do
        """
        # Use LLM to interpret intent
        prompt = f"""
Analyze this user action to understand their INTENT - what they want to accomplish.

**User Action:** "{user_action}"

**Current Context:**
- Location: {context.current_location}
- Present NPCs: {', '.join(context.present_npcs) if context.present_npcs else 'None'}
- Visible: {', '.join(context.visible_objects[:5]) if context.visible_objects else 'Nothing notable'}
- Atmosphere: {context.social_atmosphere}

**Your Task:**
Determine what the user is trying to accomplish. Focus on THEIR intent, not what you think they should do.

**Response Format (JSON only):**
{{
    "primary_want": "What they're trying to accomplish right now (or null if unclear)",
    "exploration_focus": "What they're investigating (or null)",
    "social_target": "Who they're trying to engage with (or null)",
    "movement_direction": "Where they're trying to go (or null)",
    "avoidance_pattern": "What they're avoiding (or null)",
    "confidence": 0.0-1.0,
    "reasoning": "Brief explanation"
}}

**Guidelines:**
- If action is vague/exploratory, confidence should be low (0.2-0.4)
- If action is specific/decisive, confidence should be high (0.7-1.0)
- Don't invent wants that aren't there - null is valid
- Read what they WANT, not what you think they SHOULD want
"""
        
        try:
            from openrouter_config import OpenRouterConfig
            model = OpenRouterConfig.get_model_for_role("interpretation")
            response = self.llm_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=300
            )
            
            from json_utils import extract_and_parse_json
            result = extract_and_parse_json(response.choices[0].message.content)
            
            if result:
                return UserIntent(
                    primary_want=result.get('primary_want'),
                    exploration_focus=result.get('exploration_focus'),
                    social_target=result.get('social_target'),
                    movement_direction=result.get('movement_direction'),
                    avoidance_pattern=result.get('avoidance_pattern'),
                    confidence=result.get('confidence', 0.5)
                )
        except Exception as e:
            self.logger.warning(f"Failed to interpret user intent: {e}")
        
        # Fallback: basic keyword analysis
        return self._fallback_intent_interpretation(user_action, context)
    
    def _fallback_intent_interpretation(self, user_action: str, context: ContextState) -> UserIntent:
        """Fallback intent interpretation using keywords"""
        action_lower = user_action.lower()
        
        # Check for clear wants
        want_patterns = {
            'find': ('Find something', 0.7),
            'get': ('Obtain something', 0.7),
            'talk to': ('Talk to someone', 0.8),
            'go to': ('Go somewhere', 0.8),
            'investigate': ('Investigate something', 0.7),
            'search': ('Search for something', 0.6),
            'avoid': ('Avoid something', 0.7),
            'escape': ('Escape from danger', 0.9),
        }
        
        for pattern, (want, confidence) in want_patterns.items():
            if pattern in action_lower:
                return UserIntent(
                    primary_want=want,
                    confidence=confidence
                )
        
        # Default: unclear intent
        return UserIntent(
            primary_want=None,
            confidence=0.3
        )


class ModeTransitioner:
    """
    Determines mode transitions based on user behavior and fiction state.
    NEVER pushes - only observes and responds.
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def determine_mode(self, current_state: NarrativeState, 
                      momentum_scores: Dict[str, float]) -> Tuple[NarrativeMode, str]:
        """
        Determine current mode based on user behavior and fiction state.
        
        Returns:
            (new_mode, reasoning)
        """
        intent = current_state.user_intent
        context = current_state.context
        
        # ROAM: User is drifting without clear goal
        if intent.is_drifting():
            if current_state.mode != NarrativeMode.ROAM:
                return NarrativeMode.ROAM, "User is exploring without clear direction"
            return current_state.mode, "Continuing drift-friendly exploration"
        
        # SPARK: User has shown interest in something
        if intent.is_clear() and current_state.mode == NarrativeMode.ROAM:
            return NarrativeMode.SPARK, f"User shows interest: {intent.primary_want}"
        
        # PRESSURE: User is encountering obstacles (from fiction, not forced)
        if current_state.mode == NarrativeMode.SPARK:
            # Check if fiction naturally presents obstacles
            env_pressure = momentum_scores.get('environmental_pressure', 0.0)
            social_pressure = momentum_scores.get('social_dynamics', 0.0)
            
            if env_pressure > 0.7 or social_pressure > 0.7:
                return NarrativeMode.PRESSURE, "Fiction naturally presents obstacles"
        
        # OUTCOME: User has reached natural resolution
        if current_state.mode == NarrativeMode.PRESSURE:
            # Check for resolution signals in context
            if len(context.unresolved_threads) == 0:
                return NarrativeMode.OUTCOME, "Natural resolution point reached"
        
        # OUTCOME -> ROAM: After resolution, return to exploration
        if current_state.mode == NarrativeMode.OUTCOME:
            if current_state.turns_in_current_mode >= 1:
                return NarrativeMode.ROAM, "Resolution complete, returning to exploration"
        
        # Default: stay in current mode
        return current_state.mode, f"Continuing in {current_state.mode.value} mode"
    
    def determine_tone(self, context: ContextState, momentum_scores: Dict[str, float]) -> NarrativeTone:
        """
        Determine narrative tone based on fiction state (not player state).
        """
        env_pressure = momentum_scores.get('environmental_pressure', 0.0)
        social_pressure = momentum_scores.get('social_dynamics', 0.0)
        
        # HOT: High environmental or social pressure
        if env_pressure > 0.7 or social_pressure > 0.8:
            return NarrativeTone.HOT
        
        # WARMING: Building pressure
        if env_pressure > 0.5 or social_pressure > 0.6:
            return NarrativeTone.WARMING
        
        # CALM: Low pressure environment
        return NarrativeTone.CALM


class ContextTracker:
    """
    Tracks complete context state - spatial, temporal, social, environmental.
    This is reality awareness, not game state.
    """
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
    
    def update_context(self, current_context: ContextState, 
                      scene_description: str,
                      turn_data: Dict[str, Any],
                      available_npcs: List[Any] = None) -> ContextState:
        """
        Update context state based on scene and turn data.
        """
        # Extract NPCs
        if available_npcs:
            current_context.present_npcs = [
                getattr(getattr(npc, 'sheet', None), 'name', 'Unknown') 
                if hasattr(npc, 'sheet') else str(npc)
                for npc in available_npcs
            ]
        
        # Use LLM to extract context from scene description
        try:
            context_update = self._extract_context_from_scene(scene_description)
            
            # Update context fields
            if context_update.get('location'):
                current_context.current_location = context_update['location']
            if context_update.get('time_of_day'):
                current_context.time_of_day = context_update['time_of_day']
            if context_update.get('weather'):
                current_context.weather = context_update['weather']
            if context_update.get('atmosphere'):
                current_context.location_atmosphere = context_update['atmosphere']
            if context_update.get('opportunities'):
                current_context.opportunities = context_update['opportunities']
            if context_update.get('visible_objects'):
                current_context.visible_objects = context_update['visible_objects']
            
        except Exception as e:
            self.logger.warning(f"Failed to extract context: {e}")
        
        # Track recent events
        narrative = turn_data.get('narrative_response', '')
        if narrative:
            current_context.recent_events.append(narrative)
            # Keep only last 5 events
            current_context.recent_events = current_context.recent_events[-5:]
        
        return current_context
    
    def _extract_context_from_scene(self, scene_description: str) -> Dict[str, Any]:
        """Extract context elements from scene description using LLM"""
        prompt = f"""
Extract context information from this scene description.

**Scene:**
{scene_description}

**Extract (JSON only):**
{{
    "location": "Brief location name",
    "time_of_day": "morning/afternoon/evening/night or unknown",
    "weather": "clear/rainy/stormy/etc or unknown",
    "atmosphere": "peaceful/tense/dangerous/busy/quiet/etc",
    "opportunities": ["visible opportunity 1", "visible opportunity 2"],
    "visible_objects": ["notable object 1", "notable object 2"]
}}

Focus on what's explicitly described. Use "unknown" if not mentioned.
"""
        
        from openrouter_config import OpenRouterConfig
        model = OpenRouterConfig.get_model_for_role("interpretation")
        response = self.llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=300
        )
        
        from json_utils import extract_and_parse_json
        return extract_and_parse_json(response.choices[0].message.content) or {}


class EnhancedNarrativeLoop:
    """
    Enhanced Four-Mode Narrative Loop with:
    - No push (reality doesn't push you)
    - User intent interpretation
    - Full context awareness
    - Task vs Goal distinction
    - Invisible scaffolding
    """
    
    def __init__(self, llm_client, goal_task_manager: GoalTaskManager = None):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
        
        # Core systems
        self.momentum_tracker = DiegeticMomentumTracker(llm_client)
        self.intent_interpreter = UserIntentInterpreter(llm_client)
        self.mode_transitioner = ModeTransitioner()
        self.context_tracker = ContextTracker(llm_client)
        
        # Goal/Task system
        self.goal_task_manager = goal_task_manager or GoalTaskManager()
        
        # State
        self.state = NarrativeState()
    
    def process_turn(self, turn_data: Dict[str, Any], 
                    scene_description: str,
                    time_context: Dict[str, Any] = None,
                    available_npcs: List[Any] = None) -> Dict[str, Any]:
        """
        Process a turn through the enhanced narrative loop.
        
        Returns framing guidance for narrative generation.
        """
        # 1. Update context awareness
        self.state.context = self.context_tracker.update_context(
            self.state.context,
            scene_description,
            turn_data,
            available_npcs
        )
        
        # 2. Interpret user intent
        user_action = turn_data.get('user_input', '')
        action_interpretation = turn_data.get('interpretation_data', {})
        
        self.state.user_intent = self.intent_interpreter.interpret_intent(
            user_action,
            self.state.context,
            action_interpretation
        )
        
        # 3. Analyze diegetic momentum (reality state, not player state)
        momentum_scores = self.momentum_tracker.analyze_turn_momentum(
            turn_data,
            scene_description,
            time_context,
            available_npcs
        )
        
        # 4. Determine mode based on user behavior and fiction state
        old_mode = self.state.mode
        new_mode, mode_reasoning = self.mode_transitioner.determine_mode(
            self.state,
            momentum_scores
        )
        
        mode_changed = new_mode != old_mode
        if mode_changed:
            self.state.mode = new_mode
            self.state.last_mode_change = datetime.now()
            self.state.turns_in_current_mode = 0
            self.logger.info(f"Mode transition: {old_mode.value} → {new_mode.value} ({mode_reasoning})")
        else:
            self.state.increment_turn()
        
        # 5. Determine tone based on fiction state
        self.state.tone = self.mode_transitioner.determine_tone(
            self.state.context,
            momentum_scores
        )
        
        # 6. Track scene type (doing vs reflecting)
        scene_type = self._detect_scene_type(user_action)
        if scene_type == "reflecting":
            self.state.consecutive_reflective_turns += 1
        else:
            self.state.consecutive_reflective_turns = 0
        self.state.last_scene_type = scene_type
        
        # 7. Generate framing guidance
        framing = self._generate_framing_guidance(
            mode_changed,
            mode_reasoning,
            momentum_scores
        )
        
        self.logger.info(
            f"Loop State: {self.state.mode.value} mode, "
            f"tone: {self.state.tone.value}, "
            f"intent: {self.state.user_intent.primary_want or 'drifting'}, "
            f"confidence: {self.state.user_intent.confidence:.2f}"
        )
        
        return framing
    
    def _detect_scene_type(self, user_action: str) -> str:
        """Detect if this is a 'doing' or 'reflecting' scene"""
        action_lower = user_action.lower()
        
        reflecting_words = ['think', 'consider', 'reflect', 'ponder', 'wonder', 
                          'remember', 'feel', 'realize', 'understand']
        
        if any(word in action_lower for word in reflecting_words):
            return "reflecting"
        return "doing"
    
    def _generate_framing_guidance(self, mode_changed: bool, 
                                  mode_reasoning: str,
                                  momentum_scores: Dict[str, float]) -> Dict[str, Any]:
        """Generate framing guidance for narrative generation"""
        
        guidance = {
            'mode': self.state.mode.value,
            'tone': self.state.tone.value,
            'mode_changed': mode_changed,
            'mode_reasoning': mode_reasoning,
            'scene_type': self.state.last_scene_type,
            
            # User intent (what they WANT)
            'user_intent': {
                'primary_want': self.state.user_intent.primary_want,
                'exploration_focus': self.state.user_intent.exploration_focus,
                'social_target': self.state.user_intent.social_target,
                'confidence': self.state.user_intent.confidence,
                'is_clear': self.state.user_intent.is_clear(),
                'is_drifting': self.state.user_intent.is_drifting()
            },
            
            # Context (what IS)
            'context': {
                'location': self.state.context.current_location,
                'time': self.state.context.time_of_day,
                'weather': self.state.context.weather,
                'atmosphere': self.state.context.location_atmosphere,
                'present_npcs': self.state.context.present_npcs,
                'opportunities': self.state.context.opportunities,
                'summary': self.state.context.get_summary()
            },
            
            # Momentum (fiction state)
            'momentum': momentum_scores,
            
            # Narrative guidance
            'narrative_guidance': self._get_narrative_guidance(),
            'diegetic_cues': self._get_diegetic_cues(),
            
            # Task/Goal state
            'current_task': self.goal_task_manager.current_task.description if self.goal_task_manager.current_task else None,
            'active_goals': [g.description for g in self.goal_task_manager.goals]
        }
        
        return guidance
    
    def _get_narrative_guidance(self) -> str:
        """Get mode-specific narrative guidance"""
        
        if self.state.mode == NarrativeMode.ROAM:
            return (
                "**ROAM MODE - Respond to User Exploration:**\n"
                "- Describe what the user FINDS based on their action\n"
                "- Present visible opportunities naturally (2-3 things they can see/do)\n"
                "- NO pushing toward goals - let them drift\n"
                "- Maintain the established worldbuilding atmosphere\n"
                "- Frame at point of uncertainty with diegetic elements only"
            )
        
        elif self.state.mode == NarrativeMode.SPARK:
            intent = self.state.user_intent.primary_want or "unknown interest"
            return (
                f"**SPARK MODE - User Shows Interest: {intent}:**\n"
                "- Acknowledge what caught their attention\n"
                "- Provide information about what they're interested in\n"
                "- Present related opportunities IF they exist in fiction\n"
                "- NO artificial missions - only respond to their curiosity\n"
                "- Let THEM decide if they want to pursue this"
            )
        
        elif self.state.mode == NarrativeMode.PRESSURE:
            return (
                "**PRESSURE MODE - Fiction Presents Obstacles:**\n"
                "- Describe obstacles that naturally exist in the fiction\n"
                "- Use Kishōtenketsu 'Ten' twists (perspective shifts, revelations)\n"
                "- Complications come from REALITY, not arbitrary difficulty\n"
                "- NO forced conflict - obstacles can be social, environmental, informational\n"
                "- Heighten stakes through recontextualization"
            )
        
        elif self.state.mode == NarrativeMode.OUTCOME:
            return (
                "**OUTCOME MODE - Natural Resolution:**\n"
                "- Deliver natural consequences of their actions\n"
                "- Provide closure on current thread\n"
                "- Follow with reflective sequel beat (what now?)\n"
                "- NO artificial rewards - only what makes sense in fiction\n"
                "- Allow space for processing and new direction"
            )
        
        return "Continue natural narrative flow."
    
    def _get_diegetic_cues(self) -> List[str]:
        """Generate diegetic cues based on current state"""
        cues = []
        
        # Intent-based cues
        if self.state.user_intent.is_clear():
            cues.append(f"User wants to: {self.state.user_intent.primary_want}")
        elif self.state.user_intent.is_drifting():
            cues.append("User is exploring without clear direction")
        
        # Context-based cues
        if self.state.context.opportunities:
            cues.append(f"Visible opportunities: {', '.join(self.state.context.opportunities[:3])}")
        
        if self.state.context.present_npcs:
            cues.append(f"NPCs present: {', '.join(self.state.context.present_npcs)}")
        
        # Tone-based cues
        if self.state.tone == NarrativeTone.HOT:
            cues.append("High-stakes environment")
        elif self.state.tone == NarrativeTone.WARMING:
            cues.append("Building tension")
        
        return cues
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current state for debugging or display"""
        return {
            'mode': self.state.mode.value,
            'tone': self.state.tone.value,
            'user_intent': {
                'primary_want': self.state.user_intent.primary_want,
                'confidence': self.state.user_intent.confidence
            },
            'context_summary': self.state.context.get_summary(),
            'turns_in_mode': self.state.turns_in_current_mode
        }
