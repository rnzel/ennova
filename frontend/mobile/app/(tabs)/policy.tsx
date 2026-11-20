import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'

export default function PolicyScreen() {
  const { policy, setPolicy } = useAppData()
  const [draft, setDraft] = useState(policy)
  const [saved, setSaved] = useState(false)

  const saveDraft = () => {
    setPolicy(draft)
    setSaved(true)
  }

  return (
    <AppScreen>
      <PageTitle
        eyebrow="ACCESS CONTROL"
        title="Your access policy"
        description="Review a sample policy written in ENNOVA's policy language."
      />
      <PreviewNotice>
        Editing this sample does not validate it or change any actual permissions.
      </PreviewNotice>
      <Panel>
        <Text style={styles.sectionLabel}>POLICY SOURCE</Text>
        <Text style={styles.panelTitle}>Policy draft</Text>
        <TextInput
          accessibilityLabel="Policy source"
          autoCapitalize="none"
          multiline
          onChangeText={(text) => {
            setDraft(text)
            setSaved(false)
          }}
          spellCheck={false}
          style={styles.editor}
          textAlignVertical="top"
          value={draft}
        />
        <Pressable style={styles.saveButton} onPress={saveDraft}>
          <Text style={styles.saveText}>Save preview draft</Text>
        </Pressable>
        {saved && <Text style={styles.savedText}>Draft saved in memory for this session only.</Text>}
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
    paddingVertical: 13,
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
