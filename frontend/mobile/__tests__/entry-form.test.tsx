// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface tests)

import { useState } from 'react'
import { act, fireEvent, render, waitFor } from '@testing-library/react-native'
import { Pressable, Text } from 'react-native'
import { router } from 'expo-router'
import NewEntryScreen from '@/app/entries/new'
import { AppDataProvider } from '@/context/AppDataProvider'
import { AuthProvider, useAuth } from '@/context/AuthProvider'
import { PolicyPublishManager } from '@/components/PolicyPublishManager'

jest.mock('expo-router', () => ({
  router: {
    back: jest.fn(),
    replace: jest.fn(),
  },
}))

let authContext: ReturnType<typeof useAuth> | null = null

function AuthCapture() {
  authContext = useAuth()
  return null
}

function TestApp() {
  const [showEntry, setShowEntry] = useState(true)
  return (
    <>
      {showEntry ? <NewEntryScreen /> : <Text>Another screen</Text>}
      <Pressable
        accessibilityRole="button"
        onPress={() => setShowEntry(false)}
      >
        <Text>Navigate away</Text>
      </Pressable>
    </>
  )
}

type MockRequest = {
  path: string
  method: string
  body?: unknown
}

function mockBackend({
  entryStatus = 201,
  policyStatus = 201,
  policyCode = '',
}: {
  entryStatus?: number
  policyStatus?: number
  policyCode?: string
} = {}) {
  const requests: MockRequest[] = []
  globalThis.fetch = jest.fn().mockImplementation(async (url: string, options?: RequestInit) => {
    const path = new URL(url).pathname
    const method = options?.method ?? 'GET'
    const body = typeof options?.body === 'string' ? JSON.parse(options.body) : undefined
    requests.push({ path, method, body })

    let status = 200
    let payload: unknown = {}
    if (path === '/auth/login') {
      payload = { access_token: 'fictional-token', token_type: 'Bearer' }
    } else if (path === '/entries' && method === 'GET') {
      payload = { entries: [] }
    } else if (path === '/entries' && method === 'POST') {
      status = entryStatus
      payload = status === 201
        ? {
            entry_id: 'fictional-wishes',
            kind: 'letter',
            created_at: '2040-01-01T00:00:00Z',
            topics: [],
            disclaimer: 'Fictional server disclaimer.',
          }
        : { code: 'conflict' }
    } else if (path === '/policy' && method === 'PUT') {
      status = policyStatus
      payload = status === 201
        ? { version: 1, status: 'active' }
        : { code: policyCode || 'policy_syntax_error', line: 1, column: 1 }
    }

    return {
      ok: status >= 200 && status < 300,
      status,
      text: async () => JSON.stringify(payload),
    } as Response
  })
  return requests
}

async function authenticate() {
  await act(async () => {
    if (!authContext) throw new Error('Auth context was not captured')
    await authContext.login('fictional-owner', 'fictional-password')
  })
}

async function renderEntryScreen() {
  return await render(
    <AuthProvider>
      <AppDataProvider>
        <AuthCapture />
        <TestApp />
        <PolicyPublishManager />
      </AppDataProvider>
    </AuthProvider>,
  )
}

describe('NewEntryScreen', () => {
  beforeEach(() => {
    jest.clearAllMocks()
    authContext = null
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
  })

  it('requires a recipient and release date for a Letter of Wishes', async () => {
    const view = await render(
      <AuthProvider>
        <AppDataProvider>
          <NewEntryScreen />
        </AppDataProvider>
      </AuthProvider>,
    )

    expect(view.getByText(/not a legal will/i)).toBeTruthy()
    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional test content')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(view.getByText('Letters require a recipient and release date.')).toBeTruthy()
    expect(router.replace).not.toHaveBeenCalled()

    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'sample_person')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-05-01')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(router.replace).toHaveBeenCalledWith('/(tabs)/journal')
  })

  it('validates person IDs and real dates before saving a letter', async () => {
    const requests = mockBackend()
    const view = await renderEntryScreen()
    await authenticate()

    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional letter body')
    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'Release')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-02-30')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(view.getByText('Use a valid lowercase person ID from the invitation.')).toBeTruthy()
    expect(
      requests.some((request) => request.path === '/entries' && request.method === 'POST'),
    ).toBe(false)

    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'sample_person')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    expect(view.getByText('Enter a real release date in YYYY-MM-DD format.')).toBeTruthy()
    expect(
      requests.some((request) => request.path === '/entries' && request.method === 'POST'),
    ).toBe(false)
  })

  it('posts the letter once, confirms the whole policy, and retries with only PUT', async () => {
    const requests = mockBackend()
    const view = await renderEntryScreen()
    await authenticate()

    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional letter body')
    await fireEvent.changeText(view.getByLabelText('Letter recipient'), ' sample_person ')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-05-01')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    await waitFor(() => {
      expect(view.getByText('Confirm policy replacement')).toBeTruthy()
    })
    expect(view.getByText(/This replaces the whole active policy/)).toBeTruthy()
    expect(view.queryByText(/protocol family:/)).toBeNull()
    expect(view.getByText(/release letter "Fictional wishes" to sample_person when date >= 2040-05-01/)).toBeTruthy()
    expect(requests.filter((request) => request.path === '/entries' && request.method === 'POST')).toHaveLength(1)
    expect(requests.some((request) => request.path === '/policy')).toBe(false)

    await fireEvent.press(view.getByRole('button', { name: 'Cancel policy replacement' }))
    expect(view.getByText('Letter saved, but the release date was not set.')).toBeTruthy()
    await fireEvent.press(view.getByRole('button', { name: 'Navigate away' }))
    expect(view.getByText('Another screen')).toBeTruthy()
    expect(view.getByText('Letter saved, but the release date was not set.')).toBeTruthy()
    await fireEvent.press(
      view.getByRole('button', { name: 'Retry setting the letter release date' }),
    )
    await waitFor(() => {
      expect(view.getByText('Confirm policy replacement')).toBeTruthy()
    })
    await fireEvent.press(
      view.getByRole('button', { name: 'Confirm and replace complete policy' }),
    )

    await waitFor(() => {
      expect(view.queryByText('Letter saved, but the release date was not set.')).toBeNull()
    })
    expect(requests.filter((request) => request.path === '/entries' && request.method === 'POST')).toHaveLength(1)
    expect(requests.filter((request) => request.path === '/policy' && request.method === 'PUT')).toHaveLength(1)
    expect(requests.find((request) => request.path === '/policy')?.body).toMatchObject({
      source: expect.stringContaining('release letter "Fictional wishes" to sample_person'),
    })
  })

  it('shows a letter-specific duplicate-title message without publishing policy', async () => {
    const requests = mockBackend({ entryStatus: 409 })
    const view = await renderEntryScreen()
    await authenticate()

    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional letter body')
    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'sample_person')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-05-01')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))

    await waitFor(() => {
      expect(view.getByText('A letter with this title already exists.')).toBeTruthy()
    })
    expect(requests.some((request) => request.path === '/policy')).toBe(false)
  })

  it.each([
    ['policy_frozen', 'This policy is frozen and can no longer be changed.'],
    ['policy_syntax_error', 'Policy syntax error at line 1, column 1.'],
  ])('keeps the release pending and reports %s distinctly', async (code, message) => {
    const requests = mockBackend({ policyStatus: 400, policyCode: code })
    const view = await renderEntryScreen()
    await authenticate()

    await fireEvent.press(view.getByRole('button', { name: 'Letter of Wishes' }))
    await fireEvent.changeText(view.getByLabelText('Entry title'), 'Fictional wishes')
    await fireEvent.changeText(view.getByLabelText('Entry content'), 'Fictional letter body')
    await fireEvent.changeText(view.getByLabelText('Letter recipient'), 'sample_person')
    await fireEvent.changeText(view.getByLabelText('Letter release date'), '2040-05-01')
    await fireEvent.press(view.getByRole('button', { name: 'Save entry' }))
    await waitFor(() => {
      expect(view.getByText('Confirm policy replacement')).toBeTruthy()
    })
    await fireEvent.press(
      view.getByRole('button', { name: 'Confirm and replace complete policy' }),
    )

    await waitFor(() => {
      expect(view.getAllByText(message).length).toBeGreaterThan(0)
    })
    expect(requests.filter((request) => request.path === '/entries' && request.method === 'POST')).toHaveLength(1)
    expect(requests.filter((request) => request.path === '/policy' && request.method === 'PUT')).toHaveLength(1)
  })
})
