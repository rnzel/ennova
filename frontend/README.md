# ENNOVA frontend

The frontend is the Expo + React Native app in `mobile/`.

## Run the mobile app

```powershell
cd mobile
npm install
npm start
```

Open the project with Expo Go by scanning the QR code, or press `a` to launch an
available Android emulator. A native iOS build requires macOS and Xcode; Expo Go
on an iPhone can be used for development previews.

Validate the TypeScript and create a Metro bundle with:

```powershell
npm run typecheck
npx expo export --platform android
```

## Mobile app structure

| Path | Purpose |
|---|---|
| `mobile/app/` | Expo Router screens and navigation |
| `mobile/components/` | Shared native components |
| `mobile/context/` | In-memory preview state |
| `mobile/data/` | Fictional sample content |
| `mobile/constants/theme.ts` | Logo-inspired palette and spacing |
| `mobile/assets/images/ennova-logo.jpg` | ENNOVA logo |

The app opens on an intro screen; **Get started** opens the owner sign-in preview.
The app also includes dashboard, diary list/detail/editor,
beneficiaries, access policy, Q&A, settings, and a beneficiary preview.

## Limitations

The app is a frontend skeleton. Sign-in is simulated; data is held in memory and
resets when the app restarts. There is no backend/API or AI connection, and the
frontend does not enforce authorization. Use fictional data only; never enter
real diary content or credentials.
