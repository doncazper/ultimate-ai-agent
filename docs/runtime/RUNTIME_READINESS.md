# Runtime Readiness

Status: Active M11 readiness/report validation contract, v0.15.1

M11 adds a typed runtime readiness report generated from local known contract state only. It is not a production health check, not a runtime launcher, and not evidence that a model/provider/runtime is safe to call.

The readiness report may say:

- simulated runtime contracts exist.
- local loopback policy validation exists as a supported validation-only contract.
- manual local loopback smoke remains manual-only, fixed-prompt-only, approval-gated, and non-authoritative.
- remote worker foundation remains validation/status/dry-run only.
- private mesh, tailnet, Headscale, generic WireGuard, Tailscale, mobile companion, Device Capability Broker, and Codex plugin enablement remain planned-disabled or blocked.

The readiness report must not say:

- production runtime is ready.
- real model execution is ready.
- remote execution is ready.
- live private mesh or tailnet is ready.
- mobile sensors are ready.
- Codex plugins, native build tools, Computer Use, or Chrome authenticated profile control are enabled.
- model output is truth authority.

Public API surface:

```text
GET /runtime/readiness
GET /runtime/capability-matrix
POST /runtime/smoke-reports/validate
```

These routes are status/validation only. No route executes, connects, dispatches, runs a provider call, enables a plugin, launches a native build, or performs a manual smoke call.

v0.15.1 clarifies that local loopback policy support does not imply automated smoke execution or production runtime readiness. Manual smoke remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative. `fake_manual_loopback_smoke` remains a fake/test report origin only.

## v0.18.4 Post-M20 Runtime Projection

v0.18.4 adds roadmap projection docs only. Future runtime work is planned/provisional in:

- M22 - Local Model Runtime Activation Contract.
- M23 - First Real Local LLM Call, Non-Tool, Non-Authoritative.
- v0.27.1 - Local LLM Call Hardening.

These milestones require dedicated implementation and review prompts. v0.18.4 adds no local model execution, provider call, network call, OpenWebUI bridge, tool use, memory write, or production readiness claim.
