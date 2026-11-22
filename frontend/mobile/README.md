# ENNOVA mobile app

This directory contains the Expo Router and React Native frontend for ENNOVA.

## Supported setup

- Node.js 20.19 or newer
- npm 10 or newer
- Expo Go or an emulator for the Android, iOS, or web preview

From this directory:

```powershell
npm install
npm start
```

Use `npm run android`, `npm run ios`, or `npm run web` to open a platform-specific
target. Native iOS builds require macOS and Xcode.

## Validation

```powershell
npm test
npm run lint
npm run typecheck
```

Run all three checks before changing progress, opening a pull request, or
declaring a frontend feature ready.

## API session preview

Copy `.env.example` to `.env.local` and set `EXPO_PUBLIC_API_BASE_URL` to the
running ENNOVA backend URL. The owner login and registration screens use the
backend `/auth/login` and `/auth/register-owner` routes.

JWT access tokens are currently held only in React memory. They are cleared when
the app restarts or the user signs out, and this session is not persistent.
The app does not log passwords, tokens, or diary content.

## Structure

- `app/` - Expo Router routes and layouts
- `components/` - Shared mobile UI components
- `constants/theme.ts` - App colors and spacing
- `context/AppDataProvider.tsx` - In-memory preview state
- `data/mockData.ts` - Fictional preview entries and beneficiaries

The current frontend combines API-backed owner login, entry, and policy surfaces
with in-memory preview data for unfinished features. Tokens and preview state
reset on restart. No real credentials or diary content should be entered.
