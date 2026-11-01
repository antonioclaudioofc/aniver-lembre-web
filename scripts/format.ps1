param([switch]$Check)

$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)

$ruff = '.\.venv\Scripts\ruff.exe'
if (-not (Test-Path $ruff)) {
  Write-Host 'ruff nao encontrado. Rodando: pip install -r requirements-dev.txt'
  & .\.venv\Scripts\python.exe -m pip install -q -r requirements-dev.txt
}

$failed = $false

Write-Host '== Python (ruff) =='
if ($Check) {
  & $ruff check .;          if ($LASTEXITCODE -ne 0) { $failed = $true }
  & $ruff format --check .; if ($LASTEXITCODE -ne 0) { $failed = $true }
} else {
  & $ruff check --fix .
  & $ruff format .
}

Write-Host '== CSS / JS / JSON / Markdown (prettier) =='
if (Get-Command npx -ErrorAction SilentlyContinue) {
  $mode = if ($Check) { '--check' } else { '--write' }
  npx --yes prettier@3 $mode 'base_static/**/*.{css,js}' '*.json' 'docs/**/*.md'
  if ($LASTEXITCODE -ne 0) { $failed = $true }
} else {
  Write-Warning 'Node/npx nao encontrado — pulando prettier.'
}

if ($failed) { Write-Error 'Formatacao pendente.'; exit 1 }
Write-Host 'OK'
