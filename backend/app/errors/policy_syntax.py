# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Typed policy-language errors
from .base import EnnovaError


class PolicySyntaxError(EnnovaError, ValueError):
    """A policy-language error with a source line, column, and readable detail."""

    def __init__(
        self, message: str, line: int, column: int, detail: object | None = None
    ) -> None:
        """Create a syntax error at a one-based source location."""
        self.message = message
        self.line = line
        self.column = column
        super().__init__(
            "policy_syntax_error",
            f"Line {line}, column {column}: {message}",
            detail=detail,
        )
