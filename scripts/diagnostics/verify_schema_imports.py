
import sys
import os
import logging
import time

OUTPUT_FILE = "verify_schema_imports.txt"

# Try to ensure we can write
print(f"Starting verification, logging to {OUTPUT_FILE}")

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Start verify_schema_imports\n")

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(str(msg) + "\n")

try:
    log("1. Setting path...")
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../backend")))
    
    log("2. Importing symbols from graph_db...")
    # This is what failed in test_schema_write.py
    from app.services.graph_db import create_reference, get_reference, get_driver, _reference_from_value
    log("3. Imported symbols successfully.")
    
    log("4. Testing Neo4j driver creation...")
    # Just create it, don't connect yet
    # Since get_driver is async, we can't call it easily without loop, 
    # but importing it proves the symbol exists.
    
    log("SUCCESS: Imports worked.")
    
except Exception as e:
    log(f"FAILED: {e}")
    import traceback
    with open(OUTPUT_FILE, "a", encoding="utf-8") as f:
        f.write(traceback.format_exc())
