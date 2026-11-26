# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Lead Developer / Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting authenticated owner-Q&A HTTP boundary
from __future__ import annotations

import re

from flask import Blueprint, current_app, jsonify

from app.domain.accounts import AccountRole
from app.errors import AIServiceUnavailable
from app.routes.common import (
    account_or_remote_key,
    bearer_required,
    current_account,
    json_body,
    limiter,
)

owner_ask_bp = Blueprint("owner_ask", __name__)
MAX_QUESTION_LENGTH = 2_000
_CONVERSATION_ID_RE = re.compile(r"[a-f0-9]{32}\Z")


@owner_ask_bp.post("/owner/ask")
@bearer_required(AccountRole.OWNER)
@limiter.limit("20 per minute", key_func=account_or_remote_key)
def owner_ask():
    body = json_body()
    question = body.get("question")
    if (
        not isinstance(question, str)
        or not question.strip()
        or len(question) > MAX_QUESTION_LENGTH
    ):
        raise ValueError("question is invalid")

    conversation_id = body.get("conversation_id")
    if conversation_id is not None and (
        not isinstance(conversation_id, str)
        or not _CONVERSATION_ID_RE.fullmatch(conversation_id)
    ):
        raise ValueError("conversation_id is invalid")

    service = current_app.extensions.get("owner_qa_service")
    if service is None:
        error = AIServiceUnavailable(detail="model provider is not configured")
        return jsonify({"code": error.code, "message": error.public_message}), 503

    account = current_account()
    try:
        result = service.answer(
            question,
            owner_id=account.owner_id,
            today=current_app.extensions["today"](),
            conversation_id=conversation_id,
        )
    except AIServiceUnavailable as error:
        return jsonify({"code": error.code, "message": error.public_message}), 503

    payload = {
        "answer": result.response.text,
        "no_record": result.no_record,
        "conversation_id": result.conversation_id,
        "citations": [
            {"entry_id": citation.entry_id, "date": citation.entry_date.isoformat()}
            for citation in result.response.citations
        ],
    }
    if result.response.disclaimer is not None:
        payload["disclaimer"] = result.response.disclaimer
    return jsonify(payload), 200
