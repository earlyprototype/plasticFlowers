
import asyncio
import sys
import os
from neo4j import GraphDatabase
from dotenv import dotenv_values

async def check():
    results = []
    
    try:
        config = dotenv_values(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
        password = config.get("NEO4J_PASSWORD", "plasticflower")
        uri = "neo4j://127.0.0.1:7687"
        
        results.append(f"URI: {uri}")
        
        driver = GraphDatabase.driver(uri, auth=("neo4j", password))
        results.append("DRIVER_INIT: SUCCESS")
        
        # Verify Connectivity
        try:
            driver.verify_connectivity()
            results.append("CONNECTIVITY: SUCCESS")
        except Exception as e:
            results.append(f"CONNECTIVITY: FAIL_{e}")
            
        driver.close()
        
    except Exception as e:
        results.append(f"NEO4J_ERROR: {e}")

    with open("blind_neo4j_results.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    # Driver sync usage doesn't need async loop usually but verify_connectivity might
    # fast verify
    asyncio.run(check())
