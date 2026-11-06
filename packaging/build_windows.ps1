param([string]$OutputDirectory = "dist", [string]$PythonExecutable = "python")
$ErrorActionPreference = "Stop"
& $PythonExecutable -m PyInstaller --noconfirm --clean --onedir --console --name HyunCalculator --paths . --collect-all matplotlib --hidden-import scipy.special._ufuncs --distpath $OutputDirectory --workpath work/pyinstaller --specpath work packaging/windows_entry.py
if ($LASTEXITCODE -ne 0) { throw "Windows build failed" }
$exe = Join-Path $OutputDirectory 'HyunCalculator/HyunCalculator.exe'
& $exe --list-formulas
if ($LASTEXITCODE -ne 0) { throw "Frozen formula catalog check failed" }
& $exe --generate FIN-004 --structure class --loop while
if ($LASTEXITCODE -ne 0) { throw "Frozen code generation check failed" }
Compress-Archive -Path (Join-Path $OutputDirectory 'HyunCalculator') -DestinationPath (Join-Path $OutputDirectory 'HyunCalculator-Windows-x64.zip') -Force
