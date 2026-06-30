# Dashboard Snapshot

Status: Active M12 read-only dashboard contract, v0.16.0.

The Control Center dashboard snapshot is a safe summary object for a future UI. It is read-only and generated from local known contract state passed to pure builders by API handlers.

The dashboard may summarize:

- system status.
- Foundation Gate status.
- runtime readiness.
- approval summary counts.
- API route inventory counts.
- remote worker dry-run-only status.
- private mesh planned-disabled status.
- mobile planning status.
- plugin governance status.
- provider credential readiness and CostGovernor binding posture as safe refs
  only, including provider manifest refs, provider auth ref status, consent
  refs, policy refs, revocation refs, approval refs, blocker codes, readiness
  status, unknown paid-cost approval posture, provider/model ref posture, cost
  estimate refs, budget decision refs, max-approved USD refs, future receipt
  refs, and CostGovernor decision/posture refs.
- credential vault adapter readiness, credential enrollment readiness, provider
  validation readiness, governed provider invocation readiness as blocked
  contract state, and tiny exact-approved provider lane readiness as
  disabled-default, no-provider-authority posture. Approved-no-execution is a
  request decision only after exact approval and cost gates pass.

The dashboard must not include raw events, raw receipts, prompts, file contents, memory contents, credentials, secret values, private keys, personal data, provider envelopes, runtime payloads, model output as authority, remote worker output as control input, mobile sensor output as control input, or production readiness evidence.

Provider credential readiness means reference posture only. It does not collect
provider keys, read environment values, resolve credential material, validate
keys against external services, call provider SDKs by default, run network
calls, or enable callable provider runtime. CostGovernor binding refs are
blockers and review scope only; they do not grant spend authority, bypass
unknown paid-cost approval, bypass provider/model refs, or bypass usage/cost
receipt refs. Credential Vault Backend V1 is a separate local safe-ref ledger
only; secret resolution, broad provider validation outside the exact-approved
credential validation lane, and provider invocation still
require later reviewed milestones.

The readiness gates are intentionally separate:

- Provider Credential Vault Backend V1: local safe-ref ledger for
  enroll/revoke/rotation posture only. The current dashboard keeps provider
  validation outside the exact-approved lane, provider invocation, and adapter
  runtime disabled.
- Credential Enrollment Readiness: future transient intake contract requiring
  exact refs, approval, idempotency, audit, rollback, safe-disable, and an
  approved vault backend. The current dashboard records
  `CREDENTIAL_ENROLLMENT_NOT_SCOPED` and collects no credential material.
- Provider Credential Validation v1: exact-approved one-provider validation
  lane requiring provider manifest refs, provider auth references, consent,
  policy, approval, idempotency, revocation/safe-disable refs, transient secret
  material, and redacted validation receipts. The default app posture records
  validation-blocked / approval-required states and broad provider validation
  remains out of scope.
- Governed Provider Invocation v1: future invocation contract requiring
  PolicyEngine, LocalApprovalAuthority or successor approval, provider
  allowlists, redacted request/response summaries, receipt/audit refs,
  safe-disable behavior, and rate/budget boundaries. The current dashboard
  records `PROVIDER_INVOCATION_NOT_SCOPED` and enables no provider call path.
- Tiny Exact-Approved Provider Lane: current disabled-default contract lane
  requiring exact approval, CostGovernor posture, max-approved USD, idempotency,
  redacted receipt refs, and safe-disable posture. The dashboard records
  `TINY_PROVIDER_LANE_DISABLED_BY_DEFAULT`; the default adapter performs no
  provider SDK call, network call, autonomous/background model call, or billing
  authority.

The dashboard does not scan the filesystem, inspect keychains, call runtimes, call models, dispatch remote workers, enable plugins, access sensors, or run frontend tooling.
