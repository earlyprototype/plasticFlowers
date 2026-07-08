# Graph Density Improvements - Automated Testing Script
# Tests the frontend changes for spacing and edge hiding

Write-Host "================================" -ForegroundColor Cyan
Write-Host "Graph Density Improvements Test" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host ""

$ErrorActionPreference = "Continue"
$testsPassed = 0
$testsFailed = 0
$testsSkipped = 0

# Get script directory and project root
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$projectRoot = Split-Path -Parent $scriptDir

# Test 1: Verify GraphCanvas.tsx exists and is readable
Write-Host "[Test 1] Checking GraphCanvas.tsx exists..." -NoNewline
$graphCanvasPath = Join-Path $projectRoot "frontend\src\components\graph\GraphCanvas.tsx"
if (Test-Path $graphCanvasPath) {
    Write-Host " PASS" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  ERROR: GraphCanvas.tsx not found at $graphCanvasPath" -ForegroundColor Red
    $testsFailed++
    exit 1
}

# Test 2: Verify FCOSE_OPTIONS parameter changes
Write-Host "[Test 2] Verifying fCoSE spacing parameters updated..." -NoNewline
$content = Get-Content $graphCanvasPath -Raw

$checks = @(
    @{ param = "nodeRepulsion: 25000"; found = $false },
    @{ param = "idealEdgeLength: 300"; found = $false },
    @{ param = "nodeSeparation: 200"; found = $false },
    @{ param = "gravity: 0.1"; found = $false },
    @{ param = "tilingPaddingVertical: 100"; found = $false },
    @{ param = "tilingPaddingHorizontal: 100"; found = $false }
)

$allFound = $true
foreach ($check in $checks) {
    if ($content -match [regex]::Escape($check.param)) {
        $check.found = $true
    } else {
        $allFound = $false
    }
}

if ($allFound) {
    Write-Host " PASS" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host " FAIL" -ForegroundColor Red
    foreach ($check in $checks) {
        if (-not $check.found) {
            Write-Host "  ERROR: Missing or incorrect: $($check.param)" -ForegroundColor Red
        }
    }
    $testsFailed++
}

# Test 3: Verify edge hiding code is present
Write-Host "[Test 3] Verifying edge hiding implementation..." -NoNewline

$edgeHidingChecks = @(
    "repositioningNodeIds",
    "affectedEdges",
    "PHASE 1: Hide edges",
    "PHASE 3: Fade edges back",
    "opacity: 0",
    "opacity: 1"
)

$allPresent = $true
foreach ($check in $edgeHidingChecks) {
    if (-not ($content -match [regex]::Escape($check))) {
        $allPresent = $false
        Write-Host ""
        Write-Host "  ERROR: Missing: $check" -ForegroundColor Red
    }
}

if ($allPresent) {
    Write-Host " PASS" -ForegroundColor Green
    $testsPassed++
} else {
    $testsFailed++
}

# Test 4: Verify no syntax errors (TypeScript compilation check)
Write-Host "[Test 4] Checking TypeScript compilation..." -NoNewline

$frontendPath = Join-Path $projectRoot "frontend"
Push-Location $frontendPath

# Check if node_modules exists
if (-not (Test-Path "node_modules")) {
    Write-Host " SKIP" -ForegroundColor Yellow
    Write-Host "  REASON: node_modules not found. Run 'npm install' first." -ForegroundColor Yellow
    $testsSkipped++
    Pop-Location
} else {
    # Run TypeScript compiler in check mode
    $tscOutput = & npm run build 2>&1
    $tscExitCode = $LASTEXITCODE
    
    if ($tscExitCode -eq 0) {
        Write-Host " PASS" -ForegroundColor Green
        $testsPassed++
    } else {
        Write-Host " FAIL" -ForegroundColor Red
        Write-Host "  ERROR: TypeScript compilation errors found" -ForegroundColor Red
        Write-Host "  Run 'npm run build' in frontend directory for details" -ForegroundColor Red
        $testsFailed++
    }
    Pop-Location
}

# Test 5: Verify console log statements are present
Write-Host "[Test 5] Verifying console logging for edge hiding..." -NoNewline

if ($content -match "Hiding .+ edges during animation" -and 
    $content -match "Restored .+ edges") {
    Write-Host " PASS" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host " FAIL" -ForegroundColor Red
    Write-Host "  ERROR: Expected console.log statements not found" -ForegroundColor Red
    $testsFailed++
}

# Test 6: Verify timing values are correct
Write-Host "[Test 6] Verifying animation timing values..." -NoNewline

$timingChecks = @(
    @{ desc = "Edge fade-out duration"; pattern = "duration: 300"; found = $false },
    @{ desc = "Edge fade-in duration"; pattern = "duration: 600"; found = $false },
    @{ desc = "Edge restore delay"; pattern = "1400"; found = $false }
)

$allTimingsCorrect = $true
foreach ($check in $timingChecks) {
    if ($content -match [regex]::Escape($check.pattern)) {
        $check.found = $true
    } else {
        $allTimingsCorrect = $false
    }
}

if ($allTimingsCorrect) {
    Write-Host " PASS" -ForegroundColor Green
    $testsPassed++
} else {
    Write-Host " FAIL" -ForegroundColor Red
    foreach ($check in $timingChecks) {
        if (-not $check.found) {
            Write-Host "  ERROR: Timing issue: $($check.desc) - $($check.pattern)" -ForegroundColor Red
        }
    }
    $testsFailed++
}

# Summary
Write-Host ""
Write-Host "================================" -ForegroundColor Cyan
Write-Host "Test Summary" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan
Write-Host "PASSED: $testsPassed" -ForegroundColor Green
Write-Host "FAILED: $testsFailed" -ForegroundColor Red
Write-Host "SKIPPED: $testsSkipped" -ForegroundColor Yellow
Write-Host ""

if ($testsFailed -eq 0) {
    Write-Host "All automated tests passed!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next Steps:" -ForegroundColor Cyan
    Write-Host "1. Start backend: cd backend && python -m uvicorn app.main:app --reload --port 8010" -ForegroundColor White
    Write-Host "2. Start frontend: cd frontend && npm run dev" -ForegroundColor White
    Write-Host "3. Open http://localhost:3000" -ForegroundColor White
    Write-Host "4. Follow manual testing checklist in GRAPH_DENSITY_TESTING.md" -ForegroundColor White
    Write-Host ""
    Write-Host "Key things to verify manually:" -ForegroundColor Yellow
    Write-Host "  - Zero 'invalid endpoints' console errors" -ForegroundColor White
    Write-Host "  - Edges fade out/in during flower formation" -ForegroundColor White
    Write-Host "  - Graph has 2-3x more spacing than before" -ForegroundColor White
    Write-Host "  - Console shows '[Organic Positioning] Hiding X edges' messages" -ForegroundColor White
    exit 0
} else {
    Write-Host "Some tests failed. Please review errors above." -ForegroundColor Red
    exit 1
}

