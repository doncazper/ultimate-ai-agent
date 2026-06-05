# CCC iOS Review/Receipt Read-Only Surfaces

Status: Active M46 source-only surface for v0.50.0.

v0.50.0 / M46 implements iOS Review/Receipt Read-Only Surfaces for the
source-only CCC iOS skeleton. The surface displays mock, non-authoritative,
redacted summary data for review packets and receipts. It is source-only,
read-only, redacted summary only, and has no runtime network call.

The M46 iOS source may display:

- redacted review packet summary text
- redacted receipt summary text
- mock non-authoritative status labels
- authority-boundary copy

M46 adds no backend route, no mobile API route runtime, no approval capture, no
approval execution, no raw data, no raw payload display, no raw absolute path
display, no context injection, no memory write, no file mutation, no export, no
execution, no background collection, no mobile sensor access, no credential
handling, no cookie handling, and no production authority.

Safety summary: no approval capture, no approval execution, no raw data, no
context injection, no memory write, no file mutation, no export, no execution,
no background collection, no mobile sensor access, no credential handling, and
no production authority.

M46 also adds no Xcode project, no Swift package, no Info.plist, no
entitlements, no signing workflow, no store workflow, and no TestFlight
pipeline. The `apps/ccc-ios/` tree remains source-only Swift and README content.

Python Agent Core remains the authority boundary. CCC iOS is a governance and
control client, not the agent brain. Approval refs are identifiers, not
authority. Model output, runtime output, memory, context packs, tool intents,
task plans, and approval refs do not authorize mobile review/receipt actions.

M47 remains future and is limited to TestFlight Pipeline, Internal Only.
