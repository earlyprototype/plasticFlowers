import asyncio
import os
from app.services.graph_db import list_nodes
from app.models import NodeStatus
from app.services import get_driver, close_driver

# Manually load env for Neo4j password if needed, or rely on .env loading by pydantic-settings
# But we need to ensure config is loaded.
from app.config import get_settings

async def main():
    try:
        driver = await get_driver()
        session_id = "session_f32a93f27c364149abd0b7abb1972de9"
        ghosts = await list_nodes(session_id, status=NodeStatus.GHOST)
        print(f"Ghost nodes count: {len(ghosts)}")
        for node in ghosts:
            print(f"- {node.id}: {node.label}")
    finally:
        await close_driver()

if __name__ == "__main__":
    asyncio.run(main())

