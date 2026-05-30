# 61 — Evidence Manifest and Claim Verification

Status: Foundation-level canonical policy.
Version: v0.5.6.

## Purpose

An Evidence Manifest is the claim-level proof object for factual outputs. It records what claims were made, which evidence supports each claim, what is unsupported, which sources conflict, and whether freshness or permission limits apply.

## Claim-level verification

Important factual answers should be decomposed into claims:

```text
claim -> evidence -> confidence -> freshness -> permissions -> verification status
```

This is stricter than answer-level citations. It allows QA and users to inspect whether each important factual statement is supported.

## Evidence types

Supported evidence sources include:

```text
canonical_file
active_spec
api_response
database_record
event_ledger_record
world_state_entry
memory_with_source_link
retrieved_document_chunk
provider_result_envelope
web_source
human_approval
```

## Evidence Manifest fields

```text
answer_id
run_id
question
claims
unsupported_claims
source_conflicts
freshness_status
retrieval_log_refs
verification_status
human_review_status
redactions_applied
```

## Refusal rule

If a factual answer requires evidence and evidence is missing, the agent must refuse the unsupported claim or answer with a clear limitation.

## Conflict rule

When sources conflict, the agent must identify the conflict, rank sources by authority and freshness, and avoid presenting a disputed claim as settled.

## Private-source citations

Private sources may be cited in user-visible form without exposing sensitive content:

```text
Source: private Gmail thread from Alex, visible only to you.
Source: internal policy document, access-controlled.
```

The Evidence Manifest may store private source references, but public/exported answers must obey redaction and access policy.

## QA integration

QA/Eval Agent checks:

```text
unsupported factual claims
missing citations
stale evidence
source conflicts
private-source leakage
claim/evidence mismatch
```
