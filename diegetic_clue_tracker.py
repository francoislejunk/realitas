"""
Diegetic Clue Tracker for UTAS Simulation

Detects environmental clues in narratives that imply the presence of actors.
Enables progressive discovery mechanics where following clues leads to NUA introduction.
"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from enum import Enum


class ClueType(Enum):
    """Types of environmental clues that imply actor presence."""
    FOOTPRINTS = "footprints"
    TRACKS = "tracks"
    VOICES = "voices"
    SOUNDS = "sounds"
    BLOOD_TRAIL = "blood_trail"
    SMOKE = "smoke"
    LIGHT = "light"
    MOVEMENT = "movement"
    SHADOW = "shadow"
    SCENT = "scent"


@dataclass
class ClueConfig:
    """Configuration for a specific clue type."""
    clue_type: ClueType
    keywords: List[str]
    implies: str  # What this clue implies (e.g., "NUA", "NUA (injured)")
    discovery_threshold: int  # How many follow actions before introduction
    urgency: str  # "low", "medium", "high" - affects narrative tone


class DiegeticClueTracker:
    """
    Detects and tracks environmental clues in narratives that imply actor presence.
    
    Features:
    - Pattern-based clue detection
    - Context-aware clue classification
    - Confidence scoring
    - Multiple clue type support
    """
    
    def __init__(self):
        """Initialize the clue tracker with predefined clue configurations."""
        self.clue_configs = {
            ClueType.FOOTPRINTS: ClueConfig(
                clue_type=ClueType.FOOTPRINTS,
                keywords=[
                    'footprints', 'footsteps', 'tracks', 'trail', 'boot prints',
                    'shoe prints', 'prints in the dust', 'muddy footprints'
                ],
                implies="NUA",
                discovery_threshold=3,
                urgency="medium"
            ),
            ClueType.VOICES: ClueConfig(
                clue_type=ClueType.VOICES,
                keywords=[
                    'voices', 'talking', 'conversation', 'shouting', 'yelling',
                    'whispering', 'murmuring', 'arguing', 'laughing', 'crying'
                ],
                implies="NUA",
                discovery_threshold=2,
                urgency="high"
            ),
            ClueType.SOUNDS: ClueConfig(
                clue_type=ClueType.SOUNDS,
                keywords=[
                    'footsteps', 'movement', 'rustling', 'shuffling', 'scraping',
                    'clanging', 'banging', 'tapping', 'breathing'
                ],
                implies="NUA",
                discovery_threshold=2,
                urgency="medium"
            ),
            ClueType.BLOOD_TRAIL: ClueConfig(
                clue_type=ClueType.BLOOD_TRAIL,
                keywords=[
                    'blood trail', 'fresh blood', 'blood drops', 'blood stain',
                    'bloody footprints', 'blood smear', 'crimson trail', 'trail of blood'
                ],
                implies="NUA (injured)",
                discovery_threshold=2,
                urgency="high"
            ),
            ClueType.SMOKE: ClueConfig(
                clue_type=ClueType.SMOKE,
                keywords=[
                    'smoke', 'campfire', 'fire', 'cooking smell', 'burning',
                    'smoke rising', 'smoldering', 'embers'
                ],
                implies="NUA (campfire/cooking)",
                discovery_threshold=3,
                urgency="low"
            ),
            ClueType.LIGHT: ClueConfig(
                clue_type=ClueType.LIGHT,
                keywords=[
                    'flashlight', 'torch', 'lantern', 'light moving', 'glow',
                    'flickering light', 'beam of light', 'illumination'
                ],
                implies="NUA",
                discovery_threshold=2,
                urgency="medium"
            ),
            ClueType.MOVEMENT: ClueConfig(
                clue_type=ClueType.MOVEMENT,
                keywords=[
                    'movement', 'figure', 'shadow moving', 'someone moving',
                    'motion', 'shifting', 'darting', 'glimpse of movement'
                ],
                implies="NUA",
                discovery_threshold=1,
                urgency="high"
            ),
            ClueType.SHADOW: ClueConfig(
                clue_type=ClueType.SHADOW,
                keywords=[
                    'shadow', 'silhouette', 'outline', 'shape', 'dark figure',
                    'shadowy form', 'looming shadow'
                ],
                implies="NUA",
                discovery_threshold=1,
                urgency="high"
            ),
            ClueType.SCENT: ClueConfig(
                clue_type=ClueType.SCENT,
                keywords=[
                    'smell', 'scent', 'odor', 'perfume', 'cologne', 'sweat',
                    'body odor', 'fresh scent', 'lingering smell'
                ],
                implies="NUA",
                discovery_threshold=2,
                urgency="medium"
            )
        }
        
        # Patterns for detecting "fresh" or "recent" modifiers
        self.freshness_patterns = [
            r'\b(fresh|recent|new|just made|still warm|barely settled)\b',
            r'\b(moments ago|just now|recently|not long ago)\b'
        ]
        
        # Patterns for detecting direction/continuation
        self.direction_patterns = [
            r'\b(leading|heading|going|continuing|extending)\s+(to|toward|towards|into|through|north|south|east|west)\b',
            r'\b(trail|path|tracks)\s+(leads|continues|extends|goes)\b'
        ]
    
    def analyze_narrative_for_clues(self, narrative: str) -> List[Dict[str, Any]]:
        """
        Analyze a narrative text for environmental clues that imply actor presence.
        
        Args:
            narrative: The narrative text to analyze
            
        Returns:
            List of detected clues with metadata
        """
        if not narrative:
            return []
        
        narrative_lower = narrative.lower()
        detected_clues = []
        
        for clue_type, config in self.clue_configs.items():
            # Check each keyword for this clue type
            for keyword in config.keywords:
                if keyword in narrative_lower:
                    # Extract context around the keyword
                    context = self._extract_context(narrative, keyword)
                    
                    # Filter out metaphorical usage (e.g., "music bleeding from speakers")
                    if self._is_metaphorical_usage(clue_type, context):
                        continue
                    
                    # Check for freshness indicators
                    is_fresh = self._check_freshness(context)
                    
                    # Check for direction indicators
                    has_direction = self._check_direction(context)
                    
                    # Calculate confidence
                    confidence = self._calculate_confidence(
                        keyword, context, is_fresh, has_direction
                    )
                    
                    clue_data = {
                        'type': clue_type.value,
                        'keyword': keyword,
                        'implies': config.implies,
                        'threshold': config.discovery_threshold,
                        'urgency': config.urgency,
                        'is_fresh': is_fresh,
                        'has_direction': has_direction,
                        'confidence': confidence,
                        'context': context,
                        'full_narrative': narrative
                    }
                    
                    detected_clues.append(clue_data)
                    
                    # Only detect one keyword per clue type to avoid duplicates
                    break
        
        return detected_clues
    
    def _extract_context(self, narrative: str, keyword: str, window: int = 50) -> str:
        """Extract context around a keyword."""
        narrative_lower = narrative.lower()
        keyword_lower = keyword.lower()
        
        index = narrative_lower.find(keyword_lower)
        if index == -1:
            return ""
        
        start = max(0, index - window)
        end = min(len(narrative), index + len(keyword) + window)
        
        return narrative[start:end]
    
    def _is_metaphorical_usage(self, clue_type: ClueType, context: str) -> bool:
        """
        Check if the detected keyword is being used metaphorically rather than literally.
        
        Args:
            clue_type: The type of clue detected
            context: The surrounding text context
            
        Returns:
            True if this appears to be metaphorical usage (should be filtered out)
        """
        context_lower = context.lower()
        
        # Blood trail specific metaphorical patterns
        if clue_type == ClueType.BLOOD_TRAIL:
            metaphorical_patterns = [
                r'(music|sound|light|color|paint)\s+bleed',  # "music bleeding"
                r'bleed\s+(from|through|into)\s+(speaker|wall|window)',  # "bleeding from speakers"
                r'(audio|visual|color)\s+.*\s+bleed',  # "audio bleeding"
            ]
            for pattern in metaphorical_patterns:
                if re.search(pattern, context_lower):
                    return True
        
        # Smoke specific metaphorical patterns
        if clue_type == ClueType.SMOKE:
            metaphorical_patterns = [
                r'smoke\s+(show|screen|mirror)',  # "smoke and mirrors"
                r'smoking\s+(hot|gun)',  # "smoking hot", "smoking gun"
            ]
            for pattern in metaphorical_patterns:
                if re.search(pattern, context_lower):
                    return True
        
        return False
    
    def _check_freshness(self, context: str) -> bool:
        """Check if context indicates the clue is fresh/recent."""
        context_lower = context.lower()
        
        for pattern in self.freshness_patterns:
            if re.search(pattern, context_lower):
                return True
        
        return False
    
    def _check_direction(self, context: str) -> bool:
        """Check if context indicates a direction or continuation."""
        context_lower = context.lower()
        
        for pattern in self.direction_patterns:
            if re.search(pattern, context_lower):
                return True
        
        return False
    
    def _calculate_confidence(self, keyword: str, context: str, 
                            is_fresh: bool, has_direction: bool) -> str:
        """
        Calculate confidence level for clue detection.
        
        Returns: "low", "medium", or "high"
        """
        score = 0
        
        # Base score for keyword match
        score += 1
        
        # Bonus for freshness
        if is_fresh:
            score += 1
        
        # Bonus for direction
        if has_direction:
            score += 1
        
        # Bonus for longer context (more detail)
        if len(context) > 30:
            score += 1
        
        if score >= 3:
            return "high"
        elif score >= 2:
            return "medium"
        else:
            return "low"
    
    def is_following_action(self, user_input: str, clue_type: str) -> bool:
        """
        Determine if user input represents following a specific clue type.
        
        Args:
            user_input: The user's action
            clue_type: The type of clue (e.g., "footprints")
            
        Returns:
            True if action is following this clue type
        """
        user_lower = user_input.lower()
        
        # Generic follow patterns
        follow_patterns = [
            r'\b(follow|track|pursue|chase|trail)\b',
            r'\b(continue|keep)\s+(following|tracking|pursuing)\b',
            r'\b(go|head|move)\s+(toward|towards|to|along)\b'
        ]
        
        # Check if user is following
        is_following = any(re.search(pattern, user_lower) for pattern in follow_patterns)
        
        if not is_following:
            return False
        
        # Check if they're following THIS specific clue type
        clue_keywords = self.clue_configs.get(ClueType(clue_type))
        if clue_keywords:
            # Check if any clue keyword is mentioned
            for keyword in clue_keywords.keywords:
                if keyword in user_lower:
                    return True
            
            # Also check for generic references like "the trail", "them", "it"
            generic_refs = ['trail', 'tracks', 'them', 'it', 'the sound', 'the voice']
            if any(ref in user_lower for ref in generic_refs):
                return True
        
        return False
    
    def get_clue_description(self, clue_type: str, follow_count: int, threshold: int) -> str:
        """
        Generate a description of clue progression for narrative purposes.
        
        Args:
            clue_type: Type of clue being followed
            follow_count: How many times it's been followed
            threshold: Total threshold before discovery
            
        Returns:
            Description text for narrative integration
        """
        progress = follow_count / threshold
        
        if progress < 0.33:
            return f"The {clue_type} continue, still clear..."
        elif progress < 0.66:
            return f"The {clue_type} grow more distinct. You're getting closer..."
        else:
            return f"The {clue_type} are very fresh now. The source must be nearby..."


# Global instance for easy access
_clue_tracker_instance = None

def get_clue_tracker() -> DiegeticClueTracker:
    """Get or create the global clue tracker instance."""
    global _clue_tracker_instance
    if _clue_tracker_instance is None:
        _clue_tracker_instance = DiegeticClueTracker()
    return _clue_tracker_instance
