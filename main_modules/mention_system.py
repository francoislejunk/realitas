"""Auto-extracted from redesigned_main.py"""

import sys
import os
import time
import re
import json
import random
from typing import Optional, List, Dict, Any, Tuple
from pathlib import Path

# These imports will need to be adjusted based on what's actually used in each module

def _mention_llm_rate_limited() -> bool:
    try:
        import time as _time
        now = _time.time()
    except Exception:
        return True
    try:
        global _MENTION_LLM_CALL_TIMES
        _MENTION_LLM_CALL_TIMES = [t for t in (_MENTION_LLM_CALL_TIMES or []) if (now - float(t)) <= 60.0]
        if len(_MENTION_LLM_CALL_TIMES) >= int(_MENTION_LLM_MAX_CALLS_PER_MIN):
            return True
        _MENTION_LLM_CALL_TIMES.append(now)
        return False
    except Exception:
        return True




def _extract_mentions_via_llm(text: str) -> list[dict]:
    """Use LLM to identify mentioned actors and their likely locations from narrative text."""
    try:
        from openrouter_config import OpenRouterConfig, robust_llm_call
        from json_utils import extract_and_parse_json
    except Exception:
        return []

    t = (text or '').strip()
    if not t or len(t) < 10:
        return []

    if _mention_llm_rate_limited():
        return []

    prompt = f"""You are a specialized entity extractor for a narrative simulation.
Analyze the following text and identify all CHARACTER MENTIONS.

RULES:
1. Identify specific names (e.g. "Franz", "Master Hurek") or specific roles/relationships (e.g. "The Prince", "My Mentor").
2. For each character, infer their LIKELY LOCATION if the text suggests one.
3. If no location is suggested, use "unknown".
4. Filter out geographic descriptors (e.g. "Venetian", "Roman") and common nouns.
5. Return ONLY a JSON object with a 'mentions' array.

TEXT:
{t}

JSON schema:
{{
  "mentions": [
    {{"name": "...", "location": "...", "is_role": false}}
  ]
}}"""

    try:
        client = OpenRouterConfig.create_client()
        model = OpenRouterConfig.get_model_for_role('coordination')
        
        resp = robust_llm_call(
            client=client,
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.1,
            max_tokens=500,
            call_name="mention_extraction"
        )
        
        if not resp:
            return []
            
        obj = extract_and_parse_json(resp)
        if isinstance(obj, dict) and 'mentions' in obj:
            return obj['mentions']
    except Exception:
        pass
    return []




def _capture_mentioned_actors_from_text(t: str, source: str = 'unknown', location_hint: str = None) -> None:
    """Scan narrative text for characters/roles and record them in the persistent mention system.
    This uses a hybrid approach: fast regex-based heuristics for live narrative, 
    and (optionally) LLM-based extraction for higher accuracy.
    """
    if not t or len(t) < 5:
        return

    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if cm is None:
            return
    except Exception:
        return

    # --- LLM-BASED EXTRACTION (if enabled) ---
    llm_mentions = []
    if _MENTION_LLM_ENABLED:
        try:
            llm_mentions = _extract_mentions_via_llm(t)
            for m in llm_mentions:
                name = m.get('name', '').strip()
                loc = m.get('location', '').strip()
                is_role = m.get('is_role', False)
                if name:
                    tags = [loc] if loc and loc.lower() != 'unknown' else []
                    source_val = f"LLM:{source}"
                    if is_role or name.lower().startswith('role:'):
                        role_name = name if name.lower().startswith('role:') else f"ROLE:{name}"
                        cm.add_mentioned_actor(role_name, source=source_val, location_tags=tags, hint=t[:220])
                    else:
                        cm.add_mentioned_actor(name, source=source_val, location_tags=tags, hint=t[:220])
        except Exception:
            pass

    # --- HEURISTIC/REGEX APPROACH (always runs as fallback/supplement) ---
    inferred_location = location_hint
    max_names = 10
    
    # Expand common words to filter out non-name proper nouns and common sentence starters
    common_words = {
        'The', 'A', 'An', 'This', 'That', 'He', 'She', 'It', 'They', 'You', 'I', 
        'When', 'If', 'Then', 'But', 'And', 'Or', 'There', 'Where', 'My', 'Your', 
        'His', 'Her', 'Our', 'Their', 'On', 'In', 'At', 'To', 'From', 'With',
        'Venetian', 'London', 'Paris', 'Roman', 'Greek', 'English', 'French',
        'German', 'Italian', 'Spanish', 'European', 'Asian', 'American', 'African',
        'North', 'South', 'East', 'West', 'Northern', 'Southern', 'Eastern', 'Western',
        'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
        'January', 'February', 'March', 'April', 'May', 'June', 'July', 'August',
        'September', 'October', 'November', 'December',
        # Memory Categories & Headers
        'Dreams', 'Fears', 'Secrets', 'Beliefs', 'Hobbies', 'Loss', 'Education', 'Childhood', 'Relationship', 'Location',
        'Notable', 'Moments', 'Recall', 'Type', 'Use', 'Total', 'Traceback', 'File', 'Line', 'Module', 'Error',
        # Common Nouns, Meta-Words & Sentence Starters
        'Standing', 'Walking', 'Watching', 'Witnessing', 'Spending', 'Losing', 'Learning', 'Practicing', 'Studying',
        'Questioning', 'Refusing', 'To', 'For', 'After', 'Before', 'During', 'Though', 'Every', 'All', 'Some',
        'Being', 'Trauma', 'Successfully', 'None', 'Sharing', 'Securing', 'Track', 'Tracking', 'Status', 'In', 'As',
        'Prague', 'Venice', 'Vltava', 'Jewish', 'Quarter', 'Technicians', 'Guild', 'Master', 'Prince', 'Princes',
        'War', 'Canals', 'Docks', 'Bridge', 'Library', 'Tavern', 'Market', 'Hall', 'City', 'Gate', 'Walls', 'Alley',
        'Gale', 'Darkness', 'Mud', 'Eyesight', 'Ledger', 'Park', 'Secure', 'Protect', 'Achievement', 'Soldier', 
        'Guard', 'Sometimes', 'Here', 'Seal', 'Abamixtra', 'Job', 'Captain', 'Thames', 'Hunter', 'Old', 'Silas',
        'King', 'Blackwall', 'Stoic', 'Professional', 'Young', 'Younger', 'Small', 'Great', 'Big', 'Large'
    }

    # Junk fragments often caught as inferred locations
    loc_noise = {
        'the', 'was', 'and', 'with', 'from', 'this', 'that', 'they', 'some', 'each', 'all', 'any', 'none',
        'cost', 'wall', 'full', 'kit', 'his', 'eyes', 'hunting', 'those', 'brief', 'ruined', 'behind',
        'soot', 'stained', 'window', 'northern', 'front', 'compromised', 'route', 'archival', 'crypt',
        'those', 'brief', 'his', 'eyes', 'wall', 'of', 'full', 'kit', 'from', 'the', 'cost', 'of', 'cost', 'o'
    }

    # Filter out the UA name if possible
    ua_name = ''
    try:
        from persistent_context_manager import get_context_manager
        _cm_temp = get_context_manager()
        if _cm_temp and hasattr(_cm_temp, 'context'):
            ua_name = str(getattr(_cm_temp.context, 'ua_name', '') or '').strip()
    except Exception:
        pass

    if not inferred_location:
        import re
        loc_patterns = [
            # High-confidence patterns: explicit statements about where someone is
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:should be|is probably|might be|can be found)\s+(?:at|in)\s+(?:the\s+)?([a-z]{3,}(?:\s+[a-z]{3,})?)\b",
            # "check the library for Sam" pattern
            r"check\s+(?:the\s+)?([a-z]{3,}(?:\s+[a-z]{3,})?)\s+for\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)",
            # Direct location statement: "Sam is at the library"
            r"([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)\s+(?:is|was|lives|works|stays)\s+(?:at|in)\s+(?:the\s+)?([a-z]{3,}(?:\s+[a-z]{3,})?)\b",
        ]
        
        for pattern in loc_patterns:
            match = re.search(pattern, t)
            if match:
                potential_actor = ""
                potential_loc = ""
                if "check" in pattern:
                    potential_loc = match.group(1).strip()
                    potential_actor = match.group(2).strip()
                else:
                    potential_actor = match.group(1).strip()
                    potential_loc = match.group(2).strip()
                
                # Validation: location must not be in noise list, and actor must not be a common word
                # Also ensure location is not a single short word that's likely a fragment
                if (potential_actor and potential_actor not in common_words and 
                    potential_actor.lower() not in ['you', 'me', 'my', 'i', (ua_name or '').lower()] and
                    potential_loc and potential_loc.lower() not in loc_noise and
                    len(potential_loc) > 3):
                    inferred_location = potential_loc
                    break

    def _sanitize_marked_name(raw: str) -> str:
        """Sanitize an @Name capture."""
        s = str(raw or '').strip()
        if not s:
            return ''
        s = s.strip("\"'()[]{} ")
        if not s:
            return ''
        
        # Filter out UA name
        if ua_name and s.lower() == ua_name.lower():
            return ''

        parts = [p for p in s.split() if p.strip()]
        if not parts:
            return ''
        if parts[0] in common_words:
            return ''
        if parts[0].endswith('ing') and len(parts[0]) > 4:
            return ''
        first = parts[0]
        if not first or not first[0].isalpha() or not first[0].isupper():
            return ''
        kept = [first]
        for p in parts[1:3]:
            if not p: break
            if p[0].isalpha() and p[0].islower(): break
            low = p.lower()
            if low in {'our', 'my', 'your', 'his', 'her', 'their', 'the', 'a', 'an'}: break
            if p in common_words: break
            kept.append(p)
        nm = ' '.join(kept).strip()
        
        # Final junk filter
        if nm.lower() in {'best', 'hard', 'maybe', 'unknown', 'none', 'sometimes', 'here'}:
            return ''
        if len(nm) < 2:
            return ''
        return nm

    # Best-effort prune/normalize existing mentions
    try:
        existing = list(cm.get_mentioned_actors() or []) if hasattr(cm, 'get_mentioned_actors') else []
        cleaned = []
        seen = set()
        for e in existing:
            if not isinstance(e, dict): continue
            nm0 = str(e.get('name', '') or '').strip()
            if not nm0: continue
            low0 = nm0.lower()
            if low0.startswith('role:'):
                if low0 not in seen:
                    seen.add(low0)
                    cleaned.append(e)
                continue
            nm1 = _sanitize_marked_name(nm0)
            if not nm1: continue
            key = nm1.lower()
            if key not in seen:
                seen.add(key)
                if nm1 != nm0:
                    e = dict(e)
                    e['name'] = nm1
                cleaned.append(e)
        if hasattr(cm, 'context') and hasattr(cm.context, 'mentioned_actors'):
            cm.context.mentioned_actors = cleaned
            if hasattr(cm, '_save'): cm._save()
    except Exception:
        pass

    present = set()
    try:
        if hasattr(cm, 'context') and getattr(cm.context, 'present_nuas', None):
            for n in list(cm.context.present_nuas or []):
                nn = str(n or '').strip().lower()
                if nn: present.add(nn)
    except Exception:
        pass

    candidates: list[str] = []
    role_candidates: list[str] = []
    
    # --- HEURISTIC NAME DETECTION ---
    try:
        potential_names = re.findall(r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){0,2})\b", t)
        for pn in potential_names:
            if pn in common_words: continue
            s = _sanitize_marked_name(pn)
            if s and s.lower() not in present:
                if s.lower() not in [c.lower() for c in candidates]:
                    candidates.append(s)
    except Exception:
        pass

    # --- EXPLICIT MENTION DETECTION (@ PREFIX) ---
    try:
        for m in re.finditer(r'@\{([^\}]{2,64})\}', t):
            role = (m.group(1) or '').strip().strip("\"'()[]{} ")
            if role and role.lower() not in [r.lower() for r in role_candidates]:
                role_candidates.append(role)
                if len(role_candidates) >= max_names: break

        for m in re.finditer(r'@(?!\{)([^\s\n\r\t,.;:!?]{2,64}(?:\s+[^\s\n\r\t,.;:!?]{2,64}){0,2})', t):
            raw = (m.group(1) or '').strip()
            nm = _sanitize_marked_name(raw)
            if nm and nm.lower() not in present and nm.lower() not in [c.lower() for c in candidates]:
                candidates.append(nm)
            if (len(candidates) + len(role_candidates)) >= max_names: break
    except Exception:
        pass

    if not candidates and not role_candidates:
        return

    hint = (t[:220] + '...') if len(t) > 220 else t
    tags = [inferred_location] if inferred_location else []
    for role in role_candidates:
        try: cm.add_mentioned_actor(f"ROLE:{role}", source=source, location_tags=tags, hint=hint)
        except Exception: pass
    for nm in candidates:
        try: cm.add_mentioned_actor(nm, source=source, location_tags=tags, hint=hint)
        except Exception: pass




def _clear_mentioned_actors() -> None:
    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if cm is None or not hasattr(cm, 'context'):
            return
        try:
            cm.context.mentioned_actors = []
        except Exception:
            return
        try:
            if hasattr(cm, '_save'):
                cm._save()
        except Exception:
            pass
    except Exception:
        return




def _apply_mentioned_actor_reintroduction_policy(
    *,
    available_npcs: list,
    scene_description: str,
    scene_creator=None,
    actor_registry: dict | None = None,
    max_spawns: int = 1,
    allow_generation: bool = True,
) -> list:
    """Best-effort policy to pull mentioned actors into the active scene.

    Conservative rules:
    - Only spawns at most `max_spawns` per call.
    - Never spawns actors already present.
    - Prefers re-using a previously created actor from `actor_registry`.
    - Only generates a new NUA when the mention's location tags plausibly match the current location,
      or when the mention text strongly implies immediate arrival.
    """
    spawned = []
    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if cm is None or not hasattr(cm, 'get_mentioned_actors'):
            return spawned
    except Exception:
        return spawned

    try:
        present_names = set()
        for npc in (available_npcs or []):
            try:
                n = (getattr(getattr(npc, 'sheet', None), 'name', None) or '').strip()
                if n:
                    present_names.add(n.lower())
            except Exception:
                continue
        try:
            for n in list(getattr(getattr(cm, 'context', None), 'present_nuas', None) or []):
                nn = str(n or '').strip()
                if nn:
                    present_names.add(nn.lower())
        except Exception:
            pass
    except Exception:
        present_names = set()

    try:
        current_loc = str(getattr(getattr(cm, 'context', None), 'current_location', '') or '')
        current_label = str(getattr(getattr(cm, 'context', None), 'location_label', '') or '')
    except Exception:
        current_loc = ""
        current_label = ""

    haystack = f"{current_label}\n{current_loc}\n{(scene_description or '')[:500]}".lower()
    arrival_pattern = None
    try:
        import re
        # Pattern-based, time-agnostic arrival detection (avoid enumerating long phrase lists).
        arrival_pattern = re.compile(r"\b(arriv\w*|enter\w*|walk\w*\s+in|show\w*\s+up|come\w*\s+in|step\w*\s+in)\b", re.IGNORECASE)
    except Exception:
        arrival_pattern = None

    try:
        mentioned = list(cm.get_mentioned_actors() or [])
    except Exception:
        mentioned = []

    def _score_entry(e: dict) -> tuple[float, dict]:
        reasons: dict = {}
        score = 0.0

        def _normalize_location_tags(raw: list[str]) -> list[str]:
            """Soft normalization for location tags: keep tags generic/era-neutral.

            We avoid large hard-coded lists by:
            - applying a few high-signal, low-risk normalizations
            - filtering obviously modern/anachronistic markers
            """
            try:
                import re
            except Exception:
                re = None

            out: list[str] = []
            for t0 in (raw or []):
                t = str(t0 or '').strip().lower()
                if not t:
                    continue

                # Filter obvious anachronisms (soft guardrail)
                # Keep this short and morphology-based.
                tl = t
                try:
                    if re is not None:
                        if re.search(r"\b(wifi|wi-?fi|smart\w*|app\w*|internet|online|website|social\s*media|stream\w*|podcast|email|text\s*message|sms)\b", tl):
                            continue
                    else:
                        if any(x in tl for x in ['wifi', 'wi-fi', 'smart', 'app', 'internet', 'online', 'website', 'email', 'sms']):
                            continue
                except Exception:
                    pass

                # Light canonicalization (generic place-types)
                # These are timeless place-types and do not inject era details.
                if 'book' in tl:
                    t = 'library'
                elif 'archive' in tl:
                    t = 'archives'
                elif 'police' in tl or 'precinct' in tl:
                    t = 'police station'
                elif 'hospital' in tl or 'clinic' in tl:
                    t = 'hospital'
                elif 'school' in tl or 'campus' in tl:
                    t = 'school'
                elif 'office' in tl:
                    t = 'office'
                elif 'home' in tl or 'house' in tl or 'apartment' in tl:
                    t = 'home'

                if t not in out:
                    out.append(t)

            return out

        nm = str(e.get('name', '') or '').strip()
        if not nm:
            return -1.0, {'skip': 'no_name'}
        if nm.lower() in present_names:
            return -1.0, {'skip': 'already_present'}

        try:
            tags_raw = list(e.get('location_tags') or [])
        except Exception:
            tags_raw = []
        tags = [str(t).strip().lower() for t in tags_raw if str(t).strip()]
        tags = _normalize_location_tags(tags)

        hint = str(e.get('hint', '') or '')
        hint_l = hint.lower()

        # Tag match strength
        tag_exact = False
        tag_in_haystack = False
        try:
            for t in tags:
                if not t:
                    continue
                if current_label and t == current_label.strip().lower():
                    tag_exact = True
                    break
        except Exception:
            tag_exact = False
        try:
            if not tag_exact:
                for t in tags:
                    if t and t in haystack:
                        tag_in_haystack = True
                        break
        except Exception:
            tag_in_haystack = False

        if tag_exact:
            score += 6.0
            reasons['tag_exact'] = True
        elif tag_in_haystack:
            score += 3.5
            reasons['tag_match'] = True
        else:
            reasons['tag_match'] = False

        # Arrival cue (pattern-based)
        implied_arrival = False
        try:
            if hint_l:
                if arrival_pattern is not None:
                    implied_arrival = bool(arrival_pattern.search(hint_l))
                else:
                    implied_arrival = ('arriv' in hint_l) or ('enter' in hint_l)
        except Exception:
            implied_arrival = False
        if implied_arrival:
            score += 2.5
            reasons['arrival_cue'] = True

        # Source importance + repeat mentions (derived heuristically from the source string)
        def _source_weight(src: str) -> float:
            s = (src or '').strip().lower()
            if not s:
                return 0.8
            # More authoritative: exchange outcomes and dialogue
            if 'exchange_step6' in s:
                return 2.2
            if 'exchange_step' in s:
                return 1.6
            # Perception is stronger than internal monologue
            if 'perceptual' in s:
                return 1.4
            # Scene/location seed text is moderately reliable
            if 'scene' in s or 'location' in s:
                return 1.2
            # Internal voice is weakest for external reality
            if 'internal' in s:
                return 0.6
            return 0.8
        srcs = []
        try:
            srcs = list(e.get('sources') or [])
        except Exception:
            srcs = []
        srcs = [str(s).strip() for s in srcs if str(s).strip()]
        if not srcs:
            try:
                s1 = str(e.get('source', '') or '').strip()
                if s1:
                    srcs = [s1]
            except Exception:
                srcs = []
        if srcs:
            best_src = None
            best_w = 0.0
            for s in srcs:
                w = float(_source_weight(s))
                if w > best_w:
                    best_w = w
                    best_src = s
            score += best_w
            reasons['best_source'] = best_src
            # Small bonus for repeated mentions across sources
            score += min(1.2, max(0.0, (len(set(srcs)) - 1) * 0.4))
            reasons['source_count'] = len(set(srcs))

        # Time-agnostic: do NOT use wallclock decay. Timestamp is only used as a stable tiebreaker.

        # Require at least some plausibility signal
        if not (tag_exact or tag_in_haystack or implied_arrival):
            return -1.0, {'skip': 'no_plausible_trigger'}

        return score, reasons

    ranked: list[tuple[float, dict, dict]] = []
    for e in mentioned:
        if not isinstance(e, dict):
            continue
        sc, why = _score_entry(e)
        if sc < 0:
            continue
        ranked.append((sc, why, e))

    try:
        ranked.sort(key=lambda x: (-float(x[0]), str((x[2] or {}).get('timestamp', ''))))
    except Exception:
        pass

    for sc, why, entry in ranked[:max(0, int(max_spawns))]:
        name = str(entry.get('name', '') or '').strip()
        if not name:
            continue
        if name.strip().lower().startswith('role:'):
            continue
        if name.lower() in present_names:
            continue

        actor_obj = None
        try:
            if actor_registry is not None and name in actor_registry:
                actor_obj = actor_registry[name]
        except Exception:
            actor_obj = None

        if actor_obj is None and allow_generation and scene_creator is not None and hasattr(scene_creator, 'generate_nua'):
            try:
                try:
                    tags_raw = list(entry.get('location_tags') or [])
                except Exception:
                    tags_raw = []
                hint = str(entry.get('hint', '') or '')
                tag_text = ", ".join(tags) if tags else "unknown"
                ctx = f"Mentioned actor to (re)introduce: {name}. Likely where to find them: {tag_text}. Mention context: {hint[:200]}"
                actor_obj = scene_creator.generate_nua(context=ctx, scene_description=scene_description)
                if actor_obj is not None:
                    try:
                        actor_obj.sheet.name = name
                        actor_obj.name = name
                    except Exception:
                        pass
            except Exception:
                actor_obj = None

        if actor_obj is None:
            continue

        try:
            if available_npcs is not None:
                available_npcs.append(actor_obj)
        except Exception:
            pass

        try:
            if actor_registry is not None:
                actor_registry[name] = actor_obj
        except Exception:
            pass

        try:
            if hasattr(cm, 'add_nua'):
                cm.add_nua(name)
        except Exception:
            pass

        try:
            if not SUPPRESS_DEBUG:
                print(f"{Color.SYSTEM}[MENTION SPAWN] + {name} score={sc:.2f} details={why}{Color.RESET}")
        except Exception:
            pass

        spawned.append(name)
        present_names.add(name.lower())

    return spawned




def sync_mentions_from_ua_context(actor) -> None:
    """Scan UA goals, tasks, and memories for mentioned actors to populate the mention system.
    This should be called at startup and during location shifts to ensure leads are captured.
    """
    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if not cm:
            return

        # 1. Scan Goals
        if hasattr(actor.sheet, 'goals') and actor.sheet.goals:
            for goal in actor.sheet.goals:
                _capture_mentioned_actors_from_text(goal, source="ua_goal")

        # 2. Scan Current Task
        if hasattr(actor.sheet, 'get_current_task_description'):
            task_desc = actor.sheet.get_current_task_description()
            if task_desc:
                _capture_mentioned_actors_from_text(task_desc, source="ua_task")

        # 3. Scan Key Memories
        try:
            from key_memories_system import get_key_memories
            key_memories = get_key_memories()
            if key_memories and hasattr(key_memories, 'memories'):
                for mem in key_memories.memories.values():
                    # Check pre-extracted actors
                    if hasattr(mem, 'actors_involved') and mem.actors_involved:
                        for actor_name in mem.actors_involved:
                            try:
                                loc_hint = str(getattr(mem, 'location', '') or '').strip()
                                # Drop obvious fragment locations like "From The" / "Cost Of" etc.
                                loc_l = loc_hint.lower()
                                if (not loc_hint) or (len(loc_hint) < 4) or (loc_l in {'from the', 'cost of', 'wall of', 'his eyes', 'those brief', 'a ruined'}):
                                    loc_hint = ''
                            except Exception:
                                loc_hint = ''

                            try:
                                if actor_name:
                                    # Route through mention sanitizer (pre-extracted actor lists can be noisy).
                                    _capture_mentioned_actors_from_text(
                                        f"@{str(actor_name).strip()}",
                                        source="ua_memory_actor",
                                        location_hint=loc_hint or None,
                                    )
                            except Exception:
                                pass

                    # Scan title + description for additional mentions
                    _capture_mentioned_actors_from_text(f"{mem.title}: {mem.description}", source="ua_memory")

                    # Scan full_narrative for deeper mentions
                    if hasattr(mem, 'full_narrative') and mem.full_narrative:
                        _capture_mentioned_actors_from_text(mem.full_narrative, source="ua_memory_narrative")
        except Exception:
            pass
    except Exception as e:
        if not SUPPRESS_DEBUG:
            print(f"{Color.WARNING}⚠️ Failed to sync UA context for mentions: {e}{Color.RESET}")



