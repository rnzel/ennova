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
import { useAuth } from '@/context/AuthProvider'
import { ApiError } from '@/services/api'

export default function LoginScreen() {
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [mode, setMode] = useState<'login' | 'register' | 'beneficiary'>('login')
  const [invitationCode, setInvitationCode] = useState('')
  const [error, setError] = useState('')
  const { login, registerOwner, registerBeneficiary, isLoading } = useAuth()

  const submit = async () => {
    setError('')
    const trimmedEmail = email.trim()
    if (!username.trim() || !password || (mode === 'beneficiary' && !invitationCode.trim())) {
      setError('Enter a username and password.')
      return
    }
    if (
      mode !== 'login' &&
      (!trimmedEmail || trimmedEmail.split('@').length !== 2 || trimmedEmail.length > 254)
    ) {
      setError('Enter an email with exactly one @ and no more than 254 characters.')
      return
    }
    try {
      if (mode === 'register') {
        await registerOwner(username.trim(), trimmedEmail, password)
      } else if (mode === 'beneficiary') {
        await registerBeneficiary(
          invitationCode.trim(),
          username.trim(),
          trimmedEmail,
          password,
        )
      } else {
        await login(username.trim(), password)
      }
      router.replace('/(tabs)')
    } catch (caught) {
      setError(
        caught instanceof ApiError
          ? caught.message
          : 'The request could not be completed.',
      )
    }
  }

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
            <Text style={styles.formDescription}>
              {mode === 'register'
                ? 'Create an owner account on the configured backend.'
                : mode === 'beneficiary'
                  ? 'Register with a single-use beneficiary invitation.'
                  : 'Sign in to the owner workspace.'}
            </Text>
            <View style={styles.notice}>
              <Text style={styles.noticeText}>
                Session-only preview: credentials are sent only to the configured backend.
                JWT storage is temporary and resets when the app restarts.
              </Text>
            </View>

            {error ? (
              <View style={styles.errorNotice} accessibilityRole="alert">
                <Text style={styles.errorText}>{error}</Text>
              </View>
            ) : null}

            {mode === 'beneficiary' ? (
              <>
                <Text style={styles.label}>Invitation code</Text>
                <TextInput
                  accessibilityLabel="Invitation code"
                  autoCapitalize="characters"
                  onChangeText={setInvitationCode}
                  placeholder="Enter invitation code"
                  placeholderTextColor={colors.muted}
                  style={styles.input}
                  value={invitationCode}
                />
              </>
            ) : null}

            {mode !== 'login' ? (
              <>
                <Text style={styles.label}>Email address</Text>
                <TextInput
                  accessibilityLabel="Email address"
                  autoCapitalize="none"
                  autoComplete="email"
                  autoCorrect={false}
                  keyboardType="email-address"
                  onChangeText={setEmail}
                  placeholder="Enter your email address"
                  placeholderTextColor={colors.muted}
                  style={styles.input}
                  textContentType="emailAddress"
                  value={email}
                />
              </>
            ) : null}

            <Text style={styles.label}>Username</Text>
            <TextInput
              accessibilityLabel="Username"
              autoCapitalize="none"
              autoComplete="username"
              onChangeText={setUsername}
              placeholder="Enter your username"
              placeholderTextColor={colors.muted}
              style={styles.input}
              value={username}
            />
            <Text style={styles.label}>Password</Text>
            <TextInput
              accessibilityLabel="Password"
              autoComplete="current-password"
              onChangeText={setPassword}
              placeholder="Enter a sample password"
              placeholderTextColor={colors.muted}
              secureTextEntry
              style={styles.input}
              value={password}
            />
            {mode !== 'login' ? (
              <Text style={styles.registrationHelp}>
                Username: 3-64 characters; lowercase letters, numbers, _, . or -. Password:
                10-128 characters and not the same as the username. Email: valid address up
                to 254 characters.
              </Text>
            ) : null}
            <ActionButton
              disabled={isLoading}
              label={
                isLoading
                  ? 'Please wait…'
                  : mode === 'register'
                    ? 'Create owner account'
                      : mode === 'beneficiary'
                        ? 'Register beneficiary'
                        : 'Sign in'
              }
              onPress={submit}
              style={styles.action}
            />
            <View style={styles.divider} />
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ disabled: isLoading }}
              disabled={isLoading}
              onPress={() => {
                setMode((current) => (current === 'login' ? 'register' : 'login'))
                setError('')
              }}
              style={styles.secondaryButton}
            >
              <Text style={styles.secondaryText}>
                {mode === 'login'
                  ? 'Create a new owner account'
                  : 'I already have an account'}
              </Text>
              <Text style={styles.secondaryArrow}>↗</Text>
            </Pressable>
            <View style={styles.divider} />
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ disabled: isLoading }}
              disabled={isLoading}
              onPress={() => {
                setMode((current) => (current === 'beneficiary' ? 'login' : 'beneficiary'))
                setError('')
              }}
              style={styles.secondaryButton}
            >
              <Text style={styles.secondaryText}>
                {mode === 'beneficiary'
                  ? 'Continue as owner'
                  : 'Register with an invitation code'}
              </Text>
              <Text style={styles.secondaryArrow}>↗</Text>
            </Pressable>
            <View style={styles.divider} />
            <Link href="/beneficiary" asChild>
              <Pressable accessibilityRole="link" style={styles.secondaryButton}>
                <Text style={styles.secondaryText}>Open beneficiary preview</Text>
                <Text style={styles.secondaryArrow}>↗</Text>
              </Pressable>
            </Link>
            <Text style={styles.footnote}>API access is not persistent. Tokens reset on restart.</Text>
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
  errorNotice: {
    marginBottom: 16,
    padding: 11,
    borderWidth: 1,
    borderColor: '#E6B7B7',
    borderRadius: 10,
    backgroundColor: '#FFF5F5',
  },
  errorText: {
    color: '#8A3434',
    fontSize: 12,
    lineHeight: 17,
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
  registrationHelp: {
    marginBottom: spacing.md,
    color: colors.muted,
    fontSize: 11,
    lineHeight: 16,
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
    color: colors.muted,
    fontSize: 10,
    textAlign: 'center',
  },
  backLink: {
    minHeight: 44,
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
