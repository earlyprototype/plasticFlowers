"""Test embedding exclusion in list_nodes."""
import asyncio
from app.services.graph_db import list_nodes
from app.models import NodeStatus

async def test():
    try:
        print("Testing embedding exclusion...")
        nodes = await list_nodes('session_4387d19a5939466a81c7c534662692eb', status=NodeStatus.GHOST)
        print(f'Loaded {len(nodes)} nodes')
        if nodes:
            print(f'First node has embedding: {nodes[0].embedding is not None}')
            print(f'First node label: {nodes[0].label}')
            print(f'First node status: {nodes[0].status}')
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test())

