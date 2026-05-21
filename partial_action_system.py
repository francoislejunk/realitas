"""
Partial Action System - Diegetic Interpretation of Incomplete Actions

Core Philosophy:
- NEVER deny user actions due to distance/time constraints
- ALWAYS interpret actions as partially accomplished
- Generate DIEGETIC explanations for why action didn't fully complete
- Reinterpret action intent based on what was actually achieved

Design Principles:
1. **No Denial**: User always acts, even if conditions aren't perfect
2. **Diegetic Explanation**: Fiction-based reasons for partial completion
3. **Dynamic Reinterpretation**: Adjust action based on what actually happened
4. **Narrative Consistency**: Explanations fit the world and situation

Examples:
- Goal: "Run to NUA and hug them" (20 units, 3 UT available, need 5 UT)
  Result: "You sprint toward them but trip over debris halfway, sprawling on the ground"
  Reinterpretation: Action becomes "run partway and fall"

- Goal: "Whisper secret to guard" (8 units away, whisper needs 0-2 units)
  Result: "You lean in to whisper but they're too far - your words come out as a hushed call"
  Reinterpretation: Action becomes "speak quietly from distance"
"""

import random
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum

from spatial_context_system import Position, MovementSpeed, DistanceCategory


class PartialActionReason(Enum):
    """Categories of why an action was only partially completed"""
    INSUFFICIENT_TIME = "insufficient_time"          # Ran out of UT
    OUT_OF_RANGE = "out_of_range"                   # Target too far for action type
    OBSTACLE_INTERFERENCE = "obstacle_interference"  # Physical obstacle in the way
    INTERRUPTED = "interrupted"                      # Another actor interfered
    EXHAUSTION = "exhaustion"                        # Actor too tired/injured
    ENVIRONMENTAL = "environmental"                  # Weather, terrain, etc.


@dataclass
class PartialActionResult:
    """Result of partial action interpretation"""
    original_intent: str                    # What user wanted to do
    actual_outcome: str                     # What actually happened
    partial_completion_percent: float       # 0.0 to 1.0 (how much was achieved)
    diegetic_explanation: str              # Why it didn't fully complete
    reinterpreted_action: str              # New action description for mechanics
    reason_category: PartialActionReason   # Category of partial completion
    distance_covered: Optional[float] = None  # If movement involved
    time_used: Optional[int] = None        # UT consumed
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "original_intent": self.original_intent,
            "actual_outcome": self.actual_outcome,
            "partial_completion_percent": self.partial_completion_percent,
            "diegetic_explanation": self.diegetic_explanation,
            "reinterpreted_action": self.reinterpreted_action,
            "reason_category": self.reason_category.value,
            "distance_covered": self.distance_covered,
            "time_used": self.time_used
        }


class PartialActionInterpreter:
    """
    Interprets actions that cannot be fully completed due to constraints.
    
    Never denies actions - always finds diegetic way to explain partial completion.
    """
    
    def __init__(self):
        # Diegetic explanation templates for different scenarios
        self.explanation_templates = {
            PartialActionReason.INSUFFICIENT_TIME: [
                "you run out of time before completing the action",
                "you're interrupted mid-action",
                "you have to stop before finishing",
                "you only manage to partially complete it",
                "time runs out before you can finish"
            ],
            PartialActionReason.OUT_OF_RANGE: [
                "they're too far away",
                "the distance is too great",
                "you can't quite reach them",
                "they're out of range",
                "the gap between you is too wide"
            ],
            PartialActionReason.OBSTACLE_INTERFERENCE: [
                "an obstacle blocks your path",
                "you have to navigate around obstacles",
                "something gets in the way",
                "you're impeded by the environment",
                "physical barriers slow you down"
            ],
            PartialActionReason.EXHAUSTION: [
                "you're too exhausted to continue",
                "fatigue catches up with you",
                "your injuries slow you down",
                "you don't have the energy",
                "your body can't keep up"
            ],
            PartialActionReason.ENVIRONMENTAL: [
                "the terrain works against you",
                "environmental conditions interfere",
                "the weather hampers your efforts",
                "the ground is treacherous",
                "the environment makes it difficult"
            ]
        }
        
        # Movement failure scenarios (diegetic reasons for not reaching destination)
        self.movement_failures = [
            "you trip over {obstacle} and sprawl on the ground",
            "you stumble on {obstacle} and catch yourself",
            "you slip on {surface} and lose your footing",
            "you collide with {obstacle} and stagger back",
            "you lose your balance on {surface} and have to steady yourself",
            "you misjudge the distance and have to slow down",
            "you get tangled in {obstacle} and have to stop",
            "you're forced to dodge {obstacle} and lose momentum",
            "you skid on {surface} and slide to a halt",
            "you're blocked by {obstacle} and have to find another way"
        ]
        
        # Environmental elements for failure scenarios
        self.obstacles = [
            "debris", "a chair", "scattered tools", "boxes", "equipment",
            "furniture", "a cable", "clutter", "a cart", "supplies"
        ]
        
        self.surfaces = [
            "a wet patch", "loose gravel", "an oil slick", "the slick floor",
            "uneven ground", "a puddle", "the smooth surface", "spilled liquid"
        ]
    
    def interpret_movement_action(self, 
                                 original_action: str,
                                 start_pos: Position,
                                 target_pos: Position,
                                 available_ut: int,
                                 speed: MovementSpeed = MovementSpeed.WALK,
                                 swiftness: int = 3) -> PartialActionResult:
        """
        Interpret a movement-based action that may not fully complete.
        
        Args:
            original_action: User's intended action (e.g., "run to guard and hug them")
            start_pos: Starting position
            target_pos: Target position
            available_ut: UT available for action
            speed: Movement speed
            swiftness: Actor's Swiftness S-trait (1-5, default: 3)
        
        Returns:
            PartialActionResult with diegetic explanation
        """
        # Calculate full movement time needed (with swiftness modifier)
        total_distance = start_pos.distance_to(target_pos)
        seconds_needed, ut_needed = start_pos.calculate_movement_time_with_ut(target_pos, speed, swiftness)
        
        # Calculate how far they actually get
        if available_ut >= ut_needed:
            # They have enough time - full completion
            return PartialActionResult(
                original_intent=original_action,
                actual_outcome=original_action,
                partial_completion_percent=1.0,
                diegetic_explanation="You complete the action successfully",
                reinterpreted_action=original_action,
                reason_category=PartialActionReason.INSUFFICIENT_TIME,
                distance_covered=total_distance,
                time_used=ut_needed
            )
        
        # Partial completion - calculate how far they get
        from spatial_context_system import get_effective_speed
        seconds_available = available_ut * 3  # 3 seconds per UT
        effective_speed = get_effective_speed(speed, swiftness)
        distance_covered = effective_speed * seconds_available
        completion_percent = min(distance_covered / total_distance, 0.95)  # Cap at 95%
        
        # Generate diegetic explanation for why they didn't make it
        obstacle = random.choice(self.obstacles)
        surface = random.choice(self.surfaces)
        failure_template = random.choice(self.movement_failures)
        
        # Randomly choose obstacle or surface
        if random.random() > 0.5:
            failure_reason = failure_template.format(obstacle=obstacle, surface="")
        else:
            failure_reason = failure_template.format(obstacle="", surface=surface)
        
        # Clean up formatting
        failure_reason = failure_reason.replace("  ", " ").strip()
        
        # Determine what actually happened
        if completion_percent < 0.3:
            actual_outcome = f"You start moving toward the target but {failure_reason} early on"
            reinterpreted_action = "attempt to move but fail early"
        elif completion_percent < 0.6:
            actual_outcome = f"You make it about halfway before {failure_reason}"
            reinterpreted_action = "move partway toward target"
        else:
            actual_outcome = f"You nearly reach the target but {failure_reason} at the last moment"
            reinterpreted_action = "move close to target but don't quite reach"
        
        return PartialActionResult(
            original_intent=original_action,
            actual_outcome=actual_outcome,
            partial_completion_percent=completion_percent,
            diegetic_explanation=failure_reason,
            reinterpreted_action=reinterpreted_action,
            reason_category=PartialActionReason.INSUFFICIENT_TIME,
            distance_covered=distance_covered,
            time_used=available_ut
        )
    
    def interpret_ranged_action(self,
                               original_action: str,
                               action_type: str,
                               current_distance: float,
                               required_distance_category: DistanceCategory,
                               actual_distance_category: DistanceCategory) -> PartialActionResult:
        """
        Interpret an action that requires specific range but actor is too far/close.
        
        Args:
            original_action: User's intended action
            action_type: Type of action (whisper, shout, throw, etc.)
            current_distance: Actual distance to target
            required_distance_category: Required range for action
            actual_distance_category: Actual range category
        
        Returns:
            PartialActionResult with diegetic explanation
        """
        # Determine if too far or too close
        distance_categories_ordered = [
            DistanceCategory.IMMEDIATE,
            DistanceCategory.CLOSE,
            DistanceCategory.NEAR,
            DistanceCategory.FAR,
            DistanceCategory.DISTANT
        ]
        
        required_idx = distance_categories_ordered.index(required_distance_category)
        actual_idx = distance_categories_ordered.index(actual_distance_category)
        
        if actual_idx > required_idx:
            # Too far
            return self._interpret_too_far(original_action, action_type, current_distance)
        else:
            # Too close (rare but possible)
            return self._interpret_too_close(original_action, action_type, current_distance)
    
    def _interpret_too_far(self, original_action: str, action_type: str, distance: float) -> PartialActionResult:
        """Interpret action when target is too far"""
        
        # Action-specific interpretations
        interpretations = {
            "whisper": {
                "outcome": "You lean in to whisper but they're too far - your words come out as a hushed call",
                "reinterpreted": "speak quietly from a distance",
                "completion": 0.6
            },
            "touch": {
                "outcome": "You reach out but can't quite make contact - your hand grasps at empty air",
                "reinterpreted": "reach toward target without touching",
                "completion": 0.3
            },
            "grab": {
                "outcome": "You lunge forward to grab them but they're just out of reach",
                "reinterpreted": "attempt to grab but miss",
                "completion": 0.4
            },
            "melee": {
                "outcome": "You swing but the distance is too great - your attack falls short",
                "reinterpreted": "swing at empty air",
                "completion": 0.2
            },
            "throw": {
                "outcome": "You throw but the target is too far - the object falls short",
                "reinterpreted": "throw object that doesn't reach target",
                "completion": 0.5
            },
            "talk": {
                "outcome": "You try to speak normally but have to raise your voice to be heard",
                "reinterpreted": "speak louder than intended",
                "completion": 0.8
            }
        }
        
        # Get interpretation or use default
        interp = interpretations.get(action_type.lower(), {
            "outcome": f"You attempt the action but the distance is too great - it doesn't quite work",
            "reinterpreted": "attempt action from too far away",
            "completion": 0.5
        })
        
        return PartialActionResult(
            original_intent=original_action,
            actual_outcome=interp["outcome"],
            partial_completion_percent=interp["completion"],
            diegetic_explanation=f"Target is {distance:.1f} units away - too far for {action_type}",
            reinterpreted_action=interp["reinterpreted"],
            reason_category=PartialActionReason.OUT_OF_RANGE,
            distance_covered=None,
            time_used=1  # Still takes time to attempt
        )
    
    def _interpret_too_close(self, original_action: str, action_type: str, distance: float) -> PartialActionResult:
        """Interpret action when target is too close (rare)"""
        
        return PartialActionResult(
            original_intent=original_action,
            actual_outcome=f"You're too close to effectively {action_type} - you have to adjust",
            partial_completion_percent=0.7,
            diegetic_explanation=f"Target is only {distance:.1f} units away - too close for {action_type}",
            reinterpreted_action=f"awkwardly attempt {action_type} from too close",
            reason_category=PartialActionReason.OUT_OF_RANGE,
            distance_covered=None,
            time_used=1
        )
    
    def interpret_combined_action(self,
                                 original_action: str,
                                 movement_component: Optional[PartialActionResult],
                                 action_component: str,
                                 action_ut_cost: int,
                                 total_ut_available: int) -> PartialActionResult:
        """
        Interpret combined action (movement + action) that may not fully complete.
        
        Args:
            original_action: Full intended action (e.g., "run to guard and punch them")
            movement_component: Result of movement interpretation (if any)
            action_component: The action to perform after movement
            action_ut_cost: UT cost of the action itself
            total_ut_available: Total UT available
        
        Returns:
            PartialActionResult for the combined action
        """
        if not movement_component:
            # No movement needed, just action
            return PartialActionResult(
                original_intent=original_action,
                actual_outcome=original_action,
                partial_completion_percent=1.0,
                diegetic_explanation="Action completed successfully",
                reinterpreted_action=original_action,
                reason_category=PartialActionReason.INSUFFICIENT_TIME,
                time_used=action_ut_cost
            )
        
        # Check if there's time for both movement and action
        movement_ut = movement_component.time_used or 0
        total_needed = movement_ut + action_ut_cost
        
        if total_needed <= total_ut_available:
            # Enough time for both
            return PartialActionResult(
                original_intent=original_action,
                actual_outcome=original_action,
                partial_completion_percent=1.0,
                diegetic_explanation="Action completed successfully",
                reinterpreted_action=original_action,
                reason_category=PartialActionReason.INSUFFICIENT_TIME,
                distance_covered=movement_component.distance_covered,
                time_used=total_needed
            )
        
        # Not enough time - movement happens but action doesn't
        if movement_component.partial_completion_percent < 1.0:
            # Movement itself was partial
            outcome = f"{movement_component.actual_outcome}. You don't have time to {action_component}"
            reinterpreted = movement_component.reinterpreted_action
            completion = movement_component.partial_completion_percent * 0.5  # Half credit
        else:
            # Movement completed but no time for action
            outcome = f"You reach the target but run out of time before you can {action_component}"
            reinterpreted = f"move to target without {action_component}"
            completion = 0.7  # Got there but didn't act
        
        return PartialActionResult(
            original_intent=original_action,
            actual_outcome=outcome,
            partial_completion_percent=completion,
            diegetic_explanation=f"Only {total_ut_available} UT available, needed {total_needed} UT",
            reinterpreted_action=reinterpreted,
            reason_category=PartialActionReason.INSUFFICIENT_TIME,
            distance_covered=movement_component.distance_covered,
            time_used=total_ut_available
        )
    
    def generate_narrative_description(self, result: PartialActionResult, 
                                      actor_name: str = "You") -> str:
        """
        Generate narrative description of partial action for display to user.
        
        Args:
            result: PartialActionResult to narrate
            actor_name: Name of actor performing action
        
        Returns:
            Narrative text describing what happened
        """
        if result.partial_completion_percent >= 0.95:
            # Nearly complete - treat as success
            return f"{actor_name} {result.actual_outcome}."
        
        # Partial completion - emphasize what was achieved and why it stopped
        completion_desc = ""
        if result.partial_completion_percent < 0.3:
            completion_desc = "barely begin"
        elif result.partial_completion_percent < 0.6:
            completion_desc = "partially complete"
        else:
            completion_desc = "nearly complete"
        
        narrative = f"{actor_name} {completion_desc} the action. {result.actual_outcome}."
        
        return narrative


# === GLOBAL ACCESSOR ===

_partial_action_interpreter: Optional[PartialActionInterpreter] = None

def get_partial_action_interpreter() -> PartialActionInterpreter:
    """Get or create global partial action interpreter"""
    global _partial_action_interpreter
    if _partial_action_interpreter is None:
        _partial_action_interpreter = PartialActionInterpreter()
    return _partial_action_interpreter
