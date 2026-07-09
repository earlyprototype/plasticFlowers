
import sys
import os
from datetime import datetime

# Setup paths
sys.path.insert(0, r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend")

LOG_FILE = "import_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

log("=== STARTING IMPORT DEBUG ===")

modules = [
    "app.config",
    "app.models", 
    "app.services.sse_manager",
    "app.services.redis_streams",
    "app.services.graph_db",
    "app.services.embeddings",
    "app.services.similarity",
    "app.agents.builder",
    "app.services.builder_service"
]

for mod in modules:
    log(f"Importing {mod}...")
    try:
        __import__(mod)
        log(f"Imported {mod} OK")
    except Exception as e:
        log(f"FAILED to import {mod}: {e}")
        break

log("=== DONE ===")
