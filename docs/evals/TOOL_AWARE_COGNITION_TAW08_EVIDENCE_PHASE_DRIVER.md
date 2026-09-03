# TAW-08 Owner-Private Evidence Phase Driver

This owner-private driver closes the finite founder-acceptance publication
sequence after the normal candidate merge. It does not edit a repository,
commit, push, open or merge a pull request, call a model/provider, or grant
independent, public, runtime, execution, or production authority.

The driver consumes the owner-only `FounderPrivateAcceptanceEvidence` produced
for the exact candidate merge commit `M1`. It has three explicit phases:

1. `prepare_delta` validates a clean exact `M1` checkout and emits exactly three
   staged files:
   - `docs/evals/tool_aware_cognition_taw08_acceptance_report_v1.json`;
   - `docs/kanban/current_board.md`; and
   - `docs/roadmap/PRODUCT_RELEASE_TRUTH_PACKET.md`.
2. `verify_delta` validates a clean committed `M2`, proves the complete
   `M1..M2` endpoint and per-commit history census contains exactly those three
   paths, verifies the evidence-only manifest, runs the canonical post-merge
   Foundation Gate, and emits the one staged final-publication JSON file.
3. `verify_publication` validates a clean committed `M3`, proves the complete
   `M2..M3` endpoint and per-commit history census contains only
   `docs/evals/tool_aware_cognition_taw08_final_acceptance_report_v1.json`, and
   verifies the content-addressed publication receipt.

The exact status progression is:

```text
founder_private_accepted_postmerge_pending
founder_private_accepted_final_publication_pending
founder_private_accepted_promotion_blocked
```

`founder_private_accepted_promotion_blocked` is terminal only for the current
private-dogfood acceptance lane. Independent promotion, sealed-holdout proof,
public quality claims, and production authority remain false and blocked.

## Candidate-locked execution boundary

The phase driver and worker are operational sources in the `M1` candidate
lock. The driver must execute from the exact clean `M1` checkout with Python's
isolated, no-bytecode, and no-site flags (`-I -B -S`). Its startup is
standard-library-only: before reading founder evidence or creating output, it
authenticates the OS-admin Git executable, disables repository-local file
monitoring, proves the candidate is clean, binds its own bytes and `uv.lock` to
the candidate revision, and loads TOML/wheel tooling only from a privately
staged copy of the exact locked `pip` wheel. Before every phase it also proves
that both local operational source files equal their committed `M1` Git bytes
and derives their exact SHA-256 digests.

Those two source digests are added to the phase request. The worker is copied
from the candidate bytes into a temporary owner-only file, and its digest is
also passed through the authenticated preflight environment. Inside the
isolated worker, the request digests and the running worker bytes must match the
driver and worker entries in a newly derived candidate lock. Every phase
receipt returns both source digests; the outer driver compares them with the
request before accepting or writing any artifact. A substituted external
driver, worker, request, or receipt therefore fails closed.

Repository acceptance APIs are imported only inside an isolated `-I -B -S`
child after the candidate's authenticated wheel/preflight verifier succeeds.
No ordinary `PYTHONPATH` is used for that child, and the locked environment is
materialized offline from the authenticated wheelhouse.

## Security and ownership boundary

- Founder evidence, the verified-delta receipt, phase receipts, staged
  artifacts, and output directories must be owned by the current user and
  inaccessible to group or other users.
- The driver refuses symlinks, oversized JSON, dirty worktrees, hidden Git
  index entries, unexpected changed paths, history-only or reverted extra
  paths, schema drift, digest drift, source substitution, status substitution,
  and authority expansion.
- Candidate, delta, and publication bytes and path censuses come from clean
  exact Git worktrees. The two Markdown files are reconstructed from the `M1`
  Git bytes, and every byte before the start marker and after the end marker is
  required to remain identical.
- Output creation is atomic and mode `0600`. An existing identical output is
  idempotent; a different existing output is never overwritten.

The output artifacts are staging material. Copy each artifact to its canonical
repository path, review the resulting exact path census, and commit it through
the normal protected workflow before invoking the next phase. The driver never
performs that mutation itself.

## Commands

Use absolute paths throughout. `<absolute-python>` is an absolute path to a
suitable Python interpreter. The driver path for all three phases must be the
candidate-locked copy inside the clean `M1` worktree. Founder evidence must be
the exact signed, digest-bound output of the separately reviewed owner-private
evaluator for `M1`; a capture for the pre-merge candidate head is not
interchangeable. The driver never launches that evaluator or makes a model
call.

```bash
<absolute-python> -I -B -S \
  <clean-M1-worktree>/scripts/run_tool_aware_cognition_taw08_evidence_phases.py \
  prepare_delta \
  --candidate-worktree <clean-M1-worktree> \
  --founder-evidence <owner-only-founder-evidence.json> \
  --locked-wheelhouse <locked-wheelhouse> \
  --output-dir <owner-only-prepare-output>
```

After the three staged files are the only committed `M1..M2` changes:

```bash
<absolute-python> -I -B -S \
  <clean-M1-worktree>/scripts/run_tool_aware_cognition_taw08_evidence_phases.py \
  verify_delta \
  --candidate-worktree <clean-M1-worktree> \
  --delta-worktree <clean-M2-worktree> \
  --founder-evidence <owner-only-founder-evidence.json> \
  --locked-wheelhouse <locked-wheelhouse> \
  --output-dir <owner-only-delta-output>
```

After the emitted final JSON is the only committed `M2..M3` change:

```bash
<absolute-python> -I -B -S \
  <clean-M1-worktree>/scripts/run_tool_aware_cognition_taw08_evidence_phases.py \
  verify_publication \
  --candidate-worktree <clean-M1-worktree> \
  --delta-worktree <clean-M2-worktree> \
  --publication-worktree <clean-M3-worktree> \
  --founder-evidence <owner-only-founder-evidence.json> \
  --verified-delta-receipt \
    <owner-only-delta-output>/verified_delta_phase_receipt.json \
  --locked-wheelhouse <locked-wheelhouse> \
  --output-dir <owner-only-publication-output>
```

`verify_delta` runs the full canonical Foundation Gate and can take materially
longer than the other two phases. Do not bypass, weaken, or replace that gate.

## Offline verification

The focused tests exercise owner-only IO, exact marker-span replacement, dirty
and hidden-index refusal, wheel-lock identity validation, isolated preflight
invocation without `PYTHONPATH`, candidate-bound driver/worker digests, exact
artifact censuses, status transitions, and authority-expansion rejection. They
do not call a model/provider or mutate either UAA repository worktree.

```bash
PYTHONPATH=src .venv/bin/python -m pytest -q \
  tests/test_tool_aware_cognition_taw08_evidence_phases.py
.venv/bin/python -m ruff check \
  scripts/run_tool_aware_cognition_taw08_evidence_phases.py \
  scripts/taw08_evidence_phase_worker.py \
  tests/test_tool_aware_cognition_taw08_evidence_phases.py
```
