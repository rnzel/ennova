import { Link } from 'expo-router'
import { SymbolView } from 'expo-symbols'
import { Pressable, StyleSheet, Text, useWindowDimensions, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { useAppData } from '@/context/AppDataProvider'
import { useAuth } from '@/context/AuthProvider'
import { colors, minimumTouchTarget, spacing } from '@/constants/theme'
import type { DiaryEntry } from '@/types'

export default function HomeScreen() {
  const { width, height } = useWindowDimensions()
  const compactLayout = width < 380 || height < 760 || (height > width && width / height < 0.5)
  const { entries, refreshEntries, entriesLoading, entriesError } = useAppData()
  const { accessToken, accountRole, username } = useAuth()
  const apiEntries = entries.filter((entry) => entry.source === 'api')
  const previewEntries = entries.filter((entry) => entry.source !== 'api')
  const visibleEntries = accessToken ? apiEntries : previewEntries
  const dashboardLoading = entriesLoading || (
    Boolean(accessToken) && !entriesError && entries.length > 0 && apiEntries.length === 0
  )

  return (
    <AppScreen backgroundColor={colors.canvas} compact={compactLayout}>
      <View style={styles.dashboardGreeting}>
        <View style={styles.greetingRow}>
          <Text numberOfLines={1} style={styles.greetingText}>Hello, {username ?? 'there'}!</Text>
          <Link href="/settings" asChild>
            <Pressable
              accessibilityRole="link"
              accessibilityLabel="Open profile and settings"
              style={({ pressed }) => [styles.profileButton, pressed && styles.profilePressed]}
            >
              <SymbolView
                name={{ ios: 'person.crop.circle.fill', android: 'account_circle', web: 'account_circle' }}
                tintColor={colors.teal}
                size={25}
              />
            </Pressable>
          </Link>
        </View>
        <Text style={styles.greetingDescription}>
          Welcome to Ennova, your personal memory vault.
        </Text>
      </View>

      <View style={[styles.vaultCard, compactLayout && styles.vaultCardCompact]}>
        <View style={styles.vaultLayout}>
          <View style={styles.vaultDetails}>
            <View style={styles.vaultHeadingRow}>
              <SymbolView
                name={{ ios: 'lock.shield.fill', android: 'verified_user', web: 'verified_user' }}
                tintColor={colors.teal}
                size={22}
              />
              <Text style={styles.vaultLabel}>Memory Vault</Text>
            </View>
            <View style={styles.vaultSummary}>
              <Text style={styles.entryCount}>
                {dashboardLoading || accountRole === 'beneficiary' ? '—' : visibleEntries.length}
              </Text>
              <Text style={styles.entryCountLabel}>entries</Text>
            </View>
          </View>
          {(!accessToken || accountRole === 'owner') ? <Link href="/entries/new" asChild>
            <Pressable
              accessibilityRole="link"
              accessibilityLabel="Write a diary entry"
              style={({ pressed }) => [styles.vaultWriteButton, pressed && styles.vaultWritePressed]}
            >
              <SymbolView
                name={{ ios: 'square.and.pencil', android: 'edit_note', web: 'edit_note' }}
                tintColor={colors.teal}
                size={30}
                alignSelf="center"
              />
              <Text style={styles.vaultWriteText}>Write Diary</Text>
            </Pressable>
          </Link> : null}
        </View>
      </View>

      <View style={[styles.recentCard, compactLayout && styles.recentCardCompact]}>
        <View style={styles.recentHeader}>
          <View style={styles.recentHeadingGroup}>
            <Text style={styles.sectionHeading}>Recent Memories</Text>
          </View>
          <Link
            href="/(tabs)/journal"
            accessibilityRole="link"
            accessibilityLabel="View all recent memories"
            style={styles.viewAllLink}
          >
            View All
          </Link>
        </View>

        {accountRole === 'beneficiary' ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateTitle}>Explore shared memories</Text>
            <Text style={styles.stateDescription}>
              The owner’s policy controls which records can be used in answers.
            </Text>
            <Link href="/assistant" style={styles.retryText}>Open assistant</Link>
          </View>
        ) : dashboardLoading ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateTitle}>Loading your memories</Text>
            <Text style={styles.stateDescription}>Your recent entries will appear here.</Text>
          </View>
        ) : entriesError ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateTitle}>Memories couldn’t be loaded</Text>
            <Text style={styles.stateDescription}>{entriesError}</Text>
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Retry loading memories"
              onPress={() => void refreshEntries()}
              style={styles.retryButton}
            >
              <Text style={styles.retryText}>Try again</Text>
            </Pressable>
          </View>
        ) : visibleEntries.length === 0 ? (
          <View style={styles.stateBox}>
            <Text style={styles.stateTitle}>Your archive is ready</Text>
            <Text style={styles.stateDescription}>Write your first memory to see it here.</Text>
          </View>
        ) : (
          visibleEntries.slice(0, 3).map((entry) => (
            <MemoryRow entry={entry} key={entry.id} />
          ))
        )}
      </View>

    </AppScreen>
  )
}

function MemoryRow({ entry }: { entry: DiaryEntry }) {
  return (
    <Link href={{ pathname: '/entries/[id]', params: { id: entry.id } }} asChild>
      <Pressable
        accessibilityRole="link"
        accessibilityLabel={`${entry.title}, ${entry.date}`}
        style={({ pressed }) => [
          styles.memoryRow,
          pressed && styles.memoryPressed,
        ]}
      >
        <View style={styles.memoryCopy}>
          <View style={styles.memoryTopRule} />
          <Text numberOfLines={1} style={styles.memoryTitle}>{entry.title}</Text>
          <Text numberOfLines={1} style={styles.memoryDate}>{entry.date}</Text>
        </View>
      </Pressable>
    </Link>
  )
}

const styles = StyleSheet.create({
  dashboardGreeting: {
    paddingTop: 2,
    paddingBottom: 4,
  },
  greetingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: spacing.sm,
  },
  greetingText: {
    flex: 1,
    minWidth: 0,
    color: colors.navy,
    fontSize: 25,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  profileButton: {
    width: minimumTouchTarget,
    height: minimumTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: minimumTouchTarget / 2,
    backgroundColor: colors.cyan,
  },
  profilePressed: {
    opacity: 0.75,
  },
  greetingDescription: {
    marginTop: 4,
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  topBar: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
  },
  profileMark: {
    width: 40,
    height: 40,
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 20,
    backgroundColor: colors.cyan,
  },
  welcome: {
    gap: 7,
    marginTop: 4,
  },
  welcomeCompact: {
    gap: 4,
    marginTop: 0,
  },
  welcomeTitle: {
    maxWidth: 360,
    color: colors.navy,
    fontSize: 26,
    fontWeight: '700',
    letterSpacing: -0.6,
    lineHeight: 32,
  },
  welcomeTitleCompact: {
    fontSize: 23,
    lineHeight: 28,
  },
  welcomeDescription: {
    color: colors.muted,
    fontSize: 13,
    lineHeight: 19,
  },
  vaultCard: {
    padding: spacing.md,
    borderWidth: 1,
    borderRadius: 18,
    borderColor: colors.border,
    backgroundColor: colors.surface,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.04,
    shadowRadius: 10,
    elevation: 1,
  },
  vaultCardCompact: {
    padding: 14,
  },
  vaultLayout: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  vaultDetails: {
    flex: 1,
    minWidth: 0,
    justifyContent: 'center',
    gap: 4,
  },
  vaultHeadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
  },
  vaultLabel: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 0.7,
    flexShrink: 1,
  },
  vaultDescription: {
    color: '#68758A',
    fontSize: 12,
  },
  vaultSummary: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 7,
    marginTop: 2,
  },
  entryCount: {
    color: '#17243A',
    fontSize: 36,
    fontWeight: '700',
    letterSpacing: -1,
  },
  vaultWriteButton: {
    width: '39%',
    minWidth: 105,
    minHeight: minimumTouchTarget,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 6,
    paddingHorizontal: 8,
    borderRadius: 14,
    borderWidth: 1,
    borderColor: colors.teal,
    backgroundColor: 'transparent',
  },
  vaultWritePressed: {
    opacity: 0.84,
  },
  vaultWriteText: {
    flexShrink: 1,
    color: colors.teal,
    fontSize: 11,
    fontWeight: '700',
  },
  entryCountLabel: {
    color: colors.muted,
    fontSize: 13,
  },
  sectionHeading: {
    color: colors.navy,
    fontSize: 17,
    fontWeight: '700',
  },
  recentCard: {
    width: '100%',
    alignSelf: 'stretch',
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 17,
    backgroundColor: colors.surface,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.035,
    shadowRadius: 8,
    elevation: 1,
  },
  recentCardCompact: {
    padding: 13,
  },
  recentHeader: {
    width: '100%',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    marginBottom: 20,
  },
  recentHeadingGroup: {
    flex: 1,
    minWidth: 0,
    gap: 4,
    alignItems: 'flex-start',
  },
  viewAllLink: {
    alignItems: 'center',
    justifyContent: 'center',
    paddingHorizontal: spacing.xs,
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
  memoryRow: {
    width: '100%',
    alignSelf: 'stretch',
    minHeight: 62,
    justifyContent: 'center',
    marginTop: 26,
    paddingVertical: 10,
    paddingHorizontal: 12,
    borderWidth: 1.5,
    borderColor: colors.border,
    borderRadius: 14,
    backgroundColor: colors.surface,
  },
  memoryCopy: {
    width: '100%',
    minWidth: 0,
    gap: 5,
  },
  memoryTitle: {
    width: '100%',
    color: colors.navy,
    fontSize: 14,
    fontWeight: '700',
  },
  memoryDate: {
    width: '100%',
    color: colors.muted,
    fontSize: 10,
    paddingBottom: 10,
  },
  memoryTopRule: {
    width: '100%',
    height: StyleSheet.hairlineWidth,
    marginBottom: 2,
    backgroundColor: colors.border,
  },
  memoryPressed: {
    opacity: 0.7,
  },
  stateBox: {
    alignItems: 'center',
    gap: 6,
    paddingVertical: 22,
    paddingHorizontal: spacing.sm,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  stateTitle: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '700',
    textAlign: 'center',
  },
  stateDescription: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 16,
    textAlign: 'center',
  },
  retryButton: {
    minHeight: minimumTouchTarget,
    justifyContent: 'center',
    paddingHorizontal: 12,
  },
  retryText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
})
