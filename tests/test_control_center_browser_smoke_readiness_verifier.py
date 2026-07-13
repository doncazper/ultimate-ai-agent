from typing import Any
import importlib.util
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/verify_control_center_browser_smoke_readiness.py"


def load_verifier() -> Any:
    spec = importlib.util.spec_from_file_location("verify_control_center_browser_smoke_readiness", SCRIPT)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def write_frontend_make_contract(root: Path, verifier: Any) -> None:
    (root / "Makefile").write_text(
        "\n".join(verifier.REQUIRED_FRONTEND_MAKE_FRAGMENTS),
        encoding="utf-8",
    )


def test_control_center_browser_smoke_readiness_verifier_passes_current_repo() -> None:
    verifier = load_verifier()

    assert verifier.verify(ROOT) == []


def test_control_center_browser_smoke_readiness_verifier_blocks_unsafe_ci_and_docs(tmp_path: Path) -> None:
    (tmp_path / ".github/workflows").mkdir(parents=True)
    (tmp_path / "apps/control-center").mkdir(parents=True)
    (tmp_path / "docs/control_center").mkdir(parents=True)
    (tmp_path / ".github/workflows/ci.yml").write_text(
        "jobs:\n  smoke:\n    steps:\n      - run: npx playwright test https://example.com\n",
        encoding="utf-8",
    )
    (tmp_path / "apps/control-center/package.json").write_text(
        '{"scripts":{"dev":"vite --host 127.0.0.1","preview":"vite preview --host 127.0.0.1"}}',
        encoding="utf-8",
    )
    (tmp_path / "docs/control_center/LOCAL_BROWSER_SMOKE.md").write_text(
        "Use Chrome authenticated profile control against production.\n",
        encoding="utf-8",
    )
    (tmp_path / "docs/control_center/LOCAL_BROWSER_SMOKE_REPORTING.md").write_text(
        "Local browser smoke report may include screenshots with secrets.\n",
        encoding="utf-8",
    )

    verifier = load_verifier()
    failures = verifier.verify(tmp_path)

    assert any("forbidden CI browser automation fragment" in failure for failure in failures)
    assert any("smoke doc missing required safety wording" in failure for failure in failures)
    assert any("smoke reporting doc missing required safety wording" in failure for failure in failures)
    assert any("forbidden smoke doc fragment" in failure for failure in failures)


def test_control_center_browser_smoke_readiness_allows_exact_browser_install(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            [
                *verifier.REQUIRED_CI_FRAGMENTS,
                "- name: Install Playwright Chromium",
                "PLAYWRIGHT_BROWSERS_PATH: ${{ runner.temp }}/playwright-browsers",
                "run: npx playwright install chromium",
            ]
        ),
        encoding="utf-8",
    )
    write_frontend_make_contract(tmp_path, verifier)

    assert verifier._ci_failures(tmp_path) == []


def test_control_center_browser_smoke_readiness_rejects_shared_browser_cache(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            [
                *verifier.REQUIRED_CI_FRAGMENTS,
                "- name: Install Playwright Chromium",
                "PLAYWRIGHT_BROWSERS_PATH: shared-browser-profile",
                "run: npx playwright install chromium",
            ]
        ),
        encoding="utf-8",
    )
    write_frontend_make_contract(tmp_path, verifier)

    failures = verifier._ci_failures(tmp_path)

    assert any("forbidden CI browser automation fragment" in item for item in failures)


def test_control_center_browser_smoke_readiness_rejects_chained_browser_install(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text(
        "\n".join(
            [
                *verifier.REQUIRED_CI_FRAGMENTS,
                "- name: Install Playwright Chromium",
                "run: npx playwright install chromium && npx playwright test https://example.invalid",
            ]
        ),
        encoding="utf-8",
    )
    write_frontend_make_contract(tmp_path, verifier)

    failures = verifier._ci_failures(tmp_path)

    assert any("forbidden CI browser automation fragment: playwright" in failure for failure in failures)


def test_control_center_browser_smoke_readiness_rejects_frontend_make_drift(
    tmp_path: Path,
) -> None:
    verifier = load_verifier()
    workflow = tmp_path / ".github/workflows/ci.yml"
    workflow.parent.mkdir(parents=True)
    workflow.write_text("\n".join(verifier.REQUIRED_CI_FRAGMENTS), encoding="utf-8")
    (tmp_path / "Makefile").write_text("frontend-check:\n\ttrue\n", encoding="utf-8")

    failures = verifier._ci_failures(tmp_path)

    assert any("canonical frontend Make target missing" in failure for failure in failures)
