# Safe Media Metadata Policy

The M54 Safe Media Metadata Policy is metadata-only and review-only. It permits
safe declared metadata validation for supported image, video, and audio media
types without reading or exporting raw media.

The default policy enforces:

- no raw media export
- no raw media storage
- no full-file read
- no file mutation
- no original overwrite
- no OCIO transform
- no AI gamut expansion
- no model call
- no context injection
- no memory write
- no backend route
- no Control Center control
- no dependency
- no production authority

Unsupported media types are denied without raw media output. Secret-like
metadata is denied. Caller policy cannot downgrade these boundaries.

M55 remains future.
