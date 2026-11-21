# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP grounded-Q&A route
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.ai.prompts import NEUTRAL_REPLY
from app.domain.accounts import AccountRole
from app.routes.common import (
    account_or_remote_key,
    bearer_required,
    current_account,
    json_body,
    limiter,
)

ask_bp = Blueprint("ask", __name__)
MAX_QUESTION_LENGTH = 2_000


@ask_bp.post("/ask")
@bearer_required()
@limiter.limit("20 per minute", key_func=account_or_remote_key)
def ask():
    body = json_body()
    question = body["question"]
    if not isinstance(question, str) or not question.strip() or len(question) > MAX_QUESTION_LENGTH:
        raise ValueError("question is invalid.")
    account = current_account()
    if account.role is AccountRole.OWNER:
        return jsonify({"answer": NEUTRAL_REPLY, "citations": []}), 200
    model = current_app.extensions.get("model_client")
    active = current_app.extensions["api_state"].active_policy(account.owner_id)
    if model is None or active is None:
        return jsonify({"answer": NEUTRAL_REPLY, "citations": []}), 200
    facts = current_app.extensions["facts_builder"](account.owner_id)
    response = current_app.extensions["qa_service"].answer(
        question,
        owner_id=account.owner_id,
        asker=account.person_id,
        policy_source=active.source,
        app_facts=facts,
        today=current_app.extensions["today"](),
    )
    payload = {
        "answer": response.text,
        "citations": [
            {"entry_id": item.entry_id, "date": item.entry_date.isoformat()}
            for item in response.citations
        ],
    }
    if response.disclaimer is not None:
        payload["disclaimer"] = response.disclaimer
    return jsonify(payload), 200
