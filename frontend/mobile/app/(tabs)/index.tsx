import { Link } from 'expo-router'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { Brand } from '@/components/Brand'
import { EntryRow } from '@/components/EntryRow'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { PageTitle } from '@/components/PageTitle'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'

export default function HomeScreen() {
  const { entries, beneficiaries } = useAppData()
  const sharedCount = entries.filter((entry) => entry.visibility === 'Shared').length

  return (
    <AppScreen>
      <View style={styles.topBar}>
        <Brand />
        <View style={styles.avatar}><Text style={styles.avatarText}>O</Text></View>
      </View>

      <PageTitle
        eyebrow="OWNER OVERVIEW"
        title="Your story, thoughtfully kept."
        description="A clear view of your journal and the people you have chosen to include."
      />

      <View style={styles.hero}>
        <Text style={styles.heroEyebrow}>YOUR PRIVATE LEGACY VAULT</Text>
        <Text style={styles.heroTitle}>Keep what matters, on your terms.</Text>
        <Text style={styles.heroDescription}>
          Write a memory or review the sharing choices in your sample workspace.
        </Text>
        <Link href="/entries/new" asChild>
          <Pressable accessibilityRole="link" style={styles.heroButton}>
            <Text style={styles.heroButtonText}>＋  New diary entry</Text>
          </Pressable>
        </Link>
      </View>

      <View style={styles.stats}>
        <Stat label="Entries" value={String(entries.length)} detail="In this preview" />
        <Stat label="People" value={String(beneficiaries.length)} detail="All statuses" />
        <Stat label="Shared" value={String(sharedCount)} detail="Sample entries" />
      </View>

      <Panel>
        <View style={styles.sectionHeading}>
          <View>
            <Text style={styles.sectionEyebrow}>YOUR JOURNAL</Text>
            <Text style={styles.sectionTitle}>Recent entries</Text>
          </View>
          <Link href="/(tabs)/journal" accessibilityRole="link" style={styles.link}>View all</Link>
        </View>
        {entries.slice(0, 3).map((entry) => <EntryRow entry={entry} key={entry.id} />)}
      </Panel>

      <Panel>
        <View style={styles.sectionHeading}>
          <View>
            <Text style={styles.sectionEyebrow}>PEOPLE YOU TRUST</Text>
            <Text style={styles.sectionTitle}>Access overview</Text>
          </View>
          <Link href="/(tabs)/people" accessibilityRole="link" style={styles.link}>Manage</Link>
        </View>
        <Text style={styles.panelDescription}>
          {beneficiaries.length} sample beneficiaries across pending, review, and granted states.
        </Text>
      </Panel>

      <PreviewNotice>
        This is a mobile frontend prototype. Visibility labels are examples, not security controls.
      </PreviewNotice>
    </AppScreen>
  )
}

function Stat({ label, value, detail }: { label: string; value: string; detail: string }) {
  return (
    <View style={styles.stat}>
      <Text style={styles.statLabel}>{label}</Text>
      <Text style={styles.statValue}>{value}</Text>
      <Text style={styles.statDetail}>{detail}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    marginBottom: 8,
  },
  avatar: {
    width: 36,
    height: 36,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 18,
    backgroundColor: '#D7EFF0',
  },
  avatarText: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '800',
  },
  hero: {
    gap: 10,
    padding: spacing.lg,
    borderRadius: 20,
    backgroundColor: colors.navy,
  },
  heroEyebrow: {
    color: '#A5E8E2',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.2,
  },
  heroTitle: {
    maxWidth: 340,
    color: colors.surface,
    fontSize: 25,
    fontWeight: '700',
    letterSpacing: -0.5,
    lineHeight: 31,
  },
  heroDescription: {
    color: '#D1E6EA',
    fontSize: 13,
    lineHeight: 19,
  },
  heroButton: {
    alignSelf: 'flex-start',
    minHeight: 44,
    justifyContent: 'center',
    marginTop: 4,
    paddingHorizontal: 15,
    borderRadius: 11,
    backgroundColor: colors.cyan,
  },
  heroButtonText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  stats: {
    flexDirection: 'row',
    gap: 9,
  },
  stat: {
    flex: 1,
    minWidth: 0,
    padding: 12,
    gap: 4,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 14,
    backgroundColor: colors.surface,
  },
  statLabel: {
    color: colors.muted,
    fontSize: 10,
    fontWeight: '700',
  },
  statValue: {
    color: colors.navy,
    fontSize: 23,
    fontWeight: '700',
  },
  statDetail: {
    color: colors.muted,
    fontSize: 9,
  },
  sectionHeading: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
  },
  sectionEyebrow: {
    marginBottom: 4,
    color: colors.teal,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.1,
  },
  sectionTitle: {
    color: colors.navy,
    fontSize: 17,
    fontWeight: '700',
  },
  link: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
  panelDescription: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
})
