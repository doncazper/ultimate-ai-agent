# v0.101.0 Master Plan

Release: v0.101.0 - Operator Runtime Excellence P1 durable run spine baseline.

The active product and package baseline is v0.101.0. This is a contract,
documentation, verifier, and test baseline for durable local operator run truth.
It is not a public release, beta, production runtime, or expanded-authority
milestone.

Scope:

- Add UAA-P1-010 durable run records, states, transition rules, idempotency
  keys, audit refs, receipt refs, replay refs, rollback refs, failure refs,
  restart refs, and checksum snapshot validation.
- Align README, VERSION, docs index, canonical map, roadmap, Kanban board,
  release notes, product truth, and release packet labels.
- Preserve accepted checkpoint references for checkpoint-m166,
  checkpoint-m167, and checkpoint-m168.
- Keep the Operator Runtime Excellence Program active and explicit.
- Preserve repo-owned release-truth, public security, M167 evidence, local
  smoke, performance, local model operational, and operator-shell mapping
  evidence.
- Keep all release-facing claims evidence-backed and verifier guarded.

Required invariants:

- PolicyEngine, LocalApprovalAuthority, route side-effect classification,
  OpenAPI checks, and Foundation Gate checks remain required.
- Authority remains disabled-by-default and exact-scope.
- Release-facing evidence uses safe refs and redacted summaries only.
- Duplicate durable mutations are denied by idempotency keys.
- Restart recovery is visible as run state, not hidden execution.
- No raw prompt, raw response, raw provider payload, raw path, raw log,
  username, hostname, serial, environment dump, or credential material is
  allowed in durable evidence or release-facing docs.

This baseline adds no shell/subprocess execution, unrestricted network or
browser automation, connector writes, plugin runtime import, mobile control,
autonomous background execution, provider/model authority, public distribution,
beta release, or production authority.
