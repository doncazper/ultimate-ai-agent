# M41 to M42 Boundary

Status: Active boundary after v0.45.0 / M41 - Local Prototype Safety Freeze.

M41 is a local prototype safety freeze. It adds documentation, static
verification, documentation-integrity checks, and Foundation Gate coverage for
the current local prototype posture. It does not start mobile implementation.

M42 remains future and is limited to Mobile Companion Product Contract Refresh
when it begins. M41 adds no CCC iOS app, Android app, macOS app, mobile sensor
access, OS permission integration, background service, notification runtime,
device pairing runtime, TestFlight pipeline, native build workflow, or mobile
approval authority.

The through-M60 blocked list remains active:

- no raw file browsing
- no raw file export
- no full-file reads
- no arbitrary caller-selected roots
- no shell/subprocess
- no unrestricted network tools
- no provider/model calls as authority
- no background workers
- no mobile sensors
- no plugin enablement
- no production authority
- no unreviewed memory writes
- no automatic context injection
- no raw prompt/provider payload exposure
- no credentials/cookie handling
- no remote execution
- no browser automation execution

Approval refs are not authority. Browser smoke review is local-only and remains
inspection-only.
