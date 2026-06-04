# M32 to M33 Boundary

Status: active M32 documentation.
Current active baseline: **v0.36.0**

M32 is implemented/released as Safe Local Filesystem Metadata Tool.

M32 adds exactly one runtime expansion beyond no-op:

```text
tool:filesystem_metadata.v1
```

That tool is metadata-only under server-owned safe roots. It does not add file
content reads, text previews, content hashes, directory listing, recursive
traversal, symlink following, file mutation, shell/subprocess execution, memory
writes, network calls, model/provider calls, backend execution routes, Control
Center execute controls, dependencies, or production authority.

M33 remains planned/provisional as Mobile Approval Surface Prototype, No
Sensors. M33-M40 remain planned/provisional. M32 does not add mobile native
code, mobile sensors, device pairing, notifications, background services,
mobile approval execution, or native client runtime authority.
