$ErrorActionPreference = 'Stop'
if (-not $env:APPDATA) { throw 'Windows APPDATA path is required.' }
$configPath = Join-Path $env:APPDATA 'Claude\claude_desktop_config.json'
if (-not (Test-Path -LiteralPath $configPath)) { Write-Output 'No Claude Desktop MCP configuration was found; nothing changed.'; exit 0 }
try { $config = Get-Content -Raw -LiteralPath $configPath | ConvertFrom-Json }
catch { throw "Claude configuration contains invalid JSON; it was left unchanged: $configPath" }
if ($null -eq $config -or $config -is [array] -or $config -is [string]) { Write-Output 'No 6VPN Claude connector entry was found; nothing changed.'; exit 0 }
$serversProperty = $config.PSObject.Properties['mcpServers']
if ($null -eq $serversProperty -or $null -eq $serversProperty.Value) { Write-Output 'No 6VPN Claude connector entry was found; nothing changed.'; exit 0 }
$entryProperty = $serversProperty.Value.PSObject.Properties['sixvpn-local-control']
if ($null -eq $entryProperty) { Write-Output 'No 6VPN Claude connector entry was found; nothing changed.'; exit 0 }
$serversProperty.Value.PSObject.Properties.Remove('sixvpn-local-control')
$json = ConvertTo-Json -InputObject $config -Depth 32
[System.IO.File]::WriteAllText($configPath, $json + [Environment]::NewLine, [System.Text.UTF8Encoding]::new($false))
Write-Output '6VPN Local Control was removed from Claude Desktop. Restart Claude Desktop to disconnect it.'

