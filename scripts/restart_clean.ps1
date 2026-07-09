<#
.SYNOPSIS
    Clean restart script - kills old processes and starts PlasticFlower with proper environment.

.DESCRIPTION
    This script:
    1. Kills any existing backend/frontend processes
    2. Loads environment variables from .env file
    3. Ensures Neo4j is running
    4. Starts backend (FastAPI) on port 8010
    5. Starts frontend (Next.js) on port 3000
    
.PARAMETER FakeMode
    If specified, runs backend with fake LLM/embeddings (no Gemini API calls needed).

.EXAMPLE
    .\scripts\restart_clean.ps1
    Kills old processes and starts with real Gemini.

.EXAMPLE
    .\scripts\restart_clean.ps1 -FakeMode
    Kills old processes and starts with fake LLM (for testing).
#>

param(
    [switch]$FakeMode
)

$ErrorActionPreference = "Continue"
$ProjectRoot = Split-Path -Parent $PSScriptRoot

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  PlasticFlower - Clean Restart" -ForegroundColor Cyan
Write-Host "========================================`n" -ForegroundColor Cyan

# ============================================================================
# STEP 1: Kill existing processes
# ============================================================================
Write-Host "[1/6] Stopping existing processes..." -ForegroundColor Yellow

# Kill processes on port 8010 (backend)
Write-Host "  - Checking port 8010 (backend)..." -NoNewline
$backend = Get-NetTCPConnection -LocalPort 8010 -ErrorAction SilentlyContinue
if ($backend) {
    $backendPid = $backend.OwningProcess
    Stop-Process -Id $backendPid -Force -ErrorAction SilentlyContinue
    Write-Host " Killed PID $backendPid" -ForegroundColor Green
} else {
    Write-Host " Not running" -ForegroundColor Gray
}

# Kill processes on port 3000 (frontend)
Write-Host "  - Checking port 3000 (frontend)..." -NoNewline
$frontend = Get-NetTCPConnection -LocalPort 3000 -ErrorAction SilentlyContinue
if ($frontend) {
    $frontendPid = $frontend.OwningProcess
    Stop-Process -Id $frontendPid -Force -ErrorAction SilentlyContinue
    Write-Host " Killed PID $frontendPid" -ForegroundColor Green
} else {
    Write-Host " Not running" -ForegroundColor Gray
}

# Wait for ports to be released
Start-Sleep -Seconds 2
Write-Host "  Ports cleared." -ForegroundColor Green

# ============================================================================
# STEP 2: Load environment variables
# ============================================================================
Write-Host "`n[2/6] Loading environment..." -ForegroundColor Yellow

$EnvFile = Join-Path $ProjectRoot ".env"
if (-not (Test-Path $EnvFile)) {
    Write-Host "ERROR: .env file not found at: $EnvFile" -ForegroundColor Red
    Write-Host "Please create a .env file with your GEMINI_API_KEY and NEO4J_PASSWORD" -ForegroundColor Yellow
    exit 1
}

# Load .env file
Get-Content $EnvFile | ForEach-Object {
    if ($_ -match "^([^#][^=]+)=(.*)$") {
        $key = $matches[1].Trim()
        $value = $matches[2].Trim()
        [Environment]::SetEnvironmentVariable($key, $value, "Process")
        Write-Host "  Set: $key" -ForegroundColor Gray
    }
}

# Check critical environment variables
if (-not $FakeMode) {
    if ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY)) {
        Write-Host "WARNING: GEMINI_API_KEY not set in .env file." -ForegroundColor Yellow
        Write-Host "Builder and Gardener will fail without it. Consider using -FakeMode flag." -ForegroundColor Yellow
    } else {
        Write-Host "  GEMINI_API_KEY found." -ForegroundColor Green
    }
}

if ([string]::IsNullOrWhiteSpace($env:NEO4J_PASSWORD) -or $env:NEO4J_PASSWORD -eq "your-neo4j-password-here") {
    Write-Host "ERROR: NEO4J_PASSWORD is empty or still the placeholder value." -ForegroundColor Red
    Write-Host "Edit $EnvFile and set NEO4J_PASSWORD to a real password before starting." -ForegroundColor Yellow
    exit 1
}

Write-Host "  Environment loaded." -ForegroundColor Green

# ============================================================================
# STEP 3: Check Neo4j and Redis (Docker services)
# ============================================================================
Write-Host "`n[3/6] Checking Docker services (Neo4j + Redis)..." -ForegroundColor Yellow

$DockerDir = Join-Path $ProjectRoot "docker"

# Check Neo4j
$Neo4jRunning = docker ps --filter "name=plasticflower-neo4j" --format "{{.Names}}" 2>$null
if ($Neo4jRunning) {
    Write-Host "  Neo4j already running." -ForegroundColor Green
    $Neo4jStatus = docker ps --filter "name=plasticflower-neo4j" --format "{{.Status}}" 2>$null
    if ($Neo4jStatus -match "healthy") {
        Write-Host "  Neo4j is healthy." -ForegroundColor Green
    } else {
        Write-Host "  Neo4j status: $Neo4jStatus" -ForegroundColor Yellow
    }
} else {
    Write-Host "  Neo4j not running." -ForegroundColor Yellow
}

# Check Redis
$RedisRunning = docker ps --filter "name=plasticflower-redis" --format "{{.Names}}" 2>$null
if ($RedisRunning) {
    Write-Host "  Redis already running." -ForegroundColor Green
} else {
    Write-Host "  Redis not running." -ForegroundColor Yellow
}

# Start services if any are missing
if (-not $Neo4jRunning -or -not $RedisRunning) {
    Write-Host "  Starting Docker services..." -ForegroundColor Yellow
    Push-Location $DockerDir
    docker compose --env-file $EnvFile up -d
    Pop-Location
    
    if (-not $Neo4jRunning) {
    Write-Host "  Neo4j starting... waiting 15s for readiness." -ForegroundColor Yellow
    Start-Sleep -Seconds 15
    } else {
        Write-Host "  Redis starting... waiting 3s." -ForegroundColor Yellow
        Start-Sleep -Seconds 3
    }
    Write-Host "  Docker services ready." -ForegroundColor Green
}

# Verify Redis connectivity
Write-Host "  Testing Redis connection..." -NoNewline
try {
    $RedisTest = docker exec plasticflower-redis redis-cli ping 2>$null
    if ($RedisTest -eq "PONG") {
        Write-Host " OK" -ForegroundColor Green
    } else {
        Write-Host " WARNING: Redis not responding" -ForegroundColor Yellow
    }
} catch {
    Write-Host " SKIPPED (container check failed)" -ForegroundColor Gray
}

# ============================================================================
# STEP 4: Start Backend
# ============================================================================
Write-Host "`n[4/6] Starting backend..." -ForegroundColor Yellow

$BackendDir = Join-Path $ProjectRoot "backend"

if ($FakeMode) {
    $env:PLASTICFLOWER_FAKE_LLM = "1"
    $env:PLASTICFLOWER_FAKE_EMBEDDINGS = "1"
    Write-Host "  FAKE MODE enabled (no Gemini API calls)." -ForegroundColor Yellow
} else {
    Remove-Item Env:PLASTICFLOWER_FAKE_LLM -ErrorAction SilentlyContinue
    Remove-Item Env:PLASTICFLOWER_FAKE_EMBEDDINGS -ErrorAction SilentlyContinue
    Write-Host "  REAL MODE (using Gemini API)." -ForegroundColor Green
}

# Start backend in new window (inherits environment variables automatically)
$BackendCmd = "cd '$BackendDir'; "
if ($FakeMode) {
    $BackendCmd += "`$env:PLASTICFLOWER_FAKE_LLM='1'; `$env:PLASTICFLOWER_FAKE_EMBEDDINGS='1'; "
}
$BackendCmd += "python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    $BackendCmd
) -WindowStyle Normal

Write-Host "  Backend starting on http://127.0.0.1:8010..." -ForegroundColor Yellow
Write-Host "  Waiting 8s for backend to initialize..." -ForegroundColor Gray
Start-Sleep -Seconds 8

# Check backend health
Write-Host "  Checking backend health..." -NoNewline
try {
    $Health = Invoke-WebRequest -Uri "http://127.0.0.1:8010/health" -UseBasicParsing -TimeoutSec 10 -ErrorAction Stop
    if ($Health.StatusCode -eq 200) {
        Write-Host " HEALTHY" -ForegroundColor Green
    } else {
        Write-Host " Status: $($Health.StatusCode)" -ForegroundColor Yellow
    }
} catch {
    Write-Host " FAILED" -ForegroundColor Red
    Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  Check the backend window for error details." -ForegroundColor Yellow
    Write-Host "  Common issues:" -ForegroundColor Yellow
    Write-Host "    - Neo4j not ready yet (wait longer)" -ForegroundColor Gray
    Write-Host "    - Wrong NEO4J_PASSWORD in .env" -ForegroundColor Gray
    Write-Host "    - Missing GEMINI_API_KEY (use -FakeMode if testing)" -ForegroundColor Gray
}

# ============================================================================
# STEP 5: Start Frontend
# ============================================================================
Write-Host "`n[5/6] Starting frontend..." -ForegroundColor Yellow

$FrontendDir = Join-Path $ProjectRoot "frontend"
$env:NEXT_PUBLIC_API_URL = "http://127.0.0.1:8010"

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "cd '$FrontendDir'; `$env:NEXT_PUBLIC_API_URL='http://127.0.0.1:8010'; npm run dev"
) -WindowStyle Normal

Write-Host "  Frontend starting on http://localhost:3000..." -ForegroundColor Yellow
Write-Host "  Waiting 8s for frontend to build..." -ForegroundColor Gray
Start-Sleep -Seconds 8

# ============================================================================
# STEP 6: Final verification
# ============================================================================
Write-Host "`n[6/6] Verifying servers..." -ForegroundColor Yellow

# Check backend
$backendRunning = Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue
if ($backendRunning) {
    Write-Host "  Backend: RUNNING on port 8010" -ForegroundColor Green
} else {
    Write-Host "  Backend: NOT RUNNING (check backend window)" -ForegroundColor Red
}

# Check frontend
$frontendRunning = Get-NetTCPConnection -LocalPort 3000 -State Listen -ErrorAction SilentlyContinue
if ($frontendRunning) {
    Write-Host "  Frontend: RUNNING on port 3000" -ForegroundColor Green
} else {
    Write-Host "  Frontend: NOT RUNNING (check frontend window)" -ForegroundColor Red
}

# ============================================================================
# Summary
# ============================================================================
Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "  Status Summary" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

if ($backendRunning -and $frontendRunning) {
    Write-Host "Status: ALL SERVERS RUNNING" -ForegroundColor Green
    Write-Host ""
    Write-Host "  Frontend:  http://localhost:3000" -ForegroundColor White
    Write-Host "  Backend:   http://127.0.0.1:8010" -ForegroundColor White
    Write-Host "  API Docs:  http://127.0.0.1:8010/docs" -ForegroundColor White
    Write-Host "  Neo4j:     http://localhost:7474" -ForegroundColor White
    Write-Host "  Redis:     localhost:6379" -ForegroundColor White
    Write-Host ""
    if ($FakeMode) {
        Write-Host "  Mode: FAKE (no API calls - for testing only)" -ForegroundColor Yellow
    } else {
        Write-Host "  Mode: REAL (using Gemini API)" -ForegroundColor Green
    }
    Write-Host ""
    Write-Host "Builder and Gardener are now active!" -ForegroundColor Green
    Write-Host "Redis Streams enabled for event-driven processing." -ForegroundColor Cyan
    Write-Host "Start speaking and watch nodes appear in the graph." -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Opening browser..." -ForegroundColor Gray
    Start-Process "http://localhost:3000"
} else {
    Write-Host "Status: SOME SERVERS FAILED" -ForegroundColor Red
    Write-Host ""
    Write-Host "Check the separate PowerShell windows for error messages." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Common fixes:" -ForegroundColor Yellow
    Write-Host "  1. Ensure .env has GEMINI_API_KEY and NEO4J_PASSWORD" -ForegroundColor Gray
    Write-Host "  2. Try -FakeMode flag if testing without API key" -ForegroundColor Gray
    Write-Host "  3. Check Neo4j: docker ps --filter 'name=neo4j'" -ForegroundColor Gray
    Write-Host "  4. Restart Neo4j: cd docker; docker compose restart" -ForegroundColor Gray
}

Write-Host ""
Write-Host "Press any key to close this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

