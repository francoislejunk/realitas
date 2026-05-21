"""
Internal Voice Creator Agent

Generates the actual internal voice content based on the interpretation.
This agent creates the internal monologue that is ALWAYS present in both
Roam and Exchange modes.

Four Functions:
1. MEMORY - Recall/create memories based on triggers
2. COMMENT - Personality-driven flavor comments
3. SOLUTION - Suggest actions for predicaments
4. INFORMATION - Answer questions (logic or conceptual)

Design Philosophy:
- Internal voice is ALWAYS present (never silent)
- Personality (OCEAN, MBTI, Mood) MUST be evident
- Never repeat wording - track used phrases
- Functions should not repeat back-to-back without reason
- Voice urgency matches mood (frantic, calm, etc.)
"""

import logging
import random
import os
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
from pathlib import Path

from openrouter_config import create_role_client, OpenRouterConfig, robust_llm_call, RetryConfig
from json_utils import extract_and_parse_json
from color_utils import Color

from .internal_voice_interpreter_agent import (
    InternalVoiceFunction,
    QuestionType,
    VoiceInterpretation
)

try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except ImportError:
    WorldbuildingCategory = None

from rag_lock_utils import get_multi_category_context_for_llm


# Memory categories with at least 2 starter memories each (setting-agnostic)
MEMORY_CATEGORIES = {
    "family": [
        "Your mother's warm smile in a moment of comfort",
        "Your father teaching you something important"
    ],
    "past_life": [
        "Your first day learning your craft, nervous but eager",
        "The satisfaction of mastering a difficult skill"
    ],
    "friends": [
        "Long nights talking with your closest companion",
        "A journey that went terribly wrong"
    ],
    "trauma": [
        "The event that changed everything",
        "A betrayal you never saw coming"
    ],
    "achievement": [
        "The moment you proved your worth",
        "Winning something you trained hard for"
    ],
    "relationship": [
        "Your first true love",
        "A heartbreak that took a long time to heal"
    ],
    "location": [
        "The place where you grew up",
        "A place that always felt like home"
    ],
    "childhood": [
        "Days that seemed to last forever",
        "A keepsake or object you treasured"
    ],
    "education": [
        "A mentor who believed in you",
        "A lesson learned the hard way"
    ],
    "loss": [
        "Someone you miss deeply",
        "Something precious that was taken from you"
    ],
    "secret": [
        "Something you've never told anyone",
        "A truth you keep hidden"
    ],
    "regret": [
        "A choice you wish you could take back",
        "Words left unspoken"
    ]
}


class InternalVoiceCreatorAgent:
    """Creates internal voice content based on interpretation.

    Key Responsibilities:
    1. Generate appropriate content for each function
    2. Ensure personality is ALWAYS evident
    3. Prevent repetition of wording
    4. Match urgency to mood
    5. Create/recall memories as needed
    """

    def _build_soft_grounding_rules(
        self,
        *,
        scene_description: str,
        worldbuilding_context: str = "",
        available_memories: Optional[List[str]] = None,
    ) -> str:
        continuity_facts_text = ""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                continuity_facts_text = cm.get_continuity_facts_for_llm(max_facts=8) or ""
        except Exception:
            continuity_facts_text = ""
        memories_text = "\n".join([f"- {m}" for m in (available_memories or [])[:6]])
        return f"""
**SOFT GROUNDING RULES (CRITICAL):**
Internal voice may suggest next steps and hypotheses, but must stay rooted in provided context.

Allowed:
- Plans and suggestions phrased as intentions ("you should...", "you could...", "maybe try...")
- Hypotheses phrased with uncertainty ("maybe", "might", "could be")

Forbidden:
- Asserting new facts about the world as true unless supported by SCENE/WORLDBUILDING/MEMORIES
- Introducing new named places/organizations/systems/items as factual (e.g., a specific "guild station") unless present in context

Additional forbidden (common contradiction sources):
- Do NOT assert relative spatial facts like "above", "below", "upstairs", "downstairs", "one level down" unless that relationship is explicitly present in CONTINUITY FACTS or the SCENE.
- Do NOT assert a person's exact location (e.g., "Matteo is in the archive") unless supported by CONTINUITY FACTS, MEMORIES, or the SCENE.
- Do NOT claim "near X" / "from where we stand near X" unless X is the CLOSEST landmark/feature mentioned in AUTHORITATIVE SPATIAL FACTS. If multiple landmarks are listed with distances, use the smallest-distance landmark (or avoid "near" phrasing entirely).
- Do NOT suggest repeating an action the SCENE already shows as completed (e.g., if the SCENE says you squeezed past rubble onto a higher step, do not propose "clear the rubble to get up" as the immediate next step).
- Do NOT invent environment/object states (e.g., "the forge is already active", "someone is waiting", "the door is unlocked") unless supported by SCENE, AUTHORITATIVE SPATIAL FACTS, MEMORIES, or CONTINUITY FACTS.
- If unsure, you MUST hedge: "maybe", "might", "not sure", "could be".

If you need to mention something not confirmed, keep it generic and uncertain ("someone", "somewhere", "a place to ask").

**SCENE (authoritative):**
{(scene_description or '')[:400]}

**WORLDBUILDING (authoritative excerpt):**
{(worldbuilding_context or '')[:400] if worldbuilding_context else 'None'}

**MEMORIES (authoritative excerpt):**
{memories_text if memories_text else 'None'}

**CONTINUITY FACTS (authoritative anchors):**
{(continuity_facts_text or 'None')[:800]}
"""

    def _find_ungrounded_proper_nouns(
        self,
        voice_text: str,
        *,
        allowed_context: str,
    ) -> List[str]:
        try:
            import re
        except Exception:
            return []

        vt = (voice_text or "").strip()
        if not vt:
            return []

        ctx_l = (allowed_context or "").lower()
        if not ctx_l:
            return []

        # Systemic soft grounding policy:
        # - Do NOT police single capitalized tokens (names, demonyms, titles) because
        #   they are extremely common in personal memories and cause false positives.
        # - Instead, only flag specific-seeming multi-word proper-noun phrases
        #   (e.g. "Order of X", "House Y", "Saint Z Cathedral") when not grounded.
        #
        # We still keep entity-phrase heuristics elsewhere for non-capitalized constructs.
        # Here we flag *specific-seeming* named entities, including those with common
        # lowercase connectors (e.g., "Order of X", "House de Y").
        phrase_patterns = [
            # Consecutive capitalized tokens: "Ashwood Abbey", "Loyalists Thule"
            r"\b[A-Z][a-z]{2,}(?:\s+[A-Z][a-z]{2,})+\b",
            # Capitalized phrase with lowercase connector(s): "Order of Thorns", "House of Foscari"
            r"\b[A-Z][a-z]{2,}(?:\s+(?:of|de|di|da|del|della|du|des|van|von)\s+[A-Z][a-z]{2,})+\b",
        ]

        raw_matches = []
        for pat in phrase_patterns:
            try:
                raw_matches.extend(list(re.finditer(pat, vt)))
            except Exception:
                continue

        # Dedupe overlapping matches (prefer longer spans).
        phrase_matches = []
        try:
            raw_matches.sort(key=lambda m: (-(m.end() - m.start()), m.start()))
            used_spans = []
            for m in raw_matches:
                s, e = m.start(), m.end()
                if any((s < ue and e > us) for us, ue in used_spans):
                    continue
                phrase_matches.append(m)
                used_spans.append((s, e))
            phrase_matches.sort(key=lambda m: m.start())
        except Exception:
            phrase_matches = raw_matches
        if not phrase_matches:
            return []

        # Avoid false positives from sentence starters / common nouns.
        common_capitalized = {
            "I", "We", "Our", "Us",
            "A", "An", "The",
            "And", "But", "Or",
            "When", "Every", "Each", "Now", "Then", "There", "Here",
            "After", "Before", "During", "While",
            "Last", "Next", "First",
            "She", "He", "They", "Those",
            # Pronouns/determiners that often get capitalized at sentence start
            "Their", "Theirs", "Them", "Themselves",
            "Her", "Hers", "Herself",
            "His", "Him", "Himself",
            "Its", "Itself",
            "My", "Mine", "Your", "Yours", "Yourself", "Yourselves",
            "Mother", "Father", "Mam", "Mom", "Dad",
            "Bandits",
            "Spring", "Summer", "Autumn", "Winter",
            # Directions / generic modifiers
            "North", "South", "East", "West",
            "Upper", "Lower", "High", "Low",
            # Generic quantifiers / time-words that often start clauses
            "One", "Two", "Three", "Four", "Five", "Ten", "Twenty",
            "Day", "Night", "Morning", "Evening",
            # Generic place/institution nouns
            "Gate", "Gates", "Hall", "Halls", "House", "Well", "Wells",
            "Row", "Market", "Markets", "Street", "Streets", "Commons",
            # Common sentence-starter verbs that are not entities
            "Believes", "Thinks", "Grew", "Printed", "Slipped",
        }

        def _is_sentence_initial(idx: int) -> bool:
            try:
                if idx <= 0:
                    return True
                # Walk back to find previous non-space char.
                j = idx - 1
                while j >= 0 and vt[j].isspace():
                    j -= 1
                if j < 0:
                    return True
                return vt[j] in ('.', '!', '?', '\n')
            except Exception:
                return False

        out: List[str] = []
        for m in phrase_matches:
            phrase = (m.group(0) or '').strip()
            if not phrase:
                continue

            # Ignore phrase if it's only capitalized due to being at the start of a sentence.
            if _is_sentence_initial(int(m.start() or 0)):
                continue

            # Filter out common capitalized starters inside phrases (e.g. "The Market")
            try:
                toks = [t.strip() for t in phrase.split() if t.strip()]
            except Exception:
                toks = []
            if toks and toks[0] in common_capitalized:
                continue

            # Systemic filter to avoid false positives in poetic internal voice:
            # - Ignore 2-word adjective+noun style phrases ("Old Stones", "Stones Hope")
            # - Only treat phrases as major-entity candidates when they have:
            #   - a connector pattern ("Order of X", "House de Y"), OR
            #   - 3+ tokens (more specific / entity-like)
            try:
                has_connector = bool(re.search(r"\b(of|de|di|da|del|della|du|des|van|von)\b", phrase, flags=re.IGNORECASE))
                if (not has_connector) and (len(toks) < 3):
                    continue
            except Exception:
                continue

            pl = phrase.lower()
            if pl in ctx_l:
                continue

            # If the phrase exists anywhere in RAG, treat it as grounded.
            try:
                if self._term_exists_in_rag_anywhere(phrase):
                    continue
            except Exception:
                pass

            if phrase not in out:
                out.append(phrase)

        return out

    def _term_exists_in_rag_anywhere(self, term: str) -> bool:
        if not self.rag_system:
            return False
        t = (term or '').strip()
        if not t:
            return False
        tl = t.lower()

        try:
            if hasattr(self.rag_system, 'search'):
                results = self.rag_system.search(t, top_k=8)
                for doc, _score in results or []:
                    content = getattr(doc, 'content', '') or ''
                    if tl in content.lower():
                        return True
                return False
        except Exception:
            pass

        try:
            docs = getattr(self.rag_system, 'documents', {}) or {}
            for doc in docs.values():
                content = getattr(doc, 'content', '') or ''
                if tl in content.lower():
                    return True
        except Exception:
            return False
        return False

    def _find_ungrounded_entity_phrases(self, text: str, *, allowed_context: str) -> List[str]:
        """Catch specific-seeming entities even when not capitalized.

        We intentionally keep this heuristic simple and conservative.
        """
        try:
            import re
        except Exception:
            return []

        t = (text or '').strip()
        if not t:
            return []

        ctx_l = (allowed_context or '').lower()
        if not ctx_l:
            return []

        # Phrases that often represent invented institutions/landmarks.
        # Examples: "eastern gate fountain", "guild courier exam", "lower terrace markets".
        head_nouns = (
            'gate', 'fountain', 'market', 'markets', 'tower', 'ward', 'wards', 'district', 'hall', 'halls',
            'guild', 'exam', 'ledger', 'route', 'routes', 'terrace', 'palisade', 'lift', 'loft', 'mill'
        )
        noun_alt = "|".join(head_nouns)
        pattern = rf"\b(?:[a-z][a-z\-']{{1,}}\s+){{0,3}}(?:{noun_alt})\b"

        candidates = re.findall(pattern, t.lower())
        out: List[str] = []
        for c in candidates:
            cs = (c or '').strip()
            if not cs:
                continue
            # allow generic single-word heads
            if cs in head_nouns:
                continue
            if cs in ctx_l:
                continue
            if cs not in out:
                out.append(cs)
        return out

    def _sanitize_memory_text(self, text: str, *, bad_terms: List[str]) -> str:
        try:
            import re
        except Exception:
            return text

        s = str(text or '')
        if not s.strip() or not bad_terms:
            return s

        # Never sanitize generic sentence-starter words; sanitizer is for invented entities.
        skip = {
            "when", "every", "each", "now", "then", "there", "here",
            "after", "before", "during", "while",
            "last", "next", "first",
            "she", "he", "they", "those",
            "mother", "father", "mam", "mom", "dad",
            "spring", "summer", "autumn", "winter",
            "bandits",
        }

        for term in bad_terms:
            t = (term or '').strip()
            if not t:
                continue
            if t.lower() in skip:
                continue
            # Multiword phrase: replace with generic head noun (last word)
            parts = t.split()
            if len(parts) >= 2:
                head = parts[-1]
                repl = f"a {head}"
            else:
                # Single token: likely a proper noun
                repl = "someone"
            s = re.sub(rf"\b{re.escape(t)}\b", repl, s, flags=re.IGNORECASE)
        return s
    
    # ═══════════════════════════════════════════════════════════════════════════════
    # PERSONALITY EFFECTS GUIDE - How OCEAN, MBTI, and Mood affect internal voice
    # ═══════════════════════════════════════════════════════════════════════════════
    
    PERSONALITY_EFFECTS_GUIDE = """
**HOW PERSONALITY AFFECTS INTERNAL VOICE:**

═══════════════════════════════════════════════════════════════════════════════
OCEAN (Big Five) - Core Personality Traits
═══════════════════════════════════════════════════════════════════════════════

**OPENNESS (O)** - Imagination, curiosity, creativity
- HIGH (70-100): Poetic language, metaphors, abstract connections, "What if..." thinking
  Example: "The shadows here... they remind you of ink spreading through water."
- LOW (0-30): Practical, concrete, literal, prefers familiar patterns
  Example: "It's dark. You should find some light."

**CONSCIENTIOUSNESS (C)** - Organization, discipline, planning
- HIGH (70-100): Structured thoughts, considers consequences, methodical
  Example: "First, secure the perimeter. Then assess your options."
- LOW (0-30): Impulsive thoughts, spontaneous, goes with the flow
  Example: "Eh, you'll figure it out as you go."

**EXTRAVERSION (E)** - Social energy, assertiveness, talkativeness
- HIGH (70-100): Outward-focused thoughts, thinks about others, energetic inner voice
  Example: "Talk to someone! Anyone! This silence is killing you."
- LOW (0-30): Inward-focused, prefers solitude, quieter inner voice
  Example: "...finally alone. You can think clearly now."

**AGREEABLENESS (A)** - Compassion, cooperation, trust
- HIGH (70-100): Considers others' feelings, seeks harmony, empathetic
  Example: "They look upset. You should help them, even if it's not your problem."
- LOW (0-30): Self-focused, skeptical of others, competitive
  Example: "Not your problem. You have enough to deal with."

**NEUROTICISM (N)** - Emotional volatility, anxiety, mood swings
- HIGH (70-100): Anxious thoughts, worst-case scenarios, emotional reactions
  Example: "What if this goes wrong? What if you fail? What if—"
- LOW (0-30): Calm, stable, takes things in stride
  Example: "Alright. This is fine. You've handled worse."

═══════════════════════════════════════════════════════════════════════════════
MBTI - Cognitive Processing Style
═══════════════════════════════════════════════════════════════════════════════

**I vs E (Introversion vs Extraversion)**
- I: Internal processing, thinks before speaking, reflective
- E: External processing, thinks out loud, action-oriented

**S vs N (Sensing vs Intuition)**
- S: Focus on concrete details, what IS, practical observations
  Example: "The door is wooden. Old. The lock looks rusted."
- N: Focus on patterns, what COULD BE, abstract connections
  Example: "This door... it's hiding something. You can feel it."

**T vs F (Thinking vs Feeling)**
- T: Logical analysis, pros/cons, objective reasoning
  Example: "Logically, the risk outweighs the benefit. You shouldn't."
- F: Value-based decisions, emotional impact, personal meaning
  Example: "It doesn't feel right. Something in you says no."

**J vs P (Judging vs Perceiving)**
- J: Wants closure, makes decisions, structured approach
  Example: "You need to decide NOW. This uncertainty is unbearable."
- P: Keeps options open, adaptable, goes with the flow
  Example: "Let's see how this plays out. No need to commit yet."

**MBTI Type Examples:**
- INTJ: Strategic, analytical, "You've calculated the optimal path."
- ENFP: Enthusiastic, imaginative, "Oh! What if you tried THIS instead?"
- ISTJ: Methodical, reliable, "Follow the procedure. It works."
- ESFP: Spontaneous, present-focused, "This is happening NOW. Let's go!"

═══════════════════════════════════════════════════════════════════════════════
MOOD - Current Emotional State
═══════════════════════════════════════════════════════════════════════════════

**Mood Categories & Voice Effects:**

- HAPPY/CONTENT: Optimistic phrasing, sees positives, lighter tone
  Example: "This might actually work out. You've got this."

- SAD/MELANCHOLIC: Heavy thoughts, dwelling on loss, slower pacing
  Example: "...what's the point. Everything just... fades."

- ANGRY/FRUSTRATED: Sharp thoughts, blame, aggressive phrasing
  Example: "This is ridiculous. Who designed this? Idiots."

- ANXIOUS/WORRIED: Racing thoughts, what-ifs, catastrophizing
  Example: "What if they see you? What if you're too late? What if—"

- FEARFUL/SCARED: Hypervigilant, escape-focused, short thoughts
  Example: "Run. Hide. Don't look back. Just GO."

- CALM/PEACEFUL: Measured thoughts, acceptance, clear thinking
  Example: "Alright. Assess this calmly. You have time."

- CURIOUS/INTERESTED: Questions, exploration, engagement
  Example: "Wait... what's that? You need to know more."

- DISGUSTED/REPULSED: Rejection, avoidance, strong negative reactions
  Example: "Ugh. No. You're not touching that. Absolutely not."

**Mood Intensity:**
- SUBTLE: Barely colors the thoughts, underlying tone
- MODERATE: Clearly present, affects word choice
- STRONG: Dominates the internal voice, hard to ignore
- OVERWHELMING: Consumes all thought, may cause fragmented speech

═══════════════════════════════════════════════════════════════════════════════
COMBINING TRAITS - Examples
═══════════════════════════════════════════════════════════════════════════════

**High O + High N + Anxious Mood:**
"The shadows are watching you. You can feel their eyes. What do they want?"

**Low O + High C + Calm Mood:**
"Step one: check the door. Step two: secure the room. Simple."

**High E + High A + Happy Mood:**
"Everyone here seems nice! You should introduce yourself. This could be fun!"

**Low E + Low A + Angry Mood:**
"Leave you alone. You don't need anyone. You don't WANT anyone."

**INTJ + High C + Anxious Mood:**
"You've planned for this. But what if you missed something? Run the scenarios again."

**ESFP + Low C + Happy Mood:**
"Who cares about the plan! Let's just DO it! Right now! Come on!"
"""
    
    # Condensed version for prompts (to save tokens)
    PERSONALITY_EFFECTS_CONDENSED = """
**PERSONALITY → VOICE EFFECTS (Apply these based on the actor's traits):**

OCEAN Effects:
- High O: Poetic, metaphors, "what if..." | Low O: Practical, literal, concrete
- High C: Structured, methodical, plans | Low C: Impulsive, spontaneous, casual
- High E: Outward-focused, energetic | Low E: Inward-focused, quiet, reflective
- High A: Empathetic, considers others | Low A: Self-focused, skeptical
- High N: Anxious, worst-case thinking | Low N: Calm, stable, takes things in stride

MBTI Effects:
- I/E: Internal processing vs thinks out loud
- S/N: Concrete details vs abstract patterns
- T/F: Logical analysis vs value-based feelings
- J/P: Wants closure vs keeps options open

Mood Effects:
- Happy: Optimistic, lighter tone | Sad: Heavy, dwelling, slower
- Angry: Sharp, blame, aggressive | Anxious: Racing, what-ifs
- Fearful: Hypervigilant, escape-focused | Calm: Measured, clear
- Curious: Questions, exploration | Disgusted: Rejection, avoidance

Mood Intensity: subtle (underlying) → moderate (affects words) → strong (dominates) → overwhelming (fragmented)
"""
    
    def __init__(self, storage_directory: Path = None, rag_system=None):
        self.client = create_role_client("narration")
        self.logger = logging.getLogger(__name__)
        self.storage_directory = storage_directory or Path("./simulation_data")
        self.rag_system = rag_system  # For worldbuilding context
        
        # Track used phrases to prevent repetition
        self.used_phrases: Set[str] = set()
        self.recent_outputs: List[str] = []
        self.max_recent_outputs = 20
        
        # Track created memories
        self.created_memories: Dict[str, List[Dict[str, Any]]] = {
            cat: [] for cat in MEMORY_CATEGORIES.keys()
        }
        
        # Load existing memories
        self._load_created_memories()
    
    def _get_worldbuilding_context(self, query: str, max_tokens: int = 300) -> str:
        """Get relevant worldbuilding context from RAG system."""
        if not self.rag_system:
            return ""
        try:
            categories = []
            if WorldbuildingCategory:
                categories = [
                    WorldbuildingCategory.TEMPORAL,
                    WorldbuildingCategory.CIVILIZATION,
                    WorldbuildingCategory.MECHANICS,
                    WorldbuildingCategory.CULTURE,
                    WorldbuildingCategory.NARRATION_STYLE_TONE,
                    WorldbuildingCategory.PLACES,
                ]

            context = get_multi_category_context_for_llm(
                self.rag_system,
                query=query,
                categories=categories,
                max_tokens_per_category=max(60, int(max_tokens / 3)),
                include_related=True,
            )
            return context or ""
        except Exception as e:
            self.logger.warning(f"RAG query failed: {e}")
        return ""
    
    def generate_voice(self,
                      interpretation: VoiceInterpretation,
                      scene_description: str,
                      user_action: str = "",
                      action_outcome: str = "",
                      personality_prompt: str = "",
                      actor_name: str = "Unknown",
                      current_goal: str = "",
                      current_task: str = "",
                      available_memories: List[str] = None,
                      time_context: Dict[str, Any] = None,
                      session_id: str = None) -> Dict[str, Any]:
        """
        Generate internal voice content based on interpretation.
        
        Args:
            interpretation: Result from interpreter agent
            scene_description: Current scene
            user_action: What user did
            action_outcome: Result of action
            personality_prompt: Personality section for prompts
            actor_name: Actor's name
            current_goal: Current goal
            current_task: Current task
            available_memories: Available memories to reference
            time_context: Current time info (time_string, day, period, etc.)
            
        Returns:
            Dict with voice content and metadata
        """
        # Store time context for use in generation methods
        self._current_time_context = time_context
        func = interpretation.primary_function
        
        if func == InternalVoiceFunction.INFORMATION:
            return self._generate_information_voice(
                interpretation, personality_prompt, actor_name,
                available_memories, scene_description, time_context, session_id
            )
        elif func == InternalVoiceFunction.SOLUTION:
            return self._generate_solution_voice(
                interpretation, personality_prompt, actor_name,
                scene_description, current_goal, current_task, time_context, session_id
            )
        elif func == InternalVoiceFunction.MEMORY:
            return self._generate_memory_voice(
                interpretation, personality_prompt, actor_name,
                scene_description, available_memories, time_context, session_id
            )
        elif func in (InternalVoiceFunction.TASK_GOAL_REMINDER, InternalVoiceFunction.TASK_REMINDER):
            return self._generate_task_goal_reminder_voice(
                interpretation, personality_prompt, actor_name,
                scene_description, current_goal, current_task, time_context, session_id
            )
        else:  # COMMENT
            return self._generate_comment_voice(
                interpretation, personality_prompt, actor_name,
                scene_description, user_action, action_outcome, time_context, session_id
            )
    
    def _format_time_context(self, time_context: Dict[str, Any] = None) -> str:
        """Format time context for inclusion in prompts."""
        tc = time_context or getattr(self, '_current_time_context', None)
        
        # Auto-fetch from MasterTimeCoordinator if not set
        if not tc:
            try:
                from master_time_coordinator import get_master_time_coordinator
                master_time = get_master_time_coordinator()
                if master_time:
                    tc = master_time.get_current_time_context()
            except Exception:
                pass
        
        if not tc:
            return ""
        
        time_str = tc.get('time_string', '') or tc.get('formatted_time', '')
        day = tc.get('day', '')
        period = tc.get('period', '') or tc.get('time_of_day', '')  # morning, afternoon, evening, night
        
        parts = []
        if time_str:
            parts.append(f"Current Time: {time_str}")
        if day:
            parts.append(f"Day: {day}")
        if period:
            parts.append(f"Period: {period}")
        
        if parts:
            return f"""
**TIME CONTEXT (Use for temporal awareness in thoughts):**
{chr(10).join(parts)}
"""
        return ""
    
    def _generate_information_voice(self,
                                   interpretation: VoiceInterpretation,
                                   personality_prompt: str,
                                   actor_name: str,
                                   available_memories: List[str],
                                   scene_description: str,
                                   time_context: Dict[str, Any] = None,
                                   session_id: str = None) -> Dict[str, Any]:
        """Generate internal voice for INFORMATION function"""
        question = interpretation.question_content or "unknown question"
        question_type = interpretation.question_type or QuestionType.LOGIC
        
        # Build memory context
        memories_text = "\n".join(f"- {m}" for m in (available_memories or [])[:10])
        
        # Get worldbuilding context for setting-appropriate thoughts
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{question} {scene_description[:100]} technology culture era setting",
            max_tokens=200
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - Answers must be setting-appropriate):**
{worldbuilding_context}

**SETTING ENFORCEMENT (CRITICAL):**
Answers MUST reference only technology, concepts, and knowledge that exist in the worldbuilding context above.
- NEVER use anachronistic technology or concepts that don't exist in the setting
- NEVER use metaphors that contradict the worldbuilding context provided - use only concepts that exist in the established world
- ALWAYS match the era, culture, and technology level described in the worldbuilding context
"""
        
        # Format time context
        time_section = self._format_time_context(time_context)

        spatial_facts_section = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_section = f"""

**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{sf.strip()}
"""
        except Exception:
            spatial_facts_section = ""

        grounding_section = self._build_soft_grounding_rules(
            scene_description=scene_description,
            worldbuilding_context=worldbuilding_context,
            available_memories=available_memories,
        )
        
        prompt = f"""Generate an internal voice response answering this question.

**IDENTITY (CRITICAL):**
- You are {actor_name}.
- Do NOT refer to yourself by name.
- NEVER treat {actor_name} as a separate person you can see or evaluate.
- Address the character as "you" or by their name. NEVER use "we", "us", "our", "I", or "my".

**DIEGESIS (CRITICAL):**
- Never mention maps, UI, prompts, system, simulation, or any meta concepts.

**MENTION TAGGING (CRITICAL):**
- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.
- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.
- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{{role}}'.
- Examples: '@{{mentor}}', '@{{best friend}}', '@{{captain}}'.
- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).

**QUESTION:** {question}
**QUESTION TYPE:** {question_type.value}

**AVAILABLE MEMORIES/KNOWLEDGE:**
{memories_text if memories_text else 'No specific memories loaded'}

**SCENE CONTEXT:**
{scene_description[:300]}
{time_section}{worldbuilding_section}
{spatial_facts_section}
{grounding_section}
{personality_prompt}

{self.PERSONALITY_EFFECTS_CONDENSED}

**ANTI-REPETITION - DO NOT USE THESE PHRASES:**
{self._get_anti_repetition_list()}

**🚨 CRITICAL: SOUND LIKE ACTUAL THOUGHTS, NOT NARRATION 🚨**

Internal voice must sound like how a REAL PERSON actually thinks - casual, direct, natural.

❌ BAD (too literary - sounds like narration):
- "The answer unfolds within you like petals of understanding..."
- "You sense the truth resonating through the corridors of memory..."

✅ GOOD (sounds like actual thinking - adapt to your setting):
- "[Location] is north, past the [landmark]."
- "You... don't actually know. Never came up before."
- "Complicated question. Part of you thinks yes, but..."

**GUIDELINES:**

**For LOGIC Questions (factual queries about anything concrete):**
- ANSWER THE QUESTION DIRECTLY first, then briefly reference a memory as evidence
- Pattern: "[Direct answer]. [Brief memory reference]."
- Examples (adapt to your setting):
  - "[Name]—they've been your closest since [event]."
  - "[Location] is north, past the [landmark]."
  - "[Time], the [routine] just changed."
  - "You can handle this—[mentor] drilled that into you."
  - "Tired. Been on your feet since [time marker]."
- If SPATIAL/TIME/INVENTORY info is provided, USE those specific details
- If memories are provided, weave them naturally into the answer
- If unknown, admit it: "You... don't actually know."
- Address the character as "you" or by their name - NEVER use "I", "my", "we", "our", or "us"
- Keep it brief (1-2 sentences max)

**For CONCEPTUAL Questions (abstract - moral dilemmas, meaning of, what should you do):**
- Reflect the character's values and personality
- Show internal conflict if appropriate
- Don't give a definitive answer if the question is genuinely complex
- Address the character as "you" or by their name - NEVER use "we", "our", or "us"
- Can be slightly longer (2-3 sentences)

**For IDENTITY Questions (who are you, what do you want):**
- Draw from personality and goals
- Show self-awareness or lack thereof
- Be authentic to the character
- Address the character as "you" or by their name - NEVER use "we", "our", or "us"

**VOICE URGENCY:** {interpretation.urgency}
- calm: Measured, thoughtful pace
- normal: Natural internal rhythm
- urgent: Quicker, more pressing thoughts
- frantic: Racing, fragmented thoughts

**Response Format:**
Return JSON:

{{
    "internal_voice": "The actual internal monologue (1-3 sentences)",
    "answer_confidence": "certain/probable/uncertain/unknown",
    "creates_memory": true/false,
    "memory_content": "If creates_memory is true, the memory to create",
    "memory_category": "category if creating memory"
}}
"""
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERNAL VOICE VALIDATION WITH REGENERATION
        # Retry up to 2 times if voice is describing instead of thinking
        # ═══════════════════════════════════════════════════════════════════
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + self._get_retry_instructions(attempt)
                
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": retry_prompt}],
                    model=OpenRouterConfig.get_model_for_role("narration"),
                    temperature=0.7,
                    max_tokens=400,
                    max_retries=RetryConfig.CRITICAL_MAX_RETRIES,
                    call_name="VOICE_INFORMATION"
                )
                
                result = extract_and_parse_json(response)
                
                if not result:
                    if attempt == max_retries:
                        return self._create_fallback_voice("information", interpretation.urgency)
                    continue
                
                voice_text = result.get("internal_voice", "")
                
                # Validate that voice is THINKING not DESCRIBING
                is_describing, detected_indicator = self._check_if_describing(voice_text, actor_name=actor_name)
                
                if is_describing and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING DETECTED in INFORMATION (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[INTERNAL VOICE] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_describing:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING PERSISTS in INFORMATION after {max_retries + 1} attempts: '{detected_indicator}'")

                ungrounded = self._find_ungrounded_proper_nouns(
                    voice_text,
                    allowed_context=f"{scene_description}\n\n{worldbuilding_context}\n\n{memories_text}",
                )
                if ungrounded and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ UNGROUNDED NAMES in INFORMATION (attempt {attempt + 1}): {ungrounded}")
                    prompt = prompt + (
                        "\n\nCRITICAL: Do not introduce new named places/organizations/items. "
                        f"Avoid these ungrounded names: {', '.join(ungrounded)}. "
                        "If needed, use generic phrasing (someone/somewhere) and uncertainty (maybe/might).\n"
                    )
                    continue
                
                # Track output
                self._track_output(voice_text)
                
                return {
                    "function": "information",
                    "voice_text": voice_text,
                    "answer_confidence": result.get("answer_confidence", "uncertain"),
                    "creates_memory": result.get("creates_memory", False),
                    "memory_content": result.get("memory_content"),
                    "memory_category": result.get("memory_category"),
                    "urgency": interpretation.urgency
                }
                
            except Exception as e:
                self.logger.error(f"Error generating information voice (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return self._create_fallback_voice("information", interpretation.urgency)
    
    def _generate_solution_voice(self,
                                interpretation: VoiceInterpretation,
                                personality_prompt: str,
                                actor_name: str,
                                scene_description: str,
                                current_goal: str,
                                current_task: str,
                                time_context: Dict[str, Any] = None,
                                session_id: str = None) -> Dict[str, Any]:
        """Generate internal voice for SOLUTION function"""
        predicament = interpretation.predicament_description or "current situation"
        
        # Get worldbuilding context for setting-appropriate solutions
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{predicament} {scene_description[:100]} technology tools resources era setting",
            max_tokens=200
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - Solutions must be setting-appropriate):**
{worldbuilding_context}

**SETTING ENFORCEMENT (CRITICAL):**
Suggested solutions MUST use only technology, tools, and methods that exist in the worldbuilding context above.
- NEVER suggest anachronistic solutions that don't exist in the setting
- NEVER use metaphors that contradict the worldbuilding context provided - use only concepts that exist in the established world
- ALWAYS match the era, culture, and technology level described in the worldbuilding context
"""
        
        # Format time context
        time_section = self._format_time_context(time_context)

        spatial_facts_section = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_section = f"""

**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{sf.strip()}
"""
        except Exception:
            spatial_facts_section = ""

        grounding_section = self._build_soft_grounding_rules(
            scene_description=scene_description,
            worldbuilding_context=worldbuilding_context,
            available_memories=None,
        )
        
        prompt = f"""Generate an internal voice suggesting a solution to this predicament.

**IDENTITY (CRITICAL):**
- You are {actor_name}.
- Do NOT refer to yourself by name.
- NEVER treat {actor_name} as a separate person you can see or evaluate.
- Address the character as "you" or by their name. NEVER use "we", "us", "our", "I", or "my".

**DIEGESIS (CRITICAL):**
- Never mention maps, UI, prompts, system, simulation, or any meta concepts.

**MENTION TAGGING (CRITICAL):**
- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.
- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.
- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{{role}}'.
- Examples: '@{{mentor}}', '@{{best friend}}', '@{{captain}}'.
- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).

**PREDICAMENT:** {predicament}

**CURRENT GOAL:** {current_goal or 'No specific goal'}
**CURRENT TASK:** {current_task or 'No specific task'}

**SCENE:**
{scene_description[:400]}
{time_section}{worldbuilding_section}
{spatial_facts_section}
{grounding_section}
{personality_prompt}

{self.PERSONALITY_EFFECTS_CONDENSED}

**ANTI-REPETITION - DO NOT USE THESE PHRASES:**
{self._get_anti_repetition_list()}

**GUIDELINES:**

The internal voice should:
1. Acknowledge the problem briefly
2. Suggest an idea or action that could help
3. Connect to the goal if possible
4. Reflect the character's personality in HOW they think about solutions

**🚨 CRITICAL: SOUND LIKE ACTUAL THOUGHTS, NOT NARRATION 🚨**

Problem-solving thoughts must sound like how a REAL PERSON actually thinks through problems - direct, practical, casual.

❌ BAD (too literary - sounds like narration):
- "The solution is there. Just think it through."
- "You weave through the labyrinth of options, seeking the golden thread..."

✅ GOOD (sounds like actual problem-solving - adapt to your setting):
- "Okay, think. We could try the [alternative route]."
- "That's not gonna work. What about the [other option]?"
- "Only one way out of this. We move [time constraint]."

**SOLUTION STYLE BY PERSONALITY:**
- High C (Conscientious): Methodical, step-by-step solutions
- Low C: Impulsive, "just do it" solutions
- High N (Neurotic): Worried about what could go wrong
- Low N: Confident the solution will work
- T (Thinking): Logical pros/cons analysis
- F (Feeling): What feels right, values-based

**SOLUTION TYPES:**
- Practical: "Maybe if you..."
- Creative: "What if you tried..."
- Desperate: "We could always..."
- Calculated: "The best option is..."

**CRITICAL:** Address the character as "you" or by their name. NEVER use "I", "my", "we", "our", or "us"

**VOICE URGENCY:** {interpretation.urgency}
- calm: Thoughtful problem-solving
- normal: Working through options
- urgent: Quick assessment needed
- frantic: Desperate for any solution

**Response Format:**
Return JSON:

{{
    "internal_voice": "The solution-suggesting internal monologue (2-3 sentences)",
    "solution_type": "practical/creative/desperate/calculated",
    "suggested_action": "Brief description of suggested action",
    "goal_connection": "How this connects to the goal (or 'none')"
}}
"""
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERNAL VOICE VALIDATION WITH REGENERATION
        # Retry up to 2 times if voice is describing instead of thinking
        # ═══════════════════════════════════════════════════════════════════
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + self._get_retry_instructions(attempt)
                
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": retry_prompt}],
                    model=OpenRouterConfig.get_model_for_role("narration"),
                    temperature=0.7,
                    max_tokens=400,
                    max_retries=RetryConfig.CRITICAL_MAX_RETRIES,
                    call_name="VOICE_SOLUTION"
                )
                
                result = extract_and_parse_json(response)
                
                if not result:
                    if attempt == max_retries:
                        return self._create_fallback_voice("solution", interpretation.urgency)
                    continue
                
                voice_text = result.get("internal_voice", "")
                
                # Validate that voice is THINKING not DESCRIBING
                is_describing, detected_indicator = self._check_if_describing(voice_text, actor_name=actor_name)
                
                if is_describing and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING DETECTED in SOLUTION (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[INTERNAL VOICE] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_describing:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING PERSISTS in SOLUTION after {max_retries + 1} attempts: '{detected_indicator}'")

                ungrounded = self._find_ungrounded_proper_nouns(
                    voice_text,
                    allowed_context=f"{scene_description}\n\n{worldbuilding_context}",
                )
                if ungrounded and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ UNGROUNDED NAMES in SOLUTION (attempt {attempt + 1}): {ungrounded}")
                    prompt = prompt + (
                        "\n\nCRITICAL: Do not assert new named places/organizations/systems. "
                        f"Avoid these ungrounded names: {', '.join(ungrounded)}. "
                        "Keep suggestions generic and conditional (maybe/might).\n"
                    )
                    continue
                
                self._track_output(voice_text)
                
                return {
                    "function": "solution",
                    "voice_text": voice_text,
                    "solution_type": result.get("solution_type", "practical"),
                    "suggested_action": result.get("suggested_action", ""),
                    "goal_connection": result.get("goal_connection", "none"),
                    "urgency": interpretation.urgency
                }
                
            except Exception as e:
                self.logger.error(f"Error generating solution voice (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return self._create_fallback_voice("solution", interpretation.urgency)
    
    def _generate_memory_voice(self,
                              interpretation: VoiceInterpretation,
                              personality_prompt: str,
                              actor_name: str,
                              scene_description: str,
                              available_memories: List[str],
                              time_context: Dict[str, Any] = None,
                              session_id: str = None) -> Dict[str, Any]:
        """Generate internal voice for MEMORY function"""
        trigger = interpretation.memory_trigger or "something in the scene"
        category = interpretation.memory_category or "general"
        
        # Get existing memories for this category
        existing_memories = self.created_memories.get(category, [])
        starter_memories = MEMORY_CATEGORIES.get(category, [])
        
        # Build memory context
        all_memories = existing_memories + [{"content": m} for m in starter_memories]
        memories_text = "\n".join(f"- {m.get('content', m) if isinstance(m, dict) else m}" 
                                  for m in all_memories[:5])
        
        # Get worldbuilding context for setting-appropriate memories
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{trigger} {category} {scene_description[:100]} history culture era setting",
            max_tokens=200
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - Memories must be setting-appropriate):**
{worldbuilding_context}

**SETTING ENFORCEMENT (CRITICAL):**
Memories MUST reference only technology, events, and cultural elements that exist in the worldbuilding context above.
- NEVER reference anachronistic technology or concepts that don't exist in the setting
- NEVER use metaphors that contradict the worldbuilding context provided - use only concepts that exist in the established world
- ALWAYS match the era, culture, and technology level described in the worldbuilding context
"""
        
        # Format time context
        time_section = self._format_time_context(time_context)

        spatial_facts_section = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_section = f"""

**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{sf.strip()}
"""
        except Exception:
            spatial_facts_section = ""

        grounding_section = self._build_soft_grounding_rules(
            scene_description=scene_description,
            worldbuilding_context=worldbuilding_context,
            available_memories=[
                m.get('content', m) if isinstance(m, dict) else str(m)
                for m in all_memories[:5]
            ],
        )
        
        prompt = f"""Generate an internal voice recalling or creating a memory.

**IDENTITY (CRITICAL):**
- You are {actor_name}.
- Do NOT refer to yourself by name.
- NEVER treat {actor_name} as a separate person you can see or evaluate.
- Address the character as "you" or by their name. NEVER use "we", "us", "our", "I", or "my".

**DIEGESIS (CRITICAL):**
- Never mention maps, UI, prompts, system, simulation, or any meta concepts.

**MENTION TAGGING (CRITICAL):**
- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.
- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.
- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{{role}}'.
- Examples: '@{{mentor}}', '@{{best friend}}', '@{{captain}}'.
- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).

**MEMORY TRIGGER:** {trigger}
**MEMORY CATEGORY:** {category}

**EXISTING MEMORIES IN THIS CATEGORY:**
{memories_text if memories_text else 'None yet'}

**SCENE:**
{scene_description[:300]}
{time_section}{worldbuilding_section}
{spatial_facts_section}
{grounding_section}
{personality_prompt}

{self.PERSONALITY_EFFECTS_CONDENSED}

**ANTI-REPETITION - DO NOT USE THESE PHRASES:**
{self._get_anti_repetition_list()}

**GUIDELINES:**

The internal voice should:
1. Show the memory being triggered naturally
2. Either recall an existing memory OR create a new one
3. Connect the memory to the current moment
4. Reflect emotional weight appropriate to the memory

**🚨 CRITICAL: SOUND LIKE ACTUAL THOUGHTS, NOT NARRATION 🚨**

Memory recall must sound like how a REAL PERSON actually remembers - casual, direct, personal.

❌ BAD (too literary - sounds like narration):
- "The scent of incense carries you back to mornings bathed in golden light..."
- "A tapestry of memories unfolds before your mind's eye..."

✅ GOOD (sounds like actual memory recall - adapt to your setting):
- "Smells like [familiar place]. Haven't thought about that in years."
- "Last time you saw something like this... that didn't end well."
- "Reminds you of [past era]. Simpler times."

**MEMORY STYLE BY PERSONALITY:**
- High O (Openness): Makes connections, sees patterns in memories - but still casual speech
- Low O: Factual, straightforward recollections
- High N (Neurotic): Memories tinged with anxiety or regret
- Low N: Memories recalled with acceptance and peace
- High A (Agreeable): Memories focused on relationships, warmth
- Low A: Memories focused on self, achievements, conflicts
- F (Feeling): Emotionally rich, but expressed simply
- T (Thinking): More analytical, lessons learned

**MEMORY VOICE PATTERNS:**
- Nostalgic: "This reminds you of..."
- Painful: "You try not to think about..."
- Warm: "You remember when..."
- Bittersweet: "It's been so long since..."

**CRITICAL:** Address the character as "you" or by their name. NEVER use "I", "my", "we", "our", or "us"

**VOICE URGENCY:** {interpretation.urgency}

**Response Format:**
Return JSON:

{{
    "internal_voice": "The memory-recalling internal monologue (2-3 sentences)",
    "is_new_memory": true/false,
    "memory_content": "The actual memory content (for storage)",
    "memory_category": "{category}",
    "emotional_tone": "nostalgic/painful/warm/bittersweet/neutral"
}}
"""
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERNAL VOICE VALIDATION WITH REGENERATION
        # Retry up to 2 times if voice is describing instead of thinking
        # ═══════════════════════════════════════════════════════════════════
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + self._get_retry_instructions(attempt)
                
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": retry_prompt}],
                    model=OpenRouterConfig.get_model_for_role("narration"),
                    temperature=0.7,
                    max_tokens=400,
                    max_retries=RetryConfig.CRITICAL_MAX_RETRIES,
                    call_name="VOICE_MEMORY"
                )
                
                result = extract_and_parse_json(response)
                
                if not result:
                    if attempt == max_retries:
                        return self._create_fallback_voice("memory", interpretation.urgency)
                    continue
                
                voice_text = result.get("internal_voice", "")
                
                # Validate that voice is THINKING not DESCRIBING
                is_describing, detected_indicator = self._check_if_describing(voice_text, actor_name=actor_name)
                
                if is_describing and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING DETECTED in MEMORY (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[INTERNAL VOICE] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_describing:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING PERSISTS in MEMORY after {max_retries + 1} attempts: '{detected_indicator}'")

                ungrounded = self._find_ungrounded_proper_nouns(
                    voice_text,
                    allowed_context=f"{scene_description}\n\n{worldbuilding_context}\n\n{memories_text}",
                )
                if ungrounded and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ UNGROUNDED NAMES in MEMORY (attempt {attempt + 1}): {ungrounded}")
                    prompt = prompt + (
                        "\n\nCRITICAL: Do not invent new named people/places/organizations in memories unless supported by context. "
                        f"Avoid these ungrounded names: {', '.join(ungrounded)}.\n"
                    )
                    continue
                
                self._track_output(voice_text)
                
                # Store new memory if created
                if result.get("is_new_memory") and result.get("memory_content"):
                    self._store_memory(
                        category=result.get("memory_category", category),
                        content=result.get("memory_content"),
                        emotional_tone=result.get("emotional_tone", "neutral")
                    )
                
                return {
                    "function": "memory",
                    "voice_text": voice_text,
                    "is_new_memory": result.get("is_new_memory", False),
                    "memory_content": result.get("memory_content"),
                    "memory_category": result.get("memory_category", category),
                    "emotional_tone": result.get("emotional_tone", "neutral"),
                    "urgency": interpretation.urgency
                }
                
            except Exception as e:
                self.logger.error(f"Error generating memory voice (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return self._create_fallback_voice("memory", interpretation.urgency)
    
    def _generate_comment_voice(self,
                               interpretation: VoiceInterpretation,
                               personality_prompt: str,
                               actor_name: str,
                               scene_description: str,
                               user_action: str,
                               action_outcome: str,
                               time_context: Dict[str, Any] = None,
                               session_id: str = None) -> Dict[str, Any]:
        """Generate internal voice for COMMENT function (personality flavor)"""
        
        # Get worldbuilding context for setting-appropriate thoughts
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{scene_description[:100]} technology culture era setting",
            max_tokens=200
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - Thoughts must be setting-appropriate):**
{worldbuilding_context}

**SETTING ENFORCEMENT (CRITICAL):**
Internal thoughts MUST reference only technology, concepts, and cultural elements that exist in the worldbuilding context above.
- NEVER use anachronistic technology or concepts that don't exist in the setting
- NEVER use metaphors that contradict the worldbuilding context provided - use only concepts that exist in the established world
- ALWAYS match the era, culture, and technology level described in the worldbuilding context
"""
        
        # Format time context
        time_section = self._format_time_context(time_context)

        spatial_facts_section = ""
        try:
            from spatial_context_system import build_spatial_facts
            sf = build_spatial_facts(session_id=session_id)
            if isinstance(sf, str) and sf.strip():
                spatial_facts_section = f"""

**AUTHORITATIVE SPATIAL FACTS (MUST NOT CONTRADICT):**
{sf.strip()}
"""
        except Exception:
            spatial_facts_section = ""

        grounding_section = self._build_soft_grounding_rules(
            scene_description=scene_description,
            worldbuilding_context=worldbuilding_context,
            available_memories=None,
        )
        
        prompt = f"""Generate a personality-driven internal voice comment.

**IDENTITY (CRITICAL):**
- You are {actor_name}.
- Do NOT refer to yourself by name.
- NEVER treat {actor_name} as a separate person you can see or evaluate.
- Address the character as "you" or by their name. NEVER use "we", "us", "our", "I", or "my".

**DIEGESIS (CRITICAL):**
- Never mention maps, UI, prompts, system, simulation, or any meta concepts.

**MENTION TAGGING (CRITICAL):**
- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.
- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.
- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{{role}}'.
- Examples: '@{{mentor}}', '@{{best friend}}', '@{{captain}}'.
- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).

**SCENE:**
{scene_description[:300]}

**ACTION:** {user_action}
**OUTCOME:** {action_outcome}
{time_section}{worldbuilding_section}
{spatial_facts_section}
{grounding_section}
{personality_prompt}

{self.PERSONALITY_EFFECTS_CONDENSED}

**ANTI-REPETITION - DO NOT USE THESE PHRASES:**
{self._get_anti_repetition_list()}

**GUIDELINES:**

The COMMENT function adds personality flavor. The internal voice should:
1. React to the situation in a way that reveals character
2. Show the character's unique perspective
3. Reflect their mood, values, and quirks
4. NOT be generic - must feel specific to THIS character

**🚨 CRITICAL: SOUND LIKE ACTUAL THOUGHTS, NOT NARRATION 🚨**

Internal voice must sound like how a REAL PERSON actually thinks - casual, fragmented, direct.

❌ BAD (too literary/poetic - sounds like narration):
- "We breathe the cold like a promise—sharp, honest—and catch that woman's quiet strength"
- "The morning air whispers secrets of the city's awakening soul"
- "A living blueprint for how you might shoulder the day's weight"
- "Check the lights; if one's out, report it before someone stumbles." (action-planning — still forbidden)
- "The notices still posted, so someone must've missed their rounds." (environmental observation)

✅ GOOD (sounds like actual inner monologue - adapt to your setting):
- "Cold out here. That woman looks tough—been at this a while."
- "Damn, it's late. [Comfort] smells good though."
- "She's got it handled. Keep moving."
- "Something's off about this place. Can't put your finger on it."

**RULES FOR AUTHENTIC THOUGHTS:**
1. Use casual language, contractions, even mild profanity if it fits
2. Thoughts can be incomplete or fragmented
3. NO flowery metaphors or poetic prose
4. NO describing sensory experiences (that's narration's job)
5. React to what you NOTICE, don't describe what you SEE/FEEL/HEAR
6. Keep it SHORT - real thoughts are brief
7. NO action-planning ("we'll check", "we'll log", "we'll need to")
8. NO procedural task-listing or to-do lists
9. Express FEELINGS and REACTIONS, not plans or observations

**COMMENT STYLE BY PERSONALITY (CRITICAL - APPLY THESE):**

OCEAN-driven comments:
- High O: Makes connections, sees patterns, curious - but still casual speech
- Low O: Practical, matter-of-fact, "it is what it is"
- High C: Notices order/disorder, planning thoughts, "you should..."
- Low C: Goes with the flow, casual, "whatever happens, happens"
- High E: Thinks about others, social dynamics, wants interaction
- Low E: Appreciates solitude, internal focus, quiet observations
- High A: Empathetic, considers others' feelings, wants harmony
- Low A: Critical, skeptical, self-focused, competitive
- High N: Worried undertones, what-ifs, emotional reactions
- Low N: Calm acceptance, stable, "you've got this"

MBTI-driven comments:
- S types: Notice concrete details, what IS
- N types: Notice patterns, possibilities, what COULD BE
- T types: Logical observations, analysis
- F types: Emotional reactions, value judgments
- J types: Want closure, decisive thoughts
- P types: Open-ended, exploring options

**COMMENT TYPES:**
- Observation: Noticing something others might miss
- Judgment: Opinion about what's happening
- Self-reflection: Thoughts about your own actions/feelings
- Anticipation: Thinking about what comes next
- Humor: Finding something amusing (if personality fits)
- Concern: Worrying about something
- Satisfaction: Feeling good about something

**CRITICAL:** Address the character as "you" or by their name. NEVER use "I", "my", "we", "our", or "us"

**VOICE URGENCY:** {interpretation.urgency}
- calm: Relaxed observations
- normal: Natural thought flow
- urgent: Pressing concerns
- frantic: Racing thoughts

**Response Format:**
Return JSON:

{{
    "internal_voice": "The personality-driven comment (1-2 sentences)",
    "comment_type": "observation/judgment/self-reflection/anticipation/humor/concern/satisfaction",
    "personality_elements_shown": ["list", "of", "traits", "evident"]
}}
"""
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERNAL VOICE VALIDATION WITH REGENERATION
        # Retry up to 2 times if voice is describing instead of thinking
        # ═══════════════════════════════════════════════════════════════════
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                # Add stricter constraint on retry attempts
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + f"""

🚨 CRITICAL RETRY #{attempt} - PREVIOUS ATTEMPT WAS DESCRIBING, NOT THINKING 🚨
Internal voice must be INTERNAL THOUGHTS, not scene descriptions or action narration.

ABSOLUTE REQUIREMENTS:
- Address the character as "you" or by their name - NEVER use "I", "my", "we", "our", or "us"
- Express THOUGHTS, FEELINGS, REACTIONS - not descriptions
- NO "you see", "you hear", "you notice", "you walk", "you move"
- NO "he/she/they walks/says/moves/looks"
- NO "the room is", "the area is", "the space is"
- ONLY internal monologue: opinions, memories, concerns, observations ABOUT the situation

GOOD: "Well... that went better than you expected."
GOOD: "Something feels off here. Stay careful."
BAD: "You see the door open slowly." (This is narration, not thought)
BAD: "He walks toward you." (This is description, not thought)
"""
                
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": retry_prompt}],
                    model=OpenRouterConfig.get_model_for_role("narration"),
                    temperature=0.8,  # Higher temp for more creative comments
                    max_tokens=300,
                    max_retries=RetryConfig.CRITICAL_MAX_RETRIES,
                    call_name="VOICE_COMMENT"
                )
                
                result = extract_and_parse_json(response)
                
                if not result:
                    if attempt == max_retries:
                        return self._create_fallback_voice("comment", interpretation.urgency)
                    continue
                
                voice_text = result.get("internal_voice", "")
                
                # Validate that voice is THINKING not DESCRIBING
                is_describing, detected_indicator = self._check_if_describing(voice_text, actor_name=actor_name)
                
                if is_describing and attempt < max_retries:
                    # Retry with stricter prompt
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING DETECTED (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[INTERNAL VOICE] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_describing:
                    # Final attempt still has issues - log but return anyway
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING PERSISTS after {max_retries + 1} attempts: '{detected_indicator}'")

                ungrounded = self._find_ungrounded_proper_nouns(
                    voice_text,
                    allowed_context=f"{scene_description}\n\n{worldbuilding_context}",
                )
                if ungrounded and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ UNGROUNDED NAMES in COMMENT (attempt {attempt + 1}): {ungrounded}")
                    prompt = prompt + (
                        "\n\nCRITICAL: Do not introduce new named places/organizations/items as facts in internal voice. "
                        f"Avoid these ungrounded names: {', '.join(ungrounded)}.\n"
                    )
                    continue
                
                self._track_output(voice_text)
                
                return {
                    "function": "comment",
                    "voice_text": voice_text,
                    "comment_type": result.get("comment_type", "observation"),
                    "personality_elements": result.get("personality_elements_shown", []),
                    "urgency": interpretation.urgency
                }
                
            except Exception as e:
                self.logger.error(f"Error generating comment voice (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return self._create_fallback_voice("comment", interpretation.urgency)
    
    def _generate_task_goal_reminder_voice(self,
                                        interpretation: VoiceInterpretation,
                                        personality_prompt: str,
                                        actor_name: str,
                                        scene_description: str,
                                        current_goal: str,
                                        current_task: str,
                                        time_context: Dict[str, Any] = None,
                                        session_id: str = None) -> Dict[str, Any]:
        """Generate internal voice for TASK_GOAL_REMINDER function.
        
        This creates diegetic reminders when the user is drifting from their
        current goal or task. Should feel like suddenly remembering what
        they were supposed to be doing.
        """
        drift_severity = interpretation.drift_severity or "moderate"
        
        # Get worldbuilding context for setting-appropriate reminders
        worldbuilding_context = self._get_worldbuilding_context(
            query=f"{current_goal or current_task} {scene_description[:100]} daily life priorities time management",
            max_tokens=200
        )
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (CRITICAL - Reminders must be setting-appropriate):**
{worldbuilding_context}

**SETTING ENFORCEMENT (CRITICAL):**
Reminders MUST reference only concepts, priorities, and time pressures that exist in the worldbuilding context above.
- NEVER use anachronistic concepts that don't exist in the setting
- ALWAYS match the era, culture, and technology level described
"""
        
        # Format time context
        time_section = self._format_time_context(time_context)
        
        # Determine drift language based on severity
        if drift_severity == "mild":
            drift_prompt = "A gentle nudge - the character is slightly off-track but not drastically"
        elif drift_severity == "moderate":
            drift_prompt = "A noticeable drift - the character has been doing unrelated things for a while"
        else:  # severe
            drift_prompt = "Significant drift - the character is far off course and really needs to refocus"
        
        grounding_section = self._build_soft_grounding_rules(
            scene_description=scene_description,
            worldbuilding_context=worldbuilding_context,
            available_memories=None,
        )
        
        prompt = f"""Generate an internal voice reminder about current goal/task.

**IDENTITY (CRITICAL):**
- You are {actor_name}.
- Do NOT refer to yourself by name.
- NEVER treat {actor_name} as a separate person you can see or evaluate.
- Address the character as "you" or by their name. NEVER use "we", "us", "our", "I", or "my".

**DIEGESIS (CRITICAL):**
- Never mention maps, UI, prompts, system, simulation, or any meta concepts.

**MENTION TAGGING (CRITICAL):**
- If you mention a PERSON who is not physically present in the current scene, prefix their name with '@'.
- Examples: '@Franz', '@Magda Voss', '@Brother Matthias'.
- If you are referring to an off-screen person ONLY by a ROLE/TITLE (name unknown), tag it as '@{{role}}'.
- Examples: '@{{mentor}}', '@{{best friend}}', '@{{captain}}'.
- Do NOT tag common nouns unless it is clearly referring to a specific off-screen person (name or role).

**CURRENT GOAL:** {current_goal or 'None set'}
**CURRENT TASK:** {current_task or 'None set'}

**DRIFT SEVERITY:** {drift_severity}
- {drift_prompt}

**SCENE:**
{scene_description[:300]}
{time_section}{worldbuilding_section}
{grounding_section}
{personality_prompt}

{self.PERSONALITY_EFFECTS_CONDENSED}

**ANTI-REPETITION - DO NOT USE THESE PHRASES:**
{self._get_anti_repetition_list()}

**TASK REMINDER GUIDELINES:**

The internal voice should feel like SUDDENLY REMEMBERING what they were supposed to do:
1. Natural, diegetic realization - not a system notification
2. Should reflect the character's actual priorities and values
3. Match the drift severity (gentle nudge vs urgent refocus)
4. Show personality in HOW they think about goals

**🚨 CRITICAL: SOUND LIKE ACTUAL THOUGHTS, NOT NARRATION 🚨**

Task reminders must sound like how a REAL PERSON actually remembers their priorities - casual, sudden, sometimes with mild frustration or self-deprecation.

❌ BAD (sounds like a system prompt or to-do list):
- "Reminder: Your current goal is to find the documents."
- "Task: You should be meeting Sarah at 3pm."
- "Objective incomplete. Return to mission."

❌ BAD (too literary - sounds like narration):
- "The weight of forgotten purpose settles upon your shoulders..."
- "Lost in the mists of distraction, you suddenly recall your true path..."

✅ GOOD (sounds like actual thought):
- "Wait... weren't you supposed to be looking for something?"
- "Damn, you've been chatting forever. Find those papers."
- "What are you doing? Oh right - the meeting. Get moving."
- "This is taking too long. You said you'd meet them by now."

**REMINDER PATTERNS:**
- Sudden realization: "Wait..."
- Mild self-criticism: "You've been distracted..."
- Time pressure: "We should get going..."
- Goal refocus: "The [goal] - we need to..."
- Task urgency: "We can't forget about..."

**PERSONALITY IN REMINDERS:**
- High C (Conscientious): Frustrated with self for getting distracted, anxious about time
- Low C: Casual "oh right" realization, less stress about delay
- High N (Neurotic): Worried about consequences, anxious about time passing
- Low N: Calm acknowledgment, no stress
- High A: Considering how delay affects others
- Low A: Self-focused irritation about own wasted time
- J types: Decisive "you need to" statements
- P types: Exploring "maybe you should" or "what if you"

**CRITICAL:** Address the character as "you" or by their name. NEVER use "I", "my", "we", "our", or "us"

**VOICE URGENCY:** {interpretation.urgency}
- calm: Gentle realization, no rush
- normal: Natural "oh right" moment
- urgent: Growing concern about delay
- frantic: Realization that time is critically short

**Response Format:**
Return JSON:

{{
    "internal_voice": "The task-remembering internal monologue (1-2 sentences)",
    "reminder_type": "sudden_realization/self_criticism/time_pressure/goal_refocus/task_urgency",
    "refocus_urgency": "low/medium/high",
    "suggested_action": "Brief suggestion of what to do next"
}}
"""
        
        # ═══════════════════════════════════════════════════════════════════
        # INTERNAL VOICE VALIDATION WITH REGENERATION
        # Retry up to 2 times if voice is describing instead of thinking
        # ═══════════════════════════════════════════════════════════════════
        max_retries = 2
        
        for attempt in range(max_retries + 1):
            try:
                retry_prompt = prompt
                if attempt > 0:
                    retry_prompt = prompt + self._get_retry_instructions(attempt)
                
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": retry_prompt}],
                    model=OpenRouterConfig.get_model_for_role("narration"),
                    temperature=0.7,
                    max_tokens=400,
                    max_retries=RetryConfig.CRITICAL_MAX_RETRIES,
                    call_name="VOICE_TASK_REMINDER"
                )
                
                result = extract_and_parse_json(response)
                
                if not result:
                    if attempt == max_retries:
                        return self._create_fallback_voice("task_goal_reminder", interpretation.urgency)
                    continue
                
                voice_text = result.get("internal_voice", "")
                
                # Validate that voice is THINKING not DESCRIBING
                is_describing, detected_indicator = self._check_if_describing(voice_text, actor_name=actor_name)
                
                if is_describing and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING DETECTED in TASK_REMINDER (attempt {attempt + 1}): '{detected_indicator}'")
                    print(f"[INTERNAL VOICE] 🔄 Regenerating with stricter constraints...")
                    continue
                elif is_describing:
                    print(f"[INTERNAL VOICE] ⚠️ DESCRIBING PERSISTS in TASK_REMINDER after {max_retries + 1} attempts: '{detected_indicator}'")

                ungrounded = self._find_ungrounded_proper_nouns(
                    voice_text,
                    allowed_context=f"{scene_description}\n\n{worldbuilding_context}\n\n{current_goal}\n\n{current_task}",
                )
                if ungrounded and attempt < max_retries:
                    print(f"[INTERNAL VOICE] ⚠️ UNGROUNDED NAMES in TASK_REMINDER (attempt {attempt + 1}): {ungrounded}")
                    prompt = prompt + (
                        "\n\nCRITICAL: Do not invent new named places/organizations/people in reminders. "
                        f"Avoid these ungrounded names: {', '.join(ungrounded)}. "
                        "Keep reminders focused on the goal/task itself.\n"
                    )
                    continue
                
                self._track_output(voice_text)
                
                return {
                    "function": "task_goal_reminder",
                    "voice_text": voice_text,
                    "reminder_type": result.get("reminder_type", "sudden_realization"),
                    "refocus_urgency": result.get("refocus_urgency", "medium"),
                    "suggested_action": result.get("suggested_action", ""),
                    "urgency": interpretation.urgency,
                    "drift_severity": drift_severity
                }
                
            except Exception as e:
                self.logger.error(f"Error generating task reminder voice (attempt {attempt + 1}): {e}")
                if attempt == max_retries:
                    return self._create_fallback_voice("task_goal_reminder", interpretation.urgency)

    def _check_if_describing(self, voice_text: str, actor_name: Optional[str] = None) -> tuple:
        """
        Check if internal voice is DESCRIBING instead of THINKING.
        
        Returns:
            tuple: (is_describing: bool, detected_indicator: str or None)
        """
        if not voice_text:
            return False, None
        
        voice_lower = voice_text.lower()

        # Self-identity leak: internal voice should not refer to the UA by their own name.
        # If the model uses the UA name, it often treats the UA as a separate observed entity.
        try:
            if actor_name:
                nm = str(actor_name).strip().lower()
                if nm and nm in voice_lower:
                    return True, f"self-name: {actor_name}"
        except Exception:
            pass
        
        # Patterns that indicate DESCRIBING instead of THINKING
        description_indicators = [
            # Third person descriptions
            'he walks', 'she walks', 'they walk', 'he says', 'she says', 'they say',
            'he moves', 'she moves', 'they move', 'he looks', 'she looks', 'they look',
            # Scene descriptions
            'the room is', 'the area is', 'the space is', 'the place is',
            'you see', 'you hear', 'you notice', 'you observe',
            # Action narration
            'you walk', 'you move', 'you step', 'you turn', 'you reach',
            'you grab', 'you take', 'you put', 'you open', 'you close'
        ]
        
        # Meta/UI/system language that breaks diegesis
        meta_indicators = [
            'map', 'dots on the map', 'dot on the map', 'ui', 'user interface', 'hud',
            'system', 'debug', 'metadata', 'prompt', 'llm', 'model', 'simulation',
            'player', 'character sheet', 'stats', 'initiative', 'turn order'
        ]
        
        for indicator in description_indicators:
            if indicator in voice_lower:
                return True, indicator
        
        for indicator in meta_indicators:
            if indicator in voice_lower:
                return True, f"meta: {indicator}"
        
        # Check for overly poetic/literary narration style
        poetic_indicators = [
            # Sensory narration (narrator's job, not thoughts)
            'we breathe', 'we feel the', 'we sense the', 'we taste the', 'we smell the',
            'we hear the', 'we see the', 'we watch the',
            # Overly literary phrases
            'like a promise', 'like a dream', 'like a whisper', 'like a shadow',
            'unfolds before', 'washes over', 'settles upon', 'dances across',
            'tapestry of', 'symphony of', 'canvas of', 'mosaic of',
            'corridors of', 'depths of our', 'echoes of',
            # Purple prose patterns
            'bathed in', 'shrouded in', 'cloaked in', 'draped in',
            'living blueprint', 'quiet strength', 'silent testament'
        ]
        
        # Check for action-planning narration (describing what we'll DO rather than thinking)
        action_narration_indicators = [
            # Future action planning (sounds like narration of intent)
            "we'll check", "we'll need to", "we'll have to", "we'll log", "we'll file",
            "we'll report", "we'll make sure", "we'll verify", "we'll confirm",
            # Procedural narration
            "if one's out, we", "if it's", "when we get there",
            # Environmental observation phrased as narration
            "protocol notices", "strip lights", "must've missed", "night shift",
            # Task-listing (sounds like a to-do list, not thoughts)
            "step one", "step two", "first we", "then we", "next we"
        ]
        
        for indicator in action_narration_indicators:
            if indicator in voice_lower:
                return True, f"action-narration: {indicator}"
        
        for indicator in poetic_indicators:
            if indicator in voice_lower:
                return True, f"poetic: {indicator}"
        
        return False, None
    
    def _get_retry_instructions(self, attempt: int) -> str:
        """Get retry instructions for when internal voice is describing instead of thinking"""
        return f"""

🚨 CRITICAL RETRY #{attempt} - PREVIOUS ATTEMPT WAS NARRATION, NOT THOUGHT 🚨
Internal voice must be INTERNAL THOUGHTS - how a real person actually thinks.

ABSOLUTE REQUIREMENTS:
- Address the character as "you" or by their name - NEVER use "I", "my", "we", "our", or "us"
- Express THOUGHTS, FEELINGS, REACTIONS - not descriptions or action plans
- NO "you see", "you hear", "you notice", "you walk", "you move"
- NO "he/she/they walks/says/moves/looks"
- NO "the room is", "the area is", "the space is"
- NO poetic/literary prose ("like a promise", "unfolds before us", "tapestry of")
- NO sensory descriptions ("you breathe the cold", "you feel the air", "you sense") — describe thoughts, not sensations
- NO action-planning ("we'll check", "we'll log", "we'll need to", "first we", "then we")
- NO procedural task-listing (sounds like a to-do list, not authentic thought)
- ONLY internal monologue: opinions, memories, concerns, emotional reactions

✅ GOOD (sounds like actual thinking):
- "Well... that went better than we expected."
- "Something feels off here. We should be careful."
- "Cold out here. Damn."
- "Finally. About time we got moving."
- "This place gives us the creeps."

❌ BAD (sounds like narration):
- "You see the door open slowly." (narrator voice)
- "He walks toward us." (description)
- "We breathe the cold like a promise." (poetic prose)
- "The morning air washes over us." (sensory narration)
- "We'll check the lights and log it if one's out." (action-planning, not thought)
- "Protocol notices still up, night shift missed a reset." (environmental observation)
"""
    
    def _create_fallback_voice(self, function: str, urgency: str) -> Dict[str, Any]:
        """Create a fallback voice when generation fails"""
        fallbacks = {
            "information": "We... we're not sure. Let us think about that.",
            "solution": "There has to be a way out of this.",
            "memory": "Something about this feels familiar...",
            "comment": "Hmm.",
            "task_goal_reminder": "Wait... what were we doing again?"
        }
        
        return {
            "function": function,
            "voice_text": fallbacks.get(function, "..."),
            "urgency": urgency,
            "is_fallback": True
        }
    
    def _get_anti_repetition_list(self) -> str:
        """Get list of recently used phrases to avoid"""
        if not self.recent_outputs:
            return "None yet"
        
        # Extract key phrases from recent outputs
        phrases = []
        for output in self.recent_outputs[-10:]:
            # Get first few words of each output
            words = output.split()[:5]
            if words:
                phrases.append(" ".join(words) + "...")
        
        return "\n".join(f"- {p}" for p in phrases) if phrases else "None yet"
    
    def _track_output(self, output: str):
        """Track output to prevent repetition"""
        if output:
            self.recent_outputs.append(output)
            if len(self.recent_outputs) > self.max_recent_outputs:
                self.recent_outputs.pop(0)
            
            # Track key phrases
            words = output.lower().split()
            for i in range(len(words) - 2):
                phrase = " ".join(words[i:i+3])
                self.used_phrases.add(phrase)
    
    def _store_memory(self, category: str, content: str, emotional_tone: str):
        """Store a newly created memory"""
        if category not in self.created_memories:
            self.created_memories[category] = []
        
        memory = {
            "content": content,
            "emotional_tone": emotional_tone,
            "created_at": datetime.now().isoformat()
        }
        
        self.created_memories[category].append(memory)
        self._save_created_memories()
    
    def _save_created_memories(self):
        """Save created memories to disk"""
        try:
            mem_file = self.storage_directory / "internal_voice" / "created_memories.json"
            mem_file.parent.mkdir(parents=True, exist_ok=True)
            
            import json
            with open(mem_file, 'w', encoding='utf-8') as f:
                json.dump(self.created_memories, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            self.logger.error(f"Failed to save memories: {e}")
    
    def _load_created_memories(self):
        """Load created memories from disk"""
        try:
            mem_file = self.storage_directory / "internal_voice" / "created_memories.json"
            
            if mem_file.exists():
                import json
                with open(mem_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    
                # Validate and normalize loaded data
                if isinstance(loaded, dict):
                    for category, memories in loaded.items():
                        if isinstance(memories, list):
                            self.created_memories[category] = memories
                        elif isinstance(memories, str):
                            self.created_memories[category] = [{"content": memories, "emotional_tone": "neutral"}]
                        else:
                            self.created_memories[category] = []
                    
        except Exception as e:
            self.logger.warning(f"Could not load memories: {e}")
            # Reset to empty state on error
            self.created_memories = {cat: [] for cat in MEMORY_CATEGORIES.keys()}
    
    def get_memories_for_category(self, category: str) -> List[Dict[str, Any]]:
        """Get all memories for a category"""
        created = self.created_memories.get(category, [])
        starter = [{"content": m, "emotional_tone": "neutral"} 
                   for m in MEMORY_CATEGORIES.get(category, [])]
        return created + starter
    
    def create_initial_memories(self, 
                               actor_name: str,
                               personality_prompt: str,
                               backstory: str = "") -> Dict[str, List[Dict[str, Any]]]:
        """
        Create initial memories for a new actor (at least 2 per category).
        
        This should be called when creating a new UA.
        """
        # Get comprehensive worldbuilding context from RAG for different aspects of life
        rag_queries = [
            f"daily life culture society {backstory[:50]}",
            "family relationships marriage children home life",
            "jobs occupations work careers employment",
            "education schools training learning institutions",
            "entertainment hobbies recreation leisure activities",
            "religion beliefs philosophy morality values",
            "fears dangers threats common phobias",
            "hopes dreams aspirations goals ambitions",
            "secrets crime underground hidden society",
            "locations places cities neighborhoods landmarks"
        ]
        
        worldbuilding_parts = []
        for query in rag_queries:
            context = self._get_worldbuilding_context(query, max_tokens=200)
            if context:
                worldbuilding_parts.append(context)
        
        # Deduplicate and combine
        seen = set()
        unique_parts = []
        for part in worldbuilding_parts:
            # Use first 100 chars as key to avoid near-duplicates
            key = part[:100]
            if key not in seen:
                seen.add(key)
                unique_parts.append(part)
        
        worldbuilding_context = "\n\n".join(unique_parts[:8])  # Limit to avoid token overflow
        
        worldbuilding_section = ""
        if worldbuilding_context:
            worldbuilding_section = f"""
**WORLDBUILDING CONTEXT (memories MUST reference specific details from this setting):**
{worldbuilding_context}

IMPORTANT: Use specific names, places, technologies, organizations, and cultural elements from the worldbuilding above.
Do NOT invent generic sci-fi/fantasy elements - ground every memory in THIS world's details.

"""
        
        base_prompt = f"""Create initial memories for this character across multiple categories.

**CHARACTER:** {actor_name}
**BACKSTORY:** {backstory}

{personality_prompt}
{worldbuilding_section}
**MEMORY CATEGORIES (create 2 memories each):**
1. family - Memories about parents, siblings, relatives
2. job - Work-related memories, colleagues, career moments
3. friends - Friendship memories, companions, allies
4. trauma - Difficult/painful memories that still affect them
5. achievement - Proud moments, victories, accomplishments
6. relationship - Romantic or deeply intimate relationship memories
7. location - Places that matter, homes, meaningful spots
8. childhood - Growing up memories, formative early experiences
9. education - School, training, learning moments
10. loss - Things/people lost, grief, endings
11. hobbies - Passions, interests, things they do for joy
12. beliefs - Moral moments, values tested, philosophical realizations
13. secrets - Hidden truths, guilt, things never shared
14. fears - Moments of terror, phobias discovered, dread
15. dreams - Aspirations, hopes for the future, ambitions

**CRITICAL:** All memories must be appropriate to the setting and time period from the worldbuilding context.
Do NOT include anachronistic technology, events, or cultural references.

**Response Format:**
Return JSON with EXACTLY this structure - 2 memories per category, 15 categories total (30 memories):

{{
    "family": [
        {{"content": "Specific memory about family member", "emotional_tone": "warm"}},
        {{"content": "Another family memory", "emotional_tone": "bittersweet"}}
    ],
    "job": [
        {{"content": "Work-related memory", "emotional_tone": "stressful"}},
        {{"content": "Another work memory", "emotional_tone": "proud"}}
    ],
    "friends": [
        {{"content": "Memory with a friend", "emotional_tone": "happy"}},
        {{"content": "Another friendship memory", "emotional_tone": "nostalgic"}}
    ],
    "trauma": [
        {{"content": "Difficult memory", "emotional_tone": "painful"}},
        {{"content": "Another hard memory", "emotional_tone": "haunting"}}
    ],
    "achievement": [
        {{"content": "Proud moment", "emotional_tone": "triumphant"}},
        {{"content": "Another achievement", "emotional_tone": "satisfied"}}
    ],
    "relationship": [
        {{"content": "Romantic or close relationship memory", "emotional_tone": "tender"}},
        {{"content": "Another relationship memory", "emotional_tone": "longing"}}
    ],
    "location": [
        {{"content": "Memory tied to a place", "emotional_tone": "peaceful"}},
        {{"content": "Another location memory", "emotional_tone": "melancholic"}}
    ],
    "childhood": [
        {{"content": "Growing up memory", "emotional_tone": "innocent"}},
        {{"content": "Another childhood memory", "emotional_tone": "formative"}}
    ],
    "education": [
        {{"content": "School or learning memory", "emotional_tone": "curious"}},
        {{"content": "Another education memory", "emotional_tone": "challenging"}}
    ],
    "loss": [
        {{"content": "Memory of something lost", "emotional_tone": "grief"}},
        {{"content": "Another loss memory", "emotional_tone": "acceptance"}}
    ],
    "hobbies": [
        {{"content": "Memory of a passion or interest", "emotional_tone": "joyful"}},
        {{"content": "Another hobby memory", "emotional_tone": "absorbed"}}
    ],
    "beliefs": [
        {{"content": "Moment that shaped their values", "emotional_tone": "resolute"}},
        {{"content": "Another moral/philosophical memory", "emotional_tone": "conflicted"}}
    ],
    "secrets": [
        {{"content": "Something they hide from others", "emotional_tone": "guilty"}},
        {{"content": "Another secret memory", "emotional_tone": "shameful"}}
    ],
    "fears": [
        {{"content": "Moment of terror or dread", "emotional_tone": "terrified"}},
        {{"content": "Another fear memory", "emotional_tone": "anxious"}}
    ],
    "dreams": [
        {{"content": "A hope or aspiration", "emotional_tone": "hopeful"}},
        {{"content": "Another dream/ambition memory", "emotional_tone": "determined"}}
    ]
}}

CRITICAL: You MUST include ALL 15 categories with 2 memories each. Each memory should be 2-4 sentences.
Make memories specific to this character's personality, backstory, and the setting.
"""
        
        # Retry loop for malformed responses
        max_format_retries = 3
        expected_categories = {"family", "job", "friends", "trauma", "achievement", 
                              "relationship", "location", "childhood", "education", "loss",
                              "hobbies", "beliefs", "secrets", "fears", "dreams"}
        
        result = None
        grounding_violations: list[str] = []
        strict_grounding = (os.getenv('REALITAS_STRICT_GROUNDING', '') or '').strip().lower() in ('1', 'true', 'yes', 'on')
        try:
            for format_attempt in range(max_format_retries):
                grounding_note = ""
                if grounding_violations:
                    bad = ", ".join(grounding_violations[:25])
                    grounding_note = f"""

CRITICAL RAG LOCK (HARD):
- You previously introduced proper nouns/entities not present in the provided WORLDBUILDING CONTEXT.
- You MUST NOT invent any new places, factions, organizations, landmarks, technologies, or named people.
- Do NOT use these ungrounded proper nouns again: {bad}
- Only reuse proper nouns that already appear in WORLDBUILDING CONTEXT or in the character name/backstory.
""".rstrip()

                prompt = f"{base_prompt}{grounding_note}".strip()
                response = robust_llm_call(
                    client=self.client,
                    messages=[{"role": "user", "content": prompt}],
                    model=OpenRouterConfig.get_model_for_role("memory_creation"),
                    temperature=0.7 + (format_attempt * 0.1),  # Slightly increase temp on retries
                    max_tokens=6000,  # Increased for 30 detailed memories (15 categories x 2)
                    max_retries=RetryConfig.MAX_RETRIES,
                    call_name="CREATE_INITIAL_MEMORIES"
                )
                
                result = extract_and_parse_json(response)
                
                # Validate the result structure - should have category keys, not "content"/"emotional_tone"
                if result and isinstance(result, dict):
                    # Check if LLM returned a single memory instead of categorized memories
                    if "content" in result and "emotional_tone" in result and len(result) <= 3:
                        # LLM returned a single memory object - retry
                        self.logger.warning(f"LLM returned single memory instead of categorized memories (attempt {format_attempt + 1}/{max_format_retries})")
                        if format_attempt < max_format_retries - 1:
                            continue  # Retry
                        else:
                            # Last attempt - use fallback
                            result = {"general": [result]}
                    
                    # Check if we have actual category keys
                    found_categories = set(result.keys()) & expected_categories
                    
                    if not found_categories:
                        self.logger.warning(f"No expected categories found in result. Keys: {list(result.keys())} (attempt {format_attempt + 1}/{max_format_retries})")
                        if format_attempt < max_format_retries - 1:
                            continue  # Retry
                    else:
                        # Success - we have valid categories; now enforce grounding per-category and selectively regenerate.
                        grounding_violations = []
                        allowed_context = f"{actor_name}\n{backstory}\n\n{worldbuilding_context}".strip()

                        def _violations_for_text(txt: str) -> list[str]:
                            v: list[str] = []
                            try:
                                if txt and allowed_context:
                                    v = self._find_ungrounded_proper_nouns(txt, allowed_context=allowed_context)
                                    if strict_grounding:
                                        v.extend([p for p in self._find_ungrounded_entity_phrases(txt, allowed_context=allowed_context) if p not in v])
                                        rag_missing: list[str] = []
                                        for term in v[:40]:
                                            if not self._term_exists_in_rag_anywhere(term):
                                                rag_missing.append(term)
                                        v = rag_missing
                            except Exception:
                                return []
                            return v

                        # Identify failing categories (regenerate whole category if any of its 2 memories fails).
                        failing_categories: list[str] = []
                        per_cat_violations: dict[str, list[str]] = {}
                        try:
                            for cat in sorted(list(found_categories)):
                                mems = result.get(cat)
                                if not isinstance(mems, list):
                                    continue
                                cat_texts: list[str] = []
                                for mem in mems:
                                    if isinstance(mem, dict):
                                        cat_texts.append(str(mem.get('content', '') or ''))
                                    elif isinstance(mem, str):
                                        cat_texts.append(str(mem))
                                cat_text = "\n".join([t for t in cat_texts if t.strip()])
                                v = _violations_for_text(cat_text)
                                if v:
                                    failing_categories.append(cat)
                                    per_cat_violations[cat] = v
                                    grounding_violations.extend([x for x in v if x not in grounding_violations])
                        except Exception:
                            failing_categories = []
                            per_cat_violations = {}
                            grounding_violations = []

                        # Selective regeneration loop (keeps passing categories).
                        max_regen_passes = 2
                        regen_pass = 0
                        while failing_categories and regen_pass < max_regen_passes and self.rag_system:
                            regen_pass += 1
                            bad_summary = "; ".join([f"{c}: {', '.join(per_cat_violations.get(c, [])[:6])}" for c in failing_categories[:8]])
                            regen_prompt = f"""Regenerate ONLY the following memory categories for this character.

**CHARACTER:** {actor_name}
**BACKSTORY:** {backstory}

{personality_prompt}
{worldbuilding_section}

CRITICAL RAG LOCK (HARD):
- Do NOT invent any new places, factions, organizations, landmarks, technologies, or named people.
- The following categories had ungrounded entities/phrases and must be rewritten: {', '.join(failing_categories)}
- Examples of what to avoid (not in world context): {bad_summary}

REQUIREMENTS:
- Return JSON with ONLY these keys: {', '.join(failing_categories)}
- Each key MUST contain a list of EXACTLY 2 objects: {{"content": "...", "emotional_tone": "..."}}
- Each memory should be 2-4 sentences and grounded in WORLDBUILDING CONTEXT.
""".strip()

                            regen_response = robust_llm_call(
                                client=self.client,
                                messages=[{"role": "user", "content": regen_prompt}],
                                model=OpenRouterConfig.get_model_for_role("memory_creation"),
                                temperature=0.6,
                                max_tokens=1400,
                                max_retries=RetryConfig.MAX_RETRIES,
                                call_name="CREATE_INITIAL_MEMORIES_REGEN"
                            )
                            regen_result = extract_and_parse_json(regen_response)
                            if not isinstance(regen_result, dict):
                                break

                            # Replace categories that were regenerated.
                            for cat in list(failing_categories):
                                if cat in regen_result and isinstance(regen_result.get(cat), list):
                                    result[cat] = regen_result.get(cat)

                            # Recompute failures.
                            new_failing: list[str] = []
                            new_per_cat: dict[str, list[str]] = {}
                            grounding_violations = []
                            for cat in sorted(list(found_categories)):
                                mems = result.get(cat)
                                if not isinstance(mems, list):
                                    continue
                                cat_texts = []
                                for mem in mems:
                                    if isinstance(mem, dict):
                                        cat_texts.append(str(mem.get('content', '') or ''))
                                    elif isinstance(mem, str):
                                        cat_texts.append(str(mem))
                                v = _violations_for_text("\n".join([t for t in cat_texts if t.strip()]))
                                if v:
                                    new_failing.append(cat)
                                    new_per_cat[cat] = v
                                    grounding_violations.extend([x for x in v if x not in grounding_violations])
                            failing_categories = new_failing
                            per_cat_violations = new_per_cat

                        if grounding_violations and self.rag_system:
                            msg = f"Ungrounded proper nouns in initial memories (attempt {format_attempt + 1}/{max_format_retries}): {grounding_violations[:10]}"
                            try:
                                print(f"[CREATE_INITIAL_MEMORIES] ⚠️ {msg}")
                            except Exception:
                                pass
                            self.logger.warning(msg)

                            # Final attempt: sanitize only failing categories to avoid cementing invented entities.
                            if strict_grounding and isinstance(result, dict):
                                try:
                                    for cat in failing_categories:
                                        mems = result.get(cat)
                                        if not isinstance(mems, list):
                                            continue
                                        for mem in mems:
                                            if isinstance(mem, dict) and mem.get('content'):
                                                mem['content'] = self._sanitize_memory_text(mem['content'], bad_terms=per_cat_violations.get(cat, grounding_violations))
                                except Exception:
                                    pass

                            if format_attempt < max_format_retries - 1:
                                # Only retry full generation if selective regeneration couldn't resolve grounding.
                                continue

                        self.logger.info(f"Successfully generated memories with {len(found_categories)} categories")
                        break  # Exit retry loop
            
            if result and isinstance(result, dict):
                # Merge with existing
                for category, memories in result.items():
                    # Ensure memories is a list
                    if isinstance(memories, str):
                        memories = [{"content": memories, "emotional_tone": "neutral"}]
                    elif not isinstance(memories, list):
                        memories = [{"content": str(memories), "emotional_tone": "neutral"}]
                    
                    # Normalize each item in the list to be a dict
                    normalized_memories = []
                    for mem in memories:
                        if isinstance(mem, str):
                            normalized_memories.append({"content": mem, "emotional_tone": "neutral"})
                        elif isinstance(mem, dict):
                            normalized_memories.append(mem)
                        else:
                            normalized_memories.append({"content": str(mem), "emotional_tone": "neutral"})
                    
                    # Ensure category exists in created_memories
                    if category not in self.created_memories:
                        self.created_memories[category] = []
                    
                    # Ensure it's a list before extending
                    if not isinstance(self.created_memories[category], list):
                        self.created_memories[category] = []
                    
                    self.created_memories[category].extend(normalized_memories)
                
                self._save_created_memories()
                return result
            
            return {}
            
        except Exception as e:
            self.logger.error(f"Error creating initial memories: {e}")
            return {}


# ═══════════════════════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════════════════════

# Global instance
_creator_agent: Optional[InternalVoiceCreatorAgent] = None


def get_voice_creator(storage_directory: Path = None) -> InternalVoiceCreatorAgent:
    """Get or create the global creator agent"""
    global _creator_agent
    if _creator_agent is None:
        _creator_agent = InternalVoiceCreatorAgent(storage_directory)
    return _creator_agent


def generate_internal_voice(interpretation: VoiceInterpretation,
                           scene_description: str,
                           user_action: str,
                           action_outcome: str,
                           personality_prompt: str,
                           actor_name: str,
                           current_goal: str = "") -> Dict[str, Any]:
    """Convenience function to generate internal voice"""
    creator = get_voice_creator()
    return creator.generate_voice(
        interpretation=interpretation,
        scene_description=scene_description,
        user_action=user_action,
        action_outcome=action_outcome,
        personality_prompt=personality_prompt,
        actor_name=actor_name,
        current_goal=current_goal
    )


def display_internal_voice(voice_result: Dict[str, Any]):
    """Display internal voice with appropriate formatting"""
    voice_text = voice_result.get("voice_text", "")
    function = voice_result.get("function", "comment")
    urgency = voice_result.get("urgency", "normal")
    
    if not voice_text:
        return
    
    # Choose color based on urgency
    urgency_colors = {
        "calm": Color.STATUS,
        "normal": Color.INFO,
        "urgent": Color.WARNING,
        "frantic": Color.ERROR
    }
    color = urgency_colors.get(urgency, Color.INFO)
    
    # Function icon
    function_icons = {
        "information": "💡",
        "solution": "🔧",
        "memory": "💭",
        "comment": "🗣️"
    }
    icon = function_icons.get(function, "💭")
    
    print(f"\n{color}    {icon} {voice_text}{Color.RESET}")


# ═══════════════════════════════════════════════════════════════════════════════
# TEST
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("Internal Voice Creator Agent Test\n")
    
    from .internal_voice_interpreter_agent import VoiceInterpretation, InternalVoiceFunction, QuestionType
    
    creator = InternalVoiceCreatorAgent(Path("./test_data"))
    
    # Test personality prompt
    personality_prompt = """**CHARACTER PERSONALITY**
MBTI: INFP - The Mediator
OCEAN: High Openness, High Neuroticism, Low Extraversion
Current Mood: ANXIOUS (strong)
Voice Tone: worried and racing
Core Values: authenticity, creativity
Core Fears: rejection, conflict"""
    
    # Test each function
    test_cases = [
        {
            "name": "Information - Logic Question",
            "interpretation": VoiceInterpretation(
                primary_function=InternalVoiceFunction.INFORMATION,
                question_type=QuestionType.LOGIC,
                question_content="Who is my best friend?",
                urgency="normal"
            )
        },
        {
            "name": "Solution - Predicament",
            "interpretation": VoiceInterpretation(
                primary_function=InternalVoiceFunction.SOLUTION,
                predicament_description="Trapped in a burning building",
                urgency="frantic"
            )
        },
        {
            "name": "Memory - Family Trigger",
            "interpretation": VoiceInterpretation(
                primary_function=InternalVoiceFunction.MEMORY,
                memory_trigger="Seeing an elderly woman",
                memory_category="family",
                urgency="calm"
            )
        },
        {
            "name": "Comment - Personality Flavor",
            "interpretation": VoiceInterpretation(
                primary_function=InternalVoiceFunction.COMMENT,
                urgency="normal"
            )
        }
    ]
    
    print("=== Voice Generation Tests ===\n")
    
    for test in test_cases:
        print(f"Test: {test['name']}")
        
        result = creator.generate_voice(
            interpretation=test["interpretation"],
            scene_description="You're standing in a quiet park at sunset.",
            user_action="I look around",
            action_outcome="You see the peaceful scenery",
            personality_prompt=personality_prompt,
            actor_name="Alex",
            current_goal="Find meaning in life"
        )
        
        print(f"  Function: {result.get('function')}")
        print(f"  Urgency: {result.get('urgency')}")
        print(f"  Voice: {result.get('voice_text', 'None')[:100]}...")
        print()
    
    print("✅ Internal Voice Creator Agent ready!")
