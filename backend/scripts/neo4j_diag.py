"""Neo4j diagnostic script to identify timeout source."""

import asyncio
import os
import sys
from time import perf_counter

# Add backend to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neo4j import AsyncGraphDatabase


async def main():
    # Use the same settings as the app
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("neo4j_password", os.getenv("NEO4J_PASSWORD", "plasticflower"))
    
    print(f"Connecting to: {uri}")
    print(f"User: {user}")
    print(f"Password: {'*' * len(password)} ({len(password)} chars)")
    
    # Step 1: Create driver
    print("\n[1] Creating driver...")
    t0 = perf_counter()
    driver = AsyncGraphDatabase.driver(uri, auth=(user, password))
    print(f"    Driver created in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Step 2: Verify connectivity
    print("\n[2] Verifying connectivity...")
    t0 = perf_counter()
    try:
        await driver.verify_connectivity()
        print(f"    Connectivity verified in {(perf_counter() - t0)*1000:.2f}ms")
    except Exception as e:
        print(f"    FAILED after {(perf_counter() - t0)*1000:.2f}ms: {e}")
        await driver.close()
        return
    
    # Step 3: Simple query
    print("\n[3] Running simple query (RETURN 1)...")
    t0 = perf_counter()
    async with driver.session() as session:
        result = await session.run("RETURN 1 AS ok")
        record = await result.single()
        print(f"    Result: {record['ok']} in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Step 4: Create a test node
    print("\n[4] Creating test node...")
    t0 = perf_counter()
    async with driver.session() as session:
        result = await session.run(
            "CREATE (n:TestNode {id: $id, name: $name}) RETURN n",
            id="test-diag-001",
            name="Diagnostic Test"
        )
        record = await result.single()
        print(f"    Created in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Step 5: Query the node back
    print("\n[5] Querying test node...")
    t0 = perf_counter()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n:TestNode {id: $id}) RETURN n",
            id="test-diag-001"
        )
        record = await result.single()
        print(f"    Found in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Step 6: Delete the test node
    print("\n[6] Deleting test node...")
    t0 = perf_counter()
    async with driver.session() as session:
        result = await session.run(
            "MATCH (n:TestNode {id: $id}) DELETE n",
            id="test-diag-001"
        )
        await result.consume()
        print(f"    Deleted in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Step 7: Test transaction write (like app does)
    print("\n[7] Testing execute_write transaction...")
    t0 = perf_counter()
    async with driver.session() as session:
        async def _work(tx):
            result = await tx.run(
                "CREATE (n:TestNode {id: $id, name: $name}) RETURN n",
                id="test-diag-002",
                name="Transaction Test"
            )
            return await result.single()
        
        record = await session.execute_write(_work)
        print(f"    Transaction completed in {(perf_counter() - t0)*1000:.2f}ms")
    
    # Cleanup
    async with driver.session() as session:
        await session.run("MATCH (n:TestNode) DELETE n")
    
    await driver.close()
    print("\n✅ All diagnostics passed!")


if __name__ == "__main__":
    asyncio.run(main())

