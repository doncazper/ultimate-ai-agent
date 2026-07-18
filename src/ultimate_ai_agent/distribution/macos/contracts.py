"""Typed contracts for the macOS release and update lane."""
from __future__ import annotations

import hashlib
import json
import platform
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable, Literal


RELEASE_DESCRIPTOR_SCHEMA = "uaa.macos.release.v1"
BUNDLE_MANIFEST_SCHEMA = "uaa.macos.bundle.v1"
INSTALL_RECEIPT_SCHEMA = "uaa.macos.install-receipt.v1"
PRODUCT_LINE = "ultimate-ai-agent.current"
APP_NAME = "Ultimate AI Agent"
APP_BUNDLE_NAME = f"{APP_NAME}.app"
APP_BUNDLE_IDENTIFIER = "ai.ultimate-agent.control-center"
DEFAULT_REPOSITORY = "doncazper/ultimate-ai-agent"
DEFAULT_CHANNEL = "newest"
SUPPORTED_CHANNELS = ("newest", "stable", "dev")
SUPPORTED_ARCHITECTURES = ("arm64", "x86_64")
MINIMUM_MACOS = "13.0"
MAX_DESCRIPTOR_BYTES = 64 * 1024
MAX_ARCHIVE_BYTES = 2 * 1024 * 1024 * 1024
MAX_ARCHIVE_FILES = 100_000
MAX_EXTRACTED_BYTES = 4 * 1024 * 1024 * 1024

ReleaseChannel = Literal["stable", "dev"]
UpdateChannel = Literal["newest", "stable", "dev"]

_SAFE_TAG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._+-]{0,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")
_VERSION_RE = re.compile(r"^[0-9]+(?:\.[0-9]+){1,3}(?:[-+][A-Za-z0-9._-]+)?$")


class ContractError(ValueError):
    """A release or bundle failed its fail-closed contract."""


@dataclass(frozen=True)
class ReleaseDescriptor:
    schema_version: str
    product_line: str
    tag: str
    version: str
    channel: ReleaseChannel
    source_commit: str
    source_timestamp: str
    platform: str
    architecture: str
    artifact_name: str
    artifact_sha256: str
    artifact_size: int
    minimum_macos: str
    signing_kind: str
    notarized: bool

    @classmethod
    def from_mapping(
        cls,
        value: dict[str, Any],
        *,
        expected_architecture: str | None = None,
    ) -> "ReleaseDescriptor":
        required = {
            "schema_version",
            "product_line",
            "tag",
            "version",
            "channel",
            "source_commit",
            "source_timestamp",
            "platform",
            "architecture",
            "artifact_name",
            "artifact_sha256",
            "artifact_size",
            "minimum_macos",
            "signing_kind",
            "notarized",
        }
        missing = sorted(required.difference(value))
        if missing:
            raise ContractError(
                "release descriptor missing required fields: " + ", ".join(missing)
            )
        descriptor = cls(
            schema_version=_required_string(value, "schema_version"),
            product_line=_required_string(value, "product_line"),
            tag=_required_string(value, "tag"),
            version=_required_string(value, "version"),
            channel=_release_channel(value.get("channel")),
            source_commit=_required_string(value, "source_commit").lower(),
            source_timestamp=_required_string(value, "source_timestamp"),
            platform=_required_string(value, "platform"),
            architecture=_required_string(value, "architecture"),
            artifact_name=_required_string(value, "artifact_name"),
            artifact_sha256=_required_string(value, "artifact_sha256").lower(),
            artifact_size=_required_positive_int(value, "artifact_size"),
            minimum_macos=_required_string(value, "minimum_macos"),
            signing_kind=_required_string(value, "signing_kind"),
            notarized=_required_bool(value, "notarized"),
        )
        descriptor.validate(expected_architecture=expected_architecture)
        return descriptor

    @classmethod
    def from_json_bytes(
        cls,
        payload: bytes,
        *,
        expected_architecture: str | None = None,
    ) -> "ReleaseDescriptor":
        if len(payload) > MAX_DESCRIPTOR_BYTES:
            raise ContractError("release descriptor exceeds the bounded size limit")
        try:
            value = json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ContractError("release descriptor is not valid JSON") from exc
        if not isinstance(value, dict):
            raise ContractError("release descriptor must be a JSON object")
        return cls.from_mapping(
            value,
            expected_architecture=expected_architecture,
        )

    def validate(self, *, expected_architecture: str | None = None) -> None:
        if self.schema_version != RELEASE_DESCRIPTOR_SCHEMA:
            raise ContractError("unsupported macOS release descriptor schema")
        if self.product_line != PRODUCT_LINE:
            raise ContractError("release descriptor is not on the active product line")
        if not _SAFE_TAG_RE.fullmatch(self.tag):
            raise ContractError("release descriptor tag is not safe")
        if not _VERSION_RE.fullmatch(self.version):
            raise ContractError("release descriptor version is not valid")
        if not _COMMIT_RE.fullmatch(self.source_commit):
            raise ContractError("release descriptor source commit must be an exact SHA")
        _parse_timestamp(self.source_timestamp)
        if self.platform != "macos":
            raise ContractError("release descriptor platform must be macos")
        if self.architecture not in SUPPORTED_ARCHITECTURES:
            raise ContractError("release descriptor architecture is unsupported")
        if (
            expected_architecture is not None
            and self.architecture != expected_architecture
        ):
            raise ContractError("release descriptor architecture does not match this Mac")
        expected_artifact = artifact_name(self.architecture)
        if self.artifact_name != expected_artifact:
            raise ContractError("release descriptor artifact name drifted")
        if not _SHA256_RE.fullmatch(self.artifact_sha256):
            raise ContractError("release descriptor SHA-256 is invalid")
        if self.artifact_size > MAX_ARCHIVE_BYTES:
            raise ContractError("release artifact exceeds the bounded size limit")
        if self.minimum_macos != MINIMUM_MACOS:
            raise ContractError("release descriptor minimum macOS contract drifted")
        if self.signing_kind not in {"ad-hoc", "developer-id"}:
            raise ContractError("release descriptor signing kind is unsupported")
        if self.notarized and self.signing_kind != "developer-id":
            raise ContractError("only Developer ID releases may claim notarization")

    @property
    def source_datetime(self) -> datetime:
        return _parse_timestamp(self.source_timestamp)

    def as_mapping(self) -> dict[str, Any]:
        return asdict(self)

    def to_json_bytes(self) -> bytes:
        return (
            json.dumps(self.as_mapping(), indent=2, sort_keys=True) + "\n"
        ).encode("utf-8")


@dataclass(frozen=True)
class ReleaseCandidate:
    descriptor: ReleaseDescriptor
    release_id: int
    published_at: str
    artifact_api_url: str
    descriptor_api_url: str
    github_asset_digest: str | None = None

    @property
    def published_datetime(self) -> datetime:
        return _parse_timestamp(self.published_at)


@dataclass(frozen=True)
class ReleaseSelection:
    requested_channel: UpdateChannel
    stable: ReleaseCandidate | None
    dev: ReleaseCandidate | None
    selected: ReleaseCandidate | None


def select_release(
    candidates: Iterable[ReleaseCandidate],
    channel: str = DEFAULT_CHANNEL,
) -> ReleaseSelection:
    """Select the newest valid stable/dev release by tagged commit time.

    GitHub publication time is only a deterministic tie-breaker. This permits
    historical tags to be backfilled without making an older build look newer.
    Arbitrary repository tags never enter this function: only releases with a
    valid active-product-line descriptor are candidates.
    """

    requested = normalize_channel(channel)
    materialized = list(candidates)
    stable = _newest(
        item for item in materialized if item.descriptor.channel == "stable"
    )
    dev = _newest(item for item in materialized if item.descriptor.channel == "dev")
    if requested == "stable":
        selected = stable
    elif requested == "dev":
        selected = dev
    else:
        selected = _newest(item for item in (stable, dev) if item is not None)
    return ReleaseSelection(
        requested_channel=requested,
        stable=stable,
        dev=dev,
        selected=selected,
    )


def normalize_channel(value: str) -> UpdateChannel:
    normalized = value.strip().lower()
    if normalized not in SUPPORTED_CHANNELS:
        raise ContractError(
            "update channel must be one of: " + ", ".join(SUPPORTED_CHANNELS)
        )
    return normalized  # type: ignore[return-value]


def current_architecture() -> str:
    machine = platform.machine().strip().lower()
    if machine in {"arm64", "aarch64"}:
        return "arm64"
    if machine in {"x86_64", "amd64"}:
        return "x86_64"
    raise ContractError("this Mac architecture is not supported")


def artifact_name(architecture: str) -> str:
    if architecture not in SUPPORTED_ARCHITECTURES:
        raise ContractError("unsupported macOS release architecture")
    return f"uaa-macos-{architecture}.tar.gz"


def descriptor_name(architecture: str) -> str:
    if architecture not in SUPPORTED_ARCHITECTURES:
        raise ContractError("unsupported macOS release architecture")
    return f"uaa-macos-{architecture}.release.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _newest(candidates: Iterable[ReleaseCandidate]) -> ReleaseCandidate | None:
    return max(
        candidates,
        key=lambda item: (
            item.descriptor.source_datetime,
            item.published_datetime,
            item.release_id,
        ),
        default=None,
    )


def _parse_timestamp(value: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ContractError("release timestamp is not valid ISO-8601") from exc
    if parsed.tzinfo is None:
        raise ContractError("release timestamp must include a timezone")
    return parsed


def _required_string(value: dict[str, Any], key: str) -> str:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ContractError(f"release descriptor {key} must be a non-empty string")
    return item.strip()


def _required_positive_int(value: dict[str, Any], key: str) -> int:
    item = value.get(key)
    if isinstance(item, bool) or not isinstance(item, int) or item <= 0:
        raise ContractError(f"release descriptor {key} must be a positive integer")
    return item


def _required_bool(value: dict[str, Any], key: str) -> bool:
    item = value.get(key)
    if not isinstance(item, bool):
        raise ContractError(f"release descriptor {key} must be a boolean")
    return item


def _release_channel(value: object) -> ReleaseChannel:
    if value not in {"stable", "dev"}:
        raise ContractError("release descriptor channel must be stable or dev")
    return value  # type: ignore[return-value]
