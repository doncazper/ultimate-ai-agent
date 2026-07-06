# Hermes Interface Mode With UAA Memory Bridge

Status: implemented as a governed local runtime interface contract.

UAA can operate as the Control Center shell over Hermes while UAA-native agent
planning and execution are off. Python Agent Core owns the runtime interface
mode, Hermes CLI posture, curated context pack, chat receipt, redaction, and
blocked-authority truth. Control Center renders and initiates only backend-owned
state.

Implemented routes and CLI:

- `GET /api/runtime/interface-mode`
- `GET /api/runtime/hermes/context-pack`
- `POST /api/runtime/hermes/chat`
- `scripts/dev/uaa_runtime.py inspect-interface-mode`
- `scripts/dev/uaa_runtime.py inspect-hermes-context-pack`
- `scripts/dev/uaa_runtime.py hermes-chat --mode shell_guarded|operator_override`

Modes:

- `shell_guarded`: UAA-native agent execution is off. UAA keeps redaction,
  receipts, scoped Hermes CLI calls, and stop/status posture.
- `operator_override`: explicit operator submission to Hermes with weaker UAA
  governance visibly labeled. UAA still denies unsafe args and raw persistence.
- `pure_hermes_pass_through`: visible external handoff only. UAA does not
  execute unrestricted Hermes commands.

Hermes CLI scope:

- Discovery reads `UAA_HERMES_CLI_PATH` or PATH and returns a hashed safe ref.
- Readiness uses exact argv `hermes status --all`.
- Guarded chat uses exact argv
  `hermes chat --query ... --quiet --source uaa-control-center`.
- `--yolo`, top-level `--oneshot`, arbitrary args/toolsets, shell strings, raw
  prompt/output persistence, direct memory writes, browser automation,
  connector writes, and production authority remain blocked.

Hermes context bridge:

- Hermes receives `HermesContextPack` summaries for Memory, CRM, Chat,
  Cowork/Plans, Today, Action Inbox, Evidence, Proof, and Sources.
- Sections include safe summaries, provenance refs, why-shown refs, evidence
  refs, proof refs, and route refs.
- Raw memory records, raw CRM records, raw chat transcripts, raw local paths,
  logs, credential material, and unbounded private content are not exposed.
- Hermes memory updates are candidate-only and must go through Memory Review.

Verifier:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_interface_mode.py
```

This verifier fails if UAA-native agent execution is on, if context is not
curated/redacted, if raw Memory/CRM/chat/path content is exposed, or if pure
Hermes pass-through performs execution.
