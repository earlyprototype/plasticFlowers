import sys
import os
import traceback

# Ensure backend directory is in path
sys.path.insert(0, os.path.abspath('backend'))

OUTPUT_FILE = 'verify_result.txt'

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

# Clear previous
with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("Verification Started\n")

try:
    log("Importing ReferenceNode...")
    from app.models.reference import ReferenceNode, EntityType, SearchProvider
    log("✅ Reference model imports successful")
    
    log("Importing ResearchAction...")
    from app.agents.gardener import ResearchAction
    log("✅ ResearchAction import successful")
    
    log("Importing __init__ exports...")
    from app.models import ReferenceNode as RefNodeExport
    log("✅ ReferenceNode export in __init__ successful")
    
    log("All checks passed.")
except Exception as e:
    log(f"❌ Import failed: {e}")
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
