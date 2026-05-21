from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass
class SelfEffect:
    condition: Optional[str] = None  # UA/NUA proactor path
    target_status: Optional[str] = None
    polarity: Optional[str] = None
    shift_type: Optional[str] = None
    severity: Optional[int] = None
    severity_justification: Optional[str] = None
    description: Optional[str] = None


@dataclass
class UTASFactors:
    exchange_type: Optional[str] = None
    status_to_shift: Optional[str] = None
    s_trait_to_use: Optional[str] = None
    s_trait_value: Optional[int] = None
    s_trait_justification: Optional[str] = None
    skill: Dict[str, Any] = field(default_factory=dict)
    skill_justification: Optional[str] = None
    super: Dict[str, Any] = field(default_factory=dict)
    supplement: Dict[str, Any] = field(default_factory=dict)
    stress_level: Optional[int] = None
    stress_justification: Optional[str] = None
    shift_type: Optional[str] = None
    shift_type_justification: Optional[str] = None
    shift_polarity: Optional[str] = None
    shift_polarity_justification: Optional[str] = None


@dataclass
class ActionData:
    action_noun: Optional[str] = None
    action_description: Optional[str] = None
    narrative_description: Optional[str] = None
    character_motivation: Optional[str] = None
    justification: Optional[str] = None
    utas_factors: Dict[str, Any] = field(default_factory=dict)
    self_effects: List[Dict[str, Any]] = field(default_factory=list)
    raw_action: Optional[str] = None


REQUIRED_TOP_LEVEL = [
    "narrative_description",
    "utas_factors",
]

REQUIRED_UTAS_FIELDS = [
    "exchange_type",
    "status_to_shift",
    "s_trait_to_use",
    "s_trait_value",
    "skill",
    "super",
    "supplement",
    "stress_level",
    "shift_type",
    "shift_polarity",
]


def _is_int(value) -> bool:
    try:
        int(value)
        return True
    except Exception:
        return False


def validate_action_data(data: Dict[str, Any], require_self_effects: bool = True) -> Dict[str, Any]:
    """
    Validate the normalized action dict matches the shared UTAS action contract.
    - Ensures required fields exist.
    - Ensures nested objects (skill/super/supplement) have name/value keys.
    - Ensures numeric fields are ints.
    - Enforces non-empty self_effects for proactor actions when required.
    Returns the input dict if valid; raises ValueError on violations.
    """
    if not isinstance(data, dict):
        raise ValueError("ActionData must be a dict after normalization")

    # Top-level fields
    for k in REQUIRED_TOP_LEVEL:
        if k not in data:
            raise ValueError(f"Missing required field: {k}")

    factors = data.get("utas_factors", {})
    if not isinstance(factors, dict):
        raise ValueError("utas_factors must be an object")

    # Required UTAS fields
    for k in REQUIRED_UTAS_FIELDS:
        if k not in factors:
            raise ValueError(f"utas_factors missing '{k}'")

    # Nested object checks
    for nested in ["skill", "super", "supplement"]:
        obj = factors.get(nested, {})
        if not isinstance(obj, dict) or "name" not in obj or "value" not in obj:
            raise ValueError(f"utas_factors.{nested} must be an object with 'name' and 'value'")
        # Coerce numeric where applicable
        val = obj.get("value")
        if not _is_int(val):
            raise ValueError(f"utas_factors.{nested}.value must be an integer")

    # Numeric field checks
    if not _is_int(factors.get("s_trait_value")):
        raise ValueError("utas_factors.s_trait_value must be an integer")
    if not _is_int(factors.get("stress_level")):
        raise ValueError("utas_factors.stress_level must be an integer")

    # Self-effects enforcement for proactors
    if require_self_effects:
        se = data.get("self_effects", [])
        if not isinstance(se, list) or len(se) == 0:
            raise ValueError("self_effects must be present and non-empty for proactor actions")

    return data
