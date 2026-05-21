"""
Internal Voice System - Personality and Goal-Driven Internal Monologue

Enhances the UA's internal voice with:
- Internal personality traits (including moral aspects)
- Current goals (immediate and long-term)
- Situational cue system (max 1 tidbit per response)
- Anti-bloat measures through contextual triggering

The system waits for relevant situational cues before surfacing
personality/goal information, avoiding prompt overload.
"""

from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import random


# ═══════════════════════════════════════════════════════════════════════════════
# PERSONALITY TRAIT SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class MoralAxis(Enum):
    """Moral alignment axes"""
    COMPASSION = "compassion"      # Caring vs Callous
    HONESTY = "honesty"            # Truthful vs Deceptive
    LOYALTY = "loyalty"            # Faithful vs Self-serving
    JUSTICE = "justice"            # Fair vs Exploitative
    COURAGE = "courage"            # Brave vs Cowardly


class PersonalityDimension(Enum):
    """Core personality dimensions"""
    OPENNESS = "openness"          # Curious vs Conventional
    CONSCIENTIOUSNESS = "conscientiousness"  # Organized vs Spontaneous
    EXTRAVERSION = "extraversion"  # Outgoing vs Reserved
    AGREEABLENESS = "agreeableness"  # Cooperative vs Competitive
    NEUROTICISM = "neuroticism"    # Anxious vs Stable


@dataclass
class PersonalityProfile:
    """
    Complete personality profile for inner voice generation.
    
    Values are 1-5 scale:
    1 = Very low (opposite trait dominant)
    3 = Balanced/neutral
    5 = Very high (trait dominant)
    """
    # Moral traits
    compassion: int = 3
    honesty: int = 3
    loyalty: int = 3
    justice: int = 3
    courage: int = 3
    
    # Personality dimensions
    openness: int = 3
    conscientiousness: int = 3
    extraversion: int = 3
    agreeableness: int = 3
    neuroticism: int = 3
    
    # Internal motivation
    primary_drive: str = ""  # What fundamentally motivates them
    core_fear: str = ""      # What they fear most
    core_desire: str = ""    # What they want most
    
    def get_moral_outliers(self) -> List[Tuple[str, int, str]]:
        """Get moral traits that deviate from neutral (3)"""
        outliers = []
        moral_traits = [
            ('compassion', self.compassion),
            ('honesty', self.honesty),
            ('loyalty', self.loyalty),
            ('justice', self.justice),
            ('courage', self.courage)
        ]
        
        for trait, value in moral_traits:
            if value != 3:
                direction = "high" if value > 3 else "low"
                outliers.append((trait, value, direction))
        
        return sorted(outliers, key=lambda x: abs(x[1] - 3), reverse=True)
    
    def get_personality_outliers(self) -> List[Tuple[str, int, str]]:
        """Get personality dimensions that deviate from neutral"""
        outliers = []
        dimensions = [
            ('openness', self.openness),
            ('conscientiousness', self.conscientiousness),
            ('extraversion', self.extraversion),
            ('agreeableness', self.agreeableness),
            ('neuroticism', self.neuroticism)
        ]
        
        for dim, value in dimensions:
            if value != 3:
                direction = "high" if value > 3 else "low"
                outliers.append((dim, value, direction))
        
        return sorted(outliers, key=lambda x: abs(x[1] - 3), reverse=True)


# ═══════════════════════════════════════════════════════════════════════════════
# GOAL SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

class GoalPriority(Enum):
    """Goal priority levels"""
    IMMEDIATE = "immediate"    # Right now, this moment
    SHORT_TERM = "short_term"  # Today, this scene
    MEDIUM_TERM = "medium_term"  # This week, this arc
    LONG_TERM = "long_term"    # Life goals, overarching


@dataclass
class Goal:
    """A single goal with context"""
    description: str
    priority: GoalPriority
    motivation: str = ""  # Why this goal matters
    obstacles: List[str] = field(default_factory=list)
    progress: float = 0.0  # 0-1 completion
    emotional_weight: float = 0.5  # How much it affects inner voice
    
    def is_relevant_to_context(self, context: str) -> bool:
        """Check if this goal is relevant to current context"""
        context_lower = context.lower()
        desc_lower = self.description.lower()
        
        # Check for keyword overlap
        goal_words = set(desc_lower.split())
        context_words = set(context_lower.split())
        
        overlap = goal_words & context_words
        return len(overlap) >= 2 or any(word in context_lower for word in goal_words if len(word) > 4)


@dataclass
class GoalSet:
    """Collection of goals for an actor"""
    goals: List[Goal] = field(default_factory=list)
    
    def get_by_priority(self, priority: GoalPriority) -> List[Goal]:
        """Get goals of a specific priority"""
        return [g for g in self.goals if g.priority == priority]
    
    def get_most_relevant(self, context: str, max_goals: int = 2) -> List[Goal]:
        """Get goals most relevant to current context"""
        relevant = [g for g in self.goals if g.is_relevant_to_context(context)]
        
        # Sort by emotional weight and priority
        priority_order = {
            GoalPriority.IMMEDIATE: 0,
            GoalPriority.SHORT_TERM: 1,
            GoalPriority.MEDIUM_TERM: 2,
            GoalPriority.LONG_TERM: 3
        }
        
        relevant.sort(key=lambda g: (priority_order[g.priority], -g.emotional_weight))
        return relevant[:max_goals]
    
    def add_goal(self, goal: Goal):
        """Add a goal to the set"""
        self.goals.append(goal)
    
    def remove_goal(self, description: str):
        """Remove a goal by description"""
        self.goals = [g for g in self.goals if g.description != description]


# ═══════════════════════════════════════════════════════════════════════════════
# SITUATIONAL CUE SYSTEM
# ═══════════════════════════════════════════════════════════════════════════════

@dataclass
class SituationalCue:
    """A trigger for inner voice content"""
    trigger_keywords: List[str]
    trait_or_goal: str  # Which trait/goal this triggers
    response_template: str  # Template for inner voice
    cooldown_turns: int = 3  # Minimum turns before reuse
    last_triggered: int = -100  # Turn number when last triggered


class SituationalCueSystem:
    """
    Manages situational cues for inner voice.
    
    Key principle: Maximum 1 personality/goal tidbit per response.
    Waits for relevant situational triggers rather than constant prompting.
    """
    
    def __init__(self):
        self.cues: List[SituationalCue] = []
        self.current_turn: int = 0
        self.last_triggered_cue: Optional[str] = None
        
        # Initialize default cues
        self._init_default_cues()
    
    def _init_default_cues(self):
        """Initialize default situational cues"""
        # Moral cues
        self.cues.extend([
            SituationalCue(
                trigger_keywords=["help", "hurt", "suffering", "pain", "injured"],
                trait_or_goal="compassion",
                response_template="compassion_response",
                cooldown_turns=5
            ),
            SituationalCue(
                trigger_keywords=["lie", "truth", "honest", "deceive", "secret"],
                trait_or_goal="honesty",
                response_template="honesty_response",
                cooldown_turns=5
            ),
            SituationalCue(
                trigger_keywords=["betray", "loyal", "trust", "friend", "ally"],
                trait_or_goal="loyalty",
                response_template="loyalty_response",
                cooldown_turns=5
            ),
            SituationalCue(
                trigger_keywords=["fair", "unfair", "justice", "wrong", "deserve"],
                trait_or_goal="justice",
                response_template="justice_response",
                cooldown_turns=5
            ),
            SituationalCue(
                trigger_keywords=["danger", "risk", "afraid", "brave", "coward"],
                trait_or_goal="courage",
                response_template="courage_response",
                cooldown_turns=5
            ),
        ])
        
        # Goal-related cues
        self.cues.extend([
            SituationalCue(
                trigger_keywords=["money", "debt", "pay", "afford", "cost"],
                trait_or_goal="financial_goal",
                response_template="financial_response",
                cooldown_turns=4
            ),
            SituationalCue(
                trigger_keywords=["family", "home", "mother", "father", "child"],
                trait_or_goal="family_goal",
                response_template="family_response",
                cooldown_turns=4
            ),
            SituationalCue(
                trigger_keywords=["work", "job", "boss", "career", "promotion"],
                trait_or_goal="career_goal",
                response_template="career_response",
                cooldown_turns=4
            ),
        ])
    
    def check_triggers(self, context: str, 
                       personality: PersonalityProfile,
                       goals: GoalSet) -> Optional[Dict[str, Any]]:
        """
        Check if any situational cues are triggered by current context.
        
        Returns at most ONE triggered cue (anti-bloat measure).
        """
        context_lower = context.lower()
        triggered = []
        
        for cue in self.cues:
            # Check cooldown
            if self.current_turn - cue.last_triggered < cue.cooldown_turns:
                continue
            
            # Check if any trigger keywords match
            if any(keyword in context_lower for keyword in cue.trigger_keywords):
                triggered.append(cue)
        
        if not triggered:
            return None
        
        # Select one cue (prioritize moral traits, then goals)
        # Also consider which hasn't been triggered recently
        triggered.sort(key=lambda c: c.last_triggered)
        selected_cue = triggered[0]
        
        # Mark as triggered
        selected_cue.last_triggered = self.current_turn
        self.last_triggered_cue = selected_cue.trait_or_goal
        
        # Generate response data
        return self._generate_cue_response(selected_cue, personality, goals, context)
    
    def _generate_cue_response(self, cue: SituationalCue,
                                personality: PersonalityProfile,
                                goals: GoalSet,
                                context: str) -> Dict[str, Any]:
        """Generate inner voice content for triggered cue"""
        trait = cue.trait_or_goal
        
        # Check if it's a moral trait
        moral_value = getattr(personality, trait, None)
        if moral_value is not None:
            return {
                'type': 'moral_trait',
                'trait': trait,
                'value': moral_value,
                'direction': 'high' if moral_value > 3 else 'low' if moral_value < 3 else 'neutral',
                'intensity': abs(moral_value - 3),
                'context': context[:100]
            }
        
        # Check if it's a goal trigger
        if trait.endswith('_goal'):
            relevant_goals = goals.get_most_relevant(context, max_goals=1)
            if relevant_goals:
                goal = relevant_goals[0]
                return {
                    'type': 'goal',
                    'goal': goal.description,
                    'priority': goal.priority.value,
                    'motivation': goal.motivation,
                    'emotional_weight': goal.emotional_weight,
                    'context': context[:100]
                }
        
        return {
            'type': 'generic',
            'trait': trait,
            'context': context[:100]
        }
    
    def advance_turn(self):
        """Advance the turn counter"""
        self.current_turn += 1


# ═══════════════════════════════════════════════════════════════════════════════
# INNER VOICE GENERATOR
# ═══════════════════════════════════════════════════════════════════════════════

# Response templates for different trait levels
MORAL_RESPONSE_TEMPLATES = {
    'compassion': {
        5: ["My heart aches for them.", "I can't just stand by.", "Someone has to help."],
        4: ["That's rough. Maybe I could...", "Poor soul.", "I should do something."],
        2: ["Not my problem.", "They'll figure it out.", "Can't save everyone."],
        1: ["Weakness. They brought it on themselves.", "Survival of the fittest.", "Why should I care?"]
    },
    'honesty': {
        5: ["The truth matters, even when it hurts.", "I won't lie about this.", "Deception poisons everything."],
        4: ["Better to be straight with them.", "Honesty is usually the best policy.", "I'd rather not deceive."],
        2: ["A little white lie won't hurt.", "They don't need to know everything.", "What they don't know..."],
        1: ["Truth is a tool, nothing more.", "Tell them what they want to hear.", "The lie serves me better."]
    },
    'loyalty': {
        5: ["I'd never betray them.", "We're in this together.", "My word is my bond."],
        4: ["I should stick by them.", "They've earned my trust.", "Can't abandon them now."],
        2: ["I have to look out for myself.", "Loyalty only goes so far.", "They'd do the same."],
        1: ["Everyone's expendable.", "Sentiment is weakness.", "I owe them nothing."]
    },
    'justice': {
        5: ["This isn't right. Someone has to fix it.", "They deserve better.", "Justice must be served."],
        4: ["That's not fair.", "There should be consequences.", "The system failed them."],
        2: ["Life isn't fair. Move on.", "Rules are for other people.", "Winners make their own justice."],
        1: ["Take what you can. Give nothing back.", "Fairness is a fairy tale.", "Power makes right."]
    },
    'courage': {
        5: ["Fear won't stop me.", "I've faced worse.", "Someone has to stand up."],
        4: ["I can do this.", "Deep breath. Push through.", "Courage isn't the absence of fear."],
        2: ["Maybe there's another way...", "Is this worth the risk?", "I should be careful."],
        1: ["Not worth dying for.", "Let someone else handle it.", "I need to get out of here."]
    }
}


class InternalVoiceGenerator:
    """
    Generates contextually appropriate internal voice content.
    
    Key principles:
    - Maximum 1 personality/goal tidbit per response
    - Waits for situational cues
    - Prioritizes internal personality and current goals
    - Anti-bloat through cooldowns and selective triggering
    """
    
    def __init__(self, personality: PersonalityProfile = None,
                 goals: GoalSet = None):
        self.personality = personality or PersonalityProfile()
        self.goals = goals or GoalSet()
        self.cue_system = SituationalCueSystem()
        self.recent_responses: List[str] = []  # Track to avoid repetition
    
    def generate_internal_voice(self, context: str, 
                              scene_description: str = "",
                              force_content: bool = False) -> Optional[str]:
        """
        Generate internal voice content for current context.
        
        Args:
            context: Current action/situation context
            scene_description: Full scene for additional context
            force_content: If True, always generate something
        
        Returns:
            Internal voice string or None if no relevant cue triggered
        """
        full_context = f"{context} {scene_description}"
        
        # Check for triggered cues
        cue_data = self.cue_system.check_triggers(
            full_context, self.personality, self.goals
        )
        
        if not cue_data and not force_content:
            return None
        
        # Generate response based on cue type
        if cue_data:
            if cue_data['type'] == 'moral_trait':
                response = self._generate_moral_response(cue_data)
            elif cue_data['type'] == 'goal':
                response = self._generate_goal_response(cue_data)
            else:
                response = self._generate_generic_response(cue_data)
        else:
            # Force content - use most relevant goal or strongest trait
            response = self._generate_fallback_response(full_context)
        
        # Avoid repetition
        if response in self.recent_responses:
            return None
        
        self.recent_responses.append(response)
        if len(self.recent_responses) > 10:
            self.recent_responses.pop(0)
        
        return response
    
    def _generate_moral_response(self, cue_data: Dict) -> str:
        """Generate response based on moral trait"""
        trait = cue_data['trait']
        value = cue_data['value']
        
        templates = MORAL_RESPONSE_TEMPLATES.get(trait, {})
        
        # Get appropriate templates for this value
        if value >= 4:
            options = templates.get(5, []) + templates.get(4, [])
        elif value <= 2:
            options = templates.get(1, []) + templates.get(2, [])
        else:
            return ""  # Neutral - no strong inner voice
        
        if options:
            return random.choice(options)
        return ""
    
    def _generate_goal_response(self, cue_data: Dict) -> str:
        """Generate response based on goal"""
        goal = cue_data['goal']
        motivation = cue_data.get('motivation', '')
        weight = cue_data.get('emotional_weight', 0.5)
        
        # Higher emotional weight = more intense response
        if weight >= 0.7:
            templates = [
                f"This could help with {goal}...",
                f"I can't forget about {goal}.",
                f"Everything comes back to {goal}.",
            ]
        else:
            templates = [
                f"Maybe this relates to {goal}.",
                f"I should keep {goal} in mind.",
                f"This might affect {goal}.",
            ]
        
        return random.choice(templates)
    
    def _generate_generic_response(self, cue_data: Dict) -> str:
        """Generate generic inner voice response"""
        return ""  # Don't force generic content
    
    def _generate_fallback_response(self, context: str) -> str:
        """Generate fallback when forced but no cue triggered"""
        # Use strongest moral outlier
        moral_outliers = self.personality.get_moral_outliers()
        if moral_outliers:
            trait, value, direction = moral_outliers[0]
            templates = MORAL_RESPONSE_TEMPLATES.get(trait, {})
            options = templates.get(value, [])
            if options:
                return random.choice(options)
        
        # Use most important goal
        if self.goals.goals:
            goal = self.goals.goals[0]
            return f"I need to focus on {goal.description}."
        
        return ""
    
    def advance_turn(self):
        """Advance turn counter for cooldown tracking"""
        self.cue_system.advance_turn()
    
    def set_personality(self, personality: PersonalityProfile):
        """Update personality profile"""
        self.personality = personality
    
    def add_goal(self, goal: Goal):
        """Add a goal"""
        self.goals.add_goal(goal)
    
    def remove_goal(self, description: str):
        """Remove a goal"""
        self.goals.remove_goal(description)


# ═══════════════════════════════════════════════════════════════════════════════
# INTEGRATION HELPERS
# ═══════════════════════════════════════════════════════════════════════════════

def create_personality_from_sheet(actor_sheet) -> PersonalityProfile:
    """
    Create a PersonalityProfile from an ActorSheet.
    
    Maps S-traits and personality_traits to the profile.
    """
    profile = PersonalityProfile()
    
    # Try to get personality traits from sheet
    if hasattr(actor_sheet, 'personality_traits'):
        traits = actor_sheet.personality_traits
        if isinstance(traits, dict):
            # Map internal personality to moral traits
            internal = traits.get('internal', '')
            if internal:
                # Parse internal personality for moral indicators
                internal_lower = internal.lower()
                
                if any(word in internal_lower for word in ['kind', 'caring', 'empathetic']):
                    profile.compassion = 4
                elif any(word in internal_lower for word in ['cold', 'callous', 'indifferent']):
                    profile.compassion = 2
                
                if any(word in internal_lower for word in ['honest', 'truthful', 'sincere']):
                    profile.honesty = 4
                elif any(word in internal_lower for word in ['deceptive', 'manipulative', 'cunning']):
                    profile.honesty = 2
                
                if any(word in internal_lower for word in ['loyal', 'devoted', 'faithful']):
                    profile.loyalty = 4
                elif any(word in internal_lower for word in ['selfish', 'opportunistic']):
                    profile.loyalty = 2
                
                if any(word in internal_lower for word in ['just', 'fair', 'principled']):
                    profile.justice = 4
                elif any(word in internal_lower for word in ['ruthless', 'exploitative']):
                    profile.justice = 2
                
                if any(word in internal_lower for word in ['brave', 'bold', 'fearless']):
                    profile.courage = 4
                elif any(word in internal_lower for word in ['cautious', 'timid', 'fearful']):
                    profile.courage = 2
    
    # Map S-traits to personality dimensions
    if hasattr(actor_sheet, 's_factors'):
        s_factors = actor_sheet.s_factors
        if s_factors:
            try:
                from actor_sheet import SFactorType
                # Sociability maps to extraversion
                sociability = s_factors.get_factor(SFactorType.SOCIABILITY)
                profile.extraversion = sociability
                
                # Smarts maps to openness
                smart = s_factors.get_factor(SFactorType.SMARTS)
                profile.openness = smart
                
            except Exception:
                pass
    
    return profile


def create_goals_from_sheet(actor_sheet) -> GoalSet:
    """
    Create a GoalSet from an ActorSheet.
    
    Extracts goals from sheet data.
    """
    goals = GoalSet()
    
    # Try to get goals from sheet
    if hasattr(actor_sheet, 'goals'):
        sheet_goals = actor_sheet.goals
        if isinstance(sheet_goals, list):
            for i, goal_text in enumerate(sheet_goals[:5]):  # Max 5 goals
                priority = GoalPriority.SHORT_TERM if i < 2 else GoalPriority.MEDIUM_TERM
                goals.add_goal(Goal(
                    description=goal_text,
                    priority=priority,
                    emotional_weight=0.7 - (i * 0.1)
                ))
    
    # Try to get current objective
    if hasattr(actor_sheet, 'current_objective'):
        obj = actor_sheet.current_objective
        if obj:
            goals.add_goal(Goal(
                description=obj,
                priority=GoalPriority.IMMEDIATE,
                emotional_weight=0.9
            ))
    
    return goals


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS FOR INTEGRATION
# ═══════════════════════════════════════════════════════════════════════════════

# Global generator cache
_voice_generators: Dict[str, InternalVoiceGenerator] = {}


class InternalVoiceSystem:
    """
    Singleton-style system for managing internal voice across actors.
    """
    
    @staticmethod
    def get_generator(actor_id: str, actor_sheet=None) -> InternalVoiceGenerator:
        """Get or create an internal voice generator for an actor"""
        if actor_id not in _voice_generators:
            if actor_sheet:
                personality = create_personality_from_sheet(actor_sheet)
                goals = create_goals_from_sheet(actor_sheet)
            else:
                personality = PersonalityProfile()
                goals = GoalSet()
            
            _voice_generators[actor_id] = InternalVoiceGenerator(personality, goals)
        
        return _voice_generators[actor_id]
    
    @staticmethod
    def clear_generator(actor_id: str):
        """Remove a generator from cache"""
        if actor_id in _voice_generators:
            del _voice_generators[actor_id]


def get_internal_voice_cue(actor_id: str, context: str, 
                           actor_sheet=None) -> Optional[str]:
    """
    Get an internal voice cue for the given context.
    
    This is the main integration point - call this after each action
    to potentially get an internal voice response.
    
    Args:
        actor_id: The actor's ID
        context: Current narrative context/situation
        actor_sheet: Optional ActorSheet for personality extraction
    
    Returns:
        Internal voice string or None if not triggered
    """
    generator = InternalVoiceSystem.get_generator(actor_id, actor_sheet)
    return generator.generate_internal_voice(context)


def should_trigger_voice_cue(context: str, personality: PersonalityProfile = None,
                              goals: GoalSet = None) -> bool:
    """
    Check if the current context should trigger an internal voice cue.
    
    Uses keyword matching against personality traits and goals.
    """
    if not context:
        return False
    
    context_lower = context.lower()
    
    # Check for goal-related triggers
    if goals:
        for goal in goals.get_active_goals():
            # Check if context mentions goal-related keywords
            goal_words = goal.description.lower().split()
            if any(word in context_lower for word in goal_words if len(word) > 3):
                return True
    
    # Check for personality-related triggers
    if personality:
        # Moral dilemma triggers
        moral_triggers = [
            'help', 'hurt', 'lie', 'truth', 'steal', 'give',
            'betray', 'protect', 'abandon', 'save', 'kill',
            'honest', 'cheat', 'fair', 'unfair', 'right', 'wrong'
        ]
        if any(trigger in context_lower for trigger in moral_triggers):
            return True
    
    # Emotional triggers
    emotional_triggers = [
        'fear', 'angry', 'sad', 'happy', 'love', 'hate',
        'remember', 'remind', 'family', 'friend', 'enemy'
    ]
    if any(trigger in context_lower for trigger in emotional_triggers):
        return True
    
    return False


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Internal Voice System Test\n")
    
    # Create test personality
    personality = PersonalityProfile(
        compassion=4,  # High compassion
        honesty=2,     # Low honesty (deceptive)
        loyalty=5,     # Very high loyalty
        courage=3,     # Neutral courage
        justice=4      # High justice
    )
    
    # Create test goals
    goals = GoalSet()
    goals.add_goal(Goal(
        description="pay off my debt to the syndicate",
        priority=GoalPriority.SHORT_TERM,
        motivation="They'll hurt my family if I don't",
        emotional_weight=0.9
    ))
    goals.add_goal(Goal(
        description="find out who killed my brother",
        priority=GoalPriority.LONG_TERM,
        motivation="Justice for family",
        emotional_weight=0.8
    ))
    
    # Create generator
    generator = InternalVoiceGenerator(personality, goals)
    
    # Test scenarios
    test_contexts = [
        "You see a homeless man shivering in the cold.",
        "The boss asks you to lie about the shipment.",
        "Your friend is in danger and needs help.",
        "You find a wallet full of cash on the ground.",
        "The debt collector mentions your family.",
        "Someone mentions your brother's name.",
        "You're offered a bribe to look the other way.",
    ]
    
    print("=== Internal Voice Responses ===\n")
    for context in test_contexts:
        print(f"Context: {context}")
        response = generator.generate_internal_voice(context)
        if response:
            print(f"  Internal Voice: {response}")
        else:
            print(f"  (No internal voice triggered)")
        generator.advance_turn()
        print()
    
    print("✅ Internal voice system ready!")
