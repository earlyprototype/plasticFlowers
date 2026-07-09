"""Test vector similarity search and threshold tuning.

Run from backend directory:
    python scripts/test_vector_search.py

See ADR-008 for threshold analysis results.
"""

import asyncio
from app.services.neo4j import get_driver
from app.services.graph_schema import NODE_EMBEDDING_INDEX
from app.services.embeddings import generate_embedding


async def test_existing_node():
    """Test search using an existing node's embedding."""
    driver = await get_driver()
    session_id = "session_fe90b3b2455f47dd9069df774a18efd6"
    
    get_sample = f"""
    MATCH (n:Node {{session_id: '{session_id}'}})
    WHERE n.embedding IS NOT NULL AND n.label IS NOT NULL
    RETURN n.label AS label, n.embedding AS embedding
    LIMIT 1
    """
    
    async with driver.session() as session:
        result = await session.run(get_sample)
        record = await result.single()
        if not record:
            print("No nodes with embeddings found")
            return
        
        test_label = record["label"]
        test_embedding = record["embedding"]
        print(f"Test label: {test_label}")
        print(f"Embedding dims: {len(test_embedding)}")
        
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        WHERE node.session_id = $session_id
        RETURN node.label AS label, score
        ORDER BY score DESC
        LIMIT 5
        """
        result2 = await session.run(query, {
            "index_name": NODE_EMBEDDING_INDEX,
            "top_k": 10,
            "embedding": list(test_embedding),
            "session_id": session_id
        })
        
        print("\nSimilar nodes:")
        async for rec in result2:
            print(f"  {rec['score']:.3f}: {rec['label']}")


async def test_new_labels():
    """Test search with freshly generated embeddings for various labels."""
    driver = await get_driver()
    session_id = "session_fe90b3b2455f47dd9069df774a18efd6"
    
    test_cases = [
        "artificial intelligence",
        "machine learning",
        "Neo4j database",
        "knowledge graph",
        "potato salad",  # Should be very different
    ]
    
    print("\n" + "="*60)
    print("Testing new label embeddings against existing nodes")
    print("="*60)
    
    for label in test_cases:
        embedding = await generate_embedding(label)
        print(f"\nQuery: '{label}'")
        
        query = """
        CALL db.index.vector.queryNodes($index_name, $top_k, $embedding)
        YIELD node, score
        WHERE node.session_id = $session_id AND node.label IS NOT NULL
        RETURN node.label AS label, score
        ORDER BY score DESC
        LIMIT 3
        """
        
        async with driver.session() as session:
            result = await session.run(query, {
                "index_name": NODE_EMBEDDING_INDEX,
                "top_k": 10,
                "embedding": embedding,
                "session_id": session_id
            })
            
            async for rec in result:
                print(f"  {rec['score']:.3f}: {rec['label']}")


async def test_threshold_analysis():
    """Test specific pairs to find optimal threshold."""
    
    print("\n" + "="*60)
    print("Threshold Analysis: Pair-wise similarity scores")
    print("="*60)
    
    # Test cases: (label_a, label_b, expected_merge)
    test_pairs = [
        # Obvious matches - SHOULD merge
        ("ML", "Machine Learning", True),
        ("AI", "Artificial Intelligence", True),
        ("Graph Database", "Neo4j", True),
        
        # Related but distinct - SHOULD NOT merge
        ("AI", "Machine Learning", False),
        ("Neo4j", "MongoDB", False),
        
        # Clearly different - SHOULD NOT merge
        ("AI", "Kitchen Sink", False),
        ("Machine Learning", "Potato Salad", False),
        ("Graph Database", "Coffee Machine", False),
    ]
    
    print(f"\n{'Label A':<25} {'Label B':<25} {'Score':>8} {'Expected':>10} {'Result':>10}")
    print("-" * 88)
    
    threshold_candidates = {0.85: 0, 0.88: 0, 0.90: 0, 0.92: 0, 0.94: 0, 0.96: 0}
    
    for label_a, label_b, should_merge in test_pairs:
        emb_a = await generate_embedding(label_a)
        emb_b = await generate_embedding(label_b)
        
        # Cosine similarity
        dot = sum(a * b for a, b in zip(emb_a, emb_b))
        mag_a = sum(a * a for a in emb_a) ** 0.5
        mag_b = sum(b * b for b in emb_b) ** 0.5
        score = dot / (mag_a * mag_b)
        
        expected = "MERGE" if should_merge else "DISTINCT"
        
        # Check accuracy at different thresholds
        for thresh in threshold_candidates:
            would_merge = score >= thresh
            if would_merge == should_merge:
                threshold_candidates[thresh] += 1
        
        # Determine if current 0.92 would be correct
        result = "OK" if (score >= 0.92) == should_merge else "WRONG"
        
        print(f"{label_a:<25} {label_b:<25} {score:>8.3f} {expected:>10} {result:>10}")
    
    print("\n" + "-" * 60)
    print("Threshold accuracy (correct predictions out of", len(test_pairs), "):")
    for thresh, correct in sorted(threshold_candidates.items()):
        pct = correct / len(test_pairs) * 100
        marker = " <-- CURRENT" if thresh == 0.92 else ""
        print(f"  {thresh:.2f}: {correct}/{len(test_pairs)} ({pct:.0f}%){marker}")


async def main():
    print("Test 1: Existing node embedding")
    await test_existing_node()
    
    print("\n\nTest 2: New label embeddings")
    await test_new_labels()
    
    print("\n\nTest 3: Threshold analysis")
    await test_threshold_analysis()


if __name__ == "__main__":
    asyncio.run(main())

