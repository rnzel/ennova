import { Link } from 'expo-router'
import { Pressable, StyleSheet, Text, View } from 'react-native'
import { colors } from '@/constants/theme'
import type { DiaryEntry } from '@/types'
import { VisibilityBadge } from './VisibilityBadge'

export function EntryRow({ entry }: { entry: DiaryEntry }) {
  return (
    <Link
      href={{ pathname: '/entries/[id]', params: { id: entry.id } }}
      asChild
    >
      <Pressable
        accessibilityRole="link"
        style={({ pressed }) => [styles.row, pressed && styles.pressed]}
      >
        <View style={styles.copy}>
          <Text style={styles.title} numberOfLines={1}>{entry.title}</Text>
          <Text style={styles.meta}>{entry.date} · {entry.writingMode}</Text>
          <Text style={styles.summary} numberOfLines={2}>{entry.summary}</Text>
          <VisibilityBadge visibility={entry.visibility} />
        </View>
        <Text style={styles.arrow}>›</Text>
      </Pressable>
    </Link>
  )
}

const styles = StyleSheet.create({
  row: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 14,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  copy: {
    flex: 1,
    gap: 6,
  },
  title: {
    color: colors.navy,
    fontSize: 15,
    fontWeight: '700',
  },
  meta: {
    color: colors.muted,
    fontSize: 11,
  },
  summary: {
    marginBottom: 2,
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  arrow: {
    color: colors.teal,
    fontSize: 26,
  },
  pressed: {
    opacity: 0.72,
  },
})
