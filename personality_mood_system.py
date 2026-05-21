"""
Personality & Mood System - OCEAN, MBTI, and Dynamic Emotional State

This system provides:
1. OCEAN (Big Five) personality traits - stable personality foundation
2. MBTI type - cognitive function preferences
3. Mood System - dynamic emotional state that changes based on context

The personality affects the internal voice and how the character perceives/reacts to situations.
The mood system is dynamic and constantly changes based on scene context.

Design Philosophy:
- OCEAN and MBTI are stable (set at character creation)
- Mood is dynamic (changes every turn based on context)
- All three affect internal voice tone and content
- Internal personality should ALWAYS be evident in internal voice
"""

import json
import logging
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from enum import Enum
from dataclasses import dataclass, field

from openrouter_config import create_role_client, OpenRouterConfig
from json_utils import extract_and_parse_json
from color_utils import Color


# ═══════════════════════════════════════════════════════════════════════════════
# OCEAN (BIG FIVE) PERSONALITY SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class OceanTrait(Enum):
    """The Big Five personality traits"""
    OPENNESS = "openness"               # Curious vs Conventional
    CONSCIENTIOUSNESS = "conscientiousness"  # Organized vs Spontaneous
    EXTRAVERSION = "extraversion"       # Outgoing vs Reserved
    AGREEABLENESS = "agreeableness"     # Cooperative vs Competitive
    NEUROTICISM = "neuroticism"         # Anxious vs Stable


@dataclass
class OceanProfile:
    """
    OCEAN (Big Five) personality profile.
    
    Each trait is on a 1-10 scale:
    1-3 = Low (opposite trait dominant)
    4-6 = Moderate/balanced
    7-10 = High (trait dominant)
    """
    openness: int = 5           # 1=Conventional, 10=Curious/Creative
    conscientiousness: int = 5  # 1=Spontaneous/Careless, 10=Organized/Disciplined
    extraversion: int = 5       # 1=Reserved/Introverted, 10=Outgoing/Energetic
    agreeableness: int = 5      # 1=Competitive/Skeptical, 10=Cooperative/Trusting
    neuroticism: int = 5        # 1=Stable/Calm, 10=Anxious/Emotional
    
    def get_trait_description(self, trait: OceanTrait) -> str:
        """Get a description of where the actor falls on a trait"""
        value = getattr(self, trait.value)
        
        descriptions = {
            OceanTrait.OPENNESS: {
                "low": "conventional, practical, prefers routine",
                "mid": "balanced between tradition and novelty",
                "high": "curious, creative, open to new experiences"
            },
            OceanTrait.CONSCIENTIOUSNESS: {
                "low": "spontaneous, flexible, sometimes careless",
                "mid": "moderately organized",
                "high": "disciplined, organized, detail-oriented"
            },
            OceanTrait.EXTRAVERSION: {
                "low": "reserved, introspective, prefers solitude",
                "mid": "ambivert, situationally social",
                "high": "outgoing, energetic, seeks social interaction"
            },
            OceanTrait.AGREEABLENESS: {
                "low": "competitive, skeptical, direct",
                "mid": "balanced between cooperation and competition",
                "high": "cooperative, trusting, empathetic"
            },
            OceanTrait.NEUROTICISM: {
                "low": "emotionally stable, calm under pressure",
                "mid": "normal emotional range",
                "high": "emotionally reactive, prone to anxiety/stress"
            }
        }
        
        if value <= 3:
            return descriptions[trait]["low"]
        elif value <= 6:
            return descriptions[trait]["mid"]
        else:
            return descriptions[trait]["high"]
    
    def get_dominant_traits(self) -> List[Tuple[OceanTrait, int, str]]:
        """Get traits that are notably high or low (not moderate)"""
        traits = []
        for trait in OceanTrait:
            value = getattr(self, trait.value)
            if value <= 3:
                traits.append((trait, value, "low"))
            elif value >= 7:
                traits.append((trait, value, "high"))
        return sorted(traits, key=lambda x: abs(x[1] - 5), reverse=True)
    
    def get_internal_voice_modifiers(self) -> Dict[str, str]:
        """Get modifiers for internal voice based on OCEAN"""
        modifiers = {}
        
        # High neuroticism = more worried/anxious thoughts
        if self.neuroticism >= 7:
            modifiers["anxiety_level"] = "high"
            modifiers["worry_tendency"] = "frequent"
        elif self.neuroticism <= 3:
            modifiers["anxiety_level"] = "low"
            modifiers["worry_tendency"] = "rare"
        
        # High extraversion = more social thoughts
        if self.extraversion >= 7:
            modifiers["social_focus"] = "high"
            modifiers["energy_from"] = "others"
        elif self.extraversion <= 3:
            modifiers["social_focus"] = "low"
            modifiers["energy_from"] = "solitude"
        
        # High conscientiousness = more planning thoughts
        if self.conscientiousness >= 7:
            modifiers["planning_tendency"] = "high"
            modifiers["detail_focus"] = "strong"
        elif self.conscientiousness <= 3:
            modifiers["planning_tendency"] = "low"
            modifiers["spontaneity"] = "high"
        
        # High openness = more curious/creative thoughts
        if self.openness >= 7:
            modifiers["curiosity"] = "high"
            modifiers["imagination"] = "active"
        elif self.openness <= 3:
            modifiers["practicality"] = "high"
            modifiers["tradition_focus"] = "strong"
        
        # High agreeableness = more empathetic thoughts
        if self.agreeableness >= 7:
            modifiers["empathy"] = "high"
            modifiers["conflict_avoidance"] = "strong"
        elif self.agreeableness <= 3:
            modifiers["skepticism"] = "high"
            modifiers["directness"] = "strong"
        
        return modifiers
    
    def to_dict(self) -> Dict[str, int]:
        """Serialize to dictionary"""
        return {
            "openness": self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion": self.extraversion,
            "agreeableness": self.agreeableness,
            "neuroticism": self.neuroticism
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, int]) -> 'OceanProfile':
        """Deserialize from dictionary"""
        return cls(
            openness=data.get("openness", 5),
            conscientiousness=data.get("conscientiousness", 5),
            extraversion=data.get("extraversion", 5),
            agreeableness=data.get("agreeableness", 5),
            neuroticism=data.get("neuroticism", 5)
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MBTI SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class MBTIType(Enum):
    """The 16 MBTI personality types"""
    INTJ = "INTJ"  # Architect
    INTP = "INTP"  # Logician
    ENTJ = "ENTJ"  # Commander
    ENTP = "ENTP"  # Debater
    INFJ = "INFJ"  # Advocate
    INFP = "INFP"  # Mediator
    ENFJ = "ENFJ"  # Protagonist
    ENFP = "ENFP"  # Campaigner
    ISTJ = "ISTJ"  # Logistician
    ISFJ = "ISFJ"  # Defender
    ESTJ = "ESTJ"  # Executive
    ESFJ = "ESFJ"  # Consul
    ISTP = "ISTP"  # Virtuoso
    ISFP = "ISFP"  # Adventurer
    ESTP = "ESTP"  # Entrepreneur
    ESFP = "ESFP"  # Entertainer


@dataclass
class MBTIProfile:
    """
    MBTI personality type profile.
    
    Includes the type and descriptions of cognitive preferences.
    """
    mbti_type: MBTIType = MBTIType.INTP
    
    # Individual dimension preferences (for nuance)
    introversion_extraversion: int = 5  # 1=Strong I, 10=Strong E
    sensing_intuition: int = 5          # 1=Strong S, 10=Strong N
    thinking_feeling: int = 5           # 1=Strong T, 10=Strong F
    judging_perceiving: int = 5         # 1=Strong J, 10=Strong P
    
    @property
    def type_name(self) -> str:
        """Get the nickname for this MBTI type"""
        names = {
            MBTIType.INTJ: "The Architect",
            MBTIType.INTP: "The Logician",
            MBTIType.ENTJ: "The Commander",
            MBTIType.ENTP: "The Debater",
            MBTIType.INFJ: "The Advocate",
            MBTIType.INFP: "The Mediator",
            MBTIType.ENFJ: "The Protagonist",
            MBTIType.ENFP: "The Campaigner",
            MBTIType.ISTJ: "The Logistician",
            MBTIType.ISFJ: "The Defender",
            MBTIType.ESTJ: "The Executive",
            MBTIType.ESFJ: "The Consul",
            MBTIType.ISTP: "The Virtuoso",
            MBTIType.ISFP: "The Adventurer",
            MBTIType.ESTP: "The Entrepreneur",
            MBTIType.ESFP: "The Entertainer"
        }
        return names.get(self.mbti_type, "Unknown")
    
    def get_cognitive_style(self) -> str:
        """Get a description of cognitive style"""
        type_str = self.mbti_type.value
        
        # Energy direction
        energy = "draws energy from inner world" if type_str[0] == 'I' else "draws energy from outer world"
        
        # Information gathering
        info = "focuses on concrete facts" if type_str[1] == 'S' else "focuses on patterns and possibilities"
        
        # Decision making
        decision = "decides based on logic" if type_str[2] == 'T' else "decides based on values and impact on people"
        
        # Lifestyle
        lifestyle = "prefers structure and closure" if type_str[3] == 'J' else "prefers flexibility and openness"
        
        return f"{energy}, {info}, {decision}, {lifestyle}"
    
    def get_internal_voice_style(self) -> Dict[str, str]:
        """Get internal voice style based on MBTI"""
        type_str = self.mbti_type.value
        style = {}
        
        # Thinking vs Feeling affects voice tone
        if type_str[2] == 'T':
            style["reasoning_style"] = "analytical"
            style["emotional_expression"] = "understated"
        else:
            style["reasoning_style"] = "values-based"
            style["emotional_expression"] = "expressive"
        
        # Sensing vs Intuition affects focus
        if type_str[1] == 'S':
            style["focus"] = "present details"
            style["references"] = "concrete experiences"
        else:
            style["focus"] = "future possibilities"
            style["references"] = "patterns and meanings"
        
        # Judging vs Perceiving affects urgency
        if type_str[3] == 'J':
            style["urgency"] = "decisive"
            style["planning"] = "structured"
        else:
            style["urgency"] = "exploratory"
            style["planning"] = "flexible"
        
        return style
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "mbti_type": self.mbti_type.value,
            "introversion_extraversion": self.introversion_extraversion,
            "sensing_intuition": self.sensing_intuition,
            "thinking_feeling": self.thinking_feeling,
            "judging_perceiving": self.judging_perceiving
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MBTIProfile':
        """Deserialize from dictionary"""
        return cls(
            mbti_type=MBTIType(data.get("mbti_type", "INTP")),
            introversion_extraversion=data.get("introversion_extraversion", 5),
            sensing_intuition=data.get("sensing_intuition", 5),
            thinking_feeling=data.get("thinking_feeling", 5),
            judging_perceiving=data.get("judging_perceiving", 5)
        )
    
    def derive_ocean_profile(self) -> 'OceanProfile':
        """
        Derive a compatible OCEAN profile from this MBTI type.
        
        Mapping (based on psychological research correlations):
        - I/E → Extraversion (direct mapping)
        - N/S → Openness (N = high openness)
        - T/F → Agreeableness (F = higher agreeableness)
        - J/P → Conscientiousness (J = higher conscientiousness)
        - Neuroticism is derived from combination (F types slightly higher)
        
        Returns an OceanProfile that is consistent with this MBTI type.
        """
        type_str = self.mbti_type.value
        
        # Use the dimension preferences for more nuanced mapping
        # I/E → Extraversion: direct mapping
        extraversion = self.introversion_extraversion
        
        # N/S → Openness: N types are more open
        # sensing_intuition: 1=S, 10=N
        openness = self.sensing_intuition
        
        # T/F → Agreeableness: F types tend to be more agreeable
        # thinking_feeling: 1=T, 10=F
        agreeableness = self.thinking_feeling
        
        # J/P → Conscientiousness: J types are more conscientious
        # judging_perceiving: 1=J, 10=P, so we invert
        conscientiousness = 11 - self.judging_perceiving
        
        # Neuroticism: F types and high N types tend slightly higher
        # This is a rough approximation
        base_neuroticism = 5
        if type_str[2] == 'F':
            base_neuroticism += 1
        if type_str[1] == 'N':
            base_neuroticism += 1
        if type_str[0] == 'I':
            base_neuroticism += 1  # Introverts may ruminate more
        neuroticism = min(10, max(1, base_neuroticism))
        
        return OceanProfile(
            openness=openness,
            conscientiousness=conscientiousness,
            extraversion=extraversion,
            agreeableness=agreeableness,
            neuroticism=neuroticism
        )


# ═══════════════════════════════════════════════════════════════════════════════
# MOOD SYSTEM (DYNAMIC EMOTIONAL STATE)
# ═══════════════════════════════════════════════════════════════════════════════

class MoodCategory(Enum):
    """Primary mood categories"""
    CALM = "calm"               # Peaceful, relaxed, content
    ANXIOUS = "anxious"         # Worried, nervous, on edge
    EXCITED = "excited"         # Energized, enthusiastic, eager
    ANGRY = "angry"             # Frustrated, irritated, furious
    SAD = "sad"                 # Down, melancholic, grieving
    FEARFUL = "fearful"         # Scared, terrified, panicked
    HAPPY = "happy"             # Joyful, pleased, satisfied
    FOCUSED = "focused"         # Concentrated, determined, driven
    CONFUSED = "confused"       # Uncertain, disoriented, lost
    SUSPICIOUS = "suspicious"   # Wary, distrustful, paranoid


class MoodIntensity(Enum):
    """How intense the current mood is"""
    SUBTLE = "subtle"           # Barely noticeable
    MODERATE = "moderate"       # Clearly present
    STRONG = "strong"           # Dominant emotion
    OVERWHELMING = "overwhelming"  # All-consuming


@dataclass
class MoodState:
    """
    Current emotional state - dynamic and constantly changing.
    
    The mood affects:
    - Internal voice tone (frantic vs calm)
    - Perception of events (paranoid vs trusting)
    - Decision-making style (impulsive vs careful)
    """
    primary_mood: MoodCategory = MoodCategory.CALM
    intensity: MoodIntensity = MoodIntensity.MODERATE
    secondary_mood: Optional[MoodCategory] = None  # Mixed emotions
    
    # Specific emotional values (0-10)
    stress_level: int = 3       # How stressed
    energy_level: int = 5       # How energetic
    confidence_level: int = 5   # How confident
    
    # Context
    mood_trigger: str = ""      # What caused this mood
    last_updated: datetime = field(default_factory=datetime.now)
    
    def get_voice_urgency(self) -> str:
        """Get how urgent/frantic the internal voice should be"""
        if self.intensity == MoodIntensity.OVERWHELMING:
            return "frantic"
        elif self.intensity == MoodIntensity.STRONG:
            return "urgent"
        elif self.intensity == MoodIntensity.MODERATE:
            return "normal"
        else:
            return "calm"
    
    def get_voice_tone(self) -> str:
        """Get the emotional tone for internal voice"""
        tone_map = {
            MoodCategory.CALM: "relaxed and measured",
            MoodCategory.ANXIOUS: "worried and racing",
            MoodCategory.EXCITED: "eager and energetic",
            MoodCategory.ANGRY: "sharp and intense",
            MoodCategory.SAD: "heavy and slow",
            MoodCategory.FEARFUL: "tight and panicked",
            MoodCategory.HAPPY: "light and warm",
            MoodCategory.FOCUSED: "clear and determined",
            MoodCategory.CONFUSED: "scattered and uncertain",
            MoodCategory.SUSPICIOUS: "guarded and watchful"
        }
        return tone_map.get(self.primary_mood, "neutral")
    
    def get_thought_patterns(self) -> List[str]:
        """Get typical thought patterns for this mood"""
        patterns = {
            MoodCategory.CALM: ["measured observations", "patient considerations", "steady assessments"],
            MoodCategory.ANXIOUS: ["what-if scenarios", "worst-case thinking", "hypervigilance"],
            MoodCategory.EXCITED: ["possibilities", "anticipation", "eager planning"],
            MoodCategory.ANGRY: ["grievances", "blame", "confrontational thoughts"],
            MoodCategory.SAD: ["losses", "regrets", "melancholic memories"],
            MoodCategory.FEARFUL: ["threats", "escape routes", "danger assessment"],
            MoodCategory.HAPPY: ["gratitude", "optimism", "appreciation"],
            MoodCategory.FOCUSED: ["goals", "next steps", "problem-solving"],
            MoodCategory.CONFUSED: ["questions", "uncertainty", "seeking clarity"],
            MoodCategory.SUSPICIOUS: ["motives", "hidden agendas", "trust assessment"]
        }
        return patterns.get(self.primary_mood, ["neutral observations"])
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "primary_mood": self.primary_mood.value,
            "intensity": self.intensity.value,
            "secondary_mood": self.secondary_mood.value if self.secondary_mood else None,
            "stress_level": self.stress_level,
            "energy_level": self.energy_level,
            "confidence_level": self.confidence_level,
            "mood_trigger": self.mood_trigger,
            "last_updated": self.last_updated.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MoodState':
        """Deserialize from dictionary"""
        return cls(
            primary_mood=MoodCategory(data.get("primary_mood", "calm")),
            intensity=MoodIntensity(data.get("intensity", "moderate")),
            secondary_mood=MoodCategory(data["secondary_mood"]) if data.get("secondary_mood") else None,
            stress_level=data.get("stress_level", 3),
            energy_level=data.get("energy_level", 5),
            confidence_level=data.get("confidence_level", 5),
            mood_trigger=data.get("mood_trigger", ""),
            last_updated=datetime.fromisoformat(data["last_updated"]) if data.get("last_updated") else datetime.now()
        )


class MoodAnalyzer:
    """
    Analyzes scene context to determine appropriate mood changes.
    
    The mood should change dynamically based on:
    - Scene events (danger, success, loss)
    - NPC interactions (friendly, hostile)
    - Environmental factors (dark alley vs sunny park)
    - Actor's current state (injured, tired, hungry)
    """
    
    def __init__(self):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
    
    def analyze_mood_from_context(self,
                                  current_mood: MoodState,
                                  scene_description: str,
                                  recent_events: List[str],
                                  actor_state: Dict[str, Any],
                                  ocean_profile: OceanProfile = None) -> MoodState:
        """
        Analyze context and determine new mood state.
        
        Args:
            current_mood: Current mood state
            scene_description: Current scene
            recent_events: Recent narrative events
            actor_state: Actor's current status (stamina, spirit, etc.)
            ocean_profile: OCEAN profile (affects mood sensitivity)
            
        Returns:
            Updated MoodState
        """
        # Build context for analysis
        events_text = "\n".join(f"- {e}" for e in recent_events[-5:]) if recent_events else "None"
        
        # OCEAN affects mood sensitivity
        neuroticism_mod = ""
        if ocean_profile:
            if ocean_profile.neuroticism >= 7:
                neuroticism_mod = "This character is highly sensitive to stress and emotional triggers."
            elif ocean_profile.neuroticism <= 3:
                neuroticism_mod = "This character is emotionally stable and resistant to mood swings."
        
        prompt = f"""Analyze this context and determine the character's current emotional state.

**Current Mood:** {current_mood.primary_mood.value} ({current_mood.intensity.value})
**Current Stress:** {current_mood.stress_level}/10
**Current Energy:** {current_mood.energy_level}/10

**Scene Description:**
{scene_description}

**Recent Events:**
{events_text}

**Actor State:**
- Stamina: {actor_state.get('stamina', 'Unknown')}
- Spirit: {actor_state.get('spirit', 'Unknown')}
- Injuries: {actor_state.get('injuries', 'None')}

{neuroticism_mod}

**Mood Categories:**
- calm: Peaceful, relaxed, content
- anxious: Worried, nervous, on edge
- excited: Energized, enthusiastic, eager
- angry: Frustrated, irritated, furious
- sad: Down, melancholic, grieving
- fearful: Scared, terrified, panicked
- happy: Joyful, pleased, satisfied
- focused: Concentrated, determined, driven
- confused: Uncertain, disoriented, lost
- suspicious: Wary, distrustful, paranoid

**Intensity Levels:**
- subtle: Barely noticeable
- moderate: Clearly present
- strong: Dominant emotion
- overwhelming: All-consuming

**Response Format:**
Return JSON:

{{
    "primary_mood": "mood category",
    "intensity": "intensity level",
    "secondary_mood": "optional second mood or null",
    "stress_level": 0-10,
    "energy_level": 0-10,
    "confidence_level": 0-10,
    "mood_trigger": "What in the context caused this mood",
    "reasoning": "Brief explanation of mood analysis"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.4
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            
            if not result:
                return current_mood
            
            return MoodState(
                primary_mood=MoodCategory(result.get("primary_mood", current_mood.primary_mood.value)),
                intensity=MoodIntensity(result.get("intensity", current_mood.intensity.value)),
                secondary_mood=MoodCategory(result["secondary_mood"]) if result.get("secondary_mood") else None,
                stress_level=result.get("stress_level", current_mood.stress_level),
                energy_level=result.get("energy_level", current_mood.energy_level),
                confidence_level=result.get("confidence_level", current_mood.confidence_level),
                mood_trigger=result.get("mood_trigger", ""),
                last_updated=datetime.now()
            )
            
        except Exception as e:
            self.logger.error(f"Error analyzing mood: {e}")
            return current_mood


# ═══════════════════════════════════════════════════════════════════════════════
# COMPLETE PERSONALITY PROFILE
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class CompletePersonalityProfile:
    """
    Complete personality profile combining OCEAN, MBTI, and Mood.
    
    This is the master profile that should be attached to each actor.
    OCEAN is derived from MBTI to ensure consistency (e.g., INTP will always have low Extraversion).
    """
    ocean: OceanProfile = field(default_factory=OceanProfile)
    mbti: MBTIProfile = field(default_factory=MBTIProfile)
    mood: MoodState = field(default_factory=MoodState)
    
    # Additional personality elements
    core_values: List[str] = field(default_factory=list)  # What they value most
    core_fears: List[str] = field(default_factory=list)   # What they fear most
    quirks: List[str] = field(default_factory=list)       # Unique behavioral quirks
    
    # Flag to control whether OCEAN should be derived from MBTI
    _sync_ocean_to_mbti: bool = field(default=True, repr=False)
    
    def __post_init__(self):
        """Synchronize OCEAN with MBTI after initialization."""
        if self._sync_ocean_to_mbti:
            # Derive OCEAN from MBTI to ensure consistency
            self.ocean = self.mbti.derive_ocean_profile()
    
    @classmethod
    def create_random(cls) -> 'CompletePersonalityProfile':
        """Create a random but internally consistent personality profile."""
        import random
        
        # Pick a random MBTI type
        mbti_type = random.choice(list(MBTIType))
        type_str = mbti_type.value
        
        # Set dimension preferences based on type (with some variance)
        ie = random.randint(2, 4) if type_str[0] == 'I' else random.randint(7, 9)
        sn = random.randint(2, 4) if type_str[1] == 'S' else random.randint(7, 9)
        tf = random.randint(2, 4) if type_str[2] == 'T' else random.randint(7, 9)
        jp = random.randint(2, 4) if type_str[3] == 'J' else random.randint(7, 9)
        
        mbti = MBTIProfile(
            mbti_type=mbti_type,
            introversion_extraversion=ie,
            sensing_intuition=sn,
            thinking_feeling=tf,
            judging_perceiving=jp
        )
        
        # OCEAN will be derived automatically in __post_init__
        return cls(mbti=mbti)
    
    def get_internal_voice_guidance(self) -> Dict[str, Any]:
        """
        Get comprehensive guidance for internal voice generation.
        
        This combines all personality factors into actionable guidance.
        """
        guidance = {
            # From OCEAN
            "ocean_modifiers": self.ocean.get_internal_voice_modifiers(),
            "dominant_traits": [
                (t.value, v, d) for t, v, d in self.ocean.get_dominant_traits()
            ],
            
            # From MBTI
            "mbti_type": self.mbti.mbti_type.value,
            "mbti_name": self.mbti.type_name,
            "cognitive_style": self.mbti.get_cognitive_style(),
            "voice_style": self.mbti.get_internal_voice_style(),
            
            # From Mood (dynamic)
            "current_mood": self.mood.primary_mood.value,
            "mood_intensity": self.mood.intensity.value,
            "voice_urgency": self.mood.get_voice_urgency(),
            "voice_tone": self.mood.get_voice_tone(),
            "thought_patterns": self.mood.get_thought_patterns(),
            "stress_level": self.mood.stress_level,
            "energy_level": self.mood.energy_level,
            "confidence_level": self.mood.confidence_level,
            
            # Additional
            "core_values": self.core_values,
            "core_fears": self.core_fears,
            "quirks": self.quirks
        }
        
        return guidance
    
    def get_voice_prompt_section(self) -> str:
        """
        Get a formatted prompt section for internal voice generation.
        
        This should be included in internal voice prompts.
        """
        guidance = self.get_internal_voice_guidance()
        
        # Build OCEAN section
        ocean_traits = []
        for trait, value, direction in guidance["dominant_traits"]:
            ocean_traits.append(f"- {trait}: {direction} ({value}/10)")
        ocean_section = "\n".join(ocean_traits) if ocean_traits else "- Balanced personality"
        
        # Build mood section
        mood_section = f"""Current Mood: {guidance['current_mood']} ({guidance['mood_intensity']})
Voice Tone: {guidance['voice_tone']}
Voice Urgency: {guidance['voice_urgency']}
Stress: {guidance['stress_level']}/10 | Energy: {guidance['energy_level']}/10 | Confidence: {guidance['confidence_level']}/10"""
        
        # Build complete section
        return f"""**CHARACTER PERSONALITY (MUST INFORM INTERNAL VOICE)**

**MBTI Type:** {guidance['mbti_type']} - {guidance['mbti_name']}
{guidance['cognitive_style']}

**OCEAN Traits:**
{ocean_section}

**Current Emotional State:**
{mood_section}

**Thought Patterns for Current Mood:**
{', '.join(guidance['thought_patterns'])}

**Core Values:** {', '.join(self.core_values) if self.core_values else 'Not defined'}
**Core Fears:** {', '.join(self.core_fears) if self.core_fears else 'Not defined'}

**CRITICAL:** The internal voice MUST reflect this personality. A high-neuroticism character should have worried, racing thoughts. A low-extraversion character should have introspective, solitary thoughts. The mood MUST affect the tone - an anxious mood means anxious internal voice."""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary"""
        return {
            "ocean": self.ocean.to_dict(),
            "mbti": self.mbti.to_dict(),
            "mood": self.mood.to_dict(),
            "core_values": self.core_values,
            "core_fears": self.core_fears,
            "quirks": self.quirks
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'CompletePersonalityProfile':
        """Deserialize from dictionary - don't re-sync OCEAN since it was already saved"""
        return cls(
            ocean=OceanProfile.from_dict(data.get("ocean", {})),
            mbti=MBTIProfile.from_dict(data.get("mbti", {})),
            mood=MoodState.from_dict(data.get("mood", {})),
            core_values=data.get("core_values", []),
            core_fears=data.get("core_fears", []),
            quirks=data.get("quirks", []),
            _sync_ocean_to_mbti=False  # Don't overwrite loaded OCEAN
        )


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONALITY GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

class PersonalityGenerator:
    """
    Generates complete personality profiles for actors.
    """
    
    def __init__(self):
        self.client = create_role_client("coordination")
        self.logger = logging.getLogger(__name__)
        self.mood_analyzer = MoodAnalyzer()
    
    def generate_personality(self,
                            actor_name: str,
                            occupation: str,
                            backstory: str = "",
                            existing_traits: Dict[str, str] = None) -> CompletePersonalityProfile:
        """
        Generate a complete personality profile for an actor.
        
        Args:
            actor_name: Actor's name
            occupation: Their occupation
            backstory: Background information
            existing_traits: Existing personality traits (internal/external)
            
        Returns:
            CompletePersonalityProfile
        """
        prompt = f"""Generate a complete personality profile for this character.

**Character:** {actor_name}
**Occupation:** {occupation}
**Backstory:** {backstory}
**Existing Traits:** {existing_traits}

**Generate:**

1. **OCEAN (Big Five) Traits** (1-10 scale):
   - Openness: 1=Conventional, 10=Curious/Creative
   - Conscientiousness: 1=Spontaneous, 10=Organized
   - Extraversion: 1=Reserved, 10=Outgoing
   - Agreeableness: 1=Competitive, 10=Cooperative
   - Neuroticism: 1=Stable, 10=Anxious

2. **MBTI Type**: Choose the most fitting type based on character

3. **Core Values**: 2-3 things they value most

4. **Core Fears**: 2-3 things they fear most

5. **Quirks**: 1-2 unique behavioral quirks

**Response Format:**
Return JSON:

{{
    "ocean": {{
        "openness": 1-10,
        "conscientiousness": 1-10,
        "extraversion": 1-10,
        "agreeableness": 1-10,
        "neuroticism": 1-10
    }},
    "mbti_type": "XXXX",
    "core_values": ["value1", "value2"],
    "core_fears": ["fear1", "fear2"],
    "quirks": ["quirk1"],
    "reasoning": "Brief explanation of personality choices"
}}
"""
        
        try:
            response = self.client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.6
            )
            
            result = extract_and_parse_json(response.choices[0].message.content)
            
            if not result:
                return CompletePersonalityProfile()
            
            # Build profile
            ocean_data = result.get("ocean", {})
            ocean = OceanProfile(
                openness=ocean_data.get("openness", 5),
                conscientiousness=ocean_data.get("conscientiousness", 5),
                extraversion=ocean_data.get("extraversion", 5),
                agreeableness=ocean_data.get("agreeableness", 5),
                neuroticism=ocean_data.get("neuroticism", 5)
            )
            
            mbti_type_str = result.get("mbti_type", "INTP")
            try:
                mbti_type = MBTIType(mbti_type_str)
            except ValueError:
                mbti_type = MBTIType.INTP
            
            mbti = MBTIProfile(mbti_type=mbti_type)
            
            return CompletePersonalityProfile(
                ocean=ocean,
                mbti=mbti,
                mood=MoodState(),  # Start with default calm mood
                core_values=result.get("core_values", []),
                core_fears=result.get("core_fears", []),
                quirks=result.get("quirks", [])
            )
            
        except Exception as e:
            self.logger.error(f"Error generating personality: {e}")
            return CompletePersonalityProfile()
    
    def update_mood(self,
                   profile: CompletePersonalityProfile,
                   scene_description: str,
                   recent_events: List[str],
                   actor_state: Dict[str, Any]) -> MoodState:
        """
        Update the mood based on current context.
        
        This should be called every turn to keep mood dynamic.
        """
        return self.mood_analyzer.analyze_mood_from_context(
            current_mood=profile.mood,
            scene_description=scene_description,
            recent_events=recent_events,
            actor_state=actor_state,
            ocean_profile=profile.ocean
        )


# ═══════════════════════════════════════════════════════════════════════════════
# DISPLAY FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

def display_personality_section(profile: CompletePersonalityProfile):
    """Display personality section for actor sheet"""
    print(f"{Color.INFO}├─────────────────────────────────────────────────────────┤{Color.RESET}")
    print(f"{Color.INFO}│{Color.RESET} 🧠 {Color.INFO}PERSONALITY PROFILE{Color.RESET}")
    
    # MBTI
    print(f"{Color.INFO}│{Color.RESET} MBTI: {Color.ACTOR_NAME}{profile.mbti.mbti_type.value}{Color.RESET} - {Color.STATUS}{profile.mbti.type_name}{Color.RESET}")
    
    # OCEAN
    print(f"{Color.INFO}│{Color.RESET} {Color.INFO}OCEAN Traits:{Color.RESET}")
    traits = [
        ("O", profile.ocean.openness),
        ("C", profile.ocean.conscientiousness),
        ("E", profile.ocean.extraversion),
        ("A", profile.ocean.agreeableness),
        ("N", profile.ocean.neuroticism)
    ]
    trait_bars = []
    for name, value in traits:
        bar = "█" * value + "░" * (10 - value)
        trait_bars.append(f"{name}:{bar}")
    print(f"{Color.INFO}│{Color.RESET} {Color.STATUS}{' '.join(trait_bars)}{Color.RESET}")
    
    # Current Mood
    mood_color = {
        MoodCategory.CALM: Color.SUCCESS,
        MoodCategory.ANXIOUS: Color.WARNING,
        MoodCategory.ANGRY: Color.ERROR,
        MoodCategory.FEARFUL: Color.ERROR,
        MoodCategory.SAD: Color.SYSTEM,
        MoodCategory.HAPPY: Color.SUCCESS,
        MoodCategory.EXCITED: Color.INFO,
        MoodCategory.FOCUSED: Color.INFO,
        MoodCategory.CONFUSED: Color.WARNING,
        MoodCategory.SUSPICIOUS: Color.WARNING
    }.get(profile.mood.primary_mood, Color.STATUS)
    
    print(f"{Color.INFO}│{Color.RESET} Current Mood: {mood_color}{profile.mood.primary_mood.value.upper()}{Color.RESET} ({profile.mood.intensity.value})")
    print(f"{Color.INFO}│{Color.RESET} Stress: {profile.mood.stress_level}/10 | Energy: {profile.mood.energy_level}/10 | Confidence: {profile.mood.confidence_level}/10")
    
    # Core values and fears
    if profile.core_values:
        print(f"{Color.INFO}│{Color.RESET} Values: {Color.STATUS}{', '.join(profile.core_values)}{Color.RESET}")
    if profile.core_fears:
        print(f"{Color.INFO}│{Color.RESET} Fears: {Color.STATUS}{', '.join(profile.core_fears)}{Color.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Personality & Mood System Test\n")
    
    # Create test profile
    profile = CompletePersonalityProfile(
        ocean=OceanProfile(
            openness=7,
            conscientiousness=4,
            extraversion=3,
            agreeableness=6,
            neuroticism=8
        ),
        mbti=MBTIProfile(mbti_type=MBTIType.INFP),
        mood=MoodState(
            primary_mood=MoodCategory.ANXIOUS,
            intensity=MoodIntensity.STRONG,
            stress_level=7,
            energy_level=4,
            confidence_level=3
        ),
        core_values=["authenticity", "creativity", "helping others"],
        core_fears=["rejection", "being misunderstood", "conflict"]
    )
    
    # Display
    print("=== Personality Profile ===\n")
    display_personality_section(profile)
    
    # Get voice guidance
    print("\n=== Internal Voice Guidance ===\n")
    guidance = profile.get_internal_voice_guidance()
    print(f"MBTI: {guidance['mbti_type']} - {guidance['mbti_name']}")
    print(f"Voice Tone: {guidance['voice_tone']}")
    print(f"Voice Urgency: {guidance['voice_urgency']}")
    print(f"Thought Patterns: {', '.join(guidance['thought_patterns'])}")
    
    # Get prompt section
    print("\n=== Voice Prompt Section ===\n")
    print(profile.get_voice_prompt_section())
    
    print("\n✅ Personality & Mood system ready!")
