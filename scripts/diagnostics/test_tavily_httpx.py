import asyncio
import logging
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))

# Configure logging
OUTPUT_FILE = "test_tavily_httpx_v2.txt"

# Clear file
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Starting Tavily HTTPX Test v2\n")

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s: %(message)s",
    handlers=[
        logging.FileHandler(OUTPUT_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

def log(msg):
    logging.info(msg)

try:
    log("1. Importing tavily_mcp...")
    from app.services.tavily_mcp import tavily_search
    log("2. Import success.")
except Exception as e:
    log(f"Import Failed: {e}")
    sys.exit(1)

async def run_test():
    try:
        log("3. Running search...")
        response = await tavily_search(
            query="DeepMind Gemini",
            max_results=1,
            search_depth="basic"
        )
        
        log(f"4. Search complete. Query: {response.query}")
        log(f"   Results: {len(response.results)}")
        if response.results:
            log(f"   First Result: {response.results[0].title}")
            log(f"   URL: {response.results[0].url}")
        else:
            log("   No results found.")
            
    except Exception as e:
        log(f"❌ FAILED: {e}")
        import traceback
        with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
            f.write(traceback.format_exc())

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
