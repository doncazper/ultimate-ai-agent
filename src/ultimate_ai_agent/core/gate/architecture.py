from __future__ import annotations

import ast
from dataclasses import dataclass, field
from pathlib import Path


LEGACY_EVALUATOR_RELATIVE_PATH = Path("src/ultimate_ai_agent/core/gate/evaluators.py")
LEGACY_EVALUATOR_LINE_CEILING = 120
LEGACY_CHECKS_RELATIVE_PATH = Path("src/ultimate_ai_agent/core/gate/legacy_checks.py")
LEGACY_CHECKS_LINE_CEILING = 140
LEGACY_SUPPORT_RELATIVE_PATH = Path("src/ultimate_ai_agent/core/gate/legacy_support.py")
LEGACY_SUPPORT_LINE_CEILING = 450
LEGACY_CHECK_FAMILY_DIR_RELATIVE_PATH = Path(
    "src/ultimate_ai_agent/core/gate/legacy_check_families"
)
LEGACY_CHECK_FAMILY_LINE_CEILING = 1400
CRITERIA_RELATIVE_PATH = Path("src/ultimate_ai_agent/core/gate/criteria.py")
CRITERIA_LINE_CEILING = 120
CRITERIA_FAMILY_DIR_RELATIVE_PATH = Path(
    "src/ultimate_ai_agent/core/gate/criteria_families"
)
CRITERIA_FAMILY_LINE_CEILING = 1500
LEGACY_EVALUATE_METHOD_LINE_CEILING = 80
GATE_TEST_IMPORT_CEILING = 0
NEW_EVALUATOR_MODULE_LINE_CEILING = 1500
ROUTE_BOUNDARY_MODULE_RELATIVE_PATH = Path(
    "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py"
)
ROUTE_BOUNDARY_MODULE_LINE_CEILING = 5075
EVALUATION_CONTEXT_RELATIVE_PATH = Path(
    "src/ultimate_ai_agent/core/gate/evaluation_context.py"
)
EVALUATION_CONTEXT_LINE_CEILING = 200
LEGACY_EVALUATOR_FORBIDDEN_GLOBAL_PATCH_FRAGMENTS = (
    "Path.rglob =",
    "Path.read_text =",
    "app.openapi =",
    "api_openapi.verify_openapi_contract =",
)


@dataclass(frozen=True)
class GateModuleSizeItem:
    relative_path: str
    line_count: int
    line_ceiling: int
    status: str


@dataclass(frozen=True)
class GateArchitectureReport:
    passed: bool
    items: tuple[GateModuleSizeItem, ...]
    failures: tuple[str, ...] = field(default_factory=tuple)


def evaluate_gate_architecture(root: Path | None = None) -> GateArchitectureReport:
    repo_root = root or Path.cwd()
    gate_dir = repo_root / "src" / "ultimate_ai_agent" / "core" / "gate"
    evaluator_modules_dir = gate_dir / "evaluator_modules"
    items: list[GateModuleSizeItem] = []
    failures: list[str] = []
    paths = set(gate_dir.glob("*evaluator*.py"))
    paths.add(gate_dir / LEGACY_CHECKS_RELATIVE_PATH.name)
    paths.add(gate_dir / LEGACY_SUPPORT_RELATIVE_PATH.name)
    paths.add(gate_dir / EVALUATION_CONTEXT_RELATIVE_PATH.name)
    paths.add(gate_dir / CRITERIA_RELATIVE_PATH.name)
    legacy_check_family_dir = gate_dir / LEGACY_CHECK_FAMILY_DIR_RELATIVE_PATH.name
    if legacy_check_family_dir.exists():
        paths.update(legacy_check_family_dir.glob("*.py"))
    criteria_family_dir = gate_dir / CRITERIA_FAMILY_DIR_RELATIVE_PATH.name
    if criteria_family_dir.exists():
        paths.update(criteria_family_dir.glob("*.py"))
    if evaluator_modules_dir.exists():
        paths.update(evaluator_modules_dir.glob("*.py"))
    for path in sorted(paths):
        relative_path = path.relative_to(repo_root)
        line_count = _line_count(path)
        if relative_path == LEGACY_EVALUATOR_RELATIVE_PATH:
            ceiling = LEGACY_EVALUATOR_LINE_CEILING
            status = "legacy_facade_ceiling"
        elif relative_path == LEGACY_CHECKS_RELATIVE_PATH:
            ceiling = LEGACY_CHECKS_LINE_CEILING
            status = "legacy_composition_ceiling"
        elif relative_path == LEGACY_SUPPORT_RELATIVE_PATH:
            ceiling = LEGACY_SUPPORT_LINE_CEILING
            status = "legacy_support_ceiling"
        elif relative_path.parent == LEGACY_CHECK_FAMILY_DIR_RELATIVE_PATH:
            ceiling = LEGACY_CHECK_FAMILY_LINE_CEILING
            status = "legacy_check_family_ceiling"
        elif relative_path == CRITERIA_RELATIVE_PATH:
            ceiling = CRITERIA_LINE_CEILING
            status = "criteria_facade_ceiling"
        elif relative_path.parent == CRITERIA_FAMILY_DIR_RELATIVE_PATH:
            ceiling = CRITERIA_FAMILY_LINE_CEILING
            status = "criteria_family_ceiling"
        elif relative_path == ROUTE_BOUNDARY_MODULE_RELATIVE_PATH:
            ceiling = ROUTE_BOUNDARY_MODULE_LINE_CEILING
            status = "route_boundary_extraction_ceiling"
        elif relative_path == EVALUATION_CONTEXT_RELATIVE_PATH:
            ceiling = EVALUATION_CONTEXT_LINE_CEILING
            status = "evaluation_context_ceiling"
        else:
            ceiling = NEW_EVALUATOR_MODULE_LINE_CEILING
            status = "modular_ceiling"
        item = GateModuleSizeItem(
            relative_path=str(relative_path),
            line_count=line_count,
            line_ceiling=ceiling,
            status=status,
        )
        items.append(item)
        if line_count > ceiling:
            failures.append(
                f"{item.relative_path} has {line_count} lines; ceiling is {ceiling}"
            )
        if relative_path in {
            LEGACY_EVALUATOR_RELATIVE_PATH,
            EVALUATION_CONTEXT_RELATIVE_PATH,
        }:
            failures.extend(_global_patch_failures(path))
        if relative_path == LEGACY_EVALUATOR_RELATIVE_PATH:
            failures.extend(_legacy_evaluator_failures(path))
    for path in sorted(gate_dir.rglob("*.py")):
        failures.extend(_gate_source_import_failures(path))
    return GateArchitectureReport(
        passed=not failures,
        items=tuple(items),
        failures=tuple(failures),
    )


def _line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _line in handle)


def _legacy_evaluator_failures(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    tree = ast.parse(text)
    evaluate_lines = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "evaluate":
            evaluate_lines = (node.end_lineno or node.lineno) - node.lineno + 1
            break
    if evaluate_lines > LEGACY_EVALUATE_METHOD_LINE_CEILING:
        failures.append(
            f"{path.as_posix()} evaluate() has {evaluate_lines} lines; "
            f"ceiling is {LEGACY_EVALUATE_METHOD_LINE_CEILING}"
        )
    return failures


def _global_patch_failures(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    failures: list[str] = []
    for fragment in LEGACY_EVALUATOR_FORBIDDEN_GLOBAL_PATCH_FRAGMENTS:
        if fragment in text:
            failures.append(
                f"{path.as_posix()} contains gate-owned global patch fragment {fragment!r}"
            )
    return failures


def _gate_source_import_failures(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    test_import_count = 0
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            test_import_count += sum(
                1
                for alias in node.names
                if alias.name == "tests" or alias.name.startswith("tests.")
            )
        elif isinstance(node, ast.ImportFrom) and (
            node.module == "tests" or (node.module or "").startswith("tests.")
        ):
            test_import_count += 1
    if test_import_count <= GATE_TEST_IMPORT_CEILING:
        return []
    return [
        f"{path.as_posix()} imports tests.* {test_import_count} times; "
        f"ceiling is {GATE_TEST_IMPORT_CEILING}"
    ]
