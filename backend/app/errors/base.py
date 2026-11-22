# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Typed application errors

ACCESS_DENIED_PUBLIC_MESSAGE = (
    "I couldn’t find any information in the records available to me."
)
LETTER_OF_WISHES_DISCLAIMER = (
    "Letters of Wishes in ENNOVA are personal messages and are not legal wills "
    "or substitutes for legally executed estate documents. ENNOVA does not "
    "provide legal advice."
)
GENERIC_ERROR_CODE = "internal_error"
GENERIC_PUBLIC_MESSAGE = "An unexpected error occurred."


class EnnovaError(Exception):
    """Base error that keeps internal detail out of all public representations."""

    def __init__(
        self, code: str, public_message: str, detail: object | None = None
    ) -> None:
        """Create a typed error with a safe public message and private detail."""
        self.code = code
        self.public_message = public_message
        self.detail = detail
        super().__init__(public_message, code)

    def __str__(self) -> str:
        """Return only the public message."""
        return self.public_message

    def __repr__(self) -> str:
        """Represent only the public message and stable error code."""
        return (
            f"{type(self).__name__}(code={self.code!r}, "
            f"public_message={self.public_message!r})"
        )


def to_public_response(exc: object) -> dict[str, str]:
    """Return a safe code/message pair without exposing exception internals."""
    try:
        if isinstance(exc, EnnovaError):
            return {"code": exc.code, "message": exc.public_message}
    except Exception:
        return {"code": GENERIC_ERROR_CODE, "message": GENERIC_PUBLIC_MESSAGE}
    return {"code": GENERIC_ERROR_CODE, "message": GENERIC_PUBLIC_MESSAGE}
