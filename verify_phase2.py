import sys
import os

sys.path.insert(0, os.path.abspath('backend'))

OUTPUT_FILE = 'verify_phase2.txt'

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("Phase 2 Verification\n")

try:
    log("Importing tavily_mcp...")
    from app.services.tavily_mcp import tavily_search, TavilySearchResponse
    log("✅ tavily_mcp imports OK")
    
    log("Importing researcher...")
    from app.agents.researcher import ResearcherAgent, ResearcherAgentResult
    log("✅ researcher imports OK")
    
    log("Importing from agents __init__...")
    from app.agents import ResearcherAgent as RA, ResearchAction
    log("✅ agents __init__ exports OK")
    
    log("Importing config for tavily fields...")
    from app.config import get_settings
    settings = get_settings()
    log(f"✅ config.tavily_mcp_url = {settings.tavily_mcp_url}")
    log(f"✅ config.tavily_api_key present = {bool(settings.tavily_api_key.get_secret_value())}")
    
    log("\nAll Phase 2 imports verified!")
except Exception as e:
    log(f"❌ Import failed: {e}")
    import traceback
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
