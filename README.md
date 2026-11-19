# ENNOVA

## Team

| Member | Role |
|---|---|
| Roldan Jr. Bazares | Front End |
| Ranzel Jay Gobris | Lead Developer / Back End |
| Bart Jayson Lola | Q/A |
| Jallil Sultan | UI/UX Designer |
| Jezelle Gabion | Documentator |

## Project summary
ENNOVA is a personal AI diary and digital legacy app that keeps owner-written entries private, exposes only permitted content to beneficiaries, and routes access decisions through a policy language plus Prolog rules.

## Foundation (F0)
This repository is being set up as a clean project foundation for the ENNOVA backend and future feature work.

## Local setup
1. Open a PowerShell session in the project root.
2. Create and activate the backend virtual environment:
   - `cd backend`
   - `py -3 -m venv .venv`
   - `.\.venv\Scripts\Activate.ps1`
3. Install dependencies:
   - `pip install -r requirements.txt`
4. Copy the example environment file and fill in real values for your environment:
   - `Copy-Item .env.example .env`
5. Start the app:
   - `python run.py`
6. Verify the API health check:
   - `http://localhost:5000/health`

## Notes
- Keep secrets in `.env` and never commit them.
- `backend/.env.example` contains placeholder values only.
- SWI-Prolog is installed for the later F5 logic component.

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
