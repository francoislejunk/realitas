"""
Sympathy Behavior Modifier for UTAS Simulation

Ensures sympathy values actually affect NPC behavior and decisions.
Prevents fake signals where enemies act friendly or friends act hostile.
"""

from typing import Dict, List, Any, Optional
from color_utils import Color


class SympathyBehaviorModifier:
    """
    Modifies NPC behavior based on sympathy relationships.
    
    Features:
    - Enemies refuse to help
    - Friends offer assistance
    - Sympathy affects dialogue tone
    - Sympathy affects action selection
    - Sympathy affects trust and cooperation
    """
    
    def __init__(self):
        self.behavior_overrides = {}
    
    def get_behavior_guidance(
        self,
        npc_name: str,
        target_name: str,
        sympathy_value: int,
        action_context: str
    ) -> Dict[str, Any]:
        """
        Get behavior guidance based on sympathy level.
        
        Args:
            npc_name: Name of the NPC making decision
            target_name: Name of the target actor
            sympathy_value: Current sympathy value (-5 to +5)
            action_context: Context of the action being considered
            
        Returns:
            Dict with behavior guidance
        """
        # Classify relationship
        relationship = self._classify_relationship(sympathy_value)
        
        # Get behavioral constraints
        constraints = self._get_behavioral_constraints(relationship, action_context)
        
        # Get dialogue tone
        dialogue_tone = self._get_dialogue_tone(relationship)
        
        # Get cooperation level
        cooperation = self._get_cooperation_level(relationship)
        
        # Get trust level
        trust = self._get_trust_level(relationship)
        
        return {
            'relationship': relationship,
            'sympathy_value': sympathy_value,
            'constraints': constraints,
            'dialogue_tone': dialogue_tone,
            'cooperation_level': cooperation,
            'trust_level': trust,
            'guidance_text': self._generate_guidance_text(
                npc_name, target_name, relationship, sympathy_value
            )
        }
    
    def _classify_relationship(self, sympathy_value: int) -> str:
        """Classify relationship based on sympathy value."""
        if sympathy_value <= -4:
            return "bitter_enemy"
        elif sympathy_value <= -2:
            return "enemy"
        elif sympathy_value <= -1:
            return "hostile"
        elif sympathy_value == 0:
            return "stranger"
        elif sympathy_value == 1:
            return "neutral"
        elif sympathy_value <= 2:
            return "acquaintance"
        elif sympathy_value <= 3:
            return "friendly"
        elif sympathy_value <= 4:
            return "friend"
        else:  # 5+
            return "close_friend"
    
    def _get_behavioral_constraints(
        self,
        relationship: str,
        action_context: str
    ) -> List[str]:
        """Get behavioral constraints based on relationship."""
        constraints = []
        
        if relationship in ["bitter_enemy", "enemy"]:
            constraints.append("REFUSE all requests for help")
            constraints.append("HOSTILE dialogue and actions")
            constraints.append("ATTACK if provoked or opportunity arises")
            constraints.append("NO cooperation or trust")
            constraints.append("ASSUME worst intentions")
        
        elif relationship == "hostile":
            constraints.append("RELUCTANT to help, likely refuse")
            constraints.append("SUSPICIOUS of all requests")
            constraints.append("CURT and unfriendly dialogue")
            constraints.append("MINIMAL cooperation")
        
        elif relationship == "stranger":
            constraints.append("CAUTIOUS and wary")
            constraints.append("NEUTRAL dialogue")
            constraints.append("CONDITIONAL cooperation (what's in it for me?)")
            constraints.append("VERIFY claims before trusting")
        
        elif relationship == "neutral":
            constraints.append("POLITE but not warm")
            constraints.append("WILLING to help with simple requests")
            constraints.append("BASIC cooperation")
            constraints.append("SOME trust, but verify important things")
        
        elif relationship in ["acquaintance", "friendly"]:
            constraints.append("WILLING to help with reasonable requests")
            constraints.append("FRIENDLY dialogue")
            constraints.append("GOOD cooperation")
            constraints.append("TRUST unless given reason not to")
        
        elif relationship in ["friend", "close_friend"]:
            constraints.append("EAGER to help")
            constraints.append("WARM and supportive dialogue")
            constraints.append("FULL cooperation")
            constraints.append("HIGH trust")
            constraints.append("DEFEND if attacked")
            constraints.append("WARN of dangers")
        
        return constraints
    
    def _get_dialogue_tone(self, relationship: str) -> str:
        """Get appropriate dialogue tone for relationship."""
        tone_map = {
            "bitter_enemy": "hostile, threatening, aggressive",
            "enemy": "hostile, cold, unfriendly",
            "hostile": "curt, suspicious, unfriendly",
            "stranger": "cautious, neutral, formal",
            "neutral": "polite, professional, cordial",
            "acquaintance": "friendly, casual, pleasant",
            "friendly": "warm, helpful, encouraging",
            "friend": "warm, supportive, caring",
            "close_friend": "affectionate, loyal, protective"
        }
        return tone_map.get(relationship, "neutral")
    
    def _get_cooperation_level(self, relationship: str) -> str:
        """Get cooperation level for relationship."""
        cooperation_map = {
            "bitter_enemy": "none",
            "enemy": "none",
            "hostile": "minimal",
            "stranger": "conditional",
            "neutral": "basic",
            "acquaintance": "willing",
            "friendly": "good",
            "friend": "full",
            "close_friend": "unconditional"
        }
        return cooperation_map.get(relationship, "basic")
    
    def _get_trust_level(self, relationship: str) -> str:
        """Get trust level for relationship."""
        trust_map = {
            "bitter_enemy": "none",
            "enemy": "none",
            "hostile": "very_low",
            "stranger": "low",
            "neutral": "moderate",
            "acquaintance": "moderate",
            "friendly": "high",
            "friend": "high",
            "close_friend": "complete"
        }
        return trust_map.get(relationship, "moderate")
    
    def _generate_guidance_text(
        self,
        npc_name: str,
        target_name: str,
        relationship: str,
        sympathy_value: int
    ) -> str:
        """Generate guidance text for LLM prompts."""
        guidance_templates = {
            "bitter_enemy": f"{npc_name} HATES {target_name} (sympathy {sympathy_value}). {npc_name} will REFUSE all help, be HOSTILE in dialogue, and ATTACK if given opportunity. {npc_name} assumes the WORST about {target_name}'s intentions.",
            
            "enemy": f"{npc_name} considers {target_name} an ENEMY (sympathy {sympathy_value}). {npc_name} will NOT help, be COLD and UNFRIENDLY, and may attack if provoked. NO cooperation or trust.",
            
            "hostile": f"{npc_name} is HOSTILE toward {target_name} (sympathy {sympathy_value}). {npc_name} will likely REFUSE requests, be CURT in dialogue, and be SUSPICIOUS of all claims. Minimal cooperation.",
            
            "stranger": f"{npc_name} doesn't know {target_name} (sympathy {sympathy_value}). {npc_name} is CAUTIOUS and WARY. Will consider requests but needs good reason. Neutral dialogue, conditional cooperation.",
            
            "neutral": f"{npc_name} has a NEUTRAL relationship with {target_name} (sympathy {sympathy_value}). {npc_name} is POLITE but not warm. Will help with simple requests. Basic cooperation and some trust.",
            
            "acquaintance": f"{npc_name} knows {target_name} casually (sympathy {sympathy_value}). {npc_name} is FRIENDLY and willing to help with reasonable requests. Good cooperation and trust unless given reason not to.",
            
            "friendly": f"{npc_name} is FRIENDLY with {target_name} (sympathy {sympathy_value}). {npc_name} is WARM and HELPFUL. Willing to assist and cooperate. Good trust.",
            
            "friend": f"{npc_name} considers {target_name} a FRIEND (sympathy {sympathy_value}). {npc_name} is SUPPORTIVE and CARING. Eager to help, full cooperation, high trust. Will defend if attacked.",
            
            "close_friend": f"{npc_name} and {target_name} are CLOSE FRIENDS (sympathy {sympathy_value}). {npc_name} is LOYAL and PROTECTIVE. Will do almost anything to help. Unconditional cooperation and complete trust."
        }
        
        return guidance_templates.get(relationship, f"{npc_name} has neutral feelings toward {target_name}.")
    
    def should_refuse_help(
        self,
        sympathy_value: int,
        request_difficulty: str = "moderate"
    ) -> bool:
        """Determine if NPC should refuse to help based on sympathy."""
        relationship = self._classify_relationship(sympathy_value)
        
        # Enemies always refuse
        if relationship in ["bitter_enemy", "enemy"]:
            return True
        
        # Hostile usually refuses
        if relationship == "hostile":
            return request_difficulty in ["moderate", "difficult", "dangerous"]
        
        # Strangers refuse difficult requests
        if relationship == "stranger":
            return request_difficulty in ["difficult", "dangerous"]
        
        # Everyone else helps based on difficulty
        if relationship == "neutral":
            return request_difficulty == "dangerous"
        
        # Friends rarely refuse
        return False
    
    def get_action_preference(
        self,
        sympathy_value: int,
        available_actions: List[str]
    ) -> Dict[str, str]:
        """Get action preferences based on sympathy."""
        relationship = self._classify_relationship(sympathy_value)
        
        preferences = {
            "bitter_enemy": "aggressive",
            "enemy": "aggressive",
            "hostile": "defensive",
            "stranger": "cautious",
            "neutral": "neutral",
            "acquaintance": "cooperative",
            "friendly": "helpful",
            "friend": "supportive",
            "close_friend": "protective"
        }
        
        return {
            'preference': preferences.get(relationship, "neutral"),
            'avoid_actions': self._get_actions_to_avoid(relationship),
            'prefer_actions': self._get_preferred_actions(relationship)
        }
    
    def _get_actions_to_avoid(self, relationship: str) -> List[str]:
        """Get actions to avoid based on relationship."""
        if relationship in ["friend", "close_friend"]:
            return ["attack", "threaten", "steal_from", "betray"]
        elif relationship in ["bitter_enemy", "enemy"]:
            return ["help", "cooperate", "trust", "share_information"]
        return []
    
    def _get_preferred_actions(self, relationship: str) -> List[str]:
        """Get preferred actions based on relationship."""
        if relationship in ["friend", "close_friend"]:
            return ["help", "defend", "warn", "share_information", "cooperate"]
        elif relationship in ["bitter_enemy", "enemy"]:
            return ["attack", "threaten", "refuse", "sabotage"]
        elif relationship == "hostile":
            return ["refuse", "be_suspicious", "keep_distance"]
        return ["be_cautious", "assess_situation"]
    
    def display_sympathy_guidance(
        self,
        npc_name: str,
        target_name: str,
        sympathy_value: int
    ):
        """Display sympathy-based behavior guidance."""
        guidance = self.get_behavior_guidance(npc_name, target_name, sympathy_value, "general")
        
        print(f"\n{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.INFO}🤝 SYMPATHY BEHAVIOR GUIDANCE{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}")
        print(f"{Color.SYSTEM}NPC: {npc_name}{Color.RESET}")
        print(f"{Color.SYSTEM}Target: {target_name}{Color.RESET}")
        print(f"{Color.SYSTEM}Sympathy: {sympathy_value} ({guidance['relationship']}){Color.RESET}")
        print(f"{Color.SYSTEM}Dialogue Tone: {guidance['dialogue_tone']}{Color.RESET}")
        print(f"{Color.SYSTEM}Cooperation: {guidance['cooperation_level']}{Color.RESET}")
        print(f"{Color.SYSTEM}Trust: {guidance['trust_level']}{Color.RESET}")
        
        print(f"\n{Color.NARRATIVE}Behavioral Constraints:{Color.RESET}")
        for constraint in guidance['constraints']:
            print(f"{Color.NARRATIVE}  • {constraint}{Color.RESET}")
        
        print(f"\n{Color.INFO}Guidance: {guidance['guidance_text']}{Color.RESET}")
        print(f"{Color.INFO}{'='*80}{Color.RESET}\n")


# Global instance
sympathy_behavior_modifier = SympathyBehaviorModifier()
