# Test Flower Relationship Migration
# Runs backend unit tests and provides verification queries

Write-Host "=== Flower Relationship Migration: Test Suite ===" -ForegroundColor Cyan
Write-Host ""

# 1. Install package (needs to be done from inside backend directory)
Write-Host "1. Installing backend package in editable mode..." -ForegroundColor Yellow
Push-Location "$PSScriptRoot\..\backend"
python -m pip install -e .
Pop-Location

Write-Host ""
Write-Host "2. Running graph_db unit tests..." -ForegroundColor Yellow
# Run from project root so 'from backend.app...' imports work
python -m pytest backend/tests/test_graph_db.py -v

Write-Host ""
Write-Host "3. Running all backend tests..." -ForegroundColor Yellow
python -m pytest backend/tests/ -v

Write-Host ""
Write-Host "=== Manual Verification Steps ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Open Neo4j Browser: http://localhost:7474" -ForegroundColor Yellow
Write-Host ""
Write-Host "2. Run these Cypher queries:" -ForegroundColor Yellow
Write-Host ""
Write-Host "   // Check BELONGS_TO relationships exist" -ForegroundColor Gray
Write-Host "   MATCH (n:Node)-[r:BELONGS_TO]->(f:Flower)" -ForegroundColor Gray
Write-Host "   RETURN n, r, f" -ForegroundColor Gray
Write-Host ""
Write-Host "   // Verify no flower_id properties stored (should return 0)" -ForegroundColor Gray
Write-Host "   MATCH (n:Node) WHERE n.flower_id IS NOT NULL" -ForegroundColor Gray
Write-Host "   RETURN count(n)" -ForegroundColor Gray
Write-Host ""
Write-Host "3. Start backend and frontend, create session, verify flowers form" -ForegroundColor Yellow
