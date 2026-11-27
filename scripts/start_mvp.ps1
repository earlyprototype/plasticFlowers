<#
.SYNOPSIS
    Start the plasticFlowers demo after completing the Windows setup in README.md.
.PARAMETER FakeMode
    Use synthetic LLM responses and embeddings.
.PARAMETER NoBrowser
    Keep the launcher in the terminal without opening the frontend in a browser.
#>
[CmdletBinding()]
param([switch]$FakeMode, [switch]$NoBrowser)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $PSScriptRoot
$EnvFile = Join-Path $ProjectRoot ".env"
$BackendDir = Join-Path $ProjectRoot "backend"
$FrontendDir = Join-Path $ProjectRoot "frontend"
$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
$BackendUrl = "http://127.0.0.1:8010"
$FrontendUrl = "http://127.0.0.1:3000"
$Jobs = @()
$OriginalEnvironment = @{}

function Set-LaunchVariable($Name, $Value) {
    if (-not $OriginalEnvironment.ContainsKey($Name)) {
        $OriginalEnvironment[$Name] = [Environment]::GetEnvironmentVariable($Name, "Process")
    }
    [Environment]::SetEnvironmentVariable($Name, $Value, "Process")
}

function Start-ServiceJob($Name, $Directory, $Program, $Arguments) {
    Start-Job -Name $Name -ArgumentList $Directory, $Program, $Arguments -ScriptBlock {
        param($Dir, $Exe, $CommandArguments)
        Set-Location -LiteralPath $Dir -ErrorAction Stop
        & $Exe @CommandArguments 2>&1 | ForEach-Object { "$_" }
        if ($LASTEXITCODE -ne 0) { throw "Exit code $LASTEXITCODE." }
    }
}

function Check-ServiceJobs {
    foreach ($Job in $Jobs) {
        Receive-Job $Job -ErrorAction Continue | Out-Host
        if ($Job.State -notin @("Running", "NotStarted")) {
            throw "$($Job.Name) exited unexpectedly. $($Job.ChildJobs[0].JobStateInfo.Reason)"
        }
    }
}

function Wait-ServiceResponse($Name, $Url) {
    Write-Host "Waiting for $Name at $Url"
    $Deadline = [DateTime]::UtcNow.AddSeconds(120)
    do {
        Check-ServiceJobs
        try {
            $Response = Invoke-WebRequest -Uri $Url -UseBasicParsing -TimeoutSec 5 -MaximumRedirection 0
            if ($Response.StatusCode -eq 200) { return }
        } catch {
            # Both servers can refuse connections or return a 503 during startup.
        }
        Start-Sleep -Milliseconds 500
    } while ([DateTime]::UtcNow -lt $Deadline)
    throw "$Name failed to become ready at $Url within 120 seconds."
}

try {
    if (-not (Test-Path -LiteralPath $EnvFile -PathType Leaf)) {
        throw "Copy .env.example to .env and set NEO4J_PASSWORD before starting."
    }
    $Settings = @{}
    foreach ($Line in (Get-Content -Encoding UTF8 -LiteralPath $EnvFile)) {
        if ($Line -match '^\s*([A-Za-z_][A-Za-z_0-9]*)\s*=(.*)$') {
            $Name = $Matches[1]
            $Value = $Matches[2].Trim()
            if ($Value -match '^"(.*)"$' -or $Value -match "^'(.*)'$") { $Value = $Matches[1] }
            $Settings[$Name] = $Value
            Set-LaunchVariable $Name $Value
        }
    }
    if ([string]::IsNullOrWhiteSpace($Settings.NEO4J_PASSWORD) -or $Settings.NEO4J_PASSWORD -eq "your-neo4j-password-here") {
        throw "Set NEO4J_PASSWORD in .env to a non-placeholder password."
    }
    if ($FakeMode) {
        Set-LaunchVariable "PLASTICFLOWER_FAKE_LLM" "1"
        Set-LaunchVariable "PLASTICFLOWER_FAKE_EMBEDDINGS" "1"
    }
    $FakeLlm = $env:PLASTICFLOWER_FAKE_LLM -match '^(1|true|yes|on)$'
    $FakeEmbeddings = $env:PLASTICFLOWER_FAKE_EMBEDDINGS -match '^(1|true|yes|on)$'
    if (-not ($FakeLlm -and $FakeEmbeddings) -and
        ([string]::IsNullOrWhiteSpace($env:GEMINI_API_KEY) -or $env:GEMINI_API_KEY -eq "your-gemini-api-key-here")) {
        Write-Warning "Set GEMINI_API_KEY for real inference or use -FakeMode for synthetic responses and embeddings."
    }

    if (-not (Test-Path -LiteralPath $Python -PathType Leaf)) {
        throw "Backend setup required. Follow the Windows virtual environment and pip install steps in README.md."
    }
    if (-not (Test-Path -LiteralPath (Join-Path $FrontendDir "node_modules") -PathType Container)) {
        throw "Frontend setup required. Run npm.cmd ci --prefix frontend from the project root."
    }
    $Npm = (Get-Command npm.cmd -CommandType Application -TotalCount 1).Source
    $Docker = (Get-Command docker -CommandType Application -TotalCount 1).Source

    # Check the fixed ports before probing them so an existing instance cannot satisfy readiness.
    foreach ($Service in @(@("Backend", 8010), @("Frontend", 3000))) {
        $Listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Service[1])
        try {
            $Listener.ExclusiveAddressUse = $true
            $Listener.Start()
        } catch {
            throw "$($Service[0]) failed to reserve port $($Service[1]). Check whether another instance is running."
        } finally {
            $Listener.Stop()
        }
    }

    Write-Host "Starting Neo4j and Redis..."
    $ComposeFile = Join-Path $ProjectRoot "docker\docker-compose.yml"
    & $Docker compose -f $ComposeFile --env-file $EnvFile up -d --wait --wait-timeout 180
    if ($LASTEXITCODE -ne 0) { throw "Docker Compose failed (exit code $LASTEXITCODE). Check Neo4j and Redis." }

    $Jobs += Start-ServiceJob "Backend" $BackendDir $Python @("-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8010")
    Wait-ServiceResponse "Backend" "$BackendUrl/health"

    Set-LaunchVariable "NEXT_PUBLIC_API_URL" $BackendUrl
    $Jobs += Start-ServiceJob "Frontend" $FrontendDir $Npm @("run", "dev")
    Wait-ServiceResponse "Frontend" "$FrontendUrl/"
    Check-ServiceJobs

    Write-Host "MVP Ready!"
    Write-Host "Backend: $BackendUrl/health"
    Write-Host "Frontend: $FrontendUrl/"
    Write-Host "Fake LLM: $FakeLlm. Fake embeddings: $FakeEmbeddings."
    Write-Host "Press Ctrl+C to stop the backend and frontend. Docker services stay running."
    if (-not $NoBrowser) { Start-Process "$FrontendUrl/" }
    while ($true) {
        Start-Sleep -Milliseconds 500
        Check-ServiceJobs
    }
} catch {
    [Console]::Error.WriteLine($_.Exception.Message)
    exit 1
} finally {
    foreach ($Job in $Jobs) {
        Stop-Job $Job -ErrorAction SilentlyContinue
        Remove-Job $Job -Force -ErrorAction SilentlyContinue
    }
    foreach ($Name in $OriginalEnvironment.Keys) {
        [Environment]::SetEnvironmentVariable($Name, $OriginalEnvironment[$Name], "Process")
    }
}
