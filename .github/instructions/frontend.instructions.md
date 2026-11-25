---
applyTo: "frontend/**"
---

# Copilot Instructions: ENNOVA Frontend

These instructions cover the **frontend only**. They extend the repository-wide `.github/copilot-instructions.md`; if the two ever conflict, the repository-wide file wins.

## 1. Scope

- Work only in `frontend/mobile/` (Expo / React Native). This is the primary frontend.
- Do not edit anything under `backend/`. The frontend may only describe the API it needs; it must not implement server logic.
- Never edit native directories (`android/`, `ios/`) by hand.

## 2. Before every task

1. Read `PROGRESS.md` (root) and `FRONTEND_PROGRESS.md`.
2. Build **one feature at a time**. Ask for approval before any large change (new dependency, restructuring, replacing state management, touching routing layout).
3. Work on a feature branch. Never commit directly to `main` or `master`.
4. When done: run type-check, lint, and tests; update `FRONTEND_PROGRESS.md`; follow the active task's scope for any other tracker; and log significant AI-assisted code in `docs/ai-use-log.md` with a blank verifier placeholder until review.

## 3. Tech stack (as documented from the repo)

| Area | Choice |
|---|---|
| Framework | Expo ~58 with Expo Router ~58 |
| Language | TypeScript, strict mode |
| UI | React Native core components and `expo-symbols`; no component library |
| State | React Context plus `useState` (`context/AppDataProvider.tsx`) |
| Navigation | Expo Router (file-based) only |
| Package manager | npm |
| HTTP client | Centralized `services/api.ts` |
| Session | `context/AuthProvider.tsx`, in-memory bearer token |
| Tests | Jest, `jest-expo`, React Native Testing Library |
| Lint | Expo ESLint (`npm run lint`) |

Check `frontend/mobile/package.json` and `package-lock.json` for exact versions before adding or upgrading anything. Do not add dependencies without approval.

## 4. Folder structure

```text
frontend/mobile/
├── app/            Expo Router screens and layouts
│   ├── (tabs)/     Bottom-tab screens
│   └── entries/    Entry creation and detail routes
├── assets/         Fonts and images
├── components/     Shared native UI components
├── constants/      Theme colors and spacing (theme.ts)
├── context/        In-memory app state provider
├── data/           Fictional mock data
├── services/       API client and pure policy-source helpers
└── types.ts        Shared data types
```

- Screens go in `app/`. Reusable UI goes in `components/`. Never put reusable components inside route folders.
- Shared types go in `types.ts` (union types for visibility, writing mode, beneficiary status).

## 5. Commands

Run from `frontend/mobile/`:

| Task | Command |
|---|---|
| Clean install | `npm ci` |
| Start | `npm start` |
| Android / iOS / Web | `npm run android` / `npm run ios` / `npm run web` |
| Type-check | `npm run typecheck` |
| Lint | `npm run lint` |
| Tests | `npm test` |
| Export | `npx expo export --platform android` |

- If an approved Expo-native dependency is added, use `npx expo install <package>`.
- Run type-check, lint, and tests before declaring any task complete. Do not run `npm install` to update the lockfile.

## 6. Coding conventions (match existing code)

- Function components with uppercase names; strict typing everywhere. Public functions and classes need explicit types.
- Import workspace files with the `@/*` alias (example: `app/(tabs)/journal.tsx`).
- Styles: `StyleSheet.create`, colocated in the same file as the component. Take colors and spacing from `constants/theme.ts`; do not hardcode hex values or magic spacing numbers.
- No semicolons, matching the existing files.
- Each source file starts with a short comment naming the paradigm it demonstrates and the team members, as required by the repository-wide instructions.
- Keep comments purposeful. Do not leave commented-out code.

## 7. Screens, navigation, and layout

- Use Expo Router only. Do not add React Navigation setup or React Router DOM in the mobile app.
- Existing routes: `/`, `/login`, `/(tabs)` (index, journal, people, policy, more), `/entries/new`, `/entries/[id]`, `/assistant`, `/settings`, `/beneficiary`, and `+not-found`.
- Wrap screens in `AppScreen` (safe area plus optional scroll). Reuse `ActionButton`, `Panel`, `PageTitle`, `PreviewNotice`, `EntryRow`, `VisibilityBadge`, and `Brand` before creating new components.
- Design mobile-first and cross-platform. Handle keyboard avoidance on forms, and consider performance (stable list keys, avoid heavy work in render).

## 8. State and data

- Read and mutate app data through `useAppData`. Do not create parallel stores.
- Preview data is fictional, in memory, and resets on restart. Some owner flows use the backend API; use `services/api.ts`, keep loading and safe error states explicit, and never add parallel networking or a state library.
- Show an explicit empty state for lists and search results (see `app/(tabs)/journal.tsx`).
- API-backed owner login/registration, entries, invitations, policy updates, and grounded Q&A are implemented through the shared API module. Treat mock and beneficiary-preview surfaces as previews, not authorization.

## 9. Access policy rule (critical)

- UI policy actions produce policy-language source text and submit it through `PUT /policy`; the backend lexer, parser, and interpreter validate and process it.
- The frontend must **never** generate Prolog facts directly.
- The policy source is replaced as a whole; the app has no `GET /policy`. Show the complete source and replacement warning before sending it.
- Release dates are policy statements sent through `PUT /policy`, not fields on the letter entry. Letter save and release-rule publication are separate requests.
- Use `services/policySource.ts` for person-ID validation/normalization and safe release-rule source generation; do not duplicate reserved-word lists.

## 10. Data, privacy, and security

- Use fictional data only. Never enter real diary content, real names, or credentials in code, mock data, tests, or screenshots.
- Never expose secrets. Never commit `.env` or credential files.
- Owner sign-in and registration use the configured backend. Bearer tokens remain in React memory and reset on sign-out or restart; do not log tokens, passwords, emails, titles, or diary content.
- Keep preview notices on mock or incomplete surfaces. Backend authorization remains authoritative; frontend labels and state do not grant access.
- Do not add persistent token storage or a secure-storage dependency without approval.

## 11. Accessibility

- Interactive elements need `accessibilityRole` and `accessibilityLabel`; use `accessibilityState` for selected, disabled, or busy states.
- Keep touch targets comfortably sized and text readable against the theme colors.

## 12. Testing and verification

- Add focused tests for new behavior using the existing Jest, `jest-expo`, and React Native Testing Library setup; no test dependency is needed for routine frontend changes.
- Run `npm test`, `npm run lint`, and `npm run typecheck`. For visual changes, describe the platform/device check actually performed; do not claim a native or small-screen check without doing it.
- Describe what you verified in the PR.

## 13. Git and PRs

- Feature branch, focused commits with clear messages, PR for review.
- Note AI assistance in `docs/ai-use-log.md`.

## 14. Do not

- Do not touch `backend/`, `android/`, or `ios/`.
- Do not add dependencies without approval.
- Do not invent endpoints or environment variables. Verify new API behavior against the backend contract and keep authorization on the backend.
- Do not mix multiple features in one change.

## 15. Unresolved questions (ask the team, do not assume)

- Team-certified Node.js support range. Installed Expo/React Native engines currently intersect at `^22.13.0 || ^24.3.0 || >=26.0.0`; confirm the team's supported range before claiming certification.
- Whether state should persist locally or the backend is the source of truth.
- Persistent secure token storage is not implemented.
- The backend has no `GET /policy`, so the frontend cannot read an existing active policy source.
- Instructor approval for optional mobile scope is tracked in `PROGRESS.md`; follow the active task's scope and do not assume approval.
