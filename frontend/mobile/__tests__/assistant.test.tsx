// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Scripting (owner grounded-Q&A conversation tests)

import { act, fireEvent, render, waitFor } from '@testing-library/react-native'
import AssistantScreen from '@/app/assistant'
import { AuthProvider, useAuth } from '@/context/AuthProvider'

let authContext: ReturnType<typeof useAuth> | null = null
let askResponses: Array<{ ok: boolean; status: number; payload: unknown }> = []
let requests: Array<{ path: string; method: string; body?: string }> = []

jest.setTimeout(15_000)

function AuthCapture() {
  authContext = useAuth()
  return null
}

describe('AssistantScreen', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000'
    authContext = null
    askResponses = []
    requests = []
    globalThis.fetch = jest.fn().mockImplementation(async (url: string, options?: RequestInit) => {
      const path = new URL(url).pathname
      const method = options?.method ?? 'GET'
      const body = typeof options?.body === 'string' ? options.body : undefined
      requests.push({ path, method, body })

      if (path === '/auth/login') {
        return {
          ok: true,
          status: 200,
          text: async () => JSON.stringify({
            access_token: 'fictional-token',
            token_type: 'Bearer',
          }),
        } as Response
      }

      const response = askResponses.shift()
      if (!response) throw new Error('Unexpected mocked request')
      return {
        ok: response.ok,
        status: response.status,
        text: async () => JSON.stringify(response.payload),
      } as Response
    })
  })

  it('requires sign-in before sending a question', async () => {
    const view = await render(
      <AuthProvider>
        <AssistantScreen />
      </AuthProvider>,
    )

    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'A fictional question?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))

    expect(view.getByText('Sign in as the diary owner to ask about your records.')).toBeTruthy()
    expect(requests).toHaveLength(0)
  })

  it('sends a trimmed question and displays only verified citations', async () => {
    askResponses.push({
      ok: true,
      status: 200,
      payload: {
        answer: 'A fictional answer.',
        conversation_id: 'a'.repeat(32),
        no_record: false,
        citations: [
          { entry_id: 'entry-1', date: '2040-01-01' },
          { entry_id: 7, date: '2040-01-02' },
        ],
      },
    })
    const view = await render(
      <AuthProvider>
        <>
          <AuthCapture />
          <AssistantScreen />
        </>
      </AuthProvider>,
    )
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), '  Which fictional entry?  ')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))

    await waitFor(() => expect(view.getByText('A fictional answer.')).toBeTruthy())
    expect(view.getByText('2040-01-01 · entry-1')).toBeTruthy()
    expect(view.queryByText('2040-01-02 · 7')).toBeNull()
    expect(requests.find((request) => request.path === '/owner/ask')).toMatchObject({
      method: 'POST',
      body: JSON.stringify({ question: 'Which fictional entry?' }),
    })
  })

  it('retries a failed question without changing its submitted text', async () => {
    askResponses.push(
      {
        ok: false,
        status: 503,
        payload: { code: 'ai_service_unavailable', message: 'Private service detail' },
      },
      {
        ok: true,
        status: 200,
        payload: {
          answer: 'A fictional retry answer.',
          citations: [],
          conversation_id: 'b'.repeat(32),
          no_record: true,
        },
      },
    )
    const view = await render(
      <AuthProvider>
        <>
          <AuthCapture />
          <AssistantScreen />
        </>
      </AuthProvider>,
    )
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'A retryable question?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => {
      expect(view.getByText('AI is temporarily unavailable. Please try again.')).toBeTruthy()
    })

    await fireEvent.press(view.getByRole('button', { name: 'Retry question' }))
    await waitFor(() => expect(view.getByText('A fictional retry answer.')).toBeTruthy())
    expect(view.getByText('NO SUPPORTING ENTRY FOUND')).toBeTruthy()
    expect(
      requests.filter((request) => request.path === '/owner/ask').map((request) => request.body),
    ).toEqual([
      JSON.stringify({ question: 'A retryable question?' }),
      JSON.stringify({ question: 'A retryable question?' }),
    ])
  })

  it('sends only the server-issued conversation ID for a follow-up', async () => {
    askResponses.push(
      {
        ok: true,
        status: 200,
        payload: {
          answer: 'A first grounded response.',
          citations: [{ entry_id: 'entry-1', date: '2040-01-01' }],
          conversation_id: 'c'.repeat(32),
          no_record: false,
        },
      },
      {
        ok: true,
        status: 200,
        payload: {
          answer: 'A grounded follow-up.',
          citations: [{ entry_id: 'entry-2', date: '2040-01-02' }],
          conversation_id: 'c'.repeat(32),
          no_record: false,
        },
      },
    )
    const view = await render(
      <AuthProvider>
        <>
          <AuthCapture />
          <AssistantScreen />
        </>
      </AuthProvider>,
    )
    await act(async () => {
      if (!authContext) throw new Error('Auth context was not captured')
      await authContext.login('fictional-owner', 'fictional-password')
    })

    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'My university entry?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('A first grounded response.')).toBeTruthy())
    await fireEvent.changeText(view.getByLabelText('Ask your diary assistant'), 'What about year two?')
    await fireEvent.press(view.getByRole('button', { name: 'Send question' }))
    await waitFor(() => expect(view.getByText('A grounded follow-up.')).toBeTruthy())

    expect(
      requests.filter((request) => request.path === '/owner/ask').map((request) => request.body),
    ).toEqual([
      JSON.stringify({ question: 'My university entry?' }),
      JSON.stringify({ question: 'What about year two?', conversation_id: 'c'.repeat(32) }),
    ])
  })
})
