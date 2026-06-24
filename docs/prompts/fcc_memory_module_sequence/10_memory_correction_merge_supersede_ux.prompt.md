# Correction, Merge, And Supersede UX

Goal: make `/memory` a real operator workbench for correction and relationship
between candidates.

Correction:
- Build a correction panel in `/memory`.
- Corrected text must be bounded safe summary only.
- Show original candidate refs, corrected-summary ref, receipt ref, and blocked
  capabilities.

Merge / Supersede:
- Let operator choose two or more candidates/records to merge or supersede.
- Backend records receipt refs and marks old records as superseded posture.
- No silent deletion.

Boundaries:
- No delete/export execution.
- No raw content display.
- React presentation state must not become product truth.

Verification:
- Frontend tests for correction, merge, supersede controls and receipt display.
- Backend route tests for receipt behavior.
