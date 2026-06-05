# Mobile Companion Product Contract Refresh

Status: Current M42 product contract refresh for v0.46.0.

v0.46.0 / M42 implements Mobile Companion Product Contract Refresh as
planning/docs/contracts/verifier work only. It refreshes the product roles,
surface boundaries, and next-step sequencing for mobile companion work without
starting a native app, mobile API, sensor runtime, signing workflow, or
production authority.

The Mobile Companion remains a governance/control surface, not the agent brain.
Python Agent Core remains authority for approvals, consent, receipts, redaction,
events, tool policy, and Foundation Gate decisions. Phone/mobile output is not
truth, not authority, and not execution permission.

M42 product roles:

- governance surface: future approval-status and emergency-stop status display
  only, not approval execution.
- review surface: future review and receipt display only.
- capture inbox surface: product planning only, no sensor capture.
- status surface: future local prototype status display only.
- notification surface: future planning only, no push runtime.

M42 boundaries:

- no mobile app.
- no iOS app.
- no Android app.
- no native package.
- no Swift, Kotlin, Java, React Native, Expo, Flutter, Gradle, Android Studio,
  Xcode project, or native build workflow.
- no TestFlight, App Store, Play Store, signing, provisioning, entitlement,
  keychain, keystore, certificate, or store workflow.
- no mobile API route.
- no backend route.
- no mobile mutation.
- no approval capture.
- no approval execution.
- no mobile sensor access.
- no OS permission integration.
- no background service.
- no notification runtime.
- no device pairing runtime.
- no credentials/cookie handling.
- no raw payload exposure.
- no raw prompt/provider payload exposure.
- no memory write.
- no automatic context injection.
- no file mutation.
- no network/provider/model call.
- no browser automation execution.
- no remote execution.
- no plugin enablement.
- no production authority.

M43 is implemented/released by v0.47.0 as Mobile API Boundary, Read-Only. M44
remains future and is limited to CCC iOS Skeleton, No Authority.

M42 exists to tighten the product contract before implementation work resumes.
It is not an implementation milestone for mobile clients or runtime capability.
