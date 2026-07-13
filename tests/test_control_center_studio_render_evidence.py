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
