import io
import logging
import os
import time
from pathlib import Path
from typing import Any, Dict

from flask import Blueprint, current_app, jsonify, request

from addons.intake import state
from addons.ocr import postprocess_fr
from addons.ocr.providers import azure_client

LOGGER = logging.getLogger("ticketzen.intake.api")

intake_bp = Blueprint("intake", __name__, url_prefix="/api/intake")


def _base_dir() -> Path:
    return Path(current_app.config.get("DATA_ROOT"))


@intake_bp.route("/<token>/status", methods=["GET"])
def status(token: str):
    payload = state.get_status(_base_dir(), token)
    payload["ok"] = True
    return jsonify(payload)


@intake_bp.route("/<token>/upload", methods=["POST"])
def upload(token: str):
    start = time.time()
    file = request.files.get("file")
    if not file:
        return jsonify({"ok": False, "error": "Aucun fichier"})
    resp = state.save_upload(_base_dir(), token, file)
    LOGGER.info("/upload token=%s duration=%.1fms", token, (time.time() - start) * 1000)
    if not resp.get("ok"):
        state.set_status(_base_dir(), token, "error", error=resp.get("error"))
    return jsonify(resp)


@intake_bp.route("/rotate", methods=["POST"])
def rotate():
    data = request.get_json(force=True, silent=True) or {}
    token = data.get("token")
    if not token:
        return jsonify({"ok": False, "error": "token manquant"})
    resp = state.rotate_image(_base_dir(), token, degrees=data.get("degrees"), direction=data.get("direction"))
    if not resp.get("ok"):
        state.set_status(_base_dir(), token, "error", error=resp.get("error"))
    return jsonify(resp)


@intake_bp.route("/<token>/analyze", methods=["POST"])
def analyze(token: str):
    base_dir = _base_dir()
    folder = state.ensure_dirs(base_dir, token)
    originals = list(folder.glob("original.*"))
    if not originals:
        return jsonify({"ok": False, "error": "Aucun fichier"})
    original = originals[0]
    state.set_status(base_dir, token, "analyzing", progress=50)
    start = time.time()
    try:
        content = original.read_bytes()
        content_type = "application/octet-stream"
        if original.suffix.lower() == ".pdf":
            content_type = "application/pdf"
        elif original.suffix.lower() in {".png"}:
            content_type = "image/png"
        elif original.suffix.lower() in {".jpg", ".jpeg"}:
            content_type = "image/jpeg"
        ocr_result = azure_client.analyze_document(content, content_type, config=_azure_config(), logger=LOGGER)
        processed = postprocess_fr.normalize_result(ocr_result)
        result_path = folder / "result.json"
        result_path.write_text(postprocess_fr.dump_json(processed))
        payload = state.set_status(base_dir, token, "done", progress=100, result=processed)
        LOGGER.info("/analyze token=%s duration=%.1fms", token, (time.time() - start) * 1000)
        return jsonify({"ok": True, **payload})
    except Exception as exc:  # pragma: no cover - defensive
        LOGGER.exception("Analyze failed: %s", exc)
        payload = state.set_status(base_dir, token, "error", error=str(exc))
        return jsonify({"ok": False, **payload})


def _azure_config() -> Dict[str, Any]:
    return {
        "endpoint": os.getenv("AZURE_DI_ENDPOINT", ""),
        "key": os.getenv("AZURE_DI_KEY", ""),
        "route": os.getenv("AZURE_DI_ROUTE", "formrecognizer_v21"),
        "api_version": os.getenv("AZURE_DI_API_VERSION", "v2.1"),
        "timeout": int(os.getenv("AZURE_DI_TIMEOUT_SEC", "90")),
        "dry_run": bool(int(os.getenv("OCR_DRY_RUN", "0"))),
        "cloud_enabled": bool(int(os.getenv("TICKETZEN_OCR_CLOUD_ENABLED", "1"))),
        "vendor": os.getenv("TICKETZEN_OCR_CLOUD_VENDOR", "azure"),
    }
