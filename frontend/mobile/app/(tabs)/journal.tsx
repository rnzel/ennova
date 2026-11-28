// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (journal UI)

import { useMemo, useState } from 'react'
import { Link } from 'expo-router'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { EntryRow } from '@/components/EntryRow'
import { PageTitle } from '@/components/PageTitle'
import { useAppData } from '@/context/AppDataProvider'
import { useAuth } from '@/context/AuthProvider'
import { colors, spacing } from '@/constants/theme'
import type { EntryVisibility } from '@/types'

const filters: ('All' | EntryVisibility)[] = ['All', 'Private', 'Shared', 'Restricted']

export default function JournalScreen() {
  const { entries, refreshEntries, entriesLoading, entriesError } = useAppData()
  const { accountRole } = useAuth()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<(typeof filters)[number]>('All')
  const filtered = useMemo(
    () => entries.filter((entry) => {
      const matchesVisibility = filter === 'All' || entry.visibility === filter
      const text = `${entry.title} ${entry.summary}`.toLowerCase()
      return matchesVisibility && text.includes(query.toLowerCase())
    }),
    [entries, filter, query],
  )

  return (
    <AppScreen>
      <PageTitle
        eyebrow="YOUR JOURNAL"
        title="Diary entries"
        description="Your private collection of memories, notes, and letters."
      />
      {accountRole === 'beneficiary' ? (
        <View style={styles.status}>
          <Text style={styles.statusText}>
            Shared memories are explored through answers controlled by the owner’s policy.
          </Text>
          <Link href="/assistant" style={styles.retryText}>Open assistant</Link>
        </View>
      ) : <Link href="/entries/new" asChild>
        <Pressable
          accessibilityRole="link"
          accessibilityLabel="Write a new entry"
          style={styles.newButton}
        >
          <Text style={styles.newButtonText}>＋  Write a new entry</Text>
        </Pressable>
      </Link>}
      <TextInput
        accessibilityLabel="Search entries"
        onChangeText={setQuery}
        placeholder="Search your journal"
        placeholderTextColor={colors.muted}
        style={styles.search}
        value={query}
      />
      <View style={styles.filters}>
        {filters.map((item) => (
          <Pressable
            accessibilityRole="button"
            accessibilityLabel={`Filter entries: ${item}`}
            accessibilityState={{ selected: filter === item }}
            key={item}
            onPress={() => setFilter(item)}
            style={[styles.filter, filter === item && styles.filterActive]}
          >
            <Text style={[styles.filterText, filter === item && styles.filterTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>
      {entriesLoading ? (
        <View style={styles.status}><Text style={styles.statusText}>Loading entries…</Text></View>
      ) : null}
      {entriesError ? (
        <View style={styles.status}>
          <Text style={styles.statusText}>{entriesError}</Text>
          <Pressable
            accessibilityRole="button"
            accessibilityLabel="Retry loading entries"
            style={styles.retryButton}
            onPress={() => void refreshEntries()}
          >
            <Text style={styles.retryText}>Retry</Text>
          </Pressable>
        </View>
      ) : null}
      <View style={styles.list}>
        {filtered.map((entry) => <EntryRow entry={entry} key={entry.id} />)}
        {!entriesLoading && !entriesError && filtered.length === 0 && accountRole !== 'beneficiary' && (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>
              {entries.length === 0 ? 'Your journal is empty' : 'No entries found'}
            </Text>
            <Text style={styles.emptyText}>
              {entries.length === 0
                ? 'Write a new entry to add your first memory.'
                : 'Try a different search or visibility filter.'}
            </Text>
          </View>
        )}
      </View>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  status: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 8,
    padding: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 11,
    backgroundColor: colors.surface,
  },
  statusText: {
    flex: 1,
    color: colors.muted,
    fontSize: 12,
  },
  retryText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
  retryButton: {
    minHeight: 44,
    justifyContent: 'center',
  },
  newButton: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 46,
    borderRadius: 12,
    backgroundColor: colors.navy,
  },
  newButtonText: {
    color: colors.surface,
    fontSize: 13,
    fontWeight: '700',
  },
  search: {
    minHeight: 46,
    paddingHorizontal: 13,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 11,
    backgroundColor: colors.surface,
    color: colors.ink,
    fontSize: 13,
  },
  filters: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 7,
  },
  filter: {
    minHeight: 44,
    paddingHorizontal: 11,
    justifyContent: 'center',
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    backgroundColor: colors.surface,
  },
  filterActive: {
    borderColor: colors.teal,
    backgroundColor: colors.cyan,
  },
  filterText: {
    color: colors.muted,
    fontSize: 11,
    fontWeight: '600',
  },
  filterTextActive: {
    color: colors.navy,
  },
  list: {
    paddingHorizontal: spacing.sm,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    backgroundColor: colors.surface,
  },
  empty: {
    alignItems: 'center',
    gap: 6,
    padding: spacing.xl,
  },
  emptyTitle: {
    color: colors.navy,
    fontSize: 15,
    fontWeight: '700',
  },
  emptyText: {
    color: colors.muted,
    fontSize: 12,
    textAlign: 'center',
  },
})
