import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'
import type { BeneficiaryStatus, NewBeneficiary } from '@/types'

export default function PeopleScreen() {
  const { beneficiaries, addBeneficiary } = useAppData()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [relation, setRelation] = useState('')
  const [notice, setNotice] = useState('')

  const submit = () => {
    if (!name.trim() || !email.trim() || !relation.trim()) return
    const newBeneficiary: NewBeneficiary = {
      name: name.trim(),
      email: email.trim(),
      relation: relation.trim(),
    }
    addBeneficiary(newBeneficiary)
    setName('')
    setEmail('')
    setRelation('')
    setShowForm(false)
    setNotice('Added to this preview session only.')
  }

  return (
    <AppScreen>
      <PageTitle
        eyebrow="PEOPLE YOU TRUST"
        title="Beneficiaries"
        description="Review sample access statuses and trusted people."
      />
      <Pressable style={styles.action} onPress={() => setShowForm((open) => !open)}>
        <Text style={styles.actionText}>{showForm ? 'Cancel' : '＋  Add beneficiary'}</Text>
      </Pressable>

      {showForm && (
        <Panel>
          <Text style={styles.formTitle}>Add a trusted person</Text>
          <TextInput accessibilityLabel="Full name" onChangeText={setName} placeholder="Full name" style={styles.input} value={name} />
          <TextInput accessibilityLabel="Email" autoCapitalize="none" keyboardType="email-address" onChangeText={setEmail} placeholder="Email address" style={styles.input} value={email} />
          <TextInput accessibilityLabel="Relationship" onChangeText={setRelation} placeholder="Relationship" style={styles.input} value={relation} />
          <Pressable style={styles.saveButton} onPress={submit}>
            <Text style={styles.saveText}>Add to preview</Text>
          </Pressable>
        </Panel>
      )}
      {notice ? <Text style={styles.notice}>{notice}</Text> : null}

      <View style={styles.list}>
        {beneficiaries.map((person) => (
          <View key={person.id} style={styles.person}>
            <View style={styles.avatar}><Text style={styles.avatarText}>{person.name.charAt(0)}</Text></View>
            <View style={styles.personCopy}>
              <Text style={styles.personName}>{person.name}</Text>
              <Text style={styles.personMeta}>{person.relation} · {person.email}</Text>
              <Text style={styles.personMeta}>Last activity: {person.lastSeen}</Text>
            </View>
            <Status status={person.status} />
          </View>
        ))}
      </View>
      <PreviewNotice>
        Invitations and access control are not connected. Do not enter real beneficiary information.
      </PreviewNotice>
    </AppScreen>
  )
}

function Status({ status }: { status: BeneficiaryStatus }) {
  const palette = status === 'Granted'
    ? { background: colors.success, foreground: colors.successInk }
    : status === 'Review'
      ? { background: colors.warning, foreground: colors.warningInk }
      : { background: colors.neutral, foreground: colors.neutralInk }

  return (
    <View style={[styles.status, { backgroundColor: palette.background }]}>
      <Text style={[styles.statusText, { color: palette.foreground }]}>{status}</Text>
    </View>
  )
}

const styles = StyleSheet.create({
  action: {
    alignItems: 'center',
    justifyContent: 'center',
    minHeight: 46,
    borderRadius: 12,
    backgroundColor: colors.navy,
  },
  actionText: {
    color: colors.surface,
    fontSize: 13,
    fontWeight: '700',
  },
  formTitle: {
    color: colors.navy,
    fontSize: 16,
    fontWeight: '700',
  },
  input: {
    minHeight: 44,
    paddingHorizontal: 12,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 10,
    color: colors.ink,
    fontSize: 13,
  },
  saveButton: {
    alignItems: 'center',
    paddingVertical: 12,
    borderRadius: 10,
    backgroundColor: colors.cyan,
  },
  saveText: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '800',
  },
  notice: {
    color: colors.successInk,
    fontSize: 12,
  },
  list: {
    paddingHorizontal: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 16,
    backgroundColor: colors.surface,
  },
  person: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    minHeight: 74,
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: colors.border,
  },
  avatar: {
    width: 38,
    height: 38,
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: 19,
    backgroundColor: '#D7EFF0',
  },
  avatarText: {
    color: colors.navy,
    fontSize: 14,
    fontWeight: '800',
  },
  personCopy: {
    flex: 1,
    gap: 4,
  },
  personName: {
    color: colors.navy,
    fontSize: 12,
    fontWeight: '700',
  },
  personMeta: {
    color: colors.muted,
    fontSize: 10,
  },
  status: {
    paddingHorizontal: 8,
    paddingVertical: 5,
    borderRadius: 999,
  },
  statusText: {
    fontSize: 9,
    fontWeight: '800',
  },
})
