// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Functional (intro UI)

import { router } from 'expo-router'
import { StatusBar } from 'expo-status-bar'
import { ScrollView, StyleSheet, Text, View } from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ActionButton } from '@/components/ActionButton'
import { Brand } from '@/components/Brand'
import { colors, spacing } from '@/constants/theme'

export default function IndexRoute() {
  return (
    <SafeAreaView style={styles.safeArea}>
      <StatusBar style="light" />
      <ScrollView contentContainerStyle={styles.content} showsVerticalScrollIndicator={false}>
        <Brand light />
        <View style={styles.hero}>
          <Text style={styles.eyebrow}>A PRIVATE PLACE FOR YOUR STORY</Text>
          <Text style={styles.headline}>Keep your memories yours.</Text>
          <Text style={styles.description}>
            Write privately, decide what may be shared, and leave clear guidance for the people who
            matter to you.
          </Text>
          <ActionButton
            label="Get started"
            onPress={() => router.push('/login')}
            style={styles.action}
          />
        </View>
        <View style={styles.promise}>
          <Text style={styles.promiseNumber}>01</Text>
          <Text style={styles.promiseText}>Privacy and access rules belong to the owner.</Text>
        </View>
      </ScrollView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.navy,
  },
  content: {
    flexGrow: 1,
    justifyContent: 'space-between',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
  },
  hero: {
    flexGrow: 1,
    justifyContent: 'center',
    gap: 14,
    paddingVertical: spacing.xl,
  },
  eyebrow: {
    color: '#A5E8E2',
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.4,
  },
  headline: {
    maxWidth: 380,
    color: colors.surface,
    fontSize: 38,
    fontWeight: '700',
    letterSpacing: -1,
    lineHeight: 44,
  },
  description: {
    maxWidth: 420,
    color: '#D1E6EA',
    fontSize: 14,
    lineHeight: 21,
  },
  action: {
    alignSelf: 'flex-start',
    minWidth: 150,
    marginTop: 10,
  },
  promise: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingTop: spacing.md,
    borderTopWidth: 1,
    borderTopColor: 'rgba(234, 255, 255, 0.2)',
  },
  promiseNumber: {
    width: 30,
    height: 30,
    overflow: 'hidden',
    borderWidth: 1,
    borderColor: 'rgba(219, 255, 252, 0.35)',
    borderRadius: 9,
    color: '#B9F1EB',
    fontSize: 10,
    lineHeight: 28,
    textAlign: 'center',
  },
  promiseText: {
    flex: 1,
    color: '#C6E5E8',
    fontSize: 11,
  },
})
