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

When retrieval finds no supporting entry, the endpoint returns HTTP 200 with `no_record: true`, the fixed no-support answer, and an empty citations array. Citation IDs returned by the model are filtered against the exact entries supplied to it, and citation dates come from stored entry timestamps. Requests are limited to 2,000 characters and 20 per minute per account. The endpoint returns safe 401/403 responses for missing/invalid authentication and non-owner accounts, 400 for invalid input or a conversation that is missing, expired, or belongs to another owner, and 503 when the model is unavailable.

Conversation context is process-local: it keeps at most four prior questions per conversation, expires after 30 minutes of inactivity, and is lost when the backend process restarts. Diary entries are also held by the current in-memory entry repository and are not durable across restarts. Owner retrieval uses local lexical ranking, metadata and date cues with a small synonym expansion; it does not use embeddings or an external vector database. A broad paraphrase may therefore miss an entry.

Beneficiary `POST /ask` remains a separate workflow. It resolves the owner's policy through Prolog before permitted record views reach its model context; the owner endpoint does not modify that authorization path.

Letter responses include a `disclaimer` field:
`Letters of Wishes in ENNOVA are personal messages and are not legal wills or substitutes for legally executed estate documents. ENNOVA does not provide legal advice.`

The disclaimer appears for letter creation/listing, released-letter answers, and pre-release letter-date answers. It does not appear in diary entries or neutral denied/no-record answers.

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
| `LLM_PROVIDER` | Select `ollama` or `fake` | None | Required to select an AI provider |
| `OLLAMA_HOST` | Ollama server host | `http://localhost:11434` | No |
| `OLLAMA_MODEL` | Ollama model name | None | Required when `LLM_PROVIDER=ollama` |
| `OLLAMA_ALLOW_REMOTE` | Opt in to a non-loopback Ollama host | `0` | No |
| `OLLAMA_NUM_CTX` | Ollama context size | `8192` | No |
| `OLLAMA_MAX_OUTPUT_TOKENS` | Maximum Ollama output tokens | `512` | No |
| `OLLAMA_REQUEST_TIMEOUT_SECONDS` | Per-request timeout | `30` | No |
| `OLLAMA_QUESTION_TIMEOUT_SECONDS` | Overall question deadline | `45` | No |
| `OLLAMA_CONNECT_TIMEOUT_SECONDS` | Connection timeout | `15` | No |
| `OLLAMA_READ_TIMEOUT_SECONDS` | Response read timeout | `30` | No |
| `OLLAMA_MAX_RESPONSE_BYTES` | Maximum Ollama response size | `1048576` | No |
| `RUN_LIVE_AI_TESTS` | Enable live-provider tests when set to `1` | `0` in `.env.example` | No |

`FLASK_ENV` is present in `.env.example` but is not read by the Python configuration. Ollama-specific variables apply when using the Ollama provider. The application can start without an AI provider, but model-backed Q&A is unavailable in that case.
