from __future__ import annotations
from typing import Any, Optional, Union

try:
    # Local import to avoid heavy circulars at import time
    from actor_sheet import SFactorType
except Exception:
    SFactorType = None  # type: ignore

# Canonical S-Factor label normalization map
_SFACTOR_LABELS = {
    # Canonical
    "swiftness": "Swiftness",
    "sociability": "Sociability",
    "sturdiness": "Sturdiness",
    "smarts": "Smarts",
    "shadow": "Shadow",
    # Common short forms and variants
    "swift": "Swiftness",
    "social": "Sociability",
    "sturdy": "Sturdiness",
    "smart": "Smarts",
}


def normalize_sfactor_label(value: Union[str, Any]) -> str:
    """Return the canonical display label for an S-Factor.
    Accepts a string name (any casing, including short forms) or an SFactorType enum.
    """
    if value is None:
        return "Unknown"

    # Enum support
    try:
        if SFactorType is not None and isinstance(value, SFactorType):
            return str(value.value)
    except Exception:
        pass

    # String normalization
    try:
        key = str(value).strip().lower()
    except Exception:
        return "Unknown"

    # Strip punctuation like trailing ':'
    if key.endswith(":"):
        key = key[:-1]

    return _SFACTOR_LABELS.get(key, value if isinstance(value, str) else str(value))


# N2N descriptor wrappers for consistent, centralized access
try:
    from narrative_utils import (
        N2N_Skill_Level,
        N2N_S_Trait_Level,
        N2N_Status_Level,
        N2N_Shift_Magnitude,
        N2N_Difficulty,
        N2N_Serendipity_Level,
        get_narrative_descriptor,
        get_status_descriptor,
    )
    # N2N_Super_Level was renamed to N2N_Endowment_Level in narrative_utils
    try:
        from narrative_utils import N2N_Super_Level
    except ImportError:
        try:
            from narrative_utils import N2N_Endowment_Level as N2N_Super_Level
        except ImportError:
            N2N_Super_Level = lambda v: N2N_Skill_Level(v)
except Exception:
    # Provide safe fallbacks if narrative_utils isn't importable at module import time
    def _fallback_desc(_: Optional[int]) -> str:
        return "Unknown"

    N2N_Skill_Level = _fallback_desc  # type: ignore
    N2N_S_Trait_Level = _fallback_desc  # type: ignore
    N2N_Super_Level = _fallback_desc  # type: ignore
    N2N_Status_Level = _fallback_desc  # type: ignore
    N2N_Shift_Magnitude = _fallback_desc  # type: ignore
    N2N_Difficulty = _fallback_desc  # type: ignore
    N2N_Serendipity_Level = _fallback_desc  # type: ignore

    def get_narrative_descriptor(_: Optional[int]) -> str:  # type: ignore
        return "Unknown"

    def get_status_descriptor(_: Optional[int]) -> str:  # type: ignore
        return "Unknown"


# Public convenience wrappers (semantic aliases)

def n2n_skill(value: int) -> str:
    return N2N_Skill_Level(value)


def n2n_s_trait(value: int) -> str:
    return N2N_S_Trait_Level(value)


def n2n_super(value: int) -> str:
    return N2N_Super_Level(value)


def n2n_status(value: int) -> str:
    return N2N_Status_Level(value)


def n2n_shift_magnitude(abs_value: int) -> str:
    return N2N_Shift_Magnitude(abs_value)


def n2n_difficulty(stress_level: int) -> str:
    return N2N_Difficulty(stress_level)


def n2n_serendipity(value: int) -> str:
    return N2N_Serendipity_Level(value)


# Legacy compatibility shims (route old helpers through this module)

def descriptor(value: int) -> str:
    """Generic numerical-to-descriptor mapping (legacy)."""
    return get_narrative_descriptor(value)


def status_descriptor(value: int) -> str:
    """Status numerical-to-descriptor mapping (legacy)."""
    return get_status_descriptor(value)
