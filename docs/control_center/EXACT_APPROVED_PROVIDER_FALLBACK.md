# Exact-Approved Provider Fallback

Status: core and CLI lane for two named exact-approved provider adapters only.

This lane allows fallback across the two proven tiny provider adapter scopes:
OpenAI-compatible and Anthropic-compatible. It is not a broad provider router,
not autonomous/background execution, not billing authority, and not a Control
Center toggle.

Every fallback attempt must carry its own exact scope:

- provider ref
- model ref
- credential ref
- approval ref and approval scope ref
- cost estimate ref
- budget decision ref
- max approved USD ref and value
- idempotency ref
- expected receipt ref
- usage and cost receipt refs
- redacted input and output summary refs
- safe-disable ref

Fallback uses `evaluate_exact_approved_provider_fallback()` in
`src/ultimate_ai_agent/core/providers/fallback.py`. CLI inspection is available
through `scripts/inspect_exact_approved_provider_fallback.py`.

The lane stops on the first successful complete redacted receipt. If an attempt
has unknown paid cost, missing exact refs, missing approval, missing receipt, or
incomplete actual usage/cost metadata, fallback stops fail-closed. Incomplete
actual paid cost requires review before any further provider use.

The Provider Router Dry-Run lane remains proposal-only. Its visibility and
recommended refs do not authorize fallback execution.

This lane stores only redacted refs and receipt metadata. It does not persist
raw prompts, raw responses, raw provider payloads, credentials, logs, local
paths, usernames, hostnames, environment dumps, or secrets. It adds no provider
SDK calls, no broad provider routing, no unbounded fallback, no background or
autonomous model calls, no billing authority, no provider output authority, and
no production authority.
