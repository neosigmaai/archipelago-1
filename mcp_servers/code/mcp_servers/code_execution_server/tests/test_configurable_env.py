"""Env overrides for blocked paths and the HTTP bind host.

Both values are read at import or startup, so each case runs in a fresh
interpreter instead of reloading modules other tests already hold.
"""

import json
import os
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent

PRINT_BLOCKED_PATHS = (
    "import json; from tools.code_exec import BLOCKED_PATHS; "
    "print(json.dumps(BLOCKED_PATHS))"
)
# Runs main.py as __main__ with FastMCP.run stubbed to report its host.
PRINT_MCP_HOST = (
    "import runpy, sys; from fastmcp import FastMCP; "
    "FastMCP.run = lambda self, *args, **kwargs: print(kwargs.get('host')); "
    "runpy.run_path(sys.argv[1], run_name='__main__')"
)


def _last_stdout_line(code: str, *args: str, **env: str) -> str:
    child_env = {
        key: value
        for key, value in os.environ.items()
        if key not in {"CODE_EXEC_BLOCKED_PATHS", "MCP_HOST", "MCP_TRANSPORT"}
    }
    child_env.update(PYTHONPATH=str(SERVER_DIR), **env)
    result = subprocess.run(
        [sys.executable, "-c", code, *args],
        cwd=SERVER_DIR,
        env=child_env,
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout.strip().splitlines()[-1]


def test_blocked_paths_default_unchanged():
    assert json.loads(_last_stdout_line(PRINT_BLOCKED_PATHS)) == [
        "/app",
        "/.apps_data",
        "/proc",
        "/sys",
    ]


def test_blocked_paths_from_env():
    paths = _last_stdout_line(
        PRINT_BLOCKED_PATHS, CODE_EXEC_BLOCKED_PATHS="/.apps_data:/proc::/sys"
    )
    assert json.loads(paths) == ["/.apps_data", "/proc", "/sys"]


def test_mcp_host_default_and_override():
    main = str(SERVER_DIR / "main.py")
    # Run-as-user mode skips the sandbox_fs.so startup check.
    env = {"CODE_EXEC_RUN_AS_USER": "nobody"}
    assert _last_stdout_line(PRINT_MCP_HOST, main, **env) == "0.0.0.0"
    assert (
        _last_stdout_line(PRINT_MCP_HOST, main, MCP_HOST="127.0.0.1", **env)
        == "127.0.0.1"
    )
