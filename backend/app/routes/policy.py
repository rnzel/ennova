# ENNOVA (Alaala) – Team members: Roldan Jr. Bazares – Front End; Ranzel Jay Gobris – Back End; Bart Jayson Lola – Q/A; Jallil Sultan – UI/UX Designer; Jezelle Gabion – Documentator
# Paradigm: Scripting HTTP policy boundary over the language parser
from __future__ import annotations

from flask import Blueprint, current_app, jsonify

from app.domain.accounts import AccountRole
from app.errors import PolicyFrozen, PolicySyntaxError
from app.policy import parse
from app.routes.common import bearer_required, current_account, json_body

policy_bp = Blueprint("policy", __name__)


@policy_bp.put("/policy")
@bearer_required(AccountRole.OWNER)
def update_policy():
    account = current_account()
    state = current_app.extensions["api_state"]
    if state.is_triggered(account.owner_id):
        raise PolicyFrozen()
    body = json_body()
    source = body["source"]
    try:
        policy = parse(source)
    except PolicySyntaxError as error:
        state.add_audit(
            current_app.extensions["audit_record"](
                account.account_id, account.owner_id, "policy_update",
                "rejected_syntax", current_app.extensions["clock"]()
            )
        )
        raise error
    version = state.accept_policy(
        account.owner_id, source, policy, current_app.extensions["clock"]()
    )
    return jsonify({"version": version.version, "status": "active"}), 201
