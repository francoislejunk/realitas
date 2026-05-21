import json
from actor_sheet import ActorSheet, SFactors, Item, StatusType
from actors import NonUserActor, UserActor, InanimateNonUserActor
from openrouter_config import create_role_client, OpenRouterConfig, retry_with_backoff, RetryConfig, robust_llm_call
from json_utils import _fix_json_formatting
from rag_lock_utils import get_multi_category_context_for_llm
# RAG system will provide all world context dynamically
# No more hardcoded world_context imports needed

# Import category enum for filtered RAG queries
try:
    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
except ImportError:
    WorldbuildingCategory = None  # Graceful fallback if not available

class CreatorAgent:
    """Manages scenes by dynamically generating them using an LLM."""

    def __init__(self, logger, rag_system=None, key_memories_system=None, narrative_context_manager=None, fact_system=None, mention_system=None):
        self.logger = logger
        self.rag_system = rag_system  # RAG system for worldbuilding context
        self.key_memories_system = key_memories_system  # For user memories
        self.narrative_context_manager = narrative_context_manager  # For concrete details and narrative history
        self.fact_system = fact_system  # For canonical facts
        self.mention_system = mention_system  # For actor mention tracking
        self.current_scene = None
        self.time_context = None  # Current time context for temporal awareness
        # Set a 5-minute timeout for the client
        self.client = create_role_client("scene_creation")
        self.model = OpenRouterConfig.get_model_for_role("scene_creation")

        # Warn if RAG system not provided
        if not self.rag_system:
            self.logger.log_system("WARNING: CreatorAgent initialized without RAG system. World context will be minimal.")

    def _get_actor_facts(self, actor_name: str, max_facts: int = 10) -> str:
        """
        Get formatted fact context for an actor to inject into prompts.
        Prevents contradictions by informing LLM of established facts.
        """
        if not self.fact_system:
            return ""

        try:
            context = self.fact_system.get_fact_context(actor_name, max_facts=max_facts)
            if context:
                return f"\n{context}\n"
            return ""
        except Exception as e:
            self.logger.log_system(f"WARNING: Could not fetch facts for {actor_name}: {e}")
            return ""

    def _establish_nua_facts(self, nua: 'NonUserActor', source: str = "nua_creation", turn_number: int = 0, scene_id: str = ""):
        """
        Establish canonical facts after NUA creation.
        Records actor identity, traits, possessions as facts.
        """
        if not self.fact_system:
            return

        try:
            from fact_system import FactType, FactAuthority

            actor_name = nua.sheet.name

            # Establish occupation fact
            if nua.sheet.occupation and nua.sheet.occupation not in ('Unknown', 'None'):
                self.fact_system.establish_fact(
                    fact_type=FactType.ACTOR_IDENTITY,
                    subject=actor_name,
                    predicate="occupation",
                    value=nua.sheet.occupation,
                    authority=FactAuthority.SYSTEM_CANONICAL,
                    source=source,
                    tags=[actor_name.lower(), "occupation"],
                    turn_number=turn_number,
                    scene_id=scene_id
                )

            # Establish faction fact
            if nua.sheet.faction and nua.sheet.faction not in ('None', 'none', ''):
                self.fact_system.establish_fact(
                    fact_type=FactType.ACTOR_IDENTITY,
                    subject=actor_name,
                    predicate="faction",
                    value=nua.sheet.faction,
                    authority=FactAuthority.SYSTEM_CANONICAL,
                    source=source,
                    tags=[actor_name.lower(), "faction"],
                    turn_number=turn_number,
                    scene_id=scene_id
                )

            # Establish age fact
            if hasattr(nua.sheet, 'age') and nua.sheet.age:
                self.fact_system.establish_fact(
                    fact_type=FactType.ACTOR_TRAIT,
                    subject=actor_name,
                    predicate="age",
                    value=nua.sheet.age,
                    authority=FactAuthority.SYSTEM_CANONICAL,
                    source=source,
                    tags=[actor_name.lower(), "age"],
                    turn_number=turn_number,
                    scene_id=scene_id
                )

            # Establish key personality traits as facts
            if nua.sheet.personality_traits:
                internal = nua.sheet.personality_traits.get('internal', [])
                if internal and len(internal) > 0:
                    # Take first internal trait as key personality
                    trait = internal[0] if isinstance(internal, list) else internal
                    self.fact_system.establish_fact(
                        fact_type=FactType.ACTOR_TRAIT,
                        subject=actor_name,
                        predicate="personality",
                        value=trait,
                        authority=FactAuthority.SYSTEM_CANONICAL,
                        source=source,
                        tags=[actor_name.lower(), "personality"],
                        turn_number=turn_number,
                        scene_id=scene_id
                    )

            # Establish key possessions (from inventory)
            for item in nua.sheet.inventory[:3]:  # Limit to first 3 items
                if hasattr(item, 'name') and item.name:
                    self.fact_system.establish_fact(
                        fact_type=FactType.ACTOR_POSSESSION,
                        subject=actor_name,
                        predicate="owns",
                        value=item.name,
                        authority=FactAuthority.SYSTEM_CANONICAL,
                        source=source,
                        tags=[actor_name.lower(), "possession", "inventory"],
                        turn_number=turn_number,
                        scene_id=scene_id
                    )

            self.logger.log_system(f"Established facts for NUA: {actor_name}")

        except Exception as e:
            self.logger.log_system(f"WARNING: Could not establish facts for NUA {getattr(nua, 'name', 'Unknown')}: {e}")

    def _get_actor_mention_context(self, actor_name: str, max_mentions: int = 5) -> str:
        """
        Get formatted mention context for an actor to inject into prompts.
        Shows where actor was last mentioned to prevent contradictions.
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

    def _record_nua_mention(self, nua: 'NonUserActor', location: str, context: str,
                           turn_number: int = 0, scene_id: str = ""):
        """
        Record mention when NUA is created.
        Creates PHYSICAL_PRESENCE mention with SCENE_DESCRIPTION source.
        """
        if not self.mention_system:
            return

        try:
            from mention_system import MentionType, MentionSource

            actor_name = nua.sheet.name

            # Record physical presence at creation location
            mention_id = self.mention_system.record_physical_presence(
                actor_name=actor_name,
                location=location,
                context=context or f"{actor_name} appears in the scene",
                source=MentionSource.SCENE_DESCRIPTION,
                turn_number=turn_number,
                scene_id=scene_id
            )

            self.logger.log_system(f"Recorded mention for NUA: {actor_name} at {location} (mention_id: {mention_id})")

        except Exception as e:
            self.logger.log_system(f"WARNING: Could not record mention for {actor_name}: {e}")

    def _format_time_context(self, time_context=None) -> str:
        """Format time context for inclusion in prompts."""
        tc = time_context or self.time_context
        
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
        period = tc.get('time_of_day', '') or tc.get('period', '')
        
        parts = []
        if time_str:
            parts.append(f"Current Time: {time_str}")
        if day:
            parts.append(f"Day: {day}")
        if period:
            parts.append(f"Time of Day: {period}")
        
        if parts:
            return f"""
**TIME CONTEXT (Generate content appropriate for this time):**
{chr(10).join(parts)}
"""
        return ""

    def _extract_bulleted_lines(self, text: str) -> list[str]:
        if not text:
            return []
        try:
            from rag_lock_utils import extract_rag_list_items
            return extract_rag_list_items(text)
        except Exception:
            return []

    def _extract_faction_names(self, text: str) -> list[str]:
        if not text:
            return []
        import re

        allowed: list[str] = []
        for raw in str(text).splitlines():
            s = raw.strip()
            if not s:
                continue
            if s.startswith(('-', '•', '*')):
                s = s.lstrip('-•*').strip()
            if not s:
                continue
            if s.startswith('**') and s.endswith('**'):
                continue
            if s.lower().startswith(('supporting cast', 'hunter compacts', 'vampire', 'cainite', 'factions', 'clans')):
                continue
            m = re.match(r'^([^:]{2,80}):\s*', s)
            if not m:
                continue
            name = m.group(1).strip()
            if not name:
                continue
            if name not in allowed:
                allowed.append(name)
        return allowed

    def _get_explicit_faction_whitelist(self, actor_type: str) -> list[str]:
        if not self.rag_system or not WorldbuildingCategory:
            return []

        actor_type_s = (actor_type or '').strip().lower()
        category = None
        if actor_type_s == 'ua':
            category = WorldbuildingCategory.FACTION_UA
        elif actor_type_s == 'nua':
            category = WorldbuildingCategory.FACTION_NUA
        else:
            category = WorldbuildingCategory.FACTION_MNUA

        docs = []
        try:
            if hasattr(self.rag_system, 'get_by_category'):
                docs = self.rag_system.get_by_category(category)
        except Exception:
            docs = []

        if docs:
            allowed: list[str] = []
            for doc in docs:
                content = getattr(doc, 'content', '') or ''
                for nm in self._extract_faction_names(content):
                    if nm not in allowed:
                        allowed.append(nm)
            return allowed

        try:
            ctx = self._get_rag_context(
                query="factions clans organizations",
                max_tokens=1200,
                category_filter=category
            )
            return self._extract_faction_names(ctx)
        except Exception:
            return []

    def _validate_mode_a_faction_or_raise(self, *, faction: str, allowed: list[str], label: str) -> None:
        f = (faction or '').strip()
        if not f:
            f = 'None'
        if f == 'None':
            return None
        if allowed and f not in allowed:
            raise ValueError(f"Mode A faction whitelist violation ({label}): {f}")
        return None

    def _get_explicit_goal_whitelist(self, actor_type: str) -> list[str]:
        if not self.rag_system or not WorldbuildingCategory:
            return []

        actor_type_s = (actor_type or '').strip().lower()
        category = None
        if actor_type_s == 'ua':
            category = WorldbuildingCategory.GOALS_UA
        elif actor_type_s == 'nua':
            category = WorldbuildingCategory.GOALS_NUA
        else:
            category = WorldbuildingCategory.GOALS_MNUA

        docs = []
        try:
            if hasattr(self.rag_system, 'get_by_category'):
                docs = self.rag_system.get_by_category(category)
        except Exception:
            docs = []

        if docs:
            allowed: list[str] = []
            for doc in docs:
                content = getattr(doc, 'content', '') or ''
                for ln in self._extract_bulleted_lines(content):
                    if ln not in allowed:
                        allowed.append(ln)
            return allowed

        try:
            ctx = self._get_rag_context(
                query="explicit goal library whitelist goals",
                max_tokens=1200,
                category_filter=category
            )
            return self._extract_bulleted_lines(ctx)
        except Exception:
            return []

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

    def _get_mode_b_vocab(self) -> tuple[list[str], list[str]]:
        """Returns (allowed_skills, allowed_items) extracted from MECHANICS docs, if present."""
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
                combined = self._get_rag_context(
                    query="skills vocab items vocab mechanics",
                    max_tokens=800,
                    category_filter=WorldbuildingCategory.MECHANICS,
                )
            except Exception:
                combined = ""

        if not combined:
            return ([], [])

        def _scan_vocab(header_prefix: str) -> list[str]:
            """Scan lines after a header like 'SKILLS VOCAB (Mode B):' until a blank line or a new all-caps header."""
            lines_out: list[str] = []
            in_section = False
            # Normalize the prefix for easier matching
            normalized_prefix = header_prefix.lower().rstrip(':').strip()
            
            for raw_ln in combined.splitlines():
                ln = (raw_ln or '').strip()
                if not ln:
                    # Keep looking for items if we are in section, but don't break yet
                    continue

                ln_lower = ln.lower()
                # Check if this line is the header we want (allowing for suffixes like ' (Allowed)')
                if not in_section and normalized_prefix in ln_lower and (':' in ln or '**' in ln):
                    in_section = True
                    continue

                if not in_section:
                    continue

                # Stop if we hit another section header (all caps with colon, or starting with '**')
                # Examples: 'ITEMS VOCAB (Mode B):', '**AGE RANGE:**'
                is_new_header = (':' in ln and ln.isupper()) or (ln.startswith('**') and ln.endswith('**'))
                if is_new_header:
                    # Only break if it's NOT the header we are currently scanning
                    if normalized_prefix not in ln_lower:
                        break

                if not ln.startswith('-'):
                    continue

                val = ln.lstrip('-').strip()
                if val and val not in lines_out:
                    lines_out.append(val)

            return lines_out

        allowed_skills = _scan_vocab('SKILLS VOCAB (Mode B)')
        allowed_items = _scan_vocab('ITEMS VOCAB (Mode B)')

        try:
            import os
            if os.environ.get('REALITAS_RAG_TRACE'):
                self.logger.log_system(
                    f"RAG_TRACE ModeB vocab extracted: skills={len(allowed_skills)} items={len(allowed_items)} "
                    f"skills_sample={allowed_skills[:5]} items_sample={allowed_items[:5]}"
                )
        except Exception:
            pass
        return (allowed_skills, allowed_items)

    def _validate_mode_b_terms_or_raise(self, *, skills: dict, inventory: list, label: str) -> None:
        try:
            import os
            # Mode B validation is brittle with LLM generation and can hard-fail character creation.
            # Default to disabled to avoid startup crashes; enable explicitly if desired.
            if os.environ.get('REALITAS_MODE_B_VALIDATION', '0').strip().lower() not in ('1', 'true', 'yes', 'on'):
                return None
        except Exception:
            return None

        if not self.rag_system:
            raise ValueError(f"RAG system not available for Mode B validation ({label})")

        missing: list[str] = []

        allowed_skills, allowed_items = self._get_mode_b_vocab()
        
        # Log extracted vocab if trace is enabled
        try:
            import os
            if os.environ.get('REALITAS_RAG_TRACE'):
                self.logger.log_system(f"DEBUG ModeB: Allowed Skills: {allowed_skills}")
                self.logger.log_system(f"DEBUG ModeB: Allowed Items: {allowed_items}")
        except Exception:
            pass

        def _is_allowed_skill(name: str) -> bool:
            if not name: return True
            # Case-insensitive comparison
            nl = name.lower()
            if allowed_skills:
                if any(nl == s.lower() for s in allowed_skills):
                    return True
                
                # Check for common variants
                if nl == "bartering" and any("barter" == s.lower() for s in allowed_skills):
                    return True
                if nl == "metalworking" and any("crafting" == s.lower() for s in allowed_skills):
                    return True
                if nl == "physical strength" and any("sturdiness" == s.lower() for s in allowed_skills):
                    return True
            
            # Fallback search in RAG
            return self._term_exists_in_rag_anywhere(name)

        def _is_allowed_item(name: str) -> bool:
            if not name: return True
            # Case-insensitive comparison
            if not isinstance(name, str):
                name = str(name)
            nl = name.lower()
            if allowed_items:
                if any(nl == (str(it).lower() if not isinstance(it, str) else it.lower()) for it in allowed_items):
                    return True
            
            # Fallback search in RAG
            return self._term_exists_in_rag_anywhere(name)

        if isinstance(skills, dict):
            for k in skills.keys():
                ks = str(k).strip()
                if not ks:
                    continue
                if not _is_allowed_skill(ks):
                    missing.append(f"skill:{ks}")

        if isinstance(inventory, list):
            for it in inventory:
                name = ''
                if isinstance(it, dict):
                    name = str(it.get('name', '')).strip()
                else:
                    name = str(it).strip()
                if not name:
                    continue
                if not _is_allowed_item(name):
                    missing.append(f"item:{name}")

        if missing:
            raise ValueError(f"Mode B validation failed ({label}) - not found in RAG: {', '.join(missing[:12])}")
        return None
    
    def set_time_context(self, time_context):
        """Set the current time context for generation."""
        self.time_context = time_context
    
    def _extract_response_content(self, response) -> str:
        """Extract content from LLM response, handling MiniMax M2 reasoning field."""
        if not response or not response.choices:
            return ""
        
        message = response.choices[0].message
        
        # Try content first
        if message.content and message.content.strip():
            return message.content.strip()
        
        # Fallback to reasoning field (MiniMax M2)
        if hasattr(message, 'reasoning') and message.reasoning and message.reasoning.strip():
            self.logger.log_system("DEBUG: Using reasoning field for response extraction")
            return message.reasoning.strip()
        
        return ""
    
    def _get_full_context_for_scene_creation(self) -> str:
        """Get complete context for scene creation: memories, concrete details, narrative history."""
        context_parts = []
        
        # 1. User Memories
        if self.key_memories_system:
            try:
                from key_memories_system import MemoryImportance
                memories_context = self.key_memories_system.get_memories_for_llm(
                    limit=10,
                    min_importance=MemoryImportance.NOTABLE
                )
                if memories_context:
                    context_parts.append(memories_context)
            except Exception as e:
                self.logger.log_system(f"Error getting memories for scene creation: {e}")
        
        # 2. Concrete Details
        if self.narrative_context_manager and hasattr(self.narrative_context_manager, 'detail_tracker'):
            try:
                detail_tracker = self.narrative_context_manager.detail_tracker
                # Get all concrete details
                all_details = []
                for owner, details in detail_tracker.details_by_owner.items():
                    for detail_id in details[:3]:  # Top 3 per owner
                        detail = detail_tracker.details.get(detail_id)
                        if detail:
                            all_details.append(f"- {owner}: {detail.detail_text}")
                
                if all_details:
                    context_parts.append("\n**ESTABLISHED CONCRETE DETAILS:**")
                    context_parts.append("(New scenes must maintain consistency with these)")
                    context_parts.extend(all_details)
            except Exception as e:
                self.logger.log_system(f"Error getting concrete details for scene creation: {e}")
        
        # 3. Narrative History
        if self.narrative_context_manager:
            try:
                narrative_context = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=5,
                    importance_threshold="notable",
                    key_memories_system=self.key_memories_system
                )
                if narrative_context:
                    context_parts.append("\n**RECENT NARRATIVE HISTORY:**")
                    context_parts.append(narrative_context)
            except Exception as e:
                self.logger.log_system(f"Error getting narrative history for scene creation: {e}")
        
        return "\n".join(context_parts) if context_parts else ""

    def _context_allows_remote_location(self, context: str, scene_description: str = "") -> bool:
        try:
            raw = f"{context} {scene_description}".strip()
            text = raw.lower()
        except Exception:
            return False

        # Only allow non-local locations when explicitly implied by context.
        explicit_markers = [
            "remote",
            "letter from",
            "message from",
            "call from",
            "telegram from",
            "courier from",
            "sent from",
        ]
        if any(m in text for m in explicit_markers):
            return True

        # Also allow explicit "in <Place>" / "from <Place>" patterns where <Place>
        # looks like a proper noun phrase.
        try:
            import re
            if re.search(r"\b(in|from)\s+[A-Z][A-Za-z\-']{2,}(\s+[A-Z][A-Za-z\-']{2,})*\b", raw):
                return True
        except Exception:
            pass

        return False

    def start_new_simulation(self, actor: UserActor):
        """Generates the very first scene of the simulation."""
        self.logger.log_system("Generating start scene...")
        print("Creator Agent initialized.")
        prompt = self._get_initial_scene_prompt(actor)
        self.current_scene = self._generate_scene(prompt)
        self.current_scene = self._enforce_scene_ua_goal_whitelist(self.current_scene, actor)
        return self.current_scene

    def generate_next_scene(self, actor: UserActor, previous_scene: dict, outcome: str, transition_context: dict = None):
        """Generates the next scene based on the outcome of the previous one with enhanced continuity."""
        self.logger.log_system(f"Generating next scene after outcome: {outcome}...")
        prompt = self._get_next_scene_prompt(actor, previous_scene, outcome, transition_context)
        self.current_scene = self._generate_scene(prompt)
        self.current_scene = self._enforce_scene_ua_goal_whitelist(self.current_scene, actor)
        return self.current_scene

    def _enforce_scene_ua_goal_whitelist(self, scene_data: dict, actor: UserActor) -> dict:
        """Ensure scene_elements.ua_goal is an exact Mode A goal line.

        For scenes, we use the UA's current goals as the strict whitelist.
        If the LLM invents/paraphrases a goal, we deterministically coerce it.
        """
        if not scene_data or not isinstance(scene_data, dict):
            return scene_data

        scene_elements = scene_data.get('scene_elements')
        if not scene_elements or not isinstance(scene_elements, dict):
            return scene_data

        try:
            allowed_goals = list(getattr(actor.sheet, 'goals', []) or [])
        except Exception:
            allowed_goals = []

        if not allowed_goals:
            return scene_data

        raw_goal = scene_elements.get('ua_goal', '')
        goal = (raw_goal or '').strip()
        if not goal:
            scene_elements['ua_goal'] = allowed_goals[0]
            return scene_data

        # Exact match
        if goal in allowed_goals:
            return scene_data

        # Case-insensitive match
        goal_lower = goal.lower()
        for g in allowed_goals:
            if g.lower() == goal_lower:
                scene_elements['ua_goal'] = g
                return scene_data

        # Coerce to primary goal (deterministic)
        self.logger.log_system(
            f"WARNING: Scene ua_goal not in Mode A whitelist; coercing. Got={goal!r} AllowedSample={allowed_goals[0]!r}"
        )
        scene_elements['ua_goal'] = allowed_goals[0]
        return scene_data

    def get_current_nua(self) -> NonUserActor or None:
        """Builds and returns the NonUserActor for the current scene."""
        if not self.current_scene or not self.current_scene.get('nua'):
            return None
        nua_data = self.current_scene['nua']

        personality_traits = nua_data.get('personality_traits', {})
        if not personality_traits or not personality_traits.get('internal') or not personality_traits.get('external'):
            self.logger.log_system(f"Personality traits missing or incomplete for {nua_data.get('name')}. Generating...")
            personality_traits = self._generate_personality_traits(nua_data)
        nua_data['personality_traits'] = personality_traits

        s_factors_data = nua_data.get('s_factors', {})
        required_s_factors = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
        if not s_factors_data or not required_s_factors.issubset(s_factors_data.keys()) or any(v == 0 for v in s_factors_data.values()):
            self.logger.log_system(f"S-Factors missing or invalid for {nua_data.get('name')}. Generating...")
            s_factors_data = self._generate_s_factors(nua_data)

        inventory_data = nua_data.get('inventory') or []
        self.logger.log_system(f"DEBUG NUA: Raw inventory data from LLM: {inventory_data}")
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                # CRITICAL: Enforce minimum supplement_bonus of 1 to ensure items appear in actor sheet
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
                self.logger.log_system(f"DEBUG NUA: Created item '{new_item.name}' with supplement_bonus: {new_item.supplement_bonus}")
            elif isinstance(item, str):
                # CRITICAL: Enforce minimum supplement_bonus of 1 for string items too
                new_item = Item(item, "", 1)
                inventory.append(new_item)
                self.logger.log_system(f"DEBUG NUA: Created basic item '{new_item.name}' with supplement_bonus: 1")
        
        # Log final inventory (no fallback supplements - testing LLM compliance)
        has_supplement = any(item.supplement_bonus > 0 for item in inventory)
        self.logger.log_system(f"DEBUG NUA: Has supplement items: {has_supplement}")
        self.logger.log_system(f"DEBUG NUA: Final inventory: {[(item.name, item.supplement_bonus) for item in inventory]}")
        
        if not has_supplement:
            self.logger.log_system(f"WARNING NUA: No supplement items found - LLM may not be following supplement requirements")

        nua_skills = nua_data.get('skills', {})
        if len(nua_skills) < 5:
            self.logger.log_system(f"NUA {nua_data.get('name', 'Unknown')} has only {len(nua_skills)} skills, minimum 5 required. Generating missing skills...")
            
            missing_count = 5 - len(nua_skills)
            additional_skills = self._generate_additional_skills(nua_data, nua_skills, missing_count)
            nua_skills.update(additional_skills)
            
            self.logger.log_system(f"Added {len(additional_skills)} skills: {list(additional_skills.keys())}. Total skills: {len(nua_skills)}")
        
        goals_data = nua_data.get('goals') or []
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data

        swiftness = s_factors_data.get('swiftness', 2)
        sociability = s_factors_data.get('sociability', 2)
        sturdiness = s_factors_data.get('sturdiness', 2)
        smarts = s_factors_data.get('smarts', 2)
        shadow = s_factors_data.get('shadow', 2)
        
        if sociability + smarts > 5:
            self.logger.log_system(f"WARNING: S-factors constraint violation - Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts} > 5")
            total_spirit_points = sociability + smarts
            if sociability >= smarts:
                sociability = min(sociability, 3)
                smarts = min(smarts, 5 - sociability)
            else:
                smarts = min(smarts, 3)
                sociability = min(sociability, 5 - smarts)
            self.logger.log_system(f"FIXED: Adjusted to Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts}")

        self.logger.log_system(f"DEBUG NUA: Creating ActorSheet with {len(nua_skills)} skills and inventory: {[(item.name, item.supplement_bonus) for item in inventory]}")
        nua_sheet = ActorSheet(
            name=nua_data['name'],
            s_factors=SFactors(
                swiftness=swiftness,
                sociability=sociability,
                sturdiness=sturdiness,
                smarts=smarts,
                shadow=shadow
            ),
            skills=nua_data.get('skills', {}),
            personality_traits=personality_traits,
            goals=goals_list,
            inventory=inventory,
            occupation=nua_data.get('occupation', 'Unknown')
        )
        
        # Debug: Check if inventory made it to the actor sheet
        self.logger.log_system(f"DEBUG NUA: ActorSheet created with {len(nua_sheet.inventory)} items: {[(item.name, item.supplement_bonus) for item in nua_sheet.inventory]}")
        supplement_items = [item for item in nua_sheet.inventory if item.supplement_bonus > 0]
        self.logger.log_system(f"DEBUG NUA: ActorSheet has {len(supplement_items)} supplement items: {[(item.name, item.supplement_bonus) for item in supplement_items]}")
        
        # Create NUA object
        nua = NonUserActor(nua_sheet)
        
        # Generate 3 key character-defining memories
        if self.key_memories_system:
            try:
                memories = self.generate_initial_memories(nua)
                if memories:
                    self.logger.log_system(f"✓ Generated {len(memories)} initial memories for {nua_data['name']}")
                else:
                    self.logger.log_system(f"⚠️ No memories generated for {nua_data['name']}")
            except Exception as e:
                self.logger.log_system(f"ERROR generating initial memories for {nua_data['name']}: {e}")
                import traceback
                traceback.print_exc()
        
        self.logger.log_system(f"Successfully generated NUA: {nua_data['name']} with {len([i for i in inventory if i.supplement_bonus > 0])} supplement items")
        return nua

    def generate_mnua(self, context: str, recurring_role: str = "antagonist",
                      tension_modifier: float = 1.0, relationship_significance: int = 5,
                      scene_description: str = "", tension_level: int = 0) -> NonUserActor:
        """
        Generate a Major Non-User Actor (MNUA) directly.
        
        Use this for narrative-critical characters that MUST recur:
        - Story antagonists
        - Pre-established relationships (mentor, rival, love interest)
        - Arc-defining characters
        - Faction leaders or key contacts
        
        TENSION-BASED GENERATION:
        Higher tension levels produce more formidable/dangerous MNUAs.
        - Tension 0-1: Standard MNUA, balanced stats
        - Tension 2-3: Enhanced MNUA, better skills, clearer threat
        - Tension 4-5: Formidable MNUA, high stats, significant danger
        
        Args:
            context: Description of who this character is and their role
            recurring_role: Their narrative function (antagonist, mentor, ally, rival, 
                           love_interest, contact, authority, wildcard)
            tension_modifier: How they affect difficulty (>1 = harder, <1 = easier)
            relationship_significance: Importance to UA (0-10 scale)
            scene_description: Optional scene context for generation
            tension_level: Current narrative tension (0-5), affects MNUA power level
        
        Returns:
            NonUserActor with MNUA status already set
        """
        self.logger.log_system(f"Generating MNUA with role: {recurring_role}, tension: {tension_level}")
        
        # Build enhanced prompt for MNUA generation
        role_guidance = {
            "antagonist": "This character opposes the protagonist. They should be formidable, have clear motivations, and pose a genuine threat. Their skills should challenge the UA.",
            "mentor": "This character guides and teaches. They should have wisdom, experience, and skills the UA can learn from. May have hidden depths or a troubled past.",
            "ally": "This character supports the protagonist. They should be reliable, have complementary skills, and create emotional investment.",
            "rival": "This character competes with the protagonist. They should be equally matched, create healthy tension, and could become friend or foe.",
            "love_interest": "This character has romantic potential. They should be compelling, create emotional stakes, and have their own agency and goals.",
            "contact": "This character provides information or access. They should have connections, knowledge, and their own agenda.",
            "authority": "This character has power over the UA's situation. They should command respect, have resources, and create pressure.",
            "wildcard": "This character is unpredictable. They should shift allegiances, surprise the UA, and keep things interesting.",
        }
        
        role_context = role_guidance.get(recurring_role, "This is a significant recurring character.")
        
        # Tension-based power scaling
        tension_guidance = {
            0: "Standard capability - competent but not exceptional.",
            1: "Standard capability - competent but not exceptional.",
            2: "Enhanced capability - noticeably skilled, a real challenge.",
            3: "Enhanced capability - clearly dangerous, requires caution.",
            4: "Formidable - highly skilled, poses significant threat, near-elite.",
            5: "Formidable - exceptional abilities, major threat, elite-tier.",
        }
        tension_context = tension_guidance.get(min(5, max(0, tension_level)), tension_guidance[0])
        
        # Adjust stat ranges based on tension
        if tension_level >= 4:
            stat_guidance = "Use HIGHER stat values (3-4 for physical, 2-3 for mental). Skills should be 3-5."
        elif tension_level >= 2:
            stat_guidance = "Use MODERATE-HIGH stat values (2-4 for physical, 2-3 for mental). Skills should be 2-4."
        else:
            stat_guidance = "Use BALANCED stat values (1-3 for physical, 1-2 for mental). Skills should be 1-3."

        # Get dynamic world context from RAG system (actor-specific occupations/goals)
        setting_context = self._get_setting_context()
        cultural_context = self._get_cultural_context()
        # Location policy: by default, all generated actors are in the Current Scene.
        # Only allow other locations when explicitly implied by the context.
        allow_remote_location = self._context_allows_remote_location(context=context, scene_description=scene_description)
        occupation_category = WorldbuildingCategory.MNUA_OCCUPATIONS if WorldbuildingCategory else None
        occupation_context = self._get_rag_context(
            query="occupations professions roles social class",
            max_tokens=300,
            category_filter=occupation_category
        )

        allowed_occupations: list[str] = []
        try:
            import re
            if occupation_context:
                for line in occupation_context.splitlines():
                    line_s = line.strip()
                    if not line_s.startswith(('-', '•', '*')):
                        continue
                    line_s = line_s.lstrip('-•*').strip()
                    if not line_s:
                        continue
                    if ':' not in line_s:
                        continue
                    lhs, rhs = line_s.split(':', 1)
                    lhs = lhs.strip()
                    rhs = rhs.strip()

                    if lhs:
                        candidate = re.sub(r'\([^)]*\)', '', lhs).strip()
                        if candidate.lower().startswith('the '):
                            candidate = candidate[4:].strip()
                        if candidate and candidate not in allowed_occupations:
                            allowed_occupations.append(candidate)
                        continue

                    if not rhs:
                        continue
                    rhs = re.sub(r'\([^)]*\)', '', rhs).strip()
                    rhs = rhs.replace(' or ', ', ')
                    parts = [p.strip(" \t-–—") for p in rhs.split(',')]
                    for p in parts:
                        if not p:
                            continue
                        if p.lower().startswith('the '):
                            continue
                        if p.lower() in ('and',):
                            continue
                        if p not in allowed_occupations:
                            allowed_occupations.append(p)
        except Exception:
            allowed_occupations = []
        mnua_category = WorldbuildingCategory.MNUA_GENERATION if WorldbuildingCategory else None
        mnua_generation_context = self._get_rag_context(
            query="major non-user actor generation recurring character major npc recurring tension significance",
            max_tokens=550,
            category_filter=mnua_category
        )
        goals_category = WorldbuildingCategory.MNUA_GOALS if WorldbuildingCategory else None
        goals_context = self._get_rag_context(
            query="goals motivations long-term objectives",
            max_tokens=250,
            category_filter=goals_category
        )
        # Goals are guidance-driven (no hard whitelist)
        allowed_goals = []
        allowed_goals_block = ""
        allowed_factions = self._get_explicit_faction_whitelist('mnua')
        allowed_factions_block = "\n".join([f"- {f}" for f in allowed_factions[:80]]) if allowed_factions else ""
        faction_context = self._get_faction_context_for_mnua()
        mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
        mechanics_context = self._get_rag_context(
            query="status stamina spirit supply skills endowments abilities",
            max_tokens=500,
            category_filter=mechanics_category
        )

        allowed_endowments = self._get_allowed_endowments_from_rag(actor_type='mnua')
        allowed_endowments_block = "\n".join([f"- {s}" for s in allowed_endowments[:80]]) if allowed_endowments else ""
        endowments_constraints = ""
        if allowed_endowments:
            endowments_constraints = f"""

ENDOWMENT LOCK (HARD CONSTRAINT):
- You may include 0-1 endowment ability. 
- Endowments are OPTIONAL. If none of the allowed endowments below fit the character, do NOT include any.
- If you do include an endowment, the endowment name MUST be EXACTLY one of the allowed names below (copy/paste exactly).

ALLOWED ENDOWMENTS:
{allowed_endowments_block}
""".rstrip()
        world_context = f"""
**WORLD SETTING:**
{setting_context}

**CULTURAL CONTEXT:**
{cultural_context}

**MAJOR CITIES & SETTLEMENTS:**
{cities_context}

**OCCUPATION OPTIONS (MNUA):**
{occupation_context}

**GOAL PATTERNS (MNUA):**
{goals_context}

**AVAILABLE FACTIONS/CLANS (MNUA):**
{faction_context if faction_context else "No specific factions defined - use 'None' for faction"}

**EXPLICIT FACTION LIBRARY (MNUA) - MODE A WHITELIST:**
{allowed_factions_block}

**MNUA GENERATION GUIDELINES:**
{mnua_generation_context}

**STATUS & SKILLS REFERENCE:**
{mechanics_context}
""".strip()

        allowed_occ_block = "\n".join([f"- {o}" for o in allowed_occupations]) if allowed_occupations else ""
        rag_constraints = ""
        if allowed_occupations:
            rag_constraints = f"""

OCCUPATION LOCK (HARD CONSTRAINT):
- occupation MUST be EXACTLY one of the allowed occupations below (copy/paste exactly; no other values permitted):
{allowed_occ_block}
""".rstrip()

        allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
        allowed_skill_vocab_block = "\n".join([f"- {s}" for s in allowed_skill_vocab]) if allowed_skill_vocab else ""
        allowed_item_vocab_block = "\n".join([f"- {s}" for s in allowed_item_vocab]) if allowed_item_vocab else ""
        mode_b_constraints = ""
        if allowed_skill_vocab or allowed_item_vocab:
            mode_b_constraints = f"""

MODE B VOCAB LOCK (HARD CONSTRAINTS):
- Skills MUST use EXACT names from the SKILLS VOCAB list below (copy/paste only; no modifiers like 'Advanced', 'Hooded', etc).
- Inventory item names MUST use EXACT names from the ITEMS VOCAB list below (copy/paste only; no adjectives/variants).

SKILLS VOCAB (Mode B - Allowed):
{allowed_skill_vocab_block}

ITEMS VOCAB (Mode B - Allowed):
{allowed_item_vocab_block}
""".rstrip()

        mode_b_ids_requirement = ""
        if allowed_skill_vocab or allowed_item_vocab:
            mode_b_ids_requirement = """

**MODE B OUTPUT REQUIREMENT (MANDATORY):**
- Because SKILLS/ITEMS VOCAB is provided, you MUST output `skill_ids` and `inventory_ids`.
- `skill_ids` MUST include at least 5 entries.
- `inventory_ids` MUST include 2-4 entries.
- When using ids, do NOT output free-text `skills`/`inventory` names (leave them empty objects/lists or omit them).
""".rstrip()

        allowed_occ_block = "\n".join([f"- {o}" for o in allowed_occupations]) if allowed_occupations else ""
        rag_constraints = ""
        if allowed_occupations:
            rag_constraints = f"""

OCCUPATION LOCK (HARD CONSTRAINT):
- occupation MUST be EXACTLY one of the allowed occupations below (copy/paste exactly; no other values permitted):
{allowed_occ_block}
""".rstrip()
        
        # Enhanced prompt for MNUA
        mnua_prompt = f"""Generate a MAJOR recurring character (MNUA) for a noir narrative.

CHARACTER CONTEXT:
{context}

{world_context}
{mode_b_constraints}
{rag_constraints}
{endowments_constraints}

NARRATIVE ROLE: {recurring_role.upper()}
{role_context}

TENSION LEVEL: {tension_level}/5
{tension_context}
{stat_guidance}

IMPORTANCE: This character will recur throughout the story. They need:
- Distinctive personality and memorable traits
- Clear motivations that may conflict with or align with the protagonist
- Skills appropriate to their role AND the current tension level
- Depth that allows for character development over time
- A hook that makes them interesting to interact with

{"SCENE CONTEXT: " + scene_description if scene_description else ""}

Generate a complete character with stats reflecting the tension level.
Higher tension = more formidable character. This is a MAJOR character, not a random NPC.

Return JSON with this structure:
{{
    "name": "Full Name",
    "occupation": "Their role/profession",
    "personality_traits": {{
        "internal": "How they think (Idealistic/Cynical/Pragmatic/Ambitious/etc)",
        "external": "How they act (Assertive/Charming/Intimidating/Professional/etc)"
    }},
    "endowments": {{"Power/Endowment Name": 1}},
    "s_factors": {{
        "swiftness": 1-4,
        "sociability": 1-3,
        "sturdiness": 1-4,
        "smarts": 1-3,
        "shadow": 1-4
    }},
    "skills": {{
        "skill_name": level (1-5),
        ... (at least 6 skills for major characters)
    }},
    "goals": ["Long-term goal", "Medium-term goal", "Immediate goal"],
    "inventory": [
        {{"name": "Item", "description": "What it is", "supplement_bonus": 1-3}}
    ],
    "skill_ids": [
        {{"id": 1, "level": 3}}
    ],
    "inventory_ids": [
        {{"id": 1, "description": "Item description", "supplement_bonus": 1}}
    ],
    "backstory_hook": "One sentence that hints at their history",
    "relationship_to_ua": "How they might connect to the protagonist"
}}"""

        max_retries = 3
        last_error = None
        mnua_data = None
        for attempt in range(max_retries):
            try:
                try:
                    from persistent_context_manager import get_context_manager
                    cm = get_context_manager()
                    if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                        facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                        if facts_block and isinstance(mnua_prompt, str) and mnua_prompt.strip():
                            mnua_prompt = f"{facts_block}\n\n{mnua_prompt}"
                except Exception:
                    pass
                response = robust_llm_call(
                    self.client,
                    model=self.model,
                    messages=[{"role": "user", "content": mnua_prompt}],
                    temperature=0.8,
                    max_tokens=1500
                )
                
                content = self._extract_response_content(response)
                
                # Parse JSON
                import re
                json_match = re.search(r'\{[\s\S]*\}', content)
                if json_match:
                    candidate = json.loads(_fix_json_formatting(json_match.group()))
                else:
                    raise ValueError("No JSON found in response")

                # If Mode B vocab exists, allow ID-based selection to avoid invented/variant names.
                try:
                    allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
                except Exception:
                    allowed_skill_vocab, allowed_item_vocab = ([], [])

                def _pick_allowed_name(raw_name: str, allowed: list[str]) -> str | None:
                    try:
                        if not raw_name or not allowed:
                            return None
                        rn = str(raw_name).strip()
                        if not rn:
                            return None
                        # Exact/case-insensitive match
                        rn_l = rn.lower()
                        for a in allowed:
                            if rn == a:
                                return a
                        for a in allowed:
                            if rn_l == str(a).lower():
                                return a
                        # Substring match (handles small variants)
                        for a in allowed:
                            al = str(a).lower()
                            if rn_l in al or al in rn_l:
                                return a
                        return None
                    except Exception:
                        return None

                def _coerce_skills_to_vocab(skills_in: dict, allowed: list[str]) -> dict[str, int]:
                    mapped: dict[str, int] = {}
                    if not isinstance(skills_in, dict):
                        return mapped
                    for k, v in list(skills_in.items()):
                        picked = _pick_allowed_name(str(k), allowed)
                        if not picked:
                            continue
                        try:
                            lvl = int(v)
                        except Exception:
                            lvl = 1
                        lvl = min(3, max(1, lvl))
                        mapped[picked] = lvl
                    return mapped

                def _coerce_inventory_to_vocab(inv_in: list, allowed: list[str]) -> list[dict]:
                    out: list[dict] = []
                    if not isinstance(inv_in, list):
                        return out
                    for it in inv_in:
                        try:
                            if isinstance(it, dict):
                                raw = it.get('name')
                                desc = str(it.get('description', '') or '').strip()
                                bonus = it.get('supplement_bonus', 1)
                            else:
                                raw = str(it)
                                desc = ""
                                bonus = 1
                            picked = _pick_allowed_name(str(raw), allowed)
                            if not picked:
                                continue
                            try:
                                bonus_i = int(bonus)
                            except Exception:
                                bonus_i = 1
                            bonus_i = max(1, bonus_i)
                            out.append({"name": picked, "description": desc, "supplement_bonus": bonus_i})
                        except Exception:
                            continue
                    return out

                # skill_ids: [{id:<1-based>, level:<1-5>}]
                skill_ids_raw = candidate.get('skill_ids')
                if allowed_skill_vocab and isinstance(skill_ids_raw, list) and skill_ids_raw:
                    mapped_skills: dict[str, int] = {}
                    for ent in skill_ids_raw[:12]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        raw_lvl = ent.get('level', 1)
                        try:
                            idx = int(raw_id)
                            lvl = int(raw_lvl)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_skill_vocab):
                            continue
                        lvl = min(5, max(1, lvl))
                        name = allowed_skill_vocab[idx - 1]
                        mapped_skills[name] = lvl
                    if mapped_skills:
                        candidate['skills'] = mapped_skills

                # inventory_ids: [{id:<1-based>, description:str, supplement_bonus:int}]
                inv_ids_raw = candidate.get('inventory_ids')
                if allowed_item_vocab and isinstance(inv_ids_raw, list) and inv_ids_raw:
                    mapped_inv: list[dict] = []
                    for ent in inv_ids_raw[:10]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        try:
                            idx = int(raw_id)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_item_vocab):
                            continue
                        name = allowed_item_vocab[idx - 1]
                        desc = str(ent.get('description', '') or '').strip()
                        bonus = ent.get('supplement_bonus', 1)
                        try:
                            bonus_i = int(bonus)
                        except Exception:
                            bonus_i = 1
                        bonus_i = max(1, bonus_i)
                        mapped_inv.append({"name": name, "description": desc, "supplement_bonus": bonus_i})
                    if mapped_inv:
                        candidate['inventory'] = mapped_inv

                goals_data = candidate.get('goals') or []
                if isinstance(goals_data, dict):
                    goals_list = list(goals_data.values())
                else:
                    goals_list = goals_data

                # Goals are guidance-driven (no hard whitelist)

                self._validate_mode_a_faction_or_raise(
                    faction=candidate.get('faction', 'None'),
                    allowed=allowed_factions,
                    label='MNUA'
                )

                self._validate_mode_b_terms_or_raise(
                    skills=candidate.get('skills', {}),
                    inventory=candidate.get('inventory') or [],
                    label='MNUA'
                )

                try:
                    def _coerce_to_allowed(value: str, allowed: list[str]) -> str:
                        if not allowed:
                            return value
                        v = (value or '').strip()
                        if not v:
                            return allowed[0]
                        for a in allowed:
                            if v == a:
                                return a
                        v_lower = v.lower()
                        for a in allowed:
                            if v_lower == a.lower():
                                return a
                        for a in allowed:
                            if a.lower() in v_lower:
                                return a
                        return allowed[0]

                    if allowed_occupations:
                        candidate['occupation'] = _coerce_to_allowed(candidate.get('occupation'), allowed_occupations)
                except Exception:
                    pass

                mnua_data = candidate
                break
            except Exception as e:
                last_error = e
                self.logger.log_system(f"ERROR generating MNUA (attempt {attempt + 1}/{max_retries}): {e}")
                continue

        if mnua_data is None:
            raise ValueError(f"MNUA generation failed after {max_retries} attempts: {last_error}")
        
        personality_traits = mnua_data.get('personality_traits', {"internal": "Unknown", "external": "Unknown"})
        s_factors_data = mnua_data.get('s_factors', {})
        
        # Ensure S-factors are valid
        swiftness = min(4, max(1, s_factors_data.get('swiftness', 2)))
        sociability = min(3, max(1, s_factors_data.get('sociability', 2)))
        sturdiness = min(4, max(1, s_factors_data.get('sturdiness', 2)))
        smarts = min(3, max(1, s_factors_data.get('smarts', 2)))
        shadow = min(4, max(1, s_factors_data.get('shadow', 2)))
        
        # Enforce spirit constraint
        if sociability + smarts > 5:
            if sociability >= smarts:
                sociability = min(sociability, 3)
                smarts = min(smarts, 5 - sociability)
            else:
                smarts = min(smarts, 3)
                sociability = min(sociability, 5 - smarts)
        
        # Process inventory
        inventory_data = mnua_data.get('inventory', [])
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item.get('name', 'Item'), item.get('description', ''), supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                inventory.append(Item(item, "", 1))
        
        # Process goals
        goals_data = mnua_data.get('goals', [])
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data if goals_data else []

        # Optional endowments (0-1). Normalize to {name: level}.
        endowments_raw = mnua_data.get('endowments') or {}
        endowments_norm: dict[str, int] = {}
        if isinstance(endowments_raw, dict):
            for k, v in list(endowments_raw.items())[:3]:
                name = str(k or '').strip()
                if not name:
                    continue
                try:
                    lvl = int(v)
                except Exception:
                    lvl = 1
                lvl = min(5, max(1, lvl))
                endowments_norm[name] = lvl
        elif isinstance(endowments_raw, list):
            for ent in endowments_raw[:2]:
                name = str(ent or '').strip()
                if name:
                    endowments_norm[name] = 1

        # Enforce RAG-allowed endowments if available
        endowments_norm = self._coerce_endowments_to_allowed(endowments_norm, allowed_endowments)
        mnua_data['endowments'] = endowments_norm
        
        # Create actor sheet
        mnua_sheet = ActorSheet(
            name=mnua_data.get('name', 'Unknown'),
            s_factors=SFactors(
                swiftness=swiftness,
                sociability=sociability,
                sturdiness=sturdiness,
                smarts=smarts,
                shadow=shadow
            ),
            skills=mnua_data.get('skills', {}),
            endowments=mnua_data.get('endowments', {}),
            personality_traits=personality_traits,
            goals=goals_list,
            inventory=inventory,
            occupation=mnua_data.get('occupation', recurring_role.title()),
            faction=mnua_data.get('faction', 'None')
        )

        try:
            mnua_sheet.canonical_name = mnua_sheet.name
            occ = (getattr(mnua_sheet, 'occupation', None) or '').strip()
            if not getattr(mnua_sheet, 'known_as', None):
                mnua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'unemployed', 'none'):
                if occ not in mnua_sheet.known_as:
                    mnua_sheet.known_as.append(occ)
                if not getattr(mnua_sheet, 'public_description', None):
                    mnua_sheet.public_description = f"the {occ.lower()}"
            else:
                if not mnua_sheet.known_as:
                    mnua_sheet.known_as.append('figure')
                if not getattr(mnua_sheet, 'public_description', None):
                    mnua_sheet.public_description = "the figure"
        except Exception:
            pass
        
        # Create as MNUA directly (is_mnua=True)
        mnua = NonUserActor(mnua_sheet, is_mnua=True)
        
        # Set MNUA-specific attributes
        import datetime
        mnua.mnua_status.graduation_date = datetime.datetime.now().isoformat()
        mnua.mnua_status.graduation_reason = f"Created directly as {recurring_role}"
        mnua.mnua_status.recurring_role = recurring_role
        mnua.mnua_status.relationship_significance = relationship_significance
        mnua.mnua_status.tension_modifier = tension_modifier
        mnua.mnua_status.ua_pool_access = True
        
        # Store backstory hook if provided
        if 'backstory_hook' in mnua_data:
            mnua.discovered_details['backstory_hook'] = mnua_data['backstory_hook']
        if 'relationship_to_ua' in mnua_data:
            mnua.discovered_details['relationship_to_ua'] = mnua_data['relationship_to_ua']
        
        # Generate initial memories for MNUA
        if self.key_memories_system:
            try:
                memories = self.generate_initial_memories(mnua)
                if memories:
                    self.logger.log_system(f"✓ Generated {len(memories)} initial memories for MNUA {mnua_data.get('name')}")
            except Exception as e:
                self.logger.log_system(f"ERROR generating memories for MNUA: {e}")
        
        self.logger.log_system(f"✓ Successfully generated MNUA: {mnua_data.get('name')} (Role: {recurring_role}, Tension: {tension_modifier})")
        return mnua

    def should_spawn_mnua(self, tension_level: int, scene_context: str = "",
                          existing_mnuas: int = 0) -> tuple[bool, str, str]:
        """
        Determine if current tension warrants spawning a new MNUA.
        
        Tension-based MNUA spawning rules:
        - Tension 0-2: No automatic MNUA spawn (use direct creation for story needs)
        - Tension 3: 30% chance of spawning a rival/contact
        - Tension 4: 50% chance of spawning an antagonist/authority
        - Tension 5: 80% chance of spawning a formidable antagonist
        
        Args:
            tension_level: Current narrative tension (0-5)
            scene_context: Description of current scene for context
            existing_mnuas: Number of MNUAs already in play (reduces spawn chance)
        
        Returns:
            (should_spawn: bool, suggested_role: str, spawn_reason: str)
        """
        import random
        
        # Reduce spawn chance based on existing MNUAs
        mnua_penalty = existing_mnuas * 0.15  # Each existing MNUA reduces chance by 15%
        
        spawn_rules = {
            0: (0.0, None, ""),
            1: (0.0, None, ""),
            2: (0.0, None, ""),
            3: (0.30 - mnua_penalty, ["rival", "contact", "wildcard"], "Rising tension attracts attention"),
            4: (0.50 - mnua_penalty, ["antagonist", "authority", "rival"], "High tension draws dangerous figures"),
            5: (0.80 - mnua_penalty, ["antagonist", "authority"], "Critical tension - a major threat emerges"),
        }
        
        base_chance, role_options, reason = spawn_rules.get(tension_level, (0.0, None, ""))
        
        if not role_options or base_chance <= 0:
            return False, "", ""
        
        if random.random() < base_chance:
            selected_role = random.choice(role_options)
            return True, selected_role, reason
        
        return False, "", ""

    def spawn_tension_mnua(self, tension_level: int, scene_context: str = "",
                           location: str = "") -> NonUserActor or None:
        """
        Attempt to spawn an MNUA based on current tension level.
        
        This is the main entry point for tension-triggered MNUA creation.
        Call this when tension is high and the narrative could use escalation.
        
        Args:
            tension_level: Current narrative tension (0-5)
            scene_context: Description of current scene
            location: Current location name
        
        Returns:
            New MNUA if spawned, None otherwise
        """
        should_spawn, role, reason = self.should_spawn_mnua(tension_level, scene_context)
        
        if not should_spawn:
            return None
        
        self.logger.log_system(f"⚡ TENSION SPAWN: {reason} (Tension: {tension_level}, Role: {role})")
        
        # Build context for the MNUA
        context = f"""A {role} who appears due to escalating tension.
Location: {location if location else 'Unknown'}
Scene: {scene_context[:200] if scene_context else 'Tense situation'}
This character should feel like a natural consequence of the rising stakes."""
        
        # Calculate tension modifier based on role
        role_tension_modifiers = {
            "antagonist": 1.2 + (tension_level * 0.1),  # 1.2-1.7
            "authority": 1.1 + (tension_level * 0.05),  # 1.1-1.35
            "rival": 1.0 + (tension_level * 0.05),      # 1.0-1.25
            "contact": 0.9,                              # Contacts reduce tension slightly
            "wildcard": 1.0 + (random.random() * 0.3),  # 1.0-1.3 random
        }
        
        import random
        tension_mod = role_tension_modifiers.get(role, 1.0)
        
        # Generate the MNUA
        mnua = self.generate_mnua(
            context=context,
            recurring_role=role,
            tension_modifier=tension_mod,
            relationship_significance=min(10, 4 + tension_level),  # 4-9 based on tension
            scene_description=scene_context,
            tension_level=tension_level
        )
        
        if mnua:
            # Mark as tension-spawned in MNUA status
            mnua.mnua_status.was_tension_spawned = True
            mnua.mnua_status.spawn_tension_level = tension_level
            
            # Also store in discovered_details for narrative access
            mnua.discovered_details['spawn_trigger'] = 'tension'
            mnua.discovered_details['spawn_tension_level'] = tension_level
            mnua.discovered_details['spawn_reason'] = reason
        
        return mnua

    def get_current_inua(self) -> InanimateNonUserActor or None:
        """Builds and returns the InanimateNonUserActor for the current scene."""
        if not self.current_scene or not self.current_scene.get('inua'):
            return None
        inua_data = self.current_scene['inua']

        s_factors_data = inua_data.get('s_factors', {})
        required_s_factors = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
        if not s_factors_data or not required_s_factors.issubset(s_factors_data.keys()):
            self.logger.log_system(f"S-Factors missing for INUA {inua_data.get('name')}. Generating...")
            s_factors_data = self._generate_inua_s_factors(inua_data)

        inventory_data = inua_data.get('inventory') or []
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                new_item = Item(item, "", 1)
                inventory.append(new_item)

        goals_data = inua_data.get('goals') or []
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data

        swiftness = s_factors_data.get('swiftness', 0)
        sociability = s_factors_data.get('sociability', 0)
        sturdiness = s_factors_data.get('sturdiness', 4)
        smarts = s_factors_data.get('smarts', 2)
        shadow = s_factors_data.get('shadow', 2)
        
        if sociability + smarts > 5:
            self.logger.log_system(f"WARNING: INUA S-factors constraint violation - Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts} > 5")
            sociability = min(sociability, 1)
            smarts = min(smarts, 5 - sociability)
            self.logger.log_system(f"FIXED: Adjusted INUA to Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts}")

        inua_sheet = ActorSheet(
            name=inua_data['name'],
            s_factors=SFactors(
                swiftness=swiftness,
                sociability=sociability,
                sturdiness=sturdiness,
                smarts=smarts,
                shadow=shadow
            ),
            skills=inua_data.get('skills', {}),
            personality_traits=inua_data.get('personality_traits', {'internal': 'inanimate', 'external': 'static'}),
            goals=goals_list,
            inventory=inventory,
            occupation=inua_data.get('occupation', 'Inanimate Object')
        )

        try:
            inua_sheet.canonical_name = inua_sheet.name
            occ = (getattr(inua_sheet, 'occupation', None) or '').strip()
            if not getattr(inua_sheet, 'known_as', None):
                inua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'none'):
                if occ not in inua_sheet.known_as:
                    inua_sheet.known_as.append(occ)
            if not getattr(inua_sheet, 'public_description', None):
                base = (occ or inua_sheet.name).strip()
                if base:
                    inua_sheet.public_description = base if base.lower().startswith(('the ', 'a ', 'an ')) else f"the {base.lower()}"
            if not inua_sheet.known_as:
                inua_sheet.known_as.append('object')
            if not getattr(inua_sheet, 'public_description', None):
                inua_sheet.public_description = "the object"
        except Exception:
            pass
        
        self.logger.log_system(f"Successfully generated INUA: {inua_data['name']}")
        return InanimateNonUserActor(inua_sheet)

    def generate_user_actor(self, context: str = "") -> UserActor:
        """Generates a complete UserActor based on context or user preferences."""
        self.logger.log_system("Generating new UserActor...")
        
        ua_data = self._generate_user_actor_profile(context)
        
        personality_traits = ua_data.get('personality_traits', {})
        if not personality_traits or not personality_traits.get('internal') or not personality_traits.get('external'):
            self.logger.log_system(f"Personality traits missing or incomplete for {ua_data.get('name')}. Generating...")
            personality_traits = self._generate_user_personality_traits(ua_data)
        ua_data['personality_traits'] = personality_traits

        s_factors_data = ua_data.get('s_factors', {})
        required_s_factors = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
        if not s_factors_data or not required_s_factors.issubset(s_factors_data.keys()) or any(v == 0 for v in s_factors_data.values()):
            self.logger.log_system(f"S-Factors missing or invalid for {ua_data.get('name')}. Generating...")
            s_factors_data = self._generate_user_s_factors(ua_data)

        inventory_data = ua_data.get('inventory') or []
        self.logger.log_system(f"DEBUG: Raw inventory data from LLM: {inventory_data}")
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                # CRITICAL: Enforce minimum supplement_bonus of 1 to ensure items appear in actor sheet
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
                self.logger.log_system(f"DEBUG: Created item '{new_item.name}' with supplement_bonus: {new_item.supplement_bonus}")
            elif isinstance(item, str):
                # CRITICAL: Enforce minimum supplement_bonus of 1 for string items too
                new_item = Item(item, "", 1)
                inventory.append(new_item)
                self.logger.log_system(f"DEBUG: Created basic item '{new_item.name}' with supplement_bonus: 1")
        
        # Log final inventory (no fallback supplements - testing LLM compliance)
        has_supplement = any(item.supplement_bonus > 0 for item in inventory)
        self.logger.log_system(f"DEBUG: Has supplement items: {has_supplement}")
        self.logger.log_system(f"DEBUG: Final inventory: {[(item.name, item.supplement_bonus) for item in inventory]}")
        
        if not has_supplement:
            self.logger.log_system(f"WARNING: No supplement items found - LLM may not be following supplement requirements")

        goals_data = ua_data.get('goals') or []
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data

        swiftness = s_factors_data.get('swiftness', 2)
        sociability = s_factors_data.get('sociability', 2)
        sturdiness = s_factors_data.get('sturdiness', 2)
        smarts = s_factors_data.get('smarts', 2)
        shadow = s_factors_data.get('shadow', 2)

        # Extract simulation year from UA profile
        # Note: The canonical year is set AFTER vessel selection, not here
        # Each vessel can have its own year; only the selected one becomes canonical
        simulation_year = ua_data.get('simulation_year')
        if not simulation_year:
            # Fallback: prefer the canonical year if one is already set from RAG.
            # If not set yet, try extracting from RAG rather than hardcoding a range.
            try:
                canonical_year = ActorSheet.get_simulation_year()
                if canonical_year:
                    simulation_year = canonical_year
                    self.logger.log_system(f"No simulation_year in UA profile, using canonical year: {simulation_year}")
                elif self.rag_system:
                    from worldbuilding_helpers import extract_current_year_from_rag
                    extracted_year = extract_current_year_from_rag(self.rag_system)
                    if extracted_year:
                        simulation_year = extracted_year
                        self.logger.log_system(f"No simulation_year in UA profile, extracted year from RAG: {simulation_year}")
            except Exception:
                pass
        else:
            self.logger.log_system(f"UA simulation year: {simulation_year}")
        
        self.logger.log_system(f"DEBUG: Creating ActorSheet with inventory: {[(item.name, item.supplement_bonus) for item in inventory]}")
        allowed_endowments = self._get_allowed_endowments_from_rag(actor_type='ua')
        endowments_norm = self._coerce_endowments_to_allowed(ua_data.get('endowments', {}) or {}, allowed_endowments)
        # ALWAYS ensure UA has at least one endowment pulled from RAG
        if not endowments_norm and allowed_endowments:
            endowments_norm = {allowed_endowments[0]: 1}
            self.logger.log_system(f"UA had no endowment — force-assigned from RAG: {allowed_endowments[0]}")
        ua_data['endowments'] = endowments_norm

        ua_sheet = ActorSheet(
            name=ua_data['name'],
            age=int(ua_data.get('age', 25)),
            occupation=ua_data.get('occupation', 'Traveler'),
            faction=ua_data.get('faction', 'None'),
            s_factors=SFactors(
                swiftness=swiftness,
                sociability=sociability,
                sturdiness=sturdiness,
                smarts=smarts,
                shadow=shadow
            ),
            skills=ua_data.get('skills', {}),
            endowments=ua_data.get('endowments', {}),
            personality_traits=personality_traits,
            goals=goals_list,
            inventory=inventory,
            initial_money=None,
            location=ua_data.get('location', 'Unknown'),
            is_user_actor=True,  # FIX BUG #13: Mark as user actor
            simulation_year=simulation_year  # Store the canonical year in the UA sheet
        )

        # For the UA (player), show any starting endowments immediately.
        try:
            if ua_sheet.endowments and any(v > 0 for v in ua_sheet.endowments.values()):
                ua_sheet.revealed_endowments = set(k for k, v in ua_sheet.endowments.items() if v > 0)
        except Exception:
            pass
        
        # Debug: Check if inventory made it to the actor sheet
        self.logger.log_system(f"DEBUG: ActorSheet created with {len(ua_sheet.inventory)} items: {[(item.name, item.supplement_bonus) for item in ua_sheet.inventory]}")
        supplement_items = [item for item in ua_sheet.inventory if item.supplement_bonus > 0]
        self.logger.log_system(f"DEBUG: ActorSheet has {len(supplement_items)} supplement items: {[(item.name, item.supplement_bonus) for item in supplement_items]}")
        
        # Note: generate_initial_memories() is called in main() after actor creation
        
        self.logger.log_system(f"Successfully generated UserActor: {ua_data['name']} (Year: {simulation_year})")
        return UserActor(ua_sheet)

    def _generate_user_actor_profile(self, context: str = "") -> dict:
        """Generates a complete UserActor profile including name, occupation, goals, skills, and basic inventory."""
        
        # Get dynamic world context from RAG system
        setting_context = self._get_setting_context()
        cultural_context = self._get_cultural_context()
        # Category: UA_OCCUPATIONS for UA occupation options
        occupation_category = WorldbuildingCategory.UA_OCCUPATIONS if WorldbuildingCategory else None
        occupation_context = self._get_rag_context(
            query="occupations professions jobs characters social class",
            max_tokens=300,
            category_filter=occupation_category
        )
        # Category: UA_GOALS for UA goal patterns
        goals_category = WorldbuildingCategory.UA_GOALS if WorldbuildingCategory else None
        goals_context = self._get_rag_context(
            query="goals motivations long-term objectives",
            max_tokens=250,
            category_filter=goals_category
        )
        # Category: UA_GENERATION for User Actor generation guidelines
        ua_category = WorldbuildingCategory.UA_GENERATION if WorldbuildingCategory else None
        actor_generation_context = self._get_rag_context(
            query="user actor generation player character protagonist names ages skills goals inventory personality",
            max_tokens=600,
            category_filter=ua_category
        )

        # Derive age range directly from UA_GENERATION RAG rules.
        age_min, age_max = (18, 55)
        try:
            import re
            text = actor_generation_context or ""
            # Matches formats like:
            # **AGE RANGE:** 18-55 years old
            # AGE RANGE: 18-55
            m = re.search(
                r"AGE\s*RANGE\s*:\s*(\d{1,3})\s*[-–]\s*(\d{1,3})",
                text,
                flags=re.IGNORECASE,
            )
            if m:
                a0 = int(m.group(1))
                a1 = int(m.group(2))
                if 0 < a0 < 150 and 0 < a1 < 150:
                    age_min, age_max = (min(a0, a1), max(a0, a1))
        except Exception:
            pass
        cities_category = WorldbuildingCategory.CITIES if WorldbuildingCategory else None
        cities_context = self._get_rag_context(
            query="major cities settlements",
            max_tokens=700,
            category_filter=cities_category
        )
        # Also get shared mechanics (status, skills reference)
        mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
        mechanics_context = self._get_rag_context(
            query="status stamina spirit supply skills endowments abilities",
            max_tokens=400,
            category_filter=mechanics_category
        )

        allowed_endowments = self._get_allowed_endowments_from_rag(actor_type='ua')
        allowed_endowments_block = "\n".join([f"- {s}" for s in allowed_endowments[:80]]) if allowed_endowments else ""
        endowments_constraints = ""
        if allowed_endowments:
            endowments_constraints = f"""

ENDOWMENT LOCK (HARD CONSTRAINT):
- You may include 0-1 endowment ability. 
- Endowments are OPTIONAL. If none of the allowed endowments below fit the character, do NOT include any.
- If you do include an endowment, the endowment name MUST be EXACTLY one of the allowed names below (copy/paste exactly).

ALLOWED ENDOWMENTS:
{allowed_endowments_block}
""".rstrip()

        allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
        allowed_skill_vocab_block = "\n".join([f"- {s}" for s in allowed_skill_vocab]) if allowed_skill_vocab else ""
        allowed_item_vocab_block = "\n".join([f"- {s}" for s in allowed_item_vocab]) if allowed_item_vocab else ""
        mode_b_constraints = ""
        if allowed_skill_vocab or allowed_item_vocab:
            mode_b_constraints = f"""

**MODE B VOCAB LOCK (HARD CONSTRAINTS):**
- Skills MUST use EXACT names from the SKILLS VOCAB list below (copy/paste only; no modifiers like 'Advanced', 'Hooded', etc).
- Inventory item names MUST use EXACT names from the ITEMS VOCAB list below (copy/paste only; no adjectives/variants).

SKILLS VOCAB (Mode B - Allowed):
{allowed_skill_vocab_block}

ITEMS VOCAB (Mode B - Allowed):
{allowed_item_vocab_block}
""".rstrip()

        mode_b_ids_requirement = ""
        if allowed_skill_vocab or allowed_item_vocab:
            mode_b_ids_requirement = """

**MODE B OUTPUT REQUIREMENT (MANDATORY):**
- Because SKILLS/ITEMS VOCAB is provided, you MUST output `skill_ids` and `inventory_ids`.
- For `skill_ids`: list of objects like {"id": 1, "level": 2} where id is 1-based index into SKILLS VOCAB.
- For `inventory_ids`: list of objects like {"id": 1, "description": "...", "supplement_bonus": 1} where id is 1-based index into ITEMS VOCAB.
- If you provide ids, do NOT invent any skill/item names.
""".rstrip()

        faction_context = self._get_faction_context_for_ua()
        allowed_factions = self._get_explicit_faction_whitelist('ua')
        allowed_factions_block = "\n".join([f"- {f}" for f in allowed_factions[:80]]) if allowed_factions else ""
        allowed_goals = self._get_explicit_goal_whitelist('ua')
        allowed_goals_block = "\n".join([f"- {g}" for g in allowed_goals[:80]]) if allowed_goals else ""

        allowed_city_names = []
        allowed_occupations = []
        try:
            import re

            if cities_context:
                for match in re.finditer(r'^\*\*([^*\n]{2,60})\*\*\s*$', cities_context, flags=re.MULTILINE):
                    name = match.group(1).strip()
                    if name and name not in allowed_city_names:
                        allowed_city_names.append(name)

            if occupation_context:
                for line in occupation_context.splitlines():
                    line_s = line.strip()
                    if not line_s.startswith(('-', '•', '*')):
                        continue
                    line_s = line_s.lstrip('-•*').strip()
                    if not line_s:
                        continue
                    lhs = ""
                    rhs = ""
                    if ':' in line_s:
                        lhs, rhs = line_s.split(':', 1)
                        lhs = lhs.strip()
                        rhs = rhs.strip()
                    else:
                        rhs = line_s

                    if lhs:
                        candidate = re.sub(r'\([^)]*\)', '', lhs).strip()
                        if candidate.lower().startswith('the '):
                            candidate = candidate[4:].strip()
                        if candidate and candidate not in allowed_occupations:
                            allowed_occupations.append(candidate)
                        continue

                    if not rhs:
                        continue
                    rhs = re.sub(r'\([^)]*\)', '', rhs).strip()
                    rhs = rhs.replace(' or ', ', ')
                    parts = [p.strip(" \t-–—") for p in rhs.split(',')]
                    for p in parts:
                        if not p:
                            continue
                        if p.lower().startswith('the '):
                            continue
                        if p.lower() in ('and',):
                            continue
                        if p not in allowed_occupations:
                            allowed_occupations.append(p)
        except Exception:
            allowed_city_names = []
            allowed_occupations = []

        # Include per-run generated cities as grounded cities.
        try:
            from worldbuilding_helpers import load_generated_cities
            for c in load_generated_cities() or []:
                if c and c not in allowed_city_names:
                    allowed_city_names.append(c)
        except Exception:
            pass

        allowed_city_block = "\n".join([f"- {c}" for c in allowed_city_names]) if allowed_city_names else ""
        allowed_occ_block = "\n".join([f"- {o}" for o in allowed_occupations]) if allowed_occupations else ""

        rag_constraints = ""
        if allowed_city_names or allowed_occupations:
            rag_constraints = f"""

**RAG LOCK (MIXED CONSTRAINTS):**
- Occupation MUST be EXACTLY one of the allowed occupations below (copy/paste the phrase exactly; no other occupations permitted):
{allowed_occ_block}

- Location SHOULD be one of the known cities below (copy/paste exactly), BUT MAY be a new plausible city for the era.
- If you introduce a new city, it MUST be a single city name only (no year, no commas), and must fit the time period.
Known cities (preferred):
{allowed_city_block}
""".rstrip()
        
        # Combine all RAG context
        world_context = f"""
**WORLD SETTING:**
{setting_context}

**CULTURAL CONTEXT:**
{cultural_context}

**MAJOR CITIES (ALLOWED LOCATIONS):**
{cities_context}

**OCCUPATION OPTIONS:**
{occupation_context}

**GOAL PATTERNS (UA):**
{goals_context}

**EXPLICIT GOAL LIBRARY (UA) - MODE A WHITELIST:**
{allowed_goals_block}

**AVAILABLE FACTIONS/CLANS (UA):**
{faction_context if faction_context else "No specific factions defined - use 'None' for faction"}

**EXPLICIT FACTION LIBRARY (UA) - MODE A WHITELIST:**
{allowed_factions_block}

**USER ACTOR GENERATION GUIDELINES:**
{actor_generation_context}

**STATUS & SKILLS REFERENCE:**
{mechanics_context}
""".strip()
        
        goal_id_max = len(allowed_goals) if allowed_goals else 0

        prompt = f"""
You are a character creator for an interactive simulation. Generate a compelling UserActor (player character) profile.

{world_context}

{f"Additional Context: {context}" if context else ""}{rag_constraints}{mode_b_constraints}{mode_b_ids_requirement}{endowments_constraints}

**Requirements:**
- Name: A distinctive character name
- Age: Character's age ({age_min}-{age_max} years old, appropriate for their background). MUST respect the AGE RANGE in the USER ACTOR GENERATION GUIDELINES.
- Location: Prefer a known city from the WORLD CONTEXT above, but you MAY introduce a new plausible city for the era.
-   - If you introduce a new city, it MUST be a single city name only (no year, no commas/parentheses).
-   - Do NOT invent modern/out-of-setting cities.
- Occupation: MUST be chosen from, or be a direct specialization of, the OCCUPATION OPTIONS section above. Do NOT invent jobs not supported by the RAG context.
- Faction: MUST be chosen from AVAILABLE FACTIONS/CLANS above, or use "None".
- Goals: Provide 1-3 goals as plain strings. Keep them grounded in the GOAL PATTERNS context above.
-   - Goals should be specific, actionable, and fit the era/setting.
-   - Do NOT invent out-of-setting institutions or modern systems.
- Skills: MINIMUM 5 skills with values 1-3, relevant to their background
- Inventory: 2-4 starting items with descriptions
- Skills (MODE B): Skill names MUST be EXACTLY copied from the SKILLS VOCAB (if provided).
- Inventory (MODE B): Item names MUST be EXACTLY copied from the ITEMS VOCAB (if provided).
- If SKILLS/ITEMS VOCAB is provided, you MUST return `skill_ids` and `inventory_ids` instead of free-text names:
-   - `skill_ids`: list of objects like {{"id": 1, "level": 2}} where id is 1-based index into SKILLS VOCAB.
-   - `inventory_ids`: list of objects like {{"id": 1, "description": "...", "supplement_bonus": 1}} where id is 1-based index into ITEMS VOCAB.
-   - If you provide ids, do NOT invent any skill/item names.
- Endowments: 0-1 total, grounded in the STATUS & SKILLS REFERENCE and USER ACTOR GENERATION GUIDELINES. If none, return an empty object.
- Simulation Year: Select a specific year within the TIME PERIOD mentioned in the world setting. This year becomes the canonical year for the entire simulation.

**CRITICAL - Simulation Year:**
- Based on the TIME PERIOD in the world setting, select a SPECIFIC year that fits the character's story
- This year will be used as the canonical simulation year for ALL other systems
- Consider the character's age, occupation, and goals when selecting the year
- The year should feel appropriate for the character's narrative

**CRITICAL - Supplement Requirements:**
- ALL inventory items MUST have a supplement_bonus of 1 or higher (minimum value: 1)
- Items with supplement_bonus: 0 will be HIDDEN from the actor sheet display
- Supplements represent equipment that provides mechanical bonuses
- Examples: "Lucky Charm" (+1), "Quality Tools" (+2), "Protective Gear" (+1)
- Even basic items should have supplement_bonus: 1 to ensure visibility

**CRITICAL - RAG GROUNDEDNESS (DO NOT IGNORE):**
- You MUST treat the WORLD CONTEXT above as the authoritative source.
- Location and Occupation must be supported by that context.
- If something is not mentioned or clearly implied by the WORLD CONTEXT, do NOT include it.

Respond with ONLY a valid JSON object:
{{
    "name": "Character Name",
    "age": 35,
    "location": "Constantinople",
    "occupation": "Character Background",
    "faction": "Faction/Clan from AVAILABLE FACTIONS above, or 'None'",
    "simulation_year": <YEAR_FROM_TIME_PERIOD>,
    "goals": ["Goal 1", "Goal 2"],
    "endowments": {{"Endowment/Power Name": 1}},
    "skill_ids": [
        {{"id": 1, "level": 2}},
        {{"id": 2, "level": 1}}
    ],
    "skills": {{"Primary Skill": 3, "Secondary Skill": 2, "Tertiary Skill": 2, "Basic Skill": 1, "Hobby Skill": 1}},
    "inventory_ids": [
        {{"id": 1, "description": "Item description", "supplement_bonus": 1}},
        {{"id": 2, "description": "A basic item", "supplement_bonus": 1}}
    ],
    "inventory": [
        {{"name": "Item Name", "description": "Item description", "supplement_bonus": 1}},
        {{"name": "Regular Item", "description": "A basic item", "supplement_bonus": 0}}
    ]
}}

**CRITICAL: The simulation_year MUST be a year from the TIME PERIOD specified in the WORLD SETTING above. Do NOT use 1968 or any other default - extract the actual year range from the setting.**
        """.strip()
        
        max_retries = 5
        last_error = None
        for attempt in range(max_retries):
            try:
                response = retry_with_backoff(
                    lambda: self.client.chat.completions.create(
                        model=self.model,
                        messages=[{'role': 'user', 'content': prompt}],
                        temperature=0.8
                    )
                )
                
                # Extract content using helper method (handles MiniMax M2 reasoning field)
                response_text = self._extract_response_content(response)
                self.logger.log_system(f"DEBUG: Raw UserActor API response: {response_text}")
                
                if not response_text or response_text.strip() == "":
                    raise ValueError("API returned empty response")
                
                from json_utils import extract_and_parse_json
                ua_data = extract_and_parse_json(response_text)
                
                if ua_data is None:
                    raise ValueError(f"Could not extract valid JSON from UserActor response: {response_text}")
                
                required_fields = ['name', 'occupation']
                if not all(field in ua_data for field in required_fields):
                    raise ValueError(f"Generated UserActor profile is missing required fields. Response: {ua_data}")

                # Enforce AGE RANGE from UA_GENERATION RAG rules.
                try:
                    age_val = ua_data.get('age', None)
                    if age_val is None:
                        raise ValueError(f"UserActor profile missing age (required). Response: {ua_data}")
                    age_i = int(age_val)
                    if age_i < age_min or age_i > age_max:
                        raise ValueError(
                            f"UserActor age {age_i} violates AGE RANGE {age_min}-{age_max} from UA_GENERATION RAG rules"
                        )
                    ua_data['age'] = age_i
                except ValueError:
                    raise
                except Exception:
                    raise ValueError(f"Invalid UserActor age value: {ua_data.get('age')!r}")

                # Optional endowments (0-1). Normalize to {name: level}.
                endowments_raw = ua_data.get('endowments') or {}
                endowments_norm: dict[str, int] = {}
                if isinstance(endowments_raw, dict):
                    for k, v in list(endowments_raw.items())[:3]:
                        name = str(k or '').strip()
                        if not name:
                            continue
                        try:
                            lvl = int(v)
                        except Exception:
                            lvl = 1
                        lvl = min(3, max(1, lvl))
                        endowments_norm[name] = lvl
                elif isinstance(endowments_raw, list):
                    # Allow list form like ["Relics", "Benedictions"]
                    for ent in endowments_raw[:2]:
                        name = str(ent or '').strip()
                        if name:
                            endowments_norm[name] = 1
                ua_data['endowments'] = endowments_norm

                try:
                    def _coerce_to_allowed(value: str, allowed: list[str]) -> str:
                        if not allowed:
                            return value
                        v = (value or '').strip()
                        if not v:
                            return allowed[0]
                        for a in allowed:
                            if v == a:
                                return a
                        v_lower = v.lower()
                        for a in allowed:
                            if v_lower == a.lower():
                                return a
                        for a in allowed:
                            if a.lower() in v_lower:
                                return a
                        return allowed[0]

                    if allowed_occupations:
                        ua_data['occupation'] = _coerce_to_allowed(ua_data.get('occupation'), allowed_occupations)
                except Exception:
                    pass

                # If Mode B vocab exists, allow ID-based selection to avoid invented/variant names.
                try:
                    allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
                except Exception:
                    allowed_skill_vocab, allowed_item_vocab = ([], [])

                # skill_ids: [{id:<1-based>, level:<1-3>}]
                skill_ids_raw = ua_data.get('skill_ids')
                if allowed_skill_vocab and isinstance(skill_ids_raw, list) and skill_ids_raw:
                    mapped_skills: dict[str, int] = {}
                    for ent in skill_ids_raw[:10]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        raw_lvl = ent.get('level', 1)
                        try:
                            idx = int(raw_id)
                            lvl = int(raw_lvl)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_skill_vocab):
                            continue
                        lvl = min(3, max(1, lvl))
                        name = allowed_skill_vocab[idx - 1]
                        mapped_skills[name] = lvl
                    if mapped_skills:
                        ua_data['skills'] = mapped_skills

                # Coercion fallback: if Mode B vocab exists but ids were missing/empty, map any free-text skills to vocab.
                if allowed_skill_vocab and (not isinstance(skill_ids_raw, list) or not skill_ids_raw):
                    coerced = _coerce_skills_to_vocab(ua_data.get('skills', {}) or {}, allowed_skill_vocab)
                    if coerced:
                        ua_data['skills'] = coerced

                # inventory_ids: [{id:<1-based>, description:str, supplement_bonus:int}]
                inv_ids_raw = ua_data.get('inventory_ids')
                if allowed_item_vocab and isinstance(inv_ids_raw, list) and inv_ids_raw:
                    mapped_inv: list[dict] = []
                    for ent in inv_ids_raw[:8]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        try:
                            idx = int(raw_id)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_item_vocab):
                            continue
                        name = allowed_item_vocab[idx - 1]
                        desc = str(ent.get('description', '') or '').strip()
                        bonus = ent.get('supplement_bonus', 1)
                        try:
                            bonus_i = int(bonus)
                        except Exception:
                            bonus_i = 1
                        bonus_i = max(1, bonus_i)
                        mapped_inv.append({"name": name, "description": desc, "supplement_bonus": bonus_i})
                    if mapped_inv:
                        ua_data['inventory'] = mapped_inv

                # Coercion fallback: if Mode B vocab exists but ids were missing/empty, map any free-text items to vocab.
                if allowed_item_vocab and (not isinstance(inv_ids_raw, list) or not inv_ids_raw):
                    coerced_inv = _coerce_inventory_to_vocab(ua_data.get('inventory') or [], allowed_item_vocab)
                    if coerced_inv:
                        ua_data['inventory'] = coerced_inv

                # Final Mode B fill: ensure minimum counts by adding allowed entries deterministically.
                if allowed_skill_vocab:
                    current = ua_data.get('skills') or {}
                    if isinstance(current, dict):
                        # Fill to 5 skills minimum
                        for name in allowed_skill_vocab:
                            if len(current) >= 5:
                                break
                            if name not in current:
                                current[name] = 1
                        ua_data['skills'] = current

                if allowed_item_vocab:
                    inv = ua_data.get('inventory') or []
                    if isinstance(inv, list):
                        # Fill to 2 items minimum
                        existing_names = set()
                        for it in inv:
                            try:
                                if isinstance(it, dict):
                                    existing_names.add(str(it.get('name') or '').strip())
                            except Exception:
                                continue
                        for name in allowed_item_vocab:
                            if len(inv) >= 2:
                                break
                            if name in existing_names:
                                continue
                            inv.append({"name": name, "description": "", "supplement_bonus": 1})
                            existing_names.add(name)
                        ua_data['inventory'] = inv
                
                skills = ua_data.get('skills', {})
                if len(skills) < 5:
                    raise ValueError(f"UserActor profile has only {len(skills)} skills, minimum 5 required. Skills: {skills}")

                # Goals are guidance-driven (no hard whitelist). Coerce to 1-3 strings.
                goals_list: list[str] = []
                goals_data = ua_data.get('goals') or []
                if isinstance(goals_data, dict):
                    goals_list = [str(v).strip() for v in goals_data.values() if str(v).strip()]
                else:
                    goals_list = [str(v).strip() for v in (goals_data or []) if str(v).strip()]
                goals_list = [g for g in goals_list if g]
                if len(goals_list) > 3:
                    goals_list = goals_list[:3]
                ua_data['goals'] = goals_list

                self._validate_mode_a_faction_or_raise(
                    faction=ua_data.get('faction', 'None'),
                    allowed=allowed_factions,
                    label='UA'
                )

                self._validate_mode_b_terms_or_raise(
                    skills=skills,
                    inventory=ua_data.get('inventory') or [],
                    label='UA'
                )

                try:
                    def _coerce_to_allowed(value: str, allowed: list[str]) -> str:
                        if not allowed:
                            return value
                        v = (value or '').strip()
                        if not v:
                            return allowed[0]
                        # Exact match first
                        for a in allowed:
                            if v == a:
                                return a
                        v_lower = v.lower()
                        # Substring match (handles e.g. "Constantinople, 1242" or "Scholar (Loyalists of Thule)")
                        for a in allowed:
                            if a.lower() in v_lower:
                                return a
                        # Last resort
                        return allowed[0]

                    if allowed_city_names:
                        # Do not hard-coerce city to the known list; allow new plausible cities.
                        loc = str(ua_data.get('location') or '').strip()
                        if not loc:
                            ua_data['location'] = allowed_city_names[0]
                        else:
                            # If it matches a known or previously-generated city, keep as-is.
                            loc_l = loc.lower()
                            known_l = {c.lower() for c in allowed_city_names}
                            if loc_l not in known_l:
                                # Basic sanity: reject digits ("Prague, 1238" etc.)
                                if any(ch.isdigit() for ch in loc):
                                    ua_data['location'] = allowed_city_names[0]
                                else:
                                    # Register as a generated city for this run.
                                    try:
                                        from worldbuilding_helpers import register_generated_city
                                        register_generated_city(loc)
                                        allowed_city_names.append(loc)
                                    except Exception:
                                        pass
                                    ua_data['location'] = loc
                    if allowed_occupations:
                        ua_data['occupation'] = _coerce_to_allowed(ua_data.get('occupation'), allowed_occupations)
                except Exception:
                    pass
                
                self.logger.log_system(f"Generated UserActor profile: {ua_data.get('name')} with {len(skills)} skills")
                return ua_data
            except Exception as e:
                last_error = e
                self.logger.log_system(f"ERROR generating UserActor profile (attempt {attempt + 1}/{max_retries}): {e}")
                continue

        error_msg = f"Could not generate or parse UserActor profile after {max_retries} attempts: {last_error}"
        self.logger.log_system(f"ERROR: {error_msg}")
        raise ValueError(f"UserActor profile generation failed: {error_msg}")

    def _generate_user_s_factors(self, ua_data: dict) -> dict:
        """Generates a balanced set of S-Factors for a UserActor based on their profile."""
        prompt = f"""
You are a character designer for an interactive simulation. Create balanced S-Factors for a UserActor (player character).

Character Profile:
- Name: {ua_data.get('name', 'Unknown')}
- Occupation: {ua_data.get('occupation', 'Unknown')}
- Personality: {ua_data.get('personality_traits', {})}
- Goals: {ua_data.get('goals') or []}
- Skills: {ua_data.get('skills', {})}

**MANDATORY S-FACTOR RULES - FOLLOW EXACTLY:**

1. **TOTAL POINTS: Must equal exactly 15 points across all five S-Factors**
2. **RANGE: Each S-Factor must be between 1-5 (no zeros allowed)**

**VALIDATION CHECKLIST - Verify before responding:**
✓ Swiftness + Sociability + Sturdiness + Smarts + Shadow = 15
✓ All values are between 1-5

**Valid Examples:**
- {{ "swiftness": 3, "sociability": 2, "sturdiness": 4, "smarts": 3, "shadow": 3 }} ← Total: 15 ✓
- {{ "swiftness": 4, "sociability": 3, "sturdiness": 3, "smarts": 2, "shadow": 3 }} ← Total: 15 ✓
- {{ "swiftness": 2, "sociability": 3, "sturdiness": 5, "smarts": 2, "shadow": 3 }} ← Total: 15 ✓

**Invalid Examples:**
- {{ "swiftness": 3, "sociability": 3, "sturdiness": 2, "smarts": 2, "shadow": 3 }} ← Total: 13 ✗
- {{ "swiftness": 6, "sociability": 3, "sturdiness": 2, "smarts": 2, "shadow": 2 }} ← Swiftness > 5 ✗

S-Factor Meanings:
- Swiftness: Speed, agility, reflexes, dexterity
- Sociability: Charisma, leadership, social skills, influence  
- Sturdiness: Physical strength, endurance, health, resilience
- Smarts: Intelligence, knowledge, reasoning, problem-solving
- Shadow: Stealth, cunning, deception, subterfuge

Respond with ONLY a valid JSON object. Double-check your math before responding.
        """.strip()
        
        try:
            response = retry_with_backoff(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{'role': 'user', 'content': prompt}],
                    temperature=0.2
                )
            )
            response_text = response.choices[0].message.content
            self.logger.log_system(f"DEBUG: Raw S-Factors API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            json_text = _fix_json_formatting(json_text)
            s_factors = json.loads(json_text)
            
            required_keys = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
            if (required_keys.issubset(s_factors.keys()) and
                    sum(s_factors.values()) == 15 and
                    all(1 <= v <= 5 for v in s_factors.values())):
                self.logger.log_system(f"Generated S-Factors for UserActor {ua_data.get('name')}: {s_factors}")
                return s_factors
            else:
                total = sum(s_factors.values())
                soc_smart_sum = s_factors.get('sociability', 0) + s_factors.get('smarts', 0)
                
                # Auto-fix if total is less than 15 by distributing remaining points
                if total < 15 and all(1 <= v <= 5 for v in s_factors.values()):
                    remaining = 15 - total
                    self.logger.log_system(f"Auto-fixing S-Factors: need {remaining} more points")
                    
                    # Distribute remaining points to attributes that can accept them
                    for attr in ['sturdiness', 'swiftness', 'shadow']:  # Prioritize non-spirit attributes
                        if remaining <= 0:
                            break
                        can_add = min(remaining, 5 - s_factors[attr])
                        s_factors[attr] += can_add
                        remaining -= can_add
                    
                    # If still need points, distribute to any attribute
                    if remaining > 0:
                        for attr in ['sociability', 'smarts']:
                            if remaining <= 0:
                                break
                            can_add = min(remaining, 5 - s_factors[attr])
                            if can_add > 0:
                                s_factors[attr] += can_add
                                remaining -= can_add
                    
                    # Verify the fix worked
                    if sum(s_factors.values()) == 15:
                        self.logger.log_system(f"Auto-fixed S-Factors for UserActor {ua_data.get('name')}: {s_factors}")
                        return s_factors
                
                error_msg = f"Generated S-Factors for UserActor {ua_data.get('name')} are invalid. Response: {s_factors}. Total: {total}/15"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"UserActor S-Factors generation failed: {error_msg}")
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse S-Factors for UserActor {ua_data.get('name')}: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"UserActor S-Factors generation failed: {error_msg}")

    def _generate_user_personality_traits(self, ua_data: dict) -> dict:
        """Generates personality traits for a UserActor if they are missing."""
        prompt = f"""
You are a character writer for an interactive simulation.
Based on the following UserActor (player character) profile, define their personality.
Provide one 'internal' (how they see themselves or feel inside) and one 'external' (how they present to others) trait.

Character Profile:
- Name: {ua_data.get('name', 'Unknown')}
- Occupation: {ua_data.get('occupation', 'Unknown')}
- Goals: {ua_data.get('goals') or []}
- Skills: {ua_data.get('skills', {})}

Create personality traits that would be interesting for a player to roleplay and that fit the character's background.
The traits should create internal tension or interesting roleplay opportunities.

Respond with ONLY a valid JSON object with two keys: "internal" and "external".
Example: {{ "internal": "self-doubting", "external": "confident" }}
        """.strip()
        
        try:
            response = retry_with_backoff(
                lambda: self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
            )
            response_text = response.choices[0].message.content.strip()
            self.logger.log_system(f"DEBUG: Raw personality traits API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            json_text = _fix_json_formatting(json_text)
            traits = json.loads(json_text)
            if 'internal' in traits and 'external' in traits:
                self.logger.log_system(f"Generated personality for UserActor {ua_data.get('name')}: {traits}")
                return traits
            else:
                error_msg = f"Generated personality JSON for UserActor {ua_data.get('name')} is missing required keys. Response: {traits}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"UserActor personality traits generation failed: {error_msg}")
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse personality traits for UserActor {ua_data.get('name')}: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            # Return sensible defaults instead of failing completely
            self.logger.log_system(f"Using default personality traits for {ua_data.get('name')}")
            return {"internal": "thoughtful", "external": "reserved"}

    def _generate_s_factors(self, nua_data: dict) -> dict:
        """Generates a balanced set of S-Factors for an NUA based on their profile."""
        prompt = f"""
        You are a designer for a simulation. Your task is to create a balanced character sheet for a Non-User Actor (NUA).

        Character Profile:
        - Name: {nua_data.get('name', 'Unknown')}
        - Occupation: {nua_data.get('occupation', 'Unknown')}
        - Personality: {nua_data.get('personality_traits', {})}
        - Goals: {nua_data.get('goals') or []}

        S-Factor Generation Rules:
        1.  Distribute exactly 12 points among the five S-Factors: Swiftness, Sociability, Sturdiness, Smarts, and Shadow.
        2.  Each S-Factor must have a value between 1 and 5 (inclusive). A value of 0 is not allowed.
        3.  The distribution should be logical for the character's profile. For example, a 'Spy' should have high Shadow and Smarts, while a 'Brute' should have high Sturdiness.
        

        Respond with ONLY a valid JSON object with the five S-Factor keys.
        Example for a Spy: {{ "swiftness": 3, "sociability": 2, "sturdiness": 1, "smarts": 3, "shadow": 3 }}
        """.strip()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.2
            )
            response_text = response.choices[0].message.content
            self.logger.log_system(f"DEBUG: Raw S-Factors API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            json_text = _fix_json_formatting(json_text)
            s_factors = json.loads(json_text)
            
            required_keys = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
            
            if (required_keys.issubset(s_factors.keys()) and
                    sum(s_factors.values()) == 12 and
                    all(1 <= v <= 5 for v in s_factors.values())):
                self.logger.log_system(f"Generated S-Factors for {nua_data.get('name')}: {s_factors}")
                return s_factors
            else:
                error_msg = f"Generated S-Factors for {nua_data.get('name')} are invalid. Response: {s_factors}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"S-Factors generation failed: {error_msg}")
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse S-Factors for {nua_data.get('name')}: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"S-Factors generation failed: {error_msg}")

    def _generate_personality_traits(self, nua_data: dict) -> dict:
        """Generates personality traits for an NUA if they are missing."""
        prompt = f"""
        You are a character writer for a simulation.
        Based on the following character profile, define their personality.
        Provide one 'internal' (how they see themselves or feel inside) and one 'external' (how they present to others) trait.

        Character Profile:
        - Name: {nua_data.get('name', 'Unknown')}
        - Occupation: {nua_data.get('occupation', 'Unknown')}
        - Goals: {nua_data.get('goals') or []}

        Respond with ONLY a valid JSON object with two keys: "internal" and "external".
        Example: {{ "internal": "insecure", "external": "boastful" }}
        """.strip()
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            response_text = response.choices[0].message.content.strip()
            self.logger.log_system(f"DEBUG: Raw personality traits API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            json_text = _fix_json_formatting(json_text)
            traits = json.loads(json_text)
            if 'internal' in traits and 'external' in traits:
                self.logger.log_system(f"Generated personality for {nua_data.get('name')}: {traits}")
                return traits
            else:
                error_msg = f"Generated personality JSON for {nua_data.get('name')} is missing required keys. Response: {traits}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"Personality traits generation failed: {error_msg}")
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse personality traits for {nua_data.get('name')}: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"Personality traits generation failed: {error_msg}")

    def generate_nua(self, context: str, scene_description: str, existing_names: list = None) -> NonUserActor:
        """Generate a new NUA for dynamic actor creation."""
        self.logger.log_system(f"Generating dynamic NUA with context: {context}")

        import random as _random
        _name_seed = _random.choice([
            "Use a name from Central/Eastern European origin (Czech, Slovak, Hungarian, Polish, Romanian).",
            "Use a name from Sub-Saharan African origin (Yoruba, Igbo, Zulu, Swahili, Amharic).",
            "Use a name from East Asian origin (Chinese, Japanese, Korean, Vietnamese).",
            "Use a name from South Asian origin (Hindi, Tamil, Bengali, Urdu).",
            "Use a name from Middle Eastern / North African origin (Arabic, Persian, Turkish, Hebrew).",
            "Use a name from Scandinavian or Nordic origin (Swedish, Norwegian, Danish, Finnish).",
            "Use a name from Iberian or Latin American origin (Spanish, Portuguese, Catalan).",
            "Use a name from Slavic origin (Russian, Ukrainian, Serbian, Bulgarian).",
            "Use a name from South-East Asian origin (Thai, Indonesian, Filipino, Malay).",
            "Use a name from Italian or Southern European origin (Italian, Greek, Albanian).",
        ])
        _forbidden_block = ""
        if existing_names:
            _forbidden_block = f"\n**FORBIDDEN NAMES (already in use — do NOT use or vary these):** {', '.join(existing_names)}\n"

        prompt = f"""
You are creating a Non-User Actor (NUA) for an interactive simulation.

Scene Context: {scene_description}
Interaction Context: {context}
{_forbidden_block}
**NAME DIVERSITY (MANDATORY):** {_name_seed} The name must feel authentic — not a generic Western fantasy name.

Create a complete NUA profile that fits naturally into this situation.

**Requirements:**
- Name: Culturally diverse, memorable, not matching any forbidden name above
- Age: Character's age (18-70 years old, appropriate for their role)
- Location: Geographic location where they're based (e.g., New York, Manila, Beijing)
- Pronouns: Character's pronouns (he/him, she/her, they/them)
- Occupation: Role/job that makes sense for the situation
- Goals: 1-3 objectives that fit the character
- Skills: MINIMUM 5 skills with values 1-3, relevant to their role
- Inventory: 2-4 items with descriptions and supplement bonuses
- Personality: Internal and external traits
- Memories: 2-4 background memories that define this character (childhood, relationships, experiences, knowledge)

**CRITICAL - Supplement Requirements:**
- ALL inventory items MUST have a supplement_bonus of 1 or higher
- Items with supplement_bonus: 0 will be HIDDEN from display
- Even basic items should have supplement_bonus: 1

Respond with ONLY a valid JSON object:
{{
    "name": "Character Name",
    "age": 35,
    "location": "New York",
    "pronouns": "he/him",
    "occupation": "Character Role",
    "goals": ["Primary goal", "Secondary goal"],
    "skills": {{"Primary Skill": 3, "Secondary Skill": 2, "Basic Skill": 1, "Another Skill": 2, "Final Skill": 1}},
    "inventory": [
        {{"name": "Item Name", "description": "Item description", "supplement_bonus": 1}}
    ],
    "personality_traits": {{"internal": "internal trait", "external": "external trait"}},
    "memories": [
        "Grew up in Brooklyn, learned street smarts early",
        "Lost father at age 12, had to help support family",
        "Worked various odd jobs before finding current occupation",
        "Has a younger sister who looks up to them"
    ]
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.8
            )
            response_text = response.choices[0].message.content
            
            from json_utils import extract_and_parse_json
            nua_data = extract_and_parse_json(response_text)
            
            if nua_data and 'name' in nua_data:
                self.logger.log_system(f"Generated dynamic NUA: {nua_data['name']}")
                return self._build_nua_from_data(nua_data)
            else:
                self.logger.log_system(f"Failed to generate valid NUA data")
                raise ValueError("Invalid NUA data generated")
                
        except Exception as e:
            self.logger.log_system(f"Error generating dynamic NUA: {e}")
            raise ValueError(f"Dynamic NUA generation failed: {e}")

    def generate_inua(self, context: str, scene_description: str) -> InanimateNonUserActor:
        """Generate a new INUA for dynamic actor creation."""
        self.logger.log_system(f"Generating dynamic INUA with context: {context}")
        
        prompt = f"""
You are creating an Inanimate Non-User Actor (INUA) for an interactive simulation.

Scene Context: {scene_description}
Interaction Context: {context}

Create a complete INUA profile for this inanimate object.

**Requirements:**
- Name: Object name that fits the context
- Occupation: "Inanimate Object" or specific object type
- Goals: 1-2 simple objectives (if any)
- Skills: 2-3 relevant capabilities with values 1-2
- Inventory: 1-2 component items if applicable

**S-Factor Guidelines for INUA:**
- Swiftness: Usually 0-1 (objects don't move much)
- Sociability: Usually 0 (objects don't socialize)
- Sturdiness: Usually 3-5 (objects are durable)
- Smarts: 0-3 depending on complexity
- Shadow: 1-3 depending on visibility/stealth

Respond with ONLY a valid JSON object:
{{
    "name": "Object Name",
    "occupation": "Inanimate Object",
    "goals": ["Simple objective"],
    "skills": {{"Relevant Skill": 2, "Basic Function": 1}},
    "inventory": [
        {{"name": "Component", "description": "Object component", "supplement_bonus": 1}}
    ],
    "personality_traits": {{"internal": "inanimate", "external": "static"}}
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.6
            )
            response_text = response.choices[0].message.content
            
            from json_utils import extract_and_parse_json
            inua_data = extract_and_parse_json(response_text)
            
            if inua_data and 'name' in inua_data:
                self.logger.log_system(f"Generated dynamic INUA: {inua_data['name']}")
                return self._build_inua_from_data(inua_data)
            else:
                self.logger.log_system(f"Failed to generate valid INUA data")
                raise ValueError("Invalid INUA data generated")
                
        except Exception as e:
            self.logger.log_system(f"Error generating dynamic INUA: {e}")
            raise ValueError(f"Dynamic INUA generation failed: {e}")

    def _build_nua_from_data(self, nua_data: dict):
        """Build NonUserActor from generated data."""
        # Use existing logic from get_current_nua but with dynamic data
        personality_traits = nua_data.get('personality_traits', {})
        if not personality_traits or not personality_traits.get('internal') or not personality_traits.get('external'):
            personality_traits = self._generate_personality_traits(nua_data)
        
        s_factors_data = nua_data.get('s_factors', {})
        if not s_factors_data:
            s_factors_data = self._generate_s_factors(nua_data)
        
        # Process inventory with supplement enforcement
        inventory_data = nua_data.get('inventory') or []
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                new_item = Item(item, "", 1)
                inventory.append(new_item)
        
        # Ensure minimum skills
        nua_skills = nua_data.get('skills', {})
        if len(nua_skills) < 5:
            missing_count = 5 - len(nua_skills)
            additional_skills = self._generate_additional_skills(nua_data, nua_skills, missing_count)
            nua_skills.update(additional_skills)
        
        # Extract memories from generated data
        memories = nua_data.get('memories', [])
        
        # Build actor sheet
        from actor_sheet import ActorSheet, SFactors
        nua_sheet = ActorSheet(
            name=nua_data['name'],
            s_factors=SFactors(
                swiftness=s_factors_data.get('swiftness', 2),
                sociability=s_factors_data.get('sociability', 2),
                sturdiness=s_factors_data.get('sturdiness', 2),
                smarts=s_factors_data.get('smarts', 2),
                shadow=s_factors_data.get('shadow', 2)
            ),
            skills=nua_skills,
            personality_traits=personality_traits,
            goals=nua_data.get('goals', []),
            inventory=inventory,
            occupation=nua_data.get('occupation', 'Unknown'),
            age=nua_data.get('age', 30),
            location=nua_data.get('location', 'Unknown'),
            pronouns=nua_data.get('pronouns', 'they/them'),  # Extract pronouns from generated data
            memories=memories  # Add built-in memories
        )

        try:
            nua_sheet.canonical_name = nua_sheet.name
            occ = (getattr(nua_sheet, 'occupation', None) or '').strip()
            if not getattr(nua_sheet, 'known_as', None):
                nua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'unemployed', 'none'):
                if occ not in nua_sheet.known_as:
                    nua_sheet.known_as.append(occ)
                if not getattr(nua_sheet, 'public_description', None):
                    nua_sheet.public_description = f"the {occ.lower()}"
            else:
                # Deterministic fallback so stranger-safe naming never becomes empty
                if not nua_sheet.known_as:
                    nua_sheet.known_as.append('person')
                if not getattr(nua_sheet, 'public_description', None):
                    nua_sheet.public_description = "the person"
        except Exception:
            pass
        
        from actors import NonUserActor
        return NonUserActor(nua_sheet)

    def _build_inua_from_data(self, inua_data: dict):
        """Build InanimateNonUserActor from generated data."""
        s_factors_data = inua_data.get('s_factors', {})
        if not s_factors_data:
            s_factors_data = self._generate_inua_s_factors(inua_data)
        
        # Process inventory
        inventory_data = inua_data.get('inventory') or []
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                new_item = Item(item, "", 1)
                inventory.append(new_item)
        
        # Build actor sheet
        from actor_sheet import ActorSheet, SFactors
        inua_sheet = ActorSheet(
            name=inua_data['name'],
            s_factors=SFactors(
                swiftness=s_factors_data.get('swiftness', 0),
                sociability=s_factors_data.get('sociability', 0),
                sturdiness=s_factors_data.get('sturdiness', 4),
                smarts=s_factors_data.get('smarts', 2),
                shadow=s_factors_data.get('shadow', 2)
            ),
            skills=inua_data.get('skills', {}),
            personality_traits=inua_data.get('personality_traits', {'internal': 'inanimate', 'external': 'static'}),
            goals=inua_data.get('goals', []),
            inventory=inventory,
            occupation=inua_data.get('occupation', 'Inanimate Object'),
            age=inua_data.get('age', None),
            location=inua_data.get('location', 'Unknown')
        )

        try:
            inua_sheet.canonical_name = inua_sheet.name
            occ = (getattr(inua_sheet, 'occupation', None) or '').strip()
            if not getattr(inua_sheet, 'known_as', None):
                inua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'none'):
                if occ not in inua_sheet.known_as:
                    inua_sheet.known_as.append(occ)
            if not getattr(inua_sheet, 'public_description', None):
                base = (occ or inua_sheet.name).strip()
                if base:
                    inua_sheet.public_description = base if base.lower().startswith(('the ', 'a ', 'an ')) else f"the {base.lower()}"

            # Deterministic fallback so stranger-safe naming never becomes empty
            if not inua_sheet.known_as:
                inua_sheet.known_as.append('object')
            if not getattr(inua_sheet, 'public_description', None):
                inua_sheet.public_description = "the object"
        except Exception:
            pass
        
        from actors import InanimateNonUserActor
        return InanimateNonUserActor(inua_sheet)

    def _generate_scene(self, prompt: str) -> dict or None:
        """Calls the LLM to generate scene data, with retries, and parses the JSON response."""
        try:
            from persistent_context_manager import get_context_manager
            cm = get_context_manager()
            if cm is not None and hasattr(cm, 'get_continuity_facts_for_llm'):
                facts_block = cm.get_continuity_facts_for_llm(max_facts=8) or ""
                if facts_block and isinstance(prompt, str) and prompt.strip():
                    prompt = f"{facts_block}\n\n{prompt}"
        except Exception:
            pass
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.logger.log_system(f"Generating scene, attempt {attempt + 1}/{max_retries}...")
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7
                )
                response_text = response.choices[0].message.content
                self.logger.log_system(f"DEBUG: Raw API response: {repr(response_text)}")
                
                if not response_text:
                    self.logger.log_system(f"ERROR: Attempt {attempt + 1} - Empty response from API")
                    continue
                    
                response_text = response_text.strip()

                from json_utils import extract_and_parse_json
                scene_data = extract_and_parse_json(response_text)
                
                if scene_data is None:
                    self.logger.log_system(f"ERROR: Attempt {attempt + 1} - Could not extract valid JSON from scene response")
                    continue

                # Some models occasionally wrap the scene object in a single-element JSON array.
                # Unwrap here so downstream code can treat the scene as a dict.
                if isinstance(scene_data, list):
                    if len(scene_data) == 1 and isinstance(scene_data[0], dict):
                        scene_data = scene_data[0]

                if not isinstance(scene_data, dict):
                    self.logger.log_system(
                        f"ERROR: Attempt {attempt + 1} - Scene JSON must be an object/dict, got {type(scene_data).__name__}"
                    )
                    continue

                has_scene_elements = 'scene_elements' in scene_data
                # For initial exploration scenes, NPCs are optional
                has_valid_structure = has_scene_elements and ('nua' in scene_data or 'inua' in scene_data or 
                                                            (scene_data.get('nua') is None and scene_data.get('inua') is None))
                
                if has_valid_structure:
                    # Validate population and log
                    pop_report = self.validate_scene_population(scene_data)
                    self.logger.log_system(f"POPULATION CHECK: {pop_report['population_summary']} ({pop_report['status']})")
                    if pop_report['issues']:
                        self.logger.log_system(f"POPULATION ISSUES: {', '.join(pop_report['issues'])}")
                    
                    self.logger.log_system("Successfully generated and parsed new scene.")
                    # CRITICAL: Strip banned meta-time references from scene description
                    scene_data = self._strip_meta_time_from_scene(scene_data)
                    return scene_data
                else:
                    missing_keys = []
                    if not has_scene_elements:
                        missing_keys.append("'scene_elements'")
                    if 'nua' not in scene_data and 'inua' not in scene_data:
                        missing_keys.append("'nua' or 'inua' fields")
                    self.logger.log_system(f"ERROR: Attempt {attempt + 1} - Generated scene JSON is missing required keys: {', '.join(missing_keys)}.")

            except json.JSONDecodeError as e:
                self.logger.log_system(f"ERROR: Attempt {attempt + 1} - Could not parse LLM response into scene JSON: {e}")
            except Exception as e:
                self.logger.log_system(f"ERROR: Attempt {attempt + 1} - An unexpected error occurred: {e}")
                try:
                    import traceback
                    self.logger.log_system(traceback.format_exc(limit=6))
                except Exception:
                    pass

        self.logger.log_system("FATAL: All attempts to generate a valid scene failed.")
        return None
    
    def _strip_meta_time_from_scene(self, scene_data: dict) -> dict:
        """
        Strip meta-time references (vintage, old, retro, etc.) from scene descriptions.
        This is a post-processing filter since the LLM keeps ignoring the prompt.
        """
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
        
        def clean_text(text: str) -> str:
            if not text:
                return text
            cleaned = text
            for pattern, replacement in replacements.items():
                cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
            # Clean up double spaces
            cleaned = re.sub(r'\s+', ' ', cleaned)
            return cleaned.strip()
        
        # Clean scene_elements.setting
        if 'scene_elements' in scene_data and 'setting' in scene_data['scene_elements']:
            setting_text = clean_text(scene_data['scene_elements']['setting'])
            # Replace passive "You are in" with active "You look around"
            setting_text = re.sub(r'\bYou are in\b', 'You look around', setting_text, flags=re.IGNORECASE)
            setting_text = re.sub(r'\bYou find yourself in\b', 'You see', setting_text, flags=re.IGNORECASE)
            
            # Remove meta-explanations that reference personality traits
            # Pattern: ", a [word] born from your [trait]" or ", a habit born from your [trait]"
            setting_text = re.sub(r',\s*a\s+\w+\s+born\s+from\s+your\s+\w+(\s+\w+)?\.?', '.', setting_text, flags=re.IGNORECASE)
            # Pattern: ", reflecting your [trait]" or ", showing your [trait]"
            setting_text = re.sub(r',\s*(reflecting|showing|revealing|betraying)\s+your\s+\w+(\s+\w+)?\.?', '.', setting_text, flags=re.IGNORECASE)
            # Pattern: "due to your [trait]" or "because of your [trait]"
            setting_text = re.sub(r'\s+(due\s+to|because\s+of)\s+your\s+\w+(\s+\w+)?\.?', '.', setting_text, flags=re.IGNORECASE)
            
            # Clean up double periods and extra spaces
            setting_text = re.sub(r'\.\.+', '.', setting_text)
            setting_text = re.sub(r'\s+', ' ', setting_text)
            
            scene_data['scene_elements']['setting'] = setting_text.strip()
        
        # Clean exploration_opportunities
        if 'scene_elements' in scene_data and 'exploration_opportunities' in scene_data['scene_elements']:
            opportunities = scene_data['scene_elements']['exploration_opportunities']
            if isinstance(opportunities, str):
                scene_data['scene_elements']['exploration_opportunities'] = clean_text(opportunities)
            elif isinstance(opportunities, list):
                scene_data['scene_elements']['exploration_opportunities'] = [clean_text(opp) for opp in opportunities]
        
        return scene_data
    
    def _get_rag_context(self, query: str, max_tokens: int = 800, category_filter=None) -> str:
        """
        Get world context from RAG system.
        
        Args:
            query: Search query for relevant lore
            max_tokens: Maximum tokens to retrieve
            category_filter: Optional LoreCategory filter
            
        Returns:
            Formatted context string for LLM prompts
        """
        if not self.rag_system:
            return ""
        
        try:
            context = self.rag_system.get_context_for_llm(
                query=query,
                max_tokens=max_tokens,
                category_filter=category_filter
            )
            return context if context else ""
        except Exception as e:
            self.logger.log_system(f"Warning: Could not retrieve RAG context: {e}")
            return ""
    
    def _get_setting_context(self) -> str:
        """Get time period and setting context from RAG
        
        Category: TEMPORAL
        """
        category = WorldbuildingCategory.TEMPORAL if WorldbuildingCategory else None
        return self._get_rag_context(
            query="time period setting year era current date timeline",
            max_tokens=400,
            category_filter=category
        )
    
    def _get_location_context(self, occupation: str, goals: list) -> str:
        """Get location-appropriate context from RAG
        
        Category: PLACES
        """
        query = f"locations places {occupation} {' '.join(goals[:2])}"
        category = WorldbuildingCategory.PLACES if WorldbuildingCategory else None
        return self._get_rag_context(query=query, max_tokens=400, category_filter=category)
    
    def _get_occupation_context(self, occupation: str) -> str:
        """Get occupation-specific context from RAG
        
        Category: CIVILIZATION (social classes, occupations)
        """
        category = WorldbuildingCategory.CIVILIZATION if WorldbuildingCategory else None
        return self._get_rag_context(
            query=f"occupation work job {occupation} social class",
            max_tokens=300,
            category_filter=category
        )
    
    def _get_cultural_context(self) -> str:
        """Get cultural and atmospheric context from RAG
        
        Category: CULTURE
        """
        category = WorldbuildingCategory.CULTURE if WorldbuildingCategory else None
        return self._get_rag_context(
            query="culture atmosphere music fashion social issues sensory",
            max_tokens=400,
            category_filter=category
        )
    
    def _get_faction_context_for_nua(self) -> str:
        """Get faction/clan options for NUA generation
        
        Category: FACTION_NUA
        """
        category = WorldbuildingCategory.FACTION_NUA if WorldbuildingCategory else None
        return self._get_rag_context(
            query="factions clans organizations affiliations npc groups",
            max_tokens=500,
            category_filter=category
        )
    
    def _get_faction_context_for_mnua(self) -> str:
        """Get faction/clan options for MNUA generation
        
        Category: FACTION_MNUA
        """
        category = WorldbuildingCategory.FACTION_MNUA if WorldbuildingCategory else None
        return self._get_rag_context(
            query="factions clans organizations affiliations major npc groups",
            max_tokens=500,
            category_filter=category
        )
    
    def _get_faction_context_for_ua(self) -> str:
        """Get faction/clan options for UA generation

        Category: FACTION_UA
        """
        category = WorldbuildingCategory.FACTION_UA if WorldbuildingCategory else None
        return self._get_rag_context(
            query="factions clans organizations affiliations player groups",
            max_tokens=500,
            category_filter=category
        )

    def _classify_wake_up_style(self, personality_internal: str) -> str:
        """Classify personality into wake-up style category.

        Args:
            personality_internal: Internal personality trait string

        Returns:
            One of: "alert", "gradual", "aggressive", "cautious", "reluctant", "peaceful"
        """
        personality_lower = personality_internal.lower()

        # Aggressive/angry waking
        if any(word in personality_lower for word in ["aggressive", "angry", "hostile", "violent", "furious"]):
            return "aggressive"

        # Cautious/paranoid waking
        if any(word in personality_lower for word in ["paranoid", "suspicious", "cautious", "vigilant", "wary"]):
            return "cautious"

        # Alert/determined waking
        if any(word in personality_lower for word in ["determined", "focused", "confident", "bold", "assertive"]):
            return "alert"

        # Reluctant/depressed waking
        if any(word in personality_lower for word in ["depressed", "melancholic", "weary", "exhausted", "reluctant"]):
            return "reluctant"

        # Anxious/hesitant waking
        if any(word in personality_lower for word in ["anxious", "worried", "nervous", "fearful", "uncertain"]):
            return "gradual"

        # Peaceful/calm waking (default)
        return "peaceful"

    def _get_eye_opening_verb(self, wake_up_style: str) -> str:
        """Get personality-appropriate eye-opening verb phrase.

        Args:
            wake_up_style: Wake-up style category

        Returns:
            Verb phrase like "snap open", "flutter open", etc.
        """
        import random

        verbs = {
            "alert": ["snap open", "flash open", "shoot open"],
            "gradual": ["flutter open", "slowly open", "hesitantly open"],
            "aggressive": ["burst open", "jolt open", "slam open"],
            "cautious": ["crack open", "carefully open", "slit open"],
            "reluctant": ["drag open", "heavily open", "slowly open"],
            "peaceful": ["gently open", "drift open", "softly open"]
        }

        options = verbs.get(wake_up_style, verbs["peaceful"])
        return random.choice(options)

    def _get_immediate_reaction(self, wake_up_style: str, perception: int, shadow: int) -> str:
        """Generate immediate reaction after eyes open.

        Args:
            wake_up_style: Wake-up style category
            perception: Perception S-factor value (1-5)
            shadow: Shadow S-factor value (1-5)

        Returns:
            Reaction phrase
        """
        import random

        # High shadow adds vigilance
        if shadow >= 4:
            reactions = [
                "already scanning for threats",
                "instinctively checking for danger",
                "immediately alert to your surroundings"
            ]
            return random.choice(reactions)

        # High perception adds clarity
        if perception >= 4:
            if wake_up_style in ["alert", "cautious"]:
                reactions = [
                    "with sudden clarity",
                    "taking in every detail",
                    "instantly aware of your environment"
                ]
            else:
                reactions = [
                    "as details come into focus",
                    "gradually processing your surroundings",
                    "absorbing the scene around you"
                ]
            return random.choice(reactions)

        # Low perception
        if perception <= 2:
            reactions = [
                "as your vision slowly adjusts",
                "blurry at first",
                "struggling to focus"
            ]
            return random.choice(reactions)

        # Style-based defaults
        reactions_by_style = {
            "alert": ["with immediate awareness", "fully alert", "ready"],
            "gradual": ["as consciousness returns", "slowly orienting yourself", "hesitantly"],
            "aggressive": ["with a sharp breath", "abruptly", "with sudden urgency"],
            "cautious": ["carefully assessing", "warily", "guardedly"],
            "reluctant": ["unwillingly", "with effort", "heavily"],
            "peaceful": ["as peace settles over you", "calmly", "naturally"]
        }

        options = reactions_by_style.get(wake_up_style, reactions_by_style["peaceful"])
        return random.choice(options)

    def _get_perceptual_action(self, personality_external: str, perception: int) -> str:
        """Get perceptual action verb based on external personality and perception.

        Args:
            personality_external: External personality trait string
            perception: Perception S-factor value (1-5)

        Returns:
            Action phrase like "You notice", "You scan", etc.
        """
        import random

        personality_lower = personality_external.lower()

        # Observant/perceptive
        if "observant" in personality_lower or "perceptive" in personality_lower:
            if perception >= 4:
                return random.choice(["You immediately notice", "You pick up on", "You observe"])
            else:
                return random.choice(["You notice", "You see", "You observe"])

        # Cautious/careful
        if any(word in personality_lower for word in ["cautious", "careful", "wary"]):
            return random.choice(["You carefully scan", "You check", "You assess"])

        # Impulsive/reckless
        if any(word in personality_lower for word in ["impulsive", "reckless", "hasty"]):
            return random.choice(["You're already reaching for", "You quickly look at", "You glance toward"])

        # Withdrawn/isolated
        if any(word in personality_lower for word in ["withdrawn", "isolated", "introspective"]):
            return random.choice(["You take stock of", "You quietly observe", "You note"])

        # Default
        if perception >= 4:
            return random.choice(["You notice", "You see", "You observe"])
        else:
            return random.choice(["You look around at", "You see", "You notice"])

    def _generate_dynamic_wake_up_opening(
        self,
        actor,
        world_context: str,
        personality_internal: str,
        personality_external: str,
        s_factors_note: str
    ) ->str:
        """Generate personality-specific wake-up opening example.

        This creates a dynamic example that the LLM will use as a template
        for generating the actual scene opening. The example demonstrates
        how personality and S-factors should influence the narrative style.

        Args:
            actor: UserActor with personality, S-factors, occupation
            world_context: RAG-generated world setting details
            personality_internal: Internal personality traits
            personality_external: External personality traits
            s_factors_note: Summary of notable S-factors

        Returns:
            Example opening paragraph (2-4 sentences) demonstrating the style
        """
        from actor_sheet import SFactorType
        import random

        # Get S-factor values
        # Note: Using SMARTS as a proxy for perception/awareness
        s_factors = actor.sheet.s_factors
        perception = s_factors.get_factor(SFactorType.SMARTS)  # Use Smarts for perceptual awareness
        smarts = s_factors.get_factor(SFactorType.SMARTS)
        shadow = s_factors.get_factor(SFactorType.SHADOW)
        strength = s_factors.get_factor(SFactorType.STURDINESS)  # Sturdiness = physical strength
        sociability = s_factors.get_factor(SFactorType.SOCIABILITY)

        # Classify wake-up style
        wake_up_style = self._classify_wake_up_style(personality_internal)

        # Generate components
        eye_verb = self._get_eye_opening_verb(wake_up_style)
        immediate_reaction = self._get_immediate_reaction(wake_up_style, perception, shadow)
        perceptual_action = self._get_perceptual_action(personality_external, perception)

        # Determine sensory detail count based on perception
        if perception >= 4:
            sensory_count = 3
            detail_quality = "specific sensory details (visual, audio, smell)"
        elif perception >= 3:
            sensory_count = 2
            detail_quality = "clear sensory details (visual and one other sense)"
        else:
            sensory_count = 1
            detail_quality = "obvious sensory details (primarily visual)"

        # Generate occupation-based character detail hints
        occupation_lower = actor.sheet.occupation.lower() if actor.sheet.occupation else ""
        if any(word in occupation_lower for word in ["soldier", "guard", "military", "security"]):
            character_hint = "instinctively checking for gear or assessing tactical situation"
        elif any(word in occupation_lower for word in ["artist", "painter", "creative", "musician"]):
            character_hint = "drawn to sensory or aesthetic details in the environment"
        elif any(word in occupation_lower for word in ["scholar", "academic", "librarian", "researcher"]):
            character_hint = "mind immediately turning to analytical observations"
        elif any(word in occupation_lower for word in ["criminal", "thief", "smuggler", "fence"]):
            character_hint = "checking for security, exits, or signs of disturbance"
        elif any(word in occupation_lower for word in ["doctor", "healer", "medic", "nurse"]):
            character_hint = "automatically assessing physical state or environment"
        else:
            character_hint = "a small physical action that reveals character"

        # Construct the example opening
        example_opening = f"""Your eyes {eye_verb} {immediate_reaction}. {perceptual_action} [describe environment with {sensory_count} {detail_quality}]. [Add {character_hint}, but NEVER explain why - just show the action]. [End with atmospheric detail from world context]."""

        return example_opening

    def validate_scene_population(self, scene_data: dict) -> dict:
        """
        Analyzes a generated scene to verify it is properly populated with
        content, actors, and interactables.
        
        Returns a report dict:
        {
            'status': 'valid' | 'invalid' | 'sparse',
            'issues': [],
            'population_summary': str,
            'has_actors': bool,
            'has_interactables': bool
        }
        """
        issues = []
        status = 'valid'
        
        if not scene_data or not isinstance(scene_data, dict):
            return {'status': 'invalid', 'issues': ['No scene data provided'], 'population_summary': 'None', 'has_actors': False, 'has_interactables': False}

        # 1. Structural Validation
        scene_elements = scene_data.get('scene_elements')
        if not scene_elements:
            issues.append("Missing 'scene_elements'")
            status = 'invalid'
        else:
            setting = scene_elements.get('setting', '')
            if len(setting.split()) < 20:
                issues.append("Setting description is too brief (< 20 words)")
                status = 'sparse'
            
            expl_opps = scene_elements.get('exploration_opportunities', [])
            if not expl_opps or len(expl_opps) == 0:
                issues.append("No exploration opportunities defined")
                status = 'sparse'

        # 2. Population Validation
        nua = scene_data.get('nua')
        inua = scene_data.get('inua')

        # Normalize shapes (some models return lists)
        if isinstance(nua, list):
            if len(nua) == 1 and isinstance(nua[0], dict):
                nua = nua[0]

        inua_items = []
        if isinstance(inua, dict):
            inua_items = [inua]
        elif isinstance(inua, list):
            inua_items = [x for x in inua if isinstance(x, dict)]

        has_nua = isinstance(nua, dict)
        has_inua = len(inua_items) > 0

        if nua is not None and not isinstance(nua, dict):
            issues.append(f"NUA must be an object/dict or null; got {type(nua).__name__}")
            status = 'invalid'

        if inua is not None and not isinstance(inua, (list, dict)):
            issues.append(f"INUA must be a list/object or null; got {type(inua).__name__}")
            status = 'invalid'

        if has_nua:
            if not nua.get('name') or not nua.get('occupation'):
                issues.append("NUA present but missing name or occupation")
                status = 'invalid'
            if not nua.get('skills') or len(nua.get('skills', {})) < 3:
                issues.append("NUA has insufficient skills defined")

        if inua is not None and not inua_items:
            issues.append("INUA present but empty or invalid")
            status = 'sparse' if status != 'invalid' else status

        # INUA entries are inanimate interactables; they typically need name + description.
        for idx, item in enumerate(inua_items):
            if not item.get('name') or not item.get('description'):
                issues.append(f"INUA[{idx}] missing name or description")
                status = 'sparse' if status != 'invalid' else status

        # 3. Summary
        actors_count = 1 if has_nua else 0
        interactables_count = len(inua_items) if has_inua else 0
        
        summary = f"{actors_count} NPC(s), {interactables_count} Interactable(s)"
        
        # If status is valid but purely empty (no NUA/INUA)
        if status == 'valid' and not has_nua and not has_inua:
            # This might be okay for pure exploration, but note it
            summary += " (Pure Exploration)"
            
        return {
            'status': status,
            'issues': issues,
            'population_summary': summary,
            'has_actors': has_nua,
            'has_interactables': has_inua
        }

    def _get_initial_scene_prompt(self, actor: UserActor) -> str:
        # Get dynamic world context from RAG system
        setting_context = self._get_setting_context()
        location_context = self._get_location_context(actor.sheet.occupation, actor.sheet.goals)
        occupation_context = self._get_occupation_context(actor.sheet.occupation)
        cultural_context = self._get_cultural_context()
        
        # Get INUA context for objects/interactables in scenes
        inua_category = WorldbuildingCategory.INUA_GENERATION if WorldbuildingCategory else None
        inua_context = self._get_rag_context(
            query="inanimate objects documents equipment environmental features interactables",
            max_tokens=400,
            category_filter=inua_category
        )
        
        # Combine all RAG context
        world_context = f"""
**WORLD SETTING AND CONTEXT:**
{setting_context}

**LOCATION CONTEXT:**
{location_context}

**OCCUPATION CONTEXT:**
{occupation_context}

**CULTURAL ATMOSPHERE:**
{cultural_context}

**INTERACTABLE OBJECTS (INUA) REFERENCE:**
{inua_context}
""".strip()
        
        # Extract personality traits for characterization
        personality_internal = getattr(actor.sheet, 'personality_traits', {}).get('internal', 'Determined and focused')
        personality_external = getattr(actor.sheet, 'personality_traits', {}).get('external', 'Calm and observant')
        
        # Extract S-factors for capability context
        s_factors = actor.sheet.s_factors
        from actor_sheet import SFactorType
        s_factor_summary = []
        for sf_type in SFactorType:
            value = s_factors.get_factor(sf_type)
            if value <= 1:
                s_factor_summary.append(f"{sf_type.name.capitalize()}: Minimal ({value})")
            elif value >= 4:
                s_factor_summary.append(f"{sf_type.name.capitalize()}: Exceptional ({value})")
        s_factors_note = ", ".join(s_factor_summary) if s_factor_summary else "Average across all attributes"
        
        # Extract key skills
        skills = actor.sheet.skills or {}
        top_skills = sorted(skills.items(), key=lambda x: x[1], reverse=True)[:3]
        skills_note = ", ".join([f"{name} ({val})" for name, val in top_skills]) if top_skills else "No specialized skills"
        
        # Get age and location
        age = getattr(actor.sheet, 'age', 30)
        location = getattr(actor.sheet, 'location', 'Unknown')
        simulation_year = getattr(actor.sheet, 'simulation_year', ActorSheet.get_simulation_year())

        # Get established facts about the UA (if fact system is available)
        ua_facts = self._get_actor_facts(actor.name, max_facts=15)

        return f"""You are a scenario designer for a simulation. Your task is to generate an opening exploration scene for the user's actor, {actor.name}, based on their profile.

        **Actor Profile:**
        - Name: {actor.name}
        - Age: {age} years old
        - Location: {location}, {simulation_year}
        - Occupation: {actor.sheet.occupation}
        - Goals: {', '.join(actor.sheet.goals)}
        - Personality (Internal): {personality_internal}
        - Personality (External): {personality_external}
        - Notable Attributes: {s_factors_note}
        - Key Skills: {skills_note}
{ua_facts}
        **CRITICAL - CHARACTER CONSISTENCY:**
        The scene MUST be appropriate for this specific character:
        - A {age}-year-old would realistically be found in age-appropriate locations (not a 70-year-old in a nightclub or a teenager in a corporate boardroom unless their occupation justifies it)
        - Someone with Minimal Smarts (1) should NOT have memories or situations implying academic achievement
        - Someone with Minimal Sociability (1) would likely be in solitary or low-social-interaction settings
        - Someone with Exceptional Shadow (4-5) might be in morally ambiguous or secretive situations
        - The starting location should make sense for their occupation, age, and time of day

        {world_context}

        **INITIAL SCENE PHILOSOPHY:**
        The first scene should start in ROAM mode - pure exploration without immediate conflict or NPCs. This allows the user to naturally discover the world and develop their own interests before the narrative loop introduces complications.

        **Scene Requirements:**
        The scene description must be narratively engaging and establish an exploration opportunity. It must:
        1.  **START WITH WAKING UP:** The opening line MUST begin with "Your eyes shoot open" — this is the fixed entry point for every new session. Do NOT vary this phrase.
        2.  **USE ACTIVE PERCEPTION VERBS:** After eyes open, use active perception: "You look around...", "You see...", "You notice...", "You hear...", "You smell..." - NEVER use passive "You are in..." or "You find yourself in..."
        3.  **Place the actor in an interesting location** related to their goals or occupation
        4.  **Provide multiple exploration opportunities** (places to investigate, things to examine, directions to go)
        5.  **NO NPCs or opponents** - this is pure environmental exploration
        6.  **Establish atmosphere and context** using the world setting details above
        7.  **Ground the Narrative:** Describe only the immediate physical environment and current situation. **DO NOT invent or imply any past history, relationships, or events** that are not explicitly provided in the actor's profile.
        8.  **CRITICAL: Use SECOND PERSON ("you") and PRESENT TENSE** - The user IS the character experiencing this moment NOW
        9.  **CHARACTERIZE THE UA:** Add 1-2 brief character details (thoughts, habits, or reactions) based on personality traits. Keep it subtle - don't overdo it.
        10. **FOCUS ON ACTION, NOT REASON (FIX BUG #14):** Describe WHAT the character does, NEVER WHY they do it. Show physical actions and observable behavior only. ABSOLUTELY NO explanations of motivations, personality trait references, or psychological commentary. The player experiences the character directly - let them interpret their own motivations.
            - ❌ WRONG: "Your hands reach for the notebook, a habit born from your imposter syndrome."
            - ❌ WRONG: "You glance around nervously, your anxiety showing."
            - ❌ WRONG: "You move cautiously due to your paranoia."
            - ❌ WRONG: "reflecting your determination" or "showing your confidence"
            - ✅ RIGHT: "Your hands reach for the notebook." (Just the action, no explanation)
            - ✅ RIGHT: "Your hands reach for the nearby notebook."
            - ✅ RIGHT: "You glance around the room."
            - ✅ RIGHT: "You move cautiously toward the door."
        10. **INTERIOR/EXTERIOR CONSISTENCY:** Pick ONE perspective and stick to it:
           - **EXTERIOR**: Describe what you see FROM OUTSIDE (building facades, entrances, windows, street details). You CANNOT see detailed interior layouts from outside.
           - **INTERIOR**: Describe what you see FROM INSIDE (room layout, furniture, doors, interior details). You CANNOT see exterior street details from inside.
           - **NEVER MIX**: Don't describe "standing outside" and then list interior room details. Pick one location and describe only what's visible from that vantage point.
        10. **LENGTH CONSTRAINT: 4-6 SENTENCES MAXIMUM** - Be concise and evocative, not exhaustive. Suggest details, don't inventory everything.
        11. **USE WORLD CONTEXT**: Reference specific details from the world setting context above (technology, culture, locations, etc.)

        **MODE A GOAL LOCK (HARD CONSTRAINT):**
        - The JSON field `scene_elements.ua_goal` MUST be EXACTLY one of the actor's Goals listed in the Actor Profile.
        - Copy/paste the goal line EXACTLY. Do NOT paraphrase it. Do NOT invent a new goal.

        **CRITICAL CLASSIFICATION RULES:**
        - **NUA (Non-User Actor)**: Sentient beings with consciousness, emotions, and independent thought (humans, aliens, intelligent creatures)
        - **INUA (Inanimate Non-User Actor)**: Objects, mechanisms, programmed systems, and automated entities WITHOUT consciousness
        - **Robotic/Automated Entities**: Drones, robots, security systems, AI constructs, androids, and automated guardians are ALWAYS INUA, never NUA
        - **Examples of INUA**: "Guardian-8 Security Drone", "Automated Turret", "AI Security System", "Robotic Sentry"
        - **Examples of NUA**: "Human Guard", "Alien Merchant", "Sentient AI with consciousness"

        **Dynamic Opening Style for {actor.name}:**

        Based on their personality and attributes, generate an opening that reflects:
        - **Internal Personality**: {personality_internal}
        - **External Personality**: {personality_external}
        - **Notable Attributes**: {s_factors_note}
        - **Occupation Context**: {actor.sheet.occupation}

        {self._generate_dynamic_wake_up_opening(actor, world_context, personality_internal, personality_external, s_factors_note)}

        **CRITICAL - Vary the wake-up style based on personality:**
        - Confident/determined characters wake alertly ("eyes snap/flash/shoot open")
        - Anxious/worried characters wake hesitantly ("eyes flutter/slowly/hesitantly open")
        - Paranoid characters immediately scan for threats
        - High Perception (4-5) characters notice multiple sensory details (3+)
        - Low Perception (1-2) characters notice only obvious details (1)
        - Occupation should flavor the character's immediate reaction (soldier checks for gear, artist notices aesthetics)

        **FORBIDDEN Opening Lines (WRONG - Passive Voice):**
        - "Your eyes open. You are in a small apartment..." ❌ NEVER USE "You are in"
        - "Your eyes open. You find yourself in a workshop..." ❌ NEVER USE "You find yourself"
        - "Your eyes shoot open..." ❌ NEVER USE this generic line — use the Dynamic Opening Style above instead

        **Note:** Use specific details from the WORLD SETTING AND CONTEXT above. Reference appropriate technology, cultural elements, locations, and atmosphere from the lore provided.

        **Your Task:**
        Create an exploration scene with NO NPCs or opponents. Focus on environmental storytelling and multiple investigation opportunities. Use the JSON structure below:

        ```json
        {{
            "scene_elements": {{
                "setting": "A concise description (4-6 sentences) with a personality-appropriate opening showing how {actor.name} wakes based on their traits. Follow the Dynamic Opening Style example above - vary the eye-opening verb, sensory detail count, and character reaction based on personality and S-factors. Use ACTIVE PERCEPTION ('You look around...', 'You see...', 'You notice...'). NEVER use 'You are in' or 'You find yourself'. Use world context details with appropriate technology, cultural elements, and atmosphere. Be evocative, not exhaustive.",
                "ua_goal": "MUST be EXACTLY one of the actor's Goals from the Actor Profile (copy/paste line exactly).",
                "exploration_opportunities": "List 3-4 specific things the actor can investigate, examine, or explore in this scene."
            }},
            "nua": null,
            "inua": null,
            "end_conditions": {{
                "exploration_complete": "The actor has thoroughly investigated the area and discovered key information or opportunities.",
                "new_direction": "The actor chooses to move to a different location or pursue a different approach."
            }}
        }}
        ```

        **Instructions:**
        - Focus on rich environmental details that match the world setting from the context above (use period-appropriate technology, culture, and atmosphere - vary the details to avoid repetition)
        - Provide multiple specific investigation opportunities to encourage exploration
        - Set up potential for the Four-Mode Narrative Loop to introduce NPCs later based on player actions
        - Respond with ONLY the fully populated, valid JSON object. No extra text or explanations.
        """

    def _get_next_scene_prompt(self, actor: UserActor, previous_scene: dict, outcome: str, transition_context: dict = None) -> str:
        outcome_desc = {
            'win': f"{actor.name} was victorious.",
            'lose': f"{actor.name} was defeated.",
            'flee': f"{actor.name} fled the scene."
        }.get(outcome, "The scene ended.")

        transition_info = ""
        continuity_requirement = ""
        
        if transition_context and outcome == 'scene_evaluation':
            transition_info = f"""
        **Scene Transition Context:**
        - Previous scene lasted {transition_context.get('turn_count', 'unknown')} turns
        - Transition reason: {transition_context.get('transition_reason', 'natural progression')}
        - Transition type: {transition_context.get('transition_type', 'story progression')}
        - Previous setting: {transition_context.get('previous_scene_setting', 'unknown location')}"""
            
            continuity_requirement = """
        **ENHANCED CONTINUITY REQUIREMENT:**
        Since this is a natural scene transition (not combat-driven), create stronger narrative bridges that acknowledge recent events and character development."""
        elif transition_context is None and outcome == 'scene_evaluation':
            continuity_requirement = """
        **FIRST SCENE NOTE:**
        This appears to be the first scene in the simulation. Do NOT include transition bridges since there is no previous scene to reference."""

        # Get rich narrative context if available
        narrative_context = ""
        if hasattr(self, 'narrative_context_manager') and self.narrative_context_manager:
            try:
                context_data = self.narrative_context_manager.get_context_for_llm(
                    lookback_events=8, 
                    importance_threshold="notable"
                )
                if context_data and context_data.strip():
                    narrative_context = f"""
        **RICH NARRATIVE CONTEXT:**
        {context_data}
        
        **CONTINUITY INSTRUCTION:**
        Use this narrative context to create meaningful connections between the previous events and the new scene. Reference character development, ongoing plot threads, and established relationships."""
            except Exception as e:
                self.logger.log_system(f"Warning: Could not retrieve narrative context for scene generation: {e}")

        # Get Four-Mode Narrative Loop guidance if available
        narrative_guidance = ""
        if transition_context and isinstance(transition_context, dict):
            narrative_mode = transition_context.get('narrative_mode')
            narrative_intent = transition_context.get('narrative_intent')
            narrative_tone = transition_context.get('narrative_tone')
            
            if narrative_mode:
                narrative_guidance = f"""
        **FOUR-MODE NARRATIVE GUIDANCE:**
        Current Mode: {narrative_mode.title()}
        Intent: {narrative_intent or 'Natural progression'}
        Tone: {narrative_tone or 'Balanced'}
        
        **MODE-SPECIFIC INSTRUCTIONS:**"""
                
                if narrative_mode.lower() == 'roam':
                    narrative_guidance += """
        - ROAM MODE: Focus on exploration and discovery
        - Allow drift-friendly interactions and socializing
        - Introduce gentle opportunities for interest development
        - Avoid forced conflict or high-stakes situations"""
                elif narrative_mode.lower() == 'spark':
                    narrative_guidance += """
        - SPARK MODE: Introduce gentle nudges toward purpose
        - Present opportunities that align with character goals
        - Create soft hooks that invite engagement
        - Build toward meaningful choices without pressure"""
                elif narrative_mode.lower() == 'pressure':
                    # Check for active mission
                    active_mission = transition_context.get('active_mission')
                    mission_progress = transition_context.get('mission_progress', 0.0)
                    
                    if active_mission:
                        narrative_guidance += f"""
        - PRESSURE MODE: Advance Mission '{active_mission}' (Progress: {int(mission_progress * 100)}%)
        - Create obstacles that directly challenge progress toward this mission
        - Introduce complications related to the mission goal
        - Mix hard challenges with easier wins to show progress
        - Challenge the character's approach to achieving the mission"""
                    else:
                        narrative_guidance += """
        - PRESSURE MODE: Heighten stakes through obstacles
        - Introduce complications or recontextualize information
        - Create tension through time pressure or difficult choices
        - Challenge the character's assumptions or plans"""
                elif narrative_mode.lower() == 'outcome':
                    # Check for completed mission
                    active_mission = transition_context.get('active_mission')
                    mission_progress = transition_context.get('mission_progress', 0.0)
                    
                    if active_mission and mission_progress >= 1.0:
                        narrative_guidance += f"""
        - OUTCOME MODE: Resolve Mission '{active_mission}'
        - Provide natural consequences and rewards for mission completion
        - Tie up loose ends related to this mission
        - Show how the world changed from this mission
        - Hint at new possibilities while providing closure"""
                    else:
                        narrative_guidance += """
        - OUTCOME MODE: Focus on resolution and reflection
        - Provide natural consequences for previous actions
        - Allow for character growth and learning
        - Create breathing room for processing events"""

        # Get RAG worldbuilding context for scene transition
        rag_context = ""
        if self.rag_system:
            try:
                # Search for relevant worldbuilding based on previous scene and actor goals
                prev_setting = previous_scene.get('scene_elements', {}).get('setting', '')
                search_query = f"{prev_setting[:200]} {' '.join(actor.sheet.goals[:2])}"
                categories = []
                if WorldbuildingCategory:
                    categories = [
                        WorldbuildingCategory.TEMPORAL,
                        WorldbuildingCategory.PLACES,
                        WorldbuildingCategory.CITIES,
                        WorldbuildingCategory.CULTURE,
                        WorldbuildingCategory.CIVILIZATION,
                        WorldbuildingCategory.MECHANICS,
                        WorldbuildingCategory.SUPERNATURAL,
                    ]
                rag_context = get_multi_category_context_for_llm(
                    self.rag_system,
                    query=search_query,
                    categories=categories,
                    max_tokens_per_category=90,
                    include_related=True,
                )
                if rag_context:
                    rag_context = f"\n\n**ESTABLISHED WORLDBUILDING:**\n{rag_context}\n"
            except Exception as e:
                self.logger.log_system(f"Warning: Could not retrieve RAG context for scene transition: {e}")

        return f"""You are a scenario designer for a simulation. Your task is to generate the next scene in an ongoing simulation with smooth narrative continuity.

        **Previous Scene Summary:**
        {previous_scene.get('description', previous_scene.get('scene_elements', {}).get('setting', 'Previous scene details unavailable'))}

        **Outcome of Previous Scene:**
        {outcome_desc}{transition_info}{continuity_requirement}{narrative_context}{narrative_guidance}{rag_context}

        **Actor's Current State:**
        - Name: {actor.name}
        - Stamina: {actor.sheet.statuses[StatusType.STAMINA].value}
        - Spirit: {actor.sheet.statuses[StatusType.SPIRIT].value}
        - Goals: {', '.join(actor.sheet.goals)}

        **Transition Bridge Examples:**
        - After victory: "Still catching your breath from the confrontation, you notice..."
        - After defeat: "Nursing your wounds from the encounter, you find yourself..."
        - After exploration: "Having thoroughly searched the area, you decide to..."
        - Natural progression: "The events here remind you of your true purpose, so you..."

        **Scene Requirements:**
        Generate a logical follow-up scene. The requirements depend on whether this is the first scene or a subsequent scene:

        **For SUBSEQUENT scenes (with transition context):**
        1.  **START with a transition bridge** that acknowledges what just happened
        2.  **Introduce a clear goal** for the actor based on story progression
        3.  **Introduce a Non-User Actor (NUA)** if appropriate for the scene
        4.  **Establish a new source of conflict** that feels connected to the ongoing narrative

        **CRITICAL PERSPECTIVE REQUIREMENT:**
        - **ALWAYS use SECOND PERSON ("you/your") and PRESENT TENSE for the UA**
        - The user IS the character experiencing this moment NOW
        - Never use third person (actor name) for the UA in scene descriptions

        **For FIRST scenes (no transition context):**
        1.  **Establish the setting** and immediate situation clearly
        2.  **Introduce a clear goal** for the actor
        3.  **Introduce a Non-User Actor (NUA)** if appropriate for the scene
        4.  **Establish a source of conflict** - do NOT include transition bridges

        **Enhanced Example with Transition (SECOND PERSON):**
        "After successfully bypassing the biometric checkpoint, you pocket the decrypted access token and step back into the Yield Zone transit corridor. The data you've extracted points toward a Signal Gap two sectors north, but as you move through the filtered air of the corridor, you notice a Compliance Auditor has broken from the standard patrol pattern and is now matching your pace. They seem particularly interested in your yield profile readout. When you divert into a maintenance sub-corridor to test your suspicions, they follow. It's clear they want what you're carrying, and this narrow passage offers little room to lose them."

        **Example for First Scene style only — DO NOT copy this setting, use the actor's actual Location above:**
        "The yield terminal on the wall is mid-cycle, running the morning compliance roster. Someone left a half-eaten ration block on the counter — the shift change was recent. You don't yet know if you're alone."

        Based on this, generate the next scene as a JSON object.
        Respond with ONLY a valid JSON object using the following structure.
        {{
            "scene_elements": {{
                "setting": "A brief description of the physical environment.",
                "ua_goal": "A clear, immediate goal for the actor.",
                "conflict": "A description of the core conflict.",
                "transition_bridge": "A 1-2 sentence bridge that references the previous scene's outcome (ONLY for subsequent scenes, omit for first scene)."
            }},
            "nua": {{...}} or null,
            "end_conditions": {{...}}
        }}
        """

    def generate_nua(self, context: str = "", scene_description: str = "", existing_names: list = None) -> NonUserActor:
        """Generates a Non-User Actor (NUA) for dynamic actor creation.

        NUAs are sentient characters that can take independent actions and have goals.
        """
        self.logger.log_system("Generating new NUA...")

        # Generate NUA profile using LLM
        nua_data = self._generate_nua_profile(context, scene_description, existing_names=existing_names)
        
        personality_traits = nua_data.get('personality_traits', {})
        if not personality_traits or not personality_traits.get('internal') or not personality_traits.get('external'):
            self.logger.log_system(f"Personality traits missing for {nua_data.get('name')}. Generating...")
            personality_traits = self._generate_personality_traits(nua_data)
        nua_data['personality_traits'] = personality_traits

        s_factors_data = nua_data.get('s_factors', {})
        required_s_factors = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
        if not s_factors_data or not required_s_factors.issubset(s_factors_data.keys()):
            self.logger.log_system(f"S-Factors missing for NUA {nua_data.get('name')}. Generating...")
            s_factors_data = self._generate_s_factors(nua_data)
        
        from actor_sheet import SFactors
        
        swiftness = s_factors_data.get('swiftness', 3)
        sociability = s_factors_data.get('sociability', 3)
        sturdiness = s_factors_data.get('sturdiness', 3)
        smarts = s_factors_data.get('smarts', 3)
        shadow = s_factors_data.get('shadow', 3)
        
        s_factors_obj = SFactors(
            swiftness=swiftness,
            sociability=sociability,
            sturdiness=sturdiness,
            smarts=smarts,
            shadow=shadow
        )

        nua_skills = nua_data.get('skills', {})
        if len(nua_skills) < 5:
            error_msg = f"NUA {nua_data.get('name', 'Unknown')} has only {len(nua_skills)} skills, minimum 5 required"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"NUA generation failed: {error_msg}")

        inventory_data = nua_data.get('inventory') or []
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                new_item = Item(item, "", 1)
                inventory.append(new_item)

        goals_data = nua_data.get('goals') or []
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data

        try:
            allowed_endowments = self._get_allowed_endowments_from_rag(actor_type='nua')
            endowments_norm = self._coerce_endowments_to_allowed(nua_data.get('endowments', {}) or {}, allowed_endowments)
            nua_data['endowments'] = endowments_norm
        except Exception:
            nua_data['endowments'] = {}

        nua_sheet = ActorSheet(
            name=nua_data.get('name', 'Unknown NUA'),
            s_factors=s_factors_obj,
            personality_traits=personality_traits,
            goals=goals_list,
            occupation=nua_data.get('occupation', 'Unknown'),
            faction=nua_data.get('faction', 'None'),
            skills=nua_skills,
            endowments=nua_data.get('endowments', {}),
            inventory=inventory,
            age=nua_data.get('age', 30),
            location=nua_data.get('location', 'Unknown')
        )

        try:
            nua_sheet.canonical_name = nua_sheet.name
            occ = (getattr(nua_sheet, 'occupation', None) or '').strip()
            if not getattr(nua_sheet, 'known_as', None):
                nua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'unemployed', 'none'):
                if occ not in nua_sheet.known_as:
                    nua_sheet.known_as.append(occ)
                if not getattr(nua_sheet, 'public_description', None):
                    nua_sheet.public_description = f"the {occ.lower()}"
            else:
                # Deterministic fallback so stranger-safe naming never becomes empty
                if not nua_sheet.known_as:
                    nua_sheet.known_as.append('person')
                if not getattr(nua_sheet, 'public_description', None):
                    nua_sheet.public_description = "the person"
        except Exception:
            pass
        
        # Generate OCEAN/MBTI personality profile
        try:
            from personality_mood_system import PersonalityGenerator
            personality_gen = PersonalityGenerator()
            backstory = " ".join(goals_list) if goals_list else ""
            nua_sheet.personality_profile = personality_gen.generate_personality(
                actor_name=nua_data.get('name', 'Unknown'),
                occupation=nua_data.get('occupation', 'Unknown'),
                backstory=backstory,
                existing_traits=personality_traits
            )
            self.logger.log_system(f"Generated personality profile for {nua_data['name']}")
        except Exception as e:
            self.logger.log_system(f"Could not generate personality profile: {e}")

        self.logger.log_system(f"Successfully generated NUA: {nua_data['name']} with {len(nua_skills)} skills")

        # Create NUA object
        nua = NonUserActor(nua_sheet)

        # Establish facts about this NUA
        self._establish_nua_facts(nua, source="dynamic_nua_creation")

        # Record mention for this NUA (location will be set when spawned)
        # For now, use a generic "Unknown" location since this is creation, not spawning
        # The actual spawn location will be recorded when the NUA is added to the scene
        self._record_nua_mention(
            nua,
            location="Unknown",  # Will be updated on spawn
            context=f"{nua.sheet.name} created as {nua.sheet.occupation}",
            turn_number=0,
            scene_id="nua_creation"
        )

        # Display spark creation indicator (only for the 3 spark types: MOMENTUM, EXCHANGE, CALLBACK)
        spark_type = getattr(self, '_current_spark_type', None)
        if spark_type and spark_type.upper() in ('MOMENTUM', 'EXCHANGE', 'CALLBACK'):
            # Color based on spark type
            if spark_type.upper() == 'MOMENTUM':
                color = '\033[92m'  # Green for momentum
                emoji = '🚀'
            elif spark_type.upper() == 'EXCHANGE':
                color = '\033[93m'  # Yellow for exchange
                emoji = '💬'
            else:  # CALLBACK
                color = '\033[95m'  # Magenta for callback
                emoji = '🔄'
            
            print(f"\n{color}{emoji} {spark_type.upper()} SPARK → NUA {emoji}\033[0m")
            print(f"{color}{'─' * 40}\033[0m")
            print(f"{color}  Name: {nua_data.get('name', 'Unknown')}\033[0m")
            print(f"{color}  Occupation: {nua_data.get('occupation', 'Unknown')}\033[0m")
            faction = nua_data.get('faction', 'None')
            if faction and faction != 'None':
                print(f"{color}  Faction: {faction}\033[0m")
            if nua_sheet.personality_profile:
                try:
                    mbti = nua_sheet.personality_profile.mbti_type if hasattr(nua_sheet.personality_profile, 'mbti_type') else 'Unknown'
                    print(f"{color}  MBTI: {mbti}\033[0m")
                except:
                    pass
            print(f"{color}{'─' * 40}\033[0m\n")
            # Clear after use
            self._current_spark_type = None

        return nua

    def _generate_nua_profile(self, context: str = "", scene_description: str = "", existing_names: list = None) -> dict:
        """Generates a complete NUA profile including name, occupation, goals, skills, and inventory."""
        
        # Get dynamic world context from RAG system
        setting_context = self._get_setting_context()
        cultural_context = self._get_cultural_context()

        # Location policy: by default, all generated actors are in the Current Scene.
        # Only allow other locations when explicitly implied by the context.
        allow_remote_location = self._context_allows_remote_location(context=context, scene_description=scene_description)

        cities_category = WorldbuildingCategory.CITIES if WorldbuildingCategory else None
        cities_context = self._get_rag_context(
            query="major cities settlements",
            max_tokens=700,
            category_filter=cities_category
        )
        
        # Get occupation context if we can extract it from context/scene
        # Category: NUA_OCCUPATIONS for NPC occupation options
        occupation_category = WorldbuildingCategory.NUA_OCCUPATIONS if WorldbuildingCategory else None
        if context:
            occupation_context = self._get_rag_context(
                query=f"occupation {context} social class",
                max_tokens=300,
                category_filter=occupation_category
            )
        else:
            occupation_context = self._get_rag_context(
                query="common occupations people jobs social class",
                max_tokens=300,
                category_filter=occupation_category
            )

        allowed_occupations: list[str] = []
        try:
            import re
            if occupation_context:
                for line in occupation_context.splitlines():
                    line_s = line.strip()
                    if not line_s.startswith(('-', '•', '*')):
                        continue
                    line_s = line_s.lstrip('-•*').strip()
                    if not line_s:
                        continue
                    if ':' not in line_s:
                        continue
                    lhs, rhs = line_s.split(':', 1)
                    lhs = lhs.strip()
                    rhs = rhs.strip()

                    if lhs:
                        candidate = re.sub(r'\([^)]*\)', '', lhs).strip()
                        if candidate.lower().startswith('the '):
                            candidate = candidate[4:].strip()
                        if candidate and candidate not in allowed_occupations:
                            allowed_occupations.append(candidate)
                        continue

                    if not rhs:
                        continue
                    rhs = re.sub(r'\([^)]*\)', '', rhs).strip()
                    rhs = rhs.replace(' or ', ', ')
                    parts = [p.strip(" \t-–—") for p in rhs.split(',')]
                    for p in parts:
                        if not p:
                            continue
                        if p.lower().startswith('the '):
                            continue
                        if p.lower() in ('and',):
                            continue
                        if p not in allowed_occupations:
                            allowed_occupations.append(p)
        except Exception:
            allowed_occupations = []

        # Category: NUA_GOALS for NPC goal patterns
        goals_category = WorldbuildingCategory.NUA_GOALS if WorldbuildingCategory else None
        goals_context = self._get_rag_context(
            query=f"goals motivations daily routine {context}" if context else "goals motivations daily routine",
            max_tokens=250,
            category_filter=goals_category
        )
        
        # Get NUA-specific generation guidelines
        # Category: NUA_GENERATION for Non-User Actor generation
        nua_category = WorldbuildingCategory.NUA_GENERATION if WorldbuildingCategory else None
        actor_generation_context = self._get_rag_context(
            query="non-user actor generation npc archetypes sympathy personality names ages",
            max_tokens=600,
            category_filter=nua_category
        )
        
        # Also get shared mechanics (status, skills reference)
        mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
        mechanics_context = self._get_rag_context(
            query="status stamina spirit supply skills endowments abilities",
            max_tokens=400,
            category_filter=mechanics_category
        )

        allowed_endowments = self._get_allowed_endowments_from_rag(actor_type='nua')
        allowed_endowments_block = "\n".join([f"- {s}" for s in allowed_endowments[:80]]) if allowed_endowments else ""
        endowments_constraints = ""
        if allowed_endowments:
            endowments_constraints = f"""

ENDOWMENT LOCK (HARD CONSTRAINT):
- You may include 0-1 endowment ability.
- Endowments are OPTIONAL. If none of the allowed endowments below fit the character, do NOT include any.
- If you do include an endowment, the endowment name MUST be EXACTLY one of the allowed names below (copy/paste exactly).

ALLOWED ENDOWMENTS:
{allowed_endowments_block}
""".rstrip()
        
        # Get faction context for NUAs
        faction_context = self._get_faction_context_for_nua()

        # Goals are guidance-driven (no hard whitelist)
        allowed_goals = []
        allowed_goals_block = ""

        allowed_factions = self._get_explicit_faction_whitelist('nua')
        allowed_factions_block = "\n".join([f"- {f}" for f in allowed_factions[:80]]) if allowed_factions else ""

        allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
        allowed_skill_vocab_block = "\n".join([f"- {s}" for s in allowed_skill_vocab]) if allowed_skill_vocab else ""
        allowed_item_vocab_block = "\n".join([f"- {s}" for s in allowed_item_vocab]) if allowed_item_vocab else ""
        mode_b_constraints = ""
        if allowed_skill_vocab or allowed_item_vocab:
            mode_b_constraints = f"""

**MODE B VOCAB LOCK (HARD CONSTRAINTS):**
- Skills MUST use EXACT names from the SKILLS VOCAB list below (copy/paste only; no modifiers like 'Advanced', 'Hooded', etc).
- Inventory item names MUST use EXACT names from the ITEMS VOCAB list below (copy/paste only; no adjectives/variants).

SKILLS VOCAB (Mode B - Allowed):
{allowed_skill_vocab_block}

ITEMS VOCAB (Mode B - Allowed):
{allowed_item_vocab_block}
""".rstrip()
        
        # Combine all RAG context
        world_context = f"""
**WORLD SETTING:**
{setting_context}

**CULTURAL CONTEXT:**
{cultural_context}

**OCCUPATION CONTEXT:**
{occupation_context}

**GOAL PATTERNS (NUA):**
{goals_context}

**AVAILABLE FACTIONS/CLANS:**
{faction_context if faction_context else "No specific factions defined - use 'None' for faction"}

**EXPLICIT FACTION LIBRARY (NUA) - MODE A WHITELIST:**
{allowed_factions_block}

**NUA GENERATION GUIDELINES:**
{actor_generation_context}

**STATUS & SKILLS REFERENCE:**
{mechanics_context}
""".strip()

        allowed_occ_block = "\n".join([f"- {o}" for o in allowed_occupations]) if allowed_occupations else ""
        rag_constraints = ""
        if allowed_occupations:
            rag_constraints = f"""

OCCUPATION LOCK (HARD CONSTRAINT):
- occupation MUST be EXACTLY one of the allowed occupations below (copy/paste exactly; no other values permitted):
{allowed_occ_block}
""".rstrip()
        
        # Get time context
        time_section = self._format_time_context()
        
        # Build name avoidance block
        _forbidden_names_block = ""
        if existing_names:
            _names_list = ", ".join(existing_names)
            _forbidden_names_block = f"""
**NAME PROHIBITION (HARD CONSTRAINT):**
The following names are already in use — do NOT use them or any close variant:
{_names_list}
"""

        import random as _random
        _name_seeds = _random.choice([
            "Use a name from Central/Eastern European origin (Czech, Slovak, Hungarian, Polish, Romanian).",
            "Use a name from Sub-Saharan African origin (Yoruba, Igbo, Zulu, Swahili, Amharic).",
            "Use a name from East Asian origin (Chinese, Japanese, Korean, Vietnamese).",
            "Use a name from South Asian origin (Hindi, Tamil, Bengali, Urdu, Marathi).",
            "Use a name from Middle Eastern / North African origin (Arabic, Persian, Turkish, Hebrew).",
            "Use a name from Scandinavian or Nordic origin (Swedish, Norwegian, Danish, Finnish, Icelandic).",
            "Use a name from Iberian or Latin American origin (Spanish, Portuguese, Catalan).",
            "Use a name from West African or Francophone African origin (Wolof, Mandé, Hausa, Fula).",
            "Use a name from Slavic origin (Russian, Ukrainian, Serbian, Bulgarian, Croatian).",
            "Use a name from South-East Asian origin (Thai, Indonesian, Filipino, Malay, Burmese).",
            "Use a name from Indigenous American origin (Navajo, Quechua, Nahuatl, Lakota, Maya).",
            "Use a name from Italian or Southern European origin (Italian, Greek, Albanian, Maltese).",
        ])
        _name_diversity_block = f"""
**NAME DIVERSITY (MANDATORY):**
{_name_seeds}
The name must feel authentically from that culture — not a made-up fantasy name.
Avoid generic English/Western European names unless the culture seed above calls for it.
The name should be memorable and distinct from every other name in this session.
"""

        prompt = f"""
You are creating a Non-User Actor (NUA) for an interactive simulation.

**Context:** {context if context else "A new character is needed for the current scene"}
**Scene:** {scene_description if scene_description else "General interaction"}
{time_section}
{world_context}
{mode_b_constraints}
{rag_constraints}
{endowments_constraints}
{_forbidden_names_block}
{_name_diversity_block}

**RELATIONSHIP DIVERSITY PHILOSOPHY:**
Not every NPC should be an opponent or source of conflict. Create characters that represent the full spectrum of human relationships and social dynamics:

**Relationship Types to Consider:**
- **Allies & Helpers:** Characters who share goals or can provide assistance
- **Neutral Parties:** Merchants, clerks, bystanders with their own agendas
- **Information Sources:** Witnesses, experts, locals with valuable knowledge
- **Social Connections:** Colleagues, acquaintances, community members
- **Service Providers:** Shopkeepers, mechanics, professionals offering services
- **Potential Friends:** Characters with compatible personalities or interests
- **Mentors & Guides:** Experienced individuals who could teach or advise
- **Rivals (Non-Hostile):** Competitors or those with conflicting but not antagonistic goals

**Only create opponents/antagonists when:**
- The narrative context specifically calls for conflict
- The scene is in Pressure or Outcome mode (high-stakes situations)
- The story has naturally evolved to require opposition

**For Roam and Spark modes, prioritize:**
- Helpful or neutral characters
- Social interaction opportunities
- Characters who can provide information or services
- Potential allies or friends

Generate a complete NUA profile as a JSON object with the following structure:

```json
{{
    "name": "Character Name (era-appropriate)",
    "age": 35,
    "location": "Current Scene",
    "occupation": "Character's role/job (era-appropriate)",
    "faction": "Faction/Clan from AVAILABLE FACTIONS above, or 'None' if unaffiliated",
    "personality_traits": {{
        "internal": "internal personality trait",
        "external": "external personality trait"
    }},
    "goals": ["Primary goal", "Secondary goal"],
    "s_factors": {{
        "swiftness": 1-4,
        "sociability": 1-4,
        "sturdiness": 1-4,
        "smarts": 1-4,
        "shadow": 1-4
    }},
    "skills": {{
        "Skill1": 1-4,
        "Skill2": 1-4,
        "Skill3": 1-4,
        "Skill4": 1-4,
        "Skill5": 1-4
    }},
    "endowments": {{"Endowment/Power Name": 1}},
    "inventory": [
        {{
            "name": "Item Name",
            "description": "Item description",
            "supplement_bonus": 1
        }}
    ]
}}
```

**CRITICAL - ERA ENFORCEMENT (MANDATORY):**
- You MUST create a character appropriate for the TIME PERIOD specified in the WORLD SETTING above
- ANACHRONISMS ARE FORBIDDEN - occupation, skills, inventory, and goals must fit the era
- The time period is defined exclusively by the worldbuilding context provided - do not assume or invent a period

**CRITICAL - RAG-ONLY GROUNDEDNESS (MANDATORY):**
- The WORLD CONTEXT above is the only source of truth.
- Do NOT invent factions, occupations, or locations that are not supported by the WORLD CONTEXT.
- If you cannot find support in the WORLD CONTEXT, choose a different option that IS supported.

**FACTION ASSIGNMENT:**
- Choose a faction from AVAILABLE FACTIONS/CLANS above if appropriate for this character
- Use "None" if the character is unaffiliated or if no factions are defined
- Faction should influence the character's goals, skills, and personality

**Requirements:**
- The NUA should be appropriate for the given context, scene, AND TIME PERIOD
- Age: Character's age (appropriate for their role and era)
- Location: Geographic location appropriate for the setting era
- Faction: Must be from AVAILABLE FACTIONS or "None"
- Faction (MODE A): MUST be EXACTLY copied from the EXPLICIT FACTION LIBRARY whitelist above, or use "None".
- Consider the relationship diversity philosophy above - avoid defaulting to opponents
- S-factors should total around 12 points at most and reflect the character's nature
- Must have exactly 5 skills relevant to their role AND appropriate for the era
- Must have at least one inventory item with supplement_bonus ≥ 1 (era-appropriate items only)
- Skills (MODE B): Skill names MUST be EXACTLY copied from the SKILLS VOCAB (if provided).
- Inventory (MODE B): Item names MUST be EXACTLY copied from the ITEMS VOCAB (if provided).
- If SKILLS/ITEMS VOCAB is provided, you MAY return `skill_ids` and `inventory_ids` instead of free-text names:
-   - `skill_ids`: list of objects like {{"id": 1, "level": 2}} where id is 1-based index into SKILLS VOCAB.
-   - `inventory_ids`: list of objects like {{"id": 1, "description": "...", "supplement_bonus": 1}} where id is 1-based index into ITEMS VOCAB.
-   - If you provide ids, do NOT invent any skill/item names.
- Goals should be specific and actionable, but not necessarily conflicting with the User Actor. Keep them grounded in GOAL PATTERNS above.
- Create characters who feel authentic and have their own motivations beyond opposing the player

Respond with ONLY the valid JSON object.
        """.strip()
        
        # Retry up to 3 times for empty/failed responses
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    timeout=300
                )
                
                response_content = response.choices[0].message.content
                if not response_content:
                    self.logger.log_system(f"WARNING: Empty LLM response on attempt {attempt + 1}/{max_retries}")
                    last_error = "Empty response from LLM"
                    continue
                    
                response_content = response_content.strip()
                self.logger.log_system(f"DEBUG: Raw NUA API response (attempt {attempt + 1}): {response_content[:200]}...")
                
                if "```json" in response_content:
                    json_start = response_content.find("```json") + 7
                    json_end = response_content.find("```", json_start)
                    json_text = response_content[json_start:json_end].strip()
                elif "{" in response_content and "}" in response_content:
                    json_start = response_content.find("{")
                    json_end = response_content.rfind("}") + 1
                    json_text = response_content[json_start:json_end].strip()
                else:
                    json_text = response_content.strip()
                
                if not json_text or len(json_text) < 10:
                    self.logger.log_system(f"WARNING: JSON text too short on attempt {attempt + 1}/{max_retries}: '{json_text}'")
                    last_error = f"JSON text too short: {json_text}"
                    continue
                
                # Fix JSON formatting issues (embedded quotes, etc.)
                json_text = _fix_json_formatting(json_text)
                
                nua_data = json.loads(json_text)

                # If Mode B vocab exists, allow ID-based selection to avoid invented/variant names.
                try:
                    allowed_skill_vocab, allowed_item_vocab = self._get_mode_b_vocab()
                except Exception:
                    allowed_skill_vocab, allowed_item_vocab = ([], [])

                # skill_ids: [{id:<1-based>, level:<1-4>}]
                skill_ids_raw = nua_data.get('skill_ids')
                if allowed_skill_vocab and isinstance(skill_ids_raw, list) and skill_ids_raw:
                    mapped_skills: dict[str, int] = {}
                    for ent in skill_ids_raw[:10]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        raw_lvl = ent.get('level', 1)
                        try:
                            idx = int(raw_id)
                            lvl = int(raw_lvl)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_skill_vocab):
                            continue
                        lvl = min(4, max(1, lvl))
                        name = allowed_skill_vocab[idx - 1]
                        mapped_skills[name] = lvl
                    if mapped_skills:
                        nua_data['skills'] = mapped_skills

                # inventory_ids: [{id:<1-based>, description:str, supplement_bonus:int}]
                inv_ids_raw = nua_data.get('inventory_ids')
                if allowed_item_vocab and isinstance(inv_ids_raw, list) and inv_ids_raw:
                    mapped_inv: list[dict] = []
                    for ent in inv_ids_raw[:8]:
                        if not isinstance(ent, dict):
                            continue
                        raw_id = ent.get('id')
                        try:
                            idx = int(raw_id)
                        except Exception:
                            continue
                        if idx < 1 or idx > len(allowed_item_vocab):
                            continue
                        name = allowed_item_vocab[idx - 1]
                        desc = str(ent.get('description', '') or '').strip()
                        bonus = ent.get('supplement_bonus', 1)
                        try:
                            bonus_i = int(bonus)
                        except Exception:
                            bonus_i = 1
                        bonus_i = max(1, bonus_i)
                        mapped_inv.append({"name": name, "description": desc, "supplement_bonus": bonus_i})
                    if mapped_inv:
                        nua_data['inventory'] = mapped_inv
                
                required_fields = ['name', 'occupation', 'goals', 's_factors', 'skills']
                for field in required_fields:
                    if field not in nua_data:
                        raise ValueError(f"Missing required field: {field}")

                # Enforce canonical location rule
                if not allow_remote_location:
                    nua_data['location'] = "Current Scene"

                goals_data = nua_data.get('goals') or []
                if isinstance(goals_data, dict):
                    goals_list = list(goals_data.values())
                else:
                    goals_list = goals_data

                # Goals are guidance-driven (no hard whitelist)

                self._validate_mode_a_faction_or_raise(
                    faction=nua_data.get('faction', 'None'),
                    allowed=allowed_factions,
                    label='NUA'
                )

                self._validate_mode_b_terms_or_raise(
                    skills=nua_data.get('skills', {}),
                    inventory=nua_data.get('inventory') or [],
                    label='NUA'
                )

                try:
                    def _coerce_to_allowed(value: str, allowed: list[str]) -> str:
                        if not allowed:
                            return value
                        v = (value or '').strip()
                        if not v:
                            return allowed[0]
                        for a in allowed:
                            if v == a:
                                return a
                        v_lower = v.lower()
                        for a in allowed:
                            if v_lower == a.lower():
                                return a
                        for a in allowed:
                            if a.lower() in v_lower:
                                return a
                        return allowed[0]

                    if allowed_occupations:
                        nua_data['occupation'] = _coerce_to_allowed(nua_data.get('occupation'), allowed_occupations)
                except Exception:
                    pass
                
                return nua_data
                
            except json.JSONDecodeError as e:
                last_error = f"JSON parse error: {e}"
                self.logger.log_system(f"WARNING: JSON parse failed on attempt {attempt + 1}/{max_retries}: {e}")
                continue
            except Exception as e:
                last_error = str(e)
                self.logger.log_system(f"WARNING: NUA generation failed on attempt {attempt + 1}/{max_retries}: {e}")
                continue
        
        # All retries exhausted
        error_msg = f"NUA profile generation failed after {max_retries} attempts: {last_error}"
        self.logger.log_system(f"ERROR: {error_msg}")
        raise ValueError(f"NUA profile generation failed: {error_msg}")

    def _generate_additional_skills(self, nua_data: dict, existing_skills: dict, count: int) -> dict:
        """Generate additional skills for an NUA to meet the minimum requirement."""
        prompt = f"""
Generate {count} additional skills for this NUA character to reach the minimum of 5 skills total.

**Character Context:**
- Name: {nua_data.get('name', 'Unknown')}
- Occupation: {nua_data.get('occupation', 'Unknown')}
- Existing Skills: {list(existing_skills.keys())}

**Requirements:**
- Generate exactly {count} new skills
- Skills must be different from existing ones
- Skills should be relevant to the character's role and context
- Each skill value should be 1-4
- Return as JSON object with skill names as keys and values as integers

Example format:
```json
{{
    "Skill Name 1": 2,
    "Skill Name 2": 3
}}
```

Respond with ONLY the valid JSON object.
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                timeout=300
            )
            
            response_content = response.choices[0].message.content.strip()
            self.logger.log_system(f"DEBUG: Raw additional skills API response: {response_content}")
            
            if "```json" in response_content:
                json_start = response_content.find("```json") + 7
                json_end = response_content.find("```", json_start)
                json_text = response_content[json_start:json_end].strip()
            elif "{" in response_content and "}" in response_content:
                json_start = response_content.find("{")
                json_end = response_content.rfind("}") + 1
                json_text = response_content[json_start:json_end].strip()
            else:
                json_text = response_content.strip()
            
            json_text = _fix_json_formatting(json_text)
            additional_skills = json.loads(json_text)
            
            if not isinstance(additional_skills, dict) or len(additional_skills) != count:
                fallback_skills = {
                    "Awareness": 2,
                    "Athletics": 2,
                    "Communication": 2,
                    "Survival": 2,
                    "Focus": 2
                }
                result = {}
                for skill, value in fallback_skills.items():
                    if skill not in existing_skills and len(result) < count:
                        result[skill] = value
                return result
            
            return additional_skills
            
        except Exception as e:
            self.logger.log_system(f"ERROR: Additional skills generation failed: {str(e)}")
            fallback_skills = ["Awareness", "Athletics", "Communication", "Survival", "Focus"]
            result = {}
            for i, skill in enumerate(fallback_skills):
                if skill not in existing_skills and len(result) < count:
                    result[skill] = 2
            return result

    def generate_inua(self, context: str = "", scene_description: str = "") -> InanimateNonUserActor:
        """Generates an Inanimate Non-User Actor (INUA) for the scene.
        
        INUAs are objects, environments, or abstract concepts that can be interacted with
        but don't take independent actions.
        """
        self.logger.log_system("Generating new INUA...")
        
        inua_data = self._generate_inua_profile(context, scene_description)
        
        s_factors_data = inua_data.get('s_factors', {})
        required_s_factors = {'swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow'}
        if not s_factors_data or not required_s_factors.issubset(s_factors_data.keys()):
            self.logger.log_system(f"S-Factors missing for INUA {inua_data.get('name')}. Generating...")
            s_factors_data = self._generate_inua_s_factors(inua_data)
        
        inua_skills = inua_data.get('skills', {})
        if len(inua_skills) < 5:
            error_msg = f"INUA {inua_data.get('name', 'Unknown')} has only {len(inua_skills)} skills, minimum 5 required. Skills: {inua_skills}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"INUA generation failed: {error_msg}")
        
        inventory_data = inua_data.get('inventory') or []
        inventory = []
        for item in inventory_data:
            if isinstance(item, dict):
                supplement_bonus = max(1, item.get('supplement_bonus', 1))
                new_item = Item(item['name'], item['description'], supplement_bonus)
                inventory.append(new_item)
            elif isinstance(item, str):
                new_item = Item(item, "", 1)
                inventory.append(new_item)
        
        goals_data = inua_data.get('goals') or []
        if isinstance(goals_data, dict):
            goals_list = list(goals_data.values())
        else:
            goals_list = goals_data
        
        swiftness = s_factors_data.get('swiftness', 1)
        sociability = s_factors_data.get('sociability', 0)
        sturdiness = s_factors_data.get('sturdiness', 3)
        smarts = s_factors_data.get('smarts', 1)
        shadow = s_factors_data.get('shadow', 2)
        
        if sociability + smarts > 5:
            self.logger.log_system(f"WARNING: Dynamic INUA S-factors constraint violation - Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts} > 5")
            sociability = min(sociability, 1)
            smarts = min(smarts, 5 - sociability)
            self.logger.log_system(f"FIXED: Adjusted dynamic INUA to Sociability ({sociability}) + Smarts ({smarts}) = {sociability + smarts}")

        inua_sheet = ActorSheet(
            name=inua_data['name'],
            s_factors=SFactors(
                swiftness=swiftness,
                sociability=sociability,
                sturdiness=sturdiness,
                smarts=smarts,
                shadow=shadow
            ),
            skills=inua_skills,
            personality_traits=inua_data.get('personality_traits', {'internal': 'inanimate', 'external': 'static'}),
            goals=goals_list,
            inventory=inventory,
            occupation=inua_data.get('occupation', 'Inanimate Object')
        )

        try:
            inua_sheet.canonical_name = inua_sheet.name
            occ = (getattr(inua_sheet, 'occupation', None) or '').strip()
            if not getattr(inua_sheet, 'known_as', None):
                inua_sheet.known_as = []
            if occ and occ.lower() not in ('unknown', 'none'):
                if occ not in inua_sheet.known_as:
                    inua_sheet.known_as.append(occ)
            if not getattr(inua_sheet, 'public_description', None):
                base = (occ or inua_sheet.name).strip()
                if base:
                    inua_sheet.public_description = base if base.lower().startswith(('the ', 'a ', 'an ')) else f"the {base.lower()}"

            # Deterministic fallback so stranger-safe naming never becomes empty
            if not inua_sheet.known_as:
                inua_sheet.known_as.append('object')
            if not getattr(inua_sheet, 'public_description', None):
                inua_sheet.public_description = "the object"
        except Exception:
            pass
        
        self.logger.log_system(f"Successfully generated INUA: {inua_data['name']} with {len(inua_skills)} skills")
        
        # Display spark creation indicator for INUA (only for the 3 spark types: MOMENTUM, EXCHANGE, CALLBACK)
        spark_type = getattr(self, '_current_spark_type', None)
        if spark_type and spark_type.upper() in ('MOMENTUM', 'EXCHANGE', 'CALLBACK'):
            # Color based on spark type
            if spark_type.upper() == 'MOMENTUM':
                color = '\033[92m'  # Green for momentum
                emoji = '🚀'
            elif spark_type.upper() == 'EXCHANGE':
                color = '\033[93m'  # Yellow for exchange
                emoji = '💬'
            else:  # CALLBACK
                color = '\033[95m'  # Magenta for callback
                emoji = '🔄'
            
            print(f"\n{color}{emoji} {spark_type.upper()} SPARK → INUA {emoji}\033[0m")
            print(f"{color}{'─' * 40}\033[0m")
            print(f"{color}  Name: {inua_data.get('name', 'Unknown')}\033[0m")
            print(f"{color}  Category: {inua_data.get('occupation', 'Object')}\033[0m")
            print(f"{color}{'─' * 40}\033[0m\n")
            # Clear after use
            self._current_spark_type = None
        
        return InanimateNonUserActor(inua_sheet)
    
    def _generate_inua_profile(self, context: str = "", scene_description: str = "") -> dict:
        """Generates a complete INUA profile including name, type, interaction skills, and components."""
        setting_context = self._get_setting_context()
        mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
        mechanics_context = self._get_rag_context(
            query="status stamina spirit supply skills endowments abilities",
            max_tokens=350,
            category_filter=mechanics_category
        )
        inua_category = WorldbuildingCategory.INUA_GENERATION if WorldbuildingCategory else None
        inua_generation_context = self._get_rag_context(
            query="inanimate non-user actor generation objects items documents equipment environmental supplement_bonus",
            max_tokens=650,
            category_filter=inua_category
        )
        places_category = WorldbuildingCategory.PLACES if WorldbuildingCategory else None
        places_context = self._get_rag_context(
            query=f"places location props environment {scene_description} {context}".strip(),
            max_tokens=450,
            category_filter=places_category
        )

        world_context = f"""
**WORLD SETTING:**
{setting_context}

**INUA GENERATION GUIDELINES:**
{inua_generation_context}

**PLACES / SCENE GROUNDS:**
{places_context}

**MECHANICS REFERENCE:**
{mechanics_context}
""".strip()

        prompt = f"""
You are creating an Inanimate Non-User Actor (INUA) for an interactive simulation.

{f"Context: {context}" if context else ""}
{f"Scene: {scene_description}" if scene_description else ""}

{world_context}

INUAs are objects, environments, or abstract concepts that can be interacted with but don't take independent actions.

**INUA Examples:**
- Physical Objects: Doors, locks, traps, vehicles, machines, tools, weapons
- Environmental Features: Cliffs, rivers, fires, storms, magical barriers
- Abstract Concepts: Reputation systems, time pressure, social dynamics
- Structures: Buildings, bridges, walls, fortifications

**Requirements:**
- Name: A descriptive name for the INUA
- Type: The category of inanimate object/concept
- Interaction Skills: MINIMUM 5 skills representing different ways to interact with it
- Components: 2-3 parts or aspects that can be targeted

**CRITICAL - Skills for INUAs:**
- Skills represent different interaction methods (e.g., "Lockpicking", "Climbing", "Repair")
- Values 1-3 represent difficulty of interaction (1=Easy, 2=Moderate, 3=Hard)
- Must have at least 5 different interaction skills

Respond with ONLY a valid JSON object:
{{
    "name": "INUA Name",
    "occupation": "Type of Object/Concept",
    "location": "Current Scene",
    "goals": ["Maintain function", "Resist damage"],
    "skills": {{"Interaction1": 2, "Interaction2": 3, "Interaction3": 1, "Interaction4": 2, "Interaction5": 1}},
    "inventory": [
        {{"name": "Component Name", "description": "Component description", "supplement_bonus": 1}}
    ],
    "personality_traits": {{
        "internal": "Core nature (e.g., 'sturdy', 'fragile', 'complex')",
        "external": "Observable quality (e.g., 'imposing', 'worn', 'mysterious')"
    }}
}}

**CRITICAL - RAG-ONLY GROUNDEDNESS (MANDATORY):**
- The WORLD CONTEXT above is the only source of truth.
- Do NOT invent technologies, materials, or object types that are not supported by the WORLD CONTEXT.
- Ensure the INUA fits the time period and setting.

**CRITICAL - LOCATION POLICY (MANDATORY):**
- Default: Set "location" to EXACTLY "Current Scene".
- Exception: ONLY if the Context/Scene explicitly implies a remote location (e.g., "letter from", "message from", "call from", "remote", or an explicit "in <place>") may you set a different location.
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.7
            )
            response_text = response.choices[0].message.content
            self.logger.log_system(f"DEBUG: Raw INUA API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            # Fix JSON formatting issues (embedded quotes, etc.)
            json_text = _fix_json_formatting(json_text)
            
            inua_data = json.loads(json_text)
            
            # Handle both 'occupation' and 'type' fields (LLM sometimes uses 'type')
            if 'type' in inua_data and 'occupation' not in inua_data:
                inua_data['occupation'] = inua_data['type']

            allow_remote_location = self._context_allows_remote_location(context=context, scene_description=scene_description)
            if not allow_remote_location:
                inua_data['location'] = "Current Scene"
            
            required_fields = ['name', 'occupation']
            if not all(field in inua_data for field in required_fields):
                error_msg = f"Generated INUA profile is missing required fields. Response: {inua_data}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"INUA profile generation failed: {error_msg}")
            
            skills = inua_data.get('skills', {})
            if len(skills) < 5:
                error_msg = f"INUA profile has only {len(skills)} skills, minimum 5 required. Skills: {skills}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"INUA profile generation failed: {error_msg}")
            
            self.logger.log_system(f"Generated INUA profile: {inua_data.get('name')} with {len(skills)} skills")
            return inua_data
            
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse INUA profile: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"INUA profile generation failed: {error_msg}")
    
    def _generate_inua_s_factors(self, inua_data: dict) -> dict:
        """Generates S-Factors for an INUA, typically with lower values reflecting inanimate nature."""
        prompt = f"""
You are generating S-Factors for an Inanimate Non-User Actor (INUA) in a simulation.

INUA Profile:
- Name: {inua_data.get('name', 'Unknown')}
- Type: {inua_data.get('occupation', 'Unknown')}
- Skills: {inua_data.get('skills', {})}

S-Factor Generation Rules for INUAs:
1. Distribute exactly 8 points among the five S-Factors (lower than living beings)
2. Each S-Factor must have a value between 0 and 4 (INUAs can have 0 in some areas)
3. Consider the inanimate nature - most INUAs have low Sociability and Swiftness
4. Sturdiness is often higher for physical objects
5. Smarts represents complexity/sophistication, not intelligence

S-Factor Meanings for INUAs:
- Swiftness: Speed of response/activation (usually 0-1 for most objects)
- Sociability: Ability to interface with social systems (usually 0 for pure objects)
- Sturdiness: Physical durability and resistance to damage
- Smarts: Complexity, sophistication, or built-in logic
- Shadow: Mystery, hidden aspects, or unpredictable behavior

Respond with ONLY a valid JSON object:
{{
    "swiftness": 0,
    "sociability": 0, 
    "sturdiness": 4,
    "smarts": 2,
    "shadow": 2
}}
        """.strip()
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{'role': 'user', 'content': prompt}],
                temperature=0.6
            )
            response_text = response.choices[0].message.content
            self.logger.log_system(f"DEBUG: Raw INUA S-Factors API response: {response_text}")
            
            if "```json" in response_text:
                json_start = response_text.find("```json") + 7
                json_end = response_text.find("```", json_start)
                json_text = response_text[json_start:json_end].strip()
            elif "{" in response_text and "}" in response_text:
                json_start = response_text.find("{")
                json_end = response_text.rfind("}") + 1
                json_text = response_text[json_start:json_end].strip()
            else:
                json_text = response_text.strip()
            
            json_text = _fix_json_formatting(json_text)
            s_factors_data = json.loads(json_text)
            
            required_factors = ['swiftness', 'sociability', 'sturdiness', 'smarts', 'shadow']
            if not all(factor in s_factors_data for factor in required_factors):
                error_msg = f"Generated INUA S-Factors missing required factors. Response: {s_factors_data}"
                self.logger.log_system(f"ERROR: {error_msg}")
                raise ValueError(f"INUA S-Factors generation failed: {error_msg}")
            
            total_points = sum(s_factors_data.values())
            if total_points < 6 or total_points > 10:
                self.logger.log_system(f"WARNING: INUA S-Factors total is {total_points}, expected around 8")
            
            self.logger.log_system(f"Generated INUA S-Factors for {inua_data.get('name')}: {s_factors_data}")
            return s_factors_data
            
        except (json.JSONDecodeError, TypeError, Exception) as e:
            error_msg = f"Could not generate or parse INUA S-Factors for {inua_data.get('name')}: {e}"
            self.logger.log_system(f"ERROR: {error_msg}")
            raise ValueError(f"INUA S-Factors generation failed: {error_msg}")

    def create_dynamic_actor(self, actor_info: dict, scene_description: str, actor_manager=None, spark_type: str = None):
        """
        Create a dynamic actor (NUA or INUA) based on actor_info and register it with the actor manager.
        
        Args:
            actor_info: Dictionary containing actor type, name, and context
            scene_description: Current scene context
            actor_manager: MultiActorManager instance to register the new actor
            spark_type: Which spark triggered this creation ("momentum", "exchange", "callback")
            
        Returns:
            Actor instance (NonUserActor or InanimateNonUserActor) or None if creation fails
        """
        try:
            actor_type = actor_info.get('type', 'NUA')
            actor_name = actor_info.get('name', 'Unknown')
            context = actor_info.get('context', '')
            
            # Store spark type for indicator
            self._current_spark_type = spark_type
            
            self.logger.log_system(f"Creating dynamic {actor_type}: {actor_name}")
            
            # Enhance context with scene information
            enhanced_context = f"Character: {actor_name}. Context: {context}. Current Scene: {scene_description}"
            
            if actor_type.upper() == 'INUA':
                # Use existing INUA generation - create temporary scene data structure
                inua_data = self._generate_inua_profile(enhanced_context, scene_description)
                
                # Override name if specified in actor_info
                if actor_name != 'Unknown':
                    inua_data['name'] = actor_name
                
                # Temporarily set current_scene to use existing get_current_inua logic
                original_scene = self.current_scene
                self.current_scene = {'inua': inua_data}
                inua_actor = self.get_current_inua()
                self.current_scene = original_scene
                
                # Register with actor manager if provided
                if actor_manager and inua_actor:
                    from multi_actor_manager import ActorRole
                    actor_id = actor_manager.add_actor(
                        inua_actor, 
                        role=ActorRole.SCENE_SECONDARY,
                        location_context=f"Dynamically created in scene: {scene_description[:100]}..."
                    )
                    self.logger.log_system(f"Registered INUA {inua_actor.sheet.name} with actor manager (ID: {actor_id})")
                
                return inua_actor
            else:
                # Use existing NUA generation
                nua_actor = self.generate_nua(enhanced_context, scene_description)
                
                # Override name if specified in actor_info
                if nua_actor and actor_name != 'Unknown':
                    nua_actor.sheet.name = actor_name
                    nua_actor.name = actor_name
                
                # Register with actor manager if provided
                if actor_manager and nua_actor:
                    from multi_actor_manager import ActorRole
                    actor_id = actor_manager.add_actor(
                        nua_actor, 
                        role=ActorRole.SCENE_SECONDARY,
                        location_context=f"Dynamically created in scene: {scene_description[:100]}..."
                    )
                    self.logger.log_system(f"Registered NUA {nua_actor.sheet.name} with actor manager (ID: {actor_id})")
                
                return nua_actor
                
        except Exception as e:
            self.logger.log_system(f"ERROR: Failed to create dynamic actor {actor_info.get('name', 'Unknown')}: {e}")
            return None

    def _get_allowed_endowments_from_rag(self, actor_type: str = '') -> list[str]:
        allowed: list[str] = []
        if not getattr(self, 'rag_system', None):
            return allowed

        endowments_context = ""
        try:
            at = (actor_type or '').strip().lower()
            # IMPORTANT: UA and MNUA endowments must NOT share the same pool.
            # UA endowments come from UA_GENERATION lore; MNUA endowments come from MNUA_GENERATION lore.
            # For other actor types, fall back to MECHANICS endowments reference.
            if at == 'ua':
                cat = WorldbuildingCategory.UA_GENERATION if WorldbuildingCategory else None
                endowments_context = self._get_rag_context(
                    query="endowment abilities endowments UA ENDOWMENT ABILITIES",
                    max_tokens=600,
                    category_filter=cat
                )
            elif at == 'mnua':
                cat = WorldbuildingCategory.MNUA_GENERATION if WorldbuildingCategory else None
                endowments_context = self._get_rag_context(
                    query="endowment abilities disciplines MNUA ENDOWMENT ABILITIES",
                    max_tokens=700,
                    category_filter=cat
                )
            else:
                mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
                endowments_context = self._get_rag_context(
                    query="endowments powers abilities",
                    max_tokens=500,
                    category_filter=mechanics_category
                )
        except Exception:
            endowments_context = ""

        try:
            import re
            in_endowments_section = False
            found_any = False
            # Only extract endowments from explicit sections. This prevents incidental matches
            # like "Hellfire" inside unrelated bullet lists (e.g., faction flavor text).
            section_re = re.compile(r"\b(ENDOWMENT\s*ABILITIES|ENDOWMENTS|ACTOR_ENDOWMENTS_REFERENCE)\b", re.IGNORECASE)
            header_re = re.compile(r"^(#{1,6}\s+|\*\*[^*]+\*\*\s*:?)")

            for line in endowments_context.splitlines():
                raw = line.rstrip("\n")
                line_s = raw.strip()

                if section_re.search(line_s):
                    in_endowments_section = True
                    continue

                if in_endowments_section and header_re.match(line_s) and not section_re.search(line_s):
                    if found_any:
                        break
                    continue

                if not in_endowments_section:
                    continue

                if not line_s.startswith(('-', '•', '*')):
                    continue

                line_s = line_s.lstrip('-•*').strip()
                if not line_s:
                    continue

                # Preferred formats in lore:
                # - "Type: Name (desc), Name (desc)"
                # - "Name: description"
                # - "Name - description"
                rhs = line_s
                if ':' in line_s:
                    rhs = line_s.split(':', 1)[1].strip()
                elif ' - ' in line_s:
                    rhs = line_s.split(' - ', 1)[0].strip()

                # Split into candidates.
                rhs = rhs.replace(' or ', ', ')
                parts = [p.strip() for p in re.split(r'[;,]', rhs) if p.strip()]
                for part in parts:
                    # Handle nested labels like "Dread Powers: Agonize (Pain)"
                    if ':' in part:
                        part = part.split(':', 1)[1].strip()
                    name = re.sub(r'\([^)]*\)', '', part).strip()
                    if not name:
                        continue
                    if name.lower().startswith('the '):
                        name = name[4:].strip()
                    if name and name not in allowed:
                        allowed.append(name)
                        found_any = True
        except Exception:
            pass

        if not allowed:
            # Retry with larger context if nothing found
            try:
                at = (actor_type or '').strip().lower()
                if at == 'ua':
                    cat = WorldbuildingCategory.UA_GENERATION if WorldbuildingCategory else None
                    retry_context = self._get_rag_context(
                        query="ENDOWMENT ABILITIES (explicit list)",
                        max_tokens=1400,
                        category_filter=cat
                    )
                elif at == 'mnua':
                    cat = WorldbuildingCategory.MNUA_GENERATION if WorldbuildingCategory else None
                    retry_context = self._get_rag_context(
                        query="ENDOWMENT ABILITIES (explicit list)",
                        max_tokens=1600,
                        category_filter=cat
                    )
                else:
                    mechanics_category = WorldbuildingCategory.MECHANICS if WorldbuildingCategory else None
                    retry_context = self._get_rag_context(
                        query="ACTOR_ENDOWMENTS_REFERENCE ENDOWMENT ABILITIES (explicit list)",
                        max_tokens=1400,
                        category_filter=mechanics_category
                    )
                
                if retry_context:
                    in_endowments_section = False
                    found_any = False
                    for line in retry_context.splitlines():
                        raw = line.rstrip("\n")
                        line_s = raw.strip()

                        if section_re.search(line_s):
                            in_endowments_section = True
                            continue

                        if in_endowments_section and header_re.match(line_s) and not section_re.search(line_s):
                            if found_any:
                                break
                            continue

                        if not in_endowments_section:
                            continue

                        if not line_s.startswith(('-', '•', '*')):
                            continue

                        line_s = line_s.lstrip('-•*').strip()
                        if not line_s:
                            continue

                        name = ""
                        if "**" in line_s:
                            parts = line_s.split("**")
                            if len(parts) >= 3:
                                name = parts[1].strip()
                        if not name and ":" in line_s:
                            name = line_s.split(":")[0].strip()
                        if not name:
                            name = line_s.split()[0].strip()
                        
                        if name.lower().startswith('the '):
                            name = name[4:].strip()
                        if name and name not in allowed:
                            allowed.append(name)
                            found_any = True
            except Exception:
                pass

        return allowed

    def _coerce_endowments_to_allowed(self, endowments: dict, allowed: list[str]) -> dict[str, int]:
        endowments_norm: dict[str, int] = {}
        if isinstance(endowments, dict):
            for k, v in list(endowments.items())[:3]:
                name = str(k or '').strip()
                if not name:
                    continue
                try:
                    lvl = int(v)
                except Exception:
                    lvl = 1
                lvl = min(5, max(1, lvl))
                
                # Check for exact match in allowed list
                if not allowed:
                    endowments_norm[name] = lvl
                else:
                    found = False
                    name_l = name.lower()
                    for a in allowed:
                        if a.lower() == name_l:
                            endowments_norm[a] = lvl
                            found = True
                            break
                    if not found:
                        # Use first allowed as fallback if user included an invalid one
                        endowments_norm[allowed[0]] = lvl
        return endowments_norm

        if not filtered and allowed:
            # Strict RAG lock: if the model produced an unrecognized variant but we have
            # a whitelist, force a deterministic allowed endowment instead of returning None.
            filtered = {allowed[0]: 1}

        if len(filtered) > 1:
            first = next(iter(filtered.items()))
            filtered = {first[0]: first[1]}

        return filtered

    def generate_initial_memories(self, actor) -> list:
        """
        Generate exactly 3 character-defining background memories for a newly created character.
        Works for both UserActor and NonUserActor.
        
        Args:
            actor: The actor (UserActor or NonUserActor) to generate memories for
            
        Returns:
            List of created memory dictionaries
        """
        actor_sheet = actor.sheet if hasattr(actor, 'sheet') else actor
        self.logger.log_system(f"Generating 3 key memories for {actor_sheet.name}...")
        
        # Extract S-factors for capability context
        from actor_sheet import SFactorType
        s_factors = actor_sheet.s_factors
        s_factor_notes = []
        for sf_type in SFactorType:
            value = s_factors.get_factor(sf_type)
            if value <= 1:
                s_factor_notes.append(f"{sf_type.name.capitalize()}: MINIMAL (1) - severely limited in this area")
            elif value >= 4:
                s_factor_notes.append(f"{sf_type.name.capitalize()}: EXCEPTIONAL ({value}) - highly capable")
        s_factors_context = "\n".join(s_factor_notes) if s_factor_notes else "Average capabilities across all attributes"
        
        # Build character context
        character_context = f"""
**CHARACTER PROFILE:**
- Name: {actor_sheet.name}
- Age: {actor_sheet.age}
- Occupation: {actor_sheet.occupation}
- Location: {actor_sheet.location}
- Goals: {', '.join(actor_sheet.goals) if actor_sheet.goals else 'None'}
- Personality: {actor_sheet.personality_traits.get('internal', 'Unknown')} (internal), {actor_sheet.personality_traits.get('external', 'Unknown')} (external)
- Key Skills: {', '.join([f"{k} ({v})" for k, v in list(actor_sheet.skills.items())[:3]])}

**NOTABLE ATTRIBUTES (memories MUST be consistent with these):**
{s_factors_context}
"""
        
        # Get world context from RAG
        world_context = self._get_setting_context() if self.rag_system else "Contemporary urban setting"
        
        prompt = f"""Generate EXACTLY 3 character-defining background memories for this character.

{world_context}

{character_context}

**MEMORY TYPES (choose 3 different types):**
- **Childhood/Trauma**: A formative experience from their past
- **Relationship**: An important person in their life (family, friend, mentor, rival)
- **Skill/Habit**: How they learned a key skill or developed a defining habit
- **Location/Connection**: A significant place they know well
- **Loss/Achievement**: Something that changed them

**REQUIREMENTS:**
- Generate EXACTLY 3 memories - no more, no less
- Each memory should be 1-2 sentences (concise and impactful)
- Specific and concrete (names, places, details)
- Character-defining - these shaped who they are
- Mix of different types

**CRITICAL - ATTRIBUTE CONSISTENCY:**
- If Smarts is MINIMAL (1): NO memories of academic achievement, intellectual prowess, or complex problem-solving
- If Sociability is MINIMAL (1): NO memories of being popular, charismatic, or socially successful
- If Swiftness is MINIMAL (1): NO memories of athletic achievement or physical prowess
- If Sturdiness is MINIMAL (1): NO memories of endurance feats or physical resilience
- If Shadow is MINIMAL (1): NO memories of successful deception, stealth, or manipulation
- Conversely, EXCEPTIONAL attributes (4-5) can have impressive achievements in those areas
- Age matters: A 70-year-old has different formative experiences than a 22-year-old

**FORMAT:**
Respond with ONLY a valid JSON array of exactly 3 memories:
[
    {{
        "title": "Brief memory title",
        "content": "1-2 sentence character-defining memory",
        "category": "childhood/relationship/skill/location/recent",
        "importance": "notable"
    }}
]

Generate EXACTLY 3 memories."""

        # Retry logic with exponential backoff
        max_retries = 3
        base_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                if attempt > 0:
                    import time
                    delay = base_delay * (2 ** (attempt - 1))  # 2s, 4s, 8s
                    self.logger.log_system(f"Retry attempt {attempt + 1}/{max_retries} after {delay}s delay...")
                    time.sleep(delay)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a character background generator. Your response MUST be ONLY a valid JSON array in the message content field. DO NOT include reasoning or explanations. Output ONLY the JSON array with exactly 3 memory objects. Create specific, concrete memories with names, places, and details."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    temperature=0.7,
                    max_tokens=1000,
                    timeout=45  # Increased timeout
                )
                
                if response and response.choices and response.choices[0].message.content:
                    break  # Success, exit retry loop
                elif attempt < max_retries - 1:
                    self.logger.log_system(f"Empty response on attempt {attempt + 1}, retrying...")
                    continue
                else:
                    self.logger.log_system("ERROR: No response from LLM for memory generation after all retries")
                    return []
                    
            except Exception as api_error:
                error_str = str(api_error).lower()
                # Check if it's a retryable error
                is_retryable = any(x in error_str for x in ['timeout', 'rate', 'limit', '429', '503', '502', 'connection', 'network'])
                
                if is_retryable and attempt < max_retries - 1:
                    self.logger.log_system(f"Retryable error on attempt {attempt + 1}: {api_error}")
                    continue
                else:
                    self.logger.log_system(f"ERROR: API call failed: {api_error}")
                    if attempt == max_retries - 1:
                        return []
                    raise
        
        try:
            if response and response.choices and response.choices[0].message.content:
                content = response.choices[0].message.content.strip()
                self.logger.log_system(f"DEBUG: Raw memory generation response length: {len(content)} chars")
                
                # Try to extract JSON
                if "```json" in content:
                    content = content.split("```json")[1].split("```")[0].strip()
                elif "```" in content:
                    content = content.split("```")[1].split("```")[0].strip()
                
                # Fix common JSON issues
                content = _fix_json_formatting(content)
                
                memories_data = json.loads(content)
                
                if not isinstance(memories_data, list):
                    self.logger.log_system(f"ERROR: Memories data is not a list, got: {type(memories_data)}")
                    return []
                
                if len(memories_data) != 3:
                    self.logger.log_system(f"WARNING: Expected 3 memories, got {len(memories_data)}")
                
                # Save memories to the key memories system
                created_memories = []
                if not self.key_memories_system:
                    self.logger.log_system("ERROR: KeyMemoriesSystem not available - memories cannot be saved!")
                    return []
                
                if self.key_memories_system:
                    from key_memories_system import MemoryImportance, MemoryCategory
                    
                    # Map string categories to enum
                    category_map = {
                        'childhood': MemoryCategory.DISCOVERY,
                        'relationship': MemoryCategory.RELATIONSHIP,
                        'skill': MemoryCategory.ACHIEVEMENT,
                        'location': MemoryCategory.LOCATION,
                        'recent': MemoryCategory.DISCOVERY
                    }
                    
                    importance_map = {
                        'notable': MemoryImportance.NOTABLE,
                        'routine': MemoryImportance.ROUTINE,
                        'important': MemoryImportance.IMPORTANT,
                        'critical': MemoryImportance.CRITICAL
                    }
                    
                    for mem_data in memories_data:
                        try:
                            category = category_map.get(mem_data.get('category', 'discovery').lower(), MemoryCategory.DISCOVERY)
                            importance = importance_map.get(mem_data.get('importance', 'routine').lower(), MemoryImportance.ROUTINE)
                            
                            memory_content = mem_data.get('content', '')
                            memory_id = self.key_memories_system.create_memory(
                                title=mem_data.get('title', 'Background Memory'),
                                description=memory_content,
                                full_narrative=memory_content,  # Use same content for both
                                category=category,
                                importance=importance,
                                location=actor_sheet.location,
                                actors_involved=[actor_sheet.name],
                                tags=["character_background", "defining_memory", actor_sheet.name.lower().replace(" ", "_")],
                                scene_id="character_creation"
                            )
                            
                            if memory_id:
                                created_memories.append({
                                    'id': memory_id,
                                    'title': mem_data.get('title'),
                                    'content': mem_data.get('content')
                                })
                                self.logger.log_system(f"✓ Created initial memory: {mem_data.get('title')} (ID: {memory_id})")
                            else:
                                self.logger.log_system(f"ERROR: Failed to create memory - create_memory returned None")
                        
                        except Exception as e:
                            self.logger.log_system(f"Failed to create memory: {e}")
                            continue
                    
                    self.logger.log_system(f"✓ Successfully created {len(created_memories)}/3 initial memories for {actor_sheet.name}")
                else:
                    self.logger.log_system("ERROR: KeyMemoriesSystem check failed - this shouldn't happen")
                
                return created_memories
            else:
                self.logger.log_system("ERROR: No response from LLM for memory generation")
                return []
                
        except json.JSONDecodeError as e:
            self.logger.log_system(f"ERROR: Failed to parse memory JSON: {e}")
            self.logger.log_system(f"Raw content: {content[:200]}...")
            return []
        except Exception as e:
            self.logger.log_system(f"ERROR: Failed to generate initial memories: {e}")
            import traceback
            self.logger.log_system(f"Traceback: {traceback.format_exc()}")
            return []

