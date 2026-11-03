param([switch]$InstallBuildDependencies, [switch]$Clean)
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $Root
$Python = (Get-Command py.exe -ErrorAction Stop).Source
$Icon = Join-Path $Root "ui_qt\assets\app_icon.ico"
$CheckIcon = Join-Path $Root "ui_qt\assets\check_white.svg"
$BrandAssets = @("logo_256.png", "logo_32.png", "logo_header.png", "new_logo.png") | ForEach-Object { Join-Path $Root "ui_qt\assets\$_" }

if ($InstallBuildDependencies) {
    & $Python -3.13 -m pip install -r requirements.txt pyinstaller==6.22.3
    if ($LASTEXITCODE -ne 0) { throw "Could not install native desktop build dependencies." }
}
& $Python -3.13 -c "import PyInstaller, PySide6, scipy, pandas, docx, pyreadstat"
if ($LASTEXITCODE -ne 0) { throw "Install requirements.txt and PyInstaller before building." }
if (-not (Test-Path -LiteralPath $Icon)) { throw "Native application icon missing: $Icon" }
if (-not (Test-Path -LiteralPath $CheckIcon)) { throw "Checkbox indicator icon missing: $CheckIcon" }
foreach ($asset in $BrandAssets) {
    if (-not (Test-Path -LiteralPath $asset)) { throw "JouriEpi brand asset missing: $asset" }
}

if ($Clean) {
    foreach ($path in @("build\JouriEpi", "dist\JouriEpi")) {
        if (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Recurse -Force }
    }
}

Write-Host "Building the native PySide6 workstation (onedir)..." -ForegroundColor Cyan
$Args = @(
    "--noconfirm", "--onedir", "--windowed",
    "--name", "JouriEpi", "--icon", $Icon,
    "--add-data", "$Icon;ui_qt\assets",
    "--add-data", "$CheckIcon;ui_qt\assets",
    "--paths", $Root,
    "--exclude-module", "streamlit", "--exclude-module", "webview",
    "--exclude-module", "webbrowser", "--exclude-module", "PySide6.QtWebEngineCore",
    "--exclude-module", "PySide6.QtWebEngineWidgets", "--exclude-module", "PySide6.QtWebEngineQuick",
    "--exclude-module", "PySide6.QtWebChannel",
    "--collect-all", "shiboken6",
    "--collect-all", "pyreadstat", "--collect-all", "docx",
    "--distpath", "dist", "--specpath", "build\specs", "ui_qt\main.py"
)
foreach ($asset in $BrandAssets) {
    $Args += @("--add-data", "$asset;ui_qt\assets")
}
& $Python -3.13 -m PyInstaller @Args
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed while building the native JouriEpi workstation." }

$Executable = Join-Path $Root "dist\JouriEpi\JouriEpi.exe"
if (-not (Test-Path -LiteralPath $Executable)) { throw "Native executable missing: $Executable" }

# Produce a portable onedir archive; users must extract the whole folder so
# Qt plugins and bundled scientific DLLs remain beside the executable.
$PortableArchive = Join-Path $Root "dist\JouriEpi_v1.0_Portable.zip"
New-Item -ItemType Directory -Path (Split-Path -Parent $PortableArchive) -Force | Out-Null
if (Test-Path -LiteralPath $PortableArchive) { Remove-Item -LiteralPath $PortableArchive -Force }
Add-Type -AssemblyName System.IO.Compression.FileSystem
[System.IO.Compression.ZipFile]::CreateFromDirectory(
    (Join-Path $Root "dist\JouriEpi"),
    $PortableArchive,
    [System.IO.Compression.CompressionLevel]::Optimal,
    $false
)
if (-not (Test-Path -LiteralPath $PortableArchive)) { throw "Portable archive missing: $PortableArchive" }
$Hash = (Get-FileHash -LiteralPath $PortableArchive -Algorithm SHA256).Hash.ToLowerInvariant()

# Compile the conventional Windows setup wizard as well as the portable ZIP.
# Inno Setup is a separate build prerequisite; never silently ship only one
# of the two requested distribution formats.
$CompilerCandidates = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Inno Setup 6\ISCC.exe"),
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe"
)
$Compiler = $CompilerCandidates | Where-Object { $_ -and (Test-Path -LiteralPath $_) } | Select-Object -First 1
if (-not $Compiler) {
    $Command = Get-Command "ISCC.exe" -ErrorAction SilentlyContinue
    if ($Command) { $Compiler = $Command.Source }
}
if (-not $Compiler) {
    throw "Inno Setup 6 is required to build JouriEpi_Setup_v1.0.exe. Install it from https://jrsoftware.org/isinfo.php and rerun this script. The portable ZIP has already been created."
}
Write-Host "Compiling the Windows installer with Inno Setup..." -ForegroundColor Cyan
Push-Location (Join-Path $Root "installer")
try {
    & $Compiler "/Qp" "JouriEpi.iss"
} finally {
    Pop-Location
}
if ($LASTEXITCODE -ne 0) { throw "Inno Setup failed while compiling the JouriEpi installer." }
$Setup = Join-Path $Root "dist\installer\JouriEpi_Setup_v1.0.exe"
if (-not (Test-Path -LiteralPath $Setup)) { throw "Windows setup executable missing: $Setup" }
$SetupHash = (Get-FileHash -LiteralPath $Setup -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Host "Native build complete: $Executable" -ForegroundColor Green
Write-Host "Portable package complete: $PortableArchive" -ForegroundColor Green
Write-Host "SHA-256: $Hash" -ForegroundColor Green
Write-Host "Windows installer complete: $Setup" -ForegroundColor Green
Write-Host "Installer SHA-256: $SetupHash" -ForegroundColor Green
