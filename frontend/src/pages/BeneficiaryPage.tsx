import { Link } from 'react-router-dom'
import { useAppData } from '../app/useAppData'
import { Brand } from '../components/Brand'
import { StatusBadge } from '../components/StatusBadge'

export function BeneficiaryPage() {
  const { entries } = useAppData()
  const sharedEntries = entries.filter((entry) => entry.visibility === 'Shared')

  return (
    <main className="beneficiary-page">
      <header className="beneficiary-header">
        <Link to="/login" aria-label="Return to sign in"><Brand /></Link>
        <Link className="text-link" to="/login">Exit preview <span aria-hidden="true">↗</span></Link>
      </header>

      <section className="beneficiary-welcome">
        <p className="eyebrow">BENEFICIARY PREVIEW</p>
        <h1>A window into a shared story.</h1>
        <p>This sample portal displays entries labelled Shared. Real access must always be verified by the backend.</p>
      </section>

      <section className="beneficiary-scope">
        <span className="scope-icon" aria-hidden="true">◇</span>
        <p><strong>Read-only access</strong><span>Only sample shared entries are shown here. This screen does not grant, verify, or secure access.</span></p>
        <StatusBadge label="Preview" tone="neutral" />
      </section>

      <section className="beneficiary-entry-list" aria-label="Shared sample entries">
        {sharedEntries.map((entry) => (
          <article className="beneficiary-entry" key={entry.id}>
            <div className="entry-tile-top">
              <StatusBadge label="Shared sample" tone="shared" />
              <span>{entry.date}</span>
            </div>
            <h2>{entry.title}</h2>
            <p>{entry.summary}</p>
          </article>
        ))}
        {sharedEntries.length === 0 && (
          <div className="empty-state"><h2>No shared entries</h2><p>No sample entries are currently labelled Shared.</p></div>
        )}
      </section>

      <footer className="beneficiary-footer">ENNOVA · A private legacy vault · Frontend prototype</footer>
    </main>
  )
}
