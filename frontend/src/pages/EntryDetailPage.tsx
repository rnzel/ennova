import { Link, useParams } from 'react-router-dom'
import { useAppData } from '../app/useAppData'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import { visibilityTone } from '../lib/visibility'

export function EntryDetailPage() {
  const { entryId } = useParams()
  const { entries } = useAppData()
  const entry = entries.find((item) => item.id === entryId)

  if (!entry) {
    return (
      <section className="empty-state detail-empty">
        <h1>Entry not found</h1>
        <p>It may have been cleared when this preview was refreshed.</p>
        <Link className="button button-primary" to="/owner/entries">Back to entries</Link>
      </section>
    )
  }

  return (
    <>
      <PageHeader
        eyebrow="DIARY ENTRY"
        title={entry.title}
        description={`Created ${entry.date} · ${entry.writingMode} mode`}
        action={<Link className="button button-secondary" to="/owner/entries">← All entries</Link>}
      />
      <article className="panel entry-detail">
        <div className="entry-detail-meta">
          <StatusBadge
            label={entry.visibility}
            tone={visibilityTone(entry.visibility)}
          />
          <span>Sample entry · Owner view</span>
        </div>
        <div className="entry-detail-content">{entry.content}</div>
        <div className="entry-detail-footer">
          <span>Original text</span>
          <span>Writing mode: {entry.writingMode}</span>
        </div>
      </article>
      <p className="inline-notice">
        This entry is sample data held in memory only. Visibility is not enforced by this frontend.
      </p>
    </>
  )
}
