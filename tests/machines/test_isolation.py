"""Execution isolation demonstration (MAC-005/QA-005).

The guest's enforced isolation boundary, demonstrated behaviorally:
filesystem scope (deny-by-default path resolution), protected paths,
ambient-secret refusal, environment sanitization for terminal execution
(no host identity or ambient credentials leak into the guest), and the
typed operation allow-list, which contains no raw network operation.
Network egress policy is enforced on top of this boundary at the deployment
layer (the qworkerd container profile denies external egress); within the
process boundary the guest cannot request network access at all.
"""

from __future__ import annotations

import sys
import uuid
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO_ROOT))

from quansio.qworkerd.protocol import (  # noqa: E402
    ALLOWED_OPERATIONS,
    GuestProtocol,
    GuestRejection,
)


def _guest(tmp_path, monkeypatch) -> GuestProtocol:
    # The host process carries ambient material that must NOT reach the guest.
    monkeypatch.setenv("QUAL_PG_APP_PASSWORD", "ambient-secret-value")
    monkeypatch.setenv("QUANSIO_AMBIENT_MARKER", "host-identity")
    return GuestProtocol(tmp_path / "task" / "workspace", "isolation-task")


def test_mac005_p02_filesystem_scope_is_deny_by_default(tmp_path, monkeypatch):
    guest = _guest(tmp_path, monkeypatch)
    identity = {"task_id": "isolation-task"}
    # Writes inside the workspace work.
    guest.execute("fs.write", "guest-rpc/1",
                  {"path": "workspace/inside.txt", "content": "ok"}, identity)
    # Reads outside the sandbox root are refused; writes outside the
    # workspace subtree are refused even inside the root.
    with pytest.raises(GuestRejection, match="escapes the task sandbox"):
        guest.execute("fs.read", "guest-rpc/1",
                      {"path": str(tmp_path / "outside.txt")}, identity)
    with pytest.raises(GuestRejection, match="restricted to the workspace"):
        guest.execute("fs.write", "guest-rpc/1",
                      {"path": "root-level.txt", "content": "x"}, identity)


def test_mac005_n01_no_ambient_secrets_or_host_identity_reach_guest(tmp_path, monkeypatch):
    guest = _guest(tmp_path, monkeypatch)
    identity = {"task_id": "isolation-task"}
    with pytest.raises(GuestRejection, match="ambient-secret"):
        guest.execute("fs.read", "guest-rpc/1",
                      {"path": "workspace/x", "use_ambient_credentials": True}, identity)
    # Terminal execution runs with a sanitized environment: the ambient
    # secret and host marker are absent from the child process environment.
    result = guest.execute(
        "terminal.exec", "guest-rpc/1",
        {"command": "env"}, identity,
    )
    environment = result["output"]["stdout"]
    assert "ambient-secret-value" not in environment
    assert "host-identity" not in environment
    assert "QUAL_PG_APP_PASSWORD" not in environment


def test_mac005_p03_typed_protocol_has_no_raw_network_operation(tmp_path, monkeypatch):
    """The guest operation surface exposes no socket operation: the only
    remote-content operation is the browser stub, and direct network tools
    are refused by guest policy before execution."""
    _guest(tmp_path, monkeypatch)
    network_capable = {"curl", "wget", "ssh", "scp", "nc", "sudo"}
    # No allow-listed operation performs raw networking.
    assert not any("socket" in op or "net" in op for op in ALLOWED_OPERATIONS)
    # Network tools are refused as terminal commands (policy check runs
    # before any side effect).
    for token in ("curl", "wget", "ssh"):
        guest = GuestProtocol(Path(tmp_path) / "task" / "workspace", "isolation-task")
        with pytest.raises(GuestRejection, match="refused by guest policy"):
            guest.execute("terminal.exec", "guest-rpc/1",
                          {"command": f"{token} http://example.invalid"}, {"task_id": "isolation-task"})
    assert network_capable
