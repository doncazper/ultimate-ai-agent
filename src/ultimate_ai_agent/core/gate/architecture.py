from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


LEGACY_EVALUATOR_RELATIVE_PATH = Path("src/ultimate_ai_agent/core/gate/evaluators.py")
LEGACY_EVALUATOR_LINE_CEILING = 58000
NEW_EVALUATOR_MODULE_LINE_CEILING = 1500
ROUTE_BOUNDARY_MODULE_RELATIVE_PATH = Path(
    "src/ultimate_ai_agent/core/gate/evaluator_modules/route_boundaries.py"
)
ROUTE_BOUNDARY_MODULE_LINE_CEILING = 5000


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
    if evaluator_modules_dir.exists():
        paths.update(evaluator_modules_dir.glob("*.py"))
    for path in sorted(paths):
        relative_path = path.relative_to(repo_root)
        line_count = _line_count(path)
        if relative_path == LEGACY_EVALUATOR_RELATIVE_PATH:
            ceiling = LEGACY_EVALUATOR_LINE_CEILING
            status = "legacy_ceiling"
        elif relative_path == ROUTE_BOUNDARY_MODULE_RELATIVE_PATH:
            ceiling = ROUTE_BOUNDARY_MODULE_LINE_CEILING
            status = "route_boundary_extraction_ceiling"
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
    return GateArchitectureReport(
        passed=not failures,
        items=tuple(items),
        failures=tuple(failures),
    )


def _line_count(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _line in handle)
