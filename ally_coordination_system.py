"""
Ally Coordination System for UTAS Simulation

Ensures NPCs help wounded allies and coordinate tactically.
Prevents fake signals where allies ignore each other's distress.
"""

from typing import List, Dict, Any, Optional
from actor_sheet import StatusType
from color_utils import Color


class AllyCoordinationSystem:
    """
    Handles realistic ally behavior and coordination.
    
    Features:
    - Allies help wounded friends
    - Allies coordinate attacks
    - Allies warn each other of danger
    - Allies flee together when outmatched
    """
    
    def __init__(self):
        self.ally_groups = {}  # Track which NPCs are allies
        self.coordination_history = []
    
    def auto_detect_ally_groups(self, actors: List) -> None:
        """
        Automatically detect and register ally groups based on shared occupation/faction.
        
        NPCs with the same occupation (e.g., "Guard", "Police Officer") are considered allies.
        """
        # Group actors by occupation
        occupation_groups = {}
        for actor in actors:
            if not hasattr(actor, 'sheet'):
                continue
            
            # Get occupation - normalize to lowercase for grouping
            occupation = getattr(actor.sheet, 'occupation', None)
            if not occupation:
                continue
            
            occupation_key = occupation.lower().strip()
            
            # Group similar occupations
            if 'guard' in occupation_key or 'security' in occupation_key:
                occupation_key = 'security'
            elif 'police' in occupation_key or 'cop' in occupation_key or 'officer' in occupation_key:
                occupation_key = 'police'
            elif 'soldier' in occupation_key or 'military' in occupation_key:
                occupation_key = 'military'
            elif 'gang' in occupation_key or 'thug' in occupation_key:
                occupation_key = 'gang'
            
            if occupation_key not in occupation_groups:
                occupation_groups[occupation_key] = []
            occupation_groups[occupation_key].append(actor)
        
        # Register groups with 2+ members
        for occupation, members in occupation_groups.items():
            if len(members) >= 2:
                self.register_ally_group(f"{occupation}_group", members)
                print(f"[ALLY COORD] Auto-registered {occupation} group with {len(members)} members")
    
    def register_ally_group(self, group_name: str, members: List):
        """Register a group of allies who should coordinate."""
        self.ally_groups[group_name] = {
            'members': members,
            'leader': members[0] if members else None,
            'morale': 5,  # Group morale (1-5)
            'coordination_bonus': 0
        }
    
    def check_ally_assistance_needed(
        self,
        actor,
        all_actors: List,
        current_situation: str
    ) -> Optional[Dict[str, Any]]:
        """
        Check if any allies need assistance and determine response.
        
        Args:
            actor: The NPC checking for allies
            all_actors: All actors in the scene
            current_situation: Description of current situation
            
        Returns:
            Assistance action dict if ally needs help, None otherwise
        """
        # Find actor's ally group
        ally_group = self._find_ally_group(actor)
        if not ally_group:
            return None
        
        # Check each ally's status
        for ally in ally_group['members']:
            if ally == actor:
                continue
            
            # Check if ally is wounded
            if self._is_wounded(ally):
                assistance = self._determine_assistance(actor, ally, all_actors)
                if assistance:
                    return assistance
            
            # Check if ally is in danger
            if self._is_in_danger(ally, all_actors):
                assistance = self._determine_protection(actor, ally, all_actors)
                if assistance:
                    return assistance
        
        return None
    
    def _find_ally_group(self, actor) -> Optional[Dict]:
        """Find which ally group an actor belongs to."""
        for group_name, group_data in self.ally_groups.items():
            if actor in group_data['members']:
                return group_data
        return None
    
    def _is_wounded(self, actor) -> bool:
        """Check if an actor is wounded."""
        try:
            stamina = actor.sheet.statuses[StatusType.STAMINA]
            spirit = actor.sheet.statuses[StatusType.SPIRIT]
            
            # Consider wounded if either status is critically low
            return stamina.value <= 1 or spirit.value <= 1
        except Exception:
            return False
    
    def _is_in_danger(self, actor, all_actors: List) -> bool:
        """Check if an actor is in immediate danger."""
        try:
            # Check if being attacked by checking sympathy with others
            for other in all_actors:
                if other == actor:
                    continue
                
                try:
                    sympathy = actor.sheet.get_sympathy(other.sheet.name)
                    # If someone has very negative sympathy, they're likely hostile
                    if sympathy <= -3:
                        return True
                except Exception:
                    continue
            
            return False
        except Exception:
            return False
    
    def _determine_assistance(
        self,
        actor,
        wounded_ally,
        all_actors: List
    ) -> Optional[Dict[str, Any]]:
        """Determine how to assist a wounded ally."""
        
        # Check actor's own status
        actor_stamina = actor.sheet.statuses[StatusType.STAMINA]
        actor_spirit = actor.sheet.statuses[StatusType.SPIRIT]
        
        # If actor is also critically wounded, can't help
        if actor_stamina.value <= 1 or actor_spirit.value <= 1:
            return None
        
        # Check if there are active threats
        threats = self._identify_threats(actor, all_actors)
        
        if threats:
            # If threats present, defend the wounded ally
            return {
                'action_type': 'defend_ally',
                'target': wounded_ally.sheet.name,
                'threat': threats[0].sheet.name,
                'narrative': f"{actor.sheet.name} moves to protect wounded {wounded_ally.sheet.name} from {threats[0].sheet.name}...",
                'priority': 'high'
            }
        else:
            # If no immediate threats, help the ally recover
            return {
                'action_type': 'help_ally',
                'target': wounded_ally.sheet.name,
                'narrative': f"{actor.sheet.name} rushes to help wounded {wounded_ally.sheet.name}, checking their injuries...",
                'priority': 'medium'
            }
    
    def _determine_protection(
        self,
        actor,
        endangered_ally,
        all_actors: List
    ) -> Optional[Dict[str, Any]]:
        """Determine how to protect an ally in danger."""
        
        threats = self._identify_threats(endangered_ally, all_actors)
        if not threats:
            return None
        
        primary_threat = threats[0]
        
        # Check if actor can intervene
        actor_stamina = actor.sheet.statuses[StatusType.STAMINA]
        
        if actor_stamina.value >= 3:
            # Strong enough to intervene
            return {
                'action_type': 'intervene',
                'target': endangered_ally.sheet.name,
                'threat': primary_threat.sheet.name,
                'narrative': f"{actor.sheet.name} intervenes to protect {endangered_ally.sheet.name} from {primary_threat.sheet.name}...",
                'priority': 'high'
            }
        else:
            # Too weak to intervene, call for help
            return {
                'action_type': 'call_for_help',
                'target': endangered_ally.sheet.name,
                'threat': primary_threat.sheet.name,
                'narrative': f"{actor.sheet.name} shouts for help as {primary_threat.sheet.name} threatens {endangered_ally.sheet.name}...",
                'priority': 'medium'
            }
    
    def _identify_threats(self, actor, all_actors: List) -> List:
        """Identify actors who are threats to the given actor."""
        threats = []
        
        for other in all_actors:
            if other == actor:
                continue
            
            try:
                # Check mutual sympathy
                sympathy_to_other = actor.sheet.get_sympathy(other.sheet.name)
                sympathy_from_other = other.sheet.get_sympathy(actor.sheet.name)
                
                # If either has very negative sympathy, they're a threat
                if sympathy_to_other <= -2 or sympathy_from_other <= -2:
                    threats.append(other)
            except Exception:
                continue
        
        return threats
    
    def calculate_group_morale(self, group_name: str) -> int:
        """Calculate current morale for an ally group."""
        if group_name not in self.ally_groups:
            return 3  # Default neutral morale
        
        group = self.ally_groups[group_name]
        members = group['members']
        
        if not members:
            return 1  # No members = broken morale
        
        # Count wounded and dead members
        wounded_count = sum(1 for member in members if self._is_wounded(member))
        
        # Calculate morale based on casualties
        casualty_ratio = wounded_count / len(members)
        
        if casualty_ratio >= 0.75:
            return 1  # Broken - 75%+ casualties
        elif casualty_ratio >= 0.5:
            return 2  # Shaken - 50%+ casualties
        elif casualty_ratio >= 0.25:
            return 3  # Concerned - 25%+ casualties
        elif casualty_ratio > 0:
            return 4  # Steady - some casualties
        else:
            return 5  # Strong - no casualties
    
    def should_group_flee(self, group_name: str, threat_level: int) -> bool:
        """Determine if an ally group should flee."""
        morale = self.calculate_group_morale(group_name)
        
        # Low morale + high threat = flee
        if morale <= 2 and threat_level >= 4:
            return True
        
        # Very low morale = always flee
        if morale <= 1:
            return True
        
        return False
    
    def coordinate_group_action(
        self,
        group_name: str,
        situation: str,
        available_actions: List[str]
    ) -> Dict[str, str]:
        """
        Coordinate actions for an entire ally group.
        
        Returns:
            Dict mapping actor names to coordinated actions
        """
        if group_name not in self.ally_groups:
            return {}
        
        group = self.ally_groups[group_name]
        members = group['members']
        leader = group['leader']
        
        coordinated_actions = {}
        
        # Leader makes decisions for group
        if leader and leader in members:
            # Assess situation
            morale = self.calculate_group_morale(group_name)
            
            if morale <= 2:
                # Low morale: defensive/retreat actions
                for member in members:
                    if not self._is_wounded(member):
                        coordinated_actions[member.sheet.name] = "defensive_stance"
            else:
                # Good morale: coordinated offense
                for i, member in enumerate(members):
                    if not self._is_wounded(member):
                        if i == 0:
                            coordinated_actions[member.sheet.name] = "lead_attack"
                        else:
                            coordinated_actions[member.sheet.name] = "support_attack"
        
        return coordinated_actions
    
    def display_coordination_action(self, action: Dict[str, Any]):
        """Display ally coordination action."""
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}🤝 ALLY COORDINATION{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.NARRATIVE}{action['narrative']}{Color.RESET}")
        print(f"{Color.INFO}Priority: {action['priority'].upper()}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
ally_coordinator = AllyCoordinationSystem()
