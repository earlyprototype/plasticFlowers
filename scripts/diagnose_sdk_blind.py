
import asyncio
import sys
from dotenv import dotenv_values

async def check():
    results = []
    
    try:
        from google import genai
        results.append("IMPORT_SDK: SUCCESS")
    except Exception as e:
        results.append(f"IMPORT_SDK: FAIL_{e}")
        with open("blind_sdk_results.txt", "w") as f:
            f.write("\n".join(results))
        return

    try:
        config = dotenv_values(r"c:\Users\Fab2\Desktop\AI\_plasticFlower\.env")
        key = config.get("GEMINI_API_KEY")
        
        client = genai.Client(api_key=key)
        results.append("CLIENT_INIT: SUCCESS")
        
        # Test Generation
        response = await client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents="Hello"
        )
        if response.text:
            results.append("GENERATE: SUCCESS")
            results.append(f"RESPONSE_LEN: {len(response.text)}")
        else:
            results.append("GENERATE: EMPTY_RESPONSE")
            
    except Exception as e:
        results.append(f"SDK_ERROR: {e}")

    with open("blind_sdk_results.txt", "w") as f:
        f.write("\n".join(results))

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(check())
