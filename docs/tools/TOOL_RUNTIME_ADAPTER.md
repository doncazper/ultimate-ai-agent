# Tool Runtime Adapter

Status: active M33 documentation.
Current active baseline: **v0.37.1**

M31 introduced the first governed Tool Runtime Adapter path. M32 extended that
path with one safe local filesystem metadata tool. M33 adds one bounded
redacted file preview proposal tool.

Allowed runtime tools in M33:

- `tool:no_op.v1` with `tool_name="noop"`.
- `tool:filesystem_metadata.v1` with `tool_name="filesystem_metadata"`.
- `tool:filesystem.redacted_preview.v1` with
  `tool_name="redacted_file_preview"`.

The adapter remains allowlist-only. It does not dispatch arbitrary tools,
load caller-selected modules or callables, run shell/subprocess commands, call
networks or models, mutate files, write memory, use browser/mobile/remote/plugin
actions, add backend execute routes, or create production authority.

M32 filesystem metadata lookup is metadata-only and safe-root-bound. It may
return safe path refs, existence, kind, size, extension, and modified-time
metadata. It must not return raw content, text previews, content hashes,
directory listings, recursive traversal results, symlink targets, or absolute
local paths.

M33 redacted file preview is bounded, safe-root-bound, relative-path-only, and
redacted-preview-only. It may read a small internal byte window solely for
redaction-before-return. It must not return or store raw file content, return a
full file, compute content hashes, list directories, follow symlinks, mutate
files, or perform context injection.

Approval refs, approval decisions, tool intents, task plans, execution state
transitions, context packs, memory refs, model output, runtime output,
OpenWebUI output, Control Center refs, and arbitrary strings are not authority
for filesystem metadata access, redacted preview access, or arbitrary tools.

M34-M40 remain planned/provisional.
