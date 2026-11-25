// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface tests)

import { act, fireEvent, render, waitFor } from '@testing-library/react-native'
import PolicyScreen from '@/app/(tabs)/policy'
import { PolicyPublishManager } from '@/components/PolicyPublishManager'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider, useAuth } from '@/context/AuthProvider'

let authContext: ReturnType<typeof useAuth> | null = null
let requests: { path: string; method: string }[] = []

function AuthCapture() {
  authContext = useAuth()
  return null
}

describe('PolicyScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    requests = []
    globalThis.fetch = jest.fn().mockImplementation(async (url: string, options?: RequestInit) => {
      const path = new URL(url).pathname
      const method = options?.method ?? 'GET'
      requests.push({ path, method })
      const payload = path === '/auth/login'
        ? { access_token: 'fictional-token', token_type: 'Bearer' }
        : path === '/policy'
          ? { version: 1, status: 'active' }
          : { entries: [] }
      return {
        ok: true,
        status: 200,
        text: async () => JSON.stringify(payload),
      } as Response
    })
  })

  it('generates policy source text for a deny rule', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <>
            <PolicyScreen />
            <PolicyPublishManager />
          </>
        </AppDataProvider>
      </AuthProvider>,
    )

    await fireEvent.press(view.getByRole('button', { name: 'Read access: deny verbatim' }))
    await fireEvent.press(view.getByRole('button', { name: 'Generate policy text' }))

    expect(view.getByLabelText('Policy source').props.value).toContain(
      'may not read verbatim of entries tagged "Family"',
    )
  })

  it('sanitizes template IDs and confirms the full source before local preview save', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <>
            <PolicyScreen />
            <PolicyPublishManager />
          </>
        </AppDataProvider>
      </AuthProvider>,
    )

    await fireEvent.changeText(view.getByLabelText('Recipient identifier'), 'release')
    await fireEvent.press(view.getByRole('button', { name: 'Generate policy text' }))
    expect(view.getByLabelText('Policy source').props.value).toContain('to person_release')

    await fireEvent.press(view.getByRole('button', { name: 'Review policy replacement' }))
    expect(view.getByText(/This source will not be sent to the backend/)).toBeTruthy()
    expect(view.getByText(/protocol family:/)).toBeTruthy()
    expect(view.getByText(/whole active policy/)).toBeTruthy()

    await fireEvent.press(view.getByRole('button', { name: 'Confirm local policy preview' }))
    expect(view.getByText(/Preview saved locally only/)).toBeTruthy()
  })

  it('sends an authenticated policy only after confirming the complete source', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <AuthCapture />
          <PolicyScreen />
          <PolicyPublishManager />
        </AppDataProvider>
      </AuthProvider>,
    )
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.press(view.getByRole('button', { name: 'Review policy replacement' }))
    expect(view.getByText(/This replaces the whole active policy/)).toBeTruthy()
    expect(requests.some((request) => request.path === '/policy' && request.method === 'PUT')).toBe(false)

    await fireEvent.press(
      view.getByRole('button', { name: 'Confirm and replace complete policy' }),
    )
    await waitFor(() => {
      expect(view.getByText('Policy submitted successfully.')).toBeTruthy()
    })
    expect(requests.filter((request) => request.path === '/policy' && request.method === 'PUT')).toHaveLength(1)
  })
})
