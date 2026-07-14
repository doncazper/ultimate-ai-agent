from __future__ import annotations

import hashlib
import json
from pathlib import Path
import stat
import struct


ROOT = Path(__file__).resolve().parents[1]
BASELINE = (
    ROOT / "docs/design/control_center_north_star/CURRENT_RENDER_BASELINE.json"
)
PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def test_accepted_studio_render_is_hash_dimension_and_mode_bound() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    surfaces = payload["current_surface_revisions"]
    surface = surfaces["studio"]

    assert surface["modes"] == ["chat", "code", "create"]
    assert surface["platform"] == "macos_desktop"
    render = BASELINE.parent / surface["latest"]
    info = render.lstat()
    assert stat.S_ISREG(info.st_mode)
    assert info.st_nlink == 1

    encoded = render.read_bytes()
    assert encoded.startswith(PNG_SIGNATURE)
    width, height = struct.unpack(">II", encoded[16:24])
    assert width == surface["pixel_width"] == 1586
    assert height == surface["pixel_height"] == 992
    assert hashlib.sha256(encoded).hexdigest() == surface["sha256"]


def test_accepted_skill_workbench_views_are_hash_and_signal_bound() -> None:
    payload = json.loads(BASELINE.read_text(encoding="utf-8"))
    surface = payload["current_surface_revisions"]["skill_workbench"]

    assert surface["default_view"] == "list"
    assert surface["page_size"] == 25
    assert surface["grid_filter"] == "hermes"
    assert surface["canonical_ui_reference"] == "studio_create_dense_discovery"
    assert surface["list_columns"] == [
        "skill",
        "category",
        "source",
        "rank",
        "source_signal",
        "popularity",
        "updated",
    ]
    assert surface["compact_list_columns"] == [
        "skill",
        "source",
        "rank",
        "source_signal",
    ]
    assert (
        surface["primary_value_overflow"]
        == "wrap_or_hide_whole_column_never_ellipsis"
    )
    assert surface["secondary_ellipsis_allowed"] == ["safe_summary", "safe_ref"]
    assert surface["hidden_compact_details_remain_in_inspector"] is True
    assert surface["source_signals"] == [
        "rank",
        "stars",
        "downloads",
        "ratings_when_provided",
    ]
    assert surface["risk_label"] == "not_assessed_in_inspector_only"
    for view in ("grid", "list"):
        render = BASELINE.parent / surface[view]
        info = render.lstat()
        assert stat.S_ISREG(info.st_mode)
        assert info.st_nlink == 1
        encoded = render.read_bytes()
        assert encoded.startswith(PNG_SIGNATURE)
        width, height = struct.unpack(">II", encoded[16:24])
        assert width == surface["pixel_width"] == 1586
        assert height == surface["pixel_height"] == 992
        assert hashlib.sha256(encoded).hexdigest() == surface[f"{view}_sha256"]
