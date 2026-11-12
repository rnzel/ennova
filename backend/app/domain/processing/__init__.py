# ENNOVA (Alaala) – Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator
# Paradigm: Functional entry processing
from .exceptions import AmbiguousName, TamperDetected
from .functions import (
    correct,
    diff,
    extract_names,
    extract_topics,
    hash_chain,
    hash_entry,
    normalize,
    verify_hash_chain,
)
from .models import (
    ChainedEntry,
    CorrectionRule,
    DiffSegment,
    EntryData,
    PersonReference,
)

__all__ = [
    "AmbiguousName",
    "ChainedEntry",
    "CorrectionRule",
    "DiffSegment",
    "EntryData",
    "PersonReference",
    "TamperDetected",
    "correct",
    "diff",
    "extract_names",
    "extract_topics",
    "hash_chain",
    "hash_entry",
    "normalize",
    "verify_hash_chain",
]
