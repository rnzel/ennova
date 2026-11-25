// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface tests)

import type { ReactNode } from 'react'
import { act, render, waitFor } from '@testing-library/react-native'
import EntryDetailScreen from '@/app/entries/[id]'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider, useAuth } from '@/context/AuthProvider'

jest.mock('expo-router', () => ({
  Link: ({ children }: { children: ReactNode }) =>
    require('react').createElement(require('react-native').Text, null, children),
  useLocalSearchParams: () => ({ id: 'fictional-letter' }),
}))

let authContext: ReturnType<typeof useAuth> | null = null

function AuthCapture() {
  authContext = useAuth()
  return null
}

describe('EntryDetailScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    globalThis.fetch = jest.fn().mockImplementation(async (url: string) => {
      const path = new URL(url).pathname
      const payload = path === '/auth/login'
        ? { access_token: 'fictional-token', token_type: 'Bearer' }
        : {
            entries: [{
              entry_id: 'fictional-letter',
              kind: 'letter',
              created_at: '2040-01-01T00:00:00Z',
              topics: [],
              disclaimer: 'Fictional backend disclaimer.',
            }],
          }
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify(payload),
      } as Response
    })
  })

  it('displays the server disclaimer on an API letter record', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <AuthCapture />
          <EntryDetailScreen />
        </AppDataProvider>
      </AuthProvider>,
    )

    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await waitFor(() => {
      expect(view.getByText('Fictional backend disclaimer.')).toBeTruthy()
    })
    expect(view.getByText('LETTER OF WISHES')).toBeTruthy()
  })
})
