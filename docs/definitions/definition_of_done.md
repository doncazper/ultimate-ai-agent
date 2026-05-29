# Definition of Done

Status: Canonical draft, v0.4.5

A feature is not done when code or text exists. It is done when the system can safely rely on it.

## Required for all done items

- [ ] Acceptance criteria pass.
- [ ] Tests pass.
- [ ] Evals pass where applicable.
- [ ] Contract tests pass for any public interface.
- [ ] Canonical files are updated.
- [ ] ADRs are added or updated if needed.
- [ ] Event Ledger records the work.
- [ ] Memory updates are source-linked and reviewable.
- [ ] Permission/consent implications are reflected.
- [ ] Rollback plan is documented or marked not applicable.
- [ ] Capability registry is updated.
- [ ] Dependency graph is updated.
- [ ] Release notes or change summary exists.

## Additional requirements for foundation modules

- [ ] Versioned schema or API contract exists.
- [ ] Backward-compatibility behavior is defined.
- [ ] Migration plan exists if needed.
- [ ] Shadow replay passes.
- [ ] At least one rollback drill is documented.

## Additional requirements for advanced modules

- [ ] Foundation Gate is passed.
- [ ] Tool Broker permission path is active.
- [ ] Consent Ledger entries exist.
- [ ] User Control Center visibility exists.
- [ ] Observability trace is complete.
- [ ] Noise/attention policy exists for proactive modules.
- [ ] Source credibility protocol exists for scanner/news modules.
- [ ] Skill trust scan exists for skill modules.
- [ ] Human approval gates exist for high-risk actions.


## Model routing addition, v0.4.5

For any feature that invokes LLMs or model-like runtimes, the spec must identify model classes, routing policy, cost mode, privacy level, fallback behavior, verification route, and Event Ledger fields.
