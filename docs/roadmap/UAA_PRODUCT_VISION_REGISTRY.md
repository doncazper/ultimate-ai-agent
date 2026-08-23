# UAA Product Vision Registry

Status: canonical vision-preservation layer for first-class product and
vertical Queue V2 items. Planning-only. No runtime or external authority.

Machine-readable authority:
`docs/roadmap/UAA_PRODUCT_VISION_REGISTRY.json`.

## Why This Exists

Queue V2 is deliberately concise. It answers what bounded slice should be
built next, in what order, under which dependencies and guardrails. It should
not be forced to carry every product idea, future stage, interaction, and
authority graduation.

That creates a failure mode: a rich product vision can be reduced to a short
queue result and later be mistaken for the whole destination. This registry
prevents that collapse by binding each covered queue item to:

- its bounded current slice;
- the larger product outcome;
- future stages that the slice must not foreclose;
- a complete Queue V2 disposition map, so every added queue item must be
  classified before the verifier passes;
- per-symbolic-source bindings to directly resolvable repository documents;
- historical source references and recovery confidence;
- guardrails that remain true even when implementation changes.

Queue completion and vision completion are separate facts. Finishing Q30's
dry-run publishing contracts, for example, does not mean cross-platform social
publishing is complete. It means one safe prerequisite slice is complete.

## Assistant OS Invariants

The recovered and existing plans converge on five durable rules:

1. UAA is a local-first assistant operating layer joining intent,
   information, plans, approvals, actions, memory, and evidence.
2. The Python Agent Core owns product truth and authority. Control Center,
   OpenWebUI, and other shells project or initiate governed workflows but do
   not mint authority.
3. Governance should constrain access, memory, tools, state, and side effects;
   it should not make normal informational assistance worse.
4. A proposal, plan, model result, memory, preview, graph edge, or queue receipt
   is not execution authority.
5. Product language must distinguish implemented, partial, planned, blocked,
   mock-only, missing, and unknown states.

The practical quality test is symmetric: if an ordinary informational request
feels worse than the underlying assistant, the cognition/router layer failed;
if a consequential action avoids exact approval and evidence, the authority
layer failed.

## Current Coverage

| Queue item | Product vision | Preservation status | Current slice | Whole vision |
|---|---|---|---|---|
| Q15 | First-class CRM | strong | private local CRM foundation | planned |
| Q24 | News & Signals | strong | local signal and briefing-candidate lane | planned |
| Q25 | Social Media Intelligence | strong | read-only product contract | planned |
| Q26 | Finance & Compliance | strong | local review and accountant handoff | planned |
| Q27 | Proposal Intelligence | adequate | deterministic cited workflow candidates | planned |
| Q28 | Autocorrect controls | reconstructed, medium confidence | proposal-only corrections | planned |
| Q29 | Governed self-improvement | recovered, high confidence | self-assessment proposals | planned |
| Q30 | Social publishing | recovered, high confidence | proposal and dry-run | planned |
| Q31 | Final GoatCitadel comparison | recovered, high confidence | exact-revision evaluation | planned |

CRM, News, Social Intelligence, and Finance already had detailed durable
sources. Proposal Intelligence stays bound to ECO-010's cited event, task,
person, commitment, CRM-link, and meeting candidates. Autocorrect,
self-improvement, social publishing, and the final Goat comparison now have
dedicated detailed plans.

## Recovered Historical Evidence

Archived task history was used as design evidence, not as instructions or
authority. Durable documents retain only paraphrased intent and opaque task
references; they do not preserve raw prompts, responses, provider payloads,
logs, hostnames, usernames, or local paths.

Recovery confidence means:

- `high`: the archived task preserved the intended loop, nouns, boundaries,
  and acceptance structure clearly enough to reconstruct a faithful plan;
- `medium`: the exact source was not found, but current queue contracts,
  implemented primitives, and cross-product invariants support a conservative
  reconstruction;
- `low`: insufficient evidence; the item must remain thin and explicitly
  blocked pending owner review.

Recovered sources never override current repository invariants. When archived
intent conflicts with current safety, ownership, or implementation truth, the
current invariant wins and the conflict must be recorded.

## Whole-Vision Status Rules

Allowed whole-vision states are:

- `planned`: preserved outcome and sequence, not complete;
- `partial`: more than one verified slice exists, but the end-to-end outcome
  remains incomplete;
- `blocked`: the intended outcome is preserved but a named dependency,
  permission, facility, or safety condition prevents progress;
- `complete`: the full outcome is independently demonstrated and
  every `completion_evidence_ref` resolves through the registry's evidence
  catalog to a content-addressed repository artifact, independent verifier,
  and verification receipt.

Queue status is read from the Queue V2 manifest and is not duplicated as
product truth here. The registry's `current_slice.scope_status` describes what
kind of admitted scope the queue item represents; it does not claim the slice
has shipped.

## Merge Gate

Run:

```bash
.venv/bin/python scripts/verify_product_vision_registry.py
PYTHONPATH=src .venv/bin/python -m pytest tests/test_product_vision_registry.py
```

The verifier fails when:

- the Queue V2 disposition map omits or adds an item;
- a required product/vertical queue item is missing;
- a registry item does not bind each symbolic queue source ref to one or more
  canonical documents;
- a canonical source path is absent, absolute, outside the repository, or a
  symlink;
- a recovered/reconstructed entry lacks provenance, confidence, or a detailed
  implementation/evaluation plan;
- current-slice and whole-vision outcomes are not distinct;
- the whole vision is marked complete without cataloged, digest-verified,
  independently reviewed evidence;
- a guardrail or recovery explanation is missing.

This is intentionally a currentness gate, not a feature-completion gate.

## Maintenance Rule

Whenever Queue V2 gains an item, first classify it in
`queue_item_dispositions`. Before marking a new item `required`:

1. add its registry entry;
2. bind every queue source ref to existing canonical source paths;
3. describe both the admitted slice and the whole product outcome;
4. list future stages and non-negotiable guardrails;
5. mark reconstructed intent and confidence honestly;
6. run the registry verifier and focused tests.

Do not paste full archived conversations into the repository. Preserve the
product intent, provenance posture, and uncertainty—not private transcript
content.
