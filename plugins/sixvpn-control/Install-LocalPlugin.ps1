param()
$ErrorActionPreference = 'Stop'

$sourceRoot = $PSScriptRoot
$marketplaceRoot = Join-Path $env:USERPROFILE '.agents\plugins'
$marketplacePath = Join-Path $marketplaceRoot 'marketplace.json'
$pluginRoot = Join-Path $marketplaceRoot 'sixvpn-control'
$python = (Get-Command python.exe -ErrorAction Stop).Source

New-Item -ItemType Directory -Force -Path $marketplaceRoot | Out-Null
New-Item -ItemType Directory -Force -Path $pluginRoot | Out-Null
Copy-Item -LiteralPath (Join-Path $sourceRoot 'server.py') -Destination $pluginRoot -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot 'README.md') -Destination $pluginRoot -Force
Copy-Item -LiteralPath (Join-Path $sourceRoot 'skills') -Destination $pluginRoot -Recurse -Force
New-Item -ItemType Directory -Force -Path (Join-Path $pluginRoot '.codex-plugin') | Out-Null

$utf8NoBom = [System.Text.UTF8Encoding]::new($false)
$manifest = @{
  name = 'sixvpn-local-control'
  version = '1.2.0'
  description = 'Read 6VPN status and schedules, preview schedule commands, and apply them after explicit user approval.'
  mcpServers = './.mcp.json'
  skills = './skills/'
} | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText((Join-Path $pluginRoot '.codex-plugin\plugin.json'), $manifest + [Environment]::NewLine, $utf8NoBom)

$mcp = @{
  mcpServers = @{
    sixvpn = @{
      command = $python
      args = @((Join-Path $pluginRoot 'server.py'))
      env = @{}
    }
  }
} | ConvertTo-Json -Depth 8
[System.IO.File]::WriteAllText((Join-Path $pluginRoot '.mcp.json'), $mcp + [Environment]::NewLine, $utf8NoBom)

$marketplace = if (Test-Path -LiteralPath $marketplacePath) {
  Get-Content -Raw -LiteralPath $marketplacePath | ConvertFrom-Json
} else {
  [pscustomobject]@{ name = 'delig-personal'; interface = [pscustomobject]@{ displayName = 'My Local Plugins' }; plugins = @() }
}
$plugins = @($marketplace.plugins | Where-Object { $_.name -ne 'sixvpn-local-control' })
$plugins += [pscustomobject]@{
  name = 'sixvpn-local-control'
  source = [pscustomobject]@{ source = 'local'; path = './sixvpn-control' }
  policy = [pscustomobject]@{ installation = 'AVAILABLE'; authentication = 'ON_INSTALL' }
  category = 'Productivity'
}
$marketplace | Add-Member -NotePropertyName plugins -NotePropertyValue $plugins -Force
$marketplaceJson = ConvertTo-Json -InputObject $marketplace -Depth 16
[System.IO.File]::WriteAllText($marketplacePath, $marketplaceJson + [Environment]::NewLine, $utf8NoBom)

Write-Output "Local plugin source installed: $pluginRoot"
Write-Output "Marketplace updated: $marketplacePath"
Write-Output 'Plugin is available for manual installation; it has not been enabled in ChatGPT.'
