# First Internal TestFlight Build

v0.52.0 / M48 defines the First Internal TestFlight Build milestone as a
reviewed internal build candidate record.

M48 is not a production distribution release. It adds no committed build
artifact, no IPA, no Xcode archive, no signing material, no App Store Connect
API call, no TestFlight upload, no external beta, no public distribution, and
no production authority.

The M48 build candidate is review-only and internal-only. It records safe refs
for the reviewed candidate, source snapshot, M47 pipeline manifest, and
redacted audit receipt plan. The record stores redacted metadata refs only and
does not store certificates, provisioning profiles, private keys, App Store
Connect tokens, raw mobile data, or raw file paths.

The short-form boundary is: no committed build artifact, no IPA, no signing
material, no App Store Connect, no TestFlight upload, no external beta, no
public distribution, and no production authority.

M48 keeps the repository free of Xcode projects, Swift packages, Info.plist
files, entitlements, ExportOptions.plist files, provisioning profiles,
certificates, private keys, Fastlane lanes, CI upload workflows, App Store
Connect upload workflows, archives, and IPA files.

Review-only means the M48 candidate does not grant mobile approval capture,
approval execution, context injection, memory write, raw data export, tool
execution, mobile sensor access, background collection, external beta access,
public distribution, or production authority.

Explicitly: no mobile approval capture, no approval execution, no context
injection, no memory write, no raw data export, no export, no execution, no
mobile sensor access, no background collection, and no production authority are
added by M48.

M49 remains future. M49 is the Mobile Review Approval Capture milestone and
must perform its own strict implementation, validation, and pushed-release
review before any mobile approval capture is described as implemented.
