import { useState } from 'react'
import { Link, router } from 'expo-router'
import {
  KeyboardAvoidingView,
  Platform,
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  View,
} from 'react-native'
import { SafeAreaView } from 'react-native-safe-area-context'
import { ActionButton } from '@/components/ActionButton'
import { colors, spacing } from '@/constants/theme'

export default function LoginScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView contentContainerStyle={styles.formScroll} keyboardShouldPersistTaps="handled">
          <View style={styles.formPanel}>
            <Text style={styles.formEyebrow}>OWNER WORKSPACE</Text>
            <Text style={styles.formTitle}>Welcome to ENNOVA</Text>
            <Text style={styles.formDescription}>Continue to the owner workspace preview.</Text>
            <View style={styles.notice}>
              <Text style={styles.noticeText}>
                Prototype only. Sign-in is simulated; do not enter a real password or personal information.
              </Text>
            </View>

            <Text style={styles.label}>Email address</Text>
            <TextInput
              accessibilityLabel="Email address"
              autoCapitalize="none"
              autoComplete="email"
              keyboardType="email-address"
              onChangeText={setEmail}
              placeholder="you@example.test"
              placeholderTextColor="#91A1A7"
              style={styles.input}
              value={email}
            />
            <Text style={styles.label}>Password</Text>
            <TextInput
              accessibilityLabel="Password"
              autoComplete="current-password"
              onChangeText={setPassword}
              placeholder="Enter a sample password"
              placeholderTextColor="#91A1A7"
              secureTextEntry
              style={styles.input}
              value={password}
            />
            <ActionButton
              label="Continue to preview"
              onPress={() => router.replace('/(tabs)')}
              style={styles.action}
            />
            <View style={styles.divider} />
            <Link href="/beneficiary" asChild>
              <Pressable style={styles.secondaryButton}>
                <Text style={styles.secondaryText}>Open beneficiary preview</Text>
                <Text style={styles.secondaryArrow}>↗</Text>
              </Pressable>
            </Link>
            <Text style={styles.footnote}>No data is sent to a server. Preview changes are temporary.</Text>
            <Link href="/" asChild>
              <Pressable style={styles.backLink}>
                <Text style={styles.backText}>Back to intro</Text>
              </Pressable>
            </Link>
          </View>
        </ScrollView>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  safeArea: {
    flex: 1,
    backgroundColor: colors.canvas,
  },
  keyboard: {
    flex: 1,
  },
  formScroll: {
    flexGrow: 1,
  },
  formPanel: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.lg,
    backgroundColor: colors.surface,
  },
  formEyebrow: {
    marginBottom: 8,
    color: colors.teal,
    fontSize: 10,
    fontWeight: '800',
    letterSpacing: 1.3,
  },
  formTitle: {
    color: colors.navy,
    fontSize: 26,
    fontWeight: '700',
  },
  formDescription: {
    marginTop: 6,
    marginBottom: 16,
    color: colors.muted,
    fontSize: 13,
  },
  notice: {
    marginBottom: 16,
    padding: 11,
    borderWidth: 1,
    borderColor: '#D8EEEC',
    borderRadius: 10,
    backgroundColor: '#F0FAF9',
  },
  noticeText: {
    color: '#426C74',
    fontSize: 11,
    lineHeight: 16,
  },
  label: {
    marginBottom: 6,
    color: colors.ink,
    fontSize: 12,
    fontWeight: '700',
  },
  input: {
    minHeight: 46,
    marginBottom: 13,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    color: colors.ink,
    fontSize: 14,
  },
  action: {
    marginTop: 4,
  },
  divider: {
    height: 1,
    marginVertical: 18,
    backgroundColor: colors.border,
  },
  secondaryButton: {
    minHeight: 46,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 12,
    backgroundColor: colors.surface,
  },
  secondaryText: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '700',
  },
  secondaryArrow: {
    color: colors.teal,
  },
  footnote: {
    marginTop: 13,
    color: '#91A1A7',
    fontSize: 10,
    textAlign: 'center',
  },
  backLink: {
    minHeight: 40,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: spacing.sm,
  },
  backText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
})
