# Foundation Gate Implementation Plan v0.16.0

Status: Active M12 gate plan.

M12 extends the Foundation Gate to verify the Control Center backend/API contract without adding a frontend, execution capability, plugin enablement, native build workflow, runtime calls, model/provider calls, remote dispatch, or mobile sensor access.

Gate checks include:

- Control Center contract files, tests, and docs exist.
- manifest surfaces are deterministic and read-only, preview-only, validation-only, planned-disabled, blocked, or not implemented.
- dashboard snapshots contain safe summaries only and do not expose raw events, prompts, files, memory, credentials, PII, or secret-like values.
- action preview blocks execution, mutation, credentials, arbitrary approval authority, runtime/model/provider calls, remote dispatch, plugin enablement, and mobile sensor claims.
- public API exposes only the eight M12 read-only/preview-only `/control-center/*` routes.
- public API exposes no Control Center execute, plugin-enable, runtime-execute, remote-dispatch, mobile-sensor, or frontend route.
- no frontend package files, node modules, React/Next/Vite/shadcn/Tailwind configs, native build workflows, Browser/Chrome/Computer Use bridges, plugin APIs, provider SDKs, tokenizers, billing APIs, or network calls are added.
- OpenAPI operation IDs remain unique and forbidden route fragments remain absent.

The gate must remain deterministic and local. It must not inspect live Codex plugin state, keychains, signing identities, local runtime processes, mobile devices, remote hosts, provider credentials, browser sessions, Chrome profiles, or app build tools.

## Skill Package Security Rule

All skills are untrusted packages by default until the repository has a manifest, declared permissions, source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping, Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

M12 does not add Skill Factory, skill loading, plugin loading, installer behavior, marketplace behavior, frontend build tooling, native build tooling, or runtime execution through skills. The rule remains a release gate for future capability work.
