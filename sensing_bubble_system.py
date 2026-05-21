"""
Sensing Bubble System - Coordinate-based sensory perception

Implements math-first verification of what actors can perceive based on:
- Distance from observer to target
- Sense-specific range parameters
- Environmental modifiers
- Priority sense selection (1-2 most relevant senses)

All calculations are done in code BEFORE LLM narrative processing,
following the UTAS model of math verification first.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import math


# ═══════════════════════════════════════════════════════════════════════════════
# SENSORY RANGE CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

class SenseType(Enum):
    """Types of senses for perception"""
    VISION = "vision"
    HEARING = "hearing"
    SMELL = "smell"
    TOUCH = "touch"
    TASTE = "taste"


@dataclass
class SensoryRanges:
    """
    Fixed sensory range parameters (in map units).
    
    Calibrated for 250x200 unit buildings:
    - Vision: ~100 units (half the building - walls block)
    - Hearing: ~80 units (sound travels through walls somewhat)
    - Smell: ~30 units (closer range)
    - Touch/Taste: ~2-3 units (tactile contact)
    
    These match pygame_spatial_map.SensoryRange for consistency.
    """
    # Primary senses - synced with pygame_spatial_map
    VISION_MAX: float = 100.0       # Maximum vision range (walls block)
    VISION_DETAIL: float = 50.0     # Range for detailed visual info
    VISION_CLEAR: float = 20.0      # Range for clear facial features
    
    HEARING_MAX: float = 80.0       # Maximum hearing range
    HEARING_SPEECH: float = 15.0    # Normal conversation range
    HEARING_WHISPER: float = 3.0    # Whisper range
    
    SMELL_MAX: float = 30.0         # Maximum smell range
    SMELL_STRONG: float = 15.0      # Strong odor range
    SMELL_SUBTLE: float = 8.0       # Subtle scent range
    
    TOUCH_MAX: float = 2.0          # Must be within arm's reach
    TASTE_MAX: float = 1.0          # Must be in contact


# Default ranges
DEFAULT_RANGES = SensoryRanges()


# ═══════════════════════════════════════════════════════════════════════════════
# SENSORY PERCEPTION RESULT
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensePerception:
    """Result of a single sense check"""
    sense: SenseType
    can_perceive: bool
    distance: float
    quality: str  # "clear", "partial", "faint", "none"
    detail_level: int  # 0-3 (none, low, medium, high)
    priority_score: float = 0.0  # For ranking sense relevance


@dataclass
class SensingBubbleResult:
    """Complete sensing bubble result for an observer"""
    observer_id: str
    observer_position: Tuple[float, float]
    target_id: str
    target_position: Tuple[float, float]
    distance: float
    
    # Individual sense results
    vision: SensePerception = None
    hearing: SensePerception = None
    smell: SensePerception = None
    touch: SensePerception = None
    taste: SensePerception = None
    
    # Priority senses (1-2 most relevant)
    priority_senses: List[SenseType] = field(default_factory=list)
    
    # Environmental modifiers applied
    modifiers: Dict[str, float] = field(default_factory=dict)
    
    def get_available_senses(self) -> List[SenseType]:
        """Get list of senses that can perceive the target"""
        available = []
        for sense_result in [self.vision, self.hearing, self.smell, self.touch, self.taste]:
            if sense_result and sense_result.can_perceive:
                available.append(sense_result.sense)
        return available
    
    def get_best_sense(self) -> Optional[SenseType]:
        """Get the highest priority sense that can perceive"""
        if self.priority_senses:
            return self.priority_senses[0]
        available = self.get_available_senses()
        return available[0] if available else None
    
    def format_for_narrative(self) -> str:
        """Format sensing result for LLM narrative prompt"""
        if not self.priority_senses:
            return "Cannot perceive target."
        
        parts = []
        for sense in self.priority_senses[:2]:
            result = getattr(self, sense.value, None)
            if result and result.can_perceive:
                parts.append(f"{sense.value}: {result.quality} ({result.distance:.1f} units)")
        
        return f"Priority senses: {', '.join(parts)}"


# ═══════════════════════════════════════════════════════════════════════════════
# SENSING BUBBLE CALCULATOR
# ═══════════════════════════════════════════════════════════════════════════════

class SensingBubbleCalculator:
    """
    Calculates what an observer can perceive of a target.
    
    Math-first approach: All distance calculations happen in code,
    then results are passed to LLM for narrative consistency.
    """
    
    def __init__(self, ranges: SensoryRanges = None):
        self.ranges = ranges or DEFAULT_RANGES
    
    def calculate_distance(self, pos1: Tuple[float, float], 
                          pos2: Tuple[float, float]) -> float:
        """Calculate Euclidean distance between two positions"""
        dx = pos2[0] - pos1[0]
        dy = pos2[1] - pos1[1]
        return math.sqrt(dx * dx + dy * dy)
    
    def check_vision(self, distance: float, 
                     modifiers: Dict[str, float] = None) -> SensePerception:
        """Check visual perception at distance"""
        modifiers = modifiers or {}
        
        # Apply modifiers (darkness, fog, etc.)
        effective_range = self.ranges.VISION_MAX * modifiers.get('visibility', 1.0)
        
        if distance > effective_range:
            return SensePerception(
                sense=SenseType.VISION,
                can_perceive=False,
                distance=distance,
                quality="none",
                detail_level=0
            )
        
        # Determine quality based on distance
        if distance <= self.ranges.VISION_CLEAR:
            quality = "clear"
            detail = 3
        elif distance <= self.ranges.VISION_DETAIL:
            quality = "partial"
            detail = 2
        elif distance <= effective_range:
            quality = "faint"
            detail = 1
        else:
            quality = "none"
            detail = 0
        
        # Priority score (closer = higher priority)
        priority = max(0, 1.0 - (distance / effective_range))
        
        return SensePerception(
            sense=SenseType.VISION,
            can_perceive=detail > 0,
            distance=distance,
            quality=quality,
            detail_level=detail,
            priority_score=priority
        )
    
    def check_hearing(self, distance: float,
                      modifiers: Dict[str, float] = None) -> SensePerception:
        """Check auditory perception at distance"""
        modifiers = modifiers or {}
        
        # Apply modifiers (noise, soundproofing, etc.)
        effective_range = self.ranges.HEARING_MAX * modifiers.get('sound_clarity', 1.0)
        
        if distance > effective_range:
            return SensePerception(
                sense=SenseType.HEARING,
                can_perceive=False,
                distance=distance,
                quality="none",
                detail_level=0
            )
        
        # Determine quality
        if distance <= self.ranges.HEARING_WHISPER:
            quality = "clear"  # Can hear whispers
            detail = 3
        elif distance <= self.ranges.HEARING_SPEECH:
            quality = "partial"  # Normal speech
            detail = 2
        elif distance <= effective_range:
            quality = "faint"  # Only loud sounds
            detail = 1
        else:
            quality = "none"
            detail = 0
        
        priority = max(0, 1.0 - (distance / effective_range))
        
        return SensePerception(
            sense=SenseType.HEARING,
            can_perceive=detail > 0,
            distance=distance,
            quality=quality,
            detail_level=detail,
            priority_score=priority
        )
    
    def check_smell(self, distance: float,
                    modifiers: Dict[str, float] = None) -> SensePerception:
        """Check olfactory perception at distance"""
        modifiers = modifiers or {}
        
        # Apply modifiers (wind, strong odors, etc.)
        effective_range = self.ranges.SMELL_MAX * modifiers.get('scent_strength', 1.0)
        
        if distance > effective_range:
            return SensePerception(
                sense=SenseType.SMELL,
                can_perceive=False,
                distance=distance,
                quality="none",
                detail_level=0
            )
        
        if distance <= self.ranges.SMELL_SUBTLE:
            quality = "clear"
            detail = 3
        elif distance <= self.ranges.SMELL_STRONG:
            quality = "partial"
            detail = 2
        elif distance <= effective_range:
            quality = "faint"
            detail = 1
        else:
            quality = "none"
            detail = 0
        
        # Smell has lower base priority than vision/hearing
        priority = max(0, 0.7 * (1.0 - (distance / effective_range)))
        
        return SensePerception(
            sense=SenseType.SMELL,
            can_perceive=detail > 0,
            distance=distance,
            quality=quality,
            detail_level=detail,
            priority_score=priority
        )
    
    def check_touch(self, distance: float) -> SensePerception:
        """Check tactile perception (requires close proximity)"""
        can_touch = distance <= self.ranges.TOUCH_MAX
        
        return SensePerception(
            sense=SenseType.TOUCH,
            can_perceive=can_touch,
            distance=distance,
            quality="clear" if can_touch else "none",
            detail_level=3 if can_touch else 0,
            priority_score=1.0 if can_touch else 0.0  # Highest priority when available
        )
    
    def check_taste(self, distance: float) -> SensePerception:
        """Check taste perception (requires contact)"""
        can_taste = distance <= self.ranges.TASTE_MAX
        
        return SensePerception(
            sense=SenseType.TASTE,
            can_perceive=can_taste,
            distance=distance,
            quality="clear" if can_taste else "none",
            detail_level=3 if can_taste else 0,
            priority_score=0.5 if can_taste else 0.0  # Lower priority than touch
        )
    
    def calculate_sensing_bubble(self,
                                  observer_id: str,
                                  observer_pos: Tuple[float, float],
                                  target_id: str,
                                  target_pos: Tuple[float, float],
                                  modifiers: Dict[str, float] = None) -> SensingBubbleResult:
        """
        Calculate complete sensing bubble for observer perceiving target.
        
        Args:
            observer_id: ID of the observing actor
            observer_pos: (x, y) position of observer
            target_id: ID of the target
            target_pos: (x, y) position of target
            modifiers: Environmental modifiers (visibility, sound_clarity, etc.)
        
        Returns:
            SensingBubbleResult with all sense checks and priority ranking
        """
        modifiers = modifiers or {}
        distance = self.calculate_distance(observer_pos, target_pos)
        
        # Check all senses
        vision = self.check_vision(distance, modifiers)
        hearing = self.check_hearing(distance, modifiers)
        smell = self.check_smell(distance, modifiers)
        touch = self.check_touch(distance)
        taste = self.check_taste(distance)
        
        # Determine priority senses (top 2 by score, must be perceivable)
        sense_results = [vision, hearing, smell, touch, taste]
        perceivable = [s for s in sense_results if s.can_perceive]
        perceivable.sort(key=lambda s: s.priority_score, reverse=True)
        
        priority_senses = [s.sense for s in perceivable[:2]]
        
        return SensingBubbleResult(
            observer_id=observer_id,
            observer_position=observer_pos,
            target_id=target_id,
            target_position=target_pos,
            distance=distance,
            vision=vision,
            hearing=hearing,
            smell=smell,
            touch=touch,
            taste=taste,
            priority_senses=priority_senses,
            modifiers=modifiers
        )
    
    def get_all_perceivable_targets(self,
                                     observer_id: str,
                                     observer_pos: Tuple[float, float],
                                     targets: Dict[str, Tuple[float, float]],
                                     modifiers: Dict[str, float] = None) -> List[SensingBubbleResult]:
        """
        Calculate sensing bubbles for all targets from observer's position.
        
        Returns list sorted by distance (closest first).
        """
        results = []
        
        for target_id, target_pos in targets.items():
            if target_id == observer_id:
                continue
            
            result = self.calculate_sensing_bubble(
                observer_id, observer_pos,
                target_id, target_pos,
                modifiers
            )
            
            # Only include if at least one sense can perceive
            if result.get_available_senses():
                results.append(result)
        
        # Sort by distance
        results.sort(key=lambda r: r.distance)
        
        return results


# ═══════════════════════════════════════════════════════════════════════════════
# PRIORITY SENSE SELECTION
# ═══════════════════════════════════════════════════════════════════════════════

def select_priority_senses(result: SensingBubbleResult,
                           actor_traits: Dict[str, int] = None,
                           context: str = "") -> List[SenseType]:
    """
    Select 1-2 priority senses based on:
    - What's actually perceivable
    - Actor's S-trait outliers (enhanced senses)
    - Environmental context
    
    Args:
        result: SensingBubbleResult from calculator
        actor_traits: S-trait values (smart affects observation, etc.)
        context: Scene context for relevance
    
    Returns:
        List of 1-2 priority SenseTypes
    """
    if not result.get_available_senses():
        return []
    
    actor_traits = actor_traits or {}
    
    # Base scores from sensing bubble
    scores = {}
    for sense_result in [result.vision, result.hearing, result.smell, 
                         result.touch, result.taste]:
        if sense_result and sense_result.can_perceive:
            scores[sense_result.sense] = sense_result.priority_score
    
    # Modify based on actor traits
    smart = actor_traits.get('smart', 3)
    if smart >= 4:
        # High intelligence = better visual observation
        if SenseType.VISION in scores:
            scores[SenseType.VISION] *= 1.2
    
    # Context-based modifications
    context_lower = context.lower()
    
    if any(word in context_lower for word in ['dark', 'night', 'blind', 'fog']):
        # Reduced visibility - boost hearing
        if SenseType.VISION in scores:
            scores[SenseType.VISION] *= 0.5
        if SenseType.HEARING in scores:
            scores[SenseType.HEARING] *= 1.5
    
    if any(word in context_lower for word in ['loud', 'noisy', 'music', 'crowd']):
        # Noisy environment - reduce hearing priority
        if SenseType.HEARING in scores:
            scores[SenseType.HEARING] *= 0.5
    
    if any(word in context_lower for word in ['smell', 'odor', 'stench', 'perfume', 'food']):
        # Smell is relevant
        if SenseType.SMELL in scores:
            scores[SenseType.SMELL] *= 1.5
    
    # Sort by score and return top 2
    sorted_senses = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    return [sense for sense, score in sorted_senses[:2]]


def format_sensing_for_prompt(results: List[SensingBubbleResult], 
                              actor_names: Dict[str, str] = None) -> str:
    """
    Format sensing bubble results for inclusion in LLM prompts.
    
    Args:
        results: List of SensingBubbleResult for all perceivable targets
        actor_names: Optional dict mapping actor_id to display name
    
    Returns:
        Formatted string for prompt injection
    """
    if not results:
        return "No one else is nearby."
    
    actor_names = actor_names or {}
    
    # Group by sense quality
    clearly_visible = []
    visible = []
    heard_only = []
    smelled_only = []
    within_reach = []
    
    for r in results:
        name = actor_names.get(r.target_id, r.target_id)
        dist = r.distance
        
        # Categorize by primary sense
        if r.touch and r.touch.can_perceive:
            within_reach.append(f"{name} ({dist:.0f}u)")
        elif r.vision and r.vision.can_perceive:
            if r.vision.quality == "clear":
                clearly_visible.append(f"{name} ({dist:.0f}u)")
            else:
                visible.append(f"{name} ({dist:.0f}u)")
        elif r.hearing and r.hearing.can_perceive:
            heard_only.append(f"{name} ({dist:.0f}u)")
        elif r.smell and r.smell.can_perceive:
            smelled_only.append(f"{name} ({dist:.0f}u)")
    
    parts = []
    if within_reach:
        parts.append(f"WITHIN REACH: {', '.join(within_reach)}")
    if clearly_visible:
        parts.append(f"CLEARLY VISIBLE: {', '.join(clearly_visible)}")
    if visible:
        parts.append(f"VISIBLE: {', '.join(visible)}")
    if heard_only:
        parts.append(f"HEARD (not seen): {', '.join(heard_only)}")
    if smelled_only:
        parts.append(f"SMELLED: {', '.join(smelled_only)}")
    
    return "\n".join(parts) if parts else "No one else is nearby."


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION WITH SPATIAL CONTEXT
# ═══════════════════════════════════════════════════════════════════════════════

def get_sensing_bubble_from_spatial(observer_id: str, target_id: str,
                                     session_id: str = None,
                                     modifiers: Dict[str, float] = None) -> Optional[SensingBubbleResult]:
    """
    Get sensing bubble using existing spatial context system.
    
    Bridges the sensing bubble calculator with spatial_context_system.
    """
    try:
        from spatial_context_system import get_spatial_manager
        
        spatial = get_spatial_manager(session_id=session_id)
        context = spatial.get_current_context()
        
        if not context:
            return None
        
        observer_pos = context.actor_positions.get(observer_id)
        target_pos = context.actor_positions.get(target_id)
        
        if not observer_pos or not target_pos:
            return None
        
        calculator = SensingBubbleCalculator()
        return calculator.calculate_sensing_bubble(
            observer_id,
            (observer_pos.position.x, observer_pos.position.y),
            target_id,
            (target_pos.position.x, target_pos.position.y),
            modifiers
        )
    except ImportError:
        return None
    except Exception as e:
        print(f"[SENSING] Error calculating bubble: {e}")
        return None


def get_all_perceivable_from_spatial(observer_id: str,
                                      session_id: str = None,
                                      modifiers: Dict[str, float] = None) -> List[SensingBubbleResult]:
    """
    Get sensing bubbles for all actors from observer's position.
    """
    try:
        from spatial_context_system import get_spatial_manager
        
        spatial = get_spatial_manager(session_id=session_id)
        context = spatial.get_current_context()
        
        if not context:
            return []
        
        observer_pos = context.actor_positions.get(observer_id)
        if not observer_pos:
            return []
        
        # Build targets dict
        targets = {}
        for actor_id, actor_pos in context.actor_positions.items():
            targets[actor_id] = (actor_pos.position.x, actor_pos.position.y)
        
        calculator = SensingBubbleCalculator()
        return calculator.get_all_perceivable_targets(
            observer_id,
            (observer_pos.position.x, observer_pos.position.y),
            targets,
            modifiers
        )
    except ImportError:
        return []
    except Exception as e:
        print(f"[SENSING] Error getting perceivable targets: {e}")
        return []


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Sensing Bubble System Test\n")
    
    calculator = SensingBubbleCalculator()
    
    # Test scenarios
    test_cases = [
        ("Close range", (0, 0), (2, 0)),      # 2 units - touch range
        ("Conversation", (0, 0), (5, 0)),     # 5 units - speech range
        ("Across room", (0, 0), (15, 0)),     # 15 units - visual detail
        ("Far away", (0, 0), (100, 0)),       # 100 units - distant
        ("Max range", (0, 0), (250, 0)),      # 250 units - edge of perception
        ("Out of range", (0, 0), (300, 0)),   # 300 units - beyond perception
    ]
    
    for name, observer_pos, target_pos in test_cases:
        result = calculator.calculate_sensing_bubble(
            "observer", observer_pos,
            "target", target_pos
        )
        
        print(f"=== {name} ({result.distance:.1f} units) ===")
        print(f"  Vision: {result.vision.quality} (detail: {result.vision.detail_level})")
        print(f"  Hearing: {result.hearing.quality} (detail: {result.hearing.detail_level})")
        print(f"  Smell: {result.smell.quality} (detail: {result.smell.detail_level})")
        print(f"  Touch: {result.touch.quality}")
        print(f"  Priority senses: {[s.value for s in result.priority_senses]}")
        print()
    
    print("✅ Sensing bubble system ready!")
