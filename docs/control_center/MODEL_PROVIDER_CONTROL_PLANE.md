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
- UAA GoatCitadel Runtime Parity Phase 06 role-based provider/model evidence
  for answerer, planner, reviewer, synthesizer, coder, extractor, and safety
  reviewer roles.
- GoatCitadel catch-up Phase 07 model/provider/research posture for provider
  readiness rows, model-output truth handling, and WebAccessGateway-governed
  external-information status.
- Hermes Runtime Adoption Phase 07 delegated runtime model availability
  catalog, which separates "runtime reports model availability" from "UAA may
  invoke this model" and keeps delegated Hermes/local runtime model rows
  read-only.

The Control Center `/models` surface renders this read model alongside Provider
Catalog, provider credential readiness, and local model readiness.

CLI parity:

```bash
.venv/bin/python scripts/inspect_model_provider_control_plane.py
.venv/bin/python scripts/dev/uaa_runtime.py inspect-role-provider-evidence --json
```

Verifier:

```bash
.venv/bin/python scripts/verify_model_provider_control_plane.py
.venv/bin/python scripts/verify_uaa_goatcitadel_catchup_model_provider_research.py
.venv/bin/python scripts/verify_uaa_goatcitadel_runtime_role_provider_evidence.py
.venv/bin/python scripts/verify_hermes_runtime_adoption_phase_07.py
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
