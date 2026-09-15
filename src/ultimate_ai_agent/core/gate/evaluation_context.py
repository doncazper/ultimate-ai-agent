from __future__ import annotations

from pathlib import Path
from typing import Any, Iterator


class _GateCachedText(str):
    __slots__ = ("_contains_cache", "_lower_cache", "_true_assignment_ends")

    def __new__(cls, value: str) -> "_GateCachedText":
        obj = str.__new__(cls, value)
        obj._contains_cache: dict[str, bool] = {}
        obj._lower_cache: "_GateCachedText | None" = None
        obj._true_assignment_ends: tuple[int, ...] | None = None
        return obj

    def __contains__(self, item: object) -> bool:
        # Subclasses may override equality/hash or string helpers. Keep their
        # native membership behavior without admitting them into either cache.
        if type(item) is not str:
            return str.__contains__(self, item)
        cache = self._contains_cache
        cached = cache.get(item)
        if cached is None:
            if str.__len__(item) > 5 and str.endswith(item, "=True"):
                cached = self._contains_true_assignment(item)
            else:
                cached = str.__contains__(self, item)
            cache[item] = cached
        return cached

    def _contains_true_assignment(self, item: str) -> bool:
        # Hundreds of distinct literal flags share this suffix. Enumerate its
        # endpoints once, then confirm the entire needle with native semantics.
        # The 257th endpoint is an overflow sentinel: fall back, never truncate
        # the search and mistake an unindexed occurrence for absence.
        ends = self._true_assignment_ends
        if ends is None:
            positions: list[int] = []
            start = 0
            while len(positions) <= 256:
                position = str.find(self, "=True", start)
                if position < 0:
                    break
                positions.append(position + 5)
                start = position + 1
            ends = tuple(positions)
            self._true_assignment_ends = ends
        if len(ends) > 256:
            return str.__contains__(self, item)
        return any(str.endswith(self, item, 0, end) for end in ends)

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
