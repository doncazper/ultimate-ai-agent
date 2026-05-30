from pathlib import Path

ROOT = Path.cwd()
REQUIRED_MARKERS = {
    'docs/canonical/23_security_threat_model.md': [
        'Skill Package Security Rule',
        'All skills are untrusted packages by default',
        'Tool Broker permission mapping',
        'Event Ledger logging',
        'version pinning',
        'revocation/disable support',
        'human approval for high-risk capabilities',
    ],
    'docs/canonical/30_agent_constitution.md': [
        'v0.5.7 skill package security amendment',
        'A skill is a capability package, not an authority',
    ],
    'docs/canonical/32_capability_registry_and_dependency_graph.md': [
        'Skill package capability requirements',
        'skill_manifest_ref',
        'revocation_supported',
        'high_risk_human_approval_required',
    ],
    'docs/implementation/foundation_gate_implementation_plan_v0_5_8.md': [
        'Skill Package Security Rule',
        'skill installation/loading/execution',
        'all executable skill loading remains blocked by the Foundation Gate',
    ],
}

missing = []
for rel, markers in REQUIRED_MARKERS.items():
    path = ROOT / rel
    if not path.exists():
        missing.append(f'missing file: {rel}')
        continue
    text = path.read_text()
    for marker in markers:
        if marker not in text:
            missing.append(f'{rel}: missing marker {marker!r}')

if missing:
    print('Skill package security rule verification FAILED')
    for item in missing:
        print(f'- {item}')
    raise SystemExit(1)

print('Skill package security rule verification PASSED')
