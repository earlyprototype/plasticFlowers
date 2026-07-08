import sys
import os

OUTPUT_FILE = "debug_imports.txt"

def log(msg):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(msg + "\n")

# Clear file
with open(OUTPUT_FILE, "w") as f:
    f.write("Starting Import Debug\n")

try:
    log("1. Setting path...")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
    
    log("2. Importing app.models...")
    from app.models import ReferenceNode
    log("3. Imported app.models successfully")

    log("4. Importing app.services.tavily_mcp...")
    from app.services import tavily_mcp
    log("5. Imported tavily_mcp successfully")

    log("6. Importing app.agents.researcher...")
    from app.agents.researcher import ResearcherAgent
    log("7. Imported ResearcherAgent successfully")

    log("DONE")

except Exception as e:
    log(f"FAILED: {e}")
