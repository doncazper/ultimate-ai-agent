# UAA Compatibility Naming And Schema Drift Remediation Prompts

Status: operator-run prompt pack
Purpose: remediate misleading compatibility contracts, stale schemas, incomplete exact-approval checks, and historical/non-authoritative docs drift without granting new runtime authority.

Use Prompt 00 for one end-to-end implementation pass. Use Prompts 01-05 as smaller merge-gated lanes if you want lower-risk PRs.

## Prompt 00 - Execute The Full Compatibility Drift Remediation

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Goal: fix compatibility naming and schema drift that could cause future work to build on misleading contracts. Keep the work contract-first, local-first, and safety-preserving.

Non-negotiable UAA constraints:

- Python Agent Core remains the authority.
- Do not add runtime model calls, provider SDK calls, web fetching, browser automation, connector writes, plugin runtime import, shell/subprocess execution lanes, remote dispatch, public beta/release/distribution, or production authority.
- MCP and A2A work remains metadata/import foundation only unless an accepted later milestone grants exact scoped authority.
- OpenAPI/API manifest, route side-effect, redaction, PolicyEngine, LocalApprovalAuthority, and Foundation Gate checks remain hard boundaries.
- Evidence and docs must not include raw prompts, raw responses, provider payloads, raw local paths, usernames, hostnames, env dumps, credentials, or secret-like values.
- Use `apply_patch` for edits. Do not revert unrelated worktree changes.

Findings to fix:

1. `A2AAgentCardMinimal` live model and `docs/schemas/a2a_agent_card_minimal.schema.json` disagree.
2. `AgentRuntimeAdapterManifest` live model and `docs/schemas/agent_runtime_adapter_manifest.schema.json` disagree.
3. `ProviderManifest` live model and `docs/schemas/provider_manifest.schema.json` disagree.
4. A2A/MCP exact approval-binding contracts name fields that the evaluators do not enforce.
5. `A2AAgentCardMinimal` sounds like a real A2A protocol Agent Card, but it is currently a UAA-local metadata import shim.
6. Old non-archived `docs/master_plans/*` files contain compatibility/product-direction wording that can be mistaken for current truth.

Implementation plan:

1. Add a focused verifier, for example `scripts/verify_compatibility_schema_drift.py`, that compares high-risk checked-in schemas against the live Pydantic models they are meant to represent. Cover at least:
   - `docs/schemas/a2a_agent_card_minimal.schema.json` vs the live A2A metadata import model.
   - `docs/schemas/agent_runtime_adapter_manifest.schema.json` vs `AgentRuntimeAdapterManifest`.
   - `docs/schemas/provider_manifest.schema.json` vs `ProviderManifest`.
   - `docs/schemas/extension_activation_grant.schema.json` vs its intended wrapper/record contract, or explicitly document why it is a wrapper schema and verify that wrapper shape.
2. Regenerate or rewrite the three stale schemas so they match the live models. Prefer generated Pydantic JSON Schema with small, reviewed post-processing only where the repo already uses that pattern.
3. Rename `A2AAgentCardMinimal` to a clearer UAA-local name such as `UAAA2AAgentCardMetadataImport`, while preserving a temporary compatibility alias if needed. Update imports, tests, docs, schema titles, and names so the current contract cannot be confused with official A2A protocol support.
4. Add a future/spec placeholder only if useful, for example `A2AAgentCardV1`, but keep it inert and clearly not wired to runtime dispatch. Do not claim official A2A compatibility unless there are fixture tests against the current official Agent Card shape and explicit blocked-by-default import behavior.
5. Harden A2A exact approval evaluation:
   - `task_ref`, `handoff_ref`, and `expires_ref` must be semantically checked against expected metadata/proposal/approval context, or the binding contract must be changed so it does not claim exactness for unenforced fields.
   - Add tests proving mismatches are blocked.
6. Harden MCP exact approval evaluation:
   - `argument_ref`, `scope_ref`, `budget_ref`, and `expires_ref` must be semantically checked against expected metadata/preview/approval context, or the binding contract must be changed so it does not claim exactness for unenforced fields.
   - Add tests proving mismatches are blocked.
7. Banner or move old `docs/master_plans/*` files so they are clearly historical/non-authoritative. If moving is too broad, add a top-of-file historical banner and update active indexes so future agents start from active truth docs instead.
8. Update the smallest relevant docs:
   - `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`
   - `docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md`
   - `docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md`
   - `docs/control_center/PRODUCT_LANGUAGE_RULES.md` if naming rules need tightening.
   - `docs/DOCUMENTATION_INDEX.md` only if new verifier/doc references are added.

Verification requirements:

- Run focused tests:
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_a2a_gateway_foundation.py tests/test_mcp_gateway_foundation.py tests/test_a2a_adapter_boundaries.py tests/test_sdk_adapter_boundaries.py tests/test_provider_manifests.py tests/test_extension_activation_grants.py -q`
- Run focused verifiers:
  - `PYTHONPATH=src .venv/bin/python scripts/verify_a2a_gateway_foundation.py`
  - `PYTHONPATH=src .venv/bin/python scripts/verify_mcp_gateway_foundation.py`
  - `PYTHONPATH=src .venv/bin/python scripts/verify_agent_runtime_compatibility.py`
  - `PYTHONPATH=src .venv/bin/python scripts/verify_compatibility_schema_drift.py`
- If schemas/docs indexes changed, also run:
  - `.venv/bin/python scripts/verify_documentation_integrity.py`
- If route/API manifest behavior changes, run:
  - `PYTHONPATH=src .venv/bin/python scripts/verify_openapi_contract.py`
  - `PYTHONPATH=src .venv/bin/python -m pytest tests/test_api_manifest.py tests/test_control_center_api_routes.py -q`

Definition of done:

- Stale high-risk schemas match their live models or are explicitly verified wrapper schemas.
- A2A naming no longer implies protocol-complete Agent Card support.
- MCP/A2A exact approval evaluators either enforce every field promised by docs or stop promising unenforced exactness.
- Historical master plans cannot be mistaken for current product truth.
- Product-language docs continue to say MCP/A2A are metadata/import foundation only.
- No new runtime authority is added.
- Final answer lists changed files, tests/verifiers run, skipped checks, and remaining blocked items.

## Prompt 01 - Schema/Model Drift Verifier And Schema Regeneration

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Fix only the high-risk schema/model drift lane.

Tasks:

1. Add `scripts/verify_compatibility_schema_drift.py`.
2. Make it compare checked-in JSON schemas to live Pydantic models for:
   - A2A metadata import model.
   - `AgentRuntimeAdapterManifest`.
   - `ProviderManifest`.
3. Regenerate or rewrite:
   - `docs/schemas/a2a_agent_card_minimal.schema.json`
   - `docs/schemas/agent_runtime_adapter_manifest.schema.json`
   - `docs/schemas/provider_manifest.schema.json`
4. If `extension_activation_grant.schema.json` intentionally wraps both grant and revocation records, verify that wrapper shape explicitly instead of comparing it as if it were a single Pydantic model.
5. Add focused tests or verifier assertions for required fields, property names, enum compatibility, and `additionalProperties` posture.

Constraints:

- No runtime authority changes.
- No provider/network/browser/MCP/A2A runtime calls.
- Do not rename Python classes in this prompt unless required to make schemas pass.

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_compatibility_schema_drift.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_a2a_adapter_boundaries.py tests/test_sdk_adapter_boundaries.py tests/test_provider_manifests.py tests/test_extension_activation_grants.py -q
```

## Prompt 02 - A2A Metadata Import Naming Hardening

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Fix only the misleading A2A naming lane.

Tasks:

1. Rename `A2AAgentCardMinimal` to `UAAA2AAgentCardMetadataImport` or a similarly explicit name.
2. Preserve a temporary backwards-compatible alias if needed, but mark it deprecated in comments/docstrings and tests.
3. Update imports, tests, docs, schema title, and schema filename references if appropriate.
4. Make docs say this is a UAA-local metadata import shim, not official A2A Agent Card support.
5. Optionally add an inert `A2AAgentCardV1` placeholder only if it is clearly future/spec-shaped, unregistered, blocked by default, and not used as protocol support.

Constraints:

- Do not add remote dispatch, peer auth, HTTP/gRPC execution, public agent-card discovery, provider/model calls, connector writes, browser/shell execution, or runtime authority.
- Keep `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md` honest: metadata/import contracts only.

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_a2a_gateway_foundation.py tests/test_a2a_adapter_boundaries.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_a2a_gateway_foundation.py
PYTHONPATH=src .venv/bin/python scripts/verify_compatibility_schema_drift.py
```

## Prompt 03 - Exact Approval Enforcement For A2A And MCP

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Fix only the exact-approval enforcement lane.

Tasks:

1. Inspect A2A approval docs and code:
   - `src/ultimate_ai_agent/core/capabilities/a2a_gateway.py`
   - `docs/remote/UAA_A2A_GATEWAY_FOUNDATION.md`
   - `tests/test_a2a_gateway_foundation.py`
2. Ensure `evaluate_a2a_exact_approval_binding()` blocks mismatches for every field the docs claim is exact. At minimum handle `task_ref`, `handoff_ref`, and `expires_ref` by either:
   - passing expected refs into the evaluator, or
   - binding them into a proposal/approval context object, or
   - reducing the contract/docs so they do not claim unenforced exactness.
3. Inspect MCP approval docs and code:
   - `src/ultimate_ai_agent/core/capabilities/mcp_gateway.py`
   - `docs/tooling/UAA_MCP_GATEWAY_FOUNDATION.md`
   - `tests/test_mcp_gateway_foundation.py`
4. Ensure `evaluate_mcp_exact_approval_binding()` blocks mismatches for every field the docs claim is exact. At minimum handle `argument_ref`, `scope_ref`, `budget_ref`, and `expires_ref` by either:
   - passing expected refs into the evaluator, or
   - binding them into a preview/approval context object, or
   - reducing the contract/docs so they do not claim unenforced exactness.
5. Add tests proving each newly enforced mismatch blocks with explicit reason codes.

Constraints:

- Keep runtime dispatch blocked.
- This is approval-contract hardening only, not enablement.

Run:

```bash
PYTHONPATH=src .venv/bin/python -m pytest tests/test_a2a_gateway_foundation.py tests/test_mcp_gateway_foundation.py -q
PYTHONPATH=src .venv/bin/python scripts/verify_a2a_gateway_foundation.py
PYTHONPATH=src .venv/bin/python scripts/verify_mcp_gateway_foundation.py
```

## Prompt 04 - Historical Master Plan Banner / Non-Authoritative Docs Hardening

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Fix only the old non-archived master-plan language lane.

Tasks:

1. Inspect `docs/master_plans/*` for wording such as:
   - `MCP-compatible Tool Broker and connector registry`
   - broad parity claims
   - runtime/tool/web/scanner/sandbox claims that conflict with active truth.
2. Prefer adding a clear top-of-file banner to each old master plan rather than rewriting historical content:
   - historical planning artifact
   - not active product truth
   - does not grant runtime authority
   - active truth lives in README, product release truth packet, current board, and relevant foundation docs.
3. If there is an existing archive convention, follow it. Do not move files unless the repo already has stable references or you update all references safely.
4. Update docs indexes only if needed.

Constraints:

- Do not erase historical records.
- Do not retcon release history.
- Do not make public beta, production, or broad runtime claims.

Run:

```bash
.venv/bin/python scripts/verify_documentation_integrity.py
PYTHONPATH=src .venv/bin/python scripts/verify_a2a_gateway_foundation.py
PYTHONPATH=src .venv/bin/python scripts/verify_mcp_gateway_foundation.py
```

## Prompt 05 - Final Review, Guardrails, And Regression Sweep

You are working in `/Users/sambehdjou/Documents/GitHub/ultimate-ai-agent`.

Review the compatibility drift remediation after implementation.

Tasks:

1. Search active docs and source for overclaiming phrases:
   - `A2A support`
   - `MCP support`
   - `A2A runtime support`
   - `MCP runtime support`
   - `delegation-ready`
   - `callable MCP`
   - `official Agent Card`
   - `MCP-compatible`
   - `production-ready`
   - `public beta`
2. Confirm every surviving claim is either:
   - active and evidenced, or
   - explicitly marked metadata/import foundation, blocked, planned, historical, or non-authoritative.
3. Confirm schemas match live models or have an explicit wrapper verifier.
4. Confirm exact approval evaluators enforce all promised exact refs.
5. Confirm no new runtime imports/calls were added for web, provider SDKs, browser automation, MCP clients, A2A transport, subprocess/shell lanes, or plugin runtime import.

Run:

```bash
PYTHONPATH=src .venv/bin/python scripts/verify_compatibility_schema_drift.py
PYTHONPATH=src .venv/bin/python scripts/verify_a2a_gateway_foundation.py
PYTHONPATH=src .venv/bin/python scripts/verify_mcp_gateway_foundation.py
PYTHONPATH=src .venv/bin/python scripts/verify_agent_runtime_compatibility.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_a2a_gateway_foundation.py tests/test_mcp_gateway_foundation.py tests/test_a2a_adapter_boundaries.py tests/test_sdk_adapter_boundaries.py tests/test_provider_manifests.py tests/test_extension_activation_grants.py -q
.venv/bin/python scripts/verify_documentation_integrity.py
```

Final report format:

- Summary of actual fixes.
- Files changed.
- Tests/verifiers run and results.
- Any skipped checks and why.
- Remaining blocked items, especially official A2A protocol compatibility, callable MCP/A2A runtime, and public support claims.
