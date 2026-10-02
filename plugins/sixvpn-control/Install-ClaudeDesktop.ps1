$ErrorActionPreference = 'Stop'

if (-not $env:APPDATA -or -not $env:LOCALAPPDATA) { throw 'Windows APPDATA and LOCALAPPDATA paths are required.' }
$python = (Get-Command python.exe -ErrorAction Stop).Source
$sourceRoot = $PSScriptRoot
$installRoot = Join-Path $env:LOCALAPPDATA 'SixVPNBlocker\claude-mcp'
$serverPath = Join-Path $installRoot 'server.py'
$configPath = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
$configDir = Split-Path -Parent $configPath

New-Item -ItemType Directory -Force -Path $installRoot, $configDir | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceRoot 'server.py') -Destination $serverPath -Force

if (Test-Path -LiteralPath $configPath) {
  try { $config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json }
  catch { throw "Claude configuration contains invalid JSON; it was left unchanged: $configPath" }
  if ($null -eq $config -or $config -is [array] -or $config -is [string]) { throw "Claude configuration must be a JSON object; it was left unchanged: $configPath" }
} else { $config = [pscustomobject]@{} }

$serversProperty = $config.PSObject.Properties['mcpServers']
if ($null -eq $serversProperty -or $null -eq $serversProperty.Value) {
  $servers = [pscustomobject]@{}
  if ($null -eq $serversProperty) { $config | Add-Member -NotePropertyName 'mcpServers' -NotePropertyValue $servers }
  else { $serversProperty.Value = $servers }
} else { $servers = $serversProperty.Value }
if ($servers -is [array] -or $servers -is [string] -or $servers -is [ValueType]) { throw "Claude mcpServers must be a JSON object; configuration was left unchanged: $configPath" }

if (Test-Path -LiteralPath $configPath) {
  $stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
  Copy-Item -LiteralPath $configPath -Destination "$configPath.backup-$stamp"
}
$entry = [pscustomobject]@{ command = $python; args = @($serverPath) }
$entryProperty = $servers.PSObject.Properties['sixvpn-local-control']
if ($null -eq $entryProperty) { $servers | Add-Member -NotePropertyName 'sixvpn-local-control' -NotePropertyValue $entry }
else { $entryProperty.Value = $entry }
$json = ConvertTo-Json -InputObject $config -Depth 32
[System.IO.File]::WriteAllText($configPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))

Write-Output "Claude Desktop configuration updated: $configPath"
Write-Output "Local MCP server installed: $serverPath"
Write-Output 'Restart Claude Desktop to connect. This only registers the connector; 6VPN protection stays off unless you enable it in the 6VPN app.'
