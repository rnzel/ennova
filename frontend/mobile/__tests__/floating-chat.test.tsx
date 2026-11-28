import { act, fireEvent, render, waitFor } from '@testing-library/react-native'
import { FloatingChatWidget } from '@/components/FloatingChatWidget'
import { AuthProvider, useAuth } from '@/context/AuthProvider'
import { SafeAreaProvider } from 'react-native-safe-area-context'

let authContext: ReturnType<typeof useAuth> | null = null
let responses: Array<{ ok: boolean; status: number; payload: unknown }> = []
let requests: Array<{ path: string; headers: HeadersInit; body?: string }> = []
let sessionRole: 'owner' | 'beneficiary' = 'owner'

function AuthCapture() {
  authContext = useAuth()
  return null
}

function jwtFor(role: 'owner' | 'beneficiary') {
  const claims = role === 'owner' ? 'eyJyb2xlIjoib3duZXIifQ' : 'eyJyb2xlIjoiYmVuZWZpY2lhcnkifQ'
  return `header.${claims}.signature`
}

describe('FloatingChatWidget', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    responses = []
    requests = []
    sessionRole = 'owner'
    globalThis.fetch = jest.fn().mockImplementation(async (url: string, options?: RequestInit) => {
      const path = new URL(url).pathname
      requests.push({
        path,
        headers: options?.headers ?? {},
        body: typeof options?.body === 'string' ? options.body : undefined,
      })
      if (path === '/auth/login') {
        return {
          ok: true,
          status: 200,
          text: async () => JSON.stringify({
            access_token: jwtFor(sessionRole),
            token_type: 'Bearer',
          }),
        } as Response
      }
      const response = responses.shift()
      if (!response) throw new Error('Unexpected mocked request')
      return {
        ok: response.ok,
        status: response.status,
        text: async () => JSON.stringify(response.payload),
      } as Response
    })
  })

  async function mountAs(role: 'owner' | 'beneficiary') {
    sessionRole = role
    const view = await render(
      <AuthProvider>
        <SafeAreaProvider initialMetrics={{
          frame: { x: 0, y: 0, width: 390, height: 844 },
          insets: { top: 0, left: 0, right: 0, bottom: 0 },
        }}>
          <AuthCapture />
          <FloatingChatWidget />
        </SafeAreaProvider>
      </AuthProvider>,
    )
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-user', 'fictional-password')
    })
    return view
  }

  it('opens, minimizes, reopens with the same owner conversation, and sends an authenticated owner request', async () => {
    responses.push({
      ok: true,
      status: 200,
      payload: {
        answer: 'A grounded owner answer.',
        conversation_id: 'a'.repeat(32),
        no_record: false,
        citations: [{ entry_id: 'entry-1', date: '2040-01-01' }],
      },
    }, {
      ok: true,
      status: 200,
      payload: {
        answer: 'A grounded follow-up.',
        conversation_id: 'a'.repeat(32),
        no_record: false,
        citations: [],
      },
    })
    const view = await mountAs('owner')
    await fireEvent.press(view.getByRole('button', { name: 'Open ENNOVA chat' }))
    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'What did I record?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('A grounded owner answer.')).toBeTruthy())
    expect(view.getByText('2040-01-01 · entry-1')).toBeTruthy()
    expect(requests.find((request) => request.path === '/owner/ask')).toMatchObject({
      body: JSON.stringify({ question: 'What did I record?' }),
      headers: expect.objectContaining({ Authorization: `Bearer ${jwtFor('owner')}` }),
    })

    await fireEvent.press(view.getByRole('button', { name: 'Minimize chat' }))
    await fireEvent.press(view.getByRole('button', { name: 'Open ENNOVA chat' }))
    expect(view.getByText('A grounded owner answer.')).toBeTruthy()
    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'And after that?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('A grounded follow-up.')).toBeTruthy())
    expect(requests.filter((request) => request.path === '/owner/ask').map((request) => request.body)).toEqual([
      JSON.stringify({ question: 'What did I record?' }),
      JSON.stringify({ question: 'And after that?', conversation_id: 'a'.repeat(32) }),
    ])
  })

  it('routes a beneficiary through /ask without submitting an identity', async () => {
    responses.push({
      ok: true,
      status: 200,
      payload: { answer: 'Only a permitted answer.', citations: [{ entry_id: 'shared-1', date: '2040-02-03' }] },
    })
    const view = await mountAs('beneficiary')
    await fireEvent.press(view.getByRole('button', { name: 'Open ENNOVA chat' }))
    await fireEvent.changeText(view.getByLabelText('Ask about permitted records'), 'What was shared?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('Only a permitted answer.')).toBeTruthy())
    const request = requests.find((item) => item.path === '/ask')
    expect(request?.body).toBe(JSON.stringify({ question: 'What was shared?' }))
    expect(request?.headers).toEqual(expect.objectContaining({ Authorization: `Bearer ${jwtFor('beneficiary')}` }))
    expect(requests.some((item) => item.path === '/owner/ask')).toBe(false)
  })

  it('shows safe errors, retries, and preserves the backend no-record response', async () => {
    responses.push(
      { ok: false, status: 503, payload: { code: 'ai_service_unavailable' } },
      {
        ok: true,
        status: 200,
        payload: { answer: 'No supporting entry was found.', citations: [], conversation_id: 'b'.repeat(32), no_record: true },
      },
    )
    const view = await mountAs('owner')
    await fireEvent.press(view.getByRole('button', { name: 'Open ENNOVA chat' }))
    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'A question without evidence?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('AI is temporarily unavailable. Please try again.')).toBeTruthy())
    await fireEvent.press(view.getByRole('button', { name: 'Retry question' }))
    await waitFor(() => expect(view.getByText('No supporting entry was found.')).toBeTruthy())
    expect(view.getByText('NO SUPPORTING ENTRY FOUND')).toBeTruthy()
    await fireEvent.press(view.getByRole('button', { name: 'Close chat' }))
    expect(view.getByRole('button', { name: 'Open ENNOVA chat' })).toBeTruthy()
  })

  it('shows a busy state while the backend is answering', async () => {
    let finishRequest: ((response: Response) => void) | undefined
    const view = await mountAs('owner')
    globalThis.fetch = jest.fn().mockImplementation(() => new Promise<Response>((resolve) => {
      finishRequest = resolve
    }))
    await fireEvent.press(view.getByRole('button', { name: 'Open ENNOVA chat' }))
    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'A slow question?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    expect(view.getByText('Checking permitted records…')).toBeTruthy()
    await act(async () => {
      finishRequest?.({
        ok: true,
        status: 200,
        text: async () => JSON.stringify({ answer: 'A delayed answer.', citations: [] }),
      } as Response)
    })
    await waitFor(() => expect(view.getByText('A delayed answer.')).toBeTruthy())
  })
})
