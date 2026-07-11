"""Narrow static-gate policy for the three promoted web-hybrid adapters."""

from __future__ import annotations

import ast


WEB_HYBRID_EXACT_ADAPTER_FILES = frozenset(
    {
        "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py",
        "src/ultimate_ai_agent/core/web_access/firecrawl_markdown.py",
        "src/ultimate_ai_agent/core/web_access/searxng_search.py",
    }
)
_ALLOWED_SOCKET_ATTRIBUTES = {
    "src/ultimate_ai_agent/core/web_access/firecrawl_cloud.py": {
        ("_cloud_json_request", "create_connection"),
    },
    "src/ultimate_ai_agent/core/web_access/firecrawl_markdown.py": {
        ("_loopback_json_post", "create_connection"),
        ("validate_resolved_public_target", "gaierror"),
        ("validate_resolved_public_target", "getaddrinfo"),
        ("validate_resolved_public_target", "SOCK_STREAM"),
    },
    "src/ultimate_ai_agent/core/web_access/searxng_search.py": {
        ("_loopback_json_get", "create_connection"),
    },
}


def _is_web_hybrid_promoted_static_fragment(
    rel: str,
    fragment: str,
    source_text: str,
) -> bool:
    """Accept reviewed occurrences without exempting generic authority markers."""

    if rel not in WEB_HYBRID_EXACT_ADAPTER_FILES:
        return False
    matching_lines = [
        line.strip() for line in source_text.splitlines() if fragment in line
    ]
    if not matching_lines:
        return False
    if fragment == "network_call_performed=True":
        return all(line == "network_call_performed=True," for line in matching_lines)
    if fragment == "runtime_allowed=True":
        return all(line == "provider_runtime_allowed=True," for line in matching_lines)
    if fragment != "socket.":
        return False
    try:
        tree = ast.parse(source_text)
    except SyntaxError:
        return False
    observed: set[tuple[str, str]] = set()

    class SocketVisitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.function_name = ""

        def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
            previous = self.function_name
            self.function_name = node.name
            self.generic_visit(node)
            self.function_name = previous

        def visit_Attribute(self, node: ast.Attribute) -> None:
            if isinstance(node.value, ast.Name) and node.value.id == "socket":
                observed.add((self.function_name, node.attr))
            self.generic_visit(node)

    SocketVisitor().visit(tree)
    return bool(observed) and observed <= _ALLOWED_SOCKET_ATTRIBUTES[rel]
