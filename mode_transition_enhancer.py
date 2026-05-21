"""
Mode Transition Enhancer for UTAS Simulation

Improves Four-Mode Narrative Loop transitions (Roam → Spark → Pressure → Outcome).
Prevents fake signals where mode transitions feel abrupt or unnatural.
"""

from typing import Dict, Any, Optional, List
from enum import Enum
from color_utils import Color


class NarrativeMode(Enum):
    """Four-Mode Narrative Loop states."""
    ROAM = "roam"
    SPARK = "spark"
    PRESSURE = "pressure"
    OUTCOME = "outcome"


class ModeTransitionEnhancer:
    """
    Enhances mode transitions in the Four-Mode Narrative Loop.
    
    Features:
    - Detects natural transition points
    - Provides smooth mode changes
    - Tracks narrative momentum
    - Prevents jarring transitions
    """
    
    def __init__(self):
        self.current_mode = NarrativeMode.ROAM
        self.mode_history = []
        self.turns_in_mode = 0
        self.narrative_momentum = 0  # -5 to +5
        self.tension_level = 0  # 0 to 10
        self.want_signals = []
        self.friction_signals = []
        self.closure_signals = []
    
    def assess_transition_readiness(
        self,
        user_action: str,
        scene_context: str,
        recent_outcomes: List[str]
    ) -> Dict[str, Any]:
        """
        Assess if mode transition is ready based on soft signals.
        
        Returns:
            Dict with recommended_mode, transition_ready, reasoning
        """
        # Detect soft signals
        has_want = self._detect_want_signal(user_action)
        has_friction = self._detect_friction_signal(recent_outcomes)
        has_closure = self._detect_closure_signal(scene_context, recent_outcomes)
        
        # Update signal tracking
        if has_want:
            self.want_signals.append(user_action)
        if has_friction:
            self.friction_signals.append(recent_outcomes[-1] if recent_outcomes else "")
        if has_closure:
            self.closure_signals.append(scene_context)
        
        # Determine recommended mode
        recommended_mode = self._determine_next_mode(has_want, has_friction, has_closure)
        
        # Check if transition is ready
        transition_ready = self._is_transition_ready(recommended_mode)
        
        # Generate reasoning
        reasoning = self._generate_transition_reasoning(
            recommended_mode, has_want, has_friction, has_closure
        )
        
        return {
            'current_mode': self.current_mode.value,
            'recommended_mode': recommended_mode.value,
            'transition_ready': transition_ready,
            'reasoning': reasoning,
            'turns_in_mode': self.turns_in_mode,
            'narrative_momentum': self.narrative_momentum,
            'tension_level': self.tension_level,
            'signals': {
                'want': has_want,
                'friction': has_friction,
                'closure': has_closure
            }
        }
    
    def _detect_want_signal(self, user_action: str) -> bool:
        """Detect if user action expresses a want/desire."""
        want_keywords = [
            'want', 'need', 'looking for', 'trying to', 'going to',
            'plan to', 'intend to', 'hope to', 'wish', 'desire'
        ]
        action_lower = user_action.lower()
        return any(keyword in action_lower for keyword in want_keywords)
    
    def _detect_friction_signal(self, recent_outcomes: List[str]) -> bool:
        """Detect if recent outcomes show friction/obstacles."""
        if not recent_outcomes:
            return False
        
        # Check last 3 outcomes for failures
        recent = recent_outcomes[-3:]
        friction_keywords = ['fail', 'block', 'prevent', 'stop', 'refuse', 'reject']
        
        friction_count = sum(
            1 for outcome in recent
            if any(keyword in outcome.lower() for keyword in friction_keywords)
        )
        
        return friction_count >= 2  # 2+ failures = friction
    
    def _detect_closure_signal(self, scene_context: str, recent_outcomes: List[str]) -> bool:
        """Detect if scene/situation has natural closure."""
        closure_keywords = [
            'resolved', 'completed', 'finished', 'done', 'ended',
            'accomplished', 'achieved', 'settled', 'concluded'
        ]
        
        context_lower = scene_context.lower()
        has_closure_context = any(keyword in context_lower for keyword in closure_keywords)
        
        # Also check if recent outcomes show success
        if recent_outcomes:
            last_outcome = recent_outcomes[-1].lower()
            has_success = any(word in last_outcome for word in ['success', 'achieve', 'accomplish'])
            return has_closure_context or has_success
        
        return has_closure_context
    
    def _determine_next_mode(
        self,
        has_want: bool,
        has_friction: bool,
        has_closure: bool
    ) -> NarrativeMode:
        """Determine next mode based on signals."""
        
        if self.current_mode == NarrativeMode.ROAM:
            if has_want:
                return NarrativeMode.SPARK
            return NarrativeMode.ROAM
        
        elif self.current_mode == NarrativeMode.SPARK:
            if has_friction:
                return NarrativeMode.PRESSURE
            elif self.turns_in_mode >= 3:
                return NarrativeMode.PRESSURE  # Natural progression
            return NarrativeMode.SPARK
        
        elif self.current_mode == NarrativeMode.PRESSURE:
            if has_closure:
                return NarrativeMode.OUTCOME
            elif self.turns_in_mode >= 5:
                return NarrativeMode.OUTCOME  # Force resolution
            return NarrativeMode.PRESSURE
        
        elif self.current_mode == NarrativeMode.OUTCOME:
            if self.turns_in_mode >= 2:
                return NarrativeMode.ROAM  # Return to exploration
            return NarrativeMode.OUTCOME
        
        return self.current_mode
    
    def _is_transition_ready(self, recommended_mode: NarrativeMode) -> bool:
        """Check if transition to recommended mode is ready."""
        if recommended_mode == self.current_mode:
            return False
        
        # Minimum turns in mode before transition
        min_turns = {
            NarrativeMode.ROAM: 1,
            NarrativeMode.SPARK: 2,
            NarrativeMode.PRESSURE: 3,
            NarrativeMode.OUTCOME: 1
        }
        
        return self.turns_in_mode >= min_turns.get(self.current_mode, 1)
    
    def _generate_transition_reasoning(
        self,
        recommended_mode: NarrativeMode,
        has_want: bool,
        has_friction: bool,
        has_closure: bool
    ) -> str:
        """Generate reasoning for mode transition."""
        if recommended_mode == self.current_mode:
            return f"Staying in {self.current_mode.value.upper()} mode"
        
        reasons = []
        if has_want:
            reasons.append("user expressed desire/goal")
        if has_friction:
            reasons.append("repeated obstacles detected")
        if has_closure:
            reasons.append("natural resolution point")
        
        if not reasons:
            reasons.append(f"natural progression after {self.turns_in_mode} turns")
        
        return f"Transition to {recommended_mode.value.upper()}: {', '.join(reasons)}"
    
    def execute_transition(self, new_mode: NarrativeMode) -> Dict[str, Any]:
        """Execute mode transition and return transition data."""
        old_mode = self.current_mode
        
        # Record transition
        self.mode_history.append({
            'from': old_mode.value,
            'to': new_mode.value,
            'turns_in_previous': self.turns_in_mode
        })
        
        # Update mode
        self.current_mode = new_mode
        self.turns_in_mode = 0
        
        # Clear signals
        self.want_signals = []
        self.friction_signals = []
        self.closure_signals = []
        
        # Adjust momentum and tension
        self._update_momentum_and_tension(new_mode)
        
        # Generate transition narrative
        transition_narrative = self._generate_transition_narrative(old_mode, new_mode)
        
        return {
            'old_mode': old_mode.value,
            'new_mode': new_mode.value,
            'transition_narrative': transition_narrative,
            'narrative_momentum': self.narrative_momentum,
            'tension_level': self.tension_level
        }
    
    def _update_momentum_and_tension(self, new_mode: NarrativeMode):
        """Update narrative momentum and tension based on mode."""
        if new_mode == NarrativeMode.ROAM:
            self.narrative_momentum = max(-5, self.narrative_momentum - 2)
            self.tension_level = max(0, self.tension_level - 3)
        
        elif new_mode == NarrativeMode.SPARK:
            self.narrative_momentum = min(5, self.narrative_momentum + 1)
            self.tension_level = min(10, self.tension_level + 2)
        
        elif new_mode == NarrativeMode.PRESSURE:
            self.narrative_momentum = min(5, self.narrative_momentum + 2)
            self.tension_level = min(10, self.tension_level + 3)
        
        elif new_mode == NarrativeMode.OUTCOME:
            self.narrative_momentum = 0
            self.tension_level = max(0, self.tension_level - 2)
    
    def _generate_transition_narrative(
        self,
        old_mode: NarrativeMode,
        new_mode: NarrativeMode
    ) -> str:
        """Generate narrative text for mode transition."""
        transitions = {
            (NarrativeMode.ROAM, NarrativeMode.SPARK): "Something catches your attention...",
            (NarrativeMode.SPARK, NarrativeMode.PRESSURE): "The situation intensifies...",
            (NarrativeMode.PRESSURE, NarrativeMode.OUTCOME): "A moment of resolution approaches...",
            (NarrativeMode.OUTCOME, NarrativeMode.ROAM): "Things settle back to normal...",
            (NarrativeMode.ROAM, NarrativeMode.PRESSURE): "Suddenly, tension rises...",
            (NarrativeMode.SPARK, NarrativeMode.OUTCOME): "The opportunity resolves quickly...",
        }
        
        return transitions.get((old_mode, new_mode), "The narrative shifts...")
    
    def increment_turn(self):
        """Increment turn counter for current mode."""
        self.turns_in_mode += 1
    
    def get_mode_guidance(self) -> str:
        """Get guidance text for current mode."""
        guidance = {
            NarrativeMode.ROAM: "Explore freely, socialize, discover. Low stakes, drift-friendly.",
            NarrativeMode.SPARK: "Opportunities arise, hooks appear. Gentle nudge toward purpose.",
            NarrativeMode.PRESSURE: "Stakes heighten, obstacles emerge. Tension and challenge.",
            NarrativeMode.OUTCOME: "Resolution and consequences. Reflection and closure."
        }
        return guidance.get(self.current_mode, "")
    
    def display_mode_status(self):
        """Display current mode status."""
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}📖 NARRATIVE MODE STATUS{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}Current Mode: {self.current_mode.value.upper()}{Color.RESET}")
        print(f"{Color.SYSTEM}Turns in Mode: {self.turns_in_mode}{Color.RESET}")
        print(f"{Color.SYSTEM}Momentum: {self.narrative_momentum:+d}/5{Color.RESET}")
        print(f"{Color.SYSTEM}Tension: {self.tension_level}/10{Color.RESET}")
        print(f"{Color.NARRATIVE}Guidance: {self.get_mode_guidance()}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
mode_transition_enhancer = ModeTransitionEnhancer()
