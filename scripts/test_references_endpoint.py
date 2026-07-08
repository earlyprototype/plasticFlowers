
import asyncio
import httpx
from app.services.graph_db import create_session_record, create_node, create_reference, get_driver
from app.models import Node, ReferenceNode, ReferenceSource, NodeStatus
from datetime import datetime, timezone

async def test_references_endpoint():
    session_id = f"test_ref_{int(datetime.now().timestamp())}"
    
    # 1. Setup Data
    print(f"Creating session {session_id}...")
    await create_session_record(session_id, "Ref Test", datetime.now(timezone.utc))
    
    node = Node(
        id="node1",
        label="Test Entity",
        status=NodeStatus.SOLID,
        created_at=datetime.now(timezone.utc),
        confidence=0.9,
        mentions=1,
        timestamps=[0.0],
        inferred_type="concept",
        flower_id=None
    )
    await create_node(session_id, node)
    
    ref = ReferenceNode(
        id=f"ref_{node.id}",
        node_id=node.id,
        session_id=session_id,
        entity_type="Concept",
        canonical_summary="This is a test summary.",
        confidence=0.95,
        search_provider="tavily",
        fetched_at=datetime.now(timezone.utc),
        sources=[
            ReferenceSource(title="Source 1", url="http://example.com/1", snippet="Snippet 1", source_type="web"),
            ReferenceSource(title="Source 2", url="http://example.com/2", snippet="Snippet 2", source_type="web")
        ]
    )
    await create_reference(session_id, ref)
    print("Reference created in DB.")

    # 2. Test API
    async with httpx.AsyncClient(base_url="http://127.0.0.1:8010") as client:
        print(f"Fetching references for {session_id}...")
        resp = await client.get(f"/api/sessions/{session_id}/references")
        
        if resp.status_code != 200:
            print(f"FAILED: {resp.status_code} {resp.text}")
            return
            
        data = resp.json()
        print(f"Response: {data}")
        
        refs = data.get("references", [])
        if len(refs) == 1 and refs[0]["id"] == ref.id:
            print("SUCCESS: Reference retrieved correctly.")
            print(f"Sources count: {len(refs[0]['sources'])}")
        else:
            print("FAILED: Reference data mismatch.")

    # Cleanup (Optional)
    # await delete_session_record(session_id)

if __name__ == "__main__":
    asyncio.run(test_references_endpoint())
