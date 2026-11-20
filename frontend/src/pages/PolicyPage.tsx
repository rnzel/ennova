import { useState, type FormEvent } from 'react'
import { useAppData } from '../app/useAppData'
import { PageHeader } from '../components/PageHeader'

export function PolicyPage() {
  const { policyText, setPolicyText } = useAppData()
  const [draft, setDraft] = useState(policyText)
  const [notice, setNotice] = useState('')

  const saveDraft = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setPolicyText(draft)
    setNotice('Policy draft kept in this preview session only. No rules were evaluated.')
  }

  return (
    <>
      <PageHeader
        eyebrow="ACCESS CONTROL"
        title="Your access policy"
        description="Review a sample policy written in ENNOVA's policy language."
      />

      <section className="policy-summary">
        <div className="policy-summary-icon" aria-hidden="true">◎</div>
        <div>
          <strong>Access should be explicit.</strong>
          <p>In the full application, backend authorization—not this screen—decides what a person can see.</p>
        </div>
        <span className="badge badge-neutral">Sample policy</span>
      </section>

      <form className="panel policy-editor" onSubmit={saveDraft}>
        <div className="panel-heading">
          <div>
            <p className="eyebrow">POLICY SOURCE</p>
            <h2>Policy draft</h2>
          </div>
          <span className="subtle-label">Language design preview</span>
        </div>
        <label className="visually-hidden" htmlFor="policy-source">Policy source code</label>
        <textarea
          id="policy-source"
          className="policy-textarea"
          spellCheck={false}
          value={draft}
          onChange={(event) => {
            setDraft(event.target.value)
            setNotice('')
          }}
          rows={12}
        />
        <div className="policy-editor-footer">
          <p>Editing and saving here does not validate or activate the policy.</p>
          <button className="button button-primary" type="submit">Save preview draft</button>
        </div>
        {notice && <p className="inline-notice" role="status">{notice}</p>}
      </form>

      <section className="policy-concepts">
        <article className="concept-card">
          <span className="concept-number">01</span>
          <h3>May see</h3>
          <p>Allows a beneficiary to know an entry exists, without granting its contents.</p>
        </article>
        <article className="concept-card">
          <span className="concept-number">02</span>
          <h3>May read</h3>
          <p>Defines the level of content that can be shared, such as a summary or full text.</p>
        </article>
        <article className="concept-card">
          <span className="concept-number">03</span>
          <h3>Release letter</h3>
          <p>Describes a recipient and a date condition for a letter.</p>
        </article>
      </section>
    </>
  )
}
