#!/usr/bin/env python3
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

def fail(msg):
    print(f"FAIL: {msg}")
    sys.exit(1)

def ok(msg):
    print(f"OK: {msg}")


def release_packet_paths(version_key):
    return (
        f"docs/archive/releases/v{version_key}/README_IMPORT.md",
        f"docs/archive/releases/v{version_key}/master_plan.md",
    )

def main():
    print("=== Ultimate AI Agent Baseline Consistency Verification ===")
    
    # 1. Read VERSION.md and extract version
    version_file = ROOT / "VERSION.md"
    if not version_file.exists():
        fail("VERSION.md does not exist")
    
    version_content = version_file.read_text(encoding="utf-8")
    version_match = re.search(r"Current active baseline:\s*\*\*v?(\d+\.\d+\.\d+)\*\*", version_content)
    if not version_match:
        fail("Could not find 'Current active baseline: **vX.Y.Z**' pattern in VERSION.md")
    
    version = version_match.group(1)
    version_with_underscores = version.replace(".", "_")
    ok(f"VERSION.md active baseline version: v{version}")
    
    # 2. Check pyproject.toml version
    pyproject_file = ROOT / "pyproject.toml"
    if not pyproject_file.exists():
        fail("pyproject.toml does not exist")
        
    pyproject_content = pyproject_file.read_text(encoding="utf-8")
    pyproject_match = re.search(r'(?m)^version\s*=\s*[\'"]([^\'"]+)[\'"]', pyproject_content)
    if not pyproject_match:
        fail("Could not find version setting in pyproject.toml")
        
    pyproject_version = pyproject_match.group(1)
    if pyproject_version != version:
        fail(f"pyproject.toml version ({pyproject_version}) does not match VERSION.md baseline ({version})")
    ok(f"pyproject.toml version is consistent: {pyproject_version}")
    
    # 3. Check src/ultimate_ai_agent/__init__.py __version__
    init_file = ROOT / "src" / "ultimate_ai_agent" / "__init__.py"
    if not init_file.exists():
        fail("src/ultimate_ai_agent/__init__.py does not exist")
        
    init_content = init_file.read_text(encoding="utf-8")
    init_match = re.search(r'(?m)^__version__\s*=\s*[\'"]([^\'"]+)[\'"]', init_content)
    if not init_match:
        fail("Could not find __version__ in src/ultimate_ai_agent/__init__.py")
        
    init_version = init_match.group(1)
    if init_version != version:
        fail(f"__init__.py version ({init_version}) does not match VERSION.md baseline ({version})")
    ok(f"src/ultimate_ai_agent/__init__.py version is consistent: {init_version}")
    
    # 4. Check README.md consistency
    readme_file = ROOT / "README.md"
    if not readme_file.exists():
        fail("README.md does not exist")
        
    readme_content = readme_file.read_text(encoding="utf-8")
    if f"v{version}" not in readme_content:
        fail(f"README.md does not mention the active baseline v{version}")
        
    # Generic check for active archive release-packet references.
    import_packet, master_packet = release_packet_paths(version_with_underscores)
    legacy_import_matches = re.findall(r"README_IMPORT_v(\d+_\d+_\d+)\.md", readme_content)
    legacy_plan_matches = re.findall(r"ultimate_ai_agent_master_plan_v(\d+_\d+_\d+)\.md", readme_content)
    if legacy_import_matches or legacy_plan_matches:
        fail("README.md must use docs/archive/releases release-packet paths, not root release artifacts")

    if import_packet not in readme_content:
        fail(f"README.md is missing active release packet {import_packet}")
    if master_packet not in readme_content:
        fail(f"README.md is missing active release packet {master_packet}")
    ok("README.md active baseline references are consistent (archive release packets)")
    
    # 5. Check release notes existence
    rel_notes_file = ROOT / "docs" / "release_notes" / f"v{version_with_underscores}.md"
    if not rel_notes_file.exists():
        fail(f"Active version release notes file {rel_notes_file.relative_to(ROOT)} is missing")
    ok(f"Release notes for active version exist: {rel_notes_file.relative_to(ROOT)}")
    
    # 6. Check README_IMPORT and master plan existence on disk
    import_readme_file = ROOT / import_packet
    master_plan_file = ROOT / master_packet
    
    if not import_readme_file.exists():
        fail(f"{import_packet} does not exist")
    if not master_plan_file.exists():
        fail(f"{master_packet} does not exist")
    ok("README_IMPORT and master plan archive packets exist for the current version")
    
    # 7. Check M1 contract files existence
    m1_files = [
        "src/ultimate_ai_agent/core/contracts/enums.py",
        "src/ultimate_ai_agent/core/contracts/execution_contract.py",
        "src/ultimate_ai_agent/core/contracts/context_pack.py",
        "src/ultimate_ai_agent/core/contracts/validation.py",
        "src/ultimate_ai_agent/core/contracts/factory.py",
    ]
    for rel_path in m1_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M1 file is missing: {rel_path}")
    ok("All M1 contract/validation files exist")

    # 8. Check M2 ledger files existence
    m2_files = [
        "src/ultimate_ai_agent/core/ledger/__init__.py",
        "src/ultimate_ai_agent/core/ledger/enums.py",
        "src/ultimate_ai_agent/core/ledger/events.py",
        "src/ultimate_ai_agent/core/ledger/ledger.py",
        "src/ultimate_ai_agent/core/ledger/receipts.py",
        "src/ultimate_ai_agent/core/ledger/replay.py",
        "src/ultimate_ai_agent/core/ledger/run_state.py",
        "src/ultimate_ai_agent/core/ledger/standards.py",
        "src/ultimate_ai_agent/core/ledger/validation.py",
    ]
    for rel_path in m2_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M2 ledger file is missing: {rel_path}")
    ok("All M2 ledger files exist")

    # 8.5 Check M2.5 world state/context budget/runtime/adapter files existence
    m25_files = [
        "src/ultimate_ai_agent/core/world_state/__init__.py",
        "src/ultimate_ai_agent/core/world_state/models.py",
        "src/ultimate_ai_agent/core/world_state/snapshots.py",
        "src/ultimate_ai_agent/core/world_state/validation.py",
        "src/ultimate_ai_agent/core/context_budget/__init__.py",
        "src/ultimate_ai_agent/core/context_budget/models.py",
        "src/ultimate_ai_agent/core/context_budget/token_accounting.py",
        "src/ultimate_ai_agent/core/context_budget/trimming.py",
        "src/ultimate_ai_agent/core/context_budget/validation.py",
        "src/ultimate_ai_agent/core/runtime/__init__.py",
        "src/ultimate_ai_agent/core/runtime/local_runtime.py",
        "src/ultimate_ai_agent/core/runtime/resource_budget.py",
        "src/ultimate_ai_agent/core/runtime/capability_profile.py",
        "src/ultimate_ai_agent/core/runtime/health.py",
        "src/ultimate_ai_agent/core/runtime/validation.py",
        "src/ultimate_ai_agent/core/adapters/__init__.py",
        "src/ultimate_ai_agent/core/adapters/sdk_manifest.py",
        "src/ultimate_ai_agent/core/adapters/a2a_manifest.py",
        "src/ultimate_ai_agent/core/adapters/validation.py",
    ]
    for rel_path in m25_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M2.5 file is missing: {rel_path}")
    ok("All M2.5 world state, context budget, runtime, and adapter files exist")
    
    # 8.6 Check M3 consent/tool files existence
    m3_files = [
        "src/ultimate_ai_agent/core/consent/__init__.py",
        "src/ultimate_ai_agent/core/consent/enums.py",
        "src/ultimate_ai_agent/core/consent/grants.py",
        "src/ultimate_ai_agent/core/consent/policies.py",
        "src/ultimate_ai_agent/core/consent/ledger.py",
        "src/ultimate_ai_agent/core/consent/decisions.py",
        "src/ultimate_ai_agent/core/consent/validation.py",
        "src/ultimate_ai_agent/core/tools/__init__.py",
        "src/ultimate_ai_agent/core/tools/enums.py",
        "src/ultimate_ai_agent/core/tools/manifests.py",
        "src/ultimate_ai_agent/core/tools/requests.py",
        "src/ultimate_ai_agent/core/tools/decisions.py",
        "src/ultimate_ai_agent/core/tools/broker.py",
        "src/ultimate_ai_agent/core/tools/registry.py",
        "src/ultimate_ai_agent/core/tools/capability_firewall.py",
        "src/ultimate_ai_agent/core/tools/validation.py",
    ]
    for rel_path in m3_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M3 file is missing: {rel_path}")
    ok("All M3 consent and tool files exist")

    # 8.7 Check M3.5 secret/provider files existence
    m35_files = [
        "src/ultimate_ai_agent/core/secrets/__init__.py",
        "src/ultimate_ai_agent/core/secrets/enums.py",
        "src/ultimate_ai_agent/core/secrets/credentials.py",
        "src/ultimate_ai_agent/core/secrets/handles.py",
        "src/ultimate_ai_agent/core/secrets/broker.py",
        "src/ultimate_ai_agent/core/secrets/redaction.py",
        "src/ultimate_ai_agent/core/secrets/validation.py",
        "src/ultimate_ai_agent/core/providers/__init__.py",
        "src/ultimate_ai_agent/core/providers/enums.py",
        "src/ultimate_ai_agent/core/providers/manifests.py",
        "src/ultimate_ai_agent/core/providers/registry.py",
        "src/ultimate_ai_agent/core/providers/requests.py",
        "src/ultimate_ai_agent/core/providers/results.py",
        "src/ultimate_ai_agent/core/providers/resolver.py",
        "src/ultimate_ai_agent/core/providers/normalization.py",
        "src/ultimate_ai_agent/core/providers/validation.py",
    ]
    for rel_path in m35_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M3.5 file is missing: {rel_path}")
    ok("All M3.5 secret broker and provider registry files exist")

    # 8.8 Check M4 memory/file manager files existence
    m4_files = [
        "src/ultimate_ai_agent/core/memory/__init__.py",
        "src/ultimate_ai_agent/core/memory/enums.py",
        "src/ultimate_ai_agent/core/memory/records.py",
        "src/ultimate_ai_agent/core/memory/requests.py",
        "src/ultimate_ai_agent/core/memory/decisions.py",
        "src/ultimate_ai_agent/core/memory/store.py",
        "src/ultimate_ai_agent/core/memory/retrieval.py",
        "src/ultimate_ai_agent/core/memory/policies.py",
        "src/ultimate_ai_agent/core/memory/validation.py",
        "src/ultimate_ai_agent/core/memory/redaction.py",
        "src/ultimate_ai_agent/core/files/__init__.py",
        "src/ultimate_ai_agent/core/files/enums.py",
        "src/ultimate_ai_agent/core/files/refs.py",
        "src/ultimate_ai_agent/core/files/operations.py",
        "src/ultimate_ai_agent/core/files/manager.py",
        "src/ultimate_ai_agent/core/files/diffs.py",
        "src/ultimate_ai_agent/core/files/snapshots.py",
        "src/ultimate_ai_agent/core/files/policies.py",
        "src/ultimate_ai_agent/core/files/validation.py",
        "src/ultimate_ai_agent/core/files/rollback.py",
    ]
    for rel_path in m4_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M4 file is missing: {rel_path}")
    ok("All M4 memory service and file manager files exist")

    # 8.9 Check M4.5 truth source/evidence governance files existence
    m45_files = [
        "src/ultimate_ai_agent/core/truth/__init__.py",
        "src/ultimate_ai_agent/core/truth/enums.py",
        "src/ultimate_ai_agent/core/truth/sources.py",
        "src/ultimate_ai_agent/core/truth/grounding.py",
        "src/ultimate_ai_agent/core/truth/claims.py",
        "src/ultimate_ai_agent/core/truth/evidence.py",
        "src/ultimate_ai_agent/core/truth/conflicts.py",
        "src/ultimate_ai_agent/core/truth/retrieval_log.py",
        "src/ultimate_ai_agent/core/truth/freshness.py",
        "src/ultimate_ai_agent/core/truth/router.py",
        "src/ultimate_ai_agent/core/truth/validation.py",
    ]
    for rel_path in m45_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M4.5 file is missing: {rel_path}")
    ok("All M4.5 truth source and evidence governance files exist")

    # 8.10 Check M5 kernel files existence
    m5_files = [
        "src/ultimate_ai_agent/core/kernel/__init__.py",
        "src/ultimate_ai_agent/core/kernel/enums.py",
        "src/ultimate_ai_agent/core/kernel/requests.py",
        "src/ultimate_ai_agent/core/kernel/results.py",
        "src/ultimate_ai_agent/core/kernel/receipts.py",
        "src/ultimate_ai_agent/core/kernel/runner.py",
        "src/ultimate_ai_agent/core/kernel/validation.py",
    ]
    for rel_path in m5_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M5 file is missing: {rel_path}")
    ok("All M5 minimum lovable kernel files exist")

    # 8.11 Check M6 Foundation Gate files existence
    m6_files = [
        "src/ultimate_ai_agent/core/gate/__init__.py",
        "src/ultimate_ai_agent/core/gate/enums.py",
        "src/ultimate_ai_agent/core/gate/criteria.py",
        "src/ultimate_ai_agent/core/gate/reports.py",
        "src/ultimate_ai_agent/core/gate/evaluators.py",
        "src/ultimate_ai_agent/core/gate/shadow_replay.py",
        "src/ultimate_ai_agent/core/gate/validation.py",
        "scripts/run_foundation_gate.py",
        "reports/foundation_gate/sample_foundation_gate_report.json",
        "reports/foundation_gate/sample_foundation_gate_report.md",
    ]
    for rel_path in m6_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M6 Foundation Gate file is missing: {rel_path}")
    ok("All M6 Foundation Gate and shadow replay files exist")

    # 8.12 Check M7 model router and cost/resource governor files existence
    m7_files = [
        "src/ultimate_ai_agent/core/model_router/__init__.py",
        "src/ultimate_ai_agent/core/model_router/enums.py",
        "src/ultimate_ai_agent/core/model_router/profiles.py",
        "src/ultimate_ai_agent/core/model_router/policies.py",
        "src/ultimate_ai_agent/core/model_router/requests.py",
        "src/ultimate_ai_agent/core/model_router/decisions.py",
        "src/ultimate_ai_agent/core/model_router/router.py",
        "src/ultimate_ai_agent/core/model_router/validation.py",
        "src/ultimate_ai_agent/core/costs/__init__.py",
        "src/ultimate_ai_agent/core/costs/enums.py",
        "src/ultimate_ai_agent/core/costs/budgets.py",
        "src/ultimate_ai_agent/core/costs/estimates.py",
        "src/ultimate_ai_agent/core/costs/decisions.py",
        "src/ultimate_ai_agent/core/costs/governor.py",
        "src/ultimate_ai_agent/core/costs/validation.py",
    ]
    for rel_path in m7_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M7 file is missing: {rel_path}")
    ok("All M7 model router and cost/resource governor files exist")

    # 8.13 Check M7.5 API boundary stabilization files existence
    m75_files = [
        "AGENTS.md",
        "src/ultimate_ai_agent/api/contracts.py",
        "src/ultimate_ai_agent/api/manifest.py",
        "src/ultimate_ai_agent/api/openapi.py",
        "scripts/export_openapi.py",
        "scripts/verify_openapi_contract.py",
        "docs/api/README.md",
        "docs/api/openapi_contract.md",
        "docs/api/route_inventory.md",
        "docs/standards/agents_md_support.md",
    ]
    for rel_path in m75_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M7.5 API boundary file is missing: {rel_path}")
    ok("All M7.5 API boundary stabilization files exist")

    # 8.14 Check M8 simulated model runtime adapter harness files existence
    m8_files = [
        "src/ultimate_ai_agent/core/model_runtime/__init__.py",
        "src/ultimate_ai_agent/core/model_runtime/enums.py",
        "src/ultimate_ai_agent/core/model_runtime/manifests.py",
        "src/ultimate_ai_agent/core/model_runtime/requests.py",
        "src/ultimate_ai_agent/core/model_runtime/responses.py",
        "src/ultimate_ai_agent/core/model_runtime/simulator.py",
        "src/ultimate_ai_agent/core/model_runtime/adapters.py",
        "src/ultimate_ai_agent/core/model_runtime/validation.py",
        "src/ultimate_ai_agent/core/model_runtime/redaction.py",
        "tests/test_model_runtime_manifests.py",
        "tests/test_model_runtime_requests.py",
        "tests/test_model_runtime_simulator.py",
        "tests/test_model_runtime_no_real_calls.py",
        "tests/test_model_runtime_redaction.py",
        "tests/test_model_runtime_event_metadata.py",
        "tests/test_model_runtime_api_routes.py",
        "tests/test_m8_gate_integration.py",
    ]
    for rel_path in m8_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M8 file is missing: {rel_path}")
    ok("All M8 simulated model runtime adapter harness files exist")

    # 8.15 Check M8.5 approval authority files existence
    m85_files = [
        "src/ultimate_ai_agent/core/approvals/__init__.py",
        "src/ultimate_ai_agent/core/approvals/enums.py",
        "src/ultimate_ai_agent/core/approvals/requests.py",
        "src/ultimate_ai_agent/core/approvals/grants.py",
        "src/ultimate_ai_agent/core/approvals/decisions.py",
        "src/ultimate_ai_agent/core/approvals/authority.py",
        "src/ultimate_ai_agent/core/approvals/policies.py",
        "src/ultimate_ai_agent/core/approvals/validation.py",
        "src/ultimate_ai_agent/core/approvals/receipts.py",
        "tests/test_approval_requests.py",
        "tests/test_approval_authority.py",
        "tests/test_approval_validation.py",
        "tests/test_approval_expiration.py",
        "tests/test_approval_scope.py",
        "tests/test_approval_receipts.py",
        "tests/test_approval_integration_model_router.py",
        "tests/test_approval_integration_model_runtime.py",
        "tests/test_approval_integration_tool_broker.py",
        "tests/test_approval_integration_kernel.py",
        "tests/test_m85_api_routes.py",
        "tests/test_m85_gate_integration.py",
    ]
    for rel_path in m85_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M8.5 file is missing: {rel_path}")
    ok("All M8.5 approval authority bridge files exist")

    # 8.16 Check M9 local loopback runtime adapter files existence
    m9_files = [
        "src/ultimate_ai_agent/core/model_runtime/loopback.py",
        "src/ultimate_ai_agent/core/model_runtime/execution_policy.py",
        "src/ultimate_ai_agent/core/model_runtime/transports.py",
        "src/ultimate_ai_agent/core/model_runtime/local_adapter.py",
        "tests/m9_helpers.py",
        "tests/test_local_loopback_endpoint_policy.py",
        "tests/test_local_loopback_transport.py",
        "tests/test_local_loopback_adapter.py",
        "tests/test_local_loopback_approval.py",
        "tests/test_local_loopback_no_remote.py",
        "tests/test_local_loopback_api_routes.py",
        "tests/test_m9_gate_integration.py",
    ]
    for rel_path in m9_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M9 file is missing: {rel_path}")
    ok("All M9 local loopback model runtime adapter files exist")

    # 8.17 Check M10 manual local loopback smoke harness files existence
    m10_files = [
        "src/ultimate_ai_agent/core/model_runtime/smoke_policy.py",
        "src/ultimate_ai_agent/core/model_runtime/smoke.py",
        "src/ultimate_ai_agent/core/model_runtime/manual_loopback_transport.py",
        "scripts/local_loopback_smoke.py",
        "tests/m10_helpers.py",
        "tests/test_manual_loopback_smoke_policy.py",
        "tests/test_manual_loopback_smoke_transport.py",
        "tests/test_manual_loopback_smoke_script.py",
        "tests/test_manual_loopback_smoke_api_routes.py",
        "tests/test_m10_gate_integration.py",
    ]
    for rel_path in m10_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M10 file is missing: {rel_path}")
    ok("All M10 manual local loopback smoke harness files exist")

    # 8.18 Check M10.5 remote worker foundation files existence
    m105_files = [
        "src/ultimate_ai_agent/core/remote_workers/__init__.py",
        "src/ultimate_ai_agent/core/remote_workers/enums.py",
        "src/ultimate_ai_agent/core/remote_workers/nodes.py",
        "src/ultimate_ai_agent/core/remote_workers/transports.py",
        "src/ultimate_ai_agent/core/remote_workers/registry.py",
        "src/ultimate_ai_agent/core/remote_workers/policy.py",
        "src/ultimate_ai_agent/core/remote_workers/jobs.py",
        "src/ultimate_ai_agent/core/remote_workers/results.py",
        "src/ultimate_ai_agent/core/remote_workers/audit.py",
        "src/ultimate_ai_agent/core/remote_workers/status.py",
        "src/ultimate_ai_agent/core/remote_workers/validation.py",
        "src/ultimate_ai_agent/core/remote_workers/dry_run.py",
        "tests/test_remote_worker_models.py",
        "tests/test_remote_worker_registry.py",
        "tests/test_remote_worker_policy.py",
        "tests/test_remote_worker_transports.py",
        "tests/test_remote_worker_dry_run.py",
        "tests/test_remote_worker_api_routes.py",
        "tests/test_remote_worker_no_network.py",
        "tests/test_remote_worker_gate_integration.py",
        "docs/remote/PRIVATE_MESH_TRANSPORT_POLICY.md",
        "docs/decisions/ADR-open-source-first-private-networking.md",
    ]
    for rel_path in m105_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M10.5 file is missing: {rel_path}")
    ok("All M10.5 remote worker foundation files exist")

    # 8.19 Check M11 runtime readiness gate files existence
    m11_files = [
        "src/ultimate_ai_agent/core/runtime_readiness/__init__.py",
        "src/ultimate_ai_agent/core/runtime_readiness/enums.py",
        "src/ultimate_ai_agent/core/runtime_readiness/matrix.py",
        "src/ultimate_ai_agent/core/runtime_readiness/reports.py",
        "src/ultimate_ai_agent/core/runtime_readiness/smoke_reports.py",
        "src/ultimate_ai_agent/core/runtime_readiness/validators.py",
        "src/ultimate_ai_agent/core/runtime_readiness/gate.py",
        "tests/test_runtime_capability_matrix.py",
        "tests/test_manual_smoke_report_validation.py",
        "tests/test_runtime_readiness_report.py",
        "tests/test_runtime_readiness_api_routes.py",
        "tests/test_runtime_readiness_no_execution.py",
        "tests/test_m11_gate_integration.py",
        "docs/runtime/RUNTIME_READINESS.md",
        "docs/runtime/MANUAL_SMOKE_REPORTS.md",
        "docs/runtime/RUNTIME_CAPABILITY_MATRIX.md",
    ]
    for rel_path in m11_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M11 file is missing: {rel_path}")
    ok("All M11 runtime readiness gate files exist")

    # 8.20 Check M12 Control Center contract files existence
    m12_files = [
        "src/ultimate_ai_agent/core/control_center/__init__.py",
        "src/ultimate_ai_agent/core/control_center/enums.py",
        "src/ultimate_ai_agent/core/control_center/manifest.py",
        "src/ultimate_ai_agent/core/control_center/dashboard.py",
        "src/ultimate_ai_agent/core/control_center/actions.py",
        "src/ultimate_ai_agent/core/control_center/policy.py",
        "src/ultimate_ai_agent/core/control_center/summaries.py",
        "src/ultimate_ai_agent/core/control_center/validation.py",
        "tests/test_control_center_manifest.py",
        "tests/test_control_center_dashboard.py",
        "tests/test_control_center_action_preview.py",
        "tests/test_control_center_api_routes.py",
        "tests/test_control_center_no_execution.py",
        "tests/test_m12_gate_integration.py",
        "docs/control_center/CONTROL_CENTER_CONTRACT.md",
        "docs/control_center/DASHBOARD_SNAPSHOT.md",
        "docs/control_center/ACTION_PREVIEW_POLICY.md",
    ]
    for rel_path in m12_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M12 file is missing: {rel_path}")
    ok("All M12 Control Center contract and read-only dashboard API files exist")

    # 8.21 Check M13 Web Control Center shell files existence
    m13_files = [
        "apps/control-center/package.json",
        "apps/control-center/package-lock.json",
        "apps/control-center/index.html",
        "apps/control-center/vite.config.ts",
        "apps/control-center/tsconfig.json",
        "apps/control-center/src/App.tsx",
        "apps/control-center/src/main.tsx",
        "apps/control-center/src/api/client.ts",
        "apps/control-center/src/api/endpoints.ts",
        "apps/control-center/src/api/redaction.ts",
        "apps/control-center/src/mocks/controlCenterData.ts",
        "apps/control-center/src/components/ActionPreviewForm.tsx",
        "apps/control-center/src/App.test.tsx",
        "scripts/verify_control_center_frontend.py",
        "scripts/verify_control_center_browser_smoke_readiness.py",
        "tests/test_control_center_frontend_safety_verifier.py",
        "tests/test_control_center_browser_smoke_readiness_verifier.py",
        "tests/test_m13_gate_integration.py",
        "docs/control_center/WEB_CONTROL_CENTER_SHELL.md",
        "docs/control_center/FRONTEND_SAFETY_POLICY.md",
        "docs/control_center/CONTROL_CENTER_FRONTEND_ROUTES.md",
        "docs/control_center/LOCAL_BROWSER_SMOKE.md",
    ]
    for rel_path in m13_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M13 file is missing: {rel_path}")
    ok("All M13 Web Control Center read-only shell files exist")

    # 8.22 Check M14 Web Control Center local backend connection files existence
    m14_files = [
        "apps/control-center/src/api/baseUrl.ts",
        "apps/control-center/src/api/baseUrl.test.ts",
        "tests/test_m14_gate_integration.py",
        "docs/control_center/LOCAL_BACKEND_CONNECTION.md",
    ]
    for rel_path in m14_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M14 file is missing: {rel_path}")
    ok("All M14 Web Control Center local backend connection files exist")

    # 8.23 Check M19 Mobile Companion contract/API planning files existence
    m19_files = [
        "src/ultimate_ai_agent/core/mobile_companion/__init__.py",
        "src/ultimate_ai_agent/core/mobile_companion/enums.py",
        "src/ultimate_ai_agent/core/mobile_companion/contracts.py",
        "src/ultimate_ai_agent/core/mobile_companion/permissions.py",
        "src/ultimate_ai_agent/core/mobile_companion/receipts.py",
        "src/ultimate_ai_agent/core/mobile_companion/planning.py",
        "tests/test_mobile_companion_contracts.py",
        "tests/test_mobile_companion_permissions.py",
        "tests/test_mobile_companion_no_sensor_access.py",
        "tests/test_mobile_companion_no_authority.py",
        "tests/test_m19_gate_integration.py",
        "docs/mobile/MOBILE_COMPANION_CONTRACT.md",
        "docs/mobile/MOBILE_CLIENT_SURFACE_ROLES.md",
        "docs/mobile/MOBILE_API_PLANNING.md",
        "docs/mobile/MOBILE_PERMISSION_RECEIPT_FLOW.md",
        "docs/mobile/MOBILE_SENSOR_BOUNDARY.md",
        "docs/mobile/MOBILE_SECURITY_MODEL.md",
        "docs/mobile/MOBILE_CAPTURE_POLICY.md",
        "docs/mobile/CCC_IOS_ANDROID_STRATEGY.md",
        "docs/mobile/MOBILE_PAIRING_TRUST_PLANNING.md",
        "docs/mobile/MOBILE_COMPANION_NON_GOALS.md",
    ]
    for rel_path in m19_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M19 file is missing: {rel_path}")
    ok("All M19 Mobile Companion contract/API planning files exist")

    # 8.24 Check M20 Device Capability Broker contract files existence
    m20_files = [
        "src/ultimate_ai_agent/core/device_capabilities/__init__.py",
        "src/ultimate_ai_agent/core/device_capabilities/contracts.py",
        "src/ultimate_ai_agent/core/device_capabilities/enums.py",
        "src/ultimate_ai_agent/core/device_capabilities/manifests.py",
        "src/ultimate_ai_agent/core/device_capabilities/policy.py",
        "src/ultimate_ai_agent/core/device_capabilities/receipts.py",
        "src/ultimate_ai_agent/core/device_capabilities/validation.py",
        "tests/test_device_capability_contracts.py",
        "tests/test_device_capability_manifest.py",
        "tests/test_device_capability_validation.py",
        "tests/test_device_capability_no_sensor_access.py",
        "tests/test_device_capability_no_authority.py",
        "tests/test_m20_gate_integration.py",
        "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_CONTRACT.md",
        "docs/device_capabilities/CAPABILITY_MANIFEST_SCHEMA.md",
        "docs/device_capabilities/DEVICE_PERMISSION_LIFECYCLE.md",
        "docs/device_capabilities/CAPTURE_INTENT_CONTRACT.md",
        "docs/device_capabilities/SENSOR_BOUNDARY_AND_NON_GOALS.md",
        "docs/device_capabilities/DEVICE_TRUST_AND_REVOCATION_CONTRACT.md",
        "docs/device_capabilities/DEVICE_RECEIPT_AND_REDACTION_POLICY.md",
        "docs/device_capabilities/DEVICE_CAPABILITY_SECURITY_MODEL.md",
        "docs/device_capabilities/DEVICE_CAPABILITY_BROKER_NON_GOALS.md",
        "docs/release_notes/v0_24_0.md",
        "docs/archive/releases/v0_24_0/README_IMPORT.md",
        "docs/archive/releases/v0_24_0/master_plan.md",
        "docs/implementation/foundation_gate_implementation_plan_v0_24_0.md",
    ]
    for rel_path in m20_files:
        p = ROOT / rel_path
        if not p.exists():
            fail(f"Required M20 file is missing: {rel_path}")
    ok("All M20 Device Capability Broker contract files exist")
    
    # 9. Enforce scans by delegating to verify_all
    try:
        from verify_all import run_static_scans
    except Exception as exc:
        fail(f"Could not import verify_all scan helpers: {exc}")
    run_static_scans()

    print("\nConsistency verification PASSED")

if __name__ == "__main__":
    main()
