"""
Scene Continuity Validator for UTAS Simulation

Prevents fake signals related to location, time, and context inconsistencies.
Ensures narrative stays consistent with scene state.
"""

from typing import Dict, Any, List, Optional, Tuple
from color_utils import Color
import re


class SceneContinuityValidator:
    """
    Validates and maintains scene continuity across actions and narratives.
    
    Tracks:
    - Current location (indoor/outdoor, specific place)
    - Time of day and lighting
    - Present NPCs and their states
    - Recent events
    - Environmental conditions
    """
    
    def __init__(self):
        self.current_location = None
        self.location_type = None  # 'indoor' or 'outdoor'
        self.time_of_day = None
        self.lighting = None
        self.present_npcs = []
        self.departed_npcs = []
        self.dead_npcs = []
        self.unconscious_npcs = []
        self.recent_events = []
        self.environmental_conditions = {}
    
    def update_from_scene(self, scene_description: str, time_context: Dict = None):
        """Update continuity state from scene description."""
        
        # Extract location
        self.current_location = self._extract_location(scene_description)
        self.location_type = self._determine_location_type(scene_description)
        
        # Update time and lighting
        if time_context:
            self.time_of_day = time_context.get('time_of_day')
            self.lighting = time_context.get('lighting')
        else:
            self.time_of_day = self._extract_time(scene_description)
            self.lighting = self._extract_lighting(scene_description)
        
        # Extract environmental conditions
        self.environmental_conditions = self._extract_conditions(scene_description)
    
    def validate_narrative(
        self,
        narrative: str,
        action: str,
        actor_name: str
    ) -> Tuple[bool, List[str]]:
        """
        Validate that narrative is consistent with current scene state.
        
        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        
        # Check location consistency
        location_issues = self._check_location_consistency(narrative, action)
        issues.extend(location_issues)
        
        # Check time/lighting consistency
        time_issues = self._check_time_consistency(narrative)
        issues.extend(time_issues)
        
        # Check NPC presence consistency
        npc_issues = self._check_npc_consistency(narrative)
        issues.extend(npc_issues)
        
        # Check environmental consistency
        env_issues = self._check_environmental_consistency(narrative)
        issues.extend(env_issues)
        
        is_valid = len(issues) == 0
        return is_valid, issues
    
    def _extract_location(self, scene_description: str) -> str:
        """Extract specific location from scene description."""
        scene_lower = scene_description.lower()
        
        # Common location patterns
        locations = [
            'restaurant', 'diner', 'cafe', 'bar', 'pub', 'tavern',
            'street', 'alley', 'sidewalk', 'road', 'highway',
            'apartment', 'house', 'building', 'office', 'warehouse',
            'park', 'plaza', 'square', 'parking lot',
            'store', 'shop', 'mall', 'market',
            'hotel', 'motel', 'lobby',
            'car', 'vehicle', 'bus', 'train'
        ]
        
        for location in locations:
            if location in scene_lower:
                return location
        
        return "unknown location"
    
    def _determine_location_type(self, scene_description: str) -> str:
        """Determine if location is indoor or outdoor."""
        scene_lower = scene_description.lower()
        
        # Indoor indicators
        indoor_keywords = [
            'inside', 'interior', 'indoors', 'room', 'ceiling', 'walls',
            'restaurant', 'diner', 'cafe', 'bar', 'office', 'apartment',
            'building', 'store', 'shop', 'lobby', 'hallway'
        ]
        
        # Outdoor indicators
        outdoor_keywords = [
            'outside', 'exterior', 'outdoors', 'street', 'alley', 'sidewalk',
            'sky', 'sun', 'moon', 'stars', 'clouds', 'rain', 'wind',
            'park', 'plaza', 'parking lot', 'road', 'highway'
        ]
        
        indoor_count = sum(1 for keyword in indoor_keywords if keyword in scene_lower)
        outdoor_count = sum(1 for keyword in outdoor_keywords if keyword in scene_lower)
        
        if indoor_count > outdoor_count:
            return 'indoor'
        elif outdoor_count > indoor_count:
            return 'outdoor'
        else:
            return 'ambiguous'
    
    def _extract_time(self, scene_description: str) -> str:
        """Extract time of day from scene description."""
        scene_lower = scene_description.lower()
        
        time_keywords = {
            'dawn': ['dawn', 'sunrise', 'early morning'],
            'morning': ['morning'],
            'midday': ['midday', 'noon'],
            'afternoon': ['afternoon'],
            'dusk': ['dusk', 'sunset', 'twilight'],
            'evening': ['evening'],
            'night': ['night', 'nighttime'],
            'midnight': ['midnight', 'late night']
        }
        
        for time_period, keywords in time_keywords.items():
            if any(keyword in scene_lower for keyword in keywords):
                return time_period
        
        return 'unknown'
    
    def _extract_lighting(self, scene_description: str) -> str:
        """Extract lighting conditions from scene description."""
        scene_lower = scene_description.lower()
        
        if any(word in scene_lower for word in ['dark', 'dim', 'shadowy', 'gloomy']):
            return 'dark'
        elif any(word in scene_lower for word in ['bright', 'brilliant', 'sunny', 'illuminated']):
            return 'bright'
        elif any(word in scene_lower for word in ['twilight', 'dusk', 'fading']):
            return 'dim'
        else:
            return 'normal'
    
    def _extract_conditions(self, scene_description: str) -> Dict[str, bool]:
        """Extract environmental conditions."""
        scene_lower = scene_description.lower()
        
        return {
            'raining': 'rain' in scene_lower or 'raining' in scene_lower,
            'snowing': 'snow' in scene_lower or 'snowing' in scene_lower,
            'foggy': 'fog' in scene_lower or 'foggy' in scene_lower or 'mist' in scene_lower,
            'windy': 'wind' in scene_lower or 'windy' in scene_lower or 'breeze' in scene_lower,
            'crowded': 'crowd' in scene_lower or 'crowded' in scene_lower or 'busy' in scene_lower,
            'quiet': 'quiet' in scene_lower or 'empty' in scene_lower or 'deserted' in scene_lower
        }
    
    def _check_location_consistency(self, narrative: str, action: str) -> List[str]:
        """Check for location inconsistencies using LLM semantic understanding."""
        issues = []
        narrative_lower = narrative.lower()
        action_lower = action.lower()
        
        # Check indoor/outdoor consistency (keep original hardcoded checks)
        if self.location_type == 'indoor':
            outdoor_indicators = ['outside', 'street', 'sky', 'sun', 'rain', 'wind', 'clouds']
            for indicator in outdoor_indicators:
                if indicator in narrative_lower:
                    # Use LLM to verify if this is a real violation or just dialogue/mention
                    if not self._is_dialogue_mention(narrative, indicator):
                        issues.append(f"LOCATION INCONSISTENCY: Narrative mentions '{indicator}' but scene is indoors at {self.current_location}")
        
        elif self.location_type == 'outdoor':
            indoor_indicators = ['inside', 'ceiling', 'walls', 'door', 'room']
            for indicator in indoor_indicators:
                if indicator in narrative_lower:
                    # Use LLM to verify if this is a real violation or just dialogue/mention
                    if not self._is_dialogue_mention(narrative, indicator):
                        issues.append(f"LOCATION INCONSISTENCY: Narrative mentions '{indicator}' but scene is outdoors at {self.current_location}")
        
        # Check for location changes without transition
        new_locations = ['enters', 'walks into', 'arrives at', 'leaves', 'exits']
        if any(phrase in action_lower for phrase in new_locations):
            # Location change is intentional, no validation needed
            return issues
        
        # Use LLM to semantically validate specific location consistency
        if self.current_location and self.current_location != 'unknown location':
            try:
                from openrouter_config import create_role_client, OpenRouterConfig
                client = create_role_client("coordination")
                
                validation_prompt = f"""Analyze if this narrative has a LOCATION INCONSISTENCY.

Current Scene Location: {self.current_location}
Location Type: {self.location_type or 'unknown'}
Narrative: "{narrative}"

**CRITICAL DISTINCTION:**
- ✅ ALLOWED: Mentioning locations in DIALOGUE or PROPOSALS ("Let's meet at the cafe", "How about the park?")
- ✅ ALLOWED: Mentioning locations in MEMORIES or PLANS ("I remember the restaurant", "We should go to...")
- ✅ ALLOWED: Mentioning locations as DESTINATIONS ("heading to the store", "planning to visit...")
- ✅ ALLOWED: Describing external conditions from inside ("the rain outside", "traffic on the street")
- ❌ VIOLATION: Describing the CHARACTER as CURRENTLY BEING at a different location ("sits in the cafe", "walks through the park")

**Examples:**
✅ VALID: Character at apartment says "Let's meet at the cafe tomorrow" → Just dialogue, no violation
✅ VALID: Character at apartment says "I'm heading outside" → Intentional movement, no violation
✅ VALID: Character at apartment mentions "the rain outside" → Describing external conditions, no violation
❌ INVALID: Character at apartment, narrative says "sits at the cafe counter" → Claims to BE elsewhere

Question: Does the narrative describe the character as CURRENTLY BEING at a location different from "{self.current_location}"?
Answer ONLY "YES" (violation) or "NO" (valid)."""

                response = client.chat.completions.create(
                    model=OpenRouterConfig.get_model_for_role("coordination"),
                    messages=[{"role": "user", "content": validation_prompt}],
                    temperature=0.1,
                    max_tokens=10
                )
                
                result = response.choices[0].message.content.strip().upper()
                if result == "YES":
                    issues.append(f"LOCATION INCONSISTENCY: Narrative describes character at different location than {self.current_location}")
            except Exception as e:
                # Fallback: if LLM check fails, allow the action
                print(f"{Color.WARNING}[CONTINUITY] Location validation failed, allowing action: {e}{Color.RESET}")
        
        return issues
    
    def _is_dialogue_mention(self, narrative: str, keyword: str) -> bool:
        """Use LLM to check if keyword mention is just dialogue/proposal vs actual location claim."""
        try:
            from openrouter_config import create_role_client, OpenRouterConfig
            client = create_role_client("coordination")
            
            prompt = f"""Is this keyword mentioned in DIALOGUE/PROPOSAL or as a CURRENT LOCATION DESCRIPTION?

Narrative: "{narrative}"
Keyword: "{keyword}"

**DIALOGUE/PROPOSAL (return YES):**
- In quotes/speech ("Let's go outside", "I see the rain")
- Describing external conditions ("rain outside the window")
- Future plans or suggestions

**CURRENT LOCATION (return NO):**
- Describing character's current environment as if they're there
- Action happening in that environment

Is this keyword mentioned in dialogue/proposal/external description (not claiming character is there)?
Answer ONLY "YES" (dialogue/mention) or "NO" (location claim)."""

            response = client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("coordination"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                max_tokens=10
            )
            
            result = response.choices[0].message.content.strip().upper()
            return result == "YES"
        except Exception:
            # Fallback: assume it's dialogue/mention (allow it)
            return True
    
    def _check_time_consistency(self, narrative: str) -> List[str]:
        """Check for time/lighting inconsistencies."""
        issues = []
        narrative_lower = narrative.lower()
        
        # Check lighting consistency
        if self.lighting == 'dark':
            bright_indicators = ['bright', 'sunny', 'sunlight', 'brilliant light']
            for indicator in bright_indicators:
                if indicator in narrative_lower:
                    issues.append(f"TIME INCONSISTENCY: Narrative mentions '{indicator}' but scene lighting is dark")
        
        elif self.lighting == 'bright':
            dark_indicators = ['dark', 'shadows', 'moonlight', 'starlight']
            for indicator in dark_indicators:
                if indicator in narrative_lower:
                    issues.append(f"TIME INCONSISTENCY: Narrative mentions '{indicator}' but scene lighting is bright")
        
        # Check time of day consistency
        if self.time_of_day == 'night' or self.time_of_day == 'midnight':
            day_indicators = ['morning', 'afternoon', 'daylight', 'sun']
            for indicator in day_indicators:
                if indicator in narrative_lower:
                    issues.append(f"TIME INCONSISTENCY: Narrative mentions '{indicator}' but it's {self.time_of_day}")
        
        elif self.time_of_day in ['morning', 'midday', 'afternoon']:
            night_indicators = ['night', 'midnight', 'moonlight', 'stars']
            for indicator in night_indicators:
                if indicator in narrative_lower:
                    issues.append(f"TIME INCONSISTENCY: Narrative mentions '{indicator}' but it's {self.time_of_day}")
        
        return issues
    
    def _check_npc_consistency(self, narrative: str) -> List[str]:
        """Check for NPC presence inconsistencies."""
        issues = []
        narrative_lower = narrative.lower()
        
        # Check if narrative mentions departed NPCs
        for npc_name in self.departed_npcs:
            if npc_name.lower() in narrative_lower:
                issues.append(f"NPC INCONSISTENCY: Narrative mentions {npc_name} but they left the scene")
        
        # Check if narrative mentions dead NPCs as if alive
        for npc_name in self.dead_npcs:
            if npc_name.lower() in narrative_lower:
                # Check if it's acknowledging their death
                death_context = ['dead', 'corpse', 'body', 'killed', 'died']
                if not any(word in narrative_lower for word in death_context):
                    issues.append(f"NPC INCONSISTENCY: Narrative mentions {npc_name} acting but they are dead")
        
        # Check if narrative mentions unconscious NPCs as if conscious
        for npc_name in self.unconscious_npcs:
            if npc_name.lower() in narrative_lower:
                unconscious_context = ['unconscious', 'knocked out', 'limp', 'unresponsive']
                if not any(word in narrative_lower for word in unconscious_context):
                    issues.append(f"NPC INCONSISTENCY: Narrative mentions {npc_name} acting but they are unconscious")
        
        return issues
    
    def _check_environmental_consistency(self, narrative: str) -> List[str]:
        """Check for environmental condition inconsistencies."""
        issues = []
        narrative_lower = narrative.lower()
        
        # Check weather consistency
        if self.environmental_conditions.get('raining'):
            if 'sunny' in narrative_lower or 'clear sky' in narrative_lower:
                issues.append("ENVIRONMENT INCONSISTENCY: Narrative mentions sunny/clear but it's raining")
        
        if self.environmental_conditions.get('crowded'):
            if 'empty' in narrative_lower or 'deserted' in narrative_lower:
                issues.append("ENVIRONMENT INCONSISTENCY: Narrative mentions empty/deserted but scene is crowded")
        
        if self.environmental_conditions.get('quiet'):
            if 'noisy' in narrative_lower or 'loud' in narrative_lower or 'bustling' in narrative_lower:
                issues.append("ENVIRONMENT INCONSISTENCY: Narrative mentions noisy/loud but scene is quiet")
        
        return issues
    
    def mark_npc_departed(self, npc_name: str):
        """Mark an NPC as having left the scene."""
        if npc_name in self.present_npcs:
            self.present_npcs.remove(npc_name)
        if npc_name not in self.departed_npcs:
            self.departed_npcs.append(npc_name)
            print(f"{Color.WARNING}📍 Continuity: {npc_name} has left the scene{Color.RESET}")
    
    def mark_npc_dead(self, npc_name: str):
        """Mark an NPC as dead."""
        if npc_name in self.present_npcs:
            self.present_npcs.remove(npc_name)
        if npc_name not in self.dead_npcs:
            self.dead_npcs.append(npc_name)
            print(f"{Color.ERROR}💀 Continuity: {npc_name} is dead{Color.RESET}")
    
    def mark_npc_unconscious(self, npc_name: str):
        """Mark an NPC as unconscious."""
        if npc_name not in self.unconscious_npcs:
            self.unconscious_npcs.append(npc_name)
            print(f"{Color.WARNING}😵 Continuity: {npc_name} is unconscious{Color.RESET}")
    
    def mark_npc_conscious(self, npc_name: str):
        """Mark an NPC as regaining consciousness."""
        if npc_name in self.unconscious_npcs:
            self.unconscious_npcs.remove(npc_name)
            print(f"{Color.SUCCESS}✓ Continuity: {npc_name} regains consciousness{Color.RESET}")
    
    def add_npc(self, npc_name: str):
        """Add an NPC to the scene."""
        if npc_name not in self.present_npcs and npc_name not in self.dead_npcs:
            self.present_npcs.append(npc_name)
    
    def record_event(self, event_description: str):
        """Record a significant event for continuity tracking."""
        self.recent_events.append(event_description)
        # Keep only last 10 events
        if len(self.recent_events) > 10:
            self.recent_events.pop(0)
    
    def display_continuity_warnings(self, issues: List[str]):
        """Display continuity issues as warnings."""
        if not issues:
            return
        
        print(f"\n{Color.ERROR}{'='*80}{Color.RESET}")
        print(f"{Color.ERROR}⚠️  CONTINUITY WARNINGS{Color.RESET}")
        print(f"{Color.ERROR}{'='*80}{Color.RESET}")
        
        for issue in issues:
            print(f"{Color.WARNING}   • {issue}{Color.RESET}")
        
        print(f"{Color.ERROR}{'='*80}{Color.RESET}\n")
    
    def get_continuity_context(self) -> str:
        """Get current continuity state as context string for LLMs."""
        context_parts = []
        
        context_parts.append(f"CURRENT LOCATION: {self.current_location} ({self.location_type})")
        context_parts.append(f"TIME: {self.time_of_day}, LIGHTING: {self.lighting}")
        
        if self.present_npcs:
            context_parts.append(f"PRESENT NPCs: {', '.join(self.present_npcs)}")
        
        if self.departed_npcs:
            context_parts.append(f"DEPARTED NPCs (not present): {', '.join(self.departed_npcs)}")
        
        if self.dead_npcs:
            context_parts.append(f"DEAD NPCs (cannot act): {', '.join(self.dead_npcs)}")
        
        if self.unconscious_npcs:
            context_parts.append(f"UNCONSCIOUS NPCs (cannot act): {', '.join(self.unconscious_npcs)}")
        
        if any(self.environmental_conditions.values()):
            active_conditions = [k for k, v in self.environmental_conditions.items() if v]
            context_parts.append(f"CONDITIONS: {', '.join(active_conditions)}")
        
        return "\n".join(context_parts)


# Global instance
continuity_validator = SceneContinuityValidator()
