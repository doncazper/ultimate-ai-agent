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
- provider credential readiness as safe refs only, including provider manifest
  refs, provider auth ref status, consent refs, policy refs, revocation refs,
  approval refs, blocker codes, and readiness status.
- credential vault adapter readiness, provider validation readiness, and
  governed provider invocation readiness as blocked contract states only.

The dashboard must not include raw events, raw receipts, prompts, file contents, memory contents, credentials, secret values, private keys, personal data, provider envelopes, runtime payloads, model output as authority, remote worker output as control input, mobile sensor output as control input, or production readiness evidence.

Provider credential readiness means reference posture only. It does not collect
provider keys, read environment values, resolve credential material, validate
keys against external services, call provider SDKs, or enable provider
invocation. A real credential vault/keychain adapter requires a separate
reviewed milestone.

The readiness gates are intentionally separate:

- Provider Credential Vault Adapter v1: future disabled-by-default adapter
  contract for opaque provider auth references only. The current dashboard records
  `VAULT_ADAPTER_NOT_SCOPED` and keeps adapter runtime disabled.
- Provider Credential Validation v1: future validation contract requiring
  provider manifest refs, provider auth references, consent, policy, approval,
  revocation, and redacted validation receipts. The current dashboard records
  `PROVIDER_KEY_VALIDATION_NOT_SCOPED` and performs no external validation.
- Governed Provider Invocation v1: future invocation contract requiring
  PolicyEngine, LocalApprovalAuthority or successor approval, provider
  allowlists, redacted request/response summaries, receipt/audit refs,
  safe-disable behavior, and rate/budget boundaries. The current dashboard
  records `PROVIDER_INVOCATION_NOT_SCOPED` and enables no provider call path.

The dashboard does not scan the filesystem, inspect keychains, call runtimes, call models, dispatch remote workers, enable plugins, access sensors, or run frontend tooling.
