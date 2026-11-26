// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Scripting (typed API boundary)

export type ApiAccount = {
  account_id: string
  username: string
  owner_id: string
  person_id: string | null
  role: 'owner' | 'beneficiary'
}

export type OwnerRegistrationRequest = {
  username: string
  email: string
  password: string
}

export type BeneficiaryRegistrationRequest = OwnerRegistrationRequest & {
  invitation_code: string
}

export type LoginResponse = {
  access_token: string
  token_type: 'Bearer'
}

export type ApiEntry = {
  entry_id: string
  kind: 'diary' | 'letter'
  created_at: string
  topics: string[]
  disclaimer?: string
}

export type ApiEntryList = {
  entries: ApiEntry[]
}

export type PolicyUpdateResponse = {
  version: number
  status: 'active'
}

export type AskCitation = {
  entry_id: string
  date: string
}

export type AskResponse = {
  answer: string
  citations: AskCitation[]
}

export type OwnerAskResponse = AskResponse & {
  conversation_id: string
  no_record: boolean
  disclaimer?: string
}

export type InvitationResponse = {
  invitation_code: string
  person_id: string
  expires_at: string
}

export class ApiError extends Error {
  status: number
  code: string
  line?: number
  column?: number

  constructor(status: number, code: string, message: string, line?: number, column?: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.code = code
    this.line = line
    this.column = column
  }
}

type ApiOptions = {
  method?: 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'
  body?: unknown
  token?: string
  timeoutMs?: number
}

const API_TIMEOUT_MS = 15_000

function getBaseUrl(): string {
  const value = process.env.EXPO_PUBLIC_API_BASE_URL?.trim()
  if (!value) {
    throw new ApiError(
      0,
      'api_configuration',
      'The app server is not configured. Please try again later.',
    )
  }
  return value.replace(/\/+$/, '')
}

function safeError(status: number, code: string): ApiError {
  if (code === 'ai_service_unavailable') {
    return new ApiError(status, code, 'AI is temporarily unavailable. Please try again.')
  }
  if (code === 'invalid_request') {
    return new ApiError(status, code, 'Please review the information and try again.')
  }
  if (code === 'invalid_beneficiary') {
    return new ApiError(status, code, 'That invitation is invalid or has expired.')
  }
  if (code === 'rate_limited' || status === 429) {
    return new ApiError(status, code, 'Too many attempts. Please try again later.')
  }
  if (code === 'conflict' || status === 409) {
    return new ApiError(status, code, 'The requested resource already exists.')
  }
  if (status === 401) {
    return new ApiError(status, code, 'The username or password is incorrect.')
  }
  if (status === 403) {
    return new ApiError(status, code, 'You are not allowed to perform this action.')
  }
  if (status >= 500) {
    return new ApiError(status, code, 'The server is temporarily unavailable.')
  }
  return new ApiError(status, code, 'The request could not be completed.')
}

export async function apiRequest<T>(path: string, options: ApiOptions = {}): Promise<T> {
  const baseUrl = getBaseUrl()
  const controller = new AbortController()
  const timeout = setTimeout(
    () => controller.abort(),
    options.timeoutMs ?? API_TIMEOUT_MS,
  )

  try {
    const response = await fetch(`${baseUrl}${path}`, {
      method: options.method ?? 'GET',
      headers: {
        Accept: 'application/json',
        ...(options.body !== undefined ? { 'Content-Type': 'application/json' } : {}),
        ...(options.token ? { Authorization: `Bearer ${options.token}` } : {}),
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })

    const text = await response.text()
    let payload: unknown = null
    if (text) {
      try {
        payload = JSON.parse(text)
      } catch {
        payload = null
      }
    }

    if (!response.ok) {
      const code =
        typeof payload === 'object' &&
        payload !== null &&
        'code' in payload &&
        typeof payload.code === 'string'
          ? payload.code
          : 'request_failed'
      const line =
        typeof payload === 'object' &&
        payload !== null &&
        'line' in payload &&
        typeof payload.line === 'number'
          ? payload.line
          : undefined
      const column =
        typeof payload === 'object' &&
        payload !== null &&
        'column' in payload &&
        typeof payload.column === 'number'
          ? payload.column
          : undefined
      const error = safeError(response.status, code)
      error.line = line
      error.column = column
      if (code === 'policy_frozen') {
        throw new ApiError(
          response.status,
          code,
          'This policy is frozen and can no longer be changed.',
          line,
          column,
        )
      }
      if (code === 'policy_syntax_error') {
        throw new ApiError(
          response.status,
          code,
          line && column
            ? `Policy syntax error at line ${line}, column ${column}.`
            : 'The policy text contains a syntax error.',
          line,
          column,
        )
      }
      throw error
    }

    return payload as T
  } catch (error) {
    if (error instanceof ApiError) {
      throw error
    }
    if (error instanceof Error && error.name === 'AbortError') {
      throw new ApiError(0, 'timeout', 'The request timed out. Please try again.')
    }
    throw new ApiError(0, 'network_error', 'Unable to reach the server. Check your connection.')
  } finally {
    clearTimeout(timeout)
  }
}

