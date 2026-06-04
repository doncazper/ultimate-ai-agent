# File Capability Boundary Matrix

Status: active M34 documentation.
Current through: **v0.38.0**.

M34 is planning/review only. This matrix defines the allowed sequence for
broader file capability work. A future milestone may implement only its own
row's allowed scope after tests, static verifiers, Foundation Gate coverage,
documentation, and release review are added.

| Capability | Current status | Earliest possible milestone | Allowed now? | Required approval? | Raw content allowed? | Storage allowed? | Backend route allowed? | UI allowed? | Tests/gates required |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Filesystem metadata | implemented M32 | M32 | yes, metadata-only | tool runtime policy, not approval authority | no | safe metadata result only | no new route | existing summary surfaces only | path policy, no raw content, no mutation, OpenAPI count |
| Redacted preview | implemented M33 | M33 | yes, bounded redacted preview only | tool runtime policy, not approval authority | no | redacted result and no-raw receipt only | no new route | no raw preview control | redaction-before-return, safe root, relative path, no raw/full/hash/list/mutation |
| Review packet | planned/provisional | M35 | no | future exact review packet binding | no | future no-raw review packet metadata only | no in M35 unless separately reviewed; default no | no until M36 | packet contract, redaction verification, model_copy revalidation, no authority |
| Approval capture | planned/provisional | M37 | no | yes, exact actor/resource/scope/replay-safe review approval | no | review-only audit persistence only | no public mutation route before separate review | no approve controls before M37 | exact packet binding, expired/revoked/replayed denial, no execution authority |
| Context proposal | planned/provisional | M38 | no | future handoff review approval, not injection | no | proposal metadata only | no context injection route | no until M39 | no injection, no memory write, no model/OpenWebUI handoff |
| File review UI surface | planned/provisional | M36 | no | review-only UI cannot authorize | no | local UI state only unless future reviewed | no backend route in M36 by default | review-only in M36 | no raw/copy/export/approve/inject/execute controls, mock redaction tests |
| Mobile review surface | planned/provisional | M49 | no | future mobile review approval only | no | future audit-only reviewed metadata | no before mobile API review | no before M44-M50 | mobile no-sensor/no-authority gates |
| Export/download/copy raw | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | raw export denial, UI control denial, route denial |
| Raw read | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | raw route denial, result contract denial, verifier deny-list |
| Full read | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | full-file denial, reconstruction risk checks |
| File write | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | mutation denial, route denial, side-effect gate |
| File delete | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | deletion denial, route denial, side-effect gate |
| Directory listing | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | listing/recursive traversal denial |
| Shell/subprocess | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | shell/subprocess source scan |
| Network tools | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | request/http/socket scan |
| Provider/model calls as authority | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | model/provider authority denial |
| Browser/mobile/plugin execution | blocked | after M60 only by reviewed roadmap patch | no | not applicable | no | no | no | no | browser/mobile/plugin execution denial |

## Hard Boundary

Raw file access, full-file reads, export/download/copy-raw behavior, file
writes/deletes, context injection, memory writes, shell/subprocess execution,
network/provider/model calls as authority, and arbitrary caller-selected roots
remain blocked until a later reviewed roadmap patch explicitly changes the
boundary.
