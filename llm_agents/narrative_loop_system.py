"""
Four-Mode Narrative Loop System for UTAS Simulation

This system provides invisible scaffolding for natural storytelling using universal beat patterns
from Story Circle, Kishōtenketsu, and scene-sequel transitions. The four modes (Roam, Spark, 
Pressure, Outcome) guide narrative flow without exposing gamey mechanics to users.

Design Philosophy:
- Invisible scaffolding using universal story beats
- Minimal states, maximal nuance through mode/intent/tone
- Conflict-optional with Kishōtenketsu twist support
- Diegetic cues only, no visible meters or mechanics
"""

import logging
from datetime import datetime
from typing import Dict, List, Any, Optional
from enum import Enum
from dataclasses import dataclass, field
import json
from openrouter_config import OpenRouterConfig
from .diegetic_momentum_tracker import DiegeticMomentumTracker, MomentumFactor

class NarrativeMode(Enum):
    """Four narrative modes mapping to universal story beats"""
    ROAM = "roam"        # Drift-friendly exploration (You/Need, Ki-Shō)
    SPARK = "spark"      # Gentle nudge into purpose (Need→Go, soft goal turn)
    PRESSURE = "pressure" # Heightened stakes (Struggle/Find, Ten twist)
    OUTCOME = "outcome"   # Natural resolution (Return/Change, Ketsu)

class NarrativeTone(Enum):
    """Tone coloring for narration without visible mechanics"""
    CALM = "calm"        # Peaceful, reflective, low stakes
    WARMING = "warming"  # Building tension, emerging stakes
    HOT = "hot"         # High stakes, immediate pressure

class SoftSignalType(Enum):
    """Soft signals extracted from user behavior and fiction"""
    WANT = "want"           # Explicit desire suggests Spark readiness
    FRICTION = "friction"   # Repeated blocks suggest Pressure beat
    CLOSURE = "closure"     # Natural end suggests Outcome + sequel
    STAGNATION = "stagnation" # No progress for multiple cycles

@dataclass
class SoftSignal:
    """A detected signal from user behavior or fiction state"""
    signal_type: SoftSignalType
    strength: float  # 0.0 to 1.0 confidence
    description: str
    source_data: Dict[str, Any]
    detected_at: datetime

@dataclass
class NarrativeState:
    """Current state of the narrative loop"""
    mode: NarrativeMode = NarrativeMode.ROAM
    intent: Optional[str] = None
    tone: NarrativeTone = NarrativeTone.CALM
    last_mode_change: datetime = field(default_factory=datetime.now)
    cycles_in_roam: int = 0
    reflective_cycles: int = 0  # Track reflective behavior for meander tolerance
    last_scene_type: str = "doing"  # Track "doing" vs "reflecting" for scene-sequel
    signal_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Mission/Goal Tracking
    active_mission: Optional[str] = None  # Current mission/spark being pursued
    mission_description: Optional[str] = None  # Detailed description of the mission
    available_sparks: List[str] = field(default_factory=list)  # Potential missions in SPARK mode
    mission_progress: float = 0.0  # 0.0 to 1.0, how far along the mission
    obstacles_overcome: List[str] = field(default_factory=list)  # Track progress milestones
    mission_rewards: List[str] = field(default_factory=list)  # Potential rewards for completion
    mission_started_at: Optional[datetime] = None  # When mission was accepted

    def __post_init__(self):
        if self.signal_history is None:
            self.signal_history = []
        if self.available_sparks is None:
            self.available_sparks = []
        if self.obstacles_overcome is None:
            self.obstacles_overcome = []
        if self.mission_rewards is None:
            self.mission_rewards = []
    
    def start_mission(self, mission_name: str, description: str):
        """Start tracking a new mission"""
        self.active_mission = mission_name
        self.mission_description = description
        self.mission_progress = 0.0
        self.obstacles_overcome = []
        self.mission_started_at = datetime.now()
    
    def add_obstacle_overcome(self, obstacle: str):
        """Record an obstacle that was overcome"""
        if obstacle not in self.obstacles_overcome:
            self.obstacles_overcome.append(obstacle)
            # Increase progress based on obstacles overcome
            self.mission_progress = min(1.0, len(self.obstacles_overcome) * 0.25)
    
    def complete_mission(self):
        """Mark mission as complete and prepare for resolution"""
        self.mission_progress = 1.0
    
    def clear_mission(self):
        """Clear mission data after resolution"""
        self.active_mission = None
        self.mission_description = None
        self.mission_progress = 0.0
        self.obstacles_overcome = []
        self.mission_rewards = []
        self.mission_started_at = None
    
    def has_active_mission(self) -> bool:
        """Check if there's an active mission"""
        return self.active_mission is not None
    
    def add_mission_reward(self, reward: str):
        """Add a potential reward for mission completion"""
        if reward not in self.mission_rewards:
            self.mission_rewards.append(reward)
    
    def get_mission_summary(self) -> Dict[str, Any]:
        """Get a summary of the current mission state"""
        return {
            'active_mission': self.active_mission,
            'description': self.mission_description,
            'progress': self.mission_progress,
            'obstacles_overcome': self.obstacles_overcome,
            'rewards': self.mission_rewards,
            'is_complete': self.mission_progress >= 1.0
        }

class SoftSignalDetector:
    """Detects narrative signals from user actions and fiction state"""
    
    def __init__(self, llm_client):
        self.llm_client = llm_client
        self.logger = logging.getLogger(__name__)
    
    def detect_signals_from_turn(self, turn_data: Dict[str, Any]) -> List[SoftSignal]:
        """Detect soft signals from a turn's data"""
        signals = []
        
        # Detect each signal type
        want_signal = self._detect_want_signal(turn_data)
        if want_signal:
            signals.append(want_signal)
        
        friction_signal = self._detect_friction_signal(turn_data)
        if friction_signal:
            signals.append(friction_signal)
        
        closure_signal = self._detect_closure_signal(turn_data)
        if closure_signal:
            signals.append(closure_signal)
        
        # Enhanced signal detection
        emotional_signal = self._detect_emotional_shift(turn_data)
        if emotional_signal:
            signals.append(emotional_signal)
        
        opportunity_signal = self._detect_opportunity(turn_data)
        if opportunity_signal:
            signals.append(opportunity_signal)
        
        tension_signal = self._detect_unresolved_tension(turn_data)
        if tension_signal:
            signals.append(tension_signal)
        
        return signals
    
    def _detect_want_signal(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect explicit desires or repeated attention patterns"""
        user_input = turn_data.get('user_input', '')
        
        # Use LLM to analyze for want signals
        prompt = f"""
        Analyze this user input for explicit desires or goals that suggest readiness for purposeful action:
        
        User Input: "{user_input}"
        
        Look for:
        - Direct statements of want ("I want to...", "I need to...")
        - Repeated focus on specific people, places, or objectives
        - Questions that suggest goal-seeking behavior
        - Expressions of curiosity or investigation intent
        
        Respond with JSON:
        {{
            "has_want_signal": true/false,
            "strength": 0.0-1.0,
            "description": "Brief description of the detected want",
            "intent_summary": "One-line summary of the apparent goal"
        }}
        """
        
        try:
            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            response_content = response.choices[0].message.content.strip()
            if not response_content:
                return None
                
            # Try to extract JSON from response
            from json_utils import extract_and_parse_json
            result = extract_and_parse_json(response_content)
            
            if result and result.get('has_want_signal', False):
                return SoftSignal(
                    signal_type=SoftSignalType.WANT,
                    strength=result.get('strength', 0.5),
                    description=result.get('description', 'Detected want signal'),
                    source_data={'user_input': user_input, 'intent': result.get('intent_summary')},
                    detected_at=datetime.now()
                )
        except Exception as e:
            self.logger.warning(f"Failed to detect want signal: {e}")
        
        return None
    
    def _detect_friction_signal(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect repeated blocks, time passing, or social friction"""
        # Check for continuity failures or repeated unsuccessful attempts
        continuity_result = turn_data.get('continuity_check', {})
        if continuity_result.get('judgment') == 'Not Possible':
            return SoftSignal(
                signal_type=SoftSignalType.FRICTION,
                strength=0.7,
                description="Action blocked by continuity check",
                source_data={'continuity_failure': continuity_result},
                detected_at=datetime.now()
            )
        
        # Check for low success rates or failed actions
        success_data = turn_data.get('success_calculation', {})
        if success_data.get('total_successes', 0) == 0:
            return SoftSignal(
                signal_type=SoftSignalType.FRICTION,
                strength=0.5,
                description="Action failed, suggesting obstacles",
                source_data={'failed_action': success_data},
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_closure_signal(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect natural ending points or resolution moments"""
        user_input = turn_data.get('user_input', '').lower()
        
        # Look for completion language
        completion_phrases = [
            'finished', 'done', 'complete', 'accomplished', 'resolved',
            'found', 'discovered', 'reached', 'arrived', 'succeeded',
            'successfully', 'open', 'unlock', 'meaning', 'understand',
            'reveals', 'pattern'
        ]
        
        if any(phrase in user_input for phrase in completion_phrases):
            return SoftSignal(
                signal_type=SoftSignalType.CLOSURE,
                strength=0.8,
                description="User language suggests task completion",
                source_data={'completion_language': user_input},
                detected_at=datetime.now()
            )
        
        # Check for high success rates indicating resolution
        success_data = turn_data.get('success_calculation', {})
        if success_data.get('total_successes', 0) >= 2:
            return SoftSignal(
                signal_type=SoftSignalType.CLOSURE,
                strength=0.7,
                description="High success rate suggests resolution",
                source_data={'high_success': success_data},
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_scene_type(self, turn_data: Dict[str, Any]) -> str:
        """Detect if this is a 'doing' or 'reflecting' scene for scene-sequel tracking"""
        user_input = turn_data.get('user_input', '').lower()
        
        # Reflecting indicators
        reflecting_phrases = [
            'think', 'consider', 'reflect', 'ponder', 'wonder', 'remember',
            'feel', 'realize', 'understand', 'process', 'contemplate'
        ]
        
        # Doing indicators  
        doing_phrases = [
            'go', 'move', 'walk', 'run', 'search', 'look', 'examine',
            'talk', 'speak', 'ask', 'tell', 'grab', 'take', 'use'
        ]
        
        if any(phrase in user_input for phrase in reflecting_phrases):
            return "reflecting"
        elif any(phrase in user_input for phrase in doing_phrases):
            return "doing"
        else:
            # Default based on action complexity
            return "doing" if len(user_input.split()) > 3 else "reflecting"
    
    def _detect_emotional_shift(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect emotional changes that might signal narrative transitions"""
        user_input = turn_data.get('user_input', '').lower()
        
        # Emotional shift indicators
        emotional_phrases = [
            'angry', 'frustrated', 'excited', 'worried', 'relieved', 'surprised',
            'confused', 'determined', 'hopeful', 'disappointed', 'curious'
        ]
        
        if any(phrase in user_input for phrase in emotional_phrases):
            return SoftSignal(
                signal_type=SoftSignalType.WANT,  # Emotional shifts often indicate new wants
                strength=0.6,
                description="Emotional shift detected",
                source_data={'emotional_language': user_input},
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_opportunity(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect emerging opportunities in the fiction"""
        user_input = turn_data.get('user_input', '').lower()
        
        # Opportunity indicators
        opportunity_phrases = [
            'notice', 'see', 'hear', 'find', 'discover', 'opportunity',
            'chance', 'opening', 'available', 'possible'
        ]
        
        if any(phrase in user_input for phrase in opportunity_phrases):
            return SoftSignal(
                signal_type=SoftSignalType.WANT,
                strength=0.5,
                description="Opportunity detected in fiction",
                source_data={'opportunity_language': user_input},
                detected_at=datetime.now()
            )
        
        return None
    
    def _detect_unresolved_tension(self, turn_data: Dict[str, Any]) -> Optional[SoftSignal]:
        """Detect ongoing tensions that need resolution"""
        user_input = turn_data.get('user_input', '').lower()
        
        # Tension indicators
        tension_phrases = [
            'still', 'yet', 'but', 'however', 'problem', 'issue',
            'unfinished', 'incomplete', 'waiting', 'stuck'
        ]
        
        if any(phrase in user_input for phrase in tension_phrases):
            return SoftSignal(
                signal_type=SoftSignalType.FRICTION,
                strength=0.4,
                description="Unresolved tension detected",
                source_data={'tension_language': user_input},
                detected_at=datetime.now()
            )
        
        return None

class NarrativeModeTransitioner:
    """Handles transitions between narrative modes based on soft signals"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def determine_next_mode(self, current_state: NarrativeState, 
                          signals: List[SoftSignal]) -> NarrativeMode:
        """Choose next mode based on current state and detected signals"""
        
        # Check for strong signals that override current mode
        for signal in signals:
            if signal.strength >= 0.7:
                if signal.signal_type == SoftSignalType.WANT and current_state.mode == NarrativeMode.ROAM:
                    return NarrativeMode.SPARK
                elif signal.signal_type == SoftSignalType.FRICTION:
                    return NarrativeMode.PRESSURE
                elif signal.signal_type == SoftSignalType.CLOSURE:
                    return NarrativeMode.OUTCOME
        
        # Handle meander tolerance - surface soft Spark after 2 reflective cycles in Roam
        if (current_state.mode == NarrativeMode.ROAM and 
            current_state.reflective_cycles >= 2):
            return NarrativeMode.SPARK
        
        # Natural progression patterns
        if current_state.mode == NarrativeMode.SPARK:
            # Spark can lead to Pressure if friction emerges
            friction_signals = [s for s in signals if s.signal_type == SoftSignalType.FRICTION]
            if friction_signals:
                return NarrativeMode.PRESSURE
        
        elif current_state.mode == NarrativeMode.PRESSURE:
            # Pressure naturally resolves to Outcome
            if any(s.signal_type == SoftSignalType.CLOSURE for s in signals):
                return NarrativeMode.OUTCOME
        
        elif current_state.mode == NarrativeMode.OUTCOME:
            # Outcome leads to reflective Roam (sequel beat)
            return NarrativeMode.ROAM
        
        # Default: stay in current mode
        return current_state.mode
    
    def update_tone(self, current_state: NarrativeState, 
                   signals: List[SoftSignal]) -> NarrativeTone:
        """Update narrative tone based on mode and signals"""
        
        # Pressure mode tends toward warming/hot
        if current_state.mode == NarrativeMode.PRESSURE:
            friction_strength = max([s.strength for s in signals 
                                   if s.signal_type == SoftSignalType.FRICTION] + [0])
            if friction_strength >= 0.8:
                return NarrativeTone.HOT
            elif friction_strength >= 0.5:
                return NarrativeTone.WARMING
        
        # Spark mode builds gentle warmth
        elif current_state.mode == NarrativeMode.SPARK:
            return NarrativeTone.WARMING
        
        # Roam and Outcome default to calm
        return NarrativeTone.CALM

class FourModeNarrativeLoop:
    """Main coordinator for the Four-Mode Narrative Loop system"""
    
    def __init__(self, client):
        self.client = client
        self.logger = logging.getLogger(__name__)
        self.momentum_tracker = DiegeticMomentumTracker()
        self.signal_detector = SoftSignalDetector(client)
        self.mode_transitioner = NarrativeModeTransitioner()
        self.current_state = NarrativeState(
            mode=NarrativeMode.ROAM,
            intent=None,
            tone=NarrativeTone.CALM,
            last_mode_change=datetime.now()
        )
    
    def process_turn(self, turn_data: Dict[str, Any], time_context: Dict[str, Any] = None, 
                   available_npcs: List[Any] = None) -> Dict[str, Any]:
        """Process a turn through the narrative loop and return framing guidance"""
        
        # Step 1: Analyze momentum through diegetic factors
        scene_context = turn_data.get('scene_description', '')
        momentum_scores = self.momentum_tracker.analyze_turn_momentum(turn_data, scene_context, time_context, available_npcs)
        
        # Step 2: Check for momentum-based mode transitions
        momentum_suggested_mode = self.momentum_tracker.should_trigger_mode_transition(
            momentum_scores, self.current_state.mode.value
        )
        
        # Step 3: Extract soft signals and scene type (existing system)
        signals = self.signal_detector.detect_signals_from_turn(turn_data)
        self.current_state.signal_history.extend(signals)
        
        # Detect scene type for scene-sequel tracking
        scene_type = self.signal_detector._detect_scene_type(turn_data)
        
        # Step 4: Choose mode based on both momentum and signals
        signal_suggested_mode = self.mode_transitioner.determine_next_mode(self.current_state, signals)
        
        # Prioritize momentum-based transitions for more natural flow
        new_mode_str = momentum_suggested_mode or signal_suggested_mode.value
        new_mode = NarrativeMode(new_mode_str) if isinstance(new_mode_str, str) else signal_suggested_mode
        
        # Step 3: Update state with enhanced tracking
        mode_changed = new_mode != self.current_state.mode
        if mode_changed:
            self.current_state.mode = new_mode
            self.current_state.last_mode_change = datetime.now()
            self.current_state.cycles_in_roam = 0
            self.current_state.reflective_cycles = 0
        elif new_mode == NarrativeMode.ROAM:
            self.current_state.cycles_in_roam += 1
            # Track reflective cycles for meander tolerance
            if scene_type == "reflecting":
                self.current_state.reflective_cycles += 1
            else:
                self.current_state.reflective_cycles = 0
        
        # Update scene type tracking
        self.current_state.last_scene_type = scene_type
        
        # Update tone and intent
        self.current_state.tone = self.mode_transitioner.update_tone(self.current_state, signals)
        self._update_intent(signals)
        
        # Step 4: Generate framing guidance with scene-sequel awareness
        framing_guidance = self._generate_framing_guidance(signals, mode_changed, scene_type)
        
        self.logger.info(f"Narrative Loop: {self.current_state.mode.value} mode, "
                        f"tone: {self.current_state.tone.value}, "
                        f"scene: {scene_type}, "
                        f"intent: {self.current_state.intent}")
        
        return framing_guidance
    
    def _update_intent(self, signals: List[SoftSignal]):
        """Update the current intent based on want signals"""
        want_signals = [s for s in signals if s.signal_type == SoftSignalType.WANT]
        if want_signals:
            # Use the strongest want signal
            strongest = max(want_signals, key=lambda s: s.strength)
            self.current_state.intent = strongest.description
            
            # If in SPARK mode and player shows clear intent, start mission
            if (self.current_state.mode == NarrativeMode.SPARK and 
                not self.current_state.has_active_mission() and
                strongest.strength >= 0.7):
                self.current_state.start_mission(
                    mission_name=strongest.description,
                    description=strongest.source_data.get('context', strongest.description)
                )
    
    def _generate_framing_guidance(self, signals: List[SoftSignal], mode_changed: bool, scene_type: str = "doing") -> Dict[str, Any]:
        """Generate framing guidance for the current narrative state"""
        
        # Track mission progress in PRESSURE mode
        if self.current_state.mode == NarrativeMode.PRESSURE and self.current_state.has_active_mission():
            self._track_mission_progress(signals)
        
        guidance = {
            'mode': self.current_state.mode.value,
            'tone': self.current_state.tone.value,
            'intent': self.current_state.intent,
            'scene_type': scene_type,
            'mode_changed': mode_changed,
            'framing_type': self._get_framing_type(),
            'narrative_guidance': self._get_narrative_guidance(),
            'diegetic_cues': self._get_diegetic_cues(signals),
            'setting_context': "Established worldbuilding context - technology, cultural references, and social context from RAG",
            'active_mission': self.current_state.active_mission,
            'mission_progress': self.current_state.mission_progress
        }
        
        return guidance
    
    def _track_mission_progress(self, signals: List[SoftSignal]):
        """Track mission progress based on signals and outcomes"""
        # Check for successful actions that advance the mission
        for signal in signals:
            if signal.signal_type == SoftSignalType.WANT:
                # Player is making progress toward their goal
                if signal.strength >= 0.6:
                    obstacle_desc = signal.source_data.get('action_description', 'obstacle')
                    self.current_state.add_obstacle_overcome(obstacle_desc)
            
            # Check for mission completion
            if signal.signal_type == SoftSignalType.CLOSURE:
                if self.current_state.mission_progress >= 0.75:
                    self.current_state.complete_mission()
    
    def _get_framing_type(self) -> str:
        """Determine how to frame the next scene beat"""
        mode_framing = {
            NarrativeMode.ROAM: "exploration",      # Open-ended, drift-friendly
            NarrativeMode.SPARK: "opportunity",     # Present organic prompts
            NarrativeMode.PRESSURE: "obstacle",     # Introduce friction or twists
            NarrativeMode.OUTCOME: "resolution"     # Deliver consequences + reflection
        }
        return mode_framing[self.current_state.mode]
    
    def _get_narrative_guidance(self) -> str:
        """Get mode-specific guidance for narrative generation"""
        
        if self.current_state.mode == NarrativeMode.ROAM:
            guidance = ("**ROAM MODE - Open World Freedom:**\n"
                       "- Emphasize the world is open and accessible\n"
                       "- Describe 2-3 visible locations, NUAs, or opportunities casually\n"
                       "- Make the player feel they can go anywhere based on their intent\n"
                       "- Frame at point of uncertainty with diegetic elements\n"
                       "- Allow organic exploration and socializing without pressure")
            return guidance
        
        elif self.current_state.mode == NarrativeMode.SPARK:
            guidance = ("**SPARK MODE - Introduce Potential Missions:**\n"
                       "- Casually introduce 2-3 potential missions/goals through:\n"
                       "  * NUA dialogue ('I heard the warehouse is hiring')\n"
                       "  * Environmental cues (wanted poster, broken fence, overheard conversation)\n"
                       "  * Opportunities that align with character interests\n"
                       "  * **NUA-INITIATED SITUATIONS** (50% observational, 50% forced exchange):\n"
                       "    - Observational: NUA does something interesting nearby (argument, accident, performance)\n"
                       "      → UA can choose to engage or just watch\n"
                       "    - Forced Exchange: NUA directly approaches/confronts UA (asks question, makes demand, needs help)\n"
                       "      → UA must respond, triggering contested action\n"
                       "- Frame as interesting possibilities, not obligations\n"
                       "- Let the player choose which spark to pursue\n"
                       "- Nudge toward purpose without forcing or showing mechanics")
            if self.current_state.available_sparks:
                guidance += f"\n- Available sparks: {', '.join(self.current_state.available_sparks)}"
            return guidance
        
        elif self.current_state.mode == NarrativeMode.PRESSURE:
            if self.current_state.has_active_mission():
                guidance = (f"**PRESSURE MODE - Advance Mission: '{self.current_state.active_mission}':**\n"
                           f"- Mission: {self.current_state.mission_description}\n"
                           f"- Progress: {int(self.current_state.mission_progress * 100)}%\n"
                           f"- Obstacles overcome: {len(self.current_state.obstacles_overcome)}\n"
                           "- Present challenges that directly advance this mission:\n"
                           "  * 1 hard challenge (requires planning/resources/skill)\n"
                           "  * 2 easy wins (build momentum, show progress)\n"
                           "- Each obstacle should feel like progress toward the goal\n"
                           "- Use Kishōtenketsu Ten-style twists to heighten stakes")
            else:
                guidance = ("**PRESSURE MODE - Create Obstacles:**\n"
                           "- Introduce obstacles or complications\n"
                           "- Use perspective shifts, revelations, or schedule changes\n"
                           "- Heighten stakes without forcing conflict")
            return guidance
        
        elif self.current_state.mode == NarrativeMode.OUTCOME:
            if self.current_state.has_active_mission():
                rewards_text = f"\n- Potential rewards: {', '.join(self.current_state.mission_rewards)}" if self.current_state.mission_rewards else ""
                guidance = (f"**OUTCOME MODE - Resolve Mission: '{self.current_state.active_mission}':**\n"
                           f"- Mission completed: {self.current_state.mission_description}\n"
                           f"- Obstacles overcome: {', '.join(self.current_state.obstacles_overcome)}{rewards_text}\n"
                           "- Tie up loose ends (what happened to involved NUAs?)\n"
                           "- Deliver clear rewards (items, relationships, information) OR consequences (setbacks, complications)\n"
                           "- Show how the world changed from this mission\n"
                           "- Provide closure and hint at new possibilities\n"
                           "- Follow with reflective sequel beat for processing")
            else:
                guidance = ("**OUTCOME MODE - Natural Resolution:**\n"
                           "- Deliver natural consequences or rewards in-fiction\n"
                           "- Follow with reflective sequel beat for processing and new direction")
            return guidance
        
        return "Continue natural narrative flow."
    
    def _get_diegetic_cues(self, signals: List[SoftSignal]) -> List[str]:
        """Generate diegetic cues based on current mode and signals"""
        cues = []
        
        if self.current_state.mode == NarrativeMode.SPARK:
            if self.current_state.intent:
                cues.append(f"Present opportunity related to: {self.current_state.intent}")
            else:
                cues.append("Surface gentle prompt aligned with character interests")
        
        elif self.current_state.mode == NarrativeMode.PRESSURE:
            friction_signals = [s for s in signals if s.signal_type == SoftSignalType.FRICTION]
            if friction_signals:
                cues.append("Acknowledge the obstacle and escalate or reframe")
            else:
                cues.append("Introduce complicating element or perspective shift")
        
        elif self.current_state.mode == NarrativeMode.OUTCOME:
            closure_signals = [s for s in signals if s.signal_type == SoftSignalType.CLOSURE]
            if closure_signals:
                cues.append("Acknowledge completion and provide reflection moment")
            else:
                cues.append("Bring current thread to natural resolution")
        
        return cues
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current narrative state for debugging or integration"""
        return {
            'mode': self.current_state.mode.value,
            'intent': self.current_state.intent,
            'tone': self.current_state.tone.value,
            'cycles_in_roam': self.current_state.cycles_in_roam,
            'recent_signals': [
                {
                    'type': s.signal_type.value,
                    'strength': s.strength,
                    'description': s.description
                }
                for s in self.current_state.signal_history[-5:]  # Last 5 signals
            ]
        }
