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

The app has connected API login/registration, entry, and policy surfaces. JWT
tokens are held in memory and reset on restart. Entry, beneficiary, invitation,
and Q&A surfaces outside those connections remain mock or incomplete. The
frontend does not enforce authorization; use fictional data only.
