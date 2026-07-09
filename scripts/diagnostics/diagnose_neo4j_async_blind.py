
import asyncio
import sys
from neo4j import AsyncGraphDatabase
from dotenv import dotenv_values

async def check():
    results = []
    driver = None
    try:
        config = dotenv_values(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
        password = config.get("NEO4J_PASSWORD", "plasticflower")
        uri = "neo4j://127.0.0.1:7687"
        
        results.append(f"URI: {uri}")
        
        driver = AsyncGraphDatabase.driver(uri, auth=("neo4j", password))
        results.append("ASYNC_DRIVER_INIT: SUCCESS")
        
        # Verify Connectivity
        try:
            print("Verifying connectivity...")
            await driver.verify_connectivity()
            results.append("ASYNC_CONNECTIVITY: SUCCESS")
        except Exception as e:
            results.append(f"ASYNC_CONNECTIVITY: FAIL_{e}")

        # Test Session with Transaction Function
        try:

            async with driver.session() as session:
                async def work(tx):
                    # Write query
                    res = await tx.run("CREATE (n:TestDebugNode {created_at: timestamp()}) RETURN n")
                    rec = await res.single()
                    return rec["n"]
                
                print("Testing execute_write...")
                val = await session.execute_write(work)
                results.append(f"ASYNC_TX_WRITE: SUCCESS (Node {val.id})")
                
                # Cleanup
                await session.run("MATCH (n:TestDebugNode) DELETE n")
                
        except Exception as e:
            results.append(f"ASYNC_TX_WRITE: FAIL_{e}")
            
    except Exception as e:
        results.append(f"ASYNC_GLOBAL_ERROR: {e}")
    finally:
        if driver:
            await driver.close()

    with open("blind_neo4j_async_results.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
