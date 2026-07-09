import asyncio
import sys
import os
import traceback
from datetime import datetime
from uuid import uuid4

# Setup paths
sys.path.insert(0, r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend")

# Apply policy BEFORE imports
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

from app.models import TranscriptChunk
from app.services.graph_db import list_nodes
from app.services.builder_service import BuilderService

LOG_FILE = "pipeline_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}\n")

async def test_pipeline():
    log("=== STARTING PIPELINE DEBUG ===")
    
    
    try:
        log("Imports: OK")
        
        session_id = f"debug_sess_{uuid4().hex[:8]}"
        log(f"Session ID: {session_id}")
        
        # 1. Test Neo4j Read
        log("STEP 1: Testing Neo4j Read (list_nodes)...")
        try:
            nodes = await list_nodes(session_id)
            log(f"STEP 1: OK (Got {len(nodes)} nodes)")
        except Exception as e:
            log(f"STEP 1: FAILED ({e})")
            return

        # 2. Init Service
        log("STEP 2: Initializing BuilderService...")
        try:
            service = BuilderService()
            log("STEP 2: OK")
        except Exception as e:
            log(f"STEP 2: FAILED ({e})")
            return

        # 3. Create Chunk
        chunk = TranscriptChunk(
            id=f"chunk_{uuid4().hex[:8]}",
            text="Evolutionary biology provides algorithms for optimization.",
            start_time=0.0,
            end_time=5.0,
            session_id=session_id
        )

        # 4. Test LLM invoke directly (skipping process_chunk wrapper to isolate)
        log("STEP 3: Testing LLM Invocation (internal _invoke_with_retry)...")
        try:
            # We need to access the private method or agent directly
            # Let's try calling the agent directly first
            agent_result = await service._agent.build(
                chunk_text=chunk.text,
                chunk_timestamp=chunk.start_time,
                existing_nodes=[],
                existing_relationships=[]
            )
            log(f"STEP 3: OK (Extracted {len(agent_result.nodes)} nodes)")
        except Exception as e:
            log(f"STEP 3: FAILED ({e})")
            traceback.print_exc(file=open(LOG_FILE, "a"))
            return

        # 5. Full Pipeline
        log("STEP 4: Testing Full process_chunk...")
        try:
            result = await service.process_chunk(session_id, chunk)
            log("STEP 4: OK")
            log(f"Pipeline Result: {len(result.nodes)} nodes, {len(result.relationships)} rels")
        except Exception as e:
            log(f"STEP 4: FAILED ({e})")
            traceback.print_exc(file=open(LOG_FILE, "a"))
            return
            
        log("=== DEBUG COMPLETE ===")

    except Exception as e:
        log(f"GLOBAL CRASH: {e}")
        traceback.print_exc(file=open(LOG_FILE, "a"))

if __name__ == "__main__":
    # Clear log
    with open(LOG_FILE, "w") as f:
        f.write("Init...\n")
        
    asyncio.run(test_pipeline())
