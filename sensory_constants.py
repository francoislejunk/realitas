"""
Sensory Constants - Universal truth for distance-based perception

This module defines the CANONICAL sensory ranges and capabilities
that ALL agents must use for consistency.

Distance is measured in UNITS where:
- 1 unit ≈ 1 meter / 3 feet
- Walking speed: 2.0 units/second (with Swiftness 3 = 3.0 u/s)

These constants are used by:
- NarratorAgent: To describe what UA can perceive
- InterpreterAgent: To validate action feasibility
- DeciderAgent: To determine NUA awareness
- Spatial System: For distance calculations
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from enum import Enum


# ═══════════════════════════════════════════════════════════════════════════════
# DISTANCE CATEGORIES (from spatial_context_system.py - canonical source)
# ═══════════════════════════════════════════════════════════════════════════════

class DistanceCategory(Enum):
    """Distance categories for action mechanics"""
    IMMEDIATE = "immediate"      # 0-2 units: Touch range, whisper
    CLOSE = "close"              # 3-5 units: Normal conversation
    NEAR = "near"                # 6-10 units: Raised voice, quick movement
    FAR = "far"                  # 11-20 units: Shout, significant movement
    DISTANT = "distant"          # 21+ units: Out of range for most actions


def get_distance_category(distance: float) -> DistanceCategory:
    """Get distance category from distance in units"""
    if distance <= 2:
        return DistanceCategory.IMMEDIATE
    elif distance <= 5:
        return DistanceCategory.CLOSE
    elif distance <= 10:
        return DistanceCategory.NEAR
    elif distance <= 20:
        return DistanceCategory.FAR
    else:
        return DistanceCategory.DISTANT


# ═══════════════════════════════════════════════════════════════════════════════
# SENSORY RANGE THRESHOLDS (in units)
# ═══════════════════════════════════════════════════════════════════════════════

# These are the MAXIMUM distances at which each sense can function
SENSORY_THRESHOLDS = {
    # TOUCH - Physical contact range
    "touch": 2,              # Must be within arm's reach
    
    # SMELL - Olfactory perception
    "smell_strong": 5,       # Strong odors (perfume, smoke, food)
    "smell_faint": 2,        # Faint odors (breath, subtle scents)
    
    # HEARING - Auditory perception
    "whisper": 3,            # Whispered speech
    "normal_speech": 8,      # Normal conversation volume
    "raised_voice": 15,      # Speaking loudly
    "shout": 30,             # Shouting/yelling
    "loud_noise": 50,        # Gunshots, crashes, explosions
    
    # SIGHT - Visual perception
    "facial_detail": 10,     # Expressions, eye color, small features
    "body_language": 15,     # Posture, gestures, general expression
    "identify_person": 25,   # Recognize who someone is
    "see_movement": 50,      # Notice movement, large shapes
    "see_figure": 100,       # See that someone/something is there
}


# ═══════════════════════════════════════════════════════════════════════════════
# SENSORY INFO CLASS
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SensoryCapabilities:
    """
    What senses can perceive at a given distance.
    
    Usage:
        caps = SensoryCapabilities.at_distance(6.5)
        if caps.can_talk:
            # Normal conversation is possible
        if not caps.can_see_detail:
            # Cannot make out facial expressions
    """
    distance: float
    
    # Touch
    can_touch: bool
    
    # Smell
    can_smell_strong: bool
    can_smell_faint: bool
    
    # Hearing
    can_hear_whisper: bool
    can_hear_speech: bool
    can_hear_raised: bool
    can_hear_shout: bool
    can_hear_loud: bool
    
    # Sight
    can_see_facial_detail: bool
    can_see_body_language: bool
    can_identify_person: bool
    can_see_movement: bool
    can_see_figure: bool
    
    @classmethod
    def at_distance(cls, distance: float) -> 'SensoryCapabilities':
        """Create sensory capabilities for a given distance"""
        return cls(
            distance=distance,
            # Touch
            can_touch=distance <= SENSORY_THRESHOLDS["touch"],
            # Smell
            can_smell_strong=distance <= SENSORY_THRESHOLDS["smell_strong"],
            can_smell_faint=distance <= SENSORY_THRESHOLDS["smell_faint"],
            # Hearing
            can_hear_whisper=distance <= SENSORY_THRESHOLDS["whisper"],
            can_hear_speech=distance <= SENSORY_THRESHOLDS["normal_speech"],
            can_hear_raised=distance <= SENSORY_THRESHOLDS["raised_voice"],
            can_hear_shout=distance <= SENSORY_THRESHOLDS["shout"],
            can_hear_loud=distance <= SENSORY_THRESHOLDS["loud_noise"],
            # Sight
            can_see_facial_detail=distance <= SENSORY_THRESHOLDS["facial_detail"],
            can_see_body_language=distance <= SENSORY_THRESHOLDS["body_language"],
            can_identify_person=distance <= SENSORY_THRESHOLDS["identify_person"],
            can_see_movement=distance <= SENSORY_THRESHOLDS["see_movement"],
            can_see_figure=distance <= SENSORY_THRESHOLDS["see_figure"],
        )
    
    def get_available_senses_list(self) -> List[str]:
        """Get list of available senses with icons"""
        senses = []
        if self.can_touch:
            senses.append("👆 Touch")
        if self.can_smell_faint:
            senses.append("👃 Smell (faint)")
        elif self.can_smell_strong:
            senses.append("👃 Smell (strong only)")
        if self.can_hear_whisper:
            senses.append("🤫 Whisper")
        if self.can_hear_speech:
            senses.append("💬 Speech")
        if self.can_see_facial_detail:
            senses.append("👁️ Facial Detail")
        elif self.can_see_body_language:
            senses.append("👀 Body Language")
        elif self.can_identify_person:
            senses.append("🔍 Identify Person")
        elif self.can_see_movement:
            senses.append("👁️ Movement Only")
        return senses
    
    def get_communication_mode(self) -> str:
        """Get the appropriate communication mode for this distance"""
        if self.can_hear_whisper:
            return "whisper, speak, or shout"
        elif self.can_hear_speech:
            return "speak normally or shout (too far to whisper)"
        elif self.can_hear_raised:
            return "raise voice or shout (too far for normal speech)"
        elif self.can_hear_shout:
            return "must shout (too far for normal voice)"
        else:
            return "out of hearing range"
    
    def get_visual_detail_level(self) -> str:
        """Get description of what can be seen visually"""
        if self.can_see_facial_detail:
            return "full detail - expressions, eye color, small features"
        elif self.can_see_body_language:
            return "body language - posture, gestures, general expression"
        elif self.can_identify_person:
            return "can identify who they are, but not fine details"
        elif self.can_see_movement:
            return "movement and large shapes only"
        elif self.can_see_figure:
            return "can see a figure is there, no details"
        else:
            return "too far to see clearly"


# ═══════════════════════════════════════════════════════════════════════════════
# NARRATOR CONTEXT GENERATION
# ═══════════════════════════════════════════════════════════════════════════════

def get_sensory_context_for_narrator(
    distance: float,
    target_name: str = "them"
) -> str:
    """
    Generate sensory context string for narrator prompts.
    
    This tells the narrator what senses can be used to describe
    the target at the given distance.
    
    Args:
        distance: Distance in units to the target
        target_name: Name of the target for personalized text
    
    Returns:
        Formatted string for inclusion in narrator prompts
    """
    caps = SensoryCapabilities.at_distance(distance)
    category = get_distance_category(distance)
    
    lines = [
        f"**SENSORY CONSTRAINTS FOR {target_name.upper()} (Distance: {distance:.1f} units - {category.value.upper()}):**"
    ]
    
    # Visual constraints
    lines.append(f"\n**SIGHT:**")
    if caps.can_see_facial_detail:
        lines.append(f"- ✅ Can see facial expressions, eye movements, small details")
        lines.append(f"- Use: \"You see {target_name}'s eyes narrow\", \"You notice the twitch at the corner of their mouth\"")
    elif caps.can_see_body_language:
        lines.append(f"- ⚠️ Can see body language but NOT facial details")
        lines.append(f"- Use: \"You see {target_name}'s shoulders tense\", \"You notice their stance shift\"")
        lines.append(f"- ❌ CANNOT use: facial expressions, eye contact, small features")
    elif caps.can_identify_person:
        lines.append(f"- ⚠️ Can identify who they are, but no details")
        lines.append(f"- Use: \"You see {target_name} across the room\"")
        lines.append(f"- ❌ CANNOT use: body language details, expressions")
    elif caps.can_see_movement:
        lines.append(f"- ⚠️ Can only see movement and large shapes")
        lines.append(f"- Use: \"You see a figure moving\", \"You notice movement\"")
        lines.append(f"- ❌ CANNOT use: identification, details")
    else:
        lines.append(f"- ❌ Too far to see clearly")
    
    # Hearing constraints
    lines.append(f"\n**HEARING:**")
    if caps.can_hear_whisper:
        lines.append(f"- ✅ Can hear whispers, normal speech, and shouts")
        lines.append(f"- Use any volume level in dialogue")
    elif caps.can_hear_speech:
        lines.append(f"- ⚠️ Can hear normal speech but NOT whispers")
        lines.append(f"- Use: \"You hear {target_name} say...\", raised voice, shouts")
        lines.append(f"- ❌ CANNOT use: whispered dialogue, quiet muttering")
    elif caps.can_hear_raised:
        lines.append(f"- ⚠️ Must raise voice to be heard")
        lines.append(f"- Use: \"You hear {target_name} call out...\", shouts")
        lines.append(f"- ❌ CANNOT use: normal conversation volume")
    elif caps.can_hear_shout:
        lines.append(f"- ⚠️ Must SHOUT to be heard")
        lines.append(f"- Use: \"You hear {target_name} shout...\"")
        lines.append(f"- ❌ CANNOT use: anything below shouting volume")
    else:
        lines.append(f"- ❌ Out of hearing range - no dialogue possible")
    
    # Smell constraints
    lines.append(f"\n**SMELL:**")
    if caps.can_smell_faint:
        lines.append(f"- ✅ Can smell faint scents (breath, subtle perfume)")
    elif caps.can_smell_strong:
        lines.append(f"- ⚠️ Can only smell STRONG odors (smoke, heavy perfume, food)")
        lines.append(f"- ❌ CANNOT smell: breath, subtle scents")
    else:
        lines.append(f"- ❌ Too far to smell anything")
    
    # Touch constraints
    lines.append(f"\n**TOUCH:**")
    if caps.can_touch:
        lines.append(f"- ✅ Within reach - physical contact possible")
    else:
        lines.append(f"- ❌ Too far for physical contact - would need to move closer")
    
    return "\n".join(lines)


def get_sensory_rules_for_distance(distance: float) -> Dict[str, Any]:
    """
    Get structured sensory rules for a given distance.
    
    Returns a dict that can be used programmatically to validate
    narrator output or guide action interpretation.
    """
    caps = SensoryCapabilities.at_distance(distance)
    
    return {
        "distance": distance,
        "category": get_distance_category(distance).value,
        "sight": {
            "facial_detail": caps.can_see_facial_detail,
            "body_language": caps.can_see_body_language,
            "identify": caps.can_identify_person,
            "movement": caps.can_see_movement,
            "description": caps.get_visual_detail_level(),
        },
        "hearing": {
            "whisper": caps.can_hear_whisper,
            "speech": caps.can_hear_speech,
            "raised": caps.can_hear_raised,
            "shout": caps.can_hear_shout,
            "communication_mode": caps.get_communication_mode(),
        },
        "smell": {
            "faint": caps.can_smell_faint,
            "strong": caps.can_smell_strong,
        },
        "touch": {
            "possible": caps.can_touch,
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# DISTANCE DESCRIPTORS FOR NARRATIVE
# ═══════════════════════════════════════════════════════════════════════════════

DISTANCE_NARRATIVE_DESCRIPTORS = {
    DistanceCategory.IMMEDIATE: {
        "range_phrase": "within arm's reach",
        "movement_phrase": "a single step away",
        "visual_phrase": "close enough to see every detail",
        "audio_phrase": "close enough to whisper",
    },
    DistanceCategory.CLOSE: {
        "range_phrase": "a few steps away",
        "movement_phrase": "just across from you",
        "visual_phrase": "close enough to read their expression",
        "audio_phrase": "at comfortable speaking distance",
    },
    DistanceCategory.NEAR: {
        "range_phrase": "across the room",
        "movement_phrase": "several paces away",
        "visual_phrase": "close enough to see their general demeanor",
        "audio_phrase": "would need to raise your voice slightly",
    },
    DistanceCategory.FAR: {
        "range_phrase": "at the far end",
        "movement_phrase": "a significant walk away",
        "visual_phrase": "too far to make out details",
        "audio_phrase": "would need to shout",
    },
    DistanceCategory.DISTANT: {
        "range_phrase": "barely visible in the distance",
        "movement_phrase": "would take time to reach",
        "visual_phrase": "can only see movement",
        "audio_phrase": "out of hearing range",
    },
}


def get_narrative_distance_phrase(distance: float, phrase_type: str = "range_phrase") -> str:
    """
    Get a narrative phrase describing the distance.
    
    Args:
        distance: Distance in units
        phrase_type: One of "range_phrase", "movement_phrase", "visual_phrase", "audio_phrase"
    
    Returns:
        Narrative phrase string
    """
    category = get_distance_category(distance)
    descriptors = DISTANCE_NARRATIVE_DESCRIPTORS.get(category, DISTANCE_NARRATIVE_DESCRIPTORS[DistanceCategory.NEAR])
    return descriptors.get(phrase_type, descriptors["range_phrase"])


# ═══════════════════════════════════════════════════════════════════════════════
# QUICK REFERENCE TABLE (for documentation/debugging)
# ═══════════════════════════════════════════════════════════════════════════════

SENSORY_QUICK_REFERENCE = """
╔═══════════════════════════════════════════════════════════════════════════════╗
║                    SENSORY RANGE QUICK REFERENCE                              ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║ Distance │ Category  │ Touch │ Smell  │ Whisper │ Talk │ Detail │ Identify   ║
╠══════════╪═══════════╪═══════╪════════╪═════════╪══════╪════════╪════════════╣
║  0-2     │ IMMEDIATE │  ✅   │ ✅ all │   ✅    │  ✅  │   ✅   │    ✅      ║
║  3-5     │ CLOSE     │  ❌   │ ✅ str │   ✅    │  ✅  │   ✅   │    ✅      ║
║  6-8     │ NEAR      │  ❌   │   ❌   │   ❌    │  ✅  │   ✅   │    ✅      ║
║  9-10    │ NEAR      │  ❌   │   ❌   │   ❌    │  ❌  │   ✅   │    ✅      ║
║  11-15   │ FAR       │  ❌   │   ❌   │   ❌    │  ❌  │   ❌   │    ✅      ║
║  16-25   │ FAR       │  ❌   │   ❌   │   ❌    │  ❌  │   ❌   │    ✅      ║
║  26-50   │ DISTANT   │  ❌   │   ❌   │   ❌    │  ❌  │   ❌   │    ❌      ║
╚═══════════════════════════════════════════════════════════════════════════════╝

Legend:
- Touch: Physical contact possible
- Smell: Can smell (all = faint+strong, str = strong only)
- Whisper: Can hear whispered speech
- Talk: Can hear normal conversation
- Detail: Can see facial expressions
- Identify: Can recognize who someone is
"""


if __name__ == "__main__":
    print(SENSORY_QUICK_REFERENCE)
    
    print("\n=== Test: Distance 3 units ===")
    print(get_sensory_context_for_narrator(3.0, "Marcus"))
    
    print("\n=== Test: Distance 12 units ===")
    print(get_sensory_context_for_narrator(12.0, "the guard"))
