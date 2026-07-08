# Reset Neo4j Database for Flower Relationship Migration
# This script stops Neo4j, removes the data volume, and restarts it fresh

Write-Host "=== Flower Relationship Migration: Database Reset ===" -ForegroundColor Cyan
Write-Host ""

# Navigate to docker directory
Push-Location "$PSScriptRoot\..\docker"

Write-Host "1. Stopping Neo4j container..." -ForegroundColor Yellow
docker compose down

Write-Host ""
Write-Host "2. Removing Neo4j data volume..." -ForegroundColor Yellow
docker volume rm docker_neo4j_data

Write-Host ""
Write-Host "3. Starting Neo4j with fresh database..." -ForegroundColor Yellow
docker compose up -d neo4j

Write-Host ""
Write-Host "4. Waiting for Neo4j to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host ""
Write-Host "=== Database Reset Complete ===" -ForegroundColor Green
Write-Host ""
Write-Host "Neo4j Browser: http://localhost:7474" -ForegroundColor Cyan
Write-Host "Username: neo4j" -ForegroundColor Cyan
Write-Host "Password: plasticflower" -ForegroundColor Cyan

Pop-Location

