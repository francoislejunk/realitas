from typing import Dict, Any

import json
import os
from pathlib import Path

# Lightweight in-memory registry for INUA object states
# Keyed by object name (string). Each entry is a dict with:
# {
#   'name': <str>,
#   'statuses': { 'STAMINA': int, 'SPIRIT': int, 'SUPPLY': int, ... }
# }

_registry: Dict[str, Dict[str, Any]] = {}

# Default on-disk registry path (override with env INUA_REGISTRY_PATH)
DEFAULT_REGISTRY_PATH = os.environ.get("INUA_REGISTRY_PATH", "inua_registry.json")


def get_session_registry_path(session_id: str) -> str:
    """Return the default per-session INUA registry path."""
    sid = str(session_id or 'default').strip() or 'default'
    p = Path(f"sessions/{sid}/inua_registry.json")
    p.parent.mkdir(parents=True, exist_ok=True)
    return str(p)


def load_registry_for_session(session_id: str) -> None:
    """Load INUA registry state for a given session id (best-effort)."""
    try:
        load_registry(get_session_registry_path(session_id))
    except Exception:
        return


def save_registry_for_session(session_id: str) -> str:
    """Save INUA registry state for a given session id (best-effort)."""
    try:
        return save_registry(get_session_registry_path(session_id))
    except Exception:
        return ""


def _sanitize_status_label(label: str) -> str:
    try:
        return str(label).upper()
    except Exception:
        return 'STAMINA'


def get_object_state(object_name: str) -> Dict[str, Any]:
    """
    Get (or create) the registry record for this object.
    Returns a dict with 'name' and 'statuses' mapping.
    """
    if not object_name:
        object_name = 'Object'
    rec = _registry.get(object_name)
    if rec is None:
        rec = {'name': object_name, 'statuses': {}}
        _registry[object_name] = rec
    return rec


def get_status(object_name: str, status_label: str, default: int = 3) -> int:
    rec = get_object_state(object_name)
    statuses = rec.setdefault('statuses', {})
    label = _sanitize_status_label(status_label)
    return int(statuses.get(label, default))


def set_status(object_name: str, status_label: str, value: int) -> None:
    rec = get_object_state(object_name)
    statuses = rec.setdefault('statuses', {})
    label = _sanitize_status_label(status_label)
    # Clamp to 0..5 per UTAS status bounds
    clamped = max(0, min(5, int(value)))
    statuses[label] = clamped


def merge_object_state(object_state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge an externally provided object_state into the registry (e.g., from older code paths).
    Returns the updated registry record.
    """
    if not object_state:
        return {}
    name = object_state.get('name') or 'Object'
    rec = get_object_state(name)
    ext_statuses = object_state.get('statuses') or {}
    for k, v in ext_statuses.items():
        try:
            set_status(name, k, int(v))
        except Exception:
            continue
    return rec


def save_registry(path: str = DEFAULT_REGISTRY_PATH) -> str:
    """
    Persist the in-memory INUA registry to a JSON file for cross-run persistence.
    Uses an atomic write (temp file + replace) to avoid partial writes.
    Returns the final path written.
    """
    if not path:
        path = DEFAULT_REGISTRY_PATH
    dir_name = os.path.dirname(path)
    if dir_name:
        os.makedirs(dir_name, exist_ok=True)

    tmp_path = f"{path}.tmp"
    # Dump a JSON-serializable view directly
    with open(tmp_path, 'w', encoding='utf-8') as f:
        json.dump(_registry, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, path)
    return path


def load_registry(path: str = DEFAULT_REGISTRY_PATH) -> None:
    """
    Load the INUA registry from a JSON file if it exists. This replaces the in-memory
    registry content and sanitizes status labels/values through set_status for safety.
    """
    global _registry
    if not path or not os.path.exists(path):
        return
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return
        # Rebuild registry through public setters to enforce clamping and label normalization
        _registry = {}
        for name, rec in data.items():
            try:
                statuses = (rec or {}).get('statuses') or {}
                # Ensure the object entry exists
                get_object_state(name)
                for k, v in statuses.items():
                    try:
                        set_status(name, k, int(v))
                    except Exception:
                        continue
            except Exception:
                continue
    except Exception:
        # On any load error, leave the in-memory registry as-is
        return


def clear_registry() -> None:
    _registry.clear()
