"""Exact per-origin credential and inactive browser-session lifecycle."""

from __future__ import annotations

import sqlite3
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import RLock
from typing import Literal, Protocol
from weakref import WeakKeyDictionary

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    StrictBool,
    ValidationInfo,
    model_validator,
)

from ultimate_ai_agent.core.authority import AuthorityCapability
from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)
from ultimate_ai_agent.core.time import utc_now

from .browser_keychain import (
    GOVERNED_BROWSER_CREDENTIAL_MAX_BYTES,
    GOVERNED_BROWSER_CREDENTIAL_MIN_BYTES,
    GOVERNED_BROWSER_KEYCHAIN_ITEM_ALREADY_EXISTS,
    GOVERNED_BROWSER_KEYCHAIN_ITEM_NOT_FOUND,
    GovernedBrowserCredentialRegistration,
    GovernedBrowserKeychainError,
    GovernedBrowserKeychainOperation,
    GovernedBrowserKeychainOperationReceipt,
    governed_browser_keychain_helper_receipt_ref,
)
from .contracts import (
    ExternalActionDispatchOutcome,
    ExternalActionDispatchResult,
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    ExternalActionTargetKind,
    governed_receipt_identity_payload,
    stable_governed_browser_ref,
)
from .operation_proofs import (
    GovernedBrowserOperationProof,
    GovernedBrowserOperationProofError,
    OriginSessionOperationProofMaterial,
    _attest_operation_proof,
    _record_operation_proof,
    _register_operation_proof_service,
    _require_operation_proof_service,
)
from .replay_provenance import (
    ExternalActionReplayEvidenceExpectation,
    ExternalActionReplayValidationContext,
    _build_external_action_replay_validation_context,
    _require_operation_replay_evidence_envelope,
    replay_validation_context,
    require_external_action_replay_provenance,
)
from .transaction import GovernedExternalActionKernel


MAX_GOVERNED_BROWSER_SESSION_LIFETIME = timedelta(hours=1)
_ORIGIN_SESSION_REPLAY_LANE_REF = "lane-ref:governed-browser-origin-session"
_NON_MUTATING_KEYCHAIN_ERROR_CODES = frozenset(
    {
        GOVERNED_BROWSER_KEYCHAIN_ITEM_ALREADY_EXISTS,
        GOVERNED_BROWSER_KEYCHAIN_ITEM_NOT_FOUND,
        "GOVERNED_BROWSER_CREDENTIAL_LENGTH_INVALID",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_FINGERPRINT_MISMATCH",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_COPY_SHORT_WRITE",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_FILE_CHANGED",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_FILE_UNTRUSTED",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_FINGERPRINT_MISMATCH",
        "GOVERNED_BROWSER_KEYCHAIN_HELPER_REQUEST_TOO_LARGE",
        "GOVERNED_BROWSER_KEYCHAIN_LOCKED",
        "GOVERNED_BROWSER_KEYCHAIN_UNSUPPORTED_PLATFORM",
    }
)
_OPERATION_PROOF_REF_PREFIX = (
    "operation-proof-ref:governed-browser:sha256:"
)


@dataclass(frozen=True)
class _OriginSessionStoreBinding:
    path: Path
    lock: RLock


_ORIGIN_SESSION_STORE_BINDINGS: WeakKeyDictionary[
    object,
    _OriginSessionStoreBinding,
] = WeakKeyDictionary()
_ORIGIN_SESSION_STORE_BINDINGS_LOCK = RLock()


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


def governed_browser_origin_session_operation_authority_ref(
    *,
    registration_ref: str,
    session_generation_ref: str,
    operation: GovernedBrowserOriginSessionOperation,
) -> str:
    """Derive the one lifecycle operation that an exact binding authorizes."""

    for value, label in (
        (registration_ref, "registration_ref"),
        (session_generation_ref, "session_generation_ref"),
    ):
        validate_task_ref(value, label)
    exact_operation = GovernedBrowserOriginSessionOperation(operation)
    return stable_governed_browser_ref(
        "browser-origin-session-operation-authority-ref:governed-browser",
        {
            "registration_ref": registration_ref,
            "session_generation_ref": session_generation_ref,
            "operation": exact_operation.value,
        },
    )


class GovernedBrowserOriginSessionRecipe(BaseModel):
    """One immutable operation bound to one exact external-action request."""

    schema_version: Literal[
        "uaa-governed-browser-origin-session-recipe.v1"
    ] = "uaa-governed-browser-origin-session-recipe.v1"
    recipe_ref: str = Field(..., min_length=1, max_length=240)
    operation: GovernedBrowserOriginSessionOperation
    operation_authority_ref: str = Field(..., min_length=1, max_length=240)
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
            (self.operation_authority_ref, "operation_authority_ref"),
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
        expected_operation_authority_ref = (
            governed_browser_origin_session_operation_authority_ref(
                registration_ref=self.registration_ref,
                session_generation_ref=self.session_generation_ref,
                operation=GovernedBrowserOriginSessionOperation(self.operation),
            )
        )
        if self.operation_authority_ref != expected_operation_authority_ref:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_AUTHORITY_REF_MISMATCH"
            )
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
    operation_authority_ref = (
        governed_browser_origin_session_operation_authority_ref(
            registration_ref=registration.registration_ref,
            session_generation_ref=session_generation_ref,
            operation=operation,
        )
    )
    bound_operation_refs = tuple(
        ref
        for ref in binding.resource_refs
        if ref.startswith(
            "browser-origin-session-operation-authority-ref:"
            "governed-browser:"
        )
    )
    if bound_operation_refs != (operation_authority_ref,):
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_AUTHORITY_MISMATCH"
        )
    required_resources = {
        operation_authority_ref,
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
        "operation_authority_ref": operation_authority_ref,
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
        self.path = path.expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = RLock()
        with sqlite3.connect(self.path) as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS governed_browser_origin_sessions (
                    session_ref TEXT PRIMARY KEY,
                    scope_fingerprint_ref TEXT NOT NULL,
                    record_json TEXT NOT NULL
                )
                """
            )
        with _ORIGIN_SESSION_STORE_BINDINGS_LOCK:
            _ORIGIN_SESSION_STORE_BINDINGS[self] = _OriginSessionStoreBinding(
                path=self.path,
                lock=self._lock,
            )

    def prepare(
        self,
        recipe: GovernedBrowserOriginSessionRecipe,
        *,
        operation_ref: str,
        now: datetime,
    ) -> GovernedBrowserOriginSessionRecord:
        if now >= recipe.expires_at:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_PREPARE_EXPIRED"
            )
        scope_fingerprint_ref = _session_scope_fingerprint_ref(recipe)
        binding = _exact_origin_session_store_binding(self)
        with binding.lock, sqlite3.connect(binding.path) as connection:
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
        current = GovernedBrowserOriginSessionStore._require_exact(
            self,
            recipe,
        )
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
        return GovernedBrowserOriginSessionStore._replace(
            self,
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
        current = GovernedBrowserOriginSessionStore._require_exact(
            self,
            recipe,
        )
        if current.state == GovernedBrowserOriginSessionState.revoked.value:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_CLOSE_AFTER_REVOKE_DENIED"
            )
        if current.state == GovernedBrowserOriginSessionState.closed.value:
            return current
        return GovernedBrowserOriginSessionStore._replace(
            self,
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
        current = GovernedBrowserOriginSessionStore.inspect(
            self,
            recipe.session_ref,
        )
        if current is None:
            return None
        GovernedBrowserOriginSessionStore._validate_scope(recipe, current)
        if current.state == GovernedBrowserOriginSessionState.revoked.value:
            return current
        return GovernedBrowserOriginSessionStore._replace(
            self,
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
        binding = _exact_origin_session_store_binding(self)
        with sqlite3.connect(binding.path) as connection:
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
        record = GovernedBrowserOriginSessionStore.inspect(
            self,
            recipe.session_ref,
        )
        if record is None:
            raise GovernedBrowserOriginSessionStateConflict(
                "GOVERNED_BROWSER_ORIGIN_SESSION_NOT_FOUND"
            )
        GovernedBrowserOriginSessionStore._validate_scope(recipe, record)
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
        binding = _exact_origin_session_store_binding(self)
        with binding.lock, sqlite3.connect(binding.path) as connection:
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


def _exact_origin_session_store_binding(
    store: object,
) -> _OriginSessionStoreBinding:
    if type(store) is not GovernedBrowserOriginSessionStore:
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_STORE_SOURCE_INVALID"
        )
    with _ORIGIN_SESSION_STORE_BINDINGS_LOCK:
        binding = _ORIGIN_SESSION_STORE_BINDINGS.get(store)
    if binding is None:
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_STORE_SOURCE_INVALID"
        )
    try:
        current_path = object.__getattribute__(store, "path")
        current_lock = object.__getattribute__(store, "_lock")
    except AttributeError as exc:
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_STORE_SOURCE_INVALID"
        ) from exc
    if current_path != binding.path or current_lock is not binding.lock:
        raise GovernedBrowserOriginSessionStateConflict(
            "GOVERNED_BROWSER_ORIGIN_SESSION_STORE_SOURCE_INVALID"
        )
    return binding


class ExactGovernedBrowserOriginSessionRequest(BaseModel):
    recipe_ref: str
    execution_request: ExternalActionExecutionRequest

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_request(self) -> "ExactGovernedBrowserOriginSessionRequest":
        validate_task_ref(self.recipe_ref, "recipe_ref")
        return self


def _origin_session_receipt_identity_payload(
    receipt: BaseModel,
) -> dict[str, object]:
    payload = governed_receipt_identity_payload(receipt)
    # The external receipt ref already commits to this typed snapshot. Excluding
    # the redundant projection preserves the established outer receipt identity.
    payload.pop("external_receipt_snapshot", None)
    # The recipe ref likewise commits to this immutable typed recipe. Preserve
    # the established outer identity while retaining an independently validated
    # scope projection for deserialized receipts.
    payload.pop("recipe_snapshot", None)
    return payload


def _validate_origin_session_success_evidence(
    *,
    recipe: GovernedBrowserOriginSessionRecipe,
    intent_ref: str,
    evidence_refs: tuple[str, ...],
) -> None:
    base_evidence_refs, operation_proof_ref = (
        _split_origin_session_operation_proof(evidence_refs)
    )
    if operation_proof_ref is None:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_REQUIRED"
        )
    operation = GovernedBrowserOriginSessionOperation(recipe.operation)
    operation_ref = stable_governed_browser_ref(
        "browser-origin-session-operation-ref:governed-browser",
        {
            "recipe_ref": recipe.recipe_ref,
            "intent_ref": intent_ref,
        },
    )
    helper_prefix = "helper-receipt-ref:governed-browser-keychain:"
    state_prefix = (
        "browser-origin-session-state-receipt-ref:governed-browser:"
    )
    keychain_prefix_valid = (
        len(base_evidence_refs) >= 3
        and base_evidence_refs[1].startswith(helper_prefix)
        and base_evidence_refs[2] == recipe.keychain_item_ref
    )
    if operation == GovernedBrowserOriginSessionOperation.enroll_credential:
        valid = len(base_evidence_refs) == 3 and keychain_prefix_valid
    elif operation in {
        GovernedBrowserOriginSessionOperation.prepare_session,
        GovernedBrowserOriginSessionOperation.revalidate_session,
    }:
        valid = (
            len(base_evidence_refs) == 4
            and keychain_prefix_valid
            and base_evidence_refs[3].startswith(state_prefix)
        )
    elif operation == GovernedBrowserOriginSessionOperation.close_session:
        valid = (
            len(base_evidence_refs) == 2
            and base_evidence_refs[1].startswith(state_prefix)
        )
    else:
        valid = (
            len(base_evidence_refs) in {3, 4}
            and keychain_prefix_valid
            and (
                len(base_evidence_refs) == 3
                or base_evidence_refs[3].startswith(state_prefix)
            )
        )
    if not valid or base_evidence_refs[0] != operation_ref:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_EVIDENCE_MISMATCH"
        )


def _split_origin_session_operation_proof(
    evidence_refs: tuple[str, ...],
) -> tuple[tuple[str, ...], str | None]:
    if evidence_refs and evidence_refs[-1].startswith(
        _OPERATION_PROOF_REF_PREFIX
    ):
        return evidence_refs[:-1], evidence_refs[-1]
    return evidence_refs, None


def _origin_session_failure_evidence_valid(
    *,
    recipe: GovernedBrowserOriginSessionRecipe,
    intent_ref: str,
    evidence_refs: tuple[str, ...],
    success_evidence_valid: bool,
) -> bool:
    operation = GovernedBrowserOriginSessionOperation(recipe.operation)
    operation_ref = stable_governed_browser_ref(
        "browser-origin-session-operation-ref:governed-browser",
        {
            "recipe_ref": recipe.recipe_ref,
            "intent_ref": intent_ref,
        },
    )
    keychain_failure_refs = {
        stable_governed_browser_ref(
            (
                "evidence-ref:governed-browser-origin-session:"
                "keychain-precondition-failed"
            ),
            {
                "operation_ref": operation_ref,
                "reason_code": reason_code,
            },
        )
        for reason_code in _NON_MUTATING_KEYCHAIN_ERROR_CODES
    }
    if len(evidence_refs) == 1 and evidence_refs[0] in keychain_failure_refs:
        return True
    conflict_ref = stable_governed_browser_ref(
        "evidence-ref:governed-browser-origin-session:state-conflict",
        {"operation_ref": operation_ref},
    )
    if evidence_refs == (conflict_ref,):
        return True
    return (
        operation
        == GovernedBrowserOriginSessionOperation.revalidate_session
        and success_evidence_valid
    )


def _origin_session_operation_ambiguity_evidence_valid(
    *,
    recipe: GovernedBrowserOriginSessionRecipe,
    intent_ref: str,
    evidence_refs: tuple[str, ...],
) -> bool:
    if (
        GovernedBrowserOriginSessionOperation(recipe.operation)
        != GovernedBrowserOriginSessionOperation.revoke_credential
    ):
        return False
    operation_ref = stable_governed_browser_ref(
        "browser-origin-session-operation-ref:governed-browser",
        {
            "recipe_ref": recipe.recipe_ref,
            "intent_ref": intent_ref,
        },
    )
    conflict_ref = stable_governed_browser_ref(
        "evidence-ref:governed-browser-origin-session:state-conflict",
        {"operation_ref": operation_ref},
    )
    return (
        len(evidence_refs) == 3
        and evidence_refs[0] == conflict_ref
        and evidence_refs[1].startswith(
            "helper-receipt-ref:governed-browser-keychain:"
        )
        and evidence_refs[2] == recipe.keychain_item_ref
    )


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
    recipe_snapshot: GovernedBrowserOriginSessionRecipe | None = None
    external_receipt_snapshot: ExternalActionReceipt | None = None
    approval_validation_ref: str | None = None
    authority_decision_ref: str | None = None
    budget_reservation_ref: str | None = None
    budget_release_ref: str | None = None
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
    def validate_receipt(
        self,
        info: ValidationInfo,
    ) -> "GovernedBrowserOriginSessionReceipt":
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
            self.budget_release_ref,
            self.budget_settlement_ref,
            *self.reason_refs,
        ):
            if value is not None:
                validate_task_ref(value, "governed_browser_origin_session_receipt_ref")
        external_kernel_proof_refs = (
            self.approval_validation_ref,
            self.authority_decision_ref,
            self.budget_reservation_ref,
            self.budget_release_ref,
            self.budget_settlement_ref,
        )
        if self.external_action_receipt_ref is None:
            if (
                self.recipe_snapshot is not None
                or self.external_receipt_snapshot is not None
                or any(ref is not None for ref in external_kernel_proof_refs)
                or self.replayed
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_INVALID"
                )
            if self.status != GovernedBrowserOriginSessionStatus.blocked.value:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_PROOF_CONTEXT_REQUIRED"
                )
        else:
            if self.recipe_snapshot is None:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_SNAPSHOT_REQUIRED"
                )
            if self.external_receipt_snapshot is None:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_RECEIPT_SNAPSHOT_REQUIRED"
                )
        expected_receipt_ref = stable_governed_browser_ref(
            "browser-origin-session-operation-receipt-ref:governed-browser",
            _origin_session_receipt_identity_payload(self),
        )
        if self.receipt_ref != expected_receipt_ref:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_RECEIPT_REF_MISMATCH"
            )
        external_snapshot = self.external_receipt_snapshot
        if external_snapshot is not None:
            recipe_snapshot = self.recipe_snapshot
            assert recipe_snapshot is not None
            if (
                external_snapshot.state == ExternalActionState.succeeded.value
                and self.operation is None
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_REQUIRED"
                )
            if (
                recipe_snapshot.recipe_ref != self.recipe_ref
                or recipe_snapshot.operation != self.operation
                or recipe_snapshot.binding_ref != external_snapshot.binding_ref
                or recipe_snapshot.session_ref != self.session_ref
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_RECIPE_SNAPSHOT_SCOPE_MISMATCH"
                )
            projected_context = (
                external_snapshot.receipt_ref,
                external_snapshot.transaction_ref,
                external_snapshot.intent_ref,
                external_snapshot.approval_validation_ref,
                external_snapshot.authority_decision_ref,
                external_snapshot.budget_reservation_ref,
                external_snapshot.budget_release_ref,
                external_snapshot.budget_settlement_ref,
                tuple(external_snapshot.reason_refs),
                external_snapshot.replayed,
            )
            wrapper_context = (
                self.external_action_receipt_ref,
                self.transaction_ref,
                self.intent_ref,
                self.approval_validation_ref,
                self.authority_decision_ref,
                self.budget_reservation_ref,
                self.budget_release_ref,
                self.budget_settlement_ref,
                tuple(self.reason_refs),
                self.replayed,
            )
            if wrapper_context != projected_context:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_RECEIPT_PROJECTION_MISMATCH"
                )
            if external_snapshot.state == ExternalActionState.succeeded.value and (
                any(
                    ref is None
                    for ref in (
                        external_snapshot.approval_validation_ref,
                        external_snapshot.authority_decision_ref,
                        external_snapshot.budget_reservation_ref,
                        external_snapshot.budget_settlement_ref,
                    )
                )
                or not external_snapshot.evidence_refs
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_SUCCESS_KERNEL_PROOF_REQUIRED"
                )
            if external_snapshot.state == ExternalActionState.succeeded.value:
                _validate_origin_session_success_evidence(
                    recipe=recipe_snapshot,
                    intent_ref=self.intent_ref,
                    evidence_refs=tuple(external_snapshot.evidence_refs),
                )
            if external_snapshot.replayed:
                expected_status = GovernedBrowserOriginSessionStatus.replayed
            elif external_snapshot.state == ExternalActionState.blocked.value:
                expected_status = GovernedBrowserOriginSessionStatus.blocked
            elif external_snapshot.state == ExternalActionState.failed.value:
                expected_status = GovernedBrowserOriginSessionStatus.failed
            elif (
                external_snapshot.state
                in {
                    ExternalActionState.outcome_ambiguous.value,
                    ExternalActionState.started.value,
                    ExternalActionState.prepared.value,
                }
            ):
                expected_status = GovernedBrowserOriginSessionStatus.outcome_ambiguous
            elif external_snapshot.state == ExternalActionState.succeeded.value:
                assert self.operation is not None
                expected_status = {
                    GovernedBrowserOriginSessionOperation.enroll_credential.value: (
                        GovernedBrowserOriginSessionStatus.credential_stored
                    ),
                    GovernedBrowserOriginSessionOperation.prepare_session.value: (
                        GovernedBrowserOriginSessionStatus.session_prepared
                    ),
                    GovernedBrowserOriginSessionOperation.revalidate_session.value: (
                        GovernedBrowserOriginSessionStatus.session_revalidated
                    ),
                    GovernedBrowserOriginSessionOperation.close_session.value: (
                        GovernedBrowserOriginSessionStatus.session_closed
                    ),
                    GovernedBrowserOriginSessionOperation.revoke_credential.value: (
                        GovernedBrowserOriginSessionStatus.credential_revoked
                    ),
                }[self.operation]
            else:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_STATE_INVALID"
                )
            if self.status != expected_status.value:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_EXTERNAL_STATE_MISMATCH"
                )
            if self.replayed:
                require_external_action_replay_provenance(
                    info,
                    lane_ref=_ORIGIN_SESSION_REPLAY_LANE_REF,
                    operation_ref=self.recipe_ref,
                    candidate=external_snapshot,
                )
        validate_safe_task_payload(
            self.model_dump(
                mode="json",
                exclude={
                    "cookies_used": True,
                    "recipe_snapshot": {"cookies_allowed"},
                },
            ),
            "governed_browser_origin_session_receipt",
        )
        return self


class ExactGovernedBrowserOriginSessionResult(BaseModel):
    receipt: GovernedBrowserOriginSessionReceipt
    keychain_receipt: GovernedBrowserKeychainOperationReceipt | None = None
    session: GovernedBrowserOriginSessionRecord | None = None

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_result(self) -> "ExactGovernedBrowserOriginSessionResult":
        status = GovernedBrowserOriginSessionStatus(self.receipt.status)
        successful_statuses = {
            GovernedBrowserOriginSessionStatus.credential_stored,
            GovernedBrowserOriginSessionStatus.session_prepared,
            GovernedBrowserOriginSessionStatus.session_revalidated,
            GovernedBrowserOriginSessionStatus.session_closed,
            GovernedBrowserOriginSessionStatus.credential_revoked,
        }
        if status not in successful_statuses:
            if self.keychain_receipt is not None or self.session is not None:
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_NON_SUCCESS_PROJECTION_DENIED"
                )
            return self

        recipe = self.receipt.recipe_snapshot
        external = self.receipt.external_receipt_snapshot
        assert recipe is not None
        assert external is not None
        operation = GovernedBrowserOriginSessionOperation(recipe.operation)
        expected_keychain_operation = {
            GovernedBrowserOriginSessionOperation.enroll_credential: (
                GovernedBrowserKeychainOperation.store
            ),
            GovernedBrowserOriginSessionOperation.prepare_session: (
                GovernedBrowserKeychainOperation.probe
            ),
            GovernedBrowserOriginSessionOperation.revalidate_session: (
                GovernedBrowserKeychainOperation.probe
            ),
            GovernedBrowserOriginSessionOperation.close_session: None,
            GovernedBrowserOriginSessionOperation.revoke_credential: (
                GovernedBrowserKeychainOperation.delete
            ),
        }[operation]
        session_required = operation in {
            GovernedBrowserOriginSessionOperation.prepare_session,
            GovernedBrowserOriginSessionOperation.revalidate_session,
            GovernedBrowserOriginSessionOperation.close_session,
        }
        session_denied = (
            operation == GovernedBrowserOriginSessionOperation.enroll_credential
        )
        if (
            (self.keychain_receipt is None)
            != (expected_keychain_operation is None)
            or (session_required and self.session is None)
            or (session_denied and self.session is not None)
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_SUCCESS_PROJECTION_REQUIRED"
            )

        evidence_refs = set(external.evidence_refs)
        keychain = self.keychain_receipt
        if keychain is not None:
            if (
                keychain.operation != expected_keychain_operation.value
                or keychain.registration_ref != recipe.registration_ref
                or keychain.origin_ref != recipe.origin_ref
                or keychain.credential_handle_ref != recipe.credential_handle_ref
                or keychain.credential_generation_ref
                != recipe.credential_generation_ref
                or keychain.keychain_item_ref != recipe.keychain_item_ref
                or keychain.helper_receipt_ref not in evidence_refs
                or keychain.keychain_item_ref not in evidence_refs
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_KEYCHAIN_PROJECTION_MISMATCH"
                )

        session = self.session
        if session is not None:
            expected_state = {
                GovernedBrowserOriginSessionOperation.prepare_session: (
                    GovernedBrowserOriginSessionState.prepared_inactive
                ),
                GovernedBrowserOriginSessionOperation.revalidate_session: (
                    GovernedBrowserOriginSessionState.prepared_inactive
                ),
                GovernedBrowserOriginSessionOperation.close_session: (
                    GovernedBrowserOriginSessionState.closed
                ),
                GovernedBrowserOriginSessionOperation.revoke_credential: (
                    GovernedBrowserOriginSessionState.revoked
                ),
            }[operation]
            expected_keychain_present = (
                operation
                != GovernedBrowserOriginSessionOperation.revoke_credential
            )
            if (
                session.session_ref != self.receipt.session_ref
                or session.session_ref != recipe.session_ref
                or session.session_generation_ref != recipe.session_generation_ref
                or session.registration_ref != recipe.registration_ref
                or session.origin_ref != recipe.origin_ref
                or session.credential_handle_ref != recipe.credential_handle_ref
                or session.credential_generation_ref
                != recipe.credential_generation_ref
                or session.keychain_item_ref != recipe.keychain_item_ref
                or session.created_at != recipe.created_at
                or session.expires_at != recipe.expires_at
                or session.state != expected_state.value
                or session.keychain_item_present != expected_keychain_present
                or session.state_receipt_ref not in evidence_refs
            ):
                raise ValueError(
                    "GOVERNED_BROWSER_ORIGIN_SESSION_RECORD_PROJECTION_MISMATCH"
                )
        return self


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
        self._keychain_store = keychain.store
        self._keychain_probe = keychain.probe
        self._keychain_delete = keychain.delete
        self._session_prepare = sessions.prepare
        self._session_revalidate = sessions.revalidate
        self._session_close = sessions.close
        self._session_mark_revoked = sessions.mark_revoked
        _register_operation_proof_service(
            self,
            dependencies=(
                ("_registry", registry),
                ("_kernel", kernel),
                ("_keychain", keychain),
                ("_sessions", sessions),
                ("_clock", clock),
                ("_keychain_store", self._keychain_store),
                ("_keychain_probe", self._keychain_probe),
                ("_keychain_delete", self._keychain_delete),
                ("_session_prepare", self._session_prepare),
                ("_session_revalidate", self._session_revalidate),
                ("_session_close", self._session_close),
                ("_session_mark_revoked", self._session_mark_revoked),
            ),
        )

    def execute(
        self,
        request: ExactGovernedBrowserOriginSessionRequest,
        *,
        credential_material: bytearray | None = None,
    ) -> ExactGovernedBrowserOriginSessionResult:
        service_binding = _require_operation_proof_service(self)
        dependencies = dict(service_binding.dependencies)
        registry = dependencies["_registry"]
        kernel = dependencies["_kernel"]
        sessions = dependencies["_sessions"]
        clock = dependencies["_clock"]
        keychain_store = dependencies["_keychain_store"]
        keychain_probe = dependencies["_keychain_probe"]
        keychain_delete = dependencies["_keychain_delete"]
        session_prepare = dependencies["_session_prepare"]
        session_revalidate = dependencies["_session_revalidate"]
        session_close = dependencies["_session_close"]
        session_mark_revoked = dependencies["_session_mark_revoked"]
        if (
            type(registry) is not GovernedBrowserOriginSessionRecipeRegistry
            or type(sessions) is not GovernedBrowserOriginSessionStore
            or not callable(clock)
        ):
            _zeroize_optional(credential_material)
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_SERVICE_BINDING_INVALID"
            )
        _exact_origin_session_store_binding(sessions)
        try:
            request = ExactGovernedBrowserOriginSessionRequest.model_validate(
                request.model_dump(mode="json")
            )
        except Exception:
            _zeroize_optional(credential_material)
            raise
        execution = request.execution_request
        resolved = GovernedBrowserOriginSessionRecipeRegistry.resolve(
            registry,
            request.recipe_ref,
        )
        if resolved is None:
            _zeroize_optional(credential_material)
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-origin-session:recipe-unregistered",
            )
        recipe, registration = resolved
        recipe = GovernedBrowserOriginSessionRecipe.model_validate(
            GovernedBrowserOriginSessionRecipe.model_dump(
                recipe,
                mode="json",
            )
        )
        registration = GovernedBrowserCredentialRegistration.model_validate(
            GovernedBrowserCredentialRegistration.model_dump(
                registration,
                mode="json",
            )
        )
        scope_reason = _recipe_scope_reason(recipe, registration, execution)
        if scope_reason is not None:
            _zeroize_optional(credential_material)
            return _preflight_blocked(request, scope_reason, recipe=recipe)
        operation = GovernedBrowserOriginSessionOperation(recipe.operation)
        kernel_execution = _origin_session_kernel_execution(
            execution,
            recipe=recipe,
        )
        if credential_material is not None and not isinstance(
            credential_material, bytearray
        ):
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-origin-session:"
                "credential-mutable-buffer-required",
                recipe=recipe,
            )
        if (
            operation == GovernedBrowserOriginSessionOperation.prepare_session
            and clock() >= recipe.expires_at
        ):
            _zeroize_optional(credential_material)
            return _preflight_blocked(
                request,
                "reason-ref:governed-browser-origin-session:"
                "prepare-session-expired",
                recipe=recipe,
            )
        if operation == GovernedBrowserOriginSessionOperation.enroll_credential:
            if credential_material is None:
                return _preflight_blocked(
                    request,
                    "reason-ref:governed-browser-origin-session:"
                    "credential-material-required",
                    recipe=recipe,
                )
            if not (
                GOVERNED_BROWSER_CREDENTIAL_MIN_BYTES
                <= len(credential_material)
                <= GOVERNED_BROWSER_CREDENTIAL_MAX_BYTES
            ):
                _zeroize_optional(credential_material)
                return _preflight_blocked(
                    request,
                    "reason-ref:governed-browser-origin-session:"
                    "credential-length-invalid",
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
        try:
            owned_credential_material = (
                bytearray(credential_material)
                if operation
                == GovernedBrowserOriginSessionOperation.enroll_credential
                and credential_material is not None
                else None
            )
        except BaseException:
            _zeroize_optional(credential_material)
            raise
        credential_handoff_lock = RLock()
        credential_handoff_claimed = False
        credential_handoff_closed = False

        def proved_dispatch_result(
            result: ExternalActionDispatchResult,
            *,
            material: OriginSessionOperationProofMaterial,
        ) -> ExternalActionDispatchResult:
            base_evidence_refs = tuple(result.evidence_refs)
            proof = _record_operation_proof(
                kernel,
                expected_execution=kernel_execution,
                lane_ref=_ORIGIN_SESSION_REPLAY_LANE_REF,
                operation_ref=recipe.recipe_ref,
                scope_refs=_origin_session_replay_scope_refs(recipe),
                dispatch_outcome=ExternalActionDispatchOutcome(
                    result.outcome
                ).value,
                base_evidence_refs=base_evidence_refs,
                material=material,
            )
            return ExternalActionDispatchResult.model_validate(
                {
                    **ExternalActionDispatchResult.model_dump(
                        result,
                        mode="json",
                    ),
                    "evidence_refs": (*base_evidence_refs, proof.proof_ref),
                }
            )

        def perform_dispatch(
            item: ExternalActionExecutionRequest,
            dispatch_credential_material: bytearray | None,
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
                    assert dispatch_credential_material is not None
                    captured_keychain = keychain_store(
                        registration,
                        request_ref=request_ref,
                        credential_material=dispatch_credential_material,
                    )
                    captured_keychain = _validate_origin_keychain_receipt(
                        captured_keychain,
                        registration=registration,
                        operation=GovernedBrowserKeychainOperation.store,
                        request_ref=request_ref,
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.prepare_session
                ):
                    captured_keychain = keychain_probe(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_keychain = _validate_origin_keychain_receipt(
                        captured_keychain,
                        registration=registration,
                        operation=GovernedBrowserKeychainOperation.probe,
                        request_ref=request_ref,
                    )
                    captured_session = session_prepare(
                        recipe,
                        operation_ref=operation_ref,
                        now=clock(),
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.revalidate_session
                ):
                    captured_keychain = keychain_probe(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_keychain = _validate_origin_keychain_receipt(
                        captured_keychain,
                        registration=registration,
                        operation=GovernedBrowserKeychainOperation.probe,
                        request_ref=request_ref,
                    )
                    captured_session = session_revalidate(
                        recipe,
                        operation_ref=operation_ref,
                        now=clock(),
                    )
                elif (
                    operation
                    == GovernedBrowserOriginSessionOperation.close_session
                ):
                    captured_session = session_close(
                        recipe,
                        operation_ref=operation_ref,
                        now=clock(),
                    )
                else:
                    captured_keychain = keychain_delete(
                        registration,
                        request_ref=request_ref,
                    )
                    captured_keychain = _validate_origin_keychain_receipt(
                        captured_keychain,
                        registration=registration,
                        operation=GovernedBrowserKeychainOperation.delete,
                        request_ref=request_ref,
                    )
                    captured_session = session_mark_revoked(
                        recipe,
                        operation_ref=operation_ref,
                        now=clock(),
                    )
            except GovernedBrowserKeychainError as exc:
                if str(exc) not in _NON_MUTATING_KEYCHAIN_ERROR_CODES:
                    raise
                failure_ref = stable_governed_browser_ref(
                    "evidence-ref:governed-browser-origin-session:"
                    "keychain-precondition-failed",
                    {
                        "operation_ref": operation_ref,
                        "reason_code": str(exc),
                    },
                )
                return proved_dispatch_result(
                    ExternalActionDispatchResult(
                        outcome=ExternalActionDispatchOutcome.failed,
                        evidence_refs=[failure_ref],
                        verified=False,
                    ),
                    material=OriginSessionOperationProofMaterial(
                        operation=operation.value,
                        disposition="keychain_precondition_failed",
                        request_ref=request_ref,
                    ),
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
                conflict_outcome = (
                    ExternalActionDispatchOutcome.outcome_ambiguous
                    if operation
                    == GovernedBrowserOriginSessionOperation.revoke_credential
                    and captured_keychain is not None
                    else ExternalActionDispatchOutcome.failed
                )
                return proved_dispatch_result(
                    ExternalActionDispatchResult(
                        outcome=conflict_outcome,
                        evidence_refs=conflict_evidence_refs,
                        verified=False,
                    ),
                    material=OriginSessionOperationProofMaterial(
                        operation=operation.value,
                        disposition=(
                            "revoke_state_conflict_ambiguous"
                            if conflict_outcome
                            == ExternalActionDispatchOutcome.outcome_ambiguous
                            else "state_conflict_failed"
                        ),
                        request_ref=request_ref,
                        keychain_receipt=captured_keychain,
                    ),
                )
            if (
                operation
                == GovernedBrowserOriginSessionOperation.revalidate_session
                and captured_session is not None
                and captured_session.state
                == GovernedBrowserOriginSessionState.expired.value
            ):
                assert captured_keychain is not None
                return proved_dispatch_result(
                    ExternalActionDispatchResult(
                        outcome=ExternalActionDispatchOutcome.failed,
                        evidence_refs=[
                            operation_ref,
                            captured_keychain.helper_receipt_ref,
                            captured_keychain.keychain_item_ref,
                            captured_session.state_receipt_ref,
                        ],
                        verified=False,
                    ),
                    material=OriginSessionOperationProofMaterial(
                        operation=operation.value,
                        disposition="expired_revalidation_failed",
                        request_ref=request_ref,
                        keychain_receipt=captured_keychain,
                        session_state_receipt_ref=(
                            captured_session.state_receipt_ref
                        ),
                    ),
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
            return proved_dispatch_result(
                ExternalActionDispatchResult(
                    outcome=ExternalActionDispatchOutcome.succeeded,
                    evidence_refs=list(dict.fromkeys(evidence_refs)),
                    verified=True,
                ),
                material=OriginSessionOperationProofMaterial(
                    operation=operation.value,
                    disposition="succeeded",
                    request_ref=request_ref,
                    keychain_receipt=captured_keychain,
                    session_state_receipt_ref=(
                        captured_session.state_receipt_ref
                        if captured_session is not None
                        else None
                    ),
                ),
            )

        def dispatch(
            item: ExternalActionExecutionRequest,
        ) -> ExternalActionDispatchResult:
            nonlocal credential_handoff_claimed
            dispatch_credential_material: bytearray | None = None
            if owned_credential_material is not None:
                with credential_handoff_lock:
                    if credential_handoff_closed:
                        raise RuntimeError(
                            "GOVERNED_BROWSER_CREDENTIAL_HANDOFF_CLOSED"
                        )
                    credential_handoff_claimed = True
                    dispatch_credential_material = owned_credential_material
            try:
                return perform_dispatch(item, dispatch_credential_material)
            finally:
                _zeroize_optional(dispatch_credential_material)

        try:
            external_receipt = GovernedExternalActionKernel.execute(
                kernel,
                kernel_execution,
                dispatch=dispatch,
            )
        finally:
            _zeroize_optional(credential_material)
            with credential_handoff_lock:
                if not credential_handoff_claimed:
                    credential_handoff_closed = True
                    _zeroize_optional(owned_credential_material)
        return _result_from_external_receipt(
            request=request,
            recipe=recipe,
            external_receipt=external_receipt,
            keychain_receipt=captured_keychain,
            session=captured_session,
            validation_context=(
                _origin_session_replay_context(
                    kernel,
                    expected_execution=kernel_execution,
                    recipe=recipe,
                    replay_receipt=external_receipt,
                )
                if external_receipt.replayed
                else None
            ),
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


def _validate_origin_keychain_receipt(
    receipt: GovernedBrowserKeychainOperationReceipt,
    *,
    registration: GovernedBrowserCredentialRegistration,
    operation: GovernedBrowserKeychainOperation,
    request_ref: str,
) -> GovernedBrowserKeychainOperationReceipt:
    exact = GovernedBrowserKeychainOperationReceipt.model_validate(
        GovernedBrowserKeychainOperationReceipt.model_dump(
            receipt,
            mode="json",
        )
    )
    observed = (
        exact.operation,
        exact.registration_ref,
        exact.origin_ref,
        exact.credential_handle_ref,
        exact.credential_generation_ref,
        exact.keychain_item_ref,
        exact.helper_receipt_ref,
    )
    expected = (
        operation.value,
        registration.registration_ref,
        registration.origin_ref,
        registration.credential_handle_ref,
        registration.credential_generation_ref,
        registration.keychain_item_ref,
        governed_browser_keychain_helper_receipt_ref(
            operation=operation,
            request_ref=request_ref,
        ),
    )
    if observed != expected:
        raise GovernedBrowserKeychainError(
            "GOVERNED_BROWSER_KEYCHAIN_HELPER_RECEIPT_MISMATCH"
        )
    return exact


def _origin_session_replay_scope_refs(
    recipe: GovernedBrowserOriginSessionRecipe,
) -> tuple[str, ...]:
    return (
        recipe.binding_ref,
        recipe.registration_ref,
        recipe.origin_ref,
        recipe.page_snapshot_ref,
        recipe.credential_handle_ref,
        recipe.credential_generation_ref,
        recipe.keychain_item_ref,
        recipe.session_ref,
        recipe.session_generation_ref,
        recipe.operation_authority_ref,
    )


def _validate_origin_session_operation_proof(
    proof: GovernedBrowserOperationProof,
    *,
    recipe: GovernedBrowserOriginSessionRecipe,
    expected_execution: ExternalActionExecutionRequest,
    base_evidence_refs: tuple[str, ...],
) -> None:
    material = proof.material
    if not isinstance(material, OriginSessionOperationProofMaterial):
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_KIND_MISMATCH"
        )
    operation = GovernedBrowserOriginSessionOperation(recipe.operation)
    if material.operation != operation.value:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_SCOPE_MISMATCH"
        )
    operation_ref = stable_governed_browser_ref(
        "browser-origin-session-operation-ref:governed-browser",
        {
            "recipe_ref": recipe.recipe_ref,
            "intent_ref": expected_execution.intent_ref,
        },
    )
    request_ref = stable_governed_browser_ref(
        "request-ref:governed-browser-keychain",
        {
            "operation_ref": operation_ref,
            "transaction_ref": expected_execution.binding.transaction_ref,
        },
    )
    if material.request_ref != request_ref:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_REQUEST_MISMATCH"
        )
    expected_keychain_operation = {
        GovernedBrowserOriginSessionOperation.enroll_credential: (
            GovernedBrowserKeychainOperation.store
        ),
        GovernedBrowserOriginSessionOperation.prepare_session: (
            GovernedBrowserKeychainOperation.probe
        ),
        GovernedBrowserOriginSessionOperation.revalidate_session: (
            GovernedBrowserKeychainOperation.probe
        ),
        GovernedBrowserOriginSessionOperation.close_session: None,
        GovernedBrowserOriginSessionOperation.revoke_credential: (
            GovernedBrowserKeychainOperation.delete
        ),
    }[operation]
    keychain = material.keychain_receipt
    if keychain is not None:
        if expected_keychain_operation is None:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_KEYCHAIN_DENIED"
            )
        registration = GovernedBrowserCredentialRegistration(
            registration_ref=recipe.registration_ref,
            origin_ref=recipe.origin_ref,
            credential_handle_ref=recipe.credential_handle_ref,
            credential_generation_ref=recipe.credential_generation_ref,
            keychain_item_ref=recipe.keychain_item_ref,
        )
        _validate_origin_keychain_receipt(
            keychain,
            registration=registration,
            operation=expected_keychain_operation,
            request_ref=request_ref,
        )
    session_state_ref = material.session_state_receipt_ref
    if session_state_ref is not None and session_state_ref not in base_evidence_refs:
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_STATE_MISMATCH"
        )

    conflict_ref = stable_governed_browser_ref(
        "evidence-ref:governed-browser-origin-session:state-conflict",
        {"operation_ref": operation_ref},
    )
    keychain_refs = (
        (
            keychain.helper_receipt_ref,
            keychain.keychain_item_ref,
        )
        if keychain is not None
        else ()
    )
    if material.disposition == "succeeded":
        expected_evidence = [operation_ref, *keychain_refs]
        if session_state_ref is not None:
            expected_evidence.append(session_state_ref)
        expected_outcome = ExternalActionDispatchOutcome.succeeded.value
    elif material.disposition == "keychain_precondition_failed":
        if keychain is not None or session_state_ref is not None:
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_FAILURE_INVALID"
            )
        expected_failure_refs = {
            stable_governed_browser_ref(
                "evidence-ref:governed-browser-origin-session:"
                "keychain-precondition-failed",
                {
                    "operation_ref": operation_ref,
                    "reason_code": reason_code,
                },
            )
            for reason_code in _NON_MUTATING_KEYCHAIN_ERROR_CODES
        }
        if (
            len(base_evidence_refs) != 1
            or base_evidence_refs[0] not in expected_failure_refs
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_FAILURE_INVALID"
            )
        expected_evidence = list(base_evidence_refs)
        expected_outcome = ExternalActionDispatchOutcome.failed.value
    elif material.disposition == "state_conflict_failed":
        expected_evidence = [conflict_ref, *keychain_refs]
        expected_outcome = ExternalActionDispatchOutcome.failed.value
    elif material.disposition == "revoke_state_conflict_ambiguous":
        if (
            operation
            != GovernedBrowserOriginSessionOperation.revoke_credential
            or keychain is None
            or session_state_ref is not None
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_AMBIGUITY_INVALID"
            )
        expected_evidence = [conflict_ref, *keychain_refs]
        expected_outcome = (
            ExternalActionDispatchOutcome.outcome_ambiguous.value
        )
    else:
        if (
            operation
            != GovernedBrowserOriginSessionOperation.revalidate_session
            or keychain is None
            or session_state_ref is None
        ):
            raise ValueError(
                "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_EXPIRY_INVALID"
            )
        expected_evidence = [
            operation_ref,
            *keychain_refs,
            session_state_ref,
        ]
        expected_outcome = ExternalActionDispatchOutcome.failed.value
    if (
        tuple(expected_evidence) != base_evidence_refs
        or proof.dispatch_outcome != expected_outcome
    ):
        raise ValueError(
            "GOVERNED_BROWSER_ORIGIN_SESSION_OPERATION_PROOF_EVIDENCE_MISMATCH"
        )


def _recipe_scope_reason(
    recipe: GovernedBrowserOriginSessionRecipe,
    registration: GovernedBrowserCredentialRegistration,
    request: ExternalActionExecutionRequest,
) -> str | None:
    binding = request.binding
    required_resources = {
        recipe.operation_authority_ref,
        registration.registration_ref,
        registration.credential_handle_ref,
        registration.credential_generation_ref,
        registration.keychain_item_ref,
        recipe.session_ref,
        recipe.session_generation_ref,
    }
    bound_operation_refs = tuple(
        ref
        for ref in binding.resource_refs
        if ref.startswith(
            "browser-origin-session-operation-authority-ref:"
            "governed-browser:"
        )
    )
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
            bound_operation_refs == (recipe.operation_authority_ref,),
            "reason-ref:governed-browser-origin-session:"
            "operation-authority-mismatch",
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
    validation_context: ExternalActionReplayValidationContext | None = None,
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
    elif external_receipt.state in {
        ExternalActionState.outcome_ambiguous.value,
        ExternalActionState.started.value,
        ExternalActionState.prepared.value,
    }:
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
        recipe_snapshot=recipe,
        external_receipt=external_receipt,
        reason_refs=tuple(external_receipt.reason_refs),
        validation_context=validation_context,
    )
    if validation_context is not None:
        return ExactGovernedBrowserOriginSessionResult.model_validate(
            {
                "receipt": receipt.model_dump(mode="json"),
                "keychain_receipt": keychain_receipt,
                "session": session,
            },
            context=replay_validation_context(validation_context),
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
    recipe_snapshot: GovernedBrowserOriginSessionRecipe | None = None,
    external_receipt: ExternalActionReceipt | None = None,
    validation_context: ExternalActionReplayValidationContext | None = None,
) -> GovernedBrowserOriginSessionReceipt:
    payload = {
        "status": status,
        "operation": operation,
        "recipe_ref": recipe_ref,
        "transaction_ref": execution.binding.transaction_ref,
        "intent_ref": execution.intent_ref,
        "session_ref": session_ref,
        "recipe_snapshot": recipe_snapshot,
        "external_action_receipt_ref": (
            external_receipt.receipt_ref if external_receipt is not None else None
        ),
        "external_receipt_snapshot": external_receipt,
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
        "budget_release_ref": (
            external_receipt.budget_release_ref
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
        _origin_session_receipt_identity_payload(provisional),
    )
    receipt_payload = {
        "receipt_ref": receipt_ref,
        **payload,
    }
    return (
        GovernedBrowserOriginSessionReceipt.model_validate(
            receipt_payload,
            context=replay_validation_context(validation_context),
        )
        if validation_context is not None
        else GovernedBrowserOriginSessionReceipt(**receipt_payload)
    )


def _origin_session_replay_context(
    kernel: GovernedExternalActionKernel,
    *,
    expected_execution: ExternalActionExecutionRequest,
    recipe: GovernedBrowserOriginSessionRecipe,
    replay_receipt: ExternalActionReceipt,
) -> ExternalActionReplayValidationContext:
    evidence_refs = tuple(replay_receipt.evidence_refs)
    base_evidence_refs, operation_proof_ref = (
        _split_origin_session_operation_proof(evidence_refs)
    )
    proof: GovernedBrowserOperationProof | None = None
    if operation_proof_ref is not None:
        try:
            proof = _attest_operation_proof(
                kernel,
                expected_execution=expected_execution,
                proof_ref=operation_proof_ref,
                lane_ref=_ORIGIN_SESSION_REPLAY_LANE_REF,
                operation_ref=recipe.recipe_ref,
                scope_refs=_origin_session_replay_scope_refs(recipe),
                base_evidence_refs=base_evidence_refs,
            )
            _validate_origin_session_operation_proof(
                proof,
                recipe=recipe,
                expected_execution=expected_execution,
                base_evidence_refs=base_evidence_refs,
            )
        except (GovernedBrowserOperationProofError, ValueError):
            proof = None
    try:
        _validate_origin_session_success_evidence(
            recipe=recipe,
            intent_ref=expected_execution.intent_ref,
            evidence_refs=evidence_refs,
        )
        success_evidence_valid = (
            proof is not None
            and proof.dispatch_outcome
            == ExternalActionDispatchOutcome.succeeded.value
        )
    except ValueError:
        success_evidence_valid = False
    failure_evidence_valid = (
        proof is not None
        and proof.dispatch_outcome
        == ExternalActionDispatchOutcome.failed.value
    )
    operation_ambiguity_evidence_valid = (
        proof is not None
        and proof.dispatch_outcome
        == ExternalActionDispatchOutcome.outcome_ambiguous.value
    )
    _require_operation_replay_evidence_envelope(
        replay_receipt,
        success_evidence_valid=success_evidence_valid,
        failure_evidence_valid=failure_evidence_valid,
        operation_ambiguity_evidence_valid=(
            operation_ambiguity_evidence_valid
        ),
        mismatch_error=(
            "GOVERNED_BROWSER_ORIGIN_SESSION_REPLAY_EVIDENCE_ENVELOPE_MISMATCH"
        ),
    )
    return _build_external_action_replay_validation_context(
        kernel,
        expected_execution=expected_execution,
        replay_receipt=replay_receipt,
        expectation=ExternalActionReplayEvidenceExpectation(
            lane_ref=_ORIGIN_SESSION_REPLAY_LANE_REF,
            operation_ref=recipe.recipe_ref,
            scope_refs=_origin_session_replay_scope_refs(recipe),
            evidence_refs=evidence_refs,
            operation_proof_ref=operation_proof_ref,
        ),
    )


def _origin_session_kernel_execution(
    request: ExternalActionExecutionRequest,
    *,
    recipe: GovernedBrowserOriginSessionRecipe,
) -> ExternalActionExecutionRequest:
    return ExternalActionExecutionRequest.model_validate(
        {
            **request.model_dump(mode="json"),
            "idempotency_ref": stable_governed_browser_ref(
                "idempotency-ref:governed-browser-origin-session",
                {
                    "source_idempotency_ref": request.idempotency_ref,
                    "recipe_ref": recipe.recipe_ref,
                    "operation": recipe.operation,
                    "operation_authority_ref": recipe.operation_authority_ref,
                },
            ),
        }
    )


def _zeroize_optional(value: object | None) -> None:
    if not isinstance(value, bytearray):
        return
    for index in range(len(value)):
        value[index] = 0
