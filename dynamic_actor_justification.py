"""
Dynamic Actor Justification System for UTAS Simulation

Ensures NUAs appear in scenes with narrative justification.
Prevents fake signals where NUAs randomly appear without explanation.
"""

from typing import Dict, Any, Optional, List
from color_utils import Color


class DynamicActorJustification:
    """
    Provides narrative justification for NUA appearances.
    
    Features:
    - Generates arrival narratives
    - Explains NUA presence
    - Tracks NUA locations
    - Prevents random appearances
    """
    
    def __init__(self):
        self.nua_locations = {}  # Track where each NUA is
        self.nua_roles = {}  # Track NUA roles (guard, merchant, etc.)
        self.scene_occupants = {}  # Track who belongs in each scene
    
    def register_nua(
        self,
        nua_name: str,
        role: str,
        location: str,
        belongs_here: bool = True
    ):
        """Register a NUA with their role and location."""
        self.nua_locations[nua_name] = location
        self.nua_roles[nua_name] = role
        
        if belongs_here:
            if location not in self.scene_occupants:
                self.scene_occupants[location] = []
            if nua_name not in self.scene_occupants[location]:
                self.scene_occupants[location].append(nua_name)
    
    def generate_arrival_justification(
        self,
        nua_name: str,
        nua_role: str,
        current_location: str,
        scene_context: str
    ) -> Dict[str, Any]:
        """
        Generate narrative justification for NUA appearing in scene.
        
        Returns:
            Dict with justification_type, narrative, reasoning
        """
        # Check if NUA belongs here
        belongs_here = self._nua_belongs_in_location(nua_name, current_location)
        
        # Determine justification type
        if belongs_here:
            justification_type = "native"
            narrative = self._generate_native_narrative(nua_name, nua_role, current_location)
        else:
            justification_type = "arrival"
            narrative = self._generate_arrival_narrative(nua_name, nua_role, current_location, scene_context)
        
        # Generate reasoning
        reasoning = self._generate_reasoning(nua_name, nua_role, justification_type, current_location)
        
        return {
            'justification_type': justification_type,
            'narrative': narrative,
            'reasoning': reasoning,
            'belongs_here': belongs_here
        }
    
    def _nua_belongs_in_location(self, nua_name: str, location: str) -> bool:
        """Check if NUA naturally belongs in this location."""
        if location in self.scene_occupants:
            return nua_name in self.scene_occupants[location]
        return False
    
    def _generate_native_narrative(
        self,
        nua_name: str,
        nua_role: str,
        location: str
    ) -> str:
        """Generate narrative for NUA who belongs in location."""
        role_narratives = {
            'guard': f"{nua_name} stands at their post, vigilant as always",
            'merchant': f"{nua_name} tends to their shop, arranging goods",
            'bartender': f"{nua_name} works behind the bar, cleaning glasses",
            'patron': f"{nua_name} sits at their usual spot",
            'worker': f"{nua_name} goes about their duties",
            'resident': f"{nua_name} is here, as they often are",
            'employee': f"{nua_name} continues their work"
        }
        
        return role_narratives.get(
            nua_role.lower(),
            f"{nua_name} is present, going about their business"
        )
    
    def _generate_arrival_narrative(
        self,
        nua_name: str,
        nua_role: str,
        location: str,
        scene_context: str
    ) -> str:
        """Generate narrative for NUA arriving at location."""
        # Determine arrival method based on role
        arrival_methods = {
            'guard': f"{nua_name} arrives on patrol, checking the area",
            'merchant': f"{nua_name} enters, looking for business opportunities",
            'traveler': f"{nua_name} arrives, travel-worn and weary",
            'investigator': f"{nua_name} appears, investigating the situation",
            'passerby': f"{nua_name} passes by, drawn by the commotion",
            'backup': f"{nua_name} arrives as backup, responding to the call",
            'customer': f"{nua_name} enters, seeking service",
            'visitor': f"{nua_name} arrives, visiting the location"
        }
        
        # Check scene context for specific triggers
        if 'violence' in scene_context.lower() or 'fight' in scene_context.lower():
            if nua_role.lower() in ['guard', 'police', 'security']:
                return f"{nua_name} rushes in, responding to the disturbance"
        
        if 'help' in scene_context.lower() or 'call' in scene_context.lower():
            return f"{nua_name} arrives, having heard the call for help"
        
        return arrival_methods.get(
            nua_role.lower(),
            f"{nua_name} enters the scene"
        )
    
    def _generate_reasoning(
        self,
        nua_name: str,
        nua_role: str,
        justification_type: str,
        location: str
    ) -> str:
        """Generate reasoning for NUA presence."""
        if justification_type == "native":
            return f"{nua_name} ({nua_role}) works/lives here at {location}"
        else:
            return f"{nua_name} ({nua_role}) has reason to arrive at {location}"
    
    def get_contextual_presence_reason(
        self,
        nua_name: str,
        nua_role: str,
        scene_events: List[str]
    ) -> str:
        """Get contextual reason for NUA's presence based on recent events."""
        
        # Check recent events for triggers
        events_text = ' '.join(scene_events).lower()
        
        if 'violence' in events_text or 'attack' in events_text:
            if nua_role.lower() in ['guard', 'police', 'security']:
                return f"{nua_name} responds to the violence"
        
        if 'fire' in events_text or 'smoke' in events_text:
            if nua_role.lower() in ['firefighter', 'emergency']:
                return f"{nua_name} responds to the emergency"
        
        if 'scream' in events_text or 'help' in events_text:
            if nua_role.lower() in ['guard', 'helper', 'bystander']:
                return f"{nua_name} investigates the disturbance"
        
        if 'purchase' in events_text or 'buy' in events_text:
            if nua_role.lower() in ['merchant', 'vendor', 'shopkeeper']:
                return f"{nua_name} sees a business opportunity"
        
        return f"{nua_name} happens to be nearby"
    
    def mark_nua_departed(self, nua_name: str, location: str):
        """Mark NUA as having left a location."""
        if location in self.scene_occupants:
            if nua_name in self.scene_occupants[location]:
                self.scene_occupants[location].remove(nua_name)
        
        # Update location to "departed"
        self.nua_locations[nua_name] = "departed"
    
    def mark_nua_arrived(self, nua_name: str, location: str):
        """Mark NUA as having arrived at a location."""
        self.nua_locations[nua_name] = location
        
        if location not in self.scene_occupants:
            self.scene_occupants[location] = []
        if nua_name not in self.scene_occupants[location]:
            self.scene_occupants[location].append(nua_name)
    
    def get_location_occupants(self, location: str) -> List[str]:
        """Get list of NUAs who belong in this location."""
        return self.scene_occupants.get(location, [])
    
    def validate_nua_presence(
        self,
        nua_name: str,
        location: str
    ) -> Dict[str, Any]:
        """Validate if NUA's presence makes sense."""
        current_location = self.nua_locations.get(nua_name)
        belongs_here = self._nua_belongs_in_location(nua_name, location)
        
        is_valid = (current_location == location) or belongs_here
        
        issues = []
        if not is_valid:
            if current_location and current_location != location:
                issues.append(f"{nua_name} was last seen at {current_location}, not {location}")
            if not belongs_here:
                issues.append(f"{nua_name} doesn't belong at {location}")
        
        return {
            'is_valid': is_valid,
            'current_location': current_location,
            'belongs_here': belongs_here,
            'issues': issues
        }
    
    def display_justification(self, justification: Dict[str, Any]):
        """Display NUA appearance justification."""
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}👤 NUA APPEARANCE JUSTIFICATION{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}Type: {justification['justification_type']}{Color.RESET}")
        print(f"{Color.NARRATIVE}Narrative: {justification['narrative']}{Color.RESET}")
        print(f"{Color.SYSTEM}Reasoning: {justification['reasoning']}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
dynamic_actor_justification = DynamicActorJustification()
