# ENNOVA

## Team
CS 413 Programming Languages final project.

| Member | Role |
|---|---|
| Roldan Bazares Jr. | Front End |
| Ranzel Jay Gobris | Lead Developer / Back End |
| Bart Jayson Lola | Q/A |
| Jallil Sultan | UI/UX Designer |
| Jezelle Gabion | Documentator |

## Project summary
ENNOVA is a personal AI diary and digital legacy app that keeps owner-written entries private, exposes only permitted content to beneficiaries, and routes access decisions through a policy language plus Prolog rules.

## Local setup
1. Open a terminal in the project root.
2. Create and activate the backend virtual environment:
   - PowerShell: `cd backend`, `py -3 -m venv .venv`, `.\.venv\Scripts\Activate.ps1`
   - Git Bash: `cd backend`, `python -m venv .venv`, `source .venv/Scripts/activate`
3. Install dependencies: `pip install -r requirements.txt`
4. Copy the example environment file and fill in your own values (never commit `.env`):
   - PowerShell: `Copy-Item .env.example .env`
   - Git Bash: `cp .env.example .env`
5. Set these values in `backend/.env`:
   - `JWT_SECRET_KEY`: at least 32 characters. Generate one with `python -c "import secrets; print(secrets.token_hex(32))"`.
   - `DATABASE_URL`: Aiven MySQL SQLAlchemy URL, for example `mysql+pymysql://USER:PASSWORD@HOST:PORT/DATABASE`. URL-encode special characters in the username or password.
   - `AIVEN_CA_PATH`: path to the Aiven CA certificate file supplied for your service. The backend passes it as the PyMySQL TLS CA setting.
   - `LLM_PROVIDER`: `fake` (scripted answers, no model needed) or `ollama`.
   - `OLLAMA_MODEL`: only when using Ollama. Install Ollama, run `ollama pull <model>`, and use the exact name shown by `ollama list`.
6. Install SWI-Prolog and make `swipl` available on `PATH`, or set `SWIPL_EXECUTABLE` in `.env`. Check it with `swipl --version`.
7. Run the tests from `backend/`: `pytest`
8. Start the app: `python run.py`
9. Check the health endpoint: `http://localhost:5000/health`
10. Optional demo script (no model needed): set `LLM_PROVIDER=fake`, then run `python scripts/demo_maria.py`.

Use fictional data only. Never put a real person's diary or personal details in this project.

## Frontend setup
The native mobile app is in `frontend/mobile/` and uses Expo + React Native.
Install Node.js (npm is included), then from the project root:

1. `cd frontend/mobile`
2. `npm install`
3. `npm start`
4. Scan the QR code with Expo Go, or press `a` to open an available Android emulator.
5. Run `npm run typecheck` to check the TypeScript project.

A native iOS build requires macOS and Xcode.

The native app uses the backend for owner registration/sign-in, diary entry
creation, policy submission, beneficiary invitations, beneficiary Q&A, and the
owner's grounded diary chatbot. Some unfinished screens still use local preview
data; the backend remains authoritative for access. Use fictional data only.
The logo is bundled at
`frontend/mobile/assets/images/ennova-logo.jpg`; its palette uses deep navy,
teal, and pale cyan.

### AI provider selection

The backend supports `groq`, `ollama`, and `fake` through `LLM_PROVIDER`. Groq uses the official Python SDK, `GROQ_API_KEY`, and defaults to `GROQ_MODEL=openai/gpt-oss-120b`; install dependencies from `backend/requirements.txt`, then set the key in the backend's ignored `.env`. Never put the Groq key in the mobile app. To switch providers, change `LLM_PROVIDER` and supply that provider's configuration; there is no automatic fallback. Groq sends the prompt evidence to hosted inference, and organization quotas vary by plan.

### Persistent account database

Owner accounts, beneficiary accounts, and invitations use the configured MySQL database. The `accounts` table stores normalized username/email, role, owner/person IDs, a password hash, and creation time. The `invitations` table stores only the invitation hash, owner/person IDs, expiry, and used state. Unique database constraints protect usernames, emails, and owner/person pairs. Beneficiary insertion and invitation use are committed in one transaction.

After checking the target Aiven database schema and confirming these table names are unused, initialize the schema from `backend/` with `flask --app run db upgrade`. The migration adds `accounts` and `invitations`; it does not drop tables, and its downgrade is intentionally disabled. Do not point tests at a production database. The SQL repository tests use isolated in-memory SQLite; live integration checks should use a dedicated disposable test database.

The local `.env` is loaded by the app configuration and is ignored by Git. Production uses SQLAlchemy persistence for accounts, invitations, diary entries and their hash chain, policy/lifecycle/audit state, derived summaries, and bounded owner chatbot follow-up context. Migrations do not run automatically. Apply them deliberately with `flask --app run db upgrade` from `backend/`, after checking the selected database and taking a backup. See [the API and configuration reference](docs/api-and-configuration.md) for persistence and recovery notes.

## Repository layout
| Path | Contents |
|---|---|
| `frontend/mobile/` | Expo + React Native mobile application |
| `frontend/mobile/app/` | Mobile routes and tab navigation |
| `frontend/mobile/components/` | Reusable native UI components |
| `frontend/mobile/data/` | Fictional frontend prototype data |
| `backend/app/` | Backend source code (domain, services, routes, AI) |
| `backend/app/policy/` | Policy language and the Prolog rules in `access_rules.pl` |
| `backend/scripts/` | Demo script |
| `backend/tests/` | Automated tests |
| `docs/grammar/` | EBNF grammar and sample policy programs |
| `docs/uml/` | UML diagrams based on the implemented backend and finalized requirements |
| `docs/` | Design notes, access test table, AI-use log |
| `docs/reports/` | Design report and presentation material |
| `.github/` | Repository Copilot instructions and path-specific instructions in `.github/instructions/` |
| `PROGRESS.md` | Feature tracker and weekly log |

## Notes
- Keep secrets in `.env` and never commit them.
- `backend/.env.example` contains placeholder values only.
- SWI-Prolog is required: the access rules run in it, and the tests fail (they don't skip) without it.
- Letters of Wishes in ENNOVA are personal messages and are not legal wills or substitutes for legally executed estate documents. ENNOVA does not provide legal advice.

## Known limitations
- Production diary, policy, lifecycle, audit, derived-summary, and owner follow-up data use the configured SQL database. The in-memory versions remain injectable for tests/demos.
- Production owner chatbot follow-up questions are bounded and owner-bound in SQL; test/demo adapters can remain in memory.
- Flask-Limiter uses in-memory rate-limit storage, so limits are per-process and are not suitable for production or multiple workers.
- No CI/CD, Docker, or deployment files are present.
- The Expo mobile client is a prototype and has not received full real-device or accessibility certification.
- F10 (Letter of Wishes) is incomplete.

See [docs/api-and-configuration.md](docs/api-and-configuration.md) for the REST endpoints and environment variables.

## UML diagrams

- [Use case diagram](docs/uml/use-case-diagram.md)
- [Sequence diagrams](docs/uml/sequence-diagram.md)
- [Class diagram](docs/uml/class-diagram.md)

## Branching
- `master` always works and passes all tests. Never commit directly to `master`.
- One branch per feature or task: `feature/<short-name>` (for example `feature/f3-writing-modes`), `fix/<short-name>`, `docs/<short-name>`, or `chore/<short-name>`.
- Merge into `master` through a pull request reviewed by a teammate other than the author.
- Delete the branch after merging.

## Commit messages
- Small, focused commits: one logical change each.
- Format: `type(scope): short summary`, in the imperative, up to about 72 characters.
- Types: `feat`, `fix`, `test`, `docs`, `refactor`, `chore`.
- Examples: `feat(vault): add append-only Vault class`, `test(prolog): add deny-overrides-allow cases`.
- If a commit contains AI-generated code, add `AI-assisted: yes (verified by <name>)` to the body.
- Commit under your own configured name and email.
