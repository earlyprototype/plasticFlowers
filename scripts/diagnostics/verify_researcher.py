import asyncio
import json
import logging
import os
import sys
from pathlib import Path

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

from app.agents.researcher import ResearcherAgent
from app.models import ReferenceNode

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

OUTPUT_FILE = "verify_researcher.txt"

def log_to_file(msg):
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

async def run_verification():
    """Run ResearcherAgent against fixtures using real Tavily API."""
    
    # clear output file
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write("Starting Researcher Verification\n")

    fixtures_path = Path("backend/tests/fixtures/research_testing.json")
    if not fixtures_path.exists():
        log_to_file(f"Fixtures not found at {fixtures_path}")
        return

    with open(fixtures_path, "r") as f:
        fixtures = json.load(f)

    agent = ResearcherAgent()
    
    log_to_file(f"Running verification on {len(fixtures)} fixtures...")
    log_to_file("-" * 60)

    for i, item in enumerate(fixtures):
        label = item["node_label"]
        entity_type = item["entity_type"]
        log_to_file(f"[{i+1}/{len(fixtures)}] Researching: '{label}' ({entity_type})...")
        
        try:
            # Create a fake session/node ID
            result = await agent.research(
                session_id="test_session",
                node_id=f"node_{i}",
                node_label=label,
                entity_type=entity_type,
                context=f"Testing research for {label}",
            )
            
            if result.reference:
                ref = result.reference
                log_to_file(f"  ✅ SUCCESS")
                log_to_file(f"  Provider: {result.provider_used}")
                log_to_file(f"  Summary: {ref.canonical_summary[:100]}...")
                log_to_file(f"  Sources: {len(ref.sources)}")
                if ref.sources:
                    log_to_file(f"  Top URL: {ref.sources[0].url}")
            else:
                log_to_file(f"  ⚠️ NO RESULT RETURNED")
                
        except Exception as e:
            log_to_file(f"  ❌ FAILED: {e}")
            import traceback
            # traceback.print_exc() # skip stdout traceback
            with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
                f.write(f"Traceback: {e}\n")
            
        log_to_file("-" * 60)

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_verification())
