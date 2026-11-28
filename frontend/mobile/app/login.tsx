import { useState } from 'react'
import { router } from 'expo-router'
import { SymbolView } from 'expo-symbols'
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
import { colors, minimumTouchTarget, spacing } from '@/constants/theme'
import { useAuth } from '@/context/AuthProvider'
import { ApiError } from '@/services/api'

export default function LoginScreen() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [passwordVisible, setPasswordVisible] = useState(false)
  const [error, setError] = useState('')
  const { login, registerOwner, isLoading } = useAuth()

  const submit = async () => {
    setError('')
    if (!username.trim() || !password || (mode === 'register' && !email.trim())) {
      setError(mode === 'register'
        ? 'Enter your username, email address, and password to continue.'
        : 'Enter your username and password to continue.')
      return
    }
    if (mode === 'register' && (!email.trim().includes('@') || email.trim().length > 254)) {
      setError('Enter a valid email address.')
      return
    }

    try {
      if (mode === 'register') {
        await registerOwner(username.trim(), email.trim(), password)
      } else {
        await login(username.trim(), password)
      }
      router.replace('/(tabs)')
    } catch (caught) {
      setError(caught instanceof ApiError ? caught.message : 'The request could not be completed.')
    }
  }

  return (
    <SafeAreaView style={styles.safeArea}>
      <KeyboardAvoidingView
        style={styles.keyboard}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
      >
        <ScrollView
          contentContainerStyle={styles.formScroll}
          keyboardShouldPersistTaps="handled"
          showsVerticalScrollIndicator={false}
        >
          <View style={styles.content}>
            <View style={styles.form}>
              <Text accessibilityRole="header" style={styles.title}>
                {mode === 'login' ? 'Welcome Back' : 'Create your account'}
              </Text>
              <Text style={styles.subtitle}>
                {mode === 'login'
                  ? 'Sign in to continue to your personal vault.'
                  : 'Set up your personal vault to begin.'}
              </Text>

              <View style={styles.fields}>
                {mode === 'register' ? (
                  <>
                    <Text style={styles.label}>Email address</Text>
                    <View style={styles.inputWrap}>
                      <SymbolView
                        name={{ ios: 'envelope', android: 'mail', web: 'mail' }}
                        tintColor={colors.muted}
                        size={19}
                      />
                      <TextInput
                        accessibilityLabel="Email address"
                        autoCapitalize="none"
                        autoComplete="email"
                        autoCorrect={false}
                        keyboardType="email-address"
                        onChangeText={setEmail}
                        placeholder="Enter your email address"
                        placeholderTextColor="#8793A4"
                        style={styles.input}
                        textContentType="emailAddress"
                        value={email}
                      />
                    </View>
                  </>
                ) : null}
                <Text style={styles.label}>Username</Text>
                <View style={styles.inputWrap}>
                  <SymbolView
                    name={{ ios: 'person', android: 'person', web: 'person' }}
                    tintColor={colors.muted}
                    size={19}
                  />
                  <TextInput
                    accessibilityLabel="Username"
                    autoCapitalize="none"
                    autoComplete="username"
                    autoCorrect={false}
                    onChangeText={setUsername}
                    placeholder="Enter your username"
                    placeholderTextColor="#8793A4"
                    returnKeyType="next"
                    style={styles.input}
                    textContentType="username"
                    value={username}
                  />
                </View>

                <Text style={styles.label}>Password</Text>
                <View style={styles.inputWrap}>
                  <SymbolView
                    name={{ ios: 'lock', android: 'lock', web: 'lock' }}
                    tintColor={colors.muted}
                    size={19}
                  />
                  <TextInput
                    accessibilityLabel="Password"
                    autoComplete="current-password"
                    onChangeText={setPassword}
                    onSubmitEditing={submit}
                    placeholder="Enter your password"
                    placeholderTextColor="#8793A4"
                    returnKeyType="go"
                    secureTextEntry={!passwordVisible}
                    style={styles.input}
                    textContentType="password"
                    value={password}
                  />
                  <Pressable
                    accessibilityRole="button"
                    accessibilityLabel={passwordVisible ? 'Hide password' : 'Show password'}
                    accessibilityState={{ selected: passwordVisible }}
                    hitSlop={8}
                    onPress={() => setPasswordVisible((visible) => !visible)}
                    style={styles.visibilityToggle}
                  >
                    <SymbolView
                      name={{
                        ios: passwordVisible ? 'eye.slash' : 'eye',
                        android: passwordVisible ? 'visibility_off' : 'visibility',
                        web: passwordVisible ? 'visibility_off' : 'visibility',
                      }}
                      tintColor={colors.muted}
                      size={20}
                    />
                  </Pressable>
                </View>
              </View>

              {error ? (
                <View accessibilityRole="alert" style={styles.errorNotice}>
                  <Text style={styles.errorText}>{error}</Text>
                </View>
              ) : null}

              <Pressable
                accessibilityRole="button"
                accessibilityLabel={isLoading
                  ? (mode === 'register' ? 'Creating account' : 'Signing in')
                  : (mode === 'register' ? 'Create account now' : 'Sign in')}
                accessibilityState={{ disabled: isLoading, busy: isLoading }}
                disabled={isLoading}
                onPress={submit}
                style={({ pressed }) => [styles.submit, pressed && !isLoading && styles.pressed]}
              >
                <Text style={styles.submitText}>
                  {isLoading ? (mode === 'register' ? 'Creating account…' : 'Signing in…')
                    : mode === 'register' ? 'Create Account' : 'Sign In'}
                </Text>
              </Pressable>
              <View style={styles.footerRow}>
                <Text style={styles.footer}>
                  {mode === 'login' ? "Don't have an account?" : 'Already have an account?'}
                </Text>
                <Pressable
                  accessibilityRole="button"
                  accessibilityLabel={mode === 'login' ? 'Create account' : 'Sign in'}
                  accessibilityState={{ disabled: isLoading }}
                  disabled={isLoading}
                  onPress={() => {
                    setMode((current) => current === 'login' ? 'register' : 'login')
                    setError('')
                  }}
                  style={styles.modeToggle}
                >
                  <Text style={styles.modeToggleText}>
                    {mode === 'login' ? 'Create account' : 'Sign in'}
                  </Text>
                </Pressable>
              </View>
            </View>
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
  content: {
    flexGrow: 1,
    justifyContent: 'center',
    paddingHorizontal: spacing.lg,
    paddingVertical: spacing.xl,
  },
  form: {
    width: '100%',
    maxWidth: 440,
    alignSelf: 'center',
  },
  title: {
    color: colors.navy,
    fontSize: 30,
    fontWeight: '700',
    letterSpacing: -0.7,
  },
  subtitle: {
    marginTop: 8,
    marginBottom: 32,
    color: colors.muted,
    fontSize: 14,
    lineHeight: 21,
  },
  fields: {
    gap: 11,
  },
  label: {
    marginTop: 3,
    color: colors.ink,
    fontSize: 13,
    fontWeight: '600',
  },
  inputWrap: {
    minHeight: 56,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 12,
    paddingHorizontal: 16,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 15,
    backgroundColor: colors.surface,
    shadowColor: colors.navy,
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.035,
    shadowRadius: 8,
    elevation: 1,
  },
  input: {
    flex: 1,
    minWidth: 0,
    minHeight: minimumTouchTarget,
    paddingVertical: 8,
    color: colors.navy,
    fontSize: 14,
  },
  visibilityToggle: {
    width: minimumTouchTarget,
    height: minimumTouchTarget,
    alignItems: 'center',
    justifyContent: 'center',
    marginRight: -8,
  },
  errorNotice: {
    marginTop: 16,
    padding: 12,
    borderWidth: 1,
    borderColor: '#F0CACA',
    borderRadius: 12,
    backgroundColor: '#FFF6F6',
  },
  errorText: {
    color: '#8A3434',
    fontSize: 13,
    lineHeight: 18,
  },
  submit: {
    minHeight: 56,
    overflow: 'hidden',
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 26,
    borderRadius: 15,
    backgroundColor: colors.teal,
    shadowColor: colors.teal,
    shadowOffset: { width: 0, height: 7 },
    shadowOpacity: 0.2,
    shadowRadius: 12,
    elevation: 4,
  },
  submitText: {
    color: colors.surface,
    fontSize: 15,
    fontWeight: '700',
    letterSpacing: 0.2,
  },
  pressed: {
    opacity: 0.88,
  },
  footer: {
    color: '#8490A2',
    fontSize: 12,
    textAlign: 'center',
  },
  footerRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 5,
    marginTop: 28,
  },
  modeToggle: {
    minHeight: minimumTouchTarget,
    justifyContent: 'center',
    paddingHorizontal: 4,
  },
  modeToggleText: {
    color: colors.teal,
    fontSize: 12,
    fontWeight: '700',
  },
})
