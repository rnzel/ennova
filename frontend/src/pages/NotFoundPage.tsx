import { Link } from 'react-router-dom'

export function NotFoundPage() {
  return (
    <main className="not-found-page">
      <span className="not-found-code">404</span>
      <h1>This page is not in the preview.</h1>
      <p>Use the link below to return to the ENNOVA sign-in screen.</p>
      <Link to="/login" className="button button-primary">Back to sign in</Link>
    </main>
  )
}
