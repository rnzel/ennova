import { createContext, useContext, useEffect, useState, type PropsWithChildren } from 'react'
import { initialBeneficiaries, initialEntries, initialPolicy } from '../data/mockData'
import type { Beneficiary, DiaryEntry, NewBeneficiary, NewEntry } from '../types'
import { useAuth } from './AuthProvider'
import { apiRequest, type ApiEntryList } from '@/services/api'

type AppData = {
  entries: DiaryEntry[]
  beneficiaries: Beneficiary[]
  policy: string
  addEntry: (entry: NewEntry) => void
  addBeneficiary: (beneficiary: NewBeneficiary) => void
  setPolicy: (policy: string) => void
  refreshEntries: () => Promise<void>
  entriesLoading: boolean
  entriesError: string
}

const AppDataContext = createContext<AppData | null>(null)

export function AppDataProvider({ children }: PropsWithChildren) {
  const [entries, setEntries] = useState(initialEntries)
  const [beneficiaries, setBeneficiaries] = useState(initialBeneficiaries)
  const [policy, setPolicy] = useState(initialPolicy)
  const [entriesLoading, setEntriesLoading] = useState(false)
  const [entriesError, setEntriesError] = useState('')
  const { accessToken, clearRejectedSession } = useAuth()

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

  return (
    <AppDataContext.Provider
      value={{
        entries,
        beneficiaries,
        policy,
        addEntry,
        addBeneficiary,
        setPolicy,
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
