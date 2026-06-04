# plasticFlower - Clone Reference Repositories
# Run this script to download all reference repositories

Write-Host "=== plasticFlower Reference Repository Cloning ===" -ForegroundColor Cyan
Write-Host ""

# HIGH PRIORITY
Write-Host "[HIGH] Cloning Graphiti (real-time knowledge graphs)..." -ForegroundColor Green
git clone https://github.com/getzep/graphiti.git "_discovery/_repo/real-time-kg/graphiti/repo"

Write-Host "[HIGH] Cloning GraphRAG (Microsoft LLM extraction)..." -ForegroundColor Green
git clone https://github.com/microsoft/graphrag.git "_discovery/_repo/llm-extraction/graphrag/repo"

# MEDIUM PRIORITY
Write-Host "[MEDIUM] Cloning KinGVisher (web visualization)..." -ForegroundColor Yellow
git clone https://github.com/WSE-research/KinGVisher-Knowledge-Graph-Visualizer.git "_discovery/_repo/visualization/kingvisher/repo"

Write-Host "[MEDIUM] Cloning Open Semantic Graph Explorer..." -ForegroundColor Yellow
git clone https://github.com/opensemanticsearch/open-semantic-visual-graph-explorer.git "_discovery/_repo/visualization/open-semantic-graph-explorer/repo"

# LOW PRIORITY (optional - uncomment to include)
# Write-Host "[LOW] Cloning Graphster..." -ForegroundColor Gray
# git clone https://github.com/wisecubeai/graphster.git "_discovery/_repo/llm-extraction/graphster/repo"

# Write-Host "[LOW] Cloning Pykg2vec..." -ForegroundColor Gray
# git clone https://github.com/Sujit-O/pykg2vec.git "_discovery/_repo/embeddings/pykg2vec/repo"

Write-Host ""
Write-Host "=== Cloning Complete ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:"
Write-Host "  1. Review _relevance.md in each directory"
Write-Host "  2. Start with Graphiti and GraphRAG (HIGH priority)"
Write-Host "  3. Reference visualization repos for UX patterns"
Write-Host ""


