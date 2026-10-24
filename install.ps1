<#
.SYNOPSIS
  Windows launcher for the Zenodotus installer. Finds Git Bash and runs install.sh with your arguments.

.DESCRIPTION
  install.sh is the single installer (macOS, Linux, WSL, Git Bash). This script does not reimplement it:
  it only locates Git Bash and delegates, so Windows and Unix installs cannot drift apart.
  Claude Code and the Zenodotus hooks need bash on Windows anyway (Git for Windows provides it).

.EXAMPLE
  .\install.ps1                          # Claude Code
  .\install.ps1 --target codex           # Codex CLI
  .\install.ps1 --target all             # both
#>
[CmdletBinding()]
param(
  [Parameter(ValueFromRemainingArguments = $true)]
  [string[]]$InstallArgs
)

$ErrorActionPreference = 'Stop'

function Find-GitBash {
  $candidates = @()
  # Prefer the bash that ships with Git for Windows. Skip System32\bash.exe: that is the WSL launcher,
  # which would install into the Linux home instead of your Windows profile.
  $onPath = Get-Command bash.exe -All -ErrorAction SilentlyContinue |
    Where-Object { $_.Source -notmatch '\\System32\\|\\WindowsApps\\' } |
    Select-Object -ExpandProperty Source
  $candidates += $onPath
  foreach ($base in @($env:ProgramFiles, ${env:ProgramFiles(x86)}, "$env:LocalAppData\Programs")) {
    if ($base) { $candidates += (Join-Path $base 'Git\bin\bash.exe') }
  }
  $candidates | Where-Object { $_ -and (Test-Path $_) } | Select-Object -First 1
}

$bash = Find-GitBash
if (-not $bash) {
  Write-Error @"
Git Bash was not found.
Install Git for Windows (https://git-scm.com/download/win), then run this script again.
Prefer WSL? Run ./install.sh inside WSL instead; note that installs into the WSL home, not your Windows profile.
"@
  exit 1
}

$root = $PSScriptRoot
$script = (Join-Path $root 'install.sh') -replace '\\', '/'
Write-Host "Using bash: $bash"
& $bash $script @InstallArgs
exit $LASTEXITCODE
