import { Image, StyleSheet, Text, View } from 'react-native'
import { colors } from '@/constants/theme'

type BrandProps = {
  light?: boolean
  compact?: boolean
}

export function Brand({ light = false, compact = false }: BrandProps) {
  return (
    <View style={styles.container}>
      <Image source={require('../assets/images/ennova-logo.jpg')} style={styles.logo} />
      {!compact && (
        <Text style={[styles.name, light && styles.nameLight]}>ENNOVA</Text>
      )}
    </View>
  )
}

const styles = StyleSheet.create({
  container: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
  },
  logo: {
    width: 42,
    height: 42,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  name: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '800',
    letterSpacing: 2,
  },
  nameLight: {
    color: colors.surface,
  },
})
