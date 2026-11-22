import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { colors, spacing } from '@/constants/theme'
import { useAuth } from '@/context/AuthProvider'
import { apiRequest, ApiError, type AskResponse } from '@/services/api'

export default function AssistantScreen() {
  const { accessToken, clearRejectedSession } = useAuth()
  const [question, setQuestion] = useState('')
  const [answer, setAnswer] = useState('')
  const [citations, setCitations] = useState<AskResponse['citations']>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [lastQuestion, setLastQuestion] = useState('')

  const ask = async (retryQuestion?: string) => {
    const submittedQuestion = (retryQuestion ?? question).trim()
    if (!submittedQuestion) return
    setError('')
    setAnswer('')
    setCitations([])
    setLastQuestion(submittedQuestion)

    if (!accessToken) {
      setError('Sign in first so ENNOVA can authorize your question.')
      return
    }

    setIsLoading(true)
    try {
      const response = await apiRequest<AskResponse>('/ask', {
        method: 'POST',
        token: accessToken,
        body: { question: submittedQuestion },
        timeoutMs: 45_000,
      })
      setAnswer(response.answer)
      setCitations(
        Array.isArray(response.citations)
          ? response.citations.filter(
              (citation) =>
                typeof citation.entry_id === 'string' &&
                typeof citation.date === 'string',
            )
          : [],
      )
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

  return (
    <AppScreen>
      <PageTitle
        eyebrow="GROUNDED Q&A"
        title="Ask about your memories."
        description="A future ENNOVA assistant will answer from material you are authorized to access."
      />
      <PreviewNotice>
        Answers are searched and authorized by the backend. Only authorized answers and verified citations are shown.
      </PreviewNotice>
      <Panel>
        <View style={styles.orb}><Text style={styles.orbText}>E</Text></View>
        <Text style={styles.title}>A thoughtful answer starts with permission.</Text>
        <Text style={styles.description}>
          The real service will check access before searching. Your question remains on this screen.
        </Text>
        <TextInput
          accessibilityLabel="Ask a question"
          multiline
          onChangeText={(text) => {
            setQuestion(text)
            setAnswer('')
            setCitations([])
            setError('')
          }}
          placeholder="What would you like to ask?"
          style={styles.input}
          textAlignVertical="top"
          value={question}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel={isLoading ? 'Checking permissions' : 'Ask ENNOVA'}
          accessibilityState={{ disabled: !question.trim() || isLoading }}
          disabled={!question.trim() || isLoading}
          onPress={() => void ask()}
          style={[styles.button, (!question.trim() || isLoading) && styles.disabled]}
        >
          <Text style={styles.buttonText}>{isLoading ? 'Checking permissions…' : 'Ask ENNOVA  →'}</Text>
        </Pressable>
        {answer ? (
          <View style={styles.response}>
            <Text style={styles.responseTitle}>Answer</Text>
            <Text style={styles.responseText}>{answer}</Text>
            {citations.length > 0 ? (
              <View style={styles.citations}>
                <Text style={styles.citationsTitle}>Verified citations</Text>
                {citations.map((citation) => (
                  <Text key={`${citation.entry_id}-${citation.date}`} style={styles.citation}>
                    {citation.entry_id} · {citation.date}
                  </Text>
                ))}
              </View>
            ) : null}
          </View>
        ) : null}
        {error ? (
          <View style={styles.errorNotice} accessibilityRole="alert">
            <Text style={styles.errorText}>{error}</Text>
            {lastQuestion ? (
              <Pressable
                accessibilityRole="button"
                onPress={() => void ask(lastQuestion)}
                style={styles.retryButton}
              >
                <Text style={styles.retryText}>Retry</Text>
              </Pressable>
            ) : null}
          </View>
        ) : null}
      </Panel>
      <View style={styles.steps}>
        <Text style={styles.stepsTitle}>Privacy by design</Text>
        <Text style={styles.step}>01  Check permissions before retrieval</Text>
        <Text style={styles.step}>02  Search only permitted material</Text>
        <Text style={styles.step}>03  Ground the reply in verified sources</Text>
      </View>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  orb: {
    width: 48,
    height: 48,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 16,
    backgroundColor: colors.navy,
  },
  orbText: {
    color: colors.cyan,
    fontSize: 20,
    fontWeight: '700',
  },
  title: {
    color: colors.navy,
    fontSize: 19,
    fontWeight: '700',
    lineHeight: 25,
  },
  description: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 19,
  },
  input: {
    minHeight: 105,
    marginTop: spacing.sm,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 11,
    color: colors.ink,
    fontSize: 13,
  },
  button: {
    alignItems: 'center',
    minHeight: 44,
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: colors.cyan,
  },
  disabled: {
    opacity: 0.5,
  },
  buttonText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  response: {
    gap: 5,
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#EFF8F8',
  },
  responseTitle: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  responseText: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 17,
  },
  citations: {
    gap: 5,
    marginTop: 5,
    paddingTop: 9,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  citationsTitle: {
    color: colors.navy,
    fontSize: 11,
    fontWeight: '800',
  },
  citation: {
    color: colors.teal,
    fontSize: 10,
  },
  errorNotice: {
    gap: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: '#E6B7B7',
    borderRadius: 10,
    backgroundColor: '#FFF5F5',
  },
  errorText: {
    color: '#8A3434',
    fontSize: 12,
    lineHeight: 17,
  },
  retryButton: {
    alignSelf: 'flex-start',
    minHeight: 44,
    justifyContent: 'center',
  },
  retryText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '800',
  },
  steps: {
    gap: 12,
    paddingHorizontal: 3,
  },
  stepsTitle: {
    color: colors.navy,
    fontSize: 14,
    fontWeight: '700',
  },
  step: {
    color: colors.muted,
    fontSize: 11,
  },
})
