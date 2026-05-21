"""
Tactical Awareness System for UTAS Simulation

Ensures NPCs make smart tactical decisions in combat.
Prevents fake signals where NPCs don't take cover, flee when outmatched, or use terrain.
"""

from typing import Dict, List, Any, Optional, Tuple
from actor_sheet import StatusType
from color_utils import Color

try:
    from stranger_description_system import known_actors_tracker, get_nua_definite_description
except Exception:
    known_actors_tracker = None
    get_nua_definite_description = None


class TacticalAwarenessSystem:
    """
    Provides tactical decision-making for NPCs in combat situations.
    
    Features:
    - NPCs take cover when shot at
    - NPCs flee when outmatched
    - NPCs use terrain advantages
    - NPCs call for backup
    - NPCs coordinate with allies
    """
    
    def __init__(self):
        self.tactical_situations = {}
        self.cover_positions = []
        self.threat_assessments = {}
    
    def assess_tactical_situation(
        self,
        npc,
        enemies: List,
        allies: List,
        scene_description: str
    ) -> Dict[str, Any]:
        """
        Assess the tactical situation for an NPC.
        
        Returns:
            Dict with threat_level, recommended_action, reasoning
        """
        # Calculate threat level
        threat_level = self._calculate_threat_level(npc, enemies, allies)
        
        # Assess NPC's condition
        npc_condition = self._assess_condition(npc)
        
        # Identify available cover
        available_cover = self._identify_cover(scene_description)
        
        # Determine if outmatched
        is_outmatched = self._is_outmatched(npc, enemies, allies)
        
        # Get recommended action
        recommended_action = self._get_tactical_recommendation(
            npc, threat_level, npc_condition, is_outmatched, available_cover, allies
        )
        
        return {
            'threat_level': threat_level,
            'npc_condition': npc_condition,
            'is_outmatched': is_outmatched,
            'available_cover': available_cover,
            'recommended_action': recommended_action['action'],
            'reasoning': recommended_action['reasoning'],
            'urgency': recommended_action['urgency']
        }
    
    def _calculate_threat_level(self, npc, enemies: List, allies: List) -> int:
        """Calculate threat level (1-5) based on enemy strength."""
        if not enemies:
            return 0
        
        # Count enemies
        enemy_count = len(enemies)
        ally_count = len(allies)
        
        # Assess enemy strength
        enemy_strength = 0
        for enemy in enemies:
            try:
                stamina = enemy.sheet.statuses[StatusType.STAMINA]
                enemy_strength += stamina.value
            except:
                enemy_strength += 3  # Assume average
        
        # Assess ally strength
        ally_strength = 0
        for ally in allies:
            try:
                stamina = ally.sheet.statuses[StatusType.STAMINA]
                ally_strength += stamina.value
            except:
                ally_strength += 3
        
        # Calculate relative threat
        if ally_count == 0:
            ally_strength = 0
        
        npc_stamina = npc.sheet.statuses[StatusType.STAMINA].value
        total_friendly = npc_stamina + ally_strength
        
        if total_friendly == 0:
            return 5  # Maximum threat
        
        threat_ratio = enemy_strength / total_friendly
        
        if threat_ratio >= 2.0:
            return 5  # Extreme threat
        elif threat_ratio >= 1.5:
            return 4  # High threat
        elif threat_ratio >= 1.0:
            return 3  # Moderate threat
        elif threat_ratio >= 0.5:
            return 2  # Low threat
        else:
            return 1  # Minimal threat
    
    def _assess_condition(self, npc) -> str:
        """Assess NPC's current condition."""
        try:
            stamina = npc.sheet.statuses[StatusType.STAMINA]
            spirit = npc.sheet.statuses[StatusType.SPIRIT]
            
            avg_status = (stamina.value + spirit.value) / 2
            
            if avg_status >= 4:
                return "excellent"
            elif avg_status >= 3:
                return "good"
            elif avg_status >= 2:
                return "fair"
            elif avg_status >= 1:
                return "poor"
            else:
                return "critical"
        except:
            return "unknown"
    
    def _identify_cover(self, scene_description: str) -> List[str]:
        """Identify available cover from scene description."""
        scene_lower = scene_description.lower()
        cover_options = []
        
        cover_keywords = {
            'wall': ['wall', 'brick wall', 'stone wall'],
            'car': ['car', 'vehicle', 'truck', 'van'],
            'crate': ['crate', 'box', 'container', 'barrel'],
            'furniture': ['table', 'desk', 'counter', 'bar'],
            'pillar': ['pillar', 'column', 'post'],
            'doorway': ['doorway', 'door frame', 'entrance'],
            'corner': ['corner', 'alcove', 'nook']
        }
        
        for cover_type, keywords in cover_keywords.items():
            if any(keyword in scene_lower for keyword in keywords):
                cover_options.append(cover_type)
        
        return cover_options if cover_options else ['improvised cover']
    
    def _is_outmatched(self, npc, enemies: List, allies: List) -> bool:
        """Determine if NPC is outmatched."""
        threat_level = self._calculate_threat_level(npc, enemies, allies)
        condition = self._assess_condition(npc)
        
        # Outmatched if high threat and poor condition
        if threat_level >= 4 and condition in ["poor", "critical"]:
            return True
        
        # Outmatched if extreme threat regardless of condition
        if threat_level >= 5:
            return True
        
        # Outmatched if outnumbered 3:1 or more
        if len(enemies) >= (len(allies) + 1) * 3:
            return True
        
        return False
    
    def _get_tactical_recommendation(
        self,
        npc,
        threat_level: int,
        condition: str,
        is_outmatched: bool,
        available_cover: List[str],
        allies: List
    ) -> Dict[str, Any]:
        """Get tactical recommendation based on situation."""

        def _display_name(_actor) -> str:
            try:
                name = getattr(getattr(_actor, 'sheet', None), 'name', None)
                if not name:
                    return str(_actor)
                if known_actors_tracker is None or get_nua_definite_description is None:
                    return str(name)
                try:
                    if known_actors_tracker.is_name_known(str(name)):
                        return str(name)
                except Exception:
                    return str(name)
                try:
                    replacement = get_nua_definite_description(_actor, ua_actor=None)
                    if replacement:
                        return str(replacement)
                except Exception:
                    pass
                return str(name)
            except Exception:
                return "someone"

        npc_disp = _display_name(npc)
        
        # Critical condition - flee or surrender
        if condition == "critical":
            if is_outmatched:
                return {
                    'action': 'surrender',
                    'reasoning': f"{npc_disp} is critically wounded and outmatched - surrender to survive",
                    'urgency': 'critical'
                }
            else:
                return {
                    'action': 'retreat_to_cover',
                    'reasoning': f"{npc_disp} is critically wounded - must take cover immediately",
                    'urgency': 'critical'
                }
        
        # Outmatched - flee
        if is_outmatched:
            return {
                'action': 'flee',
                'reasoning': f"{npc_disp} is outmatched (threat level {threat_level}) - tactical retreat necessary",
                'urgency': 'high'
            }
        
        # High threat - take cover
        if threat_level >= 4:
            if available_cover:
                return {
                    'action': 'take_cover',
                    'reasoning': f"{npc_disp} faces high threat - use {available_cover[0]} for cover",
                    'urgency': 'high',
                    'cover_type': available_cover[0]
                }
            else:
                return {
                    'action': 'create_distance',
                    'reasoning': f"{npc_disp} faces high threat with no cover - create distance",
                    'urgency': 'high'
                }
        
        # Moderate threat - tactical positioning
        if threat_level >= 3:
            if available_cover:
                return {
                    'action': 'use_cover',
                    'reasoning': f"{npc_disp} should use {available_cover[0]} for tactical advantage",
                    'urgency': 'moderate',
                    'cover_type': available_cover[0]
                }
            else:
                return {
                    'action': 'defensive_stance',
                    'reasoning': f"{npc_disp} should take defensive position",
                    'urgency': 'moderate'
                }
        
        # Low threat - call for backup if available
        if threat_level >= 2 and not allies:
            return {
                'action': 'call_backup',
                'reasoning': f"{npc_disp} should call for backup before engaging",
                'urgency': 'low'
            }
        
        # Minimal threat - engage normally
        return {
            'action': 'engage',
            'reasoning': f"{npc_disp} can engage normally (threat level {threat_level})",
            'urgency': 'low'
        }
    
    def should_take_cover(self, npc, being_shot_at: bool = False) -> bool:
        """Determine if NPC should take cover."""
        if being_shot_at:
            return True
        
        condition = self._assess_condition(npc)
        if condition in ["poor", "critical"]:
            return True
        
        return False
    
    def should_flee(self, npc, enemies: List, allies: List) -> bool:
        """Determine if NPC should flee."""
        is_outmatched = self._is_outmatched(npc, enemies, allies)
        condition = self._assess_condition(npc)
        
        if is_outmatched and condition in ["poor", "critical"]:
            return True
        
        if is_outmatched:
            # Check personality - brave NPCs less likely to flee
            personality = getattr(npc.sheet, 'personality_traits', {})
            if 'brave' in str(personality).lower() or 'courageous' in str(personality).lower():
                return False
            return True
        
        return False
    
    def get_cover_action_description(self, npc_name: str, cover_type: str) -> str:
        """Get narrative description of taking cover."""
        descriptions = {
            'wall': f"{npc_name} dives behind the wall, using it for cover",
            'car': f"{npc_name} crouches behind the car, shielding themselves",
            'crate': f"{npc_name} takes cover behind the crate",
            'furniture': f"{npc_name} ducks behind the furniture for protection",
            'pillar': f"{npc_name} moves behind the pillar for cover",
            'doorway': f"{npc_name} retreats to the doorway, using it for cover",
            'corner': f"{npc_name} backs into the corner, minimizing exposure",
            'improvised cover': f"{npc_name} finds improvised cover"
        }
        return descriptions.get(cover_type, f"{npc_name} takes cover")
    
    def display_tactical_assessment(
        self,
        npc,
        enemies: List,
        allies: List,
        scene_description: str
    ):
        """Display tactical assessment for debugging."""
        assessment = self.assess_tactical_situation(npc, enemies, allies, scene_description)
        
        print(f"\n{Color.WARNING}{'='*80}{Color.RESET}")
        print(f"{Color.WARNING}⚔️  TACTICAL ASSESSMENT{Color.RESET}")
        print(f"{Color.WARNING}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}NPC: {npc.sheet.name}{Color.RESET}")
        print(f"{Color.SYSTEM}Condition: {assessment['npc_condition']}{Color.RESET}")
        print(f"{Color.SYSTEM}Threat Level: {assessment['threat_level']}/5{Color.RESET}")
        print(f"{Color.SYSTEM}Outmatched: {'Yes' if assessment['is_outmatched'] else 'No'}{Color.RESET}")
        
        if assessment['available_cover']:
            print(f"{Color.SUCCESS}Available Cover: {', '.join(assessment['available_cover'])}{Color.RESET}")
        else:
            print(f"{Color.WARNING}No cover available{Color.RESET}")
        
        print(f"\n{Color.INFO}Recommended Action: {assessment['recommended_action']}{Color.RESET}")
        print(f"{Color.INFO}Urgency: {assessment['urgency']}{Color.RESET}")
        print(f"{Color.NARRATIVE}Reasoning: {assessment['reasoning']}{Color.RESET}")
        print(f"{Color.WARNING}{'='*80}{Color.RESET}\n")


# Global instance
tactical_awareness_system = TacticalAwarenessSystem()
