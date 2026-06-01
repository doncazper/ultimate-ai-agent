# Documentation Integrity Checklist

Status: Active maintenance checklist, v0.14.5

Run this checklist before every release that changes docs, roadmap, API metadata, runtime boundaries, or release status.

## Version Alignment

- `VERSION.md` active baseline matches `pyproject.toml`.
- `VERSION.md` active baseline matches `src/ultimate_ai_agent/__init__.py`.
- `README.md` points to the active `README_IMPORT_vX_Y_Z.md`.
- `README.md` points to the active `ultimate_ai_agent_master_plan_vX_Y_Z.md`.
- active release notes exist.
- active Foundation Gate implementation plan exists.

## Source-of-Truth Hierarchy

- active README/import/master docs identify the current baseline.
- canonical docs are treated as current principle/source-of-truth docs.
- historical release docs remain historical and are not presented as active truth.
- backlog docs are clearly future/not implemented.

## Stale Link Checks

- active README does not point to older import or master plan files.
- active import README includes current key docs.
- active master plan matches current release purpose.
- docs index and canonical map include newly added active docs.

## Active vs Historical Docs

- historical files are not deleted for ordinary integrity passes.
- older release notes may retain historical version language.
- current docs explain whether features are implemented, simulated, validation-only, dry-run-only, manual-only, planned/disabled, future/backlog, or blocked.

## Safety Claim Checks

- docs do not claim live model/provider/network/runtime execution unless implemented and gated.
- docs do not claim mobile app, sensor access, OS permission integration, or background service exists unless implemented and gated.
- docs do not claim remote execution, tailnet/private mesh execution, or remote approvals exist unless implemented and gated.
- docs do not claim scanners, Skill Factory, self-improvement, production persistence, or external actions exist unless implemented and gated.

## Release Note Requirements

- release notes name the release purpose.
- release notes list changed docs/verifiers/gates.
- release notes explicitly state no new runtime powers for docs-only releases.

## Roadmap Update Requirements

- active roadmap names the accepted baseline.
- future milestones remain sequenced.
- parked work is not presented as accepted baseline.
- blocked capabilities remain blocked until their security lifecycle and gate criteria exist.

## Foundation Gate Doc-Check Requirements

- documentation integrity verifier passes.
- Foundation Gate includes documentation integrity when active docs are synchronized.
- `verify_all.py` calls the documentation integrity verifier.
