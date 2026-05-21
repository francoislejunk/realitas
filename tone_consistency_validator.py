"""
Tone Consistency Validator for UTAS Simulation

Ensures narrative tone matches scene tension and context.
Prevents fake signals where serious scenes have comedic tone or vice versa.
"""

from typing import Dict, Any, Optional, List
from color_utils import Color


class ToneConsistencyValidator:
    """
    Validates and maintains consistent narrative tone.
    
    Features:
    - Detects tone mismatches
    - Suggests appropriate tone
    - Tracks scene atmosphere
    - Prevents tonal whiplash
    """
    
    def __init__(self):
        self.current_tone = "neutral"
        self.scene_atmosphere = "calm"
        self.tone_history = []
        self.violence_level = 0  # 0-5
        self.emotional_intensity = 0  # 0-5
    
    def assess_appropriate_tone(
        self,
        scene_context: str,
        recent_events: List[str],
        violence_level: int = 0,
        emotional_intensity: int = 0
    ) -> Dict[str, Any]:
        """
        Assess what tone is appropriate for current context.
        
        Returns:
            Dict with recommended_tone, atmosphere, reasoning
        """
        self.violence_level = violence_level
        self.emotional_intensity = emotional_intensity
        
        # Analyze scene context
        scene_tone = self._analyze_scene_tone(scene_context)
        event_tone = self._analyze_event_tone(recent_events)
        
        # Determine recommended tone
        recommended_tone = self._determine_tone(scene_tone, event_tone, violence_level, emotional_intensity)
        
        # Determine atmosphere
        atmosphere = self._determine_atmosphere(recommended_tone, violence_level)
        
        # Generate reasoning
        reasoning = self._generate_tone_reasoning(recommended_tone, scene_tone, event_tone)
        
        return {
            'recommended_tone': recommended_tone,
            'atmosphere': atmosphere,
            'reasoning': reasoning,
            'violence_level': violence_level,
            'emotional_intensity': emotional_intensity,
            'scene_indicators': scene_tone,
            'event_indicators': event_tone
        }
    
    def _analyze_scene_tone(self, scene_context: str) -> Dict[str, int]:
        """Analyze scene context for tone indicators."""
        context_lower = scene_context.lower()
        
        indicators = {
            'dark': 0,
            'light': 0,
            'tense': 0,
            'calm': 0,
            'violent': 0,
            'peaceful': 0
        }
        
        # Dark indicators
        dark_words = ['dark', 'shadow', 'grim', 'ominous', 'foreboding', 'sinister', 'menacing']
        indicators['dark'] = sum(1 for word in dark_words if word in context_lower)
        
        # Light indicators
        light_words = ['bright', 'cheerful', 'pleasant', 'warm', 'friendly', 'welcoming']
        indicators['light'] = sum(1 for word in light_words if word in context_lower)
        
        # Tense indicators
        tense_words = ['tense', 'nervous', 'anxious', 'uneasy', 'wary', 'cautious']
        indicators['tense'] = sum(1 for word in tense_words if word in context_lower)
        
        # Calm indicators
        calm_words = ['calm', 'peaceful', 'quiet', 'serene', 'tranquil', 'relaxed']
        indicators['calm'] = sum(1 for word in calm_words if word in context_lower)
        
        # Violent indicators
        violent_words = ['blood', 'violence', 'fight', 'weapon', 'attack', 'death', 'corpse']
        indicators['violent'] = sum(1 for word in violent_words if word in context_lower)
        
        # Peaceful indicators
        peaceful_words = ['peaceful', 'gentle', 'soft', 'quiet', 'still']
        indicators['peaceful'] = sum(1 for word in peaceful_words if word in context_lower)
        
        return indicators
    
    def _analyze_event_tone(self, recent_events: List[str]) -> Dict[str, int]:
        """Analyze recent events for tone indicators."""
        if not recent_events:
            return {'neutral': 1}
        
        indicators = {
            'violent': 0,
            'dramatic': 0,
            'mundane': 0,
            'tense': 0
        }
        
        for event in recent_events[-3:]:  # Last 3 events
            event_lower = event.lower()
            
            if any(word in event_lower for word in ['attack', 'shoot', 'kill', 'fight', 'blood']):
                indicators['violent'] += 1
            
            if any(word in event_lower for word in ['dramatic', 'intense', 'shocking', 'sudden']):
                indicators['dramatic'] += 1
            
            if any(word in event_lower for word in ['walk', 'talk', 'look', 'wait', 'stand']):
                indicators['mundane'] += 1
            
            if any(word in event_lower for word in ['tense', 'nervous', 'cautious', 'wary']):
                indicators['tense'] += 1
        
        return indicators
    
    def _determine_tone(
        self,
        scene_tone: Dict[str, int],
        event_tone: Dict[str, int],
        violence_level: int,
        emotional_intensity: int
    ) -> str:
        """Determine appropriate tone based on all factors."""
        
        # Violence overrides everything
        if violence_level >= 4:
            return "grim"
        elif violence_level >= 3:
            return "serious"
        
        # High emotional intensity
        if emotional_intensity >= 4:
            return "dramatic"
        elif emotional_intensity >= 3:
            return "tense"
        
        # Scene-based tone
        if scene_tone.get('dark', 0) >= 2:
            return "dark"
        elif scene_tone.get('violent', 0) >= 2:
            return "serious"
        elif scene_tone.get('tense', 0) >= 2:
            return "tense"
        elif scene_tone.get('calm', 0) >= 2:
            return "calm"
        elif scene_tone.get('light', 0) >= 2:
            return "light"
        
        # Event-based tone
        if event_tone.get('violent', 0) >= 2:
            return "serious"
        elif event_tone.get('dramatic', 0) >= 2:
            return "dramatic"
        elif event_tone.get('tense', 0) >= 2:
            return "tense"
        elif event_tone.get('mundane', 0) >= 2:
            return "casual"
        
        return "neutral"
    
    def _determine_atmosphere(self, tone: str, violence_level: int) -> str:
        """Determine scene atmosphere based on tone."""
        atmosphere_map = {
            'grim': 'oppressive',
            'dark': 'ominous',
            'serious': 'grave',
            'dramatic': 'intense',
            'tense': 'uneasy',
            'neutral': 'balanced',
            'calm': 'peaceful',
            'casual': 'relaxed',
            'light': 'pleasant'
        }
        
        base_atmosphere = atmosphere_map.get(tone, 'neutral')
        
        # Violence modifies atmosphere
        if violence_level >= 3:
            return 'violent'
        
        return base_atmosphere
    
    def _generate_tone_reasoning(
        self,
        recommended_tone: str,
        scene_tone: Dict[str, int],
        event_tone: Dict[str, int]
    ) -> str:
        """Generate reasoning for tone recommendation."""
        reasons = []
        
        # Scene factors
        if scene_tone.get('dark', 0) >= 2:
            reasons.append("dark scene elements")
        if scene_tone.get('violent', 0) >= 2:
            reasons.append("violent scene context")
        if scene_tone.get('tense', 0) >= 2:
            reasons.append("tense atmosphere")
        
        # Event factors
        if event_tone.get('violent', 0) >= 2:
            reasons.append("recent violence")
        if event_tone.get('dramatic', 0) >= 2:
            reasons.append("dramatic events")
        
        # Violence/emotion
        if self.violence_level >= 3:
            reasons.append(f"high violence (level {self.violence_level})")
        if self.emotional_intensity >= 3:
            reasons.append(f"high emotion (level {self.emotional_intensity})")
        
        if not reasons:
            return f"Tone: {recommended_tone} (default)"
        
        return f"Tone: {recommended_tone} ({', '.join(reasons)})"
    
    def validate_narrative_tone(
        self,
        narrative: str,
        expected_tone: str
    ) -> Dict[str, Any]:
        """
        Validate if narrative matches expected tone.
        
        Returns:
            Dict with is_consistent, detected_tone, issues
        """
        detected_tone = self._detect_narrative_tone(narrative)
        is_consistent = self._tones_compatible(expected_tone, detected_tone)
        
        issues = []
        if not is_consistent:
            issues.append(f"Tone mismatch: expected {expected_tone}, detected {detected_tone}")
        
        # Check for specific mismatches
        if expected_tone in ['grim', 'serious', 'dark'] and self._has_humor(narrative):
            issues.append("Inappropriate humor in serious scene")
        
        if expected_tone in ['light', 'casual'] and self._has_dark_imagery(narrative):
            issues.append("Dark imagery in light scene")
        
        return {
            'is_consistent': is_consistent,
            'expected_tone': expected_tone,
            'detected_tone': detected_tone,
            'issues': issues
        }
    
    def _detect_narrative_tone(self, narrative: str) -> str:
        """Detect tone from narrative text."""
        narrative_lower = narrative.lower()
        
        # Check for tone indicators
        if any(word in narrative_lower for word in ['grim', 'dark', 'ominous', 'foreboding']):
            return 'dark'
        
        if any(word in narrative_lower for word in ['serious', 'grave', 'solemn']):
            return 'serious'
        
        if any(word in narrative_lower for word in ['tense', 'nervous', 'anxious']):
            return 'tense'
        
        if any(word in narrative_lower for word in ['dramatic', 'intense', 'powerful']):
            return 'dramatic'
        
        if any(word in narrative_lower for word in ['cheerful', 'pleasant', 'bright']):
            return 'light'
        
        if any(word in narrative_lower for word in ['calm', 'peaceful', 'quiet']):
            return 'calm'
        
        return 'neutral'
    
    def _tones_compatible(self, tone1: str, tone2: str) -> bool:
        """Check if two tones are compatible."""
        if tone1 == tone2:
            return True
        
        # Compatible tone groups
        compatible_groups = [
            {'grim', 'dark', 'serious'},
            {'tense', 'dramatic', 'serious'},
            {'calm', 'neutral', 'casual'},
            {'light', 'casual', 'neutral'}
        ]
        
        for group in compatible_groups:
            if tone1 in group and tone2 in group:
                return True
        
        return False
    
    def _has_humor(self, narrative: str) -> bool:
        """Check if narrative contains humor."""
        humor_indicators = ['laugh', 'joke', 'funny', 'chuckle', 'grin', 'smirk', 'amusing']
        narrative_lower = narrative.lower()
        return any(indicator in narrative_lower for indicator in humor_indicators)
    
    def _has_dark_imagery(self, narrative: str) -> bool:
        """Check if narrative contains dark imagery."""
        dark_indicators = ['blood', 'death', 'corpse', 'violence', 'murder', 'kill', 'dark', 'shadow']
        narrative_lower = narrative.lower()
        return any(indicator in narrative_lower for indicator in dark_indicators)
    
    def display_tone_assessment(self, assessment: Dict[str, Any]):
        """Display tone assessment."""
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}🎭 TONE ASSESSMENT{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}Recommended Tone: {assessment['recommended_tone']}{Color.RESET}")
        print(f"{Color.SYSTEM}Atmosphere: {assessment['atmosphere']}{Color.RESET}")
        print(f"{Color.SYSTEM}Violence Level: {assessment['violence_level']}/5{Color.RESET}")
        print(f"{Color.SYSTEM}Emotional Intensity: {assessment['emotional_intensity']}/5{Color.RESET}")
        print(f"{Color.NARRATIVE}Reasoning: {assessment['reasoning']}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
tone_consistency_validator = ToneConsistencyValidator()
