# Apply Windows desired state from this repo.
# Source of truth: .config/windows/gamedvr.dsc.yaml
[CmdletBinding()]
param()

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Not Windows!'
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DscPath = Join-Path $RepoRoot '.config\windows\gamedvr.dsc.yaml'

if (-not (Test-Path -LiteralPath $DscPath)) {
    Write-Error "Missing desired-state file: $DscPath"
    exit 1
}

function ConvertTo-ProviderPath {
    param([Parameter(Mandatory)][string]$KeyPath)
    $normalized = $KeyPath -replace '/', '\'
    $map = @{
        'HKCU'              = 'HKCU:'
        'HKEY_CURRENT_USER' = 'HKCU:'
        'HKLM'              = 'HKLM:'
        'HKEY_LOCAL_MACHINE'= 'HKLM:'
    }
    foreach ($hive in $map.Keys) {
        if ($normalized -eq $hive -or $normalized.StartsWith("$hive\")) {
            return ($map[$hive] + $normalized.Substring($hive.Length))
        }
    }
    throw "Unsupported registry hive: $KeyPath"
}

function Test-IsElevated {
    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = [Security.Principal.WindowsPrincipal]$identity
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Read-DscRegistryDocument {
    param([Parameter(Mandatory)][string]$FilePath)

    $items = New-Object System.Collections.Generic.List[object]
    $current = $null

    foreach ($line in Get-Content -LiteralPath $FilePath) {
        if ($line -match '^\s+keyPath:\s+(.+?)\s*$') {
            if ($null -ne $current -and $current.keyPath -and $current.valueName -and $null -ne $current.dword) {
                $items.Add($current)
            }
            $current = [pscustomobject]@{
                keyPath   = $Matches[1].Trim("'").Trim('"')
                valueName = $null
                dword     = $null
            }
        }
        elseif ($null -ne $current -and $line -match '^\s+valueName:\s+(.+?)\s*$') {
            $current.valueName = $Matches[1].Trim("'").Trim('"')
        }
        elseif ($null -ne $current -and $line -match '^\s+DWord:\s+(\d+)\s*$') {
            $current.dword = [int]$Matches[1]
        }
    }

    if ($null -ne $current -and $current.keyPath -and $current.valueName -and $null -ne $current.dword) {
        $items.Add($current)
    }

    if ($items.Count -eq 0) {
        throw "No registry resources found in $FilePath"
    }

    return $items
}

function Set-DesiredDword {
    param(
        [Parameter(Mandatory)][string]$ProviderPath,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][int]$Value
    )

    if (-not (Test-Path -LiteralPath $ProviderPath)) {
        New-Item -Path $ProviderPath -Force | Out-Null
    }

    $existing = Get-ItemProperty -LiteralPath $ProviderPath -Name $Name -ErrorAction SilentlyContinue
    if ($null -ne $existing -and [int]($existing.$Name) -eq $Value) {
        Write-Host "ok  $ProviderPath\$Name = $Value"
        return
    }

    New-ItemProperty -LiteralPath $ProviderPath -Name $Name -PropertyType DWord -Value $Value -Force | Out-Null
    Write-Host "set $ProviderPath\$Name = $Value"
}

$elevated = Test-IsElevated
$desired = Read-DscRegistryDocument -FilePath $DscPath
$skipped = 0

Write-Host "Applying $DscPath"
Write-Host ""

foreach ($item in $desired) {
    $providerPath = ConvertTo-ProviderPath -KeyPath $item.keyPath
    $needsAdmin = $providerPath.StartsWith('HKLM:')

    if ($needsAdmin -and -not $elevated) {
        Write-Host "skip $providerPath\$($item.valueName) (Administrator required)"
        $skipped += 1
        continue
    }

    Set-DesiredDword -ProviderPath $providerPath -Name $item.valueName -Value $item.dword
}

Write-Host ""
if ($skipped -gt 0) {
    Write-Host "Applied with $skipped skipped HKLM value(s). Re-run elevated to set machine policy."
} else {
    Write-Host "Windows desired state applied."
}
