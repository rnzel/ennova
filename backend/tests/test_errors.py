# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Typed application-error tests
from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path

import pytest

from app.domain.processing import (
    ChainedEntry,
    EntryData,
    PersonReference,
    extract_names,
    hash_chain,
    verify_hash_chain,
)
from app.domain.processing.exceptions import (
    AmbiguousName as ProcessingAmbiguousName,
    TamperDetected as ProcessingTamperDetected,
)
from app.errors import (
    ACCESS_DENIED_PUBLIC_MESSAGE,
    AIServiceUnavailable,
    AccessDenied,
    AmbiguousName,
    EnnovaError,
    GENERIC_ERROR_CODE,
    GENERIC_PUBLIC_MESSAGE,
    PolicyFrozen,
    PolicySyntaxError,
    TamperDetected,
    to_public_response,
)


def test_internal_detail_is_excluded_from_all_exception_representations():
    secret_detail = "C:\\private\\vault\\api-key=top-secret"
    error = EnnovaError("internal_failure", "A safe public message.", secret_detail)

    assert error.detail == secret_detail
    assert str(error) == error.public_message
    assert error.code in repr(error)
    assert error.public_message in repr(error)
    assert secret_detail not in str(error)
    assert secret_detail not in repr(error)
    assert error.args == (error.public_message, error.code)
    assert all(secret_detail not in str(argument) for argument in error.args)


def test_access_denied_reasons_have_byte_identical_public_messages():
    reasons = (
        "unregistered",
        "not released",
        "explicit deny",
        "no matching grant",
        "restricted record exists",
    )
    errors = tuple(AccessDenied(detail=reason) for reason in reasons)

    expected = ACCESS_DENIED_PUBLIC_MESSAGE.encode("utf-8")
    assert all(error.public_message.encode("utf-8") == expected for error in errors)
    assert all(str(error).encode("utf-8") == expected for error in errors)
    assert tuple(error.detail for error in errors) == reasons


@pytest.mark.parametrize(
    ("error", "code", "message"),
    (
        (
            AccessDenied("detail"),
            "access_denied",
            ACCESS_DENIED_PUBLIC_MESSAGE,
        ),
        (
            AmbiguousName("private candidate list"),
            "ambiguous_name",
            "I couldn’t identify one person from that name.",
        ),
        (
            TamperDetected("position 37"),
            "tamper_detected",
            "These records could not be verified and are unavailable.",
        ),
        (
            PolicyFrozen("owner policy"),
            "policy_frozen",
            "This policy can no longer be changed.",
        ),
        (
            AIServiceUnavailable("provider response"),
            "ai_service_unavailable",
            "The AI service is temporarily unavailable.",
        ),
    ),
)
def test_typed_errors_use_safe_messages_and_keep_legacy_errors_value_errors(
    error, code, message
):
    assert error.code == code
    assert error.public_message == message
    assert str(error) == message
    assert error.args == (message, code)
    assert isinstance(AmbiguousName("detail"), ValueError)
    assert isinstance(TamperDetected("detail"), ValueError)
    assert isinstance(PolicySyntaxError("Expected token.", 2, 4), ValueError)


def test_moved_errors_are_reexported_from_processing_package():
    from app.domain.processing import AmbiguousName as PublicProcessingAmbiguousName
    from app.domain.processing import TamperDetected as PublicProcessingTamperDetected

    assert ProcessingAmbiguousName is AmbiguousName
    assert ProcessingTamperDetected is TamperDetected
    assert PublicProcessingAmbiguousName is AmbiguousName
    assert PublicProcessingTamperDetected is TamperDetected


def test_legacy_error_details_are_structured_and_private():
    ambiguous_detail = {
        "name": "Alex",
        "candidates": ("Alex Smith", "Alex Jones"),
    }
    ambiguous = AmbiguousName(ambiguous_detail)
    tampered = TamperDetected({"reason": "digest mismatch", "position": 3})

    assert ambiguous.detail == ambiguous_detail
    assert tampered.detail == {"reason": "digest mismatch", "position": 3}
    assert ambiguous.public_message not in repr(ambiguous.detail)
    assert "Alex Smith" not in repr(ambiguous)
    assert "position" not in repr(tampered)


def test_processing_errors_keep_candidate_and_chain_position_details_private():
    people = (
        PersonReference("p1", "Alex Smith", ("Alex",)),
        PersonReference("p2", "Alex Jones", ("Alex",)),
    )
    with pytest.raises(AmbiguousName) as ambiguous_error:
        extract_names("Alex called.", people)

    entry = EntryData("A private note.", datetime(2026, 11, 14, tzinfo=timezone.utc))
    chain = hash_chain((entry,))
    tampered_chain: tuple[ChainedEntry, ...] = (
        replace(chain[0], previous_hash="0" * 64),
    )
    with pytest.raises(TamperDetected) as tamper_error:
        verify_hash_chain(tampered_chain)

    assert ambiguous_error.value.detail == {
        "name": "Alex",
        "candidates": ("Alex Smith", "Alex Jones"),
    }
    assert tamper_error.value.detail == {
        "reason": "hash-chain link mismatch",
        "position": 0,
    }
    assert "Alex Smith" not in str(ambiguous_error.value)
    assert "0" * 64 not in repr(tamper_error.value)


def test_policy_syntax_error_keeps_location_and_readable_public_diagnostic():
    error = PolicySyntaxError("Expected a newline.", 4, 9, detail="parser trace")

    assert error.code == "policy_syntax_error"
    assert error.line == 4
    assert error.column == 9
    assert error.message == "Expected a newline."
    assert str(error) == "Line 4, column 9: Expected a newline."
    assert error.public_message == str(error)
    assert "parser trace" not in str(error)
    assert error.args == (error.public_message, error.code)


def test_public_response_uses_only_typed_public_fields():
    error = AccessDenied(detail="C:\\private\\secret")

    assert to_public_response(error) == {
        "code": "access_denied",
        "message": ACCESS_DENIED_PUBLIC_MESSAGE,
    }


@pytest.mark.parametrize(
    "exc",
    (
        None,
        ValueError("C:\\private\\vault\\secret.txt"),
    ),
)
def test_public_response_never_raises_or_exposes_untyped_exceptions(exc):
    assert to_public_response(exc) == {
        "code": GENERIC_ERROR_CODE,
        "message": GENERIC_PUBLIC_MESSAGE,
    }


def test_public_response_does_not_expose_chained_exception_details():
    try:
        raise AccessDenied(detail="restricted candidate") from ValueError(
            "C:\\private\\vault\\secret.txt"
        )
    except AccessDenied as error:
        response = to_public_response(error)

    assert response == {
        "code": "access_denied",
        "message": ACCESS_DENIED_PUBLIC_MESSAGE,
    }
    assert "secret.txt" not in repr(response)
    assert "restricted candidate" not in repr(response)


def test_public_response_fallback_is_safe_for_an_unusual_error_subclass():
    class BrokenError(EnnovaError):
        def __getattribute__(self, name):
            if name == "public_message":
                raise RuntimeError("C:\\private\\secret")
            return super().__getattribute__(name)

    error = BrokenError("broken", "safe", "hidden")

    assert to_public_response(error) == {
        "code": GENERIC_ERROR_CODE,
        "message": GENERIC_PUBLIC_MESSAGE,
    }


def test_error_modules_do_not_import_flask_or_database_packages():
    errors_dir = Path(__file__).parents[1] / "app" / "errors"
    source = "\n".join(
        path.read_text(encoding="utf-8")
        for path in errors_dir.glob("*.py")
    ).casefold()

    assert "import flask" not in source
    assert "from flask" not in source
    assert "sqlalchemy" not in source
    assert "pymysql" not in source
