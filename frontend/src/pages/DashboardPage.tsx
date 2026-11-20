import { Link } from 'react-router-dom'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { useAppData } from '../app/useAppData'
import { visibilityTone } from '../lib/visibility'

export function DashboardPage() {
  const { entries, beneficiaries } = useAppData()
  const sharedCount = entries.filter((entry) => entry.visibility === 'Shared').length

  const stats = [
    { label: 'Diary entries', value: entries.length, note: 'In this preview' },
    { label: 'Beneficiaries', value: beneficiaries.length, note: 'Across all statuses' },
    { label: 'Shared entries', value: sharedCount, note: 'Sample visibility setting' },
  ]

  return (
    <>
      <PageHeader
        eyebrow="OWNER OVERVIEW"
        title="Your story, thoughtfully kept."
        description="A clear view of your journal and the people you have chosen to include."
        action={
          <Link className="button button-primary" to="/owner/entries/new">
            <span aria-hidden="true">＋</span> New entry
          </Link>
        }
      />

      <section className="welcome-panel">
        <div className="welcome-copy">
          <p className="eyebrow">YOUR PRIVATE LEGACY VAULT</p>
          <h2>Keep what matters, on your terms.</h2>
          <p>
            Write a new memory, review your sharing choices, or check how your sample policy is
            organized.
          </p>
          <Link className="welcome-link" to="/owner/policy">
            Review access policy <span aria-hidden="true">→</span>
          </Link>
        </div>
        <div className="welcome-orbit" aria-hidden="true">
          <span>EN</span>
        </div>
      </section>

      <section className="stats-grid" aria-label="Workspace summary">
        {stats.map((stat, index) => (
          <article className="stat-card" key={stat.label}>
            <div className="stat-card-top">
              <span>{stat.label}</span>
              <span className="stat-number-label">0{index + 1}</span>
            </div>
            <strong>{stat.value}</strong>
            <small>{stat.note}</small>
          </article>
        ))}
      </section>

      <div className="dashboard-grid">
        <section className="panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">YOUR JOURNAL</p>
              <h2>Recent entries</h2>
            </div>
            <Link className="text-link" to="/owner/entries">View all <span aria-hidden="true">→</span></Link>
          </div>
          <div className="recent-list">
            {entries.slice(0, 3).map((entry) => (
              <Link className="recent-entry" key={entry.id} to={`/owner/entries/${entry.id}`}>
                <span className={`entry-marker marker-${entry.visibility.toLowerCase()}`} />
                <span className="recent-entry-copy">
                  <strong>{entry.title}</strong>
                  <small>{entry.date} <span>·</span> {entry.writingMode}</small>
                </span>
                <StatusBadge label={entry.visibility} tone={visibilityTone(entry.visibility)} />
                <span className="row-chevron" aria-hidden="true">›</span>
              </Link>
            ))}
          </div>
        </section>

        <section className="panel access-panel">
          <div className="panel-heading">
            <div>
              <p className="eyebrow">PEOPLE YOU TRUST</p>
              <h2>Access overview</h2>
            </div>
            <Link className="icon-link" to="/owner/beneficiaries" aria-label="Manage beneficiaries">↗</Link>
          </div>
          <p className="panel-intro">Each person has a different relationship to your story.</p>
          <div className="compact-people">
            {beneficiaries.slice(0, 3).map((person) => (
              <div className="compact-person" key={person.id}>
                <span className="avatar">{person.name.charAt(0)}</span>
                <span className="person-copy">
                  <strong>{person.name}</strong>
                  <small>{person.relation}</small>
                </span>
                <StatusBadge
                  label={person.status}
                  tone={person.status === 'Granted' ? 'success' : person.status === 'Review' ? 'warning' : 'neutral'}
                />
              </div>
            ))}
          </div>
          <Link className="button button-outline button-wide" to="/owner/beneficiaries">
            Manage beneficiaries
          </Link>
        </section>
      </div>

      <section className="privacy-note">
        <span className="privacy-note-icon" aria-hidden="true">i</span>
        <p>
          <strong>Preview reminder</strong>
          <span>Visibility labels here are sample UI only. Real access decisions must come from the backend policy engine.</span>
        </p>
      </section>
    </>
  )
}
