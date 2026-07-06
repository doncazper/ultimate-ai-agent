# UAA Hermes Runtime Plugin Metadata Posture

Status: Phase 44 repo-safe Python Core read model.  
CLI: `scripts/dev/uaa_runtime.py inspect-plugin-metadata-posture`  
Core: `src/ultimate_ai_agent/core/runtime_gateway/plugin_metadata_posture.py`

## Full-Strength

UAA should eventually support plugins, adapters, hooks, tools, memory providers,
context engines, UI extensions, and skill bundles through governed activation
grants. A mature lane would require reviewed manifests, static scans, sandbox
boundaries, activation grants, rollback, safe-disable, receipts, proof, and
operator-visible Trust posture before any extension can run.

## Repo-Safe

The current implementation is a metadata contract map only:

- adapter metadata contract
- hook metadata contract
- tool metadata contract
- memory provider metadata contract
- context engine metadata contract
- UI extension metadata contract
- skill bundle metadata contract

Each surface exposes reviewed manifest, static scan, sandbox, activation grant,
rollback, safe-disable, receipt, proof, blocked authority, promotion path, and
next-safe-action refs. It does not import plugin code, execute hooks, install
packages, execute marketplace content, enable tools, call providers, write to
connectors, or execute shell commands.

## Blocked / Needs Authority

The following remain blocked:

- plugin runtime import
- hook execution
- package installation
- marketplace content execution
- plugin code execution
- connector writes
- provider calls
- shell execution
- raw manifest persistence
- Control Center authority minting

## Exact Promotion Path

Promotion requires:

1. reviewed manifest contract
2. static scan
3. sandbox boundary
4. activation grant
5. rollback and safe-disable posture
6. receipts and proof binding
7. CLI/API/Core parity before Control Center initiation
8. route side-effect classification for any future API route
9. verifier coverage that external packages, raw manifests, connector payloads,
   provider payloads, local paths, account material, credentials, and
   secret-like material are not persisted

Planning text and metadata visibility do not grant plugin execution authority.
