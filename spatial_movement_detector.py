"""
Spatial Movement Detector - Detects movement within locations

Detects when actors move around within the same location and extracts
the target destination (obstacle, zone, or direction).
"""

import re
from typing import Optional, Dict, Any
from openrouter_config import create_role_client, OpenRouterConfig


class SpatialMovementDetector:
    """
    Detects movement within locations and extracts target destinations.
    """
    
    def __init__(self, llm_client=None):
        """Initialize with optional LLM client"""
        if llm_client is None:
            llm_client = OpenRouterConfig.create_client()
        self.llm_client = llm_client
        
        # Movement keywords
        self.movement_verbs = [
            'walk', 'move', 'go', 'head', 'run', 'sprint', 'jog',
            'approach', 'step', 'stride', 'rush', 'hurry', 'dash',
            'sneak', 'creep', 'crawl', 'climb', 'jump'
        ]
        
        # Direction keywords
        self.directions = [
            'left', 'right', 'forward', 'back', 'backward', 'backwards',
            'north', 'south', 'east', 'west',
            'center', 'middle', 'corner', 'side', 'edge',
            'front', 'rear', 'entrance', 'exit'
        ]
        
        # Prepositions indicating movement
        self.movement_prepositions = ['to', 'toward', 'towards', 'near', 'by', 'at']
    
    def detect_movement(self, text: str, scene_description: str = "") -> Optional[Dict[str, Any]]:
        """
        Detect if text indicates movement within current location.
        
        Args:
            text: User input or narrative text
            scene_description: Current scene context (for LLM)
        
        Returns:
            {
                "is_movement": True,
                "target": "workbench",
                "target_type": "obstacle",  # obstacle/zone/direction
                "movement_type": "walk",
                "confidence": "high"
            }
        """
        text_lower = text.lower()
        
        # Quick keyword check first
        has_movement_verb = any(verb in text_lower for verb in self.movement_verbs)
        has_preposition = any(prep in text_lower for prep in self.movement_prepositions)
        
        if not (has_movement_verb or has_preposition):
            return None  # No movement detected
        
        # Use LLM for detailed analysis
        try:
            prompt = f"""Analyze if this text indicates movement within the current location.

TEXT: "{text}"

SCENE CONTEXT:
{scene_description[:300] if scene_description else "Unknown location"}

Respond with JSON:
{{
    "is_movement": true/false,
    "target": "name of destination (obstacle, zone, or direction)",
    "target_type": "obstacle" or "zone" or "direction",
    "movement_type": "walk/run/sneak/etc",
    "confidence": "high/medium/low"
}}

Examples:
- "I walk to the workbench" → {{"is_movement": true, "target": "workbench", "target_type": "obstacle", "movement_type": "walk"}}
- "I move to the back of the room" → {{"is_movement": true, "target": "back", "target_type": "direction", "movement_type": "walk"}}
- "I approach the door" → {{"is_movement": true, "target": "door", "target_type": "obstacle", "movement_type": "walk"}}
- "I examine the tool" → {{"is_movement": false}}

Respond ONLY with JSON, no other text."""

            response = self.llm_client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=150
            )
            
            response_text = response.choices[0].message.content.strip()
            
            # Extract JSON
            import json
            if '```json' in response_text:
                response_text = response_text.split('```json')[1].split('```')[0].strip()
            elif '```' in response_text:
                response_text = response_text.split('```')[1].split('```')[0].strip()
            
            result = json.loads(response_text)
            
            if result.get("is_movement"):
                return result
            else:
                return None
        
        except Exception as e:
            print(f"[MOVEMENT DETECTOR] LLM analysis failed: {e}")
            
            # Fallback to pattern matching
            return self._fallback_detection(text_lower)
    
    def _fallback_detection(self, text_lower: str) -> Optional[Dict[str, Any]]:
        """Fallback pattern-based detection"""
        # Pattern: [movement verb] [preposition] [target]
        for verb in self.movement_verbs:
            for prep in self.movement_prepositions:
                pattern = rf'\b{verb}\s+{prep}\s+(?:the\s+)?(\w+(?:\s+\w+)*)'
                match = re.search(pattern, text_lower)
                if match:
                    target = match.group(1)
                    return {
                        "is_movement": True,
                        "target": target,
                        "target_type": "obstacle",  # Assume obstacle
                        "movement_type": verb,
                        "confidence": "medium"
                    }
        
        # Pattern: [movement verb] [direction]
        for verb in self.movement_verbs:
            for direction in self.directions:
                if f"{verb} {direction}" in text_lower or f"{verb} to the {direction}" in text_lower:
                    return {
                        "is_movement": True,
                        "target": direction,
                        "target_type": "direction",
                        "movement_type": verb,
                        "confidence": "medium"
                    }
        
        return None


# Global accessor
_movement_detector: Optional[SpatialMovementDetector] = None

def get_movement_detector() -> SpatialMovementDetector:
    """Get or create global movement detector"""
    global _movement_detector
    if _movement_detector is None:
        _movement_detector = SpatialMovementDetector()
    return _movement_detector
