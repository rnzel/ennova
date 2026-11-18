# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Infrastructure / Flask application factory
from __future__ import annotations

import logging
import shutil
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from flask import Flask, jsonify
from flask_limiter.errors import RateLimitExceeded

from app.ai.model_summaries import ModelSummarizer
from app.ai.provider import create_model_client
from app.ai.summaries import FakeSummarizer, InMemorySummaryStore
from app.domain.accounts import InMemoryUserRepository
from app.domain.diary import InMemoryEntryRepository
from app.errors import (
    EnnovaError,
    GENERIC_ERROR_CODE,
    GENERIC_PUBLIC_MESSAGE,
    PolicySyntaxError,
    to_public_response,
)
from app.policy import PrologAccessBridge
from app.services.access_facts import build_app_facts
from app.services.api_state import AuditRecord, InMemoryApiState
from app.services.auth_service import AuthService
from app.services.diary_service import DiaryService
from app.services.grounded_qa import GroundedQAService
from app.routes import ask_bp, auth_bp, death_bp, entries_bp, policy_bp
from app.routes.common import limiter
from .config import BaseConfig, get_database_connect_args
from .extensions import db, migrate


def create_app(
    *,
    clock=None,
    model_client=None,
    summarizer=None,
    config_overrides: dict | None = None,
) -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(BaseConfig)
    if config_overrides:
        app.config.update(config_overrides)
    app.config["MAX_CONTENT_LENGTH"] = BaseConfig.MAX_CONTENT_LENGTH

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": get_database_connect_args()
        }

    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)

    user_repository = InMemoryUserRepository()
    entry_repository = InMemoryEntryRepository()
    api_state = InMemoryApiState()
    app_clock = clock or (lambda: datetime.now(timezone.utc))
    auth_service = AuthService(
        user_repository,
        clock=app_clock,
        jwt_secret=app.config.get("JWT_SECRET_KEY"),
    )
    diary_service = DiaryService(entry_repository)
    summary_store = InMemorySummaryStore()
    if model_client is None:
        try:
            model_client = create_model_client()
        except EnnovaError:
            model_client = None
    app_summarizer = summarizer or (
        ModelSummarizer(model_client) if model_client is not None else FakeSummarizer()
    )
    swipl = shutil.which(app.config["SWIPL_EXECUTABLE"])
    if swipl is None:
        swipl = app.config["SWIPL_EXECUTABLE"]
    bridge = PrologAccessBridge(swipl)
    try:
        app_timezone = ZoneInfo(app.config["APP_TIMEZONE"])
    except Exception:
        app_timezone = timezone.utc

    def today():
        return app_clock().astimezone(app_timezone).date()

    def facts(owner_id):
        return build_app_facts(
            owner_id,
            diary_service.list_entries(owner_id),
            auth_service.registered_person_ids(owner_id),
            death_triggered=api_state.is_triggered(owner_id),
            policy_frozen=api_state.is_triggered(owner_id),
        )

    app.extensions.update(
        {
            "auth_service": auth_service,
            "diary_service": diary_service,
            "api_state": api_state,
            "audit_record": AuditRecord,
            "clock": app_clock,
            "today": today,
            "model_client": model_client,
            "summarizer": app_summarizer,
            "summary_store": summary_store,
            "facts_builder": facts,
            "limiter": limiter,
        }
    )
    if model_client is not None:
        app.extensions["qa_service"] = GroundedQAService(
            diary_service,
            bridge,
            model_client,
            summary_store,
        )

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify(
            {"code": "invalid_request", "message": GENERIC_PUBLIC_MESSAGE}
        ), 400

    @app.errorhandler(Exception)
    def handle_error(error):
        if isinstance(error, PolicySyntaxError):
            response = to_public_response(error)
            response.update({"line": error.line, "column": error.column})
            return jsonify(response), 400
        if isinstance(error, EnnovaError):
            response = to_public_response(error)
            status = (
                401 if error.code == "authentication_error"
                else 409 if error.code == "conflict"
                else 400
            )
            return jsonify(response), status
        if isinstance(error, PermissionError):
            return jsonify(
                {"code": "operation_unavailable", "message": GENERIC_PUBLIC_MESSAGE}
            ), 403
        if isinstance(error, ValueError):
            return jsonify(
                {"code": "invalid_request", "message": GENERIC_PUBLIC_MESSAGE}
            ), 400
        logging.getLogger(__name__).error(
            "Unhandled API error: %s", type(error).__name__
        )
        return jsonify(
            {"code": GENERIC_ERROR_CODE, "message": GENERIC_PUBLIC_MESSAGE}
        ), 500

    @app.errorhandler(404)
    def not_found(error):
        return jsonify(
            {"code": "not_found", "message": GENERIC_PUBLIC_MESSAGE}
        ), 404

    @app.after_request
    def security_headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers.pop("Server", None)
        return response

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(
            {"code": "request_too_large", "message": GENERIC_PUBLIC_MESSAGE}
        ), 413

    @app.errorhandler(RateLimitExceeded)
    def rate_limited(error):
        return jsonify(
            {"code": "rate_limited", "message": GENERIC_PUBLIC_MESSAGE}
        ), 429

    app.register_blueprint(auth_bp)
    app.register_blueprint(entries_bp)
    app.register_blueprint(policy_bp)
    app.register_blueprint(ask_bp)
    app.register_blueprint(death_bp)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
