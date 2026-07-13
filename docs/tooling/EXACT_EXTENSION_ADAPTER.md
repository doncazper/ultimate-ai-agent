# Exact Extension Adapter

Status: implemented for one repo-owned read-only adapter; arbitrary extension
runtime import remains blocked.

UAA has one exact extension registration that binds the reviewed
`extension-metadata-inspection` capability to the existing bounded filesystem
metadata tool. The extension does not supply executable package code. Python
Core owns the adapter, validates the pinned catalog identity, and executes only
through `AuthorityDispatcher`.

## Exact boundary

The registration fixes all executable identity fields:

- package, catalog entry, manifest, and version refs;
- capability, lane, adapter, implementation, and tool refs;
- `files/read` authority domain and capability;
- injected safe-root and exact opaque-path target binding;
- zero-cost budget reservation and settlement;
- rollback, safe-disable, idempotency, and receipt contracts.

Before every start the dispatcher re-evaluates current policy, the exact active
`AuthorityLease`, operation and cost budgets, target bindings, kill switch, and
deadline. The adapter separately re-evaluates compatibility, configuration,
health, budget, safe-disable, kill-switch, manifest, catalog, and registration
bindings. A late dynamic-posture change fails before metadata access.

Availability or registration never authorizes invocation. Approval references
are identifiers only. This read-only lane does not require a separate approval
when current policy and the exact lease permit it; policy may still deny it.

## Developer workflow

Human-readable inspection is primary:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_extensions.py \
  inspect-exact-adapter
```

Generate the reviewed manifest template on stdout:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_extensions.py \
  exact-adapter-manifest-template
```

Validate a bounded regular manifest file without importing or executing it:

```bash
PYTHONPATH=src .venv/bin/python scripts/dev/uaa_extensions.py \
  validate-exact-adapter-manifest \
  docs/tooling/exact_extension_adapter_manifest.json
```

The loader rejects symlinks, FIFOs, non-regular files, oversized files,
identity changes, invalid JSON, extra fields, and every non-allowlisted binding.

## Deliberately still blocked

- arbitrary Python, JavaScript, plugin, skill, package, or MCP runtime import;
- marketplace installation or remote package retrieval;
- extension-owned policy, approval, lease, or budget decisions;
- network, connector, shell, environment, home-directory, browser, or
  production authority;
- wildcard capabilities, targets, versions, publishers, or adapters;
- UI-owned callability or a global extension enable switch.

This reference lane demonstrates how an individually reviewed extension can
become useful without turning the catalog into an executable package loader.
Future lanes require their own exact manifest, adapter implementation, threat
review, adversarial tests, rollback, safe-disable, and request-scoped authority
evidence.
