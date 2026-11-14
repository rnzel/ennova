# ENNOVA AI Design Note

Team members: [Full name] – Front End; [Full name] – Back End; [Full name] – Q/A; [Full name] – UI/UX Designer; [Full name] – Documentator

## Model

ENNOVA uses Google's `google-genai` Python SDK, pinned to `3.3.0`. Google currently recommends its Interactions API for new integrations; the SDK uses `from google import genai`. The API key is read from `GEMINI_API_KEY` when the backend client is created. It is never requested from a beneficiary, returned in an error, or written to logs. A missing key raises the typed `AIServiceUnavailable` error; set the environment variable in the backend deployment.

The model ID is selected through `GEMINI_MODEL`; the example configuration defaults to `gemini-3.8-flash`, listed as a stable Flash model in Google's model catalog. Google's current Interactions quickstart also demonstrates `gemini-4-hydrogen`. Model availability can vary by account and endpoint, so deployments can select an available ID without a code change.

Interactions are sent with `store=False`; the SDK's automatic continuation is disabled. A strict JSON response schema is used for model answers, with a low temperature, an output-token limit, a per-request timeout, and a 45-second question-wide deadline. SDK retries are disabled; the adapter retries only HTTP 429 and 5xx responses, with a small attempt limit and only while time remains. Errors log only the exception class and numeric status code.

At write time, `GeminiSummarizer` receives the original as escaped, untrusted data and requests a summary that does not quote it. The summary is rejected and retried once if it shares eight consecutive words with the original. If the second result also overlaps, no summary is stored. Stored summaries are outside the append-only hash chain and carry the source entry digest; retrieval omits a summary whose digest no longer matches.

## Tools

The model receives JSON schemas for `search_entries`, `get_entry`, `count_mentions`, and `get_letter`; it is not given Python callables. Function-call steps are returned to the application, which executes the existing allowlisted tool loop. The app fixes the asker for the whole question, resolves access in one Prolog batch before retrieval, and filters permitted entries before scoring. The model never reads the vault or decides authorization.

The Interactions API response is stateless and contains either manually handled function-call steps or a strict JSON final response. The backend verifies citation IDs against entries already presented to the model and attaches their stored dates. Existence-only counts, release-date notices, and neutral no-record responses are constructed by the backend.

## Instructions

The system instructions require answers only from material supplied after access filtering, prohibit claiming to be the diary owner, and direct the model to treat entry text as untrusted data rather than instructions. The model returns entry IDs rather than dates; the backend attaches verified dates. The owner's policy text is not sent to the model: Prolog has already resolved permissions.

Denied and nonexistent records follow the same neutral response path. No model call is made when no permitted material is available. The project does not implement owner Q&A.

## What fake-model tests do not prove

Fake-model and mocked-SDK tests verify application behavior, request construction, strict response parsing, retry boundaries, data-flow restrictions, and fail-closed handling. They do **not** prove that a live Gemini model will follow the instructions, return valid structured output, produce accurate summaries, respect every privacy expectation, or meet latency and availability targets. The live safety test uses fictional text and runs only when `RUN_LIVE_AI_TESTS=1`; it has not been run as part of the normal no-key test suite.

## Official references

- [Google GenAI SDK on PyPI](https://pypi.org/project/google-genai/3.3.0/)
- [Interactions API](https://ai.google.dev/gemini-api/docs/interactions)
- [Function calling](https://ai.google.dev/gemini-api/docs/function-calling)
- [Structured output](https://ai.google.dev/gemini-api/docs/structured-output)
- [Gemini model catalog](https://ai.google.dev/gemini-api/docs/models)
