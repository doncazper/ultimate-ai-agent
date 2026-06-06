# OpenWebUI Safe Handoff Policy

M77 policy allows only OpenWebUI safe handoff execution inside Python Agent
Core. The policy requires safe summary only, exact approval binding, and Agent
Core authority.

The policy denies no live OpenWebUI connection, no OpenWebUI runtime call, no
provider call, no model call, no model authority, no tool execution, no memory
write, no context injection, no network call, no credentials or cookies, no raw
prompt, no raw provider payload, no raw content, no backend route, no Control
Center control, no dependency, and no production authority.

OpenWebUI is a shell/bridge, not the brain. Agent Core remains authority.
Evaluator boundaries revalidate the policy before any safe handoff result is
built.

M78 remains future.
