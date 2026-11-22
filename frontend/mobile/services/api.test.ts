import { ApiError, apiRequest } from './api'

const fetchMock = jest.fn()

describe('apiRequest', () => {
  beforeEach(() => {
    process.env.EXPO_PUBLIC_API_BASE_URL = 'http://localhost:5000/'
    fetchMock.mockReset()
    globalThis.fetch = fetchMock
  })

  it('sends JSON and attaches bearer authorization without exposing the token', async () => {
    fetchMock.mockResolvedValue({
      ok: true,
      status: 200,
      text: async () => JSON.stringify({ status: 'ok' }),
    })

    await expect(
      apiRequest<{ status: string }>('/entries', {
        method: 'POST',
        token: 'test-token',
        body: { content: 'fictional test content' },
      }),
    ).resolves.toEqual({ status: 'ok' })

    expect(fetchMock).toHaveBeenCalledWith(
      'http://localhost:5000/entries',
      expect.objectContaining({
        method: 'POST',
        headers: expect.objectContaining({
          Authorization: 'Bearer test-token',
          'Content-Type': 'application/json',
        }),
        body: JSON.stringify({ content: 'fictional test content' }),
      }),
    )
  })

  it('maps rejected credentials to a safe generic message', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 401,
      text: async () => JSON.stringify({
        code: 'authentication_error',
        message: 'Sensitive backend detail',
      }),
    })

    await expect(apiRequest('/auth/login', { method: 'POST', body: {} }))
      .rejects.toMatchObject({
        name: 'ApiError',
        status: 401,
        message: 'The username or password is incorrect.',
      })
  })

  it('preserves syntax coordinates without exposing backend error text', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({
        code: 'policy_syntax_error',
        message: 'Internal parser details',
        line: 3,
        column: 7,
      }),
    })

    await expect(apiRequest('/policy', { method: 'PUT', body: { source: 'bad' } }))
      .rejects.toMatchObject({
        status: 400,
        line: 3,
        column: 7,
        message: 'Policy syntax error at line 3, column 7.',
      })
  })

  it('returns a safe AI-unavailable message', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 500,
      text: async () => JSON.stringify({ code: 'ai_service_unavailable' }),
    })

    await expect(apiRequest('/ask', { method: 'POST', body: { question: 'test' } }))
      .rejects.toMatchObject({
        message: 'AI is temporarily unavailable. Please try again.',
      })
  })

  it('uses the safe configuration error when the API URL is missing', async () => {
    delete process.env.EXPO_PUBLIC_API_BASE_URL

    await expect(apiRequest('/health')).rejects.toBeInstanceOf(ApiError)
  })
})
