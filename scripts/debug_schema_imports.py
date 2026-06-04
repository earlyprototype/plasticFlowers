
import sys
import os

OUTPUT_FILE = "debug_schema_imports.txt"
def log(msg):
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Start debug_schema_imports\n")

try:
    log("1. Setting path...")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
    
    log("2. Importing app.models...")
    from app.models import ReferenceNode
    log("3. Imported app.models")

    log("4. Importing neo4j...")
    import neo4j
    log("5. Imported neo4j")

    log("6. Importing app.services.graph_db symbols...")
    from app.services.graph_db import create_reference, get_reference, get_driver, _reference_from_value
    log("7. Imported graph_db symbols")
    
except Exception as e:
    log(f"FAILED: {e}")
    import traceback
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(traceback.format_exc())
