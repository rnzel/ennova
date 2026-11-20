import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAppData } from '../app/useAppData'
import { PageHeader } from '../components/PageHeader'
import type { EntryVisibility, WritingMode } from '../types'

export function EntryEditorPage() {
  const [title, setTitle] = useState('')
  const [content, setContent] = useState('')
  const [visibility, setVisibility] = useState<EntryVisibility>('Private')
  const [writingMode, setWritingMode] = useState<WritingMode>('Verbatim')
  const { addEntry } = useAppData()
  const navigate = useNavigate()

  const saveEntry = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const trimmedContent = content.trim()
    addEntry({
      title: title.trim(),
      content: trimmedContent,
      summary: trimmedContent.slice(0, 150) || 'A new diary entry.',
      visibility,
      writingMode,
    })
    navigate('/owner/entries')
  }

  return (
    <>
      <PageHeader
        eyebrow="NEW JOURNAL ENTRY"
        title="Capture a moment."
        description="Your original words stay unchanged. Choose how this entry should be handled."
      />

      <form className="editor-layout" onSubmit={saveEntry}>
        <section className="panel editor-panel">
          <label className="field-label">
            Entry title
            <input
              className="text-input title-input"
              value={title}
              onChange={(event) => setTitle(event.target.value)}
              placeholder="Give this memory a name"
              maxLength={120}
              required
            />
          </label>
          <label className="field-label">
            Your entry
            <textarea
              className="text-input entry-textarea"
              value={content}
              onChange={(event) => setContent(event.target.value)}
              placeholder="Write freely. This is sample-only data and stays in memory while this page is open."
              rows={12}
              required
            />
          </label>
          <div className="editor-count">{content.length} characters</div>
          <div className="editor-actions">
            <Link className="button button-secondary" to="/owner/entries">Cancel</Link>
            <button className="button button-primary" type="submit">Save preview entry</button>
          </div>
        </section>

        <aside className="panel editor-options">
          <p className="eyebrow">ENTRY OPTIONS</p>
          <label className="field-label">
            Visibility label
            <select
              className="text-input"
              value={visibility}
              onChange={(event) => setVisibility(event.target.value as EntryVisibility)}
            >
              <option>Private</option>
              <option>Shared</option>
              <option>Restricted</option>
            </select>
          </label>
          <p className="field-help">
            A label in this prototype only. It does not grant or block access.
          </p>
          <label className="field-label">
            Writing mode
            <select
              className="text-input"
              value={writingMode}
              onChange={(event) => setWritingMode(event.target.value as WritingMode)}
            >
              <option>Verbatim</option>
              <option>Light fix</option>
              <option>Review</option>
            </select>
          </label>
          <p className="field-help">
            Writing modes are a visual selection only; text processing is not connected.
          </p>
          <div className="editor-safety-note">
            <strong>Prototype safety</strong>
            <span>Use fictional text only. Preview entries are held in memory and disappear when you refresh.</span>
          </div>
        </aside>
      </form>
    </>
  )
}
