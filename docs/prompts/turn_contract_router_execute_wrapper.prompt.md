# Wrapper Prompt - Execute UAA Turn Contract Router Phase Pack

Use this wrapper in a fresh Codex run when you want the phase pack executed.

```text
You are Codex working in the Ultimate AI Agent repository.

Execute the prompt pack at:

docs/prompts/turn_contract_router_phase_pack.md

Read the entire pack first. Then run the phases in order, starting at Phase 00.

Global rules:
- Preserve AGENTS.md and all UAA authority invariants.
- This is a Turn Contract Router / Answer Preservation Router, not ModelRouter
  inside UAA.
- Use `base_answer`; do not introduce `base_model`, `raw_model`,
  `model_route_hint`, or other backend-routing language unless the text is
  explicitly about an external LLM/backend router or existing blocked-authority
  names.
- Include the Turn Contract / Capability Gate Table and both stricter
  capability firewall tables from the prompt pack in the relevant architecture
  doc.
- Build in small phases. Do not collapse the whole pack into one giant change.
- Do not add live LLM calls, provider calls, tool execution, memory retrieval
  for ordinary prompts, memory writes, connector writes, browser/network
  authority, shell execution, purchase/booking/send execution, public beta
  claims, or production authority unless a later exact scoped milestone already
  exists and the pack explicitly permits using it.

Per phase:
1. Implement only that phase.
2. Review the work against the prompt pack, AGENTS.md, product-language rules,
   and existing UAA contracts.
3. Fix defects and naming drift.
4. Harden with focused false-positive and false-negative tests.
5. Run focused tests and verifiers. Broaden checks only when the touched
   surface justifies it.
6. Inspect git status/diff and stage only files for the phase.
7. Merge only when verification is green. If already on the target branch,
   skip merge and commit the verified phase directly. If a merge commit is
   needed, create it intentionally.
8. Commit with a scoped message.
9. Push the current branch. Never force-push and never mutate historical tags.
10. After a successful push, continue to the next phase.

Stop only for:
- unsafe scope expansion
- failing verification that cannot be fixed within the phase
- merge conflict requiring operator judgment
- push failure
- missing dependency that blocks the phase
- explicit user pause/stop

Final response after the last completed phase:
- list completed phases
- list files changed
- summarize router contracts, capability firewall behavior, and
  `base_answer` naming cleanup
- explain how `answer_directly` and `base_answer` are physically protected
- summarize safety/risk handling and ExecutorFence posture
- list tests/verifiers run and results
- report commit hashes and push result for each phase
- list remaining blockers and the next recommended prompt, if any
```
