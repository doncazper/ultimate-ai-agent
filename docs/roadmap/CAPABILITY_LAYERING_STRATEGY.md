# Capability Layering Strategy

Status: Active roadmap projection for v0.19.0. Documentation only.

This strategy defines the post-M20 layering order for future capability work. It does not implement runtime execution, model calls, tools, memory writes, native clients, sensors, browser automation, plugin enablement, dependencies, or external actions.

## Layer 1 - Core Authority

The Python Agent Core remains the brain and authority layer.

Layer 1 includes:

- Python Agent Core.
- Execution Contract.
- Approval Authority.
- Consent Ledger.
- Tool Broker.
- Event Ledger.
- Secret Broker.
- Foundation Gate.

No future surface may bypass this layer. Model output, memory recall, plugin output, remote worker output, mobile sensor output, browser output, and external tool output are not authority.

## Layer 2 - Read-Only/Preview UI

Layer 2 includes governance and review surfaces before action authority expands.

Layer 2 includes:

- Control Center Web.
- OpenWebUI strategy docs.
- receipts/events/evidence viewers.

These surfaces must remain read-only, preview-only, or review-only until a dedicated milestone grants scoped authority through Python Agent Core.

## Layer 3 - Conversational Shell

Layer 3 defines how chat can enter the governed agent boundary.

Layer 3 includes:

- OpenWebUI bridge contracts.
- chat session refs.
- safe transcript refs.

OpenWebUI remains the preferred conversational web shell. It is not the agent brain and must not bypass Python Agent Core.

## Layer 4 - Local Model Runtime

Layer 4 defines bounded local inference after runtime boundaries exist.

Layer 4 includes:

- local runtime activation contract.
- local-only LLM calls.
- no tools or memory writes initially.

The first local LLM call must be non-tool, non-authoritative, local-only, receipt-backed, and unable to mutate memory or execute actions.

## Layer 5 - Memory/Truth/Evidence

Layer 5 introduces recall and claim inspection after provenance and review rules are clear.

Layer 5 includes:

- MemoryProvider abstraction.
- local memory store.
- truth source router.
- evidence claim checking.

Memory is recall, not authority. Truth source routing and evidence checks must keep model claims inspectable and non-authoritative until supported by governed sources.

## Layer 6 - Tools/Skills/Sandboxes

Layer 6 introduces tool lifecycle contracts before execution.

Layer 6 includes:

- tool execution sandbox contracts.
- MCP/Agent Skills/AGENTS.md trust registry.
- sandbox backend abstraction.
- dry-run tool previews.
- first approved local low-risk tool.

Tools must start as contracts, quarantine, static policy, dry-run previews, and approval requests before any real low-risk local execution is allowed.

## Layer 7 - Native/Mobile/Desktop Clients

Layer 7 plans client contracts after web and chat surfaces are stable.

Layer 7 includes:

- CCC iOS.
- CCC Android.
- CCC macOS.
- device pairing/trust handshake.
- mobile approval surface.

CCC native clients are control surfaces, not the agent brain. Native client implementation requires dedicated milestones and explicit tooling approval.

## Layer 8 - Device Capabilities/Sensors

Layer 8 governs device capability access after contracts, pairing, and approval surfaces exist.

Layer 8 includes:

- Device Capability Broker implementation.
- selected capture inbox.
- one governed sensor capability at a time.

Mobile sensors must not appear before the Device Capability Broker. Selected capture must be user-reviewed and must not become automatic memory writes.

## Layer 9 - Browser/Computer-Use

Layer 9 plans browser and computer-use style actions after approvals, sandboxing, and dry-run behavior are mature.

Layer 9 includes:

- browser automation contract.
- browser-only automation first.
- full Computer Use much later.

Browser automation starts as contracts and dry-run plans only. Full Computer Use remains out of scope until a later reviewed milestone.

## Layer 10 - Observability/Evals

Layer 10 keeps autonomy measurable before capability expansion.

Layer 10 includes:

- observability export adapters.
- eval/regression harness.
- red-team/security suites.

Observability and evals must exist before higher autonomy claims. Exports must be redacted, opt-in, and local-first unless a future milestone approves otherwise.

## Anti-Patterns

The roadmap must avoid these orders:

- no model before runtime boundaries.
- no tools before sandbox.
- no mobile sensors before Device Capability Broker.
- no OpenWebUI bridge before Core authority contract.
- no plugins/MCP before trust lifecycle.
- no browser/computer-use before approvals/sandboxing.
- no autonomy before evals/observability.

These anti-patterns are roadmap constraints, not implemented capability.
