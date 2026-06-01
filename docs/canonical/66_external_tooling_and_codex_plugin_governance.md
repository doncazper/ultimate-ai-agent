# 66 - External Tooling and Codex Plugin Governance

Status: Canonical governance policy, v0.14.6

External tools, Codex plugins, build systems, review services, browser controllers, computer-use tools, cloud job systems, and plugin installers are development aids. They are not the Ultimate AI Agent core authority, not the source of truth, and not permission to bypass Agent Core governance.

## Core Rule

Codex plugins must be treated like future Tool Broker capabilities. Before use, every plugin or tool class must be classified by risk and scoped to a milestone, purpose, permission boundary, test plan, rollback plan, and approval.

Inventory is allowed. Enablement requires explicit approval.

## Plugin Categories

```text
review-only
docs/artifact generation
web UI build/test
native mobile build
native desktop build
browser authenticated profile control
computer use
cloud compute/training
plugin/skill installation
```

## Enablement Requirements

Before enabling a high-risk or critical plugin, record:

```text
purpose
scope
files affected
permissions
network access
credential/keychain access
artifact outputs
test plan
rollback plan
approval
```

Build, signing, deployment, simulator, device, browser-authenticated, computer-use, cloud-compute, and plugin-install tools require explicit milestone approval.

## Default Rule

```text
inventory anytime
enable only inside explicit milestone
high/critical tools require review gate
```

No plugin may bypass:

```text
Execution Contract
Context Pack
Approval Authority
Tool Broker
Event Ledger
Secret Broker
redaction
verifier scripts
Foundation Gate
```

## Current Decisions

- Browser + Build Web Apps may be considered for future Web Control Center work with approval.
- Chrome authenticated profile control remains disabled unless explicitly approved.
- Build iOS Apps / XcodeBuildMCP remains disabled until a dedicated Mobile Companion implementation milestone.
- Build macOS Apps remains disabled until a dedicated Desktop/macOS Companion milestone.
- CodeRabbit and GitHub read-only review can be used for release readiness with explicit review prompts.
- GitHub write, release, push, tag, or PR actions require explicit approval or direct-push rules.
- Computer Use remains disabled except explicit last-resort manual QA approval.
- Hugging Face Jobs, uploads, training, and Spaces deployment remain disabled.
- Plugin/skill installers remain disabled until Skill lifecycle security exists.
- Shell/exec commands are allowed narrowly for local verifier, test, grep, git, and script workflows only.

## Mobile and Desktop Build Plugins

iOS and macOS build plugins are future-only. They may involve Xcode, native build systems, signing identities, provisioning profiles, keychains, simulator/device access, app entitlements, camera/microphone/location permissions, push notification credentials, and App Store Connect credentials. They must remain disabled until dedicated milestones define the approval and safety boundary.

## Source-of-Truth Boundary

External review tools, coding agents, build plugins, browser controllers, and cloud tools may assist development, but their outputs are not authoritative evidence. The model is never the source of truth. The project remains governed by canonical docs, API/runtime contracts, verifier scripts, Foundation Gate, and human approval.
