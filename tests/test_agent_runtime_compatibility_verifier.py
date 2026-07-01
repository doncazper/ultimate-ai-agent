from pathlib import Path

import scripts.verify_agent_runtime_compatibility as verifier


ROOT = Path(__file__).resolve().parent.parent


def test_agent_runtime_compatibility_verifier_passes_current_repo() -> None:
    assert verifier.verify(ROOT) == []


def test_agent_runtime_compatibility_verifier_flags_forbidden_import(tmp_path: Path) -> None:
    _copy_required_tree(tmp_path)
    target = tmp_path / "src/ultimate_ai_agent/core/agent_runtime/contracts.py"
    target.write_text(f"{target.read_text(encoding='utf-8')}\nimport openai\n", encoding="utf-8")

    failures = verifier.verify(tmp_path)

    assert any("forbidden import root: openai" in failure for failure in failures)


def test_agent_runtime_compatibility_verifier_flags_authority_default(tmp_path: Path) -> None:
    _copy_required_tree(tmp_path)
    target = tmp_path / "src/ultimate_ai_agent/core/agent_runtime/contracts.py"
    target.write_text(
        target.read_text(encoding="utf-8").replace(
            "execution_authorized: bool = False",
            "execution_authorized: bool = True",
        ),
        encoding="utf-8",
    )

    failures = verifier.verify(tmp_path)

    assert any("enables forbidden authority default" in failure for failure in failures)


def _copy_required_tree(tmp_path: Path) -> None:
    for rel_path in verifier.REQUIRED_PATHS:
        source = ROOT / rel_path
        destination = tmp_path / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    for rel_path in [
        Path("src/ultimate_ai_agent/core/capabilities/models.py"),
        Path("src/ultimate_ai_agent/core/capabilities/enums.py"),
        Path("src/ultimate_ai_agent/core/capabilities/adapters/openai_tools.py"),
        Path("src/ultimate_ai_agent/core/capabilities/adapters/mcp.py"),
    ]:
        source = ROOT / rel_path
        destination = tmp_path / rel_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    (tmp_path / "src/ultimate_ai_agent/api").mkdir(parents=True, exist_ok=True)
