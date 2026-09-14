from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest

from scripts.verification import test_corpus_guard as guard


PROJECT = "apps/control-center/package.json"
LOCK = "apps/control-center/package-lock.json"


def _pair() -> tuple[dict[str, str], dict[str, str]]:
    prior = {
        PROJECT: '{"scripts":{"test":"vitest"},"devDependencies":{"vitest":"4.1.8"}}\n',
        LOCK: '{"lockfileVersion":3,"packages":{"node_modules/vitest":{"version":"4.1.8"}}}\n',
    }
    current = {path: value.replace("4.1.8", "4.1.11") for path, value in prior.items()}
    return prior, current


def _bind_pair(
    monkeypatch: pytest.MonkeyPatch, prior: dict[str, str], current: dict[str, str]
) -> None:
    monkeypatch.setattr(
        guard,
        "VITEST_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH",
        {
            path: (
                hashlib.sha256(prior[path].encode()).hexdigest(),
                hashlib.sha256(current[path].encode()).hexdigest(),
            )
            for path in prior
        },
    )


@pytest.mark.parametrize("side", ("prior", "current"))
@pytest.mark.parametrize(
    "mutation",
    (
        "manifest_byte",
        "lock_byte",
        "missing_manifest",
        "missing_lock",
        "extra_lock",
        "reversed",
    ),
)
def test_vitest_security_transition_rejects_any_pair_substitution(
    monkeypatch: pytest.MonkeyPatch, side: str, mutation: str
) -> None:
    prior, current = _pair()
    _bind_pair(monkeypatch, prior, current)
    assert guard._safe_vitest_security_dependency_alignment_paths(
        prior_by_path=prior, current_by_path=current
    ) == {PROJECT, LOCK}
    target = prior if side == "prior" else current
    if mutation == "manifest_byte":
        target[PROJECT] += " "
    elif mutation == "lock_byte":
        target[LOCK] += " "
    elif mutation == "missing_manifest":
        del target[PROJECT]
    elif mutation == "missing_lock":
        del target[LOCK]
    elif mutation == "extra_lock":
        target["apps/control-center/npm-shrinkwrap.json"] = target[LOCK]
    else:
        target[PROJECT] = (current if side == "prior" else prior)[PROJECT]
    assert not guard._safe_vitest_security_dependency_alignment_paths(
        prior_by_path=prior, current_by_path=current
    )


@pytest.mark.parametrize(
    "mutation",
    (
        "none",
        "test_script",
        "extra_lock",
        "partial_pair",
        "wrong_base",
        "different_patch",
    ),
)
def test_vitest_security_transition_keeps_collection_boundary_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    prior, current = _pair()
    _bind_pair(monkeypatch, prior, current)
    if mutation == "test_script":
        current[PROJECT] = current[PROJECT].replace(
            '"test":"vitest"', '"test":"vitest --passWithNoTests"'
        )
    elif mutation == "extra_lock":
        path = "apps/control-center/npm-shrinkwrap.json"
        prior[path], current[path] = prior[LOCK], current[LOCK]
    elif mutation == "partial_pair":
        del current[LOCK]
    elif mutation == "wrong_base":
        prior[PROJECT] = prior[PROJECT].replace("4.1.8", "4.1.7")
    elif mutation == "different_patch":
        current[LOCK] = current[LOCK].replace("4.1.11", "4.1.12")
    for path, value in current.items():
        target = tmp_path / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value)
    outputs = iter((("\0".join(current) + "\0").encode(), b"", b"", b""))
    monkeypatch.setattr(
        guard,
        "_run_git",
        lambda _repo, _args: subprocess.CompletedProcess(
            args=[], returncode=0, stdout=next(outputs), stderr=b""
        ),
    )
    monkeypatch.setattr(guard, "_base_text", lambda _repo, _base, path: prior.get(path))
    if mutation == "none":
        assert guard._changed_test_paths(tmp_path, "a" * 40) == ()
    else:
        with pytest.raises(
            guard.TestCorpusGuardError,
            match="frontend test (script|dependency boundary)",
        ):
            guard._changed_test_paths(tmp_path, "a" * 40)


def test_vitest_security_transition_matches_exact_committed_dependency_bytes() -> None:
    root = Path(__file__).parents[1]
    for path, (
        _,
        current_digest,
    ) in guard.VITEST_SECURITY_DEPENDENCY_APPROVED_SHA256_BY_PATH.items():
        assert hashlib.sha256((root / path).read_bytes()).hexdigest() == current_digest
