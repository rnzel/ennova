import { useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { Brand } from './Brand'

const navigation = [
  { label: 'Overview', to: '/owner', end: true },
  { label: 'Diary entries', to: '/owner/entries' },
  { label: 'Beneficiaries', to: '/owner/beneficiaries' },
  { label: 'Access policy', to: '/owner/policy' },
  { label: 'Ask ENNOVA', to: '/owner/ask' },
  { label: 'Settings', to: '/owner/settings' },
]

export function OwnerLayout() {
  const [menuOpen, setMenuOpen] = useState(false)
  const navigate = useNavigate()

  const leavePreview = () => navigate('/login')

  return (
    <div className="dashboard-shell">
      <aside className={`sidebar ${menuOpen ? 'sidebar-open' : ''}`}>
        <Link to="/owner" className="sidebar-brand" aria-label="ENNOVA dashboard">
          <Brand />
        </Link>

        <p className="nav-caption">WORKSPACE</p>
        <nav className="side-nav" aria-label="Owner navigation">
          {navigation.map((item, index) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={'end' in item ? item.end : false}
              className={({ isActive }) => `nav-link ${isActive ? 'nav-link-active' : ''}`}
              onClick={() => setMenuOpen(false)}
            >
              <span className="nav-index">{String(index + 1).padStart(2, '0')}</span>
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="sidebar-bottom">
          <Link to="/beneficiary" className="beneficiary-preview-link">
            Beneficiary preview <span aria-hidden="true">↗</span>
          </Link>
          <div className="owner-profile">
            <span className="avatar">O</span>
            <span>
              <strong>Diary owner</strong>
              <small>Preview account</small>
            </span>
            <button type="button" className="icon-button" onClick={leavePreview} aria-label="Sign out">
              ↪
            </button>
          </div>
        </div>
      </aside>

      <div className="workspace">
        <header className="workspace-header">
          <button
            className="menu-toggle"
            type="button"
            aria-expanded={menuOpen}
            aria-label={menuOpen ? 'Close navigation menu' : 'Open navigation menu'}
            onClick={() => setMenuOpen((open) => !open)}
          >
            <span />
            <span />
            <span />
          </button>
          <div className="workspace-status">
            <span className="status-dot" />
            Frontend preview · sample data only
          </div>
          <Link to="/owner/settings" className="header-account">
            <span className="avatar avatar-small">O</span>
            <span>Owner</span>
          </Link>
        </header>

        <main className="page-content">
          <Outlet />
        </main>
        <footer className="workspace-footer">
          ENNOVA frontend prototype <span>·</span> Sample data stays in this browser session.
        </footer>
      </div>

      {menuOpen && (
        <button
          className="sidebar-backdrop"
          type="button"
          aria-label="Close navigation menu"
          onClick={() => setMenuOpen(false)}
        />
      )}
    </div>
  )
}
