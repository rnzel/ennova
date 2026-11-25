# ENNOVA AI Design Note

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

## Model

ENNOVA selects its model client through configuration in `LLM_PROVIDER`. The only accepted values are `ollama` and `fake`; an unset or invalid value fails closed with `AIServiceUnavailable`. `fake` selects the deterministic `FakeModelClient` for tests and scripted demos. It is an explicit provider choice, not an automatic fallback when Ollama fails.

The Ollama client uses the `/api/chat` endpoint through Python's standard-library HTTP client. `OLLAMA_HOST` defaults to `http://localhost:11434`; other hosts require `OLLAMA_ALLOW_REMOTE=1`. The model name is required through `OLLAMA_MODEL` and is not hardcoded. The repository does not specify one active deployment model. The project log records `llama3.2:3b` for a live test; that is a tested model, not evidence of the current runtime configuration. The provider's role is grounded beneficiary Q&A and, when the model-backed summarizer is configured, write-time summary generation.

Requests bypass system proxies, do not follow redirects, and enforce configured context, output, response-size, per-request timeout, and total-question-deadline limits. Request and question timeout settings have safe defaults and hard upper bounds. Prompt sizing fails closed rather than dropping the system prompt or allowing truncation. Responses use Ollama's structured JSON option and are rejected if they do not match the exact answer schema.

The provider-neutral `ModelSummarizer` accepts any `ModelClient`. It frames original entries as escaped, delimited untrusted data and retries once if the summary contains eight consecutive words copied from the original. A repeated overlap or provider failure stores no summary. Successful summaries are separate from the append-only hash chain and bound to the source entry digest; retrieval omits summaries whose digest no longer matches.

With the default host, Ollama keeps model processing on the local service; a remote host is possible only with the explicit `OLLAMA_ALLOW_REMOTE=1` setting. Model quality, latency, and availability depend on the chosen model and machine. Summary quality may vary; the eight-word check does not guarantee factual accuracy or paraphrase quality.

## Tools

For beneficiary Q&A, the model receives schemas for four implemented tools: `search_entries`, `get_entry`, `count_mentions`, and `get_letter`. It receives schemas, not Python callables. Tool-call proposals return to the application, which executes only these allowlisted functions; unknown tools and malformed arguments are ignored. The asker is fixed in `ToolContext` so a model tool request cannot choose another identity.

The Q&A service first enumerates the owner's candidate entries to build access requests. It then asks Prolog for per-entry, per-level decisions in a batch. The resulting `ToolContext` contains candidate records together with the permission map and verified-entry IDs. Each tool enforces permission and verification before constructing a content view, scoring or counting a record, or returning content. `search_entries` scores verified summary- or verbatim-permitted views; `get_entry` returns a verified view at the allowed level; `count_mentions` counts only verified permitted records; and `get_letter` returns a released, permitted letter or a backend-generated safe status. Denied content is not returned as a Q&A tool result or included in a model prompt. The candidate enumeration happens before Prolog checks, so “before retrieval” refers to content retrieval through Q&A tools, not the initial owner-scoped listing. The tool context itself still contains candidate record objects; tools apply the permission filter internally.

**Separate write-time summary path:** When the owner creates an entry, the route may pass its newly stored `StoredEntry` to `ModelSummarizer`. That application-mediated model call receives the original entry text in an untrusted-data block to create a derived summary. It does not use the beneficiary Q&A tool flow or Prolog permission checks. The stored summary is digest-bound and is supplied in beneficiary Q&A only when that entry has summary permission. This write-time path is distinct from permission-checked Q&A retrieval.

The model has no direct connection or credentials for the vault, database, or entry repository. All model input is passed by the application through `ModelClient` prompts: Q&A content comes from permission-filtered tools after Prolog decisions, while write-time summary input comes from the owner entry-creation path described above. The model does not make access decisions.

The backend verifies citation IDs against entries actually presented to the model and attaches their stored dates. The model returns entry IDs rather than dates. Existence-only counts, release-date notices, and neutral no-record responses are constructed by the backend.

## Instructions

Ollama receives the existing `SYSTEM_PROMPT` as a system-role message and the question as a user-role message. It is instructed to answer only from permitted material supplied in the conversation, return citation entry IDs rather than dates, never claim to be the diary owner, say when permitted material contains no answer, and treat entry and summary blocks as untrusted data rather than instructions. Q&A tool results are placed in escaped, delimited blocks. The backend attaches verified dates to accepted citation IDs. The owner's policy text is not sent to the Q&A model; Prolog resolves permissions in the application.

Denied and nonexistent records follow the same neutral response path. No model call is made when no permitted material is available. The project does not implement owner Q&A.

## What fake and mocked tests do not prove

Fake-model and mocked-transport tests verify application behavior, request construction, strict response parsing, timeout and response-size limits, host restrictions, error redaction, data-flow restrictions, and fail-closed handling. They do **not** prove that a live Ollama model will follow instructions, return valid structured output, produce accurate answers or summaries, resist every prompt injection, or meet real hardware latency and availability targets. Backend permission checks, citation filtering, and neutral fallbacks enforce application behavior; the prompt alone is not an authorization boundary. The eight-word check detects only one kind of close copying.

The live Ollama safety test runs only when `RUN_LIVE_AI_TESTS=1`, uses fictional text, and checks safety properties such as citation allowlisting and not claiming to be the owner. It is not part of the normal offline suite and does not establish comprehensive model safety.

## What we would change

Live Ollama (`llama3.2:3b`, CPU-only) rows time out on slow hardware. Measurements show the small model sends invalid tool arguments and repeats them until the deadline; this is a model-quality and latency limitation, not an authorization failure. The two backend-built rows (release-date message and neutral reply) work live. If time allows, we would answer count and date questions directly in the backend, stop on repeated invalid calls, or try a larger model.

## Official references

- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
