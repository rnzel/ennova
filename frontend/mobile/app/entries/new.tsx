import { useState } from 'react'
import { router } from 'expo-router'
import { KeyboardAvoidingView, Platform, Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'
import type { EntryVisibility, WritingMode } from '@/types'

const visibilities: EntryVisibility[] = ['Private', 'Shared', 'Restricted']
const writingModes: WritingMode[] = ['Verbatim', 'Light fix', 'Review']

export default function NewEntryScreen() {
  const { addEntry } = useAppData()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [visibility, setVisibility] = useState<EntryVisibility>('Private')
  const [writingMode, setWritingMode] = useState<WritingMode>('Verbatim')

  const save = () => {
    const body = content.trim()
    if (!title.trim() || !body) return
    addEntry({
      title: title.trim(),
      content: body,
      summary: body.slice(0, 150),
      visibility,
      writingMode,
    })
    router.replace('/(tabs)/journal')
  }

  return (
    <AppScreen>
      <KeyboardAvoidingView behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
        <PageTitle
          eyebrow="NEW JOURNAL ENTRY"
          title="Capture a moment."
          description="Your original words stay unchanged in the sample app state."
        />
        <PreviewNotice>
          Use fictional text only. Preview entries are held in memory and disappear when the app restarts.
        </PreviewNotice>

        <Text style={styles.label}>Entry title</Text>
        <TextInput
          accessibilityLabel="Entry title"
          onChangeText={setTitle}
          placeholder="Give this memory a name"
          style={styles.input}
          value={title}
        />
        <Text style={styles.label}>Your entry</Text>
        <TextInput
          accessibilityLabel="Entry content"
          multiline
          onChangeText={setContent}
          placeholder="Write freely..."
          style={[styles.input, styles.bodyInput]}
          textAlignVertical="top"
          value={content}
        />
        <Text style={styles.label}>Visibility label</Text>
        <ChoiceRow options={visibilities} selected={visibility} onSelect={setVisibility} />
        <Text style={styles.helpText}>A prototype label only; it does not grant or block access.</Text>
        <Text style={styles.label}>Writing mode</Text>
        <ChoiceRow options={writingModes} selected={writingMode} onSelect={setWritingMode} />
        <Text style={styles.helpText}>Writing mode processing is not connected.</Text>

        <View style={styles.actions}>
          <Pressable style={styles.cancel} onPress={() => router.back()}>
            <Text style={styles.cancelText}>Cancel</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: !title.trim() || !content.trim() }}
            disabled={!title.trim() || !content.trim()}
            style={[styles.save, (!title.trim() || !content.trim()) && styles.saveDisabled]}
            onPress={save}
          >
            <Text style={styles.saveText}>Save preview entry</Text>
          </Pressable>
        </View>
      </KeyboardAvoidingView>
    </AppScreen>
  )
}

function ChoiceRow<T extends string>({
  options,
  selected,
  onSelect,
}: {
  options: T[]
  selected: T
  onSelect: (value: T) => void
}) {
  return (
    <View style={styles.choices}>
      {options.map((option) => (
        <Pressable
          accessibilityRole="button"
          accessibilityState={{ selected: selected === option }}
          key={option}
          onPress={() => onSelect(option)}
          style={[styles.choice, selected === option && styles.choiceSelected]}
        >
          <Text style={[styles.choiceText, selected === option && styles.choiceTextSelected]}>{option}</Text>
        </Pressable>
      ))}
    </View>
  )
}

const styles = StyleSheet.create({
  label: {
    marginTop: spacing.sm,
    marginBottom: 7,
    color: colors.ink,
    fontSize: 12,
    fontWeight: '700',
  },
  input: {
    minHeight: 46,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 11,
    backgroundColor: colors.surface,
    color: colors.ink,
    fontSize: 13,
  },
  bodyInput: {
    minHeight: 180,
    padding: 13,
    paddingTop: 13,
    lineHeight: 20,
  },
  choices: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  choice: {
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    backgroundColor: colors.surface,
  },
  choiceSelected: {
    borderColor: colors.teal,
    backgroundColor: '#E8F7F6',
  },
  choiceText: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '600',
  },
  choiceTextSelected: {
    color: colors.navy,
  },
  helpText: {
    marginTop: 6,
    color: colors.muted,
    fontSize: 10,
    lineHeight: 15,
  },
  actions: {
    flexDirection: 'row',
    gap: 9,
    marginTop: spacing.lg,
    marginBottom: spacing.xl,
  },
  cancel: {
    minHeight: 46,
    flex: 1,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 11,
    backgroundColor: colors.surface,
  },
  cancelText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '700',
  },
  save: {
    minHeight: 46,
    flex: 1.4,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: colors.cyan,
  },
  saveDisabled: {
    opacity: 0.5,
  },
  saveText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
})
