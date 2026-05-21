"""
Do Nothing Action System

Allows UA and NUA/INUA to explicitly choose to do nothing.
This is a valid action that:
- Advances time naturally
- Allows observation and reflection
- Lets events unfold around the character
- Provides rest and recovery opportunities

Examples:
- "I do nothing"
- "I wait"
- "I stand still"
- "I observe"
- "I rest"
"""

from typing import Dict, Any, List
from rule_of_3s import RuleOf3Category


class DoNothingAction:
    """Handles the 'do nothing' action for all actors"""
    
    # Keywords that indicate doing nothing
    DO_NOTHING_KEYWORDS = [
        # Explicit nothing
        "do nothing", "doing nothing", "i do nothing",
        
        # Waiting
        "wait", "i wait", "waiting", "wait here",
        
        # Standing/sitting still
        "stand still", "sit still", "stay still", "remain still",
        "don't move", "stay put", "hold position",
        
        # Observing passively
        "observe", "watch", "just watch", "just look",
        "take it in", "absorb the scene",
        
        # Resting
        "rest", "take a break", "pause", "catch my breath",
        
        # Thinking/reflecting
        "think", "reflect", "contemplate", "ponder",
        "gather my thoughts", "consider my options",
        
        # Letting time pass
        "let time pass", "pass the time", "kill time",
        "hang around", "loiter"
    ]
    
    @staticmethod
    def is_do_nothing_action(user_input: str) -> bool:
        """
        Check if user input is a 'do nothing' action.
        
        Args:
            user_input: The user's input string
            
        Returns:
            True if this is a do nothing action
        """
        input_lower = user_input.lower().strip()
        
        # CRITICAL: Exclude actions that contain active verbs indicating actual actions
        # These are NOT "do nothing" even if they contain keywords like "look"
        active_action_indicators = [
            "look for", "search for", "find", "go to", "head to", "head over", "walk to",
            "move to", "run to", "drive to", "travel to", "get to",
            "want to", "need to", "going to", "try to", "attempt to",
            "i'm hungry", "i'm thirsty", "i'm tired", "i need",
            "talk to", "speak to", "say to", "tell", "ask", "greet",
            "approach", "go up to", "walk up to", "head toward"
        ]
        
        for indicator in active_action_indicators:
            if indicator in input_lower:
                return False  # This is an active action, not "do nothing"
        
        # CRITICAL: Exclude if action contains dialogue (quotes indicate active speech)
        if '"' in user_input or "'" in user_input or " say " in input_lower or " said " in input_lower:
            return False  # Speech is an active action, not "do nothing"
        
        # Check for exact matches or partial matches
        for keyword in DoNothingAction.DO_NOTHING_KEYWORDS:
            if keyword in input_lower:
                return True
        
        return False
    
    @staticmethod
    def execute_do_nothing(
        actor_name: str,
        user_input: str,
        scene_description: str,
        time_context: Dict[str, Any],
        is_user_actor: bool = True
    ) -> Dict[str, Any]:
        """
        Execute a 'do nothing' action.
        
        Args:
            actor_name: Name of the actor doing nothing
            user_input: The original input
            scene_description: Current scene
            time_context: Current time context
            is_user_actor: Whether this is the user actor
            
        Returns:
            Dictionary with action results
        """
        
        # Determine the type of 'nothing' being done
        action_type = DoNothingAction._classify_nothing_type(user_input)
        
        # Generate narrative based on type
        narrative = DoNothingAction._generate_narrative(
            actor_name, action_type, scene_description, time_context
        )
        
        # Determine time cost (doing nothing still takes time)
        time_category = RuleOf3Category.THREE_MINUTE  # Default: a few minutes pass
        
        return {
            "action_type": "do_nothing",
            "nothing_type": action_type,
            "narrative": narrative,
            "time_category": time_category,
            "actor_name": actor_name,
            "is_user_actor": is_user_actor,
            "allows_events": True,  # Events can happen while doing nothing
            "allows_recovery": action_type in ["rest", "think"],  # Some types allow recovery
            "user_input": user_input
        }
    
    @staticmethod
    def _classify_nothing_type(user_input: str) -> str:
        """Classify what type of 'nothing' is being done"""
        input_lower = user_input.lower()
        
        if any(kw in input_lower for kw in ["wait", "waiting"]):
            return "wait"
        elif any(kw in input_lower for kw in ["observe", "watch", "look"]):
            return "observe"
        elif any(kw in input_lower for kw in ["rest", "break", "catch my breath"]):
            return "rest"
        elif any(kw in input_lower for kw in ["think", "reflect", "contemplate", "ponder", "consider"]):
            return "think"
        elif any(kw in input_lower for kw in ["stand still", "sit still", "stay still", "don't move"]):
            return "stay_still"
        else:
            return "passive"  # Generic doing nothing
    
    @staticmethod
    def _generate_narrative(
        actor_name: str,
        action_type: str,
        scene_description: str,
        time_context: Dict[str, Any]
    ) -> str:
        """Generate narrative for doing nothing"""
        
        time_of_day = time_context.get('time_of_day', 'day')
        
        narratives = {
            "wait": [
                f"You stand in place, letting the moments pass. The world continues around you.",
                f"Time flows by as you wait. Nothing urgent demands your attention.",
                f"You settle into a patient stance, watching the scene unfold at its own pace."
            ],
            "observe": [
                f"You take a moment to simply observe your surroundings. Details you hadn't noticed before catch your eye.",
                f"Standing still, you let your senses take in the scene. The world reveals itself in small details.",
                f"You watch quietly, absorbing the atmosphere and the subtle movements around you."
            ],
            "rest": [
                f"You take a moment to catch your breath. The brief respite is welcome.",
                f"Pausing to rest, you feel some of the tension ease from your shoulders.",
                f"You allow yourself a moment of rest. Your body appreciates the break."
            ],
            "think": [
                f"You take time to gather your thoughts, considering your situation.",
                f"Standing in quiet reflection, you turn things over in your mind.",
                f"You pause to think, letting your thoughts settle and clarify."
            ],
            "stay_still": [
                f"You remain perfectly still, a statue in the flow of time.",
                f"Motionless, you let the world move around you while you stay anchored in place.",
                f"You hold your position, unmoving, as moments tick by."
            ],
            "passive": [
                f"You do nothing in particular. Time passes.",
                f"The world continues its rhythm while you simply exist within it.",
                f"You let yourself be, without action or intent. Just being is enough."
            ]
        }
        
        import random
        return random.choice(narratives.get(action_type, narratives["passive"]))
    
    @staticmethod
    def get_do_nothing_examples() -> List[str]:
        """Get example 'do nothing' inputs for help text"""
        return [
            "I do nothing",
            "I wait",
            "I observe my surroundings",
            "I rest for a moment",
            "I think about my situation",
            "I stand still"
        ]


# Helper function for easy integration
def check_and_execute_do_nothing(
    user_input: str,
    actor_name: str,
    scene_description: str,
    time_context: Dict[str, Any],
    is_user_actor: bool = True
) -> Dict[str, Any]:
    """
    Check if input is 'do nothing' and execute if so.
    
    Returns:
        Result dict if do nothing action, None otherwise
    """
    if DoNothingAction.is_do_nothing_action(user_input):
        return DoNothingAction.execute_do_nothing(
            actor_name, user_input, scene_description, time_context, is_user_actor
        )
    return None
