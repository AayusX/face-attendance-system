param(
    [string]$Publisher = "",
    [string]$PackageName = "FaceAttendanceSystem",
    [string]$Version = "1.0.0.0",
    [string]$SourceDir = "",
    [string]$OutputDir = "",
    [switch]$SelfSign
)

$ErrorActionPreference = "Stop"
$thisDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$sdkTools = "C:\Users\techn\AppData\Local\opencode\sdk-buildtools\bin\10.0.28000.0\x64"
$makeappx = Join-Path $sdkTools "makeappx.exe"
$signtool = Join-Path $sdkTools "signtool.exe"

if (-not $SourceDir) { $SourceDir = Join-Path $thisDir "..\dist\FaceAttendance" }
if (-not $OutputDir) { $OutputDir = $thisDir }
if (-not $Publisher) { $Publisher = "CN=FaceAttendanceSystem" }
$staging = Join-Path $env:TEMP "msix_staging"

if (-not $Publisher -or $Publisher -eq "CN=FaceAttendanceSystem") {
    Write-Warning "Publisher is '$Publisher'. For Store submission set -Publisher to the exact value from Partner Center (e.g. 'CN=<publisher-id>')."
}

if (-not (Test-Path (Join-Path $SourceDir "FaceAttendance.exe"))) {
    throw "Source build not found at $SourceDir. Run build_windows.bat first."
}

if (Test-Path $staging) { Remove-Item -Recurse -Force $staging }
New-Item -ItemType Directory -Path $staging | Out-Null

Write-Host "Copying bundle into staging..."
Copy-Item -Recurse -Force (Join-Path $SourceDir "*") $staging

Write-Host "Removing portable data folders (recreated under LOCALAPPDATA on first run)..."
foreach ($dir in @("database", "exports", "faces")) {
    Remove-Item -Recurse -Force (Join-Path $staging $dir) -ErrorAction SilentlyContinue
}

Write-Host "Adding msix.marker (switches app to %LOCALAPPDATA% data)..."
New-Item -ItemType File -Path (Join-Path $staging "msix.marker") -Force | Out-Null

Write-Host "Copying store assets..."
Copy-Item -Recurse -Force (Join-Path $PSScriptRoot "..\msix_assets") (Join-Path $staging "Assets")

Write-Host "Writing AppxManifest.xml..."
$template = Get-Content (Join-Path $PSScriptRoot "AppxManifest.template.xml") -Raw
$manifest = $template.Replace("__PACKAGE_NAME__", $PackageName).Replace("__PUBLISHER__", $Publisher).Replace("__VERSION__", $Version)
Set-Content -Path (Join-Path $staging "AppxManifest.xml") -Value $manifest -Encoding UTF8

$output = Join-Path $OutputDir ("{0}_{1}_x64.msix" -f $PackageName, $Version)
if (Test-Path $output) { Remove-Item -Force $output }

Write-Host "Packing MSIX ($makeappx)..."
& $makeappx pack /d $staging /p $output /o
if ($LASTEXITCODE -ne 0) { throw "MakeAppx failed with exit code $LASTEXITCODE" }

if ($SelfSign) {
    Write-Host "Creating self-signed cert for local test-install..."
    $subject = $Publisher
    $cert = New-SelfSignedCertificate -Type CodeSigningCert -Subject $subject `
        -CertStoreLocation Cert:\CurrentUser\My -NotAfter (Get-Date).AddYears(1)
    Write-Host "Signing with signtool (thumbprint $($cert.Thumbprint))..."
    & $signtool sign /fd SHA256 /sha1 $cert.Thumbprint $output
    if ($LASTEXITCODE -ne 0) { throw "Signtool failed with exit code $LASTEXITCODE" }
    $export = Join-Path $OutputDir "test-cert.cer"
    Export-Certificate -Cert $cert -FilePath $export | Out-Null
    Write-Host "Imported to current-user so Add-AppxPackage will trust it."
    Import-Certificate -FilePath $export -CertStoreLocation Cert:\CurrentUser\Root | Out-Null
    Import-Certificate -FilePath $export -CertStoreLocation Cert:\CurrentUser\TrustedPeople | Out-Null
}

Write-Host ""
Write-Host "MSIX ready: $output"
Write-Host "Install locally with:  Add-AppxPackage -Path '$output'"