import { useState } from 'react'
import { router } from 'expo-router'
import { Pressable, StyleSheet, Switch, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { colors } from '@/constants/theme'

export default function SettingsScreen() {
  const [displayName, setDisplayName] = useState('Diary Owner')
  const [email, setEmail] = useState('owner@example.test')
  const [reminders, setReminders] = useState(false)
  const [saved, setSaved] = useState(false)

  return (
    <AppScreen>
      <PageTitle
        eyebrow="PREFERENCES"
        title="Settings"
        description="Manage the account and experience preferences shown in this prototype."
      />
      <Panel>
        <Text style={styles.section}>ACCOUNT</Text>
        <Text style={styles.panelTitle}>Profile</Text>
        <Text style={styles.label}>Display name</Text>
        <TextInput onChangeText={setDisplayName} style={styles.input} value={displayName} />
        <Text style={styles.label}>Email address</Text>
        <TextInput autoCapitalize="none" keyboardType="email-address" onChangeText={setEmail} style={styles.input} value={email} />
        <Pressable style={styles.save} onPress={() => setSaved(true)}>
          <Text style={styles.saveText}>Save preview settings</Text>
        </Pressable>
        {saved && <Text style={styles.saved}>Updated in this screen preview only.</Text>}
      </Panel>
      <Panel>
        <Text style={styles.section}>PRIVACY</Text>
        <Text style={styles.panelTitle}>Owner-controlled access</Text>
        <Text style={styles.description}>
          Beneficiary permissions belong to the owner policy and must be enforced by the backend.
        </Text>
        <View style={styles.settingRow}>
          <View style={styles.settingCopy}>
            <Text style={styles.settingTitle}>Preview reminders</Text>
            <Text style={styles.description}>This switch does not schedule notifications.</Text>
          </View>
          <Switch
            accessibilityLabel="Preview reminders"
            onValueChange={setReminders}
            thumbColor={colors.surface}
            trackColor={{ false: '#CBD8DC', true: colors.teal }}
            value={reminders}
          />
        </View>
      </Panel>
      <Panel>
        <Text style={styles.section}>SESSION</Text>
        <Text style={styles.description}>
          Sample entries and changes are stored only in app memory and reset when the app restarts.
        </Text>
        <Pressable style={styles.signOut} onPress={() => router.replace('/login')}>
          <Text style={styles.signOutText}>Return to sign in</Text>
        </Pressable>
      </Panel>
    </AppScreen>
  )
}

const styles = StyleSheet.create({
  section: {
    color: colors.teal,
    fontSize: 9,
    fontWeight: '800',
    letterSpacing: 1.1,
  },
  panelTitle: {
    marginBottom: 3,
    color: colors.navy,
    fontSize: 16,
    fontWeight: '700',
  },
  label: {
    marginTop: 7,
    marginBottom: 6,
    color: colors.ink,
    fontSize: 11,
    fontWeight: '700',
  },
  input: {
    minHeight: 43,
    paddingHorizontal: 11,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    color: colors.ink,
    fontSize: 13,
  },
  save: {
    alignItems: 'center',
    marginTop: 7,
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: colors.cyan,
  },
  saveText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  saved: {
    color: colors.successInk,
    fontSize: 10,
    textAlign: 'center',
  },
  description: {
    color: colors.muted,
    fontSize: 11,
    lineHeight: 17,
  },
  settingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    gap: 12,
    paddingTop: 12,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: colors.border,
  },
  settingCopy: {
    flex: 1,
    gap: 4,
  },
  settingTitle: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '700',
  },
  signOut: {
    alignItems: 'center',
    paddingVertical: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
  },
  signOutText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '700',
  },
})
