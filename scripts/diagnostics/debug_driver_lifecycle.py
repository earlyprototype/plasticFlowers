
import asyncio
import sys
import os
# Setup paths
sys.path.insert(0, r"c:\Users\Fab2\Desktop\AI\_plasticFlower\backend")

from app.services.neo4j import get_driver, close_driver
from neo4j import AsyncGraphDatabase

LOG_FILE = "driver_lifecycle_log.txt"

def log(msg):
    with open(LOG_FILE, "a") as f:
        f.write(f"{msg}\n")
    print(msg)

async def test_lifecycle():
    log("=== STARTING DRIVER LIFECYCLE DEBUG ===")
    
    try:
        # Loop 10 times to check for pool exhaustion (default pool is usually 100 but maybe less?)
        # If it hangs, we know connection is leaking.
        
        for i in range(1, 150):
            log(f"Iteration {i}")
            driver = await get_driver()
            
            # Read
            async with driver.session() as session:
                log(f"  Iter {i}: Read Session Acquired")
                async def read_work(tx):
                    res = await tx.run("RETURN 1 AS ok")
                    return await res.single()
                await session.execute_read(read_work)
                log(f"  Iter {i}: Read Done")
            
            # Write
            async with driver.session() as session:
                log(f"  Iter {i}: Write Session Acquired")
                async def write_work(tx):
                    res = await tx.run("MERGE (n:DebugLifecycle {id: $id}) RETURN n", id=i)
                    return await res.single()
                await session.execute_write(write_work)
                log(f"  Iter {i}: Write Done")

        log("=== SUCCESS ===")
        
    except Exception as e:
        log(f"ERROR: {e}")
    finally:
        await close_driver()

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(test_lifecycle())
