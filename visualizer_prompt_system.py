import json
import os
from typing import Any, Dict, List, Optional, Tuple


def _safe_str(v: Any) -> str:
    try:
        return str(v or "").strip()
    except Exception:
        return ""


def _truncate(s: str, max_chars: int) -> str:
    s = _safe_str(s)
    if len(s) <= max_chars:
        return s
    return s[: max(0, max_chars - 3)] + "..."


def _visualizer_cache_path() -> str:
    try:
        base = os.path.join("simulation_data", "visualizer")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "visual_identities.json")
    except Exception:
        return "visual_identities.json"


def _load_visual_identities() -> Dict[str, Any]:
    path = _visualizer_cache_path()
    try:
        if not os.path.exists(path):
            return {}
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _save_visual_identities(data: Dict[str, Any]) -> None:
    path = _visualizer_cache_path()
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def _actor_identity_key(actor: Any) -> str:
    try:
        sheet = getattr(actor, "sheet", None)
        if sheet is not None:
            cn = _safe_str(getattr(sheet, "canonical_name", None))
            nm = _safe_str(getattr(sheet, "name", None))
            if cn:
                return cn
            if nm:
                return nm
    except Exception:
        pass
    return _safe_str(getattr(actor, "name", None)) or "UA"


def _coerce_list_str(v: Any, max_items: int = 6) -> List[str]:
    if v is None:
        return []
    if isinstance(v, list):
        out = []
        for x in v:
            s = _safe_str(x)
            if s:
                out.append(s)
        return out[:max_items]
    s = _safe_str(v)
    return [s] if s else []


def _generate_visual_identity_via_creator(
    *,
    actor: Any,
    scene_description: str,
    time_context: Optional[Dict[str, Any]] = None,
    creator_agent: Any = None,
) -> Optional[Dict[str, Any]]:
    """Best-effort LLM generation of a stable UA visual identity.

    This is intentionally minimal and JSON-only. It should not invent non-diegetic elements.
    """

    ua_name = ""
    ua_occ = ""
    ua_age = None
    ua_pronouns = ""
    try:
        sheet = getattr(actor, "sheet", None)
        ua_name = _safe_str(getattr(sheet, "name", None))
        ua_occ = _safe_str(getattr(sheet, "occupation", None))
        ua_age = getattr(sheet, "age", None)
        ua_pronouns = _safe_str(getattr(sheet, "pronouns", None))
    except Exception:
        pass

    tod = ""
    ts = ""
    try:
        if isinstance(time_context, dict):
            tod_v = time_context.get("time_of_day")
            tod = _safe_str(getattr(tod_v, "value", None) or tod_v)
            ts = _safe_str(time_context.get("time_string") or time_context.get("formatted_time"))
    except Exception:
        tod = ""
        ts = ""

    inv = _extract_inventory(actor, 5)

    prompt = (
        "You are generating STABLE VISUAL IDENTITY TRAITS for image/video generation.\n"
        "This identity must stay consistent across future shots.\n\n"
        "Return ONLY valid JSON. No markdown.\n\n"
        "Required JSON keys:\n"
        "- description: 1 short clause (age range, ethnicity if clear, hair, face, notable fixed features).\n"
        "- clothing_base: short comma-separated list of core outfit items (stable across shots).\n"
        "- fixed_traits: list of 0-4 fixed features (e.g., scar, tattoo, distinctive ring).\n"
        "- cosmetics_notes: list of 0-5 small presentable notes for diegetic camcorder overlay (e.g., 'jacket scuffed', 'hands oily', 'sleeves rolled').\n\n"
        "Hard rules:\n"
        "- Modern grounded realism, no sci-fi, no supernatural.\n"
        "- Do NOT add brand names unless already implied.\n"
        "- Do NOT contradict provided character facts.\n"
        "- Keep it minimal and reusable.\n\n"
        f"Character facts:\n- Name: {ua_name or 'UA'}\n- Occupation: {ua_occ or 'Unknown'}\n- Age: {ua_age if ua_age is not None else 'Unknown'}\n- Pronouns: {ua_pronouns or 'Unknown'}\n"
        f"Time context: {tod or 'unknown'} {ts}\n"
        f"Inventory (context only): {', '.join(inv) if inv else '(none)'}\n\n"
        "Current scene (context only; do not overfit clothing to scene):\n"
        f"{_truncate(scene_description, 800)}\n"
    )

    try:
        from openrouter_config import OpenRouterConfig, create_role_client, robust_llm_call, RetryConfig

        client = None
        model = None
        try:
            client = getattr(creator_agent, "client", None)
            model = getattr(creator_agent, "model", None)
        except Exception:
            client = None
            model = None

        if client is None:
            client = create_role_client("scene_creation")
        if not model:
            model = OpenRouterConfig.get_model_for_role("scene_creation")

        raw = robust_llm_call(
            client=client,
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=220,
            max_retries=RetryConfig.QUICK_MAX_RETRIES,
            call_name="VISUAL_IDENTITY",
        )
        if not raw:
            return None

        data = json.loads(raw)
        if not isinstance(data, dict):
            return None

        return {
            "description": _safe_str(data.get("description")),
            "clothing_base": _safe_str(data.get("clothing_base")),
            "fixed_traits": _coerce_list_str(data.get("fixed_traits"), 4),
            "cosmetics_notes": _coerce_list_str(data.get("cosmetics_notes"), 6),
        }
    except Exception:
        return None


def get_or_create_visual_identity(
    *,
    actor: Any,
    scene_description: str,
    time_context: Optional[Dict[str, Any]] = None,
    creator_agent: Any = None,
) -> Dict[str, Any]:
    key = _actor_identity_key(actor)
    cache = _load_visual_identities()

    existing = cache.get(key)
    if isinstance(existing, dict):
        return existing

    # Fallback to ActorSheet public_description if present (not full appearance, but better than empty)
    fallback_desc = ""
    try:
        sheet = getattr(actor, "sheet", None)
        fallback_desc = _safe_str(getattr(sheet, "public_description", None))
    except Exception:
        fallback_desc = ""

    generated = _generate_visual_identity_via_creator(
        actor=actor,
        scene_description=scene_description,
        time_context=time_context,
        creator_agent=creator_agent,
    )

    if not generated:
        generated = {
            "description": fallback_desc,
            "clothing_base": "",
            "fixed_traits": [],
            "cosmetics_notes": [],
        }

    cache[key] = generated
    _save_visual_identities(cache)
    return generated


def _infer_location_type(scene_description: str, current_location: Optional[str] = None) -> str:
    sd = _safe_str(scene_description).lower()
    loc = _safe_str(current_location).lower()
    text = f"{loc} {sd}".strip()
    exterior_markers = [
        "street",
        "sidewalk",
        "alley",
        "parking lot",
        "park",
        "outside",
        "outdoors",
        "sky",
        "rain",
        "snow",
        "night air",
        "wind",
    ]
    for m in exterior_markers:
        if m in text:
            return "exterior"
    return "interior"


def _extract_inventory(actor: Any, max_items: int = 3) -> List[str]:
    try:
        inv = getattr(getattr(actor, "sheet", None), "inventory", None) or []
    except Exception:
        inv = []
    out: List[str] = []
    for item in list(inv)[: max_items]:
        try:
            nm = _safe_str(getattr(item, "name", None) or item)
        except Exception:
            nm = ""
        if nm:
            out.append(nm)
    return out


def _extract_statuses(actor: Any) -> Dict[str, Dict[str, Any]]:
    statuses: Dict[str, Dict[str, Any]] = {}
    try:
        st = getattr(getattr(actor, "sheet", None), "statuses", None) or {}
    except Exception:
        st = {}

    for k, v in (st or {}).items():
        try:
            key_name = _safe_str(getattr(k, "name", None) or k)
        except Exception:
            key_name = _safe_str(k)
        try:
            val = getattr(v, "value", None)
        except Exception:
            val = None

        if key_name:
            statuses[key_name.upper()] = {"value": val}

    return statuses


def _extract_sensing(max_props: int = 3, max_actors: int = 4) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]]]:
    sensing: Optional[Dict[str, Any]] = None
    present_actors: List[Dict[str, Any]] = []
    key_props: List[Dict[str, Any]] = []

    try:
        from pygame_spatial_map import get_sensing_data_from_map

        sensing = get_sensing_data_from_map()
    except Exception:
        sensing = None

    if not sensing:
        return None, present_actors, key_props

    actors = sensing.get("actors") or {}
    in_vision = set(sensing.get("actors_in_vision") or [])
    in_hearing = set(sensing.get("actors_in_hearing") or [])
    in_touch = set(sensing.get("actors_in_touch") or [])

    def _vis_label(aid: str) -> str:
        if aid in in_touch:
            return "reach"
        if aid in in_vision:
            return "visible"
        if aid in in_hearing:
            return "heard"
        return "unknown"

    actor_rows: List[Tuple[float, Dict[str, Any]]] = []
    for aid, a in actors.items():
        try:
            dist = float(a.get("distance_to_ua") or 0.0)
        except Exception:
            dist = 0.0
        actor_rows.append(
            (
                dist,
                {
                    "name": _safe_str(a.get("name")),
                    "type": _safe_str(a.get("type")) or "nua",
                    "distance_units": dist,
                    "visibility": _vis_label(aid),
                    "occupation": _safe_str(a.get("occupation")),
                },
            )
        )

    actor_rows.sort(key=lambda t: t[0])
    present_actors = [row for _, row in actor_rows[: max_actors] if row.get("name")]

    obs = sensing.get("obstacles") or {}
    prop_rows: List[Tuple[float, Dict[str, Any]]] = []
    for _, o in obs.items():
        try:
            dist = float(o.get("distance_to_ua") or 0.0)
        except Exception:
            dist = 0.0
        prop_rows.append(
            (
                dist,
                {
                    "name": _safe_str(o.get("name")),
                    "distance_units": dist,
                    "type": _safe_str(o.get("type")) or "object",
                },
            )
        )

    prop_rows.sort(key=lambda t: t[0])
    key_props = [row for _, row in prop_rows[: max_props] if row.get("name")]

    return sensing, present_actors, key_props


def build_scene_composition_traits(
    *,
    slug: str,
    actor: Any,
    scene_description: str,
    current_location: Optional[str] = None,
    time_context: Optional[Dict[str, Any]] = None,
    spoken_line: str = "",
    mode: str = "video",
    seed: int = 42,
    creator_agent: Any = None,
) -> Dict[str, Any]:
    slug = _safe_str(slug) or "untitled shot"
    spoken_line = _truncate(_safe_str(spoken_line), 220)
    mode = _safe_str(mode).lower() or "video"

    ua_name = ""
    try:
        ua_name = _safe_str(getattr(getattr(actor, "sheet", None), "name", None) or getattr(actor, "name", None))
    except Exception:
        ua_name = ""

    sensing, present_actors, key_props = _extract_sensing()

    loc_name = _safe_str(current_location) or _safe_str(sensing.get("location_name") if sensing else "")
    loc_type = _infer_location_type(scene_description, loc_name)
    try:
        sd_l = _safe_str(scene_description).lower()
        ln_l = _safe_str(loc_name).lower()
        interior_hints = (
            "interior",
            "inside",
            "indoors",
            "room",
            "hallway",
            "corridor",
            "crypt",
            "chapel",
            "basement",
            "cellar",
            "tunnel",
            "cave",
        )
        exterior_hints = ("outdoors", "outside", "street", "forest", "field", "road", "courtyard")
        if any(h in sd_l or h in ln_l for h in interior_hints) and not any(h in sd_l or h in ln_l for h in exterior_hints):
            loc_type = "interior"
    except Exception:
        pass
    loc_size = None
    try:
        loc_size = list(sensing.get("location_size") or []) if sensing else None
    except Exception:
        loc_size = None

    tod = "unknown"
    clock_string = ""
    try:
        if isinstance(time_context, dict):
            tod_v = time_context.get("time_of_day")
            tod = _safe_str(getattr(tod_v, "value", None) or tod_v) or "unknown"
            clock_string = _safe_str(time_context.get("time_string") or "")
    except Exception:
        tod = "unknown"
        clock_string = ""

    traits: Dict[str, Any] = {
        "version": "2026.1-visualizer-min",
        "seed": int(seed),
        "shot": {
            "slug": slug,
            "mode": "video" if mode != "image" else "image",
            "perspective": "third_person",
            "shot_type": "close_to_medium",
            "duration_seconds": 3,
            "extendable_take_target_seconds": 180,
            "frame_count_hint": 8,
            "resolution_hint": "low",
        },
        "camera": {
            "style": "handheld_unstable_raw",
            "lens_hint": "35mm",
            "height": "eye_level",
            "distance_to_subject": "close_to_medium",
            "motion_rules": [
                "constant_micro_jitter",
                "slight_rotational_wobble",
                "irregular_motion_blur_from_movement_only",
                "no_stabilization",
                "no_smooth_pans",
                "occasional_micro_whips",
            ],
        },
        "subject": {
            "identity_lock": {
                "canonical_name": ua_name or "UA",
                "public_aliases": [],
                "description": "",
                "fixed_traits": [],
                "clothing_base": "",
            },
            "body_state": {
                "posture": "standing_or_moving",
                "breath": "normal",
                "injury_visible": "",
            },
            "performance": {
                "emotion_surface": "alert",
                "micro_actions": ["eyes_flick", "jaw_tighten", "small_grip_adjustment"],
            },
        },
        "scene": {
            "location": {
                "name": loc_name or "Unknown Location",
                "type": loc_type,
                "size_units": loc_size or [],
            },
            "time": {
                "time_of_day": tod,
                "clock_string": clock_string,
            },
            "environment_summary": _truncate(scene_description, 600),
            "practical_lighting": {
                "sources": [],
                "rule": "practical_only_minor_exposure_fluctuation_ok",
            },
            "key_props": key_props,
            "present_actors": present_actors,
        },
        "diegetic_ui": {
            "enabled": True,
            "style": "camcorder_timestamp_vibe",
            "inventory": {"show": True, "top_items": _extract_inventory(actor, 3)},
            "condition": {"show": True, "statuses": _extract_statuses(actor)},
            "cosmetics": {"show": True, "notes": []},
        },
        "dialogue": {
            "spoken_line": spoken_line,
            "delivery": "urgent_strained_if_applicable" if spoken_line else "",
        },
        "style_constraints": {
            "photoreal_live_action": True,
            "no_animation_like_motion": True,
            "no_cinematic_smoothness": True,
            "no_slow_motion": True,
            "keep_continuity_with_reference": True,
        },
        "negative_constraints": [
            "deformed",
            "extra limbs",
            "bad hands",
            "text gibberish",
            "unreal engine",
            "anime",
        ],
    }

    # Compatibility + user-requested schema: keep existing traits AND include a stable
    # top-level block optimized for "character lock" workflows.
    try:
        ident = (traits.get("subject") or {}).get("identity_lock") or {}
        scene = traits.get("scene") or {}
        loc = (scene.get("location") or {}) if isinstance(scene, dict) else {}
        tctx = (scene.get("time") or {}) if isinstance(scene, dict) else {}
        cam = traits.get("camera") or {}
        dieg = traits.get("diegetic_ui") or {}

        neg_list = traits.get("negative_constraints")
        neg_str = ""
        try:
            if isinstance(neg_list, list):
                neg_str = ", ".join([_safe_str(x) for x in neg_list if _safe_str(x)])
            else:
                neg_str = _safe_str(neg_list)
        except Exception:
            neg_str = ""

        traits["character_identity"] = {
            "name": _safe_str(ident.get("canonical_name")) or (ua_name or "Unique_ID_01"),
            "description": _safe_str(ident.get("description")),
            "fixed_traits": _coerce_list_str(ident.get("fixed_traits"), 6),
            "clothing_base": _safe_str(ident.get("clothing_base")),
            "pose_reference": _safe_str((traits.get("subject") or {}).get("body_state", {}).get("posture"))
            if isinstance(traits.get("subject"), dict) else "",
        }

        traits["scene_context"] = {
            "environment": _safe_str(loc.get("type")) or "unknown",
            "background": _safe_str(scene.get("environment_summary")),
            "time_of_day": _safe_str(tctx.get("time_of_day")) or "unknown",
            "location_name": _safe_str(loc.get("name")) or "Unknown Location",
        }

        traits["technical_specs"] = {
            "camera": f"{_safe_str(cam.get('lens_hint') or '35mm')} lens, {_safe_str(cam.get('height') or 'eye_level')}, handheld",
            "lighting": _safe_str(((scene.get("practical_lighting") or {}) if isinstance(scene, dict) else {}).get("rule"))
            or "practical_only",
            "style": "photorealistic live-action, handheld, unstable, low-res, few frames",
            "diegetic_ui": {
                "enabled": bool((dieg.get("enabled") if isinstance(dieg, dict) else True)),
                "inventory": (dieg.get("inventory") if isinstance(dieg, dict) else {}),
                "condition": (dieg.get("condition") if isinstance(dieg, dict) else {}),
                "cosmetics": (dieg.get("cosmetics") if isinstance(dieg, dict) else {}),
            },
        }

        traits["negative_constraints"] = neg_str or neg_list
    except Exception:
        pass

    # Fill stable UA visual identity (description/clothing/cosmetics) via Creator-backed generation + cache.
    try:
        vi = get_or_create_visual_identity(
            actor=actor,
            scene_description=scene_description,
            time_context=time_context,
            creator_agent=creator_agent,
        )
        ident = traits.get("subject", {}).get("identity_lock", {})
        if isinstance(ident, dict):
            if not _safe_str(ident.get("description")):
                ident["description"] = _safe_str(vi.get("description"))
            if not _safe_str(ident.get("clothing_base")):
                ident["clothing_base"] = _safe_str(vi.get("clothing_base"))
            if not ident.get("fixed_traits"):
                ident["fixed_traits"] = _coerce_list_str(vi.get("fixed_traits"), 4)

        cos = traits.get("diegetic_ui", {}).get("cosmetics", {})
        if isinstance(cos, dict):
            if not cos.get("notes"):
                cos["notes"] = _coerce_list_str(vi.get("cosmetics_notes"), 6)
    except Exception:
        pass

    return traits


def render_final_video_prompt(*, traits: Dict[str, Any], spoken_line: str = "") -> str:
    spoken_line = _safe_str(spoken_line or (traits.get("dialogue") or {}).get("spoken_line"))
    spoken_line = _truncate(spoken_line, 220)
    traits_json = json.dumps(traits, ensure_ascii=False, indent=2)

    slug = ""
    try:
        slug = _safe_str(((traits.get("shot") or {}) if isinstance(traits.get("shot"), dict) else {}).get("slug"))
    except Exception:
        slug = ""

    line_block = spoken_line if spoken_line else ""

    return "\n".join(
        [
            "USER INPUT — SLUG",
            "(Short identifier for the shot. 3–6 words.)",
            slug,
            traits_json,
            "USER INPUT — SPOKEN LINE",
            line_block,
            "SYSTEM / TEMPLATE INSTRUCTIONS",
            "(The model generates the video prompt below using the scene traits provided above.)",
            "FINAL VIDEO PROMPT (OUTPUT ONLY) Analyze the scene traits and extend this exact",
            "moment into motion.",
            "IMPORTANT: The output clip is ~3 seconds, but it must feel like it could continue seamlessly into a",
            "single continuous 3-minute take. No cuts. No time jump. No new camera setup. Maintain continuity.",
            "Create a single continuous video shot that feels raw, handheld, and unstable, as if filmed under pressure.",
            "CAMERA (CRITICAL — PRIORITY)",
            "The camera is handheld and shaky at all times.",
            "Constant micro-jitter, uneven framing, slight rotational wobble, and irregular motion blur caused by real",
            "human movement.",
            "No stabilization. No smooth pans. No dolly or crane motion.",
            "Occasional small grip adjustments cause brief, imperfect micro-whips.",
            "Camera shake must be visible throughout the entire shot and drive the tension.",
            "SHOT",
            "Close-to-medium handheld shot of the subject from the reference image, in the same environment.",
            "The camera reacts to the subject rather than controlling them.",
            f"If dialogue is provided, the subject delivers \"{spoken_line}\" with urgency and strain." if spoken_line else "If dialogue is provided, the subject delivers the line with urgency and strain.",
            "PERFORMANCE",
            "Expression shifts subtly during the shot: jaw tightening, breath visible, eyes flicking, tension rising.",
            "The action remains one continuous moment — no cuts, no time jump.",
            "MOTION BLUR",
            "Motion blur is present due to camera shake and movement, not post effects.",
            "Blur increases slightly during emotional emphasis or camera instability.",
            "LIGHTING & SPACE",
            "Lighting remains consistent with the reference image.",
            "STYLE CONSTRAINTS",
            "Practical light sources only.",
            "Minor exposure fluctuation occurs naturally due to camera movement, not lighting changes.",
            "Photorealistic live-action.",
            "No cinematic smoothness.",
            "No slow motion.",
            "No stylized effects.",
            "No animation-like motion",
            "The shot should feel like a single raw take, captured in the middle of chaos.",
        ]
    )


def render_final_image_prompt(*, traits: Dict[str, Any]) -> str:
    traits_json = json.dumps(traits, ensure_ascii=False, indent=2)
    return "\n".join(
        [
            traits_json,
            "SYSTEM / TEMPLATE INSTRUCTIONS",
            "(Use the JSON above as the scene composition traits / reference. Generate a single image that matches it exactly.)",
        ]
    )
