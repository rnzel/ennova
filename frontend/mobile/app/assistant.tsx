import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { colors, spacing } from '@/constants/theme'

export default function AssistantScreen() {
  const [question, setQuestion] = useState('')
  const [submitted, setSubmitted] = useState(false)

  return (
    <AppScreen>
      <PageTitle
        eyebrow="GROUNDED Q&A"
        title="Ask about your memories."
        description="A future ENNOVA assistant will answer from material you are authorized to access."
      />
      <PreviewNotice>
        This prototype does not search entries or call an AI model.
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
            setSubmitted(false)
          }}
          placeholder="What would you like to ask?"
          style={styles.input}
          textAlignVertical="top"
          value={question}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ disabled: !question.trim() }}
          disabled={!question.trim()}
          onPress={() => setSubmitted(true)}
          style={[styles.button, !question.trim() && styles.disabled]}
        >
          <Text style={styles.buttonText}>Preview question  →</Text>
        </Pressable>
        {submitted && (
          <View style={styles.response}>
            <Text style={styles.responseTitle}>Preview only</Text>
            <Text style={styles.responseText}>
              Your question was not sent or searched. Connect an authorized backend before enabling answers.
            </Text>
          </View>
        )}
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
    paddingVertical: 13,
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
