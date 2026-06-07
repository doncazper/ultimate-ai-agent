# Foundation Gate Implementation Plan v1.7.0

v1.7.0 adds M103 Foundation Gate checks for Camera/Photos Metadata-Only
Contract.

Coverage:

- M103 camera/photos metadata-only contracts exist and validate.
- camera and photos remain off by default.
- safe media refs and safe metadata refs are required.
- raw media content is denied.
- camera runtime access and photo library runtime access are denied.
- image capture and video capture are denied.
- precise EXIF location, face recognition, and OCR are denied.
- media export is denied.
- native permission prompts and background media collection are denied.
- backend route and Control Center control drift are denied.
- dependency drift, memory writes, context injection, execution, and production
  authority are denied.
- active roadmap docs mark M103 implemented/released and keep M104-M150
  planned/provisional.

## Skill Package Security Rule

All skills are untrusted packages by default. Any future skill package must have
a manifest, declared permissions, source/provenance metadata, static review,
sandbox test execution, Tool Broker permission mapping, Event Ledger logging,
version pinning, revocation/disable support, and human approval for high-risk capabilities
before it can be considered for later reviewed milestones.

M103 does not add skill package execution, plugin execution, external plugins,
runtime imports, backend routes, Control Center controls, dependencies, or
production authority.
