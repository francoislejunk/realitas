"""
Encounter Checker System for UTAS Simulation

This module determines when the simulation should switch between solo exploration
and encounter modes based on UA interactions with NPCs.
"""

from typing import List, Optional, Any
from dataclasses import dataclass
from enum import Enum

class SimulationMode(Enum):
    ROAM = "roam"
    ENCOUNTER = "encounter"

@dataclass
class EncounterContext:
    mode: SimulationMode
    participants: List[Any]
    encounter_type: str = "general"
    trigger_action: str = ""

class EncounterChecker:
    """
    Manages transitions between ROAM and ENCOUNTER modes based on UA actions.
    Uses LLM analysis to detect when users want to interact with NPCs.
    """
    
    def __init__(self):
        self.current_mode = SimulationMode.ROAM
        self.current_context = EncounterContext(
            mode=SimulationMode.ROAM,
            participants=[]
        )
        
        # Keywords that suggest interaction intent
        self.interaction_keywords = [
            "talk", "speak", "ask", "tell", "say", "greet", "approach", "call",
            "attack", "fight", "strike", "hit", "shoot", "stab", "punch", "kick",
            "negotiate", "persuade", "convince", "threaten", "intimidate",
            "follow", "chase", "pursue", "confront", "challenge", "question",
            "trade", "buy", "sell", "give", "offer", "exchange", "deal",
            "help", "assist", "aid", "support", "heal", "rescue", "save",
            "sneak", "hide", "avoid", "evade", "spy", "watch", "observe",
            "him", "her", "them", "they", "the person", "the man", "the woman",
            "the guard", "the merchant", "the stranger", "the figure"
        ]
    
    def check_for_encounter(self, user_input: str, available_actors: List[Any], 
                          scene_description: str, user_actor_name: str = None) -> EncounterContext:
        """
        Check if user input indicates an encounter should begin.
        Only triggers when UA explicitly chooses to interact with an NPC.
        
        Args:
            user_input: The user's action description
            available_actors: List of available NPCs in the scene (including SPARK NPCs)
            scene_description: Current scene context
            user_actor_name: Name of the user actor (to prevent self-interaction)
            
        Returns:
            EncounterContext with updated mode and participants
        """
        user_input_lower = user_input.lower().strip()
        
        # Check if we're already in an encounter
        if self.current_mode == SimulationMode.ENCOUNTER:
            return self.current_context
        
        # Check for temporal qualifiers that indicate future planning, not immediate action
        temporal_qualifiers = ["later", "tomorrow", "next week", "next month", "eventually", 
                              "in the future", "someday", "soon", "after", "when i", "if i"]
        is_future_planning = any(qualifier in user_input_lower for qualifier in temporal_qualifiers)
        
        if is_future_planning:
            return self.current_context
        
        # Look for interaction keywords that indicate deliberate NPC interaction
        interaction_detected = any(keyword in user_input_lower for keyword in self.interaction_keywords)
        
        if not interaction_detected:
            # No interaction detected, stay in ROAM mode
            return self.current_context
        
        # Find which NPC the user is trying to interact with
        target_npc = self._identify_target_npc(user_input_lower, available_actors, scene_description)
        
        if target_npc:
            if hasattr(target_npc, 'sheet') and hasattr(target_npc.sheet, 'name') and user_actor_name:
                if target_npc.sheet.name.lower() == user_actor_name.lower():
                    return self.current_context
            # Encounter detected - UA has chosen to interact with an NPC!
            encounter_type = self._classify_encounter_type(user_input_lower)
            
            new_context = EncounterContext(
                mode=SimulationMode.ENCOUNTER,
                participants=[target_npc],  # UA will be added by the caller
                encounter_type=encounter_type,
                trigger_action=user_input
            )
            
            self.current_mode = SimulationMode.ENCOUNTER
            self.current_context = new_context
            
            return new_context
        
        # No valid target found, stay in ROAM mode
        return self.current_context
    
    def _identify_target_npc(self, user_input_lower: str, available_actors: List[Any], 
                           scene_description: str) -> Optional[Any]:
        """Identify which NPC the user is trying to interact with"""
        # First check existing actors
        if available_actors:
            # Look for direct name references
            for actor in available_actors:
                if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'name'):
                    actor_name_lower = actor.sheet.name.lower()
                    if actor_name_lower in user_input_lower:
                        return actor
                    
                    # Check for partial name matches
                    name_words = actor_name_lower.split()
                    for word in name_words:
                        if len(word) > 3 and word in user_input_lower:
                            return actor
            
            # Look for occupation/role references
            for actor in available_actors:
                if hasattr(actor, 'sheet') and hasattr(actor.sheet, 'occupation'):
                    occupation_lower = actor.sheet.occupation.lower()
                    if occupation_lower in user_input_lower:
                        return actor
            
            # If only one NPC available and interaction detected, assume it's the target
            if len(available_actors) == 1:
                return available_actors[0]
        
        # If no existing actors, use LLM to detect NPC references from scene description
        return self._detect_scene_npc_reference(user_input_lower, scene_description)
    
    def _detect_scene_npc_reference(self, user_input_lower: str, scene_description: str) -> Optional[Any]:
        """Use LLM to detect if user is referencing an NPC from the scene description"""
        from openrouter_config import create_role_client, OpenRouterConfig
        
        prompt = f"""
Analyze if the user's action is trying to interact with a character mentioned in the scene description.

**SCENE DESCRIPTION:**
{scene_description}

**USER ACTION:**
{user_input_lower}

**TASK:**
Determine if the user is trying to interact with a character/person mentioned in the scene description.

Look for:
- Direct references to people/characters in the scene (e.g., "clerk", "guard", "woman", "man")
- Pronouns referring to characters (e.g., "him", "her", "them")
- Job titles or roles mentioned in the scene

Respond with JSON:
{{
    "npc_detected": true/false,
    "npc_identifier": "the specific character reference from scene (e.g., 'clerk', 'guard', 'woman with tired eyes')",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation"
}}

If no character interaction is detected, set npc_detected to false.
"""
        
        try:
            client = create_role_client("interpretation")
            response = client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("interpretation"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            
            if result.get("npc_detected") and result.get("confidence", 0) > 0.6:
                return {
                    "create_npc": result.get("npc_identifier", "unknown character"),
                    "scene_reference": True,
                    "confidence": result.get("confidence", 0)
                }
                
        except Exception as e:
            print(f"LLM NPC detection error: {e}")
        
        return None
    
    def _classify_encounter_type(self, user_input_lower: str) -> str:
        """Use LLM to classify the type of encounter based on user action"""
        from openrouter_config import create_role_client, OpenRouterConfig
        
        prompt = f"""
Classify the type of encounter based on the user's action.

**USER ACTION:**
{user_input_lower}

**TASK:**
Determine the primary intent/type of this action. Choose from:
- combat: Fighting, attacking, violent actions
- social: Talking, asking questions, negotiating, persuading
- stealth: Sneaking, hiding, avoiding detection
- trade: Buying, selling, exchanging goods/services
- general: Other interactions not fitting above categories

Respond with JSON:
{{
    "encounter_type": "combat/social/stealth/trade/general",
    "confidence": 0.0-1.0,
    "reasoning": "brief explanation of classification"
}}
"""
        
        try:
            client = create_role_client("interpretation")
            response = client.chat.completions.create(
                model=OpenRouterConfig.get_model_for_role("interpretation"),
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            result = json.loads(response.choices[0].message.content)
            return result.get("encounter_type", "general")
            
        except Exception as e:
            print(f"LLM encounter classification error: {e}")
            # Fallback to simple keyword detection
            if any(word in user_input_lower for word in ["attack", "fight", "hit", "strike"]):
                return "combat"
            elif any(word in user_input_lower for word in ["ask", "talk", "speak", "tell"]):
                return "social"
            elif any(word in user_input_lower for word in ["sneak", "hide", "avoid"]):
                return "stealth"
            elif any(word in user_input_lower for word in ["buy", "sell", "trade"]):
                return "trade"
            else:
                return "general"
    
    def end_encounter(self) -> EncounterContext:
        """End the current encounter and return to ROAM mode"""
        self.current_mode = SimulationMode.ROAM
        self.current_context = EncounterContext(
            mode=SimulationMode.ROAM,
            participants=[]
        )
        return self.current_context
    
    def get_current_mode(self) -> SimulationMode:
        """Get the current simulation mode"""
        return self.current_mode
    
    def set_mode(self, mode: SimulationMode) -> None:
        """Set the current simulation mode"""
        self.current_mode = mode
        self.current_context.mode = mode
    
    def is_in_encounter(self) -> bool:
        """Check if currently in an encounter"""
        return self.current_mode == SimulationMode.ENCOUNTER
    
    def get_encounter_participants(self) -> List[Any]:
        """Get list of current encounter participants"""
        return self.current_context.participants if self.current_context else []
