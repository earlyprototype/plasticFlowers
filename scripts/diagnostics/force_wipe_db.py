# Force Wipe Neo4j Database
# Use this when docker volume removal fails or data is corrupted

import asyncio
import os
import sys

# Add backend to path so we can import services
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "backend"))

from app.services.neo4j import get_driver

async def wipe_database():
    print("Connecting to Neo4j...")
    driver = await get_driver()
    
    print("Wiping all data...")
    query = "MATCH (n) DETACH DELETE n"
    
    async with driver.session() as session:
        result = await session.run(query)
        summary = await result.consume()
        print(f"Deleted {summary.counters.nodes_deleted} nodes and {summary.counters.relationships_deleted} relationships.")

    print("Database is clean.")
    await driver.close()

if __name__ == "__main__":
    try:
        # Load environment variables if needed
        from dotenv import load_dotenv
        load_dotenv(os.path.join(os.path.dirname(__file__), "..", "backend", ".env"))
        
        asyncio.run(wipe_database())
    except Exception as e:
        print(f"Error: {e}")

