"""
Internal Voice Exchange System - Morality Compass

The Internal Voice is now an entity that the UA can have exchanges with.
It acts as a morality compass based on the actor's internal personality.
Appears during extreme scenarios when actions go against or align with personality.
Can shift spirit positively and negatively through exchanges.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any, Tuple
from enum import Enum
import random


class PersonalityConflictType(Enum):
    """Types of personality conflicts that trigger Internal Voice"""
    AGAINST_INTERNAL = "against_internal"  # Action goes against internal personality
    FOR_INTERNAL = "for_internal"  # Action aligns with internal personality
    AGAINST_EXTERNAL = "against_external"  # Action contradicts external persona
    FOR_EXTERNAL = "for_external"  # Action reinforces external persona
    IDENTITY_CRISIS = "identity_crisis"  # Severe misalignment between internal/external
    EXTREME_ALIGNMENT = "extreme_alignment"  # Perfect alignment, reinforcing self


class SpiritImpactDirection(Enum):
    """Direction of spirit impact"""
    POSITIVE = "positive"  # Affirming, empowering, calming
    NEGATIVE = "negative"  # Distressing, destabilizing, corrupting
    NEUTRAL = "neutral"  # Contemplative, questioning


class UAInputType(Enum):
    """How the UA responded to the Internal Voice"""
    DIALOGUE = "dialogue"         # Verbal or mental response
    PHYSICAL_ACTION = "physical"  # Physical behavioral response (ignore, continue, walk away)
    MIXED = "mixed"               # Both verbal response AND physical action


@dataclass
class PersonalityConflict:
    """Represents a conflict between action and personality"""
    conflict_type: PersonalityConflictType
    internal_trait: str
    action_description: str
    severity: float  # 0.0 to 1.0
    trigger_reason: str
    
    
@dataclass
class InternalVoiceExchangeTurn:
    """A single turn in the Internal Voice exchange"""
    step: int  # 1-6
    speaker: str  # "internal_voice" or "ua"
    content: str  # What is said
    spirit_impact_pending: bool = False  # Whether this turn contributes to spirit impact
    input_type: Optional[Any] = None    # UAInputType for UA turns — how they responded
    perceptual_description: str = ""    # Narrated physical action description, if any


@dataclass
class InternalVoiceExchange:
    """A complete 6-step exchange between UA and Internal Voice"""
    turns: List[InternalVoiceExchangeTurn] = field(default_factory=list)
    spirit_impact: SpiritImpactDirection = SpiritImpactDirection.NEUTRAL
    impact_magnitude: float = 0.0
    personality_trait_referenced: str = ""
    completed: bool = False
    

@dataclass
class SpiritState:
    """Tracks the UA's spirit state"""
    current_level: float = 0.0  # -10.0 (corrupted/broken) to +10.0 (enlightened/whole)
    stability: float = 1.0  # 0.0 to 1.0, how resistant to change
    dominant_aspect: str = ""  # Which personality aspect is dominant
    
    def apply_impact(self, direction: SpiritImpactDirection, magnitude: float):
        """Apply a spirit impact directly (magnitude already calculated as ceil(|diff|/2))"""
        if direction == SpiritImpactDirection.POSITIVE:
            self.current_level = min(10.0, self.current_level + magnitude)
        elif direction == SpiritImpactDirection.NEGATIVE:
            self.current_level = max(-10.0, self.current_level - magnitude)
        # Neutral impacts provide stability
        
    def get_spirit_description(self) -> str:
        """Get a natural-language description of current spirit state"""
        if self.current_level >= 7:
            return "You feel deeply at peace with who you are."
        elif self.current_level >= 4:
            return "You feel a strong sense of yourself."
        elif self.current_level >= 1:
            return "You feel at peace with yourself."
        elif self.current_level > -1:
            return "Something inside you is still searching."
        elif self.current_level > -4:
            return "You feel the weight of the contradiction inside you."
        elif self.current_level > -7:
            return "You feel fractured. The pieces of who you are don't quite fit together."
        else:
            return "Something inside you has gone very quiet."


class InternalVoiceExchangeSystem:
    """
    System for managing exchanges between UA and their Internal Voice.
    Acts as a morality compass based on personality.
    """
    
    def __init__(self, storage_dir: Optional[str] = None):
        self.storage_dir = storage_dir
        self.spirit_states: Dict[str, SpiritState] = {}  # actor_id -> SpiritState
        self.exchange_history: List[Dict[str, Any]] = []
        
        # Initialize LLM client for dynamic Internal Voice generation
        try:
            from openrouter_config import create_role_client, OpenRouterConfig
            self.client = create_role_client("narration")
            self.model = OpenRouterConfig.get_model_for_role("narration")
            self.use_llm = True
        except Exception:
            self.client = None
            self.model = None
            self.use_llm = False
        
    def get_or_create_spirit_state(self, actor_id: str) -> SpiritState:
        """Get or create spirit state for an actor"""
        if actor_id not in self.spirit_states:
            self.spirit_states[actor_id] = SpiritState()
        return self.spirit_states[actor_id]
    
    def detect_personality_conflict(
        self, 
        actor,
        action_description: str,
        internal_personality: str,
        external_personality: str
    ) -> Optional[PersonalityConflict]:
        """
        Detect if an action creates a personality conflict.
        Returns conflict details if detected, None otherwise.
        """
        # TODO: Implement LLM-based detection
        # For now, use keyword-based heuristics
        
        conflict = None
        severity = 0.0
        
        # Check for internal personality conflicts
        if internal_personality:
            # Example: "fear of becoming a monster again"
            if any(word in action_description.lower() for word in ['kill', 'hurt', 'violence', 'cruel']):
                if 'monster' in internal_personality.lower() or 'violence' in internal_personality.lower():
                    conflict = PersonalityConflict(
                        conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
                        internal_trait=internal_personality,
                        action_description=action_description,
                        severity=0.8,
                        trigger_reason=f"Action risks awakening feared aspects: {internal_personality}"
                    )
            
            # Check for alignment with internal personality (POSITIVE scenarios)
            positive_keywords = {
                'protect': ['protector', 'guardian', 'defender', 'shield'],
                'save': ['savior', 'rescuer', 'hero', 'protector'],
                'help': ['helper', 'care', 'compassion', 'kindness'],
                'kind': ['kindness', 'compassion', 'gentle', 'care'],
                'spare': ['mercy', 'compassion', 'forgiveness'],
                'defend': ['protector', 'guardian', 'defender'],
                'heal': ['healer', 'care', 'mend', 'restore'],
                'comfort': ['comfort', 'care', 'soothe'],
                'honest': ['truth', 'honesty', 'integrity'],
                'sacrifice': ['selfless', 'giving', 'noble']
            }
            
            for action_word, personality_traits in positive_keywords.items():
                if action_word in action_description.lower():
                    if any(trait in internal_personality.lower() for trait in personality_traits):
                        conflict = PersonalityConflict(
                            conflict_type=PersonalityConflictType.FOR_INTERNAL,
                            internal_trait=internal_personality,
                            action_description=action_description,
                            severity=0.7,
                            trigger_reason=f"Action deeply aligns with core values: {internal_personality}"
                        )
                        return conflict
            
            # Check for violence/killing (NEGATIVE scenarios)
            violence_keywords = ['kill', 'murder', 'slaughter', 'execute', 'beat', 'torture', 'cruel', 'merciless']
            if any(word in action_description.lower() for word in violence_keywords):
                # Check if personality fears becoming a monster/violent
                if any(word in internal_personality.lower() for word in ['monster', 'violence', 'killer', 'beast', 'darkness', 'animal', 'savage', 'brute']):
                    conflict = PersonalityConflict(
                        conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
                        internal_trait=internal_personality,
                        action_description=action_description,
                        severity=0.9,
                        trigger_reason=f"Violent action threatens to awaken feared aspects: {internal_personality}"
                    )
                    return conflict
                # Check if personality values peace/non-violence
                if any(word in internal_personality.lower() for word in ['peace', 'pacifist', 'gentle', 'healer', 'kind', 'compassion']):
                    conflict = PersonalityConflict(
                        conflict_type=PersonalityConflictType.AGAINST_INTERNAL,
                        internal_trait=internal_personality,
                        action_description=action_description,
                        severity=0.8,
                        trigger_reason=f"Violent action betrays core identity: {internal_personality}"
                    )
                    return conflict
        
        return conflict
    
    def should_trigger_internal_voice_exchange(
        self,
        actor,
        action_description: str,
        scene_context: str,
        is_extreme_scenario: bool = False
    ) -> bool:
        """
        Determine if an action should trigger an Internal Voice exchange.
        Only triggers during extreme scenarios or significant personality conflicts.
        """
        # Get personality info
        internal_personality = ""
        external_personality = ""
        
        if hasattr(actor, 'sheet'):
            if hasattr(actor.sheet, 'personality_traits'):
                internal_personality = actor.sheet.personality_traits.get('internal', '')
                external_personality = actor.sheet.personality_traits.get('external', '')
            elif hasattr(actor.sheet, 'personality_profile') and hasattr(actor.sheet.personality_profile, 'internal'):
                internal_personality = getattr(actor.sheet.personality_profile, 'internal', '')
                external_personality = getattr(actor.sheet.personality_profile, 'external', '')
        
        # Must have personality defined
        if not internal_personality:
            return False
        
        # Check for personality conflict
        conflict = self.detect_personality_conflict(
            actor, action_description, internal_personality, external_personality
        )
        
        if conflict:
            # Only trigger if severity is high enough (extreme scenarios)
            if conflict.severity >= 0.6 or is_extreme_scenario:
                return True
        
        return False
    
    def _generate_llm_iv_response(
        self,
        conflict_type: PersonalityConflictType,
        internal_personality: str,
        external_personality: str,
        ua_previous_response: str,
        step: int,
        completed_action: str,
        input_type=None,
        perceptual_description: str = ""
    ) -> Optional[str]:
        """
        Generate a dynamic Internal Voice response using LLM.
        Returns None if LLM call fails to allow fallback to hard-coded templates.
        """
        if not self.use_llm or not self.client:
            return None
        
        # Map conflict type to tone/context
        conflict_descriptions = {
            PersonalityConflictType.AGAINST_INTERNAL: (
                "The user has acted against their internal nature/personality. "
                "This is a moment of realization where their action conflicts with who they truly are inside. "
                "The Internal Voice should challenge, question, or confront them about this misalignment."
            ),
            PersonalityConflictType.FOR_INTERNAL: (
                "The user has acted in perfect alignment with their internal nature/personality. "
                "This is a moment of realization where their action affirms who they truly are inside. "
                "The Internal Voice should affirm, celebrate, or deepen their understanding of this alignment."
            ),
            PersonalityConflictType.AGAINST_EXTERNAL: (
                "The user's external persona/mask they show the world has cracked or slipped. "
                "This is a moment of realization where their true self peeked through the performance. "
                "The Internal Voice should observe this with curiosity, noting the gap between mask and face."
            ),
            PersonalityConflictType.FOR_EXTERNAL: (
                "The user's external persona/mask they show the world performed perfectly. "
                "This is a moment of realization where the role they play was executed flawlessly. "
                "The Internal Voice should question whether the mask has become indistinguishable from the face."
            ),
            PersonalityConflictType.IDENTITY_CRISIS: (
                "The user is experiencing severe misalignment between their internal nature and external persona. "
                "This is a moment of crisis where who they are and who they pretend to be have diverged dangerously. "
                "The Internal Voice should highlight this fracture and demand they choose which self to become."
            ),
            PersonalityConflictType.EXTREME_ALIGNMENT: (
                "The user has achieved perfect alignment between internal nature and external persona. "
                "This is a rare moment of wholeness where mask and face, inside and outside, agree completely. "
                "The Internal Voice should affirm this integration and help them remember this feeling."
            )
        }
        
        conflict_context = conflict_descriptions.get(
            conflict_type, 
            "The user has acted in a way that triggers deep self-reflection."
        )
        
        # Determine emotional tone based on step and conflict type
        if step == 3:
            step_context = (
                "This is the SECOND exchange (Step 3). The Internal Voice is reacting to the user's "
                "initial realization/response. It should acknowledge what they said, challenge their "
                "stance, and push deeper into the truth. Be conversational and responsive."
            )
        elif step == 5:
            step_context = (
                "This is the FINAL exchange (Step 5). The Internal Voice should deliver the ultimate truth "
                "based on the conversation so far. This is the culminating insight that will resonate "
                "with the user. Be profound, memorable, and transformative."
            )
        else:
            return None  # Only use LLM for steps 3 and 5
        
        # Build response-type context based on how the UA responded
        if input_type is not None and input_type == UAInputType.PHYSICAL_ACTION:
            response_type_context = (
                f"**HOW THEY RESPONDED:**\n"
                f"The person did NOT engage verbally. Instead they responded PHYSICALLY: \"{ua_previous_response}\"\n"
                + (f"Physical description: {perceptual_description}\n" if perceptual_description else "")
                + "React to their BEHAVIOR, not their words. The avoidance or action IS the message. "
                "They may be suppressing the reflection, escaping it, or expressing silently through movement."
            )
        elif input_type is not None and input_type == UAInputType.MIXED:
            response_type_context = (
                f"**HOW THEY RESPONDED:**\n"
                f"They responded both in words AND physically: \"{ua_previous_response}\"\n"
                + (f"Physical description: {perceptual_description}\n" if perceptual_description else "")
                + "React to both. Note if the physical action contradicts or reinforces what they said."
            )
        else:
            response_type_context = (
                f"**HOW THEY RESPONDED:**\n"
                f"They responded with words: \"{ua_previous_response}\""
            )

        prompt = f"""You are the Internal Voice of a person engaged in deep self-reflection after an extreme action.

**CONTEXT:**
{conflict_context}

**STEP CONTEXT:**
{step_context}

**PERSONALITY DETAILS:**
- Internal Nature: {internal_personality or "Unknown core self"}
- External Persona: {external_personality or "Unknown public face"}

**COMPLETED ACTION:**
{completed_action}

{response_type_context}

**YOUR TASK:**
Speak as the Internal Voice - the part of them that knows their true self. Use "we" and "us" to show you are part of them.

Requirements:
1. Respond directly to HOW they responded (words, behavior, or both)
2. Keep it to 1-2 sentences maximum
3. Be psychologically deep and emotionally resonant
4. Don't use flowery language - be raw and honest
5. If they acted physically to avoid the reflection, call it out — we don't disappear because they look away
6. Make it feel like a real conversation, not a monologue

Examples of good Internal Voice responses:
- "'Had to'? I've heard that before. Those words taste like ash in our mouth. Do you truly believe it, or are we hiding again?"
- "Moving away from this doesn't move us. We travel with you."
- "Yes. This is the peace that comes from alignment. When action and heart speak the same language."
- "The mask you wear grows thicker. Each denial buries us deeper. Soon there'll be nothing left to save."

Now generate the Internal Voice response:"""

        try:
            from openrouter_config import robust_llm_call, RetryConfig
            
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.8,
                max_tokens=150,
                max_retries=2,
                call_name="Internal Voice Response"
            )
            
            if response and response.strip():
                # Clean up response - remove quotes if present
                cleaned = response.strip().strip('"').strip("'")
                return cleaned
            
            return None
            
        except Exception:
            return None
    
    def generate_contextual_iv_response(
        self,
        conflict_type: PersonalityConflictType,
        internal_personality: str,
        ua_previous_response: str,
        step: int,
        completed_action: str,
        external_personality: str = "",
        input_type=None,
        perceptual_description: str = ""
    ) -> str:
        """
        Generate an Internal Voice response using LLM first, falling back to hard-coded templates.
        input_type (UAInputType) and perceptual_description let the IV react to physical actions.
        """
        # Try LLM-based dynamic generation first
        if step in [3, 5] and self.use_llm:
            llm_response = self._generate_llm_iv_response(
                conflict_type=conflict_type,
                internal_personality=internal_personality,
                external_personality=external_personality,
                ua_previous_response=ua_previous_response,
                step=step,
                completed_action=completed_action,
                input_type=input_type,
                perceptual_description=perceptual_description
            )
            if llm_response:
                return llm_response

        # Fall back to hard-coded templates
        return self._generate_template_iv_response(
            conflict_type=conflict_type,
            internal_personality=internal_personality,
            ua_previous_response=ua_previous_response,
            step=step,
            completed_action=completed_action,
            external_personality=external_personality,
            input_type=input_type
        )
    
    def _generate_template_iv_response(
        self,
        conflict_type: PersonalityConflictType,
        internal_personality: str,
        ua_previous_response: str,
        step: int,
        completed_action: str,
        external_personality: str = "",
        input_type=None
    ) -> str:
        """
        Generate an Internal Voice response using hard-coded templates.
        Kept as fallback when LLM is unavailable.
        input_type (UAInputType) allows physical-action-aware responses.
        """
        import re as _re
        ua_response_lower = ua_previous_response.lower()

        # Use word-boundary matching to avoid false positives from substrings
        # (e.g. 'is' inside 'mission', 'right' inside 'alright').
        def _has_word(text, keywords):
            return any(_re.search(r'\b' + _re.escape(kw) + r'\b', text) for kw in keywords)

        # Detect UA stance from their response
        defensive_keywords    = ['had to', 'no choice', 'forced', 'necessary', 'defend', 'protect']
        accepting_keywords    = ['yes', 'right', 'accept', 'admit', 'true', 'agree', 'know']
        defiant_keywords      = ['no', 'wrong', 'never', 'refuse', 'deny', 'disagree', 'reject']
        rationalizing_keywords = ['but', 'however', 'because', 'though', 'although', 'if']

        is_defensive    = _has_word(ua_response_lower, defensive_keywords)
        is_accepting    = _has_word(ua_response_lower, accepting_keywords)
        is_defiant      = _has_word(ua_response_lower, defiant_keywords)
        is_rationalizing = _has_word(ua_response_lower, rationalizing_keywords)

        # Physical action stances
        is_ignoring  = _has_word(ua_response_lower, ['ignore', 'dismiss', "don't care", 'not listen', 'block', 'shut out'])
        is_avoiding  = _has_word(ua_response_lower, ['walk away', 'leave', 'continue', 'keep going', 'carry on', 'move on', 'press on', 'step away'])
        is_physically_acting = (
            (input_type is not None and input_type == UAInputType.PHYSICAL_ACTION)
            or is_ignoring or is_avoiding
        )
        
        if conflict_type == PersonalityConflictType.AGAINST_INTERNAL:
            if step == 3:  # Reacting to UA's initial response
                if is_physically_acting:
                    if is_ignoring:
                        return "Acting as though we aren't here doesn't make us less present. The avoidance itself is an answer."
                    elif is_avoiding:
                        return "Moving away from this doesn't move it. Every step you take, we take with you."
                    else:
                        return "Busy hands are an old refuge. But the stillness waiting beneath doesn't go anywhere."
                elif is_defensive:
                    return "'Had to'? I've heard that before. Those words taste like ash in our mouth. Do you truly believe it, or are we hiding again?"
                elif is_accepting:
                    return "At least you don't hide from it. We both know what this cost. The question is whether we can afford the debt."
                elif is_defiant:
                    return "Anger won't wash the stain. We built walls precisely to keep this out. Now we invite it in?"
                elif is_rationalizing:
                    return "Words upon words to dress it up. The beast doesn't care for our clever reasons. It only knows hunger."
                else:
                    return "You say that, yet I feel the doubt beneath. We swore paths that didn't lead here. What happened to that promise?"

            elif step == 5:  # Final IV truth based on conversation
                if is_physically_acting:
                    if is_ignoring:
                        return "The silence between us is not peace. Avoidance is its own kind of answer, and we heard it clearly."
                    else:
                        return "All the motion in the world can't outrun the stillness waiting beneath. We'll still be here when it stops."
                elif is_defiant:
                    return "The mask you wear grows thicker. Each denial buries us deeper. Soon there'll be nothing left to save."
                elif is_accepting:
                    return "Honesty hurts, but lies would hollow us out. We carry this weight together. Never forget what it feels like."
                elif is_defensive:
                    return "'Had to' again. Necessity becomes habit becomes nature. Watch it doesn't become us permanently."
                elif is_rationalizing:
                    return "Every reason named is another stone in the wall between us. Reasoning your way out leads nowhere when it's your own self you're fleeing."
                else:
                    return "We've walked this edge before. The fall awaits if we forget who we were meant to be. Remember. Always remember."
        
        elif conflict_type == PersonalityConflictType.FOR_INTERNAL:
            if step == 3:
                if is_physically_acting:
                    return "Even in silence, you feel it — the rightness of what was done. The body already understood before the mind could argue."
                elif is_accepting:
                    return "Yes. This is the peace that comes from alignment. When action and heart speak the same language."
                elif is_defensive:
                    return "Still guarding yourself even in victory? It's safe to acknowledge when we do right. Let this warmth in."
                else:
                    return "You feel it too, don't you? The rightness singing in our chest. This is who we are when we choose well."

            elif step == 5:
                if is_physically_acting:
                    return "The action doesn't need narration. What was done speaks for both of us. Carry that knowledge."
                return "Hold this moment. Let it become part of our foundation. We are building something worthy here."
        
        elif conflict_type == PersonalityConflictType.IDENTITY_CRISIS:
            if step == 3:
                if is_physically_acting:
                    return "Moving away from the question doesn't dissolve it. The fracture travels with us."
                return "Your words split in two directions. Which of them is truly yours? The mask speaks, but whose voice answers?"
            elif step == 5:
                if is_physically_acting:
                    return "No distance is enough from a split that lives inside. The choice still waits, exactly where you left it."
                return "The fracture won't heal on its own. We must choose which self to become, or be torn apart by both."

        elif conflict_type == PersonalityConflictType.AGAINST_EXTERNAL:
            # The external persona cracked — the IV observes with curiosity, not condemnation
            ext = external_personality or "the face you show the world"
            if step == 3:
                if is_physically_acting:
                    return f"Putting distance between yourself and this moment doesn't reseal the mask. The crack is already there."
                elif is_defiant:
                    return f"Denying the crack doesn't seal it. {ext} has a dent now. Pretending otherwise only makes the next blow worse."
                elif is_accepting:
                    return f"You feel exposed. Good. Beneath that performance lives someone realer. Today they stepped forward."
                elif is_defensive:
                    return f"Embarrassed? The vulnerability you showed is not weakness. That persona was always a shield. Perhaps the arrow found the gap."
                elif is_rationalizing:
                    return f"Explaining why the mask slipped is still wearing the mask. The moment of truth doesn't need commentary."
                else:
                    return f"That wasn't the performance you rehearsed. Something genuine came through. Sit with that, before you cover it again."
            elif step == 5:
                if is_physically_acting:
                    return f"All the activity in the world won't restore what was shown. Decide what to do with that truth instead."
                elif is_defiant:
                    return f"The crack in the mask terrifies you. But what would happen if you let them see the real face entirely?"
                elif is_accepting:
                    return f"You let something true through. The world didn't end. Perhaps {ext} was never as necessary as you believed."
                elif is_defensive:
                    return f"A momentary slip, you say. Or is it that the armor grew too heavy? Even walls need maintenance."
                elif is_rationalizing:
                    return f"Context and circumstance — a careful argument. The feeling underneath doesn't care about your arguments."
                else:
                    return f"The mask and face can coexist. But only if you acknowledge both. What was shown today deserves honest inspection."

        elif conflict_type == PersonalityConflictType.FOR_EXTERNAL:
            # The external persona performed perfectly — IV questions whether the mask has eaten the face
            ext = external_personality or "the face you show the world"
            if step == 3:
                if is_physically_acting:
                    return f"Even in motion, the question follows. Played the role perfectly — but is the player still in there?"
                elif is_accepting:
                    return f"Comfortable in the role, aren't you. The question isn't whether you played {ext} well. It's whether the part still fits the player."
                elif is_defensive:
                    return f"It felt right because it was familiar. But familiarity and rightness are not the same. The groove runs deep."
                elif is_defiant:
                    return f"Of course — it's who you are. Or who you decided to be. The distinction matters, even when it's uncomfortable."
                elif is_rationalizing:
                    return f"Justification wraps it in logic. But you didn't act from logic. You acted from role. Interesting difference."
                else:
                    return f"The persona held perfectly. Long enough in the role and the original face becomes the understudy."
            elif step == 5:
                if is_physically_acting:
                    return f"The self that performs and the self that moves — are they the same one? The answer matters."
                elif is_defiant:
                    return f"Wear it proudly, then. Just remember who chose {ext} and why. That choice can always be revisited."
                elif is_accepting:
                    return f"At least you're honest about the performance. That self-awareness is the only real power here."
                elif is_defensive:
                    return f"Reaction becomes reflex becomes identity. Decide which of those you're comfortable being."
                elif is_rationalizing:
                    return f"All the reasons are real. And yet the person reciting them chose each one at some point."
                else:
                    return f"External consistency is a kind of truth. Just not the deepest kind. Make sure you remember the difference."

        elif conflict_type == PersonalityConflictType.EXTREME_ALIGNMENT:
            # Both internal and external aligned perfectly — affirming but weighty
            if step == 3:
                if is_physically_acting:
                    return "Even in motion you carry it with you. The wholeness is in the doing, not only in the words."
                elif is_defiant:
                    return "What is there to deny? You were entirely yourself. That is not a challenge — it is a gift. Few ever know this feeling."
                elif is_accepting:
                    return "Yes. This is what integration feels like. When no part of us is in hiding. The clarity is almost frightening in its completeness."
                elif is_defensive:
                    return "There is nothing to defend here. The action, the self, the face — all aligned. Why reach for justification when none is needed?"
                elif is_rationalizing:
                    return "No reasons are required. You acted from wholeness, not strategy. Let that be enough."
                else:
                    return "Listen to the silence where conflict usually lives. For once there is none. This is what alignment sounds like."
            elif step == 5:
                if is_physically_acting:
                    return "Carry this clarity forward. Every choice can move toward this alignment, or away from it. Now you know what alignment feels like in motion."
                elif is_defiant:
                    return "Your resistance makes no sense here. There is nothing to fight. The battle ended before it began."
                elif is_accepting:
                    return "Remember this feeling exactly. This is the benchmark. Every future choice is measured against this moment of wholeness."
                elif is_defensive:
                    return "There is nothing to protect against. For once the walls can come down. You are safe in yourself."
                elif is_rationalizing:
                    return "Stop explaining. The beauty of complete alignment is that it needs no justification. Simply exist in it."
                else:
                    return "Carry this clarity forward. Every choice can move toward this alignment, or away from it. Now you know the difference."

        # Default fallback
        if is_physically_acting:
            return "What the body does, the self must answer for eventually. We'll still be here when the motion stops."
        return "Listen to what you're truly saying. The truth lives between your words."

    # ── Physical action classification ──────────────────────────────────────

    _PHYSICAL_VERBS = {
        'ignore', 'dismiss', 'block', 'shut', 'suppress',
        'continue', 'keep', 'carry', 'press', 'resume',
        'walk', 'leave', 'step', 'move', 'run', 'flee', 'turn',
        'reach', 'grab', 'pick', 'put', 'place', 'hold', 'lift',
        'stand', 'sit', 'kneel', 'lean', 'rise',
        'nod', 'shake', 'shrug', 'cross', 'fold',
        'look', 'avert', 'glance', 'close', 'open',
        'breathe', 'sigh', 'exhale',
    }

    _COGNITIVE_VERBS = {
        'think', 'feel', 'believe', 'know', 'understand', 'realize',
        'wonder', 'consider', 'suppose', 'accept', 'agree', 'disagree',
        'refuse', 'admit', 'deny', 'acknowledge',
    }

    _STRONG_PHYSICAL_PHRASES = [
        'ignore', 'walk away', 'turn away', 'keep working', 'keep going',
        'move on', 'continue', 'carry on', 'dismiss', 'press on', 'look away',
        'step away', 'push it aside',
    ]

    def classify_ua_input(self, text: str) -> Tuple['UAInputType', float]:
        """
        Classify UA input as DIALOGUE, PHYSICAL_ACTION, or MIXED.
        Returns (UAInputType, confidence).
        Physical actions represent the UA acting in the world rather than engaging
        verbally with the IV — e.g. ignoring it, continuing what they were doing,
        walking away.
        """
        import re
        text_lower = text.strip().lower()

        # Speech/say verbs imply at least a dialogue component
        speech_verbs = {'say', 'tell', 'reply', 'respond', 'ask', 'speak', 'whisper', 'mutter'}
        has_speech = any(
            f' {v}' in text_lower or text_lower.startswith(v)
            for v in speech_verbs
        )

        # Check "I <verb>" pattern — the most common action form
        physical_detected = False
        cognitive_detected = False
        action_match = re.match(r"\bi\s+(\w+)", text_lower)
        if action_match:
            verb = action_match.group(1)
            if verb in self._PHYSICAL_VERBS:
                physical_detected = True
            elif verb in self._COGNITIVE_VERBS:
                cognitive_detected = True

        # Catch strong physical phrases even without explicit "I <verb>" pattern
        if any(phrase in text_lower for phrase in self._STRONG_PHYSICAL_PHRASES):
            physical_detected = True

        if physical_detected and has_speech:
            return (UAInputType.MIXED, 0.8)
        elif physical_detected and not cognitive_detected:
            return (UAInputType.PHYSICAL_ACTION, 0.85)
        else:
            return (UAInputType.DIALOGUE, 0.9)

    def generate_perceptual_description(
        self,
        action_text: str,
        scene_context: str = "",
        actor=None
    ) -> str:
        """
        Generate a brief 1-2 sentence second-person perceptual description of the
        UA's physical action during an IV exchange.  LLM-first, template fallback.
        """
        if self.use_llm and self.client:
            result = self._generate_llm_perceptual_description(action_text, scene_context, actor)
            if result:
                return result
        return self._template_perceptual_description(action_text)

    def _generate_llm_perceptual_description(
        self,
        action_text: str,
        scene_context: str = "",
        actor=None
    ) -> Optional[str]:
        """LLM-based perceptual description of a physical action."""
        if not self.use_llm or not self.client:
            return None

        prompt = f"""Generate a brief 1-2 sentence perceptual description of this physical action happening during an introspective moment.

Action: "{action_text}"
{f'Context: {scene_context}' if scene_context else ''}

Requirements:
- Write in second person ("You...")
- Sensory and concrete — what does this look and feel like?
- 1-2 sentences maximum
- Do NOT include any internal voice dialogue
- Do NOT explain motivations — only describe the physical beat
- Tone matches the weight of an introspective moment

Examples:
- "You turn back to the task at hand, hands finding their familiar rhythm, the voice dimming beneath the sounds around you."
- "Your eyes pull away, fixing on something neutral and distant. The motion of looking elsewhere feels like a small act of will."
- "You draw a slow breath, straighten your posture, and let the silence fill the space."

Generate the perceptual description:"""

        try:
            from openrouter_config import robust_llm_call
            response = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.7,
                max_tokens=80,
                max_retries=2,
                call_name="IV_Perceptual_Description"
            )
            if response and response.strip():
                cleaned = response.strip().strip('"').strip("'")
                if cleaned and cleaned[-1] not in '.!?':
                    cleaned += '.'
                return cleaned
            return None
        except Exception:
            return None

    def _template_perceptual_description(self, action_text: str) -> str:
        """Template perceptual description fallback."""
        a = action_text.lower()
        if any(w in a for w in ['ignore', 'dismiss', 'block', 'shut', 'not listen']):
            return "You push the thought to the edges of your attention, refocusing on what's in front of you."
        elif any(w in a for w in ['continue', 'keep working', 'keep going', 'carry on', 'resume', 'press on']):
            return "You return to what you were doing, hands and mind finding their rhythm again despite the undertow."
        elif any(w in a for w in ['walk away', 'leave', 'step away', 'move away', 'flee', 'run']):
            return "You put distance between yourself and the moment, though the thought follows at your heel."
        elif any(w in a for w in ['turn away', 'look away', 'avert']):
            return "Your gaze finds something else to rest on — anything but the place where the thought lives."
        elif any(w in a for w in ['nod', 'shake my head', 'shrug']):
            return "A small, involuntary motion. The body weighs in before the mind has decided what to say."
        elif any(w in a for w in ['reach', 'grab', 'pick up', 'hold', 'lift']):
            return "Your hands find something solid and tangible, an anchor outside the current of thought."
        elif any(w in a for w in ['breathe', 'sigh', 'exhale', 'inhale']):
            return "The breath moves through you deliberately, like a small act of ordering an interior grown turbulent."
        elif any(w in a for w in ['sit', 'stand', 'kneel', 'lean']):
            return "Your body shifts position, as though a new posture might change the quality of the silence."
        elif any(w in a for w in ['close', 'shut my eyes']):
            return "Your eyes close. Behind them the silence isn't empty — it has texture and weight."
        else:
            return "You move through the moment quietly, finding in action something the mind hasn't yet named."

    # ── Exchange generation ──────────────────────────────────────────────────

    def generate_6_step_internal_voice_exchange(
        self,
        actor,
        completed_action: str,
        action_result: str,
        conflict: PersonalityConflict
    ) -> InternalVoiceExchange:
        """
        Generate a full 6-step exchange between UA and Internal Voice.
        Steps 1,3,5 are IV; 2,4,6 are UA. IV responses are generated contextually.
        """
        # Get personality info
        internal_personality = ""
        external_personality = ""
        if hasattr(actor, 'sheet'):
            if hasattr(actor.sheet, 'personality_traits'):
                internal_personality = actor.sheet.personality_traits.get('internal', '')
                external_personality = actor.sheet.personality_traits.get('external', '')
            elif hasattr(actor.sheet, 'personality_profile') and hasattr(actor.sheet.personality_profile, 'internal'):
                internal_personality = getattr(actor.sheet.personality_profile, 'internal', '')
                external_personality = getattr(actor.sheet.personality_profile, 'external', '')

        # Determine spirit impact
        if conflict.conflict_type == PersonalityConflictType.AGAINST_INTERNAL:
            spirit_direction = SpiritImpactDirection.NEGATIVE
            impact_magnitude = conflict.severity
        elif conflict.conflict_type == PersonalityConflictType.FOR_INTERNAL:
            spirit_direction = SpiritImpactDirection.POSITIVE
            impact_magnitude = conflict.severity * 0.8
        elif conflict.conflict_type == PersonalityConflictType.IDENTITY_CRISIS:
            spirit_direction = SpiritImpactDirection.NEGATIVE
            impact_magnitude = conflict.severity * 1.2
        elif conflict.conflict_type == PersonalityConflictType.AGAINST_EXTERNAL:
            spirit_direction = SpiritImpactDirection.NEUTRAL
            impact_magnitude = conflict.severity * 0.6
        elif conflict.conflict_type == PersonalityConflictType.FOR_EXTERNAL:
            spirit_direction = SpiritImpactDirection.NEUTRAL
            impact_magnitude = conflict.severity * 0.5
        elif conflict.conflict_type == PersonalityConflictType.EXTREME_ALIGNMENT:
            spirit_direction = SpiritImpactDirection.POSITIVE
            impact_magnitude = conflict.severity * 1.0
        else:
            spirit_direction = SpiritImpactDirection.NEUTRAL
            impact_magnitude = 0.3

        # Step 1: Opening line based on conflict type
        if conflict.conflict_type == PersonalityConflictType.AGAINST_INTERNAL:
            opening = f"What have we done... {internal_personality} - does this not haunt you? The blood is on our hands now."
        elif conflict.conflict_type == PersonalityConflictType.FOR_INTERNAL:
            opening = f"We stood firm. {internal_personality} - this is who we are. The choice was hard, but right."
        elif conflict.conflict_type == PersonalityConflictType.IDENTITY_CRISIS:
            opening = f"Who are we becoming? The mask and face diverge dangerously. {internal_personality} - remember truth."
        elif conflict.conflict_type == PersonalityConflictType.AGAINST_EXTERNAL:
            opening = f"The face you show the world slipped just now. {internal_personality} - was that the truth beneath the mask, finally surfacing?"
        elif conflict.conflict_type == PersonalityConflictType.FOR_EXTERNAL:
            opening = f"The performance was flawless. {internal_personality} - the mask and the player moved as one. But which of them just acted?"
        elif conflict.conflict_type == PersonalityConflictType.EXTREME_ALIGNMENT:
            opening = f"No conflict. No fracture. {internal_personality} - inside and outside agreed completely. That clarity is rare. What do you feel?"
        else:
            opening = f"Consider carefully what this means for us, {internal_personality}."

        turns = [
            InternalVoiceExchangeTurn(step=1, speaker="internal_voice", content=opening, spirit_impact_pending=False),
            InternalVoiceExchangeTurn(step=2, speaker="ua", content="", spirit_impact_pending=False),
            InternalVoiceExchangeTurn(step=3, speaker="internal_voice", content="", spirit_impact_pending=False),  # Will be filled after UA responds
            InternalVoiceExchangeTurn(step=4, speaker="ua", content="", spirit_impact_pending=False),
            InternalVoiceExchangeTurn(step=5, speaker="internal_voice", content="", spirit_impact_pending=True),   # Will be filled after UA responds
            InternalVoiceExchangeTurn(step=6, speaker="ua", content="", spirit_impact_pending=True)
        ]

        exchange = InternalVoiceExchange(
            turns=turns,
            spirit_impact=spirit_direction,  # Will be recalculated based on success check
            impact_magnitude=impact_magnitude,  # Will be recalculated based on success check
            personality_trait_referenced=internal_personality,
            completed=False
        )
        
        # Store additional info for success calculation
        exchange.actor = actor
        exchange.conflict_type = conflict.conflict_type
        exchange.conflict_severity = conflict.severity
        exchange.completed_action = completed_action
        exchange.external_personality = external_personality
        
        return exchange

    def generate_step_3_response(
        self,
        exchange: InternalVoiceExchange,
        ua_step_2_response: str,
        input_type=None,
        perceptual_description: str = ""
    ) -> str:
        """Generate contextual IV response for step 3 based on UA's step 2.
        input_type (UAInputType) and perceptual_description allow the IV to react to physical actions.
        """
        return self.generate_contextual_iv_response(
            conflict_type=exchange.conflict_type,
            internal_personality=exchange.personality_trait_referenced,
            ua_previous_response=ua_step_2_response,
            step=3,
            completed_action=exchange.completed_action,
            external_personality=getattr(exchange, 'external_personality', ''),
            input_type=input_type,
            perceptual_description=perceptual_description
        )

    def generate_step_5_response(
        self,
        exchange: InternalVoiceExchange,
        ua_step_4_response: str,
        input_type=None,
        perceptual_description: str = ""
    ) -> str:
        """Generate contextual IV response for step 5 based on UA's step 4.
        input_type (UAInputType) and perceptual_description allow the IV to react to physical actions.
        """
        return self.generate_contextual_iv_response(
            conflict_type=exchange.conflict_type,
            internal_personality=exchange.personality_trait_referenced,
            ua_previous_response=ua_step_4_response,
            step=5,
            completed_action=exchange.completed_action,
            external_personality=getattr(exchange, 'external_personality', ''),
            input_type=input_type,
            perceptual_description=perceptual_description
        )

    def process_completed_exchange(
        self,
        actor_id: str,
        exchange: InternalVoiceExchange
    ) -> Tuple[str, float, str]:
        """
        Process a completed 6-step exchange with success check and apply spirit impact.
        Uses the existing calculate_unified_result formula.
        Returns (narrative_result, spirit_impact_applied, outcome).
        """
        spirit_state = self.get_or_create_spirit_state(actor_id)
        
        # Get actor and conflict info
        actor = getattr(exchange, 'actor', None)
        conflict_severity = getattr(exchange, 'conflict_severity', 0.7)
        conflict_type = getattr(exchange, 'conflict_type', PersonalityConflictType.AGAINST_INTERNAL)
        
        # Import and use the existing unified formula
        from unified_formula import calculate_unified_result
        from actor_sheet import SFactorType
        
        # UA success - use existing formula like any other action
        # STURDINESS represents the UA's resolve/conviction in the internal debate
        s_trait = SFactorType.STURDINESS
        
        ua_result = calculate_unified_result(
            actor=actor,
            s_trait=s_trait,
            skill_name="introspection",
            target_actor=None,
            shift_polarity="Subtractive",
            targeted_status=None,
            supplement_val=0,
            stress_level_override=int(3 + conflict_severity * 2)
        )
        ua_success = ua_result.get('final_result', 0)
        
        # IV success - IV is the actor's own inner voice, so it uses the actor's
        # SHADOW s-factor (self-awareness / hidden depths).  The moral weight of
        # the specific conflict is expressed as supplement_val (severity * 3,
        # capped at 3).  IV has no skill and no stress — it is pure inner gravity.
        iv_result = calculate_unified_result(
            actor=actor,
            s_trait=SFactorType.SHADOW,
            skill_name=None,
            target_actor=None,
            shift_polarity="Subtractive",
            targeted_status=None,
            supplement_val=int(conflict_severity * 3),
            stress_level_override=3,   # neutral — IV feels no external stress
        )
        iv_success = iv_result.get('final_result', 0)
        
        # Determine outcome
        difference = ua_success - iv_success
        
        if difference > 2:
            outcome = "ua_dominated"
        elif difference > 0:
            outcome = "ua_wins"
        elif difference > -2:
            outcome = "iv_wins"
        else:
            outcome = "iv_dominated"
        
        # Calculate spirit impact using exchange formula pattern: |difference|/2, round up
        import math
        base_magnitude = abs(difference) / 2
        magnitude = math.ceil(base_magnitude)
        
        direction = self._calculate_impact_direction(conflict_type, outcome)
        
        # Apply spirit impact
        spirit_state.apply_impact(direction, magnitude)
        
        # Apply status change based on debate outcome
        # Supports both real ActorSheet (uses .statuses dict) and simple mock objects (.status int)
        status_change = 0
        if actor and hasattr(actor, 'sheet'):
            sheet = actor.sheet
            # Real ActorSheet path: statuses is a dict[StatusType, Status]
            if hasattr(sheet, 'statuses') and isinstance(sheet.statuses, dict):
                try:
                    from actor_sheet import StatusType
                    spirit_obj = sheet.statuses.get(StatusType.SPIRIT)
                    if spirit_obj is not None:
                        if outcome in ["ua_dominated", "ua_wins"]:
                            status_change = 1
                            spirit_obj.modify(1)
                        else:
                            status_change = -1
                            spirit_obj.modify(-1)
                except Exception:
                    pass
            # Simple mock/legacy path: .status is a plain integer attribute
            elif hasattr(sheet, 'status') and isinstance(getattr(sheet, 'status'), int):
                if outcome in ["ua_dominated", "ua_wins"]:
                    status_change = 1
                    sheet.status = min(10, sheet.status + 1)
                else:
                    status_change = -1
                    sheet.status = max(-10, sheet.status - 1)
        
        # Generate full exchange display showing all 6 steps
        exchange_display = ""
        for turn in exchange.turns:
            if turn.speaker == "internal_voice":
                exchange_display += f"Inner Voice: {turn.content}\n\n"
            else:
                if turn.perceptual_description:
                    exchange_display += f"Perception: {turn.perceptual_description}\n"
                if turn.content:
                    exchange_display += f"You: {turn.content}\n\n"

        print(exchange_display)
        ua_pos = ua_result['positive_components']
        ua_neg = ua_result['negative_components']
        iv_pos = iv_result['positive_components']
        iv_neg = iv_result['negative_components']
        
        # Get spirit level before impact for display
        spirit_before = spirit_state.current_level - (magnitude if direction != SpiritImpactDirection.NEUTRAL else 0)
        if direction == SpiritImpactDirection.NEGATIVE:
            spirit_before = spirit_state.current_level + magnitude
        elif direction == SpiritImpactDirection.POSITIVE:
            spirit_before = spirit_state.current_level - magnitude
        
        # Generate narrative
        if outcome == "ua_dominated":
            narrative = f"You silenced the voice within. {spirit_state.get_spirit_description()}"
        elif outcome == "ua_wins":
            narrative = f"You held your ground. {spirit_state.get_spirit_description()}"
        elif outcome == "iv_wins":
            narrative = f"Something shifted inside you. {spirit_state.get_spirit_description()}"
        else:
            narrative = f"The voice within you would not be ignored. {spirit_state.get_spirit_description()}"
        
        # Record exchange
        self.exchange_history.append({
            'actor_id': actor_id,
            'turns': [{'step': t.step, 'speaker': t.speaker, 'content': t.content} for t in exchange.turns],
            'spirit_impact': direction.value,
            'impact_magnitude': magnitude,
            'new_spirit_level': spirit_state.current_level,
            'ua_success': ua_success,
            'iv_success': iv_success,
            'outcome': outcome,
            'status_change': status_change
        })
        
        exchange.completed = True
        
        return narrative, magnitude, outcome

    def _calculate_impact_magnitude(
        self,
        conflict_type: PersonalityConflictType,
        outcome: str,
        conflict_severity: float
    ) -> float:
        """Calculate magnitude of spirit impact based on conflict type and debate outcome."""
        ua_won = outcome in ("ua_dominated", "ua_wins")
        if conflict_type == PersonalityConflictType.AGAINST_INTERNAL:
            # UA held their ground → reduced blow; IV wins → full haunting weight
            return conflict_severity * (0.5 if ua_won else 1.0)
        elif conflict_type == PersonalityConflictType.FOR_INTERNAL:
            # Positive alignment — full uplift whether UA wins or not (action itself was right)
            return conflict_severity * 0.8
        elif conflict_type == PersonalityConflictType.IDENTITY_CRISIS:
            return conflict_severity * (0.6 if ua_won else 1.2)
        elif conflict_type == PersonalityConflictType.EXTREME_ALIGNMENT:
            return conflict_severity * 1.0  # full affirmation regardless of debate outcome
        else:
            return conflict_severity * (0.5 if ua_won else 0.8)

    def _calculate_impact_direction(
        self,
        conflict_type: PersonalityConflictType,
        outcome: str
    ) -> SpiritImpactDirection:
        """Calculate direction of spirit impact based on conflict type and debate outcome."""
        ua_won = outcome in ("ua_dominated", "ua_wins")
        if conflict_type == PersonalityConflictType.AGAINST_INTERNAL:
            return SpiritImpactDirection.NEGATIVE  # Always negative; magnitude differs
        elif conflict_type == PersonalityConflictType.FOR_INTERNAL:
            return SpiritImpactDirection.POSITIVE  # Always positive
        elif conflict_type == PersonalityConflictType.IDENTITY_CRISIS:
            return SpiritImpactDirection.NEUTRAL if ua_won else SpiritImpactDirection.NEGATIVE
        elif conflict_type in (PersonalityConflictType.FOR_EXTERNAL, PersonalityConflictType.AGAINST_EXTERNAL):
            return SpiritImpactDirection.POSITIVE if ua_won else SpiritImpactDirection.NEGATIVE
        elif conflict_type == PersonalityConflictType.EXTREME_ALIGNMENT:
            return SpiritImpactDirection.POSITIVE  # always positive — complete alignment affirms the self
        else:
            return SpiritImpactDirection.NEUTRAL

    def get_spirit_status(self, actor_id: str) -> Dict[str, Any]:
        """Get current spirit status for display"""
        spirit_state = self.get_or_create_spirit_state(actor_id)
        return {
            'level': spirit_state.current_level,
            'description': spirit_state.get_spirit_description(),
            'stability': spirit_state.stability
        }


# Global instance
_internal_voice_exchange_system: Optional[InternalVoiceExchangeSystem] = None


def get_internal_voice_exchange_system(storage_dir: Optional[str] = None) -> InternalVoiceExchangeSystem:
    """Get or create the global Internal Voice Exchange System"""
    global _internal_voice_exchange_system
    if _internal_voice_exchange_system is None:
        _internal_voice_exchange_system = InternalVoiceExchangeSystem(storage_dir)
    return _internal_voice_exchange_system


def reset_internal_voice_exchange_system():
    """Reset the global system (useful for testing)"""
    global _internal_voice_exchange_system
    _internal_voice_exchange_system = None
