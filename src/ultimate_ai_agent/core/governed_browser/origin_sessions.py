"""Exact per-origin credential and inactive browser-session lifecycle."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Literal, Protocol

from pydantic import BaseModel, ConfigDict, Field, StrictBool, model_validator

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .browser_keychain import (
    GovernedBrowserCredentialRegistration,
    GovernedBrowserKeychainOperationReceipt,
)
from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    stable_governed_browser_ref,
)
from .transaction import GovernedExternalActionKernel


MAX_GOVERNED_BROWSER_SESSION_LIFETIME = timedelta(hours=1)


class GovernedBrowserOriginSessionOperation(str, Enum):
    enroll_credential = "enroll_credential"
    prepare_session = "prepare_session"
    revalidate_session = "revalidate_session"
    close_session = "close_session"
    revoke_credential = "revoke_credential"


class GovernedBrowserOriginSessionState(str, Enum):
    prepared_inactive = "prepared_inactive"
    expired = "expired"
    closed = "closed"
    revoked = "revoked"


class GovernedBrowserOriginSessionStatus(str, Enum):
    credential_stored = "credential_stored"
    session_prepared = "session_prepared"
    session_revalidated = "session_revalidated"
    session_closed = "session_closed"
    credential_revoked = "credential_revoked"
    blocked = "blocked"
    failed = "failed"
    outcome_ambiguous = "outcome_ambiguous"
    replayed = "replayed"


class GovernedBrowserOriginSessionStateConflict(RuntimeError):
    pass


class GovernedBrowserKeychainPort(Protocol):
    def store(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
        credential_material: bytearray,
    ) -> GovernedBrowserKeychainOperationReceipt: ...

    def probe(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt: ...

    def delete(
        self,
        registration: GovernedBrowserCredentialRegistration,
        *,
        request_ref: str,
    ) -> GovernedBrowserKeychainOperationReceipt: ...


def governed_browser_origin_session_ref(
    *,
    registration_ref: str,
    session_generation_ref: str,
) -> str:
    for value, label in (
        (registration_ref, "registration_ref"),
        (session_generation_ref, "session_generation_ref"),
    ):
        validate_task_ref(value, label)
    return stable_governed_browser_ref(
        "browser-origin-session-ref:governed-browser",
        {
            "registration_ref": registration_ref,
            "session_generation_ref": session_generation_ref,
        },
    )


class GovernedBrowserOriginSessionRecipe(BaseModel):
    """One immutable operation bound to one exact external-action request."""

    schema_version: Literal[
        "uaa-governed-browser-origin-session-recipe.v1"
    ] = "uaa-governed-browser-origin-session-recipe.v1"
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    operation: GovernedBrowserOriginSessionOperation
    binding_ref: str = Field(..., min_length=1, max_length=240)
    registration_ref: str = Field(..., min_length=1, max_length=240)
    origin_ref: str = Field(..., min_length=1, max_length=240)
    page_snapshot_ref: str = Field(..., min_length=1, max_length=240)
    credential_handle_ref: str = Field(..., min_length=1, max_length=240)
    credential_generation_ref: str = Field(..., min_length=1, max_length=240)
    keychain_item_ref: str = Field(..., min_length=1, max_length=240)
    session_ref: str = Field(..., min_length=1, max_length=240)
    session_generation_ref: str = Field(..., min_length=1, max_length=240)
    created_at: datetime
    expires_at: datetime
    exact_capability: Literal[AuthorityCapability.execute] = (
        AuthorityCapability.execute
    )
    registered_operation_required: Literal[True] = True
    exact_authority_lease_required: Literal[True] = True
    approval_revalidation_required: Literal[True] = True
    budget_reservation_required: Literal[True] = True
    readiness_revalidation_required: Literal[True] = True
    human_presence_required: Literal[True] = True
    per_origin_isolation_required: Literal[True] = True
    browser_session_start_allowed: Literal[False] = False
    authentication_allowed: Literal[False] = False
    cookies_allowed: Literal[False] = False
    live_network_allowed: Literal[False] = False
    external_mutation_allowed: Literal[False] = False
    real_external_targets_enabled: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_recipe(self) -> "GovernedBrowserOriginSessionRecipe":
        for value, label in (
            (self.recipe_ref, "recipe_ref"),
            (self.binding_ref, "binding_ref"),
            (self.registration_ref, "registration_ref"),
            (self.origin_ref, "origin_ref"),
            (self.page_snapshot_ref, "page_snapshot_ref"),
            (self.credential_handle_ref, "credential_handle_ref"),
            (self.credential_generation_ref, "credential_generation_ref"),
            (self.keychain_item_ref, "keychain_item_ref"),
            (self.session_ref, "session_ref"),
            (self.session_generation_ref, "session_generation_ref"),
        ):
            validate_task_ref(value, label)
        if self.created_at.tzinfo is None or self.expires_at.tzinfo is None:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_TIMEZONE_REQUIRED")
        if (
            self.expires_at <= self.created_at
            or self.expires_at - self.created_at
            > MAX_GOVERNED_BROWSER_SESSION_LIFETIME
        ):
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_LIFETIME_INVALID")
        if not self.session_generation_ref.startswith(
            "browser-session-generation-ref:governed-browser:"
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_GENERATION_REF_REQUIRED"
            )
        expected_session_ref = governed_browser_origin_session_ref(
            registration_ref=self.registration_ref,
            session_generation_ref=self.session_generation_ref,
        )
        if self.session_ref != expected_session_ref:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_REF_MISMATCH")
        expected_recipe_ref = stable_governed_browser_ref(
            "browser-origin-session-recipe-ref:governed-browser",
            self.model_dump(mode="json", exclude={"recipe_ref"}),
        )
        if self.recipe_ref != expected_recipe_ref:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_REF_MISMATCH")
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_allowed"}),
            "governed_browser_origin_session_recipe",
        )
        return self


def build_governed_browser_origin_session_recipe(
    request: ExternalActionExecutionRequest,
    *,
    registration: GovernedBrowserCredentialRegistration,
    operation: GovernedBrowserOriginSessionOperation,
    session_generation_ref: str,
    created_at: datetime,
    expires_at: datetime,
) -> GovernedBrowserOriginSessionRecipe:
    execution = ExternalActionExecutionRequest.model_validate(
        request.model_dump(mode="json")
    )
    registration = GovernedBrowserCredentialRegistration.model_validate(
        registration.model_dump(mode="json")
    )
    binding = execution.binding
    if binding.target_kind != ExternalActionTargetKind.local_validation.value:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_REAL_TARGETS_INACTIVE")
    if binding.authority_capability != AuthorityCapability.execute.value:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_EXACT_CAPABILITY_MISMATCH")
    if binding.origin_ref != registration.origin_ref:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_ORIGIN_MISMATCH")
    if binding.field_schema_ref != registration.registration_ref:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRATION_MISMATCH")
    if created_at.tzinfo is None or expires_at.tzinfo is None:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_TIMEZONE_REQUIRED")
    if created_at > binding.start_deadline:
        raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_CREATED_AFTER_DEADLINE")
    session_ref = governed_browser_origin_session_ref(
        registration_ref=registration.registration_ref,
        session_generation_ref=session_generation_ref,
    )
    required_resources = {
        registration.registration_ref,
        registration.credential_handle_ref,
        registration.credential_generation_ref,
        registration.keychain_item_ref,
        session_ref,
        session_generation_ref,
    }
    if not required_resources.issubset(set(binding.resource_refs)):
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_RESOURCE_NOT_AUTHORITY_BOUND"
        )
    payload = {
        "operation": operation,
        "binding_ref": binding.binding_ref,
        "registration_ref": registration.registration_ref,
        "origin_ref": registration.origin_ref,
        "page_snapshot_ref": binding.page_snapshot_ref,
        "credential_handle_ref": registration.credential_handle_ref,
        "credential_generation_ref": registration.credential_generation_ref,
        "keychain_item_ref": registration.keychain_item_ref,
        "session_ref": session_ref,
        "session_generation_ref": session_generation_ref,
        "created_at": created_at,
        "expires_at": expires_at,
    }
    provisional = GovernedBrowserOriginSessionRecipe.model_construct(
        recipe_ref="browser-origin-session-recipe-ref:governed-browser:pending",
        **payload,
    )
    recipe_ref = stable_governed_browser_ref(
        "browser-origin-session-recipe-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"recipe_ref"}),
    )
    return GovernedBrowserOriginSessionRecipe(recipe_ref=recipe_ref, **payload)


class GovernedBrowserOriginSessionRecipeRegistry:
    """Immutable exact recipe registry coupled to credential registrations."""

    def __init__(
        self,
        *,
        registrations: Sequence[GovernedBrowserCredentialRegistration],
        recipes: Sequence[GovernedBrowserOriginSessionRecipe],
    ) -> None:
        validated_registrations = tuple(
            GovernedBrowserCredentialRegistration.model_validate(
                item.model_dump(mode="json")
            )
            for item in registrations
        )
        validated_recipes = tuple(
            GovernedBrowserOriginSessionRecipe.model_validate(
                item.model_dump(mode="json")
            )
            for item in recipes
        )
        if not validated_registrations or not validated_recipes:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRY_EMPTY")
        if len(validated_registrations) > 64 or len(validated_recipes) > 128:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRY_TOO_LARGE")
        self._registrations = {
            item.registration_ref: item for item in validated_registrations
        }
        self._recipes = {item.recipe_ref: item for item in validated_recipes}
        if len(self._registrations) != len(validated_registrations):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRATION_DUPLICATE"
            )
        if len(self._recipes) != len(validated_recipes):
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_DUPLICATE")
        for recipe in validated_recipes:
            registration = self._registrations.get(recipe.registration_ref)
            if registration is None:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRATION_UNREGISTERED"
                )
            _validate_recipe_registration(recipe, registration)

    def resolve(
        self,
        recipe_ref: str,
    ) -> tuple[
        GovernedBrowserOriginSessionRecipe,
        GovernedBrowserCredentialRegistration,
    ] | None:
        recipe = self._recipes.get(recipe_ref)
        if recipe is None:
            return None
        registration = self._registrations.get(recipe.registration_ref)
        if registration is None:
            return None
        return recipe, registration


class GovernedBrowserOriginSessionRecord(BaseModel):
    """Durable safe-ref-only state for an inactive per-origin session."""

    schema_version: Literal[
        "uaa-governed-browser-origin-session-record.v1"
    ] = "uaa-governed-browser-origin-session-record.v1"
    state_receipt_ref: str
    session_ref: str
    session_generation_ref: str
    registration_ref: str
    origin_ref: str
    credential_handle_ref: str
    credential_generation_ref: str
    keychain_item_ref: str
    state: GovernedBrowserOriginSessionState
    created_at: datetime
    expires_at: datetime
    updated_at: datetime
    last_operation_ref: str
    keychain_item_present: StrictBool
    content_free: Literal[True] = True
    browser_session_started: Literal[False] = False
    authentication_performed: Literal[False] = False
    cookies_used: Literal[False] = False
    navigation_performed: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target_used: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_record(self) -> "GovernedBrowserOriginSessionRecord":
        for value, label in (
            (self.state_receipt_ref, "state_receipt_ref"),
            (self.session_ref, "session_ref"),
            (self.session_generation_ref, "session_generation_ref"),
            (self.registration_ref, "registration_ref"),
            (self.origin_ref, "origin_ref"),
            (self.credential_handle_ref, "credential_handle_ref"),
            (self.credential_generation_ref, "credential_generation_ref"),
            (self.keychain_item_ref, "keychain_item_ref"),
            (self.last_operation_ref, "last_operation_ref"),
        ):
            validate_task_ref(value, label)
        if any(
            timestamp.tzinfo is None
            for timestamp in (self.created_at, self.expires_at, self.updated_at)
        ):
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_TIMEZONE_REQUIRED")
        if self.expires_at <= self.created_at:
            raise ValueError("GOVERNED_BROWSER_ORIGIN_SESSION_LIFETIME_INVALID")
        if (
            self.state == GovernedBrowserOriginSessionState.revoked.value
            and self.keychain_item_present
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_REVOKED_KEYCHAIN_PRESENT"
            )
        expected_receipt_ref = stable_governed_browser_ref(
            "browser-origin-session-state-receipt-ref:governed-browser",
            self.model_dump(mode="json", exclude={"state_receipt_ref"}),
        )
        if self.state_receipt_ref != expected_receipt_ref:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_STATE_RECEIPT_REF_MISMATCH"
            )
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_used"}),
            "governed_browser_origin_session_record",
        )
        return self


class GovernedBrowserOriginSessionStore:
    """SQLite lifecycle store containing no credential or web content."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governed_browser_origin_sessions (
                    session_ref TEXT PRIMARY KEY,
                    scope_fingerprint_ref TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
                """
            )

    def prepare(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        operation_ref: str,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord:
        scope_fingerprint_ref = _session_scope_fingerprint_ref(recipe)
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            row = connection.execute(
                "SELECT scope_fingerprint_ref, record_json "
                "FROM governed_browser_origin_sessions WHERE session_ref = ?",
                (recipe.session_ref,),
            ).fetchone()
            if row is not None:
                if row[0] != scope_fingerprint_ref:
                    connection.rollback()
                    raise GovernedBrowserOriginSessionStateConflict(
                        "GOVERNED_BROWSER_ORIGIN_SESSION_SCOPE_CONFLICT"
                    )
                record = GovernedBrowserOriginSessionRecord.model_validate_json(
                    row[1]
                )
                connection.commit()
                if (
                    record.state
                    != GovernedBrowserOriginSessionState.prepared_inactive.value
                ):
                    raise GovernedBrowserOriginSessionStateConflict(
                        "GOVERNED_BROWSER_ORIGIN_SESSION_REOPEN_DENIED"
                    )
                return record
            record = _build_session_record(
                recipe,
                state=GovernedBrowserOriginSessionState.prepared_inactive,
                operation_ref=operation_ref,
                keychain_item_present=True,
                now=now,
            )
            connection.execute(
                "INSERT INTO governed_browser_origin_sessions VALUES (?, ?, ?)",
                (
                    recipe.session_ref,
                    scope_fingerprint_ref,
                    record.model_dump_json(),
                ),
            )
            connection.commit()
            return record

    def revalidate(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        operation_ref: str,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord:
        current = self._require_exact(recipe)
        if current.state not in {
            GovernedBrowserOriginSessionState.prepared_inactive.value,
            GovernedBrowserOriginSessionState.expired.value,
        }:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_REVALIDATION_STATE_DENIED"
            )
        state = (
            GovernedBrowserOriginSessionState.expired
            if now >= current.expires_at
            else GovernedBrowserOriginSessionState.prepared_inactive
        )
        return self._replace(
            recipe,
            current=current,
            state=state,
            operation_ref=operation_ref,
            keychain_item_present=True,
            now=now,
        )

    def close(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        operation_ref: str,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord:
        current = self._require_exact(recipe)
        if current.state == GovernedBrowserOriginSessionState.revoked.value:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_CLOSE_AFTER_REVOKE_DENIED"
            )
        if current.state == GovernedBrowserOriginSessionState.closed.value:
            return current
        return self._replace(
            recipe,
            current=current,
            state=GovernedBrowserOriginSessionState.closed,
            operation_ref=operation_ref,
            keychain_item_present=True,
            now=now,
        )

    def mark_revoked(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        operation_ref: str,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord | None:
        current = self.inspect(recipe.session_ref)
        if current is None:
            return None
        self._validate_scope(recipe, current)
        if current.state == GovernedBrowserOriginSessionState.revoked.value:
            return current
        return self._replace(
            recipe,
            current=current,
            state=GovernedBrowserOriginSessionState.revoked,
            operation_ref=operation_ref,
            keychain_item_present=False,
            now=now,
        )

    def inspect(
        self,
        session_ref: str,
    ) -> GovernedBrowserOriginSessionRecord | None:
        validate_task_ref(session_ref, "session_ref")
        with self._connect() as connection:
            row = connection.execute(
                "SELECT record_json FROM governed_browser_origin_sessions "
                "WHERE session_ref = ?",
                (session_ref,),
            ).fetchone()
        return (
            GovernedBrowserOriginSessionRecord.model_validate_json(row[0])
            if row is not None
            else None
        )

    def _require_exact(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
    ) -> GovernedBrowserOriginSessionRecord:
        record = self.inspect(recipe.session_ref)
        if record is None:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_NOT_FOUND"
            )
        self._validate_scope(recipe, record)
        return record

    @staticmethod
    def _validate_scope(
        recipe: GovernedBrowserOriginSessionRecipe,
        record: GovernedBrowserOriginSessionRecord,
    ) -> None:
        observed = (
            record.session_ref,
            record.session_generation_ref,
            record.registration_ref,
            record.origin_ref,
            record.credential_handle_ref,
            record.credential_generation_ref,
            record.keychain_item_ref,
            record.created_at,
            record.expires_at,
        )
        expected = (
            recipe.session_ref,
            recipe.session_generation_ref,
            recipe.registration_ref,
            recipe.origin_ref,
            recipe.credential_handle_ref,
            recipe.credential_generation_ref,
            recipe.keychain_item_ref,
            recipe.created_at,
            recipe.expires_at,
        )
        if observed != expected:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_SCOPE_CONFLICT"
            )

    def _replace(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        current: GovernedBrowserOriginSessionRecord,
        state: GovernedBrowserOriginSessionState,
        operation_ref: str,
        keychain_item_present: bool,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord:
        record = _build_session_record(
            recipe,
            state=state,
            operation_ref=operation_ref,
            keychain_item_present=keychain_item_present,
            now=now,
        )
        with self._lock, self._connect() as connection:
            connection.execute("BEGIN IMMEDIATE")
            changed = connection.execute(
                "UPDATE governed_browser_origin_sessions SET record_json = ? "
                "WHERE session_ref = ? AND scope_fingerprint_ref = ? "
                "AND record_json = ?",
                (
                    record.model_dump_json(),
                    recipe.session_ref,
                    _session_scope_fingerprint_ref(recipe),
                    current.model_dump_json(),
                ),
            ).rowcount
            if changed != 1:
                connection.rollback()
                raise GovernedBrowserOriginSessionStateConflict(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_UPDATE_CONFLICT"
                )
            connection.commit()
        return record

    def _connect(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)


class ExactGovernedBrowserOriginSessionRequest(BaseModel):
    recipe_ref: str
    execution_request: ExternalActionExecutionRequest

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedBrowserOriginSessionRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        return self


class GovernedBrowserOriginSessionReceipt(BaseModel):
    """Content-free receipt separate from keychain and session projections."""

    schema_version: Literal[
        "uaa-governed-browser-origin-session-receipt.v1"
    ] = "uaa-governed-browser-origin-session-receipt.v1"
    receipt_ref: str
    status: GovernedBrowserOriginSessionStatus
    operation: GovernedBrowserOriginSessionOperation | None = None
    recipe_ref: str
    transaction_ref: str
    intent_ref: str
    session_ref: str | None = None
    external_action_receipt_ref: str | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_settlement_ref: str | None = None
    reason_refs: tuple[str, ...] = ()
    content_free: Literal[True] = True
    replayed: StrictBool = False
    automatic_retry_allowed: Literal[False] = False
    credential_material_included: Literal[False] = False
    credential_material_returned: Literal[False] = False
    browser_session_started: Literal[False] = False
    authentication_performed: Literal[False] = False
    cookies_used: Literal[False] = False
    network_call_performed: Literal[False] = False
    external_mutation_performed: Literal[False] = False
    real_external_target_used: Literal[False] = False

    model_config = ConfigDict(
        use_enum_values=True,
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_receipt(self) -> "GovernedBrowserOriginSessionReceipt":
        for value in (
            self.receipt_ref,
            self.recipe_ref,
            self.transaction_ref,
            self.intent_ref,
            self.session_ref,
            self.external_action_receipt_ref,
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_settlement_ref,
            *self.reason_refs,
        ):
            if value is not None:
                validate_task_ref(value, "governed_browser_origin_session_receipt_ref")
        expected_receipt_ref = stable_governed_browser_ref(
            "browser-origin-session-operation-receipt-ref:governed-browser",
            self.model_dump(mode="json", exclude={"receipt_ref"}),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_RECEIPT_REF_MISMATCH"
            )
        validate_safe_task_payload(
            self.model_dump(mode="json", exclude={"cookies_used"}),
            "governed_browser_origin_session_receipt",
        )
        return self


class ExactGovernedBrowserOriginSessionResult(BaseModel):
    receipt: GovernedBrowserOriginSessionReceipt
    keychain_receipt: GovernedBrowserKeychainOperationReceipt | None = None
    session: GovernedBrowserOriginSessionRecord | None = None

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)


class ExactGovernedBrowserOriginSessionService:
    """Compose registered lifecycle operations with the external-action kernel."""

    def __init__(
        self,
        *,
        registry: GovernedBrowserOriginSessionRecipeRegistry,
        kernel: GovernedExternalActionKernel,
        keychain: GovernedBrowserKeychainPort,
        sessions: GovernedBrowserOriginSessionStore,
        clock=utc_now,  # type: ignore[no-untyped-def]
    ) -> None:
        self._registry = registry
        self._kernel = kernel
        self._keychain = keychain
        self._sessions = sessions
        self._clock = clock

    def execute(
        self,
        request: ExactGovernedBrowserOriginSessionRequest,
        *,
        credential_material: bytearray | None = None,
    ) -> ExactGovernedBrowserOriginSessionResult:
        request = ExactGovernedBrowserOriginSessionRequest.model_validate(
            request.model_dump(mode="json")
        )
        execution = request.execution_request
        resolved = self._registry.resolve(request.recipe_ref)
        if resolved is None:
            _zeroize_optional(credential_material)
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-origin-session:recipe-unregistered",
            )
        recipe, registration = resolved
        scope_reason = _recipe_scope_reason(recipe, registration, execution)
        if scope_reason is not None:
            _zeroize_optional(credential_material)
            return _preflight_blocked(request, scope_reason, recipe=recipe)
        operation = GovernedBrowserOriginSessionOperation(recipe.operation)
        if operation == GovernedBrowserOriginSessionOperation.enroll_credential:
            if credential_material is None:
                return _preflight_blocked(
                    request,
                    "reason-ref:governed-browser-origin-session:"
                    "credential-material-required",
                    recipe=recipe,
                )
        elif credential_material is not None:
            _zeroize_optional(credential_material)
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-origin-session:"
                "unexpected-credential-material",
                recipe=recipe,
            )

        captured_keychain: GovernedBrowserKeychainOperationReceipt | None = None
        captured_session: GovernedBrowserOriginSessionRecord | None = None
        operation_ref = stable_governed_browser_ref(
            "browser-origin-session-operation-ref:governed-browser",
            {
                "recipe_ref": recipe.recipe_ref,
                "intent_ref": execution.intent_ref,
            },
        )

        def dispatch(
            item: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            nonlocal captured_keychain, captured_session
            request_ref = stable_governed_browser_ref(
                "request-ref:governed-browser-keychain",
                {
                    "operation_ref": operation_ref,
                    "transaction_ref": item.binding.transaction_ref,
                },
            )
            try:
                if (
                    operation
                    == GovernedBrowserOriginSessionOperation.enroll_credential
                ):
                    assert credential_material is not None
                    captured_keychain = self._keychain.store(
                        registration,
                        request_ref=request_ref,
                        credential_material=credential_material,
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.prepare_session
                ):
                    captured_keychain = self._keychain.probe(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_session = self._sessions.prepare(
                        recipe,
                        operation_ref=operation_ref,
                        now=self._clock(),
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.revalidate_session
                ):
                    captured_keychain = self._keychain.probe(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_session = self._sessions.revalidate(
                        recipe,
                        operation_ref=operation_ref,
                        now=self._clock(),
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.close_session
                ):
                    captured_session = self._sessions.close(
                        recipe,
                        operation_ref=operation_ref,
                        now=self._clock(),
                    )
                else:
                    captured_keychain = self._keychain.delete(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_session = self._sessions.mark_revoked(
                        recipe,
                        operation_ref=operation_ref,
                        now=self._clock(),
                    )
            except GovernedBrowserOriginSessionStateConflict:
                conflict_evidence_refs = [
                    stable_governed_browser_ref(
                        "evidence-ref:governed-browser-origin-session:"
                        "state-conflict",
                        {"operation_ref": operation_ref},
                    )
                ]
                if captured_keychain is not None:
                    conflict_evidence_refs.extend(
                        (
                            captured_keychain.helper_receipt_ref,
                            captured_keychain.keychain_item_ref,
                        )
                    )
                return ExternalActionDispatchResult(
                    outcome=(
                        ExternalActionDispatchOutcome.outcome_ambiguous
                        if operation
                        == GovernedBrowserOriginSessionOperation.revoke_credential
                        and captured_keychain is not None
                        else ExternalActionDispatchOutcome.failed
                    ),
                    evidence_refs=conflict_evidence_refs,
                    verified=False,
                )
            evidence_refs = [operation_ref]
            if captured_keychain is not None:
                evidence_refs.extend(
                    (
                        captured_keychain.helper_receipt_ref,
                        captured_keychain.keychain_item_ref,
                    )
                )
            if captured_session is not None:
                evidence_refs.append(captured_session.state_receipt_ref)
            return ExternalActionDispatchResult(
                outcome=ExternalActionDispatchOutcome.succeeded,
                evidence_refs=list(dict.fromkeys(evidence_refs)),
                verified=True,
            )

        try:
            external_receipt = self._kernel.execute(execution, dispatch=dispatch)
        finally:
            _zeroize_optional(credential_material)
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            keychain_receipt=captured_keychain,
            session=captured_session,
        )


def _validate_recipe_registration(
    recipe: GovernedBrowserOriginSessionRecipe,
    registration: GovernedBrowserCredentialRegistration,
) -> None:
    observed = (
        recipe.registration_ref,
        recipe.origin_ref,
        recipe.credential_handle_ref,
        recipe.credential_generation_ref,
        recipe.keychain_item_ref,
    )
    expected = (
        registration.registration_ref,
        registration.origin_ref,
        registration.credential_handle_ref,
        registration.credential_generation_ref,
        registration.keychain_item_ref,
    )
    if observed != expected:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_REGISTRATION_BINDING_MISMATCH"
        )


def _recipe_scope_reason(
    recipe: GovernedBrowserOriginSessionRecipe,
    registration: GovernedBrowserCredentialRegistration,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    required_resources = {
        registration.registration_ref,
        registration.credential_handle_ref,
        registration.credential_generation_ref,
        registration.keychain_item_ref,
        recipe.session_ref,
        recipe.session_generation_ref,
    }
    checks = (
        (
            recipe.binding_ref == binding.binding_ref,
            "reason-ref:governed-browser-origin-session:binding-mismatch",
        ),
        (
            binding.origin_ref == recipe.origin_ref == registration.origin_ref,
            "reason-ref:governed-browser-origin-session:origin-mismatch",
        ),
        (
            binding.page_snapshot_ref == recipe.page_snapshot_ref,
            "reason-ref:governed-browser-origin-session:snapshot-mismatch",
        ),
        (
            binding.field_schema_ref
            == recipe.registration_ref
            == registration.registration_ref,
            "reason-ref:governed-browser-origin-session:"
            "registration-mismatch",
        ),
        (
            binding.authority_capability == AuthorityCapability.execute.value,
            "reason-ref:governed-browser-origin-session:"
            "capability-mismatch",
        ),
        (
            required_resources.issubset(set(binding.resource_refs)),
            "reason-ref:governed-browser-origin-session:"
            "resource-not-authority-bound",
        ),
        (
            binding.target_kind == ExternalActionTargetKind.local_validation.value,
            "reason-ref:governed-browser-origin-session:"
            "real-targets-inactive",
        ),
    )
    return next((reason for allowed, reason in checks if not allowed), None)


def _session_scope_fingerprint_ref(
    recipe: GovernedBrowserOriginSessionRecipe,
) -> str:
    return stable_governed_browser_ref(
        "browser-origin-session-scope-fingerprint-ref:governed-browser",
        {
            "session_ref": recipe.session_ref,
            "session_generation_ref": recipe.session_generation_ref,
            "registration_ref": recipe.registration_ref,
            "origin_ref": recipe.origin_ref,
            "credential_handle_ref": recipe.credential_handle_ref,
            "credential_generation_ref": recipe.credential_generation_ref,
            "keychain_item_ref": recipe.keychain_item_ref,
            "created_at": recipe.created_at.isoformat(),
            "expires_at": recipe.expires_at.isoformat(),
        },
    )


def _build_session_record(
    recipe: GovernedBrowserOriginSessionRecipe,
    *,
    state: GovernedBrowserOriginSessionState,
    operation_ref: str,
    keychain_item_present: bool,
    now: datetime,
) -> GovernedBrowserOriginSessionRecord:
    payload = {
        "session_ref": recipe.session_ref,
        "session_generation_ref": recipe.session_generation_ref,
        "registration_ref": recipe.registration_ref,
        "origin_ref": recipe.origin_ref,
        "credential_handle_ref": recipe.credential_handle_ref,
        "credential_generation_ref": recipe.credential_generation_ref,
        "keychain_item_ref": recipe.keychain_item_ref,
        "state": state,
        "created_at": recipe.created_at,
        "expires_at": recipe.expires_at,
        "updated_at": now,
        "last_operation_ref": operation_ref,
        "keychain_item_present": keychain_item_present,
    }
    provisional = GovernedBrowserOriginSessionRecord.model_construct(
        state_receipt_ref=(
            "browser-origin-session-state-receipt-ref:governed-browser:pending"
        ),
        **payload,
    )
    receipt_ref = stable_governed_browser_ref(
        "browser-origin-session-state-receipt-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"state_receipt_ref"}),
    )
    return GovernedBrowserOriginSessionRecord(
        state_receipt_ref=receipt_ref,
        **payload,
    )


def _preflight_blocked(
    request: ExactGovernedBrowserOriginSessionRequest,
    reason_ref: str,
    *,
    recipe: GovernedBrowserOriginSessionRecipe | None = None,
) -> ExactGovernedBrowserOriginSessionResult:
    execution = request.execution_request
    receipt = _build_operation_receipt(
        status=GovernedBrowserOriginSessionStatus.blocked,
        operation=(
            GovernedBrowserOriginSessionOperation(recipe.operation)
            if recipe is not None
            else None
        ),
        recipe_ref=request.recipe_ref,
        execution=execution,
        session_ref=recipe.session_ref if recipe is not None else None,
        reason_refs=(reason_ref,),
    )
    return ExactGovernedBrowserOriginSessionResult(receipt=receipt)


def _result_from_external_receipt(
    *,
    request: ExactGovernedBrowserOriginSessionRequest,
    recipe: GovernedBrowserOriginSessionRecipe,
    external_receipt: ExternalActionReceipt,
    keychain_receipt: GovernedBrowserKeychainOperationReceipt | None,
    session: GovernedBrowserOriginSessionRecord | None,
) -> ExactGovernedBrowserOriginSessionResult:
    operation = GovernedBrowserOriginSessionOperation(recipe.operation)
    if external_receipt.replayed:
        status = GovernedBrowserOriginSessionStatus.replayed
        keychain_receipt = None
        session = None
    elif external_receipt.state == ExternalActionState.blocked.value:
        status = GovernedBrowserOriginSessionStatus.blocked
        keychain_receipt = None
        session = None
    elif external_receipt.state == ExternalActionState.failed.value:
        status = GovernedBrowserOriginSessionStatus.failed
        keychain_receipt = None
        session = None
    elif external_receipt.state == ExternalActionState.outcome_ambiguous.value:
        status = GovernedBrowserOriginSessionStatus.outcome_ambiguous
        keychain_receipt = None
        session = None
    else:
        status = {
            GovernedBrowserOriginSessionOperation.enroll_credential: (
                GovernedBrowserOriginSessionStatus.credential_stored
            ),
            GovernedBrowserOriginSessionOperation.prepare_session: (
                GovernedBrowserOriginSessionStatus.session_prepared
            ),
            GovernedBrowserOriginSessionOperation.revalidate_session: (
                GovernedBrowserOriginSessionStatus.session_revalidated
            ),
            GovernedBrowserOriginSessionOperation.close_session: (
                GovernedBrowserOriginSessionStatus.session_closed
            ),
            GovernedBrowserOriginSessionOperation.revoke_credential: (
                GovernedBrowserOriginSessionStatus.credential_revoked
            ),
        }[operation]
    receipt = _build_operation_receipt(
        status=status,
        operation=operation,
        recipe_ref=request.recipe_ref,
        execution=request.execution_request,
        session_ref=recipe.session_ref,
        external_receipt=external_receipt,
        reason_refs=tuple(external_receipt.reason_refs),
    )
    return ExactGovernedBrowserOriginSessionResult(
        receipt=receipt,
        keychain_receipt=keychain_receipt,
        session=session,
    )


def _build_operation_receipt(
    *,
    status: GovernedBrowserOriginSessionStatus,
    operation: GovernedBrowserOriginSessionOperation | None,
    recipe_ref: str,
    execution: ExternalActionExecutionRequest,
    session_ref: str | None,
    reason_refs: tuple[str, ...],
    external_receipt: ExternalActionReceipt | None = None,
) -> GovernedBrowserOriginSessionReceipt:
    payload = {
        "status": status,
        "operation": operation,
        "recipe_ref": recipe_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "session_ref": session_ref,
        "external_action_receipt_ref": (
            external_receipt.receipt_ref if external_receipt is not None else None
        ),
        "approval_validation_ref": (
            external_receipt.approval_validation_ref
            if external_receipt is not None
            else None
        ),
        "authority_decision_ref": (
            external_receipt.authority_decision_ref
            if external_receipt is not None
            else None
        ),
        "budget_reservation_ref": (
            external_receipt.budget_reservation_ref
            if external_receipt is not None
            else None
        ),
        "budget_settlement_ref": (
            external_receipt.budget_settlement_ref
            if external_receipt is not None
            else None
        ),
        "reason_refs": reason_refs,
        "replayed": (
            external_receipt.replayed if external_receipt is not None else False
        ),
    }
    provisional = GovernedBrowserOriginSessionReceipt.model_construct(
        receipt_ref=(
            "browser-origin-session-operation-receipt-ref:"
            "governed-browser:pending"
        ),
        **payload,
    )
    receipt_ref = stable_governed_browser_ref(
        "browser-origin-session-operation-receipt-ref:governed-browser",
        provisional.model_dump(mode="json", exclude={"receipt_ref"}),
    )
    return GovernedBrowserOriginSessionReceipt(
        receipt_ref=receipt_ref,
        **payload,
    )


def _zeroize_optional(value: bytearray | None) -> None:
    if value is None:
        return
    for index in range(len(value)):
        value[index] = 0
