# Copilot Instructions: ENNOVA Frontend

These instructions cover the **frontend only**. They extend the repository-wide `.github/copilot-instructions.md`; if the two ever conflict, the repository-wide file wins.

## 1. Scope

- Work only in `frontend/mobile/` (Expo / React Native). This is the primary frontend.
- `frontend/src/` is a preserved Vite browser prototype. Do not change it unless explicitly asked.
- Do not edit anything under `backend/`. The frontend may only describe the API it needs; it must not implement server logic.
- Never edit native directories (`android/`, `ios/`) by hand.

## 2. Before every task

1. Read `PROGRESS.md` (root) and `FRONTEND_PROGRESS.md`.
2. Build **one feature at a time**. Ask for approval before any large change (new dependency, restructuring, replacing state management, touching routing layout).
3. Work on a feature branch. Never commit directly to `main` or `master`.
4. When done: run type-check and lint, update `FRONTEND_PROGRESS.md` (and `PROGRESS.md` if a tracked feature changed), and log any AI-assisted code in `docs/ai-use-log.md` with the verifier's name.

## 3. Tech stack (as documented from the repo)

| Area | Choice |
|---|---|
| Framework | Expo ~58 with Expo Router ~58 |
| Language | TypeScript, strict mode |
| UI | React Native core components and `expo-symbols`; no component library |
| State | React Context plus `useState` (`context/AppDataProvider.tsx`) |
| Navigation | Expo Router (file-based) only |
| Package manager | npm |
| HTTP client | None yet |
| Tests | None yet |

Check `frontend/mobile/package.json` for exact versions before adding or upgrading anything.

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
└── types.ts        Shared data types
```

- Screens go in `app/`. Reusable UI goes in `components/`. Never put reusable components inside route folders.
- Shared types go in `types.ts` (union types for visibility, writing mode, beneficiary status).

## 5. Commands

Run from `frontend/mobile/`:

| Task | Command |
|---|---|
| Install | `npm install` |
| Start | `npm start` |
| Android / iOS / Web | `npm run android` / `npm run ios` / `npm run web` |
| Type-check | `npm run typecheck` |
| Export | `npx expo export --platform android` |

- Add Expo-native packages with `npx expo install <package>`, not plain `npm install`.
- Run lint and type-check before declaring any task complete.

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
- Current data is fictional, in memory, and resets on restart. Do not add persistence, networking, or a state library without approval.
- Show an explicit empty state for lists and search results (see `app/(tabs)/journal.tsx`).
- When API integration is approved: put API calls in a dedicated module (not inside screens), model loading and error states explicitly, and never log tokens or diary content.

## 9. Access policy rule (critical)

- UI policy actions must produce **policy text** that is passed through the project's lexer, parser, and interpreter.
- The frontend must **never** generate Prolog facts directly.

## 10. Data, privacy, and security

- Use fictional data only. Never enter real diary content, real names, or credentials in code, mock data, tests, or screenshots.
- Never expose secrets. Never commit `.env` or credential files.
- Sign-in is simulated; do not present it as real authentication. Keep the `PreviewNotice` disclaimers in place.
- If tokens are ever stored on device, use a secure store (for example Expo SecureStore), and only after approval.

## 11. Accessibility

- Interactive elements need `accessibilityRole` and `accessibilityLabel`; use `accessibilityState` for selected, disabled, or busy states.
- Keep touch targets comfortably sized and text readable against the theme colors.

## 12. Testing and verification

- The repository requires tests to be written and run for new features, but no test framework is installed yet. If a feature needs tests, propose a framework (for example Jest with `jest-expo` and React Native Testing Library) and wait for approval before adding it.
- Until then, at minimum run `npm run typecheck`, run the app, and manually check the changed screen on at least one native target.
- Describe what you verified in the PR.

## 13. Git and PRs

- Feature branch, focused commits with clear messages, PR for review.
- Note AI assistance in `docs/ai-use-log.md`.

## 14. Do not

- Do not touch `backend/`, `frontend/src/`, `android/`, or `ios/`.
- Do not add dependencies without approval.
- Do not implement real auth, authorization, or API calls until the backend contract is confirmed.
- Do not invent endpoints, env variable names, or Node version requirements; none are documented yet.
- Do not mix multiple features in one change.

## 15. Unresolved questions (ask the team, do not assume)

- Supported Node.js versions.
- Backend REST endpoints and authentication flow.
- Whether state should persist locally or the backend is the source of truth.
- Required test framework and accessibility standard.
- Whether mobile feature F11 is approved for scope (instructor approval pending per `PROGRESS.md`).
- Whether the Vite prototype stays, goes, or becomes reference-only.
