# ENNOVA AI Design Note

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

## Model

ENNOVA selects its model client through configuration in `LLM_PROVIDER`. The only accepted values are `ollama` and `fake`; an unset or invalid value fails closed with `AIServiceUnavailable`. `fake` selects the deterministic `FakeModelClient` for tests and scripted demos. It is an explicit provider choice, not an automatic fallback when Ollama fails.

The Ollama client uses the `/api/chat` endpoint through Python's standard-library HTTP client. `OLLAMA_HOST` defaults to `http://localhost:11434`; other hosts require `OLLAMA_ALLOW_REMOTE=1`. The model name is configured through `OLLAMA_MODEL`. The Groq adapter uses the official Groq Python SDK and the backend-only `GROQ_API_KEY`; its model is selected with `GROQ_MODEL`, defaulting to `openai/gpt-oss-120b`. Both adapters implement the same `ModelClient` interface and can serve beneficiary Q&A, owner Q&A, and model-backed summary generation. `fake` remains a deterministic test/demo provider. Provider selection never falls back silently.

Requests bypass system proxies, do not follow redirects, and enforce configured context, output, response-size, per-request timeout, and total-question-deadline limits. Request and question timeout settings have safe defaults and hard upper bounds. Prompt sizing fails closed rather than dropping the system prompt or allowing truncation. Responses use Ollama's structured JSON option and are rejected if they do not match the exact answer schema.

Groq calls use a bounded request timeout and strict response validation. Owner requests use Groq JSON Schema output. Beneficiary requests use Groq's local tool-calling interface and then the application's existing bounded orchestration; app-generated tool evidence is sent as untrusted user content on the next call because the existing `ModelPrompt` abstraction does not retain provider-specific tool-call IDs. The adapter does not grant Groq access to ENNOVA storage or execute tools itself. Groq documents that tool use and structured outputs cannot be combined in one request, so the two request modes are kept separate.

The provider-neutral `ModelSummarizer` accepts any `ModelClient`. It frames original entries as escaped, delimited untrusted data and retries once if the summary contains eight consecutive words copied from the original. A repeated overlap or provider failure stores no summary. Successful summaries are separate from the append-only hash chain and bound to the source entry digest; retrieval omits summaries whose digest no longer matches.

With the default host, Ollama keeps model processing on the local service; a remote host is possible only with the explicit `OLLAMA_ALLOW_REMOTE=1` setting. Model quality, latency, and availability depend on the chosen model and machine. Summary quality may vary; the eight-word check does not guarantee factual accuracy or paraphrase quality.

## Tools

For beneficiary Q&A, the model receives schemas for four implemented tools: `search_entries`, `get_entry`, `count_mentions`, and `get_letter`. It receives schemas, not Python callables. Tool-call proposals return to the application, which executes only these allowlisted functions; unknown tools and malformed arguments are ignored. The asker is fixed in `ToolContext` so a model tool request cannot choose another identity.

The Q&A service first enumerates the owner's candidate entries to build access requests. It then asks Prolog for per-entry, per-level decisions in a batch. The resulting `ToolContext` contains candidate records together with the permission map and verified-entry IDs. Each tool enforces permission and verification before constructing a content view, scoring or counting a record, or returning content. `search_entries` scores verified summary- or verbatim-permitted views; `get_entry` returns a verified view at the allowed level; `count_mentions` counts only verified permitted records; and `get_letter` returns a released, permitted letter or a backend-generated safe status. Denied content is not returned as a Q&A tool result or included in a model prompt. The candidate enumeration happens before Prolog checks, so “before retrieval” refers to content retrieval through Q&A tools, not the initial owner-scoped listing. The tool context itself still contains candidate record objects; tools apply the permission filter internally.

**Separate write-time summary path:** When the owner creates an entry, the route may pass its newly stored `StoredEntry` to `ModelSummarizer`. That application-mediated model call receives the original entry text in an untrusted-data block to create a derived summary. It does not use the beneficiary Q&A tool flow or Prolog permission checks. The stored summary is digest-bound and is supplied in beneficiary Q&A only when that entry has summary permission. This write-time path is distinct from permission-checked Q&A retrieval.

The model has no direct connection or credentials for the vault, database, or entry repository. All model input is passed by the application through `ModelClient` prompts: Q&A content comes from permission-filtered tools after Prolog decisions, while write-time summary input comes from the owner entry-creation path described above. The model does not make access decisions. With Groq, diary evidence is sent to Groq's hosted inference API; deployments should disclose this external processing and confirm it meets their privacy, retention, and jurisdiction requirements. `GROQ_API_KEY` stays on the backend and must never be placed in the Expo app.

The backend verifies citation IDs against entries actually presented to the model and attaches their stored dates. The model returns entry IDs rather than dates. Existence-only counts, release-date notices, and neutral no-record responses are constructed by the backend.

**Owner-specific workflow:** `OwnerGroundedQAService` receives the `owner_id` from the authenticated owner account at the route boundary, enumerates only that owner's `DiaryService` records, verifies each entry's stored hash, and discards invalid records. The local `search_owner_entries` tool ranks verified text using question terms, a small synonym expansion, extracted names and topics, and explicit or relative year cues. It returns at most six full entry views. No entry content is loaded from a client-supplied identifier, and the model never gets database credentials or an unrestricted repository handle. If retrieval returns no matching entries, the backend returns a fixed no-support answer without calling the model.

The owner service uses the same configured `ModelClient` but has its own prompt and retrieval context. It does not create beneficiary policy facts or call Prolog: an authenticated owner may read their own verified records. `attach_citations` is reused to validate model-proposed IDs against only the retrieved entries and take dates from their stored timestamps. If the model supplies no valid citation, the service returns the fixed no-support answer.

In production, follow-up context is held by `SQLAlchemyOwnerConversationStore`. The client receives an opaque ID and sends it back with follow-up questions; it does not submit transcript messages or an owner ID. The database associates each ID with the authenticated owner and keeps only the four latest questions (not assistant answers). The current account is checked for each resumed ID. Diary evidence is retrieved and hash-verified again on every question, and beneficiary Q&A has no conversation reuse. Test/demo configurations can inject the in-memory store.

## Instructions

Beneficiary Ollama Q&A receives the existing `SYSTEM_PROMPT` as a system-role message and the question as a user-role message. It is instructed to answer only from permitted material supplied in the conversation, return citation entry IDs rather than dates, never claim to be the diary owner, say when permitted material contains no answer, and treat entry and summary blocks as untrusted data rather than instructions. Q&A tool results are placed in escaped, delimited blocks. The backend attaches verified dates to accepted citation IDs. The owner's policy text is not sent to the beneficiary Q&A model; Prolog resolves permissions in the application.

Owner Q&A uses `OWNER_SYSTEM_PROMPT`. It instructs the model to act as the owner's diary assistant, use only application-supplied records, state when the records do not support an answer, avoid inventing memories or dates, distinguish recorded facts (for example, “You recorded…”) from interpretation (for example, “A possible interpretation is…”), cite exact entry IDs, never claim to be the owner, and treat `<untrusted_entry>` blocks as data rather than instructions. Previous user questions are context for follow-ups only and are explicitly not evidence. Entry dates appear inside the untrusted record block so the model can reason about chronology; the response cites IDs only, and the backend supplies trusted citation dates.

Beneficiary denied and nonexistent records follow the same neutral response path, and no model call is made when no permitted material is available. Owner Q&A has its own fixed no-support response and does not reveal any other owner's records. The two paths have separate routes and retrieval contexts; adding owner retrieval does not alter Prolog decisions or beneficiary model inputs.

## What fake and mocked tests do not prove

Fake-model and mocked-transport tests verify application behavior, request construction, strict response parsing, timeout and response-size limits, host restrictions, error redaction, owner isolation, citation filtering, data-flow restrictions, and fail-closed handling. They do **not** prove that a live Ollama model will follow instructions, return valid structured output, produce accurate answers or summaries, resist every prompt injection, or meet real hardware latency and availability targets. Backend permission checks, citation filtering, and fixed no-support responses enforce application behavior; the prompt alone is not an authorization boundary. The eight-word check detects only one kind of close copying.

Owner retrieval is lexical with date/metadata cues and a small synonym set, not semantic embeddings. It may miss paraphrases that share no useful terms. Production diary entries, policy source versions, lifecycle state, audit events, digest-bound summaries, and owner follow-up questions use SQL persistence. Parsed policy objects and Prolog facts are regenerated. The mobile transcript display is client state and there is no server conversation-list endpoint.

The live Ollama safety test runs only when `RUN_LIVE_AI_TESTS=1`, uses fictional text, and checks safety properties such as citation allowlisting and not claiming to be the owner. It is not part of the normal offline suite and does not establish comprehensive model safety. Groq unit tests mock the SDK and do not make a live Groq request or establish account quota.

## What we would change

Live Ollama (`llama3.2:3b`, CPU-only) rows time out on slow hardware. Measurements show the small model sends invalid tool arguments and repeats them until the deadline; this is a model-quality and latency limitation, not an authorization failure. The two backend-built rows (release-date message and neutral reply) work live. If time allows, we would answer count and date questions directly in the backend, stop on repeated invalid calls, or try a larger model.

## Official references

- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
- [Groq supported models](https://console.groq.com/docs/models)
- [Groq tool use](https://console.groq.com/docs/tool-use/overview)
- [Groq structured outputs](https://console.groq.com/docs/structured-outputs)
- [Groq rate limits](https://console.groq.com/docs/rate-limits)
