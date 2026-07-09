
import asyncio
import sys
import os
import logging

# Configure logging
OUTPUT_FILE = "test_schema_write_utf8_v2.txt"
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write("Starting Schema Test v2\n")

logging.basicConfig(
    level=logging.INFO,
    handlers=[
        logging.FileHandler(OUTPUT_FILE, encoding="utf-8"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

async def run_test():
    try:
        logger.info("Importing services...")
        from app.services.graph_db import create_reference, get_reference, get_driver, _reference_from_value
        
        from app.models import ReferenceNode, ReferenceSource, SearchProvider, EntityType
        logger.info("Imports success.")
    except Exception as e:
        logger.error(f"Import failed: {e}")
        return

    session_id = "test_schema_session"
    session_id = "test_schema_session"
    node_id = "test_root_node"
    
    # 1. Setup: Ensure root node exists
    driver = await get_driver()
    async with driver.session() as session:
        await session.run(
            "MERGE (n:Node {id: $node_id, session_id: $session_id, label: 'Schema Test'})",
            node_id=node_id, session_id=session_id
        )
    
    # 2. Create Reference with multiple sources
    ref_source1 = ReferenceSource(url="http://example.com/1", title="Source 1", content="Content 1")
    ref_source2 = ReferenceSource(url="http://example.com/2", title="Source 2", content="Content 2")
    
    ref = ReferenceNode(
        node_id=node_id,
        entity_type=EntityType.concept,
        search_provider=SearchProvider.tavily,
        sources=[ref_source1, ref_source2],
        canonical_summary="A summary of the sources."
    )
    
    logger.info("Creating reference with new schema...")
    try:
        created_ref = await create_reference(session_id, ref)
        logger.info(f"Reference created: {created_ref.id}")
    except Exception as e:
        logger.error(f"Failed to create persistence: {e}")
        return

    # 3. Verify in DB directly (check for Source nodes)
    async with driver.session() as session:
        result = await session.run(
            """
            MATCH (r:Reference {id: $ref_id})-[:CITED_BY]->(s:Source)
            RETURN count(s) as source_count, collect(s.url) as urls
            """,
            ref_id=created_ref.id
        )
        record = await result.single()
        source_count = record["source_count"]
        urls = record["urls"]
        
        logger.info(f"Direct DB Check: Found {source_count} connected Source nodes.")
        logger.info(f"URLs: {urls}")
        
        if source_count != 2:
            logger.error("❌ Schema verification FAILED: Expected 2 Source nodes.")
        elif "http://example.com/1" not in urls:
             logger.error("❌ Schema verification FAILED: URL 1 missing.")
        else:
             logger.info("✅ Schema verification PASSED: Source nodes exploded correctly.")

    # 4. Verify get_reference recreation
    logger.info("Testing retrieval...")
    retrieved = await get_reference(session_id, node_id)
    if retrieved and len(retrieved.sources) == 2:
        logger.info("✅ functionality: get_reference reassembled sources correctly.")
    else:
        logger.error(f"❌ functionality: get_reference failed. Sources: {len(retrieved.sources) if retrieved else 'None'}")

    await driver.close()
    # await close_redis()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(run_test())
