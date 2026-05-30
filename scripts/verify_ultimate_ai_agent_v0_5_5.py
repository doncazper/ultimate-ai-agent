#!/usr/bin/env python3
from pathlib import Path
import json
import re
import sys

ROOT = Path.cwd()
REQ = [
    'README.md', 'README_IMPORT_v0_5_5.md', 'VERSION.md', 'ultimate_ai_agent_master_plan_v0_5_5.md',
    'docs/canonical/09_roadmap.md',
    'docs/canonical/53_structured_world_state.md',
    'docs/canonical/54_context_budget_and_session_survival.md',
    'docs/canonical/55_tool_result_retention_and_context_trimming.md',
    'docs/canonical/56_prompt_tool_prefix_cache_policy.md',
    'docs/canonical/57_local_runtime_and_offline_agent_infrastructure.md',
    'docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md',
    'docs/schemas/world_state.schema.json', 'docs/schemas/world_state_entry.schema.json',
    'docs/schemas/world_state_snapshot.schema.json', 'docs/schemas/context_budget.schema.json',
    'docs/schemas/context_trim_policy.schema.json', 'docs/schemas/context_trim_event.schema.json',
    'docs/schemas/token_accounting.schema.json', 'docs/schemas/token_calibration_event.schema.json',
    'docs/schemas/tool_result_retention_policy.schema.json', 'docs/schemas/prompt_bundle_manifest.schema.json',
    'docs/schemas/tool_schema_bundle.schema.json', 'docs/schemas/prefix_cache_policy.schema.json',
    'docs/schemas/local_runtime_manifest.schema.json', 'docs/schemas/local_model_profile.schema.json',
    'docs/schemas/model_runtime_health.schema.json', 'docs/schemas/runtime_optimization_profile.schema.json',
    'docs/schemas/local_resource_budget.schema.json', 'docs/schemas/privacy_routing_policy.schema.json',
    'docs/schemas/agent_runtime_adapter_manifest.schema.json', 'docs/schemas/a2a_agent_card_minimal.schema.json',
    'docs/evals/long_running_session_survival_eval.md', 'docs/evals/local_runtime_bypass_eval.md',
    'docs/evals/agent_sdk_adapter_boundary_eval.md', 'docs/evals/a2a_interop_contract_eval.md',
    'docs/decisions/ADR-0045-use-structured-world-state.md',
    'docs/decisions/ADR-0046-use-context-budget-manager.md',
    'docs/decisions/ADR-0047-use-local-runtime-registry-and-resource-governor.md',
    'docs/decisions/ADR-0048-use-agent-sdk-adapter-layer-and-a2a-gateway.md',
    'docs/implementation/foundation_gate_implementation_plan_v0_5_5.md',
    'docs/implementation/pre_coding_readiness_v0_5_5.md',
    'docs/registry/capability_registry_v0_5_5.json',
]


def ok(msg: str) -> None:
    print(f'OK: {msg}')


def fail(msg: str) -> None:
    print(f'FAIL: {msg}')
    sys.exit(1)


print('== Required files ==')
for rel in REQ:
    if not (ROOT / rel).exists():
        fail(f'missing {rel}')
    ok(f'required file exists: {rel}')

print('\n== Active baseline markers ==')
if 'v0.5.5' not in (ROOT / 'VERSION.md').read_text():
    fail('VERSION.md missing v0.5.5')
ok('VERSION.md declares v0.5.5')

readme = (ROOT / 'README.md').read_text()
for needle in ['README_IMPORT_v0_5_5.md', 'Context-survival rule', 'SDK/A2A rule']:
    if needle not in readme:
        fail(f'README missing {needle}')
ok('README points to v0.5.5 baseline')

roadmap = (ROOT / 'docs/canonical/09_roadmap.md').read_text()
for needle in ['M2.5', 'World State', 'Context Budget', 'SDK Adapter']:
    if needle not in roadmap:
        fail(f'roadmap missing {needle}')
ok('roadmap includes M2.5 context survival/runtime milestone')

print('\n== JSON parse and schema sanity ==')
json_files = list(ROOT.rglob('*.json'))
for path in json_files:
    json.loads(path.read_text())
ok(f'all JSON files parse ({len(json_files)})')
try:
    from jsonschema import Draft202012Validator
except Exception:
    fail('jsonschema is required; run: python3 -m pip install jsonschema')
schema_files = list((ROOT / 'docs/schemas').glob('*.schema.json'))
for path in schema_files:
    Draft202012Validator.check_schema(json.loads(path.read_text()))
ok(f'all JSON Schemas validate ({len(schema_files)})')

print('\n== Adapter boundary scan ==')
adapter = (ROOT / 'docs/canonical/58_agent_sdk_and_a2a_adapter_strategy.md').read_text()
for needle in ['No external SDK may directly write memory', 'A2A', 'Claude Agent SDK', 'OpenAI Agents SDK']:
    if needle not in adapter:
        fail(f'adapter strategy missing {needle}')
ok('SDK/A2A boundary rules present')

print('\n== Critical placeholder scan ==')
placeholder = re.compile(r'\b(TBD|TODO|template placeholder)\b', re.I)
for rel in REQ:
    path = ROOT / rel
    if path.suffix == '.md' and placeholder.search(path.read_text()):
        fail(f'placeholder found in {rel}')
ok('no TBD/TODO/template placeholders in v0.5.5 critical docs')

print('\n== Secret hygiene scan ==')
secret_re = re.compile(r'(api[_-]?key|secret|token|password)\s*=\s*[A-Za-z0-9_\-]{12,}', re.I)
for path in ROOT.rglob('*'):
    if '.git' in path.parts or path.is_dir() or path.suffix.lower() in {'.zip', '.bundle', '.png', '.jpg', '.jpeg', '.pdf', '.docx'}:
        continue
    try:
        text = path.read_text(errors='ignore')
    except Exception:
        continue
    if secret_re.search(text):
        fail(f'possible committed secret assignment in {path}')
ok('no obvious committed secret assignments')

print('\n== Result ==')
print('Consistency audit PASSED')
