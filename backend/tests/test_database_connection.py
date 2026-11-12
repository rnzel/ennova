# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Infrastructure / database connectivity smoke test
import os

import pytest
from sqlalchemy import text

from app import create_app
from app.extensions import db


@pytest.mark.skipif(
    not os.getenv("DATABASE_URL") or "mysql" not in os.getenv("DATABASE_URL", "").lower(),
    reason="MySQL database credentials are not configured for this environment.",
)
def test_database_connection():
    app = create_app()
    with app.app_context():
        with db.engine.connect() as connection:
            result = connection.execute(text("SELECT 1"))
            assert result.scalar() == 1
