import { useState, type FormEvent } from 'react'
import { PageHeader } from '../components/PageHeader'

export function SettingsPage() {
  const [displayName, setDisplayName] = useState('Diary Owner')
  const [email, setEmail] = useState('owner@example.test')
  const [notice, setNotice] = useState('')

  const saveSettings = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setNotice('Settings updated in this page preview only.')
  }

  return (
    <>
      <PageHeader
        eyebrow="PREFERENCES"
        title="Settings"
        description="Manage the account and experience preferences shown in this prototype."
      />

      <div className="settings-layout">
        <nav className="settings-nav" aria-label="Settings sections">
          <a className="settings-nav-active" href="#profile">Profile</a>
          <a href="#privacy">Privacy</a>
          <a href="#experience">Experience</a>
        </nav>

        <div className="settings-content">
          <form className="panel settings-card" id="profile" onSubmit={saveSettings}>
            <div className="panel-heading">
              <div><p className="eyebrow">ACCOUNT</p><h2>Profile</h2></div>
              <span className="avatar avatar-large">O</span>
            </div>
            <label className="field-label">
              Display name
              <input className="text-input" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
            </label>
            <label className="field-label">
              Email address
              <input className="text-input" type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
            </label>
            <div className="settings-footer">
              <span>Preview data only</span>
              <button className="button button-primary" type="submit">Save preview settings</button>
            </div>
            {notice && <p className="inline-notice" role="status">{notice}</p>}
          </form>

          <section className="panel settings-card" id="privacy">
            <p className="eyebrow">DATA & ACCESS</p>
            <h2>Privacy</h2>
            <p className="settings-description">Access and retention controls are planned here. They are not active in this UI prototype.</p>
            <div className="setting-row">
              <span><strong>Owner-controlled access</strong><small>Beneficiary permissions are defined by the owner policy.</small></span>
              <span className="badge badge-neutral">Backend controlled</span>
            </div>
            <div className="setting-row">
              <span><strong>Diary storage</strong><small>Entries created in this preview are not persisted.</small></span>
              <span className="badge badge-neutral">Session only</span>
            </div>
          </section>

          <section className="panel settings-card" id="experience">
            <p className="eyebrow">EXPERIENCE</p>
            <h2>Writing preferences</h2>
            <label className="field-label">
              Default writing mode
              <select className="text-input" defaultValue="Verbatim">
                <option>Verbatim</option>
                <option>Light fix</option>
                <option>Review</option>
              </select>
            </label>
            <p className="field-help">This is a non-persistent display preference in the prototype.</p>
          </section>
        </div>
      </div>
    </>
  )
}
