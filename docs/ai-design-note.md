# ENNOVA AI Design Note

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

## Model

ENNOVA selects its model client through `LLM_PROVIDER`. The only accepted values are `ollama` and `fake`; an unset or invalid value fails closed with `AIServiceUnavailable`. The fake client is deterministic and is intended for tests and scripted demos.

The Ollama client uses the local `/api/chat` endpoint via Python's standard-library HTTP client. `OLLAMA_HOST` defaults to `http://localhost:11434`; other hosts require `OLLAMA_ALLOW_REMOTE=1`. `OLLAMA_MODEL` is required and is never hardcoded. Requests bypass system proxies, do not follow redirects, and enforce configured context, output, response-size, per-request timeout, and total-question-deadline limits. Request and question timeout settings have safe defaults and hard upper bounds. Prompt sizing fails closed rather than dropping the system prompt or allowing truncation. Responses use Ollama's structured JSON option and are rejected if they do not match the exact answer schema.

The provider-neutral `ModelSummarizer` accepts any `ModelClient`. It frames original entries as escaped, delimited untrusted data and retries once if the summary contains eight consecutive words copied from the original. A repeated overlap or provider failure stores no summary. Successful summaries are separate from the append-only hash chain and bound to the source entry digest; retrieval omits summaries whose digest no longer matches.

Ollama keeps model processing on the configured local service, but model quality, latency, and availability depend on the chosen model and machine. Summary quality may vary; the eight-word check does not guarantee factual accuracy or paraphrase quality.

## Tools

The model receives schemas for `search_entries`, `get_entry`, `count_mentions`, and `get_letter`; it is not given Python callables. Tool-call proposals are returned to the application, which executes the existing allowlisted tool loop. The service fixes the asker in `ToolContext`, resolves access in one Prolog batch before retrieval, and filters permitted entries before scoring. Unknown tools and malformed arguments are ignored. The model never reads the vault or decides authorization.

The backend verifies citation IDs against entries already presented to the model and attaches their stored dates. Existence-only counts, release-date notices, and neutral no-record responses are constructed by the backend.

## Instructions

Ollama receives the system instructions as a system-role message and the question as a user-role message. The instructions require answers only from material supplied after access filtering, prohibit claiming to be the diary owner, and direct the model to treat entry text as untrusted data rather than instructions. Permitted entries and summaries remain in escaped, delimited blocks. The model returns entry IDs rather than dates; the backend attaches verified dates. The owner's policy text is not sent to the model: Prolog has already resolved permissions.

Denied and nonexistent records follow the same neutral response path. No model call is made when no permitted material is available. The project does not implement owner Q&A.

## What fake and mocked tests do not prove

Fake-model and mocked-transport tests verify application behavior, request construction, strict response parsing, timeout and response-size limits, host restrictions, error redaction, data-flow restrictions, and fail-closed handling. They do **not** prove that a live Ollama model will follow instructions, return valid structured output, produce accurate answers or summaries, resist every prompt injection, or meet real hardware latency and availability targets. The eight-word check detects only one kind of close copying.

The live Ollama safety test runs only when `RUN_LIVE_AI_TESTS=1`, uses fictional text, and checks safety properties such as citation allowlisting and not claiming to be the owner. It is not part of the normal offline suite and does not establish comprehensive model safety.

## What we would change

Live Ollama (`llama3.2:3b`, CPU-only) rows time out on slow hardware. Measurements show the small model sends invalid tool arguments and repeats them until the deadline; this is a model-quality and latency limitation, not an authorization failure. The two backend-built rows (release-date message and neutral reply) work live. If time allows, we would answer count and date questions directly in the backend, stop on repeated invalid calls, or try a larger model.

## Official references

- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
