// Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)
// Paradigm: Scripting (API orchestration and in-memory UI state)

import { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react'
import { initialBeneficiaries, initialEntries, initialPolicy } from '../data/mockData'
import type { Beneficiary, DiaryEntry, NewBeneficiary, NewEntry } from '../types'
import { useAuth } from './AuthProvider'
import { ApiError, apiRequest, type ApiEntryList, type PolicyUpdateResponse } from '@/services/api'

export type PolicyPublishIntent = 'policy' | 'letter-release'

export type PolicyPublishOutcome = {
  intent: PolicyPublishIntent
  source: string
  mode: 'backend' | 'preview'
}

type PolicyConfirmation = {
  intent: PolicyPublishIntent
  mode: 'backend' | 'preview'
  source: string
}

type AppData = {
  entries: DiaryEntry[]
  beneficiaries: Beneficiary[]
  policy: string
  pendingReleaseSource: string | null
  pendingReleaseError: string
  policyConfirmation: PolicyConfirmation | null
  policyConfirmationError: string
  policyPublishOutcome: PolicyPublishOutcome | null
  policyFrozen: boolean
  isPublishingPolicy: boolean
  addEntry: (entry: NewEntry) => void
  addBeneficiary: (beneficiary: NewBeneficiary) => void
  setPolicy: (policy: string) => void
  requestPolicyConfirmation: (source: string, intent: PolicyPublishIntent) => void
  cancelPolicyConfirmation: () => void
  retryPendingRelease: () => void
  confirmPolicyUpdate: () => Promise<boolean>
  clearPolicyPublishOutcome: () => void
  refreshEntries: () => Promise<void>
  entriesLoading: boolean
  entriesError: string
}

const AppDataContext = createContext<AppData | null>(null)

export function AppDataProvider({ children }: PropsWithChildren) {
  const { accessToken, clearRejectedSession } = useAuth()
  const [entries, setEntries] = useState(initialEntries)
  const [beneficiaries, setBeneficiaries] = useState(initialBeneficiaries)
  const [policy, setPolicy] = useState(accessToken ? '' : initialPolicy)
  const [pendingReleaseSource, setPendingReleaseSource] = useState<string | null>(null)
  const [pendingReleaseError, setPendingReleaseError] = useState('')
  const [policyConfirmation, setPolicyConfirmation] = useState<PolicyConfirmation | null>(null)
  const [policyConfirmationError, setPolicyConfirmationError] = useState('')
  const [policyPublishOutcome, setPolicyPublishOutcome] = useState<PolicyPublishOutcome | null>(null)
  const [policyFrozen, setPolicyFrozen] = useState(false)
  const [isPublishingPolicy, setIsPublishingPolicy] = useState(false)
  const [entriesLoading, setEntriesLoading] = useState(false)
  const [entriesError, setEntriesError] = useState('')
  useEffect(() => {
    setPolicy(accessToken ? '' : initialPolicy)
  }, [accessToken])

  const refreshEntries = async () => {
    if (!accessToken) return
    setEntriesLoading(true)
    setEntriesError('')
    try {
      const response = await apiRequest<ApiEntryList>('/entries', { token: accessToken })
      setEntries(response.entries.map((entry) => {
        const date = new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(
          new Date(entry.created_at),
        )
        return {
          id: entry.entry_id,
          title: entry.entry_id,
          date,
          summary: entry.topics.length
            ? `Topics: ${entry.topics.join(', ')}`
            : 'Metadata only; entry content is not available.',
          content: '',
          visibility: 'Private',
          writingMode: 'Verbatim',
          source: 'api',
          kind: entry.kind,
          topics: entry.topics,
          disclaimer: entry.disclaimer,
        }
      }))
    } catch (error) {
      clearRejectedSession(error)
      setEntries([])
      setEntriesError(
        error instanceof Error
          ? 'Entries could not be loaded. Please try again.'
          : 'Entries could not be loaded.',
      )
    } finally {
      setEntriesLoading(false)
    }
  }

  useEffect(() => {
    if (accessToken) {
      void refreshEntries()
    }
  }, [accessToken])

  const addEntry = (entry: NewEntry) => {
    setEntries((current) => [
      {
        ...entry,
        id: `entry-${Date.now()}`,
        date: new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date()),
      },
      ...current,
    ])
  }

  const addBeneficiary = (beneficiary: NewBeneficiary) => {
    setBeneficiaries((current) => [
      ...current,
      {
        ...beneficiary,
        id: `beneficiary-${Date.now()}`,
        status: 'Pending',
        lastSeen: 'Not yet',
      },
    ])
  }

  const requestPolicyConfirmation = (source: string, intent: PolicyPublishIntent) => {
    setPolicyPublishOutcome(null)
    setPolicyConfirmationError('')
    if (intent === 'letter-release') {
      setPendingReleaseSource(source)
      setPendingReleaseError('')
    }
    setPolicyConfirmation({
      source,
      intent,
      mode: intent === 'letter-release' || accessToken ? 'backend' : 'preview',
    })
  }

  const cancelPolicyConfirmation = () => {
    setPolicyConfirmation(null)
    setPolicyConfirmationError('')
  }

  const retryPendingRelease = () => {
    if (!pendingReleaseSource || policyFrozen) return
    setPolicyConfirmationError('')
    setPendingReleaseError('')
    setPolicyConfirmation({
      source: pendingReleaseSource,
      intent: 'letter-release',
      mode: 'backend',
    })
  }

  const confirmPolicyUpdate = async (): Promise<boolean> => {
    if (!policyConfirmation || isPublishingPolicy) return false
    const confirmation = policyConfirmation

    if (!accessToken) {
      if (confirmation.mode === 'backend') {
        const message = confirmation.intent === 'letter-release'
          ? 'Sign in again to set the release date.'
          : 'Sign in again to publish this policy.'
        setPolicyConfirmationError(message)
        if (confirmation.intent === 'letter-release') {
          setPendingReleaseError(message)
        }
        return false
      }
      setPolicy(confirmation.source)
      setPolicyConfirmation(null)
      setPolicyPublishOutcome({
        intent: confirmation.intent,
        source: confirmation.source,
        mode: 'preview',
      })
      return true
    }

    setIsPublishingPolicy(true)
    setPolicyConfirmationError('')
    try {
      await apiRequest<PolicyUpdateResponse>('/policy', {
        method: 'PUT',
        token: accessToken,
        body: { source: confirmation.source },
      })
      setPolicy(confirmation.source)
      setPolicyFrozen(false)
      if (confirmation.intent === 'letter-release') {
        setPendingReleaseSource(null)
        setPendingReleaseError('')
      }
      setPolicyConfirmation(null)
      setPolicyPublishOutcome({
        intent: confirmation.intent,
        source: confirmation.source,
        mode: 'backend',
      })
      return true
    } catch (error) {
      clearRejectedSession(error)
      const message = error instanceof ApiError && error.status === 401
        ? confirmation.intent === 'letter-release'
          ? 'Your session expired. Sign in again to set the release date.'
          : 'Your session expired. Sign in again to publish this policy.'
        : error instanceof ApiError
          ? error.message
          : 'The policy could not be saved.'
      if (error instanceof ApiError && error.code === 'policy_frozen') {
        setPolicyFrozen(true)
      }
      setPolicyConfirmationError(message)
      if (confirmation.intent === 'letter-release') {
        setPendingReleaseError(message)
      }
      return false
    } finally {
      setIsPublishingPolicy(false)
    }
  }

  return (
    <AppDataContext.Provider
      value={{
        entries,
        beneficiaries,
        policy,
        pendingReleaseSource,
        pendingReleaseError,
        policyConfirmation,
        policyConfirmationError,
        policyPublishOutcome,
        policyFrozen,
        isPublishingPolicy,
        addEntry,
        addBeneficiary,
        setPolicy,
        requestPolicyConfirmation,
        cancelPolicyConfirmation,
        retryPendingRelease,
        confirmPolicyUpdate,
        clearPolicyPublishOutcome: () => setPolicyPublishOutcome(null),
        refreshEntries,
        entriesLoading,
        entriesError,
      }}
    >
      {children}
    </AppDataContext.Provider>
  )
}

export function useAppData() {
  const context = useContext(AppDataContext)
  if (!context) {
    throw new Error('useAppData must be used within AppDataProvider')
  }
  return context
}
