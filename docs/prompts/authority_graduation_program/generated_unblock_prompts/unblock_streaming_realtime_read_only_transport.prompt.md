# Unblock Streaming / Realtime Read-Only Transport

Goal:
Add or explicitly no-go one read-only progress transport for existing durable
run refs without creating a control channel.

Branch:
`codex/unblock-streaming-realtime-read-only-transport`

Base:
latest `main`

Hard constraints:
- preserve `AGENTS.md` invariants
- read-only stream only
- no run start/resume/cancel/retry over stream
- no tool execution over stream
- no provider/model streaming by default
- no provider SDK calls
- no connector writes/sends
- no shell/browser/live web execution
- no background worker or scheduler
- no external realtime transport authority
- no raw prompt, response, provider payload, tool payload, chunk, output body,
  local path, credential, cookie, token, username, hostname, or secret-like
  persistence
- no public beta, public release, or production authority

Implementation scope:
1. Re-read:
   - `AGENTS.md`
   - `docs/control_center/authority_graduation_blockers/streaming_realtime_read_only_transport_2026_07_03.md`
   - `docs/architecture/STREAMING_PROGRESS_READ_MODEL.md`
   - `tests/test_streaming_progress_read_model.py`
2. Define one read-only local progress transport for existing durable run refs,
   or record no-go if route/auth/reconnect constraints cannot be made safe.
3. If implemented, bind the transport to the existing progress read model:
   - existing run refs only
   - local/auth policy
   - bounded replay/cursor refs
   - reconnect behavior
   - polling fallback
   - redacted safe-ref event payloads
   - route status/OpenAPI/API manifest truth
4. Do not accept client mutation/control events over the transport.
5. Do not add provider stream, tool stream, connector delivery stream,
   background worker stream, or external realtime transport behavior.
6. Add or update tests proving:
   - unknown/unauthorized run refs block;
   - reconnect/cursor behavior is bounded;
   - stream payloads are safe refs only;
   - POST/control/mutation attempts are impossible or rejected;
   - polling fallback returns equivalent read-model truth;
   - provider/tool/connector/background authorities remain blocked.

Tests/verifiers:
- focused streaming progress/read-only transport pytest
- OpenAPI/API manifest checks if routes change
- route status manifest tests if route status changes
- product-language verifier
- `.venv/bin/python scripts/verify_documentation_integrity.py`
- `.venv/bin/python scripts/verify_operational_maturity.py`
- `git diff --check`

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green and no mutation/control transport was added
