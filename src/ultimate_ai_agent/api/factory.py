from __future__ import annotations

from fastapi import FastAPI


def build_app() -> FastAPI:
    """Compatibility app factory seam for the current monolithic API module.

    The existing route declarations still live in ``api.app`` for this slice.
    New route groups should register through router modules so this function can
    become the owning construction path as the legacy module is split.
    """

    from ultimate_ai_agent.api.app import app

    return app
