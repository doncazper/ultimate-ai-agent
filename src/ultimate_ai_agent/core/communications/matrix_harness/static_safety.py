"""Exact static-scan exception for the bounded Matrix harness backend."""

from __future__ import annotations

import ast
from collections import Counter
import hashlib


MATRIX_HARNESS_BACKEND_REL = (
    "src/ultimate_ai_agent/core/communications/matrix_harness/backend.py"
)
_SUBPROCESS_POPEN = "subprocess" + ".Popen("
_SUBPROCESS_RUN = "subprocess" + ".run("
_REVIEWED_BACKEND_SHA256 = (
    "9c094144e703a30b0f55c4b95ac1b13a73bd08e2f388e7c18b295773d3535630"
)
_REVIEWED_SPAWN_GATE_SOURCE = """
import os
import signal
import sys
import time

gate_fd = int(sys.argv[1])
liveness_fd = int(sys.argv[2])
token = os.read(gate_fd, 1)
os.close(gate_fd)
if token != b"1":
    os._exit(126)

try:
    watchdog_pid = os.fork()
except OSError:
    os._exit(125)

if watchdog_pid == 0:
    for watched in (signal.SIGINT, signal.SIGTERM, signal.SIGHUP):
        signal.signal(watched, signal.SIG_IGN)
    devnull = os.open(os.devnull, os.O_RDWR)
    for descriptor in (0, 1, 2):
        os.dup2(devnull, descriptor)
    if devnull > 2:
        os.close(devnull)
    while True:
        try:
            if not os.read(liveness_fd, 1):
                break
        except InterruptedError:
            continue
    os.killpg(os.getpgrp(), signal.SIGTERM)
    time.sleep(0.25)
    os.killpg(os.getpgrp(), signal.SIGKILL)
    os._exit(125)

os.close(liveness_fd)
os.execve(sys.argv[3], sys.argv[3:], os.environ)
"""
_REVIEWED_SUBPROCESS_ATTRIBUTES = Counter(
    {
        "CompletedProcess": 2,
        "DEVNULL": 3,
        "PIPE": 3,
        "Popen": 21,
        "TimeoutExpired": 7,
        "run": 1,
    }
)
_REVIEWED_SUBPROCESS_CALLS = Counter(
    {
        ("_process_group_inventory", "run"): 1,
        ("_run_probe", "CompletedProcess"): 1,
        ("_spawn", "Popen"): 1,
        ("_communicate_bounded", "TimeoutExpired"): 1,
    }
)


def _is_subprocess_attribute(node: ast.AST) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and isinstance(node.value, ast.Name)
        and (node.value.id == "subprocess")
    )


def _is_name(node: ast.AST, name: str) -> bool:
    return isinstance(node, ast.Name) and node.id == name


def _is_attribute(node: ast.AST, owner: str, attribute: str) -> bool:
    return (
        isinstance(node, ast.Attribute)
        and _is_name(node.value, owner)
        and node.attr == attribute
    )


def _keyword_map(call: ast.Call) -> dict[str, ast.AST] | None:
    if any(keyword.arg is None for keyword in call.keywords):
        return None
    keywords = {str(keyword.arg): keyword.value for keyword in call.keywords}
    if len(keywords) != len(call.keywords):
        return None
    return keywords


def _exact_spawn_call(call: ast.Call) -> bool:
    keywords = _keyword_map(call)
    if keywords is None or set(keywords) != {
        "cwd",
        "env",
        "stdin",
        "stdout",
        "stderr",
        "pass_fds",
        "start_new_session",
        "shell",
    }:
        return False
    if len(call.args) != 1 or not isinstance(call.args[0], ast.List):
        return False
    argv = call.args[0].elts
    if len(argv) != 6:
        return False
    return (
        _is_attribute(argv[0], "sys", "executable")
        and isinstance(argv[1], ast.Constant)
        and argv[1].value == "-c"
        and _is_name(argv[2], "_MATRIX_HARNESS_SPAWN_GATE")
        and isinstance(argv[3], ast.Call)
        and _is_name(argv[3].func, "str")
        and len(argv[3].args) == 1
        and _is_name(argv[3].args[0], "gate_read_fd")
        and isinstance(argv[4], ast.Call)
        and _is_name(argv[4].func, "str")
        and len(argv[4].args) == 1
        and _is_name(argv[4].args[0], "liveness_read_fd")
        and isinstance(argv[5], ast.Starred)
        and _is_name(argv[5].value, "argv")
        and isinstance(keywords["cwd"], ast.Attribute)
        and keywords["cwd"].attr == "repo_root"
        and isinstance(keywords["cwd"].value, ast.Attribute)
        and _is_name(keywords["cwd"].value.value, "self")
        and keywords["cwd"].value.attr == "config"
        and isinstance(keywords["env"], ast.Call)
        and isinstance(keywords["env"].func, ast.Attribute)
        and _is_name(keywords["env"].func.value, "self")
        and keywords["env"].func.attr == "_subprocess_env"
        and not keywords["env"].args
        and not keywords["env"].keywords
        and _is_attribute(keywords["stdin"], "subprocess", "DEVNULL")
        and _is_attribute(keywords["stdout"], "subprocess", "PIPE")
        and _is_attribute(keywords["stderr"], "subprocess", "PIPE")
        and isinstance(keywords["pass_fds"], ast.Tuple)
        and len(keywords["pass_fds"].elts) == 2
        and _is_name(keywords["pass_fds"].elts[0], "gate_read_fd")
        and _is_name(keywords["pass_fds"].elts[1], "liveness_read_fd")
        and isinstance(keywords["start_new_session"], ast.Constant)
        and keywords["start_new_session"].value is True
        and isinstance(keywords["shell"], ast.Constant)
        and keywords["shell"].value is False
    )


def _exact_inventory_call(call: ast.Call) -> bool:
    keywords = _keyword_map(call)
    if keywords is None or set(keywords) != {
        "cwd",
        "env",
        "stdin",
        "stdout",
        "stderr",
        "timeout",
        "check",
        "shell",
    }:
        return False
    if len(call.args) != 1 or not isinstance(call.args[0], ast.List):
        return False
    argv = call.args[0].elts
    expected_constants = ("/bin/ps", "-o", "pid=,pgid=,uid=,stat=", "-g")
    if len(argv) != 5 or any(
        not isinstance(argv[index], ast.Constant) or argv[index].value != expected
        for index, expected in enumerate(expected_constants)
    ):
        return False
    env = keywords["env"]
    return (
        isinstance(argv[4], ast.Call)
        and _is_name(argv[4].func, "str")
        and len(argv[4].args) == 1
        and _is_name(argv[4].args[0], "process_group_id")
        and isinstance(keywords["cwd"], ast.Constant)
        and keywords["cwd"].value == "/"
        and isinstance(env, ast.Dict)
        and len(env.keys) == 2
        and {
            key.value: value.value
            for key, value in zip(env.keys, env.values, strict=True)
            if isinstance(key, ast.Constant) and isinstance(value, ast.Constant)
        }
        == {"PATH": "/usr/bin:/bin", "LC_ALL": "C"}
        and _is_attribute(keywords["stdin"], "subprocess", "DEVNULL")
        and _is_attribute(keywords["stdout"], "subprocess", "PIPE")
        and _is_attribute(keywords["stderr"], "subprocess", "DEVNULL")
        and _is_name(
            keywords["timeout"],
            "MATRIX_HARNESS_PROCESS_INVENTORY_TIMEOUT_SECONDS",
        )
        and isinstance(keywords["check"], ast.Constant)
        and keywords["check"].value is False
        and isinstance(keywords["shell"], ast.Constant)
        and keywords["shell"].value is False
    )


def _function_node(tree: ast.Module, name: str) -> ast.FunctionDef | None:
    matches = [
        node
        for node in ast.walk(tree)
        if isinstance(node, ast.FunctionDef) and node.name == name
    ]
    return matches[0] if len(matches) == 1 else None


def _is_self_call(node: ast.AST, method: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and _is_name(node.func.value, "self")
        and node.func.attr == method
    )


def _exact_containment_control_flow(
    tree: ast.Module,
    parent_by_node: dict[ast.AST, ast.AST],
) -> bool:
    spawn = _function_node(tree, "_spawn")
    terminate = _function_node(tree, "_terminate_process_group")
    communicate = _function_node(tree, "_communicate_bounded")
    if spawn is None or terminate is None or communicate is None:
        return False

    spawn_tries = [
        statement for statement in spawn.body if isinstance(statement, ast.Try)
    ]
    if len(spawn_tries) != 1:
        return False
    spawn_try = spawn_tries[0]
    capture_exprs = [
        statement
        for statement in spawn_try.body
        if isinstance(statement, ast.Expr)
        and _is_self_call(statement.value, "_capture_process_group")
        and len(statement.value.args) == 1
        and _is_name(statement.value.args[0], "process")
    ]
    liveness_blocks = [
        statement
        for statement in spawn_try.body
        if isinstance(statement, ast.With)
        and len(statement.items) == 1
        and isinstance(statement.items[0].context_expr, ast.Attribute)
        and _is_name(statement.items[0].context_expr.value, "self")
        and statement.items[0].context_expr.attr == "_process_group_lock"
        and len(statement.body) == 1
        and isinstance(statement.body[0], ast.Assign)
        and len(statement.body[0].targets) == 1
        and isinstance(statement.body[0].targets[0], ast.Subscript)
        and isinstance(statement.body[0].targets[0].value, ast.Attribute)
        and _is_name(statement.body[0].targets[0].value.value, "self")
        and statement.body[0].targets[0].value.attr == "_process_liveness_write_fds"
        and _is_name(statement.body[0].value, "liveness_write_fd")
    ]
    if len(capture_exprs) != 1 or len(liveness_blocks) != 1:
        return False

    runtime_group_signals: dict[str, list[ast.Expr]] = {"SIGTERM": [], "SIGKILL": []}
    for statement in terminate.body:
        if not isinstance(statement, ast.Expr) or not _is_self_call(
            statement.value, "_signal_process_group"
        ):
            continue
        if len(statement.value.args) != 2:
            continue
        signal_arg = statement.value.args[1]
        if (
            isinstance(signal_arg, ast.Attribute)
            and _is_name(signal_arg.value, "signal")
            and signal_arg.attr in runtime_group_signals
        ):
            runtime_group_signals[signal_arg.attr].append(statement)
    if any(len(statements) != 1 for statements in runtime_group_signals.values()):
        return False
    if (
        runtime_group_signals["SIGTERM"][0].lineno
        >= runtime_group_signals["SIGKILL"][0].lineno
    ):
        return False

    output_limit_checks = [
        node
        for node in ast.walk(communicate)
        if isinstance(node, ast.If)
        and isinstance(node.test, ast.Compare)
        and _is_name(node.test.left, "total_bytes")
        and len(node.test.ops) == 1
        and isinstance(node.test.ops[0], ast.Gt)
        and len(node.test.comparators) == 1
        and _is_name(
            node.test.comparators[0],
            "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES",
        )
    ]
    if len(output_limit_checks) != 1:
        return False
    output_limit = output_limit_checks[0]
    if not any(
        isinstance(node, ast.Raise)
        and isinstance(node.exc, ast.Call)
        and _is_name(node.exc.func, "MatrixHarnessBackendError")
        and node.exc.args
        and isinstance(node.exc.args[0], ast.Constant)
        and node.exc.args[0].value == "MATRIX_HARNESS_OUTPUT_LIMIT_EXCEEDED"
        for node in output_limit.body
    ):
        return False

    # None of the exact containment statements may be hidden beneath a
    # constant-false control-flow decoy.
    for node in (
        capture_exprs[0],
        liveness_blocks[0],
        runtime_group_signals["SIGTERM"][0],
        runtime_group_signals["SIGKILL"][0],
        output_limit,
    ):
        parent = parent_by_node.get(node)
        while parent is not None:
            if (
                isinstance(parent, ast.If)
                and isinstance(parent.test, ast.Constant)
                and parent.test.value is False
            ):
                return False
            parent = parent_by_node.get(parent)
    return True


def _exact_reviewed_subprocess_surface(source: str) -> bool:
    try:
        tree = ast.parse(source)
    except (SyntaxError, ValueError):
        return False
    gate_values = [
        node.value.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Assign)
        and len(node.targets) == 1
        and _is_name(node.targets[0], "_MATRIX_HARNESS_SPAWN_GATE")
        and isinstance(node.value, ast.Constant)
        and isinstance(node.value.value, str)
    ]
    if len(gate_values) != 1:
        return False
    try:
        gate_tree = ast.parse(gate_values[0])
        reviewed_gate_tree = ast.parse(_REVIEWED_SPAWN_GATE_SOURCE)
    except (SyntaxError, ValueError):
        return False
    if ast.dump(gate_tree, include_attributes=False) != ast.dump(
        reviewed_gate_tree,
        include_attributes=False,
    ):
        return False

    parent_by_node = {
        child: parent
        for parent in ast.walk(tree)
        for child in ast.iter_child_nodes(parent)
    }
    subprocess_imports = [
        alias
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
        if alias.name == "subprocess"
    ]
    if len(subprocess_imports) != 1 or subprocess_imports[0].asname is not None:
        return False
    if any(
        isinstance(node, ast.ImportFrom) and node.module == "subprocess"
        for node in ast.walk(tree)
    ):
        return False

    subprocess_attributes = Counter(
        node.attr for node in ast.walk(tree) if _is_subprocess_attribute(node)
    )
    if subprocess_attributes != _REVIEWED_SUBPROCESS_ATTRIBUTES:
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Name) or node.id != "subprocess":
            continue
        parent = parent_by_node.get(node)
        if not (
            isinstance(parent, ast.Attribute)
            and parent.value is node
            and parent.attr in _REVIEWED_SUBPROCESS_ATTRIBUTES
        ):
            return False

    call_sites: Counter[tuple[str, str]] = Counter()
    reviewed_calls: dict[tuple[str, str], list[ast.Call]] = {}
    spawn_node: ast.FunctionDef | None = None
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if node.name == "_spawn" and isinstance(node, ast.FunctionDef):
            if spawn_node is not None:
                return False
            spawn_node = node
        for descendant in ast.walk(node):
            if not isinstance(descendant, ast.Call) or not _is_subprocess_attribute(
                descendant.func
            ):
                continue
            nearest_function = node
            parent = parent_by_node.get(descendant)
            while parent is not None and parent is not node:
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    nearest_function = parent
                    break
                parent = parent_by_node.get(parent)
            if nearest_function is node:
                key = (node.name, descendant.func.attr)
                call_sites[key] += 1
                reviewed_calls.setdefault(key, []).append(descendant)
    if call_sites != _REVIEWED_SUBPROCESS_CALLS or spawn_node is None:
        return False
    spawn_calls = reviewed_calls.get(("_spawn", "Popen"), [])
    inventory_calls = reviewed_calls.get(("_process_group_inventory", "run"), [])
    if (
        len(spawn_calls) != 1
        or not _exact_spawn_call(spawn_calls[0])
        or len(inventory_calls) != 1
        or not _exact_inventory_call(inventory_calls[0])
    ):
        return False
    if not _exact_containment_control_flow(tree, parent_by_node):
        return False

    capture_calls = [
        node
        for node in ast.walk(spawn_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "self"
        and node.func.attr == "_capture_process_group"
    ]
    gate_release_calls = [
        node
        for node in ast.walk(spawn_node)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == "os"
        and node.func.attr == "write"
        and len(node.args) == 2
        and isinstance(node.args[0], ast.Name)
        and node.args[0].id == "gate_write_fd"
        and isinstance(node.args[1], ast.Constant)
        and node.args[1].value == b"1"
    ]
    return (
        len(capture_calls) == 1
        and len(gate_release_calls) == 1
        and capture_calls[0].lineno < gate_release_calls[0].lineno
    )


def is_exact_matrix_harness_subprocess_site(
    *, rel_path: str, source: str, fragment: str
) -> bool:
    """Allow only the reviewed fixed-argv, local Docker harness boundary."""

    if rel_path != MATRIX_HARNESS_BACKEND_REL:
        return False
    if fragment not in {_SUBPROCESS_POPEN, _SUBPROCESS_RUN}:
        return False
    if hashlib.sha256(source.encode("utf-8")).hexdigest() != _REVIEWED_BACKEND_SHA256:
        return False
    required = (
        "MATRIX_HARNESS_DOCKER_BINARY_ABSOLUTE_REQUIRED",
        "MATRIX_HARNESS_DOCKER_BINARY_UNSAFE",
        '"--project-name",\n            "uaa-matrix-harness",',
        '"--pull",\n                "never",',
        '_MATRIX_HARNESS_SPAWN_GATE = """',
        "token = os.read(gate_fd, 1)",
        "liveness_fd = int(sys.argv[2])",
        "watchdog_pid = os.fork()",
        "if not os.read(liveness_fd, 1):",
        "os.killpg(os.getpgrp(), signal.SIGTERM)",
        "os.killpg(os.getpgrp(), signal.SIGKILL)",
        "gate_read_fd, gate_write_fd = os.pipe()",
        "liveness_read_fd, liveness_write_fd = os.pipe()",
        "pass_fds=(gate_read_fd, liveness_read_fd)",
        "self._capture_process_group(process)",
        "self._process_liveness_write_fds[process] = liveness_write_fd",
        ("inventory = self._process_group_inventory(process, process_group_id)"),
        ("self._signal_process_group(process_group_id, signal.SIGTERM)"),
        ("self._signal_process_group(process_group_id, signal.SIGKILL)"),
        "result = " + _SUBPROCESS_RUN,
        '"/bin/ps",',
        '"pid=,pgid=,uid=,stat=",',
        "MATRIX_HARNESS_PROCESS_INVENTORY_TIMEOUT_SECONDS = 1.0",
        "MATRIX_HARNESS_PROCESS_INVENTORY_LIMIT_BYTES = 16 * 1024",
        "MATRIX_HARNESS_PROCESS_GROUP_MEMBER_LIMIT = 64",
        'cwd="/"',
        'env={"PATH": "/usr/bin:/bin", "LC_ALL": "C"}',
        "check=False",
        "start_new_session=True",
        "shell=False",
        "stdin=" + "subprocess" + ".DEVNULL",
        "stdout=" + "subprocess" + ".PIPE",
        "stderr=" + "subprocess" + ".PIPE",
        "MATRIX_HARNESS_OUTPUT_LIMIT_BYTES = 64 * 1024",
        "if total_bytes > MATRIX_HARNESS_OUTPUT_LIMIT_BYTES:",
    )
    forbidden = (
        "shell" + "=True",
        "os" + ".system(",
        "subprocess" + ".call(",
        "subprocess" + ".check_call(",
        "subprocess" + ".check_output(",
        "subprocess" + ".getoutput(",
        "subprocess" + ".getstatusoutput(",
        "import " + "requests",
        "import " + "httpx",
        "import " + "urllib",
        "socket" + ".socket(",
    )
    return (
        source.count(_SUBPROCESS_POPEN) == 1
        and source.count(_SUBPROCESS_RUN) == 1
        and all(marker in source for marker in required)
        and not any(marker in source for marker in forbidden)
        and _exact_reviewed_subprocess_surface(source)
    )


def is_exact_matrix_harness_shell_scan_line(
    *, rel_path: str, source: str, stripped_line: str
) -> bool:
    if not is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=_SUBPROCESS_POPEN,
    ):
        return False
    return (
        stripped_line == "import " + "subprocess" or "subprocess" + "." in stripped_line
    )


def matrix_harness_fragment_allowed(rel_path: str, source: str, fragment: str) -> bool:
    if fragment == "import " + "subprocess":
        fragment = _SUBPROCESS_POPEN
    return is_exact_matrix_harness_subprocess_site(
        rel_path=rel_path,
        source=source,
        fragment=fragment,
    )


__all__ = (
    "MATRIX_HARNESS_BACKEND_REL",
    "is_exact_matrix_harness_shell_scan_line",
    "is_exact_matrix_harness_subprocess_site",
    "matrix_harness_fragment_allowed",
)
