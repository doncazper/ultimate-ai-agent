from __future__ import annotations

from contextlib import contextmanager
from pathlib import Path
from threading import RLock
from typing import Any, Iterator


_LEGACY_GLOBAL_CACHE_LOCK = RLock()


class GateEvaluationContext:
    """Per-run caches for Foundation Gate filesystem and OpenAPI reads.

    The legacy evaluator still contains historical direct ``Path`` and OpenAPI
    calls. Keep that compatibility path serialized here so the evaluator no
    longer owns process-wide monkeypatch mechanics.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._rglob_cache: dict[tuple[Path, str], tuple[Path, ...]] = {}
        self._read_text_cache: dict[tuple[Path, tuple[Any, ...], tuple[tuple[str, Any], ...]], str] = {}
        self._cacheable_paths: dict[Path, bool] = {}
        self._openapi_schema_cache: dict[str, Any] = {}
        self._openapi_contract_cache: dict[str, Any] = {}

    def is_cacheable(self, path: Path) -> bool:
        cached = self._cacheable_paths.get(path)
        if cached is not None:
            return cached
        try:
            cacheable = path.resolve().is_relative_to(self.root)
        except (OSError, RuntimeError):
            cacheable = False
        self._cacheable_paths[path] = cacheable
        return cacheable

    def rglob(self, path: Path, pattern: str) -> Iterator[Path]:
        if not self.is_cacheable(path):
            return path.rglob(pattern)
        key = (path, pattern)
        if key not in self._rglob_cache:
            self._rglob_cache[key] = tuple(path.rglob(pattern))
        return iter(self._rglob_cache[key])

    def read_text(self, path: Path, *args: Any, **kwargs: Any) -> str:
        if not self.is_cacheable(path):
            return path.read_text(*args, **kwargs)
        key = (path, args, tuple(sorted(kwargs.items())))
        if key not in self._read_text_cache:
            self._read_text_cache[key] = path.read_text(*args, **kwargs)
        return self._read_text_cache[key]

    @contextmanager
    def install_legacy_global_caches(self) -> Iterator[None]:
        from ultimate_ai_agent.api import app as api_app
        from ultimate_ai_agent.api import openapi as api_openapi

        with _LEGACY_GLOBAL_CACHE_LOCK:
            original_rglob = Path.rglob
            original_read_text = Path.read_text
            app = api_app.app
            original_openapi = app.openapi
            original_verify_openapi_contract = api_openapi.verify_openapi_contract

            def cached_rglob(path: Path, pattern: str) -> Any:
                if not self.is_cacheable(path):
                    return original_rglob(path, pattern)
                key = (path, pattern)
                if key not in self._rglob_cache:
                    self._rglob_cache[key] = tuple(original_rglob(path, pattern))
                return iter(self._rglob_cache[key])

            def cached_read_text(path: Path, *args: Any, **kwargs: Any) -> Any:
                if not self.is_cacheable(path):
                    return original_read_text(path, *args, **kwargs)
                key = (path, args, tuple(sorted(kwargs.items())))
                if key not in self._read_text_cache:
                    self._read_text_cache[key] = original_read_text(path, *args, **kwargs)
                return self._read_text_cache[key]

            def cached_openapi() -> Any:
                if "schema" not in self._openapi_schema_cache:
                    self._openapi_schema_cache["schema"] = original_openapi()
                return self._openapi_schema_cache["schema"]

            def cached_verify_openapi_contract(candidate_app: Any) -> Any:
                if candidate_app is not app:
                    return original_verify_openapi_contract(candidate_app)
                if "status" not in self._openapi_contract_cache:
                    self._openapi_contract_cache["status"] = (
                        original_verify_openapi_contract(candidate_app)
                    )
                return self._openapi_contract_cache["status"]

            Path.rglob = cached_rglob
            Path.read_text = cached_read_text
            app.openapi = cached_openapi
            api_openapi.verify_openapi_contract = cached_verify_openapi_contract
            try:
                yield
            finally:
                Path.rglob = original_rglob
                Path.read_text = original_read_text
                app.openapi = original_openapi
                api_openapi.verify_openapi_contract = original_verify_openapi_contract
