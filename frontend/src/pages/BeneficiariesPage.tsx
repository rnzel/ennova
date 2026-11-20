import { useState, type FormEvent } from 'react'
import { useAppData } from '../app/useAppData'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import type { BeneficiaryStatus } from '../types'

function statusTone(status: BeneficiaryStatus) {
  if (status === 'Granted') return 'success'
  if (status === 'Review') return 'warning'
  return 'neutral'
}

export function BeneficiariesPage() {
  const { beneficiaries, addBeneficiary } = useAppData()
  const [showForm, setShowForm] = useState(false)
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [relation, setRelation] = useState('')
  const [notice, setNotice] = useState('')

  const submitInvite = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    addBeneficiary({ name: name.trim(), email: email.trim(), relation: relation.trim() })
    setName('')
    setEmail('')
    setRelation('')
    setShowForm(false)
    setNotice('Sample beneficiary added to this preview session.')
  }

  return (
    <>
      <PageHeader
        eyebrow="PEOPLE YOU TRUST"
        title="Beneficiaries"
        description="Keep track of who may receive access and review pending invitations."
        action={
          <button
            type="button"
            className="button button-primary"
            onClick={() => {
              setShowForm((open) => !open)
              setNotice('')
            }}
          >
            <span aria-hidden="true">＋</span> Add beneficiary
          </button>
        }
      />

      {notice && <p className="inline-notice" role="status">{notice}</p>}

      {showForm && (
        <form className="panel invite-form" onSubmit={submitInvite}>
          <div>
            <p className="eyebrow">NEW INVITATION · PREVIEW ONLY</p>
            <h2>Add a trusted person</h2>
          </div>
          <label className="field-label">
            Full name
            <input className="text-input" value={name} onChange={(event) => setName(event.target.value)} required />
          </label>
          <label className="field-label">
            Email
            <input className="text-input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required />
          </label>
          <label className="field-label">
            Relationship
            <input className="text-input" value={relation} onChange={(event) => setRelation(event.target.value)} placeholder="e.g. Family, friend" required />
          </label>
          <div className="invite-form-actions">
            <button className="button button-secondary" type="button" onClick={() => setShowForm(false)}>Cancel</button>
            <button className="button button-primary" type="submit">Add to preview</button>
          </div>
        </form>
      )}

      <section className="panel table-panel">
        <div className="panel-heading">
          <div>
            <p className="eyebrow">ACCESS DIRECTORY</p>
            <h2>{beneficiaries.length} people</h2>
          </div>
          <span className="subtle-label">Sample statuses only</span>
        </div>
        <div className="table-scroll">
          <table className="data-table">
            <thead>
              <tr><th>Name</th><th>Relationship</th><th>Status</th><th>Last activity</th></tr>
            </thead>
            <tbody>
              {beneficiaries.map((person) => (
                <tr key={person.id}>
                  <td>
                    <span className="table-person">
                      <span className="avatar">{person.name.charAt(0)}</span>
                      <span><strong>{person.name}</strong><small>{person.email}</small></span>
                    </span>
                  </td>
                  <td>{person.relation}</td>
                  <td><StatusBadge label={person.status} tone={statusTone(person.status)} /></td>
                  <td>{person.lastSeen}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      <div className="privacy-note">
        <span className="privacy-note-icon" aria-hidden="true">i</span>
        <p><strong>Access is not automatic</strong><span>Real invitations, verification, and permissions must be handled by the backend.</span></p>
      </div>
    </>
  )
}
