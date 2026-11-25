// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Language design (UI generates policy-language source)

import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { useAuth } from '@/context/AuthProvider'
import { colors, spacing } from '@/constants/theme'
import { isValidReleaseDate, toPolicyPersonId } from '@/services/policySource'

type WritingMode = 'verbatim' | 'light_fix' | 'review'
type SelectorType = 'tagged' | 'mentioning'
type SeeMode = 'none' | 'allow' | 'deny'
type ReadMode = 'none' | 'allow_summary' | 'allow_verbatim' | 'deny_summary' | 'deny_verbatim'

const templateSources = {
  family: `protocol family:
    may see existence of entries tagged "Family"
    may read summary of entries tagged "Family"
default writing mode: light_fix
`,
  letter: `release letter "A letter for another day" to amelia when date >= 2040-05-01
trustee is marcus
`,
  custody: `transfer custody to marcus if trustee unavailable for 90 days
default writing mode: review
`,
}

export default function PolicyScreen() {
  const { accessToken } = useAuth()
  const {
    policy,
    requestPolicyConfirmation,
    policyFrozen,
    isPublishingPolicy,
    policyPublishOutcome,
    clearPolicyPublishOutcome,
  } = useAppData()
  const [previousPolicy, setPreviousPolicy] = useState(policy)
  const [draft, setDraft] = useState(policy)
  const [generationError, setGenerationError] = useState('')
  const [templateName, setTemplateName] = useState<'family' | 'letter' | 'custody'>('family')
  const [protocol, setProtocol] = useState('family')
  const [tag, setTag] = useState('Family')
  const [person, setPerson] = useState('amelia')
  const [letterTitle, setLetterTitle] = useState('A letter for another day')
  const [releaseDate, setReleaseDate] = useState('2040-05-01')
  const [writingMode, setWritingMode] = useState<WritingMode>('light_fix')
  const [selectorType, setSelectorType] = useState<SelectorType>('tagged')
  const [mentionedName, setMentionedName] = useState('amelia')
  const [seeMode, setSeeMode] = useState<SeeMode>('allow')
  const [readMode, setReadMode] = useState<ReadMode>('allow_summary')
  const [releaseEnabled, setReleaseEnabled] = useState(true)
  const [custodyEnabled, setCustodyEnabled] = useState(false)
  const [custodyPerson, setCustodyPerson] = useState('marcus')
  const [trusteeEnabled, setTrusteeEnabled] = useState(false)
  const [trusteePerson, setTrusteePerson] = useState('marcus')
  const [unavailableDays, setUnavailableDays] = useState('90')

  if (policy !== previousPolicy) {
    setPreviousPolicy(policy)
    setDraft(policy)
  }

  const applyTemplate = (name: 'family' | 'letter' | 'custody') => {
    if (policyFrozen) return
    setTemplateName(name)
    setDraft(templateSources[name])
    setGenerationError('')
    clearPolicyPublishOutcome()
  }

  const generateDraft = () => {
    if (policyFrozen) return
    if (releaseEnabled && !isValidReleaseDate(releaseDate)) {
      setGenerationError('Enter a real calendar date in YYYY-MM-DD format.')
      return
    }
    setGenerationError('')
    const safeProtocol = toPolicyPersonId(protocol, 'family')
    const safePerson = toPolicyPersonId(person, 'amelia')
    const safeMention = toPolicyPersonId(mentionedName, 'amelia')
    const safeCustodyPerson = toPolicyPersonId(custodyPerson, 'marcus')
    const safeTrusteePerson = toPolicyPersonId(trusteePerson, 'marcus')
    const jsonTag = JSON.stringify(tag.trim() || 'Family')
    const jsonTitle = JSON.stringify(letterTitle.trim() || 'A letter for another day')
    const days = /^\d+$/.test(unavailableDays) ? unavailableDays : '90'
    const selector =
      selectorType === 'tagged'
        ? `entries tagged ${jsonTag}`
        : `entries mentioning ${safeMention}`
    const lines = [`protocol ${safeProtocol}:`]
    if (seeMode === 'allow') lines.push(`    may see existence of ${selector}`)
    if (seeMode === 'deny') lines.push(`    may not see existence of ${selector}`)
    if (readMode === 'allow_summary') lines.push(`    may read summary of ${selector}`)
    if (readMode === 'allow_verbatim') lines.push(`    may read verbatim of ${selector}`)
    if (readMode === 'deny_summary') lines.push(`    may not read summary of ${selector}`)
    if (readMode === 'deny_verbatim') lines.push(`    may not read verbatim of ${selector}`)
    if (releaseEnabled) {
      lines.push(`release letter ${jsonTitle} to ${safePerson} when date >= ${releaseDate}`)
    }
    if (custodyEnabled) {
      lines.push(`transfer custody to ${safeCustodyPerson} if trustee unavailable for ${days} days`)
    }
    if (trusteeEnabled) lines.push(`trustee is ${safeTrusteePerson}`)
    lines.push(`default writing mode: ${writingMode}`)
    const source = `${lines.join('\n')}\n`
    setDraft(source)
    clearPolicyPublishOutcome()
  }

  const saveDraft = () => {
    if (policyFrozen || isPublishingPolicy || !draft.trim()) return
    requestPolicyConfirmation(draft, 'policy')
  }

  const outcomeMessage = policyPublishOutcome?.source === draft
    ? policyPublishOutcome.mode === 'preview'
      ? 'Preview saved locally only. Sign in to send this policy to the backend.'
      : 'Policy submitted successfully.'
    : ''

  return (
    <AppScreen>
      <PageTitle
        eyebrow="ACCESS CONTROL"
        title="Your access policy"
        description={
          accessToken
            ? 'Build a complete policy source in ENNOVA policy language.'
            : 'Preview a sample policy written in ENNOVA policy language.'
        }
      />
      <PreviewNotice>
        {accessToken
          ? 'No active policy source is loaded because the app cannot read it. Publishing replaces the whole policy. Policy text is sent to the backend parser; the frontend does not create Prolog facts.'
          : 'This sample policy is preview-only. Policy text is sent to the backend parser when an owner publishes; the frontend does not create Prolog facts.'}
      </PreviewNotice>
      {policyFrozen ? (
        <View style={styles.frozenNotice} accessibilityRole="alert">
          <Text style={styles.frozenTitle}>This policy is frozen</Text>
          <Text style={styles.frozenText}>Editing is disabled because the backend has frozen the policy.</Text>
        </View>
      ) : null}
      <Panel>
        <Text style={styles.sectionLabel}>POLICY BUILDER</Text>
        <Text style={styles.panelTitle}>Templates</Text>
        <View style={styles.templateRow}>
          {(['family', 'letter', 'custody'] as const).map((name) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Policy template: ${name}`}
              accessibilityState={{ disabled: policyFrozen, selected: templateName === name }}
              disabled={policyFrozen}
              key={name}
              onPress={() => applyTemplate(name)}
              style={[styles.template, templateName === name && styles.templateActive]}
            >
              <Text style={styles.templateText}>{name}</Text>
            </Pressable>
          ))}
        </View>

        <Text style={styles.fieldLabel}>Protocol name</Text>
        <TextInput
          accessibilityLabel="Protocol name"
          autoCapitalize="none"
          editable={!policyFrozen}
          onChangeText={setProtocol}
          placeholder="family"
          style={styles.fieldInput}
          value={protocol}
        />
        <Text style={styles.fieldLabel}>Entry tag</Text>
        <TextInput
          accessibilityLabel="Entry tag"
          editable={!policyFrozen}
          onChangeText={setTag}
          placeholder="Family"
          style={styles.fieldInput}
          value={tag}
        />
        <Text style={styles.fieldLabel}>Selector type</Text>
        <View style={styles.templateRow}>
          {(['tagged', 'mentioning'] as const).map((selector) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Selector type: ${selector}`}
              accessibilityState={{ disabled: policyFrozen, selected: selectorType === selector }}
              disabled={policyFrozen}
              key={selector}
              onPress={() => setSelectorType(selector)}
              style={[styles.template, selectorType === selector && styles.templateActive]}
            >
              <Text style={styles.templateText}>{selector}</Text>
            </Pressable>
          ))}
        </View>
        {selectorType === 'mentioning' ? (
          <>
            <Text style={styles.fieldLabel}>Mentioned identifier</Text>
            <TextInput
              accessibilityLabel="Mentioned identifier"
              autoCapitalize="none"
              editable={!policyFrozen}
              onChangeText={setMentionedName}
              placeholder="amelia"
              style={styles.fieldInput}
              value={mentionedName}
            />
          </>
        ) : null}
        <Text style={styles.fieldLabel}>Existence access</Text>
        <View style={styles.templateRow}>
          {(['none', 'allow', 'deny'] as const).map((mode) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Existence access: ${mode === 'allow' ? 'may see' : mode === 'deny' ? 'may not see' : 'none'}`}
              accessibilityState={{ disabled: policyFrozen, selected: seeMode === mode }}
              disabled={policyFrozen}
              key={mode}
              onPress={() => setSeeMode(mode)}
              style={[styles.template, seeMode === mode && styles.templateActive]}
            >
              <Text style={styles.templateText}>{mode === 'allow' ? 'may see' : mode === 'deny' ? 'may not see' : 'none'}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={styles.fieldLabel}>Read access</Text>
        <View style={styles.templateRow}>
          {([
            ['none', 'none'],
            ['allow_summary', 'may read summary'],
            ['allow_verbatim', 'may read verbatim'],
            ['deny_summary', 'deny summary'],
            ['deny_verbatim', 'deny verbatim'],
          ] as const).map(([mode, label]) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Read access: ${label}`}
              accessibilityState={{ disabled: policyFrozen, selected: readMode === mode }}
              disabled={policyFrozen}
              key={mode}
              onPress={() => setReadMode(mode)}
              style={[styles.template, readMode === mode && styles.templateActive]}
            >
              <Text style={styles.templateText}>{label}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={styles.fieldLabel}>Release letter</Text>
        <View style={styles.templateRow}>
          {([true, false] as const).map((enabled) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${enabled ? 'Include' : 'Exclude'} letter release`}
              accessibilityState={{ disabled: policyFrozen, selected: releaseEnabled === enabled }}
              disabled={policyFrozen}
              key={String(enabled)}
              onPress={() => setReleaseEnabled(enabled)}
              style={[styles.template, releaseEnabled === enabled && styles.templateActive]}
            >
              <Text style={styles.templateText}>{enabled ? 'include' : 'exclude'}</Text>
            </Pressable>
          ))}
        </View>
        <Text style={styles.fieldLabel}>Recipient identifier</Text>
        <TextInput
          accessibilityLabel="Recipient identifier"
          autoCapitalize="none"
          editable={!policyFrozen}
          onChangeText={setPerson}
          placeholder="amelia"
          style={styles.fieldInput}
          value={person}
        />
        <Text style={styles.fieldLabel}>Letter title</Text>
        <TextInput
          accessibilityLabel="Letter title"
          editable={!policyFrozen}
          onChangeText={setLetterTitle}
          style={styles.fieldInput}
          value={letterTitle}
        />
        <Text style={styles.fieldLabel}>Release date</Text>
        <TextInput
          accessibilityLabel="Release date"
          autoCapitalize="none"
          editable={!policyFrozen}
          onChangeText={(value) => {
            setReleaseDate(value)
            setGenerationError('')
          }}
          placeholder="2040-05-01"
          style={styles.fieldInput}
          value={releaseDate}
        />
        {generationError ? (
          <Text accessibilityRole="alert" style={styles.errorText}>
            {generationError}
          </Text>
        ) : null}
        <Text style={styles.fieldLabel}>Custody transfer</Text>
        <View style={styles.templateRow}>
          {([true, false] as const).map((enabled) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${enabled ? 'Include' : 'Exclude'} custody transfer`}
              accessibilityState={{ disabled: policyFrozen, selected: custodyEnabled === enabled }}
              disabled={policyFrozen}
              key={String(enabled)}
              onPress={() => setCustodyEnabled(enabled)}
              style={[styles.template, custodyEnabled === enabled && styles.templateActive]}
            >
              <Text style={styles.templateText}>{enabled ? 'include' : 'exclude'}</Text>
            </Pressable>
          ))}
        </View>
        {custodyEnabled ? (
          <>
            <Text style={styles.fieldLabel}>Custody recipient</Text>
            <TextInput
              accessibilityLabel="Custody recipient"
              autoCapitalize="none"
              editable={!policyFrozen}
              onChangeText={setCustodyPerson}
              placeholder="marcus"
              style={styles.fieldInput}
              value={custodyPerson}
            />
            <Text style={styles.fieldLabel}>Unavailable days</Text>
            <TextInput
              accessibilityLabel="Unavailable days"
              editable={!policyFrozen}
              keyboardType="number-pad"
              onChangeText={setUnavailableDays}
              placeholder="90"
              style={styles.fieldInput}
              value={unavailableDays}
            />
          </>
        ) : null}
        <Text style={styles.fieldLabel}>Optional trustee</Text>
        <View style={styles.templateRow}>
          {([true, false] as const).map((enabled) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`${enabled ? 'Include' : 'Exclude'} optional trustee`}
              accessibilityState={{ disabled: policyFrozen, selected: trusteeEnabled === enabled }}
              disabled={policyFrozen}
              key={String(enabled)}
              onPress={() => setTrusteeEnabled(enabled)}
              style={[styles.template, trusteeEnabled === enabled && styles.templateActive]}
            >
              <Text style={styles.templateText}>{enabled ? 'include' : 'exclude'}</Text>
            </Pressable>
          ))}
        </View>
        {trusteeEnabled ? (
          <>
            <Text style={styles.fieldLabel}>Trustee identifier</Text>
            <TextInput
              accessibilityLabel="Trustee identifier"
              autoCapitalize="none"
              editable={!policyFrozen}
              onChangeText={setTrusteePerson}
              placeholder="marcus"
              style={styles.fieldInput}
              value={trusteePerson}
            />
          </>
        ) : null}
        <Text style={styles.fieldLabel}>Default writing mode</Text>
        <View style={styles.templateRow}>
          {(['verbatim', 'light_fix', 'review'] as const).map((mode) => (
            <Pressable
              accessibilityRole="button"
              accessibilityLabel={`Default writing mode: ${mode}`}
              accessibilityState={{ disabled: policyFrozen, selected: writingMode === mode }}
              disabled={policyFrozen}
              key={mode}
              onPress={() => setWritingMode(mode)}
              style={[styles.template, writingMode === mode && styles.templateActive]}
            >
              <Text style={styles.templateText}>{mode}</Text>
            </Pressable>
          ))}
        </View>
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Generate policy text"
          accessibilityState={{ disabled: policyFrozen }}
          disabled={policyFrozen}
          onPress={generateDraft}
          style={[styles.generateButton, policyFrozen && styles.disabledButton]}
        >
          <Text style={styles.saveText}>Generate policy text</Text>
        </Pressable>
        <Text style={styles.previewTitle}>Plain-language preview</Text>
        <Text style={styles.previewText}>
          {`Protocol ${protocol || 'family'} uses ${seeMode === 'none' ? 'no existence rule' : seeMode === 'allow' ? 'may see' : 'may not see'} and ${readMode === 'none' ? 'no read rule' : readMode.replace('_', ' ')} for ${selectorType === 'tagged' ? `entries tagged ${tag || 'Family'}` : `entries mentioning ${mentionedName || 'amelia'}`}.\n${releaseEnabled ? `Release ${letterTitle || 'A letter for another day'} to ${person || 'amelia'} on or after ${releaseDate}.` : 'No letter release statement.'}\n${custodyEnabled ? `Transfer custody to ${custodyPerson || 'marcus'} after ${unavailableDays || '90'} unavailable trustee days.` : 'No custody transfer statement.'}\n${trusteeEnabled ? `Trustee: ${trusteePerson || 'marcus'}.` : 'No trustee statement.'}\nThe default writing mode is ${writingMode}.`}
        </Text>
      </Panel>
      <Panel>
        <Text style={styles.sectionLabel}>POLICY SOURCE</Text>
        <Text style={styles.panelTitle}>Policy draft</Text>
        {!draft.trim() ? (
          <Text style={styles.previewText}>
            Generate policy text or enter a policy-language source before reviewing a replacement.
          </Text>
        ) : null}
        <TextInput
          accessibilityLabel="Policy source"
          autoCapitalize="none"
          multiline
          onChangeText={(text) => {
            setDraft(text)
            clearPolicyPublishOutcome()
          }}
          editable={!policyFrozen}
          spellCheck={false}
          style={styles.editor}
          textAlignVertical="top"
          value={draft}
        />
        <Pressable
          accessibilityRole="button"
          accessibilityLabel="Review policy replacement"
          accessibilityState={{ disabled: policyFrozen || isPublishingPolicy || !draft.trim() }}
          disabled={policyFrozen || isPublishingPolicy || !draft.trim()}
          style={[styles.saveButton, (policyFrozen || isPublishingPolicy || !draft.trim()) && styles.disabledButton]}
          onPress={saveDraft}
        >
          <Text style={styles.saveText}>Review policy replacement</Text>
        </Pressable>
        {outcomeMessage ? (
          <Text style={styles.savedText} accessibilityRole="status">{outcomeMessage}</Text>
        ) : null}
      </Panel>
      <View style={styles.concepts}>
        <Concept number="01" title="May see" description="Allows someone to know an entry exists." />
        <Concept number="02" title="May read" description="Defines whether a summary or content can be read." />
        <Concept number="03" title="Release letter" description="Sets a recipient and date condition for a letter." />
      </View>
    </AppScreen>
  )
}

function Concept({ number, title, description }: { number: string; title: string; description: string }) {
  return (
    <Panel>
      <Text style={styles.conceptNumber}>{number}</Text>
      <Text style={styles.conceptTitle}>{title}</Text>
      <Text style={styles.conceptDescription}>{description}</Text>
    </Panel>
  )
}

const styles = StyleSheet.create({
  frozenNotice: {
    padding: 12,
    borderWidth: 1,
    borderColor: '#E6B7B7',
    borderRadius: 11,
    backgroundColor: '#FFF5F5',
  },
  frozenTitle: {
    color: '#8A3434',
    fontSize: 13,
    fontWeight: '700',
  },
  frozenText: {
    marginTop: 4,
    color: '#8A3434',
    fontSize: 11,
    lineHeight: 16,
  },
  templateRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  template: {
    minHeight: 44,
    justifyContent: 'center',
    paddingHorizontal: 11,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    backgroundColor: colors.surface,
  },
  templateActive: {
    borderColor: colors.teal,
    backgroundColor: '#E8F7F6',
  },
  templateText: {
    color: colors.navy,
    fontSize: 11,
    fontWeight: '700',
  },
  fieldLabel: {
    marginTop: 10,
    marginBottom: 5,
    color: colors.ink,
    fontSize: 11,
    fontWeight: '700',
  },
  fieldInput: {
    minHeight: 44,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    color: colors.ink,
    backgroundColor: colors.surface,
    fontSize: 13,
  },
  generateButton: {
    alignItems: 'center',
    minHeight: 44,
    justifyContent: 'center',
    marginTop: 12,
    paddingVertical: 12,
    borderRadius: 11,
    backgroundColor: '#D7EFF0',
  },
  previewTitle: {
    marginTop: 12,
    color: colors.navy,
    fontSize: 12,
    fontWeight: '700',
  },
  previewText: {
    marginTop: 5,
    color: colors.muted,
    fontSize: 11,
    lineHeight: 17,
  },
  sectionLabel: {
    color: colors.teal,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.1,
  },
  panelTitle: {
    color: colors.navy,
    fontSize: 17,
    fontWeight: '700',
  },
  editor: {
    minHeight: 230,
    padding: 14,
    borderRadius: 12,
    color: '#D7F0F1',
    backgroundColor: '#092F4A',
    fontFamily: 'monospace',
    fontSize: 12,
    lineHeight: 20,
  },
  saveButton: {
    alignItems: 'center',
    minHeight: 44,
    justifyContent: 'center',
    borderRadius: 11,
    backgroundColor: colors.cyan,
  },
  saveText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  savedText: {
    color: colors.successInk,
    fontSize: 11,
  },
  errorText: {
    marginTop: 8,
    color: '#8A3434',
    fontSize: 11,
    lineHeight: 16,
  },
  disabledButton: {
    opacity: 0.5,
  },
  concepts: {
    gap: spacing.sm,
  },
  conceptNumber: {
    color: colors.teal,
    fontSize: 10,
    fontWeight: '800',
  },
  conceptTitle: {
    marginTop: 4,
    color: colors.navy,
    fontSize: 14,
    fontWeight: '700',
  },
  conceptDescription: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 17,
  },
})
