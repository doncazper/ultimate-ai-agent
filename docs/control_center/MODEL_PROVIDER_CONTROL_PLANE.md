# Model/Provider Control Plane

Status: implemented read model, governed exact lanes only.

## Full-Strength Target

UAA should make model/provider handling visible and operable as a governed
runtime cockpit:

- provider adapters and provider/lane status;
- secret status without exposing secret material;
- network allowlists and endpoint refs;
- reviewed model metadata and discovery posture;
- CostGovernor and actual usage/cost receipt hooks;
- local llama.cpp lifecycle posture;
- ModelRouter and provider-router traces;
- role-based model/provider selection evidence;
- Control Center, API, CLI, verifier, and Proof parity.

## Current Repo-Safe Implementation

`GET /control-center/providers/runtime-control-plane` returns the backend-owned
`ModelProviderControlPlaneReadModel`.

The read model unifies existing UAA contracts:

- tiny exact-approved OpenAI-compatible and Anthropic-compatible live adapter
  lanes;
- exact provider credential validation lane;
- provider router dry-run lane;
- static provider catalog and cost literacy;
- CostGovernor refs and receipt requirements;
- local model inventory and M164 llama.cpp gateway posture;
- M163 llama.cpp lifecycle contract posture;
- deterministic ModelRouter trace metadata.
- deterministic, bounded provider-routing intelligence adapted from the public
  MIT-licensed ModelRouter project. The UAA-native projection uses injected
  compatibility, configuration, health, budget, cost, latency, quality,
  context, and safe-disable observations; unknown or stale evidence fails
  closed and the result remains a non-authorizing proposal.
- UAA Runtime Parity Phase 06 role-based provider/model evidence
  for answerer, planner, reviewer, synthesizer, coder, extractor, and safety
  reviewer roles.
- runtime capability foundation Phase 07 model/provider/research posture for provider
  readiness rows, model-output truth handling, and WebAccessGateway-governed
  external-information status.
- Hermes Runtime Adoption Phase 07 delegated runtime model availability
  catalog, which separates "runtime reports model availability" from "UAA may
  invoke this model" and keeps delegated Hermes/local runtime model rows
  read-only.
- Hermes Runtime Adoption Phase 08 main/auxiliary model slot posture for main
  thinking, summarization, title, approval scoring, compression, retrieval,
  vision, and review slots without hidden routing or live auxiliary calls.

The Control Center `/models` surface renders this read model alongside Provider
Catalog, provider credential readiness, and local model readiness.

CLI parity:

```bash
.venv/bin/python scripts/inspect_model_provider_control_plane.py
.venv/bin/python scripts/inspect_model_provider_control_plane.py --json
.venv/bin/python scripts/dev/uaa_runtime.py inspect-role-provider-evidence --json
```

Human-readable output is primary. JSON exposes the same redacted Python-owned
truth for automation. Candidate presentation is bounded to four rows and never
performs provider fanout.

## Reciprocal Learning Kept UAA-Native

The evidence-backed GoatCitadel comparison identified four Goat-to-UAA
patterns worth adapting. Their current UAA-native boundaries are:

- **Run Detail and readable approvals:** the existing backend-owned,
  run-attached approval queue and Proof Run Detail remain the source of truth;
  React renders them and cannot mint approval or lease authority.
- **Provider explanations:** `ProviderRoutingProposal` explains bounded
  candidates, blockers, cost, latency, quality, and readiness. A recommendation
  must still pass fresh request-scoped policy, LocalApprovalAuthority,
  AuthorityLease, budget, target, adapter, kill-switch, safe-disable, deadline,
  and idempotency evaluation before invocation.
- **Code workbench review:** transient patch content can be reduced to an exact
  hash, target fingerprint, base revision, approval-scope fingerprint,
  validation plan, rollback plan, and idempotency ref. The patch body is not
  persisted and apply remains a separately governed lane.
- **Extension developer tooling:** `uaa_extensions.py validate-entry` provides
  focused metadata, provenance, version, and pinned-hash feedback for known
  catalog entries. Validation never imports or executes an extension.

UAA intentionally does not borrow wildcard grants, approval bypasses,
content-bearing durable traces, trusted-host execution presented as sealed
isolation, or arbitrary extension imports.

Verifier:

```bash
.venv/bin/python scripts/verify_model_provider_control_plane.py
.venv/bin/python scripts/verify_uaa_runtime_model_provider_research.py
.venv/bin/python scripts/verify_uaa_runtime_role_provider_evidence.py
.venv/bin/python scripts/verify_hermes_runtime_adoption_phase_07.py
.venv/bin/python scripts/verify_hermes_runtime_adoption_phase_08.py
```

## Still Blocked

The control plane does not grant:

- broad provider runtime;
- provider SDK calls;
- provider network calls by default;
- live provider model discovery;
- raw prompt, response, provider payload, credential, local path, or raw log
  persistence;
- Control Center credential collection;
- local llama.cpp process start from the read model;
- model calls from the read model;
- delegated runtime model availability as UAA invocation permission;
- runtime default/model selection mutation;
- hidden model routing or live auxiliary model calls;
- billing actions or spend authority;
- role-based provider evidence as execution permission;
- shell execution;
- background autonomy;
- production authority.

The Phase 07 research posture also keeps provider output as proposal/evidence
only. It does not permit memory writes, action authority, context injection,
connector writes, browser automation, live web fetch, or provider search calls.

## Exact Promotion Path

Promotion from posture to execution must remain lane-specific:

1. exact approval scope;
2. provider/model/credential refs;
3. endpoint and transport allowlist refs;
4. CostGovernor decision and max-approved-cost refs;
5. idempotency ref;
6. receipt store before network;
7. redacted actual usage/cost receipt refs;
8. safe-disable or rollback posture;
9. CLI/API/Control Center parity;
10. focused tests and verifier coverage.

Promotion of one exact lane does not grant broad provider authority.
