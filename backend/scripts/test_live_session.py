"""Live end-to-end test of the plasticFlower system.

Creates a session, submits test chunks, and monitors the results.
Run while dev_server.py is running.
"""

import asyncio
import json
import sys
from datetime import datetime
import httpx

BASE_URL = "http://127.0.0.1:8010"

# Test chunks with deliberate STT errors
TEST_CHUNKS = [
    {
        "text": "Today we're talking about enter price ireland and their support programmes.",
        "start_time": 0.0,
        "end_time": 5.0,
    },
    {
        "text": "The new front tears programme is a national pre-accelerator for startups.",
        "start_time": 5.0,
        "end_time": 10.0,
    },
    {
        "text": "They also run the see dar centre for AI research in Dublin.",
        "start_time": 10.0,
        "end_time": 15.0,
    },
    {
        "text": "Machine learning and neural networks are key technologies for AI.",
        "start_time": 15.0,
        "end_time": 20.0,
    },
    {
        "text": "The programme provides funding, mentorship, and office space.",
        "start_time": 20.0,
        "end_time": 25.0,
    },
]


async def main():
    async with httpx.AsyncClient(base_url=BASE_URL, timeout=60.0) as client:
        print("=" * 60)
        print("Live End-to-End Test")
        print("=" * 60)

        # 1. Create session
        print("\n1. Creating session...")
        response = await client.post("/api/sessions", json={"name": "Live Test Session"})
        if response.status_code != 200:
            print(f"   FAIL: {response.status_code} {response.text}")
            return
        session_data = response.json()
        session_id = session_data["id"]
        print(f"   Created session: {session_id}")

        # 2. Submit chunks
        print(f"\n2. Submitting {len(TEST_CHUNKS)} chunks...")
        for i, chunk in enumerate(TEST_CHUNKS):
            response = await client.post(
                f"/api/sessions/{session_id}/chunks",
                json=chunk,
            )
            if response.status_code != 200:
                print(f"   FAIL on chunk {i}: {response.status_code} {response.text}")
                return
            result = response.json()
            nodes_created = len(result.get("nodes", []))
            rels_created = len(result.get("relationships", []))
            print(f"   Chunk {i+1}: {nodes_created} nodes, {rels_created} relationships")
            await asyncio.sleep(0.5)  # Small delay between chunks

        # 3. Wait for Gardener cycle
        print("\n3. Waiting for Gardener cycle (30 seconds)...")
        for i in range(30):
            await asyncio.sleep(1)
            if i % 10 == 9:
                print(f"   {i+1} seconds...")

        # 4. Check results
        print("\n4. Checking graph state...")
        response = await client.get(f"/api/sessions/{session_id}/graph")
        if response.status_code != 200:
            print(f"   FAIL: {response.status_code} {response.text}")
            return
        
        graph = response.json()
        nodes = graph.get("nodes", [])
        relationships = graph.get("relationships", [])
        flowers = graph.get("flowers", [])

        print(f"\n   Nodes ({len(nodes)}):")
        for node in sorted(nodes, key=lambda n: n.get("label", ""))[:15]:
            status = node.get("status", "?")
            label = node.get("label", "?")
            ntype = node.get("inferred_type", "?")
            print(f"     [{status}] {label} ({ntype})")
        if len(nodes) > 15:
            print(f"     ... and {len(nodes) - 15} more")

        print(f"\n   Relationships ({len(relationships)}):")
        for rel in relationships[:10]:
            # Find node labels
            src = next((n["label"] for n in nodes if n["id"] == rel["source_id"]), rel["source_id"])
            tgt = next((n["label"] for n in nodes if n["id"] == rel["target_id"]), rel["target_id"])
            print(f"     {src} --[{rel.get('description', '?')}]--> {tgt}")
        if len(relationships) > 10:
            print(f"     ... and {len(relationships) - 10} more")

        print(f"\n   Flowers ({len(flowers)}):")
        for flower in flowers:
            members = [n["label"] for n in nodes if n.get("flower_id") == flower["id"]]
            print(f"     [{flower['label']}]: {members[:3]}{'...' if len(members) > 3 else ''}")

        # 5. Check for STT error fixes
        print("\n5. Checking for STT corrections...")
        expected_errors = ["enter price ireland", "new front tears", "see dar"]
        expected_fixes = ["Enterprise Ireland", "New Frontiers", "CeADAR"]
        
        node_labels = [n.get("label", "").lower() for n in nodes]
        for error, fix in zip(expected_errors, expected_fixes):
            if any(fix.lower() in label for label in node_labels):
                print(f"   FIXED: '{error}' -> '{fix}'")
            elif any(error.lower() in label for label in node_labels):
                print(f"   NOT FIXED: '{error}' still present")
            else:
                print(f"   UNCLEAR: Neither '{error}' nor '{fix}' found in nodes")

        # 6. End session
        print("\n6. Ending session...")
        await client.post(f"/api/sessions/{session_id}/end")
        print("   Session ended.")

        print("\n" + "=" * 60)
        print("Test complete!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

