import { useState, type FormEvent } from 'react'
import { PageHeader } from '../components/PageHeader'

export function QAPage() {
  const [question, setQuestion] = useState('')
  const [submitted, setSubmitted] = useState(false)

  const submitQuestion = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setSubmitted(true)
  }

  return (
    <>
      <PageHeader
        eyebrow="GROUNDED Q&A"
        title="Ask about your memories."
        description="A future ENNOVA assistant will answer from material you are authorized to access."
      />

      <section className="qa-layout">
        <div className="panel qa-panel">
          <div className="qa-orb" aria-hidden="true">E</div>
          <p className="eyebrow">ENNOVA ASSISTANT</p>
          <h2>A thoughtful answer starts with permission.</h2>
          <p className="muted">
            The real service will check access before searching. This prototype does not search entries
            or call an AI model.
          </p>

          <form className="qa-form" onSubmit={submitQuestion}>
            <label className="visually-hidden" htmlFor="qa-question">Ask a question</label>
            <textarea
              id="qa-question"
              className="text-input"
              value={question}
              onChange={(event) => {
                setQuestion(event.target.value)
                setSubmitted(false)
              }}
              placeholder="What would you like to ask?"
              rows={3}
              required
            />
            <button type="submit" className="button button-primary" disabled={!question.trim()}>
              Preview question <span aria-hidden="true">→</span>
            </button>
          </form>

          {submitted && (
            <div className="qa-response" role="status">
              <strong>Preview only</strong>
              <p>Your question was not sent or searched. Connect an authorized backend before enabling answers.</p>
            </div>
          )}
        </div>

        <aside className="qa-side">
          <p className="eyebrow">PRIVACY BY DESIGN</p>
          <h2>What happens before an answer?</h2>
          <ol className="qa-steps">
            <li><span>1</span><p><strong>Check permissions</strong><small>Resolve access before retrieval.</small></p></li>
            <li><span>2</span><p><strong>Find permitted material</strong><small>Only allowed entries can be considered.</small></p></li>
            <li><span>3</span><p><strong>Ground the reply</strong><small>Use verified references and dates.</small></p></li>
          </ol>
        </aside>
      </section>
    </>
  )
}
