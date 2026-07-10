from __future__ import annotations

import http.client
import json
import threading
from pathlib import Path

import pytest
from codex_pipeline.permission_server import create_control_server


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "target"
    project.mkdir()
    return project


def _request(
    connection: http.client.HTTPConnection,
    method: str,
    path: str,
    *,
    payload: dict[str, str] | None = None,
    csrf_token: str | None = None,
    host_header: str | None = None,
) -> tuple[int, bytes]:
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    if csrf_token is not None:
        headers["X-CSRF-Token"] = csrf_token
    if host_header is not None:
        headers["Host"] = host_header
    connection.request(method, path, body=body, headers=headers)
    response = connection.getresponse()
    return response.status, response.read()


def test_server_is_loopback_only_and_mutations_require_csrf(tmp_path: Path) -> None:
    project = _project(tmp_path)
    server = create_control_server(
        project,
        control_home=tmp_path / "control",
        host="127.0.0.1",
        port=0,
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address[:2]
    connection = http.client.HTTPConnection(host, port, timeout=5)
    try:
        status, body = _request(
            connection,
            "GET",
            "/api/state",
            host_header="attacker.example",
        )
        assert status == 403
        assert json.loads(body)["error"] == "invalid Host header"

        status, body = _request(connection, "GET", "/api/state")
        assert status == 200
        state = json.loads(body)
        assert state["project"]["id"] == "target"

        status, body = _request(
            connection,
            "POST",
            "/api/set",
            payload={"gate_id": "github_write", "value": "allow"},
        )
        assert status == 403
        assert json.loads(body)["error"] == "invalid CSRF token"

        status, body = _request(
            connection,
            "POST",
            "/api/set",
            payload={"gate_id": "github_write", "value": "allow"},
            csrf_token=server.csrf_token,
        )
        assert status == 200
        state = json.loads(body)
        github_gate = next(gate for gate in state["gates"] if gate["gate_id"] == "github_write")
        assert github_gate["current"] == "allow"

        status, body = _request(
            connection,
            "POST",
            "/api/recommend",
            payload={
                "gate_id": "network_external_fetch",
                "value": "allow",
                "reason": "Codex found a scoped read-only route",
            },
            csrf_token=server.csrf_token,
        )
        assert status == 200
        state = json.loads(body)
        network_gate = next(
            gate for gate in state["gates"] if gate["gate_id"] == "network_external_fetch"
        )
        assert network_gate["recommendation"]["value"] == "allow"

        status, body = _request(
            connection,
            "POST",
            "/api/bulk",
            payload={"action": "apply-recommendations"},
            csrf_token=server.csrf_token,
        )
        assert status == 200
        state = json.loads(body)
        network_gate = next(
            gate for gate in state["gates"] if gate["gate_id"] == "network_external_fetch"
        )
        assert network_gate["current"] == "allow"

        status, body = _request(connection, "GET", "/")
        assert status == 200
        html = body.decode("utf-8")
        assert "Codex Permission Control" in html
        assert "Apply Codex recommendations" in html
        assert "confirm_each and fixed gates" in html
    finally:
        connection.close()
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    with pytest.raises(ValueError, match="loopback"):
        create_control_server(project, host="0.0.0.0")
    with pytest.raises(ValueError, match="loopback IP"):
        create_control_server(project, host="localhost")
    with pytest.raises(ValueError, match="outside the target project root"):
        create_control_server(project, control_home=project / ".control")
