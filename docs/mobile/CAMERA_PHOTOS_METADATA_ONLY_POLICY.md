# M103 Camera/Photos Metadata-Only Policy

M103 policy is contract-only and metadata-only. It requires camera and photos to
remain off by default, safe metadata refs, raw media denial, consent,
revocation, audit, exact scope, and evaluator revalidation of safety-critical
fields.

Denied policy states:

- no camera runtime access
- no photo library runtime access
- no image capture
- no video capture
- no raw media content
- no precise EXIF location
- no face recognition
- no OCR
- no media export
- no native permission prompt
- no background media collection
- no backend route
- no Control Center control
- no dependency
- no memory write
- no context injection
- no execution
- no production authority

Safe metadata refs are descriptive identifiers only. They cannot authorize media
reads, raw absolute paths, EXIF precise location use, face recognition, OCR,
exports, permission prompts, background collection, or M104 work. M104 remains
future.
