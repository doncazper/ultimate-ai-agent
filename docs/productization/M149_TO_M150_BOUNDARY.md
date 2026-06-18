# M149 to M150 Boundary

M149 may record the alpha release candidate freeze using safe refs only. It may
bind accepted M101-M148 checkpoint refs, release candidate refs, freeze
checklist refs, alpha readiness refs, evidence index refs, blocker summary
refs, signoff review refs, M150 promotion gate refs, audit refs, replay refs,
revocation refs, kill-switch refs, and no-effect receipt refs.

M149 must not implement M150. It must not publish v1.2.0-alpha, create release
tags, build or upload artifacts, distribute externally, submit to App Store or
TestFlight, release beta, run release automation, add backend routes, add
Control Center controls, add dependencies, or grant production authority.

M150 remains future. The v1.2.0-alpha target remains planned/provisional until
a later accepted milestone explicitly promotes it.
