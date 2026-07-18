from __future__ import annotations

import json
import os
import stat
from pathlib import Path

import pytest

from scripts.verify_governed_browser_queue01_group08 import verify
from tests.test_governed_browser_queue01_group08 import (
    _exact,
    _pinned,
    _service,
    _transfer_context,
)
from ultimate_ai_agent.core.governed_browser import (
    GovernedArtifactMediaType,
    GovernedArtifactQuarantineError,
    GovernedArtifactQuarantineStore,
    GovernedArtifactTransferOperation,
)


def test_quarantine_store_rejects_symlinks_substitution_and_unsafe_modes(
    tmp_path: Path,
) -> None:
    target = tmp_path / "target"
    target.mkdir(mode=0o700)
    linked = tmp_path / "linked"
    linked.symlink_to(target, target_is_directory=True)
    with pytest.raises(ValueError, match="QUARANTINE_ROOT_UNSAFE"):
        GovernedArtifactQuarantineStore(linked)
    assert stat.S_IMODE(os.lstat(target).st_mode) == 0o700

    unsafe = tmp_path / "unsafe"
    unsafe.mkdir(mode=0o755)
    with pytest.raises(ValueError, match="QUARANTINE_ROOT_UNSAFE"):
        GovernedArtifactQuarantineStore(unsafe)

    root = tmp_path / "owned"
    store = GovernedArtifactQuarantineStore(root)
    quarantine = root / "artifact-quarantine"
    moved = root / "artifact-quarantine-moved"
    quarantine.rename(moved)
    quarantine.symlink_to(moved, target_is_directory=True)
    quarantine_ref = _pinned(
        "artifact-quarantine-ref:governed-browser",
        suffix="substitution",
    )
    with pytest.raises(
        GovernedArtifactQuarantineError,
        match="SUBSTITUTION_DENIED",
    ):
        store.quarantine(
            quarantine_ref=quarantine_ref,
            payload=b"must not write",
            declared_media_type=GovernedArtifactMediaType.text_plain,
            max_bytes=1024,
        )
    assert list(moved.iterdir()) == []


def test_group08_verifier_passes_and_contains_no_raw_material() -> None:
    assert verify() == []
    source = Path(
        "src/ultimate_ai_agent/core/governed_browser/artifact_transfers.py"
    ).read_text(encoding="utf-8")
    rendered = json.dumps({"source": source})
    for forbidden in (
        "import requests",
        "from requests import",
        "import httpx",
        "from httpx import",
        "import urllib.request",
        "from urllib import request",
        "import urllib3",
        "from urllib3 import",
        "import http.client",
        "from http import client",
        "import playwright",
        "from playwright import",
        "import selenium",
        "from selenium import",
        "import subprocess",
        "/Users/",
        "file://",
    ):
        assert forbidden not in rendered


def test_immutable_download_payload_is_rejected_before_transaction(
    tmp_path: Path,
) -> None:
    store = GovernedArtifactQuarantineStore(tmp_path / "artifacts")
    request, recipe, registry = _transfer_context(
        store,
        operation=GovernedArtifactTransferOperation.download_quarantine,
        suffix="immutable-payload",
    )
    service, _, _ = _service(
        tmp_path / "kernel",
        store=store,
        request=request,
        registry=registry,
    )

    with pytest.raises(TypeError, match="MUTABLE_PAYLOAD_REQUIRED"):
        service.execute(
            _exact(request, recipe),
            injected_download_payload=b"immutable",  # type: ignore[arg-type]
        )

    assert list((tmp_path / "artifacts" / "artifact-quarantine").iterdir()) == []
    assert (
        recipe.recipe_ref.encode()
        not in (tmp_path / "kernel" / "transactions.sqlite3").read_bytes()
    )
