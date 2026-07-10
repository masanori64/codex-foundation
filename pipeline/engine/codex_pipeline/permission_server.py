from __future__ import annotations

import html
import ipaddress
import json
import secrets
import socket
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from .permission_control import (
    build_control_snapshot,
    bulk_update_toggles,
    set_recommendation,
    set_toggle,
)

MAX_REQUEST_BYTES = 64 * 1024


class PermissionControlServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler: type[BaseHTTPRequestHandler],
        *,
        project_root: Path,
        control_home: Path | None,
        csrf_token: str,
    ) -> None:
        super().__init__(server_address, handler)
        self.project_root = project_root
        self.control_home = control_home
        self.csrf_token = csrf_token


class IPv6PermissionControlServer(PermissionControlServer):
    address_family = socket.AF_INET6


def create_control_server(
    project_root: str | Path,
    *,
    control_home: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 0,
) -> PermissionControlServer:
    address = _require_loopback_host(host)
    project = Path(project_root).expanduser().resolve()
    resolved_control_home = (
        Path(control_home).expanduser().resolve() if control_home is not None else None
    )
    build_control_snapshot(project, control_home=resolved_control_home)
    csrf_token = secrets.token_urlsafe(32)
    server_class = IPv6PermissionControlServer if address.version == 6 else PermissionControlServer
    return server_class(
        (host, port),
        _handler_class(),
        project_root=project,
        control_home=resolved_control_home,
        csrf_token=csrf_token,
    )


def serve_control_gui(
    project_root: str | Path,
    *,
    control_home: str | Path | None = None,
    host: str = "127.0.0.1",
    port: int = 8768,
    open_browser: bool = True,
) -> None:
    server = create_control_server(
        project_root,
        control_home=control_home,
        host=host,
        port=port,
    )
    raw_bound_host, bound_port = server.server_address[:2]
    bound_host = (
        raw_bound_host.decode("ascii")
        if isinstance(raw_bound_host, bytes)
        else raw_bound_host
    )
    display_host = f"[{bound_host}]" if ":" in bound_host else bound_host
    url = f"http://{display_host}:{bound_port}/"
    print(f"Codex permission control: {url}")
    try:
        if open_browser:
            webbrowser.open(url)
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


def render_interactive_control_html(snapshot: dict[str, Any], *, csrf_token: str) -> str:
    project_name = html.escape(str(snapshot["project"]["id"]), quote=True)
    initial_state = _safe_script_json(snapshot)
    csrf = json.dumps(csrf_token)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Codex Permission Control — {project_name}</title>
  <style>
    :root {{ color-scheme: light; font-family: system-ui, sans-serif; }}
    body {{ margin: 0; background: #f4f6f8; color: #18212b; }}
    header {{ background: #172033; color: white; padding: 18px 24px; }}
    main {{ max-width: 1180px; margin: auto; padding: 20px; }}
    .notice {{ background: #fff4d6; border: 1px solid #d99b00; padding: 10px 12px; }}
    .toolbar {{ display: flex; flex-wrap: wrap; gap: 8px; margin: 16px 0; }}
    button {{ border: 1px solid #8b98a7; border-radius: 5px; padding: 7px 10px; cursor: pointer; }}
    button.allow {{ background: #d9f8e5; }} button.deny {{ background: #ffe1e1; }}
    button.apply {{ background: #dbeafe; }} button:disabled {{ opacity: .45; cursor: default; }}
    table {{ width: 100%; border-collapse: collapse; background: white; }}
    th, td {{ border: 1px solid #d5dce3; padding: 8px; vertical-align: top; text-align: left; }}
    th {{ background: #e9eef3; position: sticky; top: 0; }}
    code {{ white-space: nowrap; }} .reason {{ min-width: 280px; }}
    .pill {{ display: inline-block; padding: 2px 7px; border-radius: 99px; background: #eef2f6; }}
    .error {{ color: #9b1c1c; font-weight: 700; }}
  </style>
</head>
<body>
  <header><h1>Codex Permission Control</h1><div>{project_name}</div></header>
  <main>
    <p class="notice">Persistent toggle controls live outside Git. confirm_each and fixed gates are displayed but never changed by bulk actions.</p>
    <div class="toolbar">
      <button class="allow" onclick="bulk('allow')">Allow all toggle gates</button>
      <button class="deny" onclick="bulk('deny')">Deny all toggle gates</button>
      <button class="apply" onclick="bulk('apply-recommendations')">Apply Codex recommendations</button>
      <span id="message"></span>
    </div>
    <table>
      <thead><tr><th>Gate</th><th>Mode</th><th>Current</th><th>Recommendation</th><th>Reason</th><th>Controls</th></tr></thead>
      <tbody id="gate-rows"></tbody>
    </table>
  </main>
  <script>
    const csrfToken = {csrf};
    let state = {initial_state};
    const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}}[c]));
    function controls(gate) {{
      if (gate.mode !== 'toggle') return '<span class="pill">not bulk-controllable</span>';
      return `<button class="allow" onclick="setGate('${{esc(gate.gate_id)}}','allow')">Allow</button> ` +
        `<button class="deny" onclick="setGate('${{esc(gate.gate_id)}}','deny')">Deny</button>`;
    }}
    function recommendation(gate) {{
      const item = gate.recommendation;
      if (!item) return 'none';
      return `<strong>${{esc(item.value)}}</strong><br>${{esc(item.reason)}}`;
    }}
    function render() {{
      document.getElementById('gate-rows').innerHTML = state.gates.map(gate => `<tr>` +
        `<td><strong>${{esc(gate.label)}}</strong><br><code>${{esc(gate.gate_id)}}</code><br><small>owner=${{esc(gate.owner)}}</small></td>` +
        `<td><span class="pill">${{esc(gate.mode)}}</span></td>` +
        `<td><strong>${{esc(gate.current)}}</strong></td>` +
        `<td>${{recommendation(gate)}}</td>` +
        `<td class="reason">${{esc(gate.reason)}}</td>` +
        `<td>${{controls(gate)}}</td></tr>`).join('');
    }}
    async function post(path, body) {{
      const response = await fetch(path, {{
        method: 'POST',
        headers: {{'Content-Type':'application/json', 'X-CSRF-Token':csrfToken}},
        body: JSON.stringify(body),
      }});
      const payload = await response.json();
      if (!response.ok) throw new Error(payload.error || `HTTP ${{response.status}}`);
      state = payload;
      render();
      document.getElementById('message').textContent = 'saved';
    }}
    async function setGate(gateId, value) {{
      try {{ await post('/api/set', {{gate_id:gateId, value, actor:'human-gui', reason:'interactive GUI'}}); }}
      catch (error) {{ document.getElementById('message').innerHTML = `<span class="error">${{esc(error.message)}}</span>`; }}
    }}
    async function bulk(action) {{
      try {{ await post('/api/bulk', {{action, actor:'human-gui', reason:'interactive GUI bulk action'}}); }}
      catch (error) {{ document.getElementById('message').innerHTML = `<span class="error">${{esc(error.message)}}</span>`; }}
    }}
    render();
  </script>
</body>
</html>
"""


def _handler_class() -> type[BaseHTTPRequestHandler]:
    class Handler(BaseHTTPRequestHandler):
        server: PermissionControlServer

        def do_GET(self) -> None:  # noqa: N802
            if not self._accept_host_header():
                return
            path = urlparse(self.path).path
            if path == "/api/state":
                self._json(self._snapshot())
                return
            if path == "/":
                body = render_interactive_control_html(
                    self._snapshot(),
                    csrf_token=self.server.csrf_token,
                )
                self._send(HTTPStatus.OK, body.encode("utf-8"), "text/html; charset=utf-8")
                return
            self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

        def do_POST(self) -> None:  # noqa: N802
            if not self._accept_host_header():
                return
            if not secrets.compare_digest(
                self.headers.get("X-CSRF-Token", ""),
                self.server.csrf_token,
            ):
                self._json({"error": "invalid CSRF token"}, status=HTTPStatus.FORBIDDEN)
                return
            try:
                payload = self._request_json()
                path = urlparse(self.path).path
                if path == "/api/set":
                    state = set_toggle(
                        self.server.project_root,
                        _required_string(payload, "gate_id"),
                        _required_string(payload, "value"),
                        actor=str(payload.get("actor") or "human-gui"),
                        reason=str(payload.get("reason") or "interactive GUI"),
                        control_home=self.server.control_home,
                    )
                elif path == "/api/recommend":
                    state = set_recommendation(
                        self.server.project_root,
                        _required_string(payload, "gate_id"),
                        _required_string(payload, "value"),
                        actor=str(payload.get("actor") or "codex"),
                        reason=_required_string(payload, "reason"),
                        control_home=self.server.control_home,
                    )
                elif path == "/api/bulk":
                    state = bulk_update_toggles(
                        self.server.project_root,
                        _required_string(payload, "action"),
                        actor=str(payload.get("actor") or "human-gui"),
                        reason=str(payload.get("reason") or "interactive GUI bulk action"),
                        control_home=self.server.control_home,
                    )
                else:
                    self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                    return
            except (KeyError, TypeError, ValueError) as exc:
                self._json({"error": str(exc)}, status=HTTPStatus.BAD_REQUEST)
                return
            self._json(state)

        def log_message(self, format: str, *args: Any) -> None:
            return

        def _snapshot(self) -> dict[str, Any]:
            return build_control_snapshot(
                self.server.project_root,
                control_home=self.server.control_home,
            )

        def _accept_host_header(self) -> bool:
            if _is_loopback_host_header(
                self.headers.get("Host", ""),
                expected_port=int(self.server.server_address[1]),
            ):
                return True
            self._json({"error": "invalid Host header"}, status=HTTPStatus.FORBIDDEN)
            return False

        def _request_json(self) -> dict[str, Any]:
            raw_length = self.headers.get("Content-Length", "")
            try:
                length = int(raw_length)
            except ValueError as exc:
                raise ValueError("invalid Content-Length") from exc
            if length <= 0 or length > MAX_REQUEST_BYTES:
                raise ValueError("request body size is invalid")
            if self.headers.get_content_type() != "application/json":
                raise ValueError("Content-Type must be application/json")
            try:
                payload = json.loads(self.rfile.read(length).decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise ValueError("request body must be valid UTF-8 JSON") from exc
            if not isinstance(payload, dict):
                raise ValueError("request body must be a JSON object")
            return payload

        def _json(self, payload: dict[str, Any], *, status: HTTPStatus = HTTPStatus.OK) -> None:
            body = json.dumps(payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
            self._send(status, body, "application/json; charset=utf-8")

        def _send(self, status: HTTPStatus, body: bytes, content_type: str) -> None:
            self.send_response(status.value)
            self.send_header("Content-Type", content_type)
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header(
                "Content-Security-Policy",
                "default-src 'self' 'unsafe-inline'; frame-ancestors 'none'",
            )
            self.send_header("X-Frame-Options", "DENY")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

    return Handler


def _required_string(payload: dict[str, Any], key: str) -> str:
    value = str(payload.get(key) or "").strip()
    if not value:
        raise ValueError(f"{key} is required")
    return value


def _require_loopback_host(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address:
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise ValueError("permission control server host must be a loopback IP address") from exc
    if not address.is_loopback:
        raise ValueError("permission control server may bind only to loopback")
    return address


def _is_loopback_host_header(raw_host: str, *, expected_port: int) -> bool:
    raw_host = raw_host.strip()
    if not raw_host or any(character.isspace() for character in raw_host):
        return False
    if raw_host.startswith("["):
        closing = raw_host.find("]")
        if closing <= 1:
            return False
        literal = raw_host[1:closing]
        remainder = raw_host[closing + 1 :]
        if remainder:
            if not remainder.startswith(":") or not remainder[1:].isdecimal():
                return False
            port = int(remainder[1:])
        else:
            port = None
    else:
        if raw_host.count(":") > 1:
            return False
        literal, separator, raw_port = raw_host.partition(":")
        if separator:
            if not raw_port.isdecimal():
                return False
            port = int(raw_port)
        else:
            port = None
    try:
        address = ipaddress.ip_address(literal)
    except ValueError:
        return False
    return address.is_loopback and (port is None or port == expected_port)


def _safe_script_json(value: dict[str, Any]) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True).replace("<", "\\u003c")
