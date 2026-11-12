# ENNOVA

Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator

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
