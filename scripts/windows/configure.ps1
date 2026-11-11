# Compatibility entry point. Canonical code is in the Windows module.
[CmdletBinding()]
param([switch]$Check)
$target = Join-Path $PSScriptRoot '../../modules/windows-preferences/scripts/windows/configure.ps1'
& $target -Check:$Check
exit $LASTEXITCODE
