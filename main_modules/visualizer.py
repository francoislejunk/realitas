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

def _vis_video_worker_loop() -> None:
    global _vis_video_worker
    global _vis_video_pending

    while True:
        job = None
        with _vis_video_lock:
            job = _vis_video_pending
            _vis_video_pending = None
            if job is None:
                _vis_video_worker = None
                return

        try:
            from fal_video_system import generate_ltx2_video_to_latest
        except Exception:
            continue

        try:
            blocking = _env_bool("VIS_VIDEO_AUTOGEN_BLOCKING", True)
        except Exception:
            blocking = True

        try:
            generate_ltx2_video_to_latest(
                prompt=str(job.get('prompt') or ''),
                seed=job.get('seed'),
                blocking=blocking,
            )
            try:
                if _env_bool("VIS_VIDEO_DEBUG", False):
                    print(f"{Color.SYSTEM}🎬 VIS: rendered latest.mp4 (seed={job.get('seed')}){Color.RESET}")
            except Exception:
                pass
        except Exception:
            try:
                if _env_bool("VIS_VIDEO_DEBUG", False):
                    print(f"{Color.WARNING}🎬 VIS: render failed (see fal logs / prompt log){Color.RESET}")
            except Exception:
                pass
            continue




def _enqueue_visualizer_video(*, prompt: str, seed: int = None) -> None:
    global _vis_video_worker
    global _vis_video_pending

    if not prompt:
        return

    with _vis_video_lock:
        _vis_video_pending = {'prompt': str(prompt), 'seed': seed}
        try:
            if _env_bool("VIS_VIDEO_DEBUG", False):
                print(f"{Color.SYSTEM}🎬 VIS: enqueued render (seed={seed}){Color.RESET}")
        except Exception:
            pass
        if _vis_video_worker is None or (hasattr(_vis_video_worker, 'is_alive') and not _vis_video_worker.is_alive()):
            _vis_video_worker = threading.Thread(target=_vis_video_worker_loop, daemon=True)
            _vis_video_worker.start()




def _update_visualizer_context(*, ua_actor, scene_description: str, current_location: str, time_context: dict, creator_agent=None, seed: int = None) -> None:
    global _vis_context
    try:
        _vis_context = {
            'ua_actor': ua_actor,
            'scene_description': scene_description,
            'current_location': current_location,
            'time_context': time_context,
            'creator_agent': creator_agent,
            'seed': seed,
            'last_spoken_line': str(scene_description or ''),
        }
    except Exception:
        _vis_context = {}




def _maybe_start_visualizer_viewer() -> None:
    global _vis_viewer_server
    if _vis_viewer_server is not None:
        return
    if not (_env_bool("VIS_VIDEO_ENABLED", False) or _env_bool("VIS_IMAGE_ENABLED", True)):
        return
    if not _env_bool("VIS_VIEWER_ENABLED", True):
        return
    try:
        from visualizer_viewer_server import start_viewer_server
        host = os.getenv("VIS_VIEWER_HOST") or "127.0.0.1"
        try:
            port = int(os.getenv("VIS_VIEWER_PORT") or "8765")
        except Exception:
            port = 8765
        open_browser = _env_bool("VIS_VIEWER_OPEN_BROWSER", True)
        _vis_viewer_server = start_viewer_server(host=host, port=port, open_browser=open_browser)
    except Exception:
        _vis_viewer_server = None




def _trigger_realtime_image(
    *,
    ua_actor,
    scene_description: str,
    current_location: str,
    time_context: dict,
    creator_agent=None,
    seed: int = None,
    spoken_line: str = "",
    source: str = "scene_load",
    reason: str = "",
) -> None:
    if not _env_bool("VIS_IMAGE_ENABLED", True):
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: VIS_IMAGE_ENABLED is false (skipping){Color.RESET}")
        except Exception:
            pass
        return
    if not (os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY")):
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: missing FAL_API_KEY/FAL_KEY (skipping){Color.RESET}")
        except Exception:
            pass
        return

    _maybe_start_visualizer_viewer()

    try:
        from visualizer_prompt_system import build_scene_composition_traits, render_final_image_prompt
        from fal_image_system import generate_image_to_latest
    except Exception as e:
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: failed to import image modules: {e}{Color.RESET}")
        except Exception:
            pass
        return

    loc = str(current_location or "")
    slug = "scene-image"
    try:
        loc_slug = (loc or "scene").strip().lower().replace(" ", "-")
        slug = f"{loc_slug}-image"
    except Exception:
        slug = "scene-image"

    try:
        traits = build_scene_composition_traits(
            slug=slug,
            actor=ua_actor,
            scene_description=scene_description,
            current_location=loc,
            time_context=time_context,
            spoken_line=str(spoken_line or ""),
            mode="image",
            seed=(seed if seed is not None else 42),
            creator_agent=creator_agent,
        )
        prompt = render_final_image_prompt(traits=traits)

        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                _base_dir = os.path.dirname(os.path.abspath(__file__))
                _vis_dir = os.path.join(_base_dir, "..", "simulation_data", "visualizer")
                _vis_dir = os.path.abspath(_vis_dir)
                os.makedirs(_vis_dir, exist_ok=True)
                _prompt_path = os.path.join(_vis_dir, "latest_prompt.txt")
                with open(_prompt_path, "w", encoding="utf-8") as f:
                    f.write(f"SOURCE: {source}\n")
                    if reason:
                        f.write(f"REASON: {reason}\n")
                    f.write("\n")
                    f.write(prompt)
        except Exception:
            pass
    except Exception as e:
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: failed to build image prompt: {e}{Color.RESET}")
        except Exception:
            pass
        return

    try:
        blocking = _env_bool("VIS_IMAGE_BLOCKING", True)
    except Exception:
        blocking = True

    try:
        _req_id, _image_url, _latest_path = generate_image_to_latest(prompt=prompt, seed=seed, blocking=blocking)
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.SYSTEM}🖼️ VIS: rendered latest.png (seed={seed}){Color.RESET}")
        except Exception:
            pass

        try:
            if _env_bool("VIS_IMAGE_SAVE_HISTORY", True) and _latest_path and os.path.exists(_latest_path):
                try:
                    from datetime import datetime
                except Exception:
                    datetime = None
                try:
                    import shutil
                except Exception:
                    shutil = None

                if datetime is not None and shutil is not None:
                    _ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
                    _base_dir = os.path.dirname(os.path.abspath(__file__))
                    _default_hist_dir = os.path.abspath(os.path.join(_base_dir, "..", "simulation_data", "visualizer", "history"))
                    _hist_dir = os.getenv("VIS_IMAGE_HISTORY_DIR") or _default_hist_dir
                    try:
                        os.makedirs(_hist_dir, exist_ok=True)
                    except Exception:
                        pass

                    _safe_source = ''.join([c for c in str(source or 'scene_load') if c.isalnum() or c in ('-', '_')])[:32]
                    _safe_reason = ''.join([c for c in str(reason or '') if c.isalnum() or c in ('-', '_')])[:48]
                    _name_bits = [b for b in [_ts, _safe_source, (_safe_reason if _safe_reason else None)] if b]
                    _stem = "__".join(_name_bits)

                    _dst_img = os.path.join(_hist_dir, _stem + ".png")
                    try:
                        shutil.copy2(_latest_path, _dst_img)
                    except Exception:
                        pass

                    try:
                        _dst_txt = os.path.join(_hist_dir, _stem + ".txt")
                        with open(_dst_txt, "w", encoding="utf-8") as f:
                            f.write(f"SOURCE: {source}\n")
                            if reason:
                                f.write(f"REASON: {reason}\n")
                            f.write("\n")
                            f.write(prompt)
                    except Exception:
                        pass
        except Exception:
            pass
    except Exception as e:
        try:
            if _env_bool("VIS_IMAGE_DEBUG", False):
                print(f"{Color.WARNING}🖼️ VIS: image generation failed: {e}{Color.RESET}")
        except Exception:
            pass
        return




def _trigger_realtime_video(
    *,
    ua_actor,
    scene_description: str,
    current_location: str,
    time_context: dict,
    spoken_line: str,
    creator_agent=None,
    seed: int = None,
) -> None:
    if not _env_bool("VIS_VIDEO_ENABLED", False):
        return
    if not (os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY")):
        try:
            if _env_bool("VIS_VIDEO_DEBUG", False):
                print(f"{Color.WARNING}🎬 VIS: missing FAL_API_KEY/FAL_KEY (skipping){Color.RESET}")
        except Exception:
            pass
        return

    _maybe_start_visualizer_viewer()

    try:
        from visualizer_prompt_system import build_scene_composition_traits, render_final_video_prompt
        from fal_video_system import generate_ltx2_video_to_latest
    except Exception:
        try:
            if _env_bool("VIS_VIDEO_DEBUG", False):
                print(f"{Color.WARNING}🎬 VIS: failed to import visualizer/fal modules (skipping){Color.RESET}")
        except Exception:
            pass
        return

    loc = str(current_location or "")
    if not loc:
        try:
            from spatial_context_system import get_spatial_manager
            sm = get_spatial_manager(session_id=None)
            ctx = sm.get_current_context() if sm else None
            loc = str(getattr(ctx, 'current_location', '') or '') if ctx else ""
        except Exception:
            loc = ""

    slug = "realtime"
    try:
        loc_slug = (loc or "scene").strip().lower().replace(" ", "-")
        slug = f"{loc_slug}-realtime"
    except Exception:
        slug = "realtime"

    try:
        traits = build_scene_composition_traits(
            slug=slug,
            actor=ua_actor,
            scene_description=scene_description,
            current_location=loc,
            time_context=time_context,
            spoken_line=spoken_line,
            mode="video",
            seed=(seed if seed is not None else 42),
            creator_agent=creator_agent,
        )
        prompt = render_final_video_prompt(traits=traits)
    except Exception as e:
        try:
            if _env_bool("VIS_VIDEO_DEBUG", False):
                print(f"{Color.WARNING}🎬 VIS: failed to build prompt: {e}{Color.RESET}")
        except Exception:
            pass
        return

    blocking = _env_bool("VIS_VIDEO_BLOCKING", True)
    try:
        autogen_async = _env_bool("VIS_VIDEO_AUTOGEN_ASYNC", True)
        if _vis_autogen_enabled and autogen_async:
            _enqueue_visualizer_video(prompt=prompt, seed=seed)
        else:
            generate_ltx2_video_to_latest(prompt=prompt, seed=seed, blocking=blocking)
    except Exception:
        return



