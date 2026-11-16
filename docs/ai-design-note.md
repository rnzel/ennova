# ENNOVA AI Design Note

Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator

## Model

The backend selects a model adapter with `LLM_PROVIDER`: `gemini`, `ollama`, or `fake`. The value is required; an unset or invalid value raises the typed `AIServiceUnavailable` error and does not fall back to another provider. The fake provider is deterministic and needs no model server or credentials. Applications can inject a scripted fake client for tests.

Gemini uses the pinned `google-genai` SDK. Its API key is backend-only in `GEMINI_API_KEY`. The model identifier is required in `GEMINI_MODEL`; no provider model identifier is embedded as a default in code or the example environment file.

Ollama uses its local `/api/chat` endpoint through Python's standard-library HTTP client; no Ollama package or extra dependency is required. `OLLAMA_HOST` defaults to `http://localhost:11434`, and only loopback hosts are accepted unless `OLLAMA_ALLOW_REMOTE=1` is explicitly set. The client makes direct connections, ignores system proxy settings, and does not follow redirects. `OLLAMA_MODEL` is required and has no code default.

Ollama sends a system message and the question as a user message. The model receives only permitted tool-result messages, whose entry and summary text remains in escaped, delimited untrusted-data blocks. A conservative estimate covers the entire serialized request; if the request plus output reserve could exceed `OLLAMA_NUM_CTX`, the client fails closed before connecting instead of dropping the system prompt or allowing server-side truncation. Context size, output-token cap, connect/read timeouts, and maximum response bytes are explicit configuration. Requests use a low temperature, `stream: false`, and Ollama's JSON-schema structured-output option. Final text must match the exact answer schema; malformed output is rejected without repair.

Each Ollama request timeout is bounded by the remaining question-wide deadline. Server, model, timeout, response-size, and malformed-output failures all map to the same safe `AIServiceUnavailable` public message. The `ennova.ai.ollama` logger records only the exception class and a stable or numeric code, never prompts, responses, exception text, or credentials.

At write time, `GeminiSummarizer` and `OllamaSummarizer` share the same model-backed implementation. They frame original entry text as untrusted data and reject a summary containing eight consecutive words copied from the original, retrying once with stronger paraphrase instructions. A second overlap yields no summary. Provider errors also store no summary. Successful summaries are separate from the append-only hash chain and bound to the source entry digest; retrieval omits summaries whose digest no longer matches.

The local-provider trade-off is that private text can stay on the configured local service, but model quality, latency, and availability depend on the chosen model and the machine running Ollama. Summary quality can be lower or less consistent than a hosted model; the copy-overlap check is not a guarantee of factual accuracy or paraphrase quality.

## Tools

The model receives schemas for `search_entries`, `get_entry`, `count_mentions`, and `get_letter`; it is not given Python callables. Tool-call proposals are returned to the application, which executes the existing allowlisted tool loop. The service fixes the asker in `ToolContext`, resolves access in one Prolog batch before retrieval, and filters permitted entries before scoring. Unknown tools and malformed arguments are ignored. The model never reads the vault or decides authorization.

Both provider adapters return tool proposals rather than executing functions. Ollama tool responses are parsed into the same `ModelResponse` interface as Gemini; the backend remains solely responsible for invoking tools and checking their results. The backend verifies citation IDs against entries already presented to the model and attaches their stored dates. Existence-only counts, release-date notices, and neutral no-record responses are constructed by the backend.

## Instructions

The system instructions require answers only from material supplied after access filtering, prohibit claiming to be the diary owner, and direct the model to treat entry text as untrusted data rather than instructions. The system prompt is always sent as a system-role message; the question is a user-role message. The model returns entry IDs rather than dates; the backend attaches verified dates. The owner's policy text is not sent to the model: Prolog has already resolved permissions.

Denied and nonexistent records follow the same neutral response path. No model call is made when no permitted material is available. The project does not implement owner Q&A.

## What fake and mocked tests do not prove

Fake-model and mocked-transport tests verify application behavior, request construction, strict response parsing, timeout and response-size limits, host restrictions, error redaction, data-flow restrictions, and fail-closed handling. They do **not** prove that a live provider or model will follow instructions, return valid structured output, produce accurate answers or summaries, resist every prompt injection, or meet real hardware latency and availability targets. The eight-word check only detects one kind of close copying.

Live provider tests run only when `RUN_LIVE_AI_TESTS=1`, use fictional text, and assert safety properties such as citation allowlisting and not claiming to be the owner. They are separate from the normal offline test suite and do not establish comprehensive model safety.

## Official references

- [Google GenAI SDK on PyPI](https://pypi.org/project/google-genai/3.3.0/)
- [Gemini Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- [Gemini function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Gemini structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Ollama chat API](https://docs.ollama.com/api/chat)
- [Ollama structured outputs](https://docs.ollama.com/capabilities/structured-outputs)
