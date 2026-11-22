import { useState } from 'react'
import { Pressable, StyleSheet, Text, TextInput, View } from 'react-native'
import { AppScreen } from '@/components/AppScreen'
import { PageTitle } from '@/components/PageTitle'
import { Panel } from '@/components/Panel'
import { PreviewNotice } from '@/components/PreviewNotice'
import { useAppData } from '@/context/AppDataProvider'
import { colors, spacing } from '@/constants/theme'
import type { BeneficiaryStatus, NewBeneficiary } from '@/types'
import { useAuth } from '@/context/AuthProvider'
import { apiRequest, ApiError, type InvitationResponse } from '@/services/api'

export default function PeopleScreen() {
  const { beneficiaries, addBeneficiary } = useAppData()
  const { accessToken, clearRejectedSession } = useAuth()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [relation, setRelation] = useState('')
  const [notice, setNotice] = useState('')
  const [personId, setPersonId] = useState('')
  const [expiresAt, setExpiresAt] = useState('')
  const [invitationCode, setInvitationCode] = useState('')
  const [isIssuing, setIsIssuing] = useState(false)
  const [error, setError] = useState('')

  const submit = async () => {
    setError('')
    if (!name.trim() || !email.trim() || !relation.trim()) return
    if (!accessToken) {
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
      return
    }
    if (!personId.trim() || !expiresAt.trim()) {
      setError('Enter a person identifier and expiry date.')
      return
    }
    setIsIssuing(true)
    try {
      const result = await apiRequest<InvitationResponse>('/invitations', {
        method: 'POST',
        token: accessToken,
        body: {
          person_id: personId.trim().toLowerCase(),
          expires_at: expiresAt.trim(),
        },
      })
      setInvitationCode(result.invitation_code)
      setNotice(`Invitation issued for ${result.person_id}. It expires ${new Date(result.expires_at).toLocaleString()}.`)
    } catch (caught) {
      clearRejectedSession(caught)
      setError(caught instanceof ApiError ? caught.message : 'The invitation could not be issued.')
    } finally {
      setIsIssuing(false)
    }
  }

  return (
    <AppScreen>
      <PageTitle
        eyebrow="PEOPLE YOU TRUST"
        title="Beneficiaries"
        description="Review sample access statuses and trusted people."
      />
      <Pressable
        accessibilityRole="button"
        accessibilityState={{ expanded: showForm }}
        style={styles.action}
        onPress={() => setShowForm((open) => !open)}
      >
        <Text style={styles.actionText}>{showForm ? 'Cancel' : '＋  Add beneficiary'}</Text>
      </Pressable>

      {showForm && (
        <Panel>
          <Text style={styles.formTitle}>Add a trusted person</Text>
          <TextInput accessibilityLabel="Full name" onChangeText={setName} placeholder="Full name" style={styles.input} value={name} />
          <TextInput accessibilityLabel="Email" autoCapitalize="none" keyboardType="email-address" onChangeText={setEmail} placeholder="Email address" style={styles.input} value={email} />
          <TextInput accessibilityLabel="Relationship" onChangeText={setRelation} placeholder="Relationship" style={styles.input} value={relation} />
          {accessToken ? (
            <>
              <TextInput
                accessibilityLabel="Person identifier"
                autoCapitalize="none"
                onChangeText={setPersonId}
                placeholder="person_id"
                style={styles.input}
                value={personId}
              />
              <TextInput
                accessibilityLabel="Invitation expiry"
                autoCapitalize="none"
                onChangeText={setExpiresAt}
                placeholder="2026-12-31T23:59:59Z"
                style={styles.input}
                value={expiresAt}
              />
            </>
          ) : null}
          <Pressable
            accessibilityRole="button"
            accessibilityState={{ disabled: isIssuing }}
            disabled={isIssuing}
            style={styles.saveButton}
            onPress={() => void submit()}
          >
            <Text style={styles.saveText}>
              {isIssuing ? 'Issuing…' : accessToken ? 'Issue invitation' : 'Add to preview'}
            </Text>
          </Pressable>
        </Panel>
      )}
      {notice ? <Text style={styles.notice}>{notice}</Text> : null}
      {error ? <Text style={styles.errorText} accessibilityRole="alert">{error}</Text> : null}
      {invitationCode ? (
        <Panel>
          <Text style={styles.formTitle}>Invitation code</Text>
          <Text selectable style={styles.invitationCode}>{invitationCode}</Text>
          <Text style={styles.notice}>Single-use and expiring. Share it through a trusted channel.</Text>
        </Panel>
      ) : null}

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
    minHeight: 44,
    justifyContent: 'center',
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
  errorText: {
    color: '#8A3434',
    fontSize: 12,
  },
  invitationCode: {
    padding: 12,
    borderRadius: 10,
    backgroundColor: '#EFF8F8',
    color: colors.navy,
    fontSize: 16,
    fontWeight: '800',
    textAlign: 'center',
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
