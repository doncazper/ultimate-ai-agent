# Definition of Ready

Status: Canonical draft, v0.4.5

A work item cannot move to `Ready for Build` unless all applicable checks pass.

## Required for all build items

- [ ] Goal is clear.
- [ ] User/project value is stated.
- [ ] Scope and non-goals are explicit.
- [ ] Acceptance criteria are testable.
- [ ] Required canonical files are identified.
- [ ] Related ADRs are linked or marked not required.
- [ ] Dependencies are listed.
- [ ] Risk level is assigned.
- [ ] Permission impact is reviewed.
- [ ] Memory impact is reviewed.
- [ ] File impact is reviewed.
- [ ] Tool impact is reviewed.
- [ ] Rollback or undo plan exists for mutating work.
- [ ] Test/eval plan exists.

## Foundation Gate check

For any higher-order module, answer this before moving to Ready for Build:

```text
Does this item depend on scanners, companion proactivity, skill factory, self-improving code, autopilot, or high-autonomy external execution?
```

If yes, it cannot move to Ready for Build until the Foundation Gate passes.

## Advanced modules blocked until Foundation Gate passes

- [ ] Scanner Modules
- [ ] Companion Proactivity
- [ ] Skill Factory / Skill Acquisition Service
- [ ] Self-Improving Coding Framework
- [ ] Autopilot Workflows
- [ ] High-autonomy External Execution

## Required foundation before advanced work

- [ ] Execution Contract schema
- [ ] Context Pack schema
- [ ] Run/Event Ledger schema
- [ ] Memory Service V1
- [ ] File Manager V1
- [ ] Consent/Permission Ledger V1
- [ ] Tool Broker V1
- [ ] Capability Registry and Dependency Graph
- [ ] Rollback primitives
- [ ] Contract test suite
- [ ] Shadow replay harness
- [ ] Basic QA/eval baseline


## Model routing addition, v0.4.5

For any feature that invokes LLMs or model-like runtimes, the spec must identify model classes, routing policy, cost mode, privacy level, fallback behavior, verification route, and Event Ledger fields.
