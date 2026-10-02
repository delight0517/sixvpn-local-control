$ErrorActionPreference = 'Stop'

if (-not $env:USERPROFILE) { throw 'Windows USERPROFILE is required.' }
$configPath = Join-Path $env:USERPROFILE '.gemini\config\mcp_config.json'
if (-not (Test-Path -LiteralPath $configPath)) { Write-Output 'Antigravity MCP configuration was not found; nothing to remove.'; exit 0 }
try { $config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json }
catch { throw "Antigravity configuration contains invalid JSON; it was left unchanged: $configPath" }
if ($null -eq $config -or $config -is [array] -or $config -is [string]) { throw "Antigravity configuration must be a JSON object; it was left unchanged: $configPath" }
$serversProperty = $config.PSObject.Properties['mcpServers']
if ($null -eq $serversProperty -or $null -eq $serversProperty.Value) { Write-Output 'The SixVPN connector was not configured; nothing to remove.'; exit 0 }
$servers = $serversProperty.Value
if ($servers -is [array] -or $servers -is [string] -or $servers -is [ValueType]) { throw "Antigravity mcpServers must be a JSON object; configuration was left unchanged: $configPath" }
$entryProperty = $servers.PSObject.Properties['sixvpn-local-control']
if ($null -eq $entryProperty) { Write-Output 'The SixVPN connector was not configured; nothing to remove.'; exit 0 }
$servers.PSObject.Properties.Remove('sixvpn-local-control')
$json = ConvertTo-Json -InputObject $config -Depth 32
[System.IO.File]::WriteAllText($configPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Output "SixVPN connector removed from Antigravity: $configPath"
Write-Output 'Other MCP servers and the installed local copy were left unchanged.'
