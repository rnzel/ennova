import { StyleSheet, Text, View } from 'react-native'
import { colors } from '@/constants/theme'

export function PreviewNotice({ children }: { children: string }) {
  return (
    <View accessibilityRole="summary" style={styles.notice}>
      <Text style={styles.icon}>i</Text>
      <Text style={styles.message}>{children}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  notice: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: 10,
    padding: 13,
    borderWidth: 1,
    borderColor: '#D5ECEA',
    borderRadius: 13,
    backgroundColor: '#F2FBFA',
  },
  icon: {
    width: 20,
    height: 20,
    overflow: 'hidden',
    borderRadius: 10,
    color: colors.surface,
    backgroundColor: colors.teal,
    textAlign: 'center',
    textAlignVertical: 'center',
    fontSize: 12,
    fontWeight: '800',
  },
  message: {
    flex: 1,
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
})
