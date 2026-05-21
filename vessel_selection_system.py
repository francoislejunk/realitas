"""
Vessel Selection System for Realitas Neo

Provides three UA character options at simulation start, allowing users to choose
which character they want to play. Characters are generated based on the RAG
worldbuilding system's time period and setting.
"""

import logging
from typing import List, Optional, Dict, Any
from pathlib import Path
import random
from color_utils import Color
from actors import UserActor
from actor_sheet import ActorSheet, SFactors, SFactorType, Item, StatusType

from worldbuilding_helpers import load_generated_cities, register_generated_city

# Import internal voice creator for initial memory generation
try:
    from agents.internal_voice_creator_agent import InternalVoiceCreatorAgent
    INTERNAL_VOICE_AVAILABLE = True
except ImportError:
    INTERNAL_VOICE_AVAILABLE = False


class VesselSelectionSystem:
    """Manages UA character selection at simulation start"""
    
    def __init__(self, creator_agent, storage_directory: Path, rag_system=None):
        self.creator_agent = creator_agent
        self.storage_directory = Path(storage_directory)
        self.logger = logging.getLogger(__name__)
        self.rag_system = rag_system  # RAG system for occupation queries
        
        # Store generated character options
        self.generated_options: List[Dict[str, Any]] = []

    def _get_allowed_city_names(self) -> List[str]:
        if not self.rag_system:
            return []

        try:
            from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
            cities_docs = []
            if hasattr(self.rag_system, 'get_by_category'):
                cities_docs = self.rag_system.get_by_category(WorldbuildingCategory.CITIES)

            city_names: List[str] = []
            if cities_docs:
                import re
                for doc in cities_docs:
                    content = getattr(doc, 'content', '') or ''
                    for match in re.finditer(r'^\*\*([^*\n]{2,60})\*\*\s*$', content, flags=re.MULTILINE):
                        name = match.group(1).strip()
                        if name and name not in city_names:
                            city_names.append(name)

            return city_names
        except Exception:
            return []

    def _meets_archetype(self, actor: UserActor, archetype_label: str) -> bool:
        try:
            sf = actor.sheet.s_factors
            skills = dict(getattr(actor.sheet, 'skills', {}) or {})
        except Exception:
            return False

        def _skill_level(name: str) -> int:
            try:
                return int(skills.get(name, 0) or 0)
            except Exception:
                return 0

        def _sf_int(t: SFactorType) -> int:
            try:
                v = sf.get_factor(t)
                return int(v)
            except Exception:
                return -999

        shadow = _sf_int(SFactorType.SHADOW)
        swift = _sf_int(SFactorType.SWIFTNESS)
        soc = _sf_int(SFactorType.SOCIABILITY)
        sturdy = _sf_int(SFactorType.STURDINESS)
        smarts = _sf_int(SFactorType.SMARTS)

        if min(shadow, swift, soc, sturdy, smarts) < -100:
            return False

        label = (archetype_label or '').strip().lower()
        if 'stealth' in label:
            if shadow < 4 or swift < 3 or soc > 2:
                return False
            if max(_skill_level('Stealth'), _skill_level('Perception'), _skill_level('Investigation')) < 2:
                return False
            return True

        if 'social' in label:
            if soc < 4 or shadow > 2:
                return False
            if max(_skill_level('Barter'), _skill_level('Perception')) < 2:
                return False
            return True

        # Tough / problem-solver
        if sturdy < 4 and smarts < 4:
            return False
        if max(_skill_level('Endurance'), _skill_level('Crafting'), _skill_level('Investigation')) < 2:
            return False
        return True

    def _get_allowed_occupations(self) -> List[str]:
        if not self.rag_system:
            return []

        try:
            from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory
            docs = []
            if hasattr(self.rag_system, 'get_by_category'):
                docs = self.rag_system.get_by_category(WorldbuildingCategory.UA_OCCUPATIONS)

            out: List[str] = []
            if docs:
                for doc in docs:
                    content = getattr(doc, 'content', '') or ''
                    for occ in self._extract_allowed_occupations_from_text(content):
                        if occ and occ not in out:
                            out.append(occ)
            return out
        except Exception:
            return []

    def _extract_allowed_occupations_from_text(self, text: str) -> List[str]:
        if not text:
            return []
        try:
            import re

            # STRICT: only accept actual occupation bullets from UA_OCCUPATIONS.
            # Format in lore/RAG is: "- The <Occupation Name>: ..."
            # This prevents category headers like "The Martial Vigil" and prose from Analogical Summary.
            out: List[str] = []
            pattern = re.compile(r'^\s*[-•*]\s*The\s+(.+?)\s*:\s*', re.IGNORECASE)
            for raw in str(text).splitlines():
                m = pattern.match(raw)
                if not m:
                    continue
                candidate = m.group(1).strip()
                candidate = re.sub(r'\([^)]*\)', '', candidate).strip()
                candidate = candidate.rstrip(' .;')
                if candidate and not any(ch.isdigit() for ch in candidate):
                    if candidate not in out:
                        out.append(candidate)
            return out
        except Exception:
            return []

    def _coerce_to_allowed_occupation(self, value: str, allowed: List[str], used_lower: set) -> str:
        if not allowed:
            return (value or "").strip()

        raw = (value or "").strip()
        if not raw:
            for a in allowed:
                if a and a.strip() and a.strip().lower() not in used_lower:
                    return a.strip()
            return allowed[0].strip()

        import re

        raw = raw.splitlines()[0].strip()
        raw = re.sub(r'^\s*occupation\s*:\s*', '', raw, flags=re.IGNORECASE).strip()

        # Only collapse to the quoted inner string when the whole value is essentially quoted.
        # If the allowed occupation itself contains quotes plus extra words (e.g. '"Netzo" Journalist Hunter'),
        # we must preserve the full string for matching.
        m = re.match(r'^\s*"([^"]{2,120})"\s*$', raw)
        if m:
            raw = m.group(1).strip()
        else:
            m = re.match(r"^\s*'([^']{2,120})'\s*$", raw)
            if m:
                raw = m.group(1).strip()

        lowered = raw.lower()
        for a in allowed:
            if a and a.strip().lower() == lowered:
                return a.strip()

        tokens = {t for t in re.split(r'[^a-z0-9]+', lowered) if t}
        best = None
        best_score = -1
        for a in allowed:
            a_s = (a or "").strip()
            if not a_s:
                continue
            a_tokens = {t for t in re.split(r'[^a-z0-9]+', a_s.lower()) if t}
            score = len(tokens & a_tokens)
            if score > best_score:
                best_score = score
                best = a_s

        if best and best_score > 0 and best.lower() not in used_lower:
            return best

        for a in allowed:
            a_s = (a or "").strip()
            if a_s and a_s.lower() not in used_lower:
                return a_s
        return (best or allowed[0]).strip()
    
    def generate_vessel_options(self, num_options: int = 3) -> List[Dict[str, Any]]:
        """
        Generate three different UA character options using the creator agent
        Ensures each character has a DIFFERENT occupation for varied experiences
        
        Returns list of character data dictionaries
        """
        vessel_options = []
        used_occupations = set()  # Track occupations to ensure diversity
        used_locations = set()  # Track locations to ensure geographic diversity
        used_factions = set()  # Track factions to ensure diversity
        max_retries_per_option = 5  # More retries to find unique occupations

        year_range = None
        if self.rag_system:
            try:
                from worldbuilding_helpers import extract_year_range_from_rag
                year_range = extract_year_range_from_rag(self.rag_system)
            except Exception:
                year_range = None
        
        # Query RAG for different occupation types to ensure variety
        # Each character gets context from a different query
        occupation_queries = [
            "blue collar skilled trades occupations manual labor",
            "service industry occupations hospitality retail",
            "white collar office occupations professional",
            "creative artistic occupations entertainment",
            "night shift late hours occupations",
            "street level hustler occupations underground"
        ]
        
        # Location grounding (LORE-AGNOSTIC)
        # IMPORTANT: Do not seed the LLM with hardcoded city examples here.
        # We want vessel locations to be chosen strictly from the major cities
        # present in the provided WORLD CONTEXT (RAG/lore).
        location_hints = [
            "Pick a major city explicitly mentioned in the WORLD CONTEXT above.",
            "Pick a DIFFERENT major city explicitly mentioned in the WORLD CONTEXT above.",
            "Pick another DIFFERENT major city explicitly mentioned in the WORLD CONTEXT above."
        ]

        allowed_city_names = self._get_allowed_city_names()
        # Include previously generated cities (canon for this run)
        try:
            for c in load_generated_cities():
                if c and c not in allowed_city_names:
                    allowed_city_names.append(c)
        except Exception:
            pass
        allowed_occupations = self._get_allowed_occupations()
        allowed_city_keywords = [c.lower() for c in allowed_city_names]

        # Faction diversity: use CreatorAgent's explicit faction whitelist when available.
        allowed_factions: List[str] = []
        try:
            if hasattr(self.creator_agent, '_get_explicit_faction_whitelist'):
                allowed_factions = list(self.creator_agent._get_explicit_faction_whitelist('ua') or [])
        except Exception:
            allowed_factions = []
        # Normalize and precompute a non-None list.
        allowed_factions = [f for f in allowed_factions if isinstance(f, str) and f.strip()]
        allowed_non_none_factions = [f for f in allowed_factions if f.strip().lower() != 'none']

        # Preselect faction targets for each vessel option to avoid deterministic "first three" repeats.
        # Use system randomness so runs differ even when other elements are seeded.
        desired_factions: List[Optional[str]] = [None for _ in range(num_options)]
        try:
            if allowed_non_none_factions:
                srng = random.SystemRandom()
                if len(allowed_non_none_factions) >= num_options:
                    picks = list(srng.sample(allowed_non_none_factions, k=num_options))
                else:
                    picks = list(allowed_non_none_factions)
                    srng.shuffle(picks)
                    # If fewer factions than options, allow repeats but randomize order.
                    while len(picks) < num_options:
                        picks.append(srng.choice(allowed_non_none_factions))
                desired_factions = [picks[i] if i < len(picks) else None for i in range(num_options)]
        except Exception:
            desired_factions = [None for _ in range(num_options)]

        archetype_specs = [
            {
                "label": "Stealth-focused runner",
                "requirements": "- Build should feel stealthy/low-profile.\n- Target S-Factors: Shadow >= 4, Swiftness >= 3.\n- Sociability should be <= 2.\n- Key skills should emphasize Stealth/Perception/Investigation.",
            },
            {
                "label": "Social connector",
                "requirements": "- Build should feel people-oriented.\n- Target S-Factors: Sociability >= 4.\n- Shadow should be <= 2.\n- Key skills should emphasize Barter/Persuasion/Perception or other social-adjacent skills.",
            },
            {
                "label": "Tough problem-solver",
                "requirements": "- Build should feel resilient and practical.\n- Target S-Factors: Sturdiness >= 4 OR Smarts >= 4 (pick one and lean into it).\n- Key skills should emphasize Endurance/Crafting/Investigation or similar.",
            },
        ]
        
        for i in range(num_options):
            self.logger.info(f"Generating character option {i+1}/{num_options}")

            forced_year = None
            if year_range:
                start_year, end_year = year_range
                seed = (hash(("forced_year", i, start_year, end_year)) & 0xFFFFFFFF)
                rng = random.Random(seed)
                forced_year = rng.randint(start_year, end_year)
            
            # Get specific occupation context for this character
            occupation_query = occupation_queries[i % len(occupation_queries)]
            
            if self.rag_system:
                try:
                    from WORLD_BUILDER.worldbuilding_rag import WorldbuildingCategory

                    temporal_context = ""
                    if hasattr(self.rag_system, 'get_context_for_llm'):
                        temporal_context = self.rag_system.get_context_for_llm(
                            query="time period setting year era current date timeline",
                            max_tokens=350,
                            category_filter=WorldbuildingCategory.TEMPORAL
                        )

                    occupation_context = ""
                    if hasattr(self.rag_system, 'get_context_for_llm'):
                        occupation_context = self.rag_system.get_context_for_llm(
                            query=occupation_query,
                            max_tokens=500,
                            category_filter=WorldbuildingCategory.UA_OCCUPATIONS
                        )

                    # Per-option whitelist: always attempt extraction from the local RAG snippet.
                    local_allowed_occupations: List[str] = list(allowed_occupations or [])
                    if occupation_context:
                        try:
                            extracted = self._extract_allowed_occupations_from_text(occupation_context)
                            for o in extracted:
                                if o and o not in local_allowed_occupations:
                                    local_allowed_occupations.append(o)
                        except Exception:
                            pass

                    # If global whitelist extraction failed but local succeeded, keep it for subsequent options too.
                    if not allowed_occupations and local_allowed_occupations:
                        allowed_occupations = list(local_allowed_occupations)

                    ua_generation_context = ""
                    if hasattr(self.rag_system, 'get_context_for_llm'):
                        ua_generation_context = self.rag_system.get_context_for_llm(
                            query="user actor generation player character protagonist names ages skills goals inventory personality",
                            max_tokens=450,
                            category_filter=WorldbuildingCategory.UA_GENERATION
                        )

                    cities_context = ""
                    if hasattr(self.rag_system, 'get_context_for_llm'):
                        cities_context = self.rag_system.get_context_for_llm(
                            query="major cities settlements",
                            max_tokens=700,
                            category_filter=WorldbuildingCategory.CITIES
                        )

                    character_context = "\n\n".join([
                        temporal_context,
                        cities_context,
                        occupation_context,
                        ua_generation_context,
                    ]).strip()
                    self.logger.info(f"Retrieved {len(character_context)} chars for character {i+1} from RAG")
                    
                    # Build context hint from RAG data with location diversity
                    location_hint = location_hints[i % len(location_hints)]
                    used_locations_str = ", ".join(used_locations) if used_locations else "None yet"
                    
                    city_block = ""
                    if allowed_city_names:
                        # Show a limited whitelist to reduce token usage but keep the model anchored.
                        city_lines = "\n".join([f"- {c}" for c in allowed_city_names[:40]])
                        city_block = f"""

**CITY WHITELIST (HARD - copy/paste exactly one):**
{city_lines}
""".rstrip()

                    occ_block = ""
                    if allowed_occupations:
                        remaining = [o for o in allowed_occupations if o.lower() not in used_occupations]
                        seed = (hash((i, occupation_query, tuple(sorted(used_occupations)))) & 0xFFFFFFFF)
                        rng = random.Random(seed)
                        rng.shuffle(remaining)
                        shortlist = remaining[:25] if remaining else allowed_occupations[:25]
                        occ_lines = "\n".join([f"- {o}" for o in shortlist])
                        occ_block = f"""

**OCCUPATION WHITELIST (HARD - copy/paste exactly one):**
{occ_lines}
""".rstrip()

                    archetype = archetype_specs[i % len(archetype_specs)]

                    # Faction requirement: prefer a real faction and vary across vessels.
                    faction_req = None
                    try:
                        faction_req = desired_factions[i] if (i < len(desired_factions)) else None
                    except Exception:
                        faction_req = None

                    faction_block = ""
                    if allowed_factions:
                        # Keep short to reduce token usage.
                        fac_lines = "\n".join([f"- {f}" for f in allowed_factions[:40]])
                        faction_block = f"""

**FACTION OPTIONS (RAG-GROUNDED - choose exactly one, copy/paste):**
{fac_lines}
""".rstrip()

                    faction_rule = ""
                    if faction_req:
                        faction_rule = f"""

**FACTION REQUIREMENT (HARD):**
- This vessel MUST have faction exactly: {faction_req}
""".rstrip()
                    elif allowed_non_none_factions:
                        faction_rule = """

**FACTION REQUIREMENT (STRONG PREFERENCE):**
- Prefer choosing a real faction (NOT 'None') unless the character concept absolutely requires being factionless.
""".rstrip()

                    context_hint = f"""Create a character with a realistic occupation based on the world context below.

**WORLD CONTEXT FROM LORE:**
{character_context}
{city_block}
{occ_block}
{faction_block}
{faction_rule}

**LOCATION REQUIREMENT:**
- {location_hint}
- Already used locations: {used_locations_str}
- Choose a DIFFERENT city/location from those already used
- Do NOT invent modern or out-of-setting cities; only use locations explicitly supported by the WORLD CONTEXT

**ARCHETYPE REQUIREMENT (make this vessel feel meaningfully distinct):**
- Archetype: {archetype['label']}
{archetype['requirements']}

**REQUIREMENTS:**
- Choose a SPECIFIC occupation from the context above
- Make it grounded in the world's time period and setting
- Focus on the occupation types described in the context
- Ensure the occupation fits the world's economic and social structure
- If an OCCUPATION WHITELIST is provided above, the occupation MUST be EXACTLY one of those lines (copy/paste).
- If a CITY WHITELIST is provided above, the location MUST be EXACTLY one of those lines (copy/paste).
- Location must follow the LOCATION REQUIREMENT above
""".rstrip()

                    if forced_year is not None:
                        context_hint += f"""

**SIMULATION YEAR (HARD REQUIREMENT):**
- simulation_year MUST be exactly {forced_year}
""".rstrip()
                    
                except Exception as e:
                    self.logger.warning(f"RAG query failed for character {i+1}: {e}. Using fallback.")
                    location_hint = location_hints[i % len(location_hints)]
                    used_locations_str = ", ".join(used_locations) if used_locations else "None yet"
                    context_hint = f"""Create a character with a realistic occupation. Character {i+1} of {num_options} - ensure variety.

**LOCATION REQUIREMENT:**
- {location_hint}
- Already used locations: {used_locations_str}
- Choose a DIFFERENT city/location from those already used
- Do NOT invent modern or out-of-setting cities; only use locations explicitly supported by the WORLD CONTEXT"""

            # If we have a forced year from the worldbuilding TIME PERIOD range, enforce it in ALL prompt paths.
            if forced_year is not None:
                context_hint = (context_hint or "").rstrip()
                context_hint += f"""

**SIMULATION YEAR (HARD REQUIREMENT):**
- simulation_year MUST be exactly {forced_year}
- Do NOT include the year in the location string. Location must be ONLY the city name.
""".rstrip()
            else:
                # Fallback if no RAG system
                location_hint = location_hints[i % len(location_hints)]
                used_locations_str = ", ".join(used_locations) if used_locations else "None yet"
                context_hint = f"""Create a character with a realistic occupation. Character {i+1} of {num_options} - ensure variety.

**LOCATION REQUIREMENT:**
- {location_hint}
- Already used locations: {used_locations_str}
- Choose a DIFFERENT city/location from those already used
- Do NOT invent modern or out-of-setting cities; only use locations explicitly supported by the WORLD CONTEXT"""
            
            success = False
            for retry in range(max_retries_per_option):
                try:
                    # Generate a unique character using the creator agent
                    character_actor = self.creator_agent.generate_user_actor(context=context_hint)

                    if forced_year is not None:
                        try:
                            character_actor.sheet.simulation_year = forced_year
                        except Exception:
                            pass

                    # Sanitize location: some models append the year into the location field.
                    try:
                        loc = getattr(character_actor.sheet, 'location', None)
                        if isinstance(loc, str) and loc:
                            # Examples we want to fix:
                            # - "Prague, 1324"
                            # - "Vienna (1414)"
                            import re
                            cleaned = re.sub(r"\s*[,\(]\s*\d{4}\s*\)?\s*$", "", loc).strip()
                            if cleaned:
                                character_actor.sheet.location = cleaned
                    except Exception:
                        pass

                    try:
                        if local_allowed_occupations and hasattr(character_actor, 'sheet'):
                            character_actor.sheet.occupation = self._coerce_to_allowed_occupation(
                                getattr(character_actor.sheet, 'occupation', ''),
                                local_allowed_occupations,
                                used_occupations,
                            )
                    except Exception:
                        pass
                    
                    # Enforce archetype distinctness (drastically different experiences)
                    try:
                        archetype = archetype_specs[i % len(archetype_specs)]
                        if not self._meets_archetype(character_actor, archetype.get('label', '')):
                            if retry < max_retries_per_option - 1:
                                self.logger.info(
                                    f"Vessel {i+1} does not meet archetype '{archetype.get('label', '')}'. Retrying..."
                                )
                                continue
                    except Exception:
                        pass
                    
                    # Check if occupation and location are unique
                    occupation = character_actor.sheet.occupation
                    occupation_lower = occupation.lower()
                    location = character_actor.sheet.location if hasattr(character_actor.sheet, 'location') else "Unknown"
                    location_lower = location.lower()

                    # Faction check: prefer non-None and avoid repeats when possible.
                    faction_val = getattr(character_actor.sheet, 'faction', None) or getattr(character_actor.sheet, 'affiliation', None) or 'None'
                    faction_s = str(faction_val).strip() if faction_val is not None else 'None'
                    faction_l = faction_s.lower()
                    if allowed_factions:
                        # If we enforced a hard faction requirement for this option, require it.
                        if allowed_non_none_factions:
                            try:
                                desired = desired_factions[i] if (i < len(desired_factions)) else None
                            except Exception:
                                desired = None
                            if desired and faction_s != desired and retry < max_retries_per_option - 1:
                                self.logger.info(f"Faction '{faction_s}' did not meet requirement '{desired}'. Retrying...")
                                continue

                        # Avoid repeating the exact same faction across vessel options if alternatives exist.
                        if faction_l != 'none' and faction_l in used_factions and len(allowed_non_none_factions) > len(used_factions):
                            if retry < max_retries_per_option - 1:
                                self.logger.info(f"Faction '{faction_s}' already used. Retrying for diversity...")
                                continue

                    if not allowed_city_keywords:
                        # If we can't extract a city allowlist from RAG, don't block vessel generation.
                        is_allowed_location = True
                    elif location_lower and location_lower != "unknown":
                        is_allowed_location = any(k in location_lower for k in allowed_city_keywords)
                    else:
                        is_allowed_location = False

                    if not is_allowed_location:
                        if retry < max_retries_per_option - 1:
                            self.logger.info(f"Location '{location}' not supported by major city lore. Retrying...")
                            continue

                        # Final attempt: accept and register this as a generated city for the run.
                        try:
                            if location and location_lower and location_lower != 'unknown':
                                # Basic sanity checks: no digits in city name.
                                if not any(ch.isdigit() for ch in location):
                                    register_generated_city(location)
                                    if location not in allowed_city_names:
                                        allowed_city_names.append(location)
                                        allowed_city_keywords.append(location_lower)
                                    is_allowed_location = True
                        except Exception:
                            pass

                    # Check for duplicate or too-similar occupations
                    is_duplicate_occupation = False
                    for used_occ in used_occupations:
                        # Check if occupations share key words (e.g., "DJ" in both)
                        used_words = set(used_occ.lower().split())
                        new_words = set(occupation_lower.split())
                        # If they share significant words, consider it a duplicate
                        if len(used_words & new_words) > 0:
                            is_duplicate_occupation = True
                            break
                    
                    # Check for duplicate locations (exact match or same city)
                    is_duplicate_location = location_lower in used_locations
                    
                    if (is_duplicate_occupation or is_duplicate_location) and retry < max_retries_per_option - 1:
                        if is_duplicate_occupation:
                            self.logger.info(f"Occupation '{occupation}' too similar to existing. Retrying...")
                        if is_duplicate_location:
                            self.logger.info(f"Location '{location}' already used. Retrying...")
                        continue
                    
                    # Accept this character
                    used_occupations.add(occupation_lower)
                    used_locations.add(location_lower)
                    try:
                        if faction_l and faction_l != 'none':
                            used_factions.add(faction_l)
                    except Exception:
                        pass
                    
                    vessel_data = {
                        'actor': character_actor,
                        'name': character_actor.sheet.name,
                        'occupation': character_actor.sheet.occupation,
                        's_factors': {
                            sf.name: character_actor.sheet.s_factors.get_factor(sf)
                            for sf in SFactorType
                        },
                        'skills': dict(character_actor.sheet.skills),
                        'statuses': {
                            st.name: character_actor.sheet.statuses[st].value
                            for st in [StatusType.STAMINA, StatusType.SPIRIT, StatusType.SUPPLY]
                        }
                    }
                    
                    vessel_options.append(vessel_data)
                    success = True
                    break  # Success, move to next option
                    
                except Exception as e:
                    if retry < max_retries_per_option - 1:
                        self.logger.warning(f"Error generating character option {i+1} (attempt {retry+1}/{max_retries_per_option}): {e}")
                        self.logger.info(f"Retrying character option {i+1}...")
                    else:
                        self.logger.error(f"Error generating character option {i+1}: {e}")
            
            if not success:
                self.logger.warning(f"Failed to generate character option {i+1} after {max_retries_per_option} attempts")
        
        self.generated_options = vessel_options
        return vessel_options
    
    def display_vessel_options(self, vessel_options: List[Dict[str, Any]]):
        """Display character options to the user with rich formatting"""
        
        print(f"\n{Color.HEADER}{'═' * 80}{Color.RESET}")
        print(f"{Color.HEADER}                    🎭 VESSEL SELECTION 🎭{Color.RESET}")
        print(f"{Color.HEADER}{'═' * 80}{Color.RESET}\n")
        
        num_options = len(vessel_options)
        vessels_word = "Vessel has" if num_options == 1 else "Vessels have"
        print(f"{Color.INFO}{num_options} {vessels_word} been found.{Color.RESET}")
        print(f"{Color.INFO}Choose which vessel to embody.{Color.RESET}\n")
        
        for idx, vessel_data in enumerate(vessel_options, 1):
            actor = vessel_data['actor']
            
            print(f"{Color.HEADER}{'─' * 80}{Color.RESET}")
            print(f"{Color.SUCCESS}[{idx}] {actor.sheet.name.upper()}{Color.RESET}")
            print(f"{Color.HEADER}{'─' * 80}{Color.RESET}\n")
            
            # Character identity with occupation category hint
            occupation = actor.sheet.occupation
            age = actor.sheet.age if hasattr(actor.sheet, 'age') else 30
            location = actor.sheet.location if hasattr(actor.sheet, 'location') else "Unknown"
            faction = getattr(actor.sheet, 'faction', None) or getattr(actor.sheet, 'affiliation', None) or "None"
            
            # Get this vessel's simulation year (each vessel can have its own year)
            # Only after selection will the chosen year become canonical
            year = actor.sheet.simulation_year if hasattr(actor.sheet, 'simulation_year') and actor.sheet.simulation_year else ActorSheet.get_simulation_year()
            
            print(f"{Color.INFO}Age:{Color.RESET} {age} • {Color.INFO}Location:{Color.RESET} {location}, {year}")
            print(f"{Color.INFO}Occupation:{Color.RESET} {occupation}")
            print(f"{Color.INFO}Faction:{Color.RESET} {faction}")
            
            # Personality
            if hasattr(actor.sheet, 'personality_traits'):
                personality = actor.sheet.personality_traits
                if isinstance(personality, dict):
                    internal = personality.get('internal', 'N/A')
                    external = personality.get('external', 'N/A')
                    print(f"{Color.INFO}Personality:{Color.RESET} {internal} / {external}")
            print()
            
            # S-Factors
            print(f"{Color.INFO}S-Factors:{Color.RESET}")
            from narrative_utils import get_narrative_descriptor
            for s_factor_type in SFactorType:
                value = vessel_data['s_factors'][s_factor_type.name]
                bar = "█" * value + "░" * (5 - value)
                descriptor = get_narrative_descriptor(value)
                print(f"  {s_factor_type.name.capitalize():12} [{bar}] {value} ({descriptor})")
            print()
            
            # Top Skills
            print(f"{Color.INFO}Key Skills:{Color.RESET}")
            sorted_skills = sorted(vessel_data['skills'].items(), key=lambda x: x[1], reverse=True)
            for skill_name, skill_value in sorted_skills[:5]:
                bar = "█" * skill_value + "░" * (5 - skill_value)
                descriptor = get_narrative_descriptor(skill_value)
                print(f"  {skill_name:20} [{bar}] {skill_value} ({descriptor})")
            print()
        
        print(f"{Color.HEADER}{'═' * 80}{Color.RESET}\n")
    
    def get_user_selection(self, vessel_options: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get user's character selection via input"""
        
        while True:
            try:
                choice = input(f"{Color.INFO}Select your character [1-{len(vessel_options)}]: {Color.RESET}").strip()
                
                if not choice.isdigit():
                    print(f"{Color.ERROR}Please enter a number.{Color.RESET}")
                    continue
                
                choice_idx = int(choice) - 1
                
                if choice_idx < 0 or choice_idx >= len(vessel_options):
                    print(f"{Color.ERROR}Invalid selection. Choose 1-{len(vessel_options)}.{Color.RESET}")
                    continue
                
                selected_vessel = vessel_options[choice_idx]
                
                # Display selection
                print(f"\n{Color.SUCCESS}You have selected: {selected_vessel['name']}{Color.RESET}")
                print(f"{Color.INFO}Occupation: {selected_vessel['occupation']}{Color.RESET}")
                
                return selected_vessel
                    
            except KeyboardInterrupt:
                print(f"\n{Color.ERROR}Selection cancelled.{Color.RESET}")
                raise
            except Exception as e:
                print(f"{Color.ERROR}Error: {e}{Color.RESET}")
                continue
    
    def select_vessel(self) -> UserActor:
        """
        Main character selection flow
        
        Returns the selected UserActor
        """
        print(f"\n{Color.INFO}🎭 Generating character options...{Color.RESET}\n")
        
        # Generate three character options
        vessel_options = self.generate_vessel_options(num_options=3)
        
        if not vessel_options:
            raise RuntimeError("Failed to generate character options")
        
        # Display options
        self.display_vessel_options(vessel_options)
        
        # Get user selection
        selected_vessel = self.get_user_selection(vessel_options)
        
        # Set the canonical simulation year from the selected vessel
        # This is when the year becomes fixed for the entire simulation
        selected_actor = selected_vessel['actor']
        if hasattr(selected_actor.sheet, 'simulation_year') and selected_actor.sheet.simulation_year:
            ActorSheet.set_simulation_year(selected_actor.sheet.simulation_year)
            print(f"\n{Color.INFO}📅 Simulation year set to {selected_actor.sheet.simulation_year}{Color.RESET}")
        
        # Return the selected actor - memories will be created after session naming
        print(f"{Color.SUCCESS}✓ Your vessel awakens: {selected_vessel['name']}{Color.RESET}")
        
        return selected_actor
    
    def create_memories_for_actor(self, actor: UserActor):
        """
        Public method to create initial memories for an actor.
        Called after session naming is complete.
        """
        self._create_initial_memories(actor)
        print(f"{Color.SUCCESS}✓ Ready to begin{Color.RESET}\n")
    
    def _create_initial_memories(self, actor: UserActor):
        """
        Create initial memories for the selected UA using InternalVoiceCreatorAgent.
        
        This generates 2 memories per category (15 categories = 30 memories) based on
        the actor's personality, backstory, and occupation. Uses RAG to ground memories
        in the worldbuilding context.
        
        Categories: family, job, friends, trauma, achievement, relationship, location,
        childhood, education, loss, hobbies, beliefs, secrets, fears, dreams
        """
        if not INTERNAL_VOICE_AVAILABLE:
            self.logger.warning("InternalVoiceCreatorAgent not available - skipping initial memory creation")
            return
        
        try:
            print(f"\n{Color.INFO}🧠 Generating initial memories for {actor.sheet.name}...{Color.RESET}")
            
            # Create the internal voice creator agent with RAG for worldbuilding-grounded memories
            voice_creator = InternalVoiceCreatorAgent(
                storage_directory=self.storage_directory,
                rag_system=self.rag_system
            )
            
            # Build personality prompt from actor sheet
            personality_prompt = self._build_personality_prompt(actor)
            
            # Build backstory from available information
            backstory = self._build_backstory(actor)
            
            # Generate initial memories
            memories = voice_creator.create_initial_memories(
                actor_name=actor.sheet.name,
                personality_prompt=personality_prompt,
                backstory=backstory
            )
            
            if memories:
                # Count total memories created (handle both list and string formats)
                total_memories = 0
                for mems in memories.values():
                    if isinstance(mems, list):
                        total_memories += len(mems)
                    elif mems:  # String or other truthy value counts as 1
                        total_memories += 1
                categories_with_memories = len([c for c, m in memories.items() if m])
                
                print(f"{Color.SUCCESS}✓ Created {total_memories} memories across {categories_with_memories} categories{Color.RESET}")
                
                # Show a sample memory
                for category, mems in memories.items():
                    if mems:
                        # Handle case where mems is a string instead of a list
                        if isinstance(mems, str):
                            sample = mems[:60]
                        elif isinstance(mems, list) and len(mems) > 0:
                            first_mem = mems[0]
                            if isinstance(first_mem, dict):
                                sample = first_mem.get('content', str(first_mem))[:60]
                            else:
                                sample = str(first_mem)[:60]
                        else:
                            continue
                        print(f"{Color.SYSTEM}  Sample ({category}): \"{sample}...\"{Color.RESET}")
                        break
                
                # CRITICAL: Also save to KeyMemoriesSystem for the 'memories' command
                try:
                    from key_memories_system import get_key_memories, MemoryCategory, MemoryImportance
                    key_mem_system = get_key_memories()
                    
                    # Map category names to MemoryCategory enum
                    category_map = {
                        'family': MemoryCategory.RELATIONSHIP,
                        'job': MemoryCategory.DISCOVERY,
                        'friends': MemoryCategory.RELATIONSHIP,
                        'trauma': MemoryCategory.LOSS,
                        'achievement': MemoryCategory.ACHIEVEMENT,
                        'relationship': MemoryCategory.RELATIONSHIP,
                        'location': MemoryCategory.LOCATION,
                        'childhood': MemoryCategory.RELATIONSHIP,
                        'education': MemoryCategory.DISCOVERY,
                        'loss': MemoryCategory.LOSS,
                        'hobbies': MemoryCategory.DISCOVERY,
                        'beliefs': MemoryCategory.DISCOVERY,
                        'secrets': MemoryCategory.DISCOVERY,
                        'fears': MemoryCategory.LOSS,
                        'dreams': MemoryCategory.ACHIEVEMENT
                    }
                    
                    actor_tag = actor.sheet.name.lower().replace(" ", "_").replace("'", "").replace('"', '')
                    saved_count = 0
                    
                    for category, mems in memories.items():
                        mem_category = category_map.get(category, MemoryCategory.DISCOVERY)
                        
                        # Normalize mems to a list
                        if isinstance(mems, str):
                            mems_list = [{"content": mems, "emotional_tone": "neutral"}]
                        elif isinstance(mems, list):
                            mems_list = mems
                        else:
                            continue
                        
                        for mem in mems_list:
                            # Handle both dict and string formats
                            if isinstance(mem, dict):
                                content = mem.get('content', '')
                            else:
                                content = str(mem) if mem else ''
                            if content:
                                # Create a title from the first few words
                                title = content[:50].rsplit(' ', 1)[0] + "..." if len(content) > 50 else content
                                
                                # Get emotional tone if available
                                emotional_tone = mem.get('emotional_tone', 'neutral') if isinstance(mem, dict) else 'neutral'
                                
                                # Get actor's location for the memory
                                location = getattr(actor.sheet, 'location', 'Unknown') or 'Character Background'
                                
                                key_mem_system.create_memory(
                                    title=f"{category.title()}: {title}",
                                    description=content,
                                    full_narrative=content,  # Use content as full narrative for initial memories
                                    category=mem_category,
                                    importance=MemoryImportance.NOTABLE,
                                    location=location,
                                    actors_involved=[actor.sheet.name],
                                    tags=[actor_tag, "character_background", category, "initial_memory"],
                                    emotional_tone=emotional_tone
                                )
                                saved_count += 1
                    
                    if saved_count > 0:
                        print(f"{Color.SUCCESS}✓ Saved {saved_count} memories to key memory system{Color.RESET}")
                        
                except Exception as km_error:
                    self.logger.warning(f"Could not save to KeyMemoriesSystem: {km_error}")
            else:
                print(f"{Color.WARNING}⚠️ No memories generated{Color.RESET}")
                
        except Exception as e:
            self.logger.error(f"Failed to create initial memories: {e}")
            print(f"{Color.WARNING}⚠️ Memory generation failed: {e}{Color.RESET}")
    
    def _build_personality_prompt(self, actor: UserActor) -> str:
        """Build a personality prompt from the actor's sheet for memory generation"""
        sheet = actor.sheet
        
        parts = [f"**CHARACTER:** {sheet.name}"]
        
        # Add occupation
        if hasattr(sheet, 'occupation') and sheet.occupation:
            parts.append(f"**OCCUPATION:** {sheet.occupation}")
        
        # Add age
        if hasattr(sheet, 'age') and sheet.age:
            parts.append(f"**AGE:** {sheet.age}")
        
        # Add personality traits
        if hasattr(sheet, 'personality_traits') and sheet.personality_traits:
            internal = sheet.personality_traits.get('internal', '')
            external = sheet.personality_traits.get('external', '')
            if internal:
                parts.append(f"**INTERNAL PERSONALITY:** {internal}")
            if external:
                parts.append(f"**EXTERNAL PERSONALITY:** {external}")
        
        # Add OCEAN if available
        if hasattr(sheet, 'ocean') and sheet.ocean:
            ocean_str = ", ".join(f"{k}: {v}" for k, v in sheet.ocean.items())
            parts.append(f"**OCEAN:** {ocean_str}")
        
        # Add MBTI if available
        if hasattr(sheet, 'mbti') and sheet.mbti:
            parts.append(f"**MBTI:** {sheet.mbti}")
        
        # Add goals
        if hasattr(sheet, 'goals') and sheet.goals:
            goals_str = ", ".join(sheet.goals[:3])
            parts.append(f"**GOALS:** {goals_str}")
        
        return "\n".join(parts)
    
    def _build_backstory(self, actor: UserActor) -> str:
        """Build a backstory summary from available actor information"""
        sheet = actor.sheet
        parts = []
        
        # Add location context
        if hasattr(sheet, 'location') and sheet.location:
            parts.append(f"Lives/works in {sheet.location}.")
        
        # Add occupation context
        if hasattr(sheet, 'occupation') and sheet.occupation:
            parts.append(f"Works as a {sheet.occupation}.")
        
        # Add age context
        if hasattr(sheet, 'age') and sheet.age:
            parts.append(f"Is {sheet.age} years old.")
        
        # Add any existing backstory
        if hasattr(sheet, 'backstory') and sheet.backstory:
            parts.append(sheet.backstory)
        
        # Use simulation year if available, otherwise generic fallback
        if not parts:
            sim_year = ActorSheet.get_simulation_year() if hasattr(ActorSheet, 'get_simulation_year') else None
            if sim_year:
                return f"A person living their life in {sim_year}."
            else:
                return "A person living their everyday life."
        return " ".join(parts)


def create_vessel_selection_system(creator_agent, storage_directory: Path, rag_system=None) -> VesselSelectionSystem:
    """Factory function to create vessel selection system"""
    return VesselSelectionSystem(creator_agent, storage_directory, rag_system)
