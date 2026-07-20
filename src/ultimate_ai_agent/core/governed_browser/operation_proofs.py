"""Durable content-free proof for operation-specific browser dispatch evidence.

The external-action transaction ledger proves which terminal receipt was
durably committed.  This module independently proves the meaning of dynamic
evidence produced inside an exact governed-browser dispatch.  A proof is
written before the dispatch result is returned and its immutable ``proof_ref``
is appended to the kernel evidence tuple.  Replay therefore requires both the
exact terminal kernel row and the exact independently stored operation proof.

The store contains safe refs and typed boolean projections only.  It grants no
browser, network, credential, mutation, or execution authority.
"""

from __future__ import annotations

import fcntl
import hashlib
import os
import stat
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal, Union
from weakref import WeakKeyDictionary

from pydantic import BaseModel, ConfigDict, Field, model_validator

from ultimate_ai_agent.core.planning.validation import (
    validate_safe_task_payload,
    validate_task_ref,
)

from .browser_keychain import GovernedBrowserKeychainOperationReceipt
from .contracts import (
    ExternalActionExecutionRequest,
    ExternalActionReceipt,
    ExternalActionState,
    stable_governed_browser_ref,
)


MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES = 32 * 1024
MAX_GOVERNED_BROWSER_OPERATION_PROOFS = 4096
MAX_GOVERNED_BROWSER_TERMINAL_BINDING_BYTES = 32 * 1024
MAX_GOVERNED_BROWSER_TERMINAL_BINDINGS = 4096
_OPERATION_PROOF_REF_PREFIX = (
    "operation-proof-ref:governed-browser:sha256:"
)
_TERMINAL_BINDING_REF_PREFIX = (
    "terminal-binding-ref:governed-browser:sha256:"
)
_REQUEST_FINGERPRINT_REF_PREFIX = (
    "request-fingerprint-ref:governed-external-action:sha256:"
)
_OBSERVATION_LANE_REF = "replay-lane-ref:governed-browser-observation:v1"
_ACTION_LANE_REF = "replay-lane-ref:governed-browser-action:v1"
_POST_FORM_LANE_REF = "replay-lane-ref:governed-browser-post-form:v1"
_ORIGIN_SESSION_LANE_REF = "lane-ref:governed-browser-origin-session"


class GovernedBrowserOperationProofError(RuntimeError):
    """A dispatch proof could not be durably recorded or exactly attested."""


class BrowserObservationOperationProofMaterial(BaseModel):
    kind: Literal["browser_observation"] = "browser_observation"
    evidence_ref: str
    profile_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_material(self) -> "BrowserObservationOperationProofMaterial":
        validate_task_ref(self.evidence_ref, "operation_proof_evidence_ref")
        validate_task_ref(self.profile_ref, "operation_proof_profile_ref")
        return self


class BrowserActionPlanOperationProofMaterial(BaseModel):
    kind: Literal["browser_action_plan"] = "browser_action_plan"
    plan_ref: str
    projection_ref: str
    profile_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_material(self) -> "BrowserActionPlanOperationProofMaterial":
        for value, label in (
            (self.plan_ref, "operation_proof_plan_ref"),
            (self.projection_ref, "operation_proof_projection_ref"),
            (self.profile_ref, "operation_proof_profile_ref"),
        ):
            validate_task_ref(value, label)
        return self


class PostFormPlanOperationProofMaterial(BaseModel):
    kind: Literal["post_form_plan"] = "post_form_plan"
    plan_ref: str
    projection_ref: str
    profile_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_material(self) -> "PostFormPlanOperationProofMaterial":
        for value, label in (
            (self.plan_ref, "operation_proof_plan_ref"),
            (self.projection_ref, "operation_proof_projection_ref"),
            (self.profile_ref, "operation_proof_profile_ref"),
        ):
            validate_task_ref(value, label)
        return self


class GovernedBrowserDispatchFailureProofMaterial(BaseModel):
    kind: Literal["dispatch_failure"] = "dispatch_failure"
    failure_ref: str

    model_config = ConfigDict(extra="forbid", frozen=True, hide_input_in_errors=True)

    @model_validator(mode="after")
    def validate_material(self) -> "GovernedBrowserDispatchFailureProofMaterial":
        validate_task_ref(self.failure_ref, "operation_proof_failure_ref")
        return self


class OriginSessionOperationProofMaterial(BaseModel):
    kind: Literal["origin_session"] = "origin_session"
    operation: Literal[
        "enroll_credential",
        "prepare_session",
        "revalidate_session",
        "close_session",
        "revoke_credential",
    ]
    disposition: Literal[
        "succeeded",
        "keychain_precondition_failed",
        "state_conflict_failed",
        "revoke_state_conflict_ambiguous",
        "expired_revalidation_failed",
    ]
    request_ref: str
    keychain_receipt: GovernedBrowserKeychainOperationReceipt | None = None
    session_state_receipt_ref: str | None = None

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_material(self) -> "OriginSessionOperationProofMaterial":
        validate_task_ref(self.request_ref, "operation_proof_request_ref")
        if self.session_state_receipt_ref is not None:
            validate_task_ref(
                self.session_state_receipt_ref,
                "operation_proof_session_state_receipt_ref",
            )
        validate_safe_task_payload(
            OriginSessionOperationProofMaterial.model_dump(
                self,
                mode="json",
                exclude={"keychain_receipt": {"cookies_used"}},
            ),
            "governed_browser_origin_session_operation_proof_material",
        )
        return self


GovernedBrowserOperationProofMaterial = Annotated[
    Union[
        BrowserObservationOperationProofMaterial,
        BrowserActionPlanOperationProofMaterial,
        PostFormPlanOperationProofMaterial,
        GovernedBrowserDispatchFailureProofMaterial,
        OriginSessionOperationProofMaterial,
    ],
    Field(discriminator="kind"),
]


class GovernedBrowserOperationProof(BaseModel):
    """Immutable safe-ref proof of one exact dispatch evidence projection."""

    schema_version: Literal["uaa-governed-browser-operation-proof.v1"] = (
        "uaa-governed-browser-operation-proof.v1"
    )
    proof_ref: str
    store_ref: str
    lane_ref: str
    operation_ref: str
    scope_refs: tuple[str, ...] = Field(default_factory=tuple, max_length=12)
    request_fingerprint_ref: str
    transaction_ref: str
    intent_ref: str
    binding_ref: str
    dispatch_outcome: Literal["succeeded", "failed", "outcome_ambiguous"]
    base_evidence_refs: tuple[str, ...] = Field(..., min_length=1, max_length=11)
    material: GovernedBrowserOperationProofMaterial
    content_free: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    credential_material_persisted: Literal[False] = False
    browser_authority_granted: Literal[False] = False
    network_authority_granted: Literal[False] = False
    mutation_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_proof(self) -> "GovernedBrowserOperationProof":
        for value, label in (
            (self.proof_ref, "operation_proof_ref"),
            (self.store_ref, "operation_proof_store_ref"),
            (self.lane_ref, "operation_proof_lane_ref"),
            (self.operation_ref, "operation_proof_operation_ref"),
            *[(value, "operation_proof_scope_ref") for value in self.scope_refs],
            (
                self.request_fingerprint_ref,
                "operation_proof_request_fingerprint_ref",
            ),
            (self.transaction_ref, "operation_proof_transaction_ref"),
            (self.intent_ref, "operation_proof_intent_ref"),
            (self.binding_ref, "operation_proof_binding_ref"),
            *[
                (value, "operation_proof_evidence_ref")
                for value in self.base_evidence_refs
            ],
        ):
            validate_task_ref(value, label)
        if len(self.base_evidence_refs) != len(set(self.base_evidence_refs)):
            raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_EVIDENCE_DUPLICATE")
        material = self.material
        expected_evidence: tuple[str, ...] | None
        if isinstance(material, BrowserObservationOperationProofMaterial):
            if self.lane_ref != _OBSERVATION_LANE_REF:
                raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_LANE_MISMATCH")
            expected_evidence = (material.evidence_ref,)
        elif isinstance(material, BrowserActionPlanOperationProofMaterial):
            if self.lane_ref != _ACTION_LANE_REF:
                raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_LANE_MISMATCH")
            expected_evidence = (material.plan_ref, material.projection_ref)
        elif isinstance(material, PostFormPlanOperationProofMaterial):
            if self.lane_ref != _POST_FORM_LANE_REF:
                raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_LANE_MISMATCH")
            expected_evidence = (material.plan_ref, material.projection_ref)
        elif isinstance(material, GovernedBrowserDispatchFailureProofMaterial):
            if self.dispatch_outcome != "failed":
                raise ValueError(
                    "GOVERNED_BROWSER_OPERATION_PROOF_FAILURE_OUTCOME_MISMATCH"
                )
            expected_evidence = (material.failure_ref,)
        else:
            if self.lane_ref != _ORIGIN_SESSION_LANE_REF:
                raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_LANE_MISMATCH")
            expected_evidence = None
        if isinstance(
            material,
            (
                BrowserObservationOperationProofMaterial,
                BrowserActionPlanOperationProofMaterial,
                PostFormPlanOperationProofMaterial,
            ),
        ) and self.dispatch_outcome != "succeeded":
            raise ValueError(
                "GOVERNED_BROWSER_OPERATION_PROOF_SUCCESS_OUTCOME_MISMATCH"
            )
        if (
            expected_evidence is not None
            and self.base_evidence_refs != expected_evidence
        ):
            raise ValueError(
                "GOVERNED_BROWSER_OPERATION_PROOF_MATERIAL_EVIDENCE_MISMATCH"
            )
        expected_ref = stable_governed_browser_ref(
            "operation-proof-ref:governed-browser",
            GovernedBrowserOperationProof.model_dump(
                self,
                mode="json",
                exclude={"proof_ref"},
            ),
        )
        if self.proof_ref != expected_ref:
            raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_REF_MISMATCH")
        validate_safe_task_payload(
            GovernedBrowserOperationProof.model_dump(
                self,
                mode="json",
                exclude={
                    "material": {
                        "keychain_receipt": {"cookies_used"},
                    }
                },
            ),
            "governed_browser_operation_proof",
        )
        return self


class GovernedBrowserTerminalReceiptBinding(BaseModel):
    """Immutable proof of the exact terminal receipt committed by the kernel."""

    schema_version: Literal[
        "uaa-governed-browser-terminal-receipt-binding.v1"
    ] = "uaa-governed-browser-terminal-receipt-binding.v1"
    terminal_binding_ref: str
    store_ref: str
    request_fingerprint_ref: str
    terminal_receipt: ExternalActionReceipt
    operation_proof_ref: str | None = None
    content_free: Literal[True] = True
    raw_content_persisted: Literal[False] = False
    credential_material_persisted: Literal[False] = False
    browser_authority_granted: Literal[False] = False
    network_authority_granted: Literal[False] = False
    mutation_authority_granted: Literal[False] = False
    execution_authority_granted: Literal[False] = False

    model_config = ConfigDict(
        extra="forbid",
        frozen=True,
        hide_input_in_errors=True,
    )

    @model_validator(mode="after")
    def validate_binding(self) -> "GovernedBrowserTerminalReceiptBinding":
        for value, label in (
            (self.terminal_binding_ref, "terminal_binding_ref"),
            (self.store_ref, "operation_proof_store_ref"),
            (
                self.request_fingerprint_ref,
                "request_fingerprint_ref",
            ),
            *(
                [(self.operation_proof_ref, "operation_proof_ref")]
                if self.operation_proof_ref is not None
                else []
            ),
        ):
            validate_task_ref(value, label)
        if not self.request_fingerprint_ref.startswith(
            _REQUEST_FINGERPRINT_REF_PREFIX
        ):
            raise ValueError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_FINGERPRINT_INVALID"
            )
        terminal = self.terminal_receipt
        if terminal.replayed or terminal.state not in {
            ExternalActionState.blocked.value,
            ExternalActionState.succeeded.value,
            ExternalActionState.failed.value,
            ExternalActionState.outcome_ambiguous.value,
        }:
            raise ValueError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_RECEIPT_INVALID"
            )
        if (
            self.operation_proof_ref
            != _terminal_operation_proof_ref(terminal)
        ):
            raise ValueError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_OPERATION_PROOF_MISMATCH"
            )
        expected_ref = stable_governed_browser_ref(
            "terminal-binding-ref:governed-browser",
            GovernedBrowserTerminalReceiptBinding.model_dump(
                self,
                mode="json",
                exclude={"terminal_binding_ref"},
            ),
        )
        if self.terminal_binding_ref != expected_ref:
            raise ValueError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_REF_MISMATCH"
            )
        validate_safe_task_payload(
            GovernedBrowserTerminalReceiptBinding.model_dump(
                self,
                mode="json",
            ),
            "governed_browser_terminal_receipt_binding",
        )
        return self


@dataclass(frozen=True)
class _OperationProofStoreBinding:
    root: Path
    proof_directory: Path
    terminal_binding_directory: Path
    root_identity: tuple[int, int]
    proof_directory_identity: tuple[int, int]
    terminal_binding_directory_identity: tuple[int, int]
    store_ref: str
    io_lock: RLock


@dataclass(frozen=True)
class _OperationProofServiceBinding:
    service_type: type[object]
    dependencies: tuple[tuple[str, object], ...]
    proof_store: "GovernedBrowserOperationProofStore"


_STORE_BINDINGS: WeakKeyDictionary[
    object,
    _OperationProofStoreBinding,
] = WeakKeyDictionary()
_STORE_BINDINGS_LOCK = RLock()
_KERNEL_PROOF_STORES: WeakKeyDictionary[
    object,
    "GovernedBrowserOperationProofStore",
] = WeakKeyDictionary()
_KERNEL_PROOF_STORES_LOCK = RLock()
_SERVICE_BINDINGS: WeakKeyDictionary[
    object,
    _OperationProofServiceBinding,
] = WeakKeyDictionary()
_SERVICE_BINDINGS_LOCK = RLock()


class GovernedBrowserOperationProofStore:
    """Owner-only immutable store for operation and terminal proofs."""

    def __init__(self, root: Path) -> None:
        exact_root = Path(
            os.path.abspath(os.fspath(root.expanduser()))
        )
        if not exact_root.is_absolute() or exact_root == Path(exact_root.anchor):
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_ROOT_UNSAFE"
            )
        if Path(os.path.realpath(exact_root)) != exact_root:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_ROOT_UNSAFE"
            )
        try:
            initial_root_info = os.lstat(exact_root)
        except FileNotFoundError:
            initial_root_info = None
        if initial_root_info is not None and stat.S_ISLNK(
            initial_root_info.st_mode
        ):
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_ROOT_UNSAFE"
            )
        exact_root.mkdir(mode=0o700, parents=True, exist_ok=True)
        proof_directory = exact_root / "proofs"
        proof_directory.mkdir(mode=0o700, exist_ok=True)
        terminal_binding_directory = exact_root / "terminal-bindings"
        terminal_binding_directory.mkdir(mode=0o700, exist_ok=True)
        root_info = os.lstat(exact_root)
        proof_info = os.lstat(proof_directory)
        terminal_binding_info = os.lstat(terminal_binding_directory)
        for info in (root_info, proof_info, terminal_binding_info):
            if (
                not stat.S_ISDIR(info.st_mode)
                or stat.S_ISLNK(info.st_mode)
                or info.st_uid != os.geteuid()
                or info.st_mode & 0o077
            ):
                raise GovernedBrowserOperationProofError(
                    "GOVERNED_BROWSER_OPERATION_PROOF_ROOT_UNSAFE"
                )
        path_fingerprint = hashlib.sha256(
            os.fspath(exact_root).encode("utf-8")
        ).hexdigest()
        store_ref = stable_governed_browser_ref(
            "operation-proof-store-ref:governed-browser",
            {
                "path_fingerprint": path_fingerprint,
                "root_identity": (root_info.st_dev, root_info.st_ino),
                "proof_directory_identity": (
                    proof_info.st_dev,
                    proof_info.st_ino,
                ),
                "terminal_binding_directory_identity": (
                    terminal_binding_info.st_dev,
                    terminal_binding_info.st_ino,
                ),
            },
        )
        self.root = exact_root
        self.proof_directory = proof_directory
        self.terminal_binding_directory = terminal_binding_directory
        self.store_ref = store_ref
        binding = _OperationProofStoreBinding(
            root=exact_root,
            proof_directory=proof_directory,
            terminal_binding_directory=terminal_binding_directory,
            root_identity=(root_info.st_dev, root_info.st_ino),
            proof_directory_identity=(proof_info.st_dev, proof_info.st_ino),
            terminal_binding_directory_identity=(
                terminal_binding_info.st_dev,
                terminal_binding_info.st_ino,
            ),
            store_ref=store_ref,
            io_lock=RLock(),
        )
        with _STORE_BINDINGS_LOCK:
            _STORE_BINDINGS[self] = binding

    def save(
        self,
        proof: GovernedBrowserOperationProof,
    ) -> GovernedBrowserOperationProof:
        exact = GovernedBrowserOperationProof.model_validate(
            GovernedBrowserOperationProof.model_dump(proof, mode="json")
        )
        binding = _exact_store_binding(self)
        if exact.store_ref != binding.store_ref:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_STORE_MISMATCH"
            )
        payload = (
            GovernedBrowserOperationProof.model_dump_json(exact) + "\n"
        ).encode("utf-8")
        if len(payload) > MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_TOO_LARGE"
            )
        directory_fd = _open_proof_directory(self)
        filename = _proof_filename(exact.proof_ref)
        descriptor: int | None = None
        try:
            with binding.io_lock:
                fcntl.flock(directory_fd, fcntl.LOCK_EX)
                try:
                    try:
                        descriptor = os.open(
                            filename,
                            os.O_WRONLY
                            | os.O_CREAT
                            | os.O_EXCL
                            | getattr(os, "O_CLOEXEC", 0)
                            | getattr(os, "O_NOFOLLOW", 0),
                            0o600,
                            dir_fd=directory_fd,
                        )
                    except FileExistsError:
                        existing = GovernedBrowserOperationProofStore.load(
                            self,
                            proof_ref=exact.proof_ref,
                        )
                        if existing != exact:
                            raise GovernedBrowserOperationProofError(
                                "GOVERNED_BROWSER_OPERATION_PROOF_CONFLICT"
                            )
                        return existing
                    if _proof_file_count(directory_fd) > (
                        MAX_GOVERNED_BROWSER_OPERATION_PROOFS
                    ):
                        os.unlink(filename, dir_fd=directory_fd)
                        os.close(descriptor)
                        descriptor = None
                        os.fsync(directory_fd)
                        raise GovernedBrowserOperationProofError(
                            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_FULL"
                        )
                    _write_all(descriptor, payload)
                    os.fsync(descriptor)
                    info = os.fstat(descriptor)
                    if (
                        not stat.S_ISREG(info.st_mode)
                        or info.st_uid != os.geteuid()
                        or info.st_nlink != 1
                        or info.st_mode & 0o077
                        or info.st_size != len(payload)
                    ):
                        raise OSError("unsafe operation proof")
                    os.fsync(directory_fd)
                finally:
                    fcntl.flock(directory_fd, fcntl.LOCK_UN)
        except GovernedBrowserOperationProofError:
            if descriptor is not None:
                try:
                    os.unlink(filename, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                except OSError:
                    pass
            raise
        except OSError as exc:
            if descriptor is not None:
                try:
                    os.unlink(filename, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                except OSError:
                    pass
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_WRITE_FAILED"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory_fd)
        return GovernedBrowserOperationProofStore.load(
            self,
            proof_ref=exact.proof_ref,
        )

    def load(self, *, proof_ref: str) -> GovernedBrowserOperationProof:
        validate_task_ref(proof_ref, "operation_proof_ref")
        if not proof_ref.startswith(_OPERATION_PROOF_REF_PREFIX):
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_REF_REQUIRED"
            )
        binding = _exact_store_binding(self)
        directory_fd = _open_proof_directory(self)
        descriptor: int | None = None
        try:
            filename = _proof_filename(proof_ref)
            try:
                descriptor = os.open(
                    filename,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=directory_fd,
                )
                info = os.fstat(descriptor)
                path_info = os.stat(
                    filename,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.geteuid()
                    or info.st_nlink != 1
                    or info.st_mode & 0o077
                    or info.st_size
                    > MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES
                    or (info.st_dev, info.st_ino)
                    != (path_info.st_dev, path_info.st_ino)
                ):
                    raise OSError("unsafe operation proof")
                payload = _read_bounded(
                    descriptor,
                    max_bytes=MAX_GOVERNED_BROWSER_OPERATION_PROOF_BYTES,
                )
            except OSError as exc:
                raise GovernedBrowserOperationProofError(
                    "GOVERNED_BROWSER_OPERATION_PROOF_REQUIRED"
                ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory_fd)
        try:
            proof = GovernedBrowserOperationProof.model_validate_json(payload)
        except Exception as exc:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_INVALID"
            ) from exc
        if proof.proof_ref != proof_ref or proof.store_ref != binding.store_ref:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_SCOPE_MISMATCH"
            )
        return proof

    def save_terminal_binding(
        self,
        terminal_binding: GovernedBrowserTerminalReceiptBinding,
    ) -> GovernedBrowserTerminalReceiptBinding:
        exact = GovernedBrowserTerminalReceiptBinding.model_validate(
            GovernedBrowserTerminalReceiptBinding.model_dump(
                terminal_binding,
                mode="json",
            )
        )
        binding = _exact_store_binding(self)
        if exact.store_ref != binding.store_ref:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_STORE_MISMATCH"
            )
        payload = (
            GovernedBrowserTerminalReceiptBinding.model_dump_json(exact) + "\n"
        ).encode("utf-8")
        if len(payload) > MAX_GOVERNED_BROWSER_TERMINAL_BINDING_BYTES:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_TOO_LARGE"
            )
        directory_fd = _open_terminal_binding_directory(self)
        filename = _terminal_binding_filename(
            exact.terminal_receipt.receipt_ref
        )
        descriptor: int | None = None
        try:
            with binding.io_lock:
                fcntl.flock(directory_fd, fcntl.LOCK_EX)
                try:
                    try:
                        descriptor = os.open(
                            filename,
                            os.O_WRONLY
                            | os.O_CREAT
                            | os.O_EXCL
                            | getattr(os, "O_CLOEXEC", 0)
                            | getattr(os, "O_NOFOLLOW", 0),
                            0o600,
                            dir_fd=directory_fd,
                        )
                    except FileExistsError:
                        existing = (
                            GovernedBrowserOperationProofStore.load_terminal_binding(
                                self,
                                terminal_receipt_ref=(
                                    exact.terminal_receipt.receipt_ref
                                ),
                            )
                        )
                        if existing != exact:
                            raise GovernedBrowserOperationProofError(
                                "GOVERNED_BROWSER_TERMINAL_BINDING_CONFLICT"
                            )
                        return existing
                    if _proof_file_count(directory_fd) > (
                        MAX_GOVERNED_BROWSER_TERMINAL_BINDINGS
                    ):
                        os.unlink(filename, dir_fd=directory_fd)
                        os.close(descriptor)
                        descriptor = None
                        os.fsync(directory_fd)
                        raise GovernedBrowserOperationProofError(
                            "GOVERNED_BROWSER_TERMINAL_BINDING_STORE_FULL"
                        )
                    _write_all(descriptor, payload)
                    os.fsync(descriptor)
                    info = os.fstat(descriptor)
                    if (
                        not stat.S_ISREG(info.st_mode)
                        or info.st_uid != os.geteuid()
                        or info.st_nlink != 1
                        or info.st_mode & 0o077
                        or info.st_size != len(payload)
                    ):
                        raise OSError("unsafe terminal binding")
                    os.fsync(directory_fd)
                finally:
                    fcntl.flock(directory_fd, fcntl.LOCK_UN)
        except GovernedBrowserOperationProofError:
            if descriptor is not None:
                try:
                    os.unlink(filename, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                except OSError:
                    pass
            raise
        except OSError as exc:
            if descriptor is not None:
                try:
                    os.unlink(filename, dir_fd=directory_fd)
                    os.fsync(directory_fd)
                except OSError:
                    pass
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_WRITE_FAILED"
            ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory_fd)
        return GovernedBrowserOperationProofStore.load_terminal_binding(
            self,
            terminal_receipt_ref=exact.terminal_receipt.receipt_ref,
        )

    def load_terminal_binding(
        self,
        *,
        terminal_receipt_ref: str,
    ) -> GovernedBrowserTerminalReceiptBinding:
        validate_task_ref(terminal_receipt_ref, "terminal_receipt_ref")
        binding = _exact_store_binding(self)
        directory_fd = _open_terminal_binding_directory(self)
        descriptor: int | None = None
        try:
            filename = _terminal_binding_filename(terminal_receipt_ref)
            try:
                descriptor = os.open(
                    filename,
                    os.O_RDONLY
                    | getattr(os, "O_CLOEXEC", 0)
                    | getattr(os, "O_NOFOLLOW", 0)
                    | getattr(os, "O_NONBLOCK", 0),
                    dir_fd=directory_fd,
                )
                info = os.fstat(descriptor)
                path_info = os.stat(
                    filename,
                    dir_fd=directory_fd,
                    follow_symlinks=False,
                )
                if (
                    not stat.S_ISREG(info.st_mode)
                    or info.st_uid != os.geteuid()
                    or info.st_nlink != 1
                    or info.st_mode & 0o077
                    or info.st_size
                    > MAX_GOVERNED_BROWSER_TERMINAL_BINDING_BYTES
                    or (info.st_dev, info.st_ino)
                    != (path_info.st_dev, path_info.st_ino)
                ):
                    raise OSError("unsafe terminal binding")
                payload = _read_bounded(
                    descriptor,
                    max_bytes=MAX_GOVERNED_BROWSER_TERMINAL_BINDING_BYTES,
                )
            except OSError as exc:
                raise GovernedBrowserOperationProofError(
                    "GOVERNED_BROWSER_TERMINAL_BINDING_REQUIRED"
                ) from exc
        finally:
            if descriptor is not None:
                os.close(descriptor)
            os.close(directory_fd)
        try:
            terminal_binding = (
                GovernedBrowserTerminalReceiptBinding.model_validate_json(
                    payload
                )
            )
        except Exception as exc:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_INVALID"
            ) from exc
        if (
            terminal_binding.terminal_receipt.receipt_ref
            != terminal_receipt_ref
            or terminal_binding.store_ref != binding.store_ref
        ):
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_TERMINAL_BINDING_SCOPE_MISMATCH"
            )
        return terminal_binding


def _request_fingerprint_ref(request: ExternalActionExecutionRequest) -> str:
    return stable_governed_browser_ref(
        "request-fingerprint-ref:governed-external-action",
        ExternalActionExecutionRequest.model_dump(request, mode="json"),
    )


def _terminal_operation_proof_ref(
    terminal_receipt: ExternalActionReceipt,
) -> str | None:
    proof_refs = tuple(
        evidence_ref
        for evidence_ref in terminal_receipt.evidence_refs
        if evidence_ref.startswith(_OPERATION_PROOF_REF_PREFIX)
    )
    if not proof_refs:
        return None
    if (
        len(proof_refs) != 1
        or not terminal_receipt.evidence_refs
        or terminal_receipt.evidence_refs[-1] != proof_refs[0]
    ):
        raise ValueError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_OPERATION_PROOF_POSITION_INVALID"
        )
    return proof_refs[0]


def _attest_terminal_operation_proof(
    proof_store: GovernedBrowserOperationProofStore,
    *,
    request_fingerprint_ref: str,
    terminal_receipt: ExternalActionReceipt,
    operation_proof_ref: str | None,
) -> GovernedBrowserOperationProof | None:
    if operation_proof_ref is None:
        return None
    proof = GovernedBrowserOperationProofStore.load(
        proof_store,
        proof_ref=operation_proof_ref,
    )
    observed = (
        proof.store_ref,
        proof.request_fingerprint_ref,
        proof.transaction_ref,
        proof.intent_ref,
        proof.binding_ref,
        proof.base_evidence_refs,
        proof.proof_ref,
    )
    expected = (
        proof_store.store_ref,
        request_fingerprint_ref,
        terminal_receipt.transaction_ref,
        terminal_receipt.intent_ref,
        terminal_receipt.binding_ref,
        terminal_receipt.evidence_refs[:-1],
        operation_proof_ref,
    )
    if observed != expected:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_OPERATION_PROOF_INVALID"
        )
    return proof


def _record_terminal_receipt_binding(
    transaction_store: object,
    *,
    request_fingerprint_ref: str,
    terminal_receipt: ExternalActionReceipt,
) -> GovernedBrowserTerminalReceiptBinding:
    """Record proof only for the caller's just-committed terminal transition."""

    validate_task_ref(
        request_fingerprint_ref,
        "request_fingerprint_ref",
    )
    if not request_fingerprint_ref.startswith(
        _REQUEST_FINGERPRINT_REF_PREFIX
    ):
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_FINGERPRINT_INVALID"
        )
    exact_receipt = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_dump(
            terminal_receipt,
            mode="json",
        )
    )
    proof_store = _operation_proof_store_for_transaction_store(
        transaction_store
    )
    try:
        operation_proof_ref = _terminal_operation_proof_ref(exact_receipt)
    except ValueError as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_OPERATION_PROOF_INVALID"
        ) from exc
    _attest_terminal_operation_proof(
        proof_store,
        request_fingerprint_ref=request_fingerprint_ref,
        terminal_receipt=exact_receipt,
        operation_proof_ref=operation_proof_ref,
    )
    payload = {
        "store_ref": proof_store.store_ref,
        "request_fingerprint_ref": request_fingerprint_ref,
        "terminal_receipt": exact_receipt,
        "operation_proof_ref": operation_proof_ref,
    }
    provisional = GovernedBrowserTerminalReceiptBinding.model_construct(
        terminal_binding_ref=(
            "terminal-binding-ref:governed-browser:pending"
        ),
        **payload,
    )
    terminal_binding_ref = stable_governed_browser_ref(
        "terminal-binding-ref:governed-browser",
        GovernedBrowserTerminalReceiptBinding.model_dump(
            provisional,
            mode="json",
            exclude={"terminal_binding_ref"},
        ),
    )
    terminal_binding = GovernedBrowserTerminalReceiptBinding(
        terminal_binding_ref=terminal_binding_ref,
        **payload,
    )
    return GovernedBrowserOperationProofStore.save_terminal_binding(
        proof_store,
        terminal_binding,
    )


def _attest_terminal_receipt_binding(
    transaction_store: object,
    *,
    expected_execution: ExternalActionExecutionRequest,
    terminal_receipt: ExternalActionReceipt,
) -> GovernedBrowserTerminalReceiptBinding:
    """Require the immutable finalization proof for one exact durable receipt."""

    exact_execution = ExternalActionExecutionRequest.model_validate(
        ExternalActionExecutionRequest.model_dump(
            expected_execution,
            mode="json",
        )
    )
    exact_receipt = ExternalActionReceipt.model_validate(
        ExternalActionReceipt.model_dump(
            terminal_receipt,
            mode="json",
        )
    )
    proof_store = _operation_proof_store_for_transaction_store(
        transaction_store
    )
    terminal_binding = (
        GovernedBrowserOperationProofStore.load_terminal_binding(
            proof_store,
            terminal_receipt_ref=exact_receipt.receipt_ref,
        )
    )
    expected_fingerprint_ref = _request_fingerprint_ref(exact_execution)
    try:
        operation_proof_ref = _terminal_operation_proof_ref(exact_receipt)
    except ValueError as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_OPERATION_PROOF_INVALID"
        ) from exc
    if (
        terminal_binding.store_ref != proof_store.store_ref
        or terminal_binding.request_fingerprint_ref
        != expected_fingerprint_ref
        or terminal_binding.terminal_receipt != exact_receipt
        or terminal_binding.operation_proof_ref != operation_proof_ref
    ):
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_TERMINAL_BINDING_PROVENANCE_MISMATCH"
        )
    _attest_terminal_operation_proof(
        proof_store,
        request_fingerprint_ref=expected_fingerprint_ref,
        terminal_receipt=exact_receipt,
        operation_proof_ref=operation_proof_ref,
    )
    return terminal_binding


def _record_operation_proof(
    kernel: object,
    *,
    expected_execution: ExternalActionExecutionRequest,
    lane_ref: str,
    operation_ref: str,
    scope_refs: tuple[str, ...] = (),
    dispatch_outcome: Literal["succeeded", "failed", "outcome_ambiguous"],
    base_evidence_refs: tuple[str, ...],
    material: GovernedBrowserOperationProofMaterial,
) -> GovernedBrowserOperationProof:
    exact_execution = ExternalActionExecutionRequest.model_validate(
        ExternalActionExecutionRequest.model_dump(
            expected_execution,
            mode="json",
        )
    )
    store = _operation_proof_store_for_kernel(kernel)
    payload = {
        "store_ref": store.store_ref,
        "lane_ref": lane_ref,
        "operation_ref": operation_ref,
        "scope_refs": scope_refs,
        "request_fingerprint_ref": _request_fingerprint_ref(exact_execution),
        "transaction_ref": exact_execution.binding.transaction_ref,
        "intent_ref": exact_execution.intent_ref,
        "binding_ref": exact_execution.binding.binding_ref,
        "dispatch_outcome": dispatch_outcome,
        "base_evidence_refs": base_evidence_refs,
        "material": material,
    }
    provisional = GovernedBrowserOperationProof.model_construct(
        proof_ref="operation-proof-ref:governed-browser:pending",
        **payload,
    )
    proof_ref = stable_governed_browser_ref(
        "operation-proof-ref:governed-browser",
        GovernedBrowserOperationProof.model_dump(
            provisional,
            mode="json",
            exclude={"proof_ref"},
        ),
    )
    proof = GovernedBrowserOperationProof(proof_ref=proof_ref, **payload)
    return GovernedBrowserOperationProofStore.save(store, proof)


def _attest_operation_proof(
    kernel: object,
    *,
    expected_execution: ExternalActionExecutionRequest,
    proof_ref: str,
    lane_ref: str,
    operation_ref: str,
    scope_refs: tuple[str, ...],
    base_evidence_refs: tuple[str, ...],
) -> GovernedBrowserOperationProof:
    exact_execution = ExternalActionExecutionRequest.model_validate(
        ExternalActionExecutionRequest.model_dump(
            expected_execution,
            mode="json",
        )
    )
    store = _operation_proof_store_for_kernel(kernel)
    proof = GovernedBrowserOperationProofStore.load(
        store,
        proof_ref=proof_ref,
    )
    observed = (
        proof.store_ref,
        proof.lane_ref,
        proof.operation_ref,
        proof.scope_refs,
        proof.request_fingerprint_ref,
        proof.transaction_ref,
        proof.intent_ref,
        proof.binding_ref,
        proof.base_evidence_refs,
    )
    expected = (
        store.store_ref,
        lane_ref,
        operation_ref,
        scope_refs,
        _request_fingerprint_ref(exact_execution),
        exact_execution.binding.transaction_ref,
        exact_execution.intent_ref,
        exact_execution.binding.binding_ref,
        base_evidence_refs,
    )
    if observed != expected:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_PROVENANCE_MISMATCH"
        )
    return proof


def _register_operation_proof_service(
    service: object,
    *,
    dependencies: tuple[tuple[str, object], ...],
) -> GovernedBrowserOperationProofStore:
    dependency_map = dict(dependencies)
    kernel = dependency_map.get("_kernel")
    if kernel is None or len(dependency_map) != len(dependencies):
        raise ValueError("GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID")
    proof_store = _operation_proof_store_for_kernel(kernel)
    binding = _OperationProofServiceBinding(
        service_type=type(service),
        dependencies=dependencies,
        proof_store=proof_store,
    )
    with _SERVICE_BINDINGS_LOCK:
        if service in _SERVICE_BINDINGS:
            raise ValueError(
                "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_CONFLICT"
            )
        _SERVICE_BINDINGS[service] = binding
    return proof_store


def _require_operation_proof_service(
    service: object,
) -> _OperationProofServiceBinding:
    with _SERVICE_BINDINGS_LOCK:
        binding = _SERVICE_BINDINGS.get(service)
    if binding is None or type(service) is not binding.service_type:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID"
        )
    for attribute, dependency in binding.dependencies:
        try:
            current = object.__getattribute__(service, attribute)
        except AttributeError as exc:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID"
            ) from exc
        if current is not dependency:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID"
            )
    kernel = dict(binding.dependencies)["_kernel"]
    if _operation_proof_store_for_kernel(kernel) is not binding.proof_store:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_SERVICE_BINDING_INVALID"
        )
    return binding


def _operation_proof_store_for_kernel(
    kernel: object,
) -> GovernedBrowserOperationProofStore:
    from .transaction import (  # noqa: PLC0415
        ExternalActionTransactionStore,
        _bound_external_action_replay_store,
    )

    transaction_store = _bound_external_action_replay_store(kernel)
    if type(transaction_store) is not ExternalActionTransactionStore:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_KERNEL_SOURCE_INVALID"
        )
    return _operation_proof_store_for_transaction_store(transaction_store)


def _operation_proof_store_for_transaction_store(
    transaction_store: object,
) -> GovernedBrowserOperationProofStore:
    from .transaction import (  # noqa: PLC0415
        ExternalActionTransactionStore,
        _external_action_store_replay_source,
    )

    if type(transaction_store) is not ExternalActionTransactionStore:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_KERNEL_SOURCE_INVALID"
        )
    source = _external_action_store_replay_source(transaction_store)
    if source is None:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_KERNEL_SOURCE_INVALID"
        )
    source_path, _source_lock = source
    with _KERNEL_PROOF_STORES_LOCK:
        proof_store = _KERNEL_PROOF_STORES.get(transaction_store)
        if proof_store is None:
            proof_root = source_path.parent / f".{source_path.name}.operation-proofs"
            proof_store = GovernedBrowserOperationProofStore(proof_root)
            _KERNEL_PROOF_STORES[transaction_store] = proof_store
    return proof_store


def _exact_store_binding(
    store: object,
) -> _OperationProofStoreBinding:
    if type(store) is not GovernedBrowserOperationProofStore:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_INVALID"
        )
    with _STORE_BINDINGS_LOCK:
        binding = _STORE_BINDINGS.get(store)
    if binding is None:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_INVALID"
        )
    try:
        current_root = object.__getattribute__(store, "root")
        current_proof_directory = object.__getattribute__(
            store,
            "proof_directory",
        )
        current_terminal_binding_directory = object.__getattribute__(
            store,
            "terminal_binding_directory",
        )
        current_store_ref = object.__getattribute__(store, "store_ref")
        root_info = os.lstat(binding.root)
        proof_info = os.lstat(binding.proof_directory)
        terminal_binding_info = os.lstat(
            binding.terminal_binding_directory
        )
    except (AttributeError, OSError) as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        ) from exc
    if (
        current_root != binding.root
        or current_proof_directory != binding.proof_directory
        or current_terminal_binding_directory
        != binding.terminal_binding_directory
        or current_store_ref != binding.store_ref
        or not stat.S_ISDIR(root_info.st_mode)
        or stat.S_ISLNK(root_info.st_mode)
        or root_info.st_uid != os.geteuid()
        or root_info.st_mode & 0o077
        or (root_info.st_dev, root_info.st_ino) != binding.root_identity
        or not stat.S_ISDIR(proof_info.st_mode)
        or stat.S_ISLNK(proof_info.st_mode)
        or proof_info.st_uid != os.geteuid()
        or proof_info.st_mode & 0o077
        or (proof_info.st_dev, proof_info.st_ino)
        != binding.proof_directory_identity
        or not stat.S_ISDIR(terminal_binding_info.st_mode)
        or stat.S_ISLNK(terminal_binding_info.st_mode)
        or terminal_binding_info.st_uid != os.geteuid()
        or terminal_binding_info.st_mode & 0o077
        or (
            terminal_binding_info.st_dev,
            terminal_binding_info.st_ino,
        )
        != binding.terminal_binding_directory_identity
    ):
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        )
    return binding


def _open_proof_directory(store: object) -> int:
    binding = _exact_store_binding(store)
    try:
        descriptor = os.open(
            binding.proof_directory,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        ) from exc
    info = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or info.st_mode & 0o077
        or (info.st_dev, info.st_ino) != binding.proof_directory_identity
    ):
        os.close(descriptor)
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        )
    return descriptor


def _open_terminal_binding_directory(store: object) -> int:
    binding = _exact_store_binding(store)
    try:
        descriptor = os.open(
            binding.terminal_binding_directory,
            os.O_RDONLY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_DIRECTORY", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
    except OSError as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        ) from exc
    info = os.fstat(descriptor)
    if (
        not stat.S_ISDIR(info.st_mode)
        or info.st_uid != os.geteuid()
        or info.st_mode & 0o077
        or (info.st_dev, info.st_ino)
        != binding.terminal_binding_directory_identity
    ):
        os.close(descriptor)
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_SUBSTITUTION_DENIED"
        )
    return descriptor


def _proof_filename(proof_ref: str) -> str:
    validate_task_ref(proof_ref, "operation_proof_ref")
    return f"{hashlib.sha256(proof_ref.encode()).hexdigest()}.json"


def _terminal_binding_filename(terminal_receipt_ref: str) -> str:
    validate_task_ref(terminal_receipt_ref, "terminal_receipt_ref")
    return f"{hashlib.sha256(terminal_receipt_ref.encode()).hexdigest()}.json"


def _proof_file_count(directory_fd: int) -> int:
    count = 0
    try:
        with os.scandir(directory_fd) as entries:
            for entry in entries:
                if entry.name.startswith("."):
                    continue
                count += 1
                if count > MAX_GOVERNED_BROWSER_OPERATION_PROOFS:
                    break
    except OSError as exc:
        raise GovernedBrowserOperationProofError(
            "GOVERNED_BROWSER_OPERATION_PROOF_STORE_INVALID"
        ) from exc
    return count


def _write_all(descriptor: int, payload: bytes) -> None:
    view = memoryview(payload)
    offset = 0
    try:
        while offset < len(view):
            written = os.write(descriptor, view[offset:])
            if written <= 0:
                raise OSError("operation proof short write")
            offset += written
    finally:
        view.release()


def _read_bounded(descriptor: int, *, max_bytes: int) -> bytes:
    chunks: list[bytes] = []
    total = 0
    while True:
        chunk = os.read(descriptor, min(8192, max_bytes + 1 - total))
        if not chunk:
            return b"".join(chunks)
        chunks.append(chunk)
        total += len(chunk)
        if total > max_bytes:
            raise GovernedBrowserOperationProofError(
                "GOVERNED_BROWSER_OPERATION_PROOF_TOO_LARGE"
            )
