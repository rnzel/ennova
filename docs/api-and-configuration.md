# ENNOVA API and Configuration Reference

## REST endpoints

All endpoints are defined by the Flask routes in `backend/app/routes/`, except `/health`, which is registered by the application factory in `backend/app/__init__.py`.

| Method | Path | Purpose | Authentication |
|---|---|---|---|
| GET | `/health` | Report application health | None |
| POST | `/auth/register-owner` | Register an owner account | None |
| POST | `/auth/login` | Authenticate and issue a bearer token | None |
| POST | `/auth/register-beneficiary` | Redeem an invitation and register a beneficiary | None |
| POST | `/invitations` | Issue a beneficiary invitation | Owner bearer token |
| POST | `/entries` | Create a diary or letter entry | Owner bearer token |
| GET | `/entries` | List the owner's entries | Owner bearer token |
| PUT | `/policy` | Parse and activate policy text | Owner bearer token |
| POST | `/death-trigger` | Trigger the death state and freeze policy | Owner bearer token |
| POST | `/ask` | Ask a grounded question | Any bearer token |
| POST | `/owner/ask` | Ask a grounded question about the authenticated owner's diary | Owner bearer token |

### Owner AI Chatbot

`POST /owner/ask` accepts a natural-language question. The backend derives the owner identity from the validated bearer token; clients must not supply an owner ID. A server-issued `conversation_id` may be sent for a follow-up. The server keeps only recent user questions as context, bound to that owner; assistant messages are never accepted from the client as evidence.

Request:

```json
{
  "question": "What did I write about my first day at university?"
}
```

On follow-up requests, include the `conversation_id` returned for this conversation. The following illustrative response shows the shape; the answer and entry are fictional:

```json
{
  "answer": "You recorded that your first day felt exciting.",
  "no_record": false,
  "conversation_id": "32-character-server-issued-id",
  "citations": [{ "entry_id": "entry-1", "date": "2040-04-30" }]
}
```

When retrieval finds no supporting entry, the endpoint returns HTTP 200 with `no_record: true`, the fixed no-support answer, and an empty citations array. Citation IDs returned by the model are filtered against the exact entries supplied to it, and citation dates come from stored entry timestamps. Requests are limited to 2,000 characters and 20 per minute per account. The endpoint returns safe 401/403 responses for missing/invalid authentication and non-owner accounts, 400 for invalid input or a conversation that is missing or belongs to another owner, and 503 when the model is unavailable.

Conversation follow-up context is stored in SQL as at most four prior user questions per owner-bound conversation. Diary records are loaded and hash-verified again on every request. There is no conversation listing API; the client must retain the returned opaque ID. Owner retrieval uses local lexical ranking, metadata and date cues with a small synonym expansion; it does not use embeddings or an external vector database. A broad paraphrase may therefore miss an entry.

Beneficiary `POST /ask` remains a separate workflow. It resolves the owner's policy through Prolog before permitted record views reach its model context; the owner endpoint does not modify that authorization path.

Letter responses include a `disclaimer` field:
`Letters of Wishes in ENNOVA are personal messages and are not legal wills or substitutes for legally executed estate documents. ENNOVA does not provide legal advice.`

The disclaimer appears for letter creation/listing, released-letter answers, and pre-release letter-date answers. It does not appear in diary entries or neutral denied/no-record answers.

## Durable application data

The production factory uses the configured SQLAlchemy database for append-only diary and letter entries, ordered name/topic metadata, policy source versions, the irreversible death-trigger state, audit events, digest-bound derived summaries, and owner chatbot follow-up questions. The hash chain stores both the database timestamp and the exact original ISO timestamp string used in the digest. Prolog facts and parsed policy ASTs are rebuilt from persisted entries and policy source. Beneficiary Q&A remains stateless and re-evaluates current Prolog policy on every question. No upload route or document storage exists, so no file store is configured.

The new migration is forward-only to protect diary and audit data. From `backend/`, apply locally with `flask --app run db upgrade`; for deployment, back up the database, verify the target and migration plan, and run the same command in the deployment environment. Verify with `flask --app run db current`. Recovery requires restoring a consistent database backup; backups must be encrypted, access-restricted, and retention-controlled. This repository does not supply an automated backup policy.

## Environment variables

Defaults below are the application's defaults in `backend/app/config.py`, unless noted otherwise. `backend/.env.example` also supplies example values for the variables marked as template-only.

| Variable | Purpose | Default | Required |
|---|---|---|---|
| `FLASK_APP` | Flask CLI application target | `run.py` in `.env.example` | No |
| `FLASK_ENV` | Example environment setting | `development` in `.env.example`; not read by the Python configuration | No |
| `SECRET_KEY` | Flask secret key | `change-me` | No; replace for deployment |
| `JWT_SECRET_KEY` | JWT signing key | None | Yes for authentication; must be at least 32 bytes |
| `APP_TIMEZONE` | Time zone used to derive the Prolog date | `UTC` | No |
| `MAX_CONTENT_LENGTH` | Maximum request body size in bytes | `1048576` | No |
| `DATABASE_URL` | SQLAlchemy database URL | `sqlite:///ennova.db` | No; set to use MySQL |
| `AIVEN_CA_PATH` | Aiven MySQL CA certificate path | Empty | Required for CA-verified Aiven TLS |
| `SWIPL_EXECUTABLE` | SWI-Prolog executable or path | `swipl` | Required to evaluate Prolog access rules |
| `LLM_PROVIDER` | Select `groq` or `fake` | None | Required to select an AI provider |
| `GROQ_API_KEY` | Backend-only Groq API key | None | Required when `LLM_PROVIDER=groq` |
| `GROQ_MODEL` | Groq inference model ID | `openai/gpt-oss-120b` | No |
| `GROQ_QUESTION_TIMEOUT_SECONDS` | Total Groq question deadline | `45` | No |
| `RUN_LIVE_AI_TESTS` | Enable live-provider tests when set to `1` | `0` in `.env.example` | No |

`FLASK_ENV` is present in `.env.example` but is not read by the Python configuration. Groq configuration is provider-specific. Select `LLM_PROVIDER=groq` with a server-side key or `LLM_PROVIDER=fake` for deterministic tests/demos. No provider silently falls back to another. Groq is a hosted service: diary evidence included in prompts is transmitted to Groq. Keep keys out of source control and the mobile client. Availability and quotas depend on the model and Groq organization plan; check the current organization Limits page rather than assuming a free-tier allowance.