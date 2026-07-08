# UAA Runtime Extensibility Final

Status: Phase 09 implemented as read-only ecosystem hardening.

This document closes the UAA runtime capability foundation prompt pack with an
extension and capability ecosystem posture that is useful to inspect without
becoming runtime authority. External runtime examples remain read-only references for
product and architecture patterns; UAA does not copy external reference code, import
external runtime packages, or adopt broad extension execution.

## Implemented Slice

UAA now exposes explicit operator posture fields through the existing
backend-owned inspectable extension catalog:

- visibility status
- trust posture
- callable posture
- required grant refs
- blocked reason
- review evidence refs
- safe adoption posture
- install-disabled posture with AuthorityLease decision refs, exact approval
  requirement, hash refs, receipt plan refs, rollback refs, safe-disable refs,
  and blocked capability refs
- exact disabled-install record receipts plus an idempotent caller-supplied
  local disabled-record store, available only after active `workspace/write`
  AuthorityLease scope and exact LocalApprovalAuthority validation

Canonical core/API/CLI refs:

- `src/ultimate_ai_agent/core/extension_catalog/contracts.py`
- `src/ultimate_ai_agent/core/extension_catalog/install_disabled.py`
- `src/ultimate_ai_agent/core/extension_catalog/runtime.py`
- `GET /extensions/catalog`
- `POST /extensions/disabled-install-records`
- `scripts/dev/uaa_extensions.py inspect-catalog`
- `scripts/dev/uaa_extensions.py inspect-install-disabled-posture`
- `scripts/dev/uaa_extensions.py record-install-disabled-receipt`
- `scripts/verify_uaa_runtime_extensibility_final.py`
- `tests/test_runtime_extensibility_final.py`

The catalog uses safe refs and redacted summaries. It does not expose raw
package contents, raw manifests, raw local paths, raw logs, raw prompts, raw
responses, raw provider payloads, account material, credentials, cookies,
tokens, or private content.

## Visibility Is Not Callability

The catalog is visible because operators need to know why a capability exists,
why it is trusted or blocked, and what later authority would be required. It
is not a callable catalog.

Current posture:

| Surface | Status | What The Operator Can Inspect | Runtime Authority |
|---|---|---|---|
| Plugin/skill boundary metadata | implemented | package refs, reviewed hash refs, review refs, blocker refs, adoption posture | none |
| Unknown extension candidate | blocked | unknown provenance, missing review, blocked grant refs, blocked reason | none |
| Disabled install posture | implemented | exact approval requirement, workspace/write AuthorityLease decision refs, reviewed hash refs, receipt plan refs, rollback and safe-disable refs | default catalog remains read-only; disabled-install record receipt/local store path is available only when lease and exact LocalApprovalAuthority approval validate |
| Activation grant records | partial | exact-scope grant and revocation record shapes | record-only; no runtime import |
| MCP/A2A compatibility | planned | watchlist and future questions | none |
| Static package review | planned | future package review posture | none |
| Callable catalog | blocked | blocked reason refs only | none |

Plugin runtime import remains blocked. Connector writes remain blocked.
Production authority remains blocked. Broad autonomy remains blocked. Plugin
package install persistence and callable activation also remain blocked. The
disabled-record store is metadata-only and must not be treated as package
install, enablement, runtime import, execution, or production authority.

## Future Activation Grant Contract

Future extension activation work must remain exact-scoped, expiring,
auditable, revocable, and deny-by-default. A future grant cannot rely on a
catalog entry alone. It must prove:

- exact package, manifest, version, capability, actor, approval, and scope refs
- safe-disable and revocation posture
- idempotency and duplicate-grant handling
- audit and receipt refs
- rollback or rollback-readiness posture
- redaction behavior
- CLI/API/Core parity
- route side-effect classification and OpenAPI alignment
- Foundation Gate and focused verifier coverage

Approval refs are identifiers only. They do not become authority unless the
exact LocalApprovalAuthority scope is validated by a later accepted runtime
milestone.

## Developer Guidance

UAA-native capabilities must start as reviewed metadata before any runtime
behavior is considered. A capability author should:

1. Define the capability as safe-ref metadata.
2. Separate inspectable catalog visibility from callable runtime behavior.
3. Add docs, schema, tests, and verifier coverage before UI claims.
4. Keep Control Center as presentation/initiation only.
5. Add CLI/API/Core parity for every operator-relevant workflow.
6. Prove redaction, approval binding, idempotency, receipts, rollback posture,
   route classification, OpenAPI stability, and product-language accuracy.
7. Keep blocked lanes visible instead of presenting missing authority as
   shipped capability.

Do not add plugin install, plugin enablement, plugin execution, remote MCP
execution, connector writes, live web fetching, browser automation, arbitrary
shell execution, provider/model calls, remote execution, public release
claims, production authority, or broad autonomy through an ecosystem surface.

## Final 30-Day Plan

| Rank | Recommendation | Impact | Effort | Risk | Authority Needed | First Step |
|---:|---|---|---|---|---|---|
| 1 | Productize one end-to-end operator loop from Today to Action to Proof to Memory. | high | medium | medium | exact local lanes only | Add a single read model that shows run, approval, receipt, evidence, and memory refs together. |
| 2 | Add signed portable evidence export for local receipts. | high | medium | medium | local evidence export lane | Define verifier version, hash refs, approval refs, policy decision, and redacted envelope contract. |
| 3 | Harden RuntimeGateway decision traces before live provider expansion. | high | medium | high | metadata/read-only first | Bind turn router, runtime readiness, model/provider posture, and proof refs without runtime model calls. |
| 4 | Add static package review for repo-owned extension samples. | medium | medium | medium | read-only package review | Produce reviewed hash/provenance records and blocker refs without install/import. |
| 5 | Add extension trust UI over `GET /extensions/catalog`. | medium | low | low | read-only Control Center surface | Render visibility, trust, callable posture, blocked reason, and adoption posture from backend data. |
| 6 | Define the first exact callable capability lane. | medium | high | high | later scoped approval | Pick one safe local capability and prove approval, receipts, rollback, CLI/API/Core parity, and tests. |
| 7 | Add MCP/A2A contract conformance checks. | medium | medium | medium | metadata/read-only only | Validate manifests and compatibility records without remote execution. |
| 8 | Improve developer docs for capability authors. | medium | low | low | none | Add a template that requires blocked-authority and redaction sections. |

## Final Hardening Result

The Phase 09 hardening keeps the full-strength ecosystem goal visible while
shipping only the repo-safe posture: inspectable metadata, trust labels,
blocked reasons, safe adoption posture, CLI/API/Core parity, docs, tests, and
verifier coverage.

Still blocked:

- plugin runtime import
- plugin package install persistence
- skill runtime import
- callable catalog execution
- connector writes
- live web fetching
- browser automation
- arbitrary shell/subprocess execution
- provider/model calls
- remote execution
- public release claims
- production authority
- broad autonomy

This phase adds no new runtime authority.
