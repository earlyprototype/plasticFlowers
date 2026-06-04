
import asyncio
import logging
import sys
import os
from datetime import datetime, timezone
from uuid import uuid4

# Setup paths
sys.path.insert(0, r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("debug_builder")

from app.services.builder_service import BuilderService
from app.models import TranscriptChunk, Node, Relationship
from app.config import get_settings

async def debug_pipeline():
    print("\n=== PLASTIC FLOWER BUILDER DEBUGGER ===")
    
    # 1. Check Settings
    try:
        settings = get_settings()
        api_key = settings.gemini_api_key.get_secret_value()
        print(f"[CHECK] Gemini API Key preset: {bool(api_key)}")
        if api_key:
             print(f"       Key prefix: {api_key[:4]}...")
    except Exception as e:
        print(f"[ERROR] Loading settings failed: {e}")
        return

    # 2. Check Service Init
    print("\n[STEP 1] Initializing BuilderService...")
    try:
        # Enable skip_neo4j to isolate LLM issues first? 
        # No, let's test full pipeline but maybe warn if DB fails.
        # We'll stick to standard init.
        service = BuilderService()
        print("[OK] BuilderService initialized.")
    except Exception as e:
        print(f"[ERROR] Service init failed: {e}")
        return

    # 3. Create Test Chunk
    session_id = f"debug_session_{uuid4().hex[:8]}"
    chunk_id = f"chunk_{uuid4().hex[:8]}"
    text = "The concept of resilience is critical in modern distributed systems engineering. It contrasts with robustness."
    
    chunk = TranscriptChunk(
        id=chunk_id,
        text=text,
        start_time=1000.0,
        end_time=1005.0,
        session_id=session_id
    )
    print(f"\n[STEP 2] Processing Chunk: {chunk_id}")
    print(f"       Text: \"{text}\"")

    # 4. Process
    try:
        print("       Sending to process_chunk (waiting for LLM)...")
        # We manually skip the queue and call process directly
        start_t = datetime.now()
        result = await service.process_chunk(session_id, chunk)
        end_t = datetime.now()
        
        print(f"\n[SUCCESS] Pipeline Finished in {(end_t - start_t).total_seconds():.2f}s")
        print(f"       Nodes Created: {len(result.nodes)}")
        for n in result.nodes:
            print(f"         - {n.label} ({n.inferred_type})")
            
        print(f"       Relationships: {len(result.relationships)}")
        for r in result.relationships:
            print(f"         - {r.source_id} -> {r.target_id}: {r.description}")
            
    except Exception as e:
        print(f"\n[FAIL] Processing failed!")
        print(f"       Error Type: {type(e).__name__}")
        print(f"       Error Message: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(debug_pipeline())
