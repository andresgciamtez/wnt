param(
    [string]$OutputDir = "zip_build"
)

$ErrorActionPreference = "Stop"

if (Test-Path -LiteralPath "wnt.zip") {
    Remove-Item -Force -LiteralPath "wnt.zip"
}

if (-not (Test-Path -LiteralPath $OutputDir)) {
    New-Item -ItemType Directory -Path $OutputDir | Out-Null
}

$outputZip = Join-Path $OutputDir "wnt.zip"
if (Test-Path -LiteralPath $outputZip) {
    Remove-Item -Force -LiteralPath $outputZip
}

$stageRoot = Join-Path $OutputDir "deploy"
$pluginDir = Join-Path $stageRoot "wnt"
if (Test-Path -LiteralPath $pluginDir) {
    Remove-Item -Recurse -Force -LiteralPath $pluginDir
}

pb_tool deploy --no-confirm --no-docs --plugin_path $stageRoot

if (-not (Test-Path -LiteralPath $pluginDir)) {
    throw "pb_tool did not deploy the plugin to $pluginDir"
}

Get-ChildItem -LiteralPath $pluginDir -Recurse -Directory -Filter "__pycache__" |
    Remove-Item -Recurse -Force
Get-ChildItem -LiteralPath $pluginDir -Recurse -File |
    Where-Object { $_.Extension -in ".pyc", ".pyo" } |
    Remove-Item -Force

Compress-Archive -Path $pluginDir -DestinationPath $outputZip -Force
Write-Host "Created $outputZip"
