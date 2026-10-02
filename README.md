# 6VPN Local Control for ChatGPT Desktop

A small, local-only MCP connector for controlling the 6VPN app on the same Windows PC. It can read app status and schedules, preview a website schedule, and preview/apply an exact Windows app block after a separate explicit confirmation.

## Requirements

- Windows 10/11
- Python 3.10 or newer on PATH (`python.exe`)
- 6VPN installed and running on this PC
- ChatGPT Desktop with local plugin support

The connector talks only to 6VPN over `127.0.0.1`. It does not expose a cloud service or send your local authentication token to this repository. The plugin never starts 6VPN or enables protection automatically. Browser executables and critical Windows processes are rejected. App-block schedules can close the named app while active; inspect the preview before asking it to apply.

## Install

1. Download this repository using **Code → Download ZIP**, or clone it.
2. Extract the ZIP, then open PowerShell in the extracted repository folder.
3. Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\plugins\sixvpn-control\Install-LocalPlugin.ps1
```

4. Restart or refresh ChatGPT Desktop. In **Plugins**, install **6VPN Local Control** from **My Local Plugins**. Leave it disabled until you choose to enable it.
5. Keep 6VPN running when using the connector. First connection/tool use may prompt for confirmation.

Example: “평일 오전 9시부터 오후 6시까지 SNS 차단 일정 미리보기해줘.” Review the preview first; ask it to apply in a separate message only if it is correct.

For an app block, the preview states the exact executable and that it can close the app. Apply requires a separate request using the short-lived preview.

## Verify or contribute

```powershell
python -m unittest -v
```

The server uses only the Python standard library. Source and test files are under `plugins/sixvpn-control/`.

## Scope

This is a downloadable Windows/ChatGPT Desktop local connector, not a hosted connector. It requires the 6VPN app on the same PC and currently does not work as a standalone ChatGPT web/mobile plugin.
