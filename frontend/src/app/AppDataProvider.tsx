import { useState, type PropsWithChildren } from 'react'
import { AppDataContext } from './appDataContext'
import { initialBeneficiaries, initialEntries, initialPolicy } from '../data/mockData'
import type { DiaryEntry, NewBeneficiary, NewEntry } from '../types'

export function AppDataProvider({ children }: PropsWithChildren) {
  const [entries, setEntries] = useState(initialEntries)
  const [beneficiaries, setBeneficiaries] = useState(initialBeneficiaries)
  const [policyText, setPolicyText] = useState(initialPolicy)

  const addEntry = (entry: NewEntry) => {
    const newEntry: DiaryEntry = {
      ...entry,
      id: `entry-${Date.now()}`,
      date: new Intl.DateTimeFormat('en', { dateStyle: 'medium' }).format(new Date()),
    }
    setEntries((currentEntries) => [newEntry, ...currentEntries])
  }

  const addBeneficiary = (beneficiary: NewBeneficiary) => {
    setBeneficiaries((currentBeneficiaries) => [
      ...currentBeneficiaries,
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
      value={{ entries, beneficiaries, policyText, addEntry, addBeneficiary, setPolicyText }}
    >
      {children}
    </AppDataContext.Provider>
  )
}
