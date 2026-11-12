# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Infrastructure / Flask application factory
from __future__ import annotations

from flask import Flask, jsonify

from .config import BaseConfig, get_database_connect_args
from .extensions import db, migrate


def create_app() -> Flask:
    """Create and configure the Flask application instance."""
    app = Flask(__name__)
    app.config.from_object(BaseConfig)

    if app.config["SQLALCHEMY_DATABASE_URI"].startswith("mysql"):
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            "connect_args": get_database_connect_args()
        }

    db.init_app(app)
    migrate.init_app(app, db)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"}), 200

    return app
