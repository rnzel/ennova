import { createContext, useContext, useState, type PropsWithChildren } from 'react'
import { initialBeneficiaries, initialEntries, initialPolicy } from '../data/mockData'
import type { Beneficiary, DiaryEntry, NewBeneficiary, NewEntry } from '../types'

type AppData = {
  entries: DiaryEntry[]
  beneficiaries: Beneficiary[]
  policy: string
  addEntry: (entry: NewEntry) => void
  addBeneficiary: (beneficiary: NewBeneficiary) => void
  setPolicy: (policy: string) => void
}

const AppDataContext = createContext<AppData | null>(null)

export function AppDataProvider({ children }: PropsWithChildren) {
  const [entries, setEntries] = useState(initialEntries)
  const [beneficiaries, setBeneficiaries] = useState(initialBeneficiaries)
  const [policy, setPolicy] = useState(initialPolicy)

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
    <AppDataContext.Provider value={{ entries, beneficiaries, policy, addEntry, addBeneficiary, setPolicy }}>
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
