## Runtime Web Chat Plan

### Goal
- Replace the current browser-side mock-like response-bank behavior with a real runtime chat path.
- Keep the static dashboard generation flow intact.
- Preserve browser fallback to embedded response-bank answers when the local runtime service is unavailable.

### Scope
- Add a local HTTP server that serves the generated static site and a real `POST /api/chat` endpoint.
- Extend the CLI with a `serve` command.
- Update the embedded chat drawer to prefer runtime API calls and fall back to embedded responses.
- Add tests for CLI parsing, runtime chat request handling, and rendered runtime wiring.

### Non-goals
- No persistent multi-turn memory.
- No external search or new RAG layer.
- No hosted backend deployment; local runtime only.

### Steps
1. Add failing tests for:
   - `serve` CLI parsing and dispatch
   - runtime chat request handling
   - rendered chat shell runtime endpoint usage
2. Implement a lightweight local server module with:
   - static file serving from `build/site`
   - `POST /api/chat`
   - optional `GET /api/health`
3. Wire a new `serve` command into the CLI.
4. Update chat drawer JS to:
   - use runtime API on `http(s)` pages
   - fall back to embedded response bank on failure
   - surface `loading / fallback / enhanced / error` states clearly
5. Run full verification and keep the repo clean.

### Verification
- `python -m unittest discover -s tests -v`
- `python run_dashboard.py generate-today --output-dir build/site`
- `python run_dashboard.py chat --date <date> --question "..."`
