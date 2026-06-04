# Tool Runtime Adapter

Status: active M32 documentation.
Current active baseline: **v0.36.0**

M31 introduced the first governed Tool Runtime Adapter path. M32 extends that
path with exactly one safe local filesystem metadata tool.

Allowed runtime tools in M32:

- `tool:no_op.v1` with `tool_name="noop"`.
- `tool:filesystem_metadata.v1` with `tool_name="filesystem_metadata"`.

The adapter remains allowlist-only. It does not dispatch arbitrary tools,
load caller-selected modules or callables, run shell/subprocess commands, call
networks or models, mutate files, write memory, use browser/mobile/remote/plugin
actions, add backend execute routes, or create production authority.

M32 filesystem metadata lookup is metadata-only and safe-root-bound. It may
return safe path refs, existence, kind, size, extension, and modified-time
metadata. It must not return raw content, text previews, content hashes,
directory listings, recursive traversal results, symlink targets, or absolute
local paths.

Approval refs, approval decisions, tool intents, task plans, execution state
transitions, context packs, memory refs, model output, runtime output,
OpenWebUI output, Control Center refs, and arbitrary strings are not authority
for filesystem metadata access or arbitrary tools.

M33-M40 remain planned/provisional.
