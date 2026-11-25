// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: n/a (interface)

import { Modal, Pressable, ScrollView, StyleSheet, Text, View } from 'react-native'
import { ActionButton } from '@/components/ActionButton'
import { useAppData } from '@/context/AppDataProvider'
import { useAuth } from '@/context/AuthProvider'
import { colors, spacing } from '@/constants/theme'

export function PolicyPublishManager() {
  const {
    pendingReleaseSource,
    pendingReleaseError,
    policyConfirmation,
    policyConfirmationError,
    policyFrozen,
    isPublishingPolicy,
    cancelPolicyConfirmation,
    retryPendingRelease,
    confirmPolicyUpdate,
  } = useAppData()
  const { accessToken } = useAuth()
  const confirmation = policyConfirmation
  const previewOnly = confirmation?.mode === 'preview'

  return (
    <>
      {pendingReleaseSource ? (
        <View accessibilityRole="alert" style={styles.pendingNotice}>
          <Text style={styles.pendingTitle}>
            Letter saved, but the release date was not set.
          </Text>
          {pendingReleaseError ? (
            <Text style={styles.pendingMessage}>{pendingReleaseError}</Text>
          ) : null}
          <ActionButton
            accessibilityLabel="Retry setting the letter release date"
            disabled={policyFrozen || !accessToken}
            label={
              policyFrozen
                ? 'Policy is frozen'
                : accessToken
                  ? 'Retry release date'
                  : 'Sign in to retry'
            }
            onPress={retryPendingRelease}
            variant="secondary"
          />
        </View>
      ) : null}
      <Modal
        animationType="slide"
        onRequestClose={cancelPolicyConfirmation}
        transparent
        visible={confirmation !== null}
      >
        <View style={styles.backdrop}>
          <View style={styles.dialog} accessibilityViewIsModal>
            <Text accessibilityRole="header" style={styles.title}>
              Confirm policy replacement
            </Text>
            <Text style={styles.description}>
              {previewOnly
                ? 'Preview only. This source will not be sent to the backend. If it is later published, it replaces the whole active policy.'
                : 'This replaces the whole active policy. The app cannot read the backend policy, so review the complete source before continuing.'}
            </Text>
            <ScrollView
              accessibilityLabel="Complete policy source to be replaced"
              style={styles.source}
            >
              <Text selectable style={styles.sourceText}>
                {confirmation?.source ?? ''}
              </Text>
            </ScrollView>
            {policyConfirmationError ? (
              <Text accessibilityRole="alert" style={styles.error}>
                {policyConfirmationError}
              </Text>
            ) : null}
            <ActionButton
              accessibilityLabel={
                isPublishingPolicy
                  ? 'Sending policy'
                  : previewOnly
                    ? 'Confirm local policy preview'
                    : 'Confirm and replace complete policy'
              }
              disabled={
                isPublishingPolicy ||
                policyFrozen ||
                (confirmation?.mode === 'backend' && !accessToken)
              }
              label={
                isPublishingPolicy
                  ? 'Sending…'
                  : previewOnly
                    ? 'Save preview only'
                    : policyFrozen
                      ? 'Policy is frozen'
                      : 'Confirm and replace policy'
              }
              onPress={() => void confirmPolicyUpdate()}
            />
            <Pressable
              accessibilityRole="button"
              accessibilityLabel="Cancel policy replacement"
              disabled={isPublishingPolicy}
              onPress={cancelPolicyConfirmation}
              style={styles.cancel}
            >
              <Text style={styles.cancelText}>Cancel</Text>
            </Pressable>
          </View>
        </View>
      </Modal>
    </>
  )
}

const styles = StyleSheet.create({
  pendingNotice: {
    gap: spacing.sm,
    padding: spacing.md,
    borderBottomWidth: 1,
    borderColor: colors.warningInk,
    backgroundColor: colors.warning,
  },
  pendingTitle: {
    color: colors.warningInk,
    fontSize: 13,
    fontWeight: '700',
  },
  pendingMessage: {
    color: colors.warningInk,
    fontSize: 12,
    lineHeight: 17,
  },
  backdrop: {
    flex: 1,
    justifyContent: 'center',
    padding: spacing.md,
    backgroundColor: 'rgba(7, 58, 92, 0.45)',
  },
  dialog: {
    gap: spacing.sm,
    maxHeight: '90%',
    padding: spacing.md,
    borderWidth: 1,
    borderColor: colors.border,
    borderRadius: 18,
    backgroundColor: colors.surface,
  },
  title: {
    color: colors.navy,
    fontSize: 17,
    fontWeight: '700',
  },
  description: {
    color: colors.muted,
    fontSize: 12,
    lineHeight: 18,
  },
  source: {
    maxHeight: 220,
    padding: spacing.sm,
    borderRadius: 10,
    backgroundColor: colors.neutral,
  },
  sourceText: {
    color: colors.ink,
    fontFamily: 'monospace',
    fontSize: 12,
    lineHeight: 18,
  },
  error: {
    color: '#8A3434',
    fontSize: 12,
    lineHeight: 17,
  },
  cancel: {
    minHeight: 44,
    alignItems: 'center',
    justifyContent: 'center',
  },
  cancelText: {
    color: colors.navy,
    fontSize: 13,
    fontWeight: '700',
  },
})
