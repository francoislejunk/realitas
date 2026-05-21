"""
Rule of 3's Temporal Classification System for UTAS Simulation - Real-Time Version

This module implements the Rule of 3's temporal classification system for REAL-TIME simulation.

CRITICAL CHANGE: Removed THREE_HOUR category entirely.
- Only time skips allowed: SLEEP or UNCONSCIOUSNESS
- Travel is EXPERIENCED in real-time, not skipped
- Plane rides are LIVED, not teleported through
- Every moment is simulated

TWO TEMPORAL CATEGORIES:
- 3-SECOND: Combat, quick reactions, split-second decisions
- 3-MINUTE: Conversations, brief activities, travel chunks, everything else

Enhanced with LLM-based classification for intelligent temporal analysis.
"""

from enum import Enum
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
import json
import re
from openrouter_config import create_role_client, OpenRouterConfig

class RuleOf3Category(Enum):
    """Rule of 3's temporal classification categories - REAL-TIME VERSION"""
    THREE_SECOND = "3_second"
    THREE_MINUTE = "3_minute"
    SLEEP = "sleep"  # Special category for sleep actions (2-8 hours)
    # THREE_HOUR REMOVED - No time skipping except sleep/unconscious

@dataclass
class RuleOf3Context:
    """Represents the current Rule of 3's temporal context of a scene"""
    category: RuleOf3Category
    description: str
    transition_reason: Optional[str] = None
    previous_category: Optional[RuleOf3Category] = None

class RuleOf3Classifier:
    """Classifies actions and scenes into appropriate Rule of 3's temporal categories using LLM analysis"""
    
    def __init__(self):
        self.client = create_role_client("analysis")
        
        # Fallback keywords for when LLM fails
        self.fallback_keywords = {
            RuleOf3Category.THREE_SECOND: [
                "attack", "strike", "dodge", "block", "fight", "combat", "grab", "react",
                "quickly", "immediately", "instantly", "suddenly", "emergency"
            ],
            RuleOf3Category.THREE_MINUTE: [
                # Everything else goes here - conversations, travel, activities
                "talk", "ask", "look", "search", "examine", "walk", "sit", "wait",
                "drive", "travel", "fly", "ride", "journey",  # Travel is now 3-MINUTE
                "how far", "distance", "where is",
                "sleep", "rest", "nap"  # Sleep is 3-MINUTE (the action of falling asleep)
            ]
        }
        
        # Simplified transitions - only between 3-SECOND and 3-MINUTE
        self.transition_triggers = {
            # From combat to normal
            ("flee", "escape", "retreat", "disengage"): (RuleOf3Category.THREE_SECOND, RuleOf3Category.THREE_MINUTE),
            ("talk", "negotiate", "surrender", "yield"): (RuleOf3Category.THREE_SECOND, RuleOf3Category.THREE_MINUTE),
            ("calm", "breathe", "pause", "stop"): (RuleOf3Category.THREE_SECOND, RuleOf3Category.THREE_MINUTE),
            
            # From normal to combat
            ("attack", "fight", "combat", "strike"): (RuleOf3Category.THREE_MINUTE, RuleOf3Category.THREE_SECOND),
            ("danger", "threat", "emergency", "alarm"): (RuleOf3Category.THREE_MINUTE, RuleOf3Category.THREE_SECOND),
            ("ambush", "surprise", "sudden"): (RuleOf3Category.THREE_MINUTE, RuleOf3Category.THREE_SECOND),
        }

    def classify_action(self, user_input: str, scene_context: str = "") -> RuleOf3Category:
        """Classify an action into the appropriate Rule of 3's temporal category using LLM analysis"""
        try:
            # Use LLM for intelligent temporal classification
            return self._llm_classify_action(user_input, scene_context)
        except Exception as e:
            print(f"DEBUG: LLM classification failed, using fallback: {e}")
            # Fall back to keyword-based classification
            return self._fallback_classify_action(user_input)

    def _llm_classify_action(self, user_input: str, scene_context: str = "") -> RuleOf3Category:
        """Use LLM to intelligently classify temporal category"""
        prompt = f"""
Analyze this player action and classify it into the appropriate temporal category.

TEMPORAL CATEGORIES (REAL-TIME SIMULATION):
- 3_second: Combat actions, reflexes, split-second decisions (fighting, dodging, grabbing, immediate reactions)
- 3_minute: EVERYTHING ELSE - conversations, observations, activities, travel, etc.
- sleep: ONLY for actual sleeping/unconscious actions (nap, sleep, rest in bed, pass out)

CRITICAL: There is NO 3-hour category. Travel is experienced in real-time as 3_minute chunks.
- "I drive to the mall" = 3_minute (experience the drive)
- "I board the plane" = 3_minute (experience boarding and flight)
- "I sleep" = sleep (EXCEPTION: actual time passage during sleep, 2-8 hours)
- "I take a nap" = sleep (EXCEPTION: short rest, ~2 hours)

Player Action: "{user_input}"
Scene Context: "{scene_context}"

Consider:
- Is this immediate combat/reflex? → 3_second
- Is this actual sleeping/unconscious? → sleep
- Is this anything else? → 3_minute

Respond with ONLY the category: 3_second, 3_minute, or sleep
"""
        
        response = self.client.chat.completions.create(
            model=OpenRouterConfig.get_model_for_role("coordination"),
            messages=[{"role": "user", "content": prompt}],
            max_tokens=10,
            temperature=0.1
        )
        
        classification = response.choices[0].message.content.strip().lower()
        
        if "3_second" in classification:
            return RuleOf3Category.THREE_SECOND
        elif "sleep" in classification:
            return RuleOf3Category.SLEEP
        else:
            # Everything else is 3_minute
            return RuleOf3Category.THREE_MINUTE
    
    def _fallback_classify_action(self, user_input: str) -> RuleOf3Category:
        """Fallback keyword-based classification when LLM fails"""
        user_input = user_input.lower().strip()
        
        # Check for sleep keywords
        sleep_keywords = ["sleep", "nap", "doze", "slumber", "rest in bed", "lie down", "pass out", "unconscious"]
        if any(keyword in user_input for keyword in sleep_keywords):
            return RuleOf3Category.SLEEP
        
        # Check for combat/reflex keywords
        combat_keywords = self.fallback_keywords[RuleOf3Category.THREE_SECOND]
        if any(keyword in user_input for keyword in combat_keywords):
            return RuleOf3Category.THREE_SECOND
        
        # Everything else is 3_minute
        return RuleOf3Category.THREE_MINUTE

    def get_category_description(self, category: RuleOf3Category, user_input: str = "") -> str:
        """Get a contextual description of why this temporal category was chosen"""
        descriptions = {
            RuleOf3Category.THREE_SECOND: f"Combat/reflex action requiring immediate response",
            RuleOf3Category.THREE_MINUTE: f"Action experienced in real-time",
            RuleOf3Category.SLEEP: f"Sleep/unconscious state (time passage exception)"
        }
        return descriptions.get(category, "Standard action")

    def _detect_transition(self, action_lower: str, current_context: Optional[RuleOf3Context]) -> Optional[Tuple[RuleOf3Category, str]]:
        """Detect if an action would cause a Rule of 3's temporal transition"""
        for trigger_words, (from_category, to_category) in self.transition_triggers.items():
            if any(word in action_lower for word in trigger_words):
                if current_context and current_context.category == from_category:
                    reason = f"Action '{', '.join(trigger_words)}' triggers Rule of 3's transition from {from_category.value} to {to_category.value}"
                    return to_category, reason
        return None

    def get_rule_of_3s_description(self, category: RuleOf3Category) -> str:
        """Get descriptive text for a Rule of 3's category"""
        descriptions = {
            RuleOf3Category.THREE_SECOND: "Split-second timing where every moment counts. Actions happen in rapid succession with immediate consequences. Combat, quick reactions, and urgent decisions.",
            RuleOf3Category.THREE_MINUTE: "Real-time experience of actions and activities. Everything from conversations to travel is lived moment-by-moment. Time flows naturally without skips (except sleep/unconsciousness)."
        }
        return descriptions[category]

    def get_narrative_guidance(self, category: RuleOf3Category) -> Dict[str, str]:
        """Get narrative guidance for different Rule of 3's categories"""
        guidance = {
            RuleOf3Category.THREE_SECOND: {
                "pacing": "Fast, urgent, breathless - every second matters",
                "detail_level": "Focus on critical actions and immediate consequences only",
                "exchange_style": "Rapid back-and-forth, minimal exposition, action-focused",
                "scene_stability": "Scene remains tightly focused and contained",
                "narrator_tone": "Tense, immediate, high-stakes"
            },
            RuleOf3Category.THREE_MINUTE: {
                "pacing": "Natural, real-time flow - experience unfolds moment by moment", 
                "detail_level": "Balanced description with character interaction and environment",
                "exchange_style": "Natural dialogue and action flow, continuous experience",
                "scene_stability": "Scene evolves naturally, can include travel and transitions",
                "narrator_tone": "Immersive, present-tense, experiential"
            }
        }
        return guidance[category]

class RuleOf3TransitionManager:
    """Manages transitions between Rule of 3's temporal contexts"""
    
    def __init__(self):
        self.transition_history: List[RuleOf3Context] = []
        
    def process_transition(self, current_context: Optional[RuleOf3Context], 
                         new_category: RuleOf3Category, 
                         transition_reason: str) -> RuleOf3Context:
        """Process a Rule of 3's transition and create new context"""
        previous_category = current_context.category if current_context else None
        
        new_context = RuleOf3Context(
            category=new_category,
            description=self._generate_transition_description(previous_category, new_category),
            transition_reason=transition_reason,
            previous_category=previous_category
        )
        
        self.transition_history.append(new_context)
        return new_context
    
    def _generate_transition_description(self, from_category: Optional[RuleOf3Category], 
                                       to_category: RuleOf3Category) -> str:
        """Generate description for Rule of 3's transition"""
        if from_category is None:
            return f"Scene established in {to_category.value} Rule of 3's timeframe"
        
        transitions = {
            (RuleOf3Category.THREE_SECOND, RuleOf3Category.THREE_MINUTE): 
                "The immediate intensity subsides, allowing for more deliberate actions and natural flow",
            (RuleOf3Category.THREE_MINUTE, RuleOf3Category.THREE_SECOND):
                "Sudden urgency transforms the scene into split-second timing and immediate action"
        }
        
        return transitions.get((from_category, to_category), 
                             f"Rule of 3's scene transitions from {from_category.value} to {to_category.value}")

    def get_transition_narrative_cues(self, context: RuleOf3Context) -> List[str]:
        """Get narrative cues for handling Rule of 3's transitions"""
        if not context.previous_category:
            return []
        
        cues = []
        
        if context.previous_category == RuleOf3Category.THREE_SECOND and context.category == RuleOf3Category.THREE_MINUTE:
            cues.extend([
                "The adrenaline begins to fade as the immediate crisis passes...",
                "Breathing space allows for clearer thinking and conversation...",
                "The urgent pace slows to a more manageable rhythm..."
            ])
        elif context.category == RuleOf3Category.THREE_SECOND:
            cues.extend([
                "Suddenly, every second counts...",
                "The situation demands immediate action...",
                "Time seems to slow as crisis unfolds..."
            ])
        
        return cues

def get_rule_of_3s_display_name(category: RuleOf3Category) -> str:
    """Get display-friendly name for Rule of 3's category"""
    names = {
        RuleOf3Category.THREE_SECOND: "3-Second (Immediate)",
        RuleOf3Category.THREE_MINUTE: "3-Minute (Real-Time)"
    }
    return names[category]

def get_rule_of_3s_examples(category: RuleOf3Category) -> Dict[str, List[str]]:
    """Get example actions for each Rule of 3's category organized by action type"""
    examples = {
        RuleOf3Category.THREE_SECOND: {
            "fallible_gathering": [
                "I quickly scan the room for exits",
                "I glance at the guard's weapon to assess the threat"
            ],
            "fallible_overcoming": [
                "I dodge the incoming projectile",
                "I duck behind cover as shots ring out"
            ],
            "contested": [
                "I attack the guard with my sword",
                "I grapple with the assassin for control of the knife"
            ]
        },
        RuleOf3Category.THREE_MINUTE: {
            "fallible_gathering": [
                "I search the room thoroughly for clues",
                "I examine the strange artifact to understand its purpose",
                "I research the ancient texts in the library"  # Experienced in real-time chunks
            ],
            "fallible_overcoming": [
                "I carefully pick the lock on the door",
                "I climb the fence to reach the other side",
                "I drive to the mall",  # Experienced in real-time
                "I board the plane"  # Experienced in real-time
            ],
            "contested": [
                "I negotiate with the merchant about prices",
                "I arm wrestle the tavern patron for information"
            ]
        }
    }
    return examples[category]

def get_action_type_examples() -> Dict[str, Dict[str, str]]:
    """Get detailed examples and descriptions for each action type across temporal categories"""
    return {
        "fallible_gathering": {
            "description": "Information gathering actions that can fail - perception, investigation, research",
            "3_second_examples": "Quick glances, rapid assessments, split-second observations",
            "3_minute_examples": "Searching rooms, examining objects, asking questions, extended research (in real-time chunks)"
        },
        "fallible_overcoming": {
            "description": "Skill-based actions to overcome obstacles - climbing, lockpicking, repairs, travel",
            "3_second_examples": "Reflexive dodges, instant reactions, emergency maneuvers",
            "3_minute_examples": "Picking locks, climbing walls, solving puzzles, driving, flying (all experienced in real-time)"
        },
        "contested": {
            "description": "Direct opposition against NPCs - combat, negotiations, competitions",
            "3_second_examples": "Combat strikes, quick grapples, instant counters",
            "3_minute_examples": "Negotiations, arm wrestling, brief duels, extended discussions"
        }
    }
