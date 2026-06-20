from __future__ import annotations

from collections.abc import Iterable

from fastapi import APIRouter, FastAPI


def register_router_once(app: FastAPI, router: APIRouter, *, state_attr: str) -> None:
    """Register router routes once while preserving path+method distinctions."""

    if getattr(app.state, state_attr, False):
        return
    registered_keys = {_route_key(route) for route in app.router.routes}
    for route in router.routes:
        key = _route_key(route)
        if key in registered_keys:
            continue
        app.router.routes.append(route)
        registered_keys.add(key)
    setattr(app.state, state_attr, True)


def _route_key(route: object) -> tuple[str | None, tuple[str, ...]]:
    methods = getattr(route, "methods", None)
    return (
        getattr(route, "path", None),
        tuple(sorted(_safe_methods(methods))),
    )


def _safe_methods(methods: object) -> Iterable[str]:
    if isinstance(methods, (set, frozenset, list, tuple)):
        return (str(method) for method in methods)
    return ()
