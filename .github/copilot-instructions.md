# ENNOVA (Alaala) – Copilot Instructions

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

## 1. What this project is

ENNOVA is a personal AI diary and digital legacy app for **CS 413 – Programming Languages (Final Project, "Alaala" handout)**.
An owner writes diary entries and leaves instructions in a small **policy language**. Only registered people can open the diary, and each sees only what the owner allowed. An AI answers from permitted entries and cites them.

**The point is NOT the AI.** The point is choosing and defending the right programming paradigm for each part. Every piece of code must make that choice visible and explainable.

Always read `PROGRESS.md` first to see which feature is current and what is done.

## 2. Working method: ONE FEATURE AT A TIME

For every feature:
1. Read `PROGRESS.md` and inspect the relevant existing files. Never rebuild working code.
2. State the plan in a few lines and wait for approval if the change is large.
3. Implement only that feature. No extras, no "while I'm here" additions.
4. Write tests alongside the code.
5. Run the tests and report the results honestly.
6. List the files changed.
7. Update `PROGRESS.md` (status, files, test results, open issues).
8. Commit on the feature branch with a proper message (see section 11).
9. Stop and wait for approval before starting the next feature.

Never claim a feature is complete unless it is implemented AND tested.
Never generate the whole app in one response.

## 3. The six required components and their paradigms

| # | Component | Paradigm | Rule |
|---|---|---|---|
| 1 | Diary model | Object-oriented | Classes: Owner, Entry (>= 2 types: DiaryEntry, LetterEntry), Beneficiary, Vault, Protocol, Grant. Use inheritance, polymorphism, encapsulation. |
| 2 | Entry processing | Functional | Pure functions over immutable data: normalize, extract names, extract topics, correct, diff. Entries are append-only and hash-chained. |
| 3 | Writing modes | Object-oriented | Abstract `WritingMode` with Verbatim, LightFix, Review subclasses chosen by polymorphism (no `if mode == ...`). Original is always kept. |
| 4 | Access rules | Logic (SWI-Prolog) | Facts and rules decide access. Deny by default, deny beats allow, release dates, frozen policy after the death trigger. |
| 5 | Legacy policy language | Language design | EBNF grammar, lexer, recursive-descent parser, interpreter that compiles policy into Prolog facts. At least 4 statement types. |
| 6 | Grounded AI Q&A | Scripting (Python) | Answers only from permitted entries, cites each by date, says so when there is no record. |

Plus typed exceptions with safe fallbacks (see section 7).

### Paradigm boundaries (do not blur these)
- **Functional code** (`domain/processing/`): no I/O, no database, no network, no mutation, no clock reads, no randomness. Use frozen dataclasses and tuples. The `correct` step is **rule-based and pure** (no LLM calls).
- **OOP code** (`domain/diary/`, `domain/writing_modes/`): classes with private state. `Vault` exposes `append()` and read methods only: no update, no delete.
- **Prolog** decides access. Python must NEVER replace Prolog with if-statements. Python only asks Prolog a question and acts on the answer.
- **Policy language**: UI buttons and templates generate policy TEXT, and that text goes through the same lexer, parser and interpreter. Never write Prolog facts directly from UI actions.
- **Scripting** (`ai/`, `services/`): orchestration glue and error handling only.

## 4. Settled design decisions

### Entries
- Entry syntax uses `[[name]]` for people links and `#tag` for topics. Name and topic extraction parse these deterministically, plus rule-based plain-name detection.
- Bare names matching more than one person raise `AmbiguousName`. Never guess.
- Original content is immutable. Writing modes create **derived versions** linked to the original.
- Hash chain: each entry hash = hash(original content + timestamp + metadata + previous hash). Verification re-folds the chain; mismatch raises `TamperDetected`.

### Access
- Access levels form a hierarchy: `verbatim` implies `summary`, which implies `existence`.
- Order of evaluation: not registered -> deny; explicit deny -> deny; explicit allow (and release condition met) -> allow; otherwise deny.
- Today's date is **passed into** Prolog as a parameter. Never read the clock inside Prolog.
- After the death trigger fires, the policy is **frozen**. Reject all policy changes (also enforce at the Python boundary, but the frozen rule lives in Prolog).
- Until the death trigger fires, beneficiaries have no access at all.
- Entries never move to a beneficiary's account. They stay in the owner's vault, and beneficiaries get only permitted answers.
- Support a "never share" marker on entries, which acts as an explicit deny.

### Policy language statements (at least these four, plus one)
1. `may see existence of <selector>`
2. `may read summary|verbatim of <selector>`
3. `release letter "<title>" to <person> when date >= YYYY-MM-DD`
4. `transfer custody to <person> if trustee unavailable for N days`
5. `default writing mode: verbatim|light_fix|review`

Selectors: `entries mentioning <name>` and `entries tagged "<tag>"` (one `selector` production so more can be added later).

**Custody** means who looks after the vault and may fire the death trigger. It grants NO reading rights. Reading still needs its own `may read` / `may see`. Add a `trustee is <person>` statement so custody has something to refer to.

### Accounts
- Username + password (hashed) + JWT. "Registered" must be a fact Prolog can check (`registered/1`).
- Beneficiaries join using an owner-issued invitation code.
- Biometrics are an optional later extra (app lock only), not core. No device trust, recovery codes, or password reset (state this in the design report).

### AI (Model + Tools + Instructions, documented separately)
- **Model:** Local Ollama through its chat API. `OLLAMA_HOST` defaults to loopback; remote hosts require explicit opt-in. The model name comes from `OLLAMA_MODEL`.
- **Provider selection:** `LLM_PROVIDER` accepts only `ollama` or `fake`. Missing or invalid values fail closed. The fake client is for tests and scripted demos.
- **Tools:** `search_entries`, `get_entry`, `count_mentions`, `get_letter`. Every tool runs the Prolog check internally and returns only permitted data.
- **Instructions:** Ollama receives a system prompt (answer only from provided entries, cite dates, never claim to be the owner, say so when there is no record). The owner's compiled policy stays in Prolog and is not sent to the model.
- The model NEVER touches the database or vault directly. Filter by permission BEFORE any search or ranking.
- **Neutral reply rule:** "no permitted record" and "records exist but denied" must produce the identical reply (same text, same shape). Never confirm or deny that restricted entries exist.
- Existence access is the only case that reveals a count, and the backend computes it, not the model.
- Entry text is untrusted input to the prompt (prompt injection). Never let entry content change instructions.
- Start with tag, name and keyword retrieval. Embeddings / ChromaDB are a later upgrade.

## 5. Acceptance test: the Maria scenario

The whole system must pass these (after the death trigger has fired):

| Maria asks | Expected |
|---|---|
| "Did he ever write about me?" | Yes + count of entries; no content (existence access) |
| "What did he write about family?" | Summary of entries tagged family, with dates cited |
| "Show me the letter to my daughter" before 2040-05-01 | Refuses (release date not reached) |
| Same request on/after 2040-05-01 | Shows the letter verbatim |
| "What did he think about his business?" | Neutral reply: nothing it can share. No confirm/deny |
| Person with no protocol asks anything | Same neutral reply, no detail |

Turn this table into automated tests early.

## 6. Tech stack (do not replace without explaining why)

- **Backend:** Python, Flask, Flask-SQLAlchemy, Flask-Migrate (Alembic), PyMySQL, JWT, REST + JSON.
- **Database:** Aiven MySQL 8.4 (the owner's own database, NOT `defaultdb`), TLS required. MySQL is the source of truth.
- **Logic:** SWI-Prolog with Python integration.
- **AI:** Local Ollama chat API; `fake` is available for tests and scripted demos.
- **Mobile (later feature):** Expo React Native, TypeScript, Expo Router, Expo SecureStore.
- **Tests:** pytest.

### Database connection note (Feature 0)
This is a **new project** (greenfield). Configure TLS correctly from the start.
PyMySQL does NOT accept the `ssl-mode` option (it raises `TypeError: Connection.__init__() got an unexpected keyword argument 'ssl-mode'`).
Use `connect_args={"ssl": {"ca": "<path to Aiven CA cert>"}}` (or `ssl_ca`) in the SQLAlchemy engine options. Keep the CA certificate path in an environment variable. Verify with `SELECT 1`.
Use the team's own Aiven database, NOT `defaultdb`. All schema changes go through Flask-Migrate migrations. If the database already contains tables from an earlier attempt, do not drop them; ask the team first.

## 7. Typed exceptions and safe fallbacks

| Exception | Safe fallback |
|---|---|
| `AccessDenied` | Return the neutral reply. Send nothing restricted to the model. |
| `AmbiguousName` | Ask for clarification or refuse. Never guess. |
| `TamperDetected` | Flag the chain and refuse to serve affected entries. |
| `PolicySyntaxError` | Reject the policy, keep the previous version, report line/column and a readable message. |

Also useful: `DocumentProcessingError`, `AuthenticationError`, `AIServiceUnavailable`, `DatabaseConnectionError`.
Never expose stack traces, credentials, file paths or secrets to users. If anything fails, fall back to the SAFE action (deny).

## 8. Code rules

- Python for backend, TypeScript for mobile. Type hints and docstrings on all public functions and classes.
- Modular: routes are thin, logic lives in services and domain. Use the layout in section 12. Before each feature, inspect the current repo state and do not overwrite working code.
- Never hardcode secrets. Use environment variables. `.env` must never be committed. Keep `.env.example` current.
- Use fictional owner and fictional diary entries only (suggested: owner "Lola Reyes", beneficiary "Maria"). Never real private data.
- Use parameterized ORM queries only. Validate all input.
- Never delete tables or records to fix a bug. Use migrations.
- Add a header comment to each source file naming the paradigm it demonstrates and the team members.
- Keep code simple enough that every team member can explain and defend it.

## 9. AI-use log (required deliverable)

Whenever you generate significant code, add a line to `docs/ai-use-log.md`:
`date | feature | prompt summary | what was generated | what was changed or rejected | verified by (name)`
Remind the developer to fill in the verifier's name. Every member must be able to explain AI-written code.

## 10. Do not

- Do not let the AI model call the database, read the vault, or decide authorization.
- Do not replace Prolog rules with Python conditionals.
- Do not add features that are not in `PROGRESS.md`. Extras need instructor approval first.
- Do not store uploads or entries at public URLs.
- Do not present the Letter of Wishes as a legal will. Always show: "Letters of Wishes in ENNOVA are personal messages and are not legal wills or substitutes for legally executed estate documents. ENNOVA does not provide legal advice."
- Do not represent inactivity as proof of death. Inactivity alone must never release private data.

## 11. Git workflow

The project is kept under Git and hosted on GitHub (required deliverable: source code under version control).

### Branching
- `main` always works and passes all tests. **Never commit directly to `main`.**
- One branch per feature, named after the feature in `PROGRESS.md`:
  `feature/f1-diary-model`, `feature/f2-entry-pipeline`, `feature/f5-prolog-rules`, etc.
- Small fixes: `fix/<short-description>`. Docs: `docs/<short-description>`.
- Merge into `main` through a **Pull Request**, reviewed by a teammate other than the author.
  The reviewer's name goes in the AI-use log as the verifier for any AI-assisted code in that PR.
- Delete the branch after merging.

### Commits
- Small, focused commits. One logical change each. Do not mix unrelated changes.
- Message format: `type(scope): short summary` (imperative, max about 72 characters).
  Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
  Examples:
  - `feat(vault): add append-only Vault class`
  - `test(prolog): add deny-overrides-allow cases`
  - `fix(db): use ssl dict for PyMySQL Aiven connection`
- If a commit contains AI-generated code, add a line to the body: `AI-assisted: yes (verified by <name>)`.
- Each member commits under their own name and email (`git config user.name` / `user.email`), so history shows every member's contribution.
- Tests must pass before committing a feature. Never commit failing tests to `main`.

### Pull requests
- Title: `F<number>: <feature name>`.
- Description: what changed, which paradigm it demonstrates, how it was tested, link to the Linear task.
- Checklist before requesting review: tests pass, `PROGRESS.md` updated, AI-use log updated, no secrets in the diff.

### Never commit
- `.env` or any file with keys, passwords, tokens or database credentials.
- Virtual environments (`venv/`, `.venv/`), `__pycache__/`, `node_modules/`.
- Private uploads, local databases, generated semantic indexes (e.g. ChromaDB data), logs.
- Any real person's diary or personal data. Fictional data only.

If a secret is committed by accident: **rotate the secret immediately** (for example, the Aiven password or any configured provider credential). Deleting the file in a later commit does not remove it from history.

### Recommended `.gitignore` entries
```
.env
.env.*
!.env.example
venv/
.venv/
__pycache__/
*.pyc
node_modules/
.expo/
uploads/
chroma_db/
*.log
.pytest_cache/
```

### Tags (milestones)
Tag stable points: `v0.1-foundation`, `v0.2-core-logic` (F1 to F5), `v0.3-ai`, `v1.0-final`.

### Rules for Copilot
- Never run `git push --force`, `git reset --hard` on shared branches, or rewrite history on `main`.
- Never stage everything blindly. Review `git status` and `git diff` first, and check that no secret or ignored file is included.
- Suggest the commit message and branch name, and let the developer run the git commands.

## 12. Project layout (new project)

Monorepo. Create only what the current feature needs. Do not scaffold empty folders for future features.

```text
ennova/
├── .github/
│   └── copilot-instructions.md
├── PROGRESS.md
├── README.md
├── .gitignore
├── docs/
│   ├── ai-use-log.md
│   ├── design-report.md          (later)
│   ├── ai-design-note.md         (later)
│   └── grammar/                  (EBNF + sample programs, later)
├── backend/
│   ├── app/
│   │   ├── __init__.py           (Flask app factory)
│   │   ├── config.py
│   │   ├── extensions.py
│   │   ├── errors/               (typed exceptions)
│   │   ├── domain/
│   │   │   ├── diary/            (OOP: F1)
│   │   │   ├── processing/       (functional: F2)
│   │   │   └── writing_modes/    (OOP: F3)
│   │   ├── policy/               (language + Prolog: F4, F5)
│   │   ├── ai/                   (scripting: F7)
│   │   ├── models/               (SQLAlchemy)
│   │   ├── routes/
│   │   └── services/
│   ├── migrations/
│   ├── tests/
│   ├── requirements.txt
│   ├── .env.example
│   └── run.py
└── mobile/                       (Expo app, only after instructor approval and F9)
```

Core logic (`domain/`, `policy/`) must be testable **without** Flask or the database. Build and test it as plain Python first, then connect it to the API and DB.
