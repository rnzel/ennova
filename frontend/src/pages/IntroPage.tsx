import { Link } from 'react-router-dom'
import { Brand } from '../components/Brand'

export function IntroPage() {
  return (
    <main className="intro-page">
      <Brand />
      <section className="intro-content">
        <p className="eyebrow">A private place for your story</p>
        <h1>Keep your memories yours.</h1>
        <p>
          Write privately, decide what may be shared, and leave clear guidance for the people who
          matter to you.
        </p>
        <Link className="button button-primary intro-get-started" to="/login">
          Get started <span aria-hidden="true">→</span>
        </Link>
      </section>
      <div className="intro-promise">
        <span className="promise-icon">01</span>
        <span>Privacy and access rules belong to the owner.</span>
      </div>
    </main>
  )
}
