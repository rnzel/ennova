import { useEffect, useRef, useState } from 'react'
import {
  ActivityIndicator,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
  type ScrollViewInstance,
} from 'react-native'
import { ApiError } from '@/services/api'
import { askChat, verifiedCitations, type ChatRole } from '@/services/chat'
import { colors, minimumTouchTarget, spacing } from '@/constants/theme'

type ChatMessage = {
  id: string
  role: 'user' | 'assistant'
  text: string
  citations?: ReturnType<typeof verifiedCitations>
  noRecord?: boolean
  disclaimer?: string
}

const OWNER_SUGGESTIONS = [
  'What were my memorable moments?',
  'What goals did I record?',
  'What challenges did I write about?',
]

export function ChatConversation({
  role,
  token,
  clearRejectedSession,
  compact = false,
}: {
  role: ChatRole
  token: string | null
  clearRejectedSession: (error: unknown) => boolean
  compact?: boolean
}) {
  const [question, setQuestion] = useState('')
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [retryQuestion, setRetryQuestion] = useState('')
  const listRef = useRef<ScrollViewInstance | null>(null)
  const nextMessageId = useRef(0)

  useEffect(() => {
    listRef.current?.scrollToEnd({ animated: true })
  }, [messages, isLoading])

  const sendQuestion = async (rawQuestion: string, retry = false) => {
    const submittedQuestion = rawQuestion.trim()
    if (!submittedQuestion || isLoading) return
    setError('')

    if (!token) {
      setError(role === 'owner'
        ? 'Sign in as the diary owner to ask about your records.'
        : 'Sign in to ask about records available to you.')
      return
    }

    if (!retry) {
      setMessages((current) => [...current, {
        id: `message-${++nextMessageId.current}`,
        role: 'user',
        text: submittedQuestion,
      }])
    }
    setQuestion('')
    setRetryQuestion(submittedQuestion)
    setIsLoading(true)
    try {
      const response = await askChat(role, token, submittedQuestion, conversationId)
      if (role === 'owner' && response.conversation_id) {
        setConversationId(response.conversation_id)
      }
      setMessages((current) => [...current, {
        id: `message-${++nextMessageId.current}`,
        role: 'assistant',
        text: response.answer,
        citations: verifiedCitations(response.citations),
        noRecord: response.no_record,
        disclaimer: response.disclaimer,
      }])
      setRetryQuestion('')
    } catch (caught) {
      clearRejectedSession(caught)
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'The answer could not be completed. Please try again.',
      )
    } finally {
      setIsLoading(false)
    }
  }

  const title = role === 'owner' ? 'Your diary assistant' : 'Shared diary assistant'
  const suggestions = role === 'owner' ? OWNER_SUGGESTIONS : []

  return (
    <View style={[styles.conversation, compact && styles.compact]}>
      <View style={styles.heading}>
        <View style={styles.titleBlock}>
          <Text style={styles.eyebrow}>{role === 'owner' ? 'YOUR PRIVATE DIARY' : 'PERMITTED RECORDS'}</Text>
          <Text style={styles.title}>{compact ? title : 'Ask about your memories.'}</Text>
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Start a new conversation"
          accessibilityState={{ disabled: isLoading }}
          disabled={isLoading}
          onPress={() => {
            setMessages([])
            setConversationId(null)
            setQuestion('')
            setError('')
            setRetryQuestion('')
          }}
          style={styles.newConversation}
        >
          <Text style={styles.newConversationText}>New</Text>
        </Pressable>
      </View>

      <ScrollView
        ref={listRef}
        contentContainerStyle={styles.messages}
        keyboardShouldPersistTaps="handled"
        showsVerticalScrollIndicator={false}
      >
        {messages.length === 0 ? (
          <View style={styles.welcome}>
            <View style={styles.orb}><Text style={styles.orbText}>E</Text></View>
            <Text style={styles.welcomeTitle}>
              {role === 'owner'
                ? 'A thoughtful look back, grounded in your diary.'
                : 'Answers use only records made available to you.'}
            </Text>
            <Text style={styles.welcomeBody}>
              {role === 'owner'
                ? 'Explore experiences, memories, and moments you recorded. Answers show their dates.'
                : 'Ask about the diary. The owner’s access rules determine which records can be used.'}
            </Text>
            {suggestions.length ? (
              <View style={styles.suggestions}>
                {suggestions.map((suggestion) => (
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={`Ask: ${suggestion}`}
                    key={suggestion}
                    disabled={isLoading}
                    onPress={() => void sendQuestion(suggestion)}
                    style={styles.suggestion}
                  >
                    <Text style={styles.suggestionText}>{suggestion}</Text>
                  </Pressable>
                ))}
              </View>
            ) : null}
          </View>
        ) : messages.map((message) => (
          <View
            key={message.id}
            style={[styles.messageRow, message.role === 'user' ? styles.userRow : styles.assistantRow]}
          >
            <View
              accessibilityLabel={message.role === 'user' ? 'Your message' : 'Assistant response'}
              style={[styles.bubble, message.role === 'user' ? styles.userBubble : styles.assistantBubble]}
            >
              {message.role === 'assistant' && message.noRecord ? (
                <Text style={styles.noRecordLabel}>NO SUPPORTING ENTRY FOUND</Text>
              ) : null}
              <Text style={message.role === 'user' ? styles.userText : styles.assistantText}>
                {message.text}
              </Text>
              {message.citations?.length ? (
                <View style={styles.citations}>
                  <Text style={styles.citationsTitle}>From the diary</Text>
                  {message.citations.map((citation) => (
                    <Text key={`${message.id}-${citation.entry_id}-${citation.date}`} style={styles.citation}>
                      {citation.date} · {citation.entry_id}
                    </Text>
                  ))}
                </View>
              ) : null}
              {message.disclaimer ? <Text style={styles.disclaimer}>{message.disclaimer}</Text> : null}
            </View>
          </View>
        ))}
        {isLoading ? (
          <View style={[styles.messageRow, styles.assistantRow]}>
            <View style={[styles.bubble, styles.assistantBubble, styles.loadingBubble]}>
              <ActivityIndicator color={colors.teal} size="small" />
              <Text style={styles.assistantText}>Checking permitted records…</Text>
            </View>
          </View>
        ) : null}
        {error ? (
          <View style={styles.errorNotice} accessibilityRole="alert">
            <Text style={styles.errorText}>{error}</Text>
            {retryQuestion ? (
              <Pressable
                accessibilityRole="button"
                accessibilityLabel="Retry question"
                onPress={() => void sendQuestion(retryQuestion, true)}
                style={styles.retryButton}
              >
                <Text style={styles.retryText}>Retry</Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}
      </ScrollView>

      <View style={styles.composer}>
        <TextInput
          accessibilityLabel={role === 'owner' ? 'Ask your diary assistant' : 'Ask about permitted records'}
          editable={!isLoading}
          maxLength={2_000}
          multiline
          onChangeText={setQuestion}
          onSubmitEditing={() => void sendQuestion(question)}
          placeholder="Ask about a memory…"
          placeholderTextColor={colors.muted}
          returnKeyType="send"
          style={styles.input}
          textAlignVertical="center"
          value={question}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={isLoading ? 'Sending question' : 'Send question'}
          accessibilityState={{ disabled: !question.trim() || isLoading, busy: isLoading }}
          disabled={!question.trim() || isLoading}
          onPress={() => void sendQuestion(question)}
          style={[styles.sendButton, (!question.trim() || isLoading) && styles.disabled]}
        >
          <Text style={styles.sendText}>{isLoading ? '…' : 'Send'}</Text>
        </Pressable>
      </View>
      <Text style={styles.privacyNote}>
        {role === 'owner'
          ? 'Answers use verified records retrieved for your account.'
          : 'Access is checked by the diary owner’s policy for every question.'}
      </Text>
    </View>
  )
}

const styles = StyleSheet.create({
  conversation: { flex: 1, minHeight: 0, gap: spacing.sm },
  compact: { padding: spacing.md },
  heading: {
    minHeight: minimumTouchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  titleBlock: { flex: 1, gap: 3 },
  eyebrow: { color: colors.teal, fontSize: 10, fontWeight: '800', letterSpacing: 1.1 },
  title: { color: colors.navy, fontSize: 19, fontWeight: '800' },
  newConversation: {
    minWidth: minimumTouchTarget,
    minHeight: minimumTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.sm,
    borderRadius: 12,
    backgroundColor: colors.surface,
    borderWidth: 1,
    borderColor: colors.border,
  },
  newConversationText: { color: colors.teal, fontSize: 12, fontWeight: '800' },
  messages: { flexGrow: 1, gap: spacing.md, paddingVertical: spacing.sm },
  welcome: { flexGrow: 1, justifyContent: 'center', gap: spacing.md, paddingVertical: spacing.md },
  orb: { width: 48, height: 48, alignItems: 'center', justifyContent: 'center', borderRadius: 16, backgroundColor: colors.navy },
  orbText: { color: colors.cyan, fontSize: 20, fontWeight: '700' },
  welcomeTitle: { color: colors.navy, fontSize: 19, fontWeight: '700', lineHeight: 25 },
  welcomeBody: { color: colors.muted, fontSize: 13, lineHeight: 20 },
  suggestions: { gap: spacing.xs, marginTop: spacing.sm },
  suggestion: { minHeight: minimumTouchTarget, justifyContent: 'center', paddingHorizontal: spacing.md, paddingVertical: spacing.xs, borderRadius: 14, backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border },
  suggestionText: { color: colors.teal, fontSize: 12, fontWeight: '700' },
  messageRow: { width: '100%', flexDirection: 'row' },
  userRow: { justifyContent: 'flex-end' },
  assistantRow: { justifyContent: 'flex-start' },
  bubble: { maxWidth: '88%', gap: spacing.xs, padding: spacing.md, borderRadius: 18 },
  userBubble: { backgroundColor: colors.navy, borderBottomRightRadius: 5 },
  assistantBubble: { backgroundColor: colors.surface, borderWidth: 1, borderColor: colors.border, borderBottomLeftRadius: 5 },
  userText: { color: colors.surface, fontSize: 14, lineHeight: 21 },
  assistantText: { color: colors.ink, fontSize: 14, lineHeight: 21 },
  noRecordLabel: { color: colors.teal, fontSize: 9, fontWeight: '800', letterSpacing: 0.8 },
  citations: { gap: 4, marginTop: spacing.xs, paddingTop: spacing.sm, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: colors.border },
  citationsTitle: { color: colors.navy, fontSize: 11, fontWeight: '800' },
  citation: { color: colors.teal, fontSize: 11, lineHeight: 17 },
  disclaimer: { color: colors.muted, fontSize: 10, lineHeight: 15, marginTop: spacing.xs },
  loadingBubble: { flexDirection: 'row', alignItems: 'center', gap: spacing.sm },
  errorNotice: { gap: spacing.xs, padding: spacing.md, borderWidth: 1, borderColor: colors.dangerBorder, borderRadius: 14, backgroundColor: colors.dangerBackground },
  errorText: { color: colors.danger, fontSize: 12, lineHeight: 17 },
  retryButton: { alignSelf: 'flex-start', minHeight: minimumTouchTarget, justifyContent: 'center', paddingHorizontal: spacing.sm },
  retryText: { color: colors.teal, fontSize: 12, fontWeight: '800' },
  composer: { flexDirection: 'row', alignItems: 'flex-end', gap: spacing.xs },
  input: { flex: 1, minHeight: minimumTouchTarget, maxHeight: 120, paddingHorizontal: spacing.md, paddingVertical: spacing.sm, borderWidth: 1, borderColor: colors.border, borderRadius: 16, backgroundColor: colors.surface, color: colors.ink, fontSize: 14, lineHeight: 20 },
  sendButton: { minWidth: 64, minHeight: minimumTouchTarget, alignItems: 'center', justifyContent: 'center', borderRadius: 14, backgroundColor: colors.cyan },
  sendText: { color: colors.navy, fontSize: 13, fontWeight: '800' },
  disabled: { opacity: 0.5 },
  privacyNote: { color: colors.muted, fontSize: 10, textAlign: 'center', paddingBottom: spacing.xs },
})
