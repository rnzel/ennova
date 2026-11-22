# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Typed application errors
from .base import (
    ACCESS_DENIED_PUBLIC_MESSAGE,
    GENERIC_ERROR_CODE,
    GENERIC_PUBLIC_MESSAGE,
    LETTER_OF_WISHES_DISCLAIMER,
    EnnovaError,
    to_public_response,
)
from .policy_syntax import PolicySyntaxError
from .typed import (
    AIServiceUnavailable,
    AccessDenied,
    AmbiguousName,
    AuthenticationError,
    ConflictError,
    InvalidBeneficiaryError,
    PolicyFrozen,
    TamperDetected,
    UnknownWritingMode,
)

__all__ = [
    "ACCESS_DENIED_PUBLIC_MESSAGE",
    "AIServiceUnavailable",
    "AccessDenied",
    "AmbiguousName",
    "AuthenticationError",
    "ConflictError",
    "EnnovaError",
    "GENERIC_ERROR_CODE",
    "GENERIC_PUBLIC_MESSAGE",
    "LETTER_OF_WISHES_DISCLAIMER",
    "PolicyFrozen",
    "PolicySyntaxError",
    "TamperDetected",
    "to_public_response",
    "UnknownWritingMode",
    "InvalidBeneficiaryError",
]
