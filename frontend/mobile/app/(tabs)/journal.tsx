import { useMemo, useState } from 'react'
import { Link } from 'expo-router'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { EntryRow } from '@/components/EntryRow'
import { PageTitle } from '@/components/PageTitle'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'
import type { EntryVisibility } from '@/types'

const filters: Array<'All' | EntryVisibility> = ['All', 'Private', 'Shared', 'Restricted']

export default function JournalScreen() {
  const { entries } = useAppData()
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
      <Link href="/entries/new" asChild>
        <Pressable style={styles.newButton}>
          <Text style={styles.newButtonText}>＋  Write a new entry</Text>
        </Pressable>
      </Link>
      <TextInput
        accessibilityLabel="Search entries"
        onChangeText={setQuery}
        placeholder="Search your journal"
        placeholderTextColor="#91A1A7"
        style={styles.search}
        value={query}
      />
      <View style={styles.filters}>
        {filters.map((item) => (
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ selected: filter === item }}
            key={item}
            onPress={() => setFilter(item)}
            style={[styles.filter, filter === item && styles.filterActive]}
          >
            <Text style={[styles.filterText, filter === item && styles.filterTextActive]}>{item}</Text>
          </Pressable>
        ))}
      </View>
      <View style={styles.list}>
        {filtered.map((entry) => <EntryRow entry={entry} key={entry.id} />)}
        {filtered.length === 0 && (
          <View style={styles.empty}>
            <Text style={styles.emptyTitle}>No entries found</Text>
            <Text style={styles.emptyText}>Try a different search or visibility filter.</Text>
          </View>
        )}
      </View>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
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
    paddingHorizontal: 11,
    paddingVertical: 8,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 999,
    backgroundColor: colors.surface,
  },
  filterActive: {
    borderColor: colors.teal,
    backgroundColor: '#E8F7F6',
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
