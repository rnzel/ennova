export type EntryVisibility = 'Private' | 'Shared' | 'Restricted'
export type WritingMode = 'Verbatim' | 'Light fix' | 'Review'
export type BadgeTone =
  | 'neutral'
  | 'success'
  | 'warning'
  | 'danger'
  | 'private'
  | 'shared'
  | 'restricted'

export type DiaryEntry = {
  id: string
  title: string
  date: string
  summary: string
  content: string
  visibility: EntryVisibility
  writingMode: WritingMode
}

export type BeneficiaryStatus = 'Granted' | 'Review' | 'Pending'

export type Beneficiary = {
  id: string
  name: string
  email: string
  relation: string
  status: BeneficiaryStatus
  lastSeen: string
}

export type NewEntry = Omit<DiaryEntry, 'id' | 'date'>
export type NewBeneficiary = Pick<Beneficiary, 'name' | 'email' | 'relation'>
