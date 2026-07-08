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
  .\check_gemini_models.ps1 -Quota   Check quota and rate limits
  .\check_gemini_models.ps1 -Help    Show this help

"@ -ForegroundColor Cyan
    exit 0
}

$backendPath = Join-Path $PSScriptRoot "..\backend"

if ($Quota) {
    Write-Host "`nChecking Gemini API quota and rate limits..." -ForegroundColor Cyan
    $pythonScript = Join-Path $backendPath "check_quota.py"
} else {
    Write-Host "`nChecking available Gemini models..." -ForegroundColor Cyan
    $pythonScript = Join-Path $backendPath "list_models.py"
}

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


