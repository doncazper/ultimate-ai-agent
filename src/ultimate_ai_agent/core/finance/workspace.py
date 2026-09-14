"""Bounded founder-private synthetic Finance workspace over the existing kernel."""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
import os
from pathlib import Path
import re
import stat
from typing import Annotated, Literal

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictInt,
    TypeAdapter,
    model_validator,
)

from ultimate_ai_agent.core.finance.authority import FinanceMutationRequest
from ultimate_ai_agent.core.finance.crypto import (
    FinanceCryptoBackend,
    FinanceCryptoReadiness,
    MacOSFinanceCryptoBackend,
)
from ultimate_ai_agent.core.finance.import_commit import (
    FIN002_IMPORT_SAFE_DISABLE_REF,
    FinanceImportCommitProof,
)
from ultimate_ai_agent.core.finance.import_preview import preview_synthetic_csv_fixture
from ultimate_ai_agent.core.finance.models import (
    FinanceReviewDecision,
    FinanceReviewDecisionRecord,
    stable_finance_ref,
)
from ultimate_ai_agent.core.finance.operator_workflow import (
    FinancePreparedMutation,
    confirm_finance_mutation,
    prepare_finance_mutation,
)
from ultimate_ai_agent.core.finance.repository import (
    FinanceMutationReceipt,
    FinanceRepository,
)
from ultimate_ai_agent.core.finance.review_decision_commit import (
    FIN003_REVIEW_SAFE_DISABLE_REF,
    preview_finance_review_persistence,
)
from ultimate_ai_agent.core.finance.review_projection import (
    FinanceReviewItem,
    build_finance_review_projection,
)
from ultimate_ai_agent.core.finance.service import (
    FinanceKernelService,
    finance_repository_ref,
    finance_target_ref,
)
from ultimate_ai_agent.core.planning.validation import validate_task_ref
from ultimate_ai_agent.core.idempotency_contract import (
    IDEMPOTENCY_VALUE_PATTERN,
    MAX_IDEMPOTENCY_VALUE_LENGTH,
    MIN_IDEMPOTENCY_VALUE_LENGTH,
)


FINANCE_WORKSPACE_CONTRACT_REF = "contract-ref:finance/FIN-003:synthetic-in-app:v1"
FINANCE_SAMPLE_BOOK_REF = "fixture-ref:finance/FIN-001:balanced-local-book:v1"
FINANCE_SAMPLE_IMPORT_REF = "fixture-ref:finance/FIN-002:synthetic-csv-clean:v1"
FINANCE_WORKSPACE_REPOSITORY_ENV = "UAA_FINANCE_SYNTHETIC_REPOSITORY_DIR"
FINANCE_WORKSPACE_HELPER_ENV = "UAA_FINANCE_NATIVE_HELPER_PATH"
FINANCE_WORKSPACE_HELPER_DIGEST_ENV = "UAA_FINANCE_NATIVE_HELPER_SHA256"
FINANCE_WORKSPACE_DISABLE_ENV = "UAA_FINANCE_SAFE_DISABLE"
FINANCE_WORKSPACE_MAX_BODY_BYTES = 128 * 1024
FINANCE_WORKSPACE_MAX_DEPTH = 32
FinanceWorkspaceOperation = Literal[
    "create", "import_commit", "review_decision", "review_undo"
]
FinanceWorkspaceRef = Annotated[str, Field(strict=True, min_length=3, max_length=200)]
_IDEMPOTENCY_FIELD_CONSTRAINTS = {
    "min_length": MIN_IDEMPOTENCY_VALUE_LENGTH,
    "max_length": MAX_IDEMPOTENCY_VALUE_LENGTH,
    "pattern": IDEMPOTENCY_VALUE_PATTERN,
}
FinanceWorkspaceIdempotencyRef = Annotated[
    str, Field(strict=True, **_IDEMPOTENCY_FIELD_CONSTRAINTS)
]
_IDEMPOTENCY_ADAPTER = TypeAdapter(FinanceWorkspaceIdempotencyRef)


class _WorkspaceModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class FinanceWorkspaceIntent(_WorkspaceModel):
    """No paths, arbitrary input, identity grants or caller-produced evidence."""

    operation: FinanceWorkspaceOperation
    expected_revision: StrictInt = Field(ge=0, le=9_007_199_254_740_991)
    request_ref: FinanceWorkspaceRef
    idempotency_ref: FinanceWorkspaceIdempotencyRef
    review_item_ref: FinanceWorkspaceRef | None = None
    decision: FinanceReviewDecision | None = None
    compensates_event_ref: FinanceWorkspaceRef | None = None

    @model_validator(mode="after")
    def validate_intent(self) -> "FinanceWorkspaceIntent":
        for name in (
            "request_ref",
            "idempotency_ref",
            "review_item_ref",
            "compensates_event_ref",
        ):
            value = getattr(self, name)
            if value is not None:
                validate_task_ref(value, name)
        if self.operation in {"create", "import_commit"}:
            if any(
                value is not None
                for value in (
                    self.review_item_ref,
                    self.decision,
                    self.compensates_event_ref,
                )
            ):
                raise ValueError("FINANCE_WORKSPACE_INTENT_SCOPE_INVALID")
            if (self.operation == "create") != (self.expected_revision == 0):
                raise ValueError("FINANCE_WORKSPACE_INTENT_REVISION_INVALID")
        elif self.review_item_ref is None or self.expected_revision < 1:
            raise ValueError("FINANCE_WORKSPACE_REVIEW_ITEM_REQUIRED")
        elif self.operation == "review_decision":
            if self.decision is None or self.compensates_event_ref is not None:
                raise ValueError("FINANCE_WORKSPACE_DECISION_SCOPE_INVALID")
        elif self.decision is not None or self.compensates_event_ref is None:
            raise ValueError("FINANCE_WORKSPACE_UNDO_SCOPE_INVALID")
        return self


class FinanceWorkspacePreparation(_WorkspaceModel):
    schema_version: Literal["uaa-finance-workspace-preparation.v1"] = (
        "uaa-finance-workspace-preparation.v1"
    )
    configuration_ref: FinanceWorkspaceRef
    bundle: FinancePreparedMutation = Field(
        json_schema_extra={
            "properties": {
                "request": {
                    "properties": {
                        "idempotency_ref": _IDEMPOTENCY_ADAPTER.json_schema()
                    }
                }
            }
        }
    )
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False

    @model_validator(mode="after")
    def validate_transport_binding(self) -> "FinanceWorkspacePreparation":
        _IDEMPOTENCY_ADAPTER.validate_python(self.bundle.request.idempotency_ref)
        return self


class FinanceWorkspaceCommitResult(_WorkspaceModel):
    schema_version: Literal["uaa-finance-workspace-commit.v1"] = (
        "uaa-finance-workspace-commit.v1"
    )
    receipt: FinanceMutationReceipt
    import_commit: FinanceImportCommitProof | None = None
    lease_receipt_ref: FinanceWorkspaceRef
    synthetic_only: Literal[True] = True
    real_financial_data_included: Literal[False] = False


class FinanceWorkspacePendingReview(_WorkspaceModel):
    """Read-only presentation of one authenticated staged review, not a grant."""

    intent: FinanceWorkspaceIntent
    preparation: FinanceWorkspacePreparation


class FinanceWorkspaceView(_WorkspaceModel):
    schema_version: Literal["uaa-finance-workspace-view.v1"] = (
        "uaa-finance-workspace-view.v1"
    )
    contract_ref: Literal["contract-ref:finance/FIN-003:synthetic-in-app:v1"] = (
        FINANCE_WORKSPACE_CONTRACT_REF
    )
    status: Literal[
        "configuration_missing",
        "configuration_invalid",
        "helper_unavailable",
        "book_setup_required",
        "ready",
        "outcome_uncertain",
        "unavailable",
    ]
    error_code: str | None = None
    configuration_ref: FinanceWorkspaceRef | None = None
    repository_ref: FinanceWorkspaceRef | None = None
    crypto: FinanceCryptoReadiness | None = None
    revision: StrictInt | None = None
    snapshot_ref: FinanceWorkspaceRef | None = None
    projection_ref: FinanceWorkspaceRef | None = None
    safe_disable_engaged: bool = False
    import_available: bool = False
    item_count: StrictInt = Field(default=0, ge=0, le=10_000)
    history_count: StrictInt = Field(default=0, ge=0, le=4096)
    item_offset: StrictInt = Field(default=0, ge=0, le=10_000)
    history_offset: StrictInt = Field(default=0, ge=0, le=4096)
    page_limit: StrictInt = Field(default=50, ge=1, le=100)
    review_items: tuple[FinanceReviewItem, ...] = Field(default=(), max_length=100)
    decision_history: tuple[FinanceReviewDecisionRecord, ...] = Field(
        default=(), max_length=100
    )
    pending_review: FinanceWorkspacePendingReview | None = None
    synthetic_only: Literal[True] = True
    real_financial_data_allowed: Literal[False] = False
    mutation_performed: Literal[False] = False


@dataclass(frozen=True)
class FinanceWorkspaceConfiguration:
    """Trusted server/CLI configuration, never an API request or response model."""

    repository_dir: Path
    helper_path: Path
    helper_sha256: str

    def __post_init__(self) -> None:
        if (
            not self.repository_dir.is_absolute()
            or not self.helper_path.is_absolute()
            or re.fullmatch(r"[0-9a-f]{64}", self.helper_sha256) is None
        ):
            raise ValueError("FINANCE_WORKSPACE_CONFIGURATION_INVALID")

    @property
    def configuration_ref(self) -> str:
        return stable_finance_ref(
            "configuration-ref:finance:workspace",
            {
                "repository_ref": finance_repository_ref(self.repository_dir),
                "helper_path_ref": finance_target_ref(self.helper_path),
                "helper_sha256": self.helper_sha256,
                "contract_ref": FINANCE_WORKSPACE_CONTRACT_REF,
            },
        )


def finance_workspace_safe_disable(env: Mapping[str, str] | None = None) -> bool:
    values = os.environ if env is None else env
    # Unknown values fail closed; absence does not initialize or authorize work.
    return values.get(FINANCE_WORKSPACE_DISABLE_ENV, "false").strip().lower() not in {
        "0",
        "false",
        "no",
        "off",
    }


def finance_workspace_error_code(exc: Exception) -> str:
    candidate = str(exc)
    if re.fullmatch(r"(?:FINANCE|FIN00[123])_[A-Z0-9_]{1,100}", candidate):
        return candidate
    return "FINANCE_WORKSPACE_REQUEST_FAILED"


def finance_workspace_body_within_limits(body: bytes | bytearray) -> bool:
    """Shared pre-decode byte/encoding/depth gate for API and CLI bundles."""

    if len(body) > FINANCE_WORKSPACE_MAX_BODY_BYTES:
        return False
    try:
        decoded = body.decode("utf-8")
    except UnicodeDecodeError:
        return False
    if "\x00" in decoded:
        return False
    depth, quoted, escaped = 0, False, False
    for value in body:
        if quoted:
            if escaped:
                escaped = False
            elif value == 92:
                escaped = True
            elif value == 34:
                quoted = False
        elif value == 34:
            quoted = True
        elif value in (91, 123):
            depth += 1
            if depth > FINANCE_WORKSPACE_MAX_DEPTH:
                return False
        elif value in (93, 125):
            depth -= 1
            if depth < 0:
                return False
    return True


class FinanceWorkspace:
    """A single server-selected book; no test backend can be selected via env/API."""

    def __init__(
        self,
        configuration: FinanceWorkspaceConfiguration | None,
        *,
        crypto_backend: FinanceCryptoBackend | None = None,
        safe_disable_engaged: Callable[[], bool] = finance_workspace_safe_disable,
        configuration_error: Literal[
            "configuration_missing", "configuration_invalid"
        ] = "configuration_missing",
    ) -> None:
        self.configuration = configuration
        self.configuration_error = configuration_error
        self.safe_disable_engaged = safe_disable_engaged
        self.service = None
        if configuration is not None:
            crypto = crypto_backend or MacOSFinanceCryptoBackend(
                helper_path=configuration.helper_path,
                expected_helper_sha256=configuration.helper_sha256,
            )
            self.service = FinanceKernelService(
                FinanceRepository(configuration.repository_dir, crypto_backend=crypto)
            )

    @classmethod
    def from_env(cls) -> "FinanceWorkspace":
        values = [
            os.environ.get(name, "")
            for name in (
                FINANCE_WORKSPACE_REPOSITORY_ENV,
                FINANCE_WORKSPACE_HELPER_ENV,
                FINANCE_WORKSPACE_HELPER_DIGEST_ENV,
            )
        ]
        if not all(values):
            return cls(None)
        try:
            configuration = FinanceWorkspaceConfiguration(
                Path(values[0]), Path(values[1]), values[2]
            )
        except ValueError:
            return cls(None, configuration_error="configuration_invalid")
        return cls(configuration)

    def _require_service(self) -> FinanceKernelService:
        if self.service is None:
            raise ValueError("FINANCE_WORKSPACE_CONFIGURATION_REQUIRED")
        return self.service

    def _book_setup_required(self) -> bool:
        root = self._require_service().repository.root
        try:
            metadata = root.lstat()
        except FileNotFoundError:
            return True
        if (
            not stat.S_ISDIR(metadata.st_mode)
            or stat.S_ISLNK(metadata.st_mode)
            or metadata.st_uid != os.getuid()
            or metadata.st_mode & 0o077
        ):
            raise ValueError("FINANCE_REPOSITORY_ROOT_NOT_PRIVATE")
        # A partially initialized directory is not a fresh empty book. Never
        # hide an interrupted write, missing key or tombstone as setup success.
        with os.scandir(root) as entries:
            return next(entries, None) is None

    def read_view(
        self, *, item_offset: int = 0, history_offset: int = 0, limit: int = 50
    ) -> FinanceWorkspaceView:
        common = {
            "item_offset": item_offset,
            "history_offset": history_offset,
            "page_limit": limit,
            "safe_disable_engaged": self.safe_disable_engaged(),
        }
        # Validate paging before native invocation or snapshot materialization.
        FinanceWorkspaceView(status="configuration_missing", **common)
        if self.configuration is None:
            return FinanceWorkspaceView(status=self.configuration_error, **common)
        service = self._require_service()
        common.update(
            configuration_ref=self.configuration.configuration_ref,
            repository_ref=finance_repository_ref(service.repository.root),
        )
        try:
            readiness = service.repository.crypto.readiness()
            common["crypto"] = readiness
            if readiness.status != "ready":
                return FinanceWorkspaceView(status="helper_unavailable", **common)
            if self._book_setup_required():
                return FinanceWorkspaceView(
                    status="book_setup_required", revision=0, **common
                )
            snapshot = service.repository.load_snapshot_read_only(
                request_ref="request-ref:finance:workspace-inspect"
            )
            projection = build_finance_review_projection(snapshot)
            imported = any(
                item.fixture_ref == FINANCE_SAMPLE_IMPORT_REF
                for item in snapshot.import_commits
            )
            return FinanceWorkspaceView(
                status="ready",
                revision=snapshot.revision,
                snapshot_ref=projection.source_snapshot_ref,
                projection_ref=projection.projection_ref,
                import_available=not imported and not common["safe_disable_engaged"],
                item_count=len(projection.review_items),
                history_count=len(projection.decision_history),
                review_items=projection.review_items[item_offset : item_offset + limit],
                decision_history=tuple(reversed(projection.decision_history))[
                    history_offset : history_offset + limit
                ],
                **common,
            )
        except (OSError, RuntimeError, ValueError) as exc:
            code = finance_workspace_error_code(exc)
            pending_review = None
            interrupted = code == "FINANCE_PENDING_COMMIT_REQUIRES_MUTATING_RECOVERY"
            if interrupted:
                try:
                    pending_review = self._inspect_pending_review()
                except (OSError, RuntimeError, ValueError) as pending_error:
                    code = finance_workspace_error_code(pending_error)
            return FinanceWorkspaceView(
                status="outcome_uncertain" if interrupted else "unavailable",
                error_code=code,
                pending_review=pending_review,
                **common,
            )

    def _inspect_pending_review(self) -> FinanceWorkspacePendingReview:
        service = self._require_service()
        preview, receipt = service.repository.inspect_pending_review_read_only()
        intent = FinanceWorkspaceIntent(
            operation=preview.operation,
            expected_revision=preview.source_revision,
            request_ref=preview.request_ref,
            idempotency_ref=preview.idempotency_ref,
            review_item_ref=preview.review_item_ref,
            decision=preview.decision,
            compensates_event_ref=preview.compensates_event_ref,
        )
        request = FinanceMutationRequest(
            operation=preview.operation,
            repository_ref=preview.repository_ref,
            expected_revision=preview.source_revision,
            request_ref=preview.request_ref,
            idempotency_ref=preview.idempotency_ref,
            review_preview=preview,
            safe_disable_ref=FIN003_REVIEW_SAFE_DISABLE_REF,
        )
        bundle = prepare_finance_mutation(service, request)
        if bundle.preview.payload_fingerprint_ref != receipt.payload_fingerprint_ref:
            raise ValueError("FIN003_REVIEW_PENDING_PAYLOAD_INVALID")
        assert self.configuration is not None
        return FinanceWorkspacePendingReview(
            intent=intent,
            preparation=FinanceWorkspacePreparation(
                configuration_ref=self.configuration.configuration_ref,
                bundle=bundle,
            ),
        )

    def prepare(self, intent: FinanceWorkspaceIntent) -> FinanceWorkspacePreparation:
        service = self._require_service()
        if self.safe_disable_engaged():
            raise ValueError("FINANCE_SAFE_DISABLE_ENGAGED")
        if service.repository.crypto.readiness().status != "ready":
            raise ValueError("FINANCE_WORKSPACE_HELPER_UNAVAILABLE")
        common = {
            "repository_ref": finance_repository_ref(service.repository.root),
            "operation": intent.operation,
            "expected_revision": intent.expected_revision,
            "request_ref": intent.request_ref,
            "idempotency_ref": intent.idempotency_ref,
        }
        if intent.operation == "create":
            if not self._book_setup_required():
                raise ValueError("FINANCE_REPOSITORY_ALREADY_EXISTS")
            request = FinanceMutationRequest(
                fixture_ref=FINANCE_SAMPLE_BOOK_REF, **common
            )
        else:
            snapshot = service.repository.load_snapshot_read_only(
                request_ref=intent.request_ref
            )
            if snapshot.revision != intent.expected_revision:
                raise ValueError("FINANCE_STALE_REVISION")
            if intent.operation == "import_commit":
                preview = preview_synthetic_csv_fixture(
                    FINANCE_SAMPLE_IMPORT_REF,
                    existing_fingerprint_refs=tuple(
                        ref
                        for item in snapshot.import_commits
                        for ref in item.source_fingerprint_refs
                    ),
                )
                if not preview.candidates:
                    raise ValueError("FINANCE_WORKSPACE_SAMPLE_ALREADY_IMPORTED")
                request = FinanceMutationRequest(
                    fixture_ref=FINANCE_SAMPLE_IMPORT_REF,
                    import_preview_ref=preview.preview_ref,
                    import_profile_ref=preview.profile_ref,
                    import_fixture_manifest_ref=preview.import_fixture_manifest_ref,
                    import_candidate_refs=tuple(
                        item.candidate_ref for item in preview.candidates
                    ),
                    import_source_fingerprint_refs=tuple(
                        item.source_fingerprint_ref for item in preview.observations
                    ),
                    safe_disable_ref=FIN002_IMPORT_SAFE_DISABLE_REF,
                    **common,
                )
            else:
                assert intent.review_item_ref is not None
                preview = preview_finance_review_persistence(
                    snapshot,
                    review_item_ref=intent.review_item_ref,
                    request_ref=intent.request_ref,
                    idempotency_ref=intent.idempotency_ref,
                    decision=intent.decision,
                    compensates_event_ref=intent.compensates_event_ref,
                )
                request = FinanceMutationRequest(
                    review_preview=preview,
                    safe_disable_ref=FIN003_REVIEW_SAFE_DISABLE_REF,
                    **common,
                )
        assert self.configuration is not None
        return FinanceWorkspacePreparation(
            configuration_ref=self.configuration.configuration_ref,
            bundle=prepare_finance_mutation(service, request),
        )

    def _validate_preparation(self, preparation: FinanceWorkspacePreparation) -> None:
        service = self._require_service()
        assert self.configuration is not None
        request = preparation.bundle.request
        if preparation.configuration_ref != self.configuration.configuration_ref:
            raise ValueError("FINANCE_WORKSPACE_CONFIGURATION_CHANGED")
        if request.operation not in {
            "create",
            "import_commit",
            "review_decision",
            "review_undo",
        }:
            raise ValueError("FINANCE_WORKSPACE_OPERATION_NOT_ADMITTED")
        expected_fixture = (
            FINANCE_SAMPLE_BOOK_REF
            if request.operation == "create"
            else FINANCE_SAMPLE_IMPORT_REF
            if request.operation == "import_commit"
            else None
        )
        if request.fixture_ref != expected_fixture or request.target_ref is not None:
            raise ValueError("FINANCE_WORKSPACE_INPUT_NOT_ADMITTED")
        expected = prepare_finance_mutation(
            service, request, now=preparation.bundle.preview.prepared_at
        )
        if expected != preparation.bundle:
            raise ValueError("FINANCE_WORKSPACE_PREPARATION_INVALID")

    def refresh_preparation(
        self, preparation: FinanceWorkspacePreparation
    ) -> FinanceWorkspacePreparation:
        """Re-present only an exact old review intent; never recover or authorize."""

        self._validate_preparation(preparation)
        if preparation.bundle.request.operation not in {
            "review_decision",
            "review_undo",
        }:
            raise ValueError("FIN003_REVIEW_REFRESH_SCOPE_INVALID")
        return FinanceWorkspacePreparation(
            configuration_ref=preparation.configuration_ref,
            bundle=prepare_finance_mutation(
                self._require_service(), preparation.bundle.request
            ),
        )

    def commit(
        self, preparation: FinanceWorkspacePreparation, *, confirmed: bool
    ) -> dict[str, object]:
        self._validate_preparation(preparation)
        now = datetime.now(timezone.utc)
        if (
            not preparation.bundle.preview.prepared_at
            <= now
            <= preparation.bundle.preview.expires_at
        ):
            raise ValueError("FINANCE_WORKSPACE_PREPARATION_NOT_CURRENT")
        # Return the committed Core receipt independently of subsequent reads.
        # A projection failure cannot erase a successful persistence result.
        result = confirm_finance_mutation(
            self._require_service(),
            preparation.bundle,
            confirmed=confirmed,
            actor_ref="actor-ref:finance:local-workspace-operator",
            safe_disable_engaged=self.safe_disable_engaged,
        )
        return FinanceWorkspaceCommitResult(
            receipt=result["receipt"],
            import_commit=result.get("import_commit"),
            lease_receipt_ref=result["lease_receipt_ref"],
        ).model_dump(mode="json")
