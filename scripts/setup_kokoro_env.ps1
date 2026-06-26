$ErrorActionPreference = "Stop"

$ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..")
$VenvPath = Join-Path $ProjectRoot ".venv-kokoro"
$Requirements = Join-Path $ProjectRoot "requirements-kokoro.txt"
$CodexPython = "C:\Users\AlenZhu\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

function Invoke-NativeChecked {
    param(
        [string] $Exe,
        [string[]] $NativeArgs
    )

    & $Exe @NativeArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Exe $($NativeArgs -join ' ')"
    }
}

function Get-Python312 {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        try {
            & py -3.12 --version *> $null
            if ($LASTEXITCODE -eq 0) {
                return @{ Exe = "py"; Args = @("-3.12") }
            }
        } catch {}
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        $version = & python -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($version -eq "3.12" -or $version -eq "3.11" -or $version -eq "3.10") {
            return @{ Exe = "python"; Args = @() }
        }
    }

    if (Test-Path $CodexPython) {
        $version = & $CodexPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
        if ($version -eq "3.12" -or $version -eq "3.11" -or $version -eq "3.10") {
            return @{ Exe = $CodexPython; Args = @() }
        }
    }

    throw "No compatible Python found. Install Python 3.12, then run this script again."
}

$PythonCommand = Get-Python312
Write-Host "Using Python: $($PythonCommand.Exe) $($PythonCommand.Args -join ' ')"

if (-not (Test-Path $VenvPath)) {
    Invoke-NativeChecked -Exe $PythonCommand.Exe -NativeArgs @($PythonCommand.Args + @("-m", "venv", $VenvPath))
}

$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
Invoke-NativeChecked -Exe $VenvPython -NativeArgs @("-m", "pip", "install", "--upgrade", "pip")
Invoke-NativeChecked -Exe $VenvPython -NativeArgs @("-m", "pip", "install", "-r", $Requirements)

Write-Host ""
Write-Host "Kokoro environment is ready."
Write-Host "Run a test with:"
Write-Host ".\.venv-kokoro\Scripts\python.exe .\scripts\synthesize_kokoro.py --chapter 1 --limit 5"
