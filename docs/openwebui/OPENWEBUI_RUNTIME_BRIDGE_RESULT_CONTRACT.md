# OpenWebUI Runtime Bridge Result Contract

M76 returns an OpenWebUI Runtime Bridge v1 review-only bridge envelope. The
envelope carries safe refs, a safe bridge summary, stable reason codes, and a
receipt plan. It is redacted summary only.

The envelope returns no raw prompt, no raw provider payload, no raw content, no
model authority, no live OpenWebUI connection, no OpenWebUI runtime call, no
provider call, no model call, no tool execution, no memory write, no context
injection, no network call, no credentials or cookies, no backend route, no
Control Center control, no dependency, and no production authority.

`M76_OPENWEBUI_RUNTIME_BRIDGE_V1` identifies the valid review envelope.
`M77_REMAINS_FUTURE` keeps OpenWebUI safe handoff execution out of M76.

Evaluator boundaries revalidate result fields before the envelope is accepted
for review.
