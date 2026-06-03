# Safe Tool Intent Contracts

Status: active
Current through: v0.32.0
Purpose: Define safe M27 tool intent, target, input, and catalog contracts.

Safe tool intents are structured metadata contracts. They use refs and safe
summaries, not raw payloads.

M27 requires:

- structured `intent_id` refs.
- structured target refs.
- target_ref/target_kind consistency.
- safe input refs.
- explicit input trust level.
- explicit declared risk class.
- explicit declared side effects.
- catalog-backed risk and side-effect comparison.
- fixed sanitized denial messages.

M27 denies:

- unknown tools.
- unknown target refs.
- target ref/kind mismatches.
- caller-declared risk downgrades.
- hidden side effects.
- approval refs as authority.
- context-pack refs as authority.
- raw input content.
- secret-like input content.
- model output as tool input.
- runtime output as tool input.
- OpenWebUI output as tool input.

Caller metadata cannot upgrade authority. A low declared risk cannot downgrade a
catalog high-risk tool, and declared `none` side effects cannot hide catalog
side effects.
