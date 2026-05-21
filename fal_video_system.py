import json
import os
import time
import urllib.error
import urllib.request
from typing import Any, Dict, Optional, Tuple


def _env_bool(name: str, default: bool = False) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    s = str(v).strip().lower()
    if s in ("1", "true", "yes", "y", "on"):
        return True
    if s in ("0", "false", "no", "n", "off"):
        return False
    return default


def _env_int(name: str, default: int) -> int:
    v = os.getenv(name)
    if v is None:
        return default
    try:
        return int(str(v).strip())
    except Exception:
        return default


def _env_float(name: str, default: float) -> float:
    try:
        v = os.getenv(name)
        if v is None:
            return float(default)
        return float(str(v).strip())
    except Exception:
        return float(default)


def _prompt_log_path() -> str:
    p = os.getenv("VIS_VIDEO_LOG_PROMPT_PATH")
    if p:
        return p
    try:
        base = os.path.join("simulation_data", "visualizer")
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, "fal_last_prompt.txt")
    except Exception:
        return "fal_last_prompt.txt"


def _maybe_log_prompt(prompt: str) -> None:
    if not _env_bool("VIS_VIDEO_LOG_PROMPT", False):
        return
    try:
        p = str(prompt or "")
    except Exception:
        return

    try:
        # Console log (optional) + file log (always if enabled)
        if _env_bool("VIS_VIDEO_LOG_PROMPT_STDOUT", True):
            print("\n--- FAL VIDEO PROMPT (BEGIN) ---")
            print(p)
            print("--- FAL VIDEO PROMPT (END) ---\n")
    except Exception:
        pass

    try:
        path = _prompt_log_path()
        with open(path, "w", encoding="utf-8") as f:
            f.write(p)
            if not p.endswith("\n"):
                f.write("\n")
    except Exception:
        pass


def _ensure_parent_dir(path: str) -> None:
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
    except Exception:
        pass


def _http_json(method: str, url: str, *, headers: Dict[str, str], payload: Optional[Dict[str, Any]] = None, timeout: int = 60) -> Dict[str, Any]:
    data = None
    if payload is not None:
        body = json.dumps(payload).encode("utf-8")
        data = body
        headers = dict(headers)
        headers.setdefault("Content-Type", "application/json")

    req = urllib.request.Request(url=url, data=data, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read()
            if not raw:
                return {}
            try:
                obj = json.loads(raw.decode("utf-8"))
            except Exception:
                return {}
            return obj if isinstance(obj, dict) else {}
    except urllib.error.HTTPError as e:
        try:
            raw = e.read()
            msg = raw.decode("utf-8", errors="ignore") if raw else str(e)
        except Exception:
            msg = str(e)
        raise RuntimeError(f"fal HTTP {e.code} for {url}: {msg}") from e
    except Exception as e:
        raise RuntimeError(f"fal request failed for {url}: {e}") from e


def _download_file(url: str, dest_path: str, *, timeout: int = 120) -> None:
    _ensure_parent_dir(dest_path)
    tmp_path = dest_path + ".tmp"

    req = urllib.request.Request(url=url, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            with open(tmp_path, "wb") as f:
                while True:
                    chunk = resp.read(1024 * 256)
                    if not chunk:
                        break
                    f.write(chunk)
        try:
            os.replace(tmp_path, dest_path)
        except Exception:
            try:
                os.remove(dest_path)
            except Exception:
                pass
            os.rename(tmp_path, dest_path)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except Exception:
            pass


def generate_ltx2_video_to_file(
    *,
    prompt: str,
    output_path: str,
    seed: Optional[int] = None,
    blocking: bool = True,
    model_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Generate an LTX2 video via fal queue and save to output_path.

    Returns: (request_id, video_url)
    """

    fal_key = os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY")
    if not fal_key:
        return None, None

    model = model_id or os.getenv("FAL_LTX2_MODEL") or "fal-ai/ltx-2-19b/distilled/text-to-video/lora"

    enabled = _env_bool("VIS_VIDEO_ENABLED", False)
    if not enabled:
        return None, None

    try:
        _maybe_log_prompt(prompt)
    except Exception:
        pass

    queue_base = "https://queue.fal.run"
    headers = {
        "Authorization": f"Key {fal_key}",
    }

    num_frames = _env_int("VIS_LTX2_NUM_FRAMES", 24)
    fps = _env_float("VIS_LTX2_FPS", 8.0)
    video_size = os.getenv("VIS_LTX2_VIDEO_SIZE") or "landscape_4_3"
    generate_audio = _env_bool("VIS_LTX2_GENERATE_AUDIO", False)
    video_quality = os.getenv("VIS_LTX2_VIDEO_QUALITY") or "low"
    video_write_mode = os.getenv("VIS_LTX2_VIDEO_WRITE_MODE") or "fast"

    payload: Dict[str, Any] = {
        "prompt": prompt,
        "loras": [],
        "num_frames": num_frames,
        "fps": fps,
        "video_size": video_size,
        "generate_audio": generate_audio,
        "video_output_type": "X264 (.mp4)",
        "video_quality": video_quality,
        "video_write_mode": video_write_mode,
    }
    if seed is not None:
        payload["seed"] = int(seed)

    submit_url = f"{queue_base}/{model}"
    submit = _http_json("POST", submit_url, headers=headers, payload=payload, timeout=_env_int("VIS_LTX2_SUBMIT_TIMEOUT_SEC", 60))
    request_id = submit.get("request_id") or submit.get("requestId")
    status_url = submit.get("status_url")
    response_url = submit.get("response_url")
    if not request_id or not status_url or not response_url:
        return None, None

    if not blocking:
        return str(request_id), None

    poll_interval = _env_float("VIS_LTX2_POLL_INTERVAL_SEC", 2.0)
    timeout_sec = _env_int("VIS_LTX2_TIMEOUT_SEC", 600)
    deadline = time.time() + max(10, timeout_sec)

    last_status = None
    while time.time() < deadline:
        st = _http_json("GET", f"{status_url}?logs=0", headers=headers, timeout=_env_int("VIS_LTX2_STATUS_TIMEOUT_SEC", 30))
        status = (st.get("status") or "").upper()
        if status and status != last_status:
            last_status = status
        if status == "COMPLETED":
            break
        time.sleep(max(0.25, float(poll_interval)))

    if last_status != "COMPLETED":
        return str(request_id), None

    result = _http_json("GET", response_url, headers=headers, timeout=_env_int("VIS_LTX2_RESULT_TIMEOUT_SEC", 60))

    video = result.get("video") if isinstance(result, dict) else None
    video_url = None
    if isinstance(video, dict):
        video_url = video.get("url")

    if not video_url:
        return str(request_id), None

    _download_file(str(video_url), output_path, timeout=_env_int("VIS_LTX2_DOWNLOAD_TIMEOUT_SEC", 180))
    return str(request_id), str(video_url)


def generate_ltx2_video_to_latest(
    *,
    prompt: str,
    seed: Optional[int] = None,
    blocking: Optional[bool] = None,
    model_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Convenience wrapper saving to simulation_data/visualizer/latest.mp4."""

    out_dir = os.path.join("simulation_data", "visualizer")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        pass

    latest_path = os.path.join(out_dir, "latest.mp4")

    if blocking is None:
        blocking = _env_bool("VIS_VIDEO_BLOCKING", True)

    request_id, video_url = generate_ltx2_video_to_file(
        prompt=prompt,
        output_path=latest_path,
        seed=seed,
        blocking=bool(blocking),
        model_id=model_id,
    )

    return request_id, video_url, latest_path
