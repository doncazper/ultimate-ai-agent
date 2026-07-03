# Authority Lane 13: Packaging / Distribution

Goal: Make local packaging real without implying public distribution.

Allowed next promotion: repeatable local unsigned macOS app proof.

Scope:

- Local unsigned `.app` proof.
- Optional local-only archive/DMG proof if already supported.
- Setup Assistant labels must say not signed, not notarized, not public.
- No LaunchAgent/daemon/auto-update.

Still blocked:

- Signing.
- Notarization.
- Public installer.
- Auto-update.
- Distribution claim.
- Production readiness claim.

Promotion condition:

Local package build/launch proof is repeatable and visible with honest labels.

Tests/verifiers:

- package proof tests.
- setup/product-language tests.
- visual checks if setup UI changes.
- release-surface verifier if route status changes.

If blocked:

Generate an unblock prompt for the missing local package script, proof receipt,
setup label, or visual baseline.
