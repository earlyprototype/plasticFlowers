"""Quick script to check session data."""
import asyncio
from app.services.graph_db import get_driver

async def main():
    driver = await get_driver()
    session_id = "session_f7010545dc254a77861f4455eed96863"
    
    async with driver.session() as s:
        # Check nodes
        result = await s.run('''
            MATCH (n:Node {session_id: $sid})
            RETURN n.label as label, n.inferred_type as type
            LIMIT 10
        ''', sid=session_id)
        print("Nodes:")
        async for r in result:
            print(f"  - {r['label']} ({r['type']})")
        
        # Check relationships
        result = await s.run('''
            MATCH (a:Node {session_id: $sid})-[r:RELATIONSHIP]->(b:Node {session_id: $sid})
            RETURN a.label as from, r.description as rel, b.label as to
            LIMIT 10
        ''', sid=session_id)
        print("\nRelationships:")
        async for r in result:
            print(f"  - {r['from']} --[{r['rel']}]--> {r['to']}")

if __name__ == "__main__":
    asyncio.run(main())

