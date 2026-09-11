"""Packaged command-line client (UX-008) over canonical server APIs.

Every command talks to a canonical service with the stored bearer token;
the CLI never resolves identity, executes work or mutates canonical state
locally. The token file is created with owner-only permissions.
"""

from __future__ import annotations

import argparse
import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

import httpx

CONFIG_DIR = Path(os.environ.get("QUANSIO_CLI_HOME", Path.home() / ".quansio"))
CONFIG_PATH = CONFIG_DIR / "cli.json"

DEFAULT_URLS = {
    "api": "http://127.0.0.1:8080",
    "runtime": "http://127.0.0.1:8087",
    "control": "http://127.0.0.1:8081",
    "artifact": "http://127.0.0.1:8088",
    "notify": "http://127.0.0.1:8089",
}


class CliError(SystemExit):
    def __init__(self, message: str, code: int = 1):
        super().__init__(code)
        self.message = message


def load_state() -> dict[str, Any]:
    if CONFIG_PATH.is_file():
        return json.loads(CONFIG_PATH.read_text())
    return {"urls": dict(DEFAULT_URLS)}


def save_state(state: dict[str, Any]) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(state, indent=2, sort_keys=True) + "\n")
    os.chmod(CONFIG_PATH, stat.S_IRUSR | stat.S_IWUSR)


def _client(state: dict[str, Any]) -> httpx.Client:
    return httpx.Client(timeout=15.0)


def _headers(state: dict[str, Any]) -> dict[str, str]:
    token = state.get("token")
    if not token:
        raise CliError("not logged in; run `quansio login` first")
    return {"Authorization": f"Bearer {token}"}


def _request(state: dict[str, Any], method: str, service: str, path: str,
             *, json_body: Any | None = None, params: Any | None = None,
             data: bytes | None = None, extra_headers: dict | None = None,
             auth: bool = True) -> Any:
    url = state["urls"].get(service, DEFAULT_URLS[service]) + path
    headers = {**(_headers(state) if auth else {}), **(extra_headers or {})}
    try:
        response = httpx.request(
            method, url, json=json_body, params=params, content=data,
            headers=headers, timeout=15.0,
        )
    except httpx.HTTPError as error:
        raise CliError(f"{service} unreachable: {error}") from error
    if response.status_code >= 400:
        detail = response.json().get("detail") if response.content else response.text
        raise CliError(f"{method} {path} -> {response.status_code}: {detail}")
    return response.json() if response.content else {}


# -- commands ---------------------------------------------------------------


def cmd_login(args: argparse.Namespace) -> dict:
    state = load_state()
    result = _request(state, "POST", "api", "/v9/sessions", json_body={
        "tenant_id": args.tenant_id,
        "workspace_id": args.workspace_id,
        "email": args.email,
        "password": args.password,
    }, auth=False)
    state["token"] = result["token"]
    state["identity"] = result["identity"]
    save_state(state)
    return {"logged_in": True, "identity": result["identity"],
            "credentials": str(CONFIG_PATH)}


def cmd_logout(args: argparse.Namespace) -> dict:
    state = load_state()
    _request(state, "DELETE", "api", "/v9/sessions/current")
    state.pop("token", None)
    state.pop("identity", None)
    save_state(state)
    return {"logged_out": True}


def cmd_whoami(args: argparse.Namespace) -> dict:
    state = load_state()
    return _request(state, "GET", "api", "/v9/identity")


def cmd_task_start(args: argparse.Namespace) -> dict:
    state = load_state()
    return _request(state, "POST", "api", "/v9/commands", json_body={
        "command_type": "task.start",
        "arguments": {"objective": args.objective},
        "idempotency_key": args.idempotency_key or f"cli-{os.getpid()}-{args.objective[:16]}",
    })


def cmd_task_status(args: argparse.Namespace) -> dict:
    state = load_state()
    run = _request(state, "GET", "runtime", f"/v9/runs/{args.run_id}")
    events = _request(state, "GET", "runtime", "/v9/events",
                      params={"run_id": args.run_id, "after_sequence": 0})
    run_view = run["run"]
    run_view["latest_events"] = [e["event_type"] for e in events["events"][-5:]]
    return run_view


def cmd_task_cancel(args: argparse.Namespace) -> dict:
    state = load_state()
    return _request(state, "POST", "runtime", f"/v9/runs/{args.run_id}/cancel")


def cmd_approval_respond(args: argparse.Namespace) -> dict:
    state = load_state()
    identity = cmd_whoami(args)["identity"]
    return _request(state, "POST", "control",
                    f"/v9/approvals/{args.approval_id}/decision",
                    json_body={
                        "approved": args.decision == "approve",
                        "approver_id": identity["user_id"],
                    })


def cmd_artifact_get(args: argparse.Namespace) -> dict:
    state = load_state()
    return _request(state, "GET", "artifact",
                    f"/v9/artifacts/{args.digest}/metadata")


def cmd_events_follow(args: argparse.Namespace) -> dict:
    """Follow canonical events from the stored cursor; only missing events
    are applied and the cursor is advanced for the next invocation."""
    state = load_state()
    cursor = args.cursor if args.cursor is not None else int(state.get("cursors", {}).get(args.run_id, 0))
    events = _request(state, "GET", "runtime", "/v9/events",
                      params={"run_id": args.run_id, "after_sequence": cursor,
                              "consumer": "cli"})
    applied = events["events"]
    if applied:
        last = applied[-1]["sequence"]
        _request(state, "POST", "runtime", "/v9/events/cursors",
                 params={"run_id": args.run_id, "consumer": "cli",
                         "last_sequence": last})
        cursors = state.setdefault("cursors", {})
        cursors[args.run_id] = last
        save_state(state)
    return {"run_id": args.run_id, "applied": len(applied),
            "cursor": cursors_next(state, args.run_id, cursor, applied)}


def cursors_next(state: dict, run_id: str, previous: int, applied: list) -> int:
    return applied[-1]["sequence"] if applied else previous


def cmd_notifications(args: argparse.Namespace) -> dict:
    state = load_state()
    identity = cmd_whoami(args)["identity"]
    return _request(state, "GET", "notify", "/v9/notifications",
                    params={"recipient_id": identity["identity"]["user_id"],
                            "state": args.state})


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quansio",
        description="Quansio V9 command-line client (thin projection over canonical APIs)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    login = sub.add_parser("login", help="authenticate and store the session token")
    login.add_argument("--tenant-id", required=True)
    login.add_argument("--workspace-id", required=True)
    login.add_argument("--email", required=True)
    login.add_argument("--password", required=True)
    login.set_defaults(func=cmd_login)

    logout = sub.add_parser("logout", help="revoke the current session")
    logout.set_defaults(func=cmd_logout)

    whoami = sub.add_parser("whoami", help="show the server-resolved identity")
    whoami.set_defaults(func=cmd_whoami)

    task = sub.add_parser("task")
    task_sub = task.add_subparsers(dest="task_command", required=True)
    start = task_sub.add_parser("start")
    start.add_argument("--objective", required=True)
    start.add_argument("--idempotency-key", default=None)
    start.set_defaults(func=cmd_task_start)
    status = task_sub.add_parser("status")
    status.add_argument("--run-id", required=True)
    status.set_defaults(func=cmd_task_status)
    cancel = task_sub.add_parser("cancel")
    cancel.add_argument("--run-id", required=True)
    cancel.set_defaults(func=cmd_task_cancel)

    approval = sub.add_parser("approval")
    approval.add_argument("--approval-id", required=True)
    approval.add_argument("--decision", choices=["approve", "deny"], required=True)
    approval.set_defaults(func=cmd_approval_respond)

    artifact = sub.add_parser("artifact")
    artifact.add_argument("--digest", required=True)
    artifact.set_defaults(func=cmd_artifact_get)

    follow = sub.add_parser("follow")
    follow.add_argument("--run-id", required=True)
    follow.add_argument("--cursor", type=int, default=None)
    follow.set_defaults(func=cmd_events_follow)

    notifications = sub.add_parser("notifications")
    notifications.add_argument("--state", default=None)
    notifications.set_defaults(func=cmd_notifications)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        result = args.func(args)
    except CliError as error:
        print(error.message, file=sys.stderr)
        return error.code if isinstance(error.code, int) else 1
    print(json.dumps(result, indent=2, sort_keys=True, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
