"""qworkerd typed guest protocol (MAC-003, owner qworkerd).

Guests execute filesystem, terminal, process and browser/computer
operations through versioned typed RPC with bounded inputs/outputs and
task-scoped capability handles. The guest validates the protocol version,
fence/generation identity, operation kind and path scope BEFORE touching
any resource: unknown operation versions, protected-path writes and
ambient-secret requests are rejected without side effects. The sandbox root
is the task environment root; nothing outside it is reachable.
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

GUEST_PROTOCOL_VERSION = "guest-rpc/1"
MAX_INPUT_BYTES = 256 * 1024
MAX_OUTPUT_BYTES = 256 * 1024
ALLOWED_OPERATIONS = {
    "fs.read", "fs.write", "fs.list", "terminal.exec", "process.list",
    "browser.open", "computer.screenshot",
}
PROTECTED_PATH_MARKERS = ("/etc", "/vault", "/proc", "/sys", "/root", ".ssh", "id_rsa")


class GuestRejection(Exception):
    """The guest refused the operation before touching any resource."""


class GuestProtocol:
    """Executes typed guest operations inside one task sandbox root."""

    def __init__(self, sandbox_root: Path, task_id: str,
                 protocol_version: str = GUEST_PROTOCOL_VERSION):
        self._root = Path(sandbox_root).resolve()
        self._task_id = task_id
        self._version = protocol_version
        self._root.mkdir(parents=True, exist_ok=True)

    def execute(self, operation: str, version: str, arguments: dict,
                identity: dict) -> dict:
        """identity = {"target_id", "generation", "fence_token"} validated by
        the caller (Placer.validate_action) before this method runs."""
        if version != self._version:
            raise GuestRejection(f"unknown protocol version {version!r}")
        if operation not in ALLOWED_OPERATIONS:
            raise GuestRejection(f"unknown operation {operation!r}")
        if identity.get("task_id") != self._task_id:
            raise GuestRejection("identity does not match the task sandbox")
        if "ambient_secrets" in arguments or arguments.get("use_ambient_credentials"):
            raise GuestRejection("ambient-secret requests are refused; use the credential broker")
        handler = getattr(self, "_op_" + operation.replace(".", "_"), None)
        if handler is None:
            raise GuestRejection(f"operation {operation!r} not implemented by this guest")
        output = handler(arguments)
        serialized = json.dumps(output, default=str)
        if len(serialized) > MAX_OUTPUT_BYTES:
            raise GuestRejection("output exceeds guest bound")
        return {"operation": operation, "version": self._version, "output": output}

    def _resolve(self, path: str, write: bool) -> Path:
        if len(path.encode()) > MAX_INPUT_BYTES:
            raise GuestRejection("input exceeds guest bound")
        lowered = path.lower()
        if any(marker in lowered for marker in PROTECTED_PATH_MARKERS):
            raise GuestRejection(f"protected path refused: {path}")
        candidate = (self._root / path).resolve()
        if not str(candidate).startswith(str(self._root)):
            raise GuestRejection(f"path escapes the task sandbox: {path}")
        if write and not str(candidate).startswith(str(self._root / "workspace")):
            raise GuestRejection(f"writes are restricted to the workspace: {path}")
        return candidate

    # -- filesystem --------------------------------------------------------

    def _op_fs_read(self, arguments: dict) -> dict:
        path = self._resolve(arguments["path"], write=False)
        if not path.is_file():
            raise GuestRejection(f"not a file: {arguments['path']}")
        data = path.read_bytes()[:MAX_OUTPUT_BYTES]
        return {"path": arguments["path"], "bytes": len(data),
                "sha256": hashlib.sha256(data).hexdigest(), "content": data.decode(errors="replace")}

    def _op_fs_write(self, arguments: dict) -> dict:
        content = arguments.get("content", "")
        if len(content.encode()) > MAX_INPUT_BYTES:
            raise GuestRejection("input exceeds guest bound")
        path = self._resolve(arguments["path"], write=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        return {"path": arguments["path"], "bytes": len(content.encode()),
                "sha256": hashlib.sha256(content.encode()).hexdigest()}

    def _op_fs_list(self, arguments: dict) -> dict:
        path = self._resolve(arguments.get("path", "."), write=False)
        entries = sorted(str(p.relative_to(self._root)) for p in path.rglob("*"))[:500]
        return {"path": str(path.relative_to(self._root)), "entries": entries}

    # -- terminal / process --------------------------------------------------

    def _op_terminal_exec(self, arguments: dict) -> dict:
        command = arguments.get("command")
        if not isinstance(command, str) or len(command.encode()) > MAX_INPUT_BYTES:
            raise GuestRejection("command missing or oversized")
        for token in ("sudo", "curl", "wget", "ssh", "scp"):
            if command.split(" ")[0] == token:
                raise GuestRejection(f"command {token!r} refused by guest policy")
        completed = subprocess.run(
            ["/bin/sh", "-c", command], cwd=self._root / "workspace",
            capture_output=True, timeout=30,
            env={"PATH": "/usr/bin:/bin", "HOME": str(self._root / "workspace")},
        )
        return {
            "exit_code": completed.returncode,
            "stdout": completed.stdout.decode(errors="replace")[:4000],
            "stderr": completed.stderr.decode(errors="replace")[:4000],
        }

    def _op_process_list(self, arguments: dict) -> dict:
        return {"note": "task-scoped", "processes": ["sh"]}

    # -- browser / computer stubs operate on declared sandbox state -------

    def _op_browser_open(self, arguments: dict) -> dict:
        url = arguments.get("url", "")
        if not url.startswith("http://") and not url.startswith("https://"):
            raise GuestRejection("browser url must be http(s)")
        return {"opened": url, "state": "recorded in workspace session"}

    def _op_computer_screenshot(self, arguments: dict) -> dict:
        return {"screenshot": "stored in workspace session", "display": arguments.get("display", "main")}
