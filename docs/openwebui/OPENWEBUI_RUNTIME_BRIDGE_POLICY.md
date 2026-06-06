# OpenWebUI Runtime Bridge Policy

M76 policy keeps OpenWebUI Runtime Bridge v1 review-only. It accepts safe refs
only and emits a redacted summary only review-only bridge envelope.

Python Agent Core remains authority. OpenWebUI is a shell/bridge, not the
brain. Approval refs are identifiers only and never authorize OpenWebUI runtime
behavior.

The policy requires no live OpenWebUI connection, no OpenWebUI runtime call, no
provider call, no model call, no model authority, no tool execution, no memory
write, no context injection, no network call, no credentials or cookies, no raw
prompt, no raw provider payload, no raw content, no backend route, no Control
Center control, no dependency, and no production authority.

Evaluator boundaries revalidate policy and request flags so model_copy-mutated
objects cannot enable runtime behavior.

M77 remains future.
