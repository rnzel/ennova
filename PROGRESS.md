# ENNOVA (Alaala) – Progress Tracker

> Team members: [Full name], [Full name], [Full name], [Full name], [Full name]
> Course: CS 413 – Programming Languages Final Project

**Current feature:** F0 – Project foundation
**Rule:** one feature at a time. Finish, test, update this file, get approval, then move on.

Status key: `[ ]` not started, `[~]` in progress, `[x]` done and tested, `[!]` blocked

---

## Required features (from the handout)

### F0 – Project foundation (new project) `[~]`
- [ ] Create GitHub repo `ennova`, add `.gitignore`, README stub, `docs/ai-use-log.md`
- [ ] Add `.github/copilot-instructions.md` and `PROGRESS.md`
- [ ] Protect `main` (require pull request + 1 review)
- [ ] Each member sets `git config user.name` / `user.email`
- [ ] Branch for this feature: `feature/f0-foundation`
- [ ] Create `backend/` with virtual environment and `requirements.txt` (Flask, Flask-SQLAlchemy, Flask-Migrate, PyMySQL, python-dotenv, pytest)
- [ ] Flask app factory, `config.py` reading everything from environment variables
- [ ] `.env.example` with placeholders only (no real values)
- [ ] Aiven MySQL connection with correct TLS (`ssl` dict / `ssl_ca`, NOT `ssl-mode`), team's own database (not `defaultdb`)
- [ ] Verify the connection with `SELECT 1`
- [ ] `/health` endpoint
- [ ] Initialize Flask-Migrate (no tables yet)
- [ ] Install SWI-Prolog and confirm it runs (needed for F5)
- [ ] Check `git status`: no `.env`, no venv, then first commit and push
- **Paradigm:** none (infrastructure)
- **Files changed:** _(fill in)_
- **Tests:** _(fill in: health endpoint, DB connection test)_
- **Verified by:** _(name)_

### F1 – Diary model (OOP) `[ ]`
- [ ] `Owner`, `Beneficiary`, `Protocol`, `Grant` classes
- [ ] `Entry` base class with `DiaryEntry` and `LetterEntry`
- [ ] `Vault` with `append()` and read-only access (no edit/delete)
- [ ] Tests: inheritance, polymorphism, encapsulation
- **Paradigm:** Object-oriented

### F2 – Entry processing (Functional) `[ ]`
- [ ] Immutable entry data (frozen dataclasses)
- [ ] `normalize`, `extract_names` (`[[name]]`), `extract_topics` (`#tag`)
- [ ] `correct` (rule-based, pure), `diff`
- [ ] Hash chain as a fold, `TamperDetected` on mismatch
- [ ] Tests for every function and for tampering
- **Paradigm:** Functional

### F3 – Writing modes (OOP) `[ ]`
- [ ] Abstract `WritingMode`, plus `Verbatim`, `LightFix`, `Review`
- [ ] Derived versions linked to the original; original never changed
- [ ] Tests: original unchanged, polymorphic dispatch
- **Paradigm:** Object-oriented

### F4 – Policy language (Language design) `[ ]`
- [ ] EBNF grammar (`grammar.ebnf`) + at least 3 sample programs
- [ ] Lexer
- [ ] Recursive-descent parser with `PolicySyntaxError` (line/column, readable message)
- [ ] Interpreter producing Prolog facts
- [ ] Statements: may see, may read, release letter, transfer custody, default writing mode (+ `trustee is`)
- [ ] Parser tests: valid and invalid
- **Paradigm:** Language design

### F5 – Prolog access rules (Logic) `[ ]`
- [ ] `access_rules.pl`: deny by default, deny beats allow, hierarchy, release dates, registered check, frozen policy
- [ ] Python <-> Prolog bridge (Python only asks, never decides)
- [ ] Access test table (asker, entry, expected result)
- [ ] Tests: allow, deny, conflict, release date, unregistered, missing protocol, frozen
- **Paradigm:** Logic

### F6 – Accounts and registration `[ ]`
- [ ] Register / login with hashed password and JWT
- [ ] `registered/1` fact for Prolog
- [ ] Owner-issued invitation code for beneficiaries
- [ ] Tests: registration, login, bad credentials
- **Paradigm:** Scripting (supporting feature)

### F7 – Grounded AI Q&A (Scripting) `[ ]`
- [ ] Authorized retrieval (Prolog check BEFORE search)
- [ ] Tools: `search_entries`, `get_entry`, `count_mentions`, `get_letter`
- [ ] Gemini integration (key on backend only)
- [ ] System prompt + policy as instructions
- [ ] Date citations; neutral reply for no-record and denied (identical)
- [ ] Design note: model, tools, instructions
- [ ] Tests: Maria scenario (all 6 rows), prompt injection, AI unavailable, restricted entries never reach the model
- **Paradigm:** Scripting

### F8 – Typed exceptions and fallbacks `[ ]`
- [ ] `AccessDenied`, `AmbiguousName`, `TamperDetected`, `PolicySyntaxError`
- [ ] Safe fallback for each, verified by tests
- **Paradigm:** supports all

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
