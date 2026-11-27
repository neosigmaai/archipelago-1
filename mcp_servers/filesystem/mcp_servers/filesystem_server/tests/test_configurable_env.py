"""Env overrides for the filesystem root and the HTTP bind host.

Both values are read at import or startup, so each case runs in a fresh
interpreter instead of reloading modules other tests already hold.
"""

import os
import subprocess
import sys
from pathlib import Path

SERVER_DIR = Path(__file__).resolve().parent.parent

PRINT_FILESYSTEM_ROOT = (
    "from mcp_actor import paths; print(paths.TARGET_AGENT_FILESYSTEM_ROOT)"
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
        if key not in {"APP_FS_ROOT", "MCP_HOST", "MCP_TRANSPORT"}
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


def test_filesystem_root_default():
    assert _last_stdout_line(PRINT_FILESYSTEM_ROOT) == "/filesystem"


def test_filesystem_root_from_app_fs_root(tmp_path):
    root = str(tmp_path)
    assert _last_stdout_line(PRINT_FILESYSTEM_ROOT, APP_FS_ROOT=root) == root


def test_mcp_host_default_and_override():
    main = str(SERVER_DIR / "main.py")
    assert _last_stdout_line(PRINT_MCP_HOST, main) == "0.0.0.0"
    assert _last_stdout_line(PRINT_MCP_HOST, main, MCP_HOST="127.0.0.1") == "127.0.0.1"
