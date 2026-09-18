param(
    [switch]$SkipInstaller
)

$ErrorActionPreference = "Stop"
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pyproject = Get-Content -LiteralPath (Join-Path $projectRoot "pyproject.toml")
$versionLine = $pyproject | Where-Object { $_ -match '^version\s*=\s*"([^"]+)"' } | Select-Object -First 1
if (-not $versionLine) {
    throw "Versão do projeto não encontrada em pyproject.toml"
}
$version = [regex]::Match($versionLine, '^version\s*=\s*"([^"]+)"').Groups[1].Value

Push-Location $projectRoot
try {
    python -m PyInstaller --clean --noconfirm packaging/auto_sped.spec
    if ($LASTEXITCODE -ne 0) {
        throw "PyInstaller falhou com o código $LASTEXITCODE"
    }

    $executable = Join-Path $projectRoot "dist\Auto-SPED\Auto-SPED.exe"
    if (-not (Test-Path -LiteralPath $executable)) {
        throw "Executável não foi gerado em $executable"
    }

    if (-not $SkipInstaller) {
        $iscc = Get-Command iscc.exe -ErrorAction SilentlyContinue
        if (-not $iscc) {
            $standardPath = "C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
            if (Test-Path -LiteralPath $standardPath) {
                $iscc = Get-Item -LiteralPath $standardPath
            }
        }
        if (-not $iscc) {
            throw "Inno Setup 6 não encontrado; use -SkipInstaller para gerar apenas o aplicativo."
        }
        & $iscc.Source "/DMyAppVersion=$version" "packaging\installer.iss"
        if ($LASTEXITCODE -ne 0) {
            throw "Inno Setup falhou com o código $LASTEXITCODE"
        }
    }

    Write-Host "Auto-SPED $version gerado em dist\Auto-SPED"
}
finally {
    Pop-Location
}
