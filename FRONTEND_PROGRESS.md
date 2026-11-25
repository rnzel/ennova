# ENNOVA (Alaala) – Front End Progress Tracker

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
> Course: CS 413 – Programming Languages Final Project
> Scope: front end only (`frontend/mobile/`, Expo). Backend progress lives in `PROGRESS.md`. The old Vite browser prototype was removed on 2026-11-20 (branch `feature/f11-remove-vite-prototype`).

**Current feature:** F11g – Front end quality: tests and accessibility `[~]`
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
- [x] `npm run typecheck` passes (exit code 0, 2026-11-20)
- [x] Jest/React Native Testing Library setup and focused tests added during F11g (approval received)
- [x] Lint script (`AGENTS.md` requires lint before finishing; Expo ESLint and `npm run lint` are configured)
- [x] Document supported Node version and setup steps in README
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/app/`, `frontend/mobile/components/`, `frontend/mobile/constants/theme.ts`, `frontend/mobile/context/AppDataProvider.tsx`, `frontend/mobile/data/mockData.ts`, `frontend/mobile/types.ts`, `frontend/mobile/app.json`, `frontend/mobile/package.json`, `frontend/mobile/tsconfig.json`
- **Tests:** no automated tests yet. `npm run lint` and `npm run typecheck` passed (exit code 0) on 2026-11-21.
- **Open issues:** Sign-in is simulated. State is in memory and resets on restart. All data is hardcoded and fictional. No HTTP client, no persistence, no accessibility audit. Instructor approval for the mobile interface (F11) is still pending.
- **Verified by:** review pending

### F11b – API client and session `[~]`
Depends on backend F9a (REST API, bearer JWT).
- [x] Single API module (no `fetch` calls inside screens); base URL from `EXPO_PUBLIC_API_BASE_URL` in `.env.example`
- [x] Register and sign-in against the backend; replaced the simulated login
- [x] Attach bearer JWT to authenticated API requests; session rejects 401/403 responses
- [ ] Secure token storage (Expo SecureStore deferred; session is React in-memory only for now)
- [x] Loading and error states; map backend generic errors to safe user messages (never show internal detail)
- [x] Never log tokens, passwords, or diary content
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/services/api.ts`, `frontend/mobile/context/AuthProvider.tsx`, `frontend/mobile/app/login.tsx`, `frontend/mobile/app/_layout.tsx`, `frontend/mobile/.env.example`, `frontend/mobile/README.md`
- **Tests:** pending
- **Open issues:** JWT storage is intentionally in memory, resets on app restart, and is not a persistent secure-store implementation. Backend API state and rate limits are process-local. Backend added no CORS, which matters only if the Expo web target is used. Password reset and refresh tokens do not exist (out of scope).
- **Verified by:** pending

### F11c – Entries and writing modes `[~]`
Depends on F11b; backend F1, F2, F3, F6a.
- [x] Write diary entries through the API; list and detail screens use API metadata instead of mock entries after sign-in
- [x] No edit or delete UI: the vault is append-only
- [x] Hint for `[[name]]` and `#tag` entry syntax
- [~] Writing mode choice remains in the editor; the backend entry route does not accept or return writing-mode derived versions
- [ ] Show a clear message when tampering or an unavailable summary is reported by the backend
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/services/api.ts`, `frontend/mobile/context/AppDataProvider.tsx`, `frontend/mobile/app/(tabs)/journal.tsx`, `frontend/mobile/app/entries/new.tsx`, `frontend/mobile/app/entries/[id].tsx`, `frontend/mobile/types.ts`
- **Tests:** pending
- **Open issues:** The backend list route returns entry metadata only, with no entry detail/content route or writing-mode/derived-summary fields. The UI explicitly shows metadata and unavailable content; it does not invent those values. Entry save is followed by best-effort summarization on the backend, so derived content may be missing; the UI must tolerate that.
- **Verified by:** pending

### F11d – Policy builder `[x]`
Depends on F11b; backend F4 (policy language), F5 (Prolog access), F9a.
- [x] Templates for common policies
- [x] Plain-language preview of the policy
- [x] Advanced editor for policy text
- [x] Builder generates policy text and sends it through `PUT /policy`; the front end never generates Prolog facts
- [x] Show `PolicySyntaxError` line and column as a readable message
- [x] Handle `policy_frozen` by disabling edits
- [x] Builder covers tagged/mentioning selectors, may-see/deny, may-read/deny levels, release, custody, trustee, and default writing mode
- **Paradigm:** Language design (UI feeds the policy language)
- **Files changed:** `frontend/mobile/app/(tabs)/policy.tsx`, `frontend/mobile/services/api.ts`
- **Tests:** pending (builder output should be checked against the backend parser)
- **Open issues:** Parser-facing valid/invalid UI tests remain pending framework approval.
- **Verified by:** lint/typecheck pending teammate review

### F11e – Beneficiaries and invitations `[~]`
Depends on F11b; backend F6 (accounts, invitation codes).
- [x] Owner issues an invitation code and sees that it is expiring and single-use
- [x] Beneficiary registers with an invitation code
- [ ] Beneficiary view shows only permitted answers; entries never move to the heir's account
- [x] Generic failure messages for bad credentials, invalid invitations, and lockout delay
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/app/login.tsx`, `frontend/mobile/app/(tabs)/people.tsx`, `frontend/mobile/context/AuthProvider.tsx`, `frontend/mobile/services/api.ts`
- **Tests:** pending
- **Open issues:** The beneficiary answer view remains a local mock preview until F11f provides authorized backend answers.
- **Verified by:** pending

### F11f – Ask questions with cited answers `[~]`
Depends on F11b; backend F7, F7a, F7c–F7e, F8, F9a.
- [x] Question form sends to the backend `/ask` route
- [x] Display date citations returned with answers
- [x] Denied and no-record responses use the backend neutral answer and the same UI
- [x] Pre-release messages are displayed when returned by the backend
- [x] Safe AI unavailable state; slow-response timeout and retry
- [x] Client does not persist restricted content; answers exist only in screen state
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/app/assistant.tsx`, `frontend/mobile/services/api.ts`
- **Tests:** pending (cover the six Maria scenarios at UI level once the API is wired)
- **Open issues:** Backend owner `/ask` returns the neutral reply until Prolog exposes an `owner/1` fact. Live Ollama calls can time out on small CPU-only models, so UI timeouts matter. Current assistant screen is a simulated local form.
- **Verified by:** pending

### F10 – Letter of Wishes (front end) `[~]`
- [x] Letter entry screen with recipient and release date
- [x] Always-visible "not a legal will" disclaimer
- [x] Validate strict policy person IDs and real calendar dates; warn without blocking for past dates
- [x] Save the letter first, then confirm and publish the escaped release rule as a complete policy source
- [x] Keep failed release sources in shared app state; retry sends only `PUT /policy`
- [x] Show the letter-specific duplicate-title message and the server disclaimer on API letter records
- [x] Confirm full-source replacement before policy publishing; keep unauthenticated use preview-only
- [x] Share a person-ID helper between letter validation and policy templates
- **Paradigm:** n/a (interface)
- **Files changed:** `frontend/mobile/services/policySource.ts`, `frontend/mobile/components/PolicyPublishManager.tsx`, `frontend/mobile/context/AppDataProvider.tsx`, `frontend/mobile/app/_layout.tsx`, `frontend/mobile/app/entries/new.tsx`, `frontend/mobile/app/entries/[id].tsx`, `frontend/mobile/app/(tabs)/policy.tsx`, API/data types, and focused tests
- **Tests:** `npm test` (8 suites, 34 tests passed); `npm run lint` and `npm run typecheck` pass. Three generated full policy sources parsed successfully with the backend parser.
- **Open issues:** End-to-end verification against the real backend: pending. Authenticated owners should start from an empty policy in F11d because the app cannot read the active backend source. Beneficiary types do not expose person IDs; a recipient picker remains a later improvement.
- **Verified by:** pending

### F11g – Front end quality: tests and accessibility `[~]`
- [x] Agree on Jest, `jest-expo`, and React Native Testing Library; approval received 2026-11-21
- [x] Eleven tests cover API request/error behavior, auth/logout, journal search/filter, policy deny-rule generation, login validation/beneficiary mode, and Letter of Wishes form requirements
- [~] Added accessible names/roles/states to reviewed controls, keyboard avoidance and scrolling, and 44-point navigation targets; larger system-font/device validation remains pending
- [x] Reviewed remaining theme and literal text color pairs; all measured pairs meet 4.5:1 contrast (4.70:1 minimum)
- [~] Attempted a 320×568 viewport check across the routes; the browser DOM showed no horizontal overflow, but the web preview rendered without React Native styles. The minimum target is now 360×640 logical points; real small-phone check remains pending
- [x] `npm test -- --watch=false`, `npm run lint`, and `npm run typecheck` pass (2026-11-22)
- [x] Current full frontend validation: `npm test` (9 suites, 36 tests), `npm run lint`, and `npm run typecheck` pass (2026-11-25)
- **Paradigm:** n/a (quality)
- **Files changed:** `frontend/mobile/package.json`, `frontend/mobile/tsconfig.json`, `frontend/mobile/services/api.test.ts`, `frontend/mobile/context/AuthProvider.test.tsx`, `frontend/mobile/__tests__/journal.test.tsx`, `frontend/mobile/__tests__/policy.test.tsx`, `frontend/mobile/__tests__/entry-form.test.tsx`, `frontend/mobile/__tests__/login.test.tsx`, reviewed app screens, `frontend/mobile/components/ActionButton.tsx`, `frontend/mobile/components/Brand.tsx`, `frontend/mobile/components/EntryRow.tsx`, `frontend/mobile/components/PageTitle.tsx`, `frontend/mobile/constants/theme.ts`
- **Tests:** `npm test -- --watch=false` (11 passed); `npm run lint` and `npm run typecheck` pass (2026-11-22)
- **Open issues:** This remains a focused pass, not a full-app accessibility certification. Real small-phone check at 360×640 and teammate verification (Bart) remain pending.
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

## Browser prototype (removed)
- [x] Decision: remove the Vite browser prototype; `frontend/mobile/` is the only frontend
- [x] Removed `frontend/src/`, `frontend/public/`, and the Vite config, package, and tsconfig files (41 tracked files), plus the untracked `frontend/node_modules` and `frontend/dist`
- [x] Template assets (`react.svg`, `vite.svg`, `hero.png`) removed; the duplicate logo removed after its hash matched the mobile copy
- [x] Mobile typecheck passes after the removal; no files under `frontend/mobile/` were changed
- [ ] Commit the cleanup, fill in the verifier name in `docs/ai-use-log.md`, and open the PR
- **Recovery:** the full prototype is in commit `be7849d` on branch `feature/f11a-mobile-baseline`.

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
| 2026-11-20 | Vite browser prototype removed; `frontend/mobile/` is the only frontend | Reduce confusion; mobile is the intended target. Full prototype kept in commit `be7849d` |
| 2026-11-25 | Frontend Copilot guidance moved to `.github/instructions/frontend.instructions.md` with `applyTo: "frontend/**"` | Ensure frontend-specific guidance is loaded for frontend files and matches the current Expo/API/test setup |

## Weekly log
| Week | What was done | Next |
|---|---|---|
| Audit (2026-11-20) | Audited the front end: Expo skeleton with 13 routes, 8 shared components, mock data; no API, auth, persistence, or tests. Wrote front end Copilot instructions and this tracker | Get F11 approval, confirm backend contract, then F11b |
| Cleanup (2026-11-20) | Committed the mobile baseline (`be7849d`), then removed the Vite prototype (41 tracked files) on `feature/f11-remove-vite-prototype`; mobile typecheck passes | Commit, name the verifier, open PR, then confirm the F11 approval and backend contract |
| Quality setup (2026-11-21) | Added Expo ESLint configuration and fixed the two reported lint findings; documented Node/npm setup and validation in the mobile README | Automated tests remain approval-gated; confirm the test framework, then add F11g coverage |
| F11 API and policy (2026-11-21) | Added the centralized API client, in-memory auth session, API-backed entry metadata/create flow, policy submission, invitation issuance/registration, and grounded Q&A | Finish F11g screen tests and accessibility pass; retain documented backend-contract limitations |
| Web preview (2026-11-21) | Started Expo web and changed the preview configuration from server output to static output so React Native Web styles are emitted for the visible frontend preview | Verify the restarted web page visually; keep the server running on port 8081 |
| F11g quality pass (2026-11-22) | Added login/letter form tests; extended accessibility labels/roles and 44-point targets across the remaining reviewed screens; improved placeholder/footnote contrast; all 11 tests, lint, and typecheck pass | Resolve the unstyled Expo web preview or verify a styled native build at the minimum device size before deciding whether F11g can be marked complete |
| Instructions update (2026-11-25) | Moved frontend-specific guidance to a path-specific Copilot instruction with current API, policy, lint, and test guidance | Continue F11g quality/accessibility audit |

F11g quality continuation (2026-11-25): extended keyboard/scroll behavior, accessible names and navigation targets; documented the 360×640 minimum layout target and Node engine intersection. Real small-phone check and teammate verification (Bart) remain pending.

## Consolidated next steps

1. Continue F11g:
   - Add focused `AppDataProvider` and remaining policy/API form tests where useful.
   - Remaining measured text-color pairs pass 4.5:1; verify every screen on a real device at 360×640 logical points and obtain teammate verification (Bart).
   - Do not claim full-app accessibility certification without a complete device and screen audit.
   - Keep `npm test`, `npm run lint`, and `npm run typecheck` passing.
2. Continue F11c:
   - Represent derived versions and unavailable/tampered summaries only if backend routes provide those fields.
   - Keep the append-only vault with no edit/delete controls.
3. Confirm backend behavior for Letter of Wishes date storage; do not imply the entry endpoint persisted a release date.
4. Before PR:
   - Run `npm run lint` and `npm run typecheck`.
   - Fill reviewer/verifier names in this tracker and `docs/ai-use-log.md`.
   - Record the verified Expo web/mobile demo and open the frontend PR.