from __future__ import annotations

import hashlib
import stat
import struct
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RENDER_DIR = (
    ROOT
    / "docs"
    / "design"
    / "control_center_north_star"
    / "renders"
    / "news-signals-v1"
)
EXPECTED = {
    "01-news-signals-home.png": (
        1576,
        998,
        "d522b722da09de2a6beaf83cf670ce8fb30f5438f7f8f4607256962a88a231df",
    ),
    "02-news-signals-compact.png": (
        1280,
        820,
        "e86b13478913420c684fb83a97ef1016641c06216b527ffa2aeab74f1446e36f",
    ),
    "03-news-signals-narrow-desktop.png": (
        1024,
        768,
        "eff955a3fdd62997ea19f328bf639ae6bcf614e934a2bbfda6d0d70bfa420d59",
    ),
    "04-news-signals-community-filter.png": (
        1576,
        998,
        "3c631cb500208bd6749e0098955869a4a3f8fce39e778a1020fa1eb592ba653d",
    ),
}


def test_news_signals_desktop_evidence_is_hash_and_dimension_bound() -> None:
    readme = (RENDER_DIR / "README.md").read_text(encoding="utf-8")

    for name, (width, height, expected_digest) in EXPECTED.items():
        path = RENDER_DIR / name
        mode = path.lstat().st_mode
        assert stat.S_ISREG(mode), f"render evidence must be a regular file: {name}"

        payload = path.read_bytes()
        assert payload.startswith(b"\x89PNG\r\n\x1a\n")
        actual_width, actual_height = struct.unpack(">II", payload[16:24])
        assert (actual_width, actual_height) == (width, height)
        assert hashlib.sha256(payload).hexdigest() == expected_digest
        assert expected_digest in readme


def test_news_signals_render_contract_remains_fixture_only() -> None:
    readme = (RENDER_DIR / "README.md").read_text(encoding="utf-8").lower()

    assert "fixture-only" in readme
    assert "not evidence of source ingestion" in readme
    assert "no credentials" in readme
    assert "production-readiness claim" in readme
