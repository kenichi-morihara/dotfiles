$ErrorActionPreference = 'Stop'
$script = Join-Path $PSScriptRoot '../scripts/windows/configure.ps1'
$tokens = $null
$errors = $null
$null = [System.Management.Automation.Language.Parser]::ParseFile($script, [ref]$tokens, [ref]$errors)
if ($errors.Count -gt 0) { throw ($errors | Out-String) }

function Get-ItemProperty {
    param($LiteralPath, $Name, $ErrorAction)
    $values = @{}
    if ($Name -match 'IsShadow|Dwm|RecEnabled') { $values[$Name] = [byte[]]@(0,0,0,0) }
    else { $values[$Name] = 0 }
    return [pscustomobject]$values
}
function Get-Service { param($Name, $ErrorAction) return $null }
function Get-ScheduledTask { param($TaskPath, $TaskName, $ErrorAction) return $null }
function Get-Process { param($Name, $ErrorAction) return @() }
function Get-CimInstance { param($ClassName, $Filter, $ErrorAction) return @() }
function New-Item { throw 'Check attempted a write' }
function New-ItemProperty { throw 'Check attempted a registry write' }
function Set-Service { throw 'Check attempted a service update' }
function Stop-Service { throw 'Check attempted a service stop' }
function Disable-ScheduledTask { throw 'Check attempted a task update' }
function taskkill.exe { throw 'Check attempted a process stop' }
& $script -Check
