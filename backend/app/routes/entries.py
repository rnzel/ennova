# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP entry routes
from __future__ import annotations

import re

from flask import Blueprint, current_app, jsonify

from app.ai.model_summaries import store_derived_summary
from app.domain.accounts import AccountRole
from app.domain.diary import LetterEntry
from app.errors import ConflictError, LETTER_OF_WISHES_DISCLAIMER
from app.routes.common import bearer_required, current_account, json_body

entries_bp = Blueprint("entries", __name__)
_ENTRY_ID_RE = re.compile(r"[a-z0-9][a-z0-9_.-]{0,63}\Z")
MAX_ENTRY_LENGTH = 10_000


def _entry_payload(record):
    payload = {
        "entry_id": record.entry.entry_id,
        "kind": record.entry.kind,
        "created_at": record.entry.created_at.isoformat(),
        "topics": list(record.topics),
    }
    if isinstance(record.entry, LetterEntry):
        payload["disclaimer"] = LETTER_OF_WISHES_DISCLAIMER
    return payload


@entries_bp.post("/entries")
@bearer_required(AccountRole.OWNER)
def create_entry():
    account = current_account()
    state = current_app.extensions["api_state"]
    if state.is_triggered(account.owner_id):
        raise PermissionError("operation unavailable")
    body = json_body()
    entry_id = body["entry_id"]
    if not isinstance(entry_id, str) or not _ENTRY_ID_RE.fullmatch(entry_id):
        raise ValueError("entry_id is invalid.")
    content = body["content"]
    if not isinstance(content, str) or not content or len(content) > MAX_ENTRY_LENGTH:
        raise ValueError("entry content is invalid.")
    clock = current_app.extensions["clock"]
    service = current_app.extensions["diary_service"]
    try:
        if body.get("kind") == "letter":
            record = service.add_letter_entry(
                account.owner_id,
                entry_id,
                content,
                body["title"],
                body["recipient"],
                clock(),
            )
        elif body.get("kind") == "diary":
            record = service.add_diary_entry(
                account.owner_id, entry_id, content, clock()
            )
        else:
            raise ValueError("kind is invalid.")
    except ValueError as error:
        if "already exists" in str(error):
            raise ConflictError() from error
        raise
    try:
        store_derived_summary(
            record,
            current_app.extensions["summarizer"],
            current_app.extensions["summary_store"],
        )
    except Exception:
        pass
    return jsonify(_entry_payload(record)), 201


@entries_bp.get("/entries")
@bearer_required(AccountRole.OWNER)
def list_entries():
    account = current_account()
    records = current_app.extensions["diary_service"].list_entries(account.owner_id)
    return jsonify({"entries": [_entry_payload(record) for record in records]}), 200
