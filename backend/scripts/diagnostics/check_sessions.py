"""Check node distribution across sessions."""
import asyncio
import os
import sys

# Ensure we're in the right directory
os.chdir(os.path.dirname(os.path.abspath(__file__)))

# Session to check (from user's error)
TARGET_SESSION = "session_4387d19a5939466a81c7c534662692eb"
# Largest session (for comparison)
LARGEST_SESSION = "session_2425828cdbe243e69e2ae5bd4b8fdd6a"

# Let's also check if session_id is stored correctly on all nodes
CHECK_SESSION_ID_CONSISTENCY = True

async def check():
    print("Starting Neo4j check...", flush=True)
    try:
        from app.services.neo4j import get_driver
        driver = await get_driver()
        print("Driver connected", flush=True)
        
        async with driver.session() as session:
            # Count nodes per session
            result = await session.run("""
                MATCH (n:Node)
                RETURN n.session_id as session, count(n) as node_count
                ORDER BY node_count DESC
                LIMIT 10
            """)
            records = await result.data()
            
            print("\n=== NODES PER SESSION ===")
            for r in records:
                print(f"  {r['session']}: {r['node_count']} nodes")
            
            # Count total
            result = await session.run("MATCH (n:Node) RETURN count(n) as total")
            record = await result.single()
            print(f"\nTOTAL NODES: {record['total']}")
            
            # Check relationships
            result = await session.run("""
                MATCH ()-[r:RELATIONSHIP]->()
                RETURN r.session_id as session, count(r) as rel_count
                ORDER BY rel_count DESC
                LIMIT 10
            """)
            records = await result.data()
            
            print("\n=== RELATIONSHIPS PER SESSION ===")
            for r in records:
                print(f"  {r['session']}: {r['rel_count']} relationships")
            
            # Count total rels
            result = await session.run("MATCH ()-[r:RELATIONSHIP]->() RETURN count(r) as total")
            record = await result.single()
            print(f"\nTOTAL RELATIONSHIPS: {record['total']}")
            
            # Check the target session specifically
            print(f"\n=== TARGET SESSION: {TARGET_SESSION} ===")
            result = await session.run("""
                MATCH (n:Node {session_id: $sid})
                RETURN count(n) as node_count
            """, sid=TARGET_SESSION)
            record = await result.single()
            print(f"  Nodes: {record['node_count']}")
            
            result = await session.run("""
                MATCH ()-[r:RELATIONSHIP {session_id: $sid}]->()
                RETURN count(r) as rel_count
            """, sid=TARGET_SESSION)
            record = await result.single()
            print(f"  Relationships: {record['rel_count']}")
            
            # Check sample node data to see if embeddings are stored
            print("\n=== SAMPLE NODE (check for embeddings) ===")
            result = await session.run("""
                MATCH (n:Node {session_id: $sid})
                RETURN n LIMIT 1
            """, sid=TARGET_SESSION)
            record = await result.single()
            if record:
                node = dict(record['n'])
                print(f"  Keys: {list(node.keys())}")
                if 'embedding' in node and node['embedding']:
                    print(f"  Embedding length: {len(node['embedding'])}")
                else:
                    print(f"  No embedding stored")
                    
            # Simulate prompt size calculation
            print("\n=== SIMULATING PROMPT SIZE ===")
            from app.services.graph_db import list_nodes, list_relationships, list_flowers
            from app.models import NodeStatus
            
            ghosts = await list_nodes(TARGET_SESSION, status=NodeStatus.GHOST)
            solids = await list_nodes(TARGET_SESSION, status=NodeStatus.SOLID)
            rels = await list_relationships(TARGET_SESSION)
            flowers = await list_flowers(TARGET_SESSION)
            
            print(f"  Ghosts: {len(ghosts)}")
            print(f"  Solids: {len(solids)}")
            print(f"  Relationships: {len(rels)}")
            print(f"  Flowers: {len(flowers)}")
            
            # Check first node for embedding
            if ghosts:
                node = ghosts[0]
                if node.embedding:
                    print(f"  First ghost embedding length: {len(node.embedding)}")
                else:
                    print(f"  First ghost has no embedding")
            
            # Check transcript size
            print("\n=== TRANSCRIPT CHECK ===")
            from app.services.chunk_store import chunk_store
            transcript = await chunk_store.get_recent_transcript(TARGET_SESSION, word_limit=1000)
            print(f"  Transcript length: {len(transcript)} chars")
            print(f"  Word count: {len(transcript.split())}")
            
            # Simulate actual prompt with real transcript
            print("\n=== SIMULATING ACTUAL PROMPT ===")
            from app.agents.gardener import _render_prompt
            prompt = _render_prompt(
                ghost_nodes=ghosts,
                solid_nodes=solids,
                relationships=rels,
                flowers=flowers,
                recent_transcript=transcript,
                language_variant="en-GB",
            )
            print(f"  Prompt length: {len(prompt)} chars")
            print(f"  Estimated tokens: {len(prompt) // 4}")
            print(f"  First 500 chars: {prompt[:500]}")
            
            # Now check the largest session to compare
            print(f"\n=== LARGEST SESSION: {LARGEST_SESSION} ===")
            large_ghosts = await list_nodes(LARGEST_SESSION, status=NodeStatus.GHOST)
            large_solids = await list_nodes(LARGEST_SESSION, status=NodeStatus.SOLID)
            large_rels = await list_relationships(LARGEST_SESSION)
            large_flowers = await list_flowers(LARGEST_SESSION)
            large_transcript = await chunk_store.get_recent_transcript(LARGEST_SESSION, word_limit=1000)
            
            print(f"  Ghosts: {len(large_ghosts)}")
            print(f"  Solids: {len(large_solids)}")
            print(f"  Relationships: {len(large_rels)}")
            print(f"  Flowers: {len(large_flowers)}")
            print(f"  Transcript: {len(large_transcript)} chars")
            
            large_prompt = _render_prompt(
                ghost_nodes=large_ghosts,
                solid_nodes=large_solids,
                relationships=large_rels,
                flowers=large_flowers,
                recent_transcript=large_transcript,
                language_variant="en-GB",
            )
            print(f"  Prompt length: {len(large_prompt)} chars")
            print(f"  Estimated tokens: {len(large_prompt) // 4}")
            
            # Check for session_id consistency issues
            print("\n=== SESSION ID CONSISTENCY CHECK ===")
            
            # Check if any nodes have NULL session_id
            result = await session.run("""
                MATCH (n:Node) WHERE n.session_id IS NULL
                RETURN count(n) as orphans
            """)
            record = await result.single()
            print(f"  Nodes without session_id: {record['orphans']}")
            
            # Check if session_id in Node property matches expected pattern
            result = await session.run("""
                MATCH (n:Node)
                WHERE NOT n.session_id STARTS WITH 'session_'
                RETURN count(n) as malformed
            """)
            record = await result.single()
            print(f"  Nodes with malformed session_id: {record['malformed']}")
            
            # Count ALL nodes to compare with sum of per-session counts
            result = await session.run("MATCH (n:Node) RETURN count(n) as total")
            record = await result.single()
            total_all = record['total']
            
            result = await session.run("""
                MATCH (n:Node)
                WHERE n.session_id IS NOT NULL
                RETURN count(n) as with_session
            """)
            record = await result.single()
            with_session = record['with_session']
            
            print(f"  Total nodes: {total_all}")
            print(f"  Nodes with session_id: {with_session}")
            print(f"  Orphaned: {total_all - with_session}")
            
    except Exception as e:
        print(f"ERROR: {e}", flush=True)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(check())

