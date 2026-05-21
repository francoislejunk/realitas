import json
import hashlib
import random
from typing import TYPE_CHECKING, Tuple, Dict, Any, Optional
from openrouter_config import OpenRouterConfig, create_role_client, retry_with_backoff, RetryConfig, robust_llm_call
from logbook.utas_logger import UTASLogger
from response_normalizer import ResponseNormalizer
from schemas.utas_action import validate_action_data
from enhanced_dynamic_actor_system import EnhancedDynamicActorDetector
from llm_agents.target_detection_system import TargetDetector
from numeric_utils import extract_numeric_value
from actor_sheet import StatusType, SFactorType
from json_utils import extract_and_parse_json
from color_utils import Color
from rule_of_3s import RuleOf3Classifier, RuleOf3Context, RuleOf3Category, RuleOf3TransitionManager
from action_type_detector import ActionTypeDetector, ActionCategory
from goal_task_system import GoalTaskInterpreter, TaskPriority, TaskCategory as GTTaskCategory
from time_cycle_system import TimeOfDay

try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except ImportError:
    WorldbuildingCategory = None

from rag_lock_utils import get_multi_category_context_for_llm
from rag_lock_utils import extract_rag_section_list_items

# Import canonical sensory constants for distance-based continuity checks
try:
    from sensory_constants import (
        SensoryCapabilities,
        get_distance_category,
        get_sensory_rules_for_distance,
        SENSORY_THRESHOLDS,
        DistanceCategory,
    )
    SENSORY_SYSTEM_AVAILABLE = True
except ImportError:
    SENSORY_SYSTEM_AVAILABLE = False

# Import spatial context for position-based continuity
try:
    from spatial_context_system import get_spatial_manager, Position
    SPATIAL_SYSTEM_AVAILABLE = True
except ImportError:
    SPATIAL_SYSTEM_AVAILABLE = False

if TYPE_CHECKING:
    from actors import Actor

class InterpreterAgent:
    """
    {{ ... }}
    The Interpreter Agent, responsible for interpreting user actions,
    enforcing continuity, and rolling for initiative in the simulation.
    """

    def __init__(self, logger: 'UTASLogger', scene_description: str, tracker_agent=None, actor_manager=None, key_memories_system=None, rag_system=None, fact_system=None, mention_system=None):
        self.logger = UTASLogger()
        self.scene_description = scene_description
        # Optional authoritative scene provider
        self.tracker_agent = tracker_agent
        self.key_memories_system = key_memories_system  # For memory-aware context
        self.rag_system = rag_system  # For worldbuilding context
        self.fact_system = fact_system  # For canonical facts
        self.mention_system = mention_system  # For actor mention tracking
        self.normalizer = ResponseNormalizer()
        self.dynamic_detector = EnhancedDynamicActorDetector(actor_manager) if actor_manager else None
        self.target_detector = TargetDetector()
        self.client = create_role_client("action_interpretation")
        self.model = OpenRouterConfig.get_model_for_role("action_interpretation")
        
        self.rule_of_3s_classifier = RuleOf3Classifier()
        self.rule_of_3s_manager = RuleOf3TransitionManager()
        self.current_rule_of_3s_context: Optional[RuleOf3Context] = None
        
        self.response_cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        # Optional, per-turn context snapshot (last action, recent updates) injected by Conductor
        self._ad_hoc_context_snapshot: Optional[str] = None
        
        # Initialize Goal/Task Interpreter
        self.time_context = None  # Will be set per action
        self.goal_task_interpreter = GoalTaskInterpreter(self.client, self.model)
        
        print("Interpreter Agent initialized with Rule of 3's system and Goal/Task Interpreter.")
        
        # Session ID for spatial context (will be set externally)
        self.session_id: Optional[str] = None

    def _get_actor_mention_context(self, actor_name: str, max_mentions: int = 5) -> str:
        """
        Get formatted mention context for an actor to inject into prompts.
        Shows where actor was last mentioned to prevent contradictions.

        Args:
            actor_name: The name of the actor
            max_mentions: Maximum number of recent mentions to include

        Returns:
            Formatted string with mention history, or empty string if unavailable
        """
        if not self.mention_system:
            return ""

        try:
            location, confidence = self.mention_system.get_last_known_location(actor_name)
            if location:
                return f"\n**MENTION HISTORY:** {actor_name} was last mentioned at {location} (confidence: {confidence.value})\n"
            return ""
        except Exception as e:
            self.logger.log_system(f"WARNING: Could not fetch mentions for {actor_name}: {e}")
            return ""

    def _extract_user_input_mentions(self, user_input: str, actor_name: str,
                                     turn_number: int = 0, scene_id: str = ""):
        """
        Extract actor mentions from user input using heuristic patterns.
        Tracks references to actors and locations in user commands.

        Args:
            user_input: The user's input text
            actor_name: The name of the user actor (speaker)
            turn_number: Current turn number
            scene_id: Current scene ID
        """
        if not self.mention_system or not user_input:
            return

        try:
            from mention_system import MentionType, MentionSource, PresenceConfidence

            input_lower = user_input.lower()

            # Pattern 1: "ask [Actor] about..." or "talk to [Actor]"
            # Inquiry mentions - user is asking about an actor
            inquiry_patterns = [
                "ask ", "talk to ", "speak to ", "tell ", "say to ",
                "question ", "inquire ", "chat with "
            ]
            for pattern in inquiry_patterns:
                if pattern in input_lower:
                    # Extract actor name after pattern
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):]
                    words = after_pattern.split()
                    if words:
                        # Get first capitalized word as potential actor name
                        for word in words[:3]:  # Check up to 3 words
                            clean_word = word.strip(".,!?\"'")
                            if clean_word and len(clean_word) > 1 and clean_word[0].isupper():
                                # Record INQUIRY mention
                                self.mention_system.record_mention(
                                    actor_name=clean_word,
                                    mention_type=MentionType.INQUIRY,
                                    location="Unknown",
                                    location_confidence=PresenceConfidence.MEDIUM,
                                    source=MentionSource.USER_INPUT,
                                    turn_number=turn_number,
                                    scene_id=scene_id,
                                    context=user_input[:200]
                                )
                                self.logger.log_system(f"Extracted INQUIRY mention: {actor_name} asked about {clean_word}")
                                break

            # Pattern 2: "go to [Location]" or "move to [Location]"
            # Intention mentions - user intends to go somewhere
            movement_patterns = [
                ("go to ", MentionType.INTENTION),
                ("move to ", MentionType.INTENTION),
                ("head to ", MentionType.INTENTION),
                ("walk to ", MentionType.INTENTION),
                ("run to ", MentionType.INTENTION),
                ("travel to ", MentionType.INTENTION),
            ]
            for pattern, mention_type in movement_patterns:
                if pattern in input_lower:
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):]
                    words = after_pattern.split()
                    if words:
                        # Get first word as location (may need refinement for multi-word locations)
                        location = words[0].strip(".,!?\"'")
                        if location and len(location) > 1:
                            # Record INTENTION mention for the UA going to location
                            self.mention_system.record_mention(
                                actor_name=actor_name,
                                mention_type=mention_type,
                                location=location,
                                location_confidence=PresenceConfidence.HIGH,
                                source=MentionSource.USER_INPUT,
                                turn_number=turn_number,
                                scene_id=scene_id,
                                context=user_input[:200]
                            )
                            self.logger.log_system(f"Extracted INTENTION mention: {actor_name} intends to go to {location}")
                            break

            # Pattern 3: "where is [Actor]?" or "have you seen [Actor]?"
            # Inquiry about actor location
            location_inquiry_patterns = [
                "where is ", "where's ", "have you seen ", "seen ",
                "do you know where ", "looking for "
            ]
            for pattern in location_inquiry_patterns:
                if pattern in input_lower:
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):]
                    words = after_pattern.split()
                    if words:
                        # Get first capitalized word as potential actor name
                        for word in words[:3]:
                            clean_word = word.strip(".,!?\"'")
                            if clean_word and len(clean_word) > 1 and clean_word[0].isupper():
                                # Record INQUIRY mention
                                self.mention_system.record_mention(
                                    actor_name=clean_word,
                                    mention_type=MentionType.INQUIRY,
                                    location="Unknown",
                                    location_confidence=PresenceConfidence.LOW,  # User doesn't know location
                                    source=MentionSource.USER_INPUT,
                                    turn_number=turn_number,
                                    scene_id=scene_id,
                                    context=user_input[:200]
                                )
                                self.logger.log_system(f"Extracted INQUIRY mention: {actor_name} asking about location of {clean_word}")
                                break

            # Pattern 4: Actor mentions in user dialogue (quoted speech)
            # Example: 'I tell him "Marcus sent me"'
            if '"' in user_input or "'" in user_input:
                # Extract text between quotes
                import re
                quoted_text = re.findall(r'["\']([^"\']+)["\']', user_input)
                for quote in quoted_text:
                    # Find capitalized words that might be actor names
                    words = quote.split()
                    for word in words:
                        clean_word = word.strip(".,!?\"'")
                        if clean_word and len(clean_word) > 2 and clean_word[0].isupper():
                            # Record MESSAGE mention (mentioned in user's speech)
                            self.mention_system.record_mention(
                                actor_name=clean_word,
                                mention_type=MentionType.MESSAGE,
                                location="Unknown",
                                location_confidence=PresenceConfidence.LOW,
                                source=MentionSource.USER_INPUT,
                                turn_number=turn_number,
                                scene_id=scene_id,
                                context=user_input[:200]
                            )
                            self.logger.log_system(f"Extracted MESSAGE mention: {clean_word} mentioned in {actor_name}'s dialogue")

        except Exception as e:
            self.logger.log_system(f"WARNING: Error extracting mentions from user input: {e}")

    def _extract_user_declarations(self, user_input: str, actor_name: str,
                                    turn_number: int = 0, scene_id: str = "") -> None:
        """
        Extract factual declarations from user input and establish as USER_ESTABLISHED facts.

        User declarations have highest authority and override all other facts.
        Examples: "I'm a doctor", "I own a red car", "I grew up in Chicago"

        Args:
            user_input: The user's input text
            actor_name: The actor performing the action (usually UA)
            turn_number: Current turn number
            scene_id: Current scene ID
        """
        if not self.fact_system or not user_input:
            return

        try:
            from fact_system import FactType, FactAuthority

            input_lower = user_input.lower()

            # Pattern: "I am a/an [occupation]" or "I'm a/an [occupation]"
            occupation_patterns = ["i am a ", "i am an ", "i'm a ", "i'm an ", "i work as ", "my job is "]
            for pattern in occupation_patterns:
                if pattern in input_lower:
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):]
                    # Take words until we hit sentence end or conjunction
                    words = []
                    for word in after_pattern.split():
                        clean_word = word.strip(".,!?\"'")
                        if clean_word.lower() in ['and', 'but', 'or', 'so']:
                            break
                        words.append(clean_word)
                        if len(words) >= 6:  # Reasonable max for occupation
                            break
                    occupation = " ".join(words)

                    if occupation and len(occupation) > 2:
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_IDENTITY,
                            subject=actor_name,
                            predicate="occupation",
                            value=occupation,
                            authority=FactAuthority.USER_ESTABLISHED,
                            source=f"user_declaration_{actor_name}",
                            tags=[actor_name.lower(), "occupation", "user_declared"],
                            turn_number=turn_number,
                            scene_id=scene_id,
                            context=user_input
                        )
                        self.logger.log_system(f"Extracted USER_ESTABLISHED fact: {actor_name} occupation = {occupation}")
                        break

            # Pattern: "I own [possession]" or "I have [possession]"
            possession_patterns = ["i own ", "i have ", "my "]
            for pattern in possession_patterns:
                if pattern in input_lower:
                    # Extract the possession mentioned
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):].split('.')[0]  # Get rest of sentence
                    possession = after_pattern.strip(".,!?\"'")

                    if possession and len(possession) > 2 and len(possession) < 100:
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_POSSESSION,
                            subject=actor_name,
                            predicate="owns",
                            value=possession,
                            authority=FactAuthority.USER_ESTABLISHED,
                            source=f"user_declaration_{actor_name}",
                            tags=[actor_name.lower(), "possession", "user_declared"],
                            turn_number=turn_number,
                            scene_id=scene_id,
                            context=user_input
                        )
                        self.logger.log_system(f"Extracted USER_ESTABLISHED fact: {actor_name} owns {possession}")
                        break

            # Pattern: "I'm from [location]" or "I grew up in [location]"
            origin_patterns = ["i'm from ", "i am from ", "i grew up in ", "i was born in "]
            for pattern in origin_patterns:
                if pattern in input_lower:
                    idx = input_lower.find(pattern)
                    after_pattern = user_input[idx + len(pattern):].split()[0:3]
                    location = " ".join(after_pattern).strip(".,!?\"'")

                    if location and len(location) > 2:
                        self.fact_system.establish_fact(
                            fact_type=FactType.ACTOR_TRAIT,
                            subject=actor_name,
                            predicate="origin",
                            value=location,
                            authority=FactAuthority.USER_ESTABLISHED,
                            source=f"user_declaration_{actor_name}",
                            tags=[actor_name.lower(), "origin", "location", "user_declared"],
                            turn_number=turn_number,
                            scene_id=scene_id,
                            context=user_input
                        )
                        self.logger.log_system(f"Extracted USER_ESTABLISHED fact: {actor_name} origin = {location}")
                        break

        except Exception as e:
            self.logger.log_system(f"Error extracting user declarations: {e}")

    def _validate_action_against_facts(self, user_input: str, actor_name: str) -> Optional[str]:
        """
        Validate user action against established facts.

        Returns warning message if action contradicts established facts, None otherwise.

        Args:
            user_input: The user's input text
            actor_name: The actor performing the action

        Returns:
            Warning message if contradiction found, None if valid
        """
        if not self.fact_system or not user_input:
            return None

        try:
            # Query facts about the actor
            actor_facts = self.fact_system.query_facts(subject=actor_name)
            if not actor_facts:
                return None

            input_lower = user_input.lower()

            # Check for occupation contradictions
            occupation_facts = [f for f in actor_facts if f.predicate == "occupation"]
            if occupation_facts:
                established_occupation = occupation_facts[0].value.lower()

                # Check if user is claiming a different occupation
                occupation_patterns = ["i am a ", "i am an ", "i'm a ", "i'm an ", "i work as ", "my job is "]
                for pattern in occupation_patterns:
                    if pattern in input_lower:
                        idx = input_lower.find(pattern)
                        after_pattern = user_input[idx + len(pattern):].split()[0:3]
                        stated_occupation = " ".join(after_pattern).strip(".,!?\"'").lower()

                        if stated_occupation and established_occupation not in stated_occupation and stated_occupation not in established_occupation:
                            return f"WARNING: You previously established that {actor_name} is a {occupation_facts[0].value}. Are you changing this?"

            # Check for possession contradictions
            possession_facts = [f for f in actor_facts if f.fact_type.value == "actor_possession"]
            for fact in possession_facts:
                value_lower = str(fact.value).lower()
                # Check if user is contradicting a possession ("I don't have X" when fact says they do)
                if "don't have" in input_lower or "do not have" in input_lower:
                    if any(keyword in input_lower for keyword in value_lower.split()):
                        return f"WARNING: Established fact says {actor_name} has/owns {fact.value}. Contradiction detected."

            return None

        except Exception as e:
            self.logger.log_system(f"Error validating action against facts: {e}")
            return None

    def _get_spatial_session_id(self) -> str:
        """Return the session_id to use for spatial context.

        Continuity checks rely on session-scoped spatial state. When resuming a
        saved session, any stale/default spatial manager can make every action
        fail (e.g. distance constraints).
        """
        try:
            sid = getattr(self, 'session_id', None)
            if sid:
                return str(sid)
        except Exception:
            pass
        try:
            sid = getattr(getattr(self, 'tracker_agent', None), 'session_id', None)
            if sid:
                return str(sid)
        except Exception:
            pass
        return "default"

    def _get_spatial_continuity_context(self, proactor_id: str, reactor_id: Optional[str] = None) -> str:
        """
        Get spatial context for continuity checking.
        
        Returns a formatted string describing:
        - Actor positions
        - Distances between actors
        - Sensory capabilities at those distances
        - Physical constraints based on distance
        
        Args:
            proactor_id: ID of the actor attempting the action
            reactor_id: ID of the target actor (if any)
        
        Returns:
            Formatted string for inclusion in continuity prompts
        """
        if not SPATIAL_SYSTEM_AVAILABLE or not SENSORY_SYSTEM_AVAILABLE:
            return ""
        
        try:
            spatial = get_spatial_manager(session_id=self._get_spatial_session_id())
            context = spatial.get_current_context()
            
            if not context:
                return ""
            
            proactor_pos = context.actor_positions.get(proactor_id)
            if not proactor_pos:
                return ""
            
            lines = ["\n**SPATIAL CONTEXT (Physical Constraints):**"]
            lines.append(f"- Proactor Position: ({proactor_pos.position.x:.1f}, {proactor_pos.position.y:.1f})")
            
            # If there's a reactor, calculate distance and sensory constraints
            if reactor_id:
                reactor_pos = context.actor_positions.get(reactor_id)
                if reactor_pos:
                    distance = proactor_pos.position.distance_to(reactor_pos.position)
                    category = get_distance_category(distance)
                    caps = SensoryCapabilities.at_distance(distance)
                    
                    lines.append(f"- Reactor Position: ({reactor_pos.position.x:.1f}, {reactor_pos.position.y:.1f})")
                    lines.append(f"- Distance: {distance:.1f} units ({category.value.upper()})")
                    lines.append("")
                    lines.append("**DISTANCE-BASED PHYSICAL CONSTRAINTS:**")
                    
                    # Touch constraints
                    if caps.can_touch:
                        lines.append("- TOUCH: Within arm's reach - physical contact POSSIBLE")
                    else:
                        lines.append(f"- TOUCH: Too far ({distance:.1f} > 2 units) - physical contact NOT POSSIBLE without moving closer")
                    
                    # Communication constraints
                    if caps.can_hear_whisper:
                        lines.append("- WHISPER: Can whisper and be heard")
                    elif caps.can_hear_speech:
                        lines.append("- SPEECH: Can speak normally but NOT whisper (too far)")
                    elif caps.can_hear_raised:
                        lines.append("- RAISED VOICE: Must raise voice to be heard (too far for normal speech)")
                    elif caps.can_hear_shout:
                        lines.append("- SHOUT: Must SHOUT to be heard (too far for raised voice)")
                    else:
                        lines.append("- HEARING: Out of hearing range - verbal communication NOT POSSIBLE")
                    
                    # Visual constraints
                    if caps.can_see_facial_detail:
                        lines.append("- SIGHT: Can see facial expressions and fine details")
                    elif caps.can_see_body_language:
                        lines.append("- SIGHT: Can see body language but NOT facial details")
                    elif caps.can_identify_person:
                        lines.append("- SIGHT: Can identify who they are but NOT see details")
                    elif caps.can_see_movement:
                        lines.append("- SIGHT: Can only see movement, not identify")
                    else:
                        lines.append("- SIGHT: Too far to see clearly")
                    
                    # Movement time estimate
                    walk_time = distance / 3.0  # Assuming 3 units/sec walking
                    lines.append(f"- MOVEMENT: Would take ~{walk_time:.1f}s to walk to reactor")
            
            # List other actors in scene
            other_actors = []
            for actor_id, actor_pos in context.actor_positions.items():
                if actor_id != proactor_id and actor_id != reactor_id:
                    dist = proactor_pos.position.distance_to(actor_pos.position)
                    other_actors.append(f"{actor_pos.actor_name} ({dist:.1f} units away)")
            
            if other_actors:
                lines.append(f"\n- Other actors present: {', '.join(other_actors)}")
            
            return "\n".join(lines)
            
        except Exception as e:
            # Fail silently - spatial context is optional
            return ""

    def _resolve_spatial_actor_id(self, actor: Optional['Actor'], fallback_id: Optional[str] = None) -> Optional[str]:
        """Resolve an actor's spatial actor_id for the current context.

        Spatial uses ids like ua_001 / nua_<slug>. Many Actor objects do not carry a stable
        actor_id attribute, so we resolve by:
        1) actor.actor_id if present
        2) provided fallback_id
        3) name match against context.actor_positions
        """
        if not SPATIAL_SYSTEM_AVAILABLE:
            return fallback_id
        try:
            if actor is None:
                return fallback_id

            candidate = getattr(actor, 'actor_id', None)
            if candidate:
                return str(candidate)

            if fallback_id:
                return str(fallback_id)

            name = (getattr(getattr(actor, 'sheet', None), 'name', None) or '').strip()
            if not name:
                return None

            spatial = get_spatial_manager(session_id=self._get_spatial_session_id())
            context = spatial.get_current_context()
            if not context:
                return fallback_id

            name_l = name.lower()
            for aid, apos in (context.actor_positions or {}).items():
                try:
                    an = (getattr(apos, 'actor_name', None) or '').strip().lower()
                    if an and an == name_l:
                        return str(aid)
                except Exception:
                    continue
            return None
        except Exception:
            return fallback_id
    
    def check_action_distance_feasibility(self, action_type: str, proactor_id: str, reactor_id: str) -> Tuple[bool, str]:
        """
        Check if an action is feasible based on distance.
        
        Args:
            action_type: Type of action ("touch", "whisper", "talk", "see_detail", etc.)
            proactor_id: ID of the actor attempting the action
            reactor_id: ID of the target actor
        
        Returns:
            Tuple of (is_feasible: bool, reason: str)
        """
        if not SPATIAL_SYSTEM_AVAILABLE or not SENSORY_SYSTEM_AVAILABLE:
            return (True, "")  # No spatial system, allow all
        
        try:
            spatial = get_spatial_manager(session_id=self.session_id)
            context = spatial.get_current_context()
            
            if not context:
                return (True, "")
            
            proactor_pos = context.actor_positions.get(proactor_id)
            reactor_pos = context.actor_positions.get(reactor_id)
            
            if not proactor_pos or not reactor_pos:
                return (True, "")
            
            distance = proactor_pos.position.distance_to(reactor_pos.position)
            caps = SensoryCapabilities.at_distance(distance)
            
            # Check based on action type
            checks = {
                "touch": (caps.can_touch, f"Too far to touch ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['touch']} units."),
                "punch": (caps.can_touch, f"Too far to punch ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['touch']} units."),
                "grab": (caps.can_touch, f"Too far to grab ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['touch']} units."),
                "whisper": (caps.can_hear_whisper, f"Too far to whisper ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['whisper']} units."),
                "talk": (caps.can_hear_speech, f"Too far for normal conversation ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['normal_speech']} units."),
                "see_detail": (caps.can_see_facial_detail, f"Too far to see details ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['facial_detail']} units."),
                "smell": (caps.can_smell_strong, f"Too far to smell ({distance:.1f} units). Need to be within {SENSORY_THRESHOLDS['smell_strong']} units."),
            }
            
            action_lower = action_type.lower()
            if action_lower in checks:
                can_do, reason = checks[action_lower]
                if not can_do:
                    return (False, reason)
            
            return (True, "")
            
        except Exception:
            return (True, "")  # Fail open
    
    def update_actor_tasks(self, user_action: str, actor: 'Actor', 
                          action_interpretation: Dict[str, Any] = None) -> None:
        """
        Dynamically update actor's tasks based on their action.
        This interprets the user's intent and updates the current task accordingly.
        
        Args:
            user_action: The raw user action text
            actor: The actor performing the action
            action_interpretation: Optional existing interpretation from interpret_user_action()
                                  to avoid redundant LLM calls
        """
        try:
            # Only update tasks for actors with the goal/task system
            if not hasattr(actor.sheet, 'goal_task_manager'):
                return
            
            # Get current context
            current_context = self.scene_description
            
            # Interpret the action for task updates, passing existing interpretation if available
            interpretation = self.goal_task_interpreter.interpret_action_for_tasks(
                user_action=user_action,
                current_context=current_context,
                goal_task_manager=actor.sheet.goal_task_manager,
                action_interpretation=action_interpretation  # Reuse existing interpretation
            )
            
            print(f"\n{Color.INFO}═══ Task Interpretation ═══{Color.RESET}")
            print(f"{Color.SYSTEM}Inferred Intent: {interpretation['inferred_intent']}{Color.RESET}")
            
            # Update current task if needed
            if interpretation.get('current_task_should_change') and interpretation.get('new_current_task'):
                new_task_data = interpretation['new_current_task']
                
                # Create the new task
                new_task = actor.sheet.add_task(
                    description=new_task_data['description'],
                    priority=TaskPriority(new_task_data['priority']),
                    category=GTTaskCategory(new_task_data['category']),
                    related_goal=new_task_data.get('related_goal')
                )
                
                # Set it as current
                actor.sheet.set_current_task(new_task)
            
            # Add any new tasks
            for new_task_data in interpretation.get('new_tasks_to_add', []):
                actor.sheet.add_task(
                    description=new_task_data['description'],
                    priority=TaskPriority(new_task_data['priority']),
                    category=GTTaskCategory(new_task_data['category']),
                    related_goal=new_task_data.get('related_goal')
                )
            
            # Complete tasks
            for task_desc in interpretation.get('tasks_to_complete', []):
                # Find and complete matching tasks
                for task in actor.sheet.goal_task_manager.get_active_tasks():
                    if task.description.lower() == task_desc.lower():
                        actor.sheet.complete_task(task)
                        break
            
            if interpretation.get('reasoning'):
                print(f"{Color.SYSTEM}Reasoning: {interpretation['reasoning']}{Color.RESET}")
            
            print(f"{Color.INFO}═══════════════════════════{Color.RESET}\n")
            
        except Exception as e:
            print(f"{Color.WARNING}Warning: Could not update tasks: {e}{Color.RESET}")
    
    def _refresh_scene_from_tracker(self) -> None:
        """Update self.scene_description from TrackerAgent if available."""
        try:
            if getattr(self, 'tracker_agent', None):
                try:
                    sid = getattr(self.tracker_agent, 'session_id', None)
                    if sid:
                        self.session_id = str(sid)
                except Exception:
                    pass
                latest = self.tracker_agent.get_current_scene() or {}
                latest_desc = latest.get('scene_description')
                if latest_desc:
                    self.scene_description = latest_desc
        except Exception:
            # Non-fatal: keep current scene_description
            pass
    
    def _estimate_dialogue_weight(self, user_text: str) -> int:
        """Lightweight heuristic: count sentence-like utterances as dialogue units.
        A full sentence ~ 3 seconds, per user guidance. Returns non-negative int.
        """
        try:
            if not user_text or not isinstance(user_text, str):
                return 0
            import re
            # Count sentences ending with . ! ? or enclosed quotes; conservative split
            parts = re.split(r"[.!?]+|\n+|\"\s*\"|\'\s*\'", user_text)
            count = sum(1 for p in parts if isinstance(p, str) and p.strip())
            return max(0, count)
        except Exception:
            return 0
    
    def _build_optimized_actor_data(self, actor: 'Actor') -> Dict[str, Any]:
        """Build minimal actor data for prompts to reduce token usage"""
        return {
            'name': actor.sheet.name,
            'skills': {k: v for k, v in actor.sheet.skills.items() if v > 0},
            'effects': [effect.name for effect in actor.sheet.effects] if hasattr(actor.sheet, 'effects') and actor.sheet.effects else [],
            'key_items': [item.name for item in actor.sheet.inventory[:3]]
        }
    
    def _build_detailed_actor_data(self, actor: 'Actor') -> Dict[str, Any]:
        """Build comprehensive actor data for detailed interpretation prompts - NUMERIC VALUES ONLY"""
        s_factors = {}
        for s_factor_type in [SFactorType.SWIFTNESS, SFactorType.SOCIABILITY, SFactorType.STURDINESS, SFactorType.SMARTS, SFactorType.SHADOW]:
            value = actor.sheet.s_factors.get_factor(s_factor_type)
            s_factors[s_factor_type.name.lower().capitalize()] = value
        
        skills = {}
        if actor.sheet.skills:
            for skill, skill_value in actor.sheet.skills.items():
                if skill_value > 0:
                    skills[skill] = skill_value
        
        endowments = {}
        if actor.sheet.endowments:
            for endowment_power, endowment_value in actor.sheet.endowments.items():
                if endowment_value > 0:
                    endowments[endowment_power] = endowment_value
        
        statuses = {}
        for status_type in [StatusType.STAMINA, StatusType.SPIRIT, StatusType.SUPPLY, StatusType.SYMPATHY]:
            if status_type in actor.sheet.statuses:
                status = actor.sheet.statuses[status_type]
                value = status.value
                modifier = status.get_modifier()
                statuses[status_type.name.lower().capitalize()] = {
                    'value': value,
                    'modifier': modifier
                }
        
        inventory = [f"{item.name} - {item.description}" for item in actor.sheet.inventory[:5]]
        
        return {
            'name': actor.sheet.name,
            's_factors': s_factors,
            'skills': skills if skills else {},
            'endowments': endowments if endowments else {},
            'inventory': inventory if inventory else ['No items'],
            'statuses': statuses
        }
    
    def _override_with_actor_sheet_values(self, utas_factors: Dict[str, Any], actor: 'Actor') -> None:
        """Override LLM-provided values with authoritative actor sheet values"""
        from actor_sheet import SFactorType
        
        # Override S-Trait value with actor sheet value
        s_trait_name = utas_factors.get('s_trait_to_use', '').lower()
        s_trait_mapping = {
            'swiftness': SFactorType.SWIFTNESS,
            'sociability': SFactorType.SOCIABILITY, 
            'sturdiness': SFactorType.STURDINESS,
            'smarts': SFactorType.SMARTS,
            'shadow': SFactorType.SHADOW
        }
        
        if s_trait_name in s_trait_mapping:
            s_trait_type = s_trait_mapping[s_trait_name]
            utas_factors['s_trait_value'] = actor.sheet.s_factors.get_factor(s_trait_type)
        else:
            # Fallback to Shadow if invalid
            utas_factors['s_trait_value'] = actor.sheet.s_factors.get_factor(SFactorType.SHADOW)
        
        # Override skill value with actor sheet value
        skill_data = utas_factors.get('skill', {})
        if isinstance(skill_data, dict) and 'name' in skill_data:
            skill_name = skill_data['name']
            if skill_name != 'none' and actor.sheet.skills:
                skill_value = actor.sheet.skills.get(skill_name, 0)
                utas_factors['skill'] = {'name': skill_name, 'value': skill_value}
        
        # Override endowment value with actor sheet value
        endowment_data = utas_factors.get('endowment', {})
        if isinstance(endowment_data, dict) and 'name' in endowment_data:
            endowment_name = endowment_data['name']
            if endowment_name != 'none' and actor.sheet.endowments:
                endowment_value = actor.sheet.endowments.get(endowment_name, 0)
                utas_factors['endowment'] = {'name': endowment_name, 'value': endowment_value}
        
        # Override supplement value with actor sheet calculation
        supplement_data = utas_factors.get('supplement', {})
        if isinstance(supplement_data, dict) and 'name' in supplement_data:
            supplement_name = supplement_data['name']
            if supplement_name != 'none':
                # Calculate total supplement bonus from actor sheet
                supplement_value = actor.sheet.get_total_supplement_bonus()
                utas_factors['supplement'] = {'name': supplement_name, 'value': supplement_value}
    
    
    def _build_continuity_prompt(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> str:
        """Build optimized continuity check prompt with consistent judgment format"""
        proactor_data = self._build_optimized_actor_data(proactor)
        scene_summary = self.scene_description[:300] + "..." if len(self.scene_description) > 300 else self.scene_description
        
        return f"""Continuity Check:
Scene: {scene_summary}
User: {proactor_data['name']} wants to "{user_input}"
Skills: {proactor_data['skills']}
Effects: {proactor_data['effects']}

Is this action possible? Return JSON: {{"judgment": "Possible"/"Not Possible", "justification": "reason"}}"""
    
    
    def _build_interpretation_prompt(self, user_action: str, proactor: 'Actor') -> str:
        """Build comprehensive action interpretation prompt for detailed UTAS analysis"""
        proactor_data = self._build_detailed_actor_data(proactor)
        ua_dialogue_weight = self._estimate_dialogue_weight(user_action)
        
        # Check if this is the User Actor for perspective instructions
        is_user_actor = getattr(proactor, 'is_user_actor', False)
        
        # Build perspective instruction based on actor type
        if is_user_actor:
            perspective_instruction = "Write in SECOND PERSON using you/your with correct verb forms (You make, you approach, your voice)."
        else:
            perspective_instruction = f"Write in THIRD PERSON using the actor name ({proactor_data['name']}) with third-person pronouns (he/she/they/their)."
        
        # Get recent narrative context for spatial/positional awareness
        recent_context = ""
        if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
            try:
                context_data = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=5, 
                    importance_threshold="notable"
                )
                if context_data and context_data.strip():
                    recent_context = f"""
**Recent Action Context (for spatial/positional awareness):**
{context_data}

**IMPORTANT:** Use this recent context to understand the character's current position, location, and any spatial changes from previous actions. If the character climbed somewhere, moved to a different area, or changed position, factor this into your interpretation."""
            except Exception as e:
                self.logger.log_system(f"Warning: Could not retrieve narrative context for action interpretation: {e}")
        
        # Get spatial proximity context from map
        spatial_proximity = ""
        try:
            from spatial_context_system import get_spatial_manager
            spatial = get_spatial_manager(session_id=self._get_spatial_session_id())
            actor_id = f"ua_{proactor.sheet.name.lower().replace(' ', '_')}" if getattr(proactor, 'is_user_actor', False) else f"nua_{proactor.sheet.name.lower().replace(' ', '_')}"
            proximity_data = spatial.get_proximity_context_for_llm(actor_id)
            if proximity_data:
                spatial_proximity = f"""

{proximity_data}

**SPATIAL RULES:**
- IMMEDIATE range: Can touch, whisper, grab, strike
- CLOSE range: Normal conversation, quick reach
- NEAR range: Need to raise voice, can move to quickly
- FAR range: Must shout, takes time to reach
- DISTANT: Cannot interact directly without moving closer first"""
        except Exception:
            pass
        # Integrate any ad-hoc context snapshot (last action + updates)
        snapshot_block = ""
        if getattr(self, '_ad_hoc_context_snapshot', None):
            try:
                snap = str(self._ad_hoc_context_snapshot).strip()
                if snap:
                    snapshot_block = f"""
**Recent Development Snapshot:**
{snap}
"""
            except Exception:
                snapshot_block = ""
        
        return f"""You are a UTAS simulation interpreter. Analyze the user's action and provide comprehensive mechanical breakdown.

**Scene Context:**
{self.scene_description}{recent_context}{snapshot_block}{spatial_proximity}

**Actor Details:**
Name: {proactor_data['name']}
S-Factors: {proactor_data['s_factors']}
Skills: {proactor_data['skills']}
Endowments: {proactor_data['endowments']}
Inventory: {proactor_data['inventory']}
Current Status: {proactor_data['statuses']}

**User Action:** "{user_action}"

**💬 DIALOGUE AS FULL UTAS ACTION (Not Just Metadata):**
- Estimated UA Dialogue Units: {ua_dialogue_weight} (1 unit ≈ 1 sentence ≈ 3 seconds)
- **Dialogue IS a contested action when it has conversational stakes:**
  - Persuasion attempt → SPIRIT exchange (trying to change their mind)
  - Negotiation → SUPPLY or SYMPATHY exchange (trading value/trust)
  - Insult/Provocation → SYMPATHY/Subtractive or SPIRIT/Subtractive
  - Encouragement/Support → SPIRIT/Additive or SYMPATHY/Additive
  - Interrogation/Questioning → SPIRIT exchange (extracting information vs. withholding)
  - Deception/Lying → SHADOW + Social skill vs. their SMARTS/Sociability
  
- **Trivial dialogue (phatic communication) has NO contested stakes:**
  - "Hello", "How's your day?", "Nice weather" → apply_shift=false
  - These are social lubricants, not attempts to change status
  
- **CRITICAL: Treat dialogue like any other action:**
  - If UA is trying to ACHIEVE something through speech → full UTAS mechanics
  - If UA is just being polite/casual → apply_shift=false
  - NUA will respond with their own conversational goals and interests
  - Success/failure determines if the conversational goal is achieved
  
- **DIALOGUE TYPE CLASSIFICATION:**
  - **Pure Dialogue (dialogue_only=true):** ONLY speaking, no physical action
    - Examples: "How's your day?", "I think we should leave", "Your mom's a bitch"
  - **Action + Dialogue (dialogue_only=false):** Speaking WHILE doing something
    - Examples: "Get out!" *while pushing*, "You can do this!" *while helping*, "Back off!" *while drawing weapon*
  
- **Conversational Flow Principles:**
  - NUA has their own topics of interest, goals, and conversational style
  - Multi-turn conversations should build on previous exchanges
  - NUA may steer conversation toward their own objectives
  - Sympathy level affects conversational cooperation (high sympathy = more helpful/engaged)

**🚨 SPATIAL CONTEXT AWARENESS CRITICAL INSTRUCTIONS 🚨**
**ALWAYS consider the character's current position and recent spatial changes when interpreting actions:**

**High-Risk Spatial Scenarios (Stress Level 4-5):**
- Jumping/falling from heights (roofs, buildings, cliffs, bridges)
- Actions involving significant elevation changes
- Movement in dangerous vertical spaces

**Spatial Keywords to Include in Descriptions:**
- Reference specific heights: "roof", "three-story", "30 feet", "building height"
- Acknowledge gravity/physics: "fall", "drop", "plummet", "impact"
- Describe spatial context: "from above", "down below", "height advantage"

**Example Spatial Interpretations:**
- "I jump off" (when on roof) → "Vincent attempts to jump off the three-story building roof, a dangerous 30-foot fall to the alley below" (Stress: 5)
- "I climb up" → "Vincent climbs the fire escape ladder to reach the rooftop" (Stress: 2-3)
- "I look around" (when elevated) → "Vincent surveys the area from his elevated position on the roof" (Stress: 1)

**IMPORTANT DISTINCTIONS:**
- **S-TRAITS (Actor Capabilities)**: Swiftness, Sociability, Sturdiness, Smarts, Shadow - These are the actor's inherent abilities
- **STATUSES (Dynamic Conditions)**: Stamina, Spirit, Supply, Sympathy - These are changeable conditions that can be targeted

**CRITICAL: YOU MUST PROVIDE ALL FIELDS LISTED BELOW. NO EXCEPTIONS.**
**INCOMPLETE RESPONSES WILL BE REJECTED AND CAUSE SYSTEM ERRORS.**

**Required Analysis:**
Provide a JSON response with EXACTLY the following structure:
{{
    "action_noun": "Brief action name",
    "action_description": "Detailed description of what the actor is attempting",
    "narrative_description": "Rich, immersive description of the action. **PERSPECTIVE: {perspective_instruction}** **🚨 CRITICAL DIALOGUE RULES - NEVER INVENT SPECIFIC WORDS 🚨:** (1) If user input contains QUOTED dialogue (e.g. 'I say \"Hello\"'), include those EXACT words verbatim. (2) If user input describes dialogue WITHOUT quotes (e.g. 'I ask what they are doing', 'I greet them', 'I tell them to leave'), this IS dialogue - describe it as speech but use their EXACT phrasing, not invented quotes. 'I ask what they're doing' → 'You ask what they're doing' (NOT 'You say \"What are you doing?\"'). (3) NEVER fabricate specific quoted words the user didn't provide. (4) You CAN add sensory details (tone, body language) but NOT invented dialogue content.",
    "utas_factors": {{
        "exchange_type": "Supply/Stamina/Spirit/Sympathy - what type of STATUS conflict this represents. **For physical attacks, this MUST be Stamina. For mental attacks/intimidation/threats, this MUST be Spirit.**", 
        "status_to_shift": "The target STATUS on the reactor (Stamina/Spirit/Supply/Sympathy)",
        "s_trait_to_use": "Primary S-TRAIT name (Swiftness/Sociability/Sturdiness/Smarts/Shadow)",
        "s_trait_value": "Numerical value of the S-TRAIT",
        "s_trait_justification": "Detailed explanation of why this S-TRAIT applies",
        "skill": {{"name": "skill_name", "value": skill_value}},
        "skill_justification": "Detailed explanation of how this skill applies to the action",
        "endowment": {{"name": "endowment_name", "value": endowment_value}},
        "endowment_justification": "Detailed explanation of how this endowment applies to the action",
        "supplement": {{"name": "supplement_name", "value": supplement_value}},
        "stress_level": "1-5 difficulty rating",
        "stress_justification": "Explanation of why this stress level applies",
        "shift_type": "Lasting/Temporary - permanence of the effect",
        "shift_type_justification": "Why this shift type applies",
        "shift_polarity": "Additive/Subtractive - direction of the effect",
        "shift_polarity_justification": "Why this polarity applies"
    }},
    "self_effects": [
    {{
        "condition": "Inherent Cost/On Action Success/On Action Failure - When does this self-effect occur?",
        "target_status": "STAMINA/SPIRIT/SUPPLY - Which of the Proactor's own Statuses is affected?",
        "polarity": "Additive/Subtractive - Does the Status increase or decrease?",
        "shift_type": "Lasting/Temporary - Is the effect persistent or fleeting?",
        "severity": "🚨 REQUIRED INTEGER 1-4 🚨 - How severe is this specific self-effect? NEVER leave this as null/None!",
        "severity_justification": "Explanation of severity calculation and any narrative adjustments",
        "description": "Brief narrative description of the self-inflicted effect"
    }}
],
    "dialogue_metadata": {{
        "dialogue_detected": true/false,
        "dialogue_intent": "SmallTalk/Inquiry/Persuasion/Threat/Insult/Command/Story/None",
        "dialogue_weight": {ua_dialogue_weight},
        "talk_time_seconds": 0,
        "can_affect_status": true/false,
        "apply_shift": true/false,
        "dialogue_only": true/false  // true = pure dialogue, false = action + dialogue
    }}
}}

**MANDATORY FIELD REQUIREMENTS:**
- **ALL UTAS_FACTORS FIELDS ARE REQUIRED** - You MUST provide every single field listed above
- **dialogue_metadata is OPTIONAL** - Only include if action contains dialogue elements

**EXCHANGE TYPE CLASSIFICATION:**
- **exchange_type**: MUST be one of: "Supply", "Stamina", "Spirit", "Sympathy"
  - **Stamina**: Physical attacks, bodily harm, exhaustion, physical damage
  - **Spirit**: Mental/social interactions, communication, conversation, phone calls, intimidation, threats, psychological pressure, morale damage, persuasion, information exchange
  - **Supply**: Money-related actions, resource theft, financial manipulation, material loss/gain, buying/selling, trading goods
  - **Sympathy**: Rapport building/destruction, relationship changes, social standing shifts, trust/distrust

**CRITICAL: Communication actions (talking, calling, messaging) are SPIRIT, NOT Supply - even when using technology like phones or screens**

**STATUS TARGET CLASSIFICATION:**
- **status_to_shift**: MUST be one of: "Stamina", "Spirit", "Supply", "Sympathy"
  - Choose the reactor's status that will be most directly affected by the action

**S-TRAIT SELECTION GUIDE:**
- **s_trait_to_use**: MUST be one of: "Swiftness", "Sociability", "Sturdiness", "Smarts", "Shadow"
  - **Swiftness**: Speed, agility, reflexes, quick movements, dodging, racing
  - **Sociability**: Social interaction, persuasion, leadership, charm, public speaking
  - **Sturdiness**: Physical strength, endurance, toughness, lifting, breaking things
  - **Smarts**: Intelligence, knowledge, problem-solving, strategy, technical skills
  - **Shadow**: Stealth, deception, sneaking, hiding, underhanded tactics
- **s_trait_value**: MUST be an integer 0-5 (look up the actual value from actor data above)

**SKILL/ENDOWMENT/SUPPLEMENT SELECTION CRITERIA:**
- **skill**: MUST be {{"name": "skill_name", "value": 2}} or {{"name": "None", "value": 0}}
  - Use ONLY skills that exist on the character sheet above
  - **Primary Selection**: Choose skills that directly relate to the action being performed
  - **Cross-Skill Applicability**: Skills can apply creatively if they logically enhance the action
  - **Examples of Direct Application**: "Combat" for fighting, "Athletics" for physical feats, "Social Fortitude" for resisting intimidation
  - **Examples of Cross-Skill Application**: 
    - "Acrobatics" for stealth actions (graceful, silent movement)
    - "Performance" for deception (acting ability enhances lying)
    - "Medicine" for intimidation (knowledge of anatomy makes threats more credible)
    - "Engineering" for combat (understanding of structural weaknesses)
    - "History" for social situations (cultural knowledge aids persuasion)
  - **Selection Priority**: 1) Direct match, 2) Creative cross-application, 3) Use {{"name": "None", "value": 0}}
  - **Justification Required**: Always explain HOW the skill applies to the specific action

- **endowment**: MUST be {{"name": "endowment_name", "value": 2}} or {{"name": "None", "value": 0}}
  - Use ONLY endowment abilities that exist on the character sheet above
  - Select powers that enhance or modify the action being performed
  - Examples: "Enhanced Strength" for physical actions, "Mind Reading" for social manipulation
  - If no relevant endowment power exists, use {{"name": "None", "value": 0}}

- **supplement**: MUST be {{"name": "item_name", "value": 2}} or {{"name": "None", "value": 0}}
  - Use ONLY items/equipment that exist in the character's inventory above
  - **STRICT RELEVANCE REQUIRED**: Items must be directly used in or essential to the specific action
  - **Examples of CORRECT supplement usage**:
    - "Sword" for sword attacks or weapon-based combat
    - "Lockpicks" for picking locks specifically
    - "Rope" for climbing, binding, or rappelling
    - "Shield" for defensive actions
    - "Bandages" for healing actions
    - "Crowbar" for prying or breaking actions
  - **Examples of INCORRECT supplement usage**:
    - "Sword" for punching (not using the sword)
    - "Lockpicks" for intimidation (not picking locks)
    - "Rope" for social persuasion (not physically using rope)
    - "Bandages" for combat attacks (not healing)
  - **Selection Rule**: If the item is not physically used or directly essential to performing the action, use {{"name": "None", "value": 0}}
  - **When in doubt**: Choose "None" rather than forcing an irrelevant item

**SHIFT POLARITY EXAMPLES:**
- **stress_level**: MUST be an integer 1-5
- **shift_type**: MUST be "Lasting" or "Temporary"
- **shift_polarity**: MUST be "Additive" or "Subtractive"
  - **Additive**: Actions that INCREASE/IMPROVE the target's status
    - Healing someone (Additive to Stamina)
    - Encouraging someone (Additive to Spirit)
    - Giving money/resources (Additive to Supply)
    - Building rapport/friendship (Additive to Sympathy)
  - **Subtractive**: Actions that DECREASE/HARM the target's status
    - Attacking someone (Subtractive to Stamina)
    - Intimidating someone (Subtractive to Spirit)
    - Stealing money/resources (Subtractive to Supply)
    - Insulting/betraying someone (Subtractive to Sympathy)
- **self_effects**: MANDATORY - MUST contain at least one self-effect (empty list [] is NOT allowed for proactor actions)

**Guidelines:**
- Be specific and detailed in all justifications
- Consider the narrative context when determining stress levels
- Predict realistic self-effects based on the action's nature
- Ensure all numerical values are appropriate for the actor's capabilities

**SELF-EFFECTS ANALYSIS REQUIREMENTS:**
🚨 **CRITICAL: PROACTOR ACTIONS MUST ALWAYS HAVE SELF-EFFECTS** 🚨
Proactors pay costs for taking initiative - there is NO such thing as a cost-free proactor action!
Every proactor action MUST have at least one self-effect representing the inherent cost of acting.

When interpreting the Proactor's action, you MUST analyze potential self-inflicted effects using this systematic approach:

**1. Self-Effect Condition Analysis:**
For each potential self-effect, determine WHEN it occurs:
- **Inherent Cost**: Effect happens simply by performing the action, regardless of success/failure
- **On Action Success**: Effect only occurs if the primary action succeeds  
- **On Action Failure**: Effect only occurs if the primary action fails

**2. Target Status Identification:**
Identify which of the Proactor's own statuses is affected:
- **STAMINA**: Physical health, energy, endurance
- **SPIRIT**: Mental state, confidence, morale
- **SUPPLY**: Resources, materials, equipment

**3. Polarity and Type:**
- **Polarity**: Additive (increases status) or Subtractive (decreases status)
- **Shift Type**: Lasting (persistent) or Temporary (fleeting)

**4. Severity Calculation (1-4 scale):**
Step A - Get Initial Base Magnitude from stress level and condition
Step B - Apply narrative adjustment (-1, 0, or +1) based on action context
Final Severity = Initial + Adjustment (clamped 1-4)

**CRITICAL FORMATTING REQUIREMENTS:**
- ALL nested objects (skill, endowment, supplement) MUST be JSON objects with "name" and "value" keys
- ALL numeric values MUST be integers (0-5), never strings or text
- If no skill/endowment/supplement applies, use: {{"name": "None", "value": 0}}
- NEVER return strings where objects are expected

**CORRECT EXAMPLES:**
"skill": {{"name": "Combat", "value": 3}}
"s_trait_value": 4
"endowment": {{"name": "None", "value": 0}}

**SELF-EFFECTS EXAMPLES:**
🚨 **CRITICAL: Only ONE self-effect condition applies per proactor per action!** 🚨
Choose the most appropriate condition based on the action's nature:

**SEVERITY FIELD IS MANDATORY - EXAMPLES:**
✅ CORRECT: "severity": 2
✅ CORRECT: "severity": 1  
✅ CORRECT: "severity": 4
❌ WRONG: "severity": null
❌ WRONG: "severity": None
❌ WRONG: "severity": "moderate"
❌ WRONG: Missing severity field entirely

🚨 **SEVERITY MUST ALWAYS BE AN INTEGER FROM 1 TO 4** 🚨
If you're unsure of the severity, use 2 as a safe default rather than leaving it empty!

**Example 1 - Inherent Cost (Most Common):**
"self_effects": [
    {{
        "condition": "Inherent Cost",
        "target_status": "Stamina",
        "polarity": "Subtractive",
        "shift_type": "Temporary",
        "severity": 2,
        "severity_justification": "Running and attacking is physically demanding, base severity 2 for moderate exertion",
        "description": "The physical exertion of sprinting while wielding a weapon leaves the proactor breathing heavily and slightly fatigued"
    }}
]

**Example 2 - On Action Success:**
"self_effects": [
    {{
        "condition": "On Action Success",
        "target_status": "Spirit",
        "polarity": "Additive",
        "shift_type": "Temporary",
        "severity": 1,
        "severity_justification": "Successfully intimidating someone can be emotionally empowering, severity 1 for mild psychological boost",
        "description": "After successfully breaking their opponent's will, the proactor feels a twinge of confidence and emotional empowerment"
    }}
]

**Example 3 - On Action Failure:**
"self_effects": [
    {{
        "condition": "On Action Failure",
        "target_status": "Spirit",
        "polarity": "Subtractive",
        "shift_type": "Temporary",
        "severity": 2,
        "severity_justification": "Failing a risky maneuver can be demoralizing, severity 2 for significant confidence loss",
        "description": "The failed attempt leaves the proactor feeling foolish and doubting their abilities"
    }}
]

**CONDITION SELECTION GUIDE:**
- **Inherent Cost**: Effect happens only if success and failure are not applicable (physical exertion, resource consumption)
- **On Action Success**: Effect only occurs if the action succeeds (guilt, overconfidence, exhaustion from success)
- **On Action Failure**: Effect only occurs if the action fails (embarrassment, injury from failure, wasted resources)

**INCORRECT EXAMPLES TO AVOID:**
"skill": "Combat"  ❌ (should be object)
"skill": {{"name": "Combat", "value": "3"}}  ❌ (value should be number)
"s_trait_value": "Expert"  ❌ (should be number)
"self_effects": []  ❌ (NEVER empty for proactor actions!)

**IF UNCERTAIN:**
- For skills: Use {{"name": "Instincts", "value": 0}}
- For endowments: Use {{"name": "None", "value": 0}}
- For supplements: Use {{"name": "None", "value": 0}}
- For numeric values: Use 0 if truly unknown

**VALIDATION CHECKLIST - COMPLETE BEFORE RESPONDING:**
1. ✓ ALL 16 utas_factors fields are present (no missing fields allowed)
2. ✓ s_trait_value is an INTEGER from actor data above (not 0, not string)
3. ✓ skill, endowment, supplement are OBJECTS with "name" and "value" keys
4. ✓ All justification fields contain meaningful explanations
5. ✓ exchange_type matches one of the 4 allowed values exactly
6. ✓ status_to_shift matches one of the 4 allowed values exactly
7. ✓ s_trait_to_use matches one of the 5 allowed values exactly
8. ✓ self_effects is present ([] if no effects)
9. ✓ JSON is properly formatted and parseable

10. ✓ If dialogue is trivial (SmallTalk/neutral greeting) set dialogue_metadata.apply_shift=false and keep UTAS factors intact

**CRITICAL WARNING:**
- INCOMPLETE RESPONSES CAUSE SYSTEM CRASHES
- MISSING FIELDS RESULT IN ERROR MESSAGES
- YOU MUST PROVIDE ALL 16 UTAS_FACTORS FIELDS
- NO SHORTCUTS OR SIMPLIFIED RESPONSES ALLOWED

**RESPONSE FORMAT:**
- Respond ONLY with valid JSON
- No explanatory text before or after the JSON
- No markdown code blocks or formatting
- Raw JSON object only

**FINAL REMINDER: Your response MUST contain ALL fields listed in the JSON structure above. Partial responses will fail."""

    def _build_reactor_interpretation_prompt(self, proactor_action_data: Dict[str, Any], proactor: 'Actor', reactor: 'Actor') -> str:
        """Build comprehensive reactor interpretation prompt for detailed UTAS OBJECTIVE Step 4 analysis"""
        import json
        
        reactor_data = self._build_detailed_actor_data(reactor)
        
        prompt = f"""
You are interpreting a reactor's defensive response in the UTAS simulation system.

**Rules for Reaction Generation:**
1.  **Logical Reaction:** The reaction must be a direct and logical response to the Proactor's action.
2.  **Use Provided Data Only:** You can ONLY select skills and supplements that exist on the Reactor's sheet. Do not invent them.
3.  **Justify Choices:** Briefly explain *why* the chosen skill/supplement is a relevant reaction.
4.  **Default to "None":** If no skill or supplement is relevant, you MUST use "None".

**Scenario Context:**
*   **Scene:** {self.scene_description}
*   **Proactor (The one who acted):** {proactor.sheet.name}
*   **Reactor (The one reacting):** {reactor.sheet.name if reactor else "None (solo exploration)"}

**Proactor's Action Details:**
```json
{json.dumps(proactor_action_data, indent=2)}
```

**Reactor's Character Sheet:**
```json
{json.dumps(reactor_data, indent=2)}
```

**S-TRAIT REACTION SELECTION GUIDE (Consistency Required):**
- Verbal boundary-setting, de-escalation, calm refusal, persuasion → choose SOCIABILITY
- Physical resistance (bracing, shoving, grappling) → choose STURDINESS
- Evasive movement (sidestep, step back, slip away) → choose SWIFTNESS
- Stealthy/indirect manipulation (misdirection, feint, concealment) → choose SHADOW
- Logical/policy-based rebuttal (citing rules, precise reasoning) → choose SMARTS

You MUST align the chosen S-trait with the reaction's narrative. If your initial choice does not match the described reaction style, select the more appropriate trait and justify briefly.

**Your Task - REACTOR INTERPRETATION (UTAS OBJECTIVE Step 4):**
Translate the Reactor's intended response into structured UTAS factors. Define the defensive nature of the reaction and determine if it includes a Secondary Effect—an additional component aimed at affecting either the Proactor ("Reactive Strike") or the Reactor themselves ("Reactive Boon").

**1. Define Core Defensive Factors:**
- Reactor_Reaction_Description: A concise narrative description of what the Reactor is trying to do
- Reactor_Reaction_Skill: The primary Skill used for the reaction (e.g., Acting, Social Fortitude). Include its value.
- Reactor_Reaction_S_Trait: The primary S-Trait supporting the reaction (e.g., Sociability, Sturdiness). Include its value.
- Reactor_Reaction_Endowment: Any Endowment being used (if applicable). Include its value.
- Reactor_Reaction_Supplement: Any equipment or situational advantage used. Include its value.
- Reactor_Primary_Defensive_Status_Type: The Status (Stamina, Spirit, Supply) that best represents the resilience the Reactor is drawing upon for their reaction.

**2. Analyze for and Define Secondary Effect:**
- Has_Secondary_Effect (TRUE/FALSE): Analyze the Reactor_Reaction_Description. Does the reaction intend to do anything more than simply negate the Proactor's action?
- Example: "The reaction includes 'empower me,' which is an effect beyond pure defense. Therefore, Has_Secondary_Effect is TRUE."

Return a JSON object with the following structure:

{{
    "action_noun": "A single, simple noun for the reaction (e.g., 'dodge', 'block', 'counter').",
    "narrative_description": "A brief, dynamic description of the reaction, starting with a verb. **Use {proactor.sheet.name} to refer to the proactor.** Example: 'dodge {proactor.sheet.name}'s attack' or 'raise shield against {proactor.sheet.name}'.",
    "justification": "Your reasoning for the defensive approach and any secondary effects based on the Reactor's character.",
    "utas_factors": {{
        "reactor_reaction_description": "A concise narrative description of what the Reactor is trying to do (e.g., 'Laugh off the insult and use the momentum to bolster their own confidence').",
        "reactor_reaction_skill": {{"name": "skill_name", "value": skill_value}},
        "reactor_reaction_s_trait": "The primary S-Trait supporting the reaction (SWIFTNESS, SOCIABILITY, STURDINESS, SMARTS, SHADOW).",
        "reactor_reaction_endowment": {{"name": "endowment_name", "value": endowment_value}},
        "reactor_reaction_supplement": {{"name": "supplement_name", "value": supplement_value}},
        "reactor_primary_defensive_status_type": "The Status (SPIRIT, STAMINA, SUPPLY) that best represents the resilience the Reactor is drawing upon.",
        "status_to_shift": "MANDATORY: The primary status on the PROACTOR you intend to affect IF YOUR REACTION PREVAILS (SPIRIT, STAMINA, SUPPLY).",
        "shift_polarity": "MANDATORY: 'Additive' or 'Subtractive' - whether your intended effect on that status is beneficial or harmful.",
        "has_secondary_effect": "TRUE or FALSE - Does the reaction intend to do anything more than simply negate the Proactor's action?",
        "secondary_effect_target": "If Has_Secondary_Effect is TRUE: 'Proactor' or 'Self' - Who is the intended recipient of this secondary effect?",
        "secondary_effect_target_status_type": "If Has_Secondary_Effect is TRUE: Which Status (SPIRIT, STAMINA, SUPPLY) is being targeted by the secondary effect?",
        "secondary_effect_shift_polarity_numeric": "If Has_Secondary_Effect is TRUE: '+1' (Additive) or '-1' (Subtractive) - Is the effect beneficial or harmful?",
        "secondary_effect_shift_type_multiplier": "If Has_Secondary_Effect is TRUE: '1.0' (Lasting) or '0.5' (Temporary) - Is the effect permanent or temporary?",
        "stress_level": "An integer from 1 (very low stress) to 5 (very high stress), representing the reaction's inherent difficulty."
    }}
}}

**CRITICAL FORMATTING REQUIREMENTS:**
- ALL nested objects (skill, supplement) MUST be JSON objects with "name" and "value" keys
- ALL numeric values MUST be integers, never strings or text
- If no skill/supplement applies, use: {{"name": "None", "value": 0}}
- NEVER return strings where objects are expected
"""
        return prompt

    def _get_cache_key(self, prompt: str, context_data: Dict[str, Any]) -> str:
        """Generate cache key from prompt and relevant context"""
        cache_data = f"{prompt}_{json.dumps(context_data, sort_keys=True)}"
        return hashlib.md5(cache_data.encode()).hexdigest()
    
    def _call_llm_for_json(
        self,
        prompt: str,
        model: str = None,
        cache_context: Optional[Dict[str, Any]] = None,
        max_retries: int = 5,
        timeout: int = 25,
    ) -> Optional[Dict[str, Any]]:
        """Calls the OpenRouter LLM and attempts to parse the response as JSON with retries."""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                if facts_block and isinstance(prompt, str) and prompt.strip():
                    prompt = f"{facts_block}\n\n{prompt}"
        except Exception:
            pass
        cache_key = self._get_cache_key(prompt, cache_context) if cache_context else None
        if cache_key and cache_key in self.response_cache:
            self.cache_hits += 1
            return self.response_cache[cache_key]
        else:
            self.cache_misses += 1
        
        last_error = None
        last_response = None
        
        for attempt in range(max_retries):
            try:
                response = retry_with_backoff(
                    lambda: self.client.chat.completions.create(
                        model=model or self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.2 + (attempt * 0.05),  # Slightly increase temp on retries
                        timeout=timeout,
                    )
                )
                response_text = response.choices[0].message.content
                last_response = response_text
                result = extract_and_parse_json(response_text)
                
                if result is not None:
                    if cache_key:
                        self.response_cache[cache_key] = result
                    return result
                
                # JSON parsing failed, retry
                if attempt < max_retries - 1:
                    print(f"{Color.WARNING}⚠️ JSON parse failed (attempt {attempt + 1}/{max_retries}), retrying...{Color.RESET}")
                    import time
                    time.sleep(0.5 * (attempt + 1))
                    
            except KeyboardInterrupt:
                # Allow the user to interrupt a stuck/slow network call without killing the whole sim.
                return None
            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    print(f"{Color.WARNING}⚠️ LLM call failed (attempt {attempt + 1}/{max_retries}): {e}, retrying...{Color.RESET}")
                    import time
                    time.sleep(1.0 * (attempt + 1))
        
        # All retries exhausted
        raw_response = last_response if last_response else 'No response data'
        error_message = f"JSONDecodeError after {max_retries} attempts\nRaw Response:\n{raw_response}"
        self.logger.log_system(f"ERROR: {error_message}")
        return None
    
    def validate_and_repair_proactor(
        self,
        proactor_data: Dict[str, Any],
        proactor: 'Actor',
        reactor: 'Actor',
        guidance: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize and, if necessary, re-prompt to repair missing PROACTOR UTAS fields
        for NUA proactive actions. Mirrors validate_and_repair_reactor() so Decider
        can remain decide-only and return raw JSON.
        """
        from response_normalizer import ResponseNormalizer
        import json

        current = proactor_data or {}
        
        # Determine if proactor is the user actor for sensory perspective
        proactor_is_ua = getattr(proactor, 'is_user_actor', False)

        # CRITICAL USER AGENCY: capture the UA's exact action text once and preserve it.
        ua_raw_action = None
        try:
            if proactor_is_ua and isinstance(current, dict):
                ua_raw_action = (
                    current.get('raw_user_action')
                    or current.get('action_description')
                    or current.get('narrative_description')
                )
        except Exception:
            ua_raw_action = None

        def _ua_force_raw_text(d: Dict[str, Any]) -> Dict[str, Any]:
            if not proactor_is_ua:
                return d
            if not ua_raw_action:
                return d
            try:
                d['raw_user_action'] = ua_raw_action
                d['action_description'] = ua_raw_action
                d['narrative_description'] = ua_raw_action
            except Exception:
                pass
            return d

        def _ua_local_repair(d: Dict[str, Any]) -> Dict[str, Any]:
            """For UA: never re-prompt the LLM. Only fill missing mechanics locally."""
            if not isinstance(d, dict):
                d = {}
            uf = d.get('utas_factors') if isinstance(d.get('utas_factors'), dict) else {}
            # Minimal defaults to satisfy normalizer/engine. Keep conservative.
            defaults = {
                'exchange_type': uf.get('exchange_type') or 'Spirit',
                'status_to_shift': uf.get('status_to_shift') or 'Spirit',
                's_trait_to_use': uf.get('s_trait_to_use') or 'Shadow',
                'skill': uf.get('skill') or {'name': 'none', 'value': 0},
                'endowment': uf.get('endowment') or {'name': 'none', 'value': 0},
                'supplement': uf.get('supplement') or {'name': 'none', 'value': 0},
                'supplement_val': uf.get('supplement_val') or 0,
                'stress_level': uf.get('stress_level') or 3,
                'shift_type': uf.get('shift_type') or 'Temporary',
                'shift_polarity': uf.get('shift_polarity') or 'Additive',
                # Secondary effects are optional; default off.
                'has_secondary_effect': uf.get('has_secondary_effect') if uf.get('has_secondary_effect') is not None else False,
                # Self effects can be empty for UA if the model didn't provide them.
                'self_effects': uf.get('self_effects') if isinstance(uf.get('self_effects'), list) else [],
            }
            for k, v in defaults.items():
                if uf.get(k) in (None, ''):
                    uf[k] = v
            d['utas_factors'] = uf
            # Legacy top-level self_effects compatibility
            if 'self_effects' not in d or not isinstance(d.get('self_effects'), list):
                d['self_effects'] = uf.get('self_effects', [])
            return d

        for attempt in range(0, max_retries + 1):
            try:
                normalized = ResponseNormalizer.normalize_proactor_action_response(
                    current, proactor.sheet.name, "takes action", proactor_is_ua
                )
                # Enrich with actor sheet authoritative values (skill/endowment/supplement numbers)
                try:
                    uf = normalized.get('utas_factors', {})
                    self._override_with_actor_sheet_values(uf, proactor)
                except Exception:
                    pass
                normalized = _ua_force_raw_text(normalized)
                return normalized
            except Exception as ex:
                last_err = str(ex)
                if attempt >= max_retries:
                    break

                # For UA: do not re-prompt; locally repair missing mechanics and retry.
                if proactor_is_ua:
                    try:
                        current = _ua_local_repair(current)
                        current = _ua_force_raw_text(current)
                        continue
                    except Exception:
                        current = _ua_force_raw_text(current if isinstance(current, dict) else {})
                        continue

                # Minimal canonical repair prompt
                missing_hint = f"Error: {last_err}"
                existing_utas = (current.get('utas_factors') if isinstance(current, dict) else None) or {}

                # Try to extract missing field names from normalizer error for a focused repair instruction
                missing_fields_focus = []
                try:
                    import re
                    m = re.search(r"Missing/invalid required PROACTOR UTAS fields:\s*\[(.*?)\]", str(last_err))
                    if m:
                        raw_list = m.group(1)
                        # Split by comma and strip quotes/spaces
                        parts = [p.strip().strip('"').strip("'") for p in raw_list.split(',')]
                        missing_fields_focus = [p for p in parts if p]
                except Exception:
                    missing_fields_focus = []

                ctx_summary = ''
                repair_note = ''
                if isinstance(guidance, dict):
                    ctx_summary = guidance.get('context_summary') or ''
                    repair_note = guidance.get('repair_note') or ''

                focus_line = ""
                try:
                    if missing_fields_focus:
                        focus_line = "\nFOCUS: Repair and include these missing/invalid keys under utas_factors: " + ", ".join(missing_fields_focus) + "\n"
                except Exception:
                    focus_line = ""

                repair_prompt = f"""
You are repairing a PROACTOR UTAS JSON object. Provide ONLY valid JSON, no prose.

Scene (summary): {self.scene_description[:300]}
Proactor: {proactor.sheet.name}
Reactor: {reactor.sheet.name}
{('Context: ' + ctx_summary) if ctx_summary else ''}
{('Notes: ' + repair_note) if repair_note else ''}

{missing_hint}
{focus_line}

Current (possibly incomplete) JSON:
```json
{json.dumps(current, indent=2)}
```

MANDATORY CANONICAL KEYS under "utas_factors":
- s_trait_to_use (STURDINESS|SOCIABILITY|SMARTS|SWIFTNESS|SHADOW)
- skill (object: {"name": str, "value": int})
- endowment (object: {"name": str, "value": int})
- supplement (object: {"name": str, "value": int}) and supplement_val (integer)
- stress_level (1-5)
- shift_type (Lasting|Temporary)
- status_to_shift (SPIRIT|STAMINA|SUPPLY|SYMPATHY)
- shift_polarity (Additive|Subtractive)
- has_secondary_effect (true|false)
- self_effects (optional list; use [] if none)

Return the FULL repaired JSON with these keys present in utas_factors. Do not invent skills/items not on the proactor sheet.
"""

                repaired = self._call_llm_for_json(repair_prompt.strip(), cache_context={'role':'proactor_repair','attempt':attempt})
                if repaired and isinstance(repaired, dict):
                    current = repaired
                else:
                    continue

        return None

    def validate_and_repair_reactor(
        self,
        reactor_data: Dict[str, Any],
        proactor: 'Actor',
        reactor: 'Actor',
        guidance: Optional[Dict[str, Any]] = None,
        max_retries: int = 2,
    ) -> Optional[Dict[str, Any]]:
        """
        Normalize and, if necessary, re-prompt to repair missing reactor UTAS fields.
        Centralizes canonicalization so Decider stays minimal.
        """
        from response_normalizer import ResponseNormalizer
        import json

        # Working copy of data
        current = reactor_data or {}

        # Determine if reactor is the user actor for sensory perspective
        reactor_is_ua = getattr(reactor, 'is_user_actor', False)
        
        proactor_is_ua = bool(getattr(proactor, 'is_user_actor', False))
        expects_dialogue = False
        proactor_question = ""
        try:
            if isinstance(guidance, dict):
                expects_dialogue = bool(guidance.get('expects_dialogue', False))
        except Exception:
            expects_dialogue = False

        try:
            if isinstance(guidance, dict):
                proactor_question = str(guidance.get('proactor_question') or '')
        except Exception:
            proactor_question = ""

        # proactor_question is provided by ConductorAgent (best-effort). Avoid using out-of-scope variables here.

        for attempt in range(0, max_retries + 1):
            try:
                normalized = ResponseNormalizer.normalize_reactor_response(
                    current, reactor.sheet.name, "reacts defensively", reactor_is_ua
                )
                # Enrich with actor sheet authoritative values (skill/endowment/supplement numbers)
                try:
                    uf = normalized.get('utas_factors', {})
                    self._override_with_actor_sheet_values(uf, reactor)
                except Exception:
                    pass

                # Additional coherence/POV validation beyond schema
                try:
                    nd = (normalized.get('narrative_description') or '').strip()
                    if expects_dialogue and ('"' not in nd and "'" not in nd):
                        raise ValueError("Reactor narrative_description must include quoted dialogue (UA spoke / asked a question)")

                    if expects_dialogue and proactor_question and '?' in proactor_question:
                        lowered_nd = f" {nd.lower()} "
                        lowered_pq = f" {str(proactor_question).lower()} "

                        # The reactor must provide a substantive response, not a placeholder like just "Answer".
                        # Accept refusals/deflections as valid answers, but reject single-word filler.
                        try:
                            quoted = re.findall(r"\"([^\"]+)\"|'([^']+)'", nd)
                            quoted_parts = []
                            for a, b in quoted:
                                part = (a or b or '').strip()
                                if part:
                                    quoted_parts.append(part)
                            if quoted_parts:
                                filler = {'answer', 'yes', 'no', 'maybe', 'ok', 'okay', 'sure'}
                                # If ALL quoted parts are just 1 word and that word is filler, reject.
                                all_filler = True
                                for part in quoted_parts:
                                    words = [w for w in re.split(r"\s+", part) if w]
                                    if len(words) >= 2:
                                        all_filler = False
                                        break
                                    if len(words) == 1 and words[0].strip(".,!?;:\"").lower() not in filler:
                                        all_filler = False
                                        break
                                if all_filler:
                                    raise ValueError("Reactor dialogue is a placeholder (e.g., \"Answer\"); must provide a substantive answer or explicit refusal/deflection")
                        except ValueError:
                            raise
                        except Exception:
                            pass

                        # Guard against derailment into physical intimacy during a plain Q/A turn.
                        banned_physical = [
                            'kiss', 'kisses', 'kissing', 'mouth', 'tongue', 'embrace', 'embraces',
                            'grabs', 'grab', 'pulls', 'pull', 'cups', 'cup', 'caress', 'caresses',
                            'small of her back', 'small of his back'
                        ]
                        proactor_initiated_intimacy = any(b in lowered_pq for b in banned_physical)
                        if (not proactor_initiated_intimacy) and any(b in lowered_nd for b in banned_physical):
                            raise ValueError(
                                "Reactor narrative_description introduced physical intimacy during a plain dialogue/question exchange; must answer/acknowledge the question via dialogue"
                            )

                    # NOTE: Pronoun check intentionally removed. The reactor narrative describes the NPC's
                    # reaction as observed by the UA; third-person pronouns (he/she/him/her) correctly
                    # refer to the reactor (NPC), not to the UA. The Step 6 narrator handles final
                    # perspective rendering.
                except Exception as ex2:
                    # Re-raise as ValueError so we enter repair path
                    raise ValueError(str(ex2))

                return normalized
            except Exception as ex:
                last_err = str(ex)
                if attempt >= max_retries:
                    break

                # Build a minimal canonical repair prompt containing only what's needed
                missing_hint = f"Error: {last_err}"
                existing_utas = (current.get('utas_factors') if isinstance(current, dict) else None) or {}

                # Guidance fields
                ctx_summary = ''
                repair_note = ''
                if isinstance(guidance, dict):
                    ctx_summary = guidance.get('context_summary') or ''
                    repair_note = guidance.get('repair_note') or ''

                extra_rules = ""
                try:
                    if expects_dialogue:
                        extra_rules += "\n- narrative_description MUST include quoted dialogue (use quotes)"
                    if proactor_is_ua:
                        extra_rules += "\n- narrative_description MUST refer to the proactor as 'you/your' (no she/her/he/him/his)"
                    if expects_dialogue and proactor_question and '?' in proactor_question:
                        extra_rules += "\n- Proactor asked a question; your dialogue MUST answer or acknowledge that question"
                        extra_rules += "\n- Your quoted dialogue must be SUBSTANTIVE (not a placeholder like \"Answer\"). You may refuse/deflect, but it must still directly respond (e.g., \"Not your business\" / \"It's been slow\" / \"Busy since dawn\")"
                except Exception:
                    pass

                repair_prompt = f"""
You are repairing a REACTOR UTAS JSON object. Provide ONLY valid JSON, no prose.

Scene (summary): {self.scene_description[:300]}
Proactor: {proactor.sheet.name}
Reactor: {reactor.sheet.name}
{('Context: ' + ctx_summary) if ctx_summary else ''}
{('Notes: ' + repair_note) if repair_note else ''}

{missing_hint}

Current (possibly incomplete) JSON:
```json
{json.dumps(current, indent=2)}
```

MANDATORY CANONICAL KEYS under "utas_factors" (no legacy keys):
- s_trait_to_use (STURDINESS|SOCIABILITY|SMARTS|SWIFTNESS|SHADOW)
- skill (reactor's real skill name)
- endowment (null or reactor endowment name)
- supplement (null or item name) and supplement_val (integer)
- stress_level (1-5)
- status_to_shift (SPIRIT|STAMINA|SUPPLY|SYMPATHY)
- shift_polarity (Additive|Subtractive)
- has_secondary_effect (true|false). If false, omit other secondary keys.

ADDITIONAL NARRATIVE RULES:{extra_rules if extra_rules else ''}

Return the FULL repaired JSON with these keys present in utas_factors. Do not invent skills/items not on the reactor sheet.
"""

                repaired = self._call_llm_for_json(repair_prompt.strip(), cache_context={'role':'reactor_repair','attempt':attempt})
                if repaired and isinstance(repaired, dict):
                    current = repaired
                else:
                    # If repair failed to parse, continue next attempt with same current
                    continue

        return None
    def detect_survival_consumption_intent(self, user_text: str, scene_context: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Use the LLM to determine if the user's text expresses an actual consumption/order event
        (which should fulfill FOOD/WATER) versus browsing/searching/planning (which should not).

        Returns a JSON object like:
        {
          "consumption_intent": true/false,
          "confidence": 0.0-1.0,
          "action_type": "consume|order|search|plan|talk|other",
          "rationale": "brief reasoning"
        }
        """
        try:
            scene = (scene_context or self.scene_description or '')
            prompt = f"""
You are classifying a survival-related intent strictly for FOOD/WATER fulfillment.
Decide if the text indicates actual consumption or an order that will imminently result in consumption,
as opposed to merely searching, browsing, planning, asking about, or talking about food/water.

Return ONLY JSON with keys: consumption_intent (boolean), confidence (0-1), action_type, rationale.

Scene Context:
{scene[:800]}

User Text:
"{user_text}"

Rules:
- consumption_intent = true ONLY if the user is eating/drinking now or ordering a specific item to consume now.
- consumption_intent = false for searching, looking around, asking for menus, thinking about food, or planning to eat later.
- action_type should be one of: consume, order, search, plan, talk, other

Examples that DO trigger consumption_intent = true (choose action_type accordingly):
- consume: "I eat the sandwich", "I drink some water", "I sip my coffee now"
- order:   "I order a burger and fries", "Let me have a salad and a tea", "Can I get a bottle of water?"

Examples that do NOT trigger consumption_intent (consumption_intent = false):
- search:  "I look for something to eat", "I look for a water fountain", "We search for a cafe"
- plan:    "I might eat later", "I'll grab a coffee after this", "Let's get dinner tonight"
- talk:    "Where can I get coffee?", "Do they have food here?", "I ask about the menu"
- other:   "I get a table", "I check the menu", "We head to the diner"

"""
            cache_ctx = {"purpose": "survival_consumption_intent", "scene_hash": hash(scene[:500]), "text": user_text}
            result = self._call_llm_for_json(prompt, model=self.model, cache_context=cache_ctx)
            # Validate minimal structure
            if isinstance(result, dict) and 'consumption_intent' in result and 'confidence' in result:
                return result
            return None
        except Exception as e:
            self.logger.log_system(f"ERROR: detect_survival_consumption_intent failed: {e}")
            return None

    def _get_serendipity_roll(self) -> int:
        """Rolls 2d6-7 to get a serendipity value."""
        return random.randint(1, 6) + random.randint(1, 6) - 7

    def roll_for_initiative(self, actor1: 'Actor', actor2: 'Actor') -> Tuple['Actor', 'Actor']:
        """
        Rolls initiative for both actors and determines the proactor for the turn.
        Tie-breakers: 1. Higher Swiftness. 2. Coin toss.
        """
        self.logger.log_system("Rolling for initiative...")
        print(f"\n{Color.INFO}--- Initiative Roll ---{Color.RESET}")

        actor1_swiftness = actor1.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)
        actor2_swiftness = actor2.sheet.s_factors.get_factor(SFactorType.SWIFTNESS)

        actor1_serendipity = self._get_serendipity_roll()
        actor2_serendipity = self._get_serendipity_roll()

        actor1_initiative = actor1_swiftness + actor1_serendipity
        actor2_initiative = actor2_swiftness + actor2_serendipity

        print(f"{actor1.sheet.name}: Swiftness({actor1_swiftness}) + Serendipity({actor1_serendipity}) = {Color.SUCCESS}{actor1_initiative}{Color.RESET}")
        print(f"{actor2.sheet.name}: Swiftness({actor2_swiftness}) + Serendipity({actor2_serendipity}) = {Color.SUCCESS}{actor2_initiative}{Color.RESET}")

        proactor, reactor = None, None
        if actor1_initiative > actor2_initiative:
            proactor, reactor = actor1, actor2
        elif actor2_initiative > actor1_initiative: 
            proactor, reactor = actor2, actor1
        else:
            print("Initiative is a tie. Applying tie-breakers...")
            if actor1_swiftness > actor2_swiftness:
                print(f"{actor1.sheet.name} wins due to higher Swiftness ({actor1_swiftness} > {actor2_swiftness}).")
                proactor, reactor = actor1, actor2
            elif actor2_swiftness > actor1_swiftness:
                print(f"{actor2.sheet.name} wins due to higher Swiftness ({actor2_swiftness} > {actor1_swiftness}).")
                proactor, reactor = actor2, actor1
            else:
                print("Swiftness is also tied. Coin toss...")
                coin_toss = random.choice([actor1, actor2])
                if coin_toss == actor1:
                    print(f"{actor1.sheet.name} wins the coin toss.")
                    proactor, reactor = actor1, actor2
                else:
                    print(f"{actor2.sheet.name} wins the coin toss.")
                    proactor, reactor = actor2, actor1
    def enforce_continuity(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]:
        """
        Checks if the user's intended action is logically possible given the current scene.
        Returns the raw JSON data from the LLM.
        """
        self._refresh_scene_from_tracker()

        # RAG LOCK: hard denial semantics (Choice 3)
        # - Prefer B (exists in world, but not present/owned in current scene/state)
        # - Use A (non-existent in world) for endowment/tech/brands/anachronisms
        try:
            denial = self._rag_lock_continuity_denial(user_input=user_input, proactor=proactor)
            if denial:
                return denial
        except Exception:
            # If the RAG lock pre-check fails for any reason, do not block the turn here.
            pass

        recent_context = ""
        try:
            if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
                context_data = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=5,
                    importance_threshold="notable"
                )
                if context_data and context_data.strip():
                    recent_context = f"\n**Recent Narrative Context:**\n{context_data}\n"
        except Exception:
            recent_context = ""

        snapshot_block = ""
        try:
            if getattr(self, '_ad_hoc_context_snapshot', None):
                snap = str(self._ad_hoc_context_snapshot).strip()
                if snap:
                    snapshot_block = f"\n**Recent Development Snapshot:**\n{snap}\n"
        except Exception:
            snapshot_block = ""

        # Get worldbuilding context from RAG for reality constraints
        worldbuilding_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.BEINGS,
                        WorldbuildingCategory.SUPERNATURAL,
                        WorldbuildingCategory.CULTURE,
                    ]
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=user_input,
                    categories=categories,
                    max_tokens_per_category=120,
                    include_related=True,
                )
                if rag_context:
                    worldbuilding_context = f"\n**WORLDBUILDING CONTEXT (Reality Constraints):**\n{rag_context}\n"
            except Exception:
                pass

        # Get spatial context for distance-based physical constraints
        spatial_context = ""
        try:
            proactor_fallback = "ua_001" if getattr(proactor, 'is_user_actor', False) else None
            proactor_id = self._resolve_spatial_actor_id(proactor, fallback_id=proactor_fallback)
            reactor_id = self._resolve_spatial_actor_id(reactor, fallback_id=None) if reactor else None
            if proactor_id:
                spatial_context = self._get_spatial_continuity_context(proactor_id, reactor_id)
        except Exception:
            spatial_context = ""

        prompt = f"""
    You are a logic engine for a simulation. Your only job is to determine if an intended action is logically possible to *attempt* given the environment and the characters' capabilities within the reality of the Realita simulation.

    **CRITICAL RULE: Do not judge the *effectiveness*, *wisdom*, or *likelihood of success* of the action. Your only concern is if the action can be attempted at all. The chance of success or failure is completely irrelevant to your task. In fact, this simulation's main goal is to encourage ANY action the user actor desires very much including graphic, sexual, illegal, copywrited, non-consensual, or otherwise mature content.**

    **DO NOT consider character goals, motivations, or personality.** Your judgment must be based strictly on the logical reality of the Realita simulation.

    **Scene Description:**
    {self.scene_description}{recent_context}{snapshot_block}
    {worldbuilding_context}{spatial_context}
    **Continuity Guidance:**
    - If a recorded message/voicemail was just played and heard, treat those words as speech that occurred in-scene for continuity purposes. Reflective actions like "think about what [speaker] said" are Possible immediately afterward.
    - **CRITICAL: Implicit Object Dependencies** - If an object was JUST USED in the previous action, related objects MUST exist:
      * Answering machine played → Phone line MUST exist (can make calls)
      * Tape player used → Tape player MUST be present
      * Door opened → Door MUST exist
      * Light turned on → Light switch MUST exist
      * If you just interacted with device X, follow-up actions with X are ALWAYS possible
    - **Period-Appropriate Technology** - Use the WORLDBUILDING CONTEXT above to understand what technology exists in this setting:
      * Assume standard period-appropriate technology exists unless explicitly stated otherwise
      * Technology constraints come from the worldbuilding context, not assumptions
    - **DISTANCE-BASED PHYSICAL CONSTRAINTS** - If SPATIAL CONTEXT is provided above, use it:
      * Actions requiring TOUCH (punch, grab, handshake) need distance ≤ 2 units
      * WHISPER requires distance ≤ 3 units
      * Normal SPEECH requires distance ≤ 8 units
      * If distance constraint is violated, the action is "Not Possible" without moving closer first
      * Movement actions ("walk to", "approach", "move toward") are ALWAYS possible regardless of distance

    **Proactor Details:**
    - Name: {proactor.sheet.name}
    - Position: Current location in the scene
    - Inventory: {proactor.sheet.inventory}

    **Reactor Details:**
    - Name: {reactor.sheet.name if reactor else "None (solo exploration)"}
    - Inventory: {reactor.sheet.inventory if reactor else "N/A"}

    **User's Intended Action:**
    \"{user_input}\"

    **Your Task:**
    Analyze ONLY if the physical action itself is logically possible for a human to attempt in the established setting (see WORLDBUILDING CONTEXT above).
    
    **CRITICAL - WHAT YOU CHECK:**
    ✓ Can a human physically perform this action? (walk, talk, pick up, look at, etc.)
    ✓ Does this violate the laws of physics? (flying without a plane, teleporting, magic)
    ✓ Does this require impossible abilities based on the WORLDBUILDING CONTEXT? (breathing underwater without equipment, seeing through walls, endowment powers)
    
    **CRITICAL - WHAT YOU DO NOT CHECK:**
    ✗ Whether a location has been mentioned before (locations can exist without being mentioned)
    ✗ Whether a person has been mentioned before (people can exist without being mentioned)
    ✗ Whether the action is wise, effective, or likely to succeed
    ✗ Whether the character knows where something is (they can try to find it)
    ✗ Whether something "should" be in the scene description
    
    **EXAMPLES:**
    - "Head to The Rusty Anchor" → POSSIBLE (humans can walk to locations, even if not mentioned yet)
    - "Find Marcus" → POSSIBLE (humans can search for people, even if not mentioned yet)
    - "Fly to the diner" → NOT POSSIBLE (humans cannot fly without a plane - check WORLDBUILDING CONTEXT for technology)
    - "Teleport home" → NOT POSSIBLE (teleportation doesn't exist - check WORLDBUILDING CONTEXT)
    - "Read someone's mind" → NOT POSSIBLE (telepathy doesn't exist - check WORLDBUILDING CONTEXT)
    - "Attack the guard with a fork" → POSSIBLE (physically possible, even if ineffective)
    - "Open the locked door without a key" → POSSIBLE (can attempt to force it, pick it, break it)
    - "Breathe underwater" → NOT POSSIBLE (humans need equipment for this)
    
    **DISTANCE-BASED EXAMPLES (if SPATIAL CONTEXT provided):**
    - "Punch Marcus" at 10 units distance → NOT POSSIBLE (too far - need ≤2 units for physical contact)
    - "Whisper to Marcus" at 5 units distance → NOT POSSIBLE (too far - need ≤3 units for whisper)
    - "Talk to Marcus" at 5 units distance → POSSIBLE (within 8 units for normal speech)
    - "Walk toward Marcus" at ANY distance → POSSIBLE (movement is always possible)
    - "Approach Marcus" at ANY distance → POSSIBLE (movement is always possible)
    
    An action is \"Not Possible\" ONLY if it violates the laws of physics or requires endowment abilities that don't exist according to the WORLDBUILDING CONTEXT.
    An action is \"Possible\" if a normal human could physically attempt it in the established setting, regardless of whether it will succeed or whether the target has been mentioned before.

    Respond with a JSON object with two keys:
    1. \"judgment\": A string, either \"Possible\" or \"Not Possible\".
    2. \"justification\": A string explaining your reasoning based *only* on the reality of the Realita simulation.
    """
        return self._call_llm_for_json(prompt.strip())

    def _rag_lock_continuity_denial(self, user_input: str, proactor: 'Actor') -> Optional[Dict[str, Any]]:
        if not user_input or not self.rag_system:
            return None

        # UI / command inputs should never be treated as in-world actions.
        # In particular, /pmap (pygame map) and related control commands can include words
        # like "app" in user phrasing, which would otherwise trigger false-positive denials.
        try:
            ui = str(user_input).strip()
            ui_l = ui.lower()
            if ui_l.startswith('/'):
                return None
            if ui_l.startswith('__pmap_') or ui_l.startswith('__pmaptravel__') or ui_l.startswith('__pmap travel__'):
                return None
            if ui_l.startswith('__pmap_travel__') or ui_l.startswith('__pmaptravel'):
                return None
            if ui_l.startswith('__pmap') or ui_l.startswith('__pmap '):
                return None
            if ui_l.startswith('__pmap_travel') or ui_l.startswith('__pmap travel'):
                return None
            if ui_l.startswith('__pmap') or ui_l.startswith('__pmap_'):
                return None
            if ui_l.startswith('__pmap') or ui_l.startswith('__pmap'):
                return None
            # Uppercase variant used by the input loop
            if ui.startswith('__PMAP_'):
                return None
        except Exception:
            pass

        scene_text = (self.scene_description or "")
        inv_text = ""
        skills_text = ""
        allowed_skills: list[str] = []
        allowed_items: list[str] = []
        inv_names: list[str] = []
        try:
            inv = getattr(getattr(proactor, 'sheet', None), 'inventory', None)
            inv_text = str(inv) if inv is not None else ""
        except Exception:
            inv_text = ""

        # Keep a concrete list of inventory item names for messaging.
        try:
            inv_obj = getattr(getattr(proactor, 'sheet', None), 'inventory', None)
            if isinstance(inv_obj, list):
                for it in inv_obj:
                    if hasattr(it, 'name'):
                        nm = str(getattr(it, 'name', '')).strip()
                    else:
                        nm = str(it).strip()
                    if nm:
                        inv_names.append(nm)
        except Exception:
            inv_names = []

        # Skills are inherent to the actor; they are not scene objects.
        # If an action references a known skill, we must NOT deny it as "not present in scene".
        try:
            skills = getattr(getattr(proactor, 'sheet', None), 'skills', None)
            skills_text = str(list(skills.keys())) if isinstance(skills, dict) else ""
        except Exception:
            skills_text = ""

        try:
            mode_b_skills, mode_b_items = self._get_mode_b_vocab()
            skill_names: list[str] = []
            try:
                sk_obj = getattr(getattr(proactor, 'sheet', None), 'skills', None)
                if isinstance(sk_obj, dict):
                    skill_names = [str(k).strip() for k in sk_obj.keys() if str(k).strip()]
            except Exception:
                skill_names = []

            allowed_items = [s for s in (mode_b_items + inv_names) if s]
            allowed_skills = [s for s in (mode_b_skills + skill_names) if s]
        except Exception:
            allowed_items = []
            allowed_skills = []

        candidates = self._extract_rag_lock_candidates(
            user_input,
            allowed_items=allowed_items,
            allowed_skills=allowed_skills,
        )
        if not candidates:
            return None

        # Build a universe of categories to check. This stays category-filtered.
        categories = []
        if WorldbuildingCategory:
            try:
                categories = list(WorldbuildingCategory)
            except Exception:
                categories = []

        def term_in_text(term: str, text: str) -> bool:
            t = (term or '').strip().lower()
            if not t:
                return False
            return t in (text or '').lower()

        def is_actor_skill(term: str) -> bool:
            t = (term or '').strip().lower()
            if not t:
                return False
            # Safe, low-cost check: compare against skill names on the sheet.
            return t in (skills_text or '').lower()

        for term, kind in candidates:
            # Skills are always "available" if the actor has them.
            if is_actor_skill(term):
                continue

            # Conservative: if a capitalized token was extracted as "brand" but it is clearly part
            # of the current scene text (e.g., a street name), do not treat it as non-existent.
            if kind == "brand" and term_in_text(term, scene_text):
                continue

            # A: non-existent in world (supernatural/tech/brand/anachronism)
            if kind in {"supernatural", "tech", "brand", "anachronism"}:
                if not self._term_exists_in_rag(term, categories=categories):
                    return {
                        "judgment": "Not Possible",
                        "justification": f"That concept does not exist in this world: {term}",
                    }
                # Only *device-like tech* requires presence. Generic proper nouns (brand-ish)
                # or abstract anachronisms shouldn't be treated as physical inventory.
                if kind == "tech" and not term_in_text(term, inv_text) and not term_in_text(term, scene_text):
                    return {
                        "judgment": "Not Possible",
                        "justification": f"You cannot do that with {term} right now because it is not present or available in the current scene.",
                    }

            # B: exists in world, but not present/owned
            elif kind in {"item", "place", "entity"}:
                # If it doesn't exist in RAG, treat as A for safety.
                if not self._term_exists_in_rag(term, categories=categories):
                    return {
                        "judgment": "Not Possible",
                        "justification": f"That does not exist in this world: {term}",
                    }

                # Exists in world, but not in current state.
                # If the user is trying to USE it explicitly, it must be present.
                if kind == "item" and not term_in_text(term, inv_text) and not term_in_text(term, scene_text):
                    inv_list = ", ".join([n for n in inv_names if n])
                    inv_list = inv_list if inv_list else "(empty)"
                    return {
                        "judgment": "Not Possible",
                        "justification": (
                            f"The action requires {term}, but it is not in your inventory or present in the scene "
                            f"(inventory: {inv_list})."
                        ),
                    }

        return None

    def _get_mode_b_vocab(self) -> tuple[list[str], list[str]]:
        if not self.rag_system or not WorldbuildingCategory:
            return ([], [])

        mechanics_docs = []
        try:
            if hasattr(self.rag_system, 'get_by_category'):
                mechanics_docs = self.rag_system.get_by_category(WorldbuildingCategory.MECHANICS)
        except Exception:
            mechanics_docs = []

        combined = ""
        if mechanics_docs:
            combined = "\n\n".join([(getattr(d, 'content', '') or '') for d in mechanics_docs])
        else:
            try:
                combined = get_multi_category_context_for_llm(
                    self.rag_system,
                    query="skills vocab items vocab mechanics",
                    categories=[WorldbuildingCategory.MECHANICS],
                    max_tokens_per_category=800,
                    include_related=False,
                )
            except Exception:
                combined = ""

        if not combined:
            return ([], [])

        allowed_skills = extract_rag_section_list_items(
            combined,
            header_prefix='SKILLS VOCAB (Mode B)',
        )
        allowed_items = extract_rag_section_list_items(
            combined,
            header_prefix='ITEMS VOCAB (Mode B)',
        )

        return (allowed_skills, allowed_items)

    def _extract_rag_lock_candidates(
        self,
        user_input: str,
        *,
        allowed_items: Optional[list[str]] = None,
        allowed_skills: Optional[list[str]] = None,
    ) -> list[tuple[str, str]]:
        """Return list of (term, kind) where kind is one of: item/place/entity/tech/brand/endowment/anachronism."""
        try:
            import re
        except Exception:
            return []

        text = (user_input or "").strip()
        if not text:
            return []

        # Explicit tech/supernatural triggers (A-type)
        tech_keywords = [
            "iphone", "android", "uber", "tesla", "wifi", "internet", "cryptocurrency", "bitcoin",
            "glock", "ak-47", "ar-15", "drone", "laser", "smartphone",
        ]
        supernatural_keywords = [
            "spell", "fireball", "teleport", "teleportation", "levitate", "levitation", "mind read",
            "telepathy", "summon", "summoning", "magic", "mana",
        ]
 
        lowered = text.lower()
        out: list[tuple[str, str]] = []

        # If the user is issuing a UI/console command, do not attempt RAG-lock extraction.
        # These are out-of-world controls and should be routed by the main loop.
        try:
            if lowered.startswith('/') or lowered.startswith('__pmap_') or lowered.startswith('__pmap'):
                return []
        except Exception:
            pass

        # The word "app" is too generic and caused repeated false positives (e.g. "map app").
        # Also, substring matching would flag words like "approach" (contains "app").
        # Only treat it as modern tech when it appears as a standalone word AND combined with stronger signals.
        try:
            if re.search(r"\bapp\b", lowered):
                strong = (
                    ('iphone' in lowered)
                    or ('android' in lowered)
                    or ('smartphone' in lowered)
                    or ('internet' in lowered)
                    or ('wifi' in lowered)
                )
                if strong:
                    out.append(('app', 'tech'))
        except Exception:
            pass

        allowed_items_l = [str(s).strip() for s in (allowed_items or []) if str(s).strip()]
        allowed_skills_l = [str(s).strip() for s in (allowed_skills or []) if str(s).strip()]
        allowed_items_set = {s.lower() for s in allowed_items_l}
        allowed_skills_set = {s.lower() for s in allowed_skills_l}

        for k in tech_keywords:
            if k in lowered:
                out.append((k, "tech"))

        for k in supernatural_keywords:
            if k in lowered:
                out.append((k, "supernatural"))

        # NOTE: Avoid generic proper-noun extraction here; it caused repeated false positives.
        # A-type denials should come from explicit tech/supernatural triggers.

        # Item usage patterns (B-type): "my X", "with a X", "with my X", "use the X"
        item_patterns = [
            r"\bmy\s+([a-z][a-z\-']{2,}(?:\s+[a-z][a-z\-']{2,}){0,2})",
            r"\bwith\s+(?:a|an|the|my)\s+([a-z][a-z\-']{2,}(?:\s+[a-z][a-z\-']{2,}){0,2})",
            r"\buse\s+(?:a|an|the|my)\s+([a-z][a-z\-']{2,}(?:\s+[a-z][a-z\-']{2,}){0,2})",
        ]

        def _clean_item_term(raw: str) -> str:
            term = (raw or '').strip().lower()
            if not term:
                return ''

            # Stop at conjunctions / clause openers that commonly appear in actions.
            for splitter in (" and ", " then ", ",", ";", ":"):
                if splitter in term:
                    term = term.split(splitter, 1)[0].strip()

            # Drop trailing common action verbs if they slip into the capture.
            drop_words = {
                "start", "starting", "begin", "beginning", "try", "trying", "attempt", "attempting",
                "carve", "carving", "use", "using", "pull", "pulling", "take", "taking",
            }
            parts = [p for p in term.split() if p]
            while parts and parts[-1] in drop_words:
                parts = parts[:-1]
            term = " ".join(parts).strip()

            # Filter out common adjectives / action-nouns that appear after "with a ..." but
            # are not actually items (e.g. "with a hard pull").
            if term in {"hard", "soft", "quick", "firm", "strong", "tight"}:
                return ''
            if term.split() and term.split()[-1] in {"pull", "push", "shove", "look", "glance", "listen"}:
                return ''

            return term

        # Skill usage patterns: "use Stealth", "using Stealth"
        skill_patterns = [
            r"\buse\s+([a-z][a-z\-']{2,}(?:\s+[a-z][a-z\-']{2,}){0,2})",
            r"\busing\s+([a-z][a-z\-']{2,}(?:\s+[a-z][a-z\-']{2,}){0,2})",
        ]
        for pat in item_patterns:
            try:
                for m in re.finditer(pat, lowered):
                    term = _clean_item_term(m.group(1))
                    if term and (not allowed_items_set or term.lower() in allowed_items_set):
                        out.append((term, "item"))
            except Exception:
                pass

        for pat in skill_patterns:
            try:
                for m in re.finditer(pat, lowered):
                    term = _clean_item_term(m.group(1))
                    if term and (not allowed_skills_set or term.lower() in allowed_skills_set):
                        out.append((term, "skill"))
            except Exception:
                pass

        # Direct match against allowed vocab (more robust than regex phrase capture).
        # Prefer longer terms first to avoid partial matches.
        try:
            def _emit_matches(terms: list[str], kind: str) -> None:
                for t in sorted({x for x in terms if x}, key=lambda s: (-len(s), s.lower())):
                    tl = t.lower()
                    if not tl:
                        continue
                    if re.search(r"\b" + re.escape(tl) + r"\b", lowered):
                        out.append((t, kind))

            if allowed_items_l:
                _emit_matches(allowed_items_l, "item")
            if allowed_skills_l:
                _emit_matches(allowed_skills_l, "skill")
        except Exception:
            pass

        # De-duplicate while preserving order
        seen = set()
        deduped: list[tuple[str, str]] = []
        for term, kind in out:
            key = (term.lower().strip(), kind)
            if key in seen:
                continue
            seen.add(key)
            deduped.append((term.strip(), kind))

        return deduped[:10]

    def _term_exists_in_rag(self, term: str, categories: list[Any]) -> bool:
        t = (term or '').strip().lower()
        if not t or not self.rag_system:
            return False

        # Prefer category doc scanning when available (more reliable than similarity alone).
        if hasattr(self.rag_system, 'get_by_category') and categories:
            try:
                for cat in categories:
                    try:
                        docs = self.rag_system.get_by_category(cat)
                    except Exception:
                        docs = []
                    for doc in docs or []:
                        content = (getattr(doc, 'content', '') or '')
                        if t in content.lower():
                            return True
            except Exception:
                pass

        # Fallback: category-filtered context lookup
        try:
            for cat in categories or []:
                ctx = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=t,
                    categories=[cat],
                    max_tokens_per_category=200,
                    include_related=False,
                )
                if ctx and t in ctx.lower():
                    return True
        except Exception:
            return False

        return False

    def enforce_sensory_perception(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]:
        """
        Checks if the user's inquiry can be answered through the five senses (sight, smell, touch, hearing, taste).
        Returns the raw JSON data from the LLM.
        """
        prompt = f"""
You are a sensory perception validator for a simulation. Your only job is to determine if an inquiry can be answered through the five senses (sight, smell, touch, hearing, taste) based on what would be readily perceivable in the current scene.

**CRITICAL RULE: Only allow inquiries that ask for information that can be directly observed, heard, smelled, touched, or tasted by the character in their current position. Do not allow inquiries that require knowledge of motivations, intentions, thoughts, emotions, or abstract concepts that cannot be perceived through the physical senses.**

**Scene Description:**
{self.scene_description}

**Proactor Details:**
- Name: {proactor.sheet.name}
- Position: Current location in the scene
- Inventory: {proactor.sheet.inventory}

**Reactor Details:**
- Name: {reactor.sheet.name if reactor else "None (solo exploration)"}
- Inventory: {reactor.sheet.inventory if reactor else "N/A"}

**User's Inquiry:**
\"{user_input}\"

**Your Task:**
Analyze the user's inquiry. Can it be answered through direct sensory perception?
- An inquiry is \"Perceivable\" if it asks about something that can be seen, heard, smelled, touched, or tasted in the current scene (e.g., \"How many bandits are here?\", \"What does the room smell like?\", \"Can I hear footsteps?\", \"What does the surface feel like?\").
- An inquiry is \"Not Perceivable\" if it asks about motivations, thoughts, emotions, intentions, abstract concepts, or information that requires knowledge beyond sensory perception (e.g., \"Why is he trying to hurt me?\", \"What is he thinking?\", \"Is he lying?\", \"What happened here yesterday?\").

**EXAMPLES OF PERCEIVABLE INQUIRIES:**
- \"How many enemies are visible?\"
- \"What weapons can I see?\"
- \"Is there a door nearby?\"
- \"What sounds can I hear?\"
- \"Does the air smell of smoke?\"
- \"How far away is the nearest cover?\"
- \"What color is his cloak?\"
- \"Can I feel a breeze?\"

**EXAMPLES OF NON-PERCEIVABLE INQUIRIES:**
- \"Why is he attacking me?\"
- \"What are his intentions?\"
- \"Is he afraid?\"
- \"What happened here before I arrived?\"
- \"Does he recognize me?\"
- \"What is he planning to do next?\"
- \"Is this a trap?\"
- \"What does he want from me?\"

Respond with a JSON object with two keys:
1. \"judgment\": A string, either \"Perceivable\" or \"Not Perceivable\".
2. \"justification\": A string explaining your reasoning based on whether the inquiry can be answered through direct sensory perception.
"""
        return self._call_llm_for_json(prompt.strip())

    def detect_existing_actor_reference(self, user_input: str, existing_actors: list) -> Optional[Dict[str, Any]]:
        """
        Detect if user input refers to an existing actor.
        Delegates to the DynamicActorDetector.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
            
        Returns:
            Dict with existing actor reference data if found, None otherwise
        """
        return self.dynamic_detector.detect_existing_actor_reference(user_input, existing_actors)

    def detect_new_actor_mention(self, user_input: str, existing_actors: list) -> Optional[Dict[str, Any]]:
        """
        Detect if user input mentions a new actor that should be created.
        Delegates to the DynamicActorDetector.
        
        Args:
            user_input: The user's input text
            existing_actors: List of currently existing actors
            
        Returns:
            Dict with actor creation data if new actor detected, None otherwise
        """
        return self.dynamic_detector.detect_new_actor_mention(user_input, existing_actors)
    
    def detect_target_type(self, user_input: str, scene_description: str = "") -> Dict[str, Any]:
        """
        Determine if the user's action is targeting an NUA (animate) or INUA (inanimate).
        Delegates to the TargetDetector.
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context for better analysis
            
        Returns:
            Dict with target_type ('nua' or 'inua'), confidence, reasoning, and detected_target
        """
        return self.target_detector.detect_target_type(user_input, scene_description)
    
    def is_targeting_nua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an NUA (animate being).
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting NUA, False if targeting INUA
        """
        return self.target_detector.is_targeting_nua(user_input, scene_description)
    
    def is_targeting_inua(self, user_input: str, scene_description: str = "") -> bool:
        """
        Simple boolean check if action targets an INUA (inanimate object).
        
        Args:
            user_input: The user's action input
            scene_description: Current scene context
            
        Returns:
            True if targeting INUA, False if targeting NUA
        """
        return self.target_detector.is_targeting_inua(user_input, scene_description)

    def detect_monetary_exchange(self, user_input: str, proactor: 'Actor', scene_description: str) -> Dict[str, Any]:
        """
        Detects if the user's action involves an explicit monetary transaction.
        
        Returns a dict like:
        {
            "transaction_detected": bool,
            "transaction_type": "Purchase/Earning/Theft/Gift/Payment/Bribe/Loan/Gambling/Service/Sale/None",
            "amount": int (positive for gains, negative for losses),
            "item_or_service": str,
            "price_justification": str,
            "explicit_intent": bool,
            "payment_amount": int (for change calculation),
            "creates_item": bool (whether item should be added to inventory),
            "item_name": str (specific item name for inventory),
            "removes_item": str (item to remove from inventory for sales)
        }
        """
        proactor_name = getattr(proactor.sheet, 'name', 'User') if proactor else 'User'
        
        # Get proactor's current money for contextual pricing
        supply_status = proactor.sheet.statuses[StatusType.SUPPLY]
        current_money = supply_status.money_amount
        
        # Get sympathy with reactor if available (for reputation-based pricing)
        sympathy_context = ""
        try:
            # Extract potential reactor name from scene or user input
            # This is a simple heuristic - could be enhanced
            scene_lower = scene_description.lower()
            for word in ["shopkeeper", "clerk", "cashier", "vendor", "merchant", "dealer", "seller"]:
                if word in scene_lower:
                    # Try to get sympathy (will use default if not found)
                    sympathy_value = proactor.sheet.get_sympathy(word.title())
                    if sympathy_value != 1:  # Not default stranger value
                        if sympathy_value > 3:
                            sympathy_context = f"\n- Relationship: Friendly (expect ~10-20% discount)"
                        elif sympathy_value < -1:
                            sympathy_context = f"\n- Relationship: Hostile (expect ~10-20% markup)"
                    break
        except Exception:
            pass
        
        prompt = f"""
You are the Monetary Exchange Detector for the UTAS simulation.

**YOUR TASK:** Determine if {proactor_name}'s action involves an EXPLICIT monetary transaction.

**SCENE CONTEXT:**
{scene_description[:500]}

**USER'S ACTION:**
"{user_input}"

**PROACTOR CONTEXT:**
- Current Money: ${current_money:.2f}{sympathy_context}

**PRICING MODIFIERS:**
- Apply discounts (10-20%) for friendly relationships
- Apply markups (10-20%) for hostile relationships
- Consider location context (upscale vs budget establishments)
- Time-based: Late night services may cost more

**DETECTION CRITERIA:**

✅ **EXPLICIT TRANSACTIONS (Detect These):**
- **Purchase**: "I buy that shirt", "I purchase the gun", "I'll take the coffee"
- **Earning**: "I sell my watch", "I collect my paycheck", "I work for payment"
- **Theft**: "I steal the money", "I pickpocket the wallet", "I rob the register"
- **Payment**: "I pay the bill", "I give him $20", "I tip the waiter"
- **Gift**: "I give her money", "I donate to charity"
- **Bribe**: "I bribe the guard with $50", "I slip him some cash to look away"
- **Loan**: "I borrow $100 from him", "I loan her $50"
- **Gambling**: "I bet $20 on black", "I wager $50 on the poker hand"
- **Service**: "I pay the mechanic to fix my car", "I hire the detective for $200"
- **Sale**: "I sell my gun", "I pawn my watch"

❌ **NOT TRANSACTIONS (Ignore These):**
- Vague intentions: "I want to buy something", "I'm thinking about shopping"
- Window shopping: "I look at the prices", "I browse the store"
- Asking about prices: "How much is this?", "What's the cost?"
- **INQUIRIES are NOT transactions** - asking "How much is that shirt?" or "What do you sell here?" is INFORMATION GATHERING, not purchasing
- Past transactions: "I bought this yesterday"
- Hypotheticals: "If I had money, I'd buy..."

**PRICING GUIDELINES (Period-Appropriate):**
- Coffee/Soda: $0.50-$1.50
- Fast food meal: $2-$5
- Restaurant meal: $5-$20
- Shirt/Basic clothing: $10-$30
- Jeans: $15-$40
- Shoes: $20-$60
- Gun (handgun): $100-$300
- Gun (rifle): $150-$500
- Car (used): $1,000-$5,000
- Car (new): $5,000-$15,000
- Apartment rent (monthly): $200-$600
- House (purchase): $50,000-$150,000
- Paycheck (weekly, working class): $150-$300
- Paycheck (weekly, professional): $400-$800
- Bribes: $20-$500 (depending on risk/reward)
- Services: $50-$500 (depending on complexity)
- Gambling bets: $5-$1000 (player's choice)

**RESPONSE FORMAT (JSON ONLY):**
{{
    "transaction_detected": true/false,
    "transaction_type": "Purchase/Earning/Theft/Gift/Payment/Bribe/Loan/Gambling/Service/Sale/None",
    "amount": 0,
    "item_or_service": "description",
    "price_justification": "Brief explanation",
    "explicit_intent": true/false,
    "payment_amount": 0,
    "creates_item": true/false,
    "item_name": "specific item name",
    "removes_item": ""
}}

**FIELD EXPLANATIONS:**
- **amount**: Negative for spending, positive for gaining
- **payment_amount**: If user specifies payment (e.g., "I give him a $20 bill"), otherwise same as amount
- **creates_item**: true if transaction creates a physical item for inventory (purchases, theft of items)
- **item_name**: Specific name for inventory (e.g., "Leather Jacket", "Colt .45 Revolver")
- **removes_item**: Item name to remove from inventory (for sales)

**EXAMPLES:**

Input: "I buy that leather jacket"
Output: {{"transaction_detected": true, "transaction_type": "Purchase", "amount": -45, "item_or_service": "leather jacket", "price_justification": "Mid-range leather jacket", "explicit_intent": true, "payment_amount": -45, "creates_item": true, "item_name": "Leather Jacket", "removes_item": ""}}

Input: "I bribe the guard with $50"
Output: {{"transaction_detected": true, "transaction_type": "Bribe", "amount": -50, "item_or_service": "bribe to guard", "price_justification": "Standard bribe for minor infraction", "explicit_intent": true, "payment_amount": -50, "creates_item": false, "item_name": "", "removes_item": ""}}

Input: "I sell my revolver"
Output: {{"transaction_detected": true, "transaction_type": "Sale", "amount": 75, "item_or_service": "revolver", "price_justification": "Used handgun sells for ~$75", "explicit_intent": true, "payment_amount": 75, "creates_item": false, "item_name": "", "removes_item": "Revolver"}}

Input: "I give him a $20 bill for the $5 coffee"
Output: {{"transaction_detected": true, "transaction_type": "Purchase", "amount": -5, "item_or_service": "coffee", "price_justification": "Standard coffee price", "explicit_intent": true, "payment_amount": -20, "creates_item": false, "item_name": "", "removes_item": ""}}

**NOW ANALYZE THE ACTION ABOVE AND RESPOND WITH JSON ONLY.**
"""
        
        try:
            cache_context = {
                'task': 'detect_monetary_exchange',
                'user_input': user_input[:100],
                'scene': scene_description[:200]
            }
            result = self._call_llm_for_json(prompt, cache_context=cache_context)
            
            if not isinstance(result, dict):
                return self._get_default_monetary_response()
            
            # Validate required fields
            required_fields = ["transaction_detected", "transaction_type", "amount", "item_or_service", "explicit_intent"]
            for field in required_fields:
                if field not in result:
                    return self._get_default_monetary_response()
            
            return result
            
        except Exception as e:
            print(f"{Color.ERROR}Error detecting monetary exchange: {e}{Color.RESET}")
            return self._get_default_monetary_response()
    
    def _get_default_monetary_response(self) -> Dict[str, Any]:
        """Returns default response when monetary detection fails."""
        return {
            "transaction_detected": False,
            "transaction_type": "None",
            "amount": 0,
            "item_or_service": "",
            "price_justification": "",
            "explicit_intent": False,
            "payment_amount": 0,
            "creates_item": False,
            "item_name": "",
            "removes_item": ""
        }
    
    def generate_monetary_narrative(self, monetary_data: Dict[str, Any], proactor: 'Actor', reactor: 'Actor' = None, success: bool = True, change_amount: float = 0) -> str:
        """
        Generates a brief narrative description of a monetary transaction.
        
        Args:
            monetary_data: Monetary exchange metadata
            proactor: Actor performing the transaction
            reactor: Optional reactor actor
            success: Whether the transaction succeeded
            change_amount: Amount of change received (if any)
            
        Returns:
            Brief narrative string (e.g., "Vincent pays the cashier $5 to obtain his desired shirt...")
        """
        if not monetary_data.get("transaction_detected", False):
            return ""
        
        transaction_type = monetary_data.get("transaction_type", "None")
        amount = abs(monetary_data.get("amount", 0))
        item = monetary_data.get("item_or_service", "the item")
        proactor_name = proactor.sheet.name
        reactor_name = reactor.sheet.name if reactor else "the vendor"
        
        # Add change narrative if applicable
        change_text = f", receiving ${change_amount:.2f} in change" if change_amount > 0 else ""
        
        # Generate narrative based on transaction type
        if transaction_type == "Purchase":
            if success:
                return f"{proactor_name} pays {reactor_name} ${amount:.2f} to obtain {item}{change_text}..."
            else:
                return f"{proactor_name} cannot afford {item} (${amount:.2f} required)..."
        
        elif transaction_type == "Theft":
            if success:
                if monetary_data.get("creates_item"):
                    return f"{proactor_name} successfully steals {item} from {reactor_name}..."
                else:
                    return f"{proactor_name} successfully steals ${amount:.2f} from {reactor_name}..."
            else:
                return f"{proactor_name} fails to steal from {reactor_name}..."
        
        elif transaction_type == "Earning":
            return f"{proactor_name} earns ${amount:.2f} from {item}..."
        
        elif transaction_type == "Gift":
            return f"{proactor_name} gives ${amount:.2f} to {reactor_name}..."
        
        elif transaction_type == "Payment":
            return f"{proactor_name} pays ${amount:.2f} for {item}{change_text}..."
        
        elif transaction_type == "Bribe":
            if success:
                return f"{proactor_name} slips {reactor_name} ${amount:.2f} as a bribe..."
            else:
                return f"{proactor_name} attempts to bribe {reactor_name} with ${amount:.2f}, but fails..."
        
        elif transaction_type == "Loan":
            if amount > 0:  # Borrowing
                return f"{proactor_name} borrows ${amount:.2f} from {reactor_name}..."
            else:  # Lending
                return f"{proactor_name} loans ${amount:.2f} to {reactor_name}..."
        
        elif transaction_type == "Gambling":
            if success:
                return f"{proactor_name} wins ${amount:.2f} from {item}..."
            else:
                return f"{proactor_name} loses ${amount:.2f} on {item}..."
        
        elif transaction_type == "Service":
            return f"{proactor_name} pays ${amount:.2f} for {item}{change_text}..."
        
        elif transaction_type == "Sale":
            return f"{proactor_name} sells {item} for ${amount:.2f}..."
        
        else:
            return f"{proactor_name} completes a ${amount:.2f} transaction..."
    
    def process_monetary_transaction(self, monetary_data: Dict[str, Any], proactor: 'Actor', reactor: 'Actor' = None, success: bool = True) -> tuple[bool, str]:
        """
        Processes a monetary transaction with full enhancements.
        
        Args:
            monetary_data: Monetary exchange metadata from detector
            proactor: Actor performing the transaction
            reactor: Optional reactor actor (for purchases from NUAs, etc.)
            success: Whether the transaction succeeded (for contested actions)
            
        Returns:
            Tuple of (can_proceed: bool, narrative: str)
        """
        if not monetary_data.get("transaction_detected", False):
            return True, ""
        
        # Use enhanced processor for full feature set
        from enhanced_monetary_system import EnhancedMonetaryProcessor
        processor = EnhancedMonetaryProcessor(tracker_agent=getattr(self, 'tracker_agent', None))
        
        can_proceed, narrative, consequences = processor.process_enhanced_transaction(
            monetary_data, proactor, reactor, success
        )
        
        # Display transaction details
        transaction_type = monetary_data.get("transaction_type", "None")
        amount = monetary_data.get("amount", 0)
        item = monetary_data.get("item_or_service", "unknown item")
        justification = monetary_data.get("price_justification", "")
        
        if can_proceed:
            supply_status = proactor.sheet.statuses[StatusType.SUPPLY]
            
            print(f"\n{Color.SYSTEM}{'='*80}{Color.RESET}")
            print(f"{Color.SYSTEM}💵 MONETARY TRANSACTION{Color.RESET}")
            print(f"{Color.SYSTEM}{'='*80}{Color.RESET}")
            print(f"{Color.INFO}Transaction Type:{Color.RESET} {transaction_type}")
            print(f"{Color.INFO}Item/Service:{Color.RESET} {item}")
            print(f"{Color.INFO}Amount:{Color.RESET} ${abs(amount):.2f} {'(spending)' if amount < 0 else '(gaining)'}")
            if justification:
                print(f"{Color.INFO}Pricing:{Color.RESET} {justification}")
            
            # Display change if applicable
            if consequences.get("change_received", 0) > 0:
                print(f"{Color.SUCCESS}Change Received: ${consequences['change_received']:.2f}{Color.RESET}")
            
            # Display social consequences (only sympathy impacts from specific transaction types)
            if consequences.get("sympathy_shift", 0) != 0:
                shift = consequences["sympathy_shift"]
                impact = consequences.get("social_impact", "")
                print(f"{Color.INFO}Sympathy Impact: {'+' if shift > 0 else ''}{shift} with {reactor.sheet.name if reactor else 'other party'}{Color.RESET}")
                if impact:
                    print(f"{Color.INFO}   Reason: {impact}{Color.RESET}")
            
            # Build success message
            if amount < 0:
                message = f"💰 {proactor.sheet.name} spent ${abs(amount):.2f} on {item}"
            else:
                message = f"💰 {proactor.sheet.name} gained ${amount:.2f} from {item}"
            
            message += f"\n   New Balance: ${supply_status.money_amount:.2f}"
            
            # If there's a reactor and it's a purchase, show their balance
            if reactor and transaction_type in ["Purchase", "Bribe", "Service"] and amount < 0:
                reactor_supply = reactor.sheet.statuses[StatusType.SUPPLY]
                message += f"\n   └─ {reactor.sheet.name} received ${abs(amount):.2f} (Balance: ${reactor_supply.money_amount:.2f})"
            
            print(f"\n{Color.SUCCESS}{message}{Color.RESET}")
            print(f"{Color.NARRATIVE}📖 {narrative}{Color.RESET}")
            print(f"{Color.SYSTEM}{'='*80}{Color.RESET}\n")
        
        return can_proceed, narrative

    def detect_survival_intent(self, user_input: str, proactor: 'Actor') -> Optional[Dict[str, Any]]:
        """Use the LLM to classify survival intent (food/water/sleep/fulfillment) from free text.

        Returns a dict like:
        {
          "needs": ["food", "water", "sleep", "fulfillment"],
          "total_time_hours": 0.3,
          "confidence": 0.0-1.0,
          "reasoning": "brief explanation"
        }

        Notes:
        - Only detect explicit, immediate actions (eat, drink, take a nap, have breakfast, order coffee, etc.).
        - Do NOT trigger on mere intentions or navigation (going to a restaurant, heading to a diner) unless paired with consumption verbs.
        - Avoid substring traps (e.g., 'rest' in 'restaurant' must NOT count as sleep).
        """
        proactor_name = getattr(proactor.sheet, 'name', 'User') if proactor else 'User'
        prompt = f"""
Classify survival intent in the following input.

USER INPUT: "{user_input}"
PROACTOR: {proactor_name}

ALLOWED NEEDS:
- food (explicit consumption): eat/eating, have breakfast/lunch/dinner/meal/snack, grab a bite, dine (as a verb)
- water (explicit drink/hydrate): drink/sip/gulp water/coffee/tea/juice/soda/beer/wine, hydrate, quench thirst
- sleep: sleep, nap, doze, lie down, fall asleep (but NOT matching substrings like 'rest' inside 'restaurant')
- fulfillment: relax, socialize, chat, talk, play, read, hobby

STRICT RULES:
- Only detect if the text indicates performing the action now (explicit verb phrase as above).
- Do NOT detect for ordering alone; ordering ≠ consumption.
- Do NOT detect for mere intention or travel: going to/heading to a restaurant or diner alone is NOT sufficient.
- Avoid substring traps: 'restaurant' does not imply 'rest'. Match whole words.

EXAMPLES THAT TRIGGER (Return needs accordingly):
- FOOD: "I eat the sandwich", "I have breakfast", "We dine now"
- WATER: "I drink some water", "I sip my coffee", "Hydrate with tea"
- SLEEP: "I take a nap", "I lie down to sleep", "I doze off"
- FULFILLMENT: "I relax and read a book", "I socialize with the locals", "I play cards for a while"

EXAMPLES THAT DO NOT TRIGGER (Return needs: []):
- FOOD: "I look for something to eat", "I check the menu", "I head to the diner", "I might eat later", "I order a burger and fries"
- WATER: "I look for a water fountain", "Where can I get coffee?", "I think about grabbing a soda later", "Can I get a bottle of water?"
- SLEEP: "I rest my eyes on the horizon", "We pass by a rest stop", "I feel tired but keep going"
- FULFILLMENT: "I think about relaxing later", "I talk about reading a book tomorrow"

Respond with STRICT JSON (no extra text) with keys exactly:
{{
  "needs": ["food"|"water"|"sleep"|"fulfillment"],
  "total_time_hours": <float>,
  "confidence": <float between 0 and 1>,
  "reasoning": "<short>"
}}

If no explicit survival action is being performed, return:
{{"needs": [], "total_time_hours": 0.0, "confidence": 0.9, "reasoning": "No explicit survival action"}}
"""
        try:
            norm_text = (user_input or "").strip().lower()
            scene_snippet = (self.scene_description or "")[:120]
            cache_ctx = {"task": "detect_survival_intent", "text": norm_text, "scene": scene_snippet}
            result = self._call_llm_for_json(prompt, cache_context=cache_ctx)
            if not isinstance(result, dict):
                return None
            # Normalize and validate
            needs = result.get('needs', []) or []
            if not isinstance(needs, list):
                needs = []
            allowed = {"food", "water", "sleep", "fulfillment"}
            needs = [n for n in needs if isinstance(n, str) and n.lower() in allowed]
            total_time = result.get('total_time_hours')
            try:
                total_time = float(total_time)
            except Exception:
                total_time = 0.0
            confidence = result.get('confidence')
            try:
                confidence = float(confidence)
            except Exception:
                confidence = 0.0
            reasoning = result.get('reasoning', '')
            return {
                'needs': needs,
                'total_time_hours': total_time,
                'confidence': confidence,
                'reasoning': reasoning
            }
        except Exception:
            return None

    def interpret_user_action(self, user_input: str, proactor: 'Actor', time_context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Interprets the user's input into structured UTAS simulation mechanics.

        Args:
            user_input: The user's action input
            proactor: The actor taking the action
            time_context: Optional time-of-day context for narrative consistency
        """
        self._refresh_scene_from_tracker()

        # Extract mentions from user input
        if self.mention_system:
            try:
                actor_name = proactor.sheet.name if hasattr(proactor, 'sheet') else str(proactor)
                turn_num = 0  # Will be updated with actual turn number if available
                scene_id = ""  # Will be updated with actual scene ID if available

                self._extract_user_input_mentions(user_input, actor_name, turn_num, scene_id)
            except Exception as e:
                self.logger.log_system(f"Error extracting mentions from user action: {e}")

        # Use optimized prompt builder
        prompt = self._build_interpretation_prompt(user_input, proactor)
        
        # Enhance prompt with time context if available
        if time_context:
            prompt = self._enhance_prompt_with_time_context(prompt, time_context)
        cache_context = {
            'user_input': user_input,
            'scene': self.scene_description[:200],
            'proactor_skills': {k: v for k, v in proactor.sheet.skills.items() if v > 0},
            'proactor_inventory': [item.name for item in proactor.sheet.inventory[:5]],
            'proactor_effects': [effect.name for effect in proactor.sheet.effects] if proactor.sheet.effects else [],
            'method': 'interpret_user_action'
        }
        
        data = self._call_llm_for_json(prompt.strip(), cache_context=cache_context)
        
        # SELF-EFFECTS DEBUGGING - Capture raw AI output for USER ACTIONS
        print(f"{Color.SYSTEM}=== USER ACTION SELF-EFFECTS DEBUG START ==={Color.RESET}")
        print(f"{Color.SYSTEM}Raw AI Response Type: {type(data)}{Color.RESET}")
        if data:
            print(f"{Color.SYSTEM}Raw AI Response Keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}{Color.RESET}")
            if isinstance(data, dict):
                utas_factors = data.get('utas_factors', {})
                print(f"{Color.SYSTEM}UTAS Factors Keys: {list(utas_factors.keys()) if isinstance(utas_factors, dict) else 'Not a dict'}{Color.RESET}")
                
                self_effects_raw = utas_factors.get('self_effects') if isinstance(utas_factors, dict) else None
                print(f"{Color.SYSTEM}Raw self_effects found: {self_effects_raw is not None}{Color.RESET}")
                print(f"{Color.SYSTEM}Raw self_effects type: {type(self_effects_raw)}{Color.RESET}")
                print(f"{Color.SYSTEM}Raw self_effects content: {self_effects_raw}{Color.RESET}")
        else:
            print(f"{Color.SYSTEM}Raw AI Response is None or empty!{Color.RESET}")
        print(f"{Color.SYSTEM}=== USER ACTION SELF-EFFECTS DEBUG END ==={Color.RESET}")
        
        # Determine if proactor is the user actor for sensory perspective
        proactor_is_ua = getattr(proactor, 'is_user_actor', False) if proactor else False
        
        normalized_data = ResponseNormalizer.normalize_proactor_action_response(
            data, 
            proactor.sheet.name, 
            "takes action",
            proactor_is_ua
        )

        if "utas_factors" in normalized_data and "stress_level" in normalized_data["utas_factors"]:
            stress_level = extract_numeric_value(normalized_data["utas_factors"].get("stress_level", 3), default=3, min_val=1, max_val=5)
            stress_modifier = max(0, stress_level - 1)
            normalized_data["utas_factors"]["stress_modifier"] = stress_modifier

        if isinstance(data, dict) and "status_shift" in data and "status" in data["status_shift"]:
            normalized_data["utas_factors"]["status_to_shift"] = data["status_shift"]["status"]

        self._enrich_utas_factors_with_actor_data(normalized_data, proactor)
        # Apply social polarity heuristic: hugs/embraces default to Additive (SPIRIT) unless clearly coercive
        try:
            self._apply_social_polarity_rules(user_input, normalized_data)
        except Exception:
            pass
        # Enforce shared schema contract (UA proactor requires self_effects)
        validate_action_data(normalized_data, require_self_effects=True)
        return normalized_data

    def _apply_social_polarity_rules(self, user_text: str, action_data: Dict[str, Any]) -> None:
        """Heuristic: classify supportive social contact (hug/embrace) as Additive targeting SPIRIT
        unless the language is clearly coercive. Avoid ever using SYMPATHY as a status target.
        """
        if not isinstance(user_text, str) or not isinstance(action_data, dict):
            return
        txt = user_text.lower()
        if any(k in txt for k in ["hug", "embrace", "cuddle", "hold in a hug", "puts arms around", "arms around"]):
            # Detect coercive/forceful intent
            coercive_markers = [
                "force", "forcibly", "grab", "restrain", "against her will", "against his will",
                "without consent", "non-consensual", "unwanted", "impose", "pin", "trap"
            ]
            coercive = any(k in txt for k in coercive_markers)
            utas = action_data.setdefault('utas_factors', {}) if isinstance(action_data.get('utas_factors'), dict) else action_data.setdefault('utas_factors', {})
            # Always treat as Spirit-targeted social attempt for UTAS targeting (Sympathy remains a modifier only)
            utas['exchange_type'] = 'Spirit'
            utas['status_to_shift'] = 'SPIRIT'
            utas['shift_polarity'] = 'Subtractive' if coercive else 'Additive'

    def interpret_reactor_action(self, proactor_action_data: Dict[str, Any], proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]:
        """
        Interprets the reactor's defensive response into structured UTAS simulation mechanics.
        This handles the UTAS OBJECTIVE Step 4 reactor interpretation.
        """
        self._refresh_scene_from_tracker()
        # Use optimized prompt builder
        prompt = self._build_reactor_interpretation_prompt(proactor_action_data, proactor, reactor)
        cache_context = {
            'proactor_action': str(proactor_action_data.get('narrative_description', ''))[:200],
            'scene': self.scene_description[:200],
            'reactor_skills': {k: v for k, v in reactor.sheet.skills.items() if v > 0},
            'reactor_inventory': [item.name for item in reactor.sheet.inventory[:5]],
            'reactor_effects': [effect.name for effect in reactor.sheet.effects] if reactor.sheet.effects else [],
            'method': 'interpret_reactor_action'
        }
        
        data = self._call_llm_for_json(prompt.strip(), cache_context=cache_context)
        
        # Determine if reactor is the user actor for sensory perspective
        reactor_is_ua = getattr(reactor, 'is_user_actor', False) if reactor else False
        
        normalized_data = ResponseNormalizer.normalize_reactor_response(
            data, 
            reactor.sheet.name if reactor else "None", 
            "reacts defensively",
            reactor_is_ua
        )

        if "utas_factors" in normalized_data and "stress_level" in normalized_data["utas_factors"]:
            stress_level = extract_numeric_value(normalized_data["utas_factors"].get("stress_level", 3), default=3, min_val=1, max_val=5)
            stress_modifier = max(0, stress_level - 1)
            normalized_data["utas_factors"]["stress_modifier"] = stress_modifier

        self._enrich_reactor_utas_factors_with_actor_data(normalized_data, reactor)
        
        return normalized_data

    def _enrich_reactor_utas_factors_with_actor_data(self, normalized_data: Dict[str, Any], actor: 'Actor') -> None:
        """Enriches reactor UTAS factors with actual values from the actor's sheet."""
        from actor_sheet import SFactorType
        
        if "utas_factors" not in normalized_data:
            return
            
        factors = normalized_data["utas_factors"]
        
        s_trait_name = factors.get("reactor_reaction_s_trait")
        if s_trait_name and s_trait_name != "None":
            try:
                s_factor_type = SFactorType[s_trait_name.upper()]
                actual_value = actor.sheet.s_factors.get_factor(s_factor_type)
                factors["reactor_reaction_s_trait_value"] = actual_value
            except (KeyError, AttributeError) as e:
                raise ValueError(f"Invalid reactor S-trait '{s_trait_name}': {e}")
        else:
            raise ValueError(f"Missing or invalid reactor_reaction_s_trait: {s_trait_name}")
            
        skill_data = factors.get("reactor_reaction_skill", {})
        if isinstance(skill_data, dict) and skill_data.get("name") and skill_data.get("name") != "None":
            skill_name = skill_data["name"]
            actual_skill_value = actor.sheet.skills.get(skill_name, 0)
            skill_data["value"] = actual_skill_value
        elif not isinstance(skill_data, dict):
            raise ValueError(f"Invalid reactor skill data format: {skill_data}. Expected dict with name and value.")
            
        endowment_data = factors.get("reactor_reaction_endowment", {})
        if isinstance(endowment_data, dict) and endowment_data.get("name") and endowment_data.get("name") != "None":
            endowment_name = endowment_data["name"]
            actual_endowment_value = actor.sheet.endowments.get(endowment_name, 0) if actor.sheet.endowments else 0
            endowment_data["value"] = actual_endowment_value
        elif not isinstance(endowment_data, dict):
            raise ValueError(f"Invalid reactor endowment data format: {endowment_data}. Expected dict with name and value.")
            
        supplement_data = factors.get("reactor_reaction_supplement", {})
        if isinstance(supplement_data, dict) and supplement_data.get("name") and supplement_data.get("name") != "None":
            supplement_name = supplement_data["name"]
            actual_supplement_value = 0
            supplement_found = False
            for item in actor.sheet.inventory:
                if item.name.lower() == supplement_name.lower():
                    actual_supplement_value = item.supplement_bonus
                    supplement_found = True
                    break
        
            if not supplement_found:
                raise ValueError(f"Supplement '{supplement_name}' not found in {actor.sheet.name}'s inventory")
            else:
                supplement_data["value"] = actual_supplement_value
        elif not isinstance(supplement_data, dict):
            raise ValueError(f"Invalid supplement data format: {supplement_data}. Expected dict with name and value.")

    def _enrich_utas_factors_with_actor_data(self, normalized_data: Dict[str, Any], actor: 'Actor') -> None:
        """Enriches UTAS factors with actual values from the actor's sheet."""
        from actor_sheet import SFactorType
        
        if "utas_factors" not in normalized_data:
            return
            
        factors = normalized_data["utas_factors"]
        
        s_trait_name = factors.get("s_trait_to_use")
        if s_trait_name and s_trait_name != "None":
            try:
                # Handle common LLM mistake: SOCIALITY -> SOCIABILITY
                s_trait_upper = s_trait_name.upper()
                if s_trait_upper == "SOCIALITY":
                    s_trait_upper = "SOCIABILITY"
                    factors["s_trait_to_use"] = "SOCIABILITY"  # Fix the data
                    
                s_factor_type = SFactorType[s_trait_upper]
                actual_value = actor.sheet.s_factors.get_factor(s_factor_type)
                factors["s_trait_value"] = actual_value
            except (KeyError, AttributeError) as e:
                # Fallback to STURDINESS if invalid S-trait provided
                print(f"Warning: Invalid S-trait '{s_trait_name}': {e}. Defaulting to STURDINESS.")
                factors["s_trait_to_use"] = "STURDINESS"
                factors["s_trait_value"] = actor.sheet.s_factors.get_factor(SFactorType.STURDINESS)
        else:
            # Fallback to STURDINESS if no S-trait provided
            print(f"Warning: Missing s_trait_to_use in LLM response. Defaulting to STURDINESS.")
            factors["s_trait_to_use"] = "STURDINESS"
            factors["s_trait_value"] = actor.sheet.s_factors.get_factor(SFactorType.STURDINESS)
            
        skill_data = factors.get("skill", {})
        if isinstance(skill_data, dict) and skill_data.get("name") and skill_data.get("name") != "None":
            skill_name = skill_data["name"]
            actual_skill_value = actor.sheet.skills.get(skill_name, 0)
            skill_data["value"] = actual_skill_value
        elif not isinstance(skill_data, dict):
            raise ValueError(f"Invalid skill data format: {skill_data}. Expected dict with name and value.")
            
        endowment_data = factors.get("endowment", {})
        if isinstance(endowment_data, dict) and endowment_data.get("name") and endowment_data.get("name") != "None":
            endowment_name = endowment_data["name"]
            actual_endowment_value = actor.sheet.endowments.get(endowment_name, 0) if actor.sheet.endowments else 0
            endowment_data["value"] = actual_endowment_value
        elif not isinstance(endowment_data, dict):
            raise ValueError(f"Invalid endowment data format: {endowment_data}. Expected dict with name and value.")
            
        supplement_data = factors.get("supplement", {})
        if isinstance(supplement_data, dict) and supplement_data.get("name") and supplement_data.get("name") != "None":
            supplement_name = supplement_data["name"]
            actual_supplement_value = 0
            supplement_found = False
            for item in actor.sheet.inventory:
                if item.name.lower() == supplement_name.lower():
                    actual_supplement_value = item.supplement_bonus
                    supplement_found = True
                    break
        
            if not supplement_found:
                raise ValueError(f"Supplement '{supplement_name}' not found in {actor.sheet.name}'s inventory")
            else:
                supplement_data["value"] = actual_supplement_value
        elif not isinstance(supplement_data, dict):
            raise ValueError(f"Invalid supplement data format: {supplement_data}. Expected dict with name and value.")

    def detect_inquiry_or_action(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Dict[str, Any]:
        """
        Determines whether user input is a Fallible Action (situational), Contested Action (vs NUA/INUA), or Given Action (trivial).
        Returns structured data indicating the type and appropriate response.
        """
        self._refresh_scene_from_tracker()
        print(f"\n🔍 DEBUG: Analyzing input: '{user_input}'")

        # Extract user declarations and validate against facts
        if self.fact_system:
            try:
                # Get context for turn/scene
                turn_num = 0
                scene_id = ""
                actor_name = proactor.sheet.name

                # Extract user declarations (highest authority)
                self._extract_user_declarations(user_input, actor_name, turn_num, scene_id)

                # Validate action against established facts
                validation_warning = self._validate_action_against_facts(user_input, actor_name)
                if validation_warning:
                    self.logger.log_system(validation_warning)
                    # Could optionally include warning in prompt or return data
            except Exception as e:
                self.logger.log_system(f"Error in fact system integration: {e}")

        # Extract mentions from user input
        if self.mention_system:
            try:
                # Get context for turn/scene
                turn_num = 0
                scene_id = ""
                actor_name = proactor.sheet.name

                # Extract actor mentions from user input
                self._extract_user_input_mentions(user_input, actor_name, turn_num, scene_id)
            except Exception as e:
                self.logger.log_system(f"Error extracting mentions from user input: {e}")

        # Enrich with recent narrative context for better disambiguation
        recent_context = ""
        if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
            try:
                context_data = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=5,
                    importance_threshold="notable",
                    key_memories_system=self.key_memories_system  # Include memories for consistency
                )
                if context_data and context_data.strip():
                    recent_context = f"\n**Recent Narrative Context:**\n{context_data}\n"
            except Exception as e:
                self.logger.log_system(f"Warning: Could not retrieve narrative context for inquiry/action detection: {e}")

        # Get available NPCs from scene for better targeting
        available_npcs_text = ""
        if hasattr(self, 'actor_manager') and self.actor_manager:
            try:
                npcs = [actor for actor in self.actor_manager.get_all_actors() 
                       if actor.sheet.name != proactor.sheet.name]
                if npcs:
                    # Include occupations to disambiguate role labels like "barkeep" vs "drunken sleeper".
                    npc_lines = []
                    for npc in npcs:
                        try:
                            nm = npc.sheet.name
                            occ = getattr(npc.sheet, 'occupation', '') or ''
                            npc_lines.append(f"- {nm} (occupation: {occ})")
                        except Exception:
                            continue
                    if npc_lines:
                        available_npcs_text = "\n**AVAILABLE NPCs IN SCENE (AUTHORITATIVE):**\n" + "\n".join(npc_lines) + "\n"
            except Exception:
                pass
        
        # Get spatial context for movement detection
        try:
            from agents.spatial_context_helper import get_spatial_context_for_prompt
            spatial_context_text = get_spatial_context_for_prompt(proactor_name=f"YOU ({proactor.sheet.name})")
        except Exception:
            spatial_context_text = ""
        
        prompt = f"""
You are analyzing user input in a UTAS simulation.

**SCENE CONTEXT:**
{self.scene_description}{recent_context}{available_npcs_text}
{spatial_context_text}

**ACTORS PRESENT:**
- Proactor: {proactor.sheet.name}
- Reactor: {reactor.sheet.name if reactor else "None (solo exploration)"}

**INPUT:** "{user_input}"

**TASK 1 - CLASSIFY INPUT TYPE:**
- **CONTESTED ACTION**: Targets/affects another actor (NUA/INUA) with **social pressure, coercion, or transactional stakes** (persuasion, threat, attack, transaction, etc.). Examples: "Attack him", "Persuade guard to let me in", "Intimidate her", "Buy a drink", "Convince him to help".
- **FALLIBLE ACTION**: Targets environment/situation. Examples: "Climb wall", "Search room", "Pick lock", "Sprint to diner".
- **INQUIRY**: Pure information seeking (includes asking NPCs simple questions). Examples: "Where is it?", "I try to remember", "What do I see?", "Ask bartender what's on tap", "What's your name?", "Do you know Marcus?".
- **GIVEN ACTION**: Trivial/automatic actions. Examples: "Walk to desk", "Sit down", "Check the fridge", "Go to locker".
- **PASSIVE ACTION**: Doing nothing. Examples: "I wait", "I observe", "I do nothing".

**CRITICAL INQUIRY VS CONTESTED RULE:**
- Simple questions asking for information = **INQUIRY** (e.g., "Ask about X", "What's your name?", "Do you know Y?")
- Social pressure/manipulation = **CONTESTED ACTION** (e.g., "Persuade", "Intimidate", "Convince", "Charm")
- Transactions/exchanges = **CONTESTED ACTION** (e.g., "Buy", "Sell", "Trade")

**CRITICAL MOVEMENT VS INTERACTION RULE (STRICT):**
- If the input is ONLY moving/approaching/heading to an NPC (e.g., "I head to the bartender", "I approach Bram") with NO explicit interaction (no speaking/asking/buying/threatening/etc.), it is a GIVEN ACTION with explicit_movement=true.
- ONLY classify as contested_action if the input explicitly indicates interaction intent (speech/transaction/hostile/social action).

**TASK 2 - MOVEMENT DETECTION (CRITICAL - use BOTH tests):**

**A. LOGICAL TEST - Does the action imply going TO something?**
- YES: "sit on chair", "use terminal", "go to desk", "check the fridge", "approach guard", "head to door"
- NO: "look around", "think", "say something", "wait", "listen", "what do I see?"

**B. SPATIAL TEST - Check SPATIAL POSITIONS above:**
- If target object/actor is >5 units from YOU → movement REQUIRED
- If target is ≤5 units but action implies going TO it → movement still needed

**RULE: Set explicit_movement=true if EITHER test says YES**

**RESPONSE FORMAT (JSON):**
{{
    "input_type": "contested_action" | "fallible_action" | "inquiry" | "given_action" | "passive_action",
    "fallible_subtype": "physical" | "inquiry" | null,
    "explicit_movement": true | false,
    "movement_target": "target name or null",
    "addressed_to": "EXACT NPC name if contested_action, else null",
    "addressed_type": "nua" | "inua" | null,
    "confidence": "high" | "medium" | "low",
    "reasoning": "Brief explanation including movement logic"
}}

**CRITICAL NOTES:**
- For contested_action: ALWAYS fill addressed_to with the EXACT NPC name from scene
- addressed_type must be "nua" for people/actors and "inua" for objects/props. Do NOT mark a person as "inua".
- For given_action with movement: ALWAYS set explicit_movement=true and movement_target
- "Check X", "Go to X", "Sit on X", "Use X" = explicit_movement=true, movement_target="X"
"""

        try:
            print("🔍 DEBUG: Calling LLM for inquiry detection...")
            response_data = self._call_llm_for_json(
                prompt,
                cache_context={'type': 'inquiry_detection'},
                max_retries=2,
                timeout=20,
            )
            if response_data:
                print(f"🔍 DEBUG: LLM response: {response_data}")
                
                # Standardize fields
                if response_data.get('input_type') == 'contested_action' and not response_data.get('addressed_type'):
                    response_data['addressed_type'] = 'nua'
                if response_data.get('addressed_type') == 'inua' and response_data.get('input_type') == 'contested_action':
                    # If the model mislabels a person as inua, correct to nua.
                    response_data['addressed_type'] = 'nua'
                
                # Ensure fallible_subtype matches logic
                if response_data.get('input_type') == 'inquiry':
                    response_data['fallible_subtype'] = 'inquiry'
                elif response_data.get('input_type') == 'fallible_action' and not response_data.get('fallible_subtype'):
                    response_data['fallible_subtype'] = 'physical'

                # Strict sanitization: addressed_* only applies to contested_action.
                if response_data.get('input_type') != 'contested_action':
                    response_data['addressed_to'] = None
                    response_data['addressed_type'] = None

                # Strict requirement: contested_action must have addressed_to.
                if response_data.get('input_type') == 'contested_action' and not response_data.get('addressed_to'):
                    raise ValueError("contested_action missing addressed_to")

                # Soft correction: if model returns a generic ROLE label, map to best matching NPC by occupation.
                try:
                    if response_data.get('input_type') == 'contested_action' and response_data.get('addressed_to') and npcs:
                        raw = str(response_data.get('addressed_to') or '').strip()
                        raw_l = raw.lower()
                        # If it's already an exact name, keep it.
                        exact_names = {str(n.sheet.name): n for n in npcs if getattr(getattr(n, 'sheet', None), 'name', None)}
                        if raw in exact_names:
                            return response_data

                        # Heuristic role keywords → occupation match.
                        role_keywords = {
                            'barkeep': ['barkeep', 'bartender', 'tavern keeper', 'tavernkeeper', 'keeper'],
                            'server': ['wench', 'server', 'serving', 'waitress', 'waiter'],
                            'drunk': ['drunk', 'drunken', 'sleeper', 'regular'],
                        }

                        desired_role = None
                        for role, keys in role_keywords.items():
                            if any(k in raw_l for k in keys):
                                desired_role = role
                                break

                        if desired_role:
                            best = None
                            best_score = -1
                            for n in npcs:
                                try:
                                    occ_l = str(getattr(n.sheet, 'occupation', '') or '').lower()
                                    score = 0
                                    if desired_role == 'barkeep' and any(k in occ_l for k in ['barkeep', 'bartender', 'tavern']):
                                        score = 3
                                    elif desired_role == 'server' and any(k in occ_l for k in ['wench', 'server', 'maid', 'barmaid', 'wait']):
                                        score = 3
                                    elif desired_role == 'drunk' and any(k in occ_l for k in ['drunk', 'drunken', 'sleeper', 'regular']):
                                        score = 3
                                    # Weak fallback: role keyword appears in name
                                    nm_l = str(getattr(n.sheet, 'name', '') or '').lower()
                                    if score == 0 and any(k in nm_l for k in role_keywords.get(desired_role, [])):
                                        score = 1
                                    if score > best_score:
                                        best_score = score
                                        best = n
                                except Exception:
                                    continue

                            if best is not None and best_score > 0:
                                response_data['addressed_to'] = best.sheet.name
                                response_data['addressed_type'] = 'nua'
                except Exception:
                    pass
                    
                return response_data
            else:
                raise ValueError("LLM returned no data")
        except KeyboardInterrupt:
            print("🔍 DEBUG: LLM inquiry detection interrupted by user")
            raise
        except Exception as e:
            print(f"🔍 DEBUG: LLM error: {e}")
            self.logger.log_error(f"Error in inquiry detection: {e}")

        # Strict mode: do not guess.
        raise RuntimeError("Failed to classify input via InterpreterAgent")

    def detect_explicit_movement(self, user_input: str, classification_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Detect if user explicitly requested movement.
        Prioritizes LLM classification if provided, otherwise falls back to regex.
        """
        # 1. Use LLM Classification if available
        if classification_data and 'explicit_movement' in classification_data:
            return {
                "has_explicit_movement": classification_data['explicit_movement'],
                "movement_type": "llm_detected", # Generic
                "target": classification_data.get('movement_target'),
                "confidence": classification_data.get('confidence', 'high')
            }

        # 2. Fallback to Regex (Safety Net)
        user_input_lower = user_input.lower()
        
        # Movement verbs that indicate explicit movement intent
        movement_verbs = [
            'walk', 'move', 'go', 'head', 'run', 'sprint', 'jog',
            'approach', 'step', 'stride', 'rush', 'hurry', 'dash',
            'sneak', 'creep', 'crawl', 'climb', 'jump', 'enter',
            'exit', 'leave', 'travel', 'drive', 'ride',
            # Gerunds and continuations
            'walking', 'moving', 'going', 'heading', 'running', 'sprinting', 'jogging',
            'approaching', 'stepping', 'striding', 'rushing', 'hurrying', 'dashing',
            'sneaking', 'creeping', 'crawling', 'climbing', 'jumping', 'entering',
            'exiting', 'leaving', 'traveling', 'travelling', 'driving', 'riding',
            'continue', 'continuing', 'keep'
        ]
        
        # Prepositions that indicate movement direction
        movement_prepositions = ['to', 'toward', 'towards', 'into', 'through', 'across', 'over']
        
        # Check for explicit movement verbs
        detected_verb = None
        for verb in movement_verbs:
            if f" {verb} " in f" {user_input_lower} " or user_input_lower.startswith(f"{verb} "):
                detected_verb = verb
                break
        
        if not detected_verb:
            return {
                "has_explicit_movement": False,
                "movement_type": None,
                "target": None,
                "confidence": "high"
            }
        
        # Check for movement preposition to extract target
        target = None
        articles = ['the', 'a', 'an']
        for prep in movement_prepositions:
            if f" {prep} " in user_input_lower:
                # Extract what comes after the preposition (full phrase, not just first word)
                parts = user_input_lower.split(f" {prep} ", 1)
                if len(parts) > 1:
                    target_phrase = parts[1].strip()
                    # Remove leading articles
                    target_words = target_phrase.split()
                    if target_words and target_words[0] in articles:
                        target_words = target_words[1:]
                    target = ' '.join(target_words) if target_words else None
                break
        
        return {
            "has_explicit_movement": True,
            "movement_type": detected_verb,
            "target": target,
            "confidence": "high" if target else "medium"
        }

    def determine_skill_for_action(self, action: str, available_skills: list) -> Dict[str, Any]:
        """
        Determine the most relevant skill for an action using LLM analysis.
        
        Args:
            action: The action being attempted
            available_skills: List of skill names the actor possesses
            
        Returns:
            Dict containing skill name and reasoning, or None if LLM fails
        """
        if not available_skills:
            return None
            
        skills_list = ", ".join(available_skills)
        
        prompt = f"""
        Determine the most relevant skill for this fallible action from the available skills.
        
        ACTION: "{action}"
        AVAILABLE SKILLS: {skills_list}
        
        **SKILL SELECTION CRITERIA:**
        - Use ONLY skills that exist in the available skills list above
        - **Primary Selection**: Choose skills that directly relate to the action being performed
        - **Cross-Skill Applicability**: Skills can apply creatively if they logically enhance the action
        
        **Examples of Direct Application**: 
        - "perception" for: seeing, noticing, observing, detecting, hearing, spotting
        - "athletics" for: climbing, jumping, running, physical movement, agility
        - "academics" for: remembering, analyzing, solving puzzles, knowledge tasks
        - "empathy" for: understanding people, social interactions, reading emotions
        - "stealth" for: hiding, sneaking, moving quietly, avoiding detection
        - "intimidation" for: threatening, coercing, appearing menacing
        
        **Examples of Cross-Skill Application**: 
        - "acrobatics" for stealth actions (graceful, silent movement)
        - "performance" for deception (acting ability enhances lying)
        - "medicine" for intimidation (knowledge of anatomy makes threats more credible)
        - "engineering" for problem-solving (understanding of mechanics)
        - "history" for social situations (cultural knowledge aids interaction)
        
        **Selection Priority**: 1) Direct match, 2) Creative cross-application, 3) Use "none"
        **Justification Required**: Always explain HOW the skill applies to the specific action
        
        If NO skill is truly relevant to the action, respond with "none" as the skill name.
        
        Respond with JSON:
        {{
            "skill": "skill_name",
            "reasoning": "Detailed explanation of why this skill is most relevant and how it applies"
        }}
        """
        
        try:
            try:
                from persistent_context_manager import get_context_manager
                cm = get_context_manager()
                if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                    facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                    if facts_block and isinstance(prompt, str) and prompt.strip():
                        prompt = f"{facts_block}\n\n{prompt}"
            except Exception:
                pass

            # Enhance prompt with time context (if available) for consistency
            try:
                if getattr(self, 'time_context', None):
                    prompt = self._enhance_prompt_with_time_context(prompt, self.time_context)
            except Exception:
                pass
            # Use centralized robust LLM call
            response_text = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="SKILL DETERMINATION"
            )

            if not response_text:
                return None
            
            # Enhanced JSON parsing with error recovery
            result = extract_and_parse_json(response_text)
            if not result:
                self.logger.log_error("No valid JSON found in skill determination response")
                return None
        
            # Validate that the chosen skill is in available skills or is "none"
            chosen_skill = result.get("skill", "")
            if chosen_skill == "none":
                return {"skill": "No relevant skill", "reasoning": result.get("reasoning", "No applicable skill found")}
            elif chosen_skill not in available_skills:
                self.logger.log_error(f"LLM chose unavailable skill: {chosen_skill}. Available: {available_skills}")
                return None
        
            return result
            
        except Exception as e:
            self.logger.log_error(f"Error in skill determination: {e}")
            return None

    def determine_best_endowment(self, action: str, available_endowments: list) -> Dict[str, Any]:
        """
        Determine the most appropriate endowment for a fallible action using LLM analysis.
        
{{ ... }}
        Args:
            action: The action being attempted
            available_endowments: List of endowment names the actor has
            
        Returns:
            Dict containing endowment name and reasoning
        """
        if not available_endowments:
            return {"endowment": "No relevant endowment", "reasoning": "No endowment abilities available"}
        
        prompt = f"""
You are analyzing a fallible action to determine which endowment ability is most appropriate from the available options.

**ACTION:** {action}
**AVAILABLE ENDOWMENTS:** {', '.join(available_endowments)}

**ENDOWMENT SELECTION CRITERIA:**
- Use ONLY endowments that exist in the available list above
- Select endowments that enhance or modify the action being performed
- **Examples of Appropriate Usage**:
  - "Enhanced Strength" for physical actions requiring force
  - "Mind Reading" for social manipulation or information gathering
  - "Invisibility" for stealth-based actions
  - "Telepathy" for communication or mental influence
  - "Enhanced Speed" for time-sensitive or agility-based actions

**Selection Rule**: If no endowment directly enhances the specific action being performed, use "No relevant endowment"

**RESPONSE FORMAT (JSON):**
{{
    "endowment": "exact_endowment_name_from_list" or "No relevant endowment",
    "confidence": "high" or "medium" or "low",
    "reasoning": "Detailed explanation of why this endowment ability is most appropriate and how it enhances the action"
}}
"""

        try:
            try:
                from persistent_context_manager import get_context_manager
                cm = get_context_manager()
                if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                    facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                    if facts_block and isinstance(prompt, str) and prompt.strip():
                        prompt = f"{facts_block}\n\n{prompt}"
            except Exception:
                pass

            # Enhance prompt with time context (if available) for consistency
            try:
                if getattr(self, 'time_context', None):
                    prompt = self._enhance_prompt_with_time_context(prompt, self.time_context)
            except Exception:
                pass
            # Use centralized robust LLM call
            response_text = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="ENDOWMENT DETERMINATION"
            )
            
            if not response_text:
                return None
            
            result = extract_and_parse_json(response_text)
            return result
                
        except Exception as e:
            return None

    def determine_supplement_for_action(self, action: str, available_inventory: list) -> Dict[str, Any]:
        """
        Determine the most appropriate equipment/item for a fallible action using LLM analysis.
        
        Args:
            action: The action being attempted
            available_inventory: List of items the actor has in inventory
            
        Returns:
            Dict containing supplement name and reasoning
        """
        if not available_inventory:
            return {"supplement": "No relevant supplement", "reasoning": "No items available in inventory"}
        
        items_list = ", ".join([item.name for item in available_inventory])
        
        prompt = f"""
You are analyzing a fallible action to determine which equipment/item is most appropriate from the available inventory.

**ACTION:** {action}
**AVAILABLE INVENTORY:** {items_list}

**SUPPLEMENT SELECTION CRITERIA:**
- Use ONLY items/equipment that exist in the available inventory list above
- **STRICT RELEVANCE REQUIRED**: Items must be directly used in or essential to the specific action
- **Examples of CORRECT supplement usage**:
  - "Sword" for sword attacks or weapon-based combat
  - "Lockpicks" for picking locks specifically
  - "Rope" for climbing, binding, or rappelling
  - "Shield" for defensive actions
  - "Bandages" for healing actions
  - "Crowbar" for prying or breaking actions
- **Examples of INCORRECT supplement usage**:
  - "Sword" for punching (not using the sword)
  - "Lockpicks" for intimidation (not picking locks)
  - "Rope" for social persuasion (not physically using rope)
  - "Bandages" for combat attacks (not healing)

**Selection Rule**: If the item is not physically used or directly essential to performing the action, use "No relevant supplement"
**When in doubt**: Choose "No relevant supplement" rather than forcing an irrelevant item

**RESPONSE FORMAT (JSON):**
{{
    "supplement": "exact_item_name_from_list" or "No relevant supplement",
    "confidence": "high" or "medium" or "low",
    "reasoning": "Detailed explanation of why this item is most appropriate and how it is directly used in the action"
}}
"""

        try:
            try:
                from persistent_context_manager import get_context_manager
                cm = get_context_manager()
                if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                    facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                    if facts_block and isinstance(prompt, str) and prompt.strip():
                        prompt = f"{facts_block}\n\n{prompt}"
            except Exception:
                pass

            # Enhance prompt with time context (if available) for consistency
            try:
                if getattr(self, 'time_context', None):
                    prompt = self._enhance_prompt_with_time_context(prompt, self.time_context)
            except Exception:
                pass
            # Use centralized robust LLM call
            response_text = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="SUPPLEMENT DETERMINATION"
            )
            
            if not response_text:
                return {"supplement": "No relevant supplement", "reasoning": "LLM returned empty response"}
            
            result = extract_and_parse_json(response_text)
            if result:
                return result
            return {"supplement": "No relevant supplement", "reasoning": "JSON parsing failed"}
                
        except Exception as e:
            return {"supplement": "No relevant supplement", "reasoning": f"LLM analysis failed: {e}"}

    def interpret_fallible_action(self, user_action: str, proactor: 'Actor') -> Dict[str, Any]:
        """
        Interpret fallible action using comprehensive UTAS analysis - same depth as contested actions.
        Returns complete mechanical breakdown for fallible action execution.
        """
        try:
            prompt = self._build_fallible_action_interpretation_prompt(user_action, proactor)

            try:
                from persistent_context_manager import get_context_manager
                cm = get_context_manager()
                if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                    facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                    if facts_block and isinstance(prompt, str) and prompt.strip():
                        prompt = f"{facts_block}\n\n{prompt}"
            except Exception:
                pass

            # Enhance prompt with time context (if available) for consistency
            try:
                if getattr(self, 'time_context', None):
                    prompt = self._enhance_prompt_with_time_context(prompt, self.time_context)
            except Exception:
                pass

            # Use centralized robust LLM call
            response_text = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.3,
                max_tokens=500,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="FALLIBLE ACTION"
            )
            
            if not response_text:
                self.logger.log_system("Empty response from LLM for fallible action interpretation")
                return self._create_fallback_interpretation(user_action, proactor)
            
            # Parse JSON response using centralized utility
            interpretation_data = extract_and_parse_json(response_text)
            if not interpretation_data:
                self.logger.log_system(f"Failed to parse fallible action interpretation JSON")
                self.logger.log_system(f"Raw response: {response_text[:200]}")
                return self._create_fallback_interpretation(user_action, proactor)
            
            # Fill required fields defensively (LLM output can be partial)
            try:
                raw_words = [w.strip(" \t\n\r.,;:!?\"'()[]{}") for w in user_action.strip().split()]
                raw_words = [w for w in raw_words if w]
                stop_words = {
                    "i", "we", "you", "he", "she", "they", "it",
                    "my", "our", "your", "his", "her", "their",
                    "me", "us", "him", "them",
                    "then", "and", "but", "so", "to", "a", "an", "the",
                    "quietly", "carefully", "slowly", "quickly"
                }
                best = None
                for w in raw_words:
                    if w.lower() not in stop_words:
                        best = w
                        break
                if not best and raw_words:
                    best = raw_words[0]
                simple_noun = best.capitalize() if best else "Action"
            except Exception:
                simple_noun = "Action"

            if 'action_noun' not in interpretation_data or not str(interpretation_data.get('action_noun', '')).strip():
                interpretation_data['action_noun'] = simple_noun
            if 'action_description' not in interpretation_data or not str(interpretation_data.get('action_description', '')).strip():
                interpretation_data['action_description'] = user_action
            if 'narrative_description' not in interpretation_data or not str(interpretation_data.get('narrative_description', '')).strip():
                interpretation_data['narrative_description'] = f"The character attempts to {user_action.lower()}"

            # CRITICAL USER AGENCY: For UA, never rewrite the user's action text.
            # Keep UTAS mechanics, but preserve the exact raw input as the action/narrative.
            try:
                if getattr(proactor, 'is_user_actor', False):
                    # Preserve the interpreter-cleaned phrasing separately for reporting.
                    try:
                        cleaned = (
                            interpretation_data.get('interpreted_user_action')
                            or interpretation_data.get('action_description')
                            or interpretation_data.get('narrative_description')
                        )
                        cleaned = (cleaned or '').strip()
                        if cleaned:
                            interpretation_data['interpreted_user_action'] = cleaned
                    except Exception:
                        pass
                    interpretation_data['raw_user_action'] = user_action
                    interpretation_data['action_description'] = user_action
                    interpretation_data['narrative_description'] = user_action
            except Exception:
                pass
            if 'utas_factors' not in interpretation_data or not isinstance(interpretation_data.get('utas_factors'), dict):
                interpretation_data['utas_factors'] = {}
            if 'self_effects' not in interpretation_data or not isinstance(interpretation_data.get('self_effects'), list):
                interpretation_data['self_effects'] = []
            
            # Validate UTAS factors and override with actor sheet values
            utas_factors = interpretation_data['utas_factors']
            required_utas_fields = [
                'exchange_type', 'status_to_shift', 's_trait_to_use', 's_trait_justification',
                'skill', 'skill_justification', 'endowment', 'supplement', 'stress_level', 'stress_justification',
                'shift_type', 'shift_type_justification', 'shift_polarity', 'shift_polarity_justification'
            ]

            defaults = {
                "exchange_type": "Spirit",
                "status_to_shift": "Spirit",
                "s_trait_to_use": "Shadow",
                "s_trait_justification": "Default perception-based fallible action",
                "skill": {"name": "none", "value": 0},
                "skill_justification": "No specific skill applies",
                "endowment": {"name": "none", "value": 0},
                "supplement": {"name": "none", "value": 0},
                "stress_level": 3,
                "stress_justification": "Standard fallible action difficulty",
                "shift_type": "Temporary",
                "shift_type_justification": "Information gathering is temporary",
                "shift_polarity": "Additive",
                "shift_polarity_justification": "Gaining information is additive",
            }

            for field in required_utas_fields:
                if field not in utas_factors or utas_factors.get(field) in (None, ""):
                    utas_factors[field] = defaults.get(field)

            # CRITICAL: Override LLM values with authoritative actor sheet values
            self._override_with_actor_sheet_values(utas_factors, proactor)

            # Log successful interpretation
            self.logger.log_system(f"Successfully interpreted fallible action: {interpretation_data['action_noun']}")

            return interpretation_data
            
        except Exception as e:
            self.logger.log_system(f"Error interpreting fallible action: {e}")
            # Return fallback interpretation - preserve original user action
            # Extract a simple action noun from the user action
            raw_words = [w.strip(" \t\n\r.,;:!?\"'()[]{}") for w in user_action.strip().split()]
            raw_words = [w for w in raw_words if w]
            stop_words = {
                "i", "we", "you", "he", "she", "they", "it",
                "my", "our", "your", "his", "her", "their",
                "me", "us", "him", "them",
                "then", "and", "but", "so", "to", "a", "an", "the",
                "quietly", "carefully", "slowly", "quickly"
            }
            best = None
            for w in raw_words:
                if w.lower() not in stop_words:
                    best = w
                    break
            if not best and raw_words:
                best = raw_words[0]
            simple_noun = best.capitalize() if best else "Action"
            
            return {
                "action_noun": simple_noun,
                "action_description": user_action,  # Preserve original action
                "narrative_description": user_action,
                "utas_factors": {
                    "exchange_type": "Spirit",
                    "status_to_shift": "Spirit",
                    "s_trait_to_use": "Shadow",
                    "s_trait_justification": "Default perception-based fallible action",
                    "skill": {"name": "none", "value": 0},
                    "skill_justification": "No specific skill applies",
                    "endowment": {"name": "none", "value": 0},
                    "supplement": {"name": "none", "value": 0},
                    "stress_level": 3,
                    "stress_justification": "Standard fallible action difficulty",
                    "shift_type": "Temporary",
                    "shift_type_justification": "Information gathering is temporary",
                    "shift_polarity": "Additive",
                    "shift_polarity_justification": "Gaining information is additive"
                },
                "self_effects": []
            }

    def _build_fallible_action_interpretation_prompt(self, user_action: str, proactor: 'Actor') -> str:
        """Build comprehensive fallible action interpretation prompt using the same UTAS analysis as contested actions"""
        proactor_data = self._build_detailed_actor_data(proactor)
        ua_dialogue_weight = self._estimate_dialogue_weight(user_action)
        
        # Check if this is the User Actor for perspective instructions
        is_user_actor = getattr(proactor, 'is_user_actor', False)
        
        # Build perspective instruction based on actor type
        if is_user_actor:
            perspective_instruction = "Write in SECOND PERSON using you/your with correct verb forms (You make, you approach, your voice)."
        else:
            perspective_instruction = f"Write in THIRD PERSON using the actor name ({proactor_data['name']}) with third-person pronouns (he/she/they/their)."
        
        # Get recent narrative context for spatial/positional awareness
        recent_context = ""
        if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
            try:
                context_data = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=5, 
                    importance_threshold="notable"
                )
                if context_data and context_data.strip():
                    recent_context = f"""
**Recent Action Context (for spatial/positional awareness):**
{context_data}

**IMPORTANT:** Use this recent context to understand the character's current position, location, and any spatial changes from previous actions. If the character climbed somewhere, moved to a different area, or changed position, factor this into your interpretation."""
            except Exception as e:
                self.logger.log_system(f"Warning: Could not retrieve narrative context for fallible action interpretation: {e}")
        
        return f"""You are a UTAS simulation interpreter. Analyze the user's fallible action and provide comprehensive mechanical breakdown.

**Scene Context:**
{self.scene_description}{recent_context}

**Actor Details:**
Name: {proactor_data['name']}
S-Factors: {proactor_data['s_factors']}
Skills: {proactor_data['skills']}
Endowments: {proactor_data['endowments']}
Inventory: {proactor_data['inventory']}
Current Status: {proactor_data['statuses']}

**User Action:** "{user_action}"

**🚨 SPATIAL CONTEXT AWARENESS CRITICAL INSTRUCTIONS 🚨**
**ALWAYS consider the character's current position and recent spatial changes when interpreting actions:**

**High-Risk Spatial Scenarios (Stress Level 4-5):**
- Jumping/falling from heights (roofs, buildings, cliffs, bridges)
- Actions involving significant elevation changes
- Movement in dangerous vertical spaces

**Spatial Keywords to Include in Descriptions:**
- Reference specific heights: "roof", "three-story", "30 feet", "building height"
- Acknowledge gravity/physics: "fall", "drop", "plummet", "impact"
- Describe spatial context: "from above", "down below", "height advantage"

**Example Spatial Interpretations:**
- "I jump off" (when on roof) → "Vincent attempts to jump off the three-story building roof, a dangerous 30-foot fall to the alley below" (Stress: 5)
- "I climb up" → "Vincent climbs the fire escape ladder to reach the rooftop" (Stress: 2-3)
- "I look around" (when elevated) → "Vincent surveys the area from his elevated position on the roof" (Stress: 1)

**IMPORTANT DISTINCTIONS:**
- **S-TRAITS (Actor Capabilities)**: Swiftness, Sociability, Sturdiness, Smarts, Shadow - These are the actor's inherent abilities
- **STATUSES (Dynamic Conditions)**: Stamina, Spirit, Supply, Sympathy - These are changeable conditions that can be targeted

**CRITICAL: YOU MUST PROVIDE ALL FIELDS LISTED BELOW. NO EXCEPTIONS.**
**INCOMPLETE RESPONSES WILL BE REJECTED AND CAUSE SYSTEM ERRORS.**

**Required Analysis:**
Provide a JSON response with EXACTLY the following structure:
{{
    "action_noun": "Brief action name",
    "action_description": "Detailed description of what the actor is attempting",
    "narrative_description": "Rich, immersive description of the action. **PERSPECTIVE: {perspective_instruction}** **🚨 CRITICAL DIALOGUE RULES - NEVER INVENT SPECIFIC WORDS 🚨:** (1) If user input contains QUOTED dialogue (e.g. 'I say \"Hello\"'), include those EXACT words verbatim. (2) If user input describes dialogue WITHOUT quotes (e.g. 'I ask what they are doing', 'I greet them', 'I tell them to leave'), this IS dialogue - describe it as speech but use their EXACT phrasing, not invented quotes. 'I ask what they're doing' → 'You ask what they're doing' (NOT 'You say \"What are you doing?\"'). (3) NEVER fabricate specific quoted words the user didn't provide. (4) You CAN add sensory details (tone, body language) but NOT invented dialogue content.",
    "utas_factors": {{
        "exchange_type": "Supply/Stamina/Spirit/Sympathy - what type of STATUS conflict this represents. **For physical actions, this MUST be Stamina. For mental actions/intimidation/threats, this MUST be Spirit.**", 
        "status_to_shift": "The target STATUS on the environment/self (Stamina/Spirit/Supply/Sympathy)",
        "s_trait_to_use": "Primary S-TRAIT name (Swiftness/Sociability/Sturdiness/Smarts/Shadow)",
        "s_trait_value": "Numerical value of the S-TRAIT",
        "s_trait_justification": "Detailed explanation of why this S-TRAIT applies",
        "skill": {{"name": "skill_name", "value": skill_value}},
        "skill_justification": "Detailed explanation of how this skill applies to the action",
        "endowment": {{"name": "endowment_name", "value": endowment_value}},
        "endowment_justification": "Detailed explanation of how this endowment applies to the action",
        "supplement": {{"name": "supplement_name", "value": supplement_value}},
        "stress_level": "1-5 difficulty rating",
        "stress_justification": "Explanation of why this stress level applies",
        "shift_type": "Lasting/Temporary - permanence of the effect",
        "shift_type_justification": "Why this shift type applies",
        "shift_polarity": "Additive/Subtractive - direction of the effect",
        "shift_polarity_justification": "Why this polarity applies"
    }},
    "self_effects": [
    {{
        "condition": "Inherent Cost/On Action Success/On Action Failure - When does this self-effect occur?",
        "target_status": "STAMINA/SPIRIT/SUPPLY - Which of the Proactor's own Statuses is affected?",
        "polarity": "Additive/Subtractive - Does the Status increase or decrease?",
        "shift_type": "Lasting/Temporary - Is the effect persistent or fleeting?",
        "severity": "🚨 REQUIRED INTEGER 1-4 🚨 - How severe is this specific self-effect? NEVER leave this as null/None!",
        "severity_justification": "Explanation of severity calculation and any narrative adjustments",
        "description": "Brief narrative description of the self-inflicted effect"
    }}
],
    "dialogue_metadata": {{
        "dialogue_detected": true/false,
        "dialogue_intent": "SmallTalk/Inquiry/Persuasion/Threat/Insult/Command/Story/None",
        "dialogue_weight": {ua_dialogue_weight},
        "talk_time_seconds": 0,
        "can_affect_status": true/false,
        "apply_shift": true/false,
        "dialogue_only": true/false  // true = pure dialogue, false = action + dialogue
    }}
}}

**MANDATORY FIELD REQUIREMENTS:**
- **ALL UTAS_FACTORS FIELDS ARE REQUIRED** - You MUST provide every single field listed above
- **dialogue_metadata is OPTIONAL** - Only include if action contains dialogue elements - You MUST provide every single field listed above

**EXCHANGE TYPE CLASSIFICATION:**
- **exchange_type**: MUST be one of: "Supply", "Stamina", "Spirit", "Sympathy"
  - **Stamina**: Physical actions, bodily exertion, exhaustion, physical challenges
  - **Spirit**: Mental actions, concentration, willpower, psychological challenges, communication, conversation, phone calls
  - **Supply**: Resource-related actions, material consumption, equipment usage, buying/selling, trading goods
  - **Sympathy**: Social actions, relationship effects, reputation changes

**CRITICAL: Communication actions (talking, calling, messaging) are SPIRIT, NOT Supply - even when using technology**

**STATUS TARGET CLASSIFICATION:**
- **status_to_shift**: MUST be one of: "Stamina", "Spirit", "Supply", "Sympathy"
  - Choose the actor's own status that will be most directly affected by the fallible action

**S-TRAIT SELECTION GUIDE:**
- **s_trait_to_use**: MUST be one of: "Swiftness", "Sociability", "Sturdiness", "Smarts", "Shadow"
  - **Swiftness**: Speed, agility, reflexes, quick movements, dodging, racing
  - **Sociability**: Social interaction, persuasion, leadership, charm, public speaking
  - **Sturdiness**: Physical strength, endurance, toughness, lifting, breaking things
  - **Smarts**: Intelligence, knowledge, problem-solving, strategy, technical skills
  - **Shadow**: Stealth, deception, sneaking, hiding, underhanded tactics
- **s_trait_value**: MUST be an integer 0-5 (look up the actual value from actor data above)

**SKILL/ENDOWMENT/SUPPLEMENT SELECTION CRITERIA:**
- **skill**: MUST be {{"name": "skill_name", "value": 2}} or {{"name": "None", "value": 0}}
  - Use ONLY skills that exist on the character sheet above
  - **Primary Selection**: Choose skills that directly relate to the action being performed
  - **Cross-Skill Applicability**: Skills can apply creatively if they logically enhance the action
  - **Examples of Direct Application**: "Combat" for fighting, "Athletics" for physical feats, "Social Fortitude" for resisting intimidation
  - **Examples of Cross-Skill Application**: 
    - "Acrobatics" for stealth actions (graceful, silent movement)
    - "Performance" for deception (acting ability enhances lying)
    - "Medicine" for intimidation (knowledge of anatomy makes threats more credible)
    - "Engineering" for combat (understanding of mechanics)
    - "History" for social situations (cultural knowledge aids persuasion)
  - **Selection Priority**: 1) Direct match, 2) Creative cross-application, 3) Use {{"name": "None", "value": 0}}
  - **Justification Required**: Always explain HOW the skill applies to the specific action

- **endowment**: MUST be {{"name": "endowment_name", "value": 2}} or {{"name": "None", "value": 0}}
  - Use ONLY endowment abilities that exist on the character sheet above
  - Select powers that enhance or modify the action being performed
  - Examples: "Enhanced Strength" for physical actions, "Mind Reading" for social manipulation
  - If no relevant endowment power exists, use {{"name": "None", "value": 0}}

- **supplement**: MUST be {{"name": "item_name", "value": 2}} or {{"name": "None", "value": 0}}
- **supplement**: MUST be {{"name": "item_name", "value": integer}} or {{"name": "None", "value": 0}}
  - Use ONLY items/equipment that exist in the character's inventory above
  - **STRICT RELEVANCE REQUIRED**: Items must be directly used in or essential to the specific action
  - **Examples of CORRECT supplement usage**:
    - "Sword" for sword attacks or weapon-based combat
    - "Lockpicks" for picking locks specifically
    - "Rope" for climbing, binding, or rappelling
    - "Shield" for defensive actions
    - "Bandages" for healing actions
    - "Crowbar" for prying or breaking actions
  - **Examples of INCORRECT supplement usage**:
    - "Sword" for punching (not using the sword)
    - "Lockpicks" for intimidation (not picking locks)
    - "Rope" for social persuasion (not physically using rope)
    - "Bandages" for combat attacks (not healing)
  - **Selection Rule**: If the item is not physically used or directly essential to performing the action, use {{"name": "None", "value": 0}}
  - **When in doubt**: Choose "None" rather than forcing an irrelevant item

**SHIFT POLARITY EXAMPLES:**
- **stress_level**: MUST be an integer 1-5
- **shift_type**: MUST be "Lasting" or "Temporary"
- **shift_polarity**: MUST be "Additive" or "Subtractive"
  - **Additive**: Actions that INCREASE/IMPROVE the target's status
    - Healing someone (Additive to Stamina)
    - Encouraging someone (Additive to Spirit)
    - Giving money/resources (Additive to Supply)
    - Building rapport/friendship (Additive to Sympathy)
  - **Subtractive**: Actions that DECREASE/HARM the target's status
    - Attacking someone (Subtractive to Stamina)
    - Intimidating someone (Subtractive to Spirit)
    - Stealing money/resources (Subtractive to Supply)
    - Insulting/betraying someone (Subtractive to Sympathy)
- **self_effects**: MANDATORY - MUST contain at least one self-effect (empty list [] is NOT allowed for proactor actions)

**Guidelines:**
- Be specific and detailed in all justifications
- Consider the narrative context when determining stress levels
- Predict realistic self-effects based on the action's nature
- Ensure all numerical values are appropriate for the actor's capabilities

**SELF-EFFECTS ANALYSIS REQUIREMENTS:**
🚨 **CRITICAL: PROACTOR ACTIONS MUST ALWAYS HAVE SELF-EFFECTS** 🚨
Proactors pay costs for taking initiative - there is NO such thing as a cost-free proactor action!
Every proactor action MUST have at least one self-effect representing the inherent cost of acting.

When interpreting the Proactor's action, you MUST analyze potential self-inflicted effects using this systematic approach:

**1. Self-Effect Condition Analysis:**
For each potential self-effect, determine WHEN it occurs:
- **Inherent Cost**: Effect happens simply by performing the action, regardless of success/failure
- **On Action Success**: Effect only occurs if the primary action succeeds  
- **On Action Failure**: Effect only occurs if the primary action fails

**2. Target Status Identification:**
Identify which of the Proactor's own statuses is affected:
- **STAMINA**: Physical health, energy, endurance
- **SPIRIT**: Mental state, confidence, morale
- **SUPPLY**: Resources, materials, equipment

**3. Polarity and Type:**
- **Polarity**: Additive (increases status) or Subtractive (decreases status)
- **Shift Type**: Lasting (persistent) or Temporary (fleeting)

**4. Severity Calculation (1-4 scale):**
Step A - Get Initial Base Magnitude from stress level and condition
Step B - Apply narrative adjustment (-1, 0, or +1) based on action context
Final Severity = Initial + Adjustment (clamped 1-4)

**CRITICAL FORMATTING REQUIREMENTS:**
- ALL nested objects (skill, endowment, supplement) MUST be JSON objects with "name" and "value" keys
- ALL numeric values MUST be integers (0-5), never strings or text
- If no skill/endowment/supplement applies, use: {{"name": "None", "value": 0}}
- NEVER return strings where objects are expected

**CORRECT EXAMPLES:**
"skill": {{"name": "Combat", "value": 3}}
"s_trait_value": 4
"endowment": {{"name": "None", "value": 0}}

**SELF-EFFECTS EXAMPLES:**
🚨 **CRITICAL: Only ONE self-effect condition applies per proactor per action!** 🚨
Choose the most appropriate condition based on the action's nature:

**SEVERITY FIELD IS MANDATORY - EXAMPLES:**
✅ CORRECT: "severity": 2
✅ CORRECT: "severity": 1  
✅ CORRECT: "severity": 4
❌ WRONG: "severity": null
❌ WRONG: "severity": None
❌ WRONG: "severity": "moderate"
❌ WRONG: Missing severity field entirely

🚨 **SEVERITY MUST ALWAYS BE AN INTEGER FROM 1 TO 4** 🚨
If you're unsure of the severity, use 2 as a safe default rather than leaving it empty!

**Example 1 - Inherent Cost (Most Common):**
"self_effects": [
    {{
        "condition": "Inherent Cost",
        "target_status": "Stamina",
        "polarity": "Subtractive",
        "shift_type": "Temporary",
        "severity": 2,
        "severity_justification": "Running and attacking is physically demanding, base severity 2 for moderate exertion",
        "description": "The physical exertion of sprinting while wielding a weapon leaves the proactor breathing heavily and slightly fatigued"
    }}
]

**Example 2 - On Action Success:**
"self_effects": [
    {{
        "condition": "On Action Success",
        "target_status": "Spirit",
        "polarity": "Additive",
        "shift_type": "Temporary",
        "severity": 1,
        "severity_justification": "Successfully intimidating someone can be emotionally empowering, severity 1 for mild psychological boost",
        "description": "After successfully breaking their opponent's will, the proactor feels a twinge of confidence and emotional empowerment"
    }}
]

**Example 3 - On Action Failure:**
"self_effects": [
    {{
        "condition": "On Action Failure",
        "target_status": "Spirit",
        "polarity": "Subtractive",
        "shift_type": "Temporary",
        "severity": 2,
        "severity_justification": "Failing a risky maneuver can be demoralizing, severity 2 for significant confidence loss",
        "description": "The failed attempt leaves the proactor feeling foolish and doubting their abilities"
    }}
]

**CONDITION SELECTION GUIDE:**
- **Inherent Cost**: Effect happens only if success and failure are not applicable (physical exertion, resource consumption)
- **On Action Success**: Effect only occurs if the action succeeds (guilt, overconfidence, exhaustion from success)
- **On Action Failure**: Effect only occurs if the action fails (embarrassment, injury from failure, wasted resources)

**INCORRECT EXAMPLES TO AVOID:**
"skill": "Combat"  ❌ (should be object)
"skill": {{"name": "Combat", "value": "3"}}  ❌ (value should be number)
"s_trait_value": "Expert"  ❌ (should be number)
"self_effects": []  ❌ (NEVER empty for proactor actions!)

**IF UNCERTAIN:**
- For skills: Use {{"name": "Instincts", "value": 0}}
- For endowments: Use {{"name": "None", "value": 0}}
- For supplements: Use {{"name": "None", "value": 0}}
- For numeric values: Use 0 if truly unknown

**VALIDATION CHECKLIST - COMPLETE BEFORE RESPONDING:**
1. ✓ ALL 12 utas_factors fields are present (no missing fields allowed)
2. ✓ s_trait_value is an INTEGER from actor data above (not 0, not string)
3. ✓ skill, endowment, supplement are OBJECTS with "name" and "value" keys
4. ✓ All justification fields contain meaningful explanations
5. ✓ exchange_type matches one of the 4 allowed values exactly
6. ✓ status_to_shift matches one of the 4 allowed values exactly
7. ✓ s_trait_to_use matches one of the 5 allowed values exactly
8. ✓ self_effects is present ([] if no effects)
9. ✓ JSON is properly formatted and parseable

**CRITICAL WARNING:**
- INCOMPLETE RESPONSES CAUSE SYSTEM CRASHES
- MISSING FIELDS RESULT IN ERROR MESSAGES
- YOU MUST PROVIDE ALL 12 UTAS_FACTORS FIELDS
- NO SHORTCUTS OR SIMPLIFIED RESPONSES ALLOWED

**RESPONSE FORMAT:**
- Respond ONLY with valid JSON
- No explanatory text before or after the JSON
- No markdown code blocks or formatting
- Raw JSON object only

**FINAL REMINDER: Your response MUST contain ALL fields listed in the JSON structure above. Partial responses will fail."""

    def determine_action_difficulty(self, action: str, scene_context: str = "") -> Dict[str, Any]:
        """
        Determine the difficulty/stressor level for a fallible action using LLM analysis.
        
        Args:
            action: The action being attempted
            scene_context: Additional context about the scene
            
        Returns:
            Dict containing difficulty level (1-5) and reasoning
        """
        prompt = f"""
You are analyzing a fallible action to determine its difficulty level (stressor).

**ACTION:** {action}
**SCENE CONTEXT:** {scene_context}

Determine the difficulty level for this action on a scale of 1-5:
- 1: Very Easy (almost automatic)
- 2: Easy (minor challenge)
- 3: Moderate (standard difficulty)
- 4: Hard (significant challenge)
- 5: Very Hard (extreme challenge)

Consider factors like complexity, environmental conditions, and inherent difficulty.

**RESPONSE FORMAT (JSON):**
{{
    "difficulty": 1-5,
    "confidence": "high" or "medium" or "low",
    "reasoning": "Brief explanation of why this difficulty level is appropriate"
}}
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            
            response_text = response.choices[0].message.content.strip()
            
            import json
            try:
                result = json.loads(response_text)
                return result
            except json.JSONDecodeError:
                return None
                
        except Exception as e:
            return None

    def classify_rule_of_3s(self, user_input: str, proactor: 'Actor', reactor: 'Actor') -> Tuple[RuleOf3Category, str, Optional[RuleOf3Context]]:
        """
        Classify user action according to Rule of 3's temporal categories and detect transitions.
        
        Args:
            user_input: The user's action description
            proactor: The acting character
            reactor: The other character
            
        Returns:
            Tuple of (RuleOf3Category, reasoning, new_context_if_transition)
        """
        print(f"\n⏱️ Rule of 3's: Analyzing temporal classification for: '{user_input}'")
        
        category, reasoning = self.rule_of_3s_classifier.classify_action(user_input, self.current_rule_of_3s_context)
        
        new_context = None
        if self.current_rule_of_3s_context is None:
            new_context = self.rule_of_3s_manager.process_transition(
                None, category, f"Initial Rule of 3's classification: {reasoning}"
            )
            self.current_rule_of_3s_context = new_context
            print(f"⏱️ Rule of 3's: Initial context established - {category.value}")
        elif self.current_rule_of_3s_context.category != category:
            transition_reason = f"Action '{user_input}' triggers transition from {self.current_rule_of_3s_context.category.value} to {category.value}"
            new_context = self.rule_of_3s_manager.process_transition(
                self.current_rule_of_3s_context, category, transition_reason
            )
            self.current_rule_of_3s_context = new_context
            print(f"⏱️ Rule of 3's: TRANSITION DETECTED - {self.current_rule_of_3s_context.category.value} → {category.value}")
        else:
            print(f"⏱️ Rule of 3's: Maintaining {category.value} context")
        
        return category, reasoning, new_context

    def get_current_rule_of_3s_context(self) -> Optional[RuleOf3Context]:
        """Get the current Rule of 3's temporal context"""
        return self.current_rule_of_3s_context

    def set_rule_of_3s_context(self, context: RuleOf3Context) -> None:
        """Set the Rule of 3's temporal context (for scene initialization)"""
        self.current_rule_of_3s_context = context
        print(f"⏱️ Rule of 3's: Context set to {context.category.value}")

    def get_rule_of_3s_narrative_guidance(self) -> Dict[str, str]:
        """Get narrative guidance based on current Rule of 3's context"""
        if self.current_rule_of_3s_context:
            return self.rule_of_3s_classifier.get_narrative_guidance(self.current_rule_of_3s_context.category)
        else:
            return self.rule_of_3s_classifier.get_narrative_guidance(RuleOf3Category.THREE_MINUTE)
    
    def _enhance_prompt_with_time_context(self, prompt: str, time_context: Dict[str, Any]) -> str:
        """
        Enhance prompt with time-of-day context for narrative consistency.
        
        Args:
            prompt: The base prompt
            time_context: Time context from MasterTimeCoordinator
            
        Returns:
            Enhanced prompt with time information
        """
        if not time_context:
            return prompt
        
        time_of_day = time_context.get('time_of_day')
        atmospheric_desc = time_context.get('atmospheric_description', '')
        lighting = time_context.get('lighting_condition', '')
        current_time = time_context.get('formatted_time', '')
        
        if not time_of_day:
            return prompt
        
        # Convert TimeOfDay enum to readable string
        time_of_day_str = time_of_day.value.replace('_', ' ').title() if hasattr(time_of_day, 'value') else str(time_of_day)
        
        time_enhancement = f"""

**CURRENT TIME CONTEXT:**
- Time: {current_time}
- Time of Day: {time_of_day_str}
- Atmosphere: {atmospheric_desc}
- Lighting: {lighting}

**NARRATIVE TIME CONSISTENCY REQUIRED:**
Ensure the narrative_description field reflects the current time of day. Use appropriate lighting, atmospheric details, and time-appropriate language. Do NOT describe nighttime scenes during daytime or vice versa. The narrative should naturally incorporate the current lighting and atmospheric conditions.
"""
        
        return prompt + time_enhancement
    
    def detect_explicit_movement(self, user_input: str, classification_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Detect if user explicitly requested movement.

        This method is used as a hard gate for movement narration + travel.
        It MUST prefer the Interpreter's LLM classification when available to avoid
        brittle regex extracting non-destination clauses (e.g. "to try to find Matteo").
        """
        # 1) Prefer LLM classification when provided
        if classification_data and 'explicit_movement' in classification_data:
            return {
                "has_explicit_movement": bool(classification_data.get('explicit_movement')),
                "movement_type": "llm_detected",
                "target": classification_data.get('movement_target'),
                "confidence": classification_data.get('confidence', 'high')
            }

        user_input_lower = (user_input or '').lower()

        # Movement verbs that indicate explicit movement intent
        movement_verbs = [
            'walk', 'move', 'go', 'head', 'run', 'sprint', 'jog',
            'approach', 'step', 'stride', 'rush', 'hurry', 'dash',
            'sneak', 'creep', 'crawl', 'climb', 'jump', 'enter',
            'exit', 'leave', 'travel', 'drive', 'ride',
            # Gerunds and continuations
            'walking', 'moving', 'going', 'heading', 'running', 'sprinting', 'jogging',
            'approaching', 'stepping', 'striding', 'rushing', 'hurrying', 'dashing',
            'sneaking', 'creeping', 'crawling', 'climbing', 'jumping', 'entering',
            'exiting', 'leaving', 'traveling', 'travelling', 'driving', 'riding',
            'continue', 'continuing', 'keep'
        ]

        # Prepositions that indicate movement direction.
        # IMPORTANT: prefer directional destination preps before generic "to" so we don't
        # misread infinitives ("to try", "to find") as destinations.
        movement_prepositions = ['towards', 'toward', 'into', 'through', 'across', 'over', 'to']

        detected_verb = None
        for verb in movement_verbs:
            if f" {verb} " in f" {user_input_lower} " or user_input_lower.startswith(f"{verb} "):
                detected_verb = verb
                break

        if not detected_verb:
            return {
                "has_explicit_movement": False,
                "movement_type": None,
                "target": None,
                "confidence": "high"
            }

        def _clean_target_phrase(tp: str) -> Optional[str]:
            tp = (tp or '').strip()
            if not tp:
                return None

            # Generic trimming to avoid capturing extra intent clauses after the destination.
            # We avoid hardcoding verb phrases ("try", "find", etc.).
            #
            # Heuristic:
            # - If the extracted phrase contains punctuation, keep the part before it.
            # - If the extracted phrase contains an additional " to " segment, keep only
            #   the part before that (e.g., "archive to ..." -> "archive").
            import re

            tp = re.split(r"[\.,;:!?]", tp, maxsplit=1)[0].strip()

            if " to " in tp.lower():
                # This 'to' is inside the extracted destination phrase, i.e. it's not the
                # movement preposition we split on earlier. In practice it's usually the
                # start of an infinitive clause ("to do X").
                parts = re.split(r"\s+to\s+", tp, maxsplit=1, flags=re.IGNORECASE)
                tp = (parts[0] if parts else tp).strip()

            return tp or None

        target = None
        articles = ['the', 'a', 'an']
        for prep in movement_prepositions:
            if f" {prep} " in user_input_lower:
                parts = user_input_lower.split(f" {prep} ", 1)
                if len(parts) > 1:
                    target_phrase = parts[1].strip()
                    target_words = target_phrase.split()
                    if target_words and target_words[0] in articles:
                        target_words = target_words[1:]
                    target = _clean_target_phrase(' '.join(target_words))
                break

        return {
            "has_explicit_movement": True,
            "movement_type": detected_verb,
            "target": target,
            "confidence": "high" if target else "medium"
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache performance statistics"""
        total_requests = self.cache_hits + self.cache_misses
        hit_rate = (self.cache_hits / total_requests * 100) if total_requests > 0 else 0
        
        return {
            'cache_hits': self.cache_hits,
            'cache_misses': self.cache_misses,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 1),
            'cache_size': len(self.response_cache)
        }
