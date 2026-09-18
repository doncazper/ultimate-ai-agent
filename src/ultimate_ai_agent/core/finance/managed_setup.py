"""Confirmed, immutable Finance helper enrollment with bounded crash recovery."""

from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, replace
from datetime import datetime
import ctypes
import errno
import hashlib
import os
import re
from pathlib import Path
import stat
import sys
from typing import Callable, Mapping
import uuid

from ultimate_ai_agent.core.approvals import LocalApprovalAuthority
from ultimate_ai_agent.core.authority import AuthorityLeaseStore
from ultimate_ai_agent.core.authority.approval_validation import (
    AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_DIR,
    issue_authority_lease_with_backend_approval,
)
from ultimate_ai_agent.core.authority.authority_constants import (
    AUTHORITY_STATE_LOCK_KEY,
)
from ultimate_ai_agent.core.capabilities.enums import RiskLevel
from ultimate_ai_agent.core.capabilities.policy import PolicyEngine
from ultimate_ai_agent.core.finance.managed_setup_authority import (
    FIXED_CONSTRAINTS,
    MANAGED_SETUP_APPROVER_REF,
    MANAGED_SETUP_POLICY_REF,
    MANAGED_SETUP_PREPARATION_MAX_BYTES,
    ManagedFinanceSetupError,
    ManagedFinanceSetupPreparation,
    _ref,
    build_preparation,
    build_setup_lease_request,
    fail,
    managed_setup_error_code,
    parse_managed_setup_preparation,
    preparation_payload,
    require_environment,
    require_policy,
    serialize_managed_setup_preparation,
    validate_current_authority,
)
from ultimate_ai_agent.core.finance_managed_profile import (
    FINANCE_EXPLICIT_ENV_NAMES,
    FINANCE_WORKSPACE_DISABLE_ENV,
    MANAGED_MAX_TERMINAL_RECEIPTS,
    MANAGED_HELPER_MAX_BYTES,
    FinanceManagedLayout,
    FinanceManagedProfileV1,
    FinanceManagedSetupIntentV1,
    ManagedPendingAttemptV1,
    ManagedSetupStateV1,
    ManagedTerminalReceiptV1,
    VerifiedFinanceHelper,
    managed_directory_ownership_ref,
    managed_helper_ownership_ref,
    managed_ref,
    managed_repository_ref,
    managed_wire_payload,
    read_managed_profile,
    read_managed_state,
    serialize_managed_state,
    validate_managed_record,
)
from ultimate_ai_agent.core.private_path_security import (
    _private_identity,
    _require_no_extended_acl_grants_fd,
    _require_private_regular_metadata,
    require_no_extended_acl_fd,
)
from ultimate_ai_agent.core.single_writer_lock import (
    SingleWriterLockManager,
    _acquire_interprocess_lock,
    _release_interprocess_lock,
)

__all__ = [
    "ManagedFinanceSetupService",
    "ManagedFinanceSetupError",
    "ManagedFinanceSetupPreparation",
    "ManagedFinanceSetupPreparationResult",
    "ManagedFinanceSetupInspection",
    "ManagedFinanceSetupResult",
    "parse_managed_setup_preparation",
    "serialize_managed_setup_preparation",
    "managed_setup_error_code",
    "MANAGED_SETUP_PREPARATION_MAX_BYTES",
]

_SETUP_LOCKS = SingleWriterLockManager()
_DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
_FILE_FLAGS = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedFinanceSetupInspection:
    status: str
    state_ref: str | None
    profile_ref: str | None
    pending_attempt_ref: str | None
    explicit_configuration_present: bool
    safe_disable_engaged: bool
    error_code: str | None

    def model_dump(self, *, mode="json"):
        return {name: getattr(self, name) for name in self.__dataclass_fields__}


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedFinanceSetupResult:
    outcome: str
    replayed: bool
    mutation_performed: bool
    authority_state_written: bool
    receipt: ManagedTerminalReceiptV1

    def model_dump(self, *, mode="json"):
        return {
            "outcome": self.outcome,
            "replayed": self.replayed,
            "mutation_performed": self.mutation_performed,
            "authority_state_written": self.authority_state_written,
            "receipt": managed_wire_payload(self.receipt),
        }


@dataclass(frozen=True, slots=True, kw_only=True)
class ManagedFinanceSetupPreparationResult:
    status: str
    preparation: ManagedFinanceSetupPreparation | None = None
    result: ManagedFinanceSetupResult | None = None

    def model_dump(self, *, mode="json"):
        return {
            "status": self.status,
            "preparation": preparation_payload(self.preparation)
            if self.preparation
            else None,
            "result": self.result.model_dump() if self.result else None,
        }


def _hashed(record, field, kind):
    payload = managed_wire_payload(record)
    del payload[field]
    return replace(record, **{field: managed_ref(kind, payload)})


def _state(history=(), *, pending=None, active=None):
    return _hashed(
        ManagedSetupStateV1(
            state_ref="pending",
            active_profile=active,
            pending_attempt=pending,
            terminal_receipts=tuple(history),
        ),
        "state_ref",
        "state",
    )


def _intent(**values):
    provisional = FinanceManagedSetupIntentV1(
        intent_ref="pending", payload_fingerprint_ref="pending", **values
    )
    payload = managed_wire_payload(provisional)
    del payload["intent_ref"]
    del payload["payload_fingerprint_ref"]
    provisional = replace(
        provisional, payload_fingerprint_ref=managed_ref("payload", payload)
    )
    return _hashed(provisional, "intent_ref", "intent")


def _directory_metadata(descriptor, *, private):
    metadata = os.fstat(descriptor)
    if not stat.S_ISDIR(metadata.st_mode):
        fail("OWNERSHIP_UNVERIFIED")
    if private:
        if metadata.st_uid != os.getuid() or metadata.st_mode & 0o077:
            fail("OWNERSHIP_UNVERIFIED")
        require_no_extended_acl_fd(descriptor, purpose="managed setup directory")
    else:
        if metadata.st_uid not in {0, os.getuid()} or (
            metadata.st_mode & 0o022 and not metadata.st_mode & stat.S_ISVTX
        ):
            fail("OWNERSHIP_UNVERIFIED")
        _require_no_extended_acl_grants_fd(descriptor, purpose="managed setup ancestor")
    return metadata


class _OwnedLayout:
    """Fixed-layout retained descriptors; no public arbitrary-path writer API."""

    def __init__(self, layout):
        self.layout = layout
        self.fds = []
        self.links = []
        self.aliases = []
        self.root = -1
        self.lock_state = None
        self.before_mutation = lambda: None

    def close(self):
        for fd in reversed(self.fds):
            os.close(fd)
        self.fds.clear()

    def open(self):
        parts = list(self.layout.root.parts[1:])
        parent = os.open("/", _DIR_FLAGS)
        self.fds.append(parent)
        lexical = Path("/")
        aliases = 0
        while parts:
            name = parts.pop(0)
            private = not parts
            try:
                metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
            except FileNotFoundError:
                self.before_mutation()
                try:
                    os.mkdir(name, 0o700, dir_fd=parent)
                    os.fsync(parent)
                except FileExistsError:
                    pass
                metadata = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if stat.S_ISLNK(metadata.st_mode):
                if private or metadata.st_uid != 0 or aliases >= 16:
                    fail("OWNERSHIP_UNVERIFIED")
                target = os.readlink(name, dir_fd=parent)
                self.aliases.append((parent, name, metadata, target))
                expanded = (lexical / target).resolve(strict=True)
                parts = list(expanded.parts[1:]) + parts
                parent = os.open("/", _DIR_FLAGS)
                self.fds.append(parent)
                lexical = Path("/")
                aliases += 1
                continue
            fd = os.open(name, _DIR_FLAGS, dir_fd=parent)
            self.fds.append(fd)
            opened = _directory_metadata(fd, private=private)
            if not os.path.samestat(metadata, opened):
                fail("OWNERSHIP_UNVERIFIED")
            self.links.append((parent, name, fd, opened, private))
            parent = fd
            lexical /= name
        self.root = parent
        self.check()
        return self

    def check(self):
        if self.lock_state is not None:
            fd, original = self.lock_state
            linked = os.stat(".setup-v1.lock", dir_fd=self.root, follow_symlinks=False)
            current = os.fstat(fd)
            if (
                not os.path.samestat(original, current)
                or not os.path.samestat(current, linked)
                or current.st_uid != os.getuid()
                or stat.S_IMODE(current.st_mode) != 0o600
                or current.st_nlink != 1
            ):
                fail("OWNERSHIP_UNVERIFIED")
            require_no_extended_acl_fd(fd, purpose="managed setup lock")
        for parent, name, fd, original, private in self.links:
            current = _directory_metadata(fd, private=private)
            linked = os.stat(name, dir_fd=parent, follow_symlinks=False)
            if not os.path.samestat(original, current) or not os.path.samestat(
                current, linked
            ):
                fail("OWNERSHIP_UNVERIFIED")
        for parent, name, original, target in self.aliases:
            if (
                not os.path.samestat(
                    original, os.stat(name, dir_fd=parent, follow_symlinks=False)
                )
                or os.readlink(name, dir_fd=parent) != target
            ):
                fail("OWNERSHIP_UNVERIFIED")

    def directory(self, name, *, parent=None, create=False, exclusive=False):
        parent = self.root if parent is None else parent
        if create:
            self.before_mutation()
            try:
                os.mkdir(name, 0o700, dir_fd=parent)
                os.fsync(parent)
            except FileExistsError:
                if exclusive:
                    fail("OWNERSHIP_UNVERIFIED")
        before = os.stat(name, dir_fd=parent, follow_symlinks=False)
        fd = os.open(name, _DIR_FLAGS, dir_fd=parent)
        self.fds.append(fd)
        current = _directory_metadata(fd, private=True)
        if not os.path.samestat(before, current):
            fail("OWNERSHIP_UNVERIFIED")
        self.links.append((parent, name, fd, current, True))
        return fd

    @contextmanager
    def lock(self):
        self.before_mutation()
        fd = os.open(
            ".setup-v1.lock",
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK,
            0o600,
            dir_fd=self.root,
        )
        try:
            metadata = os.fstat(fd)
            linked = os.stat(".setup-v1.lock", dir_fd=self.root, follow_symlinks=False)
            if (
                not stat.S_ISREG(metadata.st_mode)
                or metadata.st_uid != os.getuid()
                or stat.S_IMODE(metadata.st_mode) != 0o600
                or metadata.st_nlink != 1
                or not os.path.samestat(metadata, linked)
            ):
                fail("OWNERSHIP_UNVERIFIED")
            require_no_extended_acl_fd(fd, purpose="managed setup lock")
            root_metadata = os.fstat(self.root)
            with _SETUP_LOCKS.acquire(
                f"managed-{root_metadata.st_dev}-{root_metadata.st_ino}"
            ):
                backend = _acquire_interprocess_lock(fd)
                try:
                    self.check()
                    if not os.path.samestat(
                        metadata,
                        os.stat(
                            ".setup-v1.lock", dir_fd=self.root, follow_symlinks=False
                        ),
                    ):
                        fail("OWNERSHIP_UNVERIFIED")
                    self.lock_state = (fd, metadata)
                    yield
                finally:
                    self.lock_state = None
                    _release_interprocess_lock(fd, backend)
        finally:
            os.close(fd)

    def forget(self, descriptor):
        metadata = os.fstat(descriptor)
        self.links = [
            link for link in self.links if not os.path.samestat(link[3], metadata)
        ]


def _exists(parent, name):
    if parent is None:
        return False
    try:
        os.stat(name, dir_fd=parent, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def _rename_exclusive(source_parent, source, target_parent, target):
    """Atomic no-replacement directory promotion; fail closed if unsupported."""
    libc = ctypes.CDLL(None, use_errno=True)
    if sys.platform == "darwin":
        function = libc.renameatx_np
        flag = 4  # RENAME_EXCL
    elif sys.platform.startswith("linux") and hasattr(libc, "renameat2"):
        function = libc.renameat2
        flag = 1  # RENAME_NOREPLACE
    else:
        fail("OWNERSHIP_UNVERIFIED")
    function.argtypes = (
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_int,
        ctypes.c_char_p,
        ctypes.c_uint,
    )
    function.restype = ctypes.c_int
    if (
        function(
            source_parent,
            source.encode("ascii"),
            target_parent,
            target.encode("ascii"),
            flag,
        )
        != 0
    ):
        if ctypes.get_errno() in {errno.EEXIST, errno.ENOTEMPTY}:
            fail("OWNERSHIP_UNVERIFIED")
        fail("MUTATION_INTERRUPTED")


class ManagedFinanceSetupService:
    def __init__(
        self,
        *,
        layout: FinanceManagedLayout,
        source_provider: Callable[[], VerifiedFinanceHelper],
        environment_provider: Callable[[], Mapping[str, str]],
        clock: Callable[[], datetime],
    ):
        self.layout = layout
        self.source_provider = source_provider
        self.environment_provider = environment_provider
        self.clock = clock
        self.policy = PolicyEngine(default_max_risk=RiskLevel.medium)

    def inspect(self):
        result = read_managed_profile(self.layout)
        environment = self.environment_provider()
        value = environment.get(FINANCE_WORKSPACE_DISABLE_ENV)
        return ManagedFinanceSetupInspection(
            status=result.status,
            state_ref=result.state_ref,
            profile_ref=result.profile.profile_ref if result.profile else None,
            pending_attempt_ref=result.state.pending_attempt.attempt_ref
            if result.state and result.state.pending_attempt
            else None,
            explicit_configuration_present=any(
                key in environment for key in FINANCE_EXPLICIT_ENV_NAMES
            ),
            safe_disable_engaged=value is not None
            and value.strip().lower() not in {"0", "false", "no", "off"},
            error_code=result.error_code,
        )

    def _read(self):
        result = read_managed_state(self.layout)
        if result.status == "invalid" or result.state_ref is None:
            fail("STATE_INVALID")
        return result

    def _historical(self, read, operation, request, idempotency, intent=None):
        for receipt in read.state.terminal_receipts if read.state else ():
            for recorded in (receipt.intent, receipt.original_enrollment_intent):
                if recorded is None:
                    continue
                if (
                    request == recorded.request_ref
                    or idempotency == recorded.idempotency_ref
                ):
                    if (
                        request != recorded.request_ref
                        or idempotency != recorded.idempotency_ref
                        or operation != recorded.operation
                        or intent is not None
                        and intent != recorded
                    ):
                        fail("STATE_CONFLICT")
                    if receipt.phase == "committed":
                        profile = read_managed_profile(self.layout)
                        if (
                            profile.status != "present"
                            or profile.state_ref != read.state_ref
                        ):
                            fail("STATE_INVALID")
                    return ManagedFinanceSetupResult(
                        outcome=receipt.phase,
                        replayed=True,
                        mutation_performed=False,
                        authority_state_written=False,
                        receipt=receipt,
                    )
        return None

    def _verified_source(self):
        try:
            helper = self.source_provider()
            if type(helper) is not VerifiedFinanceHelper:
                fail("SOURCE_UNAVAILABLE")
            validate_managed_record(helper.identity)
            if (
                type(helper.executable_bytes) is not bytes
                or len(helper.executable_bytes) != helper.identity.helper_size_bytes
                or hashlib.sha256(helper.executable_bytes).hexdigest()
                != helper.identity.helper_sha256
            ):
                fail("SOURCE_CHANGED")
            return helper
        except ManagedFinanceSetupError:
            raise
        except Exception:
            fail("SOURCE_UNAVAILABLE")

    def _profile(self, helper):
        return _hashed(
            FinanceManagedProfileV1(
                profile_ref="pending",
                repository_ref=managed_repository_ref(self.layout),
                helper=helper.identity,
            ),
            "profile_ref",
            "profile",
        )

    def prepare(self, operation, request_ref, idempotency_ref):
        for identifier in (request_ref, idempotency_ref):
            if type(identifier) is not str or not re.fullmatch(
                r"[A-Za-z0-9][A-Za-z0-9._:-]{7,199}", identifier
            ):
                fail("REQUEST_INVALID")
        if ":" not in request_ref:
            fail("REQUEST_INVALID")
        if type(operation) is not str or operation not in {
            "enroll",
            "discard_incomplete",
        }:
            fail("REQUEST_INVALID")
        read = self._read()
        historical = self._historical(read, operation, request_ref, idempotency_ref)
        if historical:
            return ManagedFinanceSetupPreparationResult(
                status="historical", result=historical
            )
        require_environment(self.environment_provider())
        state = read.state
        pending = state.pending_attempt if state else None
        if state and state.active_profile:
            fail("STATE_CONFLICT")
        if operation == "discard_incomplete":
            if (
                pending is None
                or request_ref == pending.intent.request_ref
                or idempotency_ref == pending.intent.idempotency_ref
            ):
                fail("STATE_CONFLICT")
            intent = _intent(
                operation=operation,
                expected_state_ref=read.state_ref,
                pending_attempt_ref=pending.attempt_ref,
                request_ref=request_ref,
                idempotency_ref=idempotency_ref,
            )
            profile = None
        elif pending:
            if (
                pending.intent.request_ref != request_ref
                or pending.intent.idempotency_ref != idempotency_ref
            ):
                fail("STATE_CONFLICT")
            helper = self._verified_source()
            if helper.identity != pending.desired_profile.helper:
                fail("SOURCE_CHANGED")
            intent, profile = pending.intent, pending.desired_profile
        else:
            if state and len(state.terminal_receipts) >= MANAGED_MAX_TERMINAL_RECEIPTS:
                fail("CAPACITY_EXHAUSTED")
            if os.path.lexists(self.layout.repository_dir):
                fail("STATE_CONFLICT")
            profile = self._profile(self._verified_source())
            intent = _intent(
                operation="enroll",
                expected_state_ref=read.state_ref,
                desired_profile_ref=profile.profile_ref,
                helper_ref=profile.helper.helper_ref,
                source_provenance_ref=profile.helper.source.source_provenance_ref,
                request_ref=request_ref,
                idempotency_ref=idempotency_ref,
            )
            candidate = _state(
                state.terminal_receipts if state else (),
                pending=self._pending(intent, profile),
            )
            self._serialize(candidate)
        preparation = build_preparation(
            intent, profile, read.state_ref, pending, self.clock()
        )
        require_policy(preparation, self.policy)
        return ManagedFinanceSetupPreparationResult(
            status="prepared", preparation=preparation
        )

    def refresh(self, preparation):
        preparation = parse_managed_setup_preparation(
            serialize_managed_setup_preparation(preparation)
        )
        read = self._read()
        historical = self._historical(
            read,
            preparation.intent.operation,
            preparation.intent.request_ref,
            preparation.intent.idempotency_ref,
            preparation.intent,
        )
        if historical:
            return ManagedFinanceSetupPreparationResult(
                status="historical", result=historical
            )
        refreshed = self.prepare(
            preparation.intent.operation,
            preparation.intent.request_ref,
            preparation.intent.idempotency_ref,
        )
        if refreshed.preparation and refreshed.preparation.intent != preparation.intent:
            fail("STATE_CONFLICT")
        return refreshed

    @staticmethod
    def _pending(intent, profile):
        return ManagedPendingAttemptV1(
            attempt_ref=managed_ref("attempt", managed_wire_payload(intent)),
            intent=intent,
            desired_profile=profile,
        )

    @staticmethod
    def _serialize(state):
        try:
            return serialize_managed_state(state)
        except ValueError:
            fail("CAPACITY_EXHAUSTED")

    def _bound_current(self, preparation, read):
        pending = read.state.pending_attempt if read.state else None
        if read.state_ref != preparation.observed_state_ref:
            fail("STATE_CONFLICT")
        if read.state and read.state.active_profile:
            fail("STATE_CONFLICT")
        expected = build_preparation(
            preparation.intent,
            preparation.desired_profile,
            read.state_ref,
            pending,
            preparation.prepared_at,
        )
        if serialize_managed_setup_preparation(
            expected
        ) != serialize_managed_setup_preparation(preparation):
            fail("PREPARATION_INVALID")
        if pending:
            if preparation.intent.operation == "enroll" and (
                pending.intent != preparation.intent
                or pending.desired_profile != preparation.desired_profile
            ):
                fail("STATE_CONFLICT")
            if (
                preparation.intent.operation == "discard_incomplete"
                and pending.attempt_ref != preparation.intent.pending_attempt_ref
            ):
                fail("STATE_CONFLICT")
        elif (
            preparation.intent.operation != "enroll"
            or preparation.intent.expected_state_ref != read.state_ref
        ):
            fail("STATE_CONFLICT")
        if preparation.intent.operation == "enroll":
            if (
                preparation.desired_profile is None
                or preparation.desired_profile.repository_ref
                != managed_repository_ref(self.layout)
            ):
                fail("PREPARATION_INVALID")
            if (
                preparation.intent.desired_profile_ref
                != preparation.desired_profile.profile_ref
            ):
                fail("PREPARATION_INVALID")
            validate_managed_record(
                self._pending(preparation.intent, preparation.desired_profile)
            )
        if os.path.lexists(self.layout.repository_dir):
            fail("STATE_CONFLICT")

    def confirm(self, preparation, confirmed):
        if confirmed is not True:
            fail("CONFIRMATION_REQUIRED")
        preparation = parse_managed_setup_preparation(
            serialize_managed_setup_preparation(preparation)
        )
        read = self._read()
        historical = self._historical(
            read,
            preparation.intent.operation,
            preparation.intent.request_ref,
            preparation.intent.idempotency_ref,
            preparation.intent,
        )
        if historical:
            return historical
        self._bound_current(preparation, read)
        require_environment(self.environment_provider())
        now = self.clock()
        if (
            now.tzinfo is None
            or not preparation.prepared_at <= now < preparation.expires_at
        ):
            fail("PREPARATION_EXPIRED")
        require_policy(preparation, self.policy)
        helper = None
        if preparation.intent.operation == "enroll":
            helper = self._verified_source()
            if helper.identity != preparation.desired_profile.helper:
                fail("SOURCE_CHANGED")
        approvals = LocalApprovalAuthority()
        approvals.create_request(preparation.approval_request)
        initial_grant = approvals.grant(
            preparation.approval_request.approval_request_id,
            approved_by_actor_id=MANAGED_SETUP_APPROVER_REF,
            approval_ref=preparation.expected_approval_ref,
            expires_at=preparation.expires_at,
        )
        grant_fingerprint = _ref(
            "approval-grant", initial_grant.model_dump(mode="json")
        )

        def admission_checkpoint():
            require_environment(self.environment_provider())
            current = self.clock()
            if (
                current.tzinfo is None
                or not preparation.prepared_at <= current < preparation.expires_at
            ):
                fail("PREPARATION_EXPIRED")
            require_policy(preparation, self.policy)
            if not approvals.validate_at_trusted_time(
                preparation.approval_request.to_validation_request(
                    preparation.expected_approval_ref
                ),
                current_time=current,
            ).allowed:
                fail("APPROVAL_DENIED")
            current_grant = approvals.get_grant(preparation.expected_approval_ref)
            if (
                current_grant is None
                or _ref("approval-grant", current_grant.model_dump(mode="json"))
                != grant_fingerprint
            ):
                fail("APPROVAL_DENIED")

        owned = _OwnedLayout(self.layout)
        owned.before_mutation = admission_checkpoint
        try:
            owned.open()
            with owned.lock():
                read = self._read()
                historical = self._historical(
                    read,
                    preparation.intent.operation,
                    preparation.intent.request_ref,
                    preparation.intent.idempotency_ref,
                    preparation.intent,
                )
                if historical:
                    return historical
                self._bound_current(preparation, read)
                owned.directory("authority", create=True)
                owned.directory(AUTHORITY_LEASE_APPROVAL_SIGNING_KEY_DIR, create=True)
                owned.check()
                store = AuthorityLeaseStore(self.layout.authority_dir)
                issue_id = _ref("lease-issue", {"preview": preparation.preview_ref})
                with (
                    store.lock_manager.acquire(AUTHORITY_STATE_LOCK_KEY),
                    approvals.hold_validation_lock(),
                ):
                    admission_checkpoint()
                    owned.check()
                    requirement, _grant, lease, lease_receipt = (
                        issue_authority_lease_with_backend_approval(
                            store,
                            build_setup_lease_request(preparation),
                            idempotency_ref=issue_id,
                            approved_by_actor_id=MANAGED_SETUP_APPROVER_REF,
                        )
                    )
                    if lease is None or lease_receipt.status not in {
                        "issued",
                        "replayed",
                    }:
                        fail("LEASE_DENIED")
                    current = read

                    def checkpoint():
                        nonlocal grant_fingerprint
                        require_environment(self.environment_provider())
                        evidence = validate_current_authority(
                            preparation,
                            approvals,
                            store,
                            requirement,
                            lease,
                            issue_id,
                            self.clock(),
                            self.policy,
                            grant_fingerprint,
                        )
                        grant_fingerprint = evidence["approval_grant_fingerprint_ref"]
                        owned.check()
                        if self._read().state_ref != current.state_ref:
                            fail("STATE_CONFLICT")
                        require_environment(self.environment_provider())
                        return evidence

                    def write(candidate):
                        nonlocal current
                        raw = self._serialize(candidate)
                        self._write_state(owned, raw, checkpoint)
                        current = self._read()
                        if current.state_ref != candidate.state_ref:
                            fail("STATE_CONFLICT")

                    owned.before_mutation = checkpoint
                    checkpoint()
                    state = read.state
                    history = state.terminal_receipts if state else ()
                    pending = state.pending_attempt if state else None
                    if pending is None:
                        pending = self._pending(
                            preparation.intent, preparation.desired_profile
                        )
                        write(_state(history, pending=pending))
                    if preparation.intent.operation == "enroll":
                        pending = self._enroll(
                            owned, pending, helper, history, write, checkpoint
                        )
                    evidence = checkpoint()
                    receipt = self._receipt(
                        preparation, pending, lease_receipt.receipt_ref, evidence
                    )
                    candidate = _state(
                        (*history, receipt),
                        active=pending.desired_profile
                        if receipt.phase == "committed"
                        else None,
                    )
                    self._serialize(candidate)
                    if receipt.phase == "abandoned":
                        self._discard(owned, pending, checkpoint)
                    else:
                        self._promote(owned, pending, checkpoint)
                    write(candidate)
                    return ManagedFinanceSetupResult(
                        outcome=receipt.phase,
                        replayed=False,
                        mutation_performed=True,
                        authority_state_written=lease_receipt.status == "issued",
                        receipt=receipt,
                    )
        except ManagedFinanceSetupError:
            raise
        except (OSError, ValueError):
            fail("MUTATION_INTERRUPTED")
        finally:
            owned.close()

    def _write_state(self, owned, raw, checkpoint):
        checkpoint()
        name = ".state-" + uuid.uuid4().hex + ".tmp"
        fd = os.open(
            name,
            os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=owned.root,
        )
        metadata = os.fstat(fd)
        promoted = False
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                if written <= 0:
                    fail("MUTATION_INTERRUPTED")
                offset += written
            os.fsync(fd)
            checkpoint()
            if not os.path.samestat(
                metadata, os.stat(name, dir_fd=owned.root, follow_symlinks=False)
            ):
                fail("OWNERSHIP_UNVERIFIED")
            os.replace(
                name, "state-v1.json", src_dir_fd=owned.root, dst_dir_fd=owned.root
            )
            promoted = True
            os.fsync(owned.root)
        finally:
            os.close(fd)
            if (
                not promoted
                and _exists(owned.root, name)
                and os.path.samestat(
                    metadata, os.stat(name, dir_fd=owned.root, follow_symlinks=False)
                )
            ):
                os.unlink(name, dir_fd=owned.root)

    def _helper_owned(self, directory, pending):
        fd = os.open("helper", _FILE_FLAGS, dir_fd=directory)
        try:
            initial = os.fstat(fd)
            _require_private_regular_metadata(
                initial,
                purpose="managed helper",
                maximum_bytes=MANAGED_HELPER_MAX_BYTES,
                exact_bytes=pending.desired_profile.helper.helper_size_bytes,
            )
            require_no_extended_acl_fd(fd, purpose="managed helper")
            if not initial.st_mode & stat.S_IXUSR:
                fail("OWNERSHIP_UNVERIFIED")
            digest = hashlib.sha256()
            remaining = initial.st_size
            while remaining:
                chunk = os.read(fd, min(65536, remaining))
                if not chunk:
                    fail("OWNERSHIP_UNVERIFIED")
                remaining -= len(chunk)
                digest.update(chunk)
            if (
                os.read(fd, 1)
                or digest.hexdigest() != pending.desired_profile.helper.helper_sha256
            ):
                fail("OWNERSHIP_UNVERIFIED")
            final = os.fstat(fd)
            linked = os.stat("helper", dir_fd=directory, follow_symlinks=False)
            if _private_identity(initial) != _private_identity(
                final
            ) or _private_identity(final) != _private_identity(linked):
                fail("OWNERSHIP_UNVERIFIED")
            identity = managed_helper_ownership_ref(
                final,
                attempt_ref=pending.attempt_ref,
                helper_sha256=pending.desired_profile.helper.helper_sha256,
            )
            if (
                pending.staged_helper_identity_ref is not None
                and pending.staged_helper_identity_ref != identity
            ):
                fail("OWNERSHIP_UNVERIFIED")
            return identity, final
        finally:
            os.close(fd)

    def _attempt_location(self, owned, pending, *, create=False):
        checkpoint_name = pending.attempt_ref.rsplit(":", 1)[1]
        digest = pending.desired_profile.helper.helper_sha256
        stage = (
            owned.directory("staging", create=create)
            if create or _exists(owned.root, "staging")
            else None
        )
        helpers = (
            owned.directory("helpers", create=create)
            if create or _exists(owned.root, "helpers")
            else None
        )
        staged, promoted = _exists(stage, checkpoint_name), _exists(helpers, digest)
        if staged and promoted:
            fail("OWNERSHIP_UNVERIFIED")
        if promoted:
            parent, name, final = helpers, digest, True
        else:
            parent, name, final = stage, checkpoint_name, False
        if not staged and not promoted:
            if not create:
                return None, parent, name, final, stage, helpers
            if pending.staging_directory_identity_ref is not None:
                fail("OWNERSHIP_UNVERIFIED")
        fd = owned.directory(
            name, parent=parent, create=not staged and not promoted, exclusive=True
        )
        if pending.staging_directory_identity_ref is not None:
            if (
                managed_directory_ownership_ref(
                    os.fstat(fd), attempt_ref=pending.attempt_ref
                )
                != pending.staging_directory_identity_ref
            ):
                fail("OWNERSHIP_UNVERIFIED")
        elif staged or promoted:
            fail("OWNERSHIP_UNVERIFIED")
        return fd, parent, name, final, stage, helpers

    def _enroll(self, owned, pending, helper, history, write, checkpoint):
        checkpoint()
        directory, parent, name, promoted, stage, helpers = self._attempt_location(
            owned, pending, create=True
        )
        if pending.staging_directory_identity_ref is None:
            pending = replace(
                pending,
                staging_directory_identity_ref=managed_directory_ownership_ref(
                    os.fstat(directory), attempt_ref=pending.attempt_ref
                ),
            )
            write(_state(history, pending=pending))
        if pending.staged_helper_identity_ref is None:
            if promoted or os.listdir(directory):
                fail("OWNERSHIP_UNVERIFIED")
            checkpoint()
            fd = os.open(
                "helper",
                os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                0o500,
                dir_fd=directory,
            )
            try:
                offset = 0
                while offset < len(helper.executable_bytes):
                    written = os.write(fd, helper.executable_bytes[offset:])
                    if written <= 0:
                        fail("MUTATION_INTERRUPTED")
                    offset += written
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(directory)
            pending = replace(
                pending,
                staged_helper_identity_ref=self._helper_owned(directory, pending)[0],
            )
            write(_state(history, pending=pending))
        if os.listdir(directory) != ["helper"]:
            fail("OWNERSHIP_UNVERIFIED")
        self._helper_owned(directory, pending)
        return pending

    def _promote(self, owned, pending, checkpoint):
        checkpoint()
        directory, _parent, name, promoted, stage, helpers = self._attempt_location(
            owned, pending
        )
        if directory is None:
            fail("OWNERSHIP_UNVERIFIED")
        _identity, verified_metadata = self._helper_owned(directory, pending)
        if os.listdir(directory) != ["helper"]:
            fail("OWNERSHIP_UNVERIFIED")
        if not promoted:
            checkpoint()
            if os.listdir(directory) != ["helper"] or _private_identity(
                verified_metadata
            ) != _private_identity(
                os.stat("helper", dir_fd=directory, follow_symlinks=False)
            ):
                fail("OWNERSHIP_UNVERIFIED")
            _rename_exclusive(
                stage, name, helpers, pending.desired_profile.helper.helper_sha256
            )
            owned.forget(directory)
            owned.links.append(
                (
                    helpers,
                    pending.desired_profile.helper.helper_sha256,
                    directory,
                    os.fstat(directory),
                    True,
                )
            )
            os.fsync(stage)
            os.fsync(helpers)
        return pending

    def _discard(self, owned, pending, checkpoint):
        checkpoint()
        # No original source lookup. Missing owned artifacts are safe after an interrupted cleanup.
        if not _exists(owned.root, "staging") and not _exists(owned.root, "helpers"):
            if pending.staging_directory_identity_ref is None:
                return
            return
        directory, parent, name, _promoted, _stage, _helpers = self._attempt_location(
            owned, pending
        )
        if directory is None:
            return
        if pending.staging_directory_identity_ref is None:
            fail("OWNERSHIP_UNVERIFIED")
        children = os.listdir(directory)
        if children not in ([], ["helper"]):
            fail("OWNERSHIP_UNVERIFIED")
        if "helper" in children:
            if pending.staged_helper_identity_ref is None:
                fail("OWNERSHIP_UNVERIFIED")
            _identity, verified_metadata = self._helper_owned(directory, pending)
            checkpoint()
            if _private_identity(verified_metadata) != _private_identity(
                os.stat("helper", dir_fd=directory, follow_symlinks=False)
            ):
                fail("OWNERSHIP_UNVERIFIED")
            os.unlink("helper", dir_fd=directory)
            os.fsync(directory)
        checkpoint()
        os.rmdir(name, dir_fd=parent)
        owned.forget(directory)
        os.fsync(parent)

    @staticmethod
    def _receipt(preparation, pending, lease_receipt_ref, evidence):
        committed = preparation.intent.operation == "enroll"
        receipt = ManagedTerminalReceiptV1(
            receipt_ref="pending",
            phase="committed" if committed else "abandoned",
            intent=preparation.intent,
            original_enrollment_intent=None if committed else pending.intent,
            attempt_ref=pending.attempt_ref,
            after_profile_revision=1 if committed else 0,
            profile_ref=pending.desired_profile.profile_ref,
            helper_ref=pending.desired_profile.helper.helper_ref,
            source_provenance_ref=pending.desired_profile.helper.source.source_provenance_ref,
            policy_revision_ref=MANAGED_SETUP_POLICY_REF,
            preview_ref=preparation.preview_ref,
            exact_scope_ref=preparation.exact_scope_ref,
            approval_ref=preparation.expected_approval_ref,
            authority_lease_ref=preparation.requested_lease_ref,
            lease_issue_receipt_ref=lease_receipt_ref,
            permit_ref=_ref("permit", {"preview": preparation.preview_ref, **evidence}),
            audit_event_ref=_ref("audit", {"preview": preparation.preview_ref}),
            rollback_ref=FIXED_CONSTRAINTS["exact_rollback_ref"],
            safe_disable_ref=FIXED_CONSTRAINTS["exact_safe_disable_ref"],
            **evidence,
        )
        return _hashed(receipt, "receipt_ref", "receipt")
