# Foundation Gate Implementation Plan v0.58.0

v0.58.0 adds Foundation Gate coverage for M54 Safe Media Metadata Inspector.

All skills are untrusted packages by default. Coverage continues the Skill Package Security Rule language requiring a manifest, declared permissions,
source/provenance metadata, static review, sandbox test execution, Tool Broker permission mapping,
Event Ledger logging, version pinning, revocation/disable support, and human approval for high-risk capabilities.

Gate checks verify that the media metadata inspector exists, accepts safe
declared metadata-only requests, denies unsupported media types without raw
media output, rejects raw media export/storage, full-file read, file mutation,
original overwrite, OCIO transform, AI gamut expansion, model call, context
injection, memory write, backend route, dependency, and production authority
flags, and keeps M55 future.

Static verification checks scan for raw media, transform, model-call, export,
context, memory, execution, dependency, and backend route drift. OpenAPI remains
at the accepted route boundary.
