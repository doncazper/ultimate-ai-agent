#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from ultimate_ai_agent.core.secrets import LocalCredentialVaultBackend  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect local credential vault backend V1 safe refs without reading secrets."
    )
    parser.add_argument(
        "--state-dir",
        type=Path,
        default=None,
        help="Optional credential vault backend state directory to inspect.",
    )
    args = parser.parse_args()

    backend = (
        LocalCredentialVaultBackend(args.state_dir)
        if args.state_dir is not None
        else LocalCredentialVaultBackend.default()
    )
    snapshot = backend.inspect()
    try:
        print(json.dumps(snapshot.model_dump(mode="json"), indent=2, sort_keys=True))
    except BrokenPipeError:
        return 0
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
