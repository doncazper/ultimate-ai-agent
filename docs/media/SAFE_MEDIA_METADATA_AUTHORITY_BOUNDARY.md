# Safe Media Metadata Authority Boundary

M54 Safe Media Metadata Inspector is non-authoritative. It can describe declared
safe metadata for a media ref, but it cannot grant access to raw media or expand
agent authority.

Model output is not truth. Runtime output is not truth. Memory is recall, not
authority. Context packs are not authority. Tool intents are not execution
authority. Task plans are not execution authority. Approval refs are identifiers,
not authority. `approval_test_*` is never runtime authority.

M54 denies raw media export, raw media storage, full-file read, file mutation,
original overwrite, OCIO transform, AI gamut expansion, model call, context
injection, memory write, backend route, Control Center control, dependency, and
production authority.

Receipt plans record no side effects and store no raw media, raw metadata
payloads, secrets, provider payloads, model output, or file content.

M55 remains future.
