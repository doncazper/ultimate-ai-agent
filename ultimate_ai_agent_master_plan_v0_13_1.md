# Ultimate AI Agent Master Plan v0.13.1

Status: Active baseline after the M9 loopback policy hardening patch.

## v0.13.1 Change Log

Implemented:

```text
Unconditional non-loopback endpoint denial in LocalLoopbackModelRuntimeAdapter
Loopback-only filtering for caller and endpoint allowed_hosts intersection
Explicit reason code for attempted deny_non_loopback=false override
Direct adapter regression coverage for remote and private LAN bypass attempts
API regression coverage for hostile endpoint policy payloads
Foundation Gate M9 policy override criterion
```

## Rule

Local runtime execution is not production authority. It is dev-only, loopback-only, approval-gated, and non-authoritative. Caller policy can narrow the loopback endpoint boundary, but it cannot expand the boundary to remote hosts or private LAN hosts.

## Non-Goals

v0.13.1 does not add cloud model execution, provider SDKs, API keys, secret reads, remote hosts, tokenizers, billing APIs, scanners, browser automation, SDK/A2A runtime delegation, production persistence, production auth/OAuth, or external actions.

## Roadmap Pointer

The active roadmap lives at `docs/canonical/09_roadmap.md`. Versioned master plans are historical context. If this master plan and a canonical file disagree, the active canonical file wins.
