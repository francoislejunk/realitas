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


def generate_image_to_file(
    *,
    prompt: str,
    output_path: str,
    seed: Optional[int] = None,
    blocking: bool = True,
    model_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str]]:
    fal_key = os.getenv("FAL_API_KEY") or os.getenv("FAL_KEY")
    if not fal_key:
        return None, None

    enabled = _env_bool("VIS_IMAGE_ENABLED", True)
    if not enabled:
        return None, None

    model = model_id or os.getenv("FAL_IMAGE_MODEL") or "fal-ai/flux/schnell"

    queue_base = "https://queue.fal.run"
    headers = {
        "Authorization": f"Key {fal_key}",
    }

    width = _env_int("VIS_IMAGE_WIDTH", 1024)
    height = _env_int("VIS_IMAGE_HEIGHT", 768)
    steps = _env_int("VIS_IMAGE_STEPS", 8)

    payload: Dict[str, Any] = {
        "prompt": str(prompt or ""),
        "image_size": {"width": int(width), "height": int(height)},
        "num_inference_steps": int(steps),
    }
    if seed is not None:
        payload["seed"] = int(seed)

    submit_url = f"{queue_base}/{model}"
    submit = _http_json("POST", submit_url, headers=headers, payload=payload, timeout=_env_int("VIS_IMAGE_SUBMIT_TIMEOUT_SEC", 60))
    request_id = submit.get("request_id") or submit.get("requestId")
    status_url = submit.get("status_url")
    response_url = submit.get("response_url")
    if not request_id or not status_url or not response_url:
        return None, None

    if not blocking:
        return str(request_id), None

    poll_interval = _env_float("VIS_IMAGE_POLL_INTERVAL_SEC", 2.0)
    timeout_sec = _env_int("VIS_IMAGE_TIMEOUT_SEC", 300)
    deadline = time.time() + max(10, timeout_sec)

    last_status = None
    while time.time() < deadline:
        st = _http_json("GET", f"{status_url}?logs=0", headers=headers, timeout=_env_int("VIS_IMAGE_STATUS_TIMEOUT_SEC", 30))
        status = (st.get("status") or "").upper()
        if status and status != last_status:
            last_status = status
        if status == "COMPLETED":
            break
        time.sleep(max(0.25, float(poll_interval)))

    if last_status != "COMPLETED":
        return str(request_id), None

    result = _http_json("GET", response_url, headers=headers, timeout=_env_int("VIS_IMAGE_RESULT_TIMEOUT_SEC", 60))

    image_url = None
    if isinstance(result, dict):
        imgs = result.get("images")
        if isinstance(imgs, list) and imgs:
            first = imgs[0]
            if isinstance(first, dict):
                image_url = first.get("url")

    if not image_url:
        return str(request_id), None

    _download_file(str(image_url), output_path, timeout=_env_int("VIS_IMAGE_DOWNLOAD_TIMEOUT_SEC", 180))
    return str(request_id), str(image_url)


def generate_image_to_latest(
    *,
    prompt: str,
    seed: Optional[int] = None,
    blocking: Optional[bool] = None,
    model_id: Optional[str] = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    out_dir = os.path.join("simulation_data", "visualizer")
    try:
        os.makedirs(out_dir, exist_ok=True)
    except Exception:
        pass

    latest_path = os.path.join(out_dir, "latest.png")

    if blocking is None:
        blocking = _env_bool("VIS_IMAGE_BLOCKING", True)

    request_id, image_url = generate_image_to_file(
        prompt=prompt,
        output_path=latest_path,
        seed=seed,
        blocking=bool(blocking),
        model_id=model_id,
    )

    return request_id, image_url, latest_path
