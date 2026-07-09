"""Quick diagnostic script to check Gardener state."""
import asyncio
import sys
sys.path.insert(0, '.')

from app.services.graph_db import list_nodes, list_relationships, list_flowers
from app.services.neo4j import get_driver
from app.models import NodeStatus


async def check_session(session_id: str):
    driver = await get_driver()
    
    ghost_nodes = await list_nodes(session_id, status=NodeStatus.GHOST)
    solid_nodes = await list_nodes(session_id, status=NodeStatus.SOLID)
    all_nodes = await list_nodes(session_id)
    relationships = await list_relationships(session_id)
    flowers = await list_flowers(session_id)
    
    print(f"\n=== Session: {session_id} ===")
    print(f"Total nodes: {len(all_nodes)}")
    print(f"  - GHOST: {len(ghost_nodes)}")
    print(f"  - SOLID: {len(solid_nodes)}")
    print(f"  - Other: {len(all_nodes) - len(ghost_nodes) - len(solid_nodes)}")
    print(f"Relationships: {len(relationships)}")
    print(f"Flowers: {len(flowers)}")
    
    if ghost_nodes:
        print(f"\nFirst 5 GHOST nodes:")
        for node in ghost_nodes[:5]:
            print(f"  - {node.id}: {node.label}")
    else:
        print("\nNo GHOST nodes (all confirmed or none exist)")
    
    if solid_nodes:
        print(f"\nFirst 5 SOLID nodes:")
        for node in solid_nodes[:5]:
            print(f"  - {node.id}: {node.label}")
    
    # Check for clusters (nodes with 2+ relationships)
    node_edge_counts = {}
    for rel in relationships:
        node_edge_counts[rel.source_id] = node_edge_counts.get(rel.source_id, 0) + 1
        node_edge_counts[rel.target_id] = node_edge_counts.get(rel.target_id, 0) + 1
    
    well_connected = [(nid, count) for nid, count in node_edge_counts.items() if count >= 2]
    print(f"\nNodes with 2+ connections: {len(well_connected)}")
    
    if well_connected:
        print("Top 5 most connected:")
        for nid, count in sorted(well_connected, key=lambda x: -x[1])[:5]:
            node = next((n for n in all_nodes if n.id == nid), None)
            label = node.label if node else "?"
            print(f"  - {nid}: {count} edges ({label})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python check_gardener.py <session_id>")
        print("Example: python check_gardener.py session_2ffc526a10844e0db1998ad3bc732...")
        sys.exit(1)
    
    session_id = sys.argv[1]
    asyncio.run(check_session(session_id))


