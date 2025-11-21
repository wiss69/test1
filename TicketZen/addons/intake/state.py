import json
import logging
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image

LOGGER = logging.getLogger("ticketzen.intake.state")


def ensure_dirs(base_dir: Path, token: str) -> Path:
    target = base_dir / "intake" / token
    target.mkdir(parents=True, exist_ok=True)
    return target


def file_path(base_dir: Path, token: str, *parts: str) -> Path:
    return ensure_dirs(base_dir, token) / Path(*parts)


def set_status(base_dir: Path, token: str, state: str, progress: Optional[int] = None, error: Optional[str] = None, result: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    target = file_path(base_dir, token, "status.json")
    payload: Dict[str, Any] = {"state": state}
    if progress is not None:
        payload["progress"] = progress
    if error:
        payload["error"] = error
    if result is not None:
        payload["result"] = result
    try:
        target.write_text(json.dumps(payload, ensure_ascii=False, indent=2))
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to persist status: %s", exc)
    return payload


def get_status(base_dir: Path, token: str) -> Dict[str, Any]:
    target = file_path(base_dir, token, "status.json")
    if target.exists():
        try:
            data = json.loads(target.read_text())
            data.setdefault("progress", 0)
            data.setdefault("state", "pending")
            return {"ok": True, **data}
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to read status: %s", exc)
    return {"ok": True, "state": "pending", "progress": 0}


def save_upload(base_dir: Path, token: str, file_storage) -> Dict[str, Any]:
    try:
        folder = ensure_dirs(base_dir, token)
        suffix = Path(file_storage.filename or "upload").suffix or ".bin"
        dest = folder / f"original{suffix}"
        file_storage.save(dest)
        set_status(base_dir, token, "uploaded", progress=20)
        return {"ok": True, "path": dest}
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Upload failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def rotate_image(base_dir: Path, token: str, degrees: Optional[int] = None, direction: Optional[str] = None) -> Dict[str, Any]:
    try:
        folder = ensure_dirs(base_dir, token)
        originals = list(folder.glob("original.*"))
        if not originals:
            return {"ok": False, "error": "Aucun fichier"}
        original = originals[0]
        img = Image.open(original)
        if direction == "cw":
            degrees = -90
        elif direction == "ccw":
            degrees = 90
        deg = degrees or 0
        rotated = img.rotate(deg, expand=True)
        rotated.save(original)
        return {"ok": True, "degrees": deg}
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Rotation failed: %s", exc)
        return {"ok": False, "error": str(exc)}


def result_preview(base_dir: Path, token: str) -> Dict[str, Any]:
    target = file_path(base_dir, token, "result.json")
    if not target.exists():
        return {"ok": False, "error": "Aucun résultat"}
    try:
        data = json.loads(target.read_text())
        return {"ok": True, "result": data}
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.warning("Failed to read result: %s", exc)
        return {"ok": False, "error": str(exc)}
