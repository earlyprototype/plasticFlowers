
OUTPUT_FILE = "debug_httpx_utf8.txt"
def log(msg):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Start debug_httpx\n")

try:
    log("Importing httpx...")
    import httpx
    log(f"httpx version: {httpx.__version__}")
    
    log("Importing httpx_sse...")
    import httpx_sse
    log("httpx_sse imported")
    
    log("Importing config...")
    import sys, os
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
    from app.config import get_settings
    log("config imported")
    
    s = get_settings()
    log("Settings loaded")

    log("Importing tavily_mcp module...")
    from app.services import tavily_mcp
    log("tavily_mcp module imported")
    
except Exception as e:
    log(f"FAILED: {e}")
    import traceback
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(traceback.format_exc())
