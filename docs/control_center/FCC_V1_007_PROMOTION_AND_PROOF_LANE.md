# FCC-V1-007 Promotion And Proof Lane

Status: implemented for Founder Loop V1 promotion proof.

Proof status: `founder_loop_v1_proofed`

Proof command:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_founder_loop_v1.py
```

FCC-V1-007 promotes only the Founder Loop route surfaces that now have
backend-owned state, durable receipts, Evidence Timeline visibility, manifest
truth, frontend rendering, and redaction proof:

- `/actions`
- `/chat`
- `/memory`
- `/evidence`

The promotion means the exact route behavior is proofed. It is not public
release or production readiness. It does not promote the full assistant, the
Today spine, Inbox, Settings, model lifecycle, connector workflows, or action
execution.

Proof requirements:

- Release surface manifest route status is `ship` for the four proofed route
  surfaces only.
- Route status manifest uses `founder_loop_v1_proofed`, mapped to canonical
  `shipped`.
- Mutating route metadata remains bearer protected, approval-postured,
  idempotency-required, rate-limited, and `mutating_requires_authority`.
- Action, Chat, Memory, and Evidence exercises create receipt refs.
- Evidence Timeline shows receipt-backed events for action envelopes, action
  decisions, Chat turn receipts, Chat handoffs, and Memory Review decisions.
- Evidence remains safe-ref-only and does not leak raw prompt, raw response,
  raw provider payload, raw private content, credentials, usernames, hostnames,
  or local path content.

Still blocked:

- no action execution
- no handoff execution
- no context injection
- no automatic memory writes
- no memory truth authority
- no connector writes
- no CRM or account sync
- no provider/model authority
- no shell/subprocess authority
- no public beta claim
- no public release claim
- no production authority

Routes intentionally not promoted:

- `/today` remains `partial` because the broader product spine still depends on
  future Inbox, Settings, read-only calendar/email, model lifecycle, and beta
  evidence work.
- `/inbox` remains `partial` read-only source readiness; `/settings` remains
  `partial` read-only status.
- `/models` remains blocked or partial until a separate model lifecycle proof
  lane exists.

Proof:

- `scripts/verify_founder_loop_v1.py`
- `tests/test_founder_loop_v1_proof_lane.py`
- `scripts/verify_control_center_release_surface.py`
- `scripts/verify_fcc_v1_002_action_inbox_state_machine.py`
- `scripts/verify_fcc_v1_004_chat_durable_receipt_handoff.py`
- `scripts/verify_fcc_v1_005_memory_review_decisions.py`
- `scripts/verify_fcc_v1_006_evidence_timeline_productization.py`
- `apps/control-center/src/routes.tsx`
- `docs/control_center/release_surface_manifest.json`
- `docs/control_center/route_status_manifest.json`

Next:

- The bounded Founder Loop V1 conveyor is complete through FCC-V1-007.
- Full UAA-P1-087.2 manual UI testing remains deferred until the broader
  Founder Loop implementation is ready for human trial review.
