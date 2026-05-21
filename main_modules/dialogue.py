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

def get_perception_context_for_prompt(actor, available_npcs=None, session_id=None) -> str:
    """
    Get perception context for LLM prompts based on sensing bubble.
    
    Returns formatted string of what the UA can perceive.
    """
    try:
        # Try pygame map first (most accurate)
        perception = get_perceivable_actors_for_narrative()
        if perception and perception != "No one nearby.":
            return f"\n[UA PERCEPTION]\n{perception}"
        
        # Fallback to sensing bubble system
        sensing_data = get_sensing_data_from_map()
        if sensing_data:
            parts = []
            for actor_id in sensing_data.get('actors_in_vision', []):
                actor_info = sensing_data['actors'].get(actor_id, {})
                parts.append(f"- {actor_info.get('name', actor_id)} ({actor_info.get('distance_to_ua', 0):.0f}u)")
            if parts:
                return f"\n[UA PERCEPTION - VISIBLE]\n" + "\n".join(parts)
        
        return ""
    except Exception:
        return ""




def _capture_continuity_facts_from_text(text: str, *, source: str = "narrative", base_confidence: float = 0.7) -> None:
    """Best-effort continuity-fact writer.

    Extracts a small set of stable anchors from authoritative text and stores them
    in PersistentContextManager.continuity_facts.
    
    This is intentionally conservative and uses lightweight heuristics (no LLM).
    """
    try:
        import re
    except Exception:
        return

    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if cm is None or not hasattr(cm, 'add_continuity_fact'):
            return
    except Exception:
        return

    t = (text or '').strip()
    if not t:
        return

    tl = t.lower()
    try:
        conf = float(base_confidence)
    except Exception:
        conf = 0.7
    conf = max(0.0, min(1.0, conf))

    # --- Anchor: Matteo and archive association (lead, not absolute truth) ---
    try:
        if ('matteo' in tl) and ('archive' in tl):
            cm.add_continuity_fact(
                "Matteo is connected to the archive (lead; verify on arrival).",
                confidence=min(0.75, conf),
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: last-known / last-seen location statements (generic) ---
    # Examples:
    # - "Matteo was last seen at the archive"
    # - "I last saw Matteo in the archive"
    # - "Matteo is said to be in the archive"
    # These are treated as leads unless the phrasing is extremely explicit.
    try:
        person_patterns = [
            r"\b([A-Z][a-z]{2,20})\b\s+was\s+last\s+seen\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
            r"\blast\s+saw\s+\b([A-Z][a-z]{2,20})\b\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
            r"\b([A-Z][a-z]{2,20})\b\s+(?:is|was)\s+said\s+to\s+be\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
        ]
        for pat in person_patterns:
            m = re.search(pat, t)
            if not m:
                continue
            person = (m.group(1) or '').strip()
            place = (m.group(2) or '').strip().rstrip('.').strip()
            if person and place:
                cm.add_continuity_fact(
                    f"{person} was last reported at/near {place} (lead).",
                    confidence=min(0.7, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: explicit "X is in/at Y" (high risk; keep conservative) ---
    # Only treat as high confidence if phrasing is direct and not hedged.
    try:
        direct_loc = re.search(r"\b(Matteo)\b\s+is\s+(?:in|at)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})", t)
        if direct_loc and not any(w in tl for w in ["maybe", "might", "unclear", "not sure", "seems", "said to", "rumor"]):
            place = (direct_loc.group(2) or '').strip().rstrip('.').strip()
            if place:
                cm.add_continuity_fact(
                    f"Matteo is stated to be in {place}.",
                    confidence=min(0.85, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: time/distance-to-destination statements ---
    # Examples:
    # - "10 minutes to the archive"
    # - "about 2 km from the archive"
    # - "a short walk to the archive"
    try:
        # minutes/hours
        m_time = re.search(r"\b(\d{1,3})\s*(minutes|minute|hours|hour)\b[^\n\.]{0,50}\bto\b[^\n\.]{0,10}\bthe\b\s+([A-Za-z][A-Za-z\s\-']{2,60})", tl)
        if m_time:
            qty = m_time.group(1)
            unit = m_time.group(2)
            dest = (m_time.group(3) or '').strip().rstrip('.').strip()
            if dest:
                cm.add_continuity_fact(
                    f"Estimated travel time to {dest}: {qty} {unit}.",
                    confidence=min(0.8, conf),
                    source=source,
                )

        # meters/km
        m_dist = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*(km|kilometers|kilometres|m|meters|metres)\b[^\n\.]{0,50}\bfrom\b[^\n\.]{0,10}\bthe\b\s+([A-Za-z][A-Za-z\s\-']{2,60})", tl)
        if m_dist:
            qty = m_dist.group(1)
            unit = m_dist.group(2)
            dest = (m_dist.group(3) or '').strip().rstrip('.').strip()
            if dest:
                cm.add_continuity_fact(
                    f"Estimated distance from {dest}: {qty} {unit}.",
                    confidence=min(0.75, conf),
                    source=source,
                )

        # qualitative
        if ('walk' in tl or 'stroll' in tl or 'short' in tl) and 'to the archive' in tl:
            cm.add_continuity_fact(
                "The archive is described as within walking distance (qualitative).",
                confidence=min(0.65, conf),
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: uncertainty markers ---
    # If the authoritative text says it's unclear, store that explicitly.
    try:
        uncertainty_markers = [
            "unclear",
            "not sure",
            "can't tell",
            "unknown",
            "no one knows",
            "conflicting",
        ]
        if any(u in tl for u in uncertainty_markers) and ('archive' in tl or 'matteo' in tl):
            cm.add_continuity_fact(
                "Key details about Matteo/archive are described as uncertain in the current narration.",
                confidence=0.6,
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: Archive spatial relation (above/below) ---
    # We only record if the text explicitly states a direction.
    try:
        below_patterns = [
            r"\barchive\b[^\n\.]{0,80}\bbelow\b",
            r"\bbelow\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bdownstairs\b",
            r"\bdownstairs\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\blower level\b",
        ]
        above_patterns = [
            r"\barchive\b[^\n\.]{0,80}\babove\b",
            r"\babove\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bupstairs\b",
            r"\bupstairs\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bupper level\b",
        ]

        saw_below = any(re.search(p, tl, flags=re.IGNORECASE) for p in below_patterns)
        saw_above = any(re.search(p, tl, flags=re.IGNORECASE) for p in above_patterns)

        if saw_below:
            cm.add_continuity_fact(
                "The archive is described as below the current area.",
                confidence=min(0.85, conf),
                source=source,
            )
        if saw_above:
            cm.add_continuity_fact(
                "The archive is described as above the current area.",
                confidence=min(0.85, conf),
                source=source,
            )

        # Conflict note (prevents flip-flopping certainty)
        if saw_below and saw_above:
            cm.add_continuity_fact(
                "The archive's relative position is conflicting (both above and below were stated); treat as uncertain.",
                confidence=0.55,
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: relationship statements (friend/ally/enemy) ---
    try:
        rel_patterns = [
            r"\b([A-Z][a-z]{2,20})\b\s+is\s+(?:our|my)\s+(friend|ally|enemy|foe)\b",
            r"\b([A-Z][a-z]{2,20})\b\s+counts\s+as\s+(?:a|an)\s+(friend|ally)\b",
        ]
        for pat in rel_patterns:
            m = re.search(pat, t)
            if not m:
                continue
            person = (m.group(1) or '').strip()
            rel = (m.group(2) or '').strip().lower()
            if person and rel:
                cm.add_continuity_fact(
                    f"{person} is described as {rel}.",
                    confidence=min(0.75, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: explicit self-identity statements (name) ---
    try:
        # Examples:
        # - "My name is Brother Matthias."
        # - "My name is Matthias."
        m_name = re.search(
            r"\bmy\s+name\s+is\s+([A-Z][A-Za-z\-']{1,40}(?:\s+[A-Z][A-Za-z\-']{1,40}){0,3})\b",
            t,
            flags=re.IGNORECASE,
        )
        if m_name:
            nm = (m_name.group(1) or '').strip().strip('.')
            if nm and nm.lower() not in ['unknown', 'n/a', 'none']:
                cm.add_continuity_fact(
                    f"The narrator's name is {nm}.",
                    confidence=min(0.95, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: explicit mentor identity statements ---
    try:
        mentor_pat = re.search(
            r"\b(?:our|my)\s+mentor\s+is\s+([A-Z][a-z]{2,30})\b",
            t,
            flags=re.IGNORECASE,
        )
        if mentor_pat:
            mname = (mentor_pat.group(1) or '').strip()
            if mname and mname.lower() not in ['i', 'we', 'you', 'they', 'he', 'she', 'it']:
                cm.add_continuity_fact(
                    f"{mname} is described as the narrator's mentor.",
                    confidence=min(0.75, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: mentor/teacher + taught-us (only store when phrasing is explicit) ---
    try:
        if any(k in tl for k in ['taught us', 'taught me']) and any(k in tl for k in ['rune', 'runes', 'warding']):
            if any(k in tl for k in ['mentor', 'teacher', 'master', 'monk']):
                cm.add_continuity_fact(
                    "A mentor/teacher is remembered as having taught warding runes (name may be unclear).",
                    confidence=min(0.6, conf),
                    source=source,
                )
    except Exception:
        pass

    # Negative mentor statements (only store when phrasing is explicit)
    try:
        if 'mentor' in tl:
            neg_markers = [
                'never had',
                'no mentor',
                'without a mentor',
                'without any mentor',
                'never had a proper mentor',
            ]
            if any(m in tl for m in neg_markers):
                cm.add_continuity_fact(
                    "The narrator states they never had a proper mentor (self-reported).",
                    confidence=min(0.55, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: time-of-day / lighting cues ---
    try:
        lighting_patterns = [
            (r"\bbright\s+morning\b", "Lighting is described as bright morning light."),
            (r"\bmorning\s+light\b", "Lighting is described as morning light."),
            (r"\bmorning\s+brightness\b", "Lighting is described as morning brightness."),
            (r"\bmorning\s+glare\b", "Lighting is described as morning glare."),
            (r"\bmorning\s+sun\b", "Lighting is described as morning sun."),
            (r"\bmidday\s+sun\b", "Lighting is described as midday sun."),
            (r"\bdusk\b", "Time-of-day is described as dusk."),
            (r"\bmoonlight\b", "Lighting is described as moonlight."),
            (r"\bnight\b", "Time-of-day is described as night."),
        ]
        for pat, fact in lighting_patterns:
            if re.search(pat, tl):
                cm.add_continuity_fact(
                    fact,
                    confidence=min(0.65, conf),
                    source=source,
                )
    except Exception:
        pass




def _capture_dialogue_continuity_facts(text: str, *, speaker: str, source: str, base_confidence: float = 0.65, max_quotes: int = 2) -> None:
    try:
        import re
    except Exception:
        return
    t = (text or '').strip()
    sp = (speaker or '').strip()
    if not t or not sp:
        return
    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
        if cm is None or not hasattr(cm, 'add_continuity_fact'):
            return
    except Exception:
        return
    try:
        conf = float(base_confidence)
    except Exception:
        conf = 0.65
    conf = max(0.0, min(1.0, conf))

    quotes = []
    try:
        quotes.extend(re.findall(r'“([^”]{3,220})”', t))
    except Exception:
        pass
    try:
        quotes.extend(re.findall(r'"([^\"]{3,220})"', t))
    except Exception:
        pass

    if not quotes:
        return
    seen = set()
    captured = 0
    for q in quotes:
        qq = str(q or '').strip()
        if not qq:
            continue
        key = qq.lower()
        if key in seen:
            continue
        seen.add(key)
        cm.add_continuity_fact(f"{sp} said: \"{qq}\"", confidence=conf, source=source)
        captured += 1
        if captured >= max_quotes:
            break


# --- Continuity Fact Trace (debug proof tooling) ---
_FACT_TRACE_EVENTS: list[dict] = []

_FACT_LLM_ENABLED: bool = False
_FACT_LLM_MAX_CALLS_PER_MIN: int = 6
_FACT_LLM_CALL_TIMES: list[float] = []

# Mention system LLM extraction:
_MENTION_LLM_ENABLED: bool = False  # Enable LLM-based entity extraction for mentions (DISABLED: causing empty responses during init)
_MENTION_LLM_MAX_CALLS_PER_MIN: int = 10
_MENTION_LLM_CALL_TIMES: list[float] = []

# Continuity fact extraction mode:
# - 'heuristic': only local heuristics
# - 'hybrid': heuristics first, then optional LLM fallback if none added (requires _FACT_LLM_ENABLED)
# - 'llm': LLM-only (skip heuristics; still rate-limited)
_FACT_EXTRACTION_MODE: str = 'hybrid'




def _fact_llm_rate_limited() -> bool:
    try:
        import time as _time
        now = float(_time.time())
    except Exception:
        return True
    try:
        global _FACT_LLM_CALL_TIMES
        _FACT_LLM_CALL_TIMES = [t for t in (_FACT_LLM_CALL_TIMES or []) if (now - float(t)) <= 60.0]
        if len(_FACT_LLM_CALL_TIMES) >= int(_FACT_LLM_MAX_CALLS_PER_MIN):
            return True
        _FACT_LLM_CALL_TIMES.append(now)
        return False
    except Exception:
        return True




def _extract_continuity_facts_via_llm(text: str, *, source: str, base_confidence: float, max_facts: int = 6) -> list[dict]:
    try:
        from openrouter_config import OpenRouterConfig, robust_llm_call
        from json_utils import extract_and_parse_json
        from persistent_context_manager import get_context_manager
    except Exception:
        return []

    t = (text or '').strip()
    if not t:
        return []

    try:
        max_facts_i = max(0, min(10, int(max_facts)))
    except Exception:
        max_facts_i = 6
    if max_facts_i <= 0:
        return []

    try:
        base_conf = float(base_confidence)
    except Exception:
        base_conf = 0.6
    base_conf = max(0.0, min(1.0, base_conf))

    try:
        cm = get_context_manager()
        facts_block = cm.get_continuity_facts_for_llm(max_facts=10) if (cm is not None and hasattr(cm, 'get_continuity_facts_for_llm')) else ''
    except Exception:
        facts_block = ''

    # Detect whether the text contains proper-name candidates. If yes, we will
    # prefer facts that explicitly mention those names (to avoid generic facts
    # that don't anchor continuity).
    try:
        import re
        name_candidates = re.findall(r"\b[A-Z][a-z]{2,30}\b", t)
        name_candidates = [n for n in name_candidates if n.lower() not in ['i', 'we', 'you', 'they', 'he', 'she', 'it']]
        has_names = bool(name_candidates)
    except Exception:
        has_names = False

    prompt = (
        "You are extracting continuity facts for a simulation.\n"
        "Return ONLY JSON.\n\n"
        "Rules:\n"
        "- Extract only facts explicitly stated in the text.\n"
        "- Do NOT invent backstory, causes, or motivations.\n"
        "- Prefer stable anchors (relationships, roles, identity, location, time/lighting, possessions, injuries, promises, rules).\n"
        + ("- IMPORTANT: The text contains proper names. Prefer facts that explicitly include the name(s) and what they are/do/relate to. Avoid generic facts that omit names unless it is a time/lighting fact.\n" if has_names else "")
        + "- If a detail is uncertain/hedged in the text, keep confidence low.\n"
        "- Do not include more than " + str(max_facts_i) + " items.\n\n"
        "JSON schema:\n"
        "{\n  \"facts\": [\n    {\"fact\": \"...\", \"confidence\": 0.0, \"kind\": \"relationship|role|location|time|event|status|other\"}\n  ]\n}\n\n"
        "SOURCE: " + str(source) + "\n\n"
        + (facts_block + "\n\n" if facts_block else "")
        + "TEXT:\n" + t
    )

    try:
        client = OpenRouterConfig.create_client()
        model = OpenRouterConfig.get_model_for_role('coordination')
    except Exception:
        return []

    resp = robust_llm_call(
        client=client,
        messages=[{"role": "user", "content": prompt}],
        model=model,
        temperature=0.2,
        max_tokens=600,
        response_format={"type": "json_object"},
        call_name="continuity_fact_extraction",
    )
    if not resp:
        return []

    obj = extract_and_parse_json(resp)
    if not isinstance(obj, dict):
        return []
    facts = obj.get('facts')
    if not isinstance(facts, list):
        return []

    out: list[dict] = []
    seen = set()
    for f in facts:
        if not isinstance(f, dict):
            continue
        fact = str(f.get('fact', '') or '').strip()
        if not fact:
            continue

        # If the text contains names, drop generic (name-less) facts unless they
        # are explicitly time/lighting (we still want those anchors).
        try:
            kind_raw = str(f.get('kind', '') or '').strip().lower()
        except Exception:
            kind_raw = ''
        if has_names:
            try:
                has_name_in_fact = bool(re.search(r"\b[A-Z][a-z]{2,30}\b", fact))
            except Exception:
                has_name_in_fact = False
            if (not has_name_in_fact) and (kind_raw not in ['time']):
                continue

        key = fact.lower()
        if key in seen:
            continue
        seen.add(key)
        try:
            c = float(f.get('confidence', base_conf) or base_conf)
        except Exception:
            c = base_conf
        c = max(0.0, min(1.0, c))
        c = min(c, base_conf)
        kind = str(f.get('kind', '') or '').strip() or 'other'
        out.append({'fact': fact, 'confidence': c, 'kind': kind})
        if len(out) >= max_facts_i:
            break
    return out




def _trace_continuity_fact_capture(text: str, *, source: str, base_confidence: float) -> None:
    """Capture continuity facts and record which new facts were added (debug/proof).

    This allows validating that specific narrative streams (scene/perceptual/internal voice/exchange)
    are being processed into continuity facts.
    """
    try:
        from datetime import datetime
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
    except Exception:
        cm = None
        datetime = None

    before = []
    try:
        if cm is not None and hasattr(cm, 'context'):
            before = list(getattr(cm.context, 'continuity_facts', []) or [])
    except Exception:
        before = []

    before_set = set()
    try:
        for e in before:
            if isinstance(e, dict):
                f = str(e.get('fact', '') or '').strip().lower()
                if f:
                    before_set.add(f)
    except Exception:
        before_set = set()

    # 1) Heuristic pass (if enabled by mode)
    try:
        mode = str(_FACT_EXTRACTION_MODE or 'hybrid').strip().lower()
    except Exception:
        mode = 'hybrid'

    if mode in ['heuristic', 'hybrid']:
        try:
            _capture_continuity_facts_from_text(text, source=source, base_confidence=base_confidence)
        except Exception:
            pass

    after = []
    try:
        if cm is not None and hasattr(cm, 'context'):
            after = list(getattr(cm.context, 'continuity_facts', []) or [])
    except Exception:
        after = []

    added = []
    try:
        for e in after:
            if isinstance(e, dict):
                f = str(e.get('fact', '') or '').strip()
                if f and f.lower() not in before_set:
                    added.append(f)
    except Exception:
        added = []

    # 2) LLM pass (mode-dependent)
    try:
        allow_llm = False
        if mode == 'llm':
            allow_llm = True
        elif mode == 'hybrid':
            allow_llm = bool(_FACT_LLM_ENABLED)

        should_call_llm = False
        if mode == 'llm':
            should_call_llm = True
        elif mode == 'hybrid' and (not added):
            should_call_llm = True

        if should_call_llm and allow_llm and (not _fact_llm_rate_limited()):
            try:
                llm_facts = _extract_continuity_facts_via_llm(text, source=source, base_confidence=base_confidence)
            except Exception:
                llm_facts = []
            if llm_facts and cm is not None and hasattr(cm, 'add_continuity_fact'):
                for it in llm_facts:
                    try:
                        ff = str(it.get('fact', '') or '').strip()
                        if not ff:
                            continue
                        cc = float(it.get('confidence', base_confidence) or base_confidence)
                        cc = max(0.0, min(1.0, cc))
                        cm.add_continuity_fact(ff, confidence=cc, source=str(source or 'narrative') + "_llm")
                    except Exception:
                        continue

                try:
                    after2 = list(getattr(cm.context, 'continuity_facts', []) or []) if (cm is not None and hasattr(cm, 'context')) else []
                except Exception:
                    after2 = []
                added2 = []
                try:
                    for e in after2:
                        if isinstance(e, dict):
                            f = str(e.get('fact', '') or '').strip()
                            if f and f.lower() not in before_set:
                                added2.append(f)
                except Exception:
                    added2 = []
                if added2:
                    added = added2
    except Exception:
        pass

    try:
        snippet = (str(text or '').strip().replace('\n', ' '))
        if len(snippet) > 200:
            snippet = snippet[:200] + '...'
    except Exception:
        snippet = ''

    try:
        evt = {
            'ts': (datetime.now().isoformat() if datetime else ''),
            'source': str(source or ''),
            'base_confidence': float(base_confidence),
            'snippet': snippet,
            'added': list(added),
        }
        _FACT_TRACE_EVENTS.append(evt)
        # keep bounded
        if len(_FACT_TRACE_EVENTS) > 60:
            _FACT_TRACE_EVENTS[:] = _FACT_TRACE_EVENTS[-60:]
    except Exception:
        pass

    # --- MENTION EXTRACTION INTEGRATION ---
    try:
        _capture_mentioned_actors_from_text(text, source=source)
    except Exception:
        pass

    return




def _handle_debug_context_commands(user_input: str) -> bool:
    try:
        ui = (user_input or '').strip().lower()
    except Exception:
        return False
    if not (
        ui in ['/facts', '/ivlog', '/debugctx', '/factclear', '/facttrace', '/factllm', '/factllmstatus', '/factmode', '/factmodestatus', '/mentions', '/mentioned', '/mentionedactors', '/clearmention', '/clearmentions', '/mentionsclear']
        or ui.startswith('/factadd ')
        or ui.startswith('/factllm ')
        or ui.startswith('/factmode ')
    ):
        return False

    try:
        from persistent_context_manager import get_context_manager
        cm = get_context_manager()
    except Exception:
        cm = None

    if cm is None:
        print(f"{Color.WARNING}No persistent context manager available.{Color.RESET}")
        return True

    if ui == '/factclear':
        try:
            if hasattr(cm, 'context') and hasattr(cm.context, 'continuity_facts'):
                cm.context.continuity_facts = []
                if hasattr(cm, '_save'):
                    cm._save()
            try:
                global _FACT_TRACE_EVENTS
                _FACT_TRACE_EVENTS = []
            except Exception:
                pass
            print(f"{Color.SUCCESS}✓ Cleared continuity facts{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error clearing continuity facts: {e}{Color.RESET}")
        return True

    if ui.startswith('/factadd '):
        fact_text = (user_input or '')[len('/factadd '):].strip()
        if not fact_text:
            print(f"{Color.WARNING}Usage: /factadd <fact text>{Color.RESET}")
            return True
        try:
            if hasattr(cm, 'add_continuity_fact'):
                cm.add_continuity_fact(fact_text, confidence=0.9, source='debug')
                print(f"{Color.SUCCESS}✓ Added continuity fact{Color.RESET}")
            else:
                print(f"{Color.WARNING}Context manager does not support add_continuity_fact{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error adding continuity fact: {e}{Color.RESET}")
        return True

    if ui in ['/factllm', '/factllmstatus'] or ui.startswith('/factllm '):
        try:
            global _FACT_LLM_ENABLED
            arg = (user_input or '').strip()[len('/factllm'):].strip().lower() if ui.startswith('/factllm') else ''
            if arg in ['on', 'true', '1', 'enable', 'enabled']:
                _FACT_LLM_ENABLED = True
            elif arg in ['off', 'false', '0', 'disable', 'disabled']:
                _FACT_LLM_ENABLED = False

            try:
                enabled = bool(_FACT_LLM_ENABLED)
            except Exception:
                enabled = False
            try:
                limit = int(_FACT_LLM_MAX_CALLS_PER_MIN)
            except Exception:
                limit = 0
            print(f"{Color.SYSTEM}Fact LLM extraction: {'ON' if enabled else 'OFF'} (rate limit: {limit}/min){Color.RESET}")
            if not enabled:
                print(f"{Color.SYSTEM}Use: /factllm on  (or /factllm off){Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error toggling fact LLM mode: {e}{Color.RESET}")
        return True

    if ui in ['/factmode', '/factmodestatus'] or ui.startswith('/factmode '):
        try:
            global _FACT_EXTRACTION_MODE
            arg = (user_input or '').strip()[len('/factmode'):].strip().lower() if ui.startswith('/factmode') else ''
            if arg in ['heuristic', 'hybrid', 'llm']:
                _FACT_EXTRACTION_MODE = arg
            mode = str(_FACT_EXTRACTION_MODE or 'hybrid').strip().lower()
            print(f"{Color.SYSTEM}Fact extraction mode: {mode}{Color.RESET}")
            if mode == 'hybrid':
                try:
                    enabled = bool(_FACT_LLM_ENABLED)
                except Exception:
                    enabled = False
                print(f"{Color.SYSTEM}Hybrid mode LLM fallback: {'ON' if enabled else 'OFF'} (toggle with /factllm on|off){Color.RESET}")
            print(f"{Color.SYSTEM}Use: /factmode heuristic | /factmode hybrid | /factmode llm{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error setting fact extraction mode: {e}{Color.RESET}")
        return True

    if ui == '/facttrace':
        try:
            print(f"\n{Color.SYSTEM}{'=' * 8}{Color.RESET}")
            print(f"{Color.SYSTEM}Fact Capture Trace{Color.RESET}")
            print(f"{Color.SYSTEM}{'=' * 8}{Color.RESET}")
            if not _FACT_TRACE_EVENTS:
                print(f"{Color.SYSTEM}(none){Color.RESET}")
            else:
                for e in _FACT_TRACE_EVENTS[-20:]:
                    ts = str(e.get('ts', '') or '')
                    src = str(e.get('source', '') or '')
                    sn = str(e.get('snippet', '') or '')
                    added = list(e.get('added', []) or [])
                    if added:
                        print(f"{Color.SYSTEM}- [{ts}] {src}: +{len(added)} fact(s) | {sn}{Color.RESET}")
                        for f in added[:6]:
                            print(f"{Color.SYSTEM}    - {f}{Color.RESET}")
                    else:
                        print(f"{Color.SYSTEM}- [{ts}] {src}: +0 | {sn}{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error printing fact trace: {e}{Color.RESET}")
        return True

    if ui in ['/mentions', '/mentioned', '/mentionedactors']:
        try:
            print(f"\n{Color.HEADER}{'═' * 60}{Color.RESET}")
            print(f"{Color.INFO}🧩 MENTIONED ACTORS (leads to follow up on){Color.RESET}")
            print(f"{Color.HEADER}{'═' * 60}{Color.RESET}")
            mentioned = []
            try:
                mentioned = cm.get_mentioned_actors() if cm else []
            except Exception:
                mentioned = []
            if not mentioned:
                print(f"{Color.SYSTEM}   (none tracked yet){Color.RESET}")
            else:
                # Group by location for cleaner display
                by_location = {}
                unknown_loc = []
                for e in mentioned:
                    try:
                        nm = str(e.get('name', '') or '').strip()
                        if not nm:
                            continue
                        try:
                            tags = list(e.get('location_tags') or [])
                        except Exception:
                            tags = []
                        tags = [str(t).strip() for t in tags if str(t).strip()]

                        # Format the name
                        low = nm.lower()
                        if low.startswith('role:'):
                            display_name = f"(role) {nm.split(':', 1)[1].strip()}" if ':' in nm else nm
                        else:
                            display_name = nm

                        # Get sources
                        sources = list(e.get('sources') or [])
                        source_text = f" [{', '.join(sources[:2])}]" if sources else ""

                        if tags:
                            for tag in tags:
                                if tag not in by_location:
                                    by_location[tag] = []
                                by_location[tag].append(f"{display_name}{source_text}")
                        else:
                            unknown_loc.append(f"{display_name}{source_text}")
                    except Exception:
                        continue

                # Display grouped by location
                for loc, actors in sorted(by_location.items()):
                    print(f"\n{Color.SUCCESS}📍 {loc.title()}{Color.RESET}")
                    for actor in actors:
                        print(f"   • {actor}")

                if unknown_loc:
                    print(f"\n{Color.WARNING}❓ Unknown Location{Color.RESET}")
                    for actor in unknown_loc:
                        print(f"   • {actor}")

                print(f"\n{Color.SYSTEM}Total: {len(mentioned)} mentioned actor(s){Color.RESET}")
            print(f"{Color.HEADER}{'═' * 60}{Color.RESET}")
            print(f"{Color.SYSTEM}Use /clearmention to clear all | /debug for more context{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error displaying mentioned actors: {e}{Color.RESET}")
        return True

    if ui in ['/clearmention', '/clearmentions', '/mentionsclear']:
        try:
            _clear_mentioned_actors()
            print(f"{Color.SUCCESS}✓ Cleared all mentioned actors{Color.RESET}")
        except Exception as e:
            print(f"{Color.ERROR}Error clearing mentioned actors: {e}{Color.RESET}")
        return True

    if ui in ['/facts', '/debugctx']:
        try:
            facts_block = cm.get_continuity_facts_for_llm(max_facts=25) if hasattr(cm, 'get_continuity_facts_for_llm') else ''
        except Exception:
            facts_block = ''
        print(f"\n{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        print(f"{Color.SYSTEM}Continuity Facts{Color.RESET}")
        print(f"{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        if facts_block:
            print(f"{Color.SYSTEM}{facts_block}{Color.RESET}")
        else:
            print(f"{Color.SYSTEM}(none){Color.RESET}")

    if ui in ['/ivlog', '/debugctx']:
        try:
            items = cm.get_recent_internal_voices(count=10) if hasattr(cm, 'get_recent_internal_voices') else []
        except Exception:
            items = []
        print(f"\n{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        print(f"{Color.SYSTEM}Recent Internal Voices{Color.RESET}")
        print(f"{Color.SYSTEM}{'=' * 8}{Color.RESET}")
        if items:
            for e in items:
                voice = str(e.get('voice', '')).strip()
                ts = str(e.get('timestamp', '')).strip()
                ua = str(e.get('user_action', '')).strip()
                if ua:
                    print(f"{Color.SYSTEM}- [{ts}] ({ua}) {voice}{Color.RESET}")
                else:
                    print(f"{Color.SYSTEM}- [{ts}] {voice}{Color.RESET}")
        else:
            print(f"{Color.SYSTEM}(none){Color.RESET}")

    return True

    # --- Anchor: last-known / last-seen location statements (generic) ---
    # Examples:
    # - "Matteo was last seen at the archive"
    # - "I last saw Matteo in the archive"
    # - "Matteo is said to be in the archive"
    # These are treated as leads unless the phrasing is extremely explicit.
    try:
        person_patterns = [
            r"\b([A-Z][a-z]{2,20})\b\s+was\s+last\s+seen\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
            r"\blast\s+saw\s+\b([A-Z][a-z]{2,20})\b\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
            r"\b([A-Z][a-z]{2,20})\b\s+(?:is|was)\s+said\s+to\s+be\s+(?:in|at|near)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})",
        ]
        for pat in person_patterns:
            m = re.search(pat, t)
            if not m:
                continue
            person = (m.group(1) or '').strip()
            place = (m.group(2) or '').strip().rstrip('.').strip()
            if person and place:
                cm.add_continuity_fact(
                    f"{person} was last reported at/near {place} (lead).",
                    confidence=min(0.7, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: explicit "X is in/at Y" (high risk; keep conservative) ---
    # Only treat as high confidence if phrasing is direct and not hedged.
    try:
        direct_loc = re.search(r"\b(Matteo)\b\s+is\s+(?:in|at)\s+the\s+([A-Za-z][A-Za-z\s\-']{2,60})", t)
        if direct_loc and not any(w in tl for w in ["maybe", "might", "unclear", "not sure", "seems", "said to", "rumor"]):
            place = (direct_loc.group(2) or '').strip().rstrip('.').strip()
            if place:
                cm.add_continuity_fact(
                    f"Matteo is stated to be in {place}.",
                    confidence=min(0.85, conf),
                    source=source,
                )
    except Exception:
        pass

    # --- Anchor: time/distance-to-destination statements ---
    # Examples:
    # - "10 minutes to the archive"
    # - "about 2 km from the archive"
    # - "a short walk to the archive"
    try:
        # minutes/hours
        m_time = re.search(r"\b(\d{1,3})\s*(minutes|minute|hours|hour)\b[^\n\.]{0,50}\bto\b[^\n\.]{0,10}\bthe\b\s+([A-Za-z][A-Za-z\s\-']{2,60})", tl)
        if m_time:
            qty = m_time.group(1)
            unit = m_time.group(2)
            dest = (m_time.group(3) or '').strip().rstrip('.').strip()
            if dest:
                cm.add_continuity_fact(
                    f"Estimated travel time to {dest}: {qty} {unit}.",
                    confidence=min(0.8, conf),
                    source=source,
                )

        # meters/km
        m_dist = re.search(r"\b(\d{1,3}(?:\.\d+)?)\s*(km|kilometers|kilometres|m|meters|metres)\b[^\n\.]{0,50}\bfrom\b[^\n\.]{0,10}\bthe\b\s+([A-Za-z][A-Za-z\s\-']{2,60})", tl)
        if m_dist:
            qty = m_dist.group(1)
            unit = m_dist.group(2)
            dest = (m_dist.group(3) or '').strip().rstrip('.').strip()
            if dest:
                cm.add_continuity_fact(
                    f"Estimated distance from {dest}: {qty} {unit}.",
                    confidence=min(0.75, conf),
                    source=source,
                )

        # qualitative
        if ('walk' in tl or 'stroll' in tl or 'short' in tl) and 'to the archive' in tl:
            cm.add_continuity_fact(
                "The archive is described as within walking distance (qualitative).",
                confidence=min(0.65, conf),
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: uncertainty markers ---
    # If the authoritative text says it's unclear, store that explicitly.
    try:
        uncertainty_markers = [
            "unclear",
            "not sure",
            "can't tell",
            "unknown",
            "no one knows",
            "conflicting",
        ]
        if any(u in tl for u in uncertainty_markers) and ('archive' in tl or 'matteo' in tl):
            cm.add_continuity_fact(
                "Key details about Matteo/archive are described as uncertain in the current narration.",
                confidence=0.6,
                source=source,
            )
    except Exception:
        pass

    # --- Anchor: Archive spatial relation (above/below) ---
    # We only record if the text explicitly states a direction.
    try:
        below_patterns = [
            r"\barchive\b[^\n\.]{0,80}\bbelow\b",
            r"\bbelow\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bdownstairs\b",
            r"\bdownstairs\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\blower level\b",
        ]
        above_patterns = [
            r"\barchive\b[^\n\.]{0,80}\babove\b",
            r"\babove\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bupstairs\b",
            r"\bupstairs\b[^\n\.]{0,80}\barchive\b",
            r"\barchive\b[^\n\.]{0,80}\bupper level\b",
        ]

        saw_below = any(re.search(p, tl, flags=re.IGNORECASE) for p in below_patterns)
        saw_above = any(re.search(p, tl, flags=re.IGNORECASE) for p in above_patterns)

        if saw_below:
            cm.add_continuity_fact(
                "The archive is described as below the current area.",
                confidence=min(0.85, conf),
                source=source,
            )
        if saw_above:
            cm.add_continuity_fact(
                "The archive is described as above the current area.",
                confidence=min(0.85, conf),
                source=source,
            )

        # Conflict note (prevents flip-flopping certainty)
        if saw_below and saw_above:
            cm.add_continuity_fact(
                "The archive's relative position is conflicting (both above and below were stated); treat as uncertain.",
                confidence=0.55,
                source=source,
            )
    except Exception:
        pass




def track_dialogue_exchange(speaker: str, listener: str, statement: str, statement_type: str = "statement", topic: str = None):
    """
    Track a dialogue exchange for conversation continuity.
    """
    if not DIALOGUE_CONTEXT_AVAILABLE or _dialogue_context is None:
        return
    
    try:
        _dialogue_context.add_exchange(speaker, listener, statement, statement_type, topic)
    except Exception:
        pass




def get_dialogue_context(actor1: str, actor2: str) -> Optional[Dict]:
    """
    Get conversation context between two actors.
    
    Returns dict with conversation history, topics, promises, etc.
    """
    if not DIALOGUE_CONTEXT_AVAILABLE or _dialogue_context is None:
        return None
    
    try:
        return _dialogue_context.get_context(actor1, actor2)
    except Exception:
        return None




def _get_nua_actions_context(tracker, ua_actor_id: str = None) -> str:
    """
    Get recent NUA autonomous actions for perceptual context.
    These are actions that happened and can be perceived by the UA.
    
    Args:
        tracker: The tracker agent
        ua_actor_id: The UA's actor ID to exclude from results
        
    Returns:
        Formatted string of recent NUA actions, or empty string if none
    """
    if not tracker:
        return ""
    
    try:
        if hasattr(tracker, 'get_all_recent_nua_actions'):
            return tracker.get_all_recent_nua_actions(exclude_actor_id=ua_actor_id, limit=5)
    except Exception:
        pass
    
    return ""

# Integrate SPARK into current scene with a narrative bridge for continuity

