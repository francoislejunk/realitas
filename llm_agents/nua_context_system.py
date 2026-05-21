"""
NUA context awareness system for UTAS simulation.
Tracks escalation patterns and maintains context between turns.
"""

from enum import Enum
from typing import Dict, List, Optional
import json
from openrouter_config import create_openrouter_client


class EscalationLevel(Enum):
    """Levels of escalation in interactions."""
    PEACEFUL = 1      # Friendly, neutral, cooperative
    TENSE = 2         # Suspicious, cautious, mildly hostile
    HOSTILE = 3       # Aggressive, threatening, confrontational
    VIOLENT = 4       # Physical attacks, serious threats
    LETHAL = 5        # Life-threatening actions, deadly intent


class ActionType(Enum):
    """Types of actions for context tracking."""
    SOCIAL = "social"           # Talking, negotiating, persuading
    THREATENING = "threatening" # Intimidation, warnings, posturing
    PHYSICAL = "physical"       # Attacks, grabs, pushes
    DEFENSIVE = "defensive"     # Blocking, dodging, protecting
    DECEPTIVE = "deceptive"     # Lying, misdirection, tricks
    HELPFUL = "helpful"         # Assistance, cooperation, aid


class NUAContextTracker:
    """Tracks NUA context and escalation patterns across turns."""
    
    def __init__(self, nua_name: str):
        """Initialize NUA context tracker."""
        self.nua_name = nua_name
        self.escalation_level = EscalationLevel.PEACEFUL
        self.turn_history = []
        self.ua_action_pattern = []
        self.last_ua_action_type = None
        self.consecutive_hostile_actions = 0
        self.trust_level = 3  # 1-5 scale, starts neutral
        self.client = create_openrouter_client()
        
    def record_turn(self, ua_action_data: Dict, nua_response_data: Dict, turn_number: int):
        """Record a turn's actions for context building."""
        print(f"DEBUG ESCALATION: Recording turn {turn_number} for {self.nua_name}")
        print(f"DEBUG ESCALATION: UA action data: {ua_action_data.get('narrative_description', 'NO DESCRIPTION')}")
        ua_action_type = self._classify_action_type(ua_action_data.get('narrative_description', ''))
        ua_escalation = self._determine_escalation_from_action(ua_action_data)
        
        turn_record = {
            'turn': turn_number,
            'ua_action': ua_action_data.get('narrative_description', ''),
            'ua_action_type': ua_action_type.value,
            'ua_escalation': ua_escalation.value,
            'nua_response': nua_response_data.get('narrative_description', ''),
            'escalation_before': self.escalation_level.value,
            'trust_before': self.trust_level
        }
        
        # Update patterns
        self._update_escalation_level(ua_escalation, ua_action_type)
        self._update_trust_level(ua_action_type)
        self._track_action_patterns(ua_action_type)
        
        turn_record['escalation_after'] = self.escalation_level.value
        turn_record['trust_after'] = self.trust_level
        
        self.turn_history.append(turn_record)
        self.last_ua_action_type = ua_action_type
        
    def _classify_action_type(self, action_description: str) -> ActionType:
        """Classify the type of action based on description using LLM analysis."""
        
        classification_prompt = f"""Analyze the following action and classify it into one of these categories:

Action Description: "{action_description}"

Action Types:
- SOCIAL: Conversation, negotiation, social interaction
- THREATENING: Intimidation, warnings, menacing behavior
- PHYSICAL: Physical attacks, combat, violent actions
- DEFENSIVE: Blocking, dodging, protecting, evasive actions
- DECEPTIVE: Lying, misdirection, tricks, deception
- HELPFUL: Assistance, cooperation, aid, support

Respond with ONLY the action type name: SOCIAL, THREATENING, PHYSICAL, DEFENSIVE, DECEPTIVE, or HELPFUL"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324",
                messages=[{"role": "user", "content": classification_prompt}],
                temperature=0.1
            )
            
            classification_result = response.choices[0].message.content.strip().upper()
            print(f"DEBUG ACTION TYPE: LLM classification result: {classification_result}")
            
            # Map result to enum
            type_mapping = {
                'SOCIAL': ActionType.SOCIAL,
                'THREATENING': ActionType.THREATENING,
                'PHYSICAL': ActionType.PHYSICAL,
                'DEFENSIVE': ActionType.DEFENSIVE,
                'DECEPTIVE': ActionType.DECEPTIVE,
                'HELPFUL': ActionType.HELPFUL
            }
            
            if classification_result in type_mapping:
                detected_type = type_mapping[classification_result]
                print(f"DEBUG ACTION TYPE: {detected_type.value} detected via LLM analysis")
                return detected_type
            else:
                print(f"DEBUG ACTION TYPE: Invalid LLM response '{classification_result}', defaulting to SOCIAL")
                return ActionType.SOCIAL
                
        except Exception as e:
            print(f"DEBUG ACTION TYPE: LLM analysis failed ({e}), defaulting to SOCIAL")
            return ActionType.SOCIAL
    
    def _determine_escalation_from_action(self, action_data: Dict) -> EscalationLevel:
        """Determine escalation level from action data using LLM analysis."""
        action_desc = action_data.get('narrative_description', '')
        stress_level = action_data.get('utas_factors', {}).get('stress_level', 1)
        
        print(f"DEBUG ESCALATION: Analyzing action: '{action_desc}'")
        print(f"DEBUG ESCALATION: Stress level: {stress_level}")
        
        # Use LLM to dynamically analyze escalation level
        escalation_prompt = f"""Analyze the following action and determine its escalation level based on intent and severity.

Action Description: "{action_desc}"
Actor Stress Level: {stress_level}/5

Escalation Levels:
- PEACEFUL (1): Friendly, neutral, cooperative actions
- TENSE (2): Suspicious, cautious, mildly confrontational actions  
- HOSTILE (3): Aggressive, threatening, intimidating actions
- VIOLENT (4): Physical attacks, serious physical threats, combat actions
- LETHAL (5): Life-threatening actions, deadly intent, attempts to kill or cause fatal harm

Consider:
- Physical violence level (none/minor/serious/deadly)
- Intent to harm (none/intimidate/hurt/kill)
- Weapon usage and targeting of vital areas
- Overall threat level to life and safety

Respond with ONLY the escalation level name: PEACEFUL, TENSE, HOSTILE, VIOLENT, or LETHAL"""

        try:
            response = self.client.chat.completions.create(
                model="deepseek/deepseek-chat-v3-0324",
                messages=[{"role": "user", "content": escalation_prompt}],
                temperature=0.1
            )
            
            escalation_result = response.choices[0].message.content.strip().upper()
            print(f"DEBUG ESCALATION: LLM analysis result: {escalation_result}")
            
            # Map result to enum
            escalation_mapping = {
                'PEACEFUL': EscalationLevel.PEACEFUL,
                'TENSE': EscalationLevel.TENSE,
                'HOSTILE': EscalationLevel.HOSTILE,
                'VIOLENT': EscalationLevel.VIOLENT,
                'LETHAL': EscalationLevel.LETHAL
            }
            
            if escalation_result in escalation_mapping:
                detected_level = escalation_mapping[escalation_result]
                print(f"DEBUG ESCALATION: {detected_level.name} detected via LLM analysis")
                return detected_level
            else:
                print(f"DEBUG ESCALATION: Invalid LLM response '{escalation_result}', falling back to stress-based detection")
                # Fallback to stress-based detection
                if stress_level >= 4:
                    return EscalationLevel.TENSE
                else:
                    return EscalationLevel.PEACEFUL
                    
        except Exception as e:
            print(f"DEBUG ESCALATION: LLM analysis failed ({e}), falling back to stress-based detection")
            # Fallback to stress-based detection
            if stress_level >= 4:
                return EscalationLevel.TENSE
            else:
                return EscalationLevel.PEACEFUL
    
    def _update_escalation_level(self, ua_escalation: EscalationLevel, ua_action_type: ActionType):
        """Update NUA's escalation level based on UA actions."""
        # Track consecutive hostile actions
        if ua_action_type in [ActionType.PHYSICAL, ActionType.THREATENING]:
            self.consecutive_hostile_actions += 1
        else:
            self.consecutive_hostile_actions = max(0, self.consecutive_hostile_actions - 1)
        
        # Escalation rules
        if ua_escalation.value >= EscalationLevel.LETHAL.value:
            # Lethal intent (e.g., stabbing throat) must be treated as lethal.
            self.escalation_level = EscalationLevel.LETHAL
        elif ua_escalation.value >= EscalationLevel.VIOLENT.value:
            # Violence begets violence
            self.escalation_level = EscalationLevel.VIOLENT
        elif ua_escalation.value >= EscalationLevel.HOSTILE.value:
            # Hostility escalates gradually
            if self.escalation_level.value < EscalationLevel.HOSTILE.value:
                self.escalation_level = EscalationLevel.HOSTILE
            elif self.consecutive_hostile_actions >= 2:
                self.escalation_level = EscalationLevel.VIOLENT
        elif ua_action_type == ActionType.HELPFUL and self.escalation_level.value > EscalationLevel.TENSE.value:
            # Helpful actions can de-escalate slowly
            self.escalation_level = EscalationLevel(max(1, self.escalation_level.value - 1))
    
    def _update_trust_level(self, ua_action_type: ActionType):
        """Update trust level based on UA actions."""
        if ua_action_type == ActionType.PHYSICAL:
            self.trust_level = max(1, self.trust_level - 2)
        elif ua_action_type == ActionType.THREATENING:
            self.trust_level = max(1, self.trust_level - 1)
        elif ua_action_type == ActionType.DECEPTIVE:
            self.trust_level = max(1, self.trust_level - 1)
        elif ua_action_type == ActionType.HELPFUL:
            self.trust_level = min(5, self.trust_level + 1)
        elif ua_action_type == ActionType.DEFENSIVE:
            # Defensive actions don't change trust much
            pass
    
    def _track_action_patterns(self, ua_action_type: ActionType):
        """Track patterns in UA actions."""
        self.ua_action_pattern.append(ua_action_type)
        # Keep only last 5 actions for pattern recognition
        if len(self.ua_action_pattern) > 5:
            self.ua_action_pattern.pop(0)
    
    def get_nua_response_guidance(self) -> Dict:
        """Get guidance for NUA response based on current context."""
        guidance = {
            'escalation_level': self.escalation_level.value,
            'trust_level': self.trust_level,
            'consecutive_hostile': self.consecutive_hostile_actions,
            'recommended_action_type': self._get_recommended_action_type(),
            'response_intensity': self._get_response_intensity(),
            'context_summary': self._get_context_summary()
        }
        return guidance
    
    def _get_recommended_action_type(self) -> str:
        """Get recommended action type for NUA based on context."""
        if self.escalation_level == EscalationLevel.LETHAL:
            return "lethal_response"
        elif self.escalation_level == EscalationLevel.VIOLENT:
            return "violent_response"
        elif self.escalation_level == EscalationLevel.HOSTILE:
            if self.consecutive_hostile_actions >= 2:
                return "escalate_to_violence"
            else:
                return "hostile_response"
        elif self.escalation_level == EscalationLevel.TENSE:
            return "defensive_posture"
        else:
            return "social_response"
    
    def _get_response_intensity(self) -> int:
        """Get recommended response intensity (1-5)."""
        base_intensity = self.escalation_level.value
        
        # Adjust based on consecutive hostile actions
        if self.consecutive_hostile_actions >= 3:
            base_intensity += 1
        elif self.consecutive_hostile_actions >= 2:
            base_intensity += 0.5
        
        # Adjust based on trust
        if self.trust_level <= 2:
            base_intensity += 0.5
        elif self.trust_level >= 4:
            base_intensity -= 0.5
        
        return min(5, max(1, int(base_intensity)))
    
    def _get_context_summary(self) -> str:
        """Get a summary of the current context for LLM prompts."""
        recent_actions = self.ua_action_pattern[-3:] if len(self.ua_action_pattern) >= 3 else self.ua_action_pattern
        action_pattern = " -> ".join([action.value for action in recent_actions])
        
        summary = f"Escalation: {self.escalation_level.name}, Trust: {self.trust_level}/5"
        if action_pattern:
            summary += f", Recent UA pattern: {action_pattern}"
        if self.consecutive_hostile_actions > 0:
            summary += f", Consecutive hostile actions: {self.consecutive_hostile_actions}"
        
        return summary
    
    def get_turn_history_summary(self, last_n_turns: int = 3) -> str:
        """Get a summary of the last N turns for context."""
        if not self.turn_history:
            return "No previous interactions."
        
        recent_turns = self.turn_history[-last_n_turns:]
        summary_lines = []
        
        for turn in recent_turns:
            summary_lines.append(
                f"Turn {turn['turn']}: UA {turn['ua_action_type']} -> "
                f"Escalation {turn['escalation_before']} to {turn['escalation_after']}"
            )
        
        return "\n".join(summary_lines)


class NUAContextManager:
    """Manages context for multiple NUAs."""
    
    def __init__(self):
        self.nua_contexts: Dict[str, NUAContextTracker] = {}

    @staticmethod
    def _canonicalize_nua_key(nua_name: str) -> str:
        try:
            t = str(nua_name or '').strip().lower()
            # Remove common bracket/quote wrappers used by some display names.
            t = t.replace('[', ' ').replace(']', ' ')
            t = t.replace('"', ' ').replace("'", ' ')
            t = " ".join(t.split())
            return t
        except Exception:
            return str(nua_name or '').strip().lower()
    
    def get_or_create_context(self, nua_name: str) -> NUAContextTracker:
        """Get existing context or create new one for NUA."""
        key = self._canonicalize_nua_key(nua_name)
        if key not in self.nua_contexts:
            self.nua_contexts[key] = NUAContextTracker(nua_name)
        return self.nua_contexts[key]
    
    def record_interaction(self, nua_name: str, ua_action_data: Dict, nua_response_data: Dict, turn_number: int):
        """Record an interaction for a specific NUA."""
        context = self.get_or_create_context(nua_name)
        context.record_turn(ua_action_data, nua_response_data, turn_number)
    
    def get_context_for_nua(self, nua_name: str) -> Optional[NUAContextTracker]:
        """Get context for a specific NUA."""
        return self.nua_contexts.get(self._canonicalize_nua_key(nua_name))
