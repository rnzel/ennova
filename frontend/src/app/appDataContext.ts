import { createContext } from 'react'
import type { Beneficiary, DiaryEntry, NewBeneficiary, NewEntry } from '../types'

export type AppData = {
  entries: DiaryEntry[]
  beneficiaries: Beneficiary[]
  policyText: string
  addEntry: (entry: NewEntry) => void
  addBeneficiary: (beneficiary: NewBeneficiary) => void
  setPolicyText: (policy: string) => void
}

export const AppDataContext = createContext<AppData | null>(null)
