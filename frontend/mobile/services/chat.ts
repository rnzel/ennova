import {
  apiRequest,
  type AskCitation,
  type AskResponse,
  type OwnerAskResponse,
} from '@/services/api'

export type ChatRole = 'owner' | 'beneficiary'
export type ChatAnswer = AskResponse & Partial<Pick<OwnerAskResponse, 'conversation_id' | 'no_record' | 'disclaimer'>>

export function askChat(
  role: ChatRole,
  token: string,
  question: string,
  conversationId: string | null,
): Promise<ChatAnswer> {
  const body = {
    question,
    ...(role === 'owner' && conversationId ? { conversation_id: conversationId } : {}),
  }
  return apiRequest<ChatAnswer>(role === 'owner' ? '/owner/ask' : '/ask', {
    method: 'POST',
    token,
    body,
    timeoutMs: 45_000,
  })
}

export function verifiedCitations(value: unknown): AskCitation[] {
  return Array.isArray(value)
    ? value.filter(
        (citation): citation is AskCitation =>
          typeof citation?.entry_id === 'string' && typeof citation?.date === 'string',
      )
    : []
}
