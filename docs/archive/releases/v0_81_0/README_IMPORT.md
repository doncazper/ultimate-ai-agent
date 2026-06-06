# README Import - v0.81.0

Current active baseline: **v0.81.0**.

v0.81.0 implements M77 - OpenWebUI Safe Handoff Execution. It records exact-bound
Agent Core safe handoff results over safe refs only and keeps OpenWebUI as a
shell/bridge, not the brain.

No live OpenWebUI connection, OpenWebUI runtime call, provider call, model call,
model authority, tool execution, memory write, context injection, network call,
credentials or cookies, raw prompt, raw provider payload, raw content, backend
route, Control Center control, dependency, M78 work, or production authority is
added.
