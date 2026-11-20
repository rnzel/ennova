import { StyleSheet, Text, View } from 'react-native'
import { colors } from '@/constants/theme'
import type { EntryVisibility } from '@/types'

const badgeColors: Record<EntryVisibility, { background: string; foreground: string }> = {
  Private: { background: colors.private, foreground: colors.privateInk },
  Shared: { background: colors.shared, foreground: colors.sharedInk },
  Restricted: { background: colors.restricted, foreground: colors.restrictedInk },
}

export function VisibilityBadge({ visibility }: { visibility: EntryVisibility }) {
  const palette = badgeColors[visibility]

  return (
    <View style={[styles.badge, { backgroundColor: palette.background }]}>
      <Text style={[styles.label, { color: palette.foreground }]}>{visibility}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  badge: {
    alignSelf: 'flex-start',
    paddingHorizontal: 10,
    paddingVertical: 5,
    borderRadius: 999,
  },
  label: {
    fontSize: 11,
    fontWeight: '700',
  },
})
