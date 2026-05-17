## Session-Memory Chat Plan

### Goal
- Add session-scoped follow-up memory to runtime chat.
- Keep the current single-turn path stable.

### Steps
1. Add tests for:
   - follow-up resolution
   - `/api/chat` message history payloads
   - rendered front-end message history submission
2. Implement a small session-memory helper module.
3. Extend chat analysis to classify follow-ups.
4. Extend chat pipeline to accept recent message history.
5. Update runtime web chat drawer to send recent messages.
6. Run full verification, commit, and push.

### Verification
- `python -m unittest discover -s tests -v`
- `python run_dashboard.py generate-today --output-dir build/site`
- `python run_dashboard.py chat --date <date> --question "..."`
