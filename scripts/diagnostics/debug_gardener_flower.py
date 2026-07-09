
import asyncio
import sys
import os
import logging
from datetime import datetime, timezone
from uuid import uuid4

# Setup paths
sys.path.insert(0, r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend")

# Apply policy (standard for Windows now)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

print("Importing models...", flush=True)
from app.models import Node, Relationship, RelationshipCategory, RelationshipSource, NodeStatus
print("Importing GardenerAgent...", flush=True)
from app.agents.gardener import GardenerAgent
print("Imports done.", flush=True)

# Configure basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_flower_formation():
    print("=== TESTING FLOWER FORMATION LOGIC ===")
    
    # 1. Create a "Perfect Flower" Cluster
    # Theme: Pets
    nodes = [
        Node(id="node_1", label="Dog", inferred_type="Animal", status=NodeStatus.SOLID, confidence=1.0, mentions=1, created_at=datetime.now(timezone.utc)),
        Node(id="node_2", label="Cat", inferred_type="Animal", status=NodeStatus.SOLID, confidence=1.0, mentions=1, created_at=datetime.now(timezone.utc)),
        Node(id="node_3", label="Hamster", inferred_type="Animal", status=NodeStatus.SOLID, confidence=1.0, mentions=1, created_at=datetime.now(timezone.utc)),
        Node(id="node_4", label="Pet", inferred_type="Concept", status=NodeStatus.SOLID, confidence=1.0, mentions=3, created_at=datetime.now(timezone.utc)),
    ]
    
    # Fully connected to "Pet" (Star topology)
    relationships = [
        Relationship(id="rel_1", source_id="node_1", target_id="node_4", category=RelationshipCategory.ASSOCIATIVE, description="is a", confidence=1.0, source=RelationshipSource.USER, created_at=datetime.now(timezone.utc)),
        Relationship(id="rel_2", source_id="node_2", target_id="node_4", category=RelationshipCategory.ASSOCIATIVE, description="is a", confidence=1.0, source=RelationshipSource.USER, created_at=datetime.now(timezone.utc)),
        Relationship(id="rel_3", source_id="node_3", target_id="node_4", category=RelationshipCategory.ASSOCIATIVE, description="is a", confidence=1.0, source=RelationshipSource.USER, created_at=datetime.now(timezone.utc)),
    ]
    
    print(f"Input: {len(nodes)} Solid Nodes, {len(relationships)} Relationships")
    print("Expected: 1 Flower (Label ~ 'Pets', Stem='node_4')")
    
    # 2. Run Gardener Agent
    agent = GardenerAgent()
    
    try:
        result = await agent.run(
            ghost_nodes=[],
            solid_nodes=nodes,
            relationships=relationships,
            flowers=[],
            recent_transcript="We have many pets. A dog is a pet. A cat is a pet. A hamster is also a pet.",
        )
        
        print("\n=== RAW RESULT ===")
        print(f"LLM Duration: {result.llm_duration_ms:.0f}ms")
        print(f"Flower Actions: {len(result.flower_actions)}")
        
        for action in result.flower_actions:
            print(f"- Action: {action.action}")
            print(f"  Label: {action.label}")
            print(f"  Stem: {action.stem_node_id}")
            print(f"  Members: {action.member_ids}")
            print(f"  Reason: {action.reason}")
            
        # Validation Logic Mimic (from scheduler.py)
        for action in result.flower_actions:
            member_ids = action.member_ids
            # Count edges
            edge_count = sum(1 for r in relationships if r.source_id in member_ids and r.target_id in member_ids)
            print(f"\nValidation Check for '{action.label}':")
            print(f"  Member Count: {len(member_ids)} (Requires >= 3)")
            print(f"  Edge Count: {edge_count} (Requires >= 2)")
            
            if len(member_ids) < 3:
                print("  [FAIL] Not enough members!")
            elif edge_count < 2:
                print("  [FAIL] Not enough internal edges!")
            else:
                print("  [PASS] Valid Flower Candidate")

    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_flower_formation())
