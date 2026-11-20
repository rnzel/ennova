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
