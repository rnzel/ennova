# ENNOVA (Alaala) – Front End Progress Tracker

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
> Course: CS 413 – Programming Languages Final Project
> Scope: front end only (`frontend/mobile/`, Expo). Backend progress lives in `PROGRESS.md`. `frontend/src/` is the preserved Vite prototype and is reference only.

**Current feature:** F11a – Mobile UI skeleton `[~]`
**Rule:** one feature at a time. Finish, test, update this file, get approval, then move on.

Status key: `[ ]` not started, `[~]` in progress, `[x]` done and tested, `[!]` blocked

---

## Required features (front end side)

### F11a – Mobile UI skeleton (Expo) `[~]`
- [x] Expo Router app with intro, sign-in, five tabs (home, journal, people, policy, more), entry create/detail, assistant, settings, beneficiary, and not-found routes
- [x] Shared components: `ActionButton`, `AppScreen`, `Brand`, `EntryRow`, `PageTitle`, `Panel`, `PreviewNotice`, `VisibilityBadge`
- [x] Theme constants (colors, spacing) and `StyleSheet.create` styling
- [x] `AppDataProvider` (React Context) with fictional mock entries, beneficiaries, and policy text
- [x] Journal search/filter with explicit empty state
- [x] Simulated sign-in and preview disclaimers (no real credentials or diary content)
- [ ] Automated tests (no framework installed yet; propose and get approval first)
- [ ] Lint script (`AGENTS.md` requires lint before finishing; only `typecheck` exists in `package.json`)
- [ ] Document supported Node version and setup steps in README
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/app/`, `frontend/mobile/components/`, `frontend/mobile/constants/theme.ts`, `frontend/mobile/context/AppDataProvider.tsx`, `frontend/mobile/data/mockData.ts`, `frontend/mobile/types.ts`, `frontend/mobile/app.json`, `frontend/mobile/package.json`, `frontend/mobile/tsconfig.json`
- **Tests:** none yet. Only `npm run typecheck` exists; no result was recorded in the repository audit.
- **Open issues:** Sign-in is simulated. State is in memory and resets on restart. All data is hardcoded and fictional. No HTTP client, no persistence, no accessibility audit. Instructor approval for the mobile interface (F11) is still pending.
- **Verified by:** review pending

### F11b – API client and session `[ ]`
Depends on backend F9a (REST API, bearer JWT).
- [ ] Single API module (no `fetch` calls inside screens); base URL from an Expo public env variable (name to be agreed, placeholders only in `.env.example`)
- [ ] Register and sign-in against the backend; replace the simulated login
- [ ] Attach bearer JWT to requests; handle expired or rejected tokens
- [ ] Secure token storage (e.g. Expo SecureStore, installed with `npx expo install`; needs approval)
- [ ] Loading and error states; map backend generic errors to safe user messages (never show internal detail)
- [ ] Never log tokens, passwords, or diary content
- **Paradigm:** n/a (interface)
- **Files changed:** pending
- **Tests:** pending
- **Open issues:** Backend API state and rate limits are process-local. Backend added no CORS, which matters only if the Expo web target is used. Backend contract (routes, payloads, error codes) must be confirmed with the Lead Developer. Password reset and refresh tokens do not exist (out of scope).
- **Verified by:** pending

### F11c – Entries and writing modes `[ ]`
Depends on F11b; backend F1, F2, F3, F6a.
- [ ] Write entries through the API; list and detail screens read from the API instead of mock data
- [ ] No edit or delete UI: the vault is append-only
- [ ] Hint and highlight `[[name]]` and `#tag` entry syntax
- [ ] Writing mode choice in the editor (Verbatim, LightFix, Review) and display of derived versions linked to the original
- [ ] Show a clear message when tampering or an unavailable summary is reported by the backend
- **Paradigm:** n/a (interface)
- **Files changed:** pending
- **Tests:** pending
- **Open issues:** Entry save is followed by best-effort summarization on the backend, so derived content may be missing; the UI must tolerate that.
- **Verified by:** pending

### F11d – Policy builder `[ ]`
Depends on F11b; backend F4 (policy language), F5 (Prolog access), F9a.
- [ ] Templates for common policies
- [ ] Plain-language preview of the policy
- [ ] Advanced editor for policy text
- [ ] Builder **always generates policy text** that is sent through the backend lexer, parser, and interpreter; the front end never generates Prolog facts
- [ ] Show `PolicySyntaxError` line and column as a readable message
- [ ] Handle a frozen policy (`PolicyFrozen`) without allowing edits
- [ ] Stay within the statements the grammar supports (may see, may read/deny, release letter, transfer custody, default writing mode, optional `trustee is`); check `docs/grammar/grammar.ebnf`
- **Paradigm:** Language design (UI feeds the policy language)
- **Files changed:** pending
- **Tests:** pending (builder output should be checked against the backend parser)
- **Open issues:** Current policy screen is a plain text preview with no parser connection.
- **Verified by:** pending

### F11e – Beneficiaries and invitations `[ ]`
Depends on F11b; backend F6 (accounts, invitation codes).
- [ ] Owner issues an invitation code and sees that it is expiring and single-use
- [ ] Beneficiary registers with an invitation code
- [ ] Beneficiary view shows only permitted answers; entries never move to the heir's account
- [ ] Generic failure messages for bad credentials and lockout delay
- **Paradigm:** n/a (interface)
- **Files changed:** pending
- **Tests:** pending
- **Open issues:** Current people and beneficiary screens use local sample data only.
- **Verified by:** pending

### F11f – Ask questions with cited answers `[ ]`
Depends on F11b; backend F7, F7a, F7c–F7e, F8, F9a.
- [ ] Question form sends to the backend Q&A route
- [ ] Display date citations returned with answers
- [ ] Denied and no-record responses use the same neutral message and look identical in the UI
- [ ] Show the pre-release date message when the backend sends it
- [ ] Show a safe "AI unavailable" state; handle slow responses (timeouts, retry)
- [ ] Never display or store restricted content on the client
- **Paradigm:** n/a (interface)
- **Files changed:** pending
- **Tests:** pending (cover the six Maria scenarios at UI level once the API is wired)
- **Open issues:** Backend owner `/ask` returns the neutral reply until Prolog exposes an `owner/1` fact. Live Ollama calls can time out on small CPU-only models, so UI timeouts matter. Current assistant screen is a simulated local form.
- **Verified by:** pending

### F10 – Letter of Wishes (front end) `[ ]`
- [ ] Letter entry screen with recipient and release date
- [ ] Always-visible "not a legal will" disclaimer
- **Paradigm:** n/a (interface)
- **Files changed:** pending
- **Tests:** pending
- **Open issues:** Not started. Letter title duplicates are rejected by the backend for the same owner; the UI should show that error.
- **Verified by:** pending

### F11g – Front end quality: tests and accessibility `[ ]`
- [ ] Agree on a test framework (proposal: Jest with `jest-expo` and React Native Testing Library) and get approval
- [ ] Tests for `AppDataProvider`, journal filtering, forms, and key screens
- [ ] Accessibility pass: roles, labels, states, touch targets, contrast
- [ ] `typecheck` and lint pass before each PR
- **Paradigm:** n/a (quality)
- **Files changed:** pending
- **Tests:** pending
- **Open issues:** Accessibility standard and minimum screen sizes not yet decided.
- **Verified by:** pending

### F11 – Mobile interface (Expo) overall `[~]`
- [~] F11a skeleton, F11b–F11g, and F10 front end items above
- [ ] Policy builder always generates policy text through the parser (see F11d)
- **Note:** a mobile interface is a listed extra. Confirm with the instructor first.

---

## Optional extras (front end related, instructor approval REQUIRED before building)

Each needs: paradigm stated, follows access protocol, tested, AI-code verification explained. Backend-led extras are tracked in `PROGRESS.md`.

| Extra | Paradigm | Instructor told? | Approved? | Status |
|---|---|---|---|---|
| Android app (Expo) | n/a (interface) | [ ] | [ ] | `[~]` skeleton exists, approval pending |
| Biometric app lock | n/a (platform) | [ ] | [ ] | `[ ]` |

## Out of scope (state in design report)
Device trust, recovery codes, password reset, full trustee verification workflow. Do not build screens for these.

---

## Browser prototype (reference only)
- [x] Vite app in `frontend/src/` with intro, sign-in, beneficiary, owner entries, editor, detail, beneficiaries, policy, Q&A, settings, and not-found routes
- [ ] Decision: keep, remove, or freeze as reference only
- [ ] Remove unused assets (`react.svg`, `vite.svg`, `hero.png`) if the prototype is kept
- **Rule:** do not extend it; new work goes in `frontend/mobile/`.

---

## Deliverables checklist (front end)
- [ ] Working mobile prototype under version control (history shows Roldan's commits and reviewed PRs)
- [ ] README setup steps for `frontend/mobile/` (Node version, install, start, typecheck)
- [ ] AI-use log entries for all AI-assisted front end code, with verifier names
- [ ] Policy builder shown generating text through the parser (supports the grammar deliverable)
- [ ] Parser-facing UI tests or demo script for valid and invalid policy input
- [ ] Screens for slides and live demo (Maria scenarios as seen in the app)
- [ ] All five names and the demonstrated paradigm on every source file
- [ ] Weekly updates from the front end member in Linear

## Git conventions (summary)
- Branch per feature: `feature/f<number>-<name>` (e.g. `feature/f11b-api-client`). Never commit to `main`.
- PR title `F<number>: <name>`, reviewed by a teammate (reviewer = verifier in AI-use log).
- Commit format: `type(scope): summary` (feat, fix, test, docs, refactor, chore).
- Full rules: `.github/copilot-instructions.md`, section 11.

## Defense questions to prepare (front end)
- How does the UI make sure policy actions go through the parser instead of writing Prolog facts?
- How does the app avoid revealing whether a restricted entry exists?
- Where are tokens stored, and what is never logged?
- Why is there no edit or delete button for entries?
- Which front end code did AI write and how did you check it?
- If you added a feature, which paradigm and why?

## Decision log
| Date | Decision | Reason |
|---|---|---|
| 2026-11-12 | UI builder generates policy text through the parser | Keeps Language Design component real (from `PROGRESS.md`) |
| 2026-11-12 | Mobile app postponed until instructor approves | Mobile is a listed extra (from `PROGRESS.md`) |
| 2026-11-20 | Primary front end is the Expo app in `frontend/mobile/`; Vite app is reference only | Repo docs state the mobile app is the intended target (recorded from audit) |
| 2026-11-20 | Skeleton state uses React Context with fictional in-memory data | Lets screens be built before the backend API is wired (recorded from audit) |

## Weekly log
| Week | What was done | Next |
|---|---|---|
| Audit (2026-11-20) | Audited the front end: Expo skeleton with 13 routes, 8 shared components, mock data; no API, auth, persistence, or tests. Wrote front end Copilot instructions and this tracker | Get F11 approval, confirm backend contract, then F11b |