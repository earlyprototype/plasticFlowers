#!/usr/bin/env pwsh
# Check available Gemini models via API

param(
    [switch]$Quota,
    [switch]$Help
)

if ($Help) {
    Write-Host @"

GEMINI API CHECK SCRIPT
=======================

Usage:
  .\check_gemini_models.ps1          List available models
  .\check_gemini_models.ps1 -Help    Show this help

Note: the -Quota mode was removed (backend/check_quota.py no longer exists).
For rate-limit/rotation diagnostics see backend/scripts/diagnostics/
(e.g. check_model_rotation.py).

"@ -ForegroundColor Cyan
    exit 0
}

$backendPath = Join-Path $PSScriptRoot "..\backend"

if ($Quota) {
    Write-Host "`nERROR: the -Quota mode was removed - backend/check_quota.py no longer exists." -ForegroundColor Red
    Write-Host "For quota/rate-limit diagnostics, use the scripts in backend/scripts/diagnostics/," -ForegroundColor Yellow
    Write-Host "e.g. backend/scripts/diagnostics/check_model_rotation.py (models + free-tier rate limits)." -ForegroundColor Yellow
    exit 1
}

Write-Host "`nChecking available Gemini models..." -ForegroundColor Cyan
$pythonScript = Join-Path $backendPath "scripts\diagnostics\list_models.py"

# Check if virtual environment exists
$venvPath = Join-Path $backendPath ".venv\Scripts\python.exe"

if (Test-Path $venvPath) {
    Write-Host "Using virtual environment Python..." -ForegroundColor Green
    & $venvPath $pythonScript
} else {
    Write-Host "Virtual environment not found, using system Python..." -ForegroundColor Yellow
    python $pythonScript
}

if ($LASTEXITCODE -ne 0) {
    Write-Host "`nScript failed with exit code $LASTEXITCODE" -ForegroundColor Red
    exit $LASTEXITCODE
}


