# Medical Knowledge Source Baseline

Status: implemented source catalog; local rights-gated Knowledge Dump ingestion
available separately; network ingestion and model training blocked.

UAA now registers the requested medical references in the Python Agent Core at
`ultimate_ai_agent.core.medical_knowledge`. Registration means that UAA has a
reviewed, machine-readable source target and policy posture. It does **not** mean
that copyrighted text has been copied into the repository, loaded into a model,
embedded, retrieved at runtime, or accepted as clinical authority.

## Catalog coverage

The catalog contains 15 records. PubMed Central and MEDLINE are deliberately
separate because they have different content and reuse boundaries.

| Group | Registered sources | Current posture |
| --- | --- | --- |
| Classification | ICD-11; DSM-5-TR; DSM-5-TR AMPD | ICD-11 is eligible for a future version-pinned adapter after license review. APA works are reference-only pending written AI/content-use permission. |
| General medicine | Harrison's; Merck Manual; Current Medical Diagnosis and Treatment | Reference-only pending publisher rights. |
| Pharmacology | Goodman & Gilman's; Prescribers' Digital Reference; Stahl's | Reference-only pending publisher rights. PDR claims must be cross-checked against official current labeling. |
| Specialty | Nelson Pediatrics; Schwartz's Surgery; Bates' Physical Examination | Reference-only pending publisher rights. |
| Open/official data | MEDLINE/PubMed citation data; PMC Open Access Subset; DailyMed | Eligible for future exact, read-only, versioned adapters after a separately accepted network/ingestion milestone and per-source license controls. |

## Non-negotiable use rules

- Every medical claim must cite a current source with the catalog's required
  locators, such as edition and page, PMID, PMCID plus article license, ICD
  release and entity URI, or DailyMed SET ID and SPL version.
- MEDLINE/PubMed citation metadata is not a grant to ingest article full text.
- Only the PMC Open Access Subset may be considered for systematic full-text
  import, and each article's license and later revocation state must be checked.
- DailyMed is an NLM service publishing structured labeling submitted to FDA;
  labeling version and current status must be checked at use time.
- DSM content cannot be used for generative AI or machine learning without APA
  written permission. A book purchase or web subscription alone is not treated
  as AI-training or corpus-ingestion permission.
- Source registration, retrieval, and model output are not diagnosis,
  prescribing, emergency-care, or clinical decision authority. Conflicting or
  stale evidence must be surfaced, and qualified human clinical judgment remains
  required.

## What is implemented

- Static source metadata, official origin URLs, access classes, source scopes,
  license postures, required citation locators, and future adapter scopes.
- Fail-closed validation that rejects runtime fetch, automated ingestion,
  context injection, model-weight training, diagnosis, prescribing, or truth
  authority flags.
- Focused tests covering source completeness, the proprietary-rights gate,
  PMC/MEDLINE separation, and denied-authority behavior.
- The separate `docs/knowledge/KNOWLEDGE_DUMP.md` lane can ingest an
  operator-supplied local copy only after an exact rights attestation and local
  approval. Catalog registration alone never supplies those rights.

## What remains blocked

- No source bodies, chapters, diagnostic criteria, monographs, abstracts,
  articles, or drug labels are stored in this catalog. Any separately approved
  local source content lives only in the operator's gitignored Knowledge Dump.
- No API client, crawler, downloader, embedding pipeline, vector database, RAG
  ingestion, model fine-tuning, or Control Center route/UI is added.
- Future ICD, NLM, or PMC adapters require exact WebAccessGateway scope,
  allowlisted read-only transport, license enforcement, provenance receipts,
  currentness/revocation handling, redaction, tests, and rollback/safe-disable.
- Proprietary content requires documented rights covering the intended storage,
  retrieval, embedding, and/or training use before any implementation proposal
  may advance.

## Primary policy references

- WHO ICD API and ICD-11 license: <https://icd.who.int/icdapi> and
  <https://icd.who.int/docs/icd-api/license/>
- APA copyright and permissions posture: <https://www.psychiatry.org/copyright>
- NCBI APIs: <https://www.ncbi.nlm.nih.gov/home/develop/api/>
- PMC Open Access Subset: <https://pmc.ncbi.nlm.nih.gov/tools/openftlist/>
- NLM data terms: <https://www.nlm.nih.gov/databases/download/terms_and_conditions.html>
- DailyMed web services: <https://dailymed.nlm.nih.gov/dailymed/app-support-web-services.cfm>
