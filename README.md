# 6VPN Local Control 1.1.0 for ChatGPT Desktop and Claude Desktop

A local-only MCP connector for controlling the 6VPN app on the same Windows PC. It can read app status and schedules, preview a website schedule, and preview/apply an exact Windows app block after a separate explicit confirmation.

## Requirements

- Windows 10/11
- Python 3.10 or newer on PATH (`python.exe`)
- 6VPN installed and running on this PC
- ChatGPT Desktop or Claude Desktop

The connector talks only to 6VPN over `127.0.0.1`. It does not expose a cloud service or send your local authentication token to this repository. It never starts 6VPN or enables protection automatically. Browser executables and critical Windows processes are rejected. App-block schedules can close the named app while active; inspect the preview before asking it to apply.

## Claude Desktop install (Windows)

1. Download this repository using **Code → Download ZIP**, then extract it.
2. Open PowerShell in the extracted folder and run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\plugins\sixvpn-control\Install-ClaudeDesktop.ps1
```

3. Restart Claude Desktop. The connector will appear in **Settings → Developer** as a local MCP server.
4. 6VPN must be running when you use it. The installer only registers the connector; it does not enable 6VPN protection. To disconnect, run `Uninstall-ClaudeDesktop.ps1` from the same folder and restart Claude Desktop.

The installer backs up an existing Claude config before updating it, keeps other MCP servers, and installs the server under `%LOCALAPPDATA%\SixVPNBlocker\claude-mcp` so it does not depend on where you extracted the ZIP.

## ChatGPT Desktop install

1. Download and extract the repository.
2. Run:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\plugins\sixvpn-control\Install-LocalPlugin.ps1
```

3. Restart/refresh ChatGPT Desktop. In **Plugins**, install **6VPN Local Control** from **My Local Plugins**. Leave it disabled until you choose to enable it.

## Use safely

Example: “평일 오전 9시부터 오후 6시까지 SNS 차단 일정 미리보기해줘.” Review the preview first; ask it to apply in a separate message only if it is correct.

For app blocking, the preview states the exact executable and warns that the app can be closed. Applying requires a separate request using the short-lived preview.

## Verify or contribute

```powershell
python -m unittest -v
```

The server uses only the Python standard library. Source and tests are under `plugins/sixvpn-control/`.

## Scope

This is a downloadable Windows local connector, not a hosted Claude or ChatGPT web/mobile connector. Claude Desktop supports local MCP servers and installable desktop extensions; this repository currently provides a manually run Windows installer for the local server configuration.
