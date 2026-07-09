"""Explore the current graph state for manual clustering exercise (Phase C.1)."""

import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from neo4j import GraphDatabase


def main():
    load_dotenv(Path(__file__).resolve().parents[2] / ".env")

    password = os.environ.get("NEO4J_PASSWORD")
    if not password:
        sys.exit(
            "ERROR: NEO4J_PASSWORD is not set. "
            "Set it in the repo-root .env (copy .env.example) or export it."
        )

    driver = GraphDatabase.driver(
        os.environ.get("NEO4J_URI", "neo4j://127.0.0.1:7687"),
        auth=(os.environ.get("NEO4J_USERNAME", "neo4j"), password),
    )

    with driver.session() as session:
        # Count by type
        result = session.run(
            "MATCH (n) RETURN labels(n)[0] as label, count(n) as count ORDER BY count DESC"
        )
        print("=== Node Counts by Type ===")
        for record in result:
            print(f"  {record['label']}: {record['count']}")

        # Get sessions with node counts
        result = session.run("""
            MATCH (s:Session)
            OPTIONAL MATCH (n:Node {session_id: s.id})
            WITH s, count(n) as nodeCount
            RETURN s.id as id, s.title as title, nodeCount
            ORDER BY nodeCount DESC
            LIMIT 5
        """)
        print("\n=== Sessions (by node count) ===")
        sessions = list(result)
        for record in sessions:
            print(f"  {record['id']}: {record['title']} ({record['nodeCount']} nodes)")

        # Pick largest session for detailed view
        if sessions and sessions[0]["nodeCount"] > 0:
            sid = sessions[0]["id"]
            print(f"\n=== Detailed View: Session {sid} ===")

            # Get nodes
            result = session.run(
                """
                MATCH (n:Node {session_id: $sid})
                RETURN n.id as id, n.label as label, n.status as status, 
                       n.inferred_type as type, n.mentions as mentions
                ORDER BY n.mentions DESC, n.label
            """,
                sid=sid,
            )
            print("\nNodes (sorted by mentions):")
            nodes = list(result)
            for record in nodes:
                status = record["status"] or "?"
                ntype = record["type"] or "unknown"
                mentions = record["mentions"] or 0
                print(f"  [{status}] {record['label']} ({ntype}) - {mentions} mentions")

            # Get relationships
            result = session.run(
                """
                MATCH (a:Node {session_id: $sid})-[r]->(b:Node {session_id: $sid})
                RETURN a.label as from_label, type(r) as rel_type, 
                       r.description as desc, b.label as to_label
                LIMIT 50
            """,
                sid=sid,
            )
            print("\nRelationships:")
            rels = list(result)
            for record in rels:
                desc = record["desc"] or record["rel_type"]
                print(f"  {record['from_label']} --[{desc}]--> {record['to_label']}")

            print(f"\nTotal: {len(nodes)} nodes, {len(rels)} relationships")

            # Check Flowers in this session
            result = session.run(
                """
                MATCH (f:Flower {session_id: $sid})
                OPTIONAL MATCH (n:Node)-[:BELONGS_TO]->(f)
                WITH f, collect(n.label) as members
                RETURN f.id as id, f.label as label, f.stem_node_id as stem, 
                       size(members) as member_count, members
                ORDER BY member_count DESC
            """,
                sid=sid,
            )
            flowers = list(result)
            print(f"\nFlowers ({len(flowers)}):")
            for f in flowers[:10]:  # Show first 10
                members = f["members"][:5] if f["members"] else []
                more = f"... +{len(f['members']) - 5}" if len(f["members"] or []) > 5 else ""
                print(f"  [{f['label']}] ({f['member_count']} members): {members}{more}")

    driver.close()


if __name__ == "__main__":
    main()

