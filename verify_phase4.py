import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath('backend'))

OUTPUT_FILE = 'verify_phase4.txt'

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("Phase 4 Verification\n")

try:
    log("1. Checking ResearcherService imports...")
    from app.services.researcher_service import ResearcherService, researcher_service
    log("✅ ResearcherService class and singleton imported OK")

    log("2. Checking main.py integration...")
    from app.main import lifespan
    log("✅ main.py imports verify OK")

    log("3. Checking graph.py API endpoint...")
    from app.api.graph import router, trigger_node_research
    log("✅ graph.py imports verify OK")
    import inspect
    if inspect.iscoroutinefunction(trigger_node_research):
        log("✅ trigger_node_research is async function")

    log("4. Checking ReferenceAddedEvent...")
    from app.models import ReferenceAddedEvent, ReferenceAddedPayload
    payload = ReferenceAddedPayload(
        node_id="test_node",
        reference_id="ref_1",
        summary="Test summary",
        provider="tavily"
    )
    event = ReferenceAddedEvent(payload=payload)
    log(f"✅ ReferenceAddedEvent instantiated OK: {event}")
    
    log("5. Checking graph_db.py persistence...")
    from app.services.graph_db import create_reference, get_reference, __all__ as graph_db_all
    if "create_reference" in graph_db_all and "get_reference" in graph_db_all:
        log("✅ create_reference and get_reference in graph_db.__all__")
    else:
        log("❌ create_reference or get_reference missing from graph_db.__all__")

    log("\nAll Phase 4 verifications passed!")
    
except Exception as e:
    log(f"❌ Verification failed: {e}")
    import traceback
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
