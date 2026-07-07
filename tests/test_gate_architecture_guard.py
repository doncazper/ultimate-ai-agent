from pathlib import Path

from ultimate_ai_agent.core.gate.architecture import (
    EVALUATION_CONTEXT_LINE_CEILING,
    LEGACY_EVALUATOR_LINE_CEILING,
    LEGACY_EVALUATE_METHOD_LINE_CEILING,
    LEGACY_TEST_IMPORT_CEILING,
    ROUTE_BOUNDARY_MODULE_LINE_CEILING,
    evaluate_gate_architecture,
)
from ultimate_ai_agent.core.gate.evaluator_registry import evaluator_registry


ROOT = Path(__file__).resolve().parents[1]


def test_gate_architecture_guard_accepts_current_legacy_evaluator_ceiling() -> None:
    report = evaluate_gate_architecture(ROOT)

    assert report.passed is True
    legacy = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/evaluators.py")
    )
    assert legacy.line_count <= LEGACY_EVALUATOR_LINE_CEILING
    assert legacy.status == "legacy_ceiling"
    route_boundaries = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/evaluator_modules/route_boundaries.py")
    )
    assert route_boundaries.line_count <= ROUTE_BOUNDARY_MODULE_LINE_CEILING
    assert route_boundaries.status == "route_boundary_extraction_ceiling"
    context = next(
        item
        for item in report.items
        if item.relative_path.endswith("core/gate/evaluation_context.py")
    )
    assert context.line_count <= EVALUATION_CONTEXT_LINE_CEILING
    assert context.status == "evaluation_context_ceiling"
    assert not report.failures


def test_gate_architecture_guard_ratchets_legacy_evaluator_debt() -> None:
    evaluator_path = ROOT / "src/ultimate_ai_agent/core/gate/evaluators.py"
    text = evaluator_path.read_text(encoding="utf-8")

    assert "Path.rglob =" not in text
    assert "Path.read_text =" not in text
    assert "app.openapi =" not in text
    assert text.count("from tests.") <= LEGACY_TEST_IMPORT_CEILING

    import ast

    tree = ast.parse(text)
    evaluate_node = next(
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate"
    )
    assert (
        evaluate_node.end_lineno - evaluate_node.lineno + 1
        <= LEGACY_EVALUATE_METHOD_LINE_CEILING
    )


def test_evaluator_registry_names_planned_split_boundaries() -> None:
    entries = evaluator_registry()
    names = {entry.name for entry in entries}

    assert "legacy_foundation_gate_evaluator" in names
    assert "route_contract_evaluators" in names
    assert "security_redaction_evaluators" in names
    assert "frontend_product_evaluators" in names
    assert "storage_backup_evaluators" in names
