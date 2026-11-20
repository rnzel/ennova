# Technology Stack Decision Note

Team: Roldan Jr. Bazares (Front End); Ranzel Jay Gobris (Lead Developer / Back End); Bart Jayson Lola (Q/A); Jallil Sultan (UI/UX Designer); Jezelle Gabion (Documentator)

| Concern | Paradigm | Choice | Why it fits | Status |
|---|---|---|---|---|
| OOP and functional code | Object-oriented and functional | Python 3.12 | OOP: classes, abstract bases, inheritance and encapsulation (`Entry`, `Vault`, `WritingMode`). Functional: pure functions over frozen dataclasses and tuples, with the hash chain as a fold. One language for all six components. | In use |
| Access rules | Logic | SWI-Prolog, called from Python as a subprocess | Rules, exceptions, and "deny beats allow" are declarative and auditable. A subprocess avoids native-binding problems on Windows, gives a hard timeout, and fails closed. | In use |
| Policy language | Language design | Hand-written lexer, recursive-descent parser, and interpreter in Python | Demonstrates the grammar-to-execution chain, with an EBNF in `docs/grammar/`. | In use |
| Language model | n/a | Ollama running locally, behind a `ModelClient` interface, plus a deterministic fake provider for tests | Free, no API key, and diary text never leaves the machine. Gemini was built and then removed. | In use, with limits |
| Q&A scripting | Scripting | Python service that checks Prolog, retrieves permitted entries, calls the model, and verifies citations | Glue code with typed exceptions and safe fallbacks. | In use |
| API framework | n/a | Flask with Flask-Limiter, PyJWT, and Werkzeug password hashing | Thin routes over tested services. | In use |
| Persistence | n/a | In-memory repositories now; Aiven MySQL 8.4 via SQLAlchemy planned | Interfaces let storage change later. | Planned (F9b) |
| User interface | n/a | Expo React Native with TypeScript | Chosen in the project spec. A mobile interface is an optional extra, so it needs instructor approval first. | Not started, pending approval |
| Dev tools | n/a | Git and GitHub, VS Code, GitHub Copilot, pytest, Postman | Shared workflow and automated tests. | In use |

## Trade-offs we accept
- Python is not purely functional, so purity is enforced by convention and by tests that forbid I/O imports in the functional package.
- A 3B local model on a CPU-only laptop is slow and calls tools unreliably. Backend-built answers work live, and the rest uses the fake provider.
- The Gemini client, ChromaDB, and sentence-transformers were considered and are not used.

## Versions
Python 3.12.x, SWI-Prolog <fill in>, and the pinned packages in `backend/requirements.txt`.
SWI-Prolog and Ollama are installed separately.