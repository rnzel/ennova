import type { PropsWithChildren } from 'react'
import { StyleSheet, View } from 'react-native'
import { colors, spacing } from '@/constants/theme'

export function Panel({ children }: PropsWithChildren) {
  return <View style={styles.panel}>{children}</View>
}

const styles = StyleSheet.create({
  panel: {
    padding: spacing.md,
    gap: spacing.sm,
    borderRadius: 18,
    borderWidth: 1,
    borderColor: colors.border,
    backgroundColor: colors.surface,
  },
})
