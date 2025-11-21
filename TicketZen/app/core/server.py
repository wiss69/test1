import json
import logging
import os
import platform
import secrets
from datetime import datetime
from pathlib import Path
from typing import Dict

from dotenv import load_dotenv
from flask import Flask, jsonify, redirect, render_template, request, send_from_directory, url_for

from addons.intake.api import intake_bp
from addons.intake import qrcode as qr_utils

load_dotenv()

LOGGER = logging.getLogger("ticketzen.server")


def storage_root() -> Path:
    app_name = os.getenv("APP_NAME", "TicketZen")
    if platform.system() == "Windows":
        base = Path(os.getenv("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
    else:
        base = Path.home() / "Library" / "Application Support" if platform.system() == "Darwin" else Path.home() / f".{app_name.lower()}"
    target = base / app_name / "data"
    target.mkdir(parents=True, exist_ok=True)
    return target


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(Path(__file__).resolve().parent.parent / "static"), template_folder=str(Path(__file__).resolve().parent.parent / "templates"))
    app.config["JSON_AS_ASCII"] = False
    app.config["DATA_ROOT"] = storage_root()
    app.config["SECRET_KEY"] = os.getenv("FLASK_SECRET", secrets.token_hex(16))
    app.register_blueprint(intake_bp)

    @app.after_request
    def add_cors_headers(response):
        origin = request.headers.get("Origin")
        if origin and ("localhost" in origin or "127.0.0.1" in origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Vary"] = "Origin"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type,Authorization"
            response.headers["Access-Control-Allow-Methods"] = "GET,POST,OPTIONS"
        return response

    @app.errorhandler(Exception)
    def handle_global_error(exc):
        LOGGER.exception("Unhandled error: %s", exc)
        if request.path.startswith("/api/"):
            return jsonify({"ok": False, "error": str(exc)}), 200
        return render_template("error.html", message=str(exc)), 500

    @app.route("/")
    def index():
        return render_template("index.html")

    @app.route("/scanner")
    def scanner():
        pin = qr_utils.generate_pin()
        payload_url = qr_utils.make_payload_url(request.url_root.rstrip("/"), pin)
        return render_template("scanner.html", pin=pin, payload_url=payload_url)

    @app.route("/refresh_pin")
    def refresh_pin():
        pin = qr_utils.generate_pin()
        payload_url = qr_utils.make_payload_url(request.url_root.rstrip("/"), pin)
        return jsonify({"ok": True, "pin": pin, "url": payload_url})

    @app.route("/m/<pin>")
    def mobile_intake(pin: str):
        return render_template("mobile_intake.html", pin=pin)

    @app.route("/expenses")
    def expenses():
        return render_template("expenses.html")

    @app.route("/history")
    def history():
        return render_template("history.html")

    @app.route("/warranty")
    def warranty():
        return render_template("warranty.html")

    @app.route("/retraction")
    def retraction():
        return render_template("retraction.html")

    @app.route("/dashboard")
    def dashboard():
        return render_template("dashboard.html")

    @app.route("/settings")
    def settings():
        return render_template("settings.html")

    @app.route("/api/metrics")
    def metrics():
        stats_path = app.config["DATA_ROOT"] / "metrics.json"
        payload: Dict[str, object] = {
            "ok": True,
            "scans": 0,
            "avg_latency_ms": None,
            "f1_total_date": None,
            "alerts_rate": None,
        }
        try:
            if stats_path.exists():
                payload.update(json.loads(stats_path.read_text()))
        except Exception as exc:  # pragma: no cover - defensive
            LOGGER.warning("Failed to read metrics: %s", exc)
        return jsonify(payload)

    @app.route("/debug/azure")
    def debug_azure():
        endpoint = os.getenv("AZURE_DI_ENDPOINT", "")
        key = os.getenv("AZURE_DI_KEY", "")
        response = {
            "ok": True,
            "route": os.getenv("AZURE_DI_ROUTE", "formrecognizer_v21"),
            "api_version": os.getenv("AZURE_DI_API_VERSION", "v2.1"),
            "timeout": int(os.getenv("AZURE_DI_TIMEOUT_SEC", "90")),
            "dry_run": bool(int(os.getenv("OCR_DRY_RUN", "0"))),
            "endpoint_set": bool(endpoint),
            "key_set": bool(key),
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }
        return jsonify(response)

    @app.route("/healthz")
    def healthz():
        return jsonify({"ok": True, "app": os.getenv("APP_NAME", "TicketZen")})

    return app


__all__ = ["create_app", "storage_root"]
