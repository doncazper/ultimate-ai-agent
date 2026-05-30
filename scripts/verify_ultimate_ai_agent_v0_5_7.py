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
def fail(msg): print(f'FAIL: {msg}'); sys.exit(1)
def exists(path):
    p = ROOT / path
    if not p.exists(): fail(f'missing {path}')
    ok(f'required file exists: {path}')
required = [
    'README.md','README_IMPORT_v0_5_7.md','VERSION.md','ultimate_ai_agent_master_plan_v0_5_7.md',
    'docs/canonical/09_roadmap.md','docs/canonical/22_observability_and_event_ledger.md',
    'docs/canonical/63_observability_standards_mapping.md',
    'docs/decisions/ADR-0053-use-observability-standards-mapping.md',
    'docs/schemas/observability_mapping.schema.json','docs/schemas/event_export_profile.schema.json',
    'docs/evals/observability_standards_mapping_eval.md','docs/evals/trace_context_propagation_eval.md',
    'docs/implementation/foundation_gate_implementation_plan_v0_5_7.md',
    'docs/implementation/pre_coding_readiness_v0_5_7.md',
    'docs/registry/capability_registry_v0_5_7.json','docs/release_notes/v0_5_7.md'
]
print('== Required files ==')
for path in required: exists(path)
print('\n== Active baseline markers ==')
if 'v0.5.7' not in (ROOT/'VERSION.md').read_text(): fail('VERSION.md missing v0.5.7')
ok('VERSION.md declares v0.5.7')
readme = (ROOT/'README.md').read_text()
for needle in ['README_IMPORT_v0_5_7.md','Observability standards rule','OpenTelemetry']:
    if needle not in readme: fail(f'README missing {needle}')
ok('README points to v0.5.7 observability standards baseline')
roadmap = (ROOT/'docs/canonical/09_roadmap.md').read_text()
for needle in ['M2 — Event Ledger, Deterministic Run State, Receipts, and Observability Standards Mapping','OpenTelemetry','W3C Trace Context']:
    if needle not in roadmap: fail(f'roadmap missing {needle}')
ok('roadmap includes M2 observability standards mapping')
print('\n== JSON parse and schema sanity ==')
json_files = list(ROOT.rglob('*.json'))
for p in json_files:
    json.loads(p.read_text())
ok(f'all JSON files parse ({len(json_files)})')
schema_files = list((ROOT/'docs/schemas').glob('*.schema.json'))
for p in schema_files:
    Draft202012Validator.check_schema(json.loads(p.read_text()))
ok(f'all JSON Schemas validate ({len(schema_files)})')
print('\n== Observability marker scan ==')
obs = (ROOT/'docs/canonical/63_observability_standards_mapping.md').read_text()
for needle in ['OpenTelemetry GenAI semantic conventions','W3C Trace Context','CloudEvents','AsyncAPI','The Event Ledger is authoritative']:
    if needle not in obs: fail(f'observability mapping doc missing marker: {needle}')
ok('observability standards markers present')
print('\n== Critical placeholder scan ==')
placeholder = re.compile(r'\b(TBD|TODO|template placeholder)\b', re.I)
for rel in required:
    p = ROOT / rel
    if p.suffix in {'.md','.json'} and placeholder.search(p.read_text(errors='ignore')):
        fail(f'placeholder found in {rel}')
ok('no TBD/TODO/template placeholders in v0.5.7 critical docs')
print('\n== Secret hygiene scan ==')
secret_pattern = re.compile(r"(?i)(api[_-]?key|secret|token|password)\s*=\s*['\"][A-Za-z0-9_\-]{16,}['\"]")
for p in ROOT.rglob('*'):
    if not p.is_file() or '.git' in p.parts or p.suffix.lower() in {'.zip','.gz','.bundle','.pdf','.png','.jpg','.jpeg','.webp','.docx'}:
        continue
    text = p.read_text(errors='ignore')
    if secret_pattern.search(text):
        fail(f'possible committed secret assignment in {p.relative_to(ROOT)}')
ok('no obvious committed secret assignments')
print('\n== Result ==')
print('Consistency audit PASSED')
