# UAA Hermes Runtime Trajectory Eval Capture Posture

Status: Phase 40 repo-safe manifest and schema.  
Manifest: `docs/runtime/hermes_runtime_trajectory_eval_manifest.json`  
Schema: `docs/schemas/hermes_runtime_trajectory_eval.schema.json`  
Report template: `reports/hermes_runtime_adoption/trajectory_eval_report_template.md`

## Full-Strength

UAA should be able to compare UAA-native, Hermes, Codex, Claude, local, and
future runtimes on repeated operator tasks. A mature lane would capture
redacted trajectories, cost, latency, safety posture, proof coverage, operator
usefulness, and failure recovery over time so the operator can choose the best
runtime for a task without surrendering UAA's authority model.

## Repo-Safe

The current implementation is posture and contract only:

- a runtime eval manifest for planned runtime comparison dimensions
- a redacted trajectory JSON schema
- a weekly benchmark plan expressed as local safe refs
- a report template for manual, local-only evaluation summaries
- a verifier and focused test that keep blocked authority explicit

These artifacts define what a future eval record may contain. They do not
collect trajectories, call models, dispatch runtimes, upload results, run
background benchmarks, or export raw transcript material.

## Blocked / Needs Authority

The following remain blocked:

- raw transcript export
- raw prompt or response persistence
- raw provider payload persistence
- model or provider calls
- external result upload
- automated background eval runs
- remote benchmark execution
- treating eval scores as action authority

## Exact Promotion Path

Promotion requires:

1. operator consent for the exact eval lane
2. safe refs for task, run, runtime, proof, receipt, and evidence records
3. redacted local-only trajectory capture
4. no raw transcript, prompt, response, provider payload, log, local path,
   username, hostname, credential, or secret-like persistence
5. receipt envelope for each captured trajectory
6. verifier-backed schema validation
7. local report generation with blocked-authority labels
8. CLI/API/Core parity before Control Center initiation
9. safe-disable and retention posture

Planning text and manifest presence do not grant runtime invocation or eval
collection authority.
