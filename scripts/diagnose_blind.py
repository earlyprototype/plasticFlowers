
import os
import sys
import asyncio
from dotenv import dotenv_values

async def check():
    results = []
    
    # 1. Environment
    try:
        config = dotenv_values(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
        key = config.get("GEMINI_API_KEY")
        results.append(f"ENV_READ: {'OK' if key else 'MISSING'}")
        if key:
            results.append(f"KEY_PREFIX: {key[:4]}...")
    except Exception as e:
        results.append(f"ENV_ERROR: {e}")

    # 2. Neo4j
    results.append("NEO4J_CHECK: Skipped (focusing on LLM first)")

    # 3. Gemini HTTP Check (No SDK)
    import urllib.request
    import json
    
    if key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={key}"
        data = {"contents": [{"parts": [{"text": "Hello"}]}]}
        try:
            req = urllib.request.Request(
                url, 
                json.dumps(data).encode("utf-8"), 
                {"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                if response.status == 200:
                    results.append("GEMINI_HTTP: SUCCESS")
                else:
                    results.append(f"GEMINI_HTTP: FAIL_STATUS_{response.status}")
        except Exception as e:
            results.append(f"GEMINI_HTTP: ERROR_{e}")
    else:
        results.append("GEMINI_HTTP: SKIPPED_NO_KEY")

    # Write results
    with open("blind_diag_results.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
