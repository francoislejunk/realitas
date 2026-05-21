"""
Worldbuilding Helper Functions

Utilities for extracting worldbuilding information from the RAG system.
"""

import re
import random
from typing import Optional, Tuple, List
from WORLD_BUILDER.worldbuilding_rag import WorldbuildingRAGSystem, WorldbuildingCategory

from pathlib import Path
import json

try:
    from context_store import ContextStore
except Exception:
    ContextStore = None


def extract_time_period_from_rag(rag_system: WorldbuildingRAGSystem) -> Optional[str]:
    """
    Extract the time period name from the RAG worldbuilding system.
    
    The time period is a descriptive string (e.g., "Mid-1960s to Mid-1970s")
    that the UA Creator uses to select an appropriate simulation year.
    
    Args:
        rag_system: The WorldbuildingRAGSystem instance
        
    Returns:
        Time period name string, or None if not found
        
    Example:
        >>> period = extract_time_period_from_rag(rag_system)
        >>> print(period)  # "Mid-1960s to Mid-1970s"
    """
    if not rag_system:
        return None

    try:
        context = rag_system.get_context_for_llm(
            query="TIME PERIOD timeline temporal era",
            max_tokens=800
        )

        if context:
            # Look for "TIME PERIOD: <name>" pattern
            period_match = re.search(r'TIME PERIOD:\s*([^\n]+)', context, re.IGNORECASE)
            if period_match:
                period_name = period_match.group(1).strip()
                print(f"✓ Extracted time period from RAG: {period_name}")
                return period_name

        return None

    except Exception as e:
        print(f"⚠️  Failed to extract time period from RAG: {e}")
        return None


def _generated_cities_registry_path() -> Path:
    # Repo root is the parent of this file.
    root = Path(__file__).resolve().parent
    return root / "simulation_data" / "generated_cities.json"


def _get_context_store_safe() -> Optional['ContextStore']:
    if ContextStore is None:
        return None
    try:
        return ContextStore(Path("simulation_data/context/context.db"))
    except Exception:
        return None


def _get_session_id_safe() -> str:
    # IMPORTANT: do NOT create new TrackerAgent or new context manager here,
    # because that would generate a new session_id and cause cross-session bleed.
    try:
        import persistent_context_manager as _pcm
        gcm = getattr(_pcm, '_global_context_manager', None)
        if gcm is not None:
            sid = getattr(gcm, 'session_id', None)
            if sid:
                return str(sid)
            try:
                ctx = getattr(gcm, 'context', None)
                sid2 = getattr(ctx, 'session_id', None) if ctx is not None else None
                if sid2:
                    return str(sid2)
            except Exception:
                pass
    except Exception:
        pass

    try:
        import spatial_context_system as _scs
        sm = getattr(_scs, '_spatial_manager', None)
        if sm is not None:
            sid = getattr(sm, 'session_id', None)
            if sid:
                return str(sid)
    except Exception:
        pass

    # Project-wide convention when nothing else is available.
    return 'default'


def load_generated_cities() -> List[str]:
    """Load per-run generated cities.

    These cities are treated as canon/grounded for the current run.
    """
    # Prefer SQLite (ContextStore) so canon survives long-term.
    try:
        store = _get_context_store_safe()
        if store is not None:
            events = store.get_world_events_by_type(
                session_id=_get_session_id_safe(),
                event_type='CANON_CITY',
                limit=500,
            )
            out: List[str] = []
            for e in events or []:
                payload = (e.get('payload') or {}) if isinstance(e, dict) else {}
                nm = payload.get('city') or payload.get('name') or payload.get('city_name')
                if isinstance(nm, str) and nm.strip():
                    out.append(nm.strip())
            # Older JSON fallback entries (merge)
            try:
                p = _generated_cities_registry_path()
                if p.exists():
                    data = json.loads(p.read_text(encoding="utf-8") or "[]")
                    if isinstance(data, list):
                        out.extend([str(x).strip() for x in data if isinstance(x, str) and str(x).strip()])
            except Exception:
                pass
            # Dedup (case-insensitive)
            seen = set()
            dedup: List[str] = []
            for c in out:
                cl = c.lower()
                if cl in seen:
                    continue
                seen.add(cl)
                dedup.append(c)
            return dedup
    except Exception:
        pass

    # Fallback: JSON
    p = _generated_cities_registry_path()
    try:
        if not p.exists():
            return []
        data = json.loads(p.read_text(encoding="utf-8") or "[]")
        if not isinstance(data, list):
            return []
        out: List[str] = []
        for x in data:
            if isinstance(x, str) and x.strip():
                out.append(x.strip())
        return out
    except Exception:
        return []


def save_generated_cities(cities: List[str]) -> None:
    p = _generated_cities_registry_path()
    try:
        p.parent.mkdir(parents=True, exist_ok=True)
        # Deduplicate case-insensitively but preserve first-seen casing.
        seen = set()
        out: List[str] = []
        for c in (cities or []):
            if not isinstance(c, str):
                continue
            s = c.strip()
            if not s:
                continue
            sl = s.lower()
            if sl in seen:
                continue
            seen.add(sl)
            out.append(s)
        p.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    except Exception:
        return None


def register_generated_city(city_name: str) -> None:
    """Register a city as canon for this run."""
    s = (city_name or '').strip()
    if not s:
        return None
    # Prefer SQLite persistence.
    try:
        store = _get_context_store_safe()
        if store is not None:
            # Dedupe: if already present for this session, do nothing.
            try:
                existing = load_generated_cities()
                if any((c or '').strip().lower() == s.lower() for c in (existing or [])):
                    return None
            except Exception:
                pass
            store.log_world_event(
                session_id=_get_session_id_safe(),
                location_id=None,
                event_type='CANON_CITY',
                summary=f"Canon city established: {s}",
                importance=8,
                tags=['canon', 'city'],
                payload={'city': s, 'city_name': s},
                world_time=None,
            )
            return None
    except Exception:
        pass

    # Fallback: JSON
    cities = load_generated_cities()
    cities.append(s)
    save_generated_cities(cities)


def _common_place_types_registry_path() -> Path:
    root = Path(__file__).resolve().parent
    return root / "simulation_data" / "common_place_types.json"


def load_common_place_types() -> dict[str, list[str]]:
    """Load dynamic common-place types.

    Returned dict maps canonical key -> list of synonyms.
    SQLite (ContextStore) is preferred for durability.
    """
    # Prefer SQLite
    try:
        store = _get_context_store_safe()
        if store is not None:
            events = store.get_world_events_by_type(
                session_id=_get_session_id_safe(),
                event_type='CANON_COMMON_PLACE_TYPE',
                limit=500,
            )
            out: dict[str, list[str]] = {}
            for e in events or []:
                payload = (e.get('payload') or {}) if isinstance(e, dict) else {}
                key = str(payload.get('key') or payload.get('type') or '').strip().lower()
                syns = payload.get('synonyms') or payload.get('syns') or []
                if not key:
                    continue
                if isinstance(syns, str):
                    syn_list = [p.strip().lower() for p in syns.split(',') if p.strip()]
                elif isinstance(syns, list):
                    syn_list = [str(p).strip().lower() for p in syns if str(p).strip()]
                else:
                    syn_list = []
                if syn_list:
                    # Merge with existing
                    cur = out.get(key, [])
                    for s in syn_list:
                        if s not in cur:
                            cur.append(s)
                    out[key] = cur

            # Merge JSON fallback
            try:
                p = _common_place_types_registry_path()
                if p.exists():
                    data = json.loads(p.read_text(encoding='utf-8') or '{}')
                    if isinstance(data, dict):
                        for k, v in data.items():
                            kk = str(k).strip().lower()
                            if not kk:
                                continue
                            if isinstance(v, list):
                                vv = [str(x).strip().lower() for x in v if str(x).strip()]
                            elif isinstance(v, str):
                                vv = [p.strip().lower() for p in v.split(',') if p.strip()]
                            else:
                                vv = []
                            if not vv:
                                continue
                            cur = out.get(kk, [])
                            for s in vv:
                                if s not in cur:
                                    cur.append(s)
                            out[kk] = cur
            except Exception:
                pass

            return out
    except Exception:
        pass

    # Fallback JSON only
    try:
        p = _common_place_types_registry_path()
        if not p.exists():
            return {}
        data = json.loads(p.read_text(encoding='utf-8') or '{}')
        if not isinstance(data, dict):
            return {}
        out: dict[str, list[str]] = {}
        for k, v in data.items():
            kk = str(k).strip().lower()
            if not kk:
                continue
            if isinstance(v, list):
                out[kk] = [str(x).strip().lower() for x in v if str(x).strip()]
            elif isinstance(v, str):
                out[kk] = [p.strip().lower() for p in v.split(',') if p.strip()]
        return out
    except Exception:
        return {}


def register_common_place_type(key: str, synonyms: list[str]) -> None:
    """Persist a common-place type for dynamic travel inference."""
    k = (key or '').strip().lower()
    if not k:
        return None
    syns = [str(s).strip().lower() for s in (synonyms or []) if str(s).strip()]
    if not syns:
        return None

    # Dedupe: only persist if this adds something new.
    try:
        existing = load_common_place_types() or {}
        cur = existing.get(k, []) if isinstance(existing, dict) else []
        cur_l = [str(x).strip().lower() for x in (cur or []) if str(x).strip()]
        add = [s for s in syns if s not in cur_l]
        if not add:
            return None
        syns = sorted(set(cur_l + add))
    except Exception:
        pass

    # Prefer SQLite
    try:
        store = _get_context_store_safe()
        if store is not None:
            store.log_world_event(
                session_id=_get_session_id_safe(),
                location_id=None,
                event_type='CANON_COMMON_PLACE_TYPE',
                summary=f"Common place type established: {k}",
                importance=7,
                tags=['canon', 'common_place_type', 'travel'],
                payload={'key': k, 'synonyms': syns},
                world_time=None,
            )
            return None
    except Exception:
        pass

    # Fallback JSON
    try:
        p = _common_place_types_registry_path()
        p.parent.mkdir(parents=True, exist_ok=True)
        data = {}
        if p.exists():
            try:
                data = json.loads(p.read_text(encoding='utf-8') or '{}')
            except Exception:
                data = {}
        if not isinstance(data, dict):
            data = {}
        cur = data.get(k)
        if isinstance(cur, list):
            merged = [str(x).strip().lower() for x in cur if str(x).strip()]
        elif isinstance(cur, str):
            merged = [p.strip().lower() for p in cur.split(',') if p.strip()]
        else:
            merged = []
        for s in syns:
            if s not in merged:
                merged.append(s)
        data[k] = merged
        p.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        return None


def get_simulation_year() -> int:
    """
    Get the canonical simulation year.
    
    The simulation year is set when the UA is created and stored in ActorSheet.
    This is the single source of truth for all systems.
    
    Returns:
        The simulation year as an integer
        
    Example:
        >>> year = get_simulation_year()
        >>> print(year)  # 1968 (from UA actor sheet)
    """
    from actor_sheet import ActorSheet
    return ActorSheet.get_simulation_year()


def extract_current_year_from_rag(rag_system: WorldbuildingRAGSystem) -> Optional[int]:
    """
    Extract a default year from RAG worldbuilding context.
    
    This is used ONLY for initial setup before the UA is created.
    Once the UA is created, their simulation_year becomes canonical.
    
    Args:
        rag_system: The WorldbuildingRAGSystem instance
        
    Returns:
        A year from the time period, or None if not found
    """
    if not rag_system:
        return None
    
    try:
        def _extract_years(text: str) -> list[int]:
            if not text:
                return []
            # Prefer years mentioned on a TIME PERIOD line if present.
            # Examples:
            # - "TIME PERIOD: The Dark Medieval World, 1242"
            # - "TIME PERIOD: The Dark Medieval World, 1230-1250"
            tp_range_match = re.search(
                r"TIME\s*PERIOD\s*:\s*[^\n]*?(\d{4})\s*[-–]\s*(\d{4})",
                text,
                re.IGNORECASE,
            )
            if tp_range_match:
                try:
                    y0 = int(tp_range_match.group(1))
                    y1 = int(tp_range_match.group(2))
                    years = [y0, y1]
                    years = [y for y in years if 1000 <= y <= 2999]
                    if len(years) == 2:
                        return sorted(years)
                except Exception:
                    pass

            tp_single_match = re.search(r"TIME\s*PERIOD\s*:\s*[^\n]*?(\d{4})", text, re.IGNORECASE)
            if tp_single_match:
                try:
                    y = int(tp_single_match.group(1))
                    if 1000 <= y <= 2999:
                        return [y]
                except Exception:
                    pass
            # Match 4-digit years (supports medieval and modern eras)
            matches = re.findall(r"\b(\d{4})\b", text)
            years: list[int] = []
            for m in matches:
                try:
                    years.append(int(m))
                except Exception:
                    continue
            # Filter to a sane range for the sim (still allows 1242)
            years = [y for y in years if 1000 <= y <= 2999]
            return sorted(set(years))

        # Prefer the dedicated TEMPORAL category so retrieval doesn't miss the year.
        context = rag_system.get_context_for_llm(
            query="TIME PERIOD",
            max_tokens=800,
            category_filter=WorldbuildingCategory.TEMPORAL,
            include_related=False,
        )

        years = _extract_years(context)
        if years:
            if len(years) >= 2:
                start_year = min(years)
                end_year = max(years)
                selected_year = random.randint(start_year, end_year)
                print(f"✓ Extracted year range {start_year}-{end_year} from RAG time period; selected {selected_year}")
                return selected_year
            selected_year = years[0]
            print(f"✓ Extracted year {selected_year} from RAG time period")
            return selected_year

        # Fallback: scan stored docs (useful if embeddings/search fail for some reason).
        try:
            docs_obj = getattr(rag_system, "documents", {}) or {}
            docs_iter = []
            if isinstance(docs_obj, dict):
                docs_iter = list(docs_obj.values())
            elif isinstance(docs_obj, list):
                docs_iter = docs_obj
            else:
                docs_iter = []

            temporal_years: list[int] = []
            for doc in docs_iter:
                if getattr(doc, "category", None) == WorldbuildingCategory.TEMPORAL:
                    temporal_years.extend(_extract_years(getattr(doc, "content", "")))

            temporal_years = sorted(set([y for y in temporal_years if 1000 <= y <= 2999]))
            if temporal_years:
                if len(temporal_years) >= 2:
                    start_year = min(temporal_years)
                    end_year = max(temporal_years)
                    selected_year = random.randint(start_year, end_year)
                    print(f"✓ Extracted year range {start_year}-{end_year} from RAG temporal documents; selected {selected_year}")
                    return selected_year
                selected_year = temporal_years[0]
                print(f"✓ Extracted year {selected_year} from RAG temporal documents")
                return selected_year
        except Exception:
            pass

        # Last resort: try an unfiltered query.
        context = rag_system.get_context_for_llm(
            query="TIME PERIOD year era timeline",
            max_tokens=800,
        )
        years = _extract_years(context)
        if years:
            if len(years) >= 2:
                start_year = min(years)
                end_year = max(years)
                selected_year = random.randint(start_year, end_year)
                print(f"✓ Extracted year range {start_year}-{end_year} from RAG; selected {selected_year}")
                return selected_year
            selected_year = years[0]
            print(f"✓ Extracted year {selected_year} from RAG")
            return selected_year

        return None
        
    except Exception as e:
        print(f"⚠️  Failed to extract year from RAG: {e}")
        return None


def extract_year_range_from_rag(rag_system: WorldbuildingRAGSystem) -> Optional[Tuple[int, int]]:
    if not rag_system:
        return None

    try:
        context = rag_system.get_context_for_llm(
            query="TIME PERIOD",
            max_tokens=800,
            category_filter=WorldbuildingCategory.TEMPORAL,
            include_related=False,
        )

        def _parse_range(text: str) -> Optional[Tuple[int, int]]:
            if not text:
                return None
            m = re.search(
                r"TIME\s*PERIOD\s*:\s*[^\n]*?(\d{4})\s*[-–]\s*(\d{4})",
                text,
                re.IGNORECASE,
            )
            if not m:
                return None
            y0 = int(m.group(1))
            y1 = int(m.group(2))
            if not (1000 <= y0 <= 2999 and 1000 <= y1 <= 2999):
                return None
            return (min(y0, y1), max(y0, y1))

        parsed = _parse_range(context)
        if parsed:
            return parsed

        # Fallback: scan stored docs (useful when embeddings/search misses the TIME PERIOD line).
        try:
            docs_obj = getattr(rag_system, "documents", {}) or {}
            if isinstance(docs_obj, dict):
                docs_iter = list(docs_obj.values())
            elif isinstance(docs_obj, list):
                docs_iter = docs_obj
            else:
                docs_iter = []

            for doc in docs_iter:
                try:
                    if getattr(doc, "category", None) != WorldbuildingCategory.TEMPORAL:
                        continue
                    parsed = _parse_range(getattr(doc, "content", "") or "")
                    if parsed:
                        return parsed
                except Exception:
                    continue
        except Exception:
            pass

        return None
    except Exception:
        return None


def get_temporal_context(rag_system: WorldbuildingRAGSystem) -> str:
    """
    Get the full temporal context from RAG worldbuilding.
    
    Args:
        rag_system: The WorldbuildingRAGSystem instance
        
    Returns:
        Temporal context string describing the time period
    """
    if not rag_system:
        return "Unknown time period"
    
    try:
        context = rag_system.get_context_for_llm(
            query="current year timeline temporal history era period",
            max_tokens=500
        )
        return context if context else "Unknown time period"
    except Exception:
        return "Unknown time period"
