# Capability Evaluation Lab V1

Status: implemented local read-only verification contract
Queue task: `dev-task:queue-v2-q05-capability-evaluation-lab-v1`
Contract: `contract-ref:capability-evaluation-lab:v1`
Manifest: `docs/evals/capability_evaluation_lab_v1.json`

## Outcome

Capability Evaluation Lab V1 runs four deterministic, content-free local
contract cases for UAA-native capability evaluation, Hermes trajectory-evidence
posture, the Hermes/OpenClaw parity prompt-pack contract, and the pinned
GoatCitadel comparison artifact. It produces per-case evidence digests and four
separate claim gates. A passing gate proves only that the named repository
contract still matches its pinned evidence and verifier; it does not prove an
empirical product winner or current external runtime behavior.

The UAA-native case binds the exact evaluator Git revision and the digest of
every evaluator source file. The three comparison-contract cases bind pinned
source revisions and pinned artifact digests. The runner rejects a dirty or
otherwise uncommitted evaluator source instead of pairing working-tree bytes
with the wrong commit.

## Case Registry

| Subject | Case | What a pass means | What it does not mean |
|---|---|---|---|
| UAA native | `evaluation-case-ref:capability-lab:uaa-native-contracts:v1` | The bounded capability-report truth and registry-coverage checks pass at the exact evaluator revision. | It does not graduate a maturity score or prove operator usefulness. |
| Hermes | `evaluation-case-ref:capability-lab:hermes-trajectory-contract:v1` | The pinned repo-safe trajectory manifest, schema, template, and authority posture remain internally valid. | It does not invoke Hermes or benchmark a live runtime. |
| OpenClaw | `evaluation-case-ref:capability-lab:openclaw-parity-pack:v1` | The pinned parity-gap prompt-pack contract remains deterministic and intact. | It does not claim OpenClaw parity or inspect a live/current OpenClaw source tree. |
| GoatCitadel | `evaluation-case-ref:capability-lab:goat-comparison-contract:v1` | The pinned bounded comparison artifact passes its local evidence gate. | It does not refresh GoatCitadel, perform a live comparison, or alter the recorded scores. |

The manifest is closed: executable case refs, verifier refs, subject refs, and
claim refs must agree exactly. Pinned evidence file drift fails validation.
Every case belongs to a claim gate, and all four declared subjects must remain
covered.

## Run Receipt

`CapabilityEvaluationRunReceipt` binds:

- the versioned manifest ref and digest;
- the exact evaluator Git revision and evaluator-source digest;
- every case's resolved source revision and source-evidence digest;
- expected and observed status through the claim gate;
- a content-free reason ref and per-case evidence digest;
- missing and unexpected case refs; and
- the final claim-gate and run evidence digests.

Missing cases remain in `case_count` and make their claim gate fail. They are
never removed from a complete-case denominator. Duplicate and unexpected case
results fail closed.

## Failure Attribution

Successful and truthfully blocked cases carry `none`. Timeout and evaluator
environment failures have explicit safe attribution. A generic nonzero
verifier result is `unknown` rather than being blamed on the product or the
verifier without independent evidence. Future `subject_regression` or
`verifier_failure` attribution requires a separately verified classifier.
Raw command output is discarded and is not part of a receipt.

## Inspection

Validate the versioned manifest without running cases:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_capability_evaluation_lab.py \
  --validate-only --json
```

Run the four exact local verifier cases and emit the content-free receipt:

```bash
PYTHONPATH=src .venv/bin/python scripts/run_capability_evaluation_lab.py --json
```

The runner uses the existing bounded macOS no-network verifier process
boundary. Commands are fixed in the repository registry; the manifest cannot
provide arbitrary argv.

## Authority Boundary

This lab adds no model or provider call, network fetch, browser action, shell
surface, arbitrary subprocess facility, external dataset import, hidden
training, runtime route, Control Center control, score authority, product
authority, public-release authority, or production authority. Evaluation
receipts are evidence only. Score or capability promotion still requires the
independent acceptance gates already defined by the capability-maturity
contract.
