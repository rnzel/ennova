// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface)

import { useEffect, useState } from 'react'
import { router } from 'expo-router'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { useAuth } from '@/context/AuthProvider'
import { colors, spacing } from '@/constants/theme'
import { apiRequest, ApiError, type ApiEntry } from '@/services/api'
import {
  buildReleasePolicySource,
  isPastReleaseDate,
  isPolicyPersonId,
  isValidReleaseDate,
} from '@/services/policySource'
import type { EntryVisibility, WritingMode } from '@/types'

const visibilities: EntryVisibility[] = ['Private', 'Shared', 'Restricted']
const writingModes: WritingMode[] = ['Verbatim', 'Light fix', 'Review']

export default function NewEntryScreen() {
  const {
    addEntry,
    refreshEntries,
    policy,
    requestPolicyConfirmation,
    policyFrozen,
    policyPublishOutcome,
    clearPolicyPublishOutcome,
  } = useAppData()
  const { accessToken, clearRejectedSession } = useAuth()
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [visibility, setVisibility] = useState<EntryVisibility>('Private')
  const [writingMode, setWritingMode] = useState<WritingMode>('Verbatim')
  const [entryKind, setEntryKind] = useState<'diary' | 'letter'>('diary')
  const [recipient, setRecipient] = useState('')
  const [releaseDate, setReleaseDate] = useState('')
  const [isSaving, setIsSaving] = useState(false)
  const [letterSaved, setLetterSaved] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    if (
      letterSaved &&
      policyPublishOutcome?.intent === 'letter-release' &&
      policyPublishOutcome.mode === 'backend'
    ) {
      router.replace('/(tabs)/journal')
    }
  }, [letterSaved, policyPublishOutcome])

  const save = async () => {
    const body = content.trim()
    const trimmedTitle = title.trim()
    const trimmedRecipient = recipient.trim()
    if (!trimmedTitle || !body) return
    if (entryKind === 'letter' && (!trimmedRecipient || !releaseDate)) {
      setError('Letters require a recipient and release date.')
      return
    }
    if (entryKind === 'letter' && !isPolicyPersonId(trimmedRecipient)) {
      setError('Use a valid lowercase person ID from the invitation.')
      return
    }
    if (entryKind === 'letter' && !isValidReleaseDate(releaseDate)) {
      setError('Enter a real release date in YYYY-MM-DD format.')
      return
    }
    if (entryKind === 'letter' && policyFrozen) {
      setError('This policy is frozen and can no longer be changed.')
      return
    }
    setError('')
    clearPolicyPublishOutcome()
    if (!accessToken) {
      addEntry({
        title: trimmedTitle,
        content: body,
        summary: body.slice(0, 150),
        visibility,
        writingMode,
        kind: entryKind,
      })
      router.replace('/(tabs)/journal')
      return
    }

    const entryId = trimmedTitle
      .toLowerCase()
      .normalize('NFKD')
      .replace(/[^a-z0-9.-]+/g, '-')
      .replace(/^-+|-+$/g, '')
      .slice(0, 64) || `entry-${Date.now()}`

    setIsSaving(true)
    try {
      await apiRequest<ApiEntry>('/entries', {
        method: 'POST',
        token: accessToken,
        body: {
          entry_id: entryId,
          kind: entryKind,
          content: body,
          ...(entryKind === 'letter'
            ? {
                title: trimmedTitle,
                recipient: trimmedRecipient,
                release_date: releaseDate,
              }
            : {}),
        },
      })
      await refreshEntries()
      if (entryKind === 'letter') {
        setLetterSaved(true)
        const source = buildReleasePolicySource(
          policy,
          trimmedTitle,
          trimmedRecipient,
          releaseDate,
        )
        requestPolicyConfirmation(source, 'letter-release')
      } else {
        router.replace('/(tabs)/journal')
      }
    } catch (caught) {
      clearRejectedSession(caught)
      setError(
        entryKind === 'letter' && caught instanceof ApiError && caught.status === 409
          ? 'A letter with this title already exists.'
          : caught instanceof ApiError
            ? caught.message
            : 'The entry could not be saved.',
      )
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <AppScreen>
        <PageTitle
          eyebrow="NEW JOURNAL ENTRY"
          title="Capture a moment."
          description="Your original words stay unchanged in the sample app state."
        />
        <PreviewNotice>
          Use fictional text only. Preview entries are held in memory and disappear when the app restarts.
        </PreviewNotice>
        <PreviewNotice>
          A Letter of Wishes is not a legal will and does not transfer property or appoint a legal executor.
        </PreviewNotice>
        {!accessToken ? (
          <PreviewNotice>
            This unauthenticated form is a fictional, in-memory preview only. It will not save a letter or release rule to the backend.
          </PreviewNotice>
        ) : null}

        <Text style={styles.label}>Entry kind</Text>
        <ChoiceRow
          options={['Diary', 'Letter of Wishes']}
          selected={entryKind === 'diary' ? 'Diary' : 'Letter of Wishes'}
          onSelect={(choice) => setEntryKind(choice === 'Diary' ? 'diary' : 'letter')}
        />
        {entryKind === 'letter' ? (
          <>
            <Text style={styles.label}>Recipient identifier</Text>
            <TextInput
              accessibilityLabel="Letter recipient"
              autoCapitalize="none"
              onChangeText={setRecipient}
              placeholder="person_id"
              style={styles.input}
              value={recipient}
            />
            <Text style={styles.helpText}>
              Use the person ID from the invitation. Whitespace is trimmed, but case and characters are preserved.
            </Text>
            <Text style={styles.label}>Release date</Text>
            <TextInput
              accessibilityLabel="Letter release date"
              autoCapitalize="none"
              onChangeText={setReleaseDate}
              placeholder="2040-05-01"
              style={styles.input}
              value={releaseDate}
            />
            <Text style={styles.helpText}>
              The entry records this date; release access still depends on the policy.
            </Text>
            {isPastReleaseDate(releaseDate) ? (
              <Text accessibilityRole="alert" style={styles.warningText}>
                This release date is in the past.
              </Text>
            ) : null}
          </>
        ) : null}

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
        {title || content ? (
          <Text style={styles.syntaxHint}>
            Syntax hint: use [[Person Name]] for names and #tag for tags.{' '}
            {`${title} ${content}`.match(/\[\[[^\]]+\]\]|\#[A-Za-z0-9_-]+/g)?.join('  ') ?? ''}
          </Text>
        ) : null}
        {error ? (
          <View style={styles.errorNotice} accessibilityRole="alert">
            <Text style={styles.errorText}>{error}</Text>
          </View>
        ) : null}
        {letterSaved ? (
          <Text style={styles.helpText}>
            The letter is saved. If the release date is not set, use the app-wide retry notice; retry will not post the letter again.
          </Text>
        ) : null}

        <View style={styles.actions}>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Cancel entry"
            style={styles.cancel}
            onPress={() => router.back()}
          >
            <Text style={styles.cancelText}>Cancel</Text>
          </Pressable>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={isSaving ? 'Saving entry' : 'Save entry'}
            accessibilityState={{
              disabled: !title.trim() || !content.trim() || isSaving || letterSaved,
            }}
            disabled={!title.trim() || !content.trim() || isSaving || letterSaved}
            style={[
              styles.save,
              (!title.trim() || !content.trim() || isSaving || letterSaved) && styles.saveDisabled,
            ]}
            onPress={save}
          >
            <Text style={styles.saveText}>{isSaving ? 'Saving…' : 'Save entry'}</Text>
          </Pressable>
        </View>
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
          accessibilityLabel={option}
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
    minHeight: 44,
    minWidth: 44,
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: 11,
    paddingVertical: 9,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    backgroundColor: colors.surface,
  },
  choiceSelected: {
    borderColor: colors.teal,
    backgroundColor: colors.cyan,
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
  warningText: {
    marginTop: 6,
    color: colors.warningInk,
    fontSize: 12,
    lineHeight: 17,
  },
  syntaxHint: {
    marginTop: spacing.sm,
    padding: 10,
    borderRadius: 10,
    backgroundColor: colors.cyan,
    color: '#426C74',
    fontSize: 11,
    lineHeight: 16,
  },
  errorNotice: {
    marginTop: spacing.sm,
    padding: 11,
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
