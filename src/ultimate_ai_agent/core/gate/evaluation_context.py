from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator


class _GateCachedText(str):
    def __new__(cls, value: str) -> "_GateCachedText":
        obj = str.__new__(cls, value)
        obj._contains_cache: dict[str, bool] = {}
        obj._lower_cache: "_GateCachedText | None" = None
        return obj

    def __contains__(self, item: object) -> bool:
        if not isinstance(item, str):
            return super().__contains__(item)
        cached = self._contains_cache.get(item)
        if cached is None:
            cached = super().__contains__(item)
            self._contains_cache[item] = cached
        return cached

    def lower(self) -> "_GateCachedText":
        if self._lower_cache is None:
            self._lower_cache = _GateCachedText(super().lower())
        return self._lower_cache


class GateEvaluationContext:
    """Per-run caches for Foundation Gate filesystem and OpenAPI reads.

    Evaluation caches live on this object and are passed through evaluator
    helpers explicitly. Gate evaluation must not patch process-wide ``Path`` or
    OpenAPI behavior.
    """

    def __init__(self, root: Path) -> None:
        self.root = root.resolve()
        self._rglob_cache: dict[tuple[Path, str], tuple[Path, ...]] = {}
        self._read_text_cache: dict[tuple[Path, tuple[Any, ...], tuple[tuple[str, Any], ...]], str] = {}
        self._is_file_cache: dict[Path, bool] = {}
        self._relative_path_cache: dict[tuple[Path, Path], str] = {}
        self._cacheable_paths: dict[Path, bool] = {}
        self._openapi_schema_cache: dict[str, Any] = {}
        self._openapi_contract_cache: dict[str, Any] = {}
        self._value_cache: dict[str, Any] = {}

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
            self._read_text_cache[key] = _GateCachedText(path.read_text(*args, **kwargs))
        return self._read_text_cache[key]

    def is_file(self, path: Path) -> bool:
        if not self.is_cacheable(path):
            return path.is_file()
        if path not in self._is_file_cache:
            self._is_file_cache[path] = path.is_file()
        return self._is_file_cache[path]

    def relative_path(self, path: Path, root: Path | None = None) -> str:
        base = root or self.root
        key = (path, base)
        if key not in self._relative_path_cache:
            self._relative_path_cache[key] = path.relative_to(base).as_posix()
        return self._relative_path_cache[key]

    def openapi_schema(self) -> Any:
        if "schema" not in self._openapi_schema_cache:
            from ultimate_ai_agent.api.app import app

            self._openapi_schema_cache["schema"] = app.openapi()
        return self._openapi_schema_cache["schema"]

    def openapi_paths(self) -> dict[str, Any]:
        return self.openapi_schema().get("paths", {})

    def verify_openapi_contract(self, candidate_app: Any | None = None) -> Any:
        from ultimate_ai_agent.api.app import app
        from ultimate_ai_agent.api.openapi import verify_openapi_contract

        target_app = candidate_app or app
        if target_app is not app:
            return verify_openapi_contract(target_app)
        if "status" not in self._openapi_contract_cache:
            self._openapi_contract_cache["status"] = verify_openapi_contract(target_app)
        return self._openapi_contract_cache["status"]

    def cached_value(self, key: str, factory: Any) -> Any:
        if key not in self._value_cache:
            self._value_cache[key] = factory()
        return self._value_cache[key]
