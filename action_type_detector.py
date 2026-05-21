"""
Action Type Detection System for UTAS
Determines whether actions are fallible vs contested and their specific categories.
"""

from enum import Enum
from typing import Dict, Any, Optional
import re

class ActionCategory(Enum):
    """Categories of actions for failure consequence determination."""
    MENTAL = "mental"  # Spirit penalty on <0 success (questions, thinking, observation, investigation)
    PHYSICAL = "physical"   # Stamina penalty on <0 success (physical actions)
    CONTESTED_COMBAT = "contested_combat"            # No additional penalty (already contested)
    CONTESTED_SOCIAL = "contested_social"            # No additional penalty (already contested)
    CONTESTED_RESOURCE = "contested_resource"        # No additional penalty (already contested)

class ActionTypeDetector:
    """Detects action types to determine appropriate failure consequences."""
    
    def __init__(self):
        # Keywords that indicate information gathering actions
        self.info_gathering_keywords = [
            'observe', 'look', 'examine', 'inspect', 'study', 'analyze', 'investigate',
            'search', 'scan', 'watch', 'listen', 'hear', 'smell', 'taste', 'feel',
            'perceive', 'notice', 'detect', 'discover', 'find', 'locate', 'spot',
            'identify', 'recognize', 'understand', 'comprehend', 'learn', 'gather',
            'collect', 'assess', 'evaluate', 'survey', 'scout', 'reconnaissance',
            'inquiry', 'question', 'ask', 'interrogate', 'interview', 'probe'
        ]
        
        # Keywords that indicate physical actions
        self.physical_keywords = [
            'climb', 'jump', 'leap', 'vault', 'scale', 'ascend', 'descend',
            'balance', 'navigate', 'traverse', 'cross', 'overcome', 'surmount',
            'break', 'smash', 'destroy', 'demolish', 'shatter', 'crush',
            'open', 'unlock', 'pick', 'force', 'pry', 'breach', 'penetrate',
            'lift', 'carry', 'move', 'push', 'pull', 'drag', 'haul',
            'run', 'sprint', 'dash', 'flee', 'escape', 'evade', 'dodge',
            'hide', 'conceal', 'sneak', 'stealth', 'infiltrate', 'slip',
            'craft', 'build', 'construct', 'create', 'make', 'forge',
            'repair', 'fix', 'mend', 'restore', 'heal', 'treat',
            # Common movement/locomotion phrases that often precede observation
            'go', 'head', 'walk', 'jog', 'stride', 'approach', 'enter', 'exit', 'leave', 'proceed', 'step', 'make my way', 'move to', 'go to', 'head to', 'walk to', 'run to'
        ]
        
        # Keywords that indicate contested actions (against other actors)
        self.contested_keywords = [
            'attack', 'strike', 'hit', 'punch', 'kick', 'stab', 'slash', 'shoot',
            'defend', 'block', 'parry', 'counter', 'resist', 'oppose',
            'persuade', 'convince', 'argue', 'debate', 'negotiate', 'bargain',
            'intimidate', 'threaten', 'menace', 'coerce', 'pressure',
            'deceive', 'lie', 'trick', 'fool', 'mislead', 'bluff',
            'charm', 'seduce', 'flirt', 'entice', 'allure', 'captivate',
            'compete', 'race', 'contest', 'challenge', 'duel', 'fight'
        ]

    def detect_action_category(self, action_data: Dict[str, Any]) -> ActionCategory:
        """
        Detect the category of an action based on its description and context.
        
        Args:
            action_data: Dictionary containing action information
            
        Returns:
            ActionCategory enum indicating the type of action
        """
        # Get action description from various possible fields
        description = ""
        if 'narrative_description' in action_data:
            description = action_data['narrative_description'].lower()
        elif 'action_description' in action_data:
            description = action_data['action_description'].lower()
        elif 'raw_action' in action_data:
            description = action_data['raw_action'].lower()
        
        # Check exchange type for additional context
        exchange_type = ""
        if 'utas_factors' in action_data:
            exchange_type = action_data['utas_factors'].get('exchange_type', '').lower()
        
        # Check if this is a contested action (has a reactor)
        is_contested = self._is_contested_action(action_data, description)
        
        if is_contested:
            # Determine contested action type
            if exchange_type == 'stamina' or any(keyword in description for keyword in ['attack', 'strike', 'hit', 'fight', 'combat']):
                return ActionCategory.CONTESTED_COMBAT
            elif exchange_type == 'spirit' or any(keyword in description for keyword in ['persuade', 'intimidate', 'deceive', 'charm']):
                return ActionCategory.CONTESTED_SOCIAL
            elif exchange_type == 'supply' or any(keyword in description for keyword in ['trade', 'bargain', 'negotiate', 'steal']):
                return ActionCategory.CONTESTED_RESOURCE
            else:
                # Default contested type based on exchange
                if exchange_type == 'stamina':
                    return ActionCategory.CONTESTED_COMBAT
                elif exchange_type == 'spirit':
                    return ActionCategory.CONTESTED_SOCIAL
                else:
                    return ActionCategory.CONTESTED_RESOURCE
        else:
            # This is a fallible action - determine type using earliest keyword wins strategy
            info_hits = [(kw, description.find(kw)) for kw in self.info_gathering_keywords if kw in description]
            sit_hits = [(kw, description.find(kw)) for kw in self.physical_keywords if kw in description]

            if info_hits or sit_hits:
                # If both appear, whichever occurs earliest in the string determines category
                earliest_info = min((pos for _, pos in info_hits), default=None)
                earliest_sit = min((pos for _, pos in sit_hits), default=None)

                if earliest_info is not None and earliest_sit is not None:
                    # Prefer whichever keyword appears first
                    if earliest_sit <= earliest_info:
                        return ActionCategory.PHYSICAL
                    else:
                        return ActionCategory.MENTAL
                elif earliest_sit is not None:
                    return ActionCategory.PHYSICAL
                else:
                    return ActionCategory.MENTAL
            else:
                # Default fallible categorization based on exchange type
                if exchange_type == 'spirit':
                    return ActionCategory.MENTAL
                else:
                    return ActionCategory.PHYSICAL

    def _is_contested_action(self, action_data: Dict[str, Any], description: str) -> bool:
        """
        Determine if an action is contested (against another actor) or fallible (against environment).
        
        Args:
            action_data: Action data dictionary
            description: Lowercase action description
            
        Returns:
            True if contested, False if fallible
        """
        # Check if action explicitly mentions targeting another actor
        if any(keyword in description for keyword in self.contested_keywords):
            return True
            
        # Check if action data indicates a reactor/target
        if 'target_actor' in action_data and action_data['target_actor']:
            return True
            
        # Check for pronouns indicating targeting someone
        target_pronouns = ['him', 'her', 'them', 'they', 'he', 'she']
        if any(pronoun in description.split() for pronoun in target_pronouns):
            return True
            
        # Check for specific actor names in description
        if re.search(r'\b(at|against|toward|towards)\s+\w+', description):
            return True
            
        # Default to fallible if no clear indication of targeting another actor
        return False

    def get_failure_penalty_status(self, action_category: ActionCategory) -> Optional[str]:
        """
        Get the status type that should be penalized for failure of this action category.
        
        Args:
            action_category: The category of action
            
        Returns:
            Status type name or None if no penalty applies
        """
        if action_category == ActionCategory.MENTAL:
            return "SPIRIT"
        elif action_category == ActionCategory.PHYSICAL:
            return "STAMINA"
        else:
            # Contested actions don't get additional failure penalties
            return None

    def should_apply_failure_penalty(self, action_category: ActionCategory, success_value: int) -> bool:
        """
        Determine if a failure penalty should be applied based on action category and success.
        
        Args:
            action_category: The category of action
            success_value: The calculated success value
            
        Returns:
            True if penalty should be applied
        """
        # Only apply penalties to fallible actions with negative success
        if action_category in [ActionCategory.CONTESTED_COMBAT, ActionCategory.CONTESTED_SOCIAL, ActionCategory.CONTESTED_RESOURCE]:
            return False
            
        return success_value < 0

    def is_fallible_action(self, action_description: str) -> bool:
        """
        Determine if an action is fallible (vs contested) based on description.
        
        Args:
            action_description: The action description string
            
        Returns:
            True if fallible, False if contested
        """
        # Create mock action_data for category detection
        action_data = {
            'action': action_description,
            'narrative_description': action_description
        }
        
        category = self.detect_action_category(action_data)
        
        # Fallible actions are mental and physical
        return category in [ActionCategory.MENTAL, ActionCategory.PHYSICAL]
