# Ultimate AI Agent Version

Current active baseline: **v0.15.1**

v0.15.1 clarifies the M11 runtime readiness taxonomy on top of v0.15.0. It keeps `local_loopback_policy` as a supported validation-only contract while explicitly stating real smoke execution remains manual-only, approval-gated, fixed-prompt-only, and non-authoritative. It also documents `fake_manual_loopback_smoke` as a fake/test report origin only. This patch adds no runtime execution, cloud/provider calls, remote execution, live private mesh/tailnet support, Headscale/Tailscale/WireGuard calls, mobile sensor access, plugin/tool enablement, dependencies, routes, or production readiness claims.
