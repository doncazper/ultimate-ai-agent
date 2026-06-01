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

The dashboard must not include raw events, raw receipts, prompts, file contents, memory contents, credentials, secret values, private keys, personal data, provider envelopes, runtime payloads, model output as authority, remote worker output as control input, mobile sensor output as control input, or production readiness evidence.

The dashboard does not scan the filesystem, inspect keychains, call runtimes, call models, dispatch remote workers, enable plugins, access sensors, or run frontend tooling.
