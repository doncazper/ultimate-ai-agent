"""Exact, read-only GitHub Release transport for the macOS updater.

This module is a product-distribution transport. It is not exposed to the
agent tool/runtime boundary and does not provide general-purpose web access.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .contracts import (
    DEFAULT_REPOSITORY,
    MAX_ARCHIVE_BYTES,
    MAX_DESCRIPTOR_BYTES,
    ContractError,
    ReleaseCandidate,
    ReleaseDescriptor,
    artifact_name,
    descriptor_name,
    sha256_file,
)


GITHUB_API_HOST = "api.github.com"
ALLOWED_DOWNLOAD_HOSTS = frozenset(
    {
        "api.github.com",
        "github.com",
        "objects.githubusercontent.com",
        "release-assets.githubusercontent.com",
    }
)
TOKEN_ENV = "UAA_UPDATER_GITHUB_TOKEN"
USER_AGENT = "Ultimate-AI-Agent-macOS-Updater/1"
DEFAULT_TIMEOUT_SECONDS = 12.0
MAX_RELEASES = 100


class ReleaseTransportError(RuntimeError):
    """The exact GitHub release transport could not complete safely."""


@dataclass(frozen=True)
class ReleaseCatalog:
    repository: str
    architecture: str
    candidates: tuple[ReleaseCandidate, ...]
    ignored_release_count: int
    authenticated: bool


class _SafeGitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Allow only GitHub release hosts and never forward a token cross-host."""

    def redirect_request(
        self,
        req: urllib.request.Request,
        fp: Any,
        code: int,
        msg: str,
        headers: Any,
        newurl: str,
    ) -> urllib.request.Request | None:
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname not in ALLOWED_DOWNLOAD_HOSTS:
            raise ReleaseTransportError("GitHub release redirect left the allowlist")
        redirected = super().redirect_request(req, fp, code, msg, headers, newurl)
        if redirected is not None and parsed.hostname != GITHUB_API_HOST:
            redirected.remove_header("Authorization")
        return redirected


def default_url_opener() -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(_SafeGitHubRedirectHandler())


def discover_github_token(
    *,
    environ: dict[str, str] | None = None,
    run: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> str | None:
    """Return a token from an explicit env slot or the authenticated gh CLI.

    The token is held in memory only. It is never included in command
    arguments, receipts, exceptions, or output.
    """

    environment = os.environ if environ is None else environ
    explicit = environment.get(TOKEN_ENV, "").strip()
    if explicit:
        return explicit
    gh = _find_gh(environment)
    if gh is None:
        return None
    try:
        completed = run(
            [str(gh), "auth", "token", "--hostname", "github.com"],
            text=True,
            capture_output=True,
            timeout=5.0,
            check=False,
            env=_credential_helper_env(environment),
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if completed.returncode != 0:
        return None
    token = completed.stdout.strip()
    return token or None


class GitHubReleaseClient:
    def __init__(
        self,
        *,
        repository: str = DEFAULT_REPOSITORY,
        token: str | None = None,
        opener: urllib.request.OpenerDirector | None = None,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self.repository = _validate_repository(repository)
        self.token = token
        self.opener = opener or default_url_opener()
        self.timeout_seconds = timeout_seconds

    def fetch_catalog(self, architecture: str) -> ReleaseCatalog:
        releases = self._get_json(
            f"https://{GITHUB_API_HOST}/repos/{self.repository}/releases"
            f"?per_page={MAX_RELEASES}"
        )
        if not isinstance(releases, list):
            raise ReleaseTransportError("GitHub releases response was not a list")
        candidates: list[ReleaseCandidate] = []
        ignored = 0
        for release in releases:
            candidate = self._candidate_from_release(release, architecture)
            if candidate is None:
                ignored += 1
            else:
                candidates.append(candidate)
        return ReleaseCatalog(
            repository=self.repository,
            architecture=architecture,
            candidates=tuple(candidates),
            ignored_release_count=ignored,
            authenticated=bool(self.token),
        )

    def download_artifact(
        self,
        candidate: ReleaseCandidate,
        target: Path,
    ) -> None:
        expected_prefix = (
            f"https://{GITHUB_API_HOST}/repos/{self.repository}/releases/assets/"
        )
        if not candidate.artifact_api_url.startswith(expected_prefix):
            raise ReleaseTransportError("release artifact URL left the exact API scope")
        target.parent.mkdir(parents=True, exist_ok=True)
        partial = target.with_name(target.name + ".partial")
        if partial.exists():
            partial.unlink()
        request = self._request(
            candidate.artifact_api_url,
            accept="application/octet-stream",
        )
        written = 0
        try:
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                with partial.open("wb") as handle:
                    while True:
                        chunk = response.read(1024 * 1024)
                        if not chunk:
                            break
                        written += len(chunk)
                        if (
                            written > MAX_ARCHIVE_BYTES
                            or written > candidate.descriptor.artifact_size
                        ):
                            raise ReleaseTransportError(
                                "release artifact exceeded its declared size"
                            )
                        handle.write(chunk)
        except (OSError, urllib.error.URLError) as exc:
            partial.unlink(missing_ok=True)
            raise ReleaseTransportError(
                "GitHub release artifact download failed"
            ) from exc
        if written != candidate.descriptor.artifact_size:
            partial.unlink(missing_ok=True)
            raise ReleaseTransportError("release artifact size did not match descriptor")
        digest = sha256_file(partial)
        if digest != candidate.descriptor.artifact_sha256:
            partial.unlink(missing_ok=True)
            raise ReleaseTransportError("release artifact SHA-256 verification failed")
        partial.replace(target)

    def _candidate_from_release(
        self,
        release: object,
        architecture: str,
    ) -> ReleaseCandidate | None:
        if not isinstance(release, dict) or release.get("draft") is not False:
            return None
        release_id = release.get("id")
        tag = release.get("tag_name")
        published_at = release.get("published_at")
        assets = release.get("assets")
        if (
            isinstance(release_id, bool)
            or not isinstance(release_id, int)
            or release_id <= 0
            or not isinstance(tag, str)
            or not tag
            or not isinstance(published_at, str)
            or not published_at
            or not isinstance(assets, list)
        ):
            return None
        by_name = {
            asset.get("name"): asset
            for asset in assets
            if isinstance(asset, dict) and isinstance(asset.get("name"), str)
        }
        descriptor_asset = by_name.get(descriptor_name(architecture))
        artifact_asset = by_name.get(artifact_name(architecture))
        if not isinstance(descriptor_asset, dict) or not isinstance(
            artifact_asset, dict
        ):
            return None
        descriptor_url = descriptor_asset.get("url")
        artifact_url = artifact_asset.get("url")
        if not isinstance(descriptor_url, str) or not isinstance(artifact_url, str):
            return None
        try:
            descriptor_payload = self._get_bytes(
                descriptor_url,
                limit=MAX_DESCRIPTOR_BYTES,
                accept="application/octet-stream",
            )
            descriptor = ReleaseDescriptor.from_json_bytes(
                descriptor_payload,
                expected_architecture=architecture,
            )
        except (ContractError, ReleaseTransportError):
            return None
        if descriptor.tag != tag:
            return None
        expected_prerelease = descriptor.channel == "dev"
        if release.get("prerelease") is not expected_prerelease:
            return None
        artifact_size = artifact_asset.get("size")
        if artifact_size != descriptor.artifact_size:
            return None
        digest = artifact_asset.get("digest")
        normalized_digest: str | None = None
        if digest is not None:
            if not isinstance(digest, str) or digest != (
                "sha256:" + descriptor.artifact_sha256
            ):
                return None
            normalized_digest = digest
        return ReleaseCandidate(
            descriptor=descriptor,
            release_id=release_id,
            published_at=published_at,
            artifact_api_url=artifact_url,
            descriptor_api_url=descriptor_url,
            github_asset_digest=normalized_digest,
        )

    def _get_json(self, url: str) -> object:
        payload = self._get_bytes(
            url,
            limit=4 * 1024 * 1024,
            accept="application/vnd.github+json",
        )
        try:
            return json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise ReleaseTransportError(
                "GitHub API returned invalid JSON"
            ) from exc

    def _get_bytes(self, url: str, *, limit: int, accept: str) -> bytes:
        _validate_github_api_url(url, self.repository)
        request = self._request(url, accept=accept)
        try:
            with self.opener.open(request, timeout=self.timeout_seconds) as response:
                payload = response.read(limit + 1)
        except urllib.error.HTTPError as exc:
            if exc.code in {401, 403, 404}:
                raise ReleaseTransportError(
                    "GitHub release access requires repository authentication"
                ) from exc
            raise ReleaseTransportError("GitHub release request failed") from exc
        except (OSError, urllib.error.URLError) as exc:
            raise ReleaseTransportError("GitHub release request failed") from exc
        if len(payload) > limit:
            raise ReleaseTransportError("GitHub release response exceeded its limit")
        return payload

    def _request(self, url: str, *, accept: str) -> urllib.request.Request:
        headers = {
            "Accept": accept,
            "User-Agent": USER_AGENT,
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        return urllib.request.Request(url, headers=headers, method="GET")


def _find_gh(environ: dict[str, str]) -> Path | None:
    discovered = shutil.which("gh", path=environ.get("PATH"))
    candidates = [
        Path(discovered) if discovered else None,
        Path(environ.get("HOME", "~")).expanduser() / ".local" / "bin" / "gh",
        Path("/opt/homebrew/bin/gh"),
        Path("/usr/local/bin/gh"),
    ]
    for candidate in candidates:
        if candidate is not None and candidate.is_file() and os.access(candidate, os.X_OK):
            return candidate
    return None


def _credential_helper_env(environ: dict[str, str]) -> dict[str, str]:
    allowed = {
        key: value
        for key, value in environ.items()
        if key in {"HOME", "PATH", "GH_HOST", "GH_CONFIG_DIR", "XDG_CONFIG_HOME"}
    }
    allowed.setdefault("PATH", "/usr/bin:/bin:/usr/sbin:/sbin")
    return allowed


def _validate_repository(repository: str) -> str:
    parts = repository.split("/")
    if len(parts) != 2 or any(
        not part or not all(char.isalnum() or char in "._-" for char in part)
        for part in parts
    ):
        raise ContractError("GitHub repository must be an exact owner/name pair")
    return repository


def _validate_github_api_url(url: str, repository: str) -> None:
    parsed = urllib.parse.urlparse(url)
    expected_prefix = f"/repos/{repository}/"
    if (
        parsed.scheme != "https"
        or parsed.hostname != GITHUB_API_HOST
        or not parsed.path.startswith(expected_prefix)
    ):
        raise ReleaseTransportError("GitHub release URL left the exact repository scope")
