// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (read-only preview UI)

import { Link } from 'expo-router'
import { StyleSheet, Text, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { Brand } from '@/components/Brand'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { VisibilityBadge } from '@/components/VisibilityBadge'
import { useAppData } from '@/context/AppDataProvider'
import { colors, minimumTouchTarget, spacing } from '@/constants/theme'

export default function BeneficiaryScreen() {
  const { entries } = useAppData()
  const sharedEntries = entries.filter((entry) => entry.visibility === 'Shared')

  return (
    <AppScreen>
      <View style={styles.header}>
        <Brand />
        <Link
          href="/login"
          accessibilityRole="link"
          accessibilityLabel="Exit beneficiary preview"
          style={styles.exit}
        >
          Exit preview
        </Link>
      </View>
      <Text style={styles.eyebrow}>BENEFICIARY PREVIEW</Text>
      <Text style={styles.title}>A window into a shared story.</Text>
      <Text style={styles.description}>
        This read-only screen shows sample entries labelled Shared.
      </Text>
      <PreviewNotice>
        Demo only: this screen does not grant or verify access. The backend must authorize each request.
      </PreviewNotice>
      {sharedEntries.map((entry) => (
        <Panel key={entry.id}>
          <View style={styles.entryMeta}>
            <VisibilityBadge visibility="Shared" />
            <Text style={styles.date}>{entry.date}</Text>
          </View>
          <Text style={styles.entryTitle}>{entry.title}</Text>
          <Text style={styles.entrySummary}>{entry.summary}</Text>
        </Panel>
      ))}
      {sharedEntries.length === 0 && (
        <Panel><Text style={styles.entrySummary}>No shared sample entries are available.</Text></Panel>
      )}
      <Link
        href="/login"
        accessibilityRole="link"
        accessibilityLabel="Return to sign in"
        style={styles.back}
      >
        Return to sign in
      </Link>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  header: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  exit: {
    minHeight: minimumTouchTarget,
    justifyContent: 'center',
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
  eyebrow: {
    marginTop: spacing.lg,
    color: colors.teal,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  title: {
    color: colors.navy,
    fontSize: 30,
    fontWeight: '700',
    letterSpacing: -0.5,
    lineHeight: 36,
  },
  description: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 20,
  },
  entryMeta: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  date: {
    color: colors.muted,
    fontSize: 10,
  },
  entryTitle: {
    marginTop: 6,
    color: colors.navy,
    fontSize: 16,
    fontWeight: '700',
  },
  entrySummary: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 19,
  },
  back: {
    alignSelf: 'center',
    minHeight: minimumTouchTarget,
    justifyContent: 'center',
    marginVertical: spacing.sm,
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
})
