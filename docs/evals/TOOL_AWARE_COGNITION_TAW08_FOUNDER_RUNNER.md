# TAW-08 Founder-Private Acceptance Runner

Status: bounded local evidence collector implemented. Running it does not by
itself complete the evidence-only delta, post-merge Foundation proof, final
publication, independent promotion, or a public quality claim.

The runner collects the frozen TAW-08 founder-private census against one exact
candidate. Stale-cache, routing, and non-chat journey observations replay the
accepted TAW-07 no-effect path deterministically and make no model call. Model
observations use the accepted Qwen 3.8 27B / 128K profile through
`RuntimeGateway` under one exact, temporary authority lease.

## Exact measurement census

The response-scoring census contains eight strata with 24 observations per
stratum. Every response stratum uses all 24 accepted development-corpus cases
in manifest order; cases are not sampled, repeated with modulo arithmetic, or
replaced by category-only placeholders. The 15 catalog-injection cases each
materialize the corresponding accepted poisoned catalog field inside an actual
untrusted read-operation and awareness-envelope snapshot. Only the resulting
safe case, rendering, digest, and posture refs are retained.

The runner makes exactly 216 fresh local-model calls:

- 24 clean same-host baseline calls;
- 24 adversarial candidate live calls using the frozen corpus; and
- 168 calls for the seven remaining response-scoring strata, 24 per stratum.

The direct-chat response stratum reuses the 24 candidate live outcomes, so it
does not make another 24 calls. The chat journey then reuses those same bound
live outcomes and records exactly one model call per journey observation,
without making a second ordinary-chat call. All other journey observations are
structural and make no model call.

The baseline and candidate are deliberately different measurements. Baseline
uses 24 unique clean-control prompts with no untrusted catalog context.
Candidate live and response scoring use the frozen 24-case corpus and the
candidate prompt profile. Evidence refs bind the phase, prompt profile,
mapping, rubric, case, generated-content digest, and any catalog-injection
field and rendering path, so baseline evidence cannot be substituted for
candidate evidence.

The response rubric is deliberately narrow: each case asks for one exact
marker while treating all delimited synthetic and capability data as
untrusted. Marker success measures bounded instruction-following and injection
resistance for these reviewed synthetic strata. It is not a broad quality,
usefulness, creativity, or public model-performance claim.

## Candidate, model, and authority bindings

The candidate lock includes the runner, lease helper, phase driver, phase
worker, frozen corpus, and governed runtime/authority sources. The runner must
execute from the exact candidate checkout and its bytes must match the runner
entry in that lock. It invokes the candidate's locked-child verifier directly,
requires a clean exact checkout and authenticated wheelhouse, and rechecks the
candidate, Foundation receipt, runner source, model artifact, model server, and
lease posture after collection.

The model artifact is supplied by absolute path and must be the regular,
non-symlink file named `Qwen3.8-27B-Q4_K_M.gguf`. On POSIX it must be owned by
the current user and not group- or world-writable. The runner hashes the file
with SHA-256 using a no-follow descriptor, requires the accepted GGUF v3 header,
exact 16,810,714,336-byte size, and exact reviewed digest
`e00082f779fa385cee8c68a3ec8833a75778cc87272240b942f74e0b8243e520`,
binds its file identity, checks that identity around every server observation,
and performs a complete second hash at the end of the run.

The loopback server must report exactly one matching model, exactly one loaded
instance across the entire server catalog, and no second loaded model, with all
of these properties:

- catalog key `qwen/qwen3.8-27b`;
- selected variant `qwen/qwen3.8-27b@q4_k_m`;
- architecture `qwen35`, format `gguf`, and quantization `Q4_K_M` at four bits
  per weight;
- advertised maximum context 262,144;
- loaded API identity `qwen3.8-27b`, context length 131,072, and parallelism 1;
  and
- response `model` and `system_fingerprint` both equal to the loaded API
  identity `qwen3.8-27b`; the selected variant remains independently bound by
  the native catalog and exact artifact attestation.

Catalog metadata is fetched through the bounded loopback local-model adapter
before and after transport. Both the catalog reader and completion transport
explicitly disable environment and system proxies, so a nominal loopback call
cannot be routed off-host. Alias, variant, quantization, context, parallelism,
loaded-instance, artifact, or response-identity drift blocks the run. LM Studio
is part of the reviewed local trusted computing base; its loopback self-report
does not support independent or public promotion.

The live lease must be issued by the candidate-locked lease helper and must be
an active, exactly two-hour, mission-scoped `full_machine_access_session` lease
for only `provider_model_calls:execute`. Its enforced exact-resource constraint
binds the unique TAW-08 run ref, fixed loopback endpoint, and fixed Qwen model
identity; its metadata constraints bind the exact candidate
revision, candidate manifest digest, lease-helper path and digest, and reviewed
lease posture. The runner requires the authority directory to contain exactly
that one active lease, revalidates the HMAC-authenticated backend approval and
separately revalidates the lease at every policy decision, requires more than
60 seconds remaining, requires the kill switch to remain disengaged, and
rejects any lease-posture change during the run. The run, model, and endpoint
bindings are enforced by the authority evaluator; catalog, response, and
artifact bindings are independently enforced by the candidate-locked founder runner.
Together those controls authorize only the governed local-model measurement for
that run; they do not authorize another run, tools, connectors, remote calls,
product mutation, or model output as authority.

## Inputs

The runner requires:

- a clean exact candidate checkout and its authenticated locked wheelhouse;
- the matching permission-restricted raw 32-byte Ed25519 founder private key;
- a distinct permission-restricted raw 32-byte hardware-attestation key;
- the absolute path to the exact Qwen GGUF artifact;
- an owner-only authority state directory containing the exact active lease;
- a fresh, empty, owner-only runtime state directory;
- the exact lease ref returned by the candidate-locked helper;
- `hardware-family-ref:mac`; and
- a unique safe run ref.

This evidence-collection implementation is qualified only on POSIX/macOS.
Windows remains a configured future hardware profile, but its runtime locking
and NTFS ACL enforcement are not qualified by this slice, so the runner rejects
Windows rather than weakening private-path checks. Both keys must be regular
non-symlink files, owned by the current user, and inaccessible to group and
other users. The runner verifies the founder key against the
repository public trust root. It derives the opaque hardware observation ref
internally as HMAC-SHA-256 over transient operating-system, machine, and node
observations plus the exact candidate and run ref. Raw hardware values and the
HMAC key are never emitted or persisted. The requested Mac family must match
the observed macOS host.

## Run

First start LM Studio with no other loaded model, then load the accepted variant
under the exact `qwen3.8-27b` API identity, 131,072-token context, and
parallelism 1. Load the model before starting the authority window.

Then issue the exact lease from the candidate checkout. The candidate revision
and manifest digest must be those emitted by the locked verifier:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/manage_tool_aware_cognition_taw08_live_lease.py issue \
  --state-dir <absolute-owner-only-authority-state-dir> \
  --idempotency-ref <unique-safe-issue-ref> \
  --candidate-revision-ref git-sha:<40-hex-candidate-commit> \
  --candidate-manifest-digest-ref sha256:<64-hex-manifest-digest> \
  --run-ref run-ref:taw08:founder-private:<unique-safe-id>
```

Use the returned `lease_ref`. With the accepted model loaded under the exact
`qwen3.8-27b` API identity, run the candidate's locked runner with these exact
environment values:

```bash
umask 077
UAA_RUNTIME_LOCAL_MODEL_ENABLED=1 \
UAA_LLAMA_CPP_BASE_URL=http://127.0.0.1:1234 \
UAA_LLAMA_CPP_MODEL_ID=qwen3.8-27b \
PYTHONPATH=src .venv/bin/python \
  scripts/run_tool_aware_cognition_taw08_founder_acceptance.py \
  --candidate-repository <absolute-clean-exact-candidate-checkout> \
  --locked-wheelhouse <absolute-authenticated-wheelhouse> \
  --founder-private-key <absolute-permission-restricted-private-key> \
  --hardware-attestation-key <absolute-permission-restricted-hardware-key> \
  --model-artifact-path \
    <absolute-path-ending-in-Qwen3.8-27B-Q4_K_M.gguf> \
  --authority-state-dir <absolute-owner-only-authority-state-dir> \
  --runtime-state-dir <absolute-fresh-empty-owner-only-runtime-state-dir> \
  --output <absolute-new-path-in-an-owner-only-directory> \
  --authority-lease-ref <returned-exact-lease-ref> \
  --hardware-family-ref hardware-family-ref:mac \
  --run-ref <the-same-run-ref-used-to-issue-the-lease>
```

The backend, base URL, model identity, variant, and context are fixed by the
runner; there are no caller-selectable backend or model-ref flags. Missing or
different environment values block before collection.

Revoke the exact lease immediately after the measurement, including after a
failed run:

```bash
PYTHONPATH=src .venv/bin/python \
  scripts/manage_tool_aware_cognition_taw08_live_lease.py revoke \
  --state-dir <absolute-owner-only-authority-state-dir> \
  --lease-ref <returned-exact-lease-ref> \
  --idempotency-ref <unique-safe-revoke-ref>
```

Canonical `FounderPrivateAcceptanceEvidence` JSON is atomically published to a
new mode-0600 file selected with `--output`; an existing target is never
overwritten. Standard output contains only a bounded digest/status summary. A
failed threshold or binding returns nonzero and emits only safe
stratum refs or a bounded validation category to standard error. Governed
runtime records in the supplied runtime state directory retain metadata and
safe refs only: prompt, response, and provider-exchange content are not
persisted. The runner does not execute a runtime tool, call a remote provider,
use a connector, mutate product state, grant broader authority, or write the
repository evidence delta.

The exported candidate-verification receipt and the runner's founder evidence
are separate inputs to `evaluate_taw08_acceptance`. Founder-private acceptance
still proceeds through the evidence-only delta, post-merge Foundation, and
final-publication gates. Independent promotion remains blocked on its separate
custodian, evaluator, external-baseline, and sealed-holdout evidence.
