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
   - `LLM_PROVIDER`: `fake` (scripted answers, no model needed) or `ollama`.
   - `OLLAMA_MODEL`: only when using Ollama. Install Ollama, run `ollama pull <model>`, and use the exact name shown by `ollama list`.
6. Install SWI-Prolog and make `swipl` available on `PATH`, or set `SWIPL_EXECUTABLE` in `.env`. Check it with `swipl --version`.
7. Run the tests from `backend/`: `pytest`
8. Start the app: `python run.py`
9. Check the health endpoint: `http://localhost:5000/health`
10. Optional demo script (no model needed): set `LLM_PROVIDER=fake`, then run `python scripts/demo_maria.py`.

Use fictional data only. Never put a real person's diary or personal details in this project.

## Repository layout
| Path | Contents |
|---|---|
| `backend/app/` | Backend source code (domain, services, routes, AI) |
| `backend/app/policy/` | Policy language and the Prolog rules in `access_rules.pl` |
| `backend/scripts/` | Demo script |
| `backend/tests/` | Automated tests |
| `docs/grammar/` | EBNF grammar and sample policy programs |
| `docs/` | Design notes, access test table, AI-use log |
| `docs/reports/` | Design report and presentation material |
| `.github/` | Copilot instructions |
| `PROGRESS.md` | Feature tracker and weekly log |

## Notes
- Keep secrets in `.env` and never commit them.
- `backend/.env.example` contains placeholder values only.
- SWI-Prolog is required: the access rules run in it, and the tests fail (they don't skip) without it.

## Known limitations
- Accounts, entries, policies, and audit state are in memory. There are no SQLAlchemy models or migration revisions yet.
- Flask-Limiter uses in-memory rate-limit storage, so limits are per-process and are not suitable for production or multiple workers.
- No CI/CD, Docker, or deployment files are present.
- There is no mobile app.
- F10 (Letter of Wishes) is incomplete.

See [docs/api-and-configuration.md](docs/api-and-configuration.md) for the REST endpoints and environment variables.

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
