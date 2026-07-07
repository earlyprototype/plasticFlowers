<#
.SYNOPSIS
    Start all plasticFlower MVP services for demo.

.DESCRIPTION
    Launches Neo4j (Docker), backend (FastAPI), and frontend (Next.js) in sequence.
    Opens browser to http://localhost:3000 when ready.

.PARAMETER FakeMode
    If specified, runs backend with PLASTICFLOWER_FAKE_LLM=1 and PLASTICFLOWER_FAKE_EMBEDDINGS=1
    for testing without Gemini API calls.

.EXAMPLE
    .\scripts\start_mvp.ps1
    Starts all services with real Gemini.

.EXAMPLE
    .\scripts\start_mvp.ps1 -FakeMode
    Starts all services with fake LLM/embeddings.
#>

param(
    [switch]$FakeMode
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  plasticFlower MVP Startup" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# 1. Check prerequisites
Write-Host "[1/5] Checking prerequisites..." -ForegroundColor Yellow

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Docker not found. Please install Docker Desktop." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command node -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Node.js not found. Please install Node.js 18+." -ForegroundColor Red
    exit 1
}

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "ERROR: Python not found. Please install Python 3.11+." -ForegroundColor Red
    exit 1
}

Write-Host "  Docker, Node.js, Python found." -ForegroundColor Green

# 2. Check .env file
Write-Host "`n[2/5] Checking environment..." -ForegroundColor Yellow

$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "WARNING: .env file not found. Creating from .env.example..." -ForegroundColor Yellow
    $ExampleFile = Join-Path $ProjectRoot ".env.example"
    if (Test-Path $ExampleFile) {
        Copy-Item $ExampleFile $EnvFile
        Write-Host "  Created .env from .env.example. Please edit with your credentials." -ForegroundColor Yellow
    } else {
        Write-Host "ERROR: No .env or .env.example found." -ForegroundColor Red
        exit 1
    }
}

# Load .env
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        [Environment]::SetEnvironmentVariable($matches[1].Trim(), $matches[2].Trim(), "Process")
    }
}

if (-not $FakeMode -and [string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
    Write-Host "WARNING: GEMINI_API_KEY not set. Real Gemini mode may fail." -ForegroundColor Yellow
}

Write-Host "  Environment loaded." -ForegroundColor Green

# 3. Start Neo4j
Write-Host "`n[3/5] Starting Neo4j..." -ForegroundColor Yellow

$DockerDir = Join-Path $ProjectRoot "docker"
Push-Location $DockerDir

$Neo4jRunning = docker ps --filter "name=plasticflower-neo4j" --format "{{.Names}}" 2>$null
if ($Neo4jRunning) {
    Write-Host "  Neo4j already running." -ForegroundColor Green
} else {
    docker compose up -d
    Write-Host "  Neo4j starting... waiting 10s for readiness." -ForegroundColor Yellow
    Start-Sleep -Seconds 10
}

Pop-Location

# 4. Start Backend
Write-Host "`n[4/5] Starting backend..." -ForegroundColor Yellow

$BackendDir = Join-Path $ProjectRoot "backend"

if ($FakeMode) {
    $env:PLASTICFLOWER_FAKE_LLM = "1"
    $env:PLASTICFLOWER_FAKE_EMBEDDINGS = "1"
    Write-Host "  Fake mode enabled (no Gemini API calls)." -ForegroundColor Yellow
} else {
    Remove-Item Env:PLASTICFLOWER_FAKE_LLM -ErrorAction SilentlyContinue
    Remove-Item Env:PLASTICFLOWER_FAKE_EMBEDDINGS -ErrorAction SilentlyContinue
    Write-Host "  Real Gemini mode." -ForegroundColor Green
}

$BackendJob = Start-Job -ScriptBlock {
    param($Dir, $Fake)
    Set-Location $Dir
    if ($Fake) {
        $env:PLASTICFLOWER_FAKE_LLM = "1"
        $env:PLASTICFLOWER_FAKE_EMBEDDINGS = "1"
    }
    & python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
} -ArgumentList $BackendDir, $FakeMode

Write-Host "  Backend starting on http://127.0.0.1:8010..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check backend health
try {
    $Health = Invoke-WebRequest -Uri "http://127.0.0.1:8010/health" -UseBasicParsing -TimeoutSec 10
    if ($Health.StatusCode -eq 200) {
        Write-Host "  Backend healthy." -ForegroundColor Green
    }
} catch {
    Write-Host "  Backend may still be starting. Check http://127.0.0.1:8010/health" -ForegroundColor Yellow
}

# 5. Start Frontend
Write-Host "`n[5/5] Starting frontend..." -ForegroundColor Yellow

$FrontendDir = Join-Path $ProjectRoot "frontend"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8010"

$FrontendJob = Start-Job -ScriptBlock {
    param($Dir)
    Set-Location $Dir
    $env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8010"
    & npm run dev
} -ArgumentList $FrontendDir

Write-Host "  Frontend starting on http://localhost:3000..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Open browser
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  MVP Ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "  Backend:  http://127.0.0.1:8010" -ForegroundColor White
Write-Host "  Neo4j:    http://localhost:7474" -ForegroundColor White
Write-Host ""
if ($FakeMode) {
    Write-Host "  Mode: FAKE (no Gemini API calls)" -ForegroundColor Yellow
} else {
    Write-Host "  Mode: REAL Gemini" -ForegroundColor Green
}
Write-Host ""
Write-Host "  Press Ctrl+C to stop all services." -ForegroundColor Gray
Write-Host ""

# Open browser
Start-Process "http://localhost:3000"

# Wait for user interrupt
try {
    Write-Host "Services running. Waiting for Ctrl+C..." -ForegroundColor Gray
    while ($true) {
        Start-Sleep -Seconds 5
        # Check if jobs are still running
        if ($BackendJob.State -ne "Running") {
            Write-Host "Backend stopped unexpectedly. Check logs." -ForegroundColor Red
        }
        if ($FrontendJob.State -ne "Running") {
            Write-Host "Frontend stopped unexpectedly. Check logs." -ForegroundColor Red
        }
    }
} finally {
    Write-Host "`nStopping services..." -ForegroundColor Yellow
    Stop-Job $BackendJob -ErrorAction SilentlyContinue
    Stop-Job $FrontendJob -ErrorAction SilentlyContinue
    Remove-Job $BackendJob -ErrorAction SilentlyContinue
    Remove-Job $FrontendJob -ErrorAction SilentlyContinue
    Write-Host "Services stopped. Neo4j still running (stop with: docker compose -f docker/docker-compose.yml down)" -ForegroundColor Gray
}

