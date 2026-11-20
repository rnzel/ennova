import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAppData } from '../app/useAppData'
import { PageHeader } from '../components/PageHeader'
import { StatusBadge } from '../components/StatusBadge'
import type { EntryVisibility } from '../types'
import { visibilityTone } from '../lib/visibility'

const filters: Array<'All entries' | EntryVisibility> = [
  'All entries',
  'Private',
  'Shared',
  'Restricted',
]

export function EntriesPage() {
  const { entries } = useAppData()
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<(typeof filters)[number]>('All entries')

  const visibleEntries = useMemo(
    () =>
      entries.filter((entry) => {
        const matchesFilter = filter === 'All entries' || entry.visibility === filter
        const searchText = `${entry.title} ${entry.summary}`.toLowerCase()
        return matchesFilter && searchText.includes(query.toLowerCase())
      }),
    [entries, filter, query],
  )

  return (
    <>
      <PageHeader
        eyebrow="YOUR JOURNAL"
        title="Diary entries"
        description="A private collection of memories, notes, and letters."
        action={
          <Link className="button button-primary" to="/owner/entries/new">
            <span aria-hidden="true">＋</span> New entry
          </Link>
        }
      />

      <section className="panel entries-panel">
        <div className="entries-toolbar">
          <label className="search-field">
            <span className="search-icon" aria-hidden="true">⌕</span>
            <span className="visually-hidden">Search entries</span>
            <input
              type="search"
              value={query}
              onChange={(event) => setQuery(event.target.value)}
              placeholder="Search your journal"
            />
          </label>
          <div className="filter-tabs" aria-label="Filter entries">
            {filters.map((item) => (
              <button
                type="button"
                key={item}
                className={`filter-tab ${filter === item ? 'filter-tab-active' : ''}`}
                aria-pressed={filter === item}
                onClick={() => setFilter(item)}
              >
                {item}
              </button>
            ))}
          </div>
        </div>

        <div className="entry-grid">
          {visibleEntries.map((entry) => (
            <article className="entry-tile" key={entry.id}>
              <div className="entry-tile-top">
                <StatusBadge
                  label={entry.visibility}
                  tone={visibilityTone(entry.visibility)}
                />
                <span>{entry.date}</span>
              </div>
              <h2>{entry.title}</h2>
              <p>{entry.summary}</p>
              <div className="entry-tile-bottom">
                <span>{entry.writingMode} mode</span>
                <Link to={`/owner/entries/${entry.id}`} aria-label={`Open ${entry.title}`}>
                  Read entry <span aria-hidden="true">→</span>
                </Link>
              </div>
            </article>
          ))}
          {visibleEntries.length === 0 && (
            <div className="empty-state">
              <span className="empty-state-mark">⌕</span>
              <h2>No entries found</h2>
              <p>Try a different search or visibility filter.</p>
            </div>
          )}
        </div>
      </section>
    </>
  )
}
