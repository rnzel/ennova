// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface)

import { Link, useLocalSearchParams } from 'expo-router'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { VisibilityBadge } from '@/components/VisibilityBadge'
import { useAppData } from '@/context/AppDataProvider'
import { colors } from '@/constants/theme'

export default function EntryDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>()
  const { entries } = useAppData()
  const entry = entries.find((item) => item.id === id)

  if (!entry) {
    return (
      <AppScreen>
        <PageTitle title="Entry not found" description="It may have been cleared when the app restarted." />
        <Link href="/(tabs)/journal" asChild>
          <Pressable accessibilityRole="link" style={styles.button}>
            <Text style={styles.buttonText}>Back to journal</Text>
          </Pressable>
        </Link>
      </AppScreen>
    )
  }

  return (
    <AppScreen>
      <Link href="/(tabs)/journal" style={styles.back} accessibilityRole="link">‹  All entries</Link>
      <PageTitle
        eyebrow={entry.kind === 'letter' ? 'LETTER OF WISHES' : 'DIARY ENTRY'}
        title={entry.title}
        description={`${entry.date} · ${entry.writingMode} mode`}
      />
      <Panel>
        <View style={styles.meta}>
          <VisibilityBadge visibility={entry.visibility} />
          <Text style={styles.ownerView}>
            {entry.source === 'api' ? 'Owner view · API record' : 'Owner view · sample'}
          </Text>
        </View>
        {entry.source === 'api' ? (
          <View style={styles.apiNotice}>
            <Text style={styles.apiNoticeTitle}>
              Entry content is unavailable in this view
            </Text>
            <Text style={styles.apiNoticeText}>
              The backend list response provides metadata only. No entry content was requested or stored by the app.
            </Text>
            {entry.topics?.length ? (
              <Text style={styles.apiNoticeText}>Topics: {entry.topics.join(', ')}</Text>
            ) : null}
            {entry.disclaimer ? (
              <Text style={styles.apiNoticeText}>{entry.disclaimer}</Text>
            ) : null}
          </View>
        ) : (
          <Text style={styles.content}>{entry.content}</Text>
        )}
        <View style={styles.footer}>
          <Text style={styles.footerText}>
            {entry.source === 'api' ? 'Append-only API record' : 'Original text'}
          </Text>
          <Text style={styles.footerText}>
            {entry.source === 'api' ? 'No edit or delete' : 'Not persisted'}
          </Text>
        </View>
      </Panel>
      <PreviewNotice>
        The frontend does not enforce access. Real permissions must be checked by the backend.
      </PreviewNotice>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  back: {
    minHeight: 44,
    textAlignVertical: 'center',
    color: colors.teal,
    fontSize: 13,
    fontWeight: '700',
  },
  meta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 10,
  },
  ownerView: {
    color: colors.muted,
    fontSize: 10,
  },
  apiNotice: {
    gap: 7,
    marginVertical: 12,
    padding: 12,
    borderWidth: 1,
    borderColor: '#D8EEEC',
    borderRadius: 11,
    backgroundColor: '#F0FAF9',
  },
  apiNoticeTitle: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '700',
  },
  apiNoticeText: {
    color: '#426C74',
    fontSize: 12,
    lineHeight: 18,
  },
  content: {
    marginVertical: 12,
    color: colors.ink,
    fontSize: 16,
    lineHeight: 27,
  },
  footer: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  footerText: {
    color: colors.muted,
    fontSize: 10,
  },
  button: {
    alignItems: 'center',
    padding: 14,
    borderRadius: 11,
    backgroundColor: colors.cyan,
  },
  buttonText: {
    color: colors.navy,
    fontWeight: '700',
  },
})
