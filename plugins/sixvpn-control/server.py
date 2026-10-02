#!/usr/bin/env python3
"""Local MCP bridge for 6VPN. Uses only the app's existing loopback HTTP API."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any


MAX_MESSAGE_LENGTH = 2_000
PORTS = range(17361, 17373)


def _app_port() -> int:
    """Find the running app's loopback API without exposing it to the network."""
    for port in PORTS:
        try:
            result = _request("GET", "/health", port=port, timeout=0.35)
            if result.get("ok") is True:
                return port
        except (OSError, RuntimeError, ValueError):
            continue
    raise RuntimeError("6VPN 앱이 실행 중이 아닙니다. 앱을 연 뒤 다시 시도해 주세요.")


def _request(
    method: str,
    path: str,
    *,
    port: int | None = None,
    body: dict[str, Any] | None = None,
    bearer_token: str | None = None,
    timeout: float = 5,
) -> dict[str, Any]:
    selected_port = port if port is not None else _app_port()
    payload = None if body is None else json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    if bearer_token:
        headers["Authorization"] = f"Bearer {bearer_token}"
    request = urllib.request.Request(
        f"http://127.0.0.1:{selected_port}{path}",
        data=payload,
        headers=headers,
        method=method,
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            decoded = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:1000]
        raise RuntimeError(f"6VPN 요청 실패 ({exc.code}): {detail}") from exc
    if not isinstance(decoded, dict):
        raise RuntimeError("6VPN 앱에서 예상하지 못한 응답을 받았습니다.")
    return decoded


def _agent_token() -> str:
    app_data = os.environ.get("LOCALAPPDATA")
    if not app_data:
        raise RuntimeError("Windows 로컬 앱 인증 정보를 찾을 수 없습니다.")
    token_path = os.path.join(app_data, "SixVPNBlocker", "agent_control.token")
    try:
        with open(token_path, "r", encoding="utf-8") as token_file:
            token = token_file.read().strip()
    except OSError as exc:
        raise RuntimeError("6VPN 앱을 실행해 로컬 연결을 준비해 주세요.") from exc
    if len(token) < 40:
        raise RuntimeError("6VPN 로컬 인증 정보가 유효하지 않습니다. 앱을 다시 시작해 주세요.")
    return token


def _preview_schedule_without_app_targets(message: str) -> dict[str, Any]:
    result = _request("POST", "/chat/schedule/preview", body={"message": message})
    preview = result.get("preview")
    if isinstance(preview, dict) and preview.get("appTargets"):
        raise ValueError("이 일정은 앱 실행 파일을 차단합니다. 앱 전용 차단 미리보기에서 정확한 앱 이름과 .exe를 먼저 확인하세요.")
    return result


def _text_result(value: Any, *, is_error: bool = False) -> dict[str, Any]:
    return {
        "content": [{"type": "text", "text": json.dumps(value, ensure_ascii=False, indent=2)}],
        "isError": is_error,
    }


TOOLS = [
    {
        "name": "sixvpn_status",
        "description": "6VPN 앱이 실행 중인지와 로컬 연결 상태를 확인합니다.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "sixvpn_list_schedules",
        "description": "현재 등록된 차단 일정 목록을 확인합니다.",
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "sixvpn_preview_schedule",
        "description": "차단 일정 명령을 적용하지 않고 먼저 해석해 미리보기합니다. 추가·변경·삭제·잠금·임시 허용 등 일정 외 명령은 지원하지 않습니다.",
        "inputSchema": {
            "type": "object",
            "properties": {"message": {"type": "string", "minLength": 1, "maxLength": MAX_MESSAGE_LENGTH}},
            "required": ["message"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "sixvpn_apply_schedule",
        "description": "사용자가 명시적으로 적용을 지시한 경우에만 웹 차단 일정을 저장합니다. 게임·앱 실행파일을 포함하는 일정은 여기서 적용하지 말고 전용 앱 차단 절차를 사용하세요.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "message": {"type": "string", "minLength": 1, "maxLength": MAX_MESSAGE_LENGTH},
                "confirm": {"type": "boolean", "const": True, "description": "사용자가 미리보기를 확인하고 명시적으로 적용하라고 요청한 경우에만 true."},
            },
            "required": ["message", "confirm"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False},
    },
    {
        "name": "sixvpn_preview_app_block",
        "description": "정확한 Windows 앱 이름과 실행 파일을 보여 주며 매일 하루 종일 차단하는 일정을 미리봅니다. 앱이 실행 중이면 종료될 수 있습니다. 실행 파일을 확실히 모르면 추측하지 말고 사용자에게 확인하세요.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "app_name": {"type": "string", "minLength": 1, "maxLength": 80},
                "executable": {"type": "string", "minLength": 1, "maxLength": 100, "description": "정확한 프로세스 파일명. 경로 없이 예: Valorant-Win64-Shipping.exe"},
            },
            "required": ["app_name", "executable"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": True, "destructiveHint": False, "openWorldHint": False},
    },
    {
        "name": "sixvpn_apply_app_block",
        "description": "앱 이름, 정확한 실행 파일, 매일 종일 차단, 실행 중 앱 종료 가능성을 보여 준 별도 미리보기에 대해 사용자가 다시 적용을 요청한 경우에만 5분 내 preview_id로 저장합니다.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "preview_id": {"type": "string", "minLength": 1},
                "confirm": {"type": "boolean", "const": True, "description": "사용자가 해당 미리보기를 확인하고 별도로 적용을 요청한 경우에만 true."},
            },
            "required": ["preview_id", "confirm"],
            "additionalProperties": False,
        },
        "annotations": {"readOnlyHint": False, "destructiveHint": True, "idempotentHint": False, "openWorldHint": False},
    },
]


def _reject_unsupported(message: str) -> None:
    # These existing routes also accept high-impact operations; this bridge is
    # intentionally limited to ordinary schedule creation/update only.
    blocked_terms = (
        "삭제", "지워", "없애", "합쳐", "잠금", "잠궈", "풀어", "허용",
        "임시", "디버깅", "강제 종료", "브라우저 종료", "보호 해제",
    )
    if any(term in message for term in blocked_terms):
        raise ValueError("이 명령은 ChatGPT 연결에서 지원하지 않습니다. 6VPN 앱에서 직접 처리해 주세요.")


def _call_tool(name: str, arguments: dict[str, Any]) -> Any:
    if name == "sixvpn_status":
        port = _app_port()
        health = _request("GET", "/health", port=port)
        return {"running": True, "port": port, "message": "6VPN 앱의 로컬 연결이 준비됐습니다.", "health": health}

    if name == "sixvpn_list_schedules":
        return _request("GET", "/chat/schedules")

    if name in ("sixvpn_preview_schedule", "sixvpn_apply_schedule"):
        message = arguments.get("message")
        if not isinstance(message, str) or not message.strip() or len(message) > MAX_MESSAGE_LENGTH:
            raise ValueError("명령은 1~2000자여야 합니다.")
        message = message.strip()
        _reject_unsupported(message)
        if name == "sixvpn_preview_schedule":
            return _preview_schedule_without_app_targets(message)
        if arguments.get("confirm") is not True:
            raise ValueError("적용하려면 먼저 미리보기를 확인하고 사용자가 명시적으로 적용을 요청해야 합니다.")
        _preview_schedule_without_app_targets(message)
        return _request("POST", "/chat/schedule", body={"message": message, "confirm": True})

    if name == "sixvpn_preview_app_block":
        app_name = arguments.get("app_name")
        executable = arguments.get("executable")
        if not isinstance(app_name, str) or not isinstance(executable, str):
            raise ValueError("앱 이름과 실행 파일을 함께 입력해 주세요.")
        return _request(
            "POST", "/agent/app-block/preview",
            body={"appName": app_name, "executable": executable},
            bearer_token=_agent_token(),
        )

    if name == "sixvpn_apply_app_block":
        preview_id = arguments.get("preview_id")
        if not isinstance(preview_id, str) or not preview_id.strip():
            raise ValueError("먼저 앱 차단 미리보기를 받아야 합니다.")
        if arguments.get("confirm") is not True:
            raise ValueError("사용자가 앱 차단 미리보기를 확인하고 적용을 요청해야 합니다.")
        return _request(
            "POST", "/agent/app-block/apply",
            body={"previewId": preview_id, "confirm": True},
            bearer_token=_agent_token(),
        )

    raise ValueError(f"알 수 없는 도구: {name}")


def _dispatch(message: dict[str, Any]) -> dict[str, Any] | None:
    method = message.get("method")
    request_id = message.get("id")
    if method == "notifications/initialized" or method == "notifications/cancelled":
        return None
    if method == "initialize":
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": message.get("params", {}).get("protocolVersion", "2025-03-26"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": "sixvpn-local-control", "version": "1.1.0"},
                "instructions": "6VPN 상태/일정 조회는 읽기 도구를 사용하세요. 웹 일정은 미리보기 뒤 별도 사용자 메시지로 명시적 적용을 요청받아야 저장합니다. 게임 및 앱 차단은 정확한 앱 이름과 .exe를 확인하고 전용 미리보기를 먼저 보여 주세요. 미리보기와 적용을 같은 턴에 연속 호출하지 마세요. 보호 기능을 자동으로 켜지 말고 브라우저 종료, 컴퓨터 잠금, 삭제, 합치기, 임시 허용, 셸 명령을 하지 마세요.",
            },
        }
    if method == "ping":
        return {"jsonrpc": "2.0", "id": request_id, "result": {}}
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": request_id, "result": {"tools": TOOLS}}
    if method == "tools/call":
        params = message.get("params") or {}
        try:
            result = _call_tool(str(params.get("name", "")), params.get("arguments") or {})
            return {"jsonrpc": "2.0", "id": request_id, "result": _text_result(result)}
        except Exception as exc:  # MCP tool errors must not break the stdio session.
            return {"jsonrpc": "2.0", "id": request_id, "result": _text_result({"error": str(exc)}, is_error=True)}
    if request_id is None:
        return None
    return {"jsonrpc": "2.0", "id": request_id, "error": {"code": -32601, "message": "Method not found"}}


def main() -> None:
    # MCP stdio reserves stdout for protocol messages; never print diagnostics there.
    # ChatGPT Desktop may start Python with the Windows legacy code page, but
    # MCP JSON is UTF-8 and tool descriptions/results include Korean text.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, "reconfigure"):
        sys.stderr.reconfigure(encoding="utf-8")
    for line in sys.stdin:
        try:
            message = json.loads(line)
            response = _dispatch(message)
            if response is not None:
                sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
                sys.stdout.flush()
        except Exception as exc:
            sys.stderr.write(f"6VPN MCP bridge: {exc}\n")
            sys.stderr.flush()


if __name__ == "__main__":
    main()
