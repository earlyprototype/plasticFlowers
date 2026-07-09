"""10-minute real Gemini demo for Gate 7."""
import requests
import time
import json
from datetime import datetime

BASE = "http://127.0.0.1:8010"

# Simulated lecture chunks (varied content)
CHUNKS = [
    {
        "text": "Machine learning is transforming how we build software. Neural networks, inspired by the human brain, can learn patterns from data. Deep learning is a subset that uses multiple layers.",
        "start": 0.0, "end": 30.0
    },
    {
        "text": "TensorFlow and PyTorch are the two most popular frameworks. TensorFlow was created by Google, while PyTorch came from Facebook's AI research lab.",
        "start": 30.0, "end": 60.0
    },
    {
        "text": "Supervised learning uses labelled data. You give the model examples with correct answers. Classification and regression are the main types.",
        "start": 60.0, "end": 90.0
    },
    {
        "text": "Unsupervised learning finds patterns without labels. Clustering groups similar items together. K-means is a common clustering algorithm.",
        "start": 90.0, "end": 120.0
    },
    {
        "text": "Reinforcement learning is different. An agent learns by trial and error, receiving rewards for good actions. AlphaGo used this approach to beat world champions.",
        "start": 120.0, "end": 150.0
    },
    {
        "text": "Transfer learning lets you reuse trained models. Instead of training from scratch, you fine-tune an existing model. This saves time and compute resources.",
        "start": 150.0, "end": 180.0
    },
    {
        "text": "GPT and BERT revolutionised natural language processing. These transformer models understand context better than previous approaches. Attention mechanisms are the key innovation.",
        "start": 180.0, "end": 210.0
    },
    {
        "text": "Computer vision uses convolutional neural networks. CNNs can recognise objects, faces, and scenes. Self-driving cars rely heavily on this technology.",
        "start": 210.0, "end": 240.0
    },
]

def main():
    print("=" * 60)
    print("GATE 7: 10-MINUTE REAL GEMINI DEMO")
    print("=" * 60)
    print(f"Started: {datetime.now().isoformat()}")
    print(f"Chunks to process: {len(CHUNKS)}")
    print()

    # Create session
    print("[1/4] Creating session...")
    r = requests.post(f"{BASE}/api/sessions", json={"name": "gate7-demo"})
    if r.status_code != 201:
        print(f"FAILED: {r.status_code} {r.text}")
        return
    sid = r.json()["id"]
    print(f"      Session: {sid}")

    # Submit chunks with delays to respect quota
    print(f"\n[2/4] Submitting {len(CHUNKS)} chunks...")
    for i, chunk in enumerate(CHUNKS):
        r = requests.post(f"{BASE}/api/sessions/{sid}/chunks", json={
            "text": chunk["text"],
            "start_time": chunk["start"],
            "end_time": chunk["end"]
        })
        status = "OK" if r.status_code == 202 else f"ERR {r.status_code}"
        print(f"      Chunk {i+1}/{len(CHUNKS)}: {status}")
        
        # Small delay between chunks to avoid overwhelming
        if i < len(CHUNKS) - 1:
            time.sleep(1)

    # Wait for processing
    print(f"\n[3/4] Waiting for LLM processing (60s)...")
    for i in range(12):
        time.sleep(5)
        print(f"      {(i+1)*5}s elapsed...")

    # Collect results
    print(f"\n[4/4] Collecting results...")
    
    r = requests.get(f"{BASE}/api/sessions/{sid}/nodes")
    nodes = r.json().get("nodes", [])
    
    r = requests.get(f"{BASE}/api/sessions/{sid}/relationships")
    rels = r.json().get("relationships", [])
    
    r = requests.get(f"{BASE}/api/sessions/{sid}/flowers")
    flowers = r.json().get("flowers", [])

    print()
    print("=" * 60)
    print("RESULTS")
    print("=" * 60)
    print(f"Nodes:         {len(nodes)}")
    print(f"Relationships: {len(rels)}")
    print(f"Flowers:       {len(flowers)}")
    print()

    # Show some nodes
    print("Sample nodes:")
    for n in nodes[:10]:
        print(f"  - {n['label']} ({n.get('inferred_type', 'unknown')})")
    if len(nodes) > 10:
        print(f"  ... and {len(nodes)-10} more")

    print()
    print("Sample relationships:")
    # Build node lookup
    node_map = {n['id']: n['label'] for n in nodes}
    for rel in rels[:8]:
        src = node_map.get(rel['source_id'], '?')
        tgt = node_map.get(rel['target_id'], '?')
        print(f"  - {src} -> {tgt} ({rel.get('category', '?')})")
    if len(rels) > 8:
        print(f"  ... and {len(rels)-8} more")

    # Export
    print()
    print("Exporting...")
    r = requests.get(f"{BASE}/api/sessions/{sid}/export/json")
    export_data = r.json()
    
    # Save results
    results = {
        "demo": "gate7-10min",
        "timestamp": datetime.now().isoformat(),
        "session_id": sid,
        "chunks_submitted": len(CHUNKS),
        "counts": {
            "nodes": len(nodes),
            "relationships": len(rels),
            "flowers": len(flowers)
        },
        "sample_nodes": [n['label'] for n in nodes[:15]],
        "success": len(nodes) >= 10 and len(rels) >= 5
    }
    
    with open(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\_docs\_evidence\gate7\demo_10min_results.json", "w") as f:
        json.dump(results, f, indent=2)

    print()
    print("=" * 60)
    if results["success"]:
        print("DEMO PASSED")
    else:
        print("DEMO INCOMPLETE (low counts)")
    print("=" * 60)
    print(f"Results saved to: demo_10min_results.json")

    # Cleanup
    requests.delete(f"{BASE}/api/sessions/{sid}")
    print("Session cleaned up.")

if __name__ == "__main__":
    main()

