"""
Time/Lighting Auto-Update System for UTAS Simulation

Automatically updates scene descriptions when time advances to prevent
fake signals where lighting doesn't match time of day.
"""

from typing import Dict, Any, Optional
from color_utils import Color
from datetime import datetime, timedelta


class TimeLightingUpdater:
    """
    Automatically updates scene lighting and atmosphere based on time progression.
    
    Features:
    - Detects time changes
    - Updates lighting descriptions
    - Adjusts atmospheric details
    - Maintains scene continuity
    """
    
    def __init__(self):
        self.last_time_of_day = None
        self.last_lighting = None
        self.scene_base_description = ""
        self.time_tracking = {
            'last_update': None,
            'hours_passed': 0
        }
    
    def should_update_scene(self, current_time_context: Dict) -> bool:
        """Determine if scene needs updating based on time change."""
        current_time_of_day = current_time_context.get('time_of_day')
        
        # First time
        if self.last_time_of_day is None:
            self.last_time_of_day = current_time_of_day
            return False
        
        # Time of day changed
        if current_time_of_day != self.last_time_of_day:
            return True
        
        return False
    
    def update_scene_for_time(
        self,
        scene_description: str,
        time_context: Dict,
        force_update: bool = False
    ) -> str:
        """
        Update scene description to match current time/lighting.
        
        Args:
            scene_description: Current scene description
            time_context: Current time context dict
            force_update: Force update even if time hasn't changed
            
        Returns:
            Updated scene description
        """
        time_of_day = time_context.get('time_of_day', 'unknown')
        
        # Check if update needed
        if not force_update and not self.should_update_scene(time_context):
            return scene_description
        
        # Get lighting for current time
        lighting = self._get_lighting_for_time(time_of_day)
        
        # Update scene description
        updated_scene = self._apply_lighting_changes(
            scene_description,
            time_of_day,
            lighting,
            self.last_time_of_day,
            self.last_lighting
        )
        
        # Update tracking
        self.last_time_of_day = time_of_day
        self.last_lighting = lighting
        
        # Display update notification
        if self.last_time_of_day != time_of_day:
            print(f"\n{Color.SYSTEM}⏰ TIME PROGRESSION: {self.last_time_of_day} → {time_of_day}{Color.RESET}")
            print(f"{Color.SYSTEM}💡 Lighting updated: {self.last_lighting} → {lighting}{Color.RESET}\n")
        
        return updated_scene
    
    def _get_lighting_for_time(self, time_of_day: str) -> str:
        """Get appropriate lighting description for time of day."""
        lighting_map = {
            'dawn': 'dim twilight',
            'early_morning': 'soft morning light',
            'morning': 'bright daylight',
            'midday': 'harsh midday sun',
            'afternoon': 'warm afternoon light',
            'dusk': 'fading twilight',
            'evening': 'dim evening light',
            'night': 'darkness',
            'late_night': 'deep darkness',
            'midnight': 'pitch darkness'
        }
        
        # Handle enum values
        if hasattr(time_of_day, 'value'):
            time_of_day = time_of_day.value
        
        return lighting_map.get(str(time_of_day).lower(), 'ambient light')
    
    def _apply_lighting_changes(
        self,
        scene_description: str,
        new_time: str,
        new_lighting: str,
        old_time: str,
        old_lighting: str
    ) -> str:
        """Apply lighting changes to scene description."""
        
        # If no previous lighting, just add new lighting
        if not old_lighting:
            return self._add_lighting_description(scene_description, new_lighting)
        
        # Replace old lighting references with new ones
        updated_scene = scene_description
        
        # Replace specific lighting terms
        lighting_replacements = {
            'bright': self._get_brightness_term(new_lighting),
            'dark': self._get_darkness_term(new_lighting),
            'dim': self._get_dimness_term(new_lighting),
            'sunlight': self._get_sun_term(new_lighting),
            'moonlight': self._get_moon_term(new_lighting)
        }
        
        for old_term, new_term in lighting_replacements.items():
            if old_term in updated_scene.lower() and new_term:
                # Case-insensitive replacement
                import re
                pattern = re.compile(re.escape(old_term), re.IGNORECASE)
                updated_scene = pattern.sub(new_term, updated_scene, count=1)
        
        # Add atmospheric transition if time changed significantly
        if self._is_significant_time_change(old_time, new_time):
            transition = self._get_time_transition_text(old_time, new_time)
            updated_scene = f"{transition} {updated_scene}"
        
        return updated_scene
    
    def _add_lighting_description(self, scene_description: str, lighting: str) -> str:
        """Add lighting description to scene."""
        # Add at the beginning
        return f"Under {lighting}, {scene_description[0].lower()}{scene_description[1:]}"
    
    def _get_brightness_term(self, lighting: str) -> Optional[str]:
        """Get appropriate brightness term for lighting."""
        if 'bright' in lighting or 'harsh' in lighting:
            return 'bright'
        elif 'dim' in lighting or 'fading' in lighting:
            return 'dim'
        elif 'dark' in lighting:
            return 'dark'
        return None
    
    def _get_darkness_term(self, lighting: str) -> Optional[str]:
        """Get appropriate darkness term for lighting."""
        if 'darkness' in lighting or 'pitch' in lighting:
            return 'dark'
        elif 'dim' in lighting or 'twilight' in lighting:
            return 'shadowy'
        elif 'bright' in lighting:
            return 'well-lit'
        return None
    
    def _get_dimness_term(self, lighting: str) -> Optional[str]:
        """Get appropriate dimness term for lighting."""
        if 'dim' in lighting or 'twilight' in lighting:
            return 'dim'
        elif 'bright' in lighting:
            return 'bright'
        elif 'dark' in lighting:
            return 'dark'
        return None
    
    def _get_sun_term(self, lighting: str) -> Optional[str]:
        """Get appropriate sun term for lighting."""
        if 'sun' in lighting or 'daylight' in lighting:
            return 'sunlight'
        elif 'twilight' in lighting:
            return 'fading light'
        elif 'dark' in lighting or 'night' in lighting:
            return 'darkness'
        return None
    
    def _get_moon_term(self, lighting: str) -> Optional[str]:
        """Get appropriate moon term for lighting."""
        if 'dark' in lighting or 'night' in lighting:
            return 'moonlight'
        elif 'twilight' in lighting:
            return 'fading light'
        elif 'bright' in lighting or 'day' in lighting:
            return 'sunlight'
        return None
    
    def _is_significant_time_change(self, old_time: str, new_time: str) -> bool:
        """Check if time change is significant enough for transition text."""
        if not old_time or not new_time:
            return False
        
        # Define time progression
        time_order = [
            'dawn', 'early_morning', 'morning', 'midday', 'afternoon',
            'dusk', 'evening', 'night', 'late_night', 'midnight'
        ]
        
        try:
            old_idx = time_order.index(str(old_time).lower())
            new_idx = time_order.index(str(new_time).lower())
            # Significant if more than 2 steps apart
            return abs(new_idx - old_idx) >= 2
        except ValueError:
            return False
    
    def _get_time_transition_text(self, old_time: str, new_time: str) -> str:
        """Get transition text for time change."""
        transitions = {
            ('morning', 'afternoon'): "As the day progresses,",
            ('afternoon', 'evening'): "As evening approaches,",
            ('evening', 'night'): "As night falls,",
            ('night', 'dawn'): "As dawn breaks,",
            ('dawn', 'morning'): "As morning arrives,",
            ('midday', 'dusk'): "As the day wanes,",
            ('dusk', 'night'): "As darkness descends,",
        }
        
        key = (str(old_time).lower(), str(new_time).lower())
        return transitions.get(key, f"As time passes,")
    
    def get_atmospheric_details(self, time_of_day: str, location_type: str = 'outdoor') -> str:
        """Get atmospheric details for current time and location."""
        
        atmospheric_details = {
            'dawn': {
                'outdoor': "The sky lightens with the first hints of sunrise. Birds begin their morning songs.",
                'indoor': "Faint dawn light filters through windows, casting long shadows."
            },
            'morning': {
                'outdoor': "Morning sunlight bathes everything in warm, golden light. The air is fresh and cool.",
                'indoor': "Bright morning light streams through windows, illuminating the space."
            },
            'midday': {
                'outdoor': "The sun beats down from directly overhead, creating harsh shadows.",
                'indoor': "Harsh midday light floods through windows, making the space bright and warm."
            },
            'afternoon': {
                'outdoor': "Afternoon sun casts long shadows as it begins its descent.",
                'indoor': "Warm afternoon light creates a comfortable, well-lit atmosphere."
            },
            'dusk': {
                'outdoor': "The sky takes on hues of orange and purple as the sun sets. Shadows lengthen dramatically.",
                'indoor': "Fading twilight through windows signals the approaching night."
            },
            'evening': {
                'outdoor': "Evening darkness settles in, with only artificial lights providing illumination.",
                'indoor': "Evening darkness outside makes the interior lights seem brighter."
            },
            'night': {
                'outdoor': "Night has fallen, with darkness broken only by scattered lights.",
                'indoor': "Outside windows show only darkness, making the interior feel isolated."
            },
            'midnight': {
                'outdoor': "Deep night surrounds everything. The world feels quiet and still.",
                'indoor': "The late hour is evident in the stillness and darkness outside."
            }
        }
        
        # Handle enum values
        if hasattr(time_of_day, 'value'):
            time_of_day = time_of_day.value
        
        time_key = str(time_of_day).lower()
        return atmospheric_details.get(time_key, {}).get(location_type, "")
    
    def display_time_update(self, old_time: str, new_time: str, old_lighting: str, new_lighting: str):
        """Display time/lighting update notification."""
        print(f"\n{Color.SYSTEM}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}⏰ TIME & LIGHTING UPDATE{Color.RESET}")
        print(f"{Color.SYSTEM}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}Time: {old_time} → {new_time}{Color.RESET}")
        print(f"{Color.INFO}Lighting: {old_lighting} → {new_lighting}{Color.RESET}")
        print(f"{Color.SYSTEM}{'='*80}{Color.RESET}\n")


# Global instance
time_lighting_updater = TimeLightingUpdater()
