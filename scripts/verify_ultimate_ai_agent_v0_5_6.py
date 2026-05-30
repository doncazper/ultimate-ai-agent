#!/usr/bin/env python3
from pathlib import Path
import json, re, sys
try:
    from jsonschema import Draft202012Validator
except Exception:
    print('jsonschema is required; run: python3 -m pip install jsonschema')
    raise

ROOT = Path.cwd()

def ok(msg): print(f'OK: {msg}')
def fail(msg):
    print(f'FAIL: {msg}')
    sys.exit(1)

def exists(path):
    p = ROOT / path
    if not p.exists(): fail(f'missing {path}')
    ok(f'required file exists: {path}')

required = [
    'README.md','README_IMPORT_v0_5_6.md','VERSION.md','ultimate_ai_agent_master_plan_v0_5_6.md',
    'docs/canonical/09_roadmap.md','docs/canonical/30_agent_constitution.md',
    'docs/canonical/59_truth_grounding_and_evidence_governance.md','docs/canonical/60_truth_source_router.md',
    'docs/decisions/ADR-0049-use-truth-grounding-and-evidence-governance.md',
    'docs/schemas/truth_source_manifest.schema.json','docs/schemas/grounding_policy.schema.json',
    'docs/schemas/evidence_manifest.schema.json','docs/schemas/claim_evidence.schema.json',
    'docs/schemas/source_conflict_report.schema.json','docs/schemas/retrieval_log.schema.json',
    'docs/evals/citation_accuracy_eval.md','docs/evals/api_over_document_truth_eval.md',
    'docs/evals/stale_source_refusal_eval.md','docs/evals/source_conflict_detection_eval.md',
    'docs/evals/unsupported_claim_refusal_eval.md','docs/evals/permissioned_source_access_eval.md',
    'docs/evals/fine_tuning_truth_boundary_eval.md',
    'docs/implementation/foundation_gate_implementation_plan_v0_5_6.md',
    'docs/implementation/pre_coding_readiness_v0_5_6.md',
    'docs/registry/capability_registry_v0_5_6.json','docs/release_notes/v0_5_6.md'
]

print('== Required files ==')
for path in required: exists(path)

print('\n== Active baseline markers ==')
if 'v0.5.6' not in (ROOT/'VERSION.md').read_text(): fail('VERSION.md missing v0.5.6')
ok('VERSION.md declares v0.5.6')
readme = (ROOT/'README.md').read_text()
for needle in ['README_IMPORT_v0_5_6.md','Truth-source rule','Grounding rule']:
    if needle not in readme: fail(f'README missing {needle}')
ok('README points to v0.5.6 truth governance baseline')
roadmap = (ROOT/'docs/canonical/09_roadmap.md').read_text()
for needle in ['M4.5','Truth Source Router','Evidence Governance']:
    if needle not in roadmap: fail(f'roadmap missing {needle}')
ok('roadmap includes M4.5 truth/evidence milestone')

print('\n== JSON parse and schema sanity ==')
json_files = list(ROOT.rglob('*.json'))
for p in json_files:
    json.loads(p.read_text())
ok(f'all JSON files parse ({len(json_files)})')
schema_files = list((ROOT/'docs/schemas').glob('*.schema.json'))
for p in schema_files:
    Draft202012Validator.check_schema(json.loads(p.read_text()))
ok(f'all JSON Schemas validate ({len(schema_files)})')

print('\n== Truth governance marker scan ==')
truth = (ROOT/'docs/canonical/59_truth_grounding_and_evidence_governance.md').read_text()
for needle in ['The model is never the source of truth','Truth Source Router','Evidence Manifest','Hybrid retrieval','Fine-tuning boundary']:
    if needle not in truth: fail(f'truth governance doc missing marker: {needle}')
ok('truth governance rules present')
router = (ROOT/'docs/canonical/60_truth_source_router.md').read_text()
for needle in ['canonical_file_lookup','sql_or_api_lookup','hybrid_rag_keyword_vector_rerank','human_review_queue']:
    if needle not in router: fail(f'truth router doc missing marker: {needle}')
ok('truth router source paths present')

print('\n== Critical placeholder scan ==')
placeholder = re.compile(r'\b(TBD|TODO|template placeholder)\b', re.I)
for rel in required:
    p = ROOT / rel
    if p.suffix in {'.md','.json'} and placeholder.search(p.read_text(errors='ignore')):
        fail(f'placeholder found in {rel}')
ok('no TBD/TODO/template placeholders in v0.5.6 critical docs')

print('\n== Secret hygiene scan ==')
secret_pattern = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]")
for p in ROOT.rglob('*'):
    if not p.is_file() or '.git' in p.parts or p.suffix.lower() in {'.zip','.gz','.bundle','.pdf','.png','.jpg','.jpeg','.webp','.docx'}:
        continue
    try:
        text = p.read_text(errors='ignore')
    except Exception:
        continue
    if secret_pattern.search(text):
        fail(f'possible committed secret assignment in {p.relative_to(ROOT)}')
ok('no obvious committed secret assignments')

print('\n== Result ==')
print('Consistency audit PASSED')
