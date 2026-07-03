# Blocker Report And Unblock Prompt Generator

Use this prompt whenever an authority lane cannot safely promote.

Goal: convert blockers into an immediate next implementation prompt instead of
letting them become vague roadmap fog.

For each blocker, record:

- blocker ref
- affected lane
- attempted promotion level
- why it was not unblocked
- safety/product risk
- missing backend/core/API/CLI/UI/docs/tests/verifier evidence
- smallest next safe action
- exact files likely involved
- tests/verifiers to run
- explicit authority still blocked

Then create an unblock prompt with this shape:

```markdown
# Unblock <lane> <blocker-ref>

Goal:
<one-sentence exact unblock goal>

Branch:
codex/unblock-<lane>-<short-ref>

Base:
latest main

Hard constraints:
- preserve AGENTS.md invariants
- do not broaden authority beyond this blocker
- no raw payload persistence
- no UI-only operator truth

Implementation scope:
1. ...
2. ...

Tests/verifiers:
- ...

Completion:
- commit
- push
- open focused draft PR
- do not merge unless green
```

Save generated blocker reports under:

`docs/control_center/authority_graduation_blockers/`

Save generated unblock prompts under:

`docs/prompts/authority_graduation_program/generated_unblock_prompts/`

If those directories do not exist, create them in the blocker PR. Do not create
empty placeholder files.
