# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Typed application errors
from __future__ import annotations

from .base import ACCESS_DENIED_PUBLIC_MESSAGE, EnnovaError


class AccessDenied(EnnovaError):
    """Raised when an access check does not permit the requested operation."""

    def __init__(self, detail: object | None = None) -> None:
        """Create an access error with the shared neutral public message."""
        super().__init__(
            "access_denied", ACCESS_DENIED_PUBLIC_MESSAGE, detail=detail
        )


class AmbiguousName(EnnovaError, ValueError):
    """Raised when a name could identify multiple people; details stay private."""

    def __init__(self, *args: object) -> None:
        """Keep ValueError's positional constructor while hiding its arguments."""
        detail: object | None
        if len(args) == 1:
            detail = args[0]
        else:
            detail = args or None
        super().__init__(
            "ambiguous_name",
            "I couldn’t identify one person from that name.",
            detail=detail,
        )


class TamperDetected(EnnovaError, ValueError):
    """Raised for integrity failures; verify only after access permits an entry."""

    def __init__(self, *args: object) -> None:
        """Keep ValueError's positional constructor while hiding its arguments."""
        detail: object | None
        if len(args) == 1:
            detail = args[0]
        else:
            detail = args or None
        super().__init__(
            "tamper_detected",
            "These records could not be verified and are unavailable.",
            detail=detail,
        )


class PolicyFrozen(EnnovaError):
    """Raised when a frozen legacy policy is changed."""

    def __init__(self, detail: object | None = None) -> None:
        """Create a policy-freeze error with an internal-only detail."""
        super().__init__(
            "policy_frozen",
            "This policy can no longer be changed.",
            detail=detail,
        )


class AIServiceUnavailable(EnnovaError):
    """Raised when the grounded-answer service cannot provide a response."""

    def __init__(self, detail: object | None = None) -> None:
        """Create an AI-service error with an internal-only detail."""
        super().__init__(
            "ai_service_unavailable",
            "The AI service is temporarily unavailable.",
            detail=detail,
        )


class UnknownWritingMode(EnnovaError, ValueError):
    """Raised when a policy names a writing mode that is not registered."""

    def __init__(self, detail: object | None = None) -> None:
        """Create a safe unknown-mode error without exposing the mode name."""
        super().__init__(
            "unknown_writing_mode",
            "The requested writing mode is not available.",
            detail=detail,
        )


class AuthenticationError(EnnovaError):
    """Raised when authentication cannot safely complete."""

    def __init__(self, detail: object | None = None) -> None:
        """Create a generic authentication error with private detail."""
        super().__init__(
            "authentication_error",
            "Authentication failed.",
            detail=detail,
        )


class InvalidBeneficiaryError(EnnovaError):
    """Raised when beneficiary registration cannot safely complete."""

    def __init__(self, detail: object | None = None) -> None:
        """Create one generic invitation failure for every redemption failure."""
        super().__init__(
            "invalid_beneficiary",
            "Beneficiary registration failed.",
            detail=detail,
        )
