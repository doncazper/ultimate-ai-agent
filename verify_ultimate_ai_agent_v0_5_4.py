#!/usr/bin/env python3
from pathlib import Path
import json, re, sys

ROOT = Path.cwd()
REQ = [
    'README.md','README_IMPORT_v0_5_4.md','VERSION.md','ultimate_ai_agent_master_plan_v0_5_4.md',
    'docs/canonical/09_roadmap.md',
    'docs/canonical/46_result_and_error_envelope.md','docs/canonical/47_idempotency_and_retry_policy.md',
    'docs/canonical/48_actor_authority_and_identity.md','docs/canonical/49_temporal_context_and_freshness.md',
    'docs/canonical/50_data_classification_policy.md','docs/canonical/51_redaction_and_safe_debugging.md',
    'docs/canonical/52_service_boundaries_and_dependency_injection.md',
    'docs/schemas/result_envelope.schema.json','docs/schemas/error_envelope.schema.json',
    'docs/schemas/idempotency_policy.schema.json','docs/schemas/actor_context.schema.json',
    'docs/schemas/temporal_context.schema.json','docs/schemas/data_classification.schema.json',
    'docs/schemas/redaction_policy.schema.json','docs/schemas/capability_flag.schema.json',
    'docs/testing/test_strategy_v0.md',
    'docs/implementation/foundation_gate_implementation_plan_v0_5_4.md',
    'docs/implementation/pre_coding_readiness_v0_5_4.md',
    'docs/registry/capability_registry_v0_5_4.json'
]

def ok(msg): print(f'OK: {msg}')
def fail(msg):
    print(f'FAIL: {msg}')
    sys.exit(1)

print('== Required files ==')
for r in REQ:
    p=ROOT/r
    if not p.exists(): fail(f'missing required file: {r}')
    ok(f'required file exists: {r}')

print('\n== Active baseline markers ==')
version=(ROOT/'VERSION.md').read_text()
if 'v0.5.4' not in version: fail('VERSION.md does not declare v0.5.4')
ok('VERSION.md declares v0.5.4')
readme=(ROOT/'README.md').read_text()
for needle in ['README_IMPORT_v0_5_4.md','Runtime Hygiene Micro-Foundation','docs/canonical/09_roadmap.md']:
    if needle not in readme: fail(f'README missing {needle}')
ok('README points to v0.5.4 runtime hygiene baseline')
roadmap=(ROOT/'docs/canonical/09_roadmap.md').read_text()
for needle in ['M0.5','ResultEnvelope','runtime hygiene']:
    if needle not in roadmap: fail(f'roadmap missing {needle}')
ok('roadmap includes M0.5 runtime hygiene')

print('\n== JSON parse and schema sanity ==')
json_files=list(ROOT.rglob('*.json'))
for p in json_files:
    json.loads(p.read_text())
ok(f'all JSON files parse ({len(json_files)})')
try:
    from jsonschema import Draft202012Validator
except Exception as e:
    fail('jsonschema is required for schema validation; run: python3 -m pip install jsonschema')
schema_files=list((ROOT/'docs/schemas').glob('*.schema.json'))
for p in schema_files:
    Draft202012Validator.check_schema(json.loads(p.read_text()))
ok(f'all JSON Schemas validate ({len(schema_files)})')

print('\n== Prompt registry ==')
reg_path=ROOT/'docs/registry/prompt_registry_v0_5_1.json'
if not reg_path.exists():
    reg_path=ROOT/'ultimate_ai_agent_prompt_registry_v0_5_2.json'
if reg_path.exists():
    reg=json.loads(reg_path.read_text())
    entries=reg.get('prompts') or reg.get('entries') or []
    for item in entries:
        path=item.get('path') if isinstance(item, dict) else None
        if path and not (ROOT/path).exists(): fail(f'prompt registry path missing: {path}')
    ok(f'prompt registry paths checked ({len(entries)} entries)')
else:
    print('WARN: no prompt registry found to check')

print('\n== Stale contradiction scan ==')
active=[ROOT/'README.md',ROOT/'README_IMPORT_v0_5_4.md',ROOT/'ultimate_ai_agent_master_plan_v0_5_4.md',ROOT/'docs/canonical/09_roadmap.md']
for p in active:
    txt=p.read_text()
    for bad in ['M1 — Commander Agent MVP','Tool Broker Hardening']:
        if bad in txt: fail(f'stale roadmap phrase found in {p}: {bad}')
ok('no stale roadmap contradiction phrases found in active files')

print('\n== Critical placeholder scan ==')
critical=[ROOT/f for f in REQ if f.endswith('.md')]
for p in critical:
    txt=p.read_text()
    if re.search(r'\b(TBD|TODO|template placeholder)\b', txt, re.I):
        fail(f'placeholder found in critical doc: {p}')
ok('no TBD/TODO/template placeholders in critical docs')

print('\n== Secret hygiene scan ==')
secret_re=re.compile(r'(api[_-]?key|secret|token|password)\s*=\s*[A-Za-z0-9_\-]{12,}', re.I)
for p in ROOT.rglob('*'):
    if '.git' in p.parts or p.is_dir() or p.suffix.lower() in {'.zip','.bundle','.png','.jpg','.jpeg','.pdf','.docx'}:
        continue
    try: txt=p.read_text(errors='ignore')
    except Exception: continue
    if secret_re.search(txt): fail(f'possible committed secret assignment in {p}')
ok('no obvious committed secret assignments')

print('\n== Result ==')
print('Consistency audit PASSED')
