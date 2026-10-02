import json
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

import server


class McpBridgeTests(unittest.TestCase):
    def test_initialize_advertises_tools_and_manual_approval_rule(self):
        response = server._dispatch({
            "jsonrpc": "2.0", "id": 1, "method": "initialize",
            "params": {"protocolVersion": "2025-03-26"},
        })
        self.assertEqual(response["result"]["serverInfo"]["name"], "sixvpn-local-control")
        self.assertIn("별도 사용자 메시지", response["result"]["instructions"])

    def test_tools_list_has_read_only_preview_and_marked_mutation(self):
        response = server._dispatch({"jsonrpc": "2.0", "id": 2, "method": "tools/list"})
        by_name = {tool["name"]: tool for tool in response["result"]["tools"]}
        self.assertTrue(by_name["sixvpn_preview_schedule"]["annotations"]["readOnlyHint"])
        self.assertTrue(by_name["sixvpn_apply_schedule"]["annotations"]["destructiveHint"])
        self.assertEqual(len(by_name), 6)
        self.assertTrue(by_name["sixvpn_preview_app_block"]["annotations"]["readOnlyHint"])
        self.assertTrue(by_name["sixvpn_apply_app_block"]["annotations"]["destructiveHint"])

    def test_app_block_apply_requires_separate_confirmation(self):
        with patch.object(server, "_request") as request:
            with self.assertRaises(ValueError):
                server._call_tool("sixvpn_apply_app_block", {"preview_id": "preview"})
            request.assert_not_called()

    def test_app_block_uses_authenticated_preview_and_apply_routes(self):
        with patch.object(server, "_agent_token", return_value="secret-token"), \
             patch.object(server, "_request", return_value={"ok": True}) as request:
            server._call_tool("sixvpn_preview_app_block", {
                "app_name": "My Game", "executable": "game.exe",
            })
            request.assert_called_once_with(
                "POST", "/agent/app-block/preview",
                body={"appName": "My Game", "executable": "game.exe"},
                bearer_token="secret-token",
            )
            request.reset_mock()
            server._call_tool("sixvpn_apply_app_block", {
                "preview_id": "preview", "confirm": True,
            })
            request.assert_called_once_with(
                "POST", "/agent/app-block/apply",
                body={"previewId": "preview", "confirm": True},
                bearer_token="secret-token",
            )

    def test_generic_schedule_cannot_bypass_app_specific_preview(self):
        with patch.object(server, "_request", return_value={
            "preview": {"appTargets": ["game.exe"]},
        }) as request:
            with self.assertRaises(ValueError):
                server._call_tool("sixvpn_preview_schedule", {"message": "게임 차단"})
            request.assert_called_once()

    def test_apply_requires_confirm_and_rejects_high_impact_commands(self):
        with patch.object(server, "_request", return_value={"ok": True}) as request:
            with self.assertRaises(ValueError):
                server._call_tool("sixvpn_apply_schedule", {"message": "밤 10시부터 유튜브 차단"})
            with self.assertRaises(ValueError):
                server._call_tool("sixvpn_apply_schedule", {"message": "유튜브 스케줄 삭제", "confirm": True})
            request.assert_not_called()

    def test_confirmed_apply_calls_only_schedule_endpoint(self):
        with patch.object(server, "_request", return_value={"ok": True, "applied": True}) as request:
            result = server._call_tool("sixvpn_apply_schedule", {
                "message": "매일 밤 10시부터 아침 7시까지 유튜브 차단", "confirm": True,
            })
        self.assertTrue(result["applied"])
        self.assertEqual(request.call_count, 2)
        self.assertEqual(request.call_args_list[0].args, ("POST", "/chat/schedule/preview"))
        request.assert_called_with(
            "POST", "/chat/schedule", body={
                "message": "매일 밤 10시부터 아침 7시까지 유튜브 차단", "confirm": True,
            },
        )

    def test_protocol_notifications_have_no_reply(self):
        self.assertIsNone(server._dispatch({"jsonrpc": "2.0", "method": "notifications/initialized"}))

    def test_stdio_uses_utf8_even_under_legacy_windows_code_page(self):
        request = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-03-26"}})
        env = os.environ.copy()
        env.pop("PYTHONIOENCODING", None)
        result = subprocess.run(
            [sys.executable, str(Path(server.__file__))],
            input=request + "\n",
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=env,
            timeout=5,
            check=True,
        )
        self.assertEqual(json.loads(result.stdout)["id"], 1)
        self.assertEqual(result.stderr, "")


if __name__ == "__main__":
    unittest.main()
