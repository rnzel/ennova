# ENNOVA Policy-to-Prolog Fact Mapping

Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator

The F4 interpreter emits one fact string for every statement written, in source
order. Statements inside protocol blocks are emitted at the position of that
block. Repeated protocol blocks are emitted independently and are not merged.
Every fact ends with a period.

| Policy statement | Prolog fact |
|---|---|
| `may see existence of entries mentioning <name>` in `protocol <person>:` | `grant(Person, existence, mentioning(Name)).` |
| `may read summary of entries tagged "<tag>"` in a protocol | `grant(Person, summary, tagged(Tag)).` |
| `may read verbatim of ...` in a protocol | `grant(Person, verbatim, Selector).` |
| `may not see existence of ...` in a protocol | `deny(Person, existence, Selector).` |
| `may not read summary of ...` in a protocol | `deny(Person, summary, Selector).` |
| `may not read verbatim of ...` in a protocol | `deny(Person, verbatim, Selector).` |
| `release letter "<title>" to <person> when date >= YYYY-MM-DD` | `release(Person, 'Title', date(Y,M,D)).` |
| `trustee is <person>` | `trustee(Person).` |
| `transfer custody to <person> if trustee unavailable for N days` | `custody_rule(Person, trustee_unavailable, N).` |
| `default writing mode: <mode>` | `default_mode(Mode).` |

`Person`, `Name`, and `Mode` come from lowercase bare identifiers and are
emitted as lowercase atoms. A selector is `mentioning(Name)` or `tagged(Tag)`.
Tags are case-folded before emission; `Family` becomes `family`, matching F2's
case-folded topic extraction. Tags that are not plain lowercase atoms are
single-quoted and escaped. Letter titles keep their case and are always
single-quoted. String/atom escaping is centralized; policy text is never
interpolated raw into a fact.

F4 does not infer grants, hierarchy, deny precedence, registration, or death
trigger facts. Those decisions belong to the Prolog rules in F5.
