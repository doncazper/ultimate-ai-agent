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
design tooling
OpenWebUI deployment/integration tooling
native Android build
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
- Android, Gradle, Android Studio, Play Store, signing, keystore, and Android device workflows remain disabled until a dedicated CCC Android implementation milestone.
- OpenWebUI deployment, admin/config, plugin, function, pipeline, tool, and bridge tooling remains disabled until a dedicated OpenWebUI integration milestone.
- CodeRabbit and GitHub read-only review can be used for release readiness with explicit review prompts.
- GitHub write, release, push, tag, or PR actions require explicit approval or direct-push rules.
- Computer Use remains disabled except explicit last-resort manual QA approval.
- Hugging Face Jobs, uploads, training, and Spaces deployment remain disabled.
- Plugin/skill installers remain disabled until Skill lifecycle security exists.
- Design tooling, including Figma, Stitch, Framer, screenshot-to-code, design-to-code, and AI UI generators, remains disabled unless a future milestone explicitly approves optional import/export use.
- Shell/exec commands are allowed narrowly for local verifier, test, grep, git, and script workflows only.

## Design Tooling

Design tools are development aids and are not authority. v0.18.2 records design governance in repo docs only:

- no design tools are enabled.
- no design SaaS is authority.
- no external design sync is enabled.
- no automatic design-to-code commit is allowed.
- design-to-code output must be reviewed like code.
- screenshots and design artifacts must be secret-free and treated as sensitive until reviewed.
- Browser may be used only for local UI verification under existing local browser smoke policy.
- Chrome authenticated profile control and Computer Use remain disabled.

## OpenWebUI Tooling

OpenWebUI deployment and integration tooling is future-only. OpenWebUI admin/config/deployment plugins, OpenWebUI plugins/functions/pipelines/tools, bridge helpers, and deployment automation must not be enabled without an explicit milestone.

Any future OpenWebUI bridge must be treated like external tool integration and pass Tool Broker, Approval Authority, Event Ledger, Secret Broker, Redaction, and Foundation Gate gates. It must not bypass Python Agent Core, access credentials directly, expose a public chat shell without security review, or depend on an external hosted OpenWebUI service without a reviewed contract.

v0.18.4 maps future OpenWebUI bridge work to M21 in `docs/roadmap/M21_M40_CAPABILITY_CHARTERS.md`. v0.25.0 implements M21 as contract/planning/validation only and does not enable deployment, plugins, functions, pipelines, tools, Docker Compose, or external exposure. v0.26.0 implements M22 contract-only. v0.27.0 implements M23 as manual fixed-prompt local call only and does not enable plugins, external exposure, or production authority.

## MCP/A2A Compatibility Watchlist

MCP/A2A compatibility is tracked in
`docs/tooling/MCP_A2A_COMPATIBILITY_WATCHLIST.md` as strategy/watchlist only.
It does not ship MCP/A2A runtime support and does not add runtime authority,
connector writes, plugin execution, broad tool invocation, network authority,
backend routes, OpenAPI paths, public distribution, or production authority.
Any later implementation must pass PolicyEngine, LocalApprovalAuthority, route
side-effect classification, OpenAPI checks, Foundation Gate checks, redaction,
audit, revocation, rollback, and release-evidence gates.

## Mobile and Desktop Build Plugins

iOS, Android, and macOS build plugins are future-only. They may involve Xcode, Gradle, Android Studio, native build systems, signing identities, provisioning profiles, keystores, keychains, simulator/device access, app entitlements, camera/microphone/location permissions, push notification credentials, App Store Connect credentials, and Play Store workflows. They must remain disabled until dedicated milestones define the approval and safety boundary.

v0.18.4 originally mapped future native client contracts to M31 and future
browser automation contracts to M38. v0.35.0 supersedes the old M31
native-client slot with M31 Real Tool Runtime Adapter, Single Safe No-Op Tool.
Native build plugin and browser automation work remains future
planned/provisional roadmap material. No native build plugin, browser
automation plugin, sandbox provider, MCP runtime, Agent Skills runtime, or
AGENTS.md runtime loading is enabled by v0.18.4.

## Source-of-Truth Boundary

External review tools, coding agents, build plugins, browser controllers, and cloud tools may assist development, but their outputs are not authoritative evidence. The model is never the source of truth. The project remains governed by canonical docs, API/runtime contracts, verifier scripts, Foundation Gate, and human approval.
## M19 Android and Native Tooling Boundary

v0.23.0 / M19 adds Mobile Companion Contract/API Planning only. Android tools
are future/high-risk. Gradle, Android Studio, Kotlin, Java, Play Store, and
keystore workflows require a future dedicated milestone and explicit
plugin/tooling approval. iOS tools remain future/high-risk. Swift, Xcode, App
Store Connect, signing, provisioning, and keychain workflows require future
approval. React Native, Expo, Flutter, Capacitor, and Ionic require future
approval. No tooling is enabled in M19.
