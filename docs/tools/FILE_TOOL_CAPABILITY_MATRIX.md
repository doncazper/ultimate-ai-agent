# File Tool Capability Matrix

Status: active M34 documentation.
Current through: **v0.38.0**.

| Tool ref | Status | Capability | Raw content | Mutation | Routes | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `tool:no_op.v1` | implemented M31 | deterministic no-op | no | no | no new route | safe no-side-effect runtime adapter proof |
| `tool:filesystem_metadata.v1` | implemented M32 | safe-root metadata only | no | no | no new route | no preview, hash, listing, symlink following, caller root, or mutation |
| `tool:filesystem.redacted_preview.v1` | implemented M33 | bounded redacted preview | no | no | no new route | redaction-before-return, no full-file output, no context injection |
| future review workflow contracts | planned M35 | review packet contracts | no | no | no route by default | contracts only, no CCC UI or approval persistence |
| arbitrary raw-read tool | blocked | not allowed | no | no | no | requires later reviewed roadmap patch after M60 |
| arbitrary write/delete tool | blocked | not allowed | no | no | no | requires later reviewed roadmap patch after M60 |

Approval refs, tool intents, task plans, context packs, memory refs, model
output, runtime output, OpenWebUI output, Control Center refs, and arbitrary
strings cannot authorize arbitrary file tools.
