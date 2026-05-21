from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Optional, Tuple

from json_utils import extract_and_parse_json
from openrouter_config import OpenRouterConfig, RetryConfig, robust_llm_call


@dataclass(frozen=True)
class SizingDecision:
    location_name: str
    width: float
    height: float
    expected_npc_count: int
    max_capacity: int
    location_type: str
    reasoning: str


class LocationSizer:
    @staticmethod
    def decide(location_name: str, *, location_hint: str = "") -> SizingDecision:
        base = LocationSizer._deterministic_decide(location_name, location_hint=location_hint)

        use_llm = (os.environ.get('LOCATION_SIZER_USE_LLM') or '').strip().lower() in ('1', 'true', 'yes', 'on')
        if not use_llm:
            return base

        try:
            client = OpenRouterConfig.create_role_client('coordination')
        except Exception:
            return base

        prompt = (
            "You are a location sizing system for a simulation. "
            "Given a location name and optional hint, choose realistic dimensions and population limits.\n\n"
            f"LOCATION NAME: {base.location_name}\n"
            f"HINT: {str(location_hint or '').strip()}\n\n"
            "Return ONLY valid JSON (no markdown):\n"
            "{\n"
            "  \"location_type\": \"bar|restaurant|market|station|street|alley|industrial|room|interior|other\",\n"
            "  \"width\": number,\n"
            "  \"height\": number,\n"
            "  \"max_capacity\": integer,\n"
            "  \"expected_npc_count\": integer,\n"
            "  \"reasoning\": \"short\"\n"
            "}"
        )

        response_text = robust_llm_call(
            client=client,
            messages=[{"role": "user", "content": prompt}],
            model=OpenRouterConfig.get_model_for_role('coordination'),
            temperature=0.2,
            max_tokens=220,
            max_retries=RetryConfig.QUICK_MAX_RETRIES,
            call_name="LOCATION_SIZER"
        )

        obj = extract_and_parse_json(response_text or "")
        if not isinstance(obj, dict):
            return base

        # Clamp/sanitize aggressively (never trust raw LLM numbers)
        width = LocationSizer._clamp_float(obj.get('width', base.width), 4.0, 250.0, base.width)
        height = LocationSizer._clamp_float(obj.get('height', base.height), 4.0, 200.0, base.height)

        # Capacity: allow 1..200, but also tie to physical area (2m^2 per person baseline).
        area = max(1.0, width * height)
        computed_cap = int(max(1, min(200, area // 2)))
        max_capacity = LocationSizer._clamp_int(obj.get('max_capacity', computed_cap), 1, 200, computed_cap)
        max_capacity = int(min(max_capacity, computed_cap))

        expected_npc_count = LocationSizer._clamp_int(obj.get('expected_npc_count', base.expected_npc_count), 0, 200, base.expected_npc_count)
        expected_npc_count = int(min(expected_npc_count, max_capacity))

        location_type = str(obj.get('location_type', base.location_type) or base.location_type).strip() or base.location_type
        reasoning = str(obj.get('reasoning', '') or '').strip() or base.reasoning

        return SizingDecision(
            location_name=base.location_name,
            width=float(width),
            height=float(height),
            expected_npc_count=int(expected_npc_count),
            max_capacity=int(max_capacity),
            location_type=location_type,
            reasoning=reasoning,
        )

    @staticmethod
    def _deterministic_decide(location_name: str, *, location_hint: str = "") -> SizingDecision:
        name = str(location_name or "").strip() or "Unknown"
        name_l = name.lower()
        hint_l = str(location_hint or "").lower()
        key = f"{name_l} {hint_l}".strip()

        width: float
        height: float
        expected_npc_count: int
        location_type: str
        reasoning: str

        if any(k in key for k in ("tavern", "inn", "bar", "pub", "saloon")):
            width, height = 16.0, 12.0
            expected_npc_count = 20
            location_type = "bar"
            reasoning = "Public venue sizing preset"
        elif any(k in key for k in ("restaurant", "diner", "cafe", "coffee")):
            width, height = 14.0, 10.0
            expected_npc_count = 14
            location_type = "restaurant"
            reasoning = "Food service venue sizing preset"
        elif any(k in key for k in ("market", "mall")):
            width, height = 30.0, 20.0
            expected_npc_count = 25
            location_type = "market"
            reasoning = "Commercial crowd venue sizing preset"
        elif any(k in key for k in ("station", "terminal")):
            width, height = 40.0, 25.0
            expected_npc_count = 25
            location_type = "station"
            reasoning = "Transit venue sizing preset"
        elif any(k in key for k in ("warehouse", "factory", "plant")):
            width, height = 60.0, 40.0
            expected_npc_count = 12
            location_type = "industrial"
            reasoning = "Industrial venue sizing preset"
        elif any(k in key for k in ("alley", "alleyway")):
            width, height = 30.0, 8.0
            expected_npc_count = 5
            location_type = "alley"
            reasoning = "Outdoor corridor sizing preset"
        elif any(k in key for k in ("street", "road", "sidewalk")):
            width, height = 80.0, 20.0
            expected_npc_count = 10
            location_type = "street"
            reasoning = "Street sizing preset"
        elif any(k in key for k in ("room", "office", "bedroom", "bathroom", "kitchen")):
            width, height = 8.0, 6.0
            expected_npc_count = 4
            location_type = "room"
            reasoning = "Single-room interior sizing preset"
        else:
            width, height = 12.0, 9.0
            expected_npc_count = 8
            location_type = "interior"
            reasoning = "Default interior sizing preset"

        width = float(max(4.0, width))
        height = float(max(4.0, height))
        expected_npc_count = int(max(0, expected_npc_count))
        computed_cap = int(max(1, min(200, (width * height) // 2)))
        max_capacity = int(max(expected_npc_count, computed_cap))

        return SizingDecision(
            location_name=name,
            width=width,
            height=height,
            expected_npc_count=expected_npc_count,
            max_capacity=max_capacity,
            location_type=location_type,
            reasoning=reasoning,
        )

    @staticmethod
    def _clamp_float(value: object, min_v: float, max_v: float, fallback: float) -> float:
        try:
            v = float(value)
        except Exception:
            v = float(fallback)
        return float(max(min_v, min(max_v, v)))

    @staticmethod
    def _clamp_int(value: object, min_v: int, max_v: int, fallback: int) -> int:
        try:
            v = int(float(value))
        except Exception:
            v = int(fallback)
        return int(max(min_v, min(max_v, v)))
