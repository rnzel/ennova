// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (API boundary tests)

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

  it('maps invalid registration requests without exposing backend details', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({
        code: 'invalid_request',
        message: 'Rejected person@example.com with password secret-value',
      }),
    })

    await expect(apiRequest('/auth/register-owner', { method: 'POST', body: {} }))
      .rejects.toMatchObject({
        status: 400,
        code: 'invalid_request',
        message: 'Please review the information and try again.',
      })
  })

  it('maps conflicts to a generic safe message', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 409,
      text: async () => JSON.stringify({
        code: 'conflict',
        message: 'That email person@example.com is already registered.',
      }),
    })

    await expect(apiRequest('/auth/register-owner', { method: 'POST', body: {} }))
      .rejects.toMatchObject({
        status: 409,
        code: 'conflict',
        message: 'The requested resource already exists.',
      })
  })

  it('maps rate limits to a safe retry message', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 429,
      text: async () => JSON.stringify({
        code: 'rate_limited',
        message: 'Private backend rate-limit detail',
      }),
    })

    await expect(apiRequest('/auth/register-owner', { method: 'POST', body: {} }))
      .rejects.toMatchObject({
        status: 429,
        code: 'rate_limited',
        message: 'Too many attempts. Please try again later.',
      })
  })

  it('uses one generic message for rejected beneficiary invitations', async () => {
    fetchMock.mockResolvedValue({
      ok: false,
      status: 400,
      text: async () => JSON.stringify({
        code: 'invalid_beneficiary',
        message: 'Private invitation rejection reason',
      }),
    })

    await expect(apiRequest('/auth/register-beneficiary', { method: 'POST', body: {} }))
      .rejects.toMatchObject({
        status: 400,
        code: 'invalid_beneficiary',
        message: 'That invitation is invalid or has expired.',
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

  it('maps network failures to a safe connection message', async () => {
    fetchMock.mockRejectedValue(new Error('Private network detail'))

    await expect(apiRequest('/health')).rejects.toMatchObject({
      status: 0,
      code: 'network_error',
      message: 'Unable to reach the server. Check your connection.',
    })
  })

  it('maps an aborted request to a safe timeout message', async () => {
    jest.useFakeTimers()
    fetchMock.mockImplementation(
      (_url: string, options?: RequestInit) =>
        new Promise((_resolve, reject) => {
          options?.signal?.addEventListener('abort', () => {
            reject(Object.assign(new Error('Private timeout detail'), { name: 'AbortError' }))
          })
        }),
    )

    try {
      const request = apiRequest('/health', { timeoutMs: 100 })
      const expectedError = expect(request).rejects.toMatchObject({
        status: 0,
        code: 'timeout',
        message: 'The request timed out. Please try again.',
      })
      await jest.advanceTimersByTimeAsync(100)
      await expectedError
    } finally {
      jest.useRealTimers()
    }
  })
})
