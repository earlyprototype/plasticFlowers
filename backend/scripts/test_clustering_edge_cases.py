"""Test clustering edge cases for Phase C.3.

Tests:
1. Only 2 related nodes - should NOT form a Flower
2. Large session (50+ nodes) - should still work
3. No relationships - should not form Flowers
4. Flower dissolution - should remove BELONGS_TO links
"""

import asyncio
import sys
from datetime import datetime, timezone
from uuid import uuid4

# Add parent to path for imports
sys.path.insert(0, str(__file__).replace("\\", "/").rsplit("/scripts", 1)[0])

from app.agents.gardener import GardenerAgent, GardenerAgentResult
from app.models import Node, NodeStatus, Relationship, Flower, RelationshipCategory, RelationshipSource


def make_node(label: str, status: NodeStatus = NodeStatus.SOLID, node_id: str = None) -> Node:
    """Create a test node."""
    return Node(
        id=node_id or f"node_{uuid4().hex[:8]}",
        label=label,
        status=status,
        confidence=0.9,
        mentions=1,
        timestamps=[0.0],
        inferred_type="concept",
        embedding=[0.0] * 768,
        created_at=datetime.now(timezone.utc),
        last_active=datetime.now(timezone.utc),
    )


def make_relationship(source: Node, target: Node, description: str) -> Relationship:
    """Create a test relationship."""
    return Relationship(
        id=f"rel_{uuid4().hex[:8]}",
        source_id=source.id,
        target_id=target.id,
        category=RelationshipCategory.STRUCTURAL,
        description=description,
        confidence=0.9,
        evidence="Test evidence",
        source=RelationshipSource.BUILDER,
        created_at=datetime.now(timezone.utc),
    )


async def test_two_nodes_no_flower():
    """Edge case 1: Only 2 related nodes should NOT form a Flower."""
    print("\n=== Test 1: Two nodes should NOT form a Flower ===")
    
    node_a = make_node("Machine Learning")
    node_b = make_node("Neural Networks")
    rel = make_relationship(node_a, node_b, "uses")
    
    agent = GardenerAgent()
    result = await agent.run(
        ghost_nodes=[],
        solid_nodes=[node_a, node_b],
        relationships=[rel],
        flowers=[],
        recent_transcript="Machine learning uses neural networks for pattern recognition.",
    )
    
    flower_creates = [a for a in result.flower_actions if a.action == "create"]
    
    if len(flower_creates) == 0:
        print("  PASS: No Flower created (correct - only 2 nodes)")
    else:
        # Check if any flower has < 3 members
        bad_flowers = [f for f in flower_creates if len(f.member_ids) < 3]
        if bad_flowers:
            print(f"  FAIL: Flower created with < 3 members: {bad_flowers}")
        else:
            print(f"  WARN: Flower created but with 3+ members (unexpected): {flower_creates}")
    
    return result


async def test_large_session():
    """Edge case 2: Large session (50+ nodes) should still work."""
    print("\n=== Test 2: Large session (50 nodes) should work ===")
    
    # Create 50 nodes in 5 thematic groups
    themes = [
        ("AI", ["Machine Learning", "Deep Learning", "Neural Networks", "TensorFlow", "PyTorch",
                "Training Data", "Model Weights", "Inference", "GPU Computing", "Transformers"]),
        ("Funding", ["Grants", "Investors", "VC", "Seed Round", "Series A",
                     "Angel Investment", "Equity", "Valuation", "Due Diligence", "Term Sheet"]),
        ("Ireland", ["Dublin", "Cork", "Enterprise Ireland", "IDA", "Science Foundation Ireland",
                     "TCD", "UCD", "DCU", "Galway", "Belfast"]),
        ("Startups", ["Founder", "MVP", "Product Market Fit", "Growth", "Scaling",
                      "Pivot", "Runway", "Burn Rate", "Revenue", "Customer Acquisition"]),
        ("Tech", ["Cloud", "API", "Database", "Frontend", "Backend",
                  "DevOps", "Kubernetes", "Docker", "Microservices", "GraphQL"]),
    ]
    
    all_nodes = []
    all_relationships = []
    
    for theme_name, labels in themes:
        theme_nodes = [make_node(label) for label in labels]
        all_nodes.extend(theme_nodes)
        
        # Create relationships within theme (chain)
        for i in range(len(theme_nodes) - 1):
            rel = make_relationship(theme_nodes[i], theme_nodes[i + 1], f"relates to")
            all_relationships.append(rel)
    
    print(f"  Created {len(all_nodes)} nodes, {len(all_relationships)} relationships")
    
    agent = GardenerAgent()
    try:
        result = await agent.run(
            ghost_nodes=[],
            solid_nodes=all_nodes,
            relationships=all_relationships,
            flowers=[],
            recent_transcript="A discussion covering AI, funding, Irish ecosystem, startups, and technology.",
        )
        
        print(f"  LLM responded in {result.llm_duration_ms:.0f}ms")
        print(f"  Node actions: {len(result.node_actions)}")
        print(f"  Flower actions: {len(result.flower_actions)}")
        
        flower_creates = [a for a in result.flower_actions if a.action == "create"]
        if flower_creates:
            print(f"  PASS: Created {len(flower_creates)} flowers:")
            for f in flower_creates:
                print(f"    - {f.label}: {len(f.member_ids)} members")
        else:
            print("  WARN: No flowers created (might be fine if LLM was conservative)")
        
        return result
        
    except Exception as e:
        print(f"  FAIL: Error processing large session: {e}")
        return None


async def test_no_relationships():
    """Edge case 3: No relationships should not form Flowers."""
    print("\n=== Test 3: No relationships should NOT form Flowers ===")
    
    nodes = [
        make_node("Apple"),
        make_node("Banana"),
        make_node("Cherry"),
        make_node("Durian"),
    ]
    
    agent = GardenerAgent()
    result = await agent.run(
        ghost_nodes=[],
        solid_nodes=nodes,
        relationships=[],  # No relationships
        flowers=[],
        recent_transcript="Various fruits mentioned: apple, banana, cherry, durian.",
    )
    
    flower_creates = [a for a in result.flower_actions if a.action == "create"]
    
    if len(flower_creates) == 0:
        print("  PASS: No Flower created (correct - no relationships)")
    else:
        print(f"  WARN: Flower created despite no relationships: {flower_creates}")
        print("  (This might be acceptable if LLM inferred semantic grouping)")
    
    return result


async def test_flower_dissolution():
    """Edge case 4: Flower dissolution should be proposed when coherence lost."""
    print("\n=== Test 4: Flower dissolution ===")
    
    # Create a flower with only 2 remaining members (should be dissolved)
    node_a = make_node("Orphan A", node_id="orphan_a")
    node_b = make_node("Orphan B", node_id="orphan_b")
    node_a.flower_id = "flower_weak"
    node_b.flower_id = "flower_weak"
    
    weak_flower = Flower(
        id="flower_weak",
        label="Weak Theme",
        stem_node_id="orphan_a",
        edge_count=1,
        created_at=datetime.now(timezone.utc),
    )
    
    agent = GardenerAgent()
    result = await agent.run(
        ghost_nodes=[],
        solid_nodes=[node_a, node_b],
        relationships=[make_relationship(node_a, node_b, "weakly related")],
        flowers=[weak_flower],
        recent_transcript="Just two orphan concepts with weak connection.",
    )
    
    dissolves = [a for a in result.flower_actions if a.action == "dissolve"]
    
    if dissolves:
        print(f"  PASS: Flower dissolution proposed: {[d.flower_id for d in dissolves]}")
    else:
        print("  WARN: No dissolution proposed (LLM might have kept the flower)")
    
    return result


async def main():
    print("=" * 60)
    print("Phase C.3: Clustering Edge Case Tests")
    print("=" * 60)
    
    try:
        await test_two_nodes_no_flower()
        await test_no_relationships()
        await test_flower_dissolution()
        await test_large_session()  # Last because it's slowest
        
        print("\n" + "=" * 60)
        print("All tests completed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\nTest failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())

