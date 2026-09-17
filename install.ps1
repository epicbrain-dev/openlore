<#
.SYNOPSIS
    OpenLore Cross-Platform Installer for Windows 10 & 11
.DESCRIPTION
    Provisions isolated Python runtime, installs OpenLore, deploys Web Cockpit assets,
    creates executable shims (openlore.cmd, openlore.ps1), and configures Windows User PATH.
.EXAMPLE
    irm https://raw.githubusercontent.com/epicbrain-dev/openlore/main/install.ps1 | iex
.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\install.ps1 -Yes
#>

[CmdletBinding()]
param (
    [string]$Prefix = "",
    [switch]$Yes,
    [switch]$NoModifyPath,
    [string]$WithDCC = "",
    [switch]$LaunchWeb,
    [switch]$Uninstall,
    [switch]$Quiet
)

$Host.UI.RawUI.ForegroundColor = "Cyan"
Write-Host @"
╔═════════════════════════════════════════════════════════════════════════╗
║   OpenLore — Version Control & Lore Engine for 3D Worlds & VFX          ║
║   Windows PowerShell Turnkey Installer                                  ║
╚═════════════════════════════════════════════════════════════════════════╝
"@
$Host.UI.RawUI.ForegroundColor = "White"

# 1. Locate suitable Python 3.9+
$FoundPython = $null

# Check if python command is available
$pyCmd = Get-Command python.exe -ErrorAction SilentlyContinue
if ($pyCmd) {
    $verOutput = & $pyCmd.Source -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
    if ($verOutput -match "^(\d+)\.(\d+)") {
        $major = [int]$matches[1]
        $minor = [int]$matches[2]
        if ($major -ge 3 -and $minor -ge 9) {
            $FoundPython = $pyCmd.Source
        }
    }
}

# Try py launcher
if (-not $FoundPython) {
    $pyLauncher = Get-Command py.exe -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $verOutput = & py -3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null
        if ($verOutput -match "^(\d+)\.(\d+)") {
            $major = [int]$matches[1]
            $minor = [int]$matches[2]
            if ($major -ge 3 -and $minor -ge 9) {
                $FoundPython = "py -3"
            }
        }
    }
}

# Scan standard Windows directories
if (-not $FoundPython) {
    $searchPaths = @(
        "$env:LOCALAPPDATA\Programs\Python\Python3*\python.exe",
        "$env:ProgramFiles\Python3*\python.exe",
        "C:\Python3*\python.exe"
    )
    foreach ($pat in $searchPaths) {
        $cands = Resolve-Path $pat -ErrorAction SilentlyContinue
        if ($cands) {
            $FoundPython = $cands[0].Path
            break
        }
    }
}

if (-not $FoundPython) {
    Write-Host "`n❌ Python 3.9+ was not found on your system." -ForegroundColor Red
    Write-Host "Please install Python using Windows Package Manager (winget):" -ForegroundColor Yellow
    Write-Host "  winget install Python.Python.3.12`n" -ForegroundColor Cyan
    Write-Host "Or download Python from https://www.python.org/downloads/windows/" -ForegroundColor White
    exit 1
}

Write-Host "  • Detected Python: $FoundPython" -ForegroundColor Green

# 2. Locate or download installer.py
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path -ErrorAction SilentlyContinue
$InstallerFile = ""
$TempDir = ""

if ($ScriptDir -and (Test-Path "$ScriptDir\installer.py")) {
    $InstallerFile = "$ScriptDir\installer.py"
} else {
    $TempDir = Join-Path $env:TEMP "openlore-install-$([System.Guid]::NewGuid().ToString('N'))"
    New-Item -ItemType Directory -Path $TempDir -Force | Out-Null
    $InstallerFile = Join-Path $TempDir "installer.py"
    Write-Host "  • Downloading installer manifest..." -ForegroundColor Cyan
    Invoke-WebRequest -Uri "https://raw.githubusercontent.com/epicbrain-dev/openlore/main/installer.py" -OutFile $InstallerFile -UseBasicParsing
}

# 3. Assemble arguments
$pyArgs = @($InstallerFile)
if ($Prefix) { $pyArgs += @("--prefix", $Prefix) }
if ($Yes) { $pyArgs += "--yes" }
if ($NoModifyPath) { $pyArgs += "--no-modify-path" }
if ($WithDCC) { $pyArgs += @("--with-dcc", $WithDCC) }
if ($LaunchWeb) { $pyArgs += "--launch-web" }
if ($Uninstall) { $pyArgs += "--uninstall" }
if ($Quiet) { $pyArgs += "--quiet" }

# 4. Execute installer
if ($FoundPython -eq "py -3") {
    & py -3 @pyArgs
} else {
    & $FoundPython @pyArgs
}
$ExitCode = $LASTEXITCODE

# Cleanup temp if downloaded
if ($TempDir -and (Test-Path $TempDir)) {
    Remove-Item -Recurse -Force $TempDir -ErrorAction SilentlyContinue
}

exit $ExitCode
