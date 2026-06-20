#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

def main() -> int:
    from ultimate_ai_agent.core.gate.architecture import evaluate_gate_architecture
    from ultimate_ai_agent.core.gate.evaluator_registry import evaluator_registry

    report = evaluate_gate_architecture(ROOT)
    registry = evaluator_registry()
    if not registry:
        print("FAIL: Foundation Gate evaluator registry is empty")
        return 1
    if report.failures:
        for failure in report.failures:
            print(f"FAIL: {failure}")
        return 1
    print("OK: Foundation Gate evaluator architecture guard passed")
    for item in report.items:
        print(
            f"OK: {item.relative_path} lines={item.line_count} ceiling={item.line_ceiling} status={item.status}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
