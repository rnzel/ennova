import { useState, type FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export function LoginPage() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const navigate = useNavigate()

  const openOwnerPreview = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    navigate('/owner')
  }

  return (
    <main className="login-page">
      <section className="login-panel">
        <div className="login-form-wrap">
          <p className="eyebrow">OWNER WORKSPACE</p>
          <h2>Welcome to ENNOVA</h2>
          <p className="muted">Continue to the owner workspace preview.</p>

          <div className="prototype-notice" role="note">
            This is a frontend prototype. Sign-in is simulated; do not enter a real password or
            personal information.
          </div>

          <form className="form-stack" onSubmit={openOwnerPreview}>
            <label>
              Email address
              <input
                type="email"
                autoComplete="email"
                placeholder="you@example.test"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </label>
            <label>
              Password
              <input
                type="password"
                autoComplete="current-password"
                placeholder="Enter a sample password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </label>
            <button className="button button-primary button-wide" type="submit">
              Continue to preview <span aria-hidden="true">→</span>
            </button>
          </form>

          <div className="login-divider"><span>OR</span></div>
          <Link className="button button-secondary button-wide" to="/beneficiary">
            Open beneficiary preview <span aria-hidden="true">↗</span>
          </Link>
          <p className="login-footnote">
            No data is sent to a server. Preview changes are temporary.
          </p>
          <Link className="text-link login-back-link" to="/">
            <span aria-hidden="true">←</span> Back to intro
          </Link>
        </div>
      </section>
    </main>
  )
}
