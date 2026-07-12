#!/usr/bin/env python3
"""Serve the local Control Center render-review gallery."""

from __future__ import annotations

import argparse
import functools
import http.server
from pathlib import Path
import socketserver


REPO_ROOT = Path(__file__).resolve().parents[2]
NORTH_STAR_ROOT = REPO_ROOT / "docs/design/control_center_north_star"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=4179)
    args = parser.parse_args()

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler,
        directory=str(NORTH_STAR_ROOT),
    )
    with socketserver.TCPServer((args.host, args.port), handler) as server:
        print(
            "Control Center render review: "
            f"http://{args.host}:{args.port}/render-review/"
        )
        server.serve_forever()


if __name__ == "__main__":
    main()
