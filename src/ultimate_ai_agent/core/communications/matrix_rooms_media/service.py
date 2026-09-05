from __future__ import annotations

import base64
import hashlib
import secrets
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.dispatch_contracts import (
    AuthorityDispatchRequest,
    AuthorityDispatchResult,
)
from ultimate_ai_agent.core.authority.dispatcher import (
    AuthorityDispatcher,
    build_authority_dispatch_cost_estimate_ref,
    build_authority_dispatch_cost_governor_decision_ref,
)
from ultimate_ai_agent.core.communications.matrix_messaging.broker import (
    MatrixBrokerClient,
    MatrixBrokerError,
    MatrixBrokerInvocation,
    MatrixBrokerTransientInput,
)
from ultimate_ai_agent.core.communications.matrix_session.target_policy import (
    matrix_homeserver_ref,
)
from ultimate_ai_agent.core.communications.matrix_sync import matrix_sync_private_ref
from ultimate_ai_agent.core.costs.budgets import CostBudget
from ultimate_ai_agent.core.costs.enums import BudgetScope
from ultimate_ai_agent.core.costs.estimates import CostEstimate
from ultimate_ai_agent.core.execution.validation import validate_execution_ref
from ultimate_ai_agent.core.tools.runtime.contracts import ToolInvocationRequest
from ultimate_ai_agent.core.tools.runtime.enums import ToolInvocationKind

from .adapter import (
    MatrixRoomsMediaAuthorityDispatchAdapter,
    MatrixRoomsMediaOperationResult,
)
from .authority_surfaces import (
    build_matrix_rooms_media_approval_request,
    build_matrix_rooms_media_authority_action,
)
from .constants import (
    EXTERNAL_MUTATION_OPERATIONS,
    MATRIX_MEDIA_PARSER_REF,
    NETWORK_OPERATIONS,
    MatrixRoomsMediaOperation,
    matrix_rooms_media_lane,
)
from .contracts import (
    MatrixRoomsMediaCommand,
    MatrixRoomsMediaDispatchMetadata,
    MatrixRoomsMediaReadiness,
    matrix_rooms_media_start_deadline_ref,
    stable_matrix_rooms_media_ref,
)
from .media import MatrixMediaError, MatrixMediaStore
from .search import MatrixEncryptedSearchError, MatrixEncryptedSearchIndex


@dataclass(frozen=True, repr=False)
class MatrixRoomsMediaRuntimeInput:
    homeserver_url: str | None = None
    pseudonymization_salt: bytes | None = None
    room_id: str | None = None
    member_id: str | None = None
    event_id: str | None = None
    transaction_id: str | None = None
    space_id: str | None = None
    media_uri: str | None = None
    room_name: str | None = None
    desired_state: str | None = None
    prior_state: str | None = None
    declared_media_type: str | None = None
    source_path: Path | None = None
    search_query: str | None = None
    allowed_room_refs: tuple[str, ...] = ()
    cancel_requested: Callable[[], bool] | None = None
    progress_observer: Callable[[str, int | None, int | None], None] | None = None

    def __repr__(self) -> str:
        return "MatrixRoomsMediaRuntimeInput(<redacted>)"


class MatrixRoomsMediaRuntime:
    """Sealed owner for exact room, encrypted search, and media execution."""

    def __init__(self, *_args: object, **_kwargs: object) -> None:
        raise TypeError("MATRIX_ROOMS_MEDIA_RUNTIME_FACTORY_REQUIRED")

    @classmethod
    def blocked(cls) -> MatrixRoomsMediaRuntime:
        runtime = object.__new__(cls)
        runtime._mode = "blocked"
        runtime.binding_ref = stable_matrix_rooms_media_ref(
            "runtime-binding-ref:matrix-rooms-media",
            {"mode": "blocked", "side_effect": False},
        )
        return runtime

    @classmethod
    def live(
        cls,
        *,
        broker_client: MatrixBrokerClient,
        media_store: MatrixMediaStore,
        search_index: MatrixEncryptedSearchIndex,
        runtime_input: MatrixRoomsMediaRuntimeInput,
    ) -> MatrixRoomsMediaRuntime:
        if type(broker_client) is not MatrixBrokerClient:
            raise TypeError("MATRIX_ROOMS_MEDIA_BROKER_OWNER_REQUIRED")
        if type(media_store) is not MatrixMediaStore:
            raise TypeError("MATRIX_ROOMS_MEDIA_MEDIA_STORE_OWNER_REQUIRED")
        if type(search_index) is not MatrixEncryptedSearchIndex:
            raise TypeError("MATRIX_ROOMS_MEDIA_SEARCH_INDEX_OWNER_REQUIRED")
        if type(runtime_input) is not MatrixRoomsMediaRuntimeInput:
            raise TypeError("MATRIX_ROOMS_MEDIA_RUNTIME_INPUT_REQUIRED")
        if runtime_input.cancel_requested is not None and not callable(
            runtime_input.cancel_requested
        ):
            raise TypeError("MATRIX_ROOMS_MEDIA_CANCEL_CALLBACK_INVALID")
        if runtime_input.progress_observer is not None and not callable(
            runtime_input.progress_observer
        ):
            raise TypeError("MATRIX_ROOMS_MEDIA_PROGRESS_CALLBACK_INVALID")
        runtime = object.__new__(cls)
        runtime._mode = "live"
        runtime._broker_client = broker_client
        runtime._media_store = media_store
        runtime._search_index = search_index
        runtime._runtime_input = runtime_input
        runtime.binding_ref = stable_matrix_rooms_media_ref(
            "runtime-binding-ref:matrix-rooms-media",
            {
                "mode": "live",
                "broker_binding_ref": broker_client.binding_ref,
                "media_store_binding_ref": media_store.binding_ref,
                "search_index_binding_ref": search_index.binding_ref,
            },
        )
        return runtime

    def execute(
        self, command: MatrixRoomsMediaCommand, approval_ref: str
    ) -> MatrixRoomsMediaOperationResult:
        if self._mode == "blocked":
            return _result(
                command,
                succeeded=False,
                status="configuration_required",
                evidence_ref="evidence-ref:matrix-rooms-media:runtime-not-bound",
            )
        if self._mode != "live":
            raise RuntimeError("MATRIX_ROOMS_MEDIA_RUNTIME_BINDING_INVALID")
        expected_media_root = self._broker_client.scope_root(
            account_ref=command.account_ref,
            homeserver_ref=command.homeserver_ref,
            device_ref=command.device_ref,
        )
        if self._media_store.root != expected_media_root:
            raise ValueError("MATRIX_ROOMS_MEDIA_BROKER_MEDIA_SCOPE_MISMATCH")
        transient = self._runtime_input
        try:
            validated_upload_data = _validate_transient_binding(
                command, transient, media_store=self._media_store
            )
        except MatrixMediaError:
            return _result(
                command,
                succeeded=False,
                status="blocked",
                evidence_ref="evidence-ref:matrix-media:upload-source-denied",
            )
        if command.operation == MatrixRoomsMediaOperation.search_local_read:
            return self._search(command)
        if command.operation == MatrixRoomsMediaOperation.media_materialize:
            return self._materialize(command)
        if command.operation == MatrixRoomsMediaOperation.media_preview:
            return self._preview(command)
        if command.operation == MatrixRoomsMediaOperation.media_cleanup:
            return self._cleanup(command)
        if command.operation in NETWORK_OPERATIONS:
            return self._network(
                command,
                approval_ref,
                validated_upload_data=validated_upload_data,
            )
        raise RuntimeError("MATRIX_ROOMS_MEDIA_OPERATION_UNSUPPORTED")

    def _search(
        self, command: MatrixRoomsMediaCommand
    ) -> MatrixRoomsMediaOperationResult:
        assert command.search_index_ref is not None
        query = self._runtime_input.search_query
        if query is None:
            raise MatrixEncryptedSearchError("MATRIX_SEARCH_QUERY_REQUIRED")
        try:
            results = self._search_index.search(
                index_ref=command.search_index_ref,
                account_ref=command.account_ref,
                query=query,
                allowed_room_refs=frozenset(self._runtime_input.allowed_room_refs),
                exact_room_ref=command.room_ref,
                max_results=command.max_result_count,
            )
        except MatrixEncryptedSearchError:
            return _result(
                command,
                succeeded=False,
                status="blocked",
                evidence_ref="evidence-ref:matrix-search:scope-or-index-denied",
            )
        return _result(
            command,
            succeeded=True,
            status="completed",
            evidence_ref=stable_matrix_rooms_media_ref(
                "receipt-ref:matrix-search:read",
                {
                    "query_ref": command.query_ref,
                    "result_refs": results,
                    "result_count": len(results),
                },
            ),
            extra={"result_refs": list(results), "result_count": len(results)},
        )

    def _materialize(
        self, command: MatrixRoomsMediaCommand
    ) -> MatrixRoomsMediaOperationResult:
        assert command.quarantine_ref and command.materialization_ref
        media_type = self._runtime_input.declared_media_type
        if media_type is None:
            raise MatrixMediaError("MATRIX_MEDIA_TYPE_REQUIRED")
        try:
            _path, inspection = self._media_store.materialize(
                quarantine_ref=command.quarantine_ref,
                declared_media_type=media_type,
                max_bytes=command.max_bytes,
                materialization_ref=command.materialization_ref,
            )
        except MatrixMediaError:
            return _result(
                command,
                succeeded=False,
                status="blocked",
                evidence_ref="evidence-ref:matrix-media:materialization-denied",
            )
        return _result(
            command,
            succeeded=True,
            status="materialized",
            evidence_ref=stable_matrix_rooms_media_ref(
                "receipt-ref:matrix-media:materialize",
                {
                    "materialization_ref": command.materialization_ref,
                    "byte_count": inspection.byte_count,
                    "content_fingerprint_ref": inspection.content_fingerprint_ref,
                },
            ),
            extra={
                "byte_count": inspection.byte_count,
                "materialization_ref": command.materialization_ref,
            },
        )

    def _preview(
        self, command: MatrixRoomsMediaCommand
    ) -> MatrixRoomsMediaOperationResult:
        assert command.quarantine_ref
        media_type = self._runtime_input.declared_media_type
        if media_type is None or command.parser_ref != MATRIX_MEDIA_PARSER_REF:
            return _result(
                command,
                succeeded=False,
                status="blocked",
                evidence_ref="evidence-ref:matrix-media:preview-parser-denied",
            )
        try:
            inspection = self._media_store.inspect_quarantine(
                quarantine_ref=command.quarantine_ref,
                declared_media_type=media_type,
                max_bytes=command.max_bytes,
            )
        except MatrixMediaError:
            return _result(
                command,
                succeeded=False,
                status="blocked",
                evidence_ref="evidence-ref:matrix-media:preview-denied",
            )
        return _result(
            command,
            succeeded=True,
            status="preview_metadata_ready",
            evidence_ref=stable_matrix_rooms_media_ref(
                "receipt-ref:matrix-media:preview",
                {
                    "parser_ref": command.parser_ref,
                    "byte_count": inspection.byte_count,
                    "media_type_ref": command.declared_media_type_ref,
                },
            ),
            extra={
                "byte_count": inspection.byte_count,
                "preview_content_included": False,
            },
        )

    def _cleanup(
        self, command: MatrixRoomsMediaCommand
    ) -> MatrixRoomsMediaOperationResult:
        assert command.quarantine_ref
        try:
            receipt = self._media_store.cleanup(
                quarantine_ref=command.quarantine_ref,
                materialization_ref=command.materialization_ref,
                declared_media_type=self._runtime_input.declared_media_type,
            )
        except MatrixMediaError:
            return _result(
                command,
                succeeded=False,
                status="incomplete_cleanup",
                evidence_ref="evidence-ref:matrix-media:cleanup-incomplete",
            )
        return _result(
            command,
            succeeded=True,
            status="cleaned",
            evidence_ref=receipt,
            extra={"path_absent": True, "physical_block_erasure_proven": False},
        )

    def _network(
        self,
        command: MatrixRoomsMediaCommand,
        approval_ref: str,
        *,
        validated_upload_data: bytes | None,
    ) -> MatrixRoomsMediaOperationResult:
        transient = self._runtime_input
        data = validated_upload_data
        transfer_operation = command.operation in {
            MatrixRoomsMediaOperation.media_upload,
            MatrixRoomsMediaOperation.media_download_quarantine,
        }
        if transfer_operation:
            _emit_transfer_progress(transient, "validating", None, command.max_bytes)
            if _transfer_cancel_requested(transient):
                return _cancelled_before_start_result(command)
        if command.operation == MatrixRoomsMediaOperation.media_upload:
            assert (
                transient.source_path is not None
                and transient.declared_media_type is not None
                and data is not None
            )
            _emit_transfer_progress(
                transient,
                "source_validated",
                len(data),
                len(data),
            )
            if _transfer_cancel_requested(transient):
                return _cancelled_before_start_result(command)
        invocation = MatrixBrokerInvocation(
            operation=command.operation.value,
            request_ref=command.request_ref,
            request_fingerprint_ref=command.request_fingerprint_ref,
            nonce=secrets.token_hex(24),
            issued_at=datetime.now(timezone.utc),
            deadline=command.start_deadline,
            account_ref=command.account_ref,
            homeserver_ref=command.homeserver_ref,
            device_ref=command.device_ref,
            approval_ref=approval_ref,
            lease_ref=command.lease_ref,
            idempotency_ref=command.idempotency_ref,
            budget_ref=command.budget_ref,
            readiness_ref=command.readiness_ref,
            room_ref=command.room_ref,
            event_ref=command.event_ref,
            transaction_ref=command.transaction_ref,
            member_ref=command.member_ref,
            space_ref=command.space_ref,
            media_ref=command.media_ref,
            quarantine_ref=command.quarantine_ref,
        )
        broker_transient = MatrixBrokerTransientInput(
            homeserver_url=transient.homeserver_url,
            room_id=transient.room_id,
            event_id=transient.event_id,
            transaction_id=transient.transaction_id,
            member_id=transient.member_id,
            space_id=transient.space_id,
            room_name=transient.room_name,
            desired_state=transient.desired_state,
            prior_state=transient.prior_state,
            media_uri=transient.media_uri,
            media_type=transient.declared_media_type,
            media_b64=None if data is None else base64.b64encode(data).decode("ascii"),
        )
        try:
            response = self._broker_client.execute(
                invocation,
                transient=broker_transient,
                cancel_requested=(
                    transient.cancel_requested if transfer_operation else None
                ),
                progress_observer=(
                    (
                        lambda phase: _emit_transfer_progress(
                            transient,
                            f"broker_{phase}",
                            None,
                            command.max_bytes,
                        )
                    )
                    if transfer_operation
                    else None
                ),
            )
        except MatrixBrokerError as exc:
            error_code = str(exc)
            if error_code == "MATRIX_BROKER_CANCELLED_BEFORE_START":
                return _cancelled_before_start_result(command)
            cancelled = error_code == "MATRIX_BROKER_CANCELLED_OUTCOME_UNCERTAIN"
            uncertain = error_code in {
                "MATRIX_BROKER_OUTCOME_UNCERTAIN",
                "MATRIX_BROKER_CANCELLED_OUTCOME_UNCERTAIN",
            }
            return _result(
                command,
                succeeded=False,
                status="outcome_uncertain" if uncertain else "blocked",
                evidence_ref="evidence-ref:matrix-rooms-media:broker-outcome-uncertain"
                if uncertain
                else "evidence-ref:matrix-rooms-media:broker-blocked",
                extra={
                    "automatic_retry_permitted": False,
                    "manual_retry_requires_same_idempotency_ref": True,
                    "outcome_uncertain": uncertain,
                    "cancel_requested": cancelled,
                    "broker_process_terminated": cancelled,
                },
            )
        if not response.ok:
            return _result(
                command,
                succeeded=False,
                status=response.outcome,
                evidence_ref=response.receipt_ref,
                extra={
                    "automatic_retry_permitted": False,
                    "manual_retry_requires_same_idempotency_ref": True,
                    "outcome_uncertain": response.outcome == "outcome_uncertain",
                },
            )
        extra: dict[str, object] = {
            "server_acknowledged": True,
            "replayed": response.replayed,
            "automatic_retry_permitted": False,
            "manual_retry_requires_same_idempotency_ref": True,
        }
        if response.event_ref is not None:
            extra["result_ref"] = response.event_ref
        if command.operation == MatrixRoomsMediaOperation.media_download_quarantine:
            assert (
                command.quarantine_ref is not None
                and transient.declared_media_type is not None
            )
            try:
                inspection = self._media_store.inspect_quarantine(
                    quarantine_ref=command.quarantine_ref,
                    declared_media_type=transient.declared_media_type,
                    max_bytes=command.max_bytes,
                )
            except MatrixMediaError:
                try:
                    self._media_store.cleanup(
                        quarantine_ref=command.quarantine_ref,
                        materialization_ref=None,
                        declared_media_type=transient.declared_media_type,
                    )
                except MatrixMediaError:
                    return _result(
                        command,
                        succeeded=False,
                        status="incomplete_cleanup",
                        evidence_ref="evidence-ref:matrix-media:quarantine-cleanup-incomplete",
                    )
                return _result(
                    command,
                    succeeded=False,
                    status="quarantine_rejected",
                    evidence_ref="evidence-ref:matrix-media:download-quarantine-rejected",
                )
            extra.update(
                {
                    "quarantine_ref": command.quarantine_ref,
                    "byte_count": inspection.byte_count,
                    "scan_content_included": False,
                }
            )
            _emit_transfer_progress(
                transient,
                "quarantine_validated",
                inspection.byte_count,
                inspection.byte_count,
            )
        elif command.operation == MatrixRoomsMediaOperation.media_upload:
            assert data is not None
            extra["byte_count"] = len(data)
            _emit_transfer_progress(
                transient,
                "upload_acknowledged",
                len(data),
                len(data),
            )
        return _result(
            command,
            succeeded=True,
            status=response.outcome,
            evidence_ref=response.receipt_ref,
            extra=extra,
        )


def _private_ref(prefix: str, salt: bytes, value: str | None) -> str | None:
    return None if value is None else matrix_sync_private_ref(prefix, salt, value)


def _transfer_cancel_requested(transient: MatrixRoomsMediaRuntimeInput) -> bool:
    callback = transient.cancel_requested
    if callback is None:
        return False
    try:
        return callback() is True
    except Exception:
        return True


def _emit_transfer_progress(
    transient: MatrixRoomsMediaRuntimeInput,
    phase: str,
    completed_bytes: int | None,
    total_bytes: int | None,
) -> None:
    observer = transient.progress_observer
    if observer is None:
        return
    try:
        observer(phase, completed_bytes, total_bytes)
    except Exception:
        # Progress is a content-free observation surface and never execution authority.
        return


def _cancelled_before_start_result(
    command: MatrixRoomsMediaCommand,
) -> MatrixRoomsMediaOperationResult:
    return _result(
        command,
        succeeded=False,
        status="cancelled_before_start",
        evidence_ref="evidence-ref:matrix-media:cancelled-before-start",
        extra={
            "automatic_retry_permitted": False,
            "manual_retry_requires_same_idempotency_ref": True,
            "outcome_uncertain": False,
            "cancel_requested": True,
            "broker_process_terminated": False,
        },
    )


def _validate_transient_binding(
    command: MatrixRoomsMediaCommand,
    transient: MatrixRoomsMediaRuntimeInput,
    *,
    media_store: MatrixMediaStore,
) -> bytes | None:
    salt = transient.pseudonymization_salt
    if salt is None:
        raise ValueError("MATRIX_ROOMS_MEDIA_PSEUDONYMIZATION_SALT_REQUIRED")
    homeserver_ref = (
        matrix_homeserver_ref(transient.homeserver_url)
        if transient.homeserver_url is not None
        else None
    )
    if command.operation == MatrixRoomsMediaOperation.room_create:
        if transient.desired_state is not None:
            raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
        desired_state = transient.room_name
    else:
        if transient.room_name is not None:
            raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
        desired_state = transient.desired_state
    if command.operation == MatrixRoomsMediaOperation.media_download_quarantine:
        bound_media_ref = _private_ref("media-ref:matrix", salt, transient.media_uri)
    else:
        if transient.media_uri is not None:
            raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
        bound_media_ref = command.media_ref
    bindings = (
        (command.room_ref, _private_ref("room-ref:matrix", salt, transient.room_id)),
        (
            command.member_ref,
            _private_ref("member-ref:matrix", salt, transient.member_id),
        ),
        (command.event_ref, _private_ref("event-ref:matrix", salt, transient.event_id)),
        (
            command.transaction_ref,
            _private_ref("transaction-ref:matrix", salt, transient.transaction_id),
        ),
        (command.space_ref, _private_ref("space-ref:matrix", salt, transient.space_id)),
        (command.media_ref, bound_media_ref),
        (
            command.desired_state_ref,
            _private_ref("state-ref:matrix", salt, desired_state),
        ),
        (
            command.prior_state_ref,
            _private_ref("state-ref:matrix", salt, transient.prior_state),
        ),
        (
            command.declared_media_type_ref,
            _private_ref("media-type-ref:matrix", salt, transient.declared_media_type),
        ),
    )
    if (
        command.operation in NETWORK_OPERATIONS
        and homeserver_ref != command.homeserver_ref
    ):
        raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
    if command.operation not in NETWORK_OPERATIONS and homeserver_ref is not None:
        raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
    transfer_operation = command.operation in {
        MatrixRoomsMediaOperation.media_upload,
        MatrixRoomsMediaOperation.media_download_quarantine,
    }
    if not transfer_operation and (
        transient.cancel_requested is not None
        or transient.progress_observer is not None
    ):
        raise ValueError("MATRIX_ROOMS_MEDIA_TRANSFER_CALLBACK_SCOPE_MISMATCH")
    if any(expected != actual for expected, actual in bindings):
        raise ValueError("MATRIX_ROOMS_MEDIA_TRANSIENT_BINDING_MISMATCH")
    if command.filesystem_root_ref is not None:
        actual_root_ref = _private_ref(
            "filesystem-root-ref:matrix-media", salt, str(media_store.root)
        )
        if actual_root_ref != command.filesystem_root_ref:
            raise ValueError("MATRIX_ROOMS_MEDIA_FILESYSTEM_ROOT_MISMATCH")
    validated_upload_data: bytes | None = None
    if command.source_file_ref is not None:
        if transient.source_path is None or transient.declared_media_type is None:
            raise ValueError("MATRIX_ROOMS_MEDIA_SOURCE_BINDING_REQUIRED")
        validated_upload_data, _inspection = media_store.read_upload_source(
            path=transient.source_path,
            declared_media_type=transient.declared_media_type,
            max_bytes=command.max_bytes,
        )
        source_value = (
            f"{transient.source_path}\0"
            f"{hashlib.sha256(validated_upload_data).hexdigest()}"
        )
        if (
            _private_ref("source-file-ref:matrix-media", salt, source_value)
            != command.source_file_ref
        ):
            raise ValueError("MATRIX_ROOMS_MEDIA_SOURCE_BINDING_MISMATCH")
    elif transient.source_path is not None:
        raise ValueError("MATRIX_ROOMS_MEDIA_SOURCE_BINDING_MISMATCH")
    if command.query_ref is not None:
        if (
            transient.search_query is None
            or _private_ref("query-ref:matrix-search", salt, transient.search_query)
            != command.query_ref
        ):
            raise ValueError("MATRIX_ROOMS_MEDIA_QUERY_BINDING_MISMATCH")
    elif transient.search_query is not None:
        raise ValueError("MATRIX_ROOMS_MEDIA_QUERY_BINDING_MISMATCH")
    if command.room_allowlist_ref is not None:
        for room_ref in transient.allowed_room_refs:
            try:
                validate_execution_ref(room_ref, "matrix_search_room_allowlist_ref")
            except ValueError as exc:
                raise ValueError("MATRIX_ROOMS_MEDIA_ROOM_ALLOWLIST_INVALID") from exc
            if not room_ref.startswith("room-ref:matrix:"):
                raise ValueError("MATRIX_ROOMS_MEDIA_ROOM_ALLOWLIST_INVALID")
        expected_allowlist = stable_matrix_rooms_media_ref(
            "room-allowlist-ref:matrix-search",
            {"room_refs": sorted(set(transient.allowed_room_refs))},
        )
        if command.room_allowlist_ref != expected_allowlist:
            raise ValueError("MATRIX_ROOMS_MEDIA_ROOM_ALLOWLIST_MISMATCH")
        if (
            command.room_ref is not None
            and command.room_ref not in transient.allowed_room_refs
        ):
            raise ValueError("MATRIX_ROOMS_MEDIA_SEARCH_ROOM_SCOPE_MISMATCH")
    elif transient.allowed_room_refs:
        raise ValueError("MATRIX_ROOMS_MEDIA_ROOM_ALLOWLIST_MISMATCH")
    return validated_upload_data


def _result(
    command: MatrixRoomsMediaCommand,
    *,
    succeeded: bool,
    status: str,
    evidence_ref: str,
    extra: dict[str, object] | None = None,
) -> MatrixRoomsMediaOperationResult:
    safe_output: dict[str, object] = {
        "runtime_status": status,
        "operation": command.operation.value,
        "request_fingerprint_ref": command.request_fingerprint_ref,
        "external_write_performed": succeeded
        and command.operation in EXTERNAL_MUTATION_OPERATIONS,
        "raw_content_included": False,
        "raw_identifiers_included": False,
    }
    safe_output.update(extra or {})
    return MatrixRoomsMediaOperationResult(
        succeeded=succeeded,
        safe_output=safe_output,
        evidence_refs=(evidence_ref,),
        safe_summary="The exact Matrix room, local-search, or media operation returned content-free evidence.",
    )


def build_matrix_rooms_media_dispatch_request(
    command: MatrixRoomsMediaCommand,
    *,
    adapter: MatrixRoomsMediaAuthorityDispatchAdapter,
) -> AuthorityDispatchRequest:
    lane = matrix_rooms_media_lane(command.operation)
    action = build_matrix_rooms_media_authority_action(command)
    metadata = MatrixRoomsMediaDispatchMetadata(
        command=command,
        start_deadline_ref=matrix_rooms_media_start_deadline_ref(
            command.start_deadline
        ),
    )
    tool_request = ToolInvocationRequest(
        invocation_id=command.dispatch_ref,
        tool_ref=lane.tool_ref,
        tool_name=lane.tool_name,
        invocation_kind=ToolInvocationKind.matrix_rooms_media,
        replay_key=command.idempotency_ref,
        safe_summary=f"Execute one exact Matrix {command.operation.value} lane.",
        input_refs=[command.request_ref],
        metadata_refs=[
            command.homeserver_ref,
            command.account_ref,
            command.device_ref,
            command.readiness_ref,
            command.request_fingerprint_ref,
        ],
        metadata=metadata.model_dump(mode="json"),
    )
    estimate = CostEstimate(
        estimate_id=stable_matrix_rooms_media_ref(
            "cost-estimate-ref:matrix-rooms-media",
            {"request_fingerprint_ref": command.request_fingerprint_ref},
        ),
        input_tokens=0,
        output_tokens=0,
        total_tokens=0,
        estimated_cost_usd=0,
        estimated_token_cost_usd=0,
        estimated_runtime_seconds=max(1, command.max_duration_ms // 1000),
        estimated_memory_gb=0.5,
        created_at=command.request_created_at,
    )
    budgets = [
        CostBudget(
            budget_id=stable_matrix_rooms_media_ref(
                "cost-budget-ref:matrix-rooms-media", {"run_ref": command.run_ref}
            ),
            scope=BudgetScope.run,
            scope_id=command.run_ref,
            max_cost_usd=0,
            max_runtime_seconds=max(1, command.max_duration_ms // 1000),
            max_local_memory_gb=0.5,
            created_at=command.request_created_at,
        )
    ]
    pending = AuthorityDispatchRequest(
        dispatch_ref=command.dispatch_ref,
        run_ref=command.run_ref,
        idempotency_ref=command.idempotency_ref,
        lease_ref=command.lease_ref,
        adapter_ref=lane.adapter_ref,
        action_request=action,
        tool_invocation_request=tool_request.model_dump(mode="json"),
        operation_count=1,
        estimated_cost_microusd=0,
        cost_estimate=estimate,
        cost_budgets=budgets,
        cost_estimate_ref=build_authority_dispatch_cost_estimate_ref(estimate),
        cost_governor_decision_ref=build_authority_dispatch_cost_governor_decision_ref(
            estimate, budgets
        ),
        cost_governor_allowed=True,
        start_deadline=command.start_deadline,
        safe_summary="Run one exact approved Matrix room, search, or media operation.",
    )
    policy_ref = adapter.policy_decision_ref(pending)
    return pending.model_copy(
        update={
            "action_request": action.model_copy(
                update={
                    "constraints": {
                        **action.constraints,
                        "policy_decision_ref": policy_ref,
                    }
                }
            )
        }
    )


def attach_exact_matrix_rooms_media_approval(
    request: AuthorityDispatchRequest,
    command: MatrixRoomsMediaCommand,
    *,
    approval_authority: LocalApprovalAuthority,
    approval_ref: str,
) -> AuthorityDispatchRequest:
    approval_request = approval_authority.create_request(
        build_matrix_rooms_media_approval_request(command)
    )
    return request.model_copy(
        update={
            "approval_validation_request": approval_request.to_validation_request(
                approval_ref
            )
        }
    )


def execute_matrix_rooms_media_command(
    command: MatrixRoomsMediaCommand,
    *,
    authority_state_dir: Path,
    runtime: MatrixRoomsMediaRuntime,
    readiness_provider: Callable[[MatrixRoomsMediaCommand], MatrixRoomsMediaReadiness],
    approval_ref: str | None = None,
    lease_store: AuthorityLeaseStore | None = None,
    approval_authority: LocalApprovalAuthority | None = None,
) -> AuthorityDispatchResult:
    if type(runtime) is not MatrixRoomsMediaRuntime:
        raise TypeError("MATRIX_ROOMS_MEDIA_RUNTIME_OWNER_REQUIRED")
    store = lease_store or AuthorityLeaseStore(authority_state_dir)
    approvals = approval_authority or LocalApprovalAuthority()
    adapter = MatrixRoomsMediaAuthorityDispatchAdapter(
        operation=command.operation,
        executor=runtime.execute,
        executor_binding_ref=runtime.binding_ref,
        authority_leases_provider=lambda: store.list_leases(active_only=False),
        readiness_provider=readiness_provider,
    )
    request = build_matrix_rooms_media_dispatch_request(command, adapter=adapter)
    if approval_ref is not None:
        request = attach_exact_matrix_rooms_media_approval(
            request, command, approval_authority=approvals, approval_ref=approval_ref
        )
    dispatcher = AuthorityDispatcher(
        authority_state_dir,
        adapters=[adapter],
        lease_store=store,
        approval_authority=approvals,
    )
    return dispatcher.dispatch(request)


__all__ = [
    "MatrixRoomsMediaRuntime",
    "MatrixRoomsMediaRuntimeInput",
    "attach_exact_matrix_rooms_media_approval",
    "build_matrix_rooms_media_dispatch_request",
    "execute_matrix_rooms_media_command",
]
