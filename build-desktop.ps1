$ErrorActionPreference = 'Stop'

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $root

New-Item -ItemType Directory -Force .\build | Out-Null
New-Item -ItemType Directory -Force .\dist | Out-Null

Write-Host 'Building Go management console...'
go build -o .\build\server-health-monitor-console.exe .\cmd\console
if ($LASTEXITCODE -ne 0) { throw 'Go console build failed.' }

Write-Host 'Packaging Windows desktop application...'
pyinstaller --clean --noconfirm .\ServerHealthMonitor.spec
if ($LASTEXITCODE -ne 0) { throw 'PyInstaller packaging failed.' }

Write-Host ''
Write-Host 'Build complete:' -ForegroundColor Green
Write-Host (Join-Path $root 'dist\ServerHealthMonitor.exe')
