# UAA Hermes Runtime MCP Catalog Filtering

Phase 30 adds a backend-owned MCP catalog filtering posture for the Hermes
Runtime Adoption program. It is a UAA-native metadata catalog and filter
contract, not an MCP server installer or tool runner.

## Full-Strength

UAA can inspect MCP servers and expose only reviewed tool slices. A mature lane
would let the operator see reviewed server manifests, per-tool grants,
credential refs, command allowlists, receipt requirements, safe-disable posture,
and proof links before any MCP tool becomes available.

## Repo-Safe

The current implementation is metadata-only:

- Python Agent Core owns `RuntimeMcpCatalogFilteringReadModel`.
- API route: `GET /api/runtime/mcp-catalog-filtering`.
- CLI inspection: `scripts/dev/uaa_runtime.py inspect-mcp-catalog-filtering`.
- Control Center renders server metadata, tool filter states, blocked
  activation states, route refs, CLI refs, and proof refs.
- Mock fallback is labeled non-authoritative and preserves the same blocked
  authority posture.
- No MCP server is installed, launched, contacted, or invoked.

## Blocked / Needs Authority

These remain blocked:

- installing MCP servers
- launching subprocess MCP runtimes
- OAuth login
- MCP tool invocation
- connector writes
- raw MCP manifest or tool-schema persistence
- Control Center minting authority

Blocked refs are surfaced through
`blocked-authority:mcp-catalog-no-server-install`,
`blocked-authority:mcp-catalog-no-subprocess-runtime`,
`blocked-authority:mcp-catalog-no-oauth-login`,
`blocked-authority:mcp-catalog-no-tool-invocation`,
`blocked-authority:mcp-catalog-no-connector-write`,
`blocked-authority:mcp-catalog-no-raw-manifest-persistence`, and
`blocked-authority:mcp-catalog-no-control-center-authority-mint`.

## Exact Promotion Path

Promotion requires all of the following before any MCP execution lane can move
beyond metadata:

- reviewed server manifest
- command allowlist
- credential refs only, never raw material
- exact per-tool grants
- approval binding
- idempotency
- receipt and proof refs
- safe-disable posture
- focused tests and verifier coverage
- CLI/API/Core parity
- Control Center labels that distinguish metadata, grant-required, filtered,
  blocked, and executable states

## Verification

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_hermes_runtime_mcp_catalog_filtering.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_hermes_runtime_adoption_phase_30.py
PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py
npm run test --prefix apps/control-center -- --run src/App.test.tsx src/routes.test.ts src/api/client.summaryEndpoints.test.ts
```

The verifier fails if the route is missing, classification drifts, CLI parity is
lost, or any install, subprocess runtime, login, tool invocation, connector
write, raw manifest persistence, or Control Center authority flag is enabled.
