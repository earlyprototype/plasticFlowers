"""Quick script to check session data.

Usage: python check_session.py <session_id>
Example: python check_session.py session_f7010545dc254a77861f4455eed96863
"""
import asyncio
import sys
from app.services.graph_db import get_driver

async def main():
    if len(sys.argv) < 2:
        print("Usage: python check_session.py <session_id>")
        print("Example: python check_session.py session_f7010545dc254a77861f4455eed96863")
        sys.exit(1)
    session_id = sys.argv[1]
    driver = await get_driver()
    
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

