# ENNOVA (Alaala) – Progress Tracker

> Team members: [Full name], [Full name], [Full name], [Full name], [Full name]
> Course: CS 413 – Programming Languages Final Project

**Current feature:** F7b – Gemini integration `[x]`
**Rule:** one feature at a time. Finish, test, update this file, get approval, then move on.

Status key: `[ ]` not started, `[~]` in progress, `[x]` done and tested, `[!]` blocked

---

## Required features (from the handout)

### F0 – Project foundation (new project) `[x]`
- [x] Create GitHub repo `ennova`, add `.gitignore`, README stub, `docs/ai-use-log.md`
- [x] Add `.github/copilot-instructions.md` and `PROGRESS.md`
- [x] Protect `main` (require pull request + 1 review)
- [x] Each member sets `git config user.name` / `user.email`
- [x] Branch for this feature: `feature/f0-foundation`
- [x] Create `backend/` with virtual environment and `requirements.txt` (Flask, Flask-SQLAlchemy, Flask-Migrate, PyMySQL, python-dotenv, pytest)
- [x] Flask app factory, `config.py` reading everything from environment variables
- [x] `.env.example` with placeholders only (no real values)
- [x] Aiven MySQL connection with correct TLS (`ssl` dict / `ssl_ca`, NOT `ssl-mode`), team's own database (not `defaultdb`)
- [x] Verify the connection with `SELECT 1` (configured in app and enforced when MySQL env vars are present; skipped without live Aiven creds)
- [x] `/health` endpoint
- [x] Initialize Flask-Migrate (no tables yet)
- [x] Install SWI-Prolog and confirm it runs (needed for F5)
- [x] Check `git status`: no `.env`, no venv, then first commit and push (local branch is clean aside from tracked foundation files; no secrets or local venv files are included)
- **Paradigm:** none (infrastructure)
- **Files changed:** `.gitignore`, `README.md`, `docs/ai-use-log.md`, `backend/requirements.txt`, `backend/.env.example`, `backend/run.py`, `backend/app/__init__.py`, `backend/app/config.py`, `backend/app/extensions.py`, `backend/tests/test_health.py`, `backend/tests/test_database_connection.py`, `backend/migrations/`
- **Tests:** `pytest -q tests/test_health.py tests/test_database_connection.py` (health passes; MySQL connectivity test is skipped without configured `DATABASE_URL`)
- **Verified by:** [Full name] – Q/A

### F1 – Diary model (OOP) `[x]`
- [x] `Owner`, `Beneficiary`, `Protocol`, `Grant` classes
- [x] `Entry` base class with `DiaryEntry` and `LetterEntry`
- [x] `Vault` with `append()` and read-only access (no edit/delete)
- [x] Tests: inheritance, polymorphism, encapsulation
- **Paradigm:** Object-oriented
- **Files changed:** `backend/app/domain/__init__.py`, `backend/app/domain/diary/__init__.py`, `backend/app/domain/diary/model.py`, `backend/tests/test_diary_model.py`
- **Tests:** `pytest -q tests/test_diary_model.py` (6 passed); `pytest -q tests` (8 passed)
- **Open issues:** None for F1. Prolog authorization and policy-freeze enforcement remain in their planned later features.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F2 – Entry processing (Functional) `[x]`
- [x] Immutable entry data (frozen dataclasses)
- [x] `normalize`, `extract_names` (`[[name]]`), `extract_topics` (`#tag`)
- [x] `correct` (rule-based, pure), `diff`
- [x] Hash chain as a fold, `TamperDetected` on mismatch
- [x] Tests for every function and for tampering
- **Paradigm:** Functional
- **Files changed:** `backend/app/domain/processing/__init__.py`, `backend/app/domain/processing/exceptions.py`, `backend/app/domain/processing/functions.py`, `backend/app/domain/processing/models.py`, `backend/tests/test_processing.py`
- **Tests:** `pytest -q tests/test_processing.py` (13 passed); `pytest -q tests` (21 passed)
- **Open issues:** None for F2. `correct` intentionally uses caller-supplied immutable correction rules; safe boundary fallbacks are handled in F8.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F3 – Writing modes (OOP) `[ ]`
- [ ] Abstract `WritingMode`, plus `Verbatim`, `LightFix`, `Review`
- [ ] Derived versions linked to the original; original never changed
- [ ] Tests: original unchanged, polymorphic dispatch
- **Paradigm:** Object-oriented

### F4 – Policy language (Language design) `[x]`
- [x] EBNF grammar (`grammar.ebnf`) + at least 3 sample programs
- [x] Lexer
- [x] Recursive-descent parser with `PolicySyntaxError` (line/column, readable message)
- [x] Interpreter producing Prolog facts
- [x] Statements: may see, may read/deny, release letter, transfer custody, default writing mode (+ optional top-level `trustee is`)
- [x] Parser tests: valid and invalid
- **Paradigm:** Language design
- **Files changed:** `backend/app/errors/__init__.py`, `backend/app/errors/policy_syntax.py`, `backend/app/policy/__init__.py`, `backend/app/policy/ast_nodes.py`, `backend/app/policy/lexer.py`, `backend/app/policy/parser.py`, `backend/app/policy/interpreter.py`, `backend/tests/test_policy_language.py`, `docs/grammar/grammar.ebnf`, `docs/grammar/policy-to-facts.md`, `docs/grammar/sample_*.policy`, `docs/grammar/invalid_*.policy`
- **Tests:** `pytest -q tests/test_policy_language.py` (20 passed); `pytest -q tests` (41 passed); SWI-Prolog accepted generated escaped facts
- **Open issues:** None for F4. Access hierarchy, deny precedence, registration, and death-trigger facts remain in F5.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F5 – Prolog access rules (Logic) `[x]`
- [x] `access_rules.pl`: deny by default, deny beats allow, hierarchy, release dates, registered check, frozen policy
- [x] Python <-> Prolog bridge (Python only asks, never decides)
- [x] Access test table (asker, entry, expected result)
- [x] Tests: allow, deny, conflict, release date, unregistered, missing protocol, frozen
- **Paradigm:** Logic
- **Files changed:** `backend/app/policy/access_rules.pl`, `backend/app/policy/access_bridge.py`, `backend/app/policy/__init__.py`, `backend/app/policy/interpreter.py`, `backend/tests/test_prolog_access.py`, `docs/access-test-table.md`
- **Tests:** `pytest -q tests/test_prolog_access.py` (18 passed); `pytest -q tests` (59 passed); live batched SWI-Prolog check returned `allow, deny, allow, deny`; `git diff --check` passed
- **Open issues:** `can_modify_policy/1` enforces frozen-state in Prolog; owner authentication remains the app boundary's responsibility because no owner fact is part of the specified F5 vocabulary.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F6 – Accounts and registration `[ ]`
- [ ] Register / login with hashed password and JWT
- [ ] `registered/1` fact for Prolog
- [ ] Owner-issued invitation code for beneficiaries
- [ ] Tests: registration, login, bad credentials
- **Paradigm:** Scripting (supporting feature)

### F7 – Grounded AI Q&A (Scripting) `[~]`
- [x] Authorized retrieval (Prolog check BEFORE search)
- [x] Tools: `search_entries`, `get_entry`, `count_mentions`, `get_letter`
- [x] Gemini integration (key on backend only; live calls are opt-in)
- [x] System prompt; policy remains in Prolog/backend and is not sent to the model
- [x] Date citations; neutral reply for no-record and denied (identical)
- [x] Design note: model, tools, instructions
- [x] Tests: Maria scenario (all 6 rows), prompt injection, AI unavailable, restricted entries never reach the model
- **Paradigm:** Scripting

### F7a – Grounded AI orchestration `[x]`
- [x] Add Prolog letter-status queries to the single batched F5 bridge call
- [x] Add fixed-asker retrieval tools, stored derived summaries, citation verification, and a capped tool loop
- [x] Verify entry integrity only after Prolog allows access; exclude tampered entries
- [x] Add backend-only existence counts and matching pre-release date messages
- [x] Keep denied and nonexistent entry responses identical; do not call the model when no entry is permitted
- [x] Keep policy text out of model prompts; test that other protocols, deny rules, private tags, and other letter titles do not leak
- [x] Cover the six Maria acceptance scenarios with scripted fake-model responses and required SWI-Prolog
- **Paradigm:** Scripting orchestration with Logic-based authorization and Functional/immutable entry processing
- **Files changed:** `backend/.env.example`, `backend/app/config.py`, `backend/app/policy/access_rules.pl`, `backend/app/policy/access_bridge.py`, `backend/app/policy/__init__.py`, `backend/app/ai/`, `backend/app/services/__init__.py`, `backend/app/services/grounded_qa.py`, `backend/tests/test_grounded_qa.py`, `PROGRESS.md`, `docs/ai-use-log.md`
- **Tests:** `pytest -q tests/test_grounded_qa.py` (20 passed); `pytest -q` (107 passed); `git diff --check` passed
- **Open issues:** Owner Q&A is not implemented. F7a uses only the scripted fake client; live provider behavior is not established by its tests.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F7b – Gemini integration `[x]`
- [x] Pin `google-genai` and configure backend-only `GEMINI_API_KEY`, `GEMINI_MODEL`, and opt-in live tests
- [x] Add stateless Interactions adapter with schema-only manual tools, strict JSON, bounded retries, timeouts, and safe typed failures
- [x] Add a write-time Gemini summarizer with untrusted-entry framing, one quote-overlap retry, and digest-bound artifacts
- [x] Reject stale summaries when their source digest no longer matches the stored entry
- [x] Add mocked SDK, secrecy, malformed-response, retry, deadline, hostile-entry, and gated fictional live safety tests
- [x] Keep unavailable and other-recipient letter titles out of model/tool calls; preserve Maria's own pre-release date response
- [x] Reject case-insensitive duplicate letter titles for the same owner before appending or extending the hash chain
- [x] Make Prolog fail closed on duplicate title mappings and verify one release rule cannot unlock either duplicate
- [x] Separate the ENNOVA Gemini logger from the SDK logger, set SDK logging to ERROR, and test canary redaction from exception `str`, `repr`, and `args` while capturing exactly one root-visible project log record
- [x] Confirm `NEUTRAL_REPLY` directly aliases F8's `ACCESS_DENIED_PUBLIC_MESSAGE`; the public text has one definition
- [x] Add the separate Model, Tools, and Instructions design note
- **Paradigm:** Scripting adapter with Prolog-authorized tool orchestration and derived summary artifacts
- **Files changed:** `backend/requirements.txt`, `backend/.env.example`, `backend/app/config.py`, `backend/app/ai/__init__.py`, `backend/app/ai/client.py`, `backend/app/ai/gemini.py`, `backend/app/ai/summaries.py`, `backend/app/ai/tools.py`, `backend/app/policy/access_rules.pl`, `backend/app/services/diary_service.py`, `backend/app/services/grounded_qa.py`, `backend/tests/test_gemini.py`, `backend/tests/test_grounded_qa.py`, `backend/tests/test_entry_store.py`, `docs/ai-design-note.md`, `PROGRESS.md`, `docs/ai-use-log.md`
- **Tests:** `pytest -q tests/test_entry_store.py tests/test_prolog_access.py tests/test_grounded_qa.py` (52 passed); `pytest -q` (128 passed, 1 skipped); `git diff --check` passed
- **Open issues:** `access_rules.pl` keys letter releases by person and title, not entry ID; it now denies all entries when multiple IDs share a title, including duplicate facts supplied outside `DiaryService`. The supported write path also rejects same-owner duplicate titles. The live Gemini test was skipped because `RUN_LIVE_AI_TESTS` was not enabled; no API key or real provider request was used. Fake and mocked tests do not establish live model behavior. Owner Q&A remains unimplemented.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F8 – Typed exceptions and fallbacks `[x]`
- [x] `EnnovaError` base with private detail, safe public message, and stable code
- [x] `AccessDenied`, `AmbiguousName`, `TamperDetected`, `PolicyFrozen`, `AIServiceUnavailable`, and `PolicySyntaxError`
- [x] Safe public-response fallback and legacy processing-package re-exports
- [x] Tests for detail privacy, access-denial message neutrality, fallback behavior, and compatibility
- **Paradigm:** supports all
- **Files changed:** `backend/app/errors/base.py`, `backend/app/errors/typed.py`, `backend/app/errors/__init__.py`, `backend/app/errors/policy_syntax.py`, `backend/app/domain/processing/exceptions.py`, `backend/app/domain/processing/functions.py`, `backend/tests/test_errors.py`
- **Tests:** `pytest -q tests/test_errors.py tests/test_processing.py tests/test_policy_language.py` (50 passed); `pytest -q tests` (76 passed); `git diff --check` passed
- **Safety note:** `TamperDetected` integrity verification must run only after the access check and only on permitted entries. The errors package has no Flask or database imports and does not map errors to HTTP responses.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F6a – Entry store `[x]`
- [x] Append-only `EntryRepository` and `InMemoryEntryRepository`
- [x] `DiaryService` stores original entries using F2 extraction and hash-chain functions
- [x] Hash metadata includes owner and entry IDs; timestamps are caller-supplied and timezone-aware
- [x] Explicit chain verification and head checks; reads do not verify automatically
- [x] Pure `build_app_facts` for F5 with case-folded names and tags
- [x] Fictional Lola/Maria/Nora fixture and required six-row SWI-Prolog integration test
- **Paradigm:** Object-oriented repository/service using the Functional F2 pipeline and Logic F5 access bridge
- **Files changed:** `backend/app/domain/diary/repository.py`, `backend/app/domain/diary/__init__.py`, `backend/app/services/__init__.py`, `backend/app/services/diary_service.py`, `backend/app/services/access_facts.py`, `backend/tests/conftest.py`, `backend/tests/test_entry_store.py`, `backend/tests/test_prolog_access.py`
- **Tests:** `pytest -q tests/test_entry_store.py tests/test_prolog_access.py` (29 passed); `pytest -q tests` (87 passed); `git diff --check` passed
- **Open issues:** The in-memory append is not thread-safe. A database repository must atomically read the last hash and insert the next record. Release dates are policy data, not `LetterEntry.release_date`; full-chain verification remains explicit and must follow access authorization.
- **Verified by:** [Full name] – Q/A (replace with reviewer/verifier's name)

### F9 – REST API `[ ]`
- [ ] Endpoints: auth, entries, writing modes, policy, ask-AI
- [ ] Safe error responses (no stack traces or secrets)
- [ ] Integration tests

### F10 – Letter of Wishes `[ ]`
- [ ] Letter entries with recipient and release date
- [ ] Always-visible "not a legal will" disclaimer

### F11 – Mobile interface (Expo) `[ ]`
- [ ] Sign-in, write entries, policy builder (templates + plain-language preview + advanced editor), ask questions, cited answers, denied-access messages
- [ ] Policy builder always generates policy text through the parser
- **Note:** a mobile interface is a listed extra. Confirm with instructor first.

---

## Optional extras (instructor approval REQUIRED before building)

Each needs: paradigm stated, follows access protocol, tested, AI-code verification explained.

| Extra | Paradigm | Instructor told? | Approved? | Status |
|---|---|---|---|---|
| Android app (Expo) | n/a (interface) | [ ] | [ ] | `[ ]` |
| Biometric app lock | n/a (platform) | [ ] | [ ] | `[ ]` |
| Dead-man's-switch check-in (starts death trigger) | Logic / Scripting | [ ] | [ ] | `[ ]` |
| Document vault (PDF/DOCX) | Scripting | [ ] | [ ] | `[ ]` |
| "Never share" entry marker | Logic | [ ] | [ ] | `[ ]` |
| Markdown export | Functional | [ ] | [ ] | `[ ]` |
| Semantic search (embeddings) | Scripting | [ ] | [ ] | `[ ]` |

## Out of scope (state in design report)
Device trust, recovery codes, password reset, full trustee verification workflow.

---

## Deliverables checklist
- [ ] Working prototype under version control (GitHub link, history shows all 5 members)
- [ ] README with setup steps
- [ ] AI design note (model, tools, instructions)
- [ ] EBNF grammar + at least 3 sample programs
- [ ] Prolog rule file + access test table
- [ ] Parser tests (valid and invalid)
- [ ] Short design report (paradigm choice per component, what we'd change)
- [ ] AI-use log with verifier names
- [ ] Linear workspace + weekly updates from all five members
- [ ] List of extra features and their paradigms
- [ ] Slides and live demo
- [ ] All five names on every file

## Git conventions (summary)
- Branch per feature: `feature/f<number>-<name>`. Never commit to `main`.
- PR title `F<number>: <name>`, reviewed by a teammate (reviewer = verifier in AI-use log).
- Commit format: `type(scope): summary` (feat, fix, test, docs, refactor, chore).
- Full rules: `.github/copilot-instructions.md`, section 11.

## Defense questions to prepare
- Why Prolog instead of if-statements?
- Why are entries immutable and hash-chained?
- What happens when two rules conflict?
- How do you stop the AI from seeing entries the asker may not read?
- Which code did AI write and how did you check it?
- If you added a feature, which paradigm and why?

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | Auth = username + password + JWT; biometrics optional later | Handout requires only "registered people"; no paradigm value in biometrics |
| 2026-11-12 | Entry syntax `[[name]]` and `#tag` | Makes name/topic extraction deterministic; helps `AmbiguousName` |
| 2026-11-12 | UI builder generates policy text through the parser | Keeps Language Design component real |
| 2026-11-12 | `correct` step is rule-based and pure | Keeps functional paradigm clean; LLM use lives in OOP writing modes |
| 2026-11-12 | Custody = who administers vault / fires death trigger; no read rights | Keeps deny-by-default intact |
| 2026-11-12 | Entries never move to heir's account | Beneficiaries only get permitted answers |
| 2026-11-12 | Start a NEW project (no existing code) | Clean foundation; TLS configured correctly from the start; mobile app postponed until instructor approves |
| 2026-11-12 | Git + GitHub with feature branches and reviewed PRs | Handout requires version control; PR reviewer doubles as AI-code verifier |

## Weekly log
| Week | What was done | Next |
|---|---|---|
| 1 | Brainstormed components, paradigms, access model; created Copilot instructions and this tracker | F0 foundation |
