# Authority Lane 15: Extension / Plugin Callable Promotion

Goal: let UAA inspect, validate, and eventually activate one exact extension
capability without granting broad plugin runtime import, marketplace install,
remote execution, connector writes, shell execution, browser automation,
provider/model calls, or production authority.

Allowed next promotion: Level 0-1 contract/read-only review and disabled
installation posture. Callable activation remains blocked until a later exact
capability lane proves policy validation, approval, provenance, receipts,
revocation, deny-wins handling, CLI/API/Core parity, and focused tests.

Scope:

- `extension.catalog.review`: inspect metadata, provenance, hashes, declared
  capabilities, denied capabilities, network/script indicators, and blocked
  reason refs.
- `extension.import_validate`: validate manifests and static assets without
  importing or executing code.
- `extension.install_disabled`: record disabled-by-default local install refs
  only after exact approval, hash receipts, and safe-disable posture.
- `extension.activate_exact_capability`: future lane only; exact capability id,
  exact approval scope, policy decision, idempotency, receipt, revocation, and
  rollback/safe-disable posture are required before any callable behavior.

Still blocked:

- Broad plugin runtime import.
- Automatic skill/plugin execution.
- Remote MCP/tool execution.
- Connector writes or sends.
- Runtime model/provider calls.
- Browser automation or web fetching from extension code.
- Arbitrary shell/subprocess execution.
- Network, file, credential, account, or production authority derived from a
  manifest alone.
- Public marketplace install, public release claims, or production authority.

Promotion condition:

One repo-owned or local test extension candidate can be reviewed, validated,
and recorded as disabled with provenance refs, content hashes, policy decisions,
blocked capability refs, safe-disable refs, and redacted receipt refs. Callable
activation must remain blocked unless a separate exact capability promotion is
accepted and proven.

Tests/verifiers:

- Extension catalog manifest tests.
- Malicious manifest/static indicator tests.
- Hash/provenance receipt tests.
- Disabled-by-default install posture tests.
- Deny-wins policy tests.
- Revoked capability tests.
- No plugin runtime import/no execution tests.
- CLI/API/Core parity tests for inspection paths.
- Product-language checks proving review/install posture is not callable
  authority.

If blocked:

Generate an unblock prompt for the exact missing static-review contract,
manifest validation, hash receipt, policy decision, disabled-install posture,
revocation behavior, or callable activation gate. Do not generate a broad
plugin-execution prompt.
