# Apply Windows desired state from this repo.
# Sources:
#   home/dot_config/windows/gamedvr.dsc.yaml
#   home/dot_config/windows/desired-state.json
[CmdletBinding()]
param([switch]$Check)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    Write-Error 'Not Windows!'
    exit 1
}

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = (Resolve-Path (Join-Path $ScriptDir '..\..')).Path
$DscPath = Join-Path $RepoRoot 'home\dot_config\windows\gamedvr.dsc.yaml'
$StatePath = Join-Path $RepoRoot 'home\dot_config\windows\desired-state.json'

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

function ConvertTo-ByteArray {
    param([Parameter(Mandatory)]$Values)
    [byte[]]@($Values | ForEach-Object { [byte]$_ })
}

function Test-ByteEqual {
    param($Left, $Right)
    if ($null -eq $Left -or $null -eq $Right) { return $false }
    if ($Left.Length -ne $Right.Length) { return $false }
    for ($i = 0; $i -lt $Left.Length; $i++) {
        if ([byte]$Left[$i] -ne [byte]$Right[$i]) { return $false }
    }
    return $true
}

function Set-DesiredBinary {
    param(
        [Parameter(Mandatory)][string]$ProviderPath,
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][byte[]]$Value
    )

    if (-not (Test-Path -LiteralPath $ProviderPath)) {
        New-Item -Path $ProviderPath -Force | Out-Null
    }

    $existing = Get-ItemProperty -LiteralPath $ProviderPath -Name $Name -ErrorAction SilentlyContinue
    if ($null -ne $existing -and (Test-ByteEqual $existing.$Name $Value)) {
        Write-Host "ok  $ProviderPath\$Name"
        return
    }

    New-ItemProperty -LiteralPath $ProviderPath -Name $Name -PropertyType Binary -Value $Value -Force | Out-Null
    Write-Host "set $ProviderPath\$Name"
}

function Set-DesiredService {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$StartType,
        [Parameter(Mandatory)][string]$State,
        [Parameter(Mandatory)][bool]$Elevated
    )

    $service = Get-Service -Name $Name -ErrorAction SilentlyContinue
    if ($null -eq $service) {
        Write-Host "skip service $Name (not installed)"
        return
    }

    if (-not $Elevated) {
        Write-Host "skip service $Name (Administrator required)"
        return
    }

    if ($service.StartType -ne $StartType) {
        Set-Service -Name $Name -StartupType $StartType
        Write-Host "set service $Name StartType=$StartType"
    } else {
        Write-Host "ok  service $Name StartType=$StartType"
    }

    $service.Refresh()
    if ($State -eq 'Stopped' -and $service.Status -ne 'Stopped') {
        Stop-Service -Name $Name -Force -ErrorAction Stop
        Write-Host "stop service $Name"
    } elseif ($State -eq 'Running' -and $service.Status -ne 'Running') {
        Start-Service -Name $Name -ErrorAction Stop
        Write-Host "start service $Name"
    } else {
        Write-Host "ok  service $Name state=$($service.Status)"
    }
}

function Set-DesiredScheduledTask {
    param(
        [Parameter(Mandatory)][string]$TaskPath,
        [Parameter(Mandatory)][string]$TaskName,
        [Parameter(Mandatory)][string]$State,
        [Parameter(Mandatory)][bool]$Elevated
    )

    $task = Get-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName -ErrorAction SilentlyContinue
    if ($null -eq $task) {
        Write-Host "skip task $TaskPath$TaskName (not found)"
        return
    }

    if (-not $Elevated) {
        Write-Host "skip task $TaskPath$TaskName (Administrator required)"
        return
    }

    if ($State -eq 'Disabled') {
        if ($task.State -eq 'Disabled') {
            Write-Host "ok  task $TaskPath$TaskName Disabled"
            return
        }
        Disable-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName | Out-Null
        Write-Host "set task $TaskPath$TaskName Disabled"
        return
    }

    if ($task.State -eq 'Disabled') {
        Enable-ScheduledTask -TaskPath $TaskPath -TaskName $TaskName | Out-Null
        Write-Host "set task $TaskPath$TaskName Enabled"
    } else {
        Write-Host "ok  task $TaskPath$TaskName $($task.State)"
    }
}

function Stop-DesiredProcess {
    param([Parameter(Mandatory)][string]$Name)

    $procs = @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
    if ($procs.Count -eq 0) {
        Write-Host "ok  process $Name (not running)"
        return
    }

    $image = "$Name.exe"
    & taskkill.exe /F /IM $image /T 2>$null | Out-Null
    Start-Sleep -Milliseconds 400
    $left = @(Get-Process -Name $Name -ErrorAction SilentlyContinue)
    if ($left.Count -eq 0) {
        Write-Host "stop process $Name"
    } else {
        Write-Host "skip process $Name (still running)"
    }
}

function Stop-DesiredProcessByCommandLine {
    param(
        [Parameter(Mandatory)][string]$Name,
        [Parameter(Mandatory)][string]$CommandLineMatch
    )

    $procs = @(Get-CimInstance Win32_Process -Filter "Name='$Name.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match $CommandLineMatch })
    if ($procs.Count -eq 0) {
        Write-Host "ok  process $Name ($CommandLineMatch) (not running)"
        return
    }

    foreach ($proc in $procs) {
        & taskkill.exe /F /PID $proc.ProcessId /T 2>$null | Out-Null
    }
    Start-Sleep -Milliseconds 400
    $left = @(Get-CimInstance Win32_Process -Filter "Name='$Name.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -match $CommandLineMatch })
    if ($left.Count -eq 0) {
        Write-Host "stop process $Name ($CommandLineMatch)"
    } else {
        Write-Host "skip process $Name ($CommandLineMatch) (still running)"
    }
}

if ($Check) {
    $differences = 0
    foreach ($item in (Read-DscRegistryDocument -FilePath $DscPath)) {
        $path = ConvertTo-ProviderPath -KeyPath $item.keyPath
        $existing = Get-ItemProperty -LiteralPath $path -Name $item.valueName -ErrorAction SilentlyContinue
        if ($null -eq $existing -or [int]($existing.($item.valueName)) -ne $item.dword) {
            Write-Host "DIFF $path\$($item.valueName)"
            $differences += 1
        }
    }
    $state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($item in @($state.registryBinary)) {
        $path = ConvertTo-ProviderPath -KeyPath $item.keyPath
        $existing = Get-ItemProperty -LiteralPath $path -Name $item.valueName -ErrorAction SilentlyContinue
        if ($null -eq $existing -or -not (Test-ByteEqual $existing.($item.valueName) (ConvertTo-ByteArray $item.value))) {
            Write-Host "DIFF $path\$($item.valueName)"
            $differences += 1
        }
    }
    foreach ($item in @($state.services)) {
        $service = Get-Service -Name $item.name -ErrorAction SilentlyContinue
        if ($null -ne $service -and ($service.StartType -ne $item.startType -or $service.Status -ne $item.state)) {
            Write-Host "DIFF service $($item.name)"
            $differences += 1
        }
    }
    foreach ($item in @($state.scheduledTasks)) {
        $task = Get-ScheduledTask -TaskPath $item.taskPath -TaskName $item.taskName -ErrorAction SilentlyContinue
        if ($null -ne $task -and $task.State -ne $item.state) {
            Write-Host "DIFF task $($item.taskName)"
            $differences += 1
        }
    }
    foreach ($name in @($state.stopProcesses)) {
        if (@(Get-Process -Name $name -ErrorAction SilentlyContinue).Count -gt 0) {
            Write-Host "DIFF running process $name"
            $differences += 1
        }
    }
    foreach ($item in @($state.stopProcessCommandLines)) {
        $processes = @(Get-CimInstance Win32_Process -Filter "Name='$($item.name).exe'" -ErrorAction SilentlyContinue |
            Where-Object { $_.CommandLine -match $item.commandLineMatch })
        if ($processes.Count -gt 0) {
            Write-Host "DIFF running process $($item.name)"
            $differences += 1
        }
    }
    if ($differences -gt 0) { exit 1 }
    Write-Host "Windows preferences match"
    exit 0
}

$elevated = Test-IsElevated
$skipped = 0

Write-Host "Applying $DscPath"
Write-Host ""

foreach ($item in (Read-DscRegistryDocument -FilePath $DscPath)) {
    $providerPath = ConvertTo-ProviderPath -KeyPath $item.keyPath
    $needsAdmin = $providerPath.StartsWith('HKLM:')

    if ($needsAdmin -and -not $elevated) {
        Write-Host "skip $providerPath\$($item.valueName) (Administrator required)"
        $skipped += 1
        continue
    }

    Set-DesiredDword -ProviderPath $providerPath -Name $item.valueName -Value $item.dword
}

if (Test-Path -LiteralPath $StatePath) {
    Write-Host ""
    Write-Host "Applying $StatePath"
    Write-Host ""

    $state = Get-Content -LiteralPath $StatePath -Raw -Encoding UTF8 | ConvertFrom-Json

    foreach ($item in @($state.registryBinary)) {
        if ($null -eq $item) { continue }
        $providerPath = ConvertTo-ProviderPath -KeyPath $item.keyPath
        $needsAdmin = $providerPath.StartsWith('HKLM:')
        if ($needsAdmin -and -not $elevated) {
            Write-Host "skip $providerPath\$($item.valueName) (Administrator required)"
            $skipped += 1
            continue
        }
        Set-DesiredBinary -ProviderPath $providerPath -Name $item.valueName -Value (ConvertTo-ByteArray $item.value)
    }

    foreach ($item in @($state.services)) {
        if ($null -eq $item) { continue }
        Set-DesiredService -Name $item.name -StartType $item.startType -State $item.state -Elevated $elevated
        if (-not $elevated -and $null -ne (Get-Service -Name $item.name -ErrorAction SilentlyContinue)) {
            $skipped += 1
        }
    }

    foreach ($item in @($state.scheduledTasks)) {
        if ($null -eq $item) { continue }
        Set-DesiredScheduledTask -TaskPath $item.taskPath -TaskName $item.taskName -State $item.state -Elevated $elevated
        if (-not $elevated -and $null -ne (Get-ScheduledTask -TaskPath $item.taskPath -TaskName $item.taskName -ErrorAction SilentlyContinue)) {
            $skipped += 1
        }
    }

    foreach ($item in @($state.stopProcessCommandLines)) {
        if ($null -eq $item) { continue }
        Stop-DesiredProcessByCommandLine -Name $item.name -CommandLineMatch $item.commandLineMatch
    }

    foreach ($name in @($state.stopProcesses)) {
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        Stop-DesiredProcess -Name $name
    }
}

Write-Host ""
if ($skipped -gt 0) {
    Write-Host "Applied with $skipped skipped admin-only item(s). Re-run elevated for services/tasks/HKLM."
} else {
    Write-Host "Windows desired state applied."
}
