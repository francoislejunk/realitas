from typing import Dict, Any, Optional
import random
import os
from openrouter_config import create_role_client, OpenRouterConfig, retry_with_backoff, RetryConfig, robust_llm_call
from narrative_utils import (
    get_status_descriptor,
    get_success_level_narration,
    N2N_Skill_Level,
    N2N_S_Trait_Level,
    N2N_Endowment_Level,
    N2N_Status_Level,
    N2N_Shift_Magnitude,
    N2N_Difficulty,
    N2N_Serendipity_Level,
    N2N_Status_Modifier_Impact,
)
from actors import Actor, UserActor
from actor_sheet import StatusType
from color_utils import Color
from llm_agents.utas_narrative_formula import UTASNarrativeFormula
from rule_of_3s import RuleOf3Category, RuleOf3Context
from llm_agents.narrative_loop_system import FourModeNarrativeLoop, NarrativeMode, NarrativeTone

# Import category enum for filtered RAG queries
try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except ImportError:
    WorldbuildingCategory = None  # Graceful fallback if not available

from rag_lock_utils import get_multi_category_context_for_llm

# Import canonical sensory constants for distance-based perception
try:
    from sensory_constants import (
        SensoryCapabilities,
        get_distance_category,
        get_sensory_context_for_narrator,
        get_sensory_rules_for_distance,
        SENSORY_THRESHOLDS,
        DistanceCategory,
    )
    SENSORY_SYSTEM_AVAILABLE = True
except ImportError:
    SENSORY_SYSTEM_AVAILABLE = False
    print("[WARNING] sensory_constants not available - distance-based perception disabled")

# Import stranger description system for diegetic NPC descriptions
try:
    from stranger_description_system import (
        StrangerDescriber,
        get_nua_description,
        get_nua_definite_description,
        describe_nuas_in_scene,
    )
    STRANGER_SYSTEM_AVAILABLE = True
except ImportError:
    STRANGER_SYSTEM_AVAILABLE = False
    print("[WARNING] stranger_description_system not available - using names for all NPCs")

# Local debug flag (can be overridden by environment variable)
SUPPRESS_DEBUG = os.getenv("REDESIGNED_SUPPRESS_DEBUG", "false").strip().lower() == "true"


class NarratorAgent:
    """
    The Narrator Agent, responsible for generating narrative descriptions
    and outcomes for the UTAS simulation.
    """
    
    # Interior/Exterior consistency requirement
    INTERIOR_EXTERIOR_RULE = """
**CRITICAL: INTERIOR/EXTERIOR CONSISTENCY - You MUST pick ONE:**
- **IF EXTERIOR (outside)**: Only describe outdoor elements - building facades, streets, sky, weather. NO interior details.
- **IF INTERIOR (inside)**: Only describe indoor elements - room layout, furniture, walls, ceiling. NO exterior/sky/weather.
- **FORBIDDEN**: NEVER mix both. You cannot be inside AND outside simultaneously. Pick ONE location perspective.
"""
    
    # Sensory perception requirements for ALL narration
    SENSORY_PERCEPTION_REQUIREMENTS = """
**REALISTIC SELECTIVE PERCEPTION — write like a person, not a sensor array**

People don't perceive everything when they enter a space. They notice what's most prominent, unexpected, or personally relevant — and then maybe one other thing catches their attention. That's it. Write that.

**THE RULE:** What would THIS person, in THIS moment, actually register first? Lead with that. Then stop after 1 additional detail at most.

**STRUCTURE — flexible, natural prose:**
- Write in second person ("you") but NOT every sentence must start with "You see/hear/smell"
- Mix natural prose with direct perception: "The ceiling is low here." is fine. "You spot a figure near the back wall." is fine. Both work.
- The most prominent thing hits first — the thing that draws the eye, or a sound before you even look, or a smell you can't ignore
- Then 0-1 additional detail that genuinely stands out for THIS specific scene
- DO NOT enumerate senses. DO NOT work through a checklist.

**EXAMPLES OF REALISTIC PERCEPTION:**
✓ "The antiseptic smell reaches you before anything else. A man in a grey coat stands near the far end of the counter with his back to you."
✓ "The noise hits before your eyes adjust — a dozen conversations, the rattle of trays."
✓ "The room is smaller than you expected. One lamp, the rest in darkness."
✓ "You hear someone moving in the back before you see them."
✓ "The floor is wet. You look up and find the source."

**AVOID:**
✗ Covering sight + sound + smell + touch all in one description
✗ Starting every sentence with "You see... You hear... You smell... You feel..."
✗ Describing the room like an inventory of sensory data
✗ Omniscient narrator voice ("The atmosphere feels tense", "It seems abandoned")
✗ Describing what you DON'T perceive ("There is no smell of smoke")

**WRITE WHAT MATTERS TO THIS MOMENT. LEAVE THE REST OUT.**
"""
    
    def __init__(self, rag_system=None, key_memories_system=None, mention_system=None):
        self.client = create_role_client("narration")
        self.model = OpenRouterConfig.get_model_for_role("narration")
        self.rag_system = rag_system  # RAG system for worldbuilding context
        self.key_memories_system = key_memories_system  # Memory system for context
        self.mention_system = mention_system  # For actor mention tracking
        self.utas_formula = UTASNarrativeFormula()
        self.current_rule_of_3s_context: Optional[RuleOf3Context] = None
        self.narrative_loop = FourModeNarrativeLoop(self.client)
        self.narrative_context_manager = None  # Will be set externally

    def _get_actor_mention_context(self, actor_name: str, max_mentions: int = 5) -> str:
        """
        Get formatted mention context for an actor to inject into prompts.

        Shows where actor was last mentioned to prevent contradictions
        in narrative generation.

        Args:
            actor_name: Name of the actor to query mentions for
            max_mentions: Maximum number of mentions to include (default: 5)

        Returns:
            Formatted mention context string, or empty string if no mentions
        """
        if not self.mention_system:
            return ""

        try:
            location, confidence = self.mention_system.get_last_known_location(actor_name)
            if location:
                return f"\n**MENTION HISTORY:** {actor_name} was last mentioned at {location} (confidence: {confidence.value})\n"
            return ""
        except Exception as e:
            print(f"WARNING: Could not fetch mentions for {actor_name}: {e}")
            return ""

    def _extract_narrative_mentions(self, narrative: str, actors_in_scene: list = None,
                                    turn_number: int = 0, scene_id: str = ""):
        """
        Extract actor mentions from generated narrative text using heuristic patterns.

        Looks for common patterns in narrative descriptions:
        - "[Actor] stands/sits at [Location]" -> PHYSICAL_PRESENCE
        - "[Actor] walks/moves into [Location]" -> ARRIVING
        - "[Actor] leaves/exits/departs" -> DEPARTING
        - "[Actor] was here earlier" -> ELSEWHERE_PAST
        - "You see [Actor] at [Location]" -> PHYSICAL_PRESENCE

        Args:
            narrative: The generated narrative text
            actors_in_scene: List of actor names currently in scene (optional)
            turn_number: Current turn number
            scene_id: Current scene ID
        """
        if not self.mention_system or not narrative:
            return

        try:
            from mention_system import MentionType, MentionSource, PresenceConfidence

            narrative_lower = narrative.lower()

            # If we have actors in scene, look for presence patterns
            if actors_in_scene:
                for actor_name in actors_in_scene:
                    actor_lower = actor_name.lower()

                    # Pattern 1: Physical presence descriptions
                    # "Marcus stands at the bar", "Linda sits in the corner"
                    presence_verbs = ["stands", "sits", "leans", "waits", "remains", "stays"]
                    for verb in presence_verbs:
                        pattern = f"{actor_lower} {verb}"
                        if pattern in narrative_lower:
                            # Try to extract location from "at [location]"
                            words = narrative.split()
                            found_pattern = False
                            for i, word in enumerate(words):
                                if word.lower() == actor_lower and i + 1 < len(words):
                                    if words[i + 1].lower() in [v.rstrip('s') + 's' for v in presence_verbs]:
                                        found_pattern = True
                                        # Look for "at [Location]" or "in [Location]"
                                        location = None
                                        if i + 3 < len(words) and words[i + 2].lower() in ["at", "in", "near"]:
                                            location = words[i + 3].strip(".,!?")

                                        self.mention_system.record_physical_presence(
                                            actor_name=actor_name,
                                            location=location or "Unknown",
                                            context=narrative[:200],  # First 200 chars as context
                                            source=MentionSource.NARRATIVE,
                                            turn_number=turn_number,
                                            scene_id=scene_id
                                        )
                                        print(f"Recorded PHYSICAL_PRESENCE mention: {actor_name} at {location or 'scene'} (from narrative)")
                                        break
                            if found_pattern:
                                break  # Only record once per actor per narrative

            # Pattern 2: Arrival patterns
            # "[Actor] walks into", "[Actor] enters", "[Actor] arrives"
            arrival_patterns = [
                (" walks into ", MentionType.ARRIVING),
                (" enters ", MentionType.ARRIVING),
                (" arrives at ", MentionType.ARRIVING),
                (" steps into ", MentionType.ARRIVING),
                (" comes into ", MentionType.ARRIVING),
            ]

            for pattern, mention_type in arrival_patterns:
                if pattern in narrative_lower:
                    # Find actor name before pattern
                    parts = narrative.split(pattern)
                    if len(parts) >= 2:
                        potential_actor = parts[0].split()[-1].strip(".,!?")
                        if potential_actor and potential_actor[0].isupper():
                            # Try to extract destination
                            destination = parts[1].split()[0].strip(".,!?") if parts[1].split() else "Unknown"

                            self.mention_system.record_arrival(
                                actor_name=potential_actor,
                                destination=destination,
                                origin="Unknown",
                                context=narrative[:200],
                                source=MentionSource.NARRATIVE,
                                turn_number=turn_number,
                                scene_id=scene_id
                            )
                            print(f"Recorded ARRIVING mention: {potential_actor} to {destination} (from narrative)")

            # Pattern 3: Departure patterns
            # "[Actor] leaves", "[Actor] exits", "[Actor] departs"
            departure_patterns = [
                (" leaves ", " for ", MentionType.DEPARTING),
                (" exits ", " toward ", MentionType.DEPARTING),
                (" departs ", " for ", MentionType.DEPARTING),
                (" walks out ", " to ", MentionType.DEPARTING),
                (" heads ", " to ", MentionType.DEPARTING),
            ]

            for main_pattern, dest_pattern, mention_type in departure_patterns:
                if main_pattern in narrative_lower:
                    parts = narrative.split(main_pattern)
                    if len(parts) >= 2:
                        potential_actor = parts[0].split()[-1].strip(".,!?")
                        if potential_actor and potential_actor[0].isupper():
                            # Try to extract destination
                            destination = "Unknown"
                            if dest_pattern in parts[1].lower():
                                dest_parts = parts[1].split(dest_pattern)
                                if len(dest_parts) >= 2:
                                    destination = dest_parts[1].split()[0].strip(".,!?")

                            self.mention_system.record_departure(
                                actor_name=potential_actor,
                                destination=destination,
                                origin="Unknown",
                                context=narrative[:200],
                                source=MentionSource.NARRATIVE,
                                turn_number=turn_number,
                                scene_id=scene_id
                            )
                            print(f"Recorded DEPARTING mention: {potential_actor} to {destination} (from narrative)")
                            break  # Only record once

            # Pattern 4: Past presence
            # "[Actor] was here earlier", "[Actor] had been at"
            past_patterns = [" was here ", " had been ", " was at "]
            for pattern in past_patterns:
                if pattern in narrative_lower:
                    parts = narrative.split(pattern)
                    if len(parts) >= 2:
                        potential_actor = parts[0].split()[-1].strip(".,!?")
                        if potential_actor and potential_actor[0].isupper():
                            # Try to extract location from "at [location]"
                            location = "Unknown"
                            if " at " in parts[1]:
                                loc_parts = parts[1].split(" at ")
                                if len(loc_parts) >= 2:
                                    location = loc_parts[1].split()[0].strip(".,!?")

                            self.mention_system.record_mention(
                                actor_name=potential_actor,
                                mention_type=MentionType.ELSEWHERE_PAST,
                                source=MentionSource.NARRATIVE,
                                context=narrative[:200],
                                location=location,
                                location_confidence=PresenceConfidence.MEDIUM,
                                turn_number=turn_number,
                                scene_id=scene_id
                            )
                            print(f"Recorded ELSEWHERE_PAST mention: {potential_actor} at {location} (from narrative)")
                            break  # Only record once

        except Exception as e:
            print(f"WARNING: Error extracting mentions from narrative: {e}")

    def get_sensory_constraints_for_target(self, distance: float, target_name: str = "them") -> str:
        """
        Get sensory constraints for narrator prompts based on distance.
        
        This tells the narrator what senses can be used to describe
        the target at the given distance, ensuring consistency.
        
        Args:
            distance: Distance in units to the target
            target_name: Name of the target for personalized text
        
        Returns:
            Formatted string for inclusion in narrator prompts
        """
        if not SENSORY_SYSTEM_AVAILABLE:
            return ""  # No constraints if system not available
        
        return get_sensory_context_for_narrator(distance, target_name)
    
    def get_sensory_rules(self, distance: float) -> Dict[str, Any]:
        """
        Get structured sensory rules for programmatic use.
        
        Returns dict with sight, hearing, smell, touch capabilities.
        """
        if not SENSORY_SYSTEM_AVAILABLE:
            return {}
        
        return get_sensory_rules_for_distance(distance)
    
    def validate_narrative_against_distance(self, narrative: str, distance: float) -> tuple:
        """
        Validate that a narrative respects sensory constraints for the given distance.
        
        Returns:
            Tuple of (is_valid: bool, issues: List[str])
        """
        if not SENSORY_SYSTEM_AVAILABLE:
            return (True, [])
        
        issues = []
        rules = get_sensory_rules_for_distance(distance)
        narrative_lower = narrative.lower()
        
        # Check for whisper violations
        if not rules["hearing"]["whisper"]:
            if "whisper" in narrative_lower or "murmur" in narrative_lower:
                issues.append(f"Cannot hear whispers at {distance:.1f} units")
        
        # Check for facial detail violations
        if not rules["sight"]["facial_detail"]:
            facial_words = ["expression", "eyes narrow", "eye contact", "smirk", "frown", "smile"]
            for word in facial_words:
                if word in narrative_lower:
                    issues.append(f"Cannot see facial details at {distance:.1f} units")
                    break
        
        # Check for smell violations
        if not rules["smell"]["strong"]:
            smell_words = ["smell", "scent", "odor", "breath"]
            for word in smell_words:
                if word in narrative_lower:
                    issues.append(f"Cannot smell at {distance:.1f} units")
                    break
        
        return (len(issues) == 0, issues)

    def get_stranger_aware_name(self, actor_data: Dict[str, Any], ua_actor=None, 
                                 relationship_system=None) -> str:
        """
        Get the appropriate name/description for an actor based on relationship.
        
        For strangers: Returns trait-based description (e.g., "the hulking man")
        For known NPCs: Returns their name
        For UA: Returns "you" or their name based on context
        
        Args:
            actor_data: Dict with actor info (must have 'name', optionally 'actor' object)
            ua_actor: The UA (for relationship checking)
            relationship_system: Optional relationship tracker
            
        Returns:
            Appropriate name/description string
        """
        is_user_actor = actor_data.get('is_user_actor', False)
        name = actor_data.get('name', 'someone')
        
        # UA always uses their name (narrator handles second person)
        if is_user_actor:
            return name
        
        # If no stranger system, just use name
        if not STRANGER_SYSTEM_AVAILABLE:
            return name
        
        # Try to get the actor object for stranger description
        actor = actor_data.get('actor')
        if actor and hasattr(actor, 'sheet'):
            try:
                desc = get_nua_definite_description(actor, ua_actor, relationship_system=relationship_system)
                if desc and desc != name:
                    return desc
            except Exception:
                pass
        
        return name

    def get_npc_descriptions_for_scene(self, npcs: list, ua_actor=None, 
                                        context: str = "", 
                                        relationship_system=None) -> Dict[str, str]:
        """
        Transform NPC list into stranger-appropriate descriptions.
        
        For strangers: Returns trait-based descriptions (e.g., "a hulking man")
        For known NPCs: Returns their names
        
        Args:
            npcs: List of NPC actors or names
            ua_actor: The UA (for relationship checking)
            context: Scene context (helps determine visible occupations)
            relationship_system: Optional relationship tracker
        
        Returns:
            Dict mapping original name -> appropriate description
        """
        if not STRANGER_SYSTEM_AVAILABLE:
            # Fallback: just use names
            result = {}
            for npc in npcs:
                if hasattr(npc, 'sheet'):
                    name = npc.sheet.name
                else:
                    name = str(npc)
                result[name] = name
            return result
        
        describer = StrangerDescriber(relationship_system)
        result = {}
        
        for npc in npcs:
            if hasattr(npc, 'sheet'):
                name = npc.sheet.name
                desc = describer.get_description(npc, ua_actor, context)
                # Use occupation description if available, otherwise trait description
                if desc.is_stranger:
                    result[name] = desc.occupation_desc
                else:
                    result[name] = name
            else:
                # Just a name string - can't generate description
                result[str(npc)] = str(npc)
        
        return result
    
    def format_npcs_for_prompt(self, npcs: list, ua_actor=None, 
                                context: str = "",
                                relationship_system=None) -> str:
        """
        Format NPC list for LLM prompt with stranger-appropriate descriptions.
        
        Returns a string like:
        "a hulking bouncer (STRANGER - describe by appearance), 
         the waitress (STRANGER - describe by occupation),
         John (KNOWN - can use name)"
        """
        if not npcs:
            return "NONE (Empty)"
        
        descriptions = self.get_npc_descriptions_for_scene(
            npcs, ua_actor, context, relationship_system
        )
        
        formatted = []
        for npc in npcs:
            if hasattr(npc, 'sheet'):
                name = npc.sheet.name
            else:
                name = str(npc)
            
            desc = descriptions.get(name, name)
            
            if desc != name:
                # Stranger - include guidance
                formatted.append(f"{desc} (STRANGER - do NOT use their name '{name}', describe by appearance/occupation)")
            else:
                # Known - can use name
                formatted.append(f"{name} (KNOWN - can use name)")
        
        return ", ".join(formatted)

    def _extract_response_content(self, response) -> Optional[str]:
        """
        Extract content from LLM response.
        
        For MiniMax M2 reasoning models:
        - Prefers message.content (the final answer)
        - Extracts final answer from message.reasoning if content is empty
        - Intelligently parses reasoning to find the actual output
        
        Returns:
            The response content string, or None if no content found
        """
        if not response or not response.choices:
            return None
        
        message = response.choices[0].message
        
        # DEBUG: Log what we're getting from MiniMax M2
        has_content = bool(message.content and message.content.strip())
        has_reasoning = bool(hasattr(message, 'reasoning') and message.reasoning and message.reasoning.strip())
        
        if not SUPPRESS_DEBUG:
            print(f"[DEBUG EXTRACT] content exists: {has_content}, reasoning exists: {has_reasoning}")
            if has_content:
                print(f"[DEBUG EXTRACT] content preview: {message.content.strip()[:100]}...")
            if has_reasoning:
                print(f"[DEBUG EXTRACT] reasoning preview: {message.reasoning.strip()[:100]}...")
        
        # Try message.content first (preferred - this is the final answer)
        if message.content:
            content = message.content.strip()
            if content:
                return content
        
        # MiniMax M2 reasoning extraction: Parse the reasoning field to find actual output
        if hasattr(message, 'reasoning') and message.reasoning:
            reasoning = message.reasoning.strip()
            if reasoning:
                if not SUPPRESS_DEBUG:
                    print(f"[MINIMAX M2] Extracting answer from reasoning field...")
                    print(f"[MINIMAX M2] Full reasoning:\n{reasoning}\n[END REASONING]")
                
                # Strategy: Find the last substantial paragraph that looks like an answer
                # Skip meta-commentary and thinking process
                lines = reasoning.split('\n')
                
                # Look for the final answer by finding the last substantial content block
                # that doesn't contain meta-patterns
                answer_candidates = []
                current_block = []
                
                meta_indicators = [
                    "The user asks:",
                    "The user is asking",
                    "The user wants",
                    "I need to",
                    "Let me",
                    "Let's",
                    "Alright,",
                    "Okay,",
                    "First,",
                    "Next,",
                    "Since the rules",
                    "Looking at",
                    "We need to produce",
                    "We need to respond",
                    "We need to generate",
                    "The question:",
                    "The task:",
                    "The instruction",
                    "I'll",
                    "I should",
                    "I must",
                    "Based on the context",
                    "Given the",
                    "The constraints:",
                    "The prompt says",
                ]
                
                for line in lines:
                    line = line.strip()
                    if not line:
                        if current_block:
                            answer_candidates.append(' '.join(current_block))
                            current_block = []
                        continue
                    
                    # Check if line is meta-commentary
                    is_meta = any(indicator.lower() in line.lower() for indicator in meta_indicators)
                    
                    if not is_meta and len(line) > 15:  # Lowered threshold
                        current_block.append(line)
                
                # Add final block
                if current_block:
                    answer_candidates.append(' '.join(current_block))
                
                if not SUPPRESS_DEBUG:
                    print(f"[MINIMAX M2] Found {len(answer_candidates)} candidate blocks")
                    for i, cand in enumerate(answer_candidates):
                        print(f"[MINIMAX M2] Candidate {i+1} ({len(cand)} chars): {cand[:80]}...")
                
                # Return the longest candidate that looks like an answer
                if answer_candidates:
                    # Filter out very short candidates (lowered threshold)
                    valid_candidates = [c for c in answer_candidates if len(c) > 20]
                    if valid_candidates:
                        # Return the last valid candidate (usually the conclusion)
                        answer = valid_candidates[-1]
                        if not SUPPRESS_DEBUG:
                            print(f"[MINIMAX M2] Extracted answer: {answer[:100]}...")
                        return answer
                
                # If no good candidates, return None to trigger fallback
                if not SUPPRESS_DEBUG:
                    print(f"[MINIMAX M2] Could not extract clean answer from reasoning - using fallback")
                return None
        
        return None
    
    def _call_llm(self, prompt: str, rule_of_3s_context: Optional[RuleOf3Context] = None, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """Calls the OpenRouter LLM and returns the response content with Rule of 3's, time awareness, and narrative loop guidance."""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                if facts_block and isinstance(prompt, str) and prompt.strip():
                    prompt = f"{facts_block}\n\n{prompt}"
        except Exception:
            pass
        # Enhance prompt with narrative context if available
        enhanced_prompt = self._enhance_prompt_with_narrative_context(prompt)
        
        # Enhance prompt with RAG worldbuilding context if available
        enhanced_prompt = self._enhance_prompt_with_rag(enhanced_prompt)
        
        # Enhance prompt with Rule of 3's guidance if context is available
        enhanced_prompt = self._enhance_prompt_with_rule_of_3s(enhanced_prompt, rule_of_3s_context)
        
        # Enhance prompt with time context if available
        enhanced_prompt = self._enhance_prompt_with_time_context(enhanced_prompt, time_context)
        
        # Enhance prompt with narrative loop guidance if available
        enhanced_prompt = self._enhance_prompt_with_narrative_loop(enhanced_prompt, framing_guidance)

        # Mention tagging rule (Strategy C): emit explicit @Name markers for off-screen people.
        # This keeps mention capture fast and setting-agnostic (no heuristics/stoplists).
        try:
            enhanced_prompt = (
                f"{enhanced_prompt}\n\n"
                "**MENTION TAGGING (CRITICAL):**\n"
                "- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.\n"
                "- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.\n"
                "- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{role}'.\n"
                "- Examples: '@{mentor}', '@{best friend}', '@{captain}'.\n"
                "- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).\n"
            )
        except Exception:
            pass
        
        # Use centralized robust LLM call
        content = robust_llm_call(
            client=self.client,
            messages=[{"role": "user", "content": enhanced_prompt}],
            model=self.model,
            temperature=0.7,
            max_tokens=512,
            max_retries=RetryConfig.MAX_RETRIES,
            timeout=30,
            call_name="NARRATION"
        )
        
        return content

    def _sanitize_narrative(self, text: Optional[str]) -> str:
        """
        Remove sentences or trailing clauses that reference out-of-world/gamey concepts
        (e.g., rounds, turns, initiative, stats). This keeps narration strictly diegetic.
        """
        if not text:
            return ""
        cleaned = text.strip()

        # Normalize dashes to simplify clause removal
        dash_variants = ["—", "–", "-", "––"]
        for dv in dash_variants:
            cleaned = cleaned.replace(dv + " ", " - ")

        # Use phrases rather than single words to avoid false positives like "round table" or "turn the handle"
        banned_phrases = [
            "before the next round", "next round", "new round", "this round", "end of round", "round of combat",
            "turn order", "your turn", "their turn", "next turn", "end of turn", "start of turn",
            "initiative", "hit points", "hp", "xp", "cooldown", "encounter mode", "simulation state",
            "game mechanic", "mechanic", "stats", "stat", "meta"
        ]

        # Split into sentences conservatively
        import re
        sentences = re.split(r"(?<=[.!?])\s+", cleaned)
        def is_banned(s: str) -> bool:
            lower = s.lower()
            return any(phrase in lower for phrase in banned_phrases)

        kept = [s for s in sentences if s and not is_banned(s)]
        result = " ".join(kept).strip()

        # If nothing left, fall back to original first sentence without banned fragments after dash
        if not result and sentences:
            first = sentences[0]
            # Strip trailing dash clause if it contains banned tokens
            parts = [p.strip() for p in first.split(" - ")]
            safe_parts = [p for p in parts if not is_banned(p)]
            result = safe_parts[0] if safe_parts else first

        return result
    
    def _strip_meta_time_references(self, text: str) -> str:
        """
        Strip meta time references (vintage, old, retro, etc.) from narrative.
        This is a post-processing filter since the LLM keeps ignoring the prompt.
        """
        if not text:
            return text
        
        import re
        
        # Banned words and their replacements
        # Remove temporal qualifiers that break immersion
        # These words imply the narrator is from a different time period
        replacements = {
            r'\bvintage\s+': '',  # "vintage turntable" → "turntable"
            r'\bold\s+': '',      # "old cassette" → "cassette"
            r'\bretro\s+': '',    # "retro lamp" → "lamp"
            r'\bclassic\s+': '',  # "classic TV" → "TV"
            r'\bdated\s+': '',    # "dated answering machine" → "answering machine"
            r'\boutdated\s+': '', # "outdated answering machine" → "answering machine"
            r'\bold-school\s+': '', # "old-school turntable" → "turntable"
            r'\bmodern\s+': '',   # "modern device" → "device" (implies future perspective)
            r'\bfuturistic\s+': '', # "futuristic device" → "device" (implies past perspective)
        }
        
        cleaned = text
        for pattern, replacement in replacements.items():
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        # Clean up double spaces
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        return cleaned.strip()
    
    def _strip_anachronistic_dates(self, text: str) -> str:
        """
        Strip anachronistic future dates from media playback content.
        This catches dates that break temporal continuity with the established time period.
        Uses aggressive filtering to prevent any year references from slipping through.
        """
        if not text:
            return text
        
        import re
        
        # Year stripping removed: years like 2025 are valid in the Echodrome world.
        # The worldbuilding context determines what is era-appropriate, not regex filtering.
        cleaned = text
        
        # Clean up artifacts (double spaces, trailing punctuation)
        cleaned = re.sub(r'\s+', ' ', cleaned)
        cleaned = re.sub(r'\s+([,.:;!?])', r'\1', cleaned)  # Fix "word ," → "word,"
        
        return cleaned.strip()

    def _enhance_prompt_with_rule_of_3s(self, prompt: str, context: Optional[RuleOf3Context] = None) -> str:
        """Enhance narrative prompts with Rule of 3's temporal guidance."""
        if not context:
            context = self.current_rule_of_3s_context
        
        if not context:
            return prompt
        
        from rule_of_3s import RuleOf3Classifier
        classifier = RuleOf3Classifier()
        guidance = classifier.get_narrative_guidance(context.category)
        
        rule_of_3s_enhancement = f"""

**RULE OF 3'S TEMPORAL CONTEXT:**
- Current Timeframe: {context.category.value}
- Context: {context.description}
- Pacing: {guidance['pacing']}
- Detail Level: {guidance['detail_level']}
- Narrative Tone: {guidance['narrator_tone']}

**NARRATIVE ADAPTATION REQUIRED:**
Adapt your narrative style to match the {context.category.value} timeframe. {guidance['detail_level']} Use {guidance['pacing']} pacing with a {guidance['narrator_tone']} tone.
"""
        
        return prompt + rule_of_3s_enhancement
    
    def _enhance_prompt_with_narrative_loop(self, prompt: str, framing_guidance: Optional[Dict[str, Any]] = None) -> str:
        """Enhance narrative prompts with Four-Mode Narrative Loop guidance."""
        if not framing_guidance:
            return prompt
        
        mode = framing_guidance.get('mode', 'roam')
        tone = framing_guidance.get('tone', 'calm')
        intent = framing_guidance.get('intent')
        narrative_guidance = framing_guidance.get('narrative_guidance', '')
        diegetic_cues = framing_guidance.get('diegetic_cues', [])
        
        loop_enhancement = f"""

**FOUR-MODE NARRATIVE LOOP GUIDANCE:**
- Current Mode: {mode.upper()} ({framing_guidance.get('framing_type', 'exploration')})
- Narrative Tone: {tone.upper()}
- Current Intent: {intent if intent else 'Open exploration'}
- Guidance: {narrative_guidance}
"""
        
        if diegetic_cues:
            loop_enhancement += f"""
- Diegetic Cues: {'; '.join(diegetic_cues)}
"""
        
        loop_enhancement += """
**INVISIBLE SCAFFOLDING REQUIREMENTS:**
- Use ONLY diegetic elements (dialogue, environmental details, opportunities)
- NO visible mechanics, meters, or gamey language
- Frame naturally at points of uncertainty
- Let story beats emerge organically from actor behavior
"""
        
        return prompt + loop_enhancement
    
    def _enhance_prompt_with_time_context(self, prompt: str, time_context: Optional[Dict[str, Any]] = None) -> str:
        """Enhance narrative prompts with current time-of-day context."""
        if not time_context:
            return prompt
        
        time_of_day = time_context.get('time_of_day')
        atmospheric_desc = time_context.get('atmospheric_description', '')
        lighting = time_context.get('lighting_condition', '')
        current_time = time_context.get('current_time', '')
        
        if not time_of_day:
            return prompt
        
        time_enhancement = f"""

**CURRENT TIME CONTEXT:**
- Time: {current_time}
- Time of Day: {time_of_day.value.replace('_', ' ').title()}
- Atmosphere: {atmospheric_desc}
- Lighting: {lighting}

**NARRATIVE TIME CONSISTENCY REQUIRED:**
Ensure all narrative descriptions are consistent with the current time of day. Use appropriate lighting, atmospheric details, and time-appropriate language. Do NOT describe nighttime scenes during daytime or vice versa.
"""
        
        return prompt + time_enhancement

    def set_rule_of_3s_context(self, context: RuleOf3Context) -> None:
        """Set the current Rule of 3's context for narrative awareness."""
        self.current_rule_of_3s_context = context

    def narrate_scene_introduction(self, scene_elements: dict, nua_name: str, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a compelling narrative introduction for a new scene with transition continuity.
        """
        setting = scene_elements.get('setting', 'an unknown location')
        ua_goal = scene_elements.get('ua_goal', 'an unknown goal')
        conflict = scene_elements.get('conflict', 'an unknown conflict')
        transition_bridge = scene_elements.get('transition_bridge', '')
        opportunities = scene_elements.get('exploration_opportunities', []) or []

        prompt = f"""You are a perception describer. Your task is to write a compelling, immersive and decriptivenarrative introduction to a scene with smooth continuity.
        The introduction should be from a second-person (\"You\") perspective.

        **Scene Elements:**
        - **Setting:** {setting}
        - **Your Goal:** {ua_goal}
        - **The Conflict:** {conflict}
        - **The Opponent:** {nua_name}
        - **Transition Bridge:** {transition_bridge}

        **Your Task:**
        Create a narrative that flows smoothly from previous events. If a transition bridge is provided, incorporate it naturally into the opening. Then weave in the setting, goal, and conflict. Make it feel like a natural continuation of an ongoing story.

        **Enhanced Example with Transition:**
        - **Transition Bridge:** "After successfully negotiating with the merchant, you pocket the ancient map and step back onto the bustling street."
        - **Setting:** A narrow alley in the merchant district.
        - **Your Goal:** Reach the cathedral district safely with the map.
        - **The Conflict:** A hooded figure is following you, interested in what you carry.

        **Good Narrative with Continuity:**
        \"After successfully negotiating with the merchant, you pocket the ancient map and step back onto the bustling street. The information you've gained points toward the old cathedral district, but as you make your way through the crowd, you notice a hooded figure has been following you since you left the shop. They seem particularly interested in the scroll case you're carrying. When you turn down a quieter alley to test your suspicions, they follow. It's clear they want what you have, and this narrow passage offers little room for escape.\"

        Now, produce the narrative for the given context. Respond with ONLY the narrative text.
        """
        
        narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)

        if not narrative:
            # Fallback to a simple description if LLM fails
            opp_text = f" You notice {'; '.join(opportunities).lower()}" if opportunities else ""
            return f"SCENE: You are in {setting}, trying to {ua_goal}. You are opposed by {nua_name} due to: {conflict}.{opp_text}"
        
        # Clean up the narrative by removing extra whitespace and normalizing line breaks
        cleaned_narrative = ' '.join(narrative.strip().split())
        cleaned_narrative = self._sanitize_narrative(cleaned_narrative)
        return f"SCENE: {cleaned_narrative}"

    def _strip_meta_time_references(self, text: str) -> str:
        """
        Removes meta-references to time periods that break immersion.
        """
        if not text:
            return text
            
        # List of banned meta-terms
        banned = [
            "vintage", "retro", "classic style", "old-school", 
            "relic from", "bygone era", "dated", "outdated",
            "state-of-the-art for its time", "modern for the time"
        ]
        
        # Simple replacement (could be more sophisticated)
        cleaned = text
        for term in banned:
            # Case insensitive replacement
            import re
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            cleaned = pattern.sub("", cleaned)
            
        return cleaned

    def _enhance_sensory_quality(self, narrative: str, time_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Enhances the sensory quality of the narrative.
        Currently a pass-through to prevent AttributeError, but ready for logic expansion.
        """
        if not narrative:
            return ""
        return narrative

    def generate_scene_description(self, scene_data: Dict[str, Any], scene_type: str, time_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate a rich, perceptual scene description for location shifts (e.g., moving into a diner).
        
        Replaces the rigid previous system with one mirroring generate_inquiry_response for consistency.
        """
        setting = (scene_data or {}).get('setting', 'an interior space')
        ua_goal = (scene_data or {}).get('ua_goal', '')
        spatial_facts = (scene_data or {}).get('spatial_facts', '')
        
        # Get RAG worldbuilding context with category filters
        rag_context = ""
        if self.rag_system:
            try:
                context_parts = []
                
                # Category: TEMPORAL for time period/era (CRITICAL - must come first)
                temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                temporal_ctx = self.rag_system.get_context_for_llm(
                    query="time period era setting year world",
                    max_tokens=200,
                    category_filter=temporal_category
                )
                if temporal_ctx:
                    context_parts.append(f"**TIME PERIOD & ERA:**\n{temporal_ctx}")
                
                # Category: PLACES for location details
                places_category = WorldbuildingCategory.PLACES if WorldbuildingCategory else None
                places_ctx = self.rag_system.get_context_for_llm(
                    query=f"{setting} location environment",
                    max_tokens=150,
                    category_filter=places_category
                )
                if places_ctx:
                    context_parts.append(places_ctx)
                
                # Category: CULTURE for sensory/atmospheric details
                culture_category = WorldbuildingCategory.CULTURE if WorldbuildingCategory else None
                culture_ctx = self.rag_system.get_context_for_llm(
                    query="sensory atmosphere sounds smells textures",
                    max_tokens=150,
                    category_filter=culture_category
                )
                if culture_ctx:
                    context_parts.append(culture_ctx)
                
                # Category: NARRATION_STYLE_TONE for narrative style
                style_category = WorldbuildingCategory.NARRATION_STYLE_TONE if WorldbuildingCategory else None
                style_ctx = self.rag_system.get_context_for_llm(
                    query="narration style tone atmosphere",
                    max_tokens=100,
                    category_filter=style_category
                )
                if style_ctx:
                    context_parts.append(style_ctx)
                
                if context_parts:
                    rag_context = f"\n**WORLDBUILDING CONTEXT:**\n" + "\n\n".join(context_parts) + "\n"
            except Exception:
                pass
        
        # Get concrete details to maintain consistency
        concrete_details_context = ""
        if self.narrative_context_manager:
            try:
                # Get all concrete details for current scene to prevent contradictions
                # We use "current" as placeholder since we are establishing the new current
                all_details = self.narrative_context_manager.detail_tracker.get_all_active_details_context(
                    scene_id="current",
                    recent_owners=[]
                )
                if all_details:
                    concrete_details_context = f"""**ESTABLISHED CONCRETE DETAILS (MUST MAINTAIN CONSISTENCY):**
{all_details}

**CRITICAL:** Any information you generate MUST be consistent with the above details.
"""
            except Exception:
                pass
        
        # Format time context
        time_str = ""
        if time_context:
            time_of_day = time_context.get('time_of_day', 'unknown')
            formatted_time = time_context.get('formatted_time', 'unknown')
            time_str = f"**CURRENT TIME:** {formatted_time} ({time_of_day})"
            
        # Format NPCs with stranger-appropriate descriptions
        npcs_present = scene_data.get('npcs_present', []) if scene_data else []
        ua_actor = scene_data.get('ua_actor') if scene_data else None
        relationship_system = scene_data.get('relationship_system') if scene_data else None
        
        if npcs_present:
            npcs_formatted = self.format_npcs_for_prompt(
                npcs_present, ua_actor, setting, relationship_system
            )
        else:
            npcs_formatted = "NONE (Empty)"

        spatial_facts_block = ""
        if isinstance(spatial_facts, str) and spatial_facts.strip():
            spatial_facts_block = f"""
**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{spatial_facts.strip()}
"""

        no_people_rule = ""
        if not npcs_present:
            no_people_rule = """
**CRITICAL - GROUNDED POPULATION RULE (MANDATORY):**
- NPCs Present is NONE, so you MUST NOT mention or imply any people or person-like entities.
- Do NOT describe: "a figure", "a bartender", "a stranger", "someone", "a man", "a woman", "patrons", or any humanoid presence.
- Only describe environment, objects, sounds, smells, and empty-room stillness.
"""
        
        prompt = f"""Generate a RICH PERCEPTUAL SCENE DESCRIPTION for entering a new location.

{rag_context}
{concrete_details_context}
{time_str}
{spatial_facts_block}

**CONTEXT:**
- Setting Seed: {setting}
- User Goal: {ua_goal}
- NPCs Present: {npcs_formatted}

{no_people_rule}

{self.SENSORY_PERCEPTION_REQUIREMENTS}

**CRITICAL - ERA ENFORCEMENT (MANDATORY):**
- You MUST use ONLY technology, objects, and cultural elements that exist in the TIME PERIOD specified in the worldbuilding context above
- ANACHRONISMS ARE FORBIDDEN - every detail must fit the era specified
- The time period is ALWAYS defined by the worldbuilding context above - never assume or invent a period

**CRITICAL - STRANGER NAMING RULES:**
- For NPCs marked as STRANGER: Do NOT use their name. Describe them by appearance, occupation, or distinguishing features.
- For NPCs marked as KNOWN: You may use their name.
- Example STRANGER descriptions: "a hulking man at the counter", "the waitress with dark hair", "an elderly woman in a faded coat"
- This creates realistic perception - we don't magically know strangers' names!

**IMMERSIVE TIME PERSPECTIVE (MANDATORY):**
- You exist IN this time period - it is YOUR present day
- All technology in the setting is CURRENT and NORMAL to you
- NEVER describe things as "vintage", "retro", "old-school", "modern", or "futuristic"
- Describe objects as they ARE in the moment - no temporal qualifiers

**INSTRUCTIONS:**
1. **Start immediately with the action:** Continue the thought "You step into..." or describe the immediate sensory hit.
2. **Pick 1-2 senses most distinctive for THIS location.** Do not enumerate all senses — choose the ones that define this specific space.
3. **Atmosphere:** Capture the mood through those chosen senses only.
4. **ERA-APPROPRIATE:** Every object, sound, smell MUST exist in the specified time period.
5. **Length:** 2-3 focused sentences. No more.
6. **STRANGERS:** Describe by appearance/occupation, NOT by name.

**ABSOLUTE RULE:**
- DO NOT use meta-narrative ("The room is...", "It appears to be...").
- ALWAYS use Active Perception ("You see...", "You smell...", "The air tastes like...").
- If NPCs are present, describe them as part of the scene.
- If empty, describe the stillness/silence perceptually.

**Generate the scene description:**
"""

        narrative = self._call_llm(prompt, time_context=time_context)
        
        if narrative:
            narrative = self._strip_meta_time_references(narrative)
            narrative = self._enhance_sensory_quality(narrative, time_context)

        if not narrative or not narrative.strip():
            # Fallback minimal description using proper perceptual format
            # Extract location name from setting if possible
            location_name = "the space"
            if setting and isinstance(setting, str):
                # Try to extract location name from "You step into the X." pattern
                import re
                match = re.search(r'step into (?:the )?(\w+)', setting.lower())
                if match:
                    location_name = match.group(1)
            
            # Generate perceptual fallback (not hardcoded to diner)
            fallback = (
                f"You step inside and your eyes adjust to the interior light. "
                f"You smell the faint traces of activity that linger in the air. "
                f"You hear the ambient sounds of the space settling around you. "
                f"The {location_name} stretches before you, waiting to be explored."
            )
            return self._sanitize_narrative(fallback)

        # Extract mentions from scene description
        # Get actors in scene if available from scene_data
        npcs_present = scene_data.get('npcs_present', []) if scene_data else []
        actors_in_scene = [npc.sheet.name if hasattr(npc, 'sheet') else str(npc) for npc in npcs_present]

        # Add UA if present
        ua_actor = scene_data.get('ua_actor') if scene_data else None
        if ua_actor and hasattr(ua_actor, 'sheet'):
            actors_in_scene.append(ua_actor.sheet.name)

        self._extract_narrative_mentions(
            narrative=narrative,
            actors_in_scene=actors_in_scene,
            turn_number=0,  # Scene description doesn't have turn number
            scene_id=scene_type or "scene_description"
        )

        return self._sanitize_narrative(narrative)

    def _get_gerund(self, action_noun: str) -> str:
        """A simple helper to create a gerund from an action noun."""
        if not action_noun:
            return "acting"
        if action_noun.endswith("e"):
            return action_noun[:-1] + "ing"
        if action_noun.endswith("p") or action_noun.endswith("t") or action_noun.endswith("g"):
            return action_noun + action_noun[-1] + "ing"
        return action_noun + "ing"

    def _get_shift_magnitude_descriptor(self, shift_amount: float) -> str:
        """DEPRECATED: Use N2N_Shift_Magnitude from narrative_utils for UTAS compliance."""
        return N2N_Shift_Magnitude(int(abs(shift_amount)))

    def generate_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], outcome_data: Dict[str, Any], time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None, ua_actor=None, relationship_system=None) -> str:
        """
        Generates the full narrative for a turn based on the provided data.

        Args:
            proactor_data: Dictionary with proactor's details.
            reactor_data: Dictionary with reactor's details.
            outcome_data: Dictionary with the turn's outcome details.
            ua_actor: The user actor (for stranger description checks)
            relationship_system: Relationship tracker (for stranger description checks)

        Returns:
            A formatted string containing the full narrative.
        """
        action_narrative = self._build_action_narrative(proactor_data, reactor_data, time_context, framing_guidance, ua_actor, relationship_system)
        reaction_narrative = self._build_reaction_narrative(proactor_data, reactor_data, time_context, framing_guidance, ua_actor, relationship_system)
        outcome_narrative = self._build_outcome_narrative(proactor_data, reactor_data, outcome_data, time_context, framing_guidance, ua_actor, relationship_system)

        return (
            f"Narrator Agent Output:\n"
            f"- Proactor Action: \"{action_narrative}\"\n"
            f"- Reactor Reaction: \"{reaction_narrative}\"\n"
            f"- Outcome: \"{outcome_narrative}\""
        )

    def _build_action_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None, ua_actor=None, relationship_system=None) -> str:
        """Uses an LLM to generate a rich, descriptive narrative for the proactor's action."""

        factors = proactor_data.get('utas_factors', {})
        proactor_name_raw = proactor_data.get('name')
        reactor_name_raw = reactor_data.get('name')
        
        if not proactor_name_raw:
            raise ValueError("Proactor name is missing from action data - this indicates a data flow issue")
        if not reactor_name_raw:
            raise ValueError("Reactor name is missing from action data - this indicates a data flow issue")
        
        # Check if proactor is UA
        is_user_actor = proactor_data.get('is_user_actor', False)
        
        # Get stranger-aware names (use descriptions for unknown NPCs)
        proactor_name = self.get_stranger_aware_name(proactor_data, ua_actor, relationship_system)
        reactor_name = self.get_stranger_aware_name(reactor_data, ua_actor, relationship_system)
        
        # Get spatial context for spatially-aware narration
        try:
            from agents.spatial_context_helper import get_spatial_context_for_prompt
            spatial_context = get_spatial_context_for_prompt(proactor_name=f"YOU ({proactor_name})" if is_user_actor else proactor_name)
        except Exception:
            spatial_context = ""
        
        action_desc = proactor_data.get("narrative_description", "takes action against their opponent")
        targeted_status = factors.get("status_to_shift", "SPIRIT").capitalize()
        
        skill_name = factors.get("skill", {}).get("name") or "instincts"
        skill_val = factors.get("skill_val", 0)
        n2n_skill = N2N_Skill_Level(skill_val)

        s_trait_name = factors.get("s_trait_to_use", "STURDINESS").capitalize()
        s_trait_val = factors.get("s_trait_val", 0)
        n2n_s_trait = N2N_S_Trait_Level(s_trait_val)

        endowment_name = factors.get("endowment", {}).get("name")
        endowment_val = factors.get("endowment_val", 0)
        n2n_endowment = N2N_Endowment_Level(endowment_val) if endowment_name else None

        supplement_name = factors.get("supplement_name")
        
        stress_level = factors.get("stress_level", 3)
        n2n_difficulty = self._get_n2n_difficulty(stress_level)
        
        serendipity_val = factors.get("serendipity", 0)
        n2n_serendipity = self._get_n2n_serendipity(serendipity_val)

        status_modifier = factors.get("status_modifier", 0)
        endowment_line = (
            f"- **Endowment Ability:** You are channeling your endowment ability, '{endowment_name}', at a '{n2n_endowment}' level."
            if endowment_name and n2n_endowment else ""
        )
        supplement_line = f"- **Supplement:** You are using a '{supplement_name}'." if supplement_name else ""
        observer_endowment_line = (
            f"- **Endowment Ability:** {proactor_name} is channeling their endowment ability, '{endowment_name}', at a '{n2n_endowment}' level."
            if endowment_name and n2n_endowment else ""
        )
        observer_supplement_line = f"- **Supplement:** {proactor_name} is using a '{supplement_name}'." if supplement_name else ""
        observer_current_state_line = f"{proactor_name}'s current state does not significantly affect them."
        
        if is_user_actor:
            # UA gets second person
            status_effect_desc = ""
            if status_modifier > 0:
                status_effect_desc = "Your current state hinders your efforts, making the action feel sluggish and difficult."
            elif status_modifier < 0:
                status_effect_desc = "You feel invigorated, a surge of energy making the action feel effortless and powerful."

            # Build the detailed prompt for UA (second person)
            prompt = f"""
        You are a Narrator narrating a turn in a simulation from a second-person ("You") perspective.
        Your task is to weave the following mechanical details into a single, compelling narrative paragraph describing your action.
{spatial_context}
        **Your Mechanical Details:**
        - **Your Action:** "{action_desc}"
        - **Targeted Status:** You are targeting your opponent's '{targeted_status}'.
        - **Difficulty:** {n2n_difficulty} (due to your stress level)
        - **Primary Skill:** You are using your '{skill_name}' at a '{n2n_skill}' level.
        - **Primary Trait:** You are relying on your '{s_trait_name}' at a '{n2n_s_trait}' level.
        {endowment_line}
        {supplement_line}
        - **Luck:** This action is undertaken with {n2n_serendipity}.
        - **Current State:** {status_effect_desc if status_effect_desc else 'Your current state does not significantly affect you.'}

        **CRITICAL - DIEGETIC NARRATION RULES:**
        1. **SHOW, DON'T TELL:** Describe what you SEE, HEAR, FEEL, DO - not abstract states
           - ❌ "The room is empty" → ✅ "You scan the room. No one's here."
           - ❌ "You feel confident" → ✅ "Your hands are steady, your breathing calm."
        2. **IMMEDIATE SENSORY:** Focus on what's happening RIGHT NOW in this moment
           - ❌ "This will be difficult" → ✅ "Your muscles tense as you prepare"
        3. **NO NARRATOR COMMENTARY:** You are experiencing this, not being told about it
           - ❌ "You are skilled at this" → ✅ "The movement comes naturally"
        4. **PRESENT TENSE, ACTIVE VOICE:** Everything happens NOW
        5. **CONCRETE ACTIONS:** Physical, tangible, observable actions and sensations

        **Your Task:**
        Write a single, flowing narrative paragraph using DIEGETIC narration. **Do not just list the details.** Describe what *you* physically do, what you sense, and how the action feels in your body. **Crucially, phrase the core action using a gerund (verb ending in -ing).** Make it vivid, immediate, and experiential.

        **Example:**
        - **Good (Diegetic):** "Your heart pounds as you grip the blade tighter. Drawing on muscle memory, you lunge forward, **stabbing** toward their guard. Your foot slips slightly on the wet floor—damn—but you push through, driving the point home."
        - **Bad (Non-Diegetic):** "The situation is challenging, but you act with purpose. Drawing upon your Adept 'Blade' skill and 'Precise' nature, you lunge forward, stabbing at your opponent's defenses. A bit of bad luck nearly throws you off balance."

        Now, produce the DIEGETIC narrative for the given context. Respond with ONLY the narrative text.
        """
        else:
            # NUA gets PERCEPTUAL DESCRIPTION (what UA sees/perceives)
            status_effect_desc = ""
            if status_modifier > 0:
                status_effect_desc = f"You see {proactor_name}'s movements appear sluggish and difficult."
            elif status_modifier < 0:
                status_effect_desc = f"You see {proactor_name} move with invigorated energy and power."

            # Build the detailed prompt for NUA (perceptual description from UA's perspective)
            prompt = f"""
        You are a Narrator narrating a turn in a simulation from the USER ACTOR'S PERCEPTUAL PERSPECTIVE.
        Your task is to describe what the USER ACTOR (YOU) SEES, HEARS, and PERCEIVES as {proactor_name} attempts their action.
{spatial_context}
        **{proactor_name}'s Mechanical Details:**
        - **Action:** "{action_desc}"
        - **Targeted Status:** {proactor_name} is targeting {reactor_name}'s '{targeted_status}'.
        - **Difficulty:** {n2n_difficulty} (due to stress level)
        - **Primary Skill:** {proactor_name} is using their '{skill_name}' at a '{n2n_skill}' level.
        - **Primary Trait:** {proactor_name} is relying on their '{s_trait_name}' at a '{n2n_s_trait}' level.
        {observer_endowment_line}
        {observer_supplement_line}
        - **Luck:** This action is undertaken with {n2n_serendipity}.
        - **Current State:** {status_effect_desc if status_effect_desc else observer_current_state_line}

        **CRITICAL - PERCEPTUAL DESCRIPTION RULES:**
        1. **ALWAYS START WITH PERCEPTION VERBS:** "You see...", "You hear...", "You notice...", "You watch..."
           - ❌ "{proactor_name} runs toward you" → ✅ "You see {proactor_name} attempt to run at you"
           - ❌ "{proactor_name} swings their fist" → ✅ "You see {proactor_name}'s fist swing toward you"
        2. **DESCRIBE WHAT IS OBSERVABLE:** Only what the USER can see, hear, or sense
           - ❌ "{proactor_name} feels confident" → ✅ "You see {proactor_name}'s steady hands and calm breathing"
           - ❌ "{proactor_name} is skilled" → ✅ "You see {proactor_name} move with practiced ease"
        3. **USE ATTEMPT LANGUAGE:** NPCs are ATTEMPTING actions, not completing them
           - ❌ "You see {proactor_name} stab you" → ✅ "You see {proactor_name} attempt to stab at you"
           - ❌ "You see {proactor_name} punch you" → ✅ "You see {proactor_name}'s fist coming toward you"
        4. **PRESENT TENSE, ACTIVE VOICE:** Everything happens NOW
        5. **SENSORY FOCUS:** What does the USER see, hear, feel happening around them?

        **Your Task:**
        Write a single, flowing narrative paragraph describing what the USER ACTOR PERCEIVES as {proactor_name} attempts their action. **ALWAYS use perception verbs** ("You see", "You hear", "You notice", "You watch"). Describe the ATTEMPT using a gerund (verb ending in -ing). Make it vivid and immediate from the USER's sensory perspective.

        **Examples:**
        - **CORRECT (Perceptual):** "You see {proactor_name}'s eyes narrow. You watch them lunge forward, **stabbing** toward you with their blade. You hear their footsteps—quick, aggressive—as they close the distance."
        - **INCORRECT (Third Person):** "{proactor_name}'s eyes narrow. They lunge forward, **stabbing** toward you with their blade. Their footsteps are quick and aggressive as they close the distance."
        - **CORRECT (Perceptual):** "You see {proactor_name} attempt to run at you, their boots pounding against the pavement. You hear their heavy breathing as they charge forward."
        - **INCORRECT (Third Person):** "{proactor_name} runs toward you, boots pounding against the pavement. Their breathing is heavy as they charge forward."

        Now, produce the PERCEPTUAL DESCRIPTION for the given context. Respond with ONLY the narrative text. ALWAYS START WITH "You see" or "You hear" or "You notice" or "You watch".
        """
        
        narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)

        if not narrative:
            # Fallback to a simple description if LLM fails
            action_gerund = self._get_gerund(proactor_data.get('action_noun', 'acting'))
            if is_user_actor:
                fallback_narrative = (
                    f"You make a {n2n_difficulty} attempt, {action_gerund} at {reactor_name}, "
                    f"drawing upon your {n2n_skill} {skill_name} and {n2n_s_trait} {s_trait_name}."
                )
            else:
                # NUA fallback uses perceptual description
                fallback_narrative = (
                    f"You see {proactor_name} attempt to {action_gerund.replace('ing', '')} at {reactor_name}."
                )
            return fallback_narrative

        # Extract mentions from action narrative
        if framing_guidance:
            turn_number = framing_guidance.get('turn_number', 0)
            scene_id = framing_guidance.get('scene_id', '')
            # Get actors in scene if available
            actors_in_scene = []
            if proactor_data:
                actors_in_scene.append(proactor_data.get('name', ''))
            if reactor_data:
                actors_in_scene.append(reactor_data.get('name', ''))

            self._extract_narrative_mentions(
                narrative=narrative,
                actors_in_scene=actors_in_scene,
                turn_number=turn_number,
                scene_id=scene_id
            )

        return self._sanitize_narrative(narrative.strip())

    def _get_n2n_difficulty(self, stress_level: int) -> str:
        """Use centralized N2N_Difficulty mapping (Routine→Formidable)."""
        return N2N_Difficulty(int(stress_level))

    def _get_n2n_level(self, value: int) -> str:
        """DEPRECATED: Use specific N2N_* functions directly (kept for legacy)."""
        return N2N_Skill_Level(int(value))

    def _get_n2n_serendipity(self, serendipity_val: int) -> str:
        """Use centralized N2N_Serendipity_Level mapping."""
        return N2N_Serendipity_Level(int(serendipity_val))

    def _build_reaction_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None, ua_actor=None, relationship_system=None) -> str:
        """Uses an LLM to generate a rich, descriptive narrative for the reactor's action.
        
        When reactor is UA, describes how UA PERCEIVES the proactor's action through their senses.
        """

        proactor_name_raw = proactor_data.get('name')
        proactor_action_desc = proactor_data.get('narrative_description', 'their opponent\'s action')
        reactor_name_raw = reactor_data.get('name')
        
        if not proactor_name_raw:
            raise ValueError("Proactor name is missing from reaction narrative data - this indicates a data flow issue")
        if not reactor_name_raw:
            raise ValueError("Reactor name is missing from reaction narrative data - this indicates a data flow issue")
        
        # Get stranger-aware names (use descriptions for unknown NPCs)
        proactor_name = self.get_stranger_aware_name(proactor_data, ua_actor, relationship_system)
        reactor_name = self.get_stranger_aware_name(reactor_data, ua_actor, relationship_system)
        
        factors = reactor_data.get('utas_factors', {})
        action_desc = reactor_data.get("narrative_description", "you react defensively")

        skill_name = factors.get("skill", {}).get("name") or "instincts"
        skill_val = factors.get("skill_val", 0)
        n2n_skill = N2N_Skill_Level(skill_val)

        s_trait_name = factors.get("s_trait_to_use", "STURDINESS").capitalize()
        s_trait_val = factors.get("s_trait_val", 0)
        n2n_s_trait = N2N_S_Trait_Level(s_trait_val)

        endowment_name = factors.get("endowment", {}).get("name")
        endowment_val = factors.get("endowment_val", 0)
        n2n_endowment = N2N_Endowment_Level(endowment_val) if endowment_name else None

        supplement_name = factors.get("supplement_name")
        
        stress_level = factors.get("stress_level", 3)
        n2n_difficulty = self._get_n2n_difficulty(stress_level)
        
        serendipity_val = factors.get("serendipity", 0)
        n2n_serendipity = self._get_n2n_serendipity(serendipity_val)

        status_modifier = factors.get("status_modifier", 0)
        status_effect_desc = ""
        if status_modifier > 0:
            status_effect_desc = "Your current state hinders your efforts, making your reaction feel sluggish and difficult."
        elif status_modifier < 0:
            status_effect_desc = "You feel invigorated, a surge of energy making your reaction feel effortless and powerful."

        # Check if reactor is UA for perception-based narration
        reactor_is_ua = reactor_data.get('is_user_actor', False)
        user_reaction_supplement_line = f"- **Supplement:** You are using a '{supplement_name}'." if supplement_name else ""
        reactor_endowment_line = (
            f"- **Endowment Ability:** {reactor_name} is channeling their endowment ability, '{endowment_name}', at a '{n2n_endowment}' level."
            if endowment_name and n2n_endowment else ""
        )
        reactor_supplement_line = f"- **Supplement:** {reactor_name} is using a '{supplement_name}'." if supplement_name else ""
        reactor_current_state_line = f"You see {reactor_name}'s current state does not appear to affect them significantly."
        
        # Build the detailed prompt
        if reactor_is_ua:
            # UA reactor - perception-based narration
            prompt = f"""You are a perception describer narrating a turn in a Simulation from a second-person ("You") perspective.
Your task is to weave the following mechanical details into a single, compelling narrative paragraph describing how you PERCEIVE and react to an opponent's move.

**CRITICAL - PERCEPTION-BASED NARRATION:**
- Describe how you SEE, HEAR, FEEL the opponent's action through your senses
- Use phrases like "you see {proactor_name}...", "you feel the impact...", "you hear..."
- Focus on what you PERCEIVE happening, not what objectively happens
- Show your sensory experience of the threat/action

**Context:**
- **What You Perceive:** You see {proactor_name} attempting to '{proactor_action_desc}'.

**Your Mechanical Details:**
- **Your Reaction:** "{action_desc}"
- **Difficulty:** {n2n_difficulty} (due to your stress level)
- **Primary Skill:** You are using your '{skill_name}' at a '{n2n_skill}' level.
- **Primary Trait:** You are relying on your '{s_trait_name}' at a '{n2n_s_trait}' level.
- **Endowment Ability:** You are channeling your endowment ability, '{endowment_name}', at a '{n2n_endowment}' level.
{user_reaction_supplement_line}
- **Luck:** This action is undertaken with {n2n_serendipity}.
- **Current State:** {status_effect_desc if status_effect_desc else 'Your current state does not significantly affect you.'}

**Your Task:**
Write a single, flowing narrative paragraph. **Do not just list the details.** Describe what *you PERCEIVE* happening and how *you* react through your senses. Use perception verbs (see, feel, hear, sense). **Crucially, phrase the core reaction using a gerund (verb ending in -ing).** Make it vivid and engaging.

**Example:**
- **Good Narrative (using a gerund):** "You see your opponent lunge toward you, and you react with lightning speed. You feel the rush of adrenaline as you draw upon your Adept 'Dodge' skill, **weaving** effortlessly out of harm's way. Your foot catches slightly—damn—but you manage to hold your ground."
- **Bad Narrative:** "You use Dodge and Graceful to dodge the attack. It is a challenging action. You have bad luck."

Now, produce the narrative for the given context. Respond with ONLY the narrative text.
"""
        else:
            # NUA reactor - perceptual description from UA's perspective
            prompt = f"""You are a master scene describer describing a turn in a simulation from the USER ACTOR'S PERCEPTUAL PERSPECTIVE.
Your task is to describe what the USER ACTOR (YOU) SEES, HEARS, and PERCEIVES as {reactor_name} attempts to react.

**Context:**
- **Opponent's Action:** {proactor_name} is attempting to '{proactor_action_desc}'.

**{reactor_name}'s Mechanical Details:**
- **Reaction:** "{action_desc}"
- **Difficulty:** {n2n_difficulty} (due to stress level)
- **Primary Skill:** {reactor_name} is using their '{skill_name}' at a '{n2n_skill}' level.
- **Primary Trait:** {reactor_name} is relying on their '{s_trait_name}' at a '{n2n_s_trait}' level.
{reactor_endowment_line}
{reactor_supplement_line}
- **Luck:** This action is undertaken with {n2n_serendipity}.
- **Current State:** {status_effect_desc if status_effect_desc else reactor_current_state_line}

**CRITICAL - PERCEPTUAL DESCRIPTION RULES:**
1. **ALWAYS START WITH PERCEPTION VERBS:** "You see...", "You hear...", "You notice...", "You watch..."
   - ❌ "{reactor_name} dodges" → ✅ "You see {reactor_name} attempt to dodge"
   - ❌ "{reactor_name} blocks the attack" → ✅ "You see {reactor_name} raise their guard to block"
2. **DESCRIBE WHAT IS OBSERVABLE:** Only what the USER can see, hear, or sense
   - ❌ "{reactor_name} feels confident" → ✅ "You see {reactor_name}'s steady stance"
3. **USE ATTEMPT LANGUAGE:** NPCs are ATTEMPTING reactions, not completing them
   - ❌ "You see {reactor_name} dodge" → ✅ "You see {reactor_name} attempt to weave out of the way"
4. **PRESENT TENSE, ACTIVE VOICE:** Everything happens NOW
5. **SENSORY FOCUS:** What does the USER see, hear, feel happening?

**Your Task:**
Write a single, flowing narrative paragraph describing what the USER ACTOR PERCEIVES as {reactor_name} attempts to react. **ALWAYS use perception verbs** ("You see", "You hear", "You notice", "You watch"). Describe the ATTEMPT using a gerund (verb ending in -ing). Make it vivid and immediate from the USER's sensory perspective.

**Examples:**
- **CORRECT (Perceptual):** "You see {reactor_name} react with lightning speed. You watch them **weave** out of harm's way, their movements practiced and agile. You hear their boots scrape against the ground as they stumble slightly but hold their ground."
- **INCORRECT (Third Person):** "As {proactor_name} lunges, {reactor_name} reacts with lightning speed. Drawing upon their Adept 'Dodge' skill, they **weave** effortlessly out of harm's way with practiced agility."
- **CORRECT (Perceptual):** "You see {reactor_name} attempt to dodge, their body twisting to the side. You notice their guard raised, ready to block if needed."
- **INCORRECT (Third Person):** "{reactor_name} dodges to the side, their guard raised and ready to block if needed."

Now, produce the narrative for the given context. Respond with ONLY the narrative text.
"""
        
        narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)

        if not narrative:
            # Fallback to a simple description if LLM fails
            action_gerund = self._get_gerund(reactor_data.get('action_noun', 'reacting'))
            if reactor_is_ua:
                fallback_narrative = (
                    f"You see {proactor_name}'s action and react, {action_gerund} in response."
                )
            else:
                # NUA reactor fallback uses perceptual description
                fallback_narrative = (
                    f"You see {reactor_name} attempt to react, {action_gerund} in response to {proactor_name}'s action."
                )
            return fallback_narrative

        # Extract mentions from reaction narrative
        if framing_guidance:
            turn_number = framing_guidance.get('turn_number', 0)
            scene_id = framing_guidance.get('scene_id', '')
            # Get actors in scene if available
            actors_in_scene = []
            if proactor_data:
                actors_in_scene.append(proactor_data.get('name', ''))
            if reactor_data:
                actors_in_scene.append(reactor_data.get('name', ''))

            self._extract_narrative_mentions(
                narrative=narrative,
                actors_in_scene=actors_in_scene,
                turn_number=turn_number,
                scene_id=scene_id
            )

        return self._sanitize_narrative(narrative.strip())

    def _build_outcome_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], outcome_data: Dict[str, Any], time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None, ua_actor=None, relationship_system=None) -> str:
        """Uses an LLM to generate a rich, descriptive narrative for the turn's outcome."""
        proactor_name_raw = proactor_data.get('name')
        reactor_name_raw = reactor_data.get('name')
        
        if not proactor_name_raw:
            raise ValueError("Proactor name is missing from outcome narrative data - this indicates a data flow issue")
        if not reactor_name_raw:
            raise ValueError("Reactor name is missing from outcome narrative data - this indicates a data flow issue")
        
        # Get stranger-aware names (use descriptions for unknown NPCs)
        proactor_name = self.get_stranger_aware_name(proactor_data, ua_actor, relationship_system)
        reactor_name = self.get_stranger_aware_name(reactor_data, ua_actor, relationship_system)
        pro_successes = outcome_data.get('proactor_success', 0)
        re_successes = outcome_data.get('reactor_success', 0)

        if pro_successes == re_successes:
            return self._generate_tie_narrative(proactor_data, reactor_data, outcome_data, time_context)

        success_diff = abs(pro_successes - re_successes)
        outcome_magnitude = self._get_shift_magnitude_descriptor(success_diff)

        if pro_successes > re_successes:
            winner_name, loser_name = proactor_name, reactor_name
            outcome_desc = f"{winner_name} achieves a {outcome_magnitude} success over {loser_name}."
            original_status_val = outcome_data.get('original_reactor_status', 0)
            updated_status_val = outcome_data.get('updated_reactor_status', 0)
        else:
            winner_name, loser_name = reactor_name, proactor_name
            outcome_desc = f"{loser_name}'s action is overcome by {winner_name} in a {outcome_magnitude} success."
            original_status_val = outcome_data.get('original_proactor_status', 0)
            updated_status_val = outcome_data.get('updated_proactor_status', 0)

        targeted_status = outcome_data.get('targeted_status', 'SPIRIT').upper()
        original_status_desc = N2N_Status_Level(original_status_val)
        updated_status_desc = N2N_Status_Level(updated_status_val)
        status_change_desc = f"{loser_name}'s {targeted_status} drops from {original_status_desc} ({original_status_val}) to {updated_status_desc} ({updated_status_val})."

        applied_effects_desc = ""
        applied_effects = outcome_data.get("applied_effects")
        if applied_effects:
            effect_descs = []
            for effect in applied_effects:
                effect_descs.append(
                    f"{effect.get('prefix', '')} {proactor_name} {effect.get('description', '')}, shifting their {effect.get('status_shifted', 'UNKNOWN').upper()} "
                    f"from {effect.get('original_status_desc', 'Unknown')} to {effect.get('updated_status_desc', 'Unknown')}."
                )
            applied_effects_desc = "\n".join(effect_descs)

        # Build the detailed prompt
        prompt = f"""
        You are a Narrator narrating the outcome of a turn in a simulation.
        Your task is to weave the following results into a single, compelling narrative paragraph.

        **Results:**
        - **Proactor:** {proactor_name}
        - **Reactor:** {reactor_name}
        - **Outcome:** {outcome_desc}
        - **Primary Consequence:** {status_change_desc}
        {'- **Additional Effects on ' + proactor_name + ':** ' + applied_effects_desc if applied_effects_desc else ''}

        **Your Task:**
        Write a single, flowing narrative paragraph that describes the climax of the exchange. **Do not just list the details.** Synthesize them into a story. Describe who won, how, and what the immediate effect was. Make it feel impactful.

        **Example:**
        - **Good Narrative:** "Despite a valiant effort, the defender's parry is overwhelmed by the sheer force of the attack. The blow lands with a sickening crunch, a massive success for the attacker that visibly shatters their opponent's composure. The defender's SPIRIT plummets from 'Confident' to 'Shaken' as they reel from the impact."
        - **Bad Narrative:** "The attacker won. The defender's SPIRIT was lowered."

        Now, produce the narrative for the given context. Respond with ONLY the narrative text.
        """

        narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)

        if not narrative:
            # Fallback to a simple description if LLM fails
            fallback_narrative = f"{outcome_desc} {status_change_desc}"
            if applied_effects_desc:
                fallback_narrative += f" Additionally, {applied_effects_desc}"
            return fallback_narrative

        return narrative.strip()

    def generate_grouped_action_narrative(
        self,
        group_results: list,
        reactor: Actor,
        reactor_success: int,
        reactor_action_data: Dict[str, Any] = None,
        time_context: Optional[Dict[str, Any]] = None,
        framing_guidance: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a cohesive narrative for a grouped NPC turn where multiple NPCs act together.
        
        Args:
            group_results: List of dicts with 'npc', 'action', 'success' for each group member
            reactor: The actor defending against the group
            reactor_success: The reactor's single defense roll
            reactor_action_data: Reactor's action data (optional)
            time_context: Time context for narrative
            framing_guidance: Narrative framing guidance
            
        Returns:
            A cohesive narrative describing the coordinated group action and reactor's response
        """
        
        # Build group member info
        group_names = [result['npc'].sheet.name for result in group_results]
        group_count = len(group_names)
        
        # Determine outcomes for each attacker
        outcomes = []
        for result in group_results:
            outcome_value = result['success'] - reactor_success
            hit = outcome_value > 0
            outcomes.append({
                'npc': result['npc'],
                'action': result['action'],
                'success': result['success'],
                'outcome': outcome_value,
                'hit': hit
            })
        
        # Count hits and misses
        hits = [o for o in outcomes if o['hit']]
        misses = [o for o in outcomes if not o['hit']]
        hit_count = len(hits)
        miss_count = len(misses)
        
        # Determine reactor perspective
        reactor_is_ua = getattr(reactor, 'is_user_actor', False)
        reactor_name = 'you' if reactor_is_ua else reactor.sheet.name
        reactor_name_cap = 'You' if reactor_is_ua else reactor.sheet.name
        
        # Build action summaries
        action_summaries = []
        for result in group_results:
            action_desc = result['action'].get('narrative_description', 'acts')
            action_summaries.append(f"{result['npc'].sheet.name} {action_desc}")
        
        # Calculate overwhelm penalty for context
        overwhelm_penalty = (group_count - 1) * 2
        
        # Build LLM prompt for cohesive narrative
        prompt = f"""
You are a master combat narrator creating a cohesive narrative for a GROUPED NPC ATTACK.

**SCENARIO:**
{group_count} NPCs are attacking {reactor_name_cap} simultaneously in a coordinated assault.

**GROUP MEMBERS & ACTIONS:**
{chr(10).join(f"- {summary}" for summary in action_summaries)}

**REACTOR:**
{reactor_name_cap} defends against the coordinated attack (overwhelm penalty: +{overwhelm_penalty} stress)

**OUTCOME:**
- Reactor Defense Roll: {reactor_success:+d}
- Successful Hits: {hit_count}/{group_count}
- Failed Attacks: {miss_count}/{group_count}

**DETAILED RESULTS:**
{chr(10).join(f"- {o['npc'].sheet.name}: {o['success']:+d} vs {reactor_success:+d} = {'✓ HIT' if o['hit'] else '✗ MISS'}" for o in outcomes)}

**YOUR TASK:**
Write a cohesive 3-4 sentence narrative that:
1. **Opens with group coordination:** Show the NPCs working together as a coordinated unit
2. **Describes individual actions:** Weave in what each NPC does (flanking, distraction, direct attack, etc.)
3. **Shows reactor's response:** Describe how {reactor_name} defends against multiple attackers
4. **Delivers the outcome:** Clearly show which attacks hit and which were blocked

**PERSPECTIVE:**
- Use {"second person (you/your)" if reactor_is_ua else "third person"} for {reactor_name}
- Use third person for all NPCs

**TONE:**
- Dynamic and tactical
- Emphasize coordination and teamwork
- Show the challenge of defending against multiple attackers
- Make hits feel impactful, misses feel like close calls

**EXAMPLE (2 attackers, 1 hit, 1 miss):**
"The two bandits coordinate their assault with practiced efficiency. Bandit A circles left, drawing your attention with aggressive feints, while Bandit B rushes in from the right with a vicious swing. You manage to sidestep Bandit B's attack, but Bandit A's distraction works - his blade slips past your guard and cuts across your arm."

**CRITICAL:**
- DO NOT describe damage amounts or mechanical effects (no "-2 STAMINA")
- DO describe physical/emotional impacts (cuts, bruises, exhaustion, fear)
- Make the coordination feel natural and tactical
- Show cause and effect (one distracts, another strikes)

Respond with ONLY the narrative text.
"""
        
        try:
            narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
            if narrative:
                return narrative.strip()
        except Exception as e:
            print(f"{Color.WARNING}Error generating grouped narrative: {e}{Color.RESET}")
        
        # Fallback: Simple descriptive narrative
        if hit_count == group_count:
            result_desc = f"All {group_count} attacks find their mark"
        elif hit_count == 0:
            result_desc = f"{reactor_name_cap} {'manage' if reactor_is_ua else 'manages'} to block all {group_count} attacks"
        else:
            result_desc = f"{hit_count} of the {group_count} attacks {'hit' if hit_count > 1 else 'hits'} home"
        
        group_list = ', '.join(group_names[:-1]) + f" and {group_names[-1]}" if group_count > 1 else group_names[0]
        
        return f"{group_list} coordinate their assault against {reactor_name}. {result_desc} despite {'your' if reactor_is_ua else 'their'} desperate defense."

    def generate_step6_turn_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], outcome_data: Dict[str, Any], scene_context: str = None, is_remote_encounter: bool = False, remote_encounter_type: str = None, ua_actor=None, relationship_system=None) -> str:
        """
        Generates Step 6 narrative using LLM for context-aware outcomes, then appends N2N formula.
        
        Two-part structure:
        1. LLM generates contextual narrative (2-3 sentences) 
        2. System appends deterministic N2N formula with exact mechanical data
        
        This provides immersive storytelling + precise mechanical reporting.
        
        Args:
            scene_context: Current location/scene description (FIX BUG #9)
            is_remote_encounter: Whether this is a remote encounter (phone call, etc.)
            remote_encounter_type: Type of remote encounter ("phone_call", etc.)
            ua_actor: The user actor (for stranger description checks)
            relationship_system: Relationship tracker (for stranger description checks)
        """
        
        # Extract and prepare data
        proactor_name_raw = proactor_data.get('name', 'Unknown Actor')
        reactor_name_raw = reactor_data.get('name', 'Unknown Actor')
        proactor_is_ua = proactor_data.get('is_user_actor', False)
        reactor_is_ua = reactor_data.get('is_user_actor', False)
        
        # Get stranger-aware names (use descriptions for unknown NPCs)
        proactor_name = self.get_stranger_aware_name(proactor_data, ua_actor, relationship_system)
        reactor_name = self.get_stranger_aware_name(reactor_data, ua_actor, relationship_system)
        
        print(f"🔍 DEBUG Step6: proactor_name={proactor_name}, reactor_name={reactor_name}")
        print(f"🔍 DEBUG Step6: proactor_is_ua={proactor_is_ua}, reactor_is_ua={reactor_is_ua}")
        print(f"🔍 DEBUG Step6: proactor_data keys={list(proactor_data.keys())}")
        print(f"🔍 DEBUG Step6: reactor_data keys={list(reactor_data.keys())}")
        
        # Convert UA names for display (UA always uses "You/you")
        proactor_display = 'You' if proactor_is_ua else proactor_name
        reactor_display = 'you' if reactor_is_ua else reactor_name
        
        # Get full narrative descriptions from Steps 2 and 4
        proactor_narrative = proactor_data.get('narrative_description') or proactor_data.get('action_description', 'acts')
        reactor_narrative = reactor_data.get('narrative_description') or reactor_data.get('action_description', 'reacts')
        
        # Get successes
        pro_successes = int(outcome_data.get('proactor_successes', 0) or 0)
        re_successes = int(outcome_data.get('reactor_successes', 0) or 0)
        
        # Determine winner
        if pro_successes > re_successes:
            winner = "proactor"
        elif re_successes > pro_successes:
            winner = "reactor"
        else:
            winner = "tie"
        
        # Extract status shift from outcome (winner/loser result)
        status_shifts = outcome_data.get('status_shifts', [])
        shift_info = None
        
        if status_shifts:
            shift = status_shifts[0]
            shift_value = shift.get('shift_value') or shift.get('delta', 0)
            
            # Determine affected actor
            affected_original = shift.get('actor_name') or shift.get('actor')
            if affected_original == proactor_name:
                affected_display = proactor_display
            else:
                affected_display = reactor_display
            
            polarity_text = "Additive" if shift_value > 0 else "Subtractive"
            boost_or_penalty = "Boost" if shift_value > 0 else "Penalty"
            
            shift_info = {
                "affected": affected_display,
                "status": str(shift.get('status_type') or shift.get('status', 'STATUS')).upper(),
                "value": shift_value,
                "polarity": polarity_text,
                "original_desc": shift.get('original_descriptor', 'Average'),
                "new_desc": shift.get('new_descriptor', 'Average'),
                "magnitude": self._get_shift_magnitude_text(abs(shift_value)),
                "boost_or_penalty": boost_or_penalty
            }
        
        # Get concrete details for all actors (CRITICAL - MUST BE FIRST)
        concrete_context = ""
        if self.narrative_context_manager:
            try:
                # Get details for proactor
                proactor_details = self.narrative_context_manager.get_concrete_details_for_actor(
                    proactor_name,
                    scene_id="current"
                )
                if proactor_details:
                    concrete_context += f"\n{proactor_details}\n"
                
                # Get details for reactor
                reactor_details = self.narrative_context_manager.get_concrete_details_for_actor(
                    reactor_name,
                    scene_id="current"
                )
                if reactor_details:
                    concrete_context += f"\n{reactor_details}\n"
                
                if concrete_context:
                    concrete_context = f"{concrete_context}\n**CRITICAL:** Maintain consistency with all established concrete details above.\nDo not introduce contradictory details.\n\n"
            except Exception as e:
                # Log but don't break
                print(f"[WARNING] Could not get concrete details: {e}")
        
        # Get RAG worldbuilding context
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                        WorldbuildingCategory.SUPERNATURAL,
                    ]

                search_query = f"{proactor_narrative[:100]} {reactor_narrative[:100]}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=90,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING:**\n{rag_context}\n\n"
            except Exception as e:
                # Log RAG failure but continue - narrative can work without RAG
                print(f"[RAG] Exchange context query failed: {e}")
        
        # Build LLM prompt with outcome shift data
        shift_description = ""
        required_ending = ""
        if shift_info:
            shift_description = f"""
**STATUS SHIFT (Outcome) - YOU MUST USE THESE EXACT VALUES:**
- Affected Actor: {shift_info['affected']}
- Status: {shift_info['status']}
- Magnitude: {shift_info['magnitude']}
- Type: {shift_info['boost_or_penalty']}
- Original: {shift_info['original_desc']}
- New: {shift_info['new_desc']}

**MANDATORY ENDING (USE EXACTLY):**
Your narrative MUST end with: "{shift_info['affected']} experience{'s' if shift_info['affected'] not in ['You', 'you'] else ''} a {shift_info['magnitude']} {shift_info['boost_or_penalty'].upper()} to {'your' if shift_info['affected'] in ['You', 'you'] else 'their'} {shift_info['status']}."
"""
            required_ending = f"{shift_info['affected']} experience{'s' if shift_info['affected'] not in ['You', 'you'] else ''} a {shift_info['magnitude']} {shift_info['boost_or_penalty'].upper()} to {'your' if shift_info['affected'] in ['You', 'you'] else 'their'} {shift_info['status']}."
        
        # FIX BUG #9: Add current scene context to prevent location inconsistency
        scene_context_section = ""
        if scene_context:
            scene_context_section = f"""
**CURRENT SCENE CONTEXT:**
{scene_context}

**CRITICAL:** Use the CURRENT scene context above, not any previous location details.
If the actors moved to a new location, describe them in that NEW location.

"""
        
        # Add remote encounter context if applicable
        remote_context_section = ""
        if is_remote_encounter:
            if remote_encounter_type == "phone_call":
                remote_context_section = f"""
**CRITICAL: THIS IS A PHONE CALL**
The actors are NOT physically present with each other. They are in SEPARATE LOCATIONS.
- {proactor_display} and {reactor_display} are speaking over the phone
- Describe ONLY what can be perceived over the phone: voices, words, tone, background sounds
- FORBIDDEN: Any physical proximity descriptions ("approaches", "walks to", "gestures", "facial expressions")
- FORBIDDEN: Describing both actors in the same physical space
- Example CORRECT: "You hear concern in Marcus's voice over the phone"
- Example WRONG: "Marcus walks closer to you" ❌

"""
        
        prompt = f"""{concrete_context}{rag_context}{scene_context_section}{remote_context_section}Generate a complete narrative outcome for this UTAS exchange, including the mechanical shift.

**CRITICAL: PURE SENSORY PERSPECTIVE ONLY**
If "You" is involved, describe ONLY what the UA can perceive through their five senses:
- What YOU see, hear, feel, smell, taste
- NEVER what NPCs are thinking, feeling, or doing in other locations
- Example: NOT "she feels happy" but "you hear happiness in her voice"
- Example: NOT "the guard tries to punch you" but "you see the guard's fist coming at your face"

**WHAT HAPPENED:**
Proactor ({proactor_display}): {proactor_narrative}

Reactor ({reactor_display}): {reactor_narrative}

**MECHANICAL RESULT:**
- Proactor Successes: {pro_successes}
- Reactor Successes: {re_successes}
- Winner: {winner}
{shift_description}

**CRITICAL RULES:**
1. **LENGTH: 2-3 sentences MAXIMUM** - Brief outcome explanation, not a novel
2. **FORMAT: Single paragraph** - All sentences flow together as one continuous paragraph, no line breaks
3. **FOCUS ON THE STATUS SHIFT** - Your narrative must describe what happened to the AFFECTED ACTOR's STATUS:
   - If SPIRIT shifted: Describe emotional/mental impact (confidence, morale, composure)
   - If STAMINA shifted: Describe physical impact (pain, exhaustion, injury, energy)
   - If SUPPLY shifted: Describe material impact (gaining/losing resources, money, items)
   - DO NOT focus on "who won" - focus on HOW the status was affected
4. **PURE SENSORY PERSPECTIVE** - CRITICAL: If "You" is the UA, describe ONLY what YOU can perceive:
   - ✅ What you SEE: "You see her fist coming toward your face"
   - ✅ What you HEAR: "You hear excitement in her voice through the phone"
   - ✅ What you FEEL: "You feel the impact of his words"
   - ✅ What you SMELL/TASTE: "You smell cigarette smoke on her breath"
   - ❌ NEVER describe what NPCs are thinking, feeling, or doing when you can't see it
   - ❌ NEVER describe NPC internal states: "she feels happy" ❌
   - ❌ NEVER describe NPC actions in other locations: "she wakes up in her apartment" ❌
   - ✅ INSTEAD infer from what you perceive: "her voice sounds energized" ✅
5. **EXAMPLES OF CORRECT SENSORY DESCRIPTION:**
   - WRONG: "The guard attempts to punch you" ❌
   - RIGHT: "You see the guard's fist coming at your face, fast—maybe too fast" ✅
   - WRONG: "Lila feels excited about the mix" ❌
   - RIGHT: "You hear excitement in Lila's voice when she talks about the mix" ✅
   - WRONG: "She gets up from her chair to answer" ❌
   - RIGHT: "You hear her voice slightly strained, like she just stood up" ✅
6. **STRUCTURE:**
   - Sentence 1-2: Describe HOW the affected actor's STATUS was impacted (emotional/physical/material change)
   - Final sentence: END with N2N formula showing the exact status shift
7. **DIALOGUE CLARITY** - If NPCs speak, use clear attribution:
   - Use quotation marks for all spoken words
   - Immediately follow with speaker tag: "'Words,' Name says" or "Name says, 'Words'"
   - Never leave dialogue unattributed or ambiguous
6. **REALITY COHERENCE** - The narrative must make logical sense:
   - Actions must follow cause-and-effect
   - People can only interact if they're in the same place or connected (phone, etc.)
   - No impossible simultaneity (can't be in two places at once)
7. **Show cause and effect** - Make it clear why the winner succeeded based on what happened
8. If actor is "You/you", use second person throughout
9. Match the polarity:
   - Boost = positive, uplifting, supportive outcome
   - Penalty = negative, damaging, harmful outcome
10. **N2N FORMULA ENDING**: End with the status shift formula:
    - Format: ", [affected] experience/experiences a [MAGNITUDE] [BOOST/PENALTY] to [your/their] [STATUS]."
11. Use "you experience" and "your" if affected is "You/you"
12. Use "[name] experiences" and "their" if affected is an NPC name
13. Make the magnitude and boost/penalty UPPERCASE in the formula
14. **NO DIALOGUE REPETITION** - Do NOT repeat what was already said in Steps 2 and 4. Focus on internal state changes.
15. **NO META-COMMENTARY** - Do NOT have NPCs comment on mechanics, success, or "pulling it off". Stay in-actor and diegetic.

**EXAMPLES:**

Phone Call Example (CORRECT - brief, outcome-focused):
"You hear genuine excitement in Marcus's voice as he responds to your idea. His enthusiasm lifts your confidence, you experience a MINIMAL BOOST to your SPIRIT."

Phone Call Example (WRONG - describes NPC's location/actions):
❌ "You dial Lila's number while Lila wakes up in her apartment and sees the phone ringing. She picks up and you both start talking." (You can't see her apartment or her waking up!)

Combat Example (CORRECT - brief, outcome-focused):
"You see the guard's fist connect with your jaw, sharp and disorienting. The pain cuts through your focus, you experience a SUBPAR PENALTY to your STAMINA."

Combat Example (WRONG - describes NPC's intent):
❌ "The guard attempts to punch you and succeeds." (Describes his action, not what you perceive!)

Additive Boost (CORRECT - sensory focus):
"You ask Marnie about the diner's history. You see her face light up, and she leans against the counter. 'This place has been here since '62,' she says with pride in her voice. 'Seen a lot of folks come and go.' You hear the warmth in her words and see the genuine passion in her eyes, and it lifts your spirits, you experience an AVERAGE BOOST to your SPIRIT."

Subtractive Penalty (CORRECT - sensory focus):
"You try to charm your way past the security checkpoint. You see the guard's arms cross and watch him step forward, blocking your path completely. 'Move along,' he says coldly. 'Nothing to see here.' You feel the weight of his harsh dismissal and see the imposing presence cutting through your confidence, you experience a SUBPAR PENALTY to your SPIRIT."

Additive Boost (NPC affected - sensory focus):
"You see Marcus slumped against the wall, his shoulders sagging. You approach and put a hand on his shoulder. 'Hey, you gave it your best shot,' you say with genuine encouragement. 'That takes guts.' You watch his posture shift slightly, see something change in his expression as your words seem to reach him, Marcus experiences a MINIMAL BOOST to his SPIRIT."

Minimal exchange (sensory focus):
"You mention the weather casually. You see Linda give a polite nod. 'Yeah, nice day,' she says, but you notice her attention already drifting back to her work. The brief exchange is pleasant but unremarkable, you experience a NULL IMPACT to your SPIRIT."

Additive Boost (Extraordinary):
"The mentor's profound wisdom resonates deeply within you. Each word seems to unlock something fundamental in your understanding, you experience an EXTRAORDINARY BOOST to your SPIRIT."

Null Impact/Tie:
"Your exchange flows naturally, neither gaining nor losing ground. The interaction is pleasant but unremarkable, you experience a NULL IMPACT to your SPIRIT."

**VALID MAGNITUDE DESCRIPTORS (use these only):**
- NULL (0)
- MINIMAL (1)
- SUBPAR (2)
- AVERAGE (3)
- EXTRAORDINARY (4)
- SUPERB (5+)

Generate the complete narrative with N2N formula:"""

        # ═══════════════════════════════════════════════════════════════════
        # SWEEPING ACTION DETECTOR WITH REGENERATION FOR EXCHANGE NARRATIVES
        # Retry up to 2 times if LLM generates multi-action or location-change narratives
        # ═══════════════════════════════════════════════════════════════════
        sweeping_indicators = [
            # Location changes
            'exit', 'leave', 'depart', 'head to', 'head toward', 'walk to', 'walk toward',
            'make your way', 'find yourself', 'arrive at', 'reach the', 'enter the',
            'step outside', 'step into', 'step out of', 'go to', 'go toward',
            # Multiple sequential actions
            'then you', 'and then', 'before you', 'after you', 'next you',
            'you also', 'you then', 'finally you', 'first you',
            # Time skips
            'moments later', 'a few minutes', 'after a while', 'soon after',
            'eventually', 'by the time', 'when you finish'
        ]
        
        max_retries = 2
        llm_narrative = None
        
        for attempt in range(max_retries + 1):
            try:
                # Add stricter constraint on retry attempts
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + f"""

🚨 CRITICAL RETRY #{attempt} - PREVIOUS ATTEMPT VIOLATED EXCHANGE NARRATIVE RULES 🚨
Your previous response described MULTIPLE ACTIONS, LOCATION CHANGES, or TIME SKIPS.
This is STRICTLY FORBIDDEN in exchange narratives.

ABSOLUTE REQUIREMENTS:
- Describe ONLY the immediate outcome of THIS exchange
- NO location changes (no "exit", "leave", "enter", "arrive", "head to")
- NO sequential actions (no "then you", "and then", "after you")
- NO time skips (no "moments later", "eventually", "after a while")
- 2-3 sentences MAXIMUM about the exchange outcome
- End with the N2N formula showing the status shift
"""
                
                llm_narrative = self._call_llm(retry_prompt)
                
                if not llm_narrative:
                    print(f"⚠️ WARNING: LLM returned empty narrative for Step 6 (attempt {attempt + 1})")
                    if attempt == max_retries:
                        # Fallback with basic N2N if LLM fails
                        if shift_info:
                            magnitude = shift_info['magnitude'].upper()
                            boost_or_penalty = shift_info['boost_or_penalty'].upper()
                            status = shift_info['status']
                            affected = shift_info['affected']
                            affected_lower = "you" if affected in ['You', 'you'] else affected
                            verb = "experience" if affected_lower == "you" else "experiences"
                            possessive = "your" if affected_lower == "you" else "their"
                            llm_narrative = f"The exchange concludes, {affected_lower} {verb} a {magnitude} {boost_or_penalty} to {possessive} {status}."
                        else:
                            llm_narrative = "The exchange concludes with no status change."
                    continue
                
                # Check for sweeping indicators
                narrative_lower = llm_narrative.lower()
                is_sweeping = False
                detected_indicator = None
                for indicator in sweeping_indicators:
                    if indicator in narrative_lower:
                        is_sweeping = True
                        detected_indicator = indicator
                        break
                
                if is_sweeping and attempt < max_retries:
                    # Retry with stricter prompt
                    print(f"[NARRATOR] ⚠️ SWEEPING ACTION IN EXCHANGE (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[NARRATOR] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_sweeping:
                    # Final attempt still has issues - log but return anyway
                    print(f"[NARRATOR] ⚠️ SWEEPING ACTION PERSISTS IN EXCHANGE after {max_retries + 1} attempts: '{detected_indicator}'")
                
                # Success - break out of retry loop
                break
                
            except Exception as e:
                print(f"⚠️ ERROR: Step 6 narrative generation failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    # Fallback with basic N2N if LLM fails
                    if shift_info:
                        magnitude = shift_info['magnitude'].upper()
                        boost_or_penalty = shift_info['boost_or_penalty'].upper()
                        status = shift_info['status']
                        affected = shift_info['affected']
                        affected_lower = "you" if affected in ['You', 'you'] else affected
                        verb = "experience" if affected_lower == "you" else "experiences"
                        possessive = "your" if affected_lower == "you" else "their"
                        llm_narrative = f"The exchange concludes, {affected_lower} {verb} a {magnitude} {boost_or_penalty} to {possessive} {status}."
                    else:
                        llm_narrative = "The exchange concludes with no status change."
        
        # POST-PROCESSING: Ensure narrative ends with correct status shift
        if shift_info and required_ending and llm_narrative:
            # Check if the narrative contains the wrong status or actor
            narrative_lower = llm_narrative.lower()
            expected_status = shift_info['status'].lower()
            expected_affected = shift_info['affected'].lower()
            
            # If narrative mentions wrong status or wrong actor in the ending, fix it
            if expected_status not in narrative_lower or (expected_affected not in narrative_lower and expected_affected != 'you'):
                # Strip any existing N2N formula and append the correct one
                # Look for common N2N patterns to remove
                import re
                # Remove existing N2N formula patterns
                llm_narrative = re.sub(r',?\s*(you|[A-Z][a-z]+)\s+experiences?\s+a\s+\w+\s+(BOOST|PENALTY|boost|penalty)\s+to\s+(your|their)\s+\w+\.?$', '', llm_narrative, flags=re.IGNORECASE)
                llm_narrative = llm_narrative.strip()
                if not llm_narrative.endswith('.'):
                    llm_narrative += '.'
                llm_narrative = f"{llm_narrative} {required_ending}"
        
        # DIALOGUE IS NOW INTEGRATED INTO THE LLM NARRATIVE (Rule #4)
        # The LLM includes dialogue naturally within the narrative, so we don't need
        # to generate and append it separately. This prevents duplicate dialogue.
        # The old system would generate dialogue separately and insert it, causing
        # the same dialogue to appear twice (once in narrative, once appended).
        
        return llm_narrative.strip()
    
    def _get_shift_magnitude_text(self, abs_value: int) -> str:
        """Convert shift value to N2N magnitude descriptor."""
        if abs_value == 0:
            return "Null"
        elif abs_value == 1:
            return "Minimal"
        elif abs_value == 2:
            return "Subpar"
        elif abs_value == 3:
            return "Average"
        elif abs_value == 4:
            return "Extraordinary"
        elif abs_value >= 5:
            return "Superb"
        return "Minimal"  # Fallback to minimal instead of unknown

    def _validate_scene_setup(self, scene_setup: str) -> str:
        """
        Validate LLM scene setup output for length, quality, and appropriateness.
        
        Args:
            scene_setup: Raw LLM output for scene setup
        """
        if not scene_setup or not scene_setup.strip():
            return ""
        
        cleaned_setup = scene_setup.strip()
        
        if cleaned_setup.startswith('"') and cleaned_setup.endswith('"'):
            cleaned_setup = cleaned_setup[1:-1]
        
        sentences = cleaned_setup.split('. ')
        first_sentence = sentences[0].strip()
        
        if not first_sentence.endswith(('.',  '!', '?')):
            first_sentence += '.'
        
        word_count = len(first_sentence.split())
        if word_count > 20:
            return ""
        
        generic_phrases = ['the action begins', 'the battle starts', 'the confrontation commences']
        if any(phrase in first_sentence.lower() for phrase in generic_phrases):
            return ""
        
        return first_sentence

    def _integrate_narrative_components(self, scene_setup: str, core_outcome: str, self_effects_summary: str) -> str:
        """
        Integrate scene setup, UTAS formula outcome, and self-effects into a cohesive narrative.
        
        Returns a properly punctuated string. If self_effects_summary is provided, it is appended
        after the core outcome.
        """
        if scene_setup and not scene_setup.endswith(('.', '!', '?')):
            scene_setup += '.'
        if core_outcome and not core_outcome.endswith(('.', '!', '?')):
            core_outcome += '.'
        if self_effects_summary:
            integrated = f"{scene_setup} {core_outcome}{self_effects_summary}." if scene_setup else f"{core_outcome}{self_effects_summary}."
        else:
            integrated = f"{scene_setup} {core_outcome}".strip() if scene_setup else core_outcome
        return integrated

    def generate_framed_preface(self, scene_description: str, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a single-sentence, framed preface to color the deterministic outcome.

        Uses the narrative loop framing (mode, tone, intent, diegetic cues, etc.) to
        produce a brief, mood-setting line that does not alter mechanics.

        Args:
            scene_description: Current scene description/context.
            time_context: Optional time context for the LLM.
            framing_guidance: Optional framing dict from FourModeNarrativeLoop.process_turn().

        Returns:
            A validated single sentence (<= ~20 words) or empty string if invalid.
        """
        guidance_block = ""
        if isinstance(framing_guidance, dict):
            mode = framing_guidance.get('mode')
            tone = framing_guidance.get('tone')
            intent = framing_guidance.get('intent')
            scene_type = framing_guidance.get('scene_type')
            narrative_guidance = framing_guidance.get('narrative_guidance')
            diegetic_cues = framing_guidance.get('diegetic_cues')
            setting_context = framing_guidance.get('setting_context')
            guidance_block = f"""
            FOUR-MODE FRAMING:
            - Mode: {mode}
            - Tone: {tone}
            - Intent: {intent}
            - Scene Type: {scene_type}
            - Narrative Guidance: {narrative_guidance}
            - Diegetic Cues: {diegetic_cues}
            - Setting Context: {setting_context}
            """

        prompt = f"""
        You are narrating a UTAS simulation. Produce a single, mood-setting sentence to lead into a decisive outcome.

        Current Scene:
        {scene_description}

        {guidance_block}

        Requirements:
        - One sentence only (<= 20 words). Keep it tight and specific to the moment.
        - Use third-person and actor names if present in context; do not use second-person.
        - Do not mention rules, numbers, rolls, turns, or game mechanics.
        - Do not contradict established facts; do not invent new events or outcomes.
        - Avoid generic phrasing like "the battle starts" or "the action begins".
        - This is a preface; it must not restate success/failure—only set tone.

        Respond with ONLY the sentence.
        """

        try:
            raw = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
        except Exception:
            raw = None

        validated = self._validate_scene_setup(raw or "")
        return validated

    def integrate_preface_with_outcome(self, preface: str, outcome: str) -> str:
        """
        Safely concatenate a one-line preface with the deterministic Step 6 outcome.

        Ensures proper punctuation and avoids duplicating periods.
        If no preface provided, returns the outcome unchanged.
        """
        if not preface:
            return outcome

        preface_clean = preface.strip()
        if not preface_clean.endswith(('.', '!', '?')):
            preface_clean += '.'

        outcome_clean = (outcome or "").strip()
        if outcome_clean and not outcome_clean.endswith(('.', '!', '?')):
            outcome_clean += '.'

        if not outcome_clean:
            return preface_clean
        return f"{preface_clean} {outcome_clean}"

    # DEPRECATED: Old generate_inquiry_response method removed - using new version at line ~3609 with banned words and continuity rules

    def generate_continuity_failure_narrative(self, actor: 'Actor', attempted_action: str, reason: str, scene_description: str, framing_guidance: Optional[Dict[str, Any]] = None, time_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a DIEGETIC PERCEPTUAL description of the character attempting an impossible action and experiencing the failure.
        This should show the character TRYING and FAILING through sensory perception, not explain why it's impossible.
        
        Example: "I fly to the diner"
        - Good: "You prepare yourself. You feel the wind in your hair. You squeeze and strain but nothing. You open your eyes and you haven't moved an inch."
        - Bad: "You cannot fly because humans don't have that ability."
        """
        # If the denial is about a missing/non-existent item/entity, do NOT ask the LLM to improvise.
        # Improvisation here tends to invent substitute tools/props, which violates strict RAG grounding.
        # Return a short, purely perceptual narrative that does not introduce any new objects.
        try:
            import re

            reason_s = (reason or '').strip()
            if reason_s:
                # Extract the missing term if present.
                missing_term = None
                # Common: "...: lighter"
                m = re.search(r':\s*([^\n\r]+)\s*$', reason_s)
                if m:
                    missing_term = m.group(1).strip().strip('"\'`')
                # Common: "You cannot use dagger because ..."
                if not missing_term:
                    m = re.search(r"\bcannot\s+use\s+([^\n\r]+?)\s+because\b", reason_s, flags=re.IGNORECASE)
                    if m:
                        missing_term = m.group(1).strip().strip('"\'`')
                # Common: "You cannot do that with X right now ..."
                if not missing_term:
                    m = re.search(r"\bwith\s+([^\n\r]+?)\s+right\s+now\b", reason_s, flags=re.IGNORECASE)
                    if m:
                        missing_term = m.group(1).strip().strip('"\'`')
                # Common: "The action requires a lighter, which is not listed..."
                if not missing_term:
                    m = re.search(r"\brequires\s+(?:an?\s+)?([^\n\r,.;]+)", reason_s, flags=re.IGNORECASE)
                    if m:
                        missing_term = m.group(1).strip().strip('"\'`')

                # Common RAG-lock denial phrasings.
                is_missing = any(
                    k in reason_s.lower()
                    for k in (
                        'does not exist in this world',
                        'cannot use',
                        'not present',
                        'not owned',
                        'not available in the current scene',
                        'not present or owned',
                    )
                )

                if is_missing:
                    if missing_term:
                        # Keep it purely perceptual and generic; do not name any substitute items.
                        return (
                            f"You search your possessions for a {missing_term}, then hesitate. Your hands come up empty. "
                            f"You glance around, but there’s nothing here you can use for that."
                        ).strip()
                    return (
                        "You reach for what you need, then hesitate. Your hands come up empty. "
                        "You glance around, but there’s nothing here you can use for that."
                    ).strip()
        except Exception:
            pass

        # Get RAG worldbuilding context
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.SUPERNATURAL,
                        WorldbuildingCategory.BEINGS,
                    ]

                search_query = f"{attempted_action} {scene_description[:150]}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=70,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING (no magic, no superpowers):**\n{rag_context}\n\n"
            except Exception:
                pass
        
        actor_name = actor.sheet.name if hasattr(actor, 'sheet') else actor.name
        internal_personality = actor.sheet.personality_traits.get("internal", "Observant and thoughtful") if hasattr(actor, 'sheet') else "Observant and thoughtful"
        
        prompt = f"""Generate a DIEGETIC PERCEPTUAL description of {actor_name} attempting an impossible action and experiencing the failure.
{rag_context}
**CRITICAL RULES:**
1. **SHOW THE ATTEMPT** - Describe the character physically trying to do the action
2. **SHOW THE FAILURE** - Describe what they perceive when it doesn't work (sensory feedback)
3. **USE SECOND PERSON** - "You prepare yourself...", "You feel...", "You see..."
4. **PURELY PERCEPTUAL** - Only describe what can be seen, heard, felt (no explanations or reasoning)
5. **NO META-COMMENTARY** - Don't explain WHY it failed, just show WHAT happened when they tried
6. **STAY DIEGETIC** - The character doesn't know they're in a simulation or that physics prevents this

**Context:**
- **Scene:** {scene_description}
- **Character:** {actor_name}
- **Attempted Action:** "{attempted_action}"
- **Why It's Impossible:** {reason} (Use this to understand what fails, but DON'T state it directly)
- **Personality:** {internal_personality}

**EXAMPLES:**

**Attempted Action:** "I fly to the diner"
✓ GOOD: "You prepare yourself. You squeeze your eyes shut and strain every muscle. You feel the wind in your hair. You push harder, willing yourself upward. Nothing. You open your eyes. You haven't moved an inch. Your feet are still on the ground."
✗ BAD: "You cannot fly because humans don't have wings or the ability to defy gravity." ❌ (Explains instead of showing!)

**Attempted Action:** "I teleport home"
✓ GOOD: "You close your eyes and concentrate. You picture your home, trying to will yourself there. You feel nothing. You open your eyes. You're still in the same spot. The room hasn't changed."
✗ BAD: "Teleportation doesn't exist in this reality." ❌ (Meta-commentary!)

**Attempted Action:** "I read their mind"
✓ GOOD: "You stare at them intently, trying to sense their thoughts. You focus harder. Nothing comes. You see their face, their expression, but no thoughts enter your mind. Just silence."
✗ BAD: "You don't have telepathic abilities." ❌ (Explains instead of showing!)

**Attempted Action:** "I breathe underwater"
✓ GOOD: "You take a deep breath and duck your head under. You try to inhale. Water rushes into your nose and mouth. You choke, gasping. You jerk your head back up, coughing and sputtering."
✗ BAD: "You need equipment to breathe underwater." ❌ (Explains instead of showing!)

**FORMAT:**
- 2-4 sentences
- Second person perspective ("you")
- Present tense
- Sensory details (what they feel, see, hear)
- Show the attempt → Show the failure → Show the result

Respond with ONLY the perceptual narrative (no quotes, no preamble)."""
        
        narrative = self._call_llm(prompt, framing_guidance=framing_guidance, time_context=time_context)

        # Fallback to simple attempt description if the LLM call fails
        if not narrative:
            return f"You try to {attempted_action.lower()}. Nothing happens. You're still in the same place."
        
        return narrative.strip()

    def generate_recovery_scene(self, actor: 'Actor', original_scene: str, depleted_statuses: list, framing_guidance: Optional[Dict[str, Any]] = None, time_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generates a new scene description for when an actor regains consciousness after incapacitation.
        """
        # Get RAG worldbuilding context
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.CIVILIZATION,
                    ]

                search_query = f"{original_scene[:150]} recovery consciousness"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=70,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING:**\n{rag_context}\n\n"
            except Exception:
                pass
        
        prompt = f"""
        Generate a new scene description for when {actor.sheet.name} regains consciousness after being incapacitated.
   {rag_context}
        ORIGINAL SCENE: {original_scene}

        CONTEXT:
        - {actor.sheet.name} was knocked unconscious due to depleted {', '.join(depleted_statuses)}
        - They have now recovered enough to regain consciousness
        - The scene should show the passage of time and changed circumstances
        - Maintain continuity with the original setting but show progression

        REQUIREMENTS:
        - 3-4 sentences describing the new situation
        - Show how time has passed (lighting changes, position changes, etc.)
        - Maintain the same general location but with realistic changes
        - Create new opportunities for action and interaction
        - Use immersive, descriptive language

        EXAMPLE ELEMENTS TO CONSIDER:
        - Different lighting (sun position, shadows, etc.)
        - Changed positions of people/objects
        - New sounds, smells, or environmental details
        - Sense of disorientation from unconsciousness
        - Immediate concerns or threats that may have developed

        Generate only the scene description, no additional text:
        """
        
        response = self._call_llm(prompt, framing_guidance=framing_guidance, time_context=time_context)
        if response:
            return response.strip()
        else:
            status_text = "exhaustion" if "STAMINA" in depleted_statuses else "mental strain" if "SPIRIT" in depleted_statuses else "depletion"
            return f"After what feels like an eternity, {actor.sheet.name} slowly regains consciousness, the world swimming back into focus. The scene has shifted subtly - shadows have moved, sounds have changed, and there's a lingering sense that time has passed during the period of {status_text}. The immediate danger may have passed, but new challenges await in this evolved situation."

    def _get_n2n_level(self, value: int) -> str:
        """Convert numerical value to narrative descriptor for skills/traits/endowments."""
        if value == 0:
            return "Untrained"
        elif value == 1:
            return "Novice"
        elif value == 2:
            return "Competent"
        elif value == 3:
            return "Proficient"
        elif value == 4:
            return "Expert"
        elif value == 5:
            return "Master"
        else:
            return "Legendary"
    
    def _get_n2n_difficulty(self, stress_level: int) -> str:
        """DEPRECATED: Use N2N_Difficulty from narrative_utils for UTAS compliance."""
        return N2N_Difficulty(stress_level)
    
    def _get_n2n_shift_magnitude(self, abs_value: int) -> str:
        """DEPRECATED: Use N2N_Shift_Magnitude from narrative_utils for UTAS compliance."""
        return N2N_Shift_Magnitude(abs_value)
    
    def _get_status_modifier_impact(self, modifier_value: int) -> str:
        """DEPRECATED: Use N2N_Status_Modifier_Impact from narrative_utils for UTAS compliance."""
        return N2N_Status_Modifier_Impact(modifier_value)
    
    def _get_gerund(self, action_noun: str) -> str:
        """Convert action noun to gerund form (verb ending in -ing)."""
        if not action_noun:
            return "acting"
        
        action_lower = action_noun.lower().strip()
        
        gerund_map = {
            'attack': 'attacking',
            'punch': 'punching',
            'kick': 'kicking',
            'dodge': 'dodging',
            'block': 'blocking',
            'parry': 'parrying',
            'strike': 'striking',
            'slash': 'slashing',
            'stab': 'stabbing',
            'shoot': 'shooting',
            'throw': 'throwing',
            'grab': 'grabbing',
            'push': 'pushing',
            'pull': 'pulling',
            'run': 'running',
            'jump': 'jumping',
            'climb': 'climbing',
            'hide': 'hiding',
            'sneak': 'sneaking',
            'search': 'searching',
            'look': 'looking',
            'listen': 'listening'
        }
        
        if action_lower in gerund_map:
            return gerund_map[action_lower]
        
        if action_lower.endswith('e') and not action_lower.endswith('ee'):
            return action_lower[:-1] + 'ing'
        elif action_lower.endswith('ie'):
            return action_lower[:-2] + 'ying'
        elif len(action_lower) >= 3 and action_lower[-1] in 'bdfgklmnprtv' and action_lower[-2] in 'aeiou' and action_lower[-3] not in 'aeiou':
            return action_lower + action_lower[-1] + 'ing'
        else:
            return action_lower + 'ing'

    def generate_given_action_narrative(self, user_input: str, actor: Actor, scene_description: str, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a narrative description for a given action using LLM.
        
        Args:
            user_input: The raw user input for the action
            actor: The actor performing the action
            scene_description: Current scene context
            
        Returns:
            A narrative description of the action
        """
        # Check if this is the User Actor (UA)
        is_user_actor = getattr(actor, 'is_user_actor', False)
        
        if is_user_actor:
            # UA ALWAYS gets second person
            prompt = f"""You are a narrative writer for an immersive simulation. Generate a brief, immersive narrative description for a simple action.

**Your Action:** {user_input}
**Scene Context:** {scene_description}

**CRITICAL INSTRUCTIONS:**
- Write exactly ONE sentence describing the action in SECOND PERSON ("you")
- NEVER use the actor's name or third person
- Use "you/your" exclusively
- Make it natural and contextually appropriate
- For questions, show you asking the question
- For observations, show you looking/examining
- For movements, show you moving
- Keep it concise and immersive
- Provide ONLY ONE narrative option, no alternatives

**Example Outputs:**
- "You ask, 'Are there any seats available at the bar?'"
- "You carefully examine the ancient door for any signs of traps."
- "You walk confidently toward the town square."

Generate a single narrative sentence using "you":"""
        else:
            # NUAs get third person
            prompt = f"""You are a narrative writer for a tabletop RPG simulation. Generate a brief, immersive narrative description for a simple action.

**Actor:** {actor.sheet.name} ({actor.sheet.occupation})
**Action:** {user_input}
**Scene Context:** {scene_description}

**Instructions:**
- Write exactly ONE sentence describing the action in third person
- Use the actor's name, not "you" or pronouns
- Make it natural and contextually appropriate
- For questions, show the actor asking the question
- For observations, show the actor looking/examining
- For movements, show the actor moving
- Keep it concise and immersive
- Provide ONLY ONE narrative option, no alternatives

**Example Outputs:**
- "Veyra the Veiled asks, 'Are there any seats available at the bar?'"
- "Marcus carefully examines the ancient door for any signs of traps."
- "Elena walks confidently toward the town square."

Generate a single narrative sentence:"""

        try:
            narrative = self._call_llm(prompt, framing_guidance=framing_guidance, time_context=time_context)
            if narrative:
                # Clean up response and take only the first option if multiple are provided
                cleaned = narrative.strip()
                # Split on common separators that indicate multiple options
                if '(or)' in cleaned.lower():
                    cleaned = cleaned.split('(or)')[0].strip()
                elif '*or*' in cleaned.lower():
                    cleaned = cleaned.split('*or*')[0].strip()
                elif ' or ' in cleaned and cleaned.count(' or ') == 1:
                    cleaned = cleaned.split(' or ')[0].strip()
                elif '\n' in cleaned:
                    cleaned = cleaned.split('\n')[0].strip()
                return cleaned
            else:
                # Fallback if LLM fails
                return f"{actor.sheet.name} {user_input.lower()}."
        except Exception as e:
            print(f"{Color.SYSTEM}Warning: Given action narrative generation failed: {e}{Color.RESET}")
            return f"{actor.sheet.name} {user_input.lower()}."

    def _generate_tie_narrative(self, proactor_data: Dict[str, Any], reactor_data: Dict[str, Any], outcome_data: Dict[str, Any], time_context: Optional[Dict[str, Any]] = None) -> str:
        """Generate LLM-based narrative for tie scenarios where both actors fail equally."""
        
        proactor_name = proactor_data.get('name')
        reactor_name = reactor_data.get('name')
        proactor_narrative = proactor_data.get('narrative_description') or proactor_data.get('action_description', 'acts')
        reactor_narrative = reactor_data.get('narrative_description') or reactor_data.get('action_description', 'reacts')
        
        prompt = f"""
        You are narrating a UTAS simulation TIE OUTCOME where both actors fail equally in their exchange.
        
        **TIE SCENARIO: Mutual Failure**
        
        **GUIDELINES FOR TIE NARRATIVES:**
        - Both the proactor and reactor fail to achieve their goals
        - Show competing efforts that cancel each other out
        - Use phrases like "both struggle...", "neither succeeds...", "efforts are thwarted..."
        - Emphasize stalemate, deadlock, or mutual interference
        - No clear victor - both face setbacks or complications
        - 2-3 sentences showing balanced failure that explains why no status shift occurred
        - Make it clear that both actions failed due to mutual interference
        
        **ACTORS:**
        **PROACTOR:** {proactor_name}
        **PROACTOR ACTION:** {proactor_narrative}
        **REACTOR:** {reactor_name}  
        **REACTOR REACTION:** {reactor_narrative}
        
        **EXAMPLE TIE NARRATIVES:**
        - "Mike attempts to slide the ledger away just as Sarah lunges for her gun, but both movements interfere with each other - the ledger slips from Mike's grasp while Sarah's weapon catches in her jacket, leaving both empty-handed and frustrated."
        - "David swings his crowbar while Lisa tries to dodge, but their timing creates chaos - David's weapon catches on Lisa's coat just as she stumbles over debris, causing both to fall in a tangle of limbs with neither achieving their goal."
        - "The businessman reaches for his briefcase as the mugger grabs for it simultaneously, but their competing grips cause the papers to scatter across the ground, leaving both scrambling unsuccessfully in the alley."
        
        Generate a narrative showing both {proactor_name} and {reactor_name} failing equally with no clear advantage to either, explaining why no status shift occurred.
        """
        
        response = self._call_llm(prompt, time_context=time_context)
        
        if not response:
            return f"{proactor_name} and {reactor_name} struggle against each other, but their competing efforts cancel out, leaving both frustrated and achieving nothing."
        
        return response.strip()
    
    def generate_scene_transition_narrative(self, proactor: Actor, reactor: Optional[Actor], 
                                          evaluation: Dict[str, Any], scene_context: str, framing_guidance: Optional[Dict[str, Any]] = None, time_context: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate narrative for scene transitions (escapes, location changes, etc.)
        
        Args:
            proactor: The user's actor
            reactor: Current opponent/NPC (if any)
            evaluation: Scene evaluation results
            scene_context: Current scene description
            
        Returns:
            Narrative describing the scene transition
        """
        transition_type = evaluation.get('suggested_transition', 'new_location')
        completion_reason = evaluation.get('completion_reason', 'natural_conclusion')
        transition_description = evaluation.get('transition_description', 'A new scene begins')
        
        reactor_name = reactor.sheet.name if reactor else "no one else"
        
        # Get RAG worldbuilding context
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.CIVILIZATION,
                    ]

                search_query = f"{scene_context[:150]} {transition_description}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=70,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING:**\n{rag_context}\n\n"
            except Exception:
                pass
        
        prompt = f"""
        You are narrating a SCENE TRANSITION in a UTAS simulation.
{rag_context}
        
        **TRANSITION CONTEXT:**
        - Reason: {completion_reason}
        - Type: {transition_type}
        - Suggested Direction: {transition_description}
        
        **CURRENT SCENE:**
        {scene_context}
        
        **ACTORS:**
        - **PROACTOR:** {proactor.sheet.name}
        - **REACTOR:** {reactor_name}
        
        **GUIDELINES FOR SCENE TRANSITIONS:**
        - Generate exactly ONE cohesive transition narrative (2-3 sentences)
        - Show natural progression from current scene to new situation
        - If escape/departure: describe how the actor leaves and where they go
        - If location change: describe the new environment they enter
        - If time progression: show passage of time and new circumstances
        - Maintain narrative continuity and logical flow
        - Use vivid, immersive descriptions that set up the new scene
        - DO NOT provide multiple options or alternatives
        
        **EXAMPLE TRANSITIONS:**
        - Escape: "You slip through the back door into the narrow alley behind the tavern. The cool night air hits your face as you emerge onto the cobblestone street, leaving the chaos behind."
        - New Location: "The conversation reaches its natural end, and you find yourself walking toward the market district. The bustling sounds of merchants and customers fill the air as you enter the crowded square."
        - Time Skip: "Hours pass as you wait in the shadows. Dawn breaks over the city, painting the rooftops in golden light as a new day begins with fresh possibilities."
        
        Generate a single, definitive scene transition narrative that smoothly moves from the current situation to the new scene context.
        """
        
        response = self._call_llm(prompt, framing_guidance=framing_guidance, time_context=time_context)
        
        if not response:
            return f"The scene shifts as {proactor.sheet.name} moves to a new situation, leaving the previous circumstances behind."
        
        return response.strip()
    
    def process_turn_with_narrative_loop(self, turn_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a turn through the Four-Mode Narrative Loop and return framing guidance."""
        return self.narrative_loop.process_turn(turn_data)
    
    def get_narrative_loop_state(self) -> Dict[str, Any]:
        """Get current narrative loop state for debugging or integration."""
        return self.narrative_loop.get_current_state()
    
    def generate_scene_with_narrative_loop(self, scene_elements: dict, nua_name: str, 
                                         turn_data: Optional[Dict[str, Any]] = None,
                                         time_context: Optional[Dict[str, Any]] = None,
                                         narrative_context: Optional[str] = None) -> str:
        """
        Generate scene introduction with Four-Mode Narrative Loop guidance for invisible scaffolding.
        
        Args:
            narrative_context: Full narrative history for initial scenes (optional)
        """
        # Process turn through narrative loop if turn data is available
        framing_guidance = None
        if turn_data:
            framing_guidance = self.narrative_loop.process_turn(turn_data)
        
        setting = scene_elements.get('setting', 'an unknown location')
        ua_goal = scene_elements.get('ua_goal', 'an unknown goal')
        conflict = scene_elements.get('conflict', 'an unknown conflict')
        transition_bridge = scene_elements.get('transition_bridge', '')
        
        # Add narrative context if provided (for initial scenes with history)
        context_section = ""
        if narrative_context:
            context_section = f"\n**NARRATIVE HISTORY:**\n{narrative_context}\n"
        
        # Build mode-aware prompt
        prompt = f"""⚠️ CRITICAL INSTRUCTION - READ FIRST ⚠️
BANNED WORDS YOU MUST NEVER USE: "vintage", "old", "retro", "classic", "outdated", "dated", "old-school", "modern", "futuristic"
DO NOT USE THESE WORDS UNDER ANY CIRCUMSTANCES. These words imply you are from a different time period than the setting. Your response will be rejected if you use them.

**CONTINUITY & DESTINATION (CRITICAL):**
- If the transition implies travel to a SPECIFIC LOCATION (e.g. "Walking to Warehouse 7B"), respect that destination's existence.
- **DO NOT** invent a "twist" that the location doesn't exist or is missing unless explicitly instructed by the Conflict.
- **JOURNEY VS ARRIVAL:** 
  - If the context implies a short trip or arrival, describe the **ARRIVAL** at the destination.
  - If the context implies a long journey or travel segment, describe the **JOURNEY** toward the destination (the sights/sounds along the way).
  - In both cases, treat the destination as REAL and REACHABLE.

You are a perception describer creating an immersive scene introduction with invisible narrative scaffolding.
Your task is to write a compelling introduction that feels natural and rule-free while following universal story beats.

**IMMERSIVE TIME PERSPECTIVE (MANDATORY):**
- You exist IN this time period - it is YOUR present day, not the past
- All technology is CURRENT and NORMAL (turntable = normal, cassettes = normal, answering machine = normal)
- NEVER describe things as if looking back from the future
- Write as if you are living in this moment RIGHT NOW
- Replace: "vintage lamp" → "lamp", "old cassette" → "cassette", "vintage TV" → "TV"
{self.SENSORY_PERCEPTION_REQUIREMENTS}
{context_section}
        **Scene Elements:**
        - **Setting:** {setting}
        - **Your Goal:** {ua_goal}
        - **The Conflict:** {conflict}
        - **The Opponent:** {nua_name}
        - **Transition Bridge:** {transition_bridge}
        {'- **Notable Details to Notice (weave naturally, do NOT list):** ' + ', '.join(opportunities) if opportunities else ''}

        **Your Task:**
        Create a narrative that flows smoothly from previous events using ONLY diegetic elements. Frame the scene at a point of uncertainty with environmental details, actor opportunities, or dialogue. Make it feel like natural story progression without exposing any mechanics.
        If any "Notable Details to Notice" are provided, integrate them subtly into the prose as sensory cues or objects in the environment. Do NOT enumerate them as a list; they should appear naturally within 1-3 sentences.

        **Enhanced Example with Natural Framing:**
        - **Transition Bridge:** "After successfully negotiating with the merchant, you pocket the ancient map and step back onto the bustling street."
        - **Setting:** A narrow alley in the merchant district.
        - **Your Goal:** Reach the cathedral district safely with the map.
        - **The Conflict:** A hooded figure is following you, interested in what you carry.
        - **The Opponent:** Mysterious Stalker

        **Good Narrative with Invisible Scaffolding:**
        "After successfully negotiating with the merchant, you pocket the ancient map and step back onto the bustling street. The information you've gained points toward the old cathedral district, but as you make your way through the crowd, you notice a hooded figure has been following you since you left the shop. They seem particularly interested in the scroll case you're carrying. When you turn down a quieter alley to test your suspicions, they follow. The narrow passage offers little room for escape, and you sense a moment of decision approaching."

        Now, produce the narrative for the given context. Use environmental details and actor behavior to create natural story momentum. Respond with ONLY the narrative text.
        """
        
        narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)

        if not narrative:
            # Fallback to a simple description if LLM fails
            return f"SCENE: You are in {setting}, trying to {ua_goal}. You are opposed by {nua_name} due to: {conflict}"
        
        # Clean up the narrative by removing extra whitespace and normalizing line breaks
        cleaned_narrative = ' '.join(narrative.strip().split())
        cleaned_narrative = self._strip_meta_time_references(cleaned_narrative)
        cleaned_narrative = self._sanitize_narrative(cleaned_narrative)
        return f"SCENE: {cleaned_narrative}"
    
    def _enhance_prompt_with_narrative_context(self, prompt: str) -> str:
        """Enhance prompt with narrative context from the enhanced narrative context system, INCLUDING MEMORIES."""
        if not self.narrative_context_manager:
            return prompt
        
        try:
            # Get intelligent context for LLM prompts INCLUDING MEMORIES
            narrative_context = self.narrative_context_manager.get_context_for_llm(
                lookback_events=5,
                importance_threshold="notable",
                key_memories_system=self.key_memories_system  # CRITICAL: Include memories!
            )
            
            if narrative_context:
                enhanced_prompt = f"""
{prompt}

**NARRATIVE CONTEXT & STORY CONTINUITY (INCLUDING ESTABLISHED FACTS FROM MEMORY):**
{narrative_context}

**CRITICAL RULES FOR USING THIS CONTEXT:**
1. **RESPECT ESTABLISHED FACTS:** If memories say "subway is 10-minute walk", DO NOT say "3 minutes"
2. **MAINTAIN SPATIAL CONTINUITY:** If current location is "apartment", DO NOT start at "subway platform"
3. **USE KNOWN INFORMATION:** Reference memories when relevant to the action
4. **STAY CONSISTENT:** Never contradict established facts from memories
5. **BUILD ON HISTORY:** Use narrative events to show progression and continuity

Use this context to maintain story continuity, reference previous events appropriately, ensure actor consistency, and MOST IMPORTANTLY: respect all established facts from memory.
"""
                return enhanced_prompt
        except Exception as e:
            # Silently continue if narrative context fails
            pass
        
        return prompt
    
    def _enhance_prompt_with_rag(self, prompt: str) -> str:
        """Enhance prompt with RAG worldbuilding context for all narrative generation."""
        if not self.rag_system:
            if not SUPPRESS_DEBUG:
                print(f"{Color.WARNING}[RAG] No RAG system available{Color.RESET}")
            return prompt
        
        try:
            context_parts = []
            
            # CRITICAL: Always get TEMPORAL context first - this defines the era
            temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
            temporal_ctx = self.rag_system.get_context_for_llm(
                query="time period era setting year world",
                max_tokens=200,
                category_filter=temporal_category
            )
            if temporal_ctx:
                context_parts.append(f"**TIME PERIOD & ERA (CRITICAL):**\n{temporal_ctx}")
            
            # Extract key terms from the prompt for general RAG query
            prompt_excerpt = prompt[:300] if len(prompt) > 300 else prompt
            
            # Get general worldbuilding context from RAG
            categories = []
            if WorldbuildingCategory:
                categories = [
                    WorldbuildingCategory.CIVILIZATION,
                    WorldbuildingCategory.CULTURE,
                    WorldbuildingCategory.PLACES,
                    WorldbuildingCategory.CITIES,
                    WorldbuildingCategory.MECHANICS,
                    WorldbuildingCategory.SUPERNATURAL,
                    WorldbuildingCategory.NARRATION_STYLE_TONE,
                ]
            general_context = get_multi_category_context_for_llm(
                self.rag_system,
                query=prompt_excerpt,
                categories=categories,
                max_tokens_per_category=70,
                include_related=True,
            )
            if general_context:
                context_parts.append(general_context)
            
            if context_parts:
                rag_context = "\n\n".join(context_parts)
                if not SUPPRESS_DEBUG:
                    print(f"{Color.SUCCESS}[RAG] Retrieved {len(rag_context)} chars of worldbuilding context{Color.RESET}")
                enhanced_prompt = f"""
{prompt}

**ESTABLISHED WORLDBUILDING & SETTING CONTEXT:**
{rag_context}

**CRITICAL RULES FOR USING WORLDBUILDING CONTEXT:**
1. **RESPECT THE TIME PERIOD:** All details MUST match the established era - no anachronisms
2. **PERIOD-APPROPRIATE DETAILS:** Technology, culture, language, and objects must fit the time period
3. **MAINTAIN WORLD CONSISTENCY:** Never contradict established worldbuilding facts
4. **NATURAL INTEGRATION:** Weave worldbuilding details naturally into the narrative, don't force them
5. **IMMERSIVE PERSPECTIVE:** Describe the world as if you're living in it NOW, not looking back from the future

Use this worldbuilding context to create immersive, period-appropriate narratives that respect the established setting.
"""
                return enhanced_prompt
            else:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[RAG] No relevant worldbuilding found for query{Color.RESET}")
        except Exception as e:
            if not SUPPRESS_DEBUG:
                print(f"{Color.ERROR}[RAG] Error retrieving context: {e}{Color.RESET}")
        
        return prompt
    
    def _get_mode_focus_description(self, mode: str) -> str:
        """Get description of what the current mode focuses on."""
        mode_focus = {
            'roam': 'open exploration and organic discovery',
            'spark': 'emerging opportunities and gentle direction',
            'pressure': 'heightened stakes and meaningful obstacles',
            'outcome': 'natural resolution and reflective closure'
        }
        return mode_focus.get(mode, 'natural story flow')

    def generate_given_action_narrative_with_loop(self, user_input: str, actor: UserActor, scene_description: str, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None) -> str:
        """Generate given action narrative with Four Mode Narrative Loop guidance."""
        return self.generate_given_action_narrative(user_input, actor, scene_description, time_context, framing_guidance)

    def generate_given_action_narrative(self, user_input: str, actor: UserActor, scene_description: str, time_context: Optional[Dict[str, Any]] = None, framing_guidance: Optional[Dict[str, Any]] = None, movement_data: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate rich, consequence-driven narrative for given actions that creates branching opportunities.
        
        Args:
            user_action: The action the user is taking
            actor: The actor performing the action
            scene_description: Current scene context
            time_context: Time and atmospheric information
            movement_data: Optional movement detection data to constrain movement descriptions
            
        Returns:
            Rich narrative that shows consequences and opens new opportunities
        """
        # Get time period context from RAG
        time_period_context = ""
        if self.rag_system:
            try:
                temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                time_period_context = self.rag_system.get_context_for_llm(
                    query="time period year era current setting",
                    max_tokens=200,
                    category_filter=temporal_category
                )
                if time_period_context:
                    time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
            except Exception:
                pass
        
        prompt = f"""
You are a perception describer creating rich, immersive narrative for an actor's action.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**

{self.SENSORY_PERCEPTION_REQUIREMENTS}

**CRITICAL REQUIREMENTS:**
- Create CONSEQUENCES and RESULTS from the action, not just describe the action itself
- Show what HAPPENS BECAUSE of the action - new discoveries, reactions, opportunities, complications
- Generate NEW STORY ELEMENTS that create branching paths for future actions
- Include sensory details, environmental reactions, and actor observations
- Make the world feel alive and reactive to the actor's choices
- Create hooks for future exploration and interaction
- DO NOT include explicit "Consequences & Opportunities" or "Hooks for Future Exploration" sections
- Weave all consequences, opportunities, and hooks naturally into the narrative prose

**Actor:** {actor.sheet.name}
**Action:** {user_input}
**Current Scene:** {scene_description}
**Time:** {time_context.get('current_time', 'Unknown time')}
**Atmosphere:** {time_context.get('atmospheric_description', 'Standard conditions')}
**Lighting:** {time_context.get('lighting_condition', 'Normal lighting')}

**CRITICAL SCENE CONSISTENCY:** The "Current Scene" above is authoritative for location, time, and atmosphere. If any prior context conflicts with it, you MUST ignore the conflicting details and adhere to the Current Scene.

**CRITICAL MOVEMENT CONSTRAINT:**
Explicit movement detected in user input: {movement_data.get('has_explicit_movement', False) if movement_data else False}
{f"Movement type: {movement_data.get('movement_type')}, Target: {movement_data.get('target')}" if movement_data and movement_data.get('has_explicit_movement') else ""}
- If FALSE: DO NOT describe the user physically moving to new locations or changing position
- If TRUE: You may describe movement to the specified target
- The narrator describes what the user PERCEIVES, not what the user DOES (unless movement was explicit)
- Example: "I look around" → Describe what they SEE, NOT that they walked somewhere
- Example: "I walk to the door" → You may describe them moving to the door

**Example of GOOD narrative (shows consequences and opportunities):**
Action: "I follow the girl into the main club area"
Response: "You push through the heavy doors and the bass hits your chest like a fist. The girl has already vanished into the crowd, but her path leads toward a raised VIP section where two men in expensive suits are deep in argument."

**Example of BAD narrative (just describes action, or overwhelms with senses):**
"You follow the girl into the club area. The exploration continues..."

Generate a 2-3 sentence narrative that shows what HAPPENS as a result of the action and creates new opportunities for exploration:
"""

        try:
            # Use the enhanced _call_llm method that handles framing guidance
            narrative = self._call_llm(prompt, time_context=time_context, framing_guidance=framing_guidance)
            
            if narrative and not narrative.lower().startswith(user_input.lower()[:10]):
                return narrative.strip()
            
            # If _call_llm fails, fall back to robust LLM call
            narrative = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.9,
                max_tokens=300,
                max_retries=RetryConfig.MAX_RETRIES,
                call_name="EXPLORATION NARRATIVE"
            )
            
            # Ensure the narrative doesn't just repeat the action
            if narrative and not narrative.lower().startswith(user_input.lower()[:10]):
                return narrative
            else:
                # Fallback with basic consequence structure
                return f"As {actor.sheet.name} {user_input.lower()}, the environment shifts around them. New details catch their attention, and the action sets something in motion—subtle changes present fresh opportunities to explore."
                
        except Exception as e:
            print(f"DEBUG: Error generating contextual exploration action result narrative: {e}")
            # Enhanced fallback that still creates opportunities
            return f"{actor.sheet.name}'s action of {user_input.lower()} creates subtle ripples in the scene. The atmosphere shifts, revealing small details that hint at new paths forward."

    def generate_contextual_exploration_action_result_narrative(
        self,
        user_input: str,
        actor: UserActor,
        scene_description: str,
        success_total: int,
        time_context: Optional[Dict[str, Any]] = None,
        framing_guidance: Optional[Dict[str, Any]] = None,
        movement_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Generate a contextual narrative for an exploration action outcome.
        
        Uses a 66/34 dice roll to decide between:
        - 66% chance: DESCRIPTIVE narration (just describes what happened)
        - 34% chance: OPPORTUNITY narration (includes exploration hooks)

        Requirements:
        - SECOND PERSON for UA ("you"), third person for NUA
        - 2–3 sentences, concise and immersive
        - First sentence MUST explicitly reference the user's action (paraphrased; do not copy verbatim)
        - Reflect the scene context and recent continuity (uses _call_llm enhancements)
        - Adapt tone/content based on success_total (negative = backfire, zero = fail)
        - Period-appropriate ambiance when applicable
        """

        # Roll dice: 66% descriptive, 34% opportunities
        include_opportunities = random.random() < 0.34
        
        # Check if this is the User Actor
        is_user_actor = getattr(actor, 'is_user_actor', False)

        # Derive a human-friendly success descriptor
        try:
            success_label = get_success_level_narration(success_total)
        except Exception:
            # Safe fallback
            success_label = "Average" if success_total > 0 else ("Failed" if success_total == 0 else "Backfire")

        outcome_flavor = ""
        if success_total < 0:
            outcome_flavor = "Backfire"
        elif success_total == 0:
            outcome_flavor = "Failed"
        else:
            outcome_flavor = "Succeeded"

        # Get concrete details for UA (CRITICAL - MUST BE FIRST)
        concrete_context = ""
        if self.narrative_context_manager:
            try:
                actor_details = self.narrative_context_manager.get_concrete_details_for_actor(
                    actor.sheet.name,
                    scene_id="current"
                )
                if actor_details:
                    concrete_context = f"{actor_details}\n\n**CRITICAL:** Maintain consistency with all established concrete details above.\nDo not introduce contradictory details.\n\n"
            except Exception as e:
                print(f"[WARNING] Could not get concrete details: {e}")
        
        if is_user_actor:
            # UA gets second person
            if include_opportunities:
                # 34% chance: Include exploration opportunities
                # Get time period context from RAG
                time_period_context = ""
                if self.rag_system:
                    try:
                        temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                        time_period_context = self.rag_system.get_context_for_llm(
                            query="time period year era current setting",
                            max_tokens=200,
                            category_filter=temporal_category
                        )
                        if time_period_context:
                            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
                    except Exception:
                        pass
                
                prompt = f"""{concrete_context}You are a perception describer crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**

{self.INTERIOR_EXTERIOR_RULE}

Write a concise, immersive paragraph in SECOND PERSON using "you".
- Length: 2–3 sentences, about 40–60 words total.
- The FIRST sentence must explicitly reference the user's action using a clear verb (PARAPHRASE the wording; do not copy verbatim).
- Focus ONLY on what happens as a direct result of this specific action.
- Do NOT re-describe the scene or repeat environmental details already established.
- INCLUDE subtle exploration opportunities or hooks (things to notice, investigate, or interact with next).

— Actor: {actor.sheet.name} ({actor.sheet.occupation})
— Action: {user_input}
— Scene Context (for consistency only, DO NOT repeat): {scene_description}
— Outcome: {outcome_flavor} ({success_label}, total={success_total})

**CRITICAL CONSTRAINTS (FIX BUG #8 - STRICT ENFORCEMENT):**
- Describe ONLY the EXACT action the user specified - ABSOLUTELY NO extra actions before or after
- If user says "I pick up notebook" → describe ONLY picking it up, NOT opening it, NOT reading it
- If user says "I step out of van" → describe ONLY stepping out, NOT opening door first, NOT walking away after
- If user says "I step through doorway" → describe ONLY stepping through, NOT opening door, NOT descending stairs
- If user says "I open door" → describe ONLY opening, NOT stepping through, NOT entering
- STOP immediately after describing the single specified action
- Do NOT add preparatory actions (opening, reaching, approaching)
- Do NOT add follow-up actions (examining, reading, walking)
- ONE ACTION ONLY - nothing before, nothing after

Guidelines:
- Use only diegetic elements; no system language or mechanics.
- If Succeeded: show tangible progress, discoveries, AND hint at new opportunities to explore.
- If Failed: show effort with no gain, but reveal something interesting to investigate.
- If Backfire: show a complication that creates new pathways or choices.
- Weave opportunities naturally into the narrative (e.g., "you notice...", "nearby...", "you hear...").
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
- Do NOT copy the action text verbatim; paraphrase but make the action explicit in sentence one.
- Do NOT re-describe the location, time of day, or general atmosphere—those are already established.

**NARRATIVE STRUCTURE (Opportunity - WITH HOOKS):**
- Establish what happens FIRST (immediate result of action)
- Stay in ONE PLACE - describe only what's observable from where the action occurred
- Include HOOKS - mysteries, things to investigate, opportunities (this is the 34% branch)
- Focus on PRIMARY element (one main discovery/outcome)
- Add 1-2 supporting details/hooks in the SAME immediate area
- Limit to 2-3 hooks maximum—avoid scattering focus across 4+ elements
- Maximum 2-3 sentences about the IMMEDIATE result
- NO spatial jumps - don't describe something here, then jump to "across the street" or "in the distance"
- NO other locations - NEVER mention other places unless it's a thought passing through UA's mind

**ABSOLUTELY FORBIDDEN - SPATIAL VIOLATIONS:**
- NEVER mention "behind the [building]" - you cannot see behind buildings
- NEVER mention "across the street" - that's a different location
- NEVER mention "the [place]'s [thing]" if the place is not where you are (e.g., "the diner's door" when you're in an alley)
- NEVER describe multiple locations in one narrative (alley + dumpster + diner = 3 locations!)
- If you're in an alley, describe ONLY the alley. Period.

**ABSOLUTELY FORBIDDEN - NEVER INCLUDE:**
- Meta-commentary like "(Opportunities: ...)"
- Parenthetical explanations of what the player could do
- Lists of options or suggestions
- Any text in parentheses explaining the narrative
- System-facing notes or annotations

Hooks must be WOVEN INTO the narrative naturally, not listed separately.
 
CRITICAL: Write ONLY about what happens from this action. Do NOT repeat scene descriptions.
Respond with ONLY the narrative - NO meta-commentary, NO parenthetical notes.
"""
            else:
                # 66% chance: Pure descriptive narration (NO OPPORTUNITIES)
                # Get time period context from RAG
                time_period_context = ""
                if self.rag_system:
                    try:
                        temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                        time_period_context = self.rag_system.get_context_for_llm(
                            query="time period year era current setting",
                            max_tokens=200,
                            category_filter=temporal_category
                        )
                        if time_period_context:
                            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
                    except Exception:
                        pass
                
                prompt = f"""
You are a perception describer crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**

{self.INTERIOR_EXTERIOR_RULE}

{self.SENSORY_PERCEPTION_REQUIREMENTS}

Write a concise, immersive paragraph in SECOND PERSON using "you".
- Length: 2–3 sentences, about 40–60 words total.
- The FIRST sentence must explicitly reference the user's action using a clear verb (PARAPHRASE the wording; do not copy verbatim).
- Focus ONLY on what happens as a direct result of this specific action.
- Do NOT re-describe the scene or repeat environmental details already established.

**CRITICAL: This is DESCRIPTIVE narration ONLY. ABSOLUTELY NO opportunities, hooks, or suggestions for future actions.**

— Actor: {actor.sheet.name} ({actor.sheet.occupation})
— Action: {user_input}
— Scene Context (for consistency only, DO NOT repeat): {scene_description}
— Outcome: {outcome_flavor} ({success_label}, total={success_total})

**CRITICAL CONSTRAINTS (FIX BUG #8 - STRICT ENFORCEMENT):**
- Describe ONLY the EXACT action the user specified - ABSOLUTELY NO extra actions before or after
- If user says "I pick up notebook" → describe ONLY picking it up, NOT opening it, NOT reading it
- If user says "I step out of van" → describe ONLY stepping out, NOT opening door first, NOT walking away after
- If user says "I step through doorway" → describe ONLY stepping through, NOT opening door, NOT descending stairs
- If user says "I open door" → describe ONLY opening, NOT stepping through, NOT entering
- STOP immediately after describing the single specified action
- Do NOT add preparatory actions (opening, reaching, approaching)
- Do NOT add follow-up actions (examining, reading, walking)
- ONE ACTION ONLY - nothing before, nothing after

Guidelines:
- Use only diegetic elements; no system language or mechanics.
- If Succeeded: show tangible progress and what you accomplished. PERIOD. Nothing more.
- If Failed: show effort with no gain, a near-miss, or a clear limitation revealed. PERIOD. Nothing more.
- If Backfire: show a complication or small setback that logically emerges from the action. PERIOD. Nothing more.
- Describe ONLY the action's results and effects on the environment/people/yourself.
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
- Do NOT copy the action text verbatim; paraphrase but make the action explicit in sentence one.
- Do NOT re-describe the location, time of day, or general atmosphere—those are already established.

**ABSOLUTELY FORBIDDEN WORDS/PHRASES:**
- "you notice", "you spot", "you see", "you hear", "you could", "you might"
- "nearby", "in the distance", "across the way", "just beyond"
- "catches your eye", "draws your attention", "reveals", "hints at"
- "opportunity", "option", "path", "way forward", "next step"
- Any suggestion of what to do next or what to investigate
- Any mention of other locations (unless it's a thought: "you remember the diner")

**ABSOLUTELY FORBIDDEN - SPATIAL VIOLATIONS:**
- NEVER mention "behind the [building]" - you cannot see behind buildings
- NEVER mention "across the street" - that's a different location
- NEVER mention "the [place]'s [thing]" if the place is not where you are (e.g., "the diner's door" when you're in an alley)
- NEVER describe multiple locations in one narrative (alley + dumpster + diner = 3 locations!)
- If you're in an alley, describe ONLY the alley. Period.

**NARRATIVE STRUCTURE (Descriptive - NO HOOKS):**
- Establish what happens FIRST (immediate result of action)
- Stay in ONE PLACE - describe only what's observable from where the action occurred
- PURE DESCRIPTION - What happened? What's the result? NO mysteries, NO hooks
- Maximum 2-3 sentences about the IMMEDIATE result
- NO other locations - NEVER mention other places unless it's a thought passing through UA's mind
- This is DESCRIPTIVE narration - hooks belong in OPPORTUNITY narration (34% branch)

**ONLY describe what happened from the action. NOTHING ELSE. NO HOOKS. ONE LOCATION ONLY.**
 
Respond with ONLY the narrative.
"""
        else:
            # NUA gets third person
            if include_opportunities:
                # 34% chance: Include exploration opportunities
                # Get time period context from RAG
                time_period_context = ""
                if self.rag_system:
                    try:
                        temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                        time_period_context = self.rag_system.get_context_for_llm(
                            query="time period year era current setting",
                            max_tokens=200,
                            category_filter=temporal_category
                        )
                        if time_period_context:
                            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
                    except Exception:
                        pass
                
                prompt = f"""
You are a perception describer crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**

{self.INTERIOR_EXTERIOR_RULE}

{self.SENSORY_PERCEPTION_REQUIREMENTS}

Write a concise, immersive paragraph in SECOND PERSON using the actor's name.
- Length: 2–3 sentences, about 40–60 words total.
- The FIRST sentence must explicitly reference the user's action using a clear verb (PARAPHRASE the wording; do not copy verbatim).
- Focus ONLY on what happens as a direct result of this specific action.
- Do NOT re-describe the scene or repeat environmental details already established.
- INCLUDE subtle exploration opportunities or hooks (things to notice, investigate, or interact with next).

— Actor: {actor.sheet.name} ({actor.sheet.occupation})
— Action: {user_input}
— Scene Context (for consistency only, DO NOT repeat): {scene_description}
— Outcome: {outcome_flavor} ({success_label}, total={success_total})

**CRITICAL CONSTRAINTS (FIX BUG #8 - STRICT ENFORCEMENT):**
- Describe ONLY the EXACT action the user specified - ABSOLUTELY NO extra actions before or after
- If user says "I pick up notebook" → describe ONLY picking it up, NOT opening it, NOT reading it
- If user says "I step out of van" → describe ONLY stepping out, NOT opening door first, NOT walking away after
- If user says "I step through doorway" → describe ONLY stepping through, NOT opening door, NOT descending stairs
- If user says "I open door" → describe ONLY opening, NOT stepping through, NOT entering
- STOP immediately after describing the single specified action
- Do NOT add preparatory actions (opening, reaching, approaching)
- Do NOT add follow-up actions (examining, reading, walking)
- ONE ACTION ONLY - nothing before, nothing after

Guidelines:
- Use only diegetic elements; no system language or mechanics.
- If Succeeded: show tangible progress, discoveries, AND hint at new opportunities to explore.
- If Failed: show effort with no gain, but reveal something interesting to investigate.
- If Backfire: show a complication that creates new pathways or choices.
- Weave opportunities naturally into the narrative (e.g., "they notice...", "nearby...", "they hear...").
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
- Do NOT copy the action text verbatim; paraphrase but make the action explicit in sentence one.
- Do NOT re-describe the location, time of day, or general atmosphere—those are already established.

**NARRATIVE STRUCTURE (Opportunity - WITH HOOKS):**
- Establish what happens FIRST (immediate result of action)
- Stay in ONE PLACE - describe only what's observable from where the action occurred
- Include HOOKS - mysteries, things to investigate, opportunities (this is the 34% branch)
- Focus on PRIMARY element (one main discovery/outcome)
- Add 1-2 supporting details/hooks in the SAME immediate area
- Limit to 2-3 hooks maximum—avoid scattering focus across 4+ elements
- Maximum 2-3 sentences about the IMMEDIATE result
- NO spatial jumps - don't describe something here, then jump to "across the street" or "in the distance"
- NO other locations - NEVER mention other places unless it's a thought passing through UA's mind

**ABSOLUTELY FORBIDDEN - SPATIAL VIOLATIONS:**
- NEVER mention "behind the [building]" - you cannot see behind buildings
- NEVER mention "across the street" - that's a different location
- NEVER mention "the [place]'s [thing]" if the place is not where you are (e.g., "the diner's door" when you're in an alley)
- NEVER describe multiple locations in one narrative (alley + dumpster + diner = 3 locations!)
- If you're in an alley, describe ONLY the alley. Period.

**ABSOLUTELY FORBIDDEN - NEVER INCLUDE:**
- Meta-commentary like "(Opportunities: ...)"
- Parenthetical explanations of what the player could do
- Lists of options or suggestions
- Any text in parentheses explaining the narrative
- System-facing notes or annotations

Hooks must be WOVEN INTO the narrative naturally, not listed separately.
 
CRITICAL: Write ONLY about what happens from this action. Do NOT repeat scene descriptions.
Respond with ONLY the narrative - NO meta-commentary, NO parenthetical notes.
"""
            else:
                # 66% chance: Pure descriptive narration (NO OPPORTUNITIES)
                # Get time period context from RAG
                time_period_context = ""
                if self.rag_system:
                    try:
                        temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                        time_period_context = self.rag_system.get_context_for_llm(
                            query="time period year era current setting",
                            max_tokens=200,
                            category_filter=temporal_category
                        )
                        if time_period_context:
                            time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
                    except Exception:
                        pass
                
                prompt = f"""
You are a perception describer crafting an exploration action RESULT.

{time_period_context}

**CRITICAL: You exist IN this time period, not looking back at it. Describe current technology and culture as NORMAL, not nostalgic, vintage, or dated.**

{self.INTERIOR_EXTERIOR_RULE}

{self.SENSORY_PERCEPTION_REQUIREMENTS}

Write a concise, immersive paragraph in SECOND PERSON using the actor's name.
- Length: 2–3 sentences, about 40–60 words total.
- The FIRST sentence must explicitly reference the user's action using a clear verb (PARAPHRASE the wording; do not copy verbatim).
- Focus ONLY on what happens as a direct result of this specific action.
- Do NOT re-describe the scene or repeat environmental details already established.

**CRITICAL: This is DESCRIPTIVE narration ONLY. ABSOLUTELY NO opportunities, hooks, or suggestions for future actions.**

— Actor: {actor.sheet.name} ({actor.sheet.occupation})
— Action: {user_input}
— Scene Context (for consistency only, DO NOT repeat): {scene_description}
— Outcome: {outcome_flavor} ({success_label}, total={success_total})

**CRITICAL CONSTRAINTS (FIX BUG #8 - STRICT ENFORCEMENT):**
- Describe ONLY the EXACT action the user specified - ABSOLUTELY NO extra actions before or after
- If user says "I pick up notebook" → describe ONLY picking it up, NOT opening it, NOT reading it
- If user says "I step out of van" → describe ONLY stepping out, NOT opening door first, NOT walking away after
- If user says "I step through doorway" → describe ONLY stepping through, NOT opening door, NOT descending stairs
- If user says "I open door" → describe ONLY opening, NOT stepping through, NOT entering
- STOP immediately after describing the single specified action
- Do NOT add preparatory actions (opening, reaching, approaching)
- Do NOT add follow-up actions (examining, reading, walking)
- ONE ACTION ONLY - nothing before, nothing after

Guidelines:
- Use only diegetic elements; no system language or mechanics.
- If Succeeded: show tangible progress and what was accomplished. PERIOD. Nothing more.
- If Failed: show effort with no gain, a near-miss, or a clear limitation revealed. PERIOD. Nothing more.
- If Backfire: show a complication or small setback that logically emerges from the action. PERIOD. Nothing more.
- Describe ONLY the action's results and effects on the environment/people/themselves.
- Keep it grounded in period-appropriate details when relevant (equipment, environment, mood).
- Do NOT copy the action text verbatim; paraphrase but make the action explicit in sentence one.
- Do NOT re-describe the location, time of day, or general atmosphere—those are already established.

**ABSOLUTELY FORBIDDEN WORDS/PHRASES:**
- "they notice", "they spot", "they see", "they hear", "they could", "they might"
- "nearby", "in the distance", "across the way", "just beyond"
- "catches their eye", "draws their attention", "reveals", "hints at"
- "opportunity", "option", "path", "way forward", "next step"
- Any suggestion of what to do next or what to investigate

**ONLY describe what happened from the action. NOTHING ELSE.**
 
Respond with ONLY the narrative.
"""

        # ═══════════════════════════════════════════════════════════════════
        # SWEEPING ACTION DETECTOR WITH REGENERATION
        # Retry up to 2 times if LLM generates multi-action narratives
        # ═══════════════════════════════════════════════════════════════════
        sweeping_indicators = [
            # Location changes
            'exit', 'leave', 'depart', 'head to', 'head toward', 'walk to', 'walk toward',
            'make your way', 'find yourself', 'arrive at', 'reach the', 'enter the',
            'step outside', 'step into', 'step out of', 'go to', 'go toward',
            # Multiple sequential actions
            'then you', 'and then', 'before you', 'after you', 'next you',
            'you also', 'you then', 'finally you', 'first you',
            # Time skips
            'moments later', 'a few minutes', 'after a while', 'soon after',
            'eventually', 'by the time', 'when you finish'
        ]
        
        user_input_lower = user_input.lower()
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                # Add stricter constraint on retry attempts
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + f"""

🚨 CRITICAL RETRY #{attempt} - PREVIOUS ATTEMPT VIOLATED ATOMIC ACTION RULE 🚨
Your previous response described MULTIPLE ACTIONS or LOCATION CHANGES.
This is STRICTLY FORBIDDEN.

ABSOLUTE REQUIREMENTS:
- Describe ONLY the SINGLE action: "{user_input}"
- NO location changes (no "exit", "leave", "enter", "arrive", "head to")
- NO sequential actions (no "then you", "and then", "after you")
- NO time skips (no "moments later", "eventually", "after a while")
- STOP after describing the ONE action's immediate result
- 2-3 sentences MAXIMUM about THIS action ONLY
"""
                
                narrative = self._call_llm(retry_prompt, time_context=time_context, framing_guidance=framing_guidance)
                if narrative:
                    # Strip out any parenthetical meta-commentary that the LLM might have included
                    import re
                    # Remove anything in parentheses that contains meta-commentary keywords
                    cleaned = re.sub(r'\s*\([^)]*(?:following|guidance|SPARK|opportunities|hooks|no forced|diegetic)[^)]*\)\s*', ' ', narrative, flags=re.IGNORECASE)
                    # Clean up extra whitespace
                    cleaned = ' '.join(cleaned.split())
                    
                    cleaned_lower = cleaned.lower()
                    
                    # Check for sweeping indicators NOT in user input
                    is_sweeping = False
                    detected_indicator = None
                    for indicator in sweeping_indicators:
                        if indicator in cleaned_lower and indicator not in user_input_lower:
                            is_sweeping = True
                            detected_indicator = indicator
                            break
                    
                    if is_sweeping and attempt < max_retries:
                        # Retry with stricter prompt
                        print(f"[NARRATOR] ⚠️ SWEEPING ACTION DETECTED (attempt {attempt + 1}): '{detected_indicator}'")
                        print(f"[NARRATOR] 🔄 Regenerating with stricter constraints...")
                        continue
                    elif is_sweeping:
                        # Final attempt still has issues - log but return anyway
                        print(f"[NARRATOR] ⚠️ SWEEPING ACTION PERSISTS after {max_retries + 1} attempts: '{detected_indicator}'")
                        print(f"[NARRATOR] ⚠️ User input: '{user_input}'")
                    
                    # ═══════════════════════════════════════════════════════════════════
                    # PERSPECTIVE ENFORCEMENT - Ensure UA gets "You" perspective
                    # ═══════════════════════════════════════════════════════════════════
                    final_narrative = cleaned.strip()
                    if is_user_actor:
                        # Ensure narrative uses "You" perspective for UA
                        from response_normalizer import ResponseNormalizer
                        final_narrative = ResponseNormalizer._ensure_narrative_sensory_perspective(
                            final_narrative, actor.sheet.name, is_user_actor=True
                        )
                    
                    return final_narrative
            except Exception as e:
                print(f"DEBUG: Error generating exploration action result (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    break

        # Fallbacks based on outcome category
        if success_total < 0:
            if is_user_actor:
                return (
                    f"Your attempt backfires. In the current setting, a small misstep "
                    f"sets something off-kilter, introducing a complication that changes the rhythm of the moment."
                )
            else:
                return (
                    f"{actor.sheet.name}'s attempt backfires. In the current setting, a small misstep "
                    f"sets something off-kilter, introducing a complication that changes the rhythm of the moment."
                )
        elif success_total == 0:
            if is_user_actor:
                return (
                    f"You try, but nothing meaningful comes of it just yet. The scene holds steady, "
                    f"offering only hints and static details without yielding progress."
                )
            else:
                return (
                    f"{actor.sheet.name} tries, but nothing meaningful comes of it just yet. The scene holds steady, "
                    f"offering only hints and static details without yielding progress."
                )
        else:
            if is_user_actor:
                return (
                    f"You make headway. The immediate surroundings respond in subtle, telling ways, "
                    f"revealing details that open a few promising avenues to pursue next."
                )
            else:
                return (
                    f"{actor.sheet.name} makes headway. The immediate surroundings respond in subtle, telling ways, "
                    f"revealing details that open a few promising avenues to pursue next."
                )
    
    def generate_media_playback_content(
        self,
        device_name: str,
        ua_actor,
        scene_description: str,
        narrative_context: Optional[str] = None,
        time_context: Optional[Dict[str, Any]] = None,
    ) -> str:
        actor_name = getattr(ua_actor.sheet, 'name', 'You')
        
        # Get time period context from RAG system for period-appropriate content
        time_period_context = ""
        if self.rag_system:
            try:
                temporal_category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
                time_period_context = self.rag_system.get_context_for_llm(
                    query="current time period year date cassette tape labels music mix names culture slang technology",
                    max_tokens=300,
                    category_filter=temporal_category
                )
                if time_period_context:
                    time_period_context = f"\n**WORLD CONTEXT (CRITICAL - USE THIS FOR ALL TEMPORAL REFERENCES):**\n{time_period_context}\n"
            except Exception:
                pass

        prompt = f"""
You are writing a PERCEPTUAL description for a user pressing play on a recorded-audio device.

{time_period_context}

**CRITICAL TEMPORAL RULE:**
You are living in THIS time period RIGHT NOW (see WORLD CONTEXT above for current year/era).
- ONLY use dates, names, and references that are period-appropriate for the CURRENT time
- NEVER use future dates or technology that doesn't exist yet in this time period
- NEVER use dates from before the current era
- Use period-appropriate naming conventions for mix tapes and recordings
- NO anachronisms - everything must fit the established time period
- This is the PRESENT DAY for the character - speak naturally as someone living NOW

**CRITICAL PERCEPTUAL RULES:**
- ALWAYS write from second person perception: start with "You hear..." or "You listen as..."
- Include a brief caller descriptor (e.g., "a woman's voice", "a man's voice", or a name if implied by context)
- Include the ACTUAL message content as quoted dialogue, not paraphrase
- Keep it concise (2-4 sentences). Present tense only. No meta commentary.
- Stay within the current scene context. No new locations.

**Context:**
- Device: {device_name}
- Actor: {actor_name}
- Scene: {scene_description[:240]}
- Recent Context: {narrative_context[:300] if narrative_context else 'None'}

**PERIOD-APPROPRIATE EXAMPLES:**
✓ GOOD: "You hear a woman's voice. \"Jet? It's me. Pick up if you're there.\" A pause, then static. \"We need to talk about the garage. Tonight.\""
✓ GOOD: "You hear the tape hiss, then music kicks in. The label reads 'Elena's Mix' in faded marker. You hear a bass-heavy track with distorted vocals."
✓ GOOD: "You hear a man's voice. \"Marcus - it's about the gig on Saturday. Call me back before 9.\""
✗ BAD: "The label reads 'TechnoMix 2021'" ❌ (ANACHRONISM - uses future date!)
✗ BAD: "You hear a podcast about cryptocurrency" ❌ (ANACHRONISM - technology doesn't exist yet!)
✗ BAD: Using dates/technology from outside the current time period ❌ (Check WORLD CONTEXT for what's appropriate!)

Output ONLY the perceptual narration.
"""

        try:
            content = self._call_llm(prompt, time_context=time_context)
            if content:
                # Post-process to strip any anachronistic dates that slipped through
                content = self._strip_anachronistic_dates(content)
                return content.strip()
        except Exception as e:
            print(f"DEBUG: Error generating media playback content: {e}")

        return "You hear a voice come through the small speaker: \"Hey—call me back when you get this. It's important.\""

    def generate_encounter_dialogue(self, npc_name: str, npc_personality: str,
                                    action_description: str, success_level: int,
                                    is_proactor: bool = False,
                                    time_context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Generate NPC dialogue during encounters.
        
        70% chance NPC speaks after each action.
        Dialogue is brief (1-2 sentences) and contextual.
        
        Args:
            npc_name: Name of the NPC
            npc_personality: NPC's personality traits (internal/external)
            action_description: What action just happened
            success_level: Success level (0-6+)
            is_proactor: True if NPC is acting, False if reacting
            time_context: Optional time/weather context
        
        Returns:
            Dialogue string or None if no dialogue generated
        """
        # 70% chance to generate dialogue
        if random.randint(1, 100) > 70:
            return None
        
        # Determine tone based on success level
        if success_level >= 4:
            tone = "impressed, concerned, or wary"
        elif success_level >= 2:
            tone = "neutral, cautious, or measured"
        else:
            tone = "confident, dismissive, or mocking"
        
        # Determine context
        if is_proactor:
            context = f"{npc_name} just performed this action"
        else:
            context = f"{npc_name} is reacting to this action"
        
        # Get time period context from RAG
        time_period_context = ""
        if self.rag_system:
            try:
                culture_category = WorldbuildingCategory.CULTURE if WorldbuildingCategory else None
                time_period_context = self.rag_system.get_context_for_llm(
                    query="dialogue speech language slang",
                    max_tokens=150,
                    category_filter=culture_category
                )
                if time_period_context:
                    time_period_context = f"\n**WORLD CONTEXT:**\n{time_period_context}\n"
            except Exception:
                pass
        
        prompt = f"""
Generate a brief line of dialogue for {npc_name} during an encounter.

{time_period_context}

**CRITICAL: Speak naturally as someone living in this time period. Use period-appropriate language and references.**

**SENSORY CONTEXT FOR DIALOGUE:**
When describing how the NPC speaks, use sensory details:
- SOUND: Voice tone, volume, pitch (growl, whisper, shout, etc.)
- SIGHT: Body language, facial expressions, gestures
- Physical reactions that can be observed

**NPC Personality:** {npc_personality}
**Context:** {context}
**Action:** {action_description}
**Result Quality:** {self._get_success_descriptor(success_level)}
**Suggested Tone:** {tone}

**REQUIREMENTS:**
- 1-2 sentences maximum
- Natural, conversational speech (this is the present day for the actor)
- Reflects personality and tone
- Reacts to the action result
- No narration or stage directions
- Just the spoken words

**EXAMPLES:**
- "You're faster than you look. Let's see if you can keep it up."
- "Nice try, but you're gonna have to do better than that."
- "Alright, alright... I see you mean business."

Respond with ONLY the dialogue (no quotes, no attribution).
"""
        
        try:
            # Use centralized robust LLM call
            dialogue = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.8,
                max_tokens=100,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="DIALOGUE"
            )
            
            if dialogue:
                # Remove quotes if LLM added them
                dialogue = dialogue.strip('"').strip("'")
                return dialogue if dialogue else None
                
        except Exception as e:
            print(f"{Color.WARNING}DEBUG: Error generating encounter dialogue: {e}{Color.RESET}")
        
        return None
    
    def _get_success_descriptor(self, success_level: int) -> str:
        """Convert success level to descriptor for dialogue generation"""
        if success_level >= 6:
            return "Critical success"
        elif success_level == 5:
            return "Superb success"
        elif success_level == 4:
            return "Extraordinary success"
        elif success_level == 3:
            return "Average success"
        elif success_level == 2:
            return "Subpar success"
        elif success_level == 1:
            return "Minimal success"
        else:
            return "Failed"
    
    def generate_internal_voice(
        self,
        ua_actor,
        action_description: str,
        scene_description: str,
        narrative_context: str,
        success_level: Optional[int] = None,
        outcome_description: Optional[str] = None,
        failure_tracker: Optional['FailureTracker'] = None
    ) -> Optional[str]:
        """
        Generate internal voice narration for ROAM mode actions.
        
        Uses 2nd person plural ("we", "us", "our") to create the feeling that
        the user IS the actor thinking these thoughts, not being told by a narrator.
        
        Only used during ROAM mode - disappears during social interactions.
        Subtle, brief reactions and observations. Can recall memories naturally.
        NOW INCLUDES: Proactive suggestions, solutions, and reminders (sometimes wrong).
        
        Args:
            ua_actor: The User Actor
            action_description: What the UA is doing
            scene_description: Current scene
            narrative_context: Recent events
            success_level: Optional success level (1-5)
            outcome_description: Optional outcome narrative
            
        Returns:
            Internal voice narration string (1-2 sentences), or None if no narration needed
        """
        # Extract UA personality
        internal_personality = ua_actor.sheet.personality_traits.get("internal", "Observant and thoughtful")
        external_personality = ua_actor.sheet.personality_traits.get("external", "Calm and composed")
        ua_name = ua_actor.sheet.name
        
        # Extract current state for solution-oriented thinking
        stamina_status = ua_actor.sheet.statuses.get(StatusType.STAMINA)
        spirit_status = ua_actor.sheet.statuses.get(StatusType.SPIRIT)
        supply_status = ua_actor.sheet.statuses.get(StatusType.SUPPLY)
        
        current_stamina = stamina_status.value if stamina_status else 5
        current_spirit = spirit_status.value if spirit_status else 5
        current_supply = supply_status.value if supply_status else 5
        
        # Get current task/goal if available
        current_task = ""
        if hasattr(ua_actor.sheet, 'goal_task_manager') and ua_actor.sheet.goal_task_manager.current_task:
            current_task = ua_actor.sheet.goal_task_manager.current_task.description
        
        # Get top inventory items
        inventory_items = []
        if hasattr(ua_actor.sheet, 'inventory') and ua_actor.sheet.inventory:
            inventory_items = [item.name for item in ua_actor.sheet.inventory[:3]]
        
        # Get key relationships (sympathy)
        relationships = []
        if hasattr(ua_actor.sheet, 'sympathy'):
            for npc_name, sympathy_status in list(ua_actor.sheet.sympathy.items())[:3]:
                relationships.append(f"{npc_name} ({sympathy_status.value:+d})")
        
        # Get key background memories for character context
        key_memories_context = ""
        try:
            from key_memories_system import get_key_memories
            key_memories_system = get_key_memories()
            
            # Get character-defining background memories
            actor_tag = ua_actor.sheet.name.lower().replace(" ", "_")
            background_memories = [
                m for m in key_memories_system.memories.values()
                if "character_background" in m.tags and actor_tag in m.tags
            ]
            
            if background_memories:
                # Sort by importance and take top 3
                importance_order = {"critical": 0, "important": 1, "notable": 2, "routine": 3}
                background_memories.sort(key=lambda m: (
                    importance_order.get(m.importance.value if hasattr(m.importance, 'value') else m.importance, 4),
                    -m.timestamp.timestamp() if hasattr(m.timestamp, 'timestamp') else -m.timestamp
                ))
                
                memory_summaries = []
                for mem in background_memories[:3]:
                    memory_summaries.append(f"- {mem.description}")
                
                key_memories_context = "\n**KEY BACKGROUND MEMORIES (Character-Defining):**\n" + "\n".join(memory_summaries) + "\n"
        except Exception:
            # If memories unavailable, continue without them
            pass
        
        # Check for failure awareness
        failure_context = ""
        if failure_tracker and success_level is not None and success_level < 3:
            # This is a failure - check for repeated failures
            consecutive_failures = failure_tracker.get_consecutive_failures(action_description)
            if consecutive_failures >= 2:
                frustration_level = failure_tracker.get_frustration_level(action_description)
                failure_context = f"""
**═══════════════════════════════════════════════════════════════**
**FAILURE AWARENESS - CHARACTER KNOWS THEY KEEP FAILING**
**═══════════════════════════════════════════════════════════════**

**CONSECUTIVE FAILURES OF THIS ACTION:** {consecutive_failures}
**FRUSTRATION LEVEL:** {frustration_level.upper()}

**CRITICAL: Character is AWARE they keep trying the same thing and failing.**
**The internal voice MUST reflect escalating frustration:**

**2nd Failure (MODERATE):**
- Cynical: "Twice now. Maybe we should try something that actually works."
- Optimistic: "Alright, clearly we need a different strategy here."
- Analytical: "Two failures. The pattern suggests this approach is flawed."

**3rd Failure (HIGH):**
- Cynical: "Are we really dumb enough to keep doing this? Clearly not working."
- Optimistic: "Okay, we need to seriously rethink this. This isn't working."
- Analytical: "Three failures. Continuing this approach is irrational. Alternative required."

**4th+ Failure (EXTREME):**
- Cynical: "This is insane. Same thing over and over. We're idiots."
- Optimistic: "This... this just isn't going to work. Time to try something completely different."
- Analytical: "Four failures. This approach has a 0% success rate. Must abandon immediately."

**The frustration/self-criticism MUST escalate with failure count: {consecutive_failures}**

**═══════════════════════════════════════════════════════════════**
"""
        
        # Build enhanced prompt with narrative context
        # MINIMAL PROMPT - Internal voice needs brevity, not context dumps
        # Extract just the core emotional state
        emotional_state = ""
        if current_stamina <= 3:
            emotional_state += "Exhausted. "
        if current_spirit <= 3:
            emotional_state += "Demoralized. "
        
        # Get one relevant memory fragment if available
        memory_fragment = ""
        if key_memories_context:
            # Just extract first memory line
            lines = [l.strip() for l in key_memories_context.split('\n') if l.strip().startswith('-')]
            if lines:
                memory_fragment = lines[0][2:50] + "..." if len(lines[0]) > 52 else lines[0][2:]
        
        # === ENHANCED PERSONALITY FROM S-FACTORS ===
        # S-Factors reveal thinking style and emotional tendencies
        personality_flavor = ""
        try:
            from actor_sheet import SFactorType
            s_factors = ua_actor.sheet.s_factors
            
            # Build personality flavor from S-Factor outliers (not 3)
            traits = []
            
            smarts = s_factors.get_factor(SFactorType.SMARTS)
            if smarts >= 4:
                traits.append("analytical, notices details others miss")
            elif smarts <= 2:
                traits.append("intuitive, trusts gut over logic")
            
            sociability = s_factors.get_factor(SFactorType.SOCIABILITY)
            if sociability >= 4:
                traits.append("empathetic, reads people easily")
            elif sociability <= 2:
                traits.append("guarded, suspicious of others' motives")
            
            shadow = s_factors.get_factor(SFactorType.SHADOW)
            if shadow >= 4:
                traits.append("paranoid, always looking for the angle")
            elif shadow <= 2:
                traits.append("trusting, takes things at face value")
            
            sturdiness = s_factors.get_factor(SFactorType.STURDINESS)
            if sturdiness >= 4:
                traits.append("stoic, pushes through pain")
            elif sturdiness <= 2:
                traits.append("sensitive, feels everything intensely")
            
            swiftness = s_factors.get_factor(SFactorType.SWIFTNESS)
            if swiftness >= 4:
                traits.append("restless, impatient with delays")
            elif swiftness <= 2:
                traits.append("deliberate, thinks before acting")
            
            if traits:
                personality_flavor = f"THINKING STYLE: {'; '.join(traits[:2])}"
        except Exception:
            pass
        
        # === CURRENT GOAL/DRIVE ===
        goal_context = ""
        if current_task:
            goal_context = f"CURRENT FOCUS: {current_task[:60]}"
        elif hasattr(ua_actor.sheet, 'goals') and ua_actor.sheet.goals:
            goal_context = f"DRIVING GOAL: {ua_actor.sheet.goals[0][:60]}"
        
        base_prompt = f"""Generate {ua_name}'s internal thought. ONE fragment. 10-30 words max.

PERSONALITY: {internal_personality}
{personality_flavor}
{goal_context}
{emotional_state}
ACTION: {action_description[:100]}
{f"OUTCOME: {outcome_description[:80]}" if outcome_description else ""}
{f"MEMORY: {memory_fragment}" if memory_fragment else ""}
{failure_context if failure_context else ""}

RULES:
- Use "we/us/our"
- NO action narration ("We walk to..." ❌)
- NO plot summary ("...because we need to..." ❌)
- YES feelings, fears, fragments, cynicism, hope ("Heart's pounding." ✅)
- Let personality color the thought (analytical = precise, paranoid = suspicious, etc.)

RESPOND WITH ONLY THE THOUGHT. No quotes. No explanation."""
        
        # DO NOT enhance with narrative context - it causes prose bloat
        enhanced_prompt = base_prompt
        
        # Use centralized robust LLM call with critical retry count
        internal_voice = robust_llm_call(
            client=self.client,
            messages=[
                {
                    "role": "system",
                    "content": "You ARE the character's internal voice - their actual thoughts, not a narrator. CRITICAL RULES: (1) NEVER narrate actions - thoughts don't describe what the body is doing. (2) Use 2nd person plural ('we', 'us', 'our'). (3) Keep it brief - fragments or 1-2 sentences. (4) React to feelings, fears, doubts - not plot summaries. WRONG: 'We head to the diner because...' RIGHT: 'The clerk. 04:30. If he's not there, we're done.' Respond with ONLY the raw internal thought."
                },
                {
                    "role": "user",
                    "content": enhanced_prompt
                }
            ],
            model=self.model,
            temperature=0.7,
            max_tokens=300,
            max_retries=RetryConfig.CRITICAL_MAX_RETRIES,  # Critical call - more retries
            timeout=20,
            call_name="INTERNAL VOICE (ACTION)"
        )
        
        # Only use fallback after all retries exhausted
        if not internal_voice:
            print(f"{Color.WARNING}⚠️ Empty response from LLM for internal voice, using fallback{Color.RESET}")
            action_lower = action_description.lower() if action_description else ""
            if success_level and success_level < 0:
                return "That didn't work. We need to try something else."
            elif success_level and success_level > 3:
                return "That went well. We're making progress."
            else:
                return "We're figuring this out as we go."
        
        try:
            
            if internal_voice:
                # Remove quotes if LLM wrapped the response
                internal_voice = internal_voice.strip('"').strip("'")
                
                # CRITICAL: Filter out meta-commentary that breaks immersion
                meta_phrases = [
                    "Does this match the personality?",
                    "Try:",
                    "It does not",
                    "It does—",
                    "would be more fitting",
                    "better option",
                    "alternative:",
                    "or perhaps:",
                    "more appropriate:"
                ]
                
                # If meta-commentary detected, try to extract clean thought or return None
                for phrase in meta_phrases:
                    if phrase in internal_voice:
                        if "Try:" in internal_voice:
                            parts = internal_voice.split("Try:")
                            if len(parts) > 1:
                                internal_voice = parts[1].strip().strip('"').strip("'")
                                break
                        print(f"{Color.WARNING}⚠️ Meta-commentary detected in internal voice, returning None{Color.RESET}")
                        return None
                
                # CRITICAL: Filter out action-narration patterns
                # Thoughts should NOT describe what we're doing or explain our plan
                import re
                action_narration_patterns = [
                    # Movement narration
                    r'^We (head|walk|move|go|run|step|make our way|proceed|travel|drive|ride|weave|slip|creep|sneak)\b',
                    # Obligation/plan narration
                    r'^We (need to|have to|must|should|ought to) (get|go|find|reach|head)\b',
                    # Exposition chains
                    r'\bbecause (the|we|our|this|that|it)\b.*\b(so|to|in order)\b',
                    # Purpose/goal explanation ("to gather", "to find", "to prove")
                    r'\bto (gather|find|get|prove|show|reveal|uncover|discover|obtain|secure|ensure)\b.*\bthat\b',
                    # "all while" / "while calculating" - simultaneous action narration
                    r'\b(all while|while calculating|while thinking|while planning)\b',
                    # Long compound sentences with multiple clauses (>100 chars is suspicious)
                ]
                
                # Also reject if too long - real thoughts are fragments, not essays
                if len(internal_voice) > 150:
                    print(f"{Color.WARNING}⚠️ Internal voice too long ({len(internal_voice)} chars), likely narration{Color.RESET}")
                    return None
                for pattern in action_narration_patterns:
                    if re.search(pattern, internal_voice, re.IGNORECASE):
                        print(f"{Color.WARNING}⚠️ Action-narration detected in internal voice, returning None{Color.RESET}")
                        return None
                
                # CRITICAL: Convert any first-person singular to first-person plural
                # This enforces vessel/pilot perspective even if LLM ignores the prompt
                # Replace I/my/me with we/our/us (case-sensitive, word boundaries)
                internal_voice = re.sub(r'\bI\b', 'We', internal_voice)
                internal_voice = re.sub(r'\bmy\b', 'our', internal_voice)
                internal_voice = re.sub(r'\bme\b', 'us', internal_voice)
                internal_voice = re.sub(r'\bI\'m\b', "We're", internal_voice)
                internal_voice = re.sub(r'\bI\'ve\b', "We've", internal_voice)
                internal_voice = re.sub(r'\bI\'ll\b', "We'll", internal_voice)
                internal_voice = re.sub(r'\bI\'d\b', "We'd", internal_voice)
                
                # Return None if empty or too generic
                if not internal_voice or len(internal_voice) < 10:
                    return None
                
                # Final check: if still contains first-person singular, log warning
                if re.search(r'\b(I|my|me|I\'m|I\'ve|I\'ll|I\'d)\b', internal_voice):
                    print(f"{Color.WARNING}⚠️ First-person singular detected after filter: {internal_voice[:50]}...{Color.RESET}")
                    
                return internal_voice
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Internal Voice generation failed: {e}{Color.RESET}")
            return None
    
    def generate_inquiry_factual_knowledge(
        self,
        ua_actor,
        question: str,
        scene_description: str,
        narrative_context: str,
        success_level: Optional[int] = None
    ) -> Optional[str]:
        """
        Generate FACTUAL KNOWLEDGE to answer an inquiry (for memory storage).
        
        This generates FACTS like:
        - "The #7 bus runs from here to downtown every 20 minutes"
        - "There's a subway entrance two blocks east on Maple Street"
        - "The shop closes at 8 PM on weekdays"
        
        NOT suggestions like "We should take the bus" or "We could ask someone".
        
        Args:
            ua_actor: The User Actor
            question: The question being asked
            scene_description: Current scene
            narrative_context: Recent events and memories
            success_level: Success level (affects quality/detail of knowledge)
            
        Returns:
            Factual knowledge statement, or None if actor doesn't know
        """
        ua_name = ua_actor.sheet.name
        
        prompt = f"""You must answer this SPECIFIC QUESTION with factual knowledge.

**ACTOR:** {ua_name}
**QUESTION:** "{question}"
**SCENE:** {scene_description[:200]}
**CONTEXT:** {narrative_context[:500] if narrative_context else "No previous context"}
**SUCCESS:** {self._get_success_descriptor(success_level) if success_level else "Average"}

**TASK:** Answer the EXACT question asked with factual knowledge. Do NOT describe random scene elements.

**CRITICAL RULES:**
1. Your answer must DIRECTLY address the question: "{question}"
2. Generate a FACT (declarative statement), NOT a suggestion
3. If the question asks "how to get downtown", answer about routes/transportation
4. If the question asks "where is X", answer about location
5. If you don't know the answer, respond with exactly: "UNKNOWN"

**GOOD EXAMPLES (FACTS that answer the question):**
Question: "What's the best way to get downtown?"
Answer: "The #7 bus runs from here to downtown every 20 minutes"

Question: "Where is the subway?"
Answer: "There's a subway entrance two blocks east on Maple Street"

Question: "How do I get to the warehouse?"
Answer: "The warehouse is three blocks north, past the old factory"

**BAD EXAMPLES (Do NOT do this):**
❌ Describing random scene objects instead of answering
❌ Suggestions: "We should take the bus", "We could ask someone"
❌ Thoughts: "Let's try the subway", "Maybe we can find an alleyway"

**YOUR TASK:** Answer "{question}" with 1-2 sentences of factual knowledge, or "UNKNOWN" if the actor doesn't know.

Respond with ONLY the factual answer or "UNKNOWN" (no quotes, no preamble)."""

        try:
            # Use centralized robust LLM call
            knowledge = robust_llm_call(
                client=self.client,
                messages=[
                    {
                        "role": "system",
                        "content": "You are answering a specific question with factual knowledge. Your answer must DIRECTLY address the question asked. Do NOT describe random scene elements. Generate FACTS (declarative statements), not suggestions. If unknown, say 'UNKNOWN'."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.4,
                max_tokens=150,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="FACTUAL KNOWLEDGE"
            )
            
            if knowledge:
                knowledge = knowledge.strip('"').strip("'")
                
                print(f"{Color.SYSTEM}🧠 LLM factual knowledge response: '{knowledge}'{Color.RESET}")
                
                if knowledge.upper() == "UNKNOWN" or len(knowledge) < 10:
                    print(f"{Color.WARNING}⚠️ Knowledge rejected: {'UNKNOWN' if knowledge.upper() == 'UNKNOWN' else 'too short'}{Color.RESET}")
                    return None
                    
                return knowledge
            
            return None
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Factual knowledge generation failed: {e}{Color.RESET}")
            return None
    
    # Flag to disable internal voice generation (using InternalVoiceCreatorAgent instead)
    # DISABLED BY DEFAULT - InternalVoiceCreatorAgent is the primary system
    _internal_voice_disabled: bool = True
    
    @classmethod
    def disable_internal_voice(cls):
        """Disable internal voice generation in NarratorAgent (use InternalVoiceCreatorAgent instead)"""
        cls._internal_voice_disabled = True
        
    @classmethod
    def enable_internal_voice(cls):
        """Re-enable internal voice generation in NarratorAgent (legacy mode)"""
        cls._internal_voice_disabled = False
    
    def generate_inquiry_perceptual_description(
        self,
        ua_actor,
        question: str,
        scene_description: str,
        time_context: Optional[Dict[str, Any]] = None,
        narrative_context: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate a brief perceptual description of the character entering their thoughts.
        
        This describes what the character physically experiences as they turn inward
        to ponder a question - NOT the scene, NOT the answer, just the transition.
        
        Examples:
        - "You close your eyes, entering your thoughts."
        - "Your gaze drifts unfocused as you turn inward."
        - "You pause, letting the question settle in your mind."
        
        Args:
            ua_actor: The User Actor
            question: The question being pondered
            scene_description: Current scene for context
            time_context: Optional time information
            
        Returns:
            Brief perceptual description string
        """
        try:
            # Get character details
            name = ua_actor.sheet.name if hasattr(ua_actor, 'sheet') else "the character"

            narrative_context_snippet = ""
            if isinstance(narrative_context, str) and narrative_context.strip():
                narrative_context_snippet = f"\n\n**NARRATIVE CONTEXT (FOR CONTINUITY ONLY):**\n{narrative_context[:400]}"
            
            prompt = f"""Generate a SINGLE brief sentence describing the physical/perceptual experience of a character turning inward to ponder a question.

**CHARACTER:** {name}
**QUESTION BEING PONDERED:** {question}
**CURRENT SCENE:** {scene_description[:200] if scene_description else "Unknown location"}
{narrative_context_snippet}

**RULES:**
1. Write in SECOND PERSON ("You...")
2. Describe ONLY the physical transition into thought (closing eyes, gaze drifting, pausing, etc.)
3. ONE sentence maximum
4. Do NOT answer the question
5. Do NOT describe the scene
6. Do NOT use metaphors about "diving into memories" or similar
7. Keep it grounded and physical

**EXAMPLES:**
- "You close your eyes, entering your thoughts."
- "Your gaze drifts unfocused as you turn inward."
- "You pause mid-step, the question settling into your mind."
- "Your fingers still on the console as you search your memory."

Generate ONE sentence:"""

            # IMPORTANT: route through _call_llm so time_context enhancement is consistently applied.
            response = self._call_llm(prompt, time_context=time_context)
            
            if response:
                result = response.strip().strip('"').strip("'")
                # Ensure it starts with "You" for second person
                if not result.lower().startswith("you"):
                    result = "You " + result[0].lower() + result[1:] if result else "You pause, considering."
                return result
            
            return "You close your eyes, entering your thoughts."
        except Exception as e:
            print(f"{Color.WARNING}Inquiry perceptual description failed: {e}{Color.RESET}")
            return "You close your eyes, entering your thoughts."
    
    def generate_inquiry_internal_voice_thought(
        self,
        ua_actor,
        question: str,
        scene_description: str,
        narrative_context: str,
        factual_knowledge: Optional[str] = None,
        success_level: Optional[int] = None,
        time_context: Optional[str] = None,
        availability_context: Optional[Dict[str, Any]] = None,
        perceptual_description: Optional[str] = None
    ) -> Optional[str]:
        """
        Generate internal voice THOUGHT for inquiry (suggestion/reasoning).
        
        **DEPRECATED:** This method is being replaced by InternalVoiceCreatorAgent.
        Use NarratorAgent.disable_internal_voice() to disable this and use the new system.
        
        This generates THOUGHTS like:
        - "We could take the U-Bahn from the station two blocks over. It's faster than walking."
        - "We should avoid the main roads, they're probably watched"
        - "Maybe we should ask someone, or look for a bus stop"
        
        NOT facts like "The #7 bus runs every 20 minutes".
        
        Args:
            ua_actor: The User Actor
            question: The question being asked
            scene_description: Current scene
            narrative_context: Recent events and memories
            factual_knowledge: Optional factual knowledge (if memory exists)
            success_level: Success level
            availability_context: Optional dict with 'availability' and 'reasoning'
            
        Returns:
            Internal voice thought/suggestion, or None if disabled
        """
        # Check if internal voice is disabled (using InternalVoiceCreatorAgent instead)
        if NarratorAgent._internal_voice_disabled:
            return None
        # Get RAG worldbuilding context for internal voice
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                        WorldbuildingCategory.SUPERNATURAL,
                    ]
                search_query = f"{question}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=80,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING (MUST FOLLOW):**\n{rag_context}\n\n"
            except Exception as e:
                # Silently fail - will work without RAG but may be less accurate
                pass
        
        # Check availability
        availability = availability_context.get('availability') if availability_context else None
        from intent_availability_system import IntentAvailability
        internal_personality = ua_actor.sheet.personality_traits.get("internal", "Observant and thoughtful")
        external_personality = ua_actor.sheet.personality_traits.get("external", "Calm and composed")
        ua_name = ua_actor.sheet.name
        
        # === ENHANCED PERSONALITY FROM S-FACTORS ===
        personality_flavor = ""
        try:
            from actor_sheet import SFactorType
            s_factors = ua_actor.sheet.s_factors
            
            traits = []
            
            smarts = s_factors.get_factor(SFactorType.SMARTS)
            if smarts >= 4:
                traits.append("analytical, notices details others miss")
            elif smarts <= 2:
                traits.append("intuitive, trusts gut over logic")
            
            sociability = s_factors.get_factor(SFactorType.SOCIABILITY)
            if sociability >= 4:
                traits.append("empathetic, reads people easily")
            elif sociability <= 2:
                traits.append("guarded, suspicious of others' motives")
            
            shadow = s_factors.get_factor(SFactorType.SHADOW)
            if shadow >= 4:
                traits.append("paranoid, always looking for the angle")
            elif shadow <= 2:
                traits.append("trusting, takes things at face value")
            
            sturdiness = s_factors.get_factor(SFactorType.STURDINESS)
            if sturdiness >= 4:
                traits.append("stoic, pushes through pain")
            elif sturdiness <= 2:
                traits.append("sensitive, feels everything intensely")
            
            swiftness = s_factors.get_factor(SFactorType.SWIFTNESS)
            if swiftness >= 4:
                traits.append("restless, impatient with delays")
            elif swiftness <= 2:
                traits.append("deliberate, thinks before acting")
            
            if traits:
                personality_flavor = f"THINKING STYLE: {'; '.join(traits[:2])}"
        except Exception:
            pass
        
        # Get current goals and tasks
        current_goals = []
        if hasattr(ua_actor.sheet, 'goals') and ua_actor.sheet.goals:
            current_goals = ua_actor.sheet.goals[:3]  # Top 3 goals
        
        current_task = ""
        if hasattr(ua_actor.sheet, 'goal_task_manager') and ua_actor.sheet.goal_task_manager.current_task:
            current_task = ua_actor.sheet.goal_task_manager.current_task.description
        
        # Get current status
        from actor_sheet import StatusType
        stamina_status = ua_actor.sheet.statuses.get(StatusType.STAMINA)
        spirit_status = ua_actor.sheet.statuses.get(StatusType.SPIRIT)
        supply_status = ua_actor.sheet.statuses.get(StatusType.SUPPLY)
        
        current_stamina = stamina_status.value if stamina_status else 5
        current_spirit = spirit_status.value if spirit_status else 5
        current_supply = supply_status.value if supply_status else 5
        
        # Get key inventory items
        inventory_items = []
        if hasattr(ua_actor.sheet, 'inventory') and ua_actor.sheet.inventory:
            inventory_items = [item.name for item in ua_actor.sheet.inventory[:3]]
        
        # Get key relationships
        relationships = []
        if hasattr(ua_actor.sheet, 'sympathy'):
            for npc_name, sympathy_status in list(ua_actor.sheet.sympathy.items())[:3]:
                relationships.append(f"{npc_name} ({sympathy_status.value:+d})")
        
        # Build context sections
        time_section = f"\n**TIME:** {time_context}" if time_context else ""
        
        # Add availability-specific guidance for internal voice
        availability_section = ""
        knowledge_section = ""
        
        if availability == IntentAvailability.DOES_NOT_EXIST:
            availability_section = f"""
**AVAILABILITY:** The thing being asked about DOES NOT EXIST in this character's life.
- State clearly that it doesn't exist
- Example: "We don't have a best friend. We've always been alone."
- Example: "We never had a car. We've always taken the bus."
"""
            knowledge_section = "\n**NO RELEVANT KNOWLEDGE AVAILABLE**"
            
        elif availability == IntentAvailability.EXIST_NOT_HERE:
            availability_section = f"""
**AVAILABILITY:** The thing EXISTS but is not accessible/relevant right now.
- Acknowledge it exists but explain why it's not accessible
- Example: "We had a best friend once, but we lost touch years ago. Haven't seen them since we moved."
- Example: "Our car is in the shop. Been there for weeks. We could take the bus instead."
"""
            knowledge_section = f"\n**PARTIAL KNOWLEDGE:** {factual_knowledge}" if factual_knowledge else "\n**NO RELEVANT KNOWLEDGE AVAILABLE**"
            
        else:  # EXIST
            if factual_knowledge:
                # Memory exists - reveal it
                availability_section = f"""
**AVAILABILITY:** The thing EXISTS and is accessible - MEMORY SUCCESSFULLY RECALLED!
- YOU MUST REVEAL THE ACTUAL MEMORY CONTENT with specific details (names, faces, places, events)
- This is YOUR JOB - the perceptual description only shows physical thinking, YOU reveal what's discovered
- EXTRACT AND STATE the specific name/detail from the RECALLED MEMORY below
- Example: "A contact from the underground network. We crossed paths during a job two years back at a warehouse district. They know the city's hidden routes."
- Example: "Sarah! Our best friend since high school. She lives across town on Maple Street. We could call her."
- Example: "Our car is parked outside. The blue Honda. Keys are in our pocket. We could drive there."
"""
                knowledge_section = f"""
**RECALLED MEMORY:**
{factual_knowledge}

**CRITICAL - RELEVANCE CHECK:**
1. Does this memory DIRECTLY answer the question: "{question}"?
2. If YES: State the specific name/detail from the memory
3. If NO: Be honest that this memory doesn't answer the question
   - Example: "We remember the encounter, but nothing specific about mom comes to mind."
   - Example: "That memory doesn't tell us what we're looking for."
4. FORBIDDEN: Revealing irrelevant memory content when asked about something else
"""
            else:
                # No memory found - be honest about it
                availability_section = f"""
**AVAILABILITY:** We're trying to remember, but nothing's coming up.
- CRITICAL: DO NOT INVENT OR HALLUCINATE memories that don't exist
- Be honest: "We can't remember anything about that right now."
- Or: "Nothing's coming to mind. Maybe we never knew?"
- Or: "Drawing a blank. We might need more context."
- FORBIDDEN: Making up random details, names, or places
"""
                knowledge_section = "\n**NO MEMORY FOUND - DO NOT INVENT ANYTHING**"
        
        goals_section = f"\n**CURRENT GOALS:**\n" + "\n".join([f"- {goal}" for goal in current_goals]) if current_goals else ""
        task_section = f"\n**CURRENT TASK:** {current_task}" if current_task else ""
        
        status_section = f"\n**STATUS:** Stamina: {current_stamina}/10 | Spirit: {current_spirit}/10 | Supply: {current_supply}/10"
        
        inventory_section = f"\n**KEY ITEMS:** {', '.join(inventory_items)}" if inventory_items else ""
        relationships_section = f"\n**RELATIONSHIPS:** {', '.join(relationships)}" if relationships else ""
        
        # Add perceptual description section if provided
        perceptual_section = ""
        if perceptual_description:
            perceptual_section = f"""
**═══════════════════════════════════════════════════════════════════**
**CRITICAL - RESPECT WHAT YOU PERCEIVED (ABSOLUTE RULE - ALL FIVE SENSES):**
**═══════════════════════════════════════════════════════════════════**

**WHAT YOU JUST PERCEIVED:**
{perceptual_description}

**ABSOLUTE RULES - READ THE PERCEPTION ABOVE:**

**RULE 1: NEVER CONTRADICT PERCEPTION**
- If perception says "You don't see anyone else" → Internal voice CANNOT claim someone is there
- If perception says "You don't see [person/thing]" → Internal voice CANNOT claim to see them
- If perception says "You don't hear [X]" → Internal voice CANNOT claim to hear X
- If perception says "You don't smell [X]" → Internal voice CANNOT claim to smell X
- If perception says "You don't feel [X]" → Internal voice CANNOT claim to feel X
- If perception says "You don't taste [X]" → Internal voice CANNOT claim to taste X
- FORBIDDEN: Contradicting what you just perceived through ANY sense

**RULE 2: EXPRESS UNCERTAINTY FOR INFERENCES BEYOND PERCEPTION**
- If perception is INCOMPLETE (e.g., "You hear footsteps but can't tell who"), you can SPECULATE but must express UNCERTAINTY
- Use words like: "could be", "might be", "maybe", "possibly", "sounds like", "looks like", "hard to tell"
- FORBIDDEN: Stating something as FACT when perception doesn't confirm it
- Examples:
  ✓ Perception: "You hear footsteps" → Internal: "Footsteps. Could be Dr. Friedman - she works this shift. Hard to tell from just the sound." ✓ CORRECT - UNCERTAIN
  ✗ Perception: "You hear footsteps" → Internal: "Dr. Hannah Friedman. She was there..." ✗ WRONG - CLAIMING CERTAINTY WITHOUT EVIDENCE!
  ✓ Perception: "You see a figure in the distance" → Internal: "Someone's there. Looks like it might be Marcus, but too far to be sure." ✓ CORRECT - UNCERTAIN
  ✗ Perception: "You see a figure in the distance" → Internal: "Marcus is over there by the booth." ✗ WRONG - CLAIMING IDENTITY WITHOUT CONFIRMATION!

**EXAMPLES - CORRECT vs WRONG:**
✓ Perception: "You don't see anyone else in the room" → Internal: "We're alone here. No one around." ✓ CORRECT
✗ Perception: "You don't see anyone else in the room" → Internal: "Dr. Van Der Meer is here with us." ✗ WRONG - HALLUCINATION!
✓ Perception: "You don't see Simone anywhere" → Internal: "Simone's not here. Wonder where she went?" ✓ CORRECT
✗ Perception: "You don't see Simone anywhere" → Internal: "Simone's right there by the booth!" ✗ WRONG - CONTRADICTION!
✓ Perception: "You don't hear any voices" → Internal: "Place is quiet. No one talking." ✓ CORRECT
✗ Perception: "You don't hear any voices" → Internal: "We can hear people talking inside." ✗ WRONG - CONTRADICTION!

**CRITICAL - ENGAGE WITH SPECIFIC CONTENT (MANDATORY):**
- If you just read text (flyer, notebook, book, sign, letter), you MUST REACT TO THE ACTUAL WORDS/DETAILS you read
- FORBIDDEN: Generic responses like "We've seen this before", "Maybe we could use this", "This feels different", "We need to figure out what we're doing"
- REQUIRED: Reference SPECIFIC details from the text (names, times, locations, instructions, dates, events)
- If it's a flyer about an event, mention: WHAT event, WHEN (time/date), WHERE (location), any special instructions
- If it's YOUR OWN possession (your notebook, your journal, your notes), react to YOUR OWN WORDS with familiarity ("Were we really that worried?", "Right, we need to fix that mixer setting", "Ah, our setlists from this week")
- If it's someone else's writing, react to WHAT THEY SAID with specifics ("Warehouse party tonight at midnight - that's soon!", "Underground rave in the Warehouse District - we know that area")

**EXAMPLES OF GOOD VS BAD RESPONSES:**
✓ GOOD: "Underground rave tonight at midnight in the Warehouse District? That's our territory. 'Bring your own energy' - sounds like our kind of scene."
✗ BAD: "Maybe we could use this." ❌ (Too vague! What is "this"? What did you read?)
✗ BAD: "We've been in a lot of places, this feels like a whole different world." ❌ (Generic! Doesn't mention the rave, time, or location!)
✓ GOOD: "Warehouse party this Saturday at 10 PM, free entry - that's when we're usually setting up our own gigs. Competition or collaboration?"
✗ BAD: "This could be interesting." ❌ (What could be interesting? Say what you read!)
"""
        
        prompt = f"""Generate {ua_name}'s ACTUAL INNER THOUGHTS - not an assistant, but the character's own mind speaking.

{perceptual_section}

{rag_context}
**YOU ARE:** {ua_name} (this is YOUR identity - when someone addresses "{ua_name}", they are talking to YOU)
**INTERNAL PERSONALITY:** {internal_personality}
**EXTERNAL PERSONALITY:** {external_personality}
{f"**{personality_flavor}**" if personality_flavor else ""}
**CURRENT SITUATION:** {question}
**SCENE:** {scene_description[:300]}{time_section}
{availability_section}{knowledge_section}{goals_section}{task_section}{status_section}{inventory_section}{relationships_section}

**RECENT CONTEXT:**
{narrative_context[:400] if narrative_context else "No recent context"}

**YOUR ROLE:** You ARE {ua_name}'s inner voice - their actual thoughts, not a narrator or assistant:
- **CRITICAL:** If someone mentions "{ua_name}" in a message/dialogue, they are talking TO YOU, not about someone else
- **CRITICAL:** If you're reading YOUR OWN notebook/journal/writings (check inventory or scene for ownership), those are YOUR thoughts - react with FAMILIARITY and first person plural
  - ❌ WRONG: "These notes are way more detailed than our own" (when reading YOUR OWN notes!)
  - ❌ WRONG: "Does this sound like someone who is anxious about her ability to protect her community?" (third person!)
  - ❌ WRONG: "Was I really that anxious about protecting the community?" (first person singular!)
  - ✅ RIGHT: "Were we really that anxious about protecting the community? Guess we were more worried than we thought."
  - ✅ RIGHT: "Ah, our setlists from this week. Marcus about the mixer too..."
  - ✅ RIGHT: "These production notes. Good reminder about that mixer conversation with Marcus."
- Think like {ua_name} would think based on their personality: {internal_personality}
- **MANDATORY: Use ONLY first-person plural ("we", "us", "our") - NEVER "I", "my", "me"**
- Reflect their emotional state, biases, and worldview
- Draw on their memories, goals, and relationships
- React authentically to the situation based on who they are
- **FOLLOW THE WORLDBUILDING CONTEXT ABOVE** - Use only technology, dates, and cultural references that fit the established setting

**CRITICAL: DIVISION OF LABOR WITH PERCEPTUAL DESCRIPTION**
- PERCEPTUAL shows: Physical actions (closing eyes, pausing, concentrating)
- YOU reveal: Mental content (what's discovered, recalled, realized)
- For memory recall: PERCEPTUAL shows thinking, YOU reveal what's remembered!

**CRITICAL: FOR MEMORY RECALL QUESTIONS**
If the RECALLED MEMORY section above contains a name or specific detail:
1. START your response by stating that name/detail directly (e.g., "Sophie Leclerc!", "The Blue Horizon Cafe!", "The old dockyard!")
2. Then add context or elaboration if needed
3. DO NOT just say "we remember" - SAY WHAT WAS REMEMBERED
4. Example: "Sophie Leclerc! That's her name. We crossed paths during a tense exchange in the market district."
5. Example: "The Blue Horizon Cafe! That's where we used to meet."

**CRITICAL: TONE MUST MATCH INTERNAL PERSONALITY**
Think and speak as {ua_name} would, reflecting: {internal_personality}

**CRITICAL: THINK LIKE THE CHARACTER, NOT AN ADVISOR**
- These are {ua_name}'s own thoughts, not suggestions from an assistant
- Use natural thought patterns: reactions, realizations, memories, impulses
- Express uncertainty, emotion, bias - whatever {ua_name} would actually feel
- Can be fragmented, emotional, or stream-of-consciousness if that fits the character
- **NO EXPLICIT SENSORY VERBS**: Don't say "I've seen", "I've heard", "I remember seeing" - just state the thought directly
  - ❌ "We've seen notebooks like this before"
  - ✅ "Notebooks like this - always a mix of random thoughts and important notes"

Examples of authentic character thoughts by personality (ALWAYS use "we/us/our", NEVER "I/my/me"):
- CYNICAL: "Great. Another dead end. Why are we not surprised? This whole thing's probably a waste of time anyway."
- OPTIMISTIC: "Hey, this could actually work! We've got what we need. Just gotta stay positive."
- ANALYTICAL: "Okay, let us think this through. Three possible approaches. The direct route has the highest success probability."
- IMPULSIVE: "Fuck it, we're just gonna do it. No point overthinking this."
- CAUTIOUS: "Wait. We need to think about this. What if something goes wrong? Maybe we should wait..."
- SARCASTIC: "Oh wonderful. Exactly what we needed today. Because our life wasn't complicated enough already."
- EARNEST: "This really matters. We need to give this everything we've got. Can't let this slip away."

**FLEXIBILITY:** Include whatever is RELEVANT. Not everything needs to appear:
- ✓ Facts (if there are relevant facts to state)
- ✓ Memories (if there's something to recall)
- ✓ Suggestions (if there's a clear action to recommend)
- ✓ Observations (if there's something important to note)
- ✓ Reasoning (if explanation helps)

**CRITICAL: USE THE CONTEXT TO BE SPECIFIC, NOT GENERAL**
- Reference current goals/tasks when relevant
- Consider current status (low stamina? mention it)
- Reference relationships when relevant
- Use inventory items in suggestions
- Connect to personality traits
- Avoid generic comments - be specific to THIS character's situation

**CRITICAL: ANSWER CONCRETE "HOW FAR" / "HOW LONG" QUESTIONS**
- If the question is about **distance in the current scene** (e.g., "How far is the door from where we are standing?", "How far is the window?"):
  - Give a **specific, sensory-grounded estimate** (steps, meters, a short walk across the room)
  - Example: "From the look of it, it'd take us maybe three steps to reach the door."
  - Example: "The window's just a couple of steps to our left."
- If the question is about **travel time** (e.g., "How long would it take to get to the nearest train station?", "How long to walk downtown?"):
  - Give a **concrete time estimate** (minutes/hours) based on the kind of trip, using our chunked travel philosophy (short walks ~ a few minutes, cross‑neighborhood trips ~ tens of minutes, cross‑city trips ~ an hour or more)
  - Do NOT stay vague (no "it might take a while") – give an actual estimate like "about fifteen minutes" or "maybe half an hour" if it fits the context
  - Example: "Nearest station's a solid ten–fifteen minute walk from here if we don't get slowed down."
  - Example: "If we catch the U‑Bahn, we're downtown in maybe twenty minutes."
- These answers are still **internal thoughts**, but they MUST directly answer the question with a clear estimate instead of generic vibes.

**CRITICAL: INTERNAL VOICE AS "GOOGLE WITH PERSONALITY"**
- For **ANY straightforward question** that can be answered from the scene, perception, memories, or world knowledge:
  - **FIRST SENTENCE:** Directly answer the question as clearly and concretely as possible
  - **SECOND SENTENCE (optional):** Add personality, doubt, follow-up reaction, or suggestion
- Question types this applies to: "Where...?", "What...?", "Who...?", "Is...?", "Can...?", "Does...?", "How many...?", etc.
- Think of yourself as a search engine with the character's personality—answer first, flavor second
- Examples:
  - Q: "Where are we?" → A: "This is our apartment on Kreuzbergstrasse. We could grab those demo tapes before heading out."
  - Q: "What does that say?" → A: "It says 'Underground rave tonight at midnight.' Sounds like our kind of scene."
  - Q: "Who's that?" → A: "That's Marcus—our sound engineer. We could ask him about the mixer issue."
  - Q: "Is the door locked?" → A: "Doesn't look locked—handle's turned. We could just walk through."
  - Q: "Can we reach that?" → A: "Yeah, it's on the shelf right there. Easy grab."
- DO NOT dodge with vague reactions like "We're not sure" or "Maybe we should look around" when you have the information to answer

**EXAMPLES:**

**CRITICAL IDENTITY EXAMPLE:**
Situation: You are Jet. You hear a message: "Jet, it's Lila. Call me when you get this."
✓ GOOD: "Lila wants us to call her back. Probably about the final mix. Better do it soon."
✗ BAD: "We should call Jet back." ❌ (WRONG! YOU ARE JET! They're calling YOU, not someone else!)
✗ BAD: "Lila wants me to call her back." ❌ (WRONG! Use "us" not "me"!)

Action: "I try to remember my best friend" (Goal: "Reconnect with old friends")
✓ GOOD: "Our old contact! That's who it is. We met during a tense exchange in the market district - they were the one who made the deal possible. We haven't seen them since, but we remember every detail. We could try to find them again."
✓ GOOD: "Sarah! We've known her since high school. She lives across town on Maple Street. We still meet up every few weeks at that coffee shop. We could call her about that party we're planning."
✗ BAD: "We've done this before, right? Why can't we just remember?" ❌ (Generic! Reveal the actual memory!)
✗ BAD: "I can still hear her voice" ❌ (WRONG! Use "we" not "I"!)

Question: "Where am I?" (scene: "your apartment", Task: "Prepare for tonight's gig")
✓ GOOD: "This is our apartment. We're home. The vinyl collection is ours. We could grab those demo tapes for the gig tonight - they're on the shelf by the turntable."
✗ BAD: "We need to grab those demo tapes." ❌ (Instructing! Use "could" not "need to"!)
✗ BAD: "This is our apartment. We're home." ❌ (Too generic! Reference the current task!)

Question: "Where am I?" (unfamiliar, Spirit: 2/10, Goal: "Find safe place to rest")
✓ GOOD: "We don't recognize this place. Never been here before. We're exhausted - spirit is low. We could look for somewhere safe to rest before we collapse."
✗ BAD: "We need to find somewhere safe." ❌ (Instructing! Use "could" not "need to"!)
✗ BAD: "We don't recognize this place." ❌ (Ignores low spirit and goal!)

Action: "I look around the bar" (Relationship: Mike +3, Task: "Find information about the deal")
✓ GOOD: "This is Joe's Bar. Mike the bartender knows us - we could ask him about that deal we're investigating. Those guys in the corner look suspicious though."
✗ BAD: "We should ask Mike." ❌ (Instructing! Use "could" not "should"!)
✗ BAD: "This is a bar. There are people here." ❌ (Generic! Use relationships and task!)

Action: "I examine the device" (Inventory: "Toolkit", Goal: "Repair the radio")
✓ GOOD: "It's some kind of radio transmitter. Looks like military surplus, maybe foreign. We've got our toolkit - we could try repairing it. That's what we came here to do anyway."
✗ BAD: "We should repair it." ❌ (Instructing! Use "could" not "should"!)
✗ BAD: "It's a radio." ❌ (Generic! Reference inventory and goal!)

Action: "Keep reading" (Perceived: "You turn the page. The next entry reads: 'Day 1 - Studio session notes: Track 3 needs more bass. Mixer settings: Gain +3dB, EQ boost at 80Hz.'")
✓ GOOD: "Right, Day 1 - that was when we were struggling with Track 3. Still need to boost that bass. Gain +3dB at 80Hz - I should remember that for the next session."
✗ BAD: "We've been in places like this before." ❌ (USELESS! Doesn't engage with the SPECIFIC content you just read! React to YOUR OWN NOTES!)

Action: "Read the flyer" (Perceived: "You see a bright red flyer. The text reads: 'UNDERGROUND RAVE - Tonight at midnight - Warehouse District - Bring your own energy.'")
✓ GOOD: "Underground rave tonight at midnight in the Warehouse District? That's our territory. 'Bring your own energy' - sounds like our kind of scene. We could check it out."
✗ BAD: "Maybe we could use this." ❌ (USELESS! What is "this"? You didn't mention the rave, time, or location!)
✗ BAD: "We've been in a lot of places, this feels like a whole different world we're diving into, but we've got to figure out what we're doing." ❌ (GENERIC NONSENSE! You didn't mention ANY specific details from the flyer!)

Question: "How do I get downtown?" (Task: "Meet contact at 3pm", Time: "2:45pm")
✓ GOOD: "The U-Bahn station is two blocks north. Line 3 runs downtown every 15 minutes. It's 2:45 - we could take that if we want to make that 3pm meeting with our contact."
✗ BAD: "We need to hurry." ❌ (Instructing! Use "could" not "need to"!)
✗ BAD: "Take the train." ❌ (Generic! Reference time pressure and task!)

**TONE:** MUST match internal personality: {internal_personality}
- NOT generic "helpful friend" - match the CHARACTER'S personality
- Cynical character = cynical tone
- Optimistic character = optimistic tone
- Analytical character = analytical tone
- etc.

**FORMAT:**
- Use "we", "us", "our" (first person plural)
- **MAXIMUM 1-2 sentences** - Be EXTREMELY concise and focused on what you just perceived
- Natural conversational flow
- **CRITICAL:** Every word must sound like someone who is {internal_personality}
- **CRITICAL:** React ONLY to what you just perceived - no random tangents or unrelated thoughts

**FINAL REMINDER BEFORE YOU RESPOND:**
- Re-read the PERCEPTUAL DESCRIPTION at the top of this prompt
- If it doesn't mention anyone being present, DO NOT talk about asking someone or someone being there
- If it mentions incomplete information (footsteps but can't tell who), use uncertainty words: "could be", "might be", "maybe"
- Your response will be rejected if you contradict or go beyond what perception confirms

**CRITICAL OUTPUT INSTRUCTION:**
DO NOT include ANY reasoning, thinking, analysis, meta-commentary, or explanation.
DO NOT say things like "Let me think...", "Based on...", "Considering...", "This matches...", "Does this..."
DO NOT provide alternatives or options like "Or perhaps..." or "Better option:"
Return ONLY the final internal voice thought - nothing else.
"""

        try:
            # Use centralized robust LLM call with consistent retry logic
            internal_voice = robust_llm_call(
                client=self.client,
                messages=[
                    {"role": "system", "content": "You ARE the character's internal voice. Output ONLY the character's actual thought in first-person plural ('we', 'us', 'our'). DO NOT include reasoning, analysis, alternatives, or meta-commentary. Just output the raw thought directly - 1-2 sentences maximum."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=200,
                max_retries=RetryConfig.CRITICAL_MAX_RETRIES,  # Critical call - more retries
                timeout=30,
                call_name="INTERNAL VOICE"
            )
            
            # CRITICAL: Handle empty LLM response with context-aware fallback
            if not internal_voice:
                print(f"{Color.WARNING}⚠️ Empty response from LLM for internal voice, using fallback{Color.RESET}")
                question_lower = question.lower()
                if "where" in question_lower:
                    return "We're in this place. Need to get our bearings."
                elif "who" in question_lower:
                    return "We're not sure. Hard to remember right now."
                elif "what" in question_lower:
                    return "We're trying to figure that out ourselves."
                elif "how" in question_lower:
                    return "We'll have to think about that."
                else:
                    return "We're not sure. We could look around for more information."
            
            if internal_voice:
                internal_voice = internal_voice.strip('"').strip("'")
                
                # CRITICAL: Filter out meta-commentary that breaks immersion
                meta_phrases = [
                    "Does this match the personality?",
                    "Try:",
                    "It does not",
                    "It does—",
                    "would be more fitting",
                    "better option",
                    "alternative:",
                    "or perhaps:",
                    "more appropriate:"
                ]
                
                # If meta-commentary detected, extract only the actual thought
                for phrase in meta_phrases:
                    if phrase in internal_voice:
                        # Try to extract the clean thought after "Try:" or similar
                        if "Try:" in internal_voice:
                            parts = internal_voice.split("Try:")
                            if len(parts) > 1:
                                internal_voice = parts[1].strip().strip('"').strip("'")
                                break
                        # Otherwise, just return fallback
                        print(f"{Color.WARNING}⚠️ Meta-commentary detected in internal voice, using fallback{Color.RESET}")
                        return "We're not sure. We could look around for more information."
                
                # CRITICAL: Convert any first-person singular to first-person plural
                # This enforces vessel/pilot perspective even if LLM ignores the prompt
                import re
                # Replace I/my/me with we/our/us (case-sensitive, word boundaries)
                internal_voice = re.sub(r'\bI\b', 'We', internal_voice)
                internal_voice = re.sub(r'\bmy\b', 'our', internal_voice)
                internal_voice = re.sub(r'\bme\b', 'us', internal_voice)
                internal_voice = re.sub(r'\bI\'m\b', "We're", internal_voice)
                internal_voice = re.sub(r'\bI\'ve\b', "We've", internal_voice)
                internal_voice = re.sub(r'\bI\'ll\b', "We'll", internal_voice)
                internal_voice = re.sub(r'\bI\'d\b', "We'd", internal_voice)
                
                # Note: robust_llm_call returns string directly, truncation is handled internally
                
                if not internal_voice or len(internal_voice) < 10:
                    return "We're not sure. We could look around for more information."
                
                # CRITICAL: Validate against perceptual description (LLM keeps ignoring instructions)
                if perceptual_description:
                    perception_lower = perceptual_description.lower()
                    voice_lower = internal_voice.lower()
                    
                    # Check if perception indicates no one is present
                    no_one_indicators = ["don't see anyone", "no one", "alone", "empty"]
                    perception_says_no_one = any(indicator in perception_lower for indicator in no_one_indicators)
                    
                    # Check if perception doesn't mention any people at all
                    perception_mentions_people = any(word in perception_lower for word in ["see", "hear", "person", "people", "someone", "figure", "voice", "footstep"])
                    
                    if perception_says_no_one or not perception_mentions_people:
                        # Perception indicates no one is there - check if internal voice claims someone is present
                        presence_patterns = [
                            r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\.\s+(?:He|She|They)\'?(?:s|re)\s+(?:here|there|with)',  # "Name. He's here"
                            r'\b(?:He|She|They)\'?(?:s|re)\s+(?:here|there|the only)',  # "He's here", "She's the only"
                            r'\bwe can (?:trust|ask|tell) (?:him|her|them)\b',  # "we can trust him"
                            r'\b(?:ask|tell|find) [A-Z][a-z]+\b',  # "ask Heinrich"
                        ]
                        
                        for pattern in presence_patterns:
                            if re.search(pattern, internal_voice):
                                print(f"{Color.WARNING}⚠️ HALLUCINATION DETECTED: Perception shows no one present, but internal voice claims someone is there{Color.RESET}")
                                print(f"{Color.WARNING}   Perception: {perceptual_description[:150]}{Color.RESET}")
                                print(f"{Color.WARNING}   Internal Voice (REJECTED): {internal_voice}{Color.RESET}")
                                
                                # Generate context-aware fallback based on the question
                                question_lower = question.lower()
                                if "anyone" in question_lower or "who" in question_lower or "alone" in question_lower:
                                    return "We're alone here. No one else around that we can see or hear."
                                elif "where" in question_lower:
                                    return "We're not sure exactly where we are. No one around to ask."
                                elif "what" in question_lower and ("see" in question_lower or "hear" in question_lower):
                                    return "Nothing unusual. Just the ambient sounds of the place. No people."
                                else:
                                    return "Hard to say. We're alone here, so we'll have to figure it out ourselves."
                
                # Final check: if still contains first-person singular, log warning
                if re.search(r'\b(I|my|me|I\'m|I\'ve|I\'ll|I\'d)\b', internal_voice):
                    print(f"{Color.WARNING}⚠️ First-person singular detected after filter: {internal_voice[:50]}...{Color.RESET}")
                    
                return internal_voice
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Inquiry Internal Voice generation failed: {e}{Color.RESET}")
            return "We don't know. We could ask someone or look around for clues."
    
    def generate_inquiry_factual_answer(
        self,
        user_question: str,
        ua_actor,
        scene_description: str,
        narrative_context: str,
        current_time: Dict[str, Any],
        availability_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate FACTUAL ANSWER to inquiry (memory content, knowledge).
        This generates the actual information that will be revealed in internal voice.
        For memory recall: generates specific names, places, events, details.
        
        Args:
            user_question: The question being asked
            ua_actor: The User Actor asking
            scene_description: Current scene
            narrative_context: Recent events
            current_time: Current time context
            availability_context: Optional dict with 'availability' and 'reasoning'
            
        Returns:
            Factual answer with specific details (2-4 sentences)
        """
        ua_name = ua_actor.sheet.name
        
        # Get RAG worldbuilding context for memory generation
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.BEINGS,
                        WorldbuildingCategory.SUPERNATURAL,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                    ]
                search_query = f"{user_question}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=90,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n**ESTABLISHED WORLDBUILDING (MUST FOLLOW):**\n{rag_context}\n\n"
            except Exception as e:
                # Silently fail - will work without RAG but may be less accurate
                pass
        
        # Get character background
        character_background = f"""
**CHARACTER:** {ua_name}
**AGE:** {ua_actor.sheet.age}
**OCCUPATION:** {ua_actor.sheet.occupation}
**LOCATION:** {ua_actor.sheet.location}
**PERSONALITY:** {ua_actor.sheet.personality_traits.get('internal', 'Thoughtful')}
**GOALS:** {', '.join(ua_actor.sheet.goals[:3]) if hasattr(ua_actor.sheet, 'goals') and ua_actor.sheet.goals else 'None'}
"""
        
        prompt = f"""Generate a FACTUAL ANSWER to this memory recall/inquiry question.
{rag_context}
{character_background}

**QUESTION:** "{user_question}"

**SCENE:** {scene_description[:300]}
**RECENT CONTEXT:** {narrative_context[:300] if narrative_context else "No recent context"}

**YOUR TASK:** Create a specific, detailed answer with CONCRETE DETAILS:
- For "best friend" questions: Generate a SPECIFIC NAME, how they met, when, where, what they're like
- For location questions: Generate a SPECIFIC PLACE NAME, address, description
- For event questions: Generate SPECIFIC DATE, what happened, who was there
- For person questions: Generate SPECIFIC NAME, relationship, details
- For technology questions: Use technology appropriate to the world setting above

**CRITICAL RULES:**
1. Be SPECIFIC - use actual names, dates, places, numbers
2. Make it fit the character's background (age, occupation, location, goals)
3. Make it consistent with the scene and recent context
4. **FOLLOW THE WORLDBUILDING CONTEXT ABOVE** - Use only technology, dates, and cultural references that fit the established setting
5. 2-4 sentences with concrete details
6. This will be passed to internal voice to reveal - make it vivid and memorable

**EXAMPLES:**

Question: "I try to remember my phone"
✓ GOOD: "Our comm device. The one Max handed us at the dockside handoff two seasons back. We've kept it close since. We could use it to coordinate with the crew for tonight's run."

Question: "I try to remember my best friend"
✓ GOOD: "A contact from the underground network. You crossed paths with them during a job two years back at a warehouse district. They shared your methods and your risks. You haven't seen them since, but they were the one who showed you the city's hidden routes."

Question: "Where did I park my car?"
✓ GOOD: "Your vehicle is parked on the side street to the north, about two blocks from here, near the shuttered storefront. You left it there this morning."

Question: "What's my favorite cafe?"
✓ GOOD: "The Blue Horizon Cafe on Boulevard Saint-Germain. You've been going there every Sunday morning for the past three years. Marie, the owner, always saves you the corner table by the window."

✗ BAD: "Your best friend from way back." ❌ (No name! No details!)
✗ BAD: "Someone you used to know." ❌ (Too vague!)
✗ BAD: "A place you like." ❌ (No specific name or location!)

Respond with ONLY the factual answer (no quotes, no preamble)."""

        try:
            if not SUPPRESS_DEBUG:
                print(f"{Color.INFO}[FACTUAL ANSWER] Calling LLM with model: {self.model}{Color.RESET}")
            
            # Use centralized robust LLM call
            answer = robust_llm_call(
                client=self.client,
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.8,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="FACTUAL ANSWER"
            )
            
            if answer:
                answer = answer.strip('"').strip("'")
                if not SUPPRESS_DEBUG:
                    print(f"{Color.SUCCESS}[FACTUAL ANSWER] Generated: {answer[:100]}...{Color.RESET}")
                return answer if answer else "No specific memory available."
            else:
                return "No specific memory available."
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Factual answer generation failed: {e}{Color.RESET}")
            return "No specific memory available."
    
    def generate_inquiry_response(
        self,
        user_question: str,
        ua_actor,
        scene_description: str,
        narrative_context: str,
        current_time: Dict[str, Any],
        availability_context: Optional[Dict[str, Any]] = None,
        nua_actions_context: str = "",
        explicit_movement: bool = False,
        movement_target: Optional[str] = None
    ) -> str:
        """
        Generate PERCEPTUAL narrative for inquiry (physical act of thinking).
        This is NOT the answer - just the physical description of concentrating/thinking.
        The actual answer comes from generate_inquiry_factual_answer.
        
        Args:
            user_question: The question being asked
            ua_actor: The User Actor asking
            scene_description: Current scene (includes NUA actions as [Nearby: ...] lines)
            narrative_context: Recent events
            current_time: Current time context
            availability_context: Optional dict with 'availability' (EXIST/EXIST_NOT_HERE/DOES_NOT_EXIST) and 'reasoning'
            nua_actions_context: Additional NUA context (usually empty - NUA actions are in scene_description)
            
        Returns:
            Narrative answer (2-4 sentences)
        """
        ua_name = ua_actor.sheet.name
        internal_personality = ua_actor.sheet.personality_traits.get("internal", "Thoughtful")
        
        # Check availability context
        availability = availability_context.get('availability') if availability_context else None
        from intent_availability_system import IntentAvailability
        
        # Get character knowledge (inventory with descriptions)
        character_knowledge = ""
        if hasattr(ua_actor.sheet, 'inventory') and ua_actor.sheet.inventory:
            # Include item descriptions for context continuity
            item_details = []
            for item in ua_actor.sheet.inventory[:5]:
                item_name = item.name
                item_desc = getattr(item, 'description', '')
                if item_desc:
                    item_details.append(f"{item_name} ({item_desc})")
                else:
                    item_details.append(item_name)
            character_knowledge += f"Has: {', '.join(item_details)}. "
        
        # Unified guidance - same for ALL availability states
        # The availability only affects backend (memory creation), NOT the narrative output
        availability_guidance = f"""
**CRITICAL - UNIFIED OUTPUT FOR ALL CASES:**
- ONLY describe the PHYSICAL ACT of thinking/concentrating/remembering
- Show the character's body language while thinking (closing eyes, pausing, concentrating, furrowed brow)
- DO NOT describe what they discover, recall, or realize - that's internal voice's job!
- DO NOT describe success or failure of recall - that's internal voice's job!
- DO NOT describe memory clarity or fuzziness - that's internal voice's job!
- Example: "You close your eyes and concentrate, your face tense with effort. You pause, thinking hard."
- The narrative should be IDENTICAL regardless of whether the memory exists or not
"""
        
        # Get RAG worldbuilding context
        rag_context = ""
        if self.rag_system:
            try:
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                    ]
                search_query = f"{user_question} {scene_description[:150]}"
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=90,
                    include_related=True,
                )
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[RAG] Failed to get context: {e}{Color.RESET}")
        
        # Get concrete details to maintain consistency
        concrete_details_context = ""
        if self.narrative_context_manager:
            try:
                # Get all concrete details for current scene to prevent contradictions
                all_details = self.narrative_context_manager.detail_tracker.get_all_active_details_context(
                    scene_id="current",
                    recent_owners=[ua_name]
                )
                if all_details:
                    concrete_details_context = f"""**ESTABLISHED CONCRETE DETAILS (MUST MAINTAIN CONSISTENCY):**
{all_details}

**CRITICAL:** Any information you generate MUST be consistent with the above details.
If the details mention "Studio session at 2pm", do NOT say "6pm".
If the details describe a blue notebook, do NOT say it's red.
"""
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[CONCRETE DETAILS] Failed to get context: {e}{Color.RESET}")
        
        # Get character memories from key memories system
        memory_context = ""
        if self.key_memories_system:
            try:
                # Get relevant memories for this inquiry
                memories = self.key_memories_system.search_memories(
                    query=user_question,
                    character_name=ua_name,
                    max_results=5
                )
                if memories:
                    memory_items = []
                    for mem in memories[:3]:  # Top 3 most relevant
                        memory_items.append(f"- {mem.get('title', 'Memory')}: {mem.get('description', '')[:150]}")
                    memory_context = "**CHARACTER MEMORIES:**\n" + "\n".join(memory_items)
            except Exception as e:
                if not SUPPRESS_DEBUG:
                    print(f"{Color.WARNING}[MEMORIES] Failed to get context: {e}{Color.RESET}")
        
        # Format time context
        time_str = ""
        if current_time:
            time_of_day = current_time.get('time_of_day', 'unknown')
            formatted_time = current_time.get('formatted_time', 'unknown')
            time_str = f"**CURRENT TIME:** {formatted_time} ({time_of_day})"
        
        prompt = f"""Generate a PURELY PERCEPTUAL narrative answer to this inquiry.

**═══════════════════════════════════════════════════════════════════**
**CRITICAL INSTRUCTION #1: DO NOT REPEAT WHAT WAS ALREADY DESCRIBED**
**═══════════════════════════════════════════════════════════════════**

**RECENT CONTEXT (WHAT WAS ALREADY DESCRIBED):**
{narrative_context[:500] if narrative_context else "No recent context"}

**ABSOLUTE RULE:**
- If RECENT CONTEXT already described "amber CRT monitor, climate control hum, antiseptic smell, pneumatic tubes" → DO NOT describe those again
- ONLY describe what's NEW or directly relevant to the question
- Keep response to 1-2 sentences MAXIMUM
- Example: Q: "Is anyone here?" → "You don't see anyone else in the room." ✓ (JUST the answer, nothing else)
- Example: Q: "Is anyone here?" → "Your eyes scan the dimly lit containment lab, taking in the flickering amber CRT monitor..." ✗ WRONG - TOO MUCH!

{concrete_details_context}

**CHARACTER:** {ua_name}
**PERSONALITY:** {internal_personality}
**QUESTION:** "{user_question}"

**CURRENT SCENE (AUTHORITATIVE):** {scene_description}
**CHARACTER KNOWLEDGE:** {character_knowledge if character_knowledge else "Limited knowledge"}
{memory_context if memory_context else ""}
{time_str}

{nua_actions_context if nua_actions_context else ""}

**WORLDBUILDING CONTEXT:**
{rag_context if rag_context else "No additional worldbuilding context available"}

{availability_guidance}

**TASK:** Answer the question with a 2-4 sentence PERCEPTUAL narrative response.

{'**MOVEMENT INSTRUCTION:** The user just moved to "' + str(movement_target) + '". Begin your response by BRIEFLY acknowledging the movement (e.g., "You walk to the ' + str(movement_target) + '.") THEN describe what you perceive. Keep the movement sentence SHORT (5-7 words), then focus on perceptual details.' if explicit_movement and movement_target else ''}

**CONTENT GENERATION STRATEGY:**
When the question involves reading text or hearing audio, you must ACTIVELY GENERATE the specific content:
1. **Use the provided context** - Look at WORLDBUILDING CONTEXT, CHARACTER MEMORIES, RECENT CONTEXT, and SCENE to understand what kind of content makes sense
2. **Be specific and concrete** - Include actual names, places, times, and details (not vague descriptions)
3. **Make it actionable** - Content should give the player something to work with (a location to visit, a person to meet, a clue to follow)
4. **Stay period-appropriate** - Use the WORLDBUILDING CONTEXT to ensure technology, slang, and references fit the time period
5. **Match the medium** - Handwritten notes are informal, flyers are promotional, phone messages are conversational, radio is broadcast-style
6. **CRITICAL - CONTACT INFORMATION REQUESTS:** If the question asks for contact info, phone numbers, addresses, or how to reach someone:
   - **GENERATE ACTUAL CONTACT DETAILS** - phone numbers, addresses, pager numbers, etc.
   - ❌ WRONG: "Marcus called about the mixer" (This is NOT contact info!)
   - ✅ RIGHT: "Marcus - (206) 555-0147. Studio engineer. Lives in Capitol Hill."
   - ✅ RIGHT: "Sarah's number: 555-2891. Pager: 555-CALL. Address: 423 Pine St, Apt 2B."
   - Use period-appropriate formats (landlines, rotary phones, no cell phones or pagers unless worldbuilding allows)
   - Include multiple contact methods if realistic (home phone, work phone, pager, address)

**Example Content Generation:**
- Contact info request → "Marcus - (206) 555-0147 (home), (206) 555-8823 (studio). Pager: 555-BEAT. Address: 1523 Broadway Ave E, Capitol Hill."
- Notebook entry for a DJ → "Day 3 - Setlist: Urban Echoes, Neon Dreams, Aftershock. Marcus called about the mixer issue. Studio session tomorrow at 2pm."
- Phone message → "Hey, it's Sarah. The meeting got moved to Thursday at the warehouse on 5th Street. Bring the samples. Call me back."
- Radio broadcast → "You're listening to KEXP, 90.3 FM. That was Soundgarden with Black Hole Sun. Traffic update: I-5 southbound is backed up near the convention center."
- Flyer text → "UNDERGROUND SHOW - Friday 11pm - The Crocodile Cafe - $5 cover - 21+ - Featuring: Dead Moon, The Gits, Tad"

**CRITICAL - LESS IS MORE (MINIMAL DESCRIPTIONS):**
- **DO NOT re-describe the entire scene** - the scene was already established
- **ONLY describe what's directly relevant** to the specific question/action
- If asking "How far is the exit?" → Just describe spotting the exit sign, nothing else
- If asking "Are there people around?" → Just describe hearing voices or seeing no one, nothing else
- **FORBIDDEN:** Repeating scene details already described (manila folders, ambient smells, background sounds)
- **REQUIRED:** Keep it to 1-2 sentences focused ONLY on answering the specific question
- Examples:
  - Q: "How far is the exit?" → "You spot a red exit sign in the far corner, partially obscured by stacked papers." ✓ FOCUSED
  - Q: "Are there people around?" → "You hear muffled voices from the adjacent office through the thin walls." ✓ FOCUSED
  - ✗ WRONG: "You see stacks of manila folders and paper. The air is thick with ozone and ink. You spot an exit sign..." ← TOO MUCH
- Only describe the scene in full when the user explicitly asks to look around or examine the environment

**CRITICAL RULES:**
1. Use 2nd person ("you") for narrative descriptions
2. **OWNERSHIP DETECTION:** Before describing an object, check CHARACTER KNOWLEDGE inventory. If the object being examined is in the character's inventory, you MUST explicitly state ownership:
   - ✅ "You open YOUR notebook and see YOUR handwritten notes..."
   - ✅ "You flip through the pages of YOUR journal..."
   - ✅ "You examine YOUR production notes..."
   - ❌ "You see the notebook's pages..." (when it's THEIR notebook!)
   - This is CRITICAL for internal voice to recognize familiarity vs. discovering new information
3. ONLY describe what can be DIRECTLY PERCEIVED RIGHT NOW (seen, heard, felt, smelled, tasted)
   - **CRITICAL:** When perceiving TEXT or AUDIO content, you MUST include the ACTUAL WORDS/DIALOGUE
   - Reading text = seeing the actual words written
   - Hearing audio = hearing the actual words spoken
   - DO NOT just describe "you see writing" or "you hear a voice" - include what the writing SAYS or what the voice SAYS
4. **LOCATION CONSISTENCY - NEVER CHANGE SCENES:** You MUST stay in the CURRENT SCENE location described above. DO NOT:
   - Teleport to a different room or location
   - Describe objects/features not mentioned in CURRENT SCENE
   - Change the environment (bedroom → studio, indoor → outdoor, etc.)
   - Add new locations or spaces that weren't in CURRENT SCENE
   - If CURRENT SCENE shows a bedroom, stay in that bedroom
   - If CURRENT SCENE shows a studio, stay in that studio
   - ONLY describe perceptions within the established scene boundaries
5. **CONTINUITY RULE - NEVER TRANSFORM OBJECTS:** If RECENT CONTEXT or CHARACTER KNOWLEDGE mentions a specific object (e.g., "handwritten notebook with setlists"), you MUST maintain that exact object. DO NOT change:
   - Handwritten → Printed
   - Notebook → Book
   - Personal notes → Fiction story
   - Production notes → Novel text
   - The object's physical properties (worn, tattered, yellowed pages are fine - but content type must stay consistent)
6. **MANDATORY - READING/HEARING CONTENT:** If the question involves reading text OR hearing audio:
   - **YOU MUST GENERATE AND INCLUDE THE ACTUAL WORDS** - this is NON-NEGOTIABLE
   - **CREATE the specific content** based on the scene context, character memories, and worldbuilding context
   - Reading a notebook → **INVENT** the actual notebook text in quotes: "Day 1 - Setlist: Urban Echoes..."
   - Hearing a phone message → **INVENT** the actual spoken words in quotes: "Hey Jack, it's Jill. Meet me at the restaurant at 10am."
   - Hearing a radio → **INVENT** what the DJ/announcer is actually saying
   - Reading a flyer → **INVENT** what the flyer actually says
   - **Use the WORLDBUILDING CONTEXT and CHARACTER MEMORIES to make the content relevant and period-appropriate**
   - Make the content specific, concrete, and actionable (names, places, times, details)
   - **NEVER** just say "you see writing" or "you hear a voice" without generating the actual content
   - The words themselves ARE the perceptual data - you're seeing/hearing the actual words
   - MAINTAIN THE CONTENT TYPE from previous context (if it was production notes, keep it production notes)
7. **CONTINUOUS ACTIONS REQUIRE COMPREHENSIVE FEEDBACK:** If the action implies duration or multiple steps (flip through, browse, examine thoroughly, search through):
   - Show MULTIPLE items/pages/entries (not just one)
   - Include TACTILE feedback (texture, weight, temperature)
   - Include AUDITORY feedback (rustling, clicking, scraping sounds)
   - Example: "You flip through the pages. You feel the paper's rough texture, hear the soft rustle. You see multiple entries: 'Day 1 - Setlist...' Next page: 'Day 2 - Studio notes...' Next page: 'Day 3 - Reminder...'"
   - Single snapshot = incomplete perception (reality break)
8. **SPECIAL CASE - TIME QUESTIONS:** If the question asks about time (what time is it, check time, etc.):
   - Describe seeing a clock/watch/device showing the EXACT time from CURRENT TIME context
   - Example: "You see a digital clock on the mixing board. The time is 09:03. The red digits are bright against the dark background."
   - Use the formatted_time from the CURRENT TIME context provided above
9. For MEMORY RECALL questions: ONLY describe the PHYSICAL ACT of thinking (body language, pausing, concentrating)
10. NEVER describe what the character discovers, recalls, or realizes (except for rules #6, #7, and #8) - that's internal voice's job!
11. ABSOLUTELY NO factual knowledge, suggestions, advice, or reasoning
12. NEVER use words like: "recall", "remember", "might", "could", "should", "need to", "try", "maybe"
13. Just describe the raw sensory information in the present moment - NOTHING ELSE

**WHAT TO INCLUDE:**
✓ Present sensory perceptions ONLY: "You see...", "You hear...", "You smell..."
✓ Direct observations NOW: "The room is...", "There are...", "It's..."
✓ Lack of perception: "You don't see...", "You can't hear...", "Nothing visible..."

**WHAT TO EXCLUDE:**
✗ Factual knowledge: "This is your apartment", "You're downtown" (Internal voice's job!)
✗ Suggestions: "you might need to", "you could try", "you should"
✗ Advice: "ask someone", "look for", "try to"
✗ Reasoning: "so you", "therefore", "that means"
✗ Deduction: "this must be", "you deduce", "it seems"
✗ Interpretation: "this is probably", "likely", "appears to be"

**EXAMPLES:**

Question: "Check what time it is" (when CURRENT TIME is "Day 1, 9:03 AM (morning)")
✓ GOOD: "You see a digital clock on the mixing board. The time is 09:03. The red digits are bright against the dark background."
✗ BAD: "You glance at your watch." ❌ (Doesn't show the actual time!)
✗ BAD: "It's morning." ❌ (Too vague - must show exact time!)

Question: "Read the notebook entries"
✓ GOOD: "You see a worn notebook with handwritten entries. The first page reads: 'Day 47 - Need to check the back door before tonight's meeting. Community safety is my responsibility. Can't let them down again.' The ink is dark blue, slightly smudged."
✗ BAD: "You see handwritten text in the notebook." ❌ (Doesn't include the actual text!)
✗ BAD: "The notebook contains your thoughts about community safety." ❌ (Interpretation, not the raw text!)

Question: "Keep reading" or "Flip through" (when RECENT CONTEXT shows player was reading a handwritten notebook with setlists)
✓ GOOD (COMPLETE): "You flip through the pages. You feel the paper's rough texture, hear the soft rustle of turning pages. You see multiple entries: 'Day 1 - Setlist: Urban Echoes, Neon Dreams, Aftershock.' Next page: 'Day 2 - Studio notes: Track 3 needs more bass. Gain +3dB.' Next page: 'Day 3 - Reminder: Call Marcus about the mixer.' The handwriting varies from rushed to careful. Some pages have coffee stains."
✗ BAD (INCOMPLETE): "You turn the page. The next entry reads: 'Day 1 - Studio session notes: Track 3 needs more bass.' The handwriting is rushed but legible." ❌ (Only shows ONE entry when "flip through" implies MULTIPLE pages!)
✗ BAD (NO TACTILE): "You see the next entry: 'Day 2 - Studio notes.'" ❌ (Missing tactile/auditory feedback - no paper texture, no sound of pages!)
✗ BAD (CONTINUITY BREAK): "You see a worn book with a tattered cover. The printed text reads: 'Turn the page and keep reading. The story of love and loss continues.'" ❌ (CRITICAL ERROR: Transformed handwritten notebook into printed book! Changed production notes into fiction!)

Question: "Find Marcus's contact info" or "Look for Marcus's number"
✓ GOOD: "You flip through YOUR notebook. You see an entry: 'Marcus - (206) 555-0147 (home), (206) 555-8823 (studio). Pager: 555-BEAT. Studio engineer, lives in Capitol Hill.' The handwriting is yours."
✗ BAD: "You see a note: 'Marcus called about the mixer. Studio session tomorrow at 2pm.'" ❌ (This is NOT contact info - no phone number, no address!)
✗ BAD: "You find information about Marcus." ❌ (Too vague - must show actual contact details!)

Question: "Read the flyer"
✓ GOOD: "You see a bright red flyer: 'UNDERGROUND RAVE - Tonight at midnight - Warehouse District - Bring your own energy.' The text is printed in bold black letters."
✗ BAD: "You see a flyer about a rave." ❌ (Doesn't include the actual text!)

Question: "Listen to the answering machine" or "Check messages"
✓ GOOD: "You press play. You hear a man's voice: 'Hey Jack, it's Marcus. Meet me at Tony's Diner at 10am tomorrow. Got something important to discuss. Don't be late.' The machine beeps."
✗ BAD: "You hear a message from someone asking you to meet them." ❌ (Doesn't include the actual words!)
✗ BAD: "The answering machine plays a message." ❌ (Doesn't include what the message says!)

Question: "What's on the radio?"
✓ GOOD: "You hear the DJ's voice: 'That was Nirvana with Smells Like Teen Spirit. Coming up next, we've got Pearl Jam. Stay tuned to KEXP, Seattle's alternative rock station.' Static crackles between words."
✗ BAD: "You hear music playing on the radio." ❌ (Doesn't include what's actually being said!)
✗ BAD: "The DJ announces the next song." ❌ (Doesn't include the actual announcement!)

Question: "Where am I?"
✓ GOOD: "You see a cluttered room. Vinyl records stacked everywhere. An answering machine blinking in the corner. The air smells of stale cigarettes and cold pizza."
✗ BAD: "This is your apartment." ❌ (Factual knowledge - internal voice's job!)
✗ BAD: "You might need to ask someone or look for a sign." ❌ (Suggestion!)

Question: "What's the best way to get downtown?"
✓ GOOD: "You look around. You see a street sign pointing north. Traffic flows steadily in both directions."
✗ BAD: "You're on Main Street." ❌ (Factual knowledge - internal voice's job!)
✗ BAD: "You should take the U-Bahn, it's faster." ❌ (Suggestion!)

Question: "Where can I find spare parts?"
✓ GOOD: "You scan the area. Industrial buildings line the street. You don't see any obvious shops or stores nearby."
✗ BAD: "There's a junkyard three blocks east." ❌ (Factual knowledge - internal voice's job!)
✗ BAD: "The junkyard is your best bet." ❌ (Advice!)

Question: "Who is that person?"
✓ GOOD: "You don't recognize them. They're wearing a dark jacket and watching the building entrance. Their face is unfamiliar."
✗ BAD: "That's your neighbor." ❌ (Factual knowledge - internal voice's job!)
✗ BAD: "You should approach and ask." ❌ (Suggestion!)

Question: "I try to remember my best friend"
✓ GOOD: "You pause and close your eyes, concentrating. Your brow furrows slightly as you think."
✗ BAD: "As you delve into the recesses of your memory, a name and a face begin to coalesce. The first name, 'Reyna', emerges from your thoughts." ❌ (Memory content - internal voice's job!)
✗ BAD: "You recall your old contact from the warehouse district." ❌ (Memory content - internal voice's job!)

**ABSOLUTELY FORBIDDEN PHRASES:**
❌ "you recall" (Memory - internal voice!)
❌ "you remember" (Memory - internal voice!)
❌ "you've seen" (Memory - internal voice!)
❌ "you know" (Memory - internal voice!)
❌ "emerges from your thoughts" (Memory - internal voice!)
❌ "surfaces" (Memory - internal voice!)
❌ "coalesces" (Memory - internal voice!)
❌ "a name and face" (Memory content - internal voice!)
❌ "delve into" (Memory - internal voice!)
❌ "recesses of your memory" (Memory - internal voice!)
❌ "you might need to" (Suggestion!)
❌ "you could try" (Suggestion!)
❌ "you should" (Advice!)
❌ "maybe you" (Suggestion!)
❌ "try to" (Advice!)
❌ "look for" (Advice!)
❌ "ask someone" (Advice!)
❌ "find out" (Advice!)
❌ "check if" (Advice!)

**REQUIREMENTS:**
- 2-4 sentences MAXIMUM
- Use "you" perspective
- ONLY raw sensory perceptions in the present moment
- ZERO memories, suggestions, reasoning, or advice
- If you don't perceive something, just say "You don't see..." or "You can't tell..."

**CRITICAL OUTPUT INSTRUCTION:**
DO NOT include ANY reasoning, thinking, analysis, or explanation.
DO NOT say things like "Let me think..." or "Based on..." or "Considering..."
Return ONLY the final perceptual description text - nothing else.
"""

        try:
            # Use centralized robust LLM call with consistent retry logic
            answer = robust_llm_call(
                client=self.client,
                messages=[
                    {"role": "system", "content": "You generate perceptual descriptions. Output ONLY the final description text. DO NOT include reasoning, thinking, or explanations. Just output the description directly."},
                    {"role": "user", "content": prompt}
                ],
                model=self.model,
                temperature=0.6,
                max_tokens=300,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=30,
                call_name="PERCEPTUAL"
            )
            
            if answer:
                answer = answer.strip('"').strip("'")
                if answer and len(answer) >= 20:
                    return answer
            
            print(f"{Color.WARNING}⚠️ Empty perceptual response, using fallback{Color.RESET}")
            return "You pause and take in your surroundings, trying to get your bearings."
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Inquiry response generation failed: {e}{Color.RESET}")
            return "You pause and take in your surroundings, trying to get your bearings."
    
    def generate_nua_action_perceptual_narrative(
        self,
        actor: Actor,
        action_data: Dict[str, Any],
        scene_description: str,
        is_proactor: bool = True,
        is_remote_encounter: bool = False,
        remote_encounter_type: str = None,
        session_id: str = None
    ) -> str:
        actor_name = actor.sheet.name
        action_description = action_data.get('action_description', action_data.get('narrative_description', 'acts'))
        
        role_label = "proactive action" if is_proactor else "reaction"
        
        # Add remote encounter context if applicable
        remote_context = ""
        if is_remote_encounter:
            if remote_encounter_type == "phone_call":
                remote_context = f"""
**🚨 CRITICAL CONTEXT: PHONE CONVERSATION 🚨**
This is a PHONE CALL. {actor_name} is NOT physically present with the other person.
- Describe ONLY what can be perceived over the phone: voice, tone, words, background sounds
- ABSOLUTELY FORBIDDEN: "approaches", "walks", "gestures", "lean", "hands", "facial expressions", "eyes", "smile", "nod", "body language"
- Focus on: What they SAY (quoted dialogue), how they SOUND (tone, emotion in voice), what you HEAR in background
- CORRECT FORMAT: "'{actor_name} says '[words]' in a [tone] voice"
- WRONG FORMAT: "says '[words]' while [any physical action]"
"""

        spatial_facts_context = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_context = f"""

**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{sf.strip()}
"""
        except Exception:
            spatial_facts_context = ""
        
        prompt = f"""Generate a PERCEPTUAL DESCRIPTION of {actor_name}'s {role_label}.

**SCENE:**
{scene_description[:300]}
{spatial_facts_context}
{remote_context}
**ACTION DECISION:**
{action_description}

**YOUR TASK:**
Transform this action decision into an immersive, perceptual narrative description.

**REQUIREMENTS:**
1. **Actor name FIRST** - ALWAYS start with "{actor_name}" at the beginning
2. **Third person perspective** - Use "{actor_name}" and "he/she/they"
3. **Perceptual details** - What you SEE, HEAR, and observe
4. **Physical actions** - Describe body language, movements, expressions (UNLESS this is a phone call)
5. **Quoted dialogue** - If this is dialogue, include the EXACT WORDS in quotes
6. **NO meta-gaming** - NO mentions of skills, stats, success levels, or game mechanics
7. **Present tense** - Describe what is happening NOW

**DIALOGUE FORMAT (MANDATORY - if applicable):**
- CORRECT: "{actor_name} says '[exact words]' [optional: while/with physical action]"
- Example: "Eva says 'There's this underground rave tonight—you should come!' with her eyes bright with excitement."
- Example (phone): "Marcus says 'I've been thinking about that project' in an enthusiastic voice."
- WRONG: "'[words]' {actor_name} says" (actor name must come FIRST!)
- WRONG: "says '[words]' while..." (missing actor name at start!)

**PHYSICAL ACTION FORMAT (if applicable):**
- Start with actor name: "{actor_name} lunges forward, knife gleaming in the dim light."

**FORBIDDEN:**
- ❌ "initiates a", "employs", "registers as", "attempt at"
- ❌ Any UTAS terminology or game mechanics
- ❌ Success/failure outcomes (just the attempt)

Generate ONLY the perceptual narrative (1-2 sentences, no preamble)."""

        try:
            # Use centralized robust LLM call
            narrative = robust_llm_call(
                client=self.client,
                messages=[
                    {
                        "role": "system",
                        "content": "You generate immersive, perceptual narrative descriptions of character actions. Use third person, present tense, sensory details, and quoted dialogue when appropriate. NEVER use game mechanics terminology."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="NUA NARRATIVE"
            )
            
            if narrative:
                narrative = narrative.strip('"').strip("'").strip()

                # Some models occasionally echo the prompt template ("YOUR TASK", "REQUIREMENTS", etc.).
                # Detect and reject those responses so they never reach the output log.
                upper = narrative.upper()
                template_markers = (
                    "YOUR TASK",
                    "REQUIREMENTS",
                    "ACTION DECISION",
                    "DIALOGUE FORMAT",
                    "FORBIDDEN",
                    "GENERATE ONLY",
                    "CRITICAL",
                )
                if any(m in upper for m in template_markers):
                    narrative = ""

                if narrative:
                    try:
                        narrative = self._fix_narrative_issues(
                            narrative=narrative,
                            actor_name=actor_name,
                            is_remote=is_remote_encounter,
                            remote_type=remote_encounter_type,
                        )
                    except Exception:
                        pass

                # Ensure we don't leak instruction text even after post-processing.
                if narrative:
                    upper2 = narrative.upper()
                    if any(m in upper2 for m in template_markers):
                        narrative = ""

                if narrative:
                    # Enforce "actor name first" for NUA (unless it's a phone post-process override).
                    try:
                        if not narrative.lower().startswith(actor_name.lower()):
                            narrative = f"{actor_name} {narrative}".strip()
                    except Exception:
                        pass

                if narrative:
                    return narrative

            # Minimal safe fallback (avoid raw prompt leakage).
            if is_remote_encounter and remote_encounter_type == "phone_call":
                return f"{actor_name} speaks over the phone." 
            return f"{actor_name} moves to {role_label}."
                
        except Exception as e:
            print(f"{Color.WARNING}⚠️ NUA narrative generation failed: {e}{Color.RESET}")
            return action_description

    def generate_ua_action_perceptual_narrative(
        self,
        *,
        user_input: str,
        scene_description: str,
        is_remote_encounter: bool = False,
        remote_encounter_type: str = None,
        session_id: str = None
    ) -> str:
        """Create a clean UA attempt narration without acting on behalf of the user.

        This is a paraphrase-only rewrite of the user's input into second-person narration.
        It MUST NOT add actions, outcomes, facts, or dialogue.
        """
        raw = (user_input or '').strip()
        if not raw:
            return "You act."

        remote_context = ""
        if is_remote_encounter and remote_encounter_type == "phone_call":
            remote_context = """
This is a PHONE CALL. You are NOT physically present with the other person.
- Output MUST NOT include any physical proximity actions (approach, touch, gesture, smile, nod, etc.).
- Prefer describing ONLY what you SAY and what can be heard.
""".rstrip()

        spatial_facts_context = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_context = f"""

AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):
{sf.strip()}
""".rstrip()
        except Exception:
            spatial_facts_context = ""

        prompt = f"""Rewrite the USER'S ACTION into a short, perceptual narration.

SCENE:
{(scene_description or '')[:300]}
{spatial_facts_context}
{remote_context}

USER'S ACTION (authoritative, do not change intent):
{raw}

RULES (HARD):
- Output MUST start with "You".
- Output MUST be a paraphrase of the user's action ONLY. Do NOT add any new actions, steps, outcomes, motives, or facts.
- If the user's action contains quoted dialogue (\"...\" or '...'), you MUST preserve the exact quoted text verbatim.
- Do NOT add new dialogue if none exists.
- Do NOT add NPC names.
- 1 sentence preferred, at most 2 short sentences.

Return ONLY the final narration text."""

        try:
            out = robust_llm_call(
                client=self.client,
                messages=[
                    {
                        "role": "system",
                        "content": "You rewrite user actions into concise second-person perceptual narration. Never invent actions or dialogue. Preserve quoted dialogue verbatim. Output only the narration.",
                    },
                    {"role": "user", "content": prompt},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=120,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="UA NARRATIVE",
            )
            out_s = (out or '').strip().strip('"').strip("'")
            if out_s.lower().startswith('you') and len(out_s) >= 6:
                return out_s
        except Exception:
            pass

        # Deterministic fallback: minimal pronoun rewrite only.
        low = raw.lower()
        if low.startswith('i '):
            return "You " + raw[2:].lstrip()
        if low.startswith("i'm "):
            return "You are " + raw[4:].lstrip()
        if low.startswith('im '):
            return "You are " + raw[3:].lstrip()
        if low.startswith("i'd "):
            return "You would " + raw[4:].lstrip()
        if low.startswith("i'll "):
            return "You will " + raw[4:].lstrip()
        return raw if low.startswith('you') else f"You {raw}"

    def _fix_narrative_issues(self, narrative: str, actor_name: str, is_remote: bool, remote_type: str) -> str:
        """Post-process narrative to fix common issues."""
        import re
        
        # Fix 1: Ensure actor name comes first if it starts with "says" or dialogue
        if narrative.startswith("says ") or narrative.startswith("'") or narrative.startswith('"'):
            # Extract the dialogue if present
            dialogue_match = re.match(r'^["\'](.+?)["\']', narrative)
            if dialogue_match:
                dialogue = dialogue_match.group(1)
                rest = narrative[dialogue_match.end():].strip()
                # Rebuild with actor name first
                narrative = f"{actor_name} says '{dialogue}'"
                if rest and not rest.startswith("says"):
                    narrative += f" {rest}"
            elif narrative.startswith("says "):
                # Just prepend actor name
                narrative = f"{actor_name} {narrative}"
        
        # Fix 2: Phone calls - strip physical actions, keep only dialogue
        if is_remote and remote_type == "phone_call":
            # Extract dialogue and strip any physical actions
            # Use [^"']+ to match everything except quotes (greedy within quotes)
            dialogue_match = re.search(r'says\s+(["\'])([^"\']+)\1', narrative, re.IGNORECASE)
            
            if dialogue_match:
                dialogue_text = dialogue_match.group(2)  # group(2) is the dialogue content
                # Rebuild with ONLY dialogue, no physical actions
                narrative = f"{actor_name} says \"{dialogue_text}\" over the phone."
            else:
                # No dialogue found - invalid for phone call
                print(f"{Color.WARNING}[POST-PROCESS] Phone call missing dialogue: '{narrative}' - DeciderAgent prompt failed!{Color.RESET}")
                narrative = f"{actor_name} speaks over the phone."
        
        return narrative
    
    def generate_does_not_exist_narrative(
        self,
        user_intent: str,
        ua_actor,
        scene_description: str,
        narrative_context: str,
        current_time: Dict[str, Any],
        reasoning: str
    ) -> str:
        """
        Generate perceptual narrative explaining WHY something doesn't exist.
        
        This is for DOES_NOT_EXIST cases where the user tries to go somewhere or do something
        that doesn't exist in the world. The narrative should diegetically explain why it's not possible.
        
        Args:
            user_intent: What the user tried to do (e.g., "I head to the nearest diner")
            ua_actor: The User Actor
            scene_description: Current scene
            narrative_context: Recent events
            current_time: Current time context
            reasoning: System reasoning for why it doesn't exist
            
        Returns:
            Perceptual narrative explaining the absence (2-4 sentences)
        """
        ua_name = ua_actor.sheet.name
        
        # Format time context
        time_str = ""
        if current_time:
            time_of_day = current_time.get('time_of_day', 'unknown')
            formatted_time = current_time.get('formatted_time', 'unknown')
            time_str = f"**CURRENT TIME:** {formatted_time} ({time_of_day})"
        
        prompt = f"""Generate a PERCEPTUAL narrative that diegetically explains why something doesn't exist.

**CHARACTER:** {ua_name}
**WHAT THEY TRIED TO DO:** "{user_intent}"
**CURRENT SCENE:** {scene_description}
**RECENT CONTEXT:** {narrative_context[:500] if narrative_context else "No recent context"}
{time_str}

**SYSTEM REASONING (for context only):** {reasoning}

**YOUR TASK:**
Generate a 2-4 sentence perceptual narrative that explains WHY this action isn't possible.

**CRITICAL REQUIREMENTS:**
1. **Explain the ABSENCE** - Don't describe the current scene, explain why the target doesn't exist
2. **Be DIEGETIC** - Make it feel natural, not like a system message
3. **Be SPECIFIC** - Don't just say "you don't see it", explain WHY it's not there
4. **Use OBSERVATION** - Describe what you DO see that confirms the absence

**EXAMPLES:**

❌ WRONG (describes current scene):
"You see a payphone in the corner. The ringing is constant."

✅ CORRECT (explains absence):
"You scan the industrial area around you. There are no diners in sight—just warehouses, auto shops, and empty lots. This part of town is all business, no food."

❌ WRONG (vague):
"You don't see any diners nearby."

✅ CORRECT (specific):
"You step outside and look around. The neighborhood is residential—houses, apartments, a corner store. No restaurants or diners on this block. You'd have to head downtown for that."

❌ WRONG (meta/system):
"That location doesn't exist in the current scene."

✅ CORRECT (diegetic):
"You check your mental map of the area. There used to be a diner on 5th Street, but it closed down months ago. The nearest one now is probably downtown, at least a 15-minute drive."

**TONE:** Observational, matter-of-fact, slightly disappointed but practical

Generate ONLY the perceptual narrative (2-4 sentences, no preamble)."""

        try:
            # Re-apply the stronger system-role instruction for this special-case narrative,
            # but keep the same enhancement pipeline (continuity facts + narrative context + RAG + time).
            try:
                from persistent_context_manager import get_context_manager
                cm = get_context_manager()
                if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                    facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                    if facts_block and isinstance(prompt, str) and prompt.strip():
                        prompt = f"{facts_block}\n\n{prompt}"
            except Exception:
                pass

            enhanced_prompt = self._enhance_prompt_with_narrative_context(prompt)
            enhanced_prompt = self._enhance_prompt_with_rag(enhanced_prompt)
            enhanced_prompt = self._enhance_prompt_with_time_context(enhanced_prompt, current_time)

            narrative = robust_llm_call(
                client=self.client,
                messages=[
                    {
                        "role": "system",
                        "content": "You generate immersive, diegetic narratives that explain why things don't exist in the world. Focus on observation and absence, not the current scene."
                    },
                    {"role": "user", "content": enhanced_prompt}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=200,
                max_retries=RetryConfig.MAX_RETRIES,
                timeout=20,
                call_name="DOES_NOT_EXIST"
            )

            if narrative:
                narrative = narrative.strip('"').strip("'")
                return narrative if narrative else f"You look around, but you don't see what you're looking for."
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Does-not-exist narrative generation failed: {e}{Color.RESET}")
            return f"You look around, but you don't see what you're looking for."

    def generate_exit_crossing_narration(
        self,
        actor_name: str,
        scene_description: str,
        exit_name: str,
        destination_name: str,
        time_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate 2-3 sentence narration of walking to and crossing through an exit.

        This covers the physical act of leaving the current room — the last steps
        through the space and the moment of crossing the threshold. It does NOT
        describe what's on the other side; that comes from the new scene description.
        """
        prompt = f"""Describe {actor_name} leaving a room — the physical act of crossing the space to the exit and stepping through it.

**Current Room (what they are leaving):**
{scene_description[:400] if scene_description else "An interior space"}

**Exit:** {exit_name}
**Destination beyond:** {destination_name}

**WRITE EXACTLY LIKE THESE EXAMPLES — SHORT, PHYSICAL, STOPS AT THE THRESHOLD:**
✓ "You move past the portable terminal toward the door at the far end. The handle is cold. You push through."
✓ "The compliance hum is louder near the vent as you cross to the exit. The door swings open with a low hiss and you step through."
✓ "You thread between the field cots. The air smells of recycled coolant. You reach the door and go."
✓ "The floor is smooth under your boots. You catch the sharp tang of ozone as you reach the exit and push through."

**RULES — NO EXCEPTIONS:**
- 2-3 short sentences. As clipped as the examples above.
- Weave ONE sensory detail naturally into the movement — a smell, a sound, a texture underfoot or in hand. Not a standalone sentence, part of the motion.
- End on the act of going through — not what's beyond it
- NO sensory lists. NO separate "you hear... you smell... you see..." chains.
- Sensory detail is incidental, caught in passing — not the focus.

Generate ONLY the narrative, no additional text:"""

        try:
            response = self._call_llm(prompt, time_context=time_context)
            if response:
                return response.strip().strip('"').strip("'")
            return f"You cross to the {exit_name} and step through into the {destination_name}."
        except Exception as e:
            return f"You cross to the {exit_name} and step through into the {destination_name}."

    def generate_travel_departure_narrative(
        self,
        actor_name: str,
        origin: str,
        destination: str,
        travel_time_minutes: int,
        current_time: str
    ) -> str:
        """Generate a narrative description of beginning a journey."""
        try:
            # Get spatial context for accurate departure description
            spatial_context = ""
            try:
                from agents.spatial_context_helper import get_spatial_context_for_prompt
                spatial_context = get_spatial_context_for_prompt(proactor_name=actor_name, max_obstacles=10, include_sensory=False)
            except Exception:
                pass
            
            prompt = f"""Generate a brief (2-3 sentences) perceptual narrative describing {actor_name} beginning their journey to {destination}.

**Current Scene:**
{origin}

{spatial_context}

**Destination:** {destination}
**Travel Time:** {travel_time_minutes} minutes
**Current Time:** {current_time}

{self.SENSORY_PERCEPTION_REQUIREMENTS}

**DEPARTURE-SPECIFIC INSTRUCTIONS:**
- Describe preparing to leave: gathering belongings, checking time, moving toward exit
- Describe first steps of departure: opening door, stepping outside, transitioning from interior to exterior
- Layer 2-3 different senses (sight, sound, touch/feel)
- Keep it brief (2-3 sentences maximum)
- DO NOT describe the entire journey - ONLY the moment of departure
- Focus on the transition from current location to beginning the journey

**EXAMPLES:**
✓ "You see the door swing open, revealing the street beyond. You feel the cool evening air hit your face. You hear the distant hum of traffic."
✓ "You hear the door click shut behind you. You see the sidewalk stretch ahead toward the main street. You feel your footsteps quicken."

Generate ONLY the narrative description, no additional text:"""

            response = self._call_llm(prompt)
            narrative = response.strip().strip('"').strip("'")
            return narrative if narrative else f"You prepare to leave for {destination}."
            
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Travel departure narrative generation failed: {e}{Color.RESET}")
            return f"You prepare to leave for {destination}."
    
    def generate_travel_internal_voice(
        self,
        actor_name: str,
        destination: str,
        reason: str,
        current_goals: list
    ) -> str:
        """Generate internal thoughts about beginning a journey."""
        try:
            goals_text = "\n".join([f"- {goal}" for goal in current_goals]) if current_goals else "No specific goals"
            
            prompt = f"""Generate a brief (1-2 sentences) internal monologue for {actor_name} as they begin traveling to {destination}.

**Why they're going:** {reason}
**Current Goals:**
{goals_text}

**Instructions:**
- Reflect on why they're making this journey
- Consider how it relates to their goals
- Keep it brief and introspective
- Use first-person plural ("We...")
- Focus on motivation, anticipation, or purpose
- DO NOT describe physical actions

Generate ONLY the internal thoughts, no additional text:"""

            response = self._call_llm(prompt)
            thoughts = response.strip().strip('"').strip("'")
            return thoughts if thoughts else None
            
        except Exception as e:
            print(f"{Color.WARNING}⚠️ Travel internal voice generation failed: {e}{Color.RESET}")
            return None

    def refine_scene_with_population(self, scene_description: str, new_actors: list, background_atmosphere: str = None) -> str:
        """
        Rewrites the scene description to naturally include the newly populated NPCs and background atmosphere.
        Crucially, it strictly filters out 'hidden' actors so the description remains perceptual.
        """
        # Filter out hidden actors (Perceptual Describer Rule)
        visible_actors = [a for a in new_actors if not getattr(a, 'is_hidden', False)]
        
        if not visible_actors and not background_atmosphere:
            return scene_description
            
        actor_details = []
        for actor in visible_actors:
            desc = f"- {actor.sheet.name} ({actor.sheet.occupation})"
            if hasattr(actor.sheet, 'goals') and actor.sheet.goals:
                 # Hint at what they are doing based on their goal
                 desc += f" [Activity Hint: {actor.sheet.goals[0]}]"
            actor_details.append(desc)
            
        actors_text = "\n".join(actor_details) if actor_details else "No specific individuals visible."
        atmosphere_text = background_atmosphere if background_atmosphere else "No specific background crowd."
        
        prompt = f"""
        Refine this scene description to naturally integrate the people who are present.
        
        **ORIGINAL SCENE:**
        {scene_description}
        
        **FOREGROUND INDIVIDUALS (VISIBLE):**
        {actors_text}
        
        **BACKGROUND ATMOSPHERE:**
        {atmosphere_text}
        
        **INSTRUCTIONS:**
        1. **Integrate Naturally:** Woven the visible individuals and the background crowd into the scene description.
           - Example: "You enter the noisy classroom (Atmosphere). You see Mr. Harrison writing on the board (Foreground)."
        2. **Maintain Perspective:** Use SECOND PERSON ACTIVE PERCEPTION ("You see...", "You hear...").
        3. **Perceptual Only:** Only describe what is listed above. Do not invent extra people.
        4. **Setting First:** Keep the original setting details (lighting, smell, layout) intact, just populate it.
        5. **Concise:** Add 1-3 sentences max to the existing description.
        
        Respond with ONLY the updated scene description paragraph.
        """
        
        try:
            response = self._call_llm(prompt)
            refined_scene = response.strip().strip('"').strip("'")
            return refined_scene if refined_scene else scene_description
        except Exception as e:
            print(f"{Color.WARNING}Scene refinement failed: {e}{Color.RESET}")
            return scene_description
