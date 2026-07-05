# Unblock CRM Connector Read Lanes Prompt

Use this only after CRM M2 local command center is accepted and a separate
authority graduation is requested.

Implement the smallest exact-scoped CRM connector read lane that preserves UAA
authority invariants. Start from
`docs/control_center/authority_graduation_blockers/crm_connector_read_lanes_2026_07_05.md`.

Requirements:

- Define one named read-only source lane and one test-account/source scope.
- Route all agent-facing source access through the approved gateway boundary.
- Add PolicyEngine, LocalApprovalAuthority, idempotency where applicable,
  audit, redaction, safe-disable, CLI/API/Control Center parity, OpenAPI,
  route classification, tests, docs, and verifier coverage.
- Persist safe refs, bounded summaries, source metadata refs, decisions, and
  receipts only.
- Do not add connector writes, sends, calendar writes, account sync, contact
  merge/create, provider/model calls, browser automation, background polling,
  public beta, public release, production readiness, or production authority.

If any exact authority prerequisite is missing, stop with a blocker report
instead of implementing runtime connector access.
