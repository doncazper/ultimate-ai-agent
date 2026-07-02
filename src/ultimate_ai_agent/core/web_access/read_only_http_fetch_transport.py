"""Exact real-world transport for the read-only HTTP fetch lane.

This module is the approved WebAccessGateway transport boundary for
`read_only_real_world_web_fetch`. It deliberately exposes one factory, uses
stdlib HTTPS GET only, follows no redirects, and returns only bounded bytes to
the M72 redaction/output builder.
"""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import socket
import ssl
from typing import Any, Mapping
from urllib.parse import urlsplit


TRANSPORT_REF = "http-fetch-transport:web-access-gateway-real-world-v1"
_MAX_HTTP_HEADER_BYTES = 32768


@dataclass(frozen=True)
class _ResolvedPeer:
    family: int
    sockaddr: Any
    ip: str


def build_read_only_real_world_http_fetch_transport():  # type: ignore[no-untyped-def]
    """Return the exact WebAccessGateway-approved HTTPS GET transport."""

    def transport(request: Any, policy: Any) -> Mapping[str, Any]:
        target = _normalized_real_world_fetch_target(request, policy)
        peer = _resolve_public_peer(target["host"])
        context = ssl.create_default_context()
        timeout = min(float(getattr(policy, "timeout_seconds", 5)), 5.0)
        limit = int(getattr(policy, "max_response_bytes", 65536))
        status_code, content_type, cookies_present, body = _open_https_get(
            peer=peer,
            host=target["host"],
            path=target["path"],
            timeout=timeout,
            response_limit_bytes=limit,
            context=context,
        )

        return {
            "status_code": status_code,
            "content_type": content_type,
            "body": body,
            "final_url": None,
            "redirected": False,
            "headers_present": False,
            "cookies_present": cookies_present,
        }

    transport.transport_ref = TRANSPORT_REF  # type: ignore[attr-defined]
    transport.real_world_transport_performed = True  # type: ignore[attr-defined]
    return transport


def _normalized_real_world_fetch_target(request: Any, policy: Any) -> dict[str, str]:
    """Validate transport invariants before any socket opens."""

    parts = urlsplit(str(request.url))
    if parts.scheme != "https":
        raise ValueError("HTTPS_ONLY_REQUIRED")
    if parts.username or parts.password:
        raise ValueError("URL_CREDENTIALS_DENIED")
    if parts.query:
        raise ValueError("QUERY_STRING_DENIED")
    if parts.fragment:
        raise ValueError("URL_FRAGMENT_DENIED")
    host = (parts.hostname or "").strip().lower().rstrip(".")
    allowed_hosts = {
        str(host).strip().lower().rstrip(".")
        for host in getattr(policy, "allowed_hosts", ())
    }
    if not host or host not in allowed_hosts:
        raise ValueError("HOST_NOT_ALLOWLISTED_DENIED")
    path = parts.path or "/"
    if not path.startswith("/"):
        raise ValueError("URL_PATH_INVALID")
    if any(ord(char) < 32 or ord(char) == 127 for char in path):
        raise ValueError("URL_PATH_CONTROL_CHAR_DENIED")
    try:
        path.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("URL_PATH_ENCODING_DENIED") from exc
    return {"host": host, "path": path}


def _resolve_public_peer(host: str) -> _ResolvedPeer:
    try:
        infos = socket.getaddrinfo(host, 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise ValueError("HTTP_FETCH_DNS_RESOLUTION_FAILED") from exc
    if not infos:
        raise ValueError("HTTP_FETCH_DNS_RESOLUTION_FAILED")
    for info in infos:
        family = info[0]
        sockaddr = info[4]
        if not sockaddr:
            raise ValueError("HTTP_FETCH_DNS_RESOLUTION_FAILED")
        ip = str(sockaddr[0])
        if not _is_public_ip(ip):
            raise ValueError("PRIVATE_OR_LOCAL_RESOLVED_HOST_DENIED")
        return _ResolvedPeer(family=family, sockaddr=sockaddr, ip=ip)
    raise ValueError("HTTP_FETCH_DNS_RESOLUTION_FAILED")


def _open_https_get(
    *,
    peer: _ResolvedPeer,
    host: str,
    path: str,
    timeout: float,
    response_limit_bytes: int,
    context: ssl.SSLContext,
) -> tuple[int, str, bool, bytes]:
    raw_sock = socket.socket(peer.family, socket.SOCK_STREAM)
    tls_sock = None
    try:
        raw_sock.settimeout(timeout)
        raw_sock.connect(peer.sockaddr)
        tls_sock = context.wrap_socket(raw_sock, server_hostname=host)
        peer_ip = str(tls_sock.getpeername()[0])
        if not _is_public_ip(peer_ip):
            raise ValueError("PRIVATE_OR_LOCAL_RESOLVED_HOST_DENIED")
        request_bytes = _http_get_request_bytes(host=host, path=path)
        tls_sock.sendall(request_bytes)
        status_code, headers, body = _read_http_response(
            tls_sock,
            response_limit_bytes=response_limit_bytes,
        )
    except OSError as exc:
        raise ValueError("HTTP_FETCH_TRANSPORT_FAILED") from exc
    finally:
        if tls_sock is not None:
            tls_sock.close()
        raw_sock.close()

    if 300 <= status_code <= 399:
        raise ValueError("REDIRECTS_DENIED")
    if headers.get("content-encoding", "identity").lower() not in {"identity", ""}:
        raise ValueError("UNSUPPORTED_RESPONSE_ENCODING_DENIED")
    transfer_encoding = headers.get("transfer-encoding", "").lower()
    if transfer_encoding == "chunked":
        body = _decode_chunked_body(body, response_limit_bytes)
    elif transfer_encoding not in {"", "identity"}:
        raise ValueError("UNSUPPORTED_TRANSFER_ENCODING_DENIED")
    content_type = headers.get("content-type", "application/octet-stream")
    content_type = content_type.split(";", 1)[0].strip().lower() or "application/octet-stream"
    cookies_present = "set-cookie" in headers
    return status_code, content_type, cookies_present, body[:response_limit_bytes]


def _http_get_request_bytes(*, host: str, path: str) -> bytes:
    return (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}\r\n"
        "User-Agent: ultimate-ai-agent-read-only-fetch/1\r\n"
        "Accept: text/plain, text/html, application/json;q=0.9, */*;q=0.1\r\n"
        "Accept-Encoding: identity\r\n"
        "Connection: close\r\n"
        "\r\n"
    ).encode("ascii")


def _read_http_response(
    tls_sock: Any,
    *,
    response_limit_bytes: int,
) -> tuple[int, dict[str, str], bytes]:
    buffer = b""
    delimiter = b"\r\n\r\n"
    while delimiter not in buffer:
        chunk = tls_sock.recv(4096)
        if not chunk:
            break
        buffer += chunk
        if len(buffer) > _MAX_HTTP_HEADER_BYTES + response_limit_bytes + 1:
            raise ValueError("HTTP_RESPONSE_HEADERS_TOO_LARGE")
    if delimiter not in buffer:
        raise ValueError("HTTP_RESPONSE_HEADERS_INVALID")

    header_bytes, body = buffer.split(delimiter, 1)
    if len(header_bytes) > _MAX_HTTP_HEADER_BYTES:
        raise ValueError("HTTP_RESPONSE_HEADERS_TOO_LARGE")
    status_code, headers = _parse_http_headers(header_bytes)
    while len(body) <= response_limit_bytes:
        chunk = tls_sock.recv(min(4096, response_limit_bytes + 1 - len(body)))
        if not chunk:
            break
        body += chunk
    return status_code, headers, body[:response_limit_bytes]


def _parse_http_headers(header_bytes: bytes) -> tuple[int, dict[str, str]]:
    try:
        header_text = header_bytes.decode("iso-8859-1")
    except UnicodeDecodeError as exc:
        raise ValueError("HTTP_RESPONSE_HEADERS_INVALID") from exc
    lines = header_text.split("\r\n")
    status_line = lines[0].strip()
    parts = status_line.split(None, 2)
    if len(parts) < 2 or not parts[0].startswith("HTTP/"):
        raise ValueError("HTTP_RESPONSE_STATUS_INVALID")
    try:
        status_code = int(parts[1])
    except ValueError as exc:
        raise ValueError("HTTP_RESPONSE_STATUS_INVALID") from exc
    headers: dict[str, str] = {}
    for line in lines[1:]:
        if not line:
            continue
        if ":" not in line:
            raise ValueError("HTTP_RESPONSE_HEADERS_INVALID")
        name, value = line.split(":", 1)
        headers[name.strip().lower()] = value.strip()
    return status_code, headers


def _decode_chunked_body(body: bytes, response_limit_bytes: int) -> bytes:
    decoded = bytearray()
    position = 0
    while position < len(body) and len(decoded) < response_limit_bytes:
        line_end = body.find(b"\r\n", position)
        if line_end == -1:
            break
        size_token = body[position:line_end].split(b";", 1)[0].strip()
        try:
            chunk_size = int(size_token, 16)
        except ValueError as exc:
            raise ValueError("UNSUPPORTED_TRANSFER_ENCODING_DENIED") from exc
        position = line_end + 2
        if chunk_size == 0:
            break
        available = max(0, min(chunk_size, len(body) - position))
        remaining = response_limit_bytes - len(decoded)
        decoded.extend(body[position : position + min(available, remaining)])
        if len(decoded) >= response_limit_bytes or available < chunk_size:
            break
        position += chunk_size
        if body[position : position + 2] == b"\r\n":
            position += 2
        elif position < len(body):
            raise ValueError("UNSUPPORTED_TRANSFER_ENCODING_DENIED")
    return bytes(decoded)


def _is_public_ip(value: str) -> bool:
    ip = ipaddress.ip_address(value)
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )
