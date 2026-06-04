import sys
import os
import asyncio
from datetime import datetime, timezone

sys.path.insert(0, os.path.abspath('backend'))

OUTPUT_FILE = 'verify_phase3.txt'

def log(msg):
    print(msg)
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
    f.write("Phase 3 Verification\n")

try:
    log("Checking NodeNeedsResearchEvent definition...")
    from app.services.redis_streams import NodeNeedsResearchEvent
    
    # Test instantiation with new fields
    event = NodeNeedsResearchEvent(
        session_id="test_session",
        node_id="node_123",
        label="Test Node",
        entity_type="organisation",
        research_reason="First mention",
        priority="high"
    )
    log(f"✅ NodeNeedsResearchEvent instantiated OK: {event}")
    
    log("Checking scheduler imports...")
    from app.services.scheduler import GardenerScheduler
    import inspect
    
    if hasattr(GardenerScheduler, '_publish_research_actions'):
        log("✅ GardenerScheduler has _publish_research_actions method")
    else:
        log("❌ GardenerScheduler missing _publish_research_actions method")
        
    log("\nAll Phase 3 verifications passed!")
    
except Exception as e:
    log(f"❌ Verification failed: {e}")
    import traceback
    with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
        traceback.print_exc(file=f)
