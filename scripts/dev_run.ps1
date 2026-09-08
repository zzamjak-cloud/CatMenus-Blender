$ErrorActionPreference = "Stop"

$RootDir = Resolve-Path (Join-Path $PSScriptRoot "..")
$AddonId = "cat_menus"
$BlenderBinary = $env:BLENDER_BINARY
if ([string]::IsNullOrWhiteSpace($BlenderBinary)) {
    $BlenderBinary = Join-Path $env:ProgramFiles "Blender Foundation\Blender 5.2\blender.exe"
}

if (-not (Test-Path -LiteralPath $BlenderBinary -PathType Leaf)) {
    Write-Error "Blender 실행 파일을 찾을 수 없습니다: $BlenderBinary"
}

if (-not (Test-Path -LiteralPath (Join-Path $RootDir "blender_manifest.toml") -PathType Leaf)) {
    Write-Error "저장소 루트에 blender_manifest.toml이 없습니다: $RootDir"
}

$VersionOutput = & $BlenderBinary --background --factory-startup --version
if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
$BlenderVersion = (($VersionOutput | Select-Object -First 1) -split "\s+")[1]

if ([string]::IsNullOrWhiteSpace($env:CATMENUS_BLENDER_PROFILE)) {
    # 저장소 안에 프로필을 두면 Extension 링크가 자기 자신을 가리켜 빌드가 무한 재귀한다.
    $ProfileDir = Join-Path $env:LOCALAPPDATA "Blender Foundation\Blender\CatMenusBlenderDev\$BlenderVersion"
} else {
    $ProfileDir = $env:CATMENUS_BLENDER_PROFILE
}

$ExtensionsDir = Join-Path $ProfileDir "extensions\user_default"
$LinkPath = Join-Path $ExtensionsDir $AddonId
New-Item -ItemType Directory -Force -Path $ExtensionsDir | Out-Null

if (Test-Path -LiteralPath $LinkPath) {
    $Item = Get-Item -LiteralPath $LinkPath -Force
    if ($Item.LinkType -eq "Junction" -or $Item.LinkType -eq "SymbolicLink") {
        $Target = [System.IO.Path]::GetFullPath($Item.Target)
        $Expected = [System.IO.Path]::GetFullPath($RootDir)
        if ($Target -ne $Expected) {
            Remove-Item -LiteralPath $LinkPath -Force
            New-Item -ItemType Junction -Path $LinkPath -Target $RootDir | Out-Null
        }
    } else {
        Write-Error "Extension 링크 위치에 실제 파일 또는 폴더가 있습니다: $LinkPath"
    }
} else {
    New-Item -ItemType Junction -Path $LinkPath -Target $RootDir | Out-Null
}

$env:BLENDER_USER_RESOURCES = $ProfileDir
$env:CATMENUS_SOURCE_DIR = $RootDir
$env:CATMENUS_ADDON_ID = $AddonId

& $BlenderBinary --python-exit-code 1 --python (Join-Path $RootDir "scripts\dev_bootstrap.py") @args
exit $LASTEXITCODE
