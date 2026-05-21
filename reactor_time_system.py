"""
Time-based reactor inquiry system for UTAS simulation.
Manages time budgets for reactor responses based on proactor action speed.
"""

from enum import Enum
from rule_of_3s import RuleOf3Category
from color_utils import Color
from openrouter_config import OpenRouterConfig
import json


class ActionSpeed(Enum):
    """Classification of action speeds for time budget calculation."""
    INSTANT = "instant"        # 1-2 seconds (punch, grab, quick strike)
    FAST = "fast"             # 3-6 seconds (insult, shout, simple action)
    MODERATE = "moderate"     # 7-15 seconds (negotiate, explain, complex action)
    SLOW = "slow"            # 16-30 seconds (detailed planning, long speech)
    EXTENDED = "extended"    # 30+ seconds (complex rituals, long processes)


class ReactorTimeManager:
    """Manages time budgets and inquiry tracking for reactor responses."""
    
    def __init__(self):
        self.time_budget = 0
        self.time_used = 0
        self.inquiry_count = 0
        self.max_inquiries = 0
        
    def calculate_time_budget(self, proactor_action_data):
        """Calculate time budget based on proactor action characteristics."""
        # Handle both dict input (from main simulation) and direct RuleOf3Category (from tests)
        if isinstance(proactor_action_data, dict):
            rule_of_3s_category = proactor_action_data.get('rule_of_3s_category', RuleOf3Category.THREE_SECOND)
            stress_level = proactor_action_data.get('utas_factors', {}).get('stress_level', 1)
            action_description = proactor_action_data.get('narrative_description', '').lower()
        else:
            # Direct RuleOf3Category input (for testing)
            rule_of_3s_category = proactor_action_data
            stress_level = 1
            action_description = ''
        
        # Base time from Rule of 3s
        base_time = self._get_base_time_from_rule_of_3s(rule_of_3s_category)
        
        # Adjust based on action type
        action_speed = self._classify_action_speed(action_description, stress_level)
        time_multiplier = self._get_time_multiplier(action_speed)
        
        # Override base time for verbal actions that got misclassified as THREE_SECOND
        verbal_keywords = ['whisper', 'speak', 'talk', 'say', 'tell', 'negotiate', 'explain', 'argue', 'shout', 'call']
        if (rule_of_3s_category == RuleOf3Category.THREE_SECOND and 
            any(keyword in action_description for keyword in verbal_keywords)):
            base_time = 15  # Override to give reasonable time for verbal actions
        
        self.time_budget = int(base_time * time_multiplier)
        self.time_used = 0
        self.inquiry_count = 0
        self.max_inquiries = self._calculate_max_inquiries(self.time_budget)
        
        return {
            'time_budget': self.time_budget,
            'action_speed': action_speed.value,
            'max_inquiries': self.max_inquiries,
            'base_time': base_time,
            'multiplier': time_multiplier
        }
    
    def _get_base_time_from_rule_of_3s(self, category):
        """Get base time allocation from Rule of 3s category."""
        time_mapping = {
            RuleOf3Category.THREE_SECOND: 3,
            RuleOf3Category.THREE_MINUTE: 180,  # 3 minutes in seconds
            # THREE_HOUR removed - real-time simulation only
        }
        return time_mapping.get(category, 180)  # Default to 3 minutes
    
    def _classify_action_speed(self, action_description, stress_level):
        """Classify action speed using keyword-based classification."""
        return self._classify_action_speed_keywords(action_description, stress_level)
    
    
    def _classify_action_speed_keywords(self, action_description, stress_level):
        """Classify action speed based on keywords and stress level."""
        action_lower = action_description.lower()
        
        # INSTANT actions (1-2 seconds)
        instant_keywords = ['grab', 'lunge', 'pounce', 'snatch', 'tackle']
        if any(word in action_lower for word in instant_keywords):
            return ActionSpeed.INSTANT
        
        # FAST actions (3-6 seconds)  
        fast_keywords = ['punch', 'hit', 'strike', 'attack', 'slash', 'stab', 'shoot', 'throw', 'shout', 'yell', 'insult', 'deceive']
        if any(word in action_lower for word in fast_keywords):
            return ActionSpeed.FAST
        
        # MODERATE actions (7-15 seconds)
        moderate_keywords = ['speak', 'talk', 'brandish', 'show', 'display', 'negotiate', 'explain', 'persuade', 'intimidate']
        if any(word in action_lower for word in moderate_keywords):
            return ActionSpeed.MODERATE
        
        # SLOW actions (16-30 seconds)
        slow_keywords = ['plan', 'scheme', 'prepare', 'ritual', 'ceremony', 'speech']
        if any(word in action_lower for word in slow_keywords):
            return ActionSpeed.SLOW
        
        # Default based on stress level
        if stress_level >= 4:
            return ActionSpeed.FAST  # High stress = urgent actions
        elif stress_level <= 2:
            return ActionSpeed.MODERATE  # Low stress = more deliberate
        else:
            return ActionSpeed.MODERATE  # Standard default
    
    def _get_time_multiplier(self, action_speed):
        """Get time multiplier based on action speed."""
        multipliers = {
            ActionSpeed.INSTANT: 1.0,    # 3 seconds for instant reactions
            ActionSpeed.FAST: 1.5,       # 4.5 seconds for fast actions
            ActionSpeed.MODERATE: 2.0,   # 6 seconds for moderate actions
            ActionSpeed.SLOW: 2.5,       # 7.5 seconds for slow actions
            ActionSpeed.EXTENDED: 3.0    # 9 seconds for extended actions
        }
        return multipliers.get(action_speed, 1.0)
    
    def _calculate_max_inquiries(self, time_budget):
        """Calculate maximum number of inquiries based on time budget."""
        # Each inquiry takes 3-6 seconds on average
        avg_inquiry_time = 4.5
        return max(1, int(time_budget / avg_inquiry_time))
    
    def consume_inquiry_time(self, inquiry_complexity='simple', inquiry_text=''):
        """Consume time for an inquiry and return if time remains."""
        complexity_time = {
            'simple': 1,    # Quick question
            'moderate': 2,  # Detailed question
            'complex': 3    # Very detailed question
        }
        
        time_cost = complexity_time.get(inquiry_complexity, 4)
        self.time_used += time_cost
        self.inquiry_count += 1
        
        return self.get_remaining_time() > 0
    
    def get_remaining_time(self):
        """Get remaining time budget."""
        return max(0, self.time_budget - self.time_used)
    
    def advance_reactor_time(self, duration_seconds):
        """Advance the reactor's time usage by the given duration."""
        self.time_used += duration_seconds
    
    def has_time_remaining(self):
        """Check if reactor has time remaining for actions."""
        return self.get_remaining_time() > 0
    
    def get_time_status(self):
        """Get current time status for debugging/display."""
        return {
            'budget': self.time_budget,
            'used': self.time_used,
            'remaining': self.get_remaining_time(),
            'inquiries_made': self.inquiry_count,
            'max_inquiries': self.max_inquiries,
            'time_expired': not self.has_time_remaining()
        }
    
    def classify_inquiry_complexity(self, inquiry_text):
        """Classify inquiry complexity based on content."""
        word_count = len(inquiry_text.split())
        
        if word_count <= 5:
            return 'simple'
        elif word_count <= 12:
            return 'moderate'
        else:
            return 'complex'


def create_time_expired_result():
    """Create a reactor result for when time expires."""
    return {
        'success_level': 0,
        'time_expired': True,
        'narrative': "Time runs out before a defensive action can be taken.",
        'automatic_failure': True
    }


def display_time_budget_info(time_info, show_details=False):
    """Display time budget information (for debugging)."""
    if show_details:
        print(f"{Color.SYSTEM}⏱️ Reactor Time Budget: {time_info['time_budget']}s ({time_info['action_speed']} action){Color.RESET}")
        print(f"{Color.SYSTEM}   Max inquiries: {time_info['max_inquiries']}{Color.RESET}")
