import { StyleSheet, Text, View } from 'react-native'
import { colors } from '@/constants/theme'

type PageTitleProps = {
  eyebrow?: string
  title: string
  description?: string
}

export function PageTitle({ eyebrow, title, description }: PageTitleProps) {
  return (
    <View style={styles.container}>
      {eyebrow && <Text style={styles.eyebrow}>{eyebrow.toUpperCase()}</Text>}
      <Text accessibilityRole="header" style={styles.title}>{title}</Text>
      {description && <Text style={styles.description}>{description}</Text>}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    gap: 7,
    paddingVertical: 5,
  },
  eyebrow: {
    color: colors.teal,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.4,
  },
  title: {
    color: colors.navy,
    fontSize: 28,
    fontWeight: '700',
    letterSpacing: -0.5,
  },
  description: {
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
})
