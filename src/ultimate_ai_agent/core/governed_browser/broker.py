"""Injected isolated browser broker behind :class:`WebAccessGateway`.

No browser engine or network dependency is imported. A future adapter may
consume the ephemeral private profile directory, but Queue 01 uses only
deterministic injected transports and keeps external mutation disabled.
"""

from __future__ import annotations

import tempfile
from collections.abc import Mapping
from pathlib import Path
from threading import BoundedSemaphore, Lock
from typing import Any, Protocol
from uuid import uuid4

from ultimate_ai_agent.core.web_access import (
    WebAccessAdapterKind,
    WebAccessGateway,
    WebAccessPolicy,
    WebAccessPolicyDecision,
    WebAccessRequest,
    WebAccessRequestKind,
)

from .contracts import stable_governed_browser_ref


class IsolatedBrowserTransport(Protocol):
    def observe(
        self,
        *,
        request: WebAccessRequest,
        profile_directory: Path,
        profile_ref: str,
    ) -> Mapping[str, Any]: ...


class IsolatedBrowserBrokerAdapter:
    """Bounded, ephemeral-profile adapter for injected observation only."""

    adapter_kind = WebAccessAdapterKind.LOCAL_BROWSER_OBSERVE

    def __init__(
        self,
        *,
        transport: IsolatedBrowserTransport,
        allowed_origin_refs: set[str],
        max_concurrency: int = 1,
        external_mutation_enabled: bool = False,
    ) -> None:
        if not allowed_origin_refs:
            raise ValueError("GOVERNED_BROWSER_ALLOWED_ORIGIN_REQUIRED")
        if max_concurrency < 1 or max_concurrency > 4:
            raise ValueError("GOVERNED_BROWSER_CONCURRENCY_OUT_OF_BOUNDS")
        if external_mutation_enabled:
            raise ValueError("GOVERNED_BROWSER_EXTERNAL_MUTATION_MUST_REMAIN_INACTIVE")
        self._transport = transport
        self._allowed_origin_refs = frozenset(allowed_origin_refs)
        self._semaphore = BoundedSemaphore(max_concurrency)
        self._history_lock = Lock()
        self._closed_profiles: list[str] = []
        self.external_mutation_enabled = False
        self.max_concurrency = max_concurrency

    @property
    def closed_profile_refs(self) -> tuple[str, ...]:
        with self._history_lock:
            return tuple(self._closed_profiles)

    def execute(
        self,
        request: WebAccessRequest,
        decision: WebAccessPolicyDecision,
    ) -> Mapping[str, Any]:
        del decision
        if request.kind != WebAccessRequestKind.BROWSER_OBSERVE:
            return self._blocked("GOVERNED_BROWSER_OBSERVE_ONLY")
        origin_ref = request.metadata.get("exact_origin_ref")
        if origin_ref not in self._allowed_origin_refs:
            return self._blocked("GOVERNED_BROWSER_EXACT_ORIGIN_DENIED")
        if request.metadata.get("ordinary_profile_requested") is True:
            return self._blocked("GOVERNED_BROWSER_ORDINARY_PROFILE_DENIED")
        if request.metadata.get("mutation_requested") is True:
            return self._blocked("GOVERNED_BROWSER_EXTERNAL_MUTATION_INACTIVE")
        acquired = self._semaphore.acquire(blocking=False)
        if not acquired:
            return self._blocked("GOVERNED_BROWSER_CONCURRENCY_LIMIT_REACHED")
        profile_ref = stable_governed_browser_ref(
            "browser-profile-ref:ephemeral", {"nonce": uuid4().hex}
        )
        try:
            with tempfile.TemporaryDirectory(
                prefix="uaa-governed-browser-"
            ) as directory:
                result = dict(
                    self._transport.observe(
                        request=request,
                        profile_directory=Path(directory),
                        profile_ref=profile_ref,
                    )
                )
            result.update(
                {
                    "allowed": True,
                    "profile_ref": profile_ref,
                    "profile_ephemeral": True,
                    "ordinary_profile_used": False,
                    "external_mutation_enabled": False,
                    "content_untrusted": True,
                    "web_content_instruction_use_allowed": False,
                }
            )
            return result
        finally:
            with self._history_lock:
                self._closed_profiles.append(profile_ref)
            self._semaphore.release()

    @staticmethod
    def _blocked(reason: str) -> Mapping[str, Any]:
        return {
            "allowed": False,
            "status": "blocked",
            "reason_codes": [reason],
            "profile_ephemeral": True,
            "ordinary_profile_used": False,
            "external_mutation_enabled": False,
            "content_untrusted": True,
            "web_content_instruction_use_allowed": False,
        }


def create_isolated_browser_broker_gateway(
    broker: IsolatedBrowserBrokerAdapter,
) -> WebAccessGateway:
    """Place the broker behind the existing deny-by-default gateway policy."""

    return WebAccessGateway(
        policy=WebAccessPolicy(
            allow_governed_web_evidence=False,
            allow_browser_observe=True,
            allow_browser_action_dry_run=False,
        ),
        adapters={WebAccessRequestKind.BROWSER_OBSERVE: broker},
    )
